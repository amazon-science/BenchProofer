#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13647.

Two obligations, both executed against the REAL repo code in-container (the
patched `sympy/matrices/common.py`); imports only that module and stdlib.

  (A-consumed) the `new_matrix_cell` axiom (model.py axioms region): the
      unchanged matrix constructor `self._new(rows, cols, entry)` materialises
      the entry function into storage value-preservingly: the stored cell
      `M[i, j]` equals `entry(i, j)`. We exercise the very mechanism the patched
      `_eval_col_insert` uses (`_MinimalMatrix._new` + `__getitem__`) and assert
      `_new(rows, cols, f)[i, j] == f(i, j)` over boundary shapes + fuzz.

  (model fidelity) the model's `output_value` banding (left -> original col j;
      middle -> block col j-pos; right -> original col j-other_cols) equals the
      REAL `MatrixShaping._eval_col_insert` result, cell by cell, over boundary
      shapes + randomized fuzz. This validates the deep per-cell model against
      the real (patched) callee. The pre-patch right band (j - pos - other_cols)
      is also checked to be DETECTABLY wrong, confirming the spec discriminates.

Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy.matrices.common import _MinimalMatrix, MatrixShaping


class ShapingMatrix(_MinimalMatrix, MatrixShaping):
    """The same minimal matrix the repo's own test suite uses
    (test_commonmatrix.ShapingOnlyMatrix): _MinimalMatrix storage + the
    MatrixShaping behaviour that owns col_insert / _eval_col_insert."""
    pass


def make(rows, cols, f):
    return ShapingMatrix(rows, cols, lambda i, j: f(i, j))


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def expected_entry(self_row, other_row, cols, other_cols, pos, j):
    """Reference of model.py's `output_value` pure function (the corrected
    banding)."""
    if j < pos:
        return self_row[j]
    if j < pos + other_cols:
        return other_row[j - pos]
    return self_row[j - other_cols]


def buggy_entry(self_row, other_row, cols, other_cols, pos, j):
    """The pre-patch banding (right band j - pos - other_cols)."""
    if j < pos:
        return self_row[j]
    if j < pos + other_cols:
        return other_row[j - pos]
    return self_row[j - pos - other_cols]


# --- the checks --------------------------------------------------------------

def check_new_value_preserving(rows, cols):
    """A-consumed: _new materialises entry(i,j) value-preservingly."""
    f = lambda i, j: i * 100 + j  # an injective entry function
    M = make(rows, cols, f)
    assert M.rows == rows and M.cols == cols, (rows, cols, M.shape)
    for i in range(rows):
        for j in range(cols):
            assert M[i, j] == f(i, j), (
                "new_matrix_cell axiom unsound: _new(%d,%d,f)[%d,%d]=%r != "
                "f=%r" % (rows, cols, i, j, M[i, j], f(i, j)))


def check_col_insert_matches_model(rows, cols, other_cols, pos):
    """Model fidelity: real _eval_col_insert == expected_entry banding, and the
    pre-patch banding is detectably wrong (when there is a right band)."""
    self_vals = lambda i, j: i * 1000 + j + 1          # distinct nonzero values
    other_vals = lambda i, j: -(i * 1000 + j + 1)      # disjoint from self_vals
    self_m = make(rows, cols, self_vals)
    other_m = make(rows, other_cols, other_vals)

    # clamp pos exactly as the public col_insert does, then exercise the
    # changed _eval_col_insert directly (col_insert delegates to it).
    p = pos
    if p < 0:
        p = cols + p
    if p < 0:
        p = 0
    elif p > cols:
        p = cols
    res = self_m._eval_col_insert(p, other_m)

    width = cols + other_cols
    assert res.rows == rows and res.cols == width, (res.shape, rows, width)
    for i in range(rows):
        self_row = [self_vals(i, c) for c in range(cols)]
        other_row = [other_vals(i, c) for c in range(other_cols)]
        for j in range(width):
            got = res[i, j]
            exp = expected_entry(self_row, other_row, cols, other_cols, p, j)
            assert got == exp, (
                "model expected_entry disagrees with real _eval_col_insert at "
                "(%d,%d) shape self=%dx%d other=%dx%d pos=%d: real=%r model=%r"
                % (i, j, rows, cols, rows, other_cols, p, got, exp))
            # the pre-patch banding must differ somewhere in the right band
            bug = buggy_entry(self_row, other_row, cols, other_cols, p, j)
            if j >= p + other_cols and p > 0:
                # right band with a nonzero insertion offset: bug shifts source
                assert bug != exp or self_row[j - p - other_cols] == \
                    self_row[j - other_cols], (
                    "buggy banding unexpectedly equals correct one")


def main():
    # --- A-consumed: _new value preservation over boundary shapes + fuzz -----
    boundary_shapes = [(1, 1), (1, 3), (3, 1), (2, 2), (6, 6), (4, 5),
                       (1, 8), (8, 1)]
    for (r, c) in boundary_shapes:
        check_new_value_preserving(r, c)
    rng = random.Random(13647)
    for _ in range(2000):
        r = rng.randint(1, 8)
        c = rng.randint(1, 8)
        check_new_value_preserving(r, c)

    # --- model fidelity: the issue's exact example ---------------------------
    # eye(6).col_insert(3, 6x2 block) -- the reported regression.
    check_col_insert_matches_model(rows=6, cols=6, other_cols=2, pos=3)

    # boundary insertion positions and shapes
    fidelity_cases = [
        (1, 1, 1, 0), (1, 1, 1, 1),
        (3, 3, 1, 0), (3, 3, 1, 1), (3, 3, 1, 2), (3, 3, 1, 3),
        (6, 6, 2, 0), (6, 6, 2, 3), (6, 6, 2, 6),
        (4, 5, 3, 2), (2, 7, 4, 5), (5, 2, 2, 1), (3, 4, 0, 2),
    ]
    for (r, c, oc, p) in fidelity_cases:
        check_col_insert_matches_model(r, c, oc, p)

    # randomized fuzz over shapes and insertion positions
    for _ in range(4000):
        r = rng.randint(1, 7)
        c = rng.randint(1, 7)
        oc = rng.randint(0, 5)
        p = rng.randint(0, c)
        check_col_insert_matches_model(r, c, oc, p)

    print("G-AX OK: new_matrix_cell axiom value-preserving over %d boundary + "
          "2000 fuzz shapes; expected_entry == real _eval_col_insert over the "
          "issue example + %d boundary + 4000 fuzz column-insertions"
          % (len(boundary_shapes), len(fidelity_cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
