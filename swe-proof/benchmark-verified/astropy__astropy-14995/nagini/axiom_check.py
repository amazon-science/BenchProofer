#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14995.

Executes the REAL element-wise combiner callable that the changed decision
*invokes* in case (4) — ``numpy.bitwise_or``, the ``handle_mask`` argument the
issue and the FAIL_TO_PASS test use — on boundary + randomized inputs and
asserts that every observation matches the axioms in model.py.

The two kind-A obligations (the combiner is the UNCHANGED callee the patched
decision calls; it is axiomatized, not modelled deeply):

  (combine_masks, A-consumed)  the abstract combiner is shape-preserving: for
      two equal-length 1-D flag arrays, the combination has the same length.
      model.py: Ensures(Implies(len(a)==len(b), len(Result())==len(a))).

  (apply_combiner, A-consumed)  the materializing call returns exactly the
      element-wise combination, i.e. the real ``np.bitwise_or`` output. We model
      its value as the opaque ``combine_masks``; here we additionally confirm the
      real callee is a deterministic pure function of the two inputs (so the
      opaque modelling is sound) and is shape-preserving — the only property the
      proof consumes.

The decision under specification (cases 1-3, the actual bug) never calls the
combiner, so its correctness does not rely on the combiner's value semantics —
only on the shape-preservation contract checked here.

Imports nothing repo-specific: ``numpy`` is the dependency the gold patch's
``handle_mask=np.bitwise_or`` call uses. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


def check_shape_preserving(a, b):
    """combine_masks / apply_combiner: equal-length inputs -> same-length out."""
    arr_a = np.array(a, dtype=np.int64)
    arr_b = np.array(b, dtype=np.int64)
    out = np.bitwise_or(arr_a, arr_b)          # the real combiner (handle_mask)
    assert out.shape == arr_a.shape, (
        "combiner not shape-preserving on %r,%r: out shape %r vs in %r"
        % (a, b, out.shape, arr_a.shape))
    assert len(out.tolist()) == len(a), (
        "combiner length axiom unsound on %r,%r: |out|=%d, |a|=%d"
        % (a, b, len(out.tolist()), len(a)))


def check_deterministic_pure(a, b):
    """apply_combiner modelled as opaque combine_masks(a,b): confirm the real
    callee is a deterministic function of (a,b) alone."""
    arr_a = np.array(a, dtype=np.int64)
    arr_b = np.array(b, dtype=np.int64)
    o1 = np.bitwise_or(arr_a, arr_b).tolist()
    o2 = np.bitwise_or(arr_a, arr_b).tolist()
    assert o1 == o2, "combiner not deterministic on %r,%r" % (a, b)
    # commutative degenerate check on the no-op cases the issue exercises:
    # combining a mask with an all-zero array of the same shape returns the mask
    zeros = [0] * len(a)
    assert np.bitwise_or(arr_a, np.array(zeros, dtype=np.int64)).tolist() == a, (
        "bitwise_or with zeros changed the mask on %r" % (a,))


def main():
    # --- boundary cases over the flag/bitmask domain ----------------------
    boundary = [
        ([], []),
        ([0], [0]),
        ([1], [0]),
        ([0], [1]),
        ([64], [64]),
        ([0, 1, 64], [64, 1, 0]),          # F2P bitmask rows
        ([8, 0, 1], [2, 1, 0]),
        ([2, 1, 0], [8, 0, 2]),
        ([0, 1, 0, 1, 0, 1, 0, 1, 0], [0, 1, 64, 8, 0, 1, 2, 1, 0]),  # flattened
        ([255, 128, 7], [1, 2, 248]),
        ([0, 0, 0], [0, 0, 0]),
    ]
    for a, b in boundary:
        check_shape_preserving(a, b)
        if a:
            check_deterministic_pure(a, b)

    # --- randomized fuzz over bitmask values ------------------------------
    rng = random.Random(14995)
    for _ in range(20000):
        n = rng.randint(0, 16)
        a = [rng.randint(0, 255) for _ in range(n)]
        b = [rng.randint(0, 255) for _ in range(n)]
        check_shape_preserving(a, b)
        if a:
            check_deterministic_pure(a, b)

    print("G-AX OK: combine_masks/apply_combiner axioms (shape-preserving, "
          "deterministic) sound against real numpy.bitwise_or on %d boundary "
          "+ 20000 fuzz input pairs" % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
