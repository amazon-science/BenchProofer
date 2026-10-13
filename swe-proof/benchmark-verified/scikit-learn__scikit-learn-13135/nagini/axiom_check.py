#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13135.

Executes the REAL numeric callee the modeled computation invokes —
`numpy.ndarray.sort` (in-place ascending sort), the operation the gold patch
adds as `centers.sort()` — on boundary cases and randomized fuzz inputs, and
asserts that every observation satisfies the `order4` @ContractOnly axiom in
model.py.

The axiom (model.py axioms region), for four real centres each in `[lo, hi]`:

    order4(a, b, c, d, lo, hi) is a rearrangement of length four that
      * has length 4,
      * keeps every element within [lo, hi], and
      * is non-decreasing: Result()[k] <= Result()[k+1].

These are the WEAKEST clauses the proof consumes (it never needs which value
lands where, nor an exact value). The check verifies them on the real sort.

It also reproduces the discriminator the bundle turns on: on UNSORTED centres
the pre-patch interior midpoints `(centers[1:] + centers[:-1]) * 0.5` need NOT
be monotone (so the bracketed boundary list is out of order and the downstream
`np.digitize` would raise), while after `centers.sort()` the midpoints are
monotone and the boundary list is non-decreasing — exactly what the fix
restores.

Imports nothing repo-specific: only `numpy` (the module the patch calls) and the
standard-library `random`. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


def midpoints_bracketed(centers, col_min, col_max):
    """The bin-boundary list the kmeans branch builds from `centers`:
    np.r_[col_min, (centers[1:] + centers[:-1]) * 0.5, col_max]."""
    interior = (centers[1:] + centers[:-1]) * 0.5
    return np.r_[col_min, interior, col_max]


def is_non_decreasing(arr):
    return bool(np.all(np.diff(arr) >= 0.0))


def check_order4(values, lo, hi):
    """Assert the REAL numpy sort meets the three order4 Ensures clauses."""
    assert all(lo <= v <= hi for v in values), "inputs must lie in [lo, hi]"
    centers = np.array(values, dtype=np.float64)
    n = centers.shape[0]
    centers.sort()                                   # the REAL callee (in place)
    # (1) length-preservation
    assert centers.shape[0] == n, (
        "order4 axiom unsound: sort changed length %d -> %d"
        % (n, centers.shape[0]))
    # (2) bound-preservation: every element still in [lo, hi]
    for v in centers:
        assert lo <= v <= hi, (
            "order4 axiom unsound: sorted element %r left [%r, %r]"
            % (v, lo, hi))
    # (3) non-decreasing order
    assert is_non_decreasing(centers), (
        "order4 axiom unsound: sort did not yield non-decreasing order: %r"
        % (centers.tolist(),))


def main():
    # --- order4 boundary cases (each a 4-tuple of centres in [lo, hi]) -------
    lo, hi = 0.0, 10.0
    boundary = [
        [0.0, 0.0, 0.0, 0.0],            # all equal (degenerate)
        [0.0, 10.0, 0.0, 10.0],          # bounds, duplicated
        [1.0, 2.0, 3.0, 4.0],            # already sorted
        [4.0, 3.0, 2.0, 1.0],            # reverse sorted
        [2.0, 1.0, 4.0, 3.0],            # arbitrary permutation
        [5.0, 5.0, 5.0, 5.0],            # interior constant
        [0.0, 5.0, 5.0, 10.0],
        [10.0, 0.0, 5.0, 2.5],
        # centres reminiscent of the failing-test column [0, 0.5, 2, 3, 9, 10]
        [0.25, 9.5, 2.5, 6.0],
        [9.5, 0.25, 6.0, 2.5],
    ]
    for vals in boundary:
        check_order4(vals, lo, hi)

    # --- order4 randomized fuzz ----------------------------------------------
    rng = random.Random(13135)
    n_fuzz = 200000
    for _ in range(n_fuzz):
        a_lo = rng.uniform(-1e6, 1e6)
        width = rng.uniform(0.0, 1e6)
        b_hi = a_lo + width
        vals = [rng.uniform(a_lo, b_hi) for _ in range(4)]
        check_order4(vals, a_lo, b_hi)

    # --- the discriminator: unsorted centres -> non-monotone boundary list;
    #     sorting first -> monotone boundary list -------------------------------
    col_min, col_max = 0.0, 10.0
    # an UNSORTED set of centres for which the pre-patch boundaries are NOT
    # monotone (a high centre between two lower ones inflates an early midpoint)
    unsorted = np.array([1.0, 9.0, 2.0, 8.0], dtype=np.float64)
    pre = midpoints_bracketed(unsorted.copy(), col_min, col_max)
    assert not is_non_decreasing(pre), (
        "expected the pre-patch (unsorted) boundary list to be out of order, "
        "got monotone %r" % (pre.tolist(),))

    sorted_centers = unsorted.copy()
    sorted_centers.sort()                            # the REAL fix
    post = midpoints_bracketed(sorted_centers, col_min, col_max)
    assert is_non_decreasing(post), (
        "expected the post-fix (sorted) boundary list to be non-decreasing, "
        "got %r" % (post.tolist(),))

    # fuzz the discriminator: after sorting, the bracketed boundary list is
    # ALWAYS non-decreasing (this is the property the fix guarantees)
    for _ in range(50000):
        k = rng.randint(2, 8)
        a_lo = rng.uniform(-1e3, 1e3)
        b_hi = a_lo + rng.uniform(0.0, 1e3)
        centers = np.array([rng.uniform(a_lo, b_hi) for _ in range(k)],
                           dtype=np.float64)
        centers.sort()
        post = midpoints_bracketed(centers, a_lo, b_hi)
        assert is_non_decreasing(post), (
            "post-sort boundary list not monotone for centres %r in [%r,%r]: %r"
            % (centers.tolist(), a_lo, b_hi, post.tolist()))

    print("G-AX OK: order4 axiom sound on %d boundary + %d fuzz inputs "
          "(numpy.ndarray.sort: length-preserving, [lo,hi]-bounded, "
          "non-decreasing); discriminator confirmed (unsorted centres give a "
          "non-monotone boundary list, sorting first guarantees a monotone one "
          "over 50000 fuzz cases)."
          % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
