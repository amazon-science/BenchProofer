#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-3151.

The only library predicate the modeled ordering-validation loop relies on is the
pandas monotonicity test (`pandas.Index.is_monotonic_increasing` /
`is_monotonic_decreasing`, called at xarray/core/combine.py:506-507). It is
modeled DEEPLY in Solution.lean's `pure` region (`isMonoInc` / `isMonoDec`), not
behind a consumed axiom; this is an **A-reference**, and G-AX validates that deep
model against the real callee:

  isMonoInc(xs) == pandas.Index(xs).is_monotonic_increasing   (non-strict: a <= b)
  isMonoDec(xs) == pandas.Index(xs).is_monotonic_decreasing   (non-strict: a >= b)

over boundary cases (empty, singleton, sorted, reverse, with-repeats,
non-monotonic, and the issue's `['a','c','b']` rank ordering) plus randomized
fuzz. Imports only `pandas` — the same library the gold patch's loop calls.
Exit 0 iff every observation matches the deep model.
"""
import random
import sys

import pandas as pd


# --- Solution.lean deep-model reference encodings (in lock-step with `pure`) --

def iso_mono_inc(xs):
    """isMonoInc: each element <= its successor (non-strict). [] and [_] true."""
    return all(xs[k] <= xs[k + 1] for k in range(len(xs) - 1))


def iso_mono_dec(xs):
    """isMonoDec: each element >= its successor (non-strict). [] and [_] true."""
    return all(xs[k] >= xs[k + 1] for k in range(len(xs) - 1))


# --- the A-reference checks --------------------------------------------------

def check_monotonic_reference(xs):
    """Assert the deep model matches REAL pandas monotonicity on Index(xs)."""
    idx = pd.Index(xs)
    real_inc = bool(idx.is_monotonic_increasing)
    real_dec = bool(idx.is_monotonic_decreasing)
    model_inc = iso_mono_inc(xs)
    model_dec = iso_mono_dec(xs)
    assert model_inc == real_inc, (
        "isMonoInc deep model unsound on %r: pandas=%r model=%r"
        % (xs, real_inc, model_inc))
    assert model_dec == real_dec, (
        "isMonoDec deep model unsound on %r: pandas=%r model=%r"
        % (xs, real_dec, model_dec))


def main():
    boundary = [
        [],                       # empty index -> both monotonic
        [0],                      # singleton -> both monotonic
        [0, 1, 2, 3],             # strictly increasing
        [3, 2, 1, 0],             # strictly decreasing
        [0, 0, 1, 1, 2],          # non-strict increasing (repeats)
        [2, 1, 1, 0, 0],          # non-strict decreasing (repeats)
        [1, 1, 1],                # constant -> both monotonic
        [0, 2, 1],                # the issue's ['a','c','b'] rank order -> neither
        [1, 0, 2],                # neither monotonic
        [5, 5, 4, 6],             # neither
        [-3, -1, 0, 4],           # negatives, increasing
        [10, 0],                  # pair decreasing
        [0, 10],                  # pair increasing
    ]
    for xs in boundary:
        check_monotonic_reference(xs)

    # randomized fuzz: small integer ranks (allowing repeats and ties)
    rng = random.Random(3151)
    for _ in range(20000):
        n = rng.randint(0, 8)
        xs = [rng.randint(0, 5) for _ in range(n)]
        check_monotonic_reference(xs)

    print("G-AX OK: isMonoInc/isMonoDec deep model (== pandas.Index "
          "monotonicity) sound on %d boundary + 20000 fuzz indexes"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
