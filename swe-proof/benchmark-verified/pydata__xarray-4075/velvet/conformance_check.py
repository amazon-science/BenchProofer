#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4075 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (da <-> List (Option Int), weights <-> List Int, the
              weightsAreLogical flag <-> bool dtype). The impl computes the mask
              `maskOf da` (R/I) and the NUMERIC reduction `arithDot mask weights`
              (the `logical = false` leg of reduceDot the gold impl routes BOTH
              carriers through — R/I), then masks a zero total to absent (R/I).
              The A-reference `reduceDot` is exercised here on its arithmetic leg
              only, which is the concrete `arithDot` fold (an I op); the logical
              leg the gold impl never reaches stays out of scope (it is the bug,
              audited by G-AX). No consumed axiom is substituted.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Weighted._sum_of_weights`,
              reached through the public `DataArray.weighted(weights)
              .sum_of_weights()` API (the real correctness oracle, G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + numpy + xarray only. The fuzz seed is pinned (mapping.md §4).
The modeled slice is the full reduction of a 1-D (da, weights) pair to a scalar
(the F2P scenario); higher ranks broadcast the identical per-position semantics.
"""
import math
import random
import sys

import numpy as np
import xarray as xr


SEED = 4075
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean maskOf/arithDot, transliterated -----------

def shadow(da_vals, weight_vals, logical):
    """sumOfWeightsSpec (da) (weights), the R/I shadow of the impl.

    `da_vals[i] is None` <-> a missing datum (none); otherwise present (some _).
    The gold impl routes logical-carrier weights through the SAME numeric
    reduction as the others, so the shadow always uses the arithmetic total.
    """
    mask = [v is not None for v in da_vals]
    s = sum(w if m else 0 for m, w in zip(mask, weight_vals))
    return None if s == 0 else int(s)


# --- the oracle: patch.diff behaviour via the public API ---------------------

def oracle(da_vals, weight_vals, logical):
    """ORACLE: the patched _sum_of_weights, via DataArray.weighted().
    sum_of_weights(). A missing datum is NaN (float carrier needed for NaN);
    weights are carried as bool when `logical`, else int — exactly the dtype
    branch the patch keys on."""
    da = xr.DataArray(
        np.array([np.nan if v is None else float(v) for v in da_vals], dtype=float))
    if logical:
        w = xr.DataArray(np.array([bool(v) for v in weight_vals], dtype=bool))
    else:
        w = xr.DataArray(np.array(weight_vals, dtype=int))
    res = da.weighted(w).sum_of_weights()
    v = res.values.item()
    return None if (isinstance(v, float) and math.isnan(v)) else int(v)


def fuzz_inputs(n, rng):
    # boundary cases first (the F2P scenarios + masking + empties)
    yield ([1, 2], [1, 1], True)          # test_weighted_sum_of_weights_bool -> 2
    yield ([1, 1], [1, 1], True)          # mean-bool numerator path -> sow 2
    yield ([1, 2], [1, 1], False)
    yield ([1, None], [1, 1], True)       # one masked datum -> 1
    yield ([None, None], [1, 1], True)    # all masked -> 0 -> None
    yield ([1, 2], [0, 0], True)          # zero total -> None
    yield ([1, 2], [0, 0], False)
    yield ([1, 2, 3], [1, 0, 1], True)
    yield ([1], [1], True)
    yield ([1], [0], False)
    for _ in range(n):
        k = rng.randint(1, 12)
        logical = rng.random() < 0.5
        da_vals = [None if rng.random() < 0.25 else rng.randint(-9, 9)
                   for _ in range(k)]
        if logical:
            weight_vals = [rng.randint(0, 1) for _ in range(k)]      # bool carrier
        else:
            weight_vals = [rng.randint(-9, 9) for _ in range(k)]
        yield (da_vals, weight_vals, logical)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for da_vals, weight_vals, logical in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s = shadow(da_vals, weight_vals, logical)
        o = oracle(da_vals, weight_vals, logical)
        if s != o:
            disagreements.append((da_vals, weight_vals, logical, s, o))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for da, w, lg, s, o in disagreements:
            print("  da=%r weights=%r logical=%r shadow=%r oracle=%r"
                  % (da, w, lg, s, o))
        return 1
    print("G-CONF OK: R/I shadow of sumOfWeights agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
