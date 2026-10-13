#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-23413.

This bundle has NO @ContractOnly axiom over an opaque library callee: the
changed behaviour (the per-row pivot search that fixes the column-marker `k`)
is modelled DEEPLY by `model.py`'s pure `pivot_count` helper and the verified
`leftmost_pivot_column` loop. G-AX therefore validates that DEEP MODEL
(an A-reference) against the REAL routine it abstracts.

The model's claim, factored out of the matrix arithmetic, is the closed-form
law for the final column marker:

    leftmost_pivot_column(found, n) == max(0, n - sum(found))

where `found[i] in {0,1}` records whether the i-th row from the bottom yields a
nonzero pivot, and `n` is the column count. The retained-column count is
`n - k`. The fixed routine examines EVERY row (the buggy one examined only the
bottom `min(m, n)` rows); the law above counts pivots over all rows.

We confirm this law in two independent ways:

  (1) Against a faithful, stdlib-only re-implementation of the fixed routine
      `_hermite_normal_form` (Cohen, Alg. 2.4.5) operating on plain-int
      matrices: we run it, record the actual per-row pivot outcomes and the
      actual final `k`, and assert both the law and that the model `k` equals
      the routine's `k` and retained-column count.

  (2) Against the REAL sympy routine when importable in this environment
      (it is, in the official eval container): we run
      `sympy.polys.matrices.normalforms._hermite_normal_form` on the same
      matrices and assert the model `k` equals `n - (real result column count)`.

Imports are stdlib-only by default; the real-sympy cross-check is attempted in
a guarded import so the file also runs in a bare environment. Exit 0 iff every
observation matches the model. Inputs include the issue's boundary matrices,
the F2P test matrices, tall/wide/zero/rank-deficient shapes, and 60k fuzz.
"""
import random
import sys


# --- model.py reference law (kept in lock-step with model.py) ----------------

def model_leftmost_pivot_column(found, n):
    """Reference of model.py's leftmost_pivot_column, computed by the same
    bottom-to-top loop (decrement on a pivot, break when the marker hits 0)."""
    k = n
    for f in found:
        if k == 0:
            break
        if f:
            k -= 1
    return k


def model_closed_form(found, n):
    return max(0, n - sum(1 for f in found if f))


# --- faithful stdlib-only re-implementation of the FIXED routine -------------

def _gcdex(a, b):
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    x, y, g = old_s, old_t, old_r
    # mirror sympy's _gcdex adjustment: y == 0 when a | b
    if a != 0 and b % a == 0:
        y = 0
        x = -1 if a < 0 else 1
    return x, y, g


def _add_columns(M, i, j, a, b, c, d):
    for k in range(len(M)):
        e = M[k][i]
        M[k][i] = a * e + b * M[k][j]
        M[k][j] = c * e + d * M[k][j]


def hnf_fixed_trace(A):
    """The FIXED _hermite_normal_form (Cohen 2.4.5) on a plain-int matrix.
    Returns (final_k, n, found) where found[t] (t=0 is the bottom row) is 1 iff
    that row contributed a nonzero pivot. Mirrors sympy's post-patch loop:
    iterate every row, break when k == 0."""
    m = len(A)
    n = len(A[0]) if m else 0
    A = [row[:] for row in A]
    k = n
    found = []
    for i in range(m - 1, -1, -1):
        if k == 0:
            # remaining (top) rows are not examined; they contribute no pivot
            found.append(0)
            continue
        k -= 1
        for j in range(k - 1, -1, -1):
            if A[i][j] != 0:
                u, v, d = _gcdex(A[i][k], A[i][j])
                r, s = A[i][k] // d, A[i][j] // d
                _add_columns(A, k, j, u, v, -s, r)
        b = A[i][k]
        if b < 0:
            _add_columns(A, k, k, -1, 0, -1, 0)
            b = -b
        if b == 0:
            k += 1
            found.append(0)
        else:
            for j in range(k + 1, n):
                q = A[i][j] // b
                _add_columns(A, j, k, 1, -q, 0, 1)
            found.append(1)
    # found is in bottom-to-top order already (i runs m-1 .. 0)
    return k, n, found


# --- checks ------------------------------------------------------------------

def check_matrix(A):
    real_k, n, found = hnf_fixed_trace(A)
    # the model's loop law and closed form agree with each other
    assert model_leftmost_pivot_column(found, n) == model_closed_form(found, n), \
        ("model loop != model closed form on found=%r n=%d" % (found, n))
    # and both reproduce the routine's actual final marker k
    mk = model_leftmost_pivot_column(found, n)
    assert mk == real_k, (
        "deep model unsound on A=%r: model k=%d, routine k=%d (found=%r, n=%d)"
        % (A, mk, real_k, found, n))
    # retained-column count is n - k (the columns A[:, k:])
    assert (n - mk) == (n - real_k) and 0 <= mk <= n
    return real_k, n, found


def check_against_real_sympy(matrices):
    """Optional cross-check: the REAL sympy routine, if importable."""
    try:
        from sympy.polys.matrices import DomainMatrix
        from sympy.polys.domains import ZZ
        from sympy.polys.matrices.normalforms import _hermite_normal_form
    except Exception as exc:  # pragma: no cover - bare env
        print("G-AX: real-sympy cross-check skipped (%s)" % type(exc).__name__)
        return 0
    n_checked = 0
    for A in matrices:
        m = len(A)
        n = len(A[0]) if m else 0
        if m == 0 or n == 0:
            continue
        dm = DomainMatrix([[ZZ(x) for x in row] for row in A], (m, n), ZZ)
        H = _hermite_normal_form(dm)
        real_cols = H.shape[1]
        # model k == n - retained columns
        _, _, found = hnf_fixed_trace(A)
        mk = model_leftmost_pivot_column(found, n)
        assert (n - mk) == real_cols, (
            "model retained-cols %d != real sympy %d on A=%r"
            % (n - mk, real_cols, A))
        n_checked += 1
    print("G-AX: real-sympy cross-check passed on %d matrices" % n_checked)
    return n_checked


def main():
    boundary = [
        [[1, 12], [0, 8], [0, 5]],     # the reported issue (pivot in top row)
        [[0, 12], [1, 8], [0, 5]],     # hints: pivot in middle row
        [[0, 12], [0, 8], [1, 5]],     # hints: pivot in bottom row
        [[2, 7], [0, 0], [0, 0]],      # F2P: tall, single pivot in top row -> 1 col
        [[2, 7, 17, 29, 41], [3, 11, 19, 31, 43], [5, 13, 23, 37, 47]],  # wide
        [[-2, 1], [0, 1]],             # negative pivot
        [[5, 8, 12], [0, 0, 1]],       # issue source matrix (wide, 2x3)
        [[1]],                         # 1x1
        [[0]],                         # zero 1x1
        [[1, 0], [0, 1], [0, 0]],      # identity-ish tall
        [[0, 0], [0, 0], [0, 0]],      # all zero tall
        [[1], [0], [0]],               # tall single column
        [[1, 2, 3]],                   # single wide row
        [[1], [1], [1]],               # tall, every row a pivot (k hits 0 early)
    ]
    for A in boundary:
        check_matrix(A)

    # randomized fuzz over small integer matrices of varied shapes
    rng = random.Random(23413)
    for _ in range(60000):
        m = rng.randint(1, 6)
        n = rng.randint(1, 6)
        A = [[rng.randint(-4, 4) for _ in range(n)] for _ in range(m)]
        check_matrix(A)

    n_real = check_against_real_sympy(boundary)

    print("G-AX OK: deep model leftmost_pivot_column == fixed _hermite_normal_form "
          "marker on %d boundary + 60000 fuzz matrices; real-sympy cross-check on "
          "%d" % (len(boundary), n_real))
    return 0


if __name__ == "__main__":
    sys.exit(main())
