#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6461 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. `List[int]` is a plain Python list; there
are no @Pure helpers and no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
the attribute-selection callback that `xarray.core.computation.where`
constructs when asked (keep_attrs=True) to preserve the second positional
argument's attributes. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.

Two oracle harnesses:
  1. CAPTURED-CALLBACK path (the bulk, >=1e5 inputs): call the real `where`
     with the module's array-combining entry point temporarily replaced by a
     recorder, so the genuinely-constructed callback (a closure over the real
     second argument) is captured; then invoke that real callback directly on
     the attribute-mapping list. This exercises exactly the modelled
     input->output map of the callback.
  2. END-TO-END path (boundary + a fuzz slice): run the real, unpatched-in-
     memory `where` on real DataArray/scalar argument combinations and compare
     the attributes of the produced object. This exercises the full plumbing
     that forwards the callback's choice to the output.

Type bridge (mapping.md section 2): an attribute mapping (dict) maps to an
opaque int identity; the empty mapping (also what a bare scalar carries) maps
to identity 0. The bridge realizes identity k as the dict {"tag": k} for k>0
and {} for 0 (injective, so dict content <-> identity is a bijection), and
compares by content because the repo copies attribute mappings on assignment.
`present` is the list of identities of the arguments that carry a mapping, in
argument order; `x_pos` locates the second argument's own mapping in that list
(-1 when it carries none); generation enforces the Requires clauses
(x_pos in {-1} u [0, len(present)); present[x_pos] == x_attrs when in bounds;
x_attrs == 0 when x_pos == -1).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 captured-callback
fuzz pairs + end-to-end boundary/fuzz. Pinned fuzz seed: 6461.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

SEED = 6461
N_FUZZ_CB = 100_000
N_FUZZ_E2E = 1_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def attrs_to_keep(present, x_attrs, x_pos):
    return x_attrs


# --- bridge: int identity <-> attribute-mapping dict ---------------------------

def dict_of(identity):
    """Realize an identity as a concrete attribute mapping (fresh object)."""
    return {} if identity == 0 else {"tag": identity}


def identity_ok(real_dict, identity):
    """The real callback's returned mapping agrees (by content) with the
    identity the shadow selected."""
    return real_dict == dict_of(identity)


def requires_hold(present, x_attrs, x_pos):
    if not (x_pos == -1 or (0 <= x_pos < len(present))):
        return False
    if 0 <= x_pos < len(present) and present[x_pos] != x_attrs:
        return False
    if x_pos == -1 and x_attrs != 0:
        return False
    return True


# --- oracle harness 1: capture the real callback ------------------------------

def capture_callback(where_fn, computation_mod, x_obj):
    """Call the real `where` with the module's array-combining entry point
    replaced by a recorder, so the callback it genuinely constructs (closing
    over the real second argument) is captured for direct invocation."""
    recorded = {}

    def recorder(*args, **kwargs):
        recorded["cb"] = kwargs.get("keep_attrs")
        return None

    orig = computation_mod.apply_ufunc
    computation_mod.apply_ufunc = recorder
    try:
        where_fn(0, x_obj, 0, keep_attrs=True)
    finally:
        computation_mod.apply_ufunc = orig
    cb = recorded.get("cb")
    if not callable(cb):
        print("SETUP ERROR: could not capture the selection callback "
              "(got %r)" % (cb,))
        sys.exit(2)
    return cb


def make_x(xr, x_pos, x_attrs, rng):
    """A real second argument: a DataArray owning the mapping when it is
    supposed to carry one, else a bare scalar (which carries none)."""
    if x_pos == -1:
        return rng.choice([0, 1, -3, 2.5])
    return xr.DataArray(0, attrs=dict_of(x_attrs))


def check_captured(xr, computation_mod, present, x_attrs, x_pos, rng):
    assert requires_hold(present, x_attrs, x_pos)
    x_obj = make_x(xr, x_pos, x_attrs, rng)
    cb = capture_callback(computation_mod.where, computation_mod, x_obj)
    attrs_list = [dict_of(k) for k in present]

    shadow = attrs_to_keep(list(present), x_attrs, x_pos)
    try:
        real = cb(attrs_list, None)
    except Exception as exc:  # a raising callback can never agree
        return ("DISAGREEMENT (real callback raised)\n"
                "  present=%r x_attrs=%r x_pos=%r\n  shadow=%r\n  real: %r"
                % (present, x_attrs, x_pos, shadow, exc))
    if not identity_ok(real, shadow):
        return ("DISAGREEMENT\n  present=%r x_attrs=%r x_pos=%r\n"
                "  shadow=%r (mapping %r)\n  real=%r"
                % (present, x_attrs, x_pos, shadow, dict_of(shadow), real))
    return None


# --- oracle harness 2: end-to-end through the real plumbing -------------------

def check_end_to_end(xr, where_fn, cond_id, x_id, y_id):
    """cond/x/y each either a DataArray carrying the mapping for the given
    identity, or (identity is None) a bare scalar. Derives the model inputs
    from the configuration, runs the real `where` for real, and compares the
    output's attribute mapping with the shadow's selection."""
    import numpy as np

    cond = (xr.DataArray([True, False], dims="d", attrs=dict_of(cond_id))
            if cond_id is not None else True)
    x = (xr.DataArray(np.array([1.0, 2.0]), dims="d", attrs=dict_of(x_id))
         if x_id is not None else 1)
    y = (xr.DataArray(np.array([3.0, 4.0]), dims="d", attrs=dict_of(y_id))
         if y_id is not None else 0)
    if cond_id is None and x_id is None and y_id is None:
        return None, 0  # no array-typed argument: outside this harness

    # derive the model inputs from the configuration
    ids = [i for i in (cond_id, x_id, y_id) if i is not None]
    present = list(ids)
    if x_id is None:
        x_pos, x_attrs = -1, 0
    else:
        x_pos = (1 if cond_id is not None else 0)
        x_attrs = x_id
    assert requires_hold(present, x_attrs, x_pos)

    shadow = attrs_to_keep(list(present), x_attrs, x_pos)
    try:
        actual = where_fn(cond, x, y, keep_attrs=True)
    except Exception as exc:
        return ("DISAGREEMENT (end-to-end raised)\n"
                "  cond_id=%r x_id=%r y_id=%r  (present=%r x_attrs=%r "
                "x_pos=%r)\n  shadow=%r\n  real: %r"
                % (cond_id, x_id, y_id, present, x_attrs, x_pos,
                   shadow, exc)), 1
    real_attrs = dict(getattr(actual, "attrs", {}))
    if not identity_ok(real_attrs, shadow):
        return ("DISAGREEMENT (end-to-end)\n"
                "  cond_id=%r x_id=%r y_id=%r  (present=%r x_attrs=%r "
                "x_pos=%r)\n  shadow=%r (mapping %r)\n  real=%r"
                % (cond_id, x_id, y_id, present, x_attrs, x_pos,
                   shadow, dict_of(shadow), real_attrs)), 1
    return None, 1


# --- input generation ----------------------------------------------------------

def boundary_triples():
    """(present, x_attrs, x_pos) boundary cases, all Requires-satisfying."""
    return [
        ([], 0, -1),                    # no argument carries a mapping
        ([5], 0, -1),                   # scalar second arg, one carried mapping
        ([5, 9], 0, -1),                # scalar second arg, two carried mappings
        ([7], 7, 0),                    # second arg's mapping is the only one
        ([1, 2], 1, 0),                 # at the front
        ([1, 2], 2, 1),                 # at the historical constant offset
        ([1, 2, 3], 2, 1),              # the all-carrying configuration
        ([1, 2, 3], 3, 2),              # at the back
        ([0], 0, 0),                    # second arg carries the empty mapping
        ([4, 0, 6], 0, 1),              # empty mapping among non-empty ones
        ([3, 3, 3], 3, 0),              # repeated identities
        ([3, 3, 3], 3, 2),
        (list(range(1, 9)), 4, 3),      # longer list, interior position
        (list(range(1, 9)), 8, 7),
        ([9, 8, 7, 6, 5], 0, -1),       # scalar second arg, many mappings
    ]


def rand_triple(rng):
    n = rng.randint(0, 7)
    present = [rng.randint(0, 30) for _ in range(n)]
    if n == 0 or rng.random() < 0.35:
        x_pos, x_attrs = -1, 0
    else:
        x_pos = rng.randint(0, n - 1)
        x_attrs = present[x_pos]
    return present, x_attrs, x_pos


def main():
    sys.setrecursionlimit(10_000)
    import xarray as xr                       # the REAL patched repo
    from xarray.core import computation       # module owning `where`

    rng = random.Random(SEED)
    checked = 0

    # -- captured-callback path: boundary --
    for present, x_attrs, x_pos in boundary_triples():
        err = check_captured(xr, computation, present, x_attrs, x_pos, rng)
        if err:
            print(err)
            return 1
        checked += 1

    # -- captured-callback path: fuzz --
    for _ in range(N_FUZZ_CB):
        present, x_attrs, x_pos = rand_triple(rng)
        err = check_captured(xr, computation, present, x_attrs, x_pos, rng)
        if err:
            print(err)
            return 1
        checked += 1

    # -- end-to-end path: all scalar/DataArray shapes of the three arguments --
    e2e = 0
    id_choices = (None, 0, 3)  # scalar / empty mapping / non-empty mapping
    for cond_id in id_choices:
        for x_id in id_choices:
            for y_id in id_choices:
                err, n = check_end_to_end(xr, computation.where,
                                          cond_id, x_id, y_id)
                if err:
                    print(err)
                    return 1
                checked += n
                e2e += n

    # -- end-to-end path: fuzz over identities and scalar placement --
    for _ in range(N_FUZZ_E2E):
        cond_id = rng.choice([None, rng.randint(0, 30)])
        x_id = rng.choice([None, rng.randint(0, 30)])
        y_id = rng.choice([None, rng.randint(0, 30)])
        if cond_id is None and x_id is None and y_id is None:
            cond_id = rng.randint(0, 30)
        err, n = check_end_to_end(xr, computation.where, cond_id, x_id, y_id)
        if err:
            print(err)
            return 1
        checked += n
        e2e += n

    print("G-CONF OK: shadow impl == real selection callback on %d inputs "
          "(%d boundary + %d captured-callback fuzz + %d end-to-end, seed %d)."
          % (checked, len(boundary_triples()), N_FUZZ_CB, e2e, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
