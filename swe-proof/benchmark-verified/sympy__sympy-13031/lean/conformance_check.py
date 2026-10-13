#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-13031.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean skeletons
`implementation_hJoin` (= SparseMatrix.row_join, horizontal join `[A B]`) and
`implementation_vJoin` (= SparseMatrix.col_join, vertical join `[A;B]`) and diffs
them against the REAL patched primitives over a boundary catalogue plus >=1e5
randomized draws. End-to-end `hstack`/`vstack` (= reduce over the binary join)
are also checked against the folded shadow, covering the exact issue shapes.

The Lean `Mat` carrier has a `kind` component (the concrete matrix class);
both specs pin `result.kind = self.kind` — i.e. the join always returns a
matrix of the receiver's class, NEVER `other` itself (the hidden test asserts
`type(a.row_join(b)) == type(a)` with a sparse receiver and a dense argument).
The differential therefore also checks `type(real_result) is type(self)`,
including mixed sparse-receiver/dense-argument draws.

Inputs are restricted to the proof's precondition (the no-`ShapeError` domain):
  hJoin: self.cols == 0  OR  self.rows == other.rows
  vJoin: self.rows == 0  OR  self.cols == other.cols

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 13031
N_RANDOM = 60_000  # per binary primitive -> >= 1e5 total


# ---- Python shadows (transliterations of the Lean impls / specs) ----
# A shadow matrix is (rows, cols, get, kind); kind is the receiver's concrete
# Python class (the Lean Nat kind tag under the recorded bijection).

def shadow_hjoin(s_rows, s_cols, s_get, s_kind, o_rows, o_cols, o_get, o_kind):
    """Shadow of implementation_hJoin. Returns (rows, cols, get, kind)."""
    if s_cols == 0 and s_rows != o_rows:
        # concatCols (zeroColsMat o_rows s_kind) other == other's shape/entries,
        # self's kind
        return o_rows, o_cols, (lambda i, j: o_get(i, j)), s_kind
    # concatCols self other (kind = self's)
    return (s_rows, s_cols + o_cols,
            (lambda i, j: s_get(i, j) if j < s_cols else o_get(i, j - s_cols)),
            s_kind)


def shadow_vjoin(s_rows, s_cols, s_get, s_kind, o_rows, o_cols, o_get, o_kind):
    """Shadow of implementation_vJoin. Returns (rows, cols, get, kind)."""
    if s_rows == 0 and s_cols != o_cols:
        # concatRows (zeroRowsMat o_cols s_kind) other
        return o_rows, o_cols, (lambda i, j: o_get(i, j)), s_kind
    # concatRows self other
    return (s_rows + o_rows, s_cols,
            (lambda i, j: s_get(i, j) if i < s_rows else o_get(i - s_rows, j)),
            s_kind)


def make_get(data):
    return lambda i, j: data[i][j]


def main():
    from sympy import SparseMatrix, Matrix

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def smat(rows, cols, data):
        return SparseMatrix(rows, cols, lambda i, j: data[i][j])

    def dmat(rows, cols, data):
        return Matrix(rows, cols, lambda i, j: data[i][j])

    def cmp_mat(real, exp_rows, exp_cols, exp_get, exp_kind, tag):
        nonlocal disagreements, checked
        if type(real) is not exp_kind:
            disagreements += 1
            if disagreements <= 8:
                print(f"KIND MISMATCH [{tag}] got={type(real).__name__} "
                      f"exp={exp_kind.__name__}")
            return
        checked += 1  # the kind check itself
        if real.rows != exp_rows or real.cols != exp_cols:
            disagreements += 1
            if disagreements <= 8:
                print(f"SHAPE MISMATCH [{tag}] got=({real.rows},{real.cols}) "
                      f"exp=({exp_rows},{exp_cols})")
            return
        for i in range(exp_rows):
            for j in range(exp_cols):
                got = int(real[i, j])
                ex = int(exp_get(i, j))
                checked += 1
                if got != ex:
                    disagreements += 1
                    if disagreements <= 8:
                        print(f"MISMATCH [{tag}] i={i} j={j}: real={got} shadow={ex}")

    def gen_data(rows, cols, lo, hi):
        return [[rng.randint(lo, hi) for _ in range(cols)] for _ in range(rows)]

    # ----- hJoin (row_join) -----
    for k in range(N_RANDOM):
        small = (k % 3 == 0)
        hi = 3 if small else 9
        o_rows = rng.randint(0, 4)
        o_cols = rng.randint(0, 4)
        if rng.random() < 0.5:
            # self.cols == 0 branch (rows free, exercises the null-stack fix)
            s_rows = rng.randint(0, 4)
            s_cols = 0
        else:
            # self.rows == other.rows branch (cols free)
            s_rows = o_rows
            s_cols = rng.randint(0, 4)
        s_data = gen_data(s_rows, s_cols, -hi, hi)
        o_data = gen_data(o_rows, o_cols, -hi, hi)
        # every 4th draw uses a DENSE `other` (receiver stays sparse) so the
        # kind observable is exercised across classes, as the hidden test does
        dense_other = (k % 4 == 0)
        o_real = (dmat if dense_other else smat)(o_rows, o_cols, o_data)
        o_kind = type(o_real)
        s_real = smat(s_rows, s_cols, s_data)
        real = s_real.row_join(o_real)
        er, ec, eg, ek = shadow_hjoin(s_rows, s_cols, make_get(s_data), SparseMatrix,
                                      o_rows, o_cols, make_get(o_data), o_kind)
        cmp_mat(real, er, ec, eg, ek, "hJoin")

    # ----- vJoin (col_join) -----
    for k in range(N_RANDOM):
        small = (k % 3 == 0)
        hi = 3 if small else 9
        o_rows = rng.randint(0, 4)
        o_cols = rng.randint(0, 4)
        if rng.random() < 0.5:
            s_rows = 0
            s_cols = rng.randint(0, 4)
        else:
            s_cols = o_cols
            s_rows = rng.randint(0, 4)
        s_data = gen_data(s_rows, s_cols, -hi, hi)
        o_data = gen_data(o_rows, o_cols, -hi, hi)
        dense_other = (k % 4 == 0)
        o_real = (dmat if dense_other else smat)(o_rows, o_cols, o_data)
        o_kind = type(o_real)
        real = smat(s_rows, s_cols, s_data).col_join(o_real)
        er, ec, eg, ek = shadow_vjoin(s_rows, s_cols, make_get(s_data), SparseMatrix,
                                      o_rows, o_cols, make_get(o_data), o_kind)
        cmp_mat(real, er, ec, eg, ek, "vJoin")

    # ----- the hidden test's exact kind scenario: sparse receiver, dense arg --
    a = SparseMatrix(0, 0, {})
    b = Matrix([[1], [2]])
    cmp_mat(a.row_join(b), 2, 1, (lambda i, j: [[1], [2]][i][j]),
            SparseMatrix, "kind-hidden-rj")
    b2 = Matrix([[1, 2]])
    cmp_mat(a.col_join(b2), 1, 2, (lambda i, j: [[1, 2]][i][j]),
            SparseMatrix, "kind-hidden-cj")

    # ----- end-to-end hstack/vstack vs folded shadow (the issue scenario) -----
    # hstack == reduce(row_join); the exact issue: zeros(0,n) for n in 0..3.
    def fold_h(mats):
        rows, cols, get, kind = mats[0]
        for (r2, c2, g2, k2) in mats[1:]:
            rows, cols, get, kind = shadow_hjoin(rows, cols, get, kind,
                                                 r2, c2, g2, k2)
        return rows, cols, get, kind

    def fold_v(mats):
        rows, cols, get, kind = mats[0]
        for (r2, c2, g2, k2) in mats[1:]:
            rows, cols, get, kind = shadow_vjoin(rows, cols, get, kind,
                                                 r2, c2, g2, k2)
        return rows, cols, get, kind

    # the literal issue case + randomized variadic stacks
    issue_h = [(0, n, make_get([]), SparseMatrix) for n in range(4)]
    real = SparseMatrix.hstack(*[SparseMatrix.zeros(0, n) for n in range(4)])
    er, ec, eg, ek = fold_h(issue_h)
    cmp_mat(real, er, ec, eg, ek, "hstack-issue")

    issue_v = [(n, 0, make_get([[] for _ in range(n)]), SparseMatrix)
               for n in range(4)]
    real = SparseMatrix.vstack(*[SparseMatrix.zeros(n, 0) for n in range(4)])
    er, ec, eg, ek = fold_v(issue_v)
    cmp_mat(real, er, ec, eg, ek, "vstack-issue")

    for _ in range(4000):
        # random hstack: all share a common row count r (so every join is legal)
        r = rng.randint(0, 3)
        parts = []
        real_parts = []
        for _ in range(rng.randint(2, 4)):
            c = rng.randint(0, 3)
            d = gen_data(r, c, -4, 4)
            parts.append((r, c, make_get(d), SparseMatrix))
            real_parts.append(smat(r, c, d))
        real = SparseMatrix.hstack(*real_parts)
        er, ec, eg, ek = fold_h(parts)
        cmp_mat(real, er, ec, eg, ek, "hstack-rand")

        c = rng.randint(0, 3)
        parts = []
        real_parts = []
        for _ in range(rng.randint(2, 4)):
            r = rng.randint(0, 3)
            d = gen_data(r, c, -4, 4)
            parts.append((r, c, make_get(d), SparseMatrix))
            real_parts.append(smat(r, c, d))
        real = SparseMatrix.vstack(*real_parts)
        er, ec, eg, ek = fold_v(parts)
        cmp_mat(real, er, ec, eg, ek, "vstack-rand")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
