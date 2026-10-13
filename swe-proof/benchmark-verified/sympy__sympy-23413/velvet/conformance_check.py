#!/usr/bin/env python3
"""G-CONF cross-language differential test for sympy__sympy-23413 (plan §4.1).

The gate runs this inside the instance image with the GOLD PATCH APPLIED
(`apply_gold=True`), so `sympy.polys.matrices.normalforms._hermite_normal_form`
is the PATCHED (correct) function — the behavioural oracle.

We build the R/I shadow of `Solution.lean`'s `hermiteNormalForm` impl region in
Python and differential-test it against that oracle on >= 1e5 fuzzed inputs:

  * R/I ops (the loop STRUCTURE the spec pins) transliterated to Python:
      - iterate rows from the bottom (`rowsLeft = numRows` downward), processing
        row index `rowsLeft - 1` each step;
      - continue while `rowsLeft > 0 AND k > 0` (the early stop once every column
        has received a pivot);
      - thread the matrix and the unassigned-pivot count `k` through the steps;
      - finally `slice mat k`.
    This is exactly the control/data flow of `hermiteNormalForm`'s `do` block.

  * A-reference callees, left as the REAL repo callees (NOT re-modeled): the
    per-row reduction `step_row` is built from the UNCHANGED helpers
    `add_columns` / `_gcdex` (the body of the patched `_hermite_normal_form`'s
    inner loop, unchanged by the patch), and the final `slice` is the UNCHANGED
    `DomainMatrix.from_rep(mat)[:, k:]`. G-CONF isolates the R/I loop structure;
    the per-row body soundness is G-AX's job (axiom_check.py).

So the shadow is the structural loop driving the real per-row reduction; the
oracle is the patched `_hermite_normal_form`. They must agree (as DomainMatrix
over ZZ) on every input. Exit 0 iff zero disagreements.

Inputs are fuzzed over random integer matrices of varied shapes and magnitudes
(including m > n, the bug's regime), with `random.Random(23413)`. Exit 0 iff
zero disagreements.
"""
import random
import sys

from sympy import ZZ
from sympy.polys.matrices import DomainMatrix
from sympy.polys.matrices.normalforms import (
    _hermite_normal_form, add_columns, _gcdex,
)

SEED = 23413
N_TARGET = 100000


def step_row(n, A, k, i):
    """The A-reference per-row reduction, left as the REAL unchanged repo body
    (add_columns / _gcdex). Returns (A, k')."""
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


def shadow(A):
    """R/I shadow of hermiteNormalForm's `do` block: process rows from the
    bottom up while at least one column still awaits a pivot, threading the
    matrix and the count k; then keep the pivot columns. The per-row reduction
    and the slice are the REAL (A-reference) callees."""
    m, n = A.shape
    rep = A.to_dense().rep.copy()
    k = n
    rows_left = m
    while rows_left > 0 and k > 0:
        rep, k = step_row(n, rep, k, rows_left - 1)
        rows_left -= 1
    return DomainMatrix.from_rep(rep)[:, k:]


def dm(rows, m, n):
    return DomainMatrix([[ZZ(x) for x in r] for r in rows], (m, n), ZZ)


def main():
    rng = random.Random(SEED)

    # deterministic boundary cases first (the issue + F2P tests)
    boundary = [
        ([[1, 12], [0, 8], [0, 5]], 3, 2),
        ([[2, 7], [0, 0], [0, 0]], 3, 2),
        ([[5, 8, 12], [0, 0, 1]], 2, 3),
        ([[0, 12], [1, 8], [0, 5]], 3, 2),
        ([[0, 12], [0, 8], [1, 5]], 3, 2),
        ([[-2, 1], [0, 1]], 2, 2),
        ([[12, 6, 4], [3, 9, 6], [2, 16, 14]], 3, 3),
    ]

    n = 0
    n_disagree = 0
    examples = []

    def run(rows, m, nn):
        nonlocal n, n_disagree
        A = dm(rows, m, nn)
        oracle = _hermite_normal_form(A)    # patched (correct) function
        sh = shadow(A)
        if oracle != sh:
            n_disagree += 1
            if len(examples) < 5:
                examples.append((repr(rows), repr(oracle.to_Matrix()),
                                 repr(sh.to_Matrix())))
        n += 1

    for rows, m, nn in boundary:
        run(rows, m, nn)

    while n < N_TARGET:
        m = rng.randint(1, 6)
        nn = rng.randint(1, 6)
        hi = rng.choice([1, 2, 3, 5, 9, 30, 200])
        rows = [[rng.randint(-hi, hi) for _ in range(nn)] for _ in range(m)]
        run(rows, m, nn)

    if n_disagree:
        print("G-CONF FAIL: %d/%d disagreements between the R/I shadow and the "
              "patched _hermite_normal_form (seed=%d)." % (n_disagree, n, SEED))
        for ex in examples:
            print("  rows=%s | oracle=%s | shadow=%s" % ex)
        return 1

    print("G-CONF OK: R/I shadow of hermiteNormalForm (process all rows bottom-up "
          "with the k>0 early stop, per-row reduction and slice left as the real "
          "callees) agrees with the patched _hermite_normal_form on %d inputs "
          "(seed=%d), 0 disagreements." % (n, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
