#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13647 (nagini).

SHADOW: the impl region of model.py `insert_row`, copied verbatim below with
the contract calls (Requires/Ensures/Invariant/Assert) stripped, plus the
@Pure helper `output_value` copied over as a plain function (it is only used
inside contracts, so stripping the contracts removes its call sites; it is
kept for completeness of the impl-region copy). The carrier is plain
`List[int]` rows — no PSeq shim needed. The single @ContractOnly callee
`new_matrix_cell` calls the REAL repo mechanism it models (mapping.md §3.1):
`_MinimalMatrix._new` materialising a per-position value function into
storage, read back via `__getitem__` — exercised here at the single-cell
granularity the model uses.

ORACLE: the REAL patched repo function the model models per mapping.md —
`MatrixShaping._eval_col_insert` (sympy/matrices/common.py), run on the same
minimal matrix the repo's own test suite uses (`_MinimalMatrix` +
`MatrixShaping`). The gate applies patch.diff to /testbed before this script
runs; PYTHONPATH=/testbed makes the patched code importable.

Type bridge (mapping.md §2): the model abstracts one matrix row as a
`List[int]` (the per-cell behaviour is row-independent), so each check builds
a real matrix whose row `i` holds exactly the shadow's `self_row` /
`other_row` values, runs the real `_eval_col_insert(pos, other)`, extracts
row `i` of the result as a list of ints, and compares it `==` against the
shadow's output list. Most cases use a 1-row matrix (the abstraction's
granularity); a slice of the boundary/fuzz cases uses multi-row matrices and
checks every row, exercising the row-independence bridge itself.

Input domain (the model's Requires): cols >= 0, other_cols >= 0,
0 <= pos <= cols, len(self_row) == cols, len(other_row) == other_cols.
Entry values are arbitrary ints (negative / zero / large included). Boundary
cases cover empty rows on either side, pos at 0 / cols / interior, width-1
rows, and the shapes from the public issue report; fuzz draws shapes up to
9 columns per side with pos uniform over [0, cols].

>= 1e5 Requires-satisfying inputs: 34 boundary + 100000 fuzz cases.
Pinned fuzz seed: 13647.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

from sympy.matrices.common import _MinimalMatrix, MatrixShaping

SEED = 13647
N_FUZZ = 100_000


class ShapingMatrix(_MinimalMatrix, MatrixShaping):
    """Same minimal composition the repo test suite uses: _MinimalMatrix
    storage + the MatrixShaping behaviour that owns _eval_col_insert."""
    pass


# --- @ContractOnly callee -> the REAL repo function it models -----------------
# mapping.md §3.1: new_matrix_cell models _new materialising a per-position
# value into storage, read back through __getitem__, at single-cell
# granularity.

def new_matrix_cell(value):
    m = ShapingMatrix(1, 1, lambda i, j: value)
    return m[0, 0]


# --- pure helper from model.py, decorator + contracts stripped ----------------

def output_value(self_row, other_row, cols, other_cols, pos, j):
    if j < pos:
        return self_row[j]
    if j < pos + other_cols:
        return other_row[j - pos]
    return self_row[j - other_cols]


# --- the impl region of model.py, verbatim (contract calls stripped) ----------

def insert_row(self_row, other_row, cols, other_cols, pos):
    width = cols + other_cols
    result = []  # type: list
    j = 0
    while j < width:
        if j < pos:
            v = self_row[j]
        elif j < pos + other_cols:
            v = other_row[j - pos]
        else:
            v = self_row[j - other_cols]
        old_result = result
        result = result + [new_matrix_cell(v)]
        j = j + 1
    return result


# --- oracle: the real patched _eval_col_insert, row extracted -----------------

def real_insert_rows(self_rows, other_rows, cols, other_cols, pos):
    """Run the REAL _eval_col_insert on matrices whose rows are the given
    lists; return every row of the result as a list of ints."""
    rows = len(self_rows)
    self_m = ShapingMatrix(rows, cols,
                           lambda i, j: self_rows[i][j])
    other_m = ShapingMatrix(rows, other_cols,
                            lambda i, j: other_rows[i][j])
    res = self_m._eval_col_insert(pos, other_m)
    width = cols + other_cols
    return [[res[i, j] for j in range(width)] for i in range(rows)]


def check_case(self_rows, other_rows, cols, other_cols, pos):
    real_rows = real_insert_rows(self_rows, other_rows, cols, other_cols, pos)
    for i in range(len(self_rows)):
        shadow_out = insert_row(self_rows[i], other_rows[i],
                                cols, other_cols, pos)
        if shadow_out != real_rows[i]:
            return ("DISAGREEMENT\n"
                    "  row=%d cols=%r other_cols=%r pos=%r\n"
                    "  self_row=%r\n  other_row=%r\n"
                    "  shadow=%r\n  real=%r"
                    % (i, cols, other_cols, pos,
                       self_rows[i], other_rows[i],
                       shadow_out, real_rows[i]))
    return None


def boundary_cases():
    """(self_rows, other_rows, cols, other_cols, pos) tuples. Entry values
    chosen distinct across the two sides so any band mix-up is visible."""
    def srow(c):
        return [1000 + k for k in range(c)]

    def orow(c):
        return [-(2000 + k) for k in range(c)]

    cases = []
    shapes = [
        (0, 0, 0),                       # both empty
        (0, 1, 0), (0, 3, 0),            # empty original, block only
        (1, 0, 0), (1, 0, 1),            # empty block, pos at both ends
        (3, 0, 0), (3, 0, 2), (3, 0, 3),
        (1, 1, 0), (1, 1, 1),            # width-1 both sides
        (2, 1, 0), (2, 1, 1), (2, 1, 2),
        (3, 2, 0), (3, 2, 1), (3, 2, 2), (3, 2, 3),
        (6, 2, 0), (6, 2, 3), (6, 2, 6),  # the issue report's row shape
        (5, 3, 2), (7, 4, 5), (2, 2, 1),
        (8, 1, 4), (1, 8, 1), (4, 4, 4),
    ]
    for (c, oc, p) in shapes:
        cases.append(([srow(c)], [orow(oc)], c, oc, p))
    # value-domain edges on a mid-insertion shape
    for vals in ([0, 0, 0], [-1, 0, 1], [2**62, -2**62, 7]):
        cases.append(([list(vals)], [[5, -5]], 3, 2, 1))
    # multi-row bridge cases: every row checked against the same real result
    for (c, oc, p, r) in [(3, 2, 1, 4), (6, 2, 3, 6), (2, 3, 0, 3),
                          (4, 1, 4, 2), (0, 2, 0, 3)]:
        cases.append((
            [[i * 100 + k for k in range(c)] for i in range(r)],
            [[-(i * 100 + k + 1) for k in range(oc)] for i in range(r)],
            c, oc, p))
    return cases


def rand_case(rng):
    cols = rng.randint(0, 9)
    other_cols = rng.randint(0, 9)
    pos = rng.randint(0, cols)
    rows = 1 if rng.random() < 0.9 else rng.randint(2, 4)
    self_rows = [[rng.randint(-10**6, 10**6) for _ in range(cols)]
                 for _ in range(rows)]
    other_rows = [[rng.randint(-10**6, 10**6) for _ in range(other_cols)]
                  for _ in range(rows)]
    return self_rows, other_rows, cols, other_cols, pos


def main():
    checked = 0
    n_boundary = 0
    for case in boundary_cases():
        err = check_case(*case)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(*rand_case(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow insert_row == real _eval_col_insert rows on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee -> real _new/__getitem__)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
