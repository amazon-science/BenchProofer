#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13647 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`insertColumns` / `spliceRow` / `spliceCols`) transliterated to
              Python over the *real* repo type (a sympy `Matrix`), via the
              mapping.md bijection (`List (List Int)` ↔ the matrix's rows;
              `Int` ↔ an integer matrix entry; `pos : Nat` ↔ the insert
              position). The splice is the per-row `take pos ++ orow ++ drop pos`.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sympy.matrices.dense.Matrix.col_insert` applied at base_commit
              (the real correctness oracle, G-RESOLVE). col_insert clamps `pos`
              into [0, cols] and requires equal row counts, then calls the
              patched `_eval_col_insert`.

There are no A-tagged callees (the operation is pure positional rearrangement),
so the shadow is pure R/I (`conf_skip = false`). They must agree on every
Requires-satisfying input (rectangular matrices, equal row counts, 0<=pos<=cols).
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib + sympy only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 13647
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean spliceRow/spliceCols, transliterated -------
def shadow_splice(srows, orows, pos):
    """spliceCols pos srows orows: per-row `take pos ++ orow ++ drop pos`.

    Mirrors the backward `while` fold of `insertColumns`, which prepends one
    spliced row per step and so computes exactly the row-wise list splice."""
    out = []
    for s, o in zip(srows, orows):
        out.append(s[:pos] + list(o) + s[pos:])
    return out


def oracle_col_insert(srows, orows, pos):
    """patch.diff's behaviour: the patched Matrix.col_insert, read back as a
    plain list-of-rows so it is directly comparable to the shadow.

    Importing exercises the *patched* repo source (the harness applies
    patch.diff at base_commit before this runs)."""
    from sympy import Matrix
    M = Matrix(srows) if srows else Matrix(0, 0, [])
    V = Matrix(orows) if orows else Matrix(0, 0, [])
    R = M.col_insert(pos, V)
    return [[int(R[i, j]) for j in range(R.cols)] for i in range(R.rows)]


def rand_matrix_pair(rng):
    """A rectangular (self, other) pair on the modeled domain: equal row counts,
    each rectangular, with self width c and a clamped position in [0, c]."""
    rows = rng.randint(1, 5)     # col_insert needs rows >= 1 to be meaningful
    c = rng.randint(1, 6)        # self.cols >= 1 (empty self short-circuits)
    oc = rng.randint(1, 4)       # other must have >= 1 column to insert
    srows = [[rng.randint(-9, 9) for _ in range(c)] for _ in range(rows)]
    orows = [[rng.randint(-9, 9) for _ in range(oc)] for _ in range(rows)]
    pos = rng.randint(0, c)      # in-range (post-clamp) position
    return srows, orows, pos


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    # the issue's exact example: eye(6), insert 2*ones(6,2) at pos 3
    eye6 = [[1 if i == j else 0 for j in range(6)] for i in range(6)]
    ones62 = [[2, 2] for _ in range(6)]
    yield (eye6, ones62, 3)
    yield (eye6, ones62, 0)            # insert at the very front
    yield (eye6, ones62, 6)            # insert at the very end
    yield ([[5]], [[7]], 0)           # 1x1 cases
    yield ([[5]], [[7]], 1)
    yield ([[1, 2, 3]], [[9]], 1)     # single row
    yield ([[1, 2, 3]], [[8, 9]], 2)
    yield ([[1], [2], [3]], [[7], [8], [9]], 0)  # single column self
    for _ in range(n):
        yield rand_matrix_pair(rng)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for srows, orows, pos in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_splice(srows, orows, pos)
        oracle = oracle_col_insert(srows, orows, pos)
        if shadow != oracle:
            disagreements.append((srows, orows, pos, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, o, p, sh, orc in disagreements:
            print("  self=%r other=%r pos=%r shadow=%r oracle=%r"
                  % (s, o, p, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of insertColumns (per-row take/drop splice) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
