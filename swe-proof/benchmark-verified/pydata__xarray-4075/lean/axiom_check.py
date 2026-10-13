#!/usr/bin/env python3
"""G-AX — validate the deep-model A-reference for pydata__xarray-4075.

The modeled function `_sum_of_weights` aggregates the not-null mask against the
weights via the array contraction `xr.dot`. That callee is UNCHANGED by the patch
and is modeled DEEPLY in Solution.lean as `zipDot` (an integer
multiply-and-accumulate over the aligned pairs) — an A-reference, not a consumed
axiom. This check runs the REAL callee (`xr.dot`, exactly what the post-patch
body calls, on the INTEGER-cast weights as the fix prescribes) on boundary +
fuzzed boolean inputs and asserts the deep model reproduces it exactly.

Property validated (the A-reference contract):
  zipDot(zip(mask, weights)) == int(xr.dot(mask, weights.astype(int)))
where zipDot sums 1 for each aligned position with both flags set.

This is precisely the bug/fix boundary: WITHOUT the .astype(int) cast,
xr.dot of two boolean arrays returns the boolean OR (saturates at 1); the deep
model is the INTEGER contraction, and the cast is what makes the real callee
agree with it.

exit 0 iff the deep model matches the real callee on every input.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray import DataArray

SEED = 4075           # pinned in mapping.md
N = 120_000           # >= 10^5


def zip_dot(mask, weights):
    """Python mirror of Lean `zipDot` (front-recursive integer fold)."""
    total = 0
    for m, w in zip(mask, weights):
        if m and w:
            total += 1
    return total


def real_callee(mask, weights):
    """The REAL unchanged callee invoked by the post-patch body:
    xr.dot(mask, weights.astype(int)) — the boolean weights cast to int, as the
    fix prescribes."""
    if len(mask) == 0:
        return 0
    m = DataArray(np.array(mask, dtype=bool), dims="x")
    w = DataArray(np.array(weights, dtype=bool), dims="x")
    return int(xr.dot(m, w.astype(int), dims="x").values)


def rand_case(rng):
    n = rng.randint(0, 12)
    mask = [rng.random() < 0.6 for _ in range(n)]
    weights = [rng.random() < 0.6 for _ in range(n)]
    return mask, weights


def main() -> int:
    rng = random.Random(SEED)

    fixed = [
        ([True, True], [True, True]),
        ([True], [True]),
        ([True, False], [False, True]),
        ([False, False], [True, True]),
        ([True, True, True], [True, False, True]),
        ([True, True, True, True], [True, True, True, True]),
        ([False], [False]),
    ]
    cases = fixed + [rand_case(rng) for _ in range(N)]

    mismatches = 0
    examples = []
    for mask, weights in cases:
        model = zip_dot(mask, weights)
        real = real_callee(mask, weights)
        if model != real:
            mismatches += 1
            if len(examples) < 10:
                examples.append((mask, weights, model, real))

    if mismatches:
        print(f"G-AX FAIL: deep model diverges from real callee on "
              f"{mismatches} inputs")
        for m, w, mo, r in examples:
            print(f"  mask={m} weights={w} model={mo} real={r}")
        return 1

    print(f"G-AX OK: deep model == xr.dot(mask, weights.astype(int)) on "
          f"{len(cases)} inputs (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
