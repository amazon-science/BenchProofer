#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-7336 (nagini).

SHADOW: the impl region of model.py's ``finalize_return``, copied VERBATIM
below with only the contract calls (Requires / Ensures) stripped. The @Pure
helpers of the pure region (the two target sentinels, ``NO_UNIT`` and
``is_genuine_target``) and the pure deep model ``convert_unit`` copy over as
plain functions; ``RetVal`` copies as a plain two-field record. There are no
@ContractOnly callees (mapping.md section 3: the axioms region is empty).

ORACLE: the REAL patched repo behaviour the model models per mapping.md
section 1 — the return-finalisation tail of the ``quantity_input`` wrapper
(``astropy/units/decorators.py``). The gate applies patch.diff to /testbed
before this script runs and sets PYTHONPATH so ``astropy.units`` resolves to
the patched package. Each probe decorates a one-argument identity function
with ``quantity_input``, giving it the return annotation the abstract target
lowers to, calls it with the value the abstract ``RetVal`` lowers to, and
observes exactly the two modelled observables of the result: whether it is
the ``None`` object, and (when a quantity) its unit.

TYPE BRIDGE (mapping.md section 2):
  * ``target: int`` <-> the declared return annotation. ``TARGET_UNSPECIFIED``
    (-1) lowers to "no return annotation" (``inspect.Signature.empty`` on the
    real signature); ``TARGET_NOVALUE`` (-2) lowers to a ``None`` return
    annotation; every genuine id (>= 0 here) lowers to a distinct real unit
    from a fixed palette (plus a few string-form spellings of the same
    units, which share the id of the unit they denote).
  * ``ret: RetVal`` <-> the wrapped function's return value. ``is_none`` <->
    "the returned object is ``None``" (then ``unit == NO_UNIT()``); otherwise
    the return value is a real quantity ``value * palette[unit]``.
  * The result is raised back the same way: ``out is None`` <-> ``is_none``;
    ``out.unit`` looked up in the palette <-> ``unit``.

INPUT DOMAIN: exactly the Requires of ``finalize_return`` (``ret.is_none ==
(ret.unit == NO_UNIT())``) intersected with the domain on which the deep
model ``convert_unit`` is stated (mapping.md sections 2/3.1): the conversion
is only ever applied to a genuine quantity whose unit is convertible into the
genuine target, so under a genuine target the return value is a quantity and
the source unit is drawn from the same dimensional family as the target.
Under the two sentinel targets the return value ranges over ``None`` and
quantities of every palette unit — including the discriminating probes where
a quantity or ``None`` returns under a no-value annotation and must pass
through untouched.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): deterministic boundary cases
(``None`` and every palette unit under both sentinel targets; every
same-family (source, target) unit pair under a genuine target, including
source == target; string-form target spellings; a spread of magnitudes
including 0, negatives, tiny and huge values) plus 100000 random fuzz probes
over (target kind, family, source unit, target unit, value). Pinned fuzz
seed: 7336. Exit 0 iff zero disagreements; on disagreement prints the input
and both outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 7336
N_FUZZ = 100000


# --- pure region of model.py, contracts stripped ------------------------------

def TARGET_UNSPECIFIED():
    # the "no return target was declared" sentinel
    return -1


def TARGET_NOVALUE():
    # the "declared to produce nothing" target
    return -2


def NO_UNIT():
    # the unit id carried by the no-value object (it has none)
    return -3


def is_genuine_target(target):
    """A declared return target is a genuine unit target exactly when it is
    neither the unspecified sentinel nor the no-value target."""
    return target != TARGET_UNSPECIFIED() and target != TARGET_NOVALUE()


def convert_unit(q_unit, target):
    # deep model of the conversion: the unit id of a quantity after
    # converting it into `target` is the target unit id
    return target


class RetVal(object):
    """Two-field record: whether the value is the no-value object, and its
    current unit id when it is a quantity (contracts stripped)."""

    def __init__(self, is_none, unit):
        self.is_none = is_none
        self.unit = unit


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def finalize_return(ret, target):
    if is_genuine_target(target):
        return RetVal(False, convert_unit(ret.unit, target))
    else:
        return RetVal(ret.is_none, ret.unit)


# --- bridge: abstract unit ids / targets <-> real astropy objects -------------

def build_bridge():
    """Palette of real units, grouped into dimensional families so every
    genuine (source, target) pair fed to the oracle is convertible."""
    import astropy.units as u
    families = [
        [u.deg, u.arcsec, u.arcmin, u.rad, u.mas, u.hourangle],
        [u.m, u.km, u.cm, u.mm, u.micron, u.pc, u.au],
        [u.s, u.ms, u.min, u.h, u.d],
        [u.J, u.eV, u.erg, u.keV],
        [u.kg, u.g, u.mg],
        [u.V, u.mV],
        [u.Hz, u.kHz, u.MHz],
    ]
    units = [x for fam in families for x in fam]
    id_of = {}
    for i, x in enumerate(units):
        id_of[str(x)] = i
    fam_ids = []
    for fam in families:
        fam_ids.append([id_of[str(x)] for x in fam])
    return units, id_of, fam_ids


KIND_UNSPEC = "unspecified"
KIND_NOVALUE = "novalue"
KIND_GENUINE = "genuine"


def make_probe(kind, annotation=None):
    """A one-argument identity function run through the real decorator; the
    single parameter is deliberately unannotated so only the modelled
    return-finalisation decision is exercised."""
    from astropy.units import quantity_input

    def raw(value):
        return value

    if kind == KIND_NOVALUE:
        raw.__annotations__["return"] = None
    elif kind == KIND_GENUINE:
        raw.__annotations__["return"] = annotation
    # KIND_UNSPEC: no return annotation at all
    return quantity_input(raw)


UNKNOWN_UNIT = 10 ** 9  # oracle unit outside the palette (forces a mismatch)


def observe(out, id_of):
    """The two modelled observables of the real result, raised to the
    abstract carrier."""
    if out is None:
        return (True, NO_UNIT())
    return (False, id_of.get(str(out.unit), UNKNOWN_UNIT))


def check(probe, kind, ann_desc, is_none, src_unit, src_id, target_id,
          value, id_of):
    """Run oracle and shadow on one abstract input; return an error string on
    disagreement, else None."""
    # lower: abstract RetVal -> the real return value
    obj = None if is_none else value * src_unit
    real = observe(probe(obj), id_of)

    # shadow: the contract-stripped impl region on the abstract input
    ret = RetVal(is_none, NO_UNIT() if is_none else src_id)
    res = finalize_return(ret, target_id)
    shadow = (res.is_none, res.unit)

    if shadow != real:
        return ("DISAGREEMENT on input kind=%s annotation=%s "
                "ret=(is_none=%r, unit=%r [%s], value=%r) target=%r:\n"
                "  shadow (impl region)  = (is_none=%r, unit=%r)\n"
                "  real (patched repo)   = (is_none=%r, unit=%r)"
                % (kind, ann_desc, is_none,
                   NO_UNIT() if is_none else src_id,
                   "-" if is_none else str(src_unit), value, target_id,
                   shadow[0], shadow[1], real[0], real[1]))
    return None


def main():
    units, id_of, fam_ids = build_bridge()
    fam_of_id = {}
    for fi, ids in enumerate(fam_ids):
        for i in ids:
            fam_of_id[i] = fi

    # genuine target specs: every palette unit, plus string-form spellings
    # (which denote — and share the id of — the corresponding palette unit)
    genuine_specs = [(i, units[i], str(units[i])) for i in range(len(units))]
    for s in ("deg", "m", "s"):
        genuine_specs.append((id_of[s], s, "'%s' (string form)" % s))

    probe_unspec = make_probe(KIND_UNSPEC)
    probe_novalue = make_probe(KIND_NOVALUE)
    genuine_probes = [make_probe(KIND_GENUINE, ann)
                      for (_i, ann, _d) in genuine_specs]

    values = [0.0, 1.0, -1.0, 2.5, 1e6, 1e-6, -12345.678]
    checked = 0
    n_boundary = 0

    def run(err):
        if err:
            print(err)
            sys.exit(1)

    # --- boundary: sentinel targets x {None, every palette unit} x values ---
    for kind, probe, target_id in (
            (KIND_UNSPEC, probe_unspec, TARGET_UNSPECIFIED()),
            (KIND_NOVALUE, probe_novalue, TARGET_NOVALUE())):
        run(check(probe, kind, "-", True, None, None, target_id, None, id_of))
        checked += 1
        n_boundary += 1
        for sid in range(len(units)):
            for v in values:
                run(check(probe, kind, "-", False, units[sid], sid,
                          target_id, v, id_of))
                checked += 1
                n_boundary += 1

    # --- boundary: every same-family (source, target) pair x values ---------
    for gi, (tid, _ann, desc) in enumerate(genuine_specs):
        for sid in fam_ids[fam_of_id[tid]]:
            for v in values:
                run(check(genuine_probes[gi], KIND_GENUINE, desc, False,
                          units[sid], sid, tid, v, id_of))
                checked += 1
                n_boundary += 1

    # --- randomized fuzz over (kind, family, source, target, value) ---------
    rng = random.Random(SEED)
    n_genuine = len(genuine_specs)
    for _ in range(N_FUZZ):
        v = rng.choice((
            rng.uniform(-1e3, 1e3),
            rng.uniform(-1e12, 1e12),
            float(rng.randint(-10, 10)),
            rng.uniform(-1e-9, 1e-9),
        ))
        k = rng.random()
        if k < 0.6:
            gi = rng.randrange(n_genuine)
            tid, _ann, desc = genuine_specs[gi]
            sid = rng.choice(fam_ids[fam_of_id[tid]])
            err = check(genuine_probes[gi], KIND_GENUINE, desc, False,
                        units[sid], sid, tid, v, id_of)
        else:
            if k < 0.8:
                kind, probe, target_id = (KIND_UNSPEC, probe_unspec,
                                          TARGET_UNSPECIFIED())
            else:
                kind, probe, target_id = (KIND_NOVALUE, probe_novalue,
                                          TARGET_NOVALUE())
            if rng.random() < 0.25:
                err = check(probe, kind, "-", True, None, None, target_id,
                            None, id_of)
            else:
                sid = rng.randrange(len(units))
                err = check(probe, kind, "-", False, units[sid], sid,
                            target_id, v, id_of)
        run(err)
        checked += 1

    print("G-CONF OK: shadow impl == real patched return-finalisation on "
          "%d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
