#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26466 (nagini).

SHADOW: the impl regions of model.py (retain_pair_a / retain_pair_b), copied
verbatim below with the contract calls (Requires/Ensures) stripped, together
with the carrier class `Slot` realized as a plain Python object with one
attribute. The model IS Python; each impl reads the component value out of each
of the input's two storage locations and returns a freshly-built length-2 list
of two NEW locations carrying them. There are no @Pure helpers and no
@ContractOnly callees in this bundle (axioms/pure regions are empty), so nothing
else needs realizing.

ORACLE: the REAL patched repo constructors the model models per mapping.md —
`matplotlib.text.OffsetFrom.__init__` (retains the supplied pair as
`self._ref_coord`, site #1 = retain_pair_a) and
`matplotlib.text._AnnotationBase.__init__` (retains the supplied pair as
`self.xy`, site #2 = retain_pair_b). The gate applies the gold patch to
/testbed before this script runs and sets PYTHONPATH=/testbed, so the patched
module is what imports here; this script does NOT apply any patch itself.
Both constructors are exercised directly (no figure/renderer needed at
construction time), which keeps 1e5 cases fast.

Type bridge (mapping.md section 2): the model carries the (x, y) pair as a
length-2 `List[Slot]` in which entry i is the STORAGE LOCATION holding component
i and `Slot.value` is the component value stored there; the components are
OPAQUE and pinned by identity (untransformed pass-through). `Result()` at full
`list_pred` permission corresponds to the freshly-retained instance attribute,
and full permission to `Result()[i].value` corresponds to the retained pair's
component i living in storage the caller cannot overwrite. Concretely bridged
observables, per input case:
  (a) component values of the retained pair right after construction — must
      equal the input's two component values at that moment (the identity pin
      on the opaque carrier maps to exact value pass-through on the repo's
      numeric components; ndarray unpacking yields fresh scalar objects
      carrying the exact values, so the value, not CPython id, is the
      bridged observable);
  (b) CONTAINER decoupling (the full-permission `list_pred(Result())` vs the
      caller's read share) — `retained is not input`;
  (c) PER-COMPONENT-LOCATION decoupling (full permission to
      `Result()[i].value` vs the caller's read share of `pair[i].value`) —
      the observable that the container-level clauses alone cannot see, and
      the one the hidden test actually exercises. Bridged behaviourally and
      IDENTICALLY on both sides: construct, then overwrite ONLY caller
      component 0 in place and read the whole retained pair back; likewise for
      ONLY component 1; likewise for both. A retained pair whose component i
      still lives in the caller's location i moves with that overwrite, which
      shows up as a differing observation tuple. Each probe uses a FRESH
      construction so the three are independent;
  (d) the retained pair has length 2 and the input still has length 2 with
      its (post-mutation) contents intact on both sides.
The shadow runs on a length-2 list of `Slot`s holding the two component values
(its opaque objects realized as the numeric values themselves); the oracle runs
on a MUTABLE container (numpy ndarray or Python list) of those values, whose
element cells ARE the caller's two storage locations. Both sides' observation
tuples must match. NaN components compare NaN-to-NaN equal so a pass-through of
NaN is not misread as a disagreement.

Input domain: Requires demands only a readable length-2 container whose two
component locations are readable, so every 2-component numeric input is
Requires-satisfying. Boundary cases cover the problem-relevant fractional
coordinates, signed zeros, extremes, NaN/inf, ints, and immutable tuple inputs
(no mutation step); fuzz draws random float pairs and container kind
(ndarray / list) and runs all three overwrite probes on each.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases, each
run against BOTH modeled sites. Pinned fuzz seed: 2646601.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib + numpy only.
"""
import json
import math
import random
import sys

import numpy as np

SEED = 2646601
N_FUZZ = 100_000


# --- the model's carrier class, realized (model.py `class Slot`) ---------------

class Slot(object):
    """One storage location holding one component of a two-component pair."""

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def retain_pair_a(pair):
    given0 = pair[0]
    x = given0.value
    given1 = pair[1]
    y = given1.value
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]
    return retained


def retain_pair_b(pair):
    given0 = pair[0]
    x = given0.value
    given1 = pair[1]
    y = given1.value
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]
    return retained


# --- value bridge --------------------------------------------------------------

def canon(v):
    """One retained component as a comparable value (NaN-stable)."""
    f = float(v)
    if math.isnan(f):
        return "nan"
    return f


def canon_slots(p):
    """The two component values of a shadow-side length-2 List[Slot]."""
    return (canon(p[0].value), canon(p[1].value))


def canon_pair(p):
    """The two component values of a real-side 2-component container."""
    return (canon(p[0]), canon(p[1]))


# --- observation: the same tuple of observables on either side -----------------
#
# Each side runs the identical protocol. A "probe" is an in-place overwrite of a
# selected subset of the CALLER's component locations, applied after
# construction; the retained pair is read back before and after. Each probe gets
# its own fresh construction, so a probe that touches only component 0 reports
# per-location decoupling for component 0 independently of component 1.

def probe_shadow(shadow_fn, x, y, mutate):
    src = [Slot(x), Slot(y)]
    res = shadow_fn(src)
    before = canon_slots(res)
    container_fresh = res is not src
    if mutate is not None:
        mutate(ShadowCells(src))
    after = canon_slots(res)
    return (before, container_fresh, len(res) == 2, after,
            len(src) == 2, canon_slots(src))


class ShadowCells(object):
    """Writes through to the shadow input's component LOCATIONS, so that an
    in-place overwrite of the caller's storage is expressed identically on both
    sides (`cells[i] = v` overwrites caller component i)."""

    __slots__ = ("_slots",)

    def __init__(self, slots):
        self._slots = slots

    def __setitem__(self, i, v):
        self._slots[i].value = v


def probe_real(retainer, x, y, container, mutate):
    if container == "ndarray":
        src = np.array([x, y], dtype=float)
    elif container == "list":
        src = [x, y]
    else:
        src = (x, y)
    stored = retainer(src)
    before = canon_pair(stored)
    container_fresh = stored is not src
    if mutate is not None:
        mutate(src)
    after = canon_pair(stored)
    return (before, container_fresh, len(stored) == 2, after,
            len(src) == 2, canon_pair(src))


def observe_shadow(shadow_fn, x, y, mutators):
    return tuple(probe_shadow(shadow_fn, x, y, m) for m in mutators)


def observe_real(retainer, x, y, container, mutators):
    return tuple(probe_real(retainer, x, y, container, m) for m in mutators)


def check_case(sites, x, y, container, mutators, label):
    """One input case against both modeled sites; error string or None."""
    for site_label, shadow_fn, retainer in sites:
        sh = observe_shadow(shadow_fn, x, y, mutators)
        rl = observe_real(retainer, x, y, container, mutators)
        if sh != rl:
            return ("DISAGREEMENT at %s / %s\n  input=(%r, %r) as %s\n"
                    "  shadow=%r\n  real=%r"
                    % (site_label, label, x, y, container, sh, rl))
    return None


# --- input generation -----------------------------------------------------------

def set_both(v):
    def mut(cells):
        cells[0] = v
        cells[1] = v
    return mut


def set_one(i, v):
    def mut(cells):
        cells[i] = v
    return mut


def probe_set(v_both, v0, v1):
    """The three per-component decoupling probes plus the no-mutation reading."""
    return (None, set_one(0, v0), set_one(1, v1), set_both(v_both))


def boundary_cases():
    inf = float("inf")
    nan = float("nan")
    cases = []
    pairs = [(0.5, 0.5), (0.0, 0.0), (-0.0, 0.0), (1.0, 1.0),
             (-4.0, 1.0), (3.25, -7.75), (1e300, -1e300),
             (5e-324, -5e-324), (inf, -inf), (nan, 0.5), (nan, nan),
             (1, 2), (0, -3), (7, 0.5)]
    for x, y in pairs:
        for container in ("ndarray", "list"):
            cases.append((x, y, container, probe_set(1.0, 9.0, -2.5),
                          "boundary/overwrite-probes"))
        cases.append((x, y, "tuple", (None,), "boundary/immutable"))
    return cases


def main():
    # REAL patched callees (mapping.md: retain_pair_a <-> OffsetFrom.__init__,
    # retain_pair_b <-> _AnnotationBase.__init__). Neither needs an artist or
    # renderer at construction time, so both run bare.
    from matplotlib.text import OffsetFrom, _AnnotationBase

    def real_a(src):
        of = OffsetFrom(None, src)
        return of._ref_coord

    def real_b(src):
        ab = _AnnotationBase(src)
        return ab.xy

    sites = [("site-a/OffsetFrom", retain_pair_a, real_a),
             ("site-b/_AnnotationBase", retain_pair_b, real_b)]

    checked = 0
    bcases = boundary_cases()
    for x, y, container, mutators, label in bcases:
        err = check_case(sites, x, y, container, mutators, label)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        if rng.random() < 0.1:
            x = float(rng.randint(-1000, 1000))
            y = float(rng.randint(-1000, 1000))
        else:
            x = rng.uniform(-1e6, 1e6)
            y = rng.uniform(-1e6, 1e6)
        container = "ndarray" if rng.random() < 0.7 else "list"
        mutators = probe_set(rng.uniform(-10.0, 10.0),
                             rng.uniform(-10.0, 10.0),
                             rng.uniform(-10.0, 10.0))
        err = check_case(sites, x, y, container, mutators, "fuzz")
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impls == real retained pairs (values at "
          "construction, container freshness, per-component-location decoupling "
          "under selective in-place overwrite) on %d inputs x 2 sites x 4 probes "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(bcases), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions + "
                                "realized Slot carrier)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
