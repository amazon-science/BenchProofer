#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-12907 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (numpy 2-D int arrays), via
              the mapping.md bijection (`List (List Int)` ↔ a 2-D ndarray of
              0/1 rows; `widenRight`/`widenLeft`/`++` ↔ zero-padding + row
              stacking). The impl region has NO A-tagged callee (the whole
              block-diagonal assembly is concrete list arithmetic), so the
              shadow is pure R/I and G-CONF carries real weight (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `astropy.modeling.separable._cstack` applied at base_commit, on
              the array/array branch (both operands are coord-matrix ndarrays,
              i.e. neither is a Model). This is the branch the gold patch fixes
              and the branch the FAIL_TO_PASS nested-compound tests exercise.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + numpy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np

SEED = 12907
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean widenRight/widenLeft/blockDiag ------------
def widen_right(rc, row):
    """widenRight (c : Char-free) : row ++ replicate rc 0."""
    return list(row) + [0] * rc


def widen_left(lc, row):
    """widenLeft : replicate lc 0 ++ row."""
    return [0] * lc + list(row)


def shadow_cstack(left, right):
    """blockDiag left right lc rc, transliterated to a numpy array.

    `left`/`right` are 2-D ndarrays; lc/rc are their column counts. Mirrors the
    impl region: upper = left rows widened right, lower = right rows widened
    left, concatenated rows-wise (List `++`)."""
    lc = left.shape[1]
    rc = right.shape[1]
    upper = [widen_right(rc, row) for row in left]
    lower = [widen_left(lc, row) for row in right]
    return np.array(upper + lower, dtype=float)


# --- the oracle: patch.diff's real _cstack, array/array branch ---------------
def oracle_cstack(left, right):
    """patch.diff's behaviour. We import the patched repo callee and drive its
    array/array branch by passing two ndarrays (neither is a Model), which is
    exactly the branch the gold hunk edits."""
    from astropy.modeling.separable import _cstack
    return np.asarray(_cstack(left, right), dtype=float)


def fuzz_inputs(n, rng):
    # boundary cases first: 1x1 blocks, single-row / single-col, all-zero,
    # all-one, identity-like, and the nested-compound shapes the F2P tests hit.
    boundary = [
        (np.array([[1]]), np.array([[1]])),
        (np.array([[1, 1], [1, 1]]), np.array([[1]])),            # rot & sh1
        (np.array([[1, 1], [1, 1]]), np.array([[1, 0], [0, 1]])),  # rot & (sh1&sh2)
        (np.array([[1, 0], [0, 1]]), np.array([[1, 0], [0, 1]])),
        (np.array([[0]]), np.array([[0]])),
        (np.array([[1, 0, 1]]), np.array([[0, 1]])),
        (np.array([[1], [0], [1]]), np.array([[1, 1]])),
    ]
    for L, R in boundary:
        yield L, R
    for _ in range(n):
        lr = rng.randint(1, 4)
        lc = rng.randint(1, 4)
        rr = rng.randint(1, 4)
        rc = rng.randint(1, 4)
        L = np.array([[rng.randint(0, 1) for _ in range(lc)] for _ in range(lr)])
        R = np.array([[rng.randint(0, 1) for _ in range(rc)] for _ in range(rr)])
        yield L, R


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for L, R in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_cstack(L, R)
        oracle = oracle_cstack(L, R)
        if shadow.shape != oracle.shape or not np.array_equal(shadow, oracle):
            disagreements.append((L.tolist(), R.tolist(),
                                  shadow.tolist(), oracle.tolist()))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for L, R, sh, orc in disagreements:
            print("  left=%r right=%r shadow=%r oracle=%r" % (L, R, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of combineParallel agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
