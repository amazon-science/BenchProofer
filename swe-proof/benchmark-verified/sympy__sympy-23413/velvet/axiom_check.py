#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-23413.

Validates the A-reference callees of Solution.lean against the REAL repository
code. Runs against the UNPATCHED (base_commit) source — the gate mounts the
bundle read-only and does NOT apply the gold patch — which is exactly right
here, because the two A-reference callees are UNCHANGED by the gold patch:

  (A-reference) `stepRow numCols A k i`
        == the per-row reduction the algorithm performs in place on the working
           dense representation: assign a pivot to a rightmost column at row
           `i`, clearing entries to its left and reducing entries to its right.
           This is the body of the `for i in ...` loop of `_hermite_normal_form`
           (`sympy/polys/matrices/normalforms.py`), spelled out below as
           `step_row` from the UNCHANGED helpers `add_columns` / `_gcdex`.
  (A-reference) `slice mat k`
        == `DomainMatrix.from_rep(mat)[:, k:]`, the final column selection that
           keeps the assigned pivot columns. UNCHANGED.

Neither the per-row reduction body nor the final slice is touched by the gold
patch (which only changes the OUTER row-iteration range and adds an early stop);
so the soundness of these A-references can be checked on the pre-patch source.

The check asserts:

  1. (decomposition fidelity / A-reference soundness) re-running the WHOLE
     pre-patch `_hermite_normal_form` as the composition

         reduce over rows `i = m-1, ..., m-min(m,n)` of `step_row`, then slice

     reproduces the real `_hermite_normal_form` EXACTLY on boundary + fuzz. This
     witnesses that `step_row` (the model's `stepRow`) and the slice (the
     model's `slice`) faithfully transliterate the unchanged callees: the only
     thing the gold patch changes is the row range / break that drives them,
     which is modeled CONCRETELY in Solution.lean's loop, not axiomatized.

  2. (pivot-count contract) `step_row` returns an updated unassigned-pivot count
     `k'` with `k-1 <= k' <= k` (drops by one when a pivot is placed, unchanged
     when the row is all-zero from the pivot column leftward) — the only
     structural fact Solution.lean's loop relies on about the callee's second
     return value.

  3. (purity / determinism) `step_row` and `slice` are deterministic pure
     functions of their inputs (recomputing on a fresh copy gives an equal
     result).

Imports only `sympy` (the package the patch lives in) + stdlib. Exit 0 iff
every obligation holds.
"""
import random
import sys

from sympy import ZZ
from sympy.polys.matrices import DomainMatrix
from sympy.polys.matrices.normalforms import (
    _hermite_normal_form, add_columns, _gcdex,
)


def step_row(n, A, k, i):
    """stepRow (Solution.lean), transliterated: the UNCHANGED per-row reduction
    body of `_hermite_normal_form`, operating in place on the dense rep `A`.
    Returns (A, k') with the updated unassigned-pivot count."""
    k -= 1
    for j in range(k - 1, -1, -1):
        if A[i][j] != 0:
            u, v, d = _gcdex(A[i][k], A[i][j])
            r, s = A[i][k] // d, A[i][j] // d
            add_columns(A, k, j, u, v, -s, r)
    b = A[i][k]
    if b < 0:
        add_columns(A, k, k, -1, 0, -1, 0)
        b = -b
    if b == 0:
        k += 1
    else:
        for j in range(k + 1, n):
            q = A[i][j] // b
            add_columns(A, j, k, 1, -q, 0, 1)
    return A, k


def select_slice(rep, k):
    """slice (Solution.lean), transliterated: the UNCHANGED final column
    selection keeping the assigned pivot columns."""
    return DomainMatrix.from_rep(rep)[:, k:]


def prepatch_decomposition(A):
    """The whole PRE-PATCH `_hermite_normal_form` rebuilt from the A-reference
    callees: reduce over the `min(m, n)` bottom rows, then slice."""
    m, n = A.shape
    rep = A.to_dense().rep.copy()
    rows = min(m, n)
    k = n
    last_k = k
    for i in range(m - 1, m - 1 - rows, -1):
        before = k
        rep, k = step_row(n, rep, k, i)
        # (2) pivot-count contract: k decreases by one or stays put.
        assert before - 1 <= k <= before, (
            "step_row pivot-count out of contract: k went %d -> %d" % (before, k))
        last_k = k
    return select_slice(rep, k), last_k


def dm(rows):
    m = len(rows)
    n = len(rows[0]) if m else 0
    return DomainMatrix([[ZZ(x) for x in r] for r in rows], (m, n), ZZ)


def check_one(rows):
    A = dm(rows)
    # (1) decomposition fidelity: model composition == real pre-patch callee.
    expected = _hermite_normal_form(A)
    observed, _ = prepatch_decomposition(A)
    assert observed == expected, (
        "stepRow/slice decomposition unsound on %r: real _hermite_normal_form "
        "gave %r, decomposition gives %r"
        % (rows, expected.to_Matrix(), observed.to_Matrix()))
    # (3) purity: recompute on a fresh copy, must match.
    observed2, _ = prepatch_decomposition(A)
    assert observed2 == observed, "decomposition non-deterministic on %r" % (rows,)


def main():
    # --- boundary cases ---------------------------------------------------
    boundary = [
        [[1]],
        [[0]],
        [[1, 12], [0, 8], [0, 5]],     # the issue's m > n case
        [[0, 12], [1, 8], [0, 5]],     # hint: pivot in row 2
        [[0, 12], [0, 8], [1, 5]],     # hint: pivot in row 3
        [[2, 7], [0, 0], [0, 0]],      # F2P: rank-deficient tall matrix
        [[5, 8, 12], [0, 0, 1]],       # the reporter's transposed matrix
        [[-2, 1], [0, 1]],
        [[12, 6, 4], [3, 9, 6], [2, 16, 14]],
        [[2, 7]],
        [[2], [7]],
        [[0, 0], [0, 0]],
        [[3, 3, 3], [3, 3, 3], [3, 3, 3]],
    ]
    for rows in boundary:
        check_one(rows)

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(23413)
    n_fuzz = 0
    for _ in range(6000):
        m = rng.randint(1, 5)
        n = rng.randint(1, 5)
        hi = rng.choice([1, 2, 4, 8, 25])
        rows = [[rng.randint(-hi, hi) for _ in range(n)] for _ in range(m)]
        check_one(rows)
        n_fuzz += 1

    print("G-AX OK: stepRow (== the unchanged per-row reduction body) and slice "
          "(== the unchanged DomainMatrix[:, k:]) faithfully recompose the real "
          "pre-patch _hermite_normal_form on %d boundary + %d fuzz matrices; "
          "step_row's pivot-count contract (k-1 <= k' <= k) holds throughout."
          % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
