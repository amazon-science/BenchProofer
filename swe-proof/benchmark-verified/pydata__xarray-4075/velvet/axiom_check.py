#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4075.

Validates the ONE deep-model reference of this bundle (there are no consumed
axioms) against the REAL unchanged callee it models:

  (A-reference) `reduceDot` (Solution.lean pure region) == the unchanged shared
      reduction `xarray.core.computation.dot` (reached via `Weighted._reduce`),
      the carrier-polymorphic operation `_sum_of_weights` delegates to. Both
      legs are checked:

        reduceDot mask weights False = arithDot mask weights
            <=>  int(dot(mask_bool, weights_int, dims=...))      # numeric total
        reduceDot mask weights True  = anyMasked mask weights
            <=>  bool(dot(mask_bool, weights_bool, dims=...))    # truth-valued

      The contrast IS the bug: `dot` of two boolean arrays collapses the
      contraction to a single truth value (problem statement:
      `xr.dot([True, True], [True, True]) -> True`, not 2), so logical-carrier
      weights must be routed through the numeric leg to be summed.

Imports `numpy` + `xarray` — the same package the gold patch lives in (the repo
under test); plus stdlib. Exit 0 iff both legs are sound on every observation.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray.core.computation import dot


# --- Solution.lean pure-region reference encodings (kept in lock-step) -------

def arith_dot(mask, weights):
    """reduceDot _ _ False: arithmetic total of weights at present positions."""
    return sum(w if m else 0 for m, w in zip(mask, weights))


def any_masked(mask, weights):
    """reduceDot _ _ True: 1 iff any present position carries a nonzero weight."""
    return 1 if any(m and (w != 0) for m, w in zip(mask, weights)) else 0


# --- the real callee ---------------------------------------------------------

def real_reduce(mask, weights, logical):
    """The REAL shared reduction: dot(mask, weights, dims=...). When `logical`,
    weights are carried as a boolean array (the dtype that triggers the bug);
    otherwise as an integer array. `mask` is always boolean (it is da.notnull()).
    """
    da_mask = xr.DataArray(np.array(mask, dtype=bool))
    if logical:
        w = xr.DataArray(np.array([bool(v) for v in weights], dtype=bool))
    else:
        w = xr.DataArray(np.array(weights, dtype=int))
    return dot(da_mask, w, dims=...).values.item()


# --- the checks --------------------------------------------------------------

def check_arith_leg(mask, weights):
    observed = int(real_reduce(mask, weights, logical=False))
    expected = arith_dot(mask, weights)
    assert observed == expected, (
        "reduceDot arithmetic leg unsound on mask=%r weights=%r: "
        "real dot gave %r, deep model gives %r"
        % (mask, weights, observed, expected))


def check_logical_leg(mask, weights):
    # logical-carrier values are exactly {0,1}; model anyMasked returns 1/0,
    # real dot returns True/False. Compare at the int level (no double-mask).
    weights01 = [1 if v != 0 else 0 for v in weights]
    observed = int(real_reduce(mask, weights01, logical=True))
    expected = any_masked(mask, weights01)
    assert observed == expected, (
        "reduceDot logical leg unsound on mask=%r weights=%r: "
        "real dot gave %r, deep model gives %r"
        % (mask, weights01, observed, expected))


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        ([True, True], [1, 1]),            # the F2P sum_of_weights scenario
        ([True, True], [1, 0]),
        ([True, False], [1, 1]),
        ([False, True], [1, 1]),
        ([True, True, False], [1, 1, 1]),
        ([False, False], [0, 0]),
        ([True, True], [2, 3]),            # arithmetic-only magnitudes
        ([True], [1]),
        ([False], [1]),
        ([True, True, True, True], [5, 0, 3, 0]),
        ([True, False, True], [0, 7, 0]),
    ]
    for mask, weights in boundary:
        check_arith_leg(mask, weights)
        check_logical_leg(mask, weights)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(4075)
    for _ in range(20000):
        n = rng.randint(1, 12)
        mask = [rng.random() < 0.5 for _ in range(n)]
        # arithmetic leg: arbitrary integer weights (incl. negatives, zeros)
        weights = [rng.randint(-50, 50) for _ in range(n)]
        check_arith_leg(mask, weights)
        # logical leg: boolean-carrier weights (values restricted to {0,1})
        check_logical_leg(mask, weights)

    print("G-AX OK: reduceDot deep model (== real xr.dot, both legs) sound on "
          "%d boundary + 20000 fuzz (mask, weights) pairs." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
