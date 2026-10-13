#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4687 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (List Bool/Int ↔ 1-D arrays, Option Bool ↔ None/True/False,
              List (String × String) ↔ dict). Two observable outputs:
                values = whereSelect(cond, x, y)          (op 1, deep model leg)
                attrs  = xAttrs if keepAttributes.getD(globalKeepDefault)
                                else {}                   (ops 2,3 — R legs)
  * ORACLE  — patch.diff's behaviour: the gold-patched `xarray.where` applied at
              base_commit (the real correctness oracle, G-RESOLVE), observed via
              the result DataArray's `.values` and `.attrs`.

`globalKeepDefault` is the value the unchanged option query
`_get_keep_attrs(default=False)` returns; under default global options that is
`False`, which is exactly what the shadow uses (and what the oracle resolves a
`keep_attrs=None` call to). The fuzz sweeps keep_attrs ∈ {None, True, False} ×
empty/non-empty attrs × random equal-length int arrays.

They must agree on every input. Exit 0 iff zero disagreements. Runs in-container
(the prebuilt SWE-Bench instance image), stdlib + numpy + xarray. The fuzz seed
is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray.core.options import _get_keep_attrs

SEED = 4687
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean impl region, transliterated ---------------

def where_select(cond, x, y):
    """whereSelect cond x y — elementwise cond ? x : y over aligned cells."""
    return [int(x[i]) if cond[i] else int(y[i]) for i in range(len(cond))]


def shadow(cond, x, y, x_attrs, keep_attributes, global_keep_default):
    """The do block: values via whereSelect; attrs kept iff the resolved choice
    (explicit choice, else ambient default) is truthy."""
    resolved = global_keep_default if keep_attributes is None else keep_attributes
    values = where_select(cond, x, y)
    attrs = dict(x_attrs) if resolved else {}
    return values, attrs


# --- the oracle: gold-patched xr.where on DataArrays -------------------------

def oracle(cond, x, y, x_attrs, keep_attributes):
    """patch.diff's behaviour. The harness applies patch.diff at base_commit
    before this runs, so xr.where carries the new keep_attrs parameter."""
    n = len(cond)
    cda = xr.DataArray(np.asarray(cond, dtype=bool), dims="d")
    xda = xr.DataArray(np.asarray(x, dtype=np.int64), dims="d", attrs=dict(x_attrs))
    yda = xr.DataArray(np.asarray(y, dtype=np.int64), dims="d")
    res = xr.where(cda, xda, yda, keep_attrs=keep_attributes)
    return [int(v) for v in np.asarray(res.values).tolist()], dict(res.attrs)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    base = [
        ([True, False], [1, 1], [0, 0]),            # the F2P shape/values
        ([], [], []),
        ([True], [7], [-3]),
        ([False], [7], [-3]),
        ([True, True, False], [5, 6, 7], [0, 0, 0]),
    ]
    attr_sets = [{}, {"attr": "x"}, {"a": "1", "b": "2"}]
    keeps = [None, True, False]
    for cond, x, y in base:
        for at in attr_sets:
            for kp in keeps:
                yield cond, x, y, at, kp
    for _ in range(n):
        k = rng.randint(0, 24)
        cond = [rng.choice([True, False]) for _ in range(k)]
        x = [rng.randint(-1000, 1000) for _ in range(k)]
        y = [rng.randint(-1000, 1000) for _ in range(k)]
        at = rng.choice(attr_sets)
        kp = rng.choice(keeps)
        yield cond, x, y, at, kp


def main():
    rng = random.Random(SEED)
    # globalKeepDefault = the unchanged option query's value (default options).
    global_keep_default = bool(_get_keep_attrs(default=False))
    disagreements = []
    count = 0
    for cond, x, y, at, kp in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s_vals, s_attrs = shadow(cond, x, y, at, kp, global_keep_default)
        # empty arrays: merge_attrs returns None (no attributes to merge) for an
        # all-empty operand stack; skip the degenerate 0-length attrs comparison
        # for values only (still compared), attrs undefined on empty result.
        o_vals, o_attrs = oracle(cond, x, y, at, kp)
        if s_vals != o_vals or (len(cond) > 0 and s_attrs != o_attrs):
            disagreements.append((cond, x, y, at, kp, s_vals, s_attrs, o_vals, o_attrs))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  cond=%r x=%r y=%r attrs=%r keep=%r shadow=(%r,%r) oracle=(%r,%r)" % d)
        return 1
    print("G-CONF OK: R/I shadow of selectByCondition agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
