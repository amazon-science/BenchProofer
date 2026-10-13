#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_sumOfWeights
against the patch.diff behaviour (the post-patch `_sum_of_weights`, boolean case).

The impl region has R/I content (the accumulator `for` loop over the paired
mask/weights, integer increments, and the zero-aggregate -> missing masking), so
this runs a real fuzz. The shadow reproduces the Lean impl's control flow
op-for-op: walk the aligned (mask, weight) pairs, add 1 whenever both are set,
and map a zero total to the missing sentinel (None ~ NaN). The reduction op
(the array contraction) is A-tagged (a deep-model reference to `xr.dot`), so —
per the G-CONF protocol — it is realised here by the REAL repo callee: the real
`xr.dot` applied to the not-null mask and the INTEGER-cast weights.

The patched side is an independent reconstruction of the POST-patch
`_sum_of_weights` body over a 1-D boolean DataArray: mask = da.notnull(); since
the weights are boolean, reduce mask against weights.astype(int) via xr.dot;
then sum_of_weights.where(sum_of_weights != 0.0).

We assert zero disagreements over >=10^5 fuzzed boolean inputs. exit 0 iff zero
disagreements.
"""
import math
import random
import sys

import numpy as np
import xarray as xr
from xarray import DataArray

SEED = 4075           # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(mask_bools, weight_bools):
    """R/I shadow of implementation_sumOfWeights.
        acc = 0                                   -- let mut acc := 0
        for (m, w) in zip(mask, weights):         -- for (m,w) in mask.zip weights do
            if m and w: acc += 1                  -- the integer multiply-accumulate
        if acc == 0: return None                  -- if acc = 0 then none
        return acc                                 -- some acc
    The reduction (acc) is the A-reference contraction; realise it via the REAL
    callee `xr.dot` on the not-null mask and the integer-cast weights, exactly as
    the post-patch code does for boolean weights."""
    n = len(mask_bools)
    if n == 0:
        return None
    mask = DataArray(np.array(mask_bools, dtype=bool), dims="x")
    weights = DataArray(np.array(weight_bools, dtype=bool), dims="x")
    # A-reference op via the real repo callee, integer-cast inputs:
    acc = float(xr.dot(mask, weights.astype(int), dims="x").values)
    if acc == 0.0:
        return None
    return acc


def patched_sum_of_weights(mask_bools, weight_bools):
    """Independent reconstruction of the POST-patch _sum_of_weights body
    (boolean-weights branch) over a 1-D DataArray."""
    n = len(mask_bools)
    if n == 0:
        return None
    da_mask = DataArray(np.array(mask_bools, dtype=bool), dims="x")
    weights = DataArray(np.array(weight_bools, dtype=bool), dims="x")
    # bool -> int because xr.dot of two boolean arrays uses boolean algebra
    if weights.dtype == bool:
        sow = xr.dot(da_mask, weights.astype(int), dims="x")
    else:
        sow = xr.dot(da_mask, weights, dims="x")
    valid = sow != 0.0
    res = sow.where(valid)
    v = float(res.values)
    if math.isnan(v):
        return None
    return v


def rand_case(rng):
    n = rng.randint(0, 12)
    mask = [rng.random() < 0.6 for _ in range(n)]
    weights = [rng.random() < 0.6 for _ in range(n)]
    return mask, weights


def norm(x):
    return None if x is None else float(x)


def main() -> int:
    rng = random.Random(SEED)

    fixed = [
        ([True, True], [True, True]),          # F2P discriminator -> 2
        ([True], [True]),                       # -> 1
        ([True, False], [False, True]),         # -> None
        ([False, False], [True, True]),         # -> None
        ([True, True, True], [True, False, True]),  # -> 2
        ([], []),                               # empty -> None
        ([True, True, True, True], [True, True, True, True]),  # -> 4
    ]
    cases = fixed + [rand_case(rng) for _ in range(N)]

    disagreements = 0
    examples = []
    for mask, weights in cases:
        got = norm(shadow(mask, weights))
        want = norm(patched_sum_of_weights(mask, weights))
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((mask, weights, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for m, w, g, wnt in examples:
            print(f"  mask={m} weights={w} shadow={g} patched={wnt}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
