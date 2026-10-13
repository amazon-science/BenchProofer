#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-13647.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_colInsert` skeleton (the R/I per-entry accessor) and diffs it
against the REAL patched `Matrix.col_insert` over a discrete catalogue plus
>=1e5 randomized draws.

  observable: every entry `M.col_insert(pos, other)[i, j]` of the inserted
  matrix, for fuzzed host `self` (rows x cols), inserted block `other`
  (rows x ocols) and insertion column `pos in 0..cols`.

Shadow (transliteration of implementation_colInsert / problem_spec_colInsert):
    if j < pos:                  -> self[i, j]
    elif pos <= j < pos+ocols:   -> other[i, j - pos]
    else:                        -> self[i, j - ocols]   # gold arithmetic

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 13647
N_RANDOM = 120_000  # >= 1e5


def shadow_entry(self_rows, self_data, other_data, pos, ocols, i, j):
    """Python shadow of implementation_colInsert at (i, j).
    self_data[i][c] = self[i, c];  other_data[i][c] = other[i, c]."""
    if j < pos:
        return self_data[i][j]
    if pos <= j < pos + ocols:
        return other_data[i][j - pos]
    return self_data[i][j - ocols]


def main():
    from sympy import Matrix

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def gen_case(rng, small):
        if small:
            rows = rng.randint(1, 4)
            scols = rng.randint(1, 4)
            ocols = rng.randint(1, 4)
            lo, hi = -3, 3
        else:
            rows = rng.randint(1, 7)
            scols = rng.randint(1, 7)
            ocols = rng.randint(1, 7)
            lo, hi = -9, 9
        self_data = [[rng.randint(lo, hi) for _ in range(scols)] for _ in range(rows)]
        other_data = [[rng.randint(lo, hi) for _ in range(ocols)] for _ in range(rows)]
        pos = rng.randint(0, scols)  # insertion column in 0..scols inclusive
        return rows, scols, ocols, pos, self_data, other_data

    # deterministic boundary catalogue first
    boundary = [
        (1, 1, 1, 0), (1, 1, 1, 1), (3, 3, 2, 0), (3, 3, 2, 3),
        (6, 6, 2, 3),  # the exact issue 13643 shape
    ]
    cases = []
    for rows, scols, ocols, pos in boundary:
        self_data = [[(1 if r == c else 0) for c in range(scols)] for r in range(rows)]
        other_data = [[2 for _ in range(ocols)] for _ in range(rows)]
        cases.append((rows, scols, ocols, pos, self_data, other_data))

    # randomized draws
    for k in range(N_RANDOM):
        cases.append(gen_case(rng, small=(k % 3 == 0)))

    for rows, scols, ocols, pos, self_data, other_data in cases:
        M = Matrix(rows, scols, lambda i, j: self_data[i][j])
        V = Matrix(rows, ocols, lambda i, j: other_data[i][j])
        real = M.col_insert(pos, V)
        # frame check on shape too
        if real.rows != rows or real.cols != scols + ocols:
            disagreements += 1
            if disagreements <= 5:
                print(f"SHAPE MISMATCH rows={rows} scols={scols} ocols={ocols} "
                      f"got=({real.rows},{real.cols})")
            continue
        for i in range(rows):
            for j in range(scols + ocols):
                got = int(real[i, j])
                exp = int(shadow_entry(rows, self_data, other_data, pos, ocols, i, j))
                checked += 1
                if got != exp:
                    disagreements += 1
                    if disagreements <= 5:
                        print(f"MISMATCH i={i} j={j} pos={pos} scols={scols} "
                              f"ocols={ocols}: real={got} shadow={exp}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
