#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13135.

This bundle consumes NO axioms. Its single kind-A obligation is an
**A-reference**: the deep model `asc` (Solution.lean pure region) — the
ascending reordering of the cluster representatives — must equal the REAL
library reordering routine the modeled computation delegates to, namely
NumPy's in-place ascending sort `ndarray.sort()` (`centers.sort()` in the
patched code).

The check runs the REAL callee (`numpy.ndarray.sort`) on boundary inputs and
randomized fuzz, and asserts every observation matches the model:

  (A-reference) for any finite 1-D array `c`,
        list(c_after_real_sort)  ==  sorted(list(c))      # the `asc` model
        and the result is non-decreasing (the monotonicity the model encodes).

NumPy is the repository's mandatory dependency and is the exact module the gold
patch calls; importing it here is importing the real callee, not a re-model.
The model side (`sorted`) is Python's stdlib total order. For finite (non-NaN)
floats the two total orders coincide, so any disagreement is a real soundness
defect. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


def asc_model(values):
    """Reference implementation of Solution.lean's deep model `asc`: the
    ascending reordering (Python stdlib total order on finite reals)."""
    return sorted(values)


def check_sort_reference(values):
    """Assert the deep model asc(values) == the REAL numpy ndarray.sort()."""
    c = np.array(values, dtype=np.float64)
    c.sort()                                   # real callee: in-place asc sort
    observed = list(c)
    expected = asc_model(list(np.array(values, dtype=np.float64)))
    assert observed == expected, (
        "asc deep model unsound on %r: numpy .sort() gave %r, model gives %r"
        % (values, observed, expected))
    # monotonicity the model relies on downstream
    for k in range(len(observed) - 1):
        assert observed[k] <= observed[k + 1], (
            "numpy .sort() not non-decreasing on %r: %r" % (values, observed))


def main():
    # --- boundary cases ------------------------------------------------------
    boundary = [
        [],
        [0.0],
        [1.0, 2.0],
        [2.0, 1.0],                       # already reversed
        [3.0, 1.0, 2.0],
        [1.0, 1.0, 1.0],                  # all equal
        [2.0, 2.0, 1.0, 1.0],             # ties
        [-1.0, -3.0, 0.0, 5.0, -2.0],
        [1e-8, 1e8, -1e8, 0.0],
        [0.5, 0.5000001, 0.4999999],      # near-ties
        # the issue's reproducer: KMeans 1-D centers that come out unsorted
        [9.5, 0.25, 2.5, 6.0, 1.25],
    ]
    for vals in boundary:
        check_sort_reference(vals)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(13135)
    for _ in range(20000):
        n = rng.randint(0, 12)
        vals = [rng.uniform(-1e6, 1e6) for _ in range(n)]
        # occasionally inject ties / integral values to stress tie-ordering
        if n and rng.random() < 0.3:
            v = rng.choice(vals)
            vals[rng.randrange(n)] = v
        check_sort_reference(vals)

    print("G-AX OK: asc deep model (== numpy ndarray.sort) sound on %d boundary "
          "+ 20000 fuzz finite-float arrays; all results non-decreasing."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
