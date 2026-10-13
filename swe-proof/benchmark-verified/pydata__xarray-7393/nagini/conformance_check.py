#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-7393 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helper
`effective_type` copies over as a plain function; `DenseArray.__init__` keeps
its two field initialisations with the Ensures dropped. There are no
@ContractOnly callees in this bundle (the materialisation step is modelled
deeply), so the shadow is fully executable as-is.

ORACLE: the REAL patched repo function the model models per mapping.md —
`xarray.core.indexing.PandasMultiIndexingAdapter.__array__` on the
multi-index-level branch (`level is not None`). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched module
importable. Each oracle call builds a real `pd.MultiIndex` from a level array,
wraps it in the adapter with a declared element type, and calls
`__array__(requested)` directly — exactly the code path `.values` drives.

Type bridge (mapping.md section 2): numpy element types map to opaque int
codes via an interning table (distinct dtypes <-> distinct codes; a `None`
requested type maps to Python None). The per-label values are List[int]; the
oracle result's `.dtype` maps back to a code compared against the shadow's
`etype`, and its element list compares against the shadow's `values`.

Input domain: Requires demands only read-only access to `level_values`
(fractional permission); the model never constrains declared/storage/requested.
mapping.md section 2 scopes the value bijection to lossless (widening-class)
casts — the callee's operating domain — so generated values are integers in
[-128, 127], exactly representable in every element type drawn from the pool
{int8,int16,int32,int64,float32,float64}. The storage element type is whatever
the real pandas index reports for the constructed level values (it is an
observed, non-influencing input, passed through to the shadow verbatim).
Both 1-level and 2-level indexes are exercised (level selection included).

>= 1e5 Requires-satisfying inputs: boundary cases + fuzz; each constructed
index is probed under every (requested, declared) combination, each a distinct
input to the modeled function. Pinned fuzz seed: 7393.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy (+ the repo's own pandas/xarray) only.
"""
import json
import random
import sys

import numpy as np

SEED = 7393
TARGET = 100_000

DTYPE_POOL = ["int8", "int16", "int32", "int64", "float32", "float64"]


# --- pure helper from model.py, contracts stripped -----------------------------

def effective_type(requested, declared):
    if requested is None:
        return declared
    return requested


# --- DenseArray from model.py, Ensures stripped ---------------------------------

class DenseArray:
    def __init__(self):
        self.etype = 0
        self.values = []


# --- the impl region of model.py, verbatim, contract calls stripped -------------

def materialize_level(requested, declared, storage_type, level_values):
    res = DenseArray()
    dtype = requested
    if dtype is None:
        dtype = declared
    # `dtype` is now the resolved element type; build the dense array with it.
    res.etype = dtype
    i = 0
    while i < len(level_values):
        res.values.append(level_values[i])
        i = i + 1
    return res


# --- bridge: np.dtype <-> opaque int code ---------------------------------------

_CODES = {}


def code_of(dt):
    """Intern a numpy dtype as an opaque int code (distinct dtypes <-> distinct
    codes), mirroring the model's carrier abstraction."""
    key = np.dtype(dt).str
    if key not in _CODES:
        _CODES[key] = len(_CODES)
    return _CODES[key]


def build_index(pd, values, level_dtype, n_levels, pick_level):
    """Build a real multi-index over `values` (stored at whatever element type
    pandas promotes `level_dtype` to) and return (mi, level_name, storage_dt)."""
    arrays = [np.array(values, dtype=level_dtype) for _ in range(n_levels)]
    names = ["lv%d" % k for k in range(n_levels)]
    mi = pd.MultiIndex.from_arrays(arrays, names=names)
    level_name = names[pick_level]
    storage_dt = mi.get_level_values(level_name).values.dtype
    return mi, level_name, storage_dt


def check_one(adapter_cls, mi, level_name, storage_dt, values,
              level_dtype, declared, requested, n_levels, pick_level):
    """Wrap the prebuilt index with declared element type `declared`, call the
    real __array__(requested), and diff against the shadow. Returns an error
    string on disagreement, else None."""
    requested_dt = None if requested is None else np.dtype(requested)
    declared_dt = np.dtype(declared)

    adapter = adapter_cls(mi, dtype=declared_dt, level=level_name)
    real = adapter.__array__(requested_dt)

    shadow = materialize_level(
        None if requested is None else code_of(requested_dt),
        code_of(declared_dt),
        code_of(storage_dt),
        list(values),
    )

    err = None
    if code_of(real.dtype) != shadow.etype:
        err = ("element-type code mismatch: real dtype %r (code %d) vs shadow "
               "etype %d" % (real.dtype, code_of(real.dtype), shadow.etype))
    else:
        real_vals = real.tolist()
        if len(real_vals) != len(shadow.values) or any(
                rv != sv for rv, sv in zip(real_vals, shadow.values)):
            err = ("value mismatch: real %r vs shadow %r"
                   % (real_vals, shadow.values))
    if err:
        return ("DISAGREEMENT\n  values=%r level_dtype=%r declared=%r "
                "requested=%r storage=%r n_levels=%d pick_level=%d\n  %s"
                % (values, level_dtype, declared, requested, str(storage_dt),
                   n_levels, pick_level, err))
    return None


def boundary_cases():
    """(values, level_dtype) boundary pool; each is crossed with every
    (declared, requested) combination by the driver."""
    return [
        ([], "int8"),
        ([], "int64"),
        ([0], "int8"),
        ([0, 1], "int32"),                 # the canonical narrow-coordinate case
        ([0, 1], "float32"),
        ([-128, 127], "int8"),             # int8 extremes (exact in every pool dtype)
        ([127, -128, 0, 1, -1], "int16"),
        ([5, 5, 5], "int64"),              # repeated labels
        ([-1, 0, 1], "float64"),
        (list(range(-10, 11)), "int32"),
    ]


def main():
    import pandas as pd
    from xarray.core.indexing import PandasMultiIndexingAdapter  # REAL patched repo class

    requested_pool = [None] + DTYPE_POOL

    checked = 0

    # Boundary layer: every boundary (values, level_dtype) x declared x
    # requested, on 1-level and 2-level (level 1 selected) indexes.
    for values, level_dtype in boundary_cases():
        for n_levels, pick in ((1, 0), (2, 1)):
            mi, level_name, storage_dt = build_index(
                pd, values, level_dtype, n_levels, pick)
            for declared in DTYPE_POOL:
                for requested in requested_pool:
                    err = check_one(PandasMultiIndexingAdapter, mi, level_name,
                                    storage_dt, values, level_dtype, declared,
                                    requested, n_levels, pick)
                    if err:
                        print(err)
                        return 1
                    checked += 1

    # Fuzz layer: random value vectors; each constructed index probed under
    # every (declared, requested) combination — 42 distinct modeled-function
    # inputs per index.
    rng = random.Random(SEED)
    while checked < TARGET:
        n = rng.randint(0, 8)
        values = [rng.randint(-128, 127) for _ in range(n)]
        level_dtype = rng.choice(DTYPE_POOL)
        n_levels = rng.choice((1, 2))
        pick = rng.randrange(n_levels)
        mi, level_name, storage_dt = build_index(
            pd, values, level_dtype, n_levels, pick)
        for declared in DTYPE_POOL:
            for requested in requested_pool:
                err = check_one(PandasMultiIndexingAdapter, mi, level_name,
                                storage_dt, values, level_dtype, declared,
                                requested, n_levels, pick)
                if err:
                    print(err)
                    return 1
                checked += 1

    print("G-CONF OK: shadow impl == real materialisation on %d inputs "
          "(boundary + fuzz, seed %d)." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
