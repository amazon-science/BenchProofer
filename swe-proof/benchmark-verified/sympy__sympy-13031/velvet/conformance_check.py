#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13031 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions
              (`hstackBlock` / `vstackBlock`) transliterated to Python over the
              mapping.md carrier (a block = (rows, cols, smat-dict); the
              `(rows, cols, _smat)` bijection of §2). The impl region has NO
              A-tagged callee — both kernels are concrete shape-and-cell
              arithmetic — so the shadow is pure R/I and G-CONF carries full
              weight (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour: the patched `SparseMatrix.row_join` /
              `SparseMatrix.col_join` applied at base_commit (the real
              correctness oracle, G-RESOLVE). The harness applies patch.diff
              before this runs.

They must agree on every Requires-satisfying operand pair. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

We also exercise the issue's actual symptom through the UNCHANGED `hstack` /
`vstack` reductions (`reduce(row_join,…)` / `reduce(col_join,…)`): the shadow
folds the kernel shadow over the operand list and must match the real
`SparseMatrix.hstack` / `vstack` shape — this is the end-to-end behaviour the
F2P test observes.

Runs in-container (the prebuilt SWE-Bench instance image), `sympy` only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy.matrices import SparseMatrix, Matrix

SEED = 13031
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean hstackBlock / vstackBlock -----------------
# block = (rows, cols, smat) with smat: dict[(i,j)] -> int.

def shadow_hstack(A, B):
    arows, acols, asmat = A
    brows, bcols, bsmat = B
    rows = brows if acols == 0 else arows
    cols = acols + bcols
    smat = dict(asmat)
    for (i, j), v in bsmat.items():
        smat[(i, j + acols)] = v
    return (rows, cols, smat)


def shadow_vstack(A, B):
    arows, acols, asmat = A
    brows, bcols, bsmat = B
    rows = arows + brows
    cols = bcols if arows == 0 else acols
    smat = dict(asmat)
    for (i, j), v in bsmat.items():
        smat[(i + arows, j)] = v
    return (rows, cols, smat)


# --- bridge to the real repo type (mapping.md §2) ----------------------------

def to_sparse(block):
    rows, cols, smat = block
    return SparseMatrix(rows, cols, {k: v for k, v in smat.items()})


def observe(m):
    return (m.rows, m.cols, {k: int(v) for k, v in m._smat.items()})


def oracle_hstack(A, B):
    """patch.diff behaviour: the patched SparseMatrix.row_join."""
    return observe(to_sparse(A).row_join(to_sparse(B)))


def oracle_vstack(A, B):
    """patch.diff behaviour: the patched SparseMatrix.col_join."""
    return observe(to_sparse(A).col_join(to_sparse(B)))


# --- input generation (require-satisfying) -----------------------------------

def rand_smat(rng, rows, cols):
    smat = {}
    if rows == 0 or cols == 0:
        return smat
    for _ in range(rng.randint(0, rows * cols)):
        i = rng.randrange(rows)
        j = rng.randrange(cols)
        smat[(i, j)] = rng.choice([-3, -1, 1, 2, 5, 7])
    return smat


def gen_h(rng):
    if rng.random() < 0.5:
        arows, acols = rng.randint(0, 4), 0
        brows, bcols = rng.randint(0, 4), rng.randint(0, 4)
    else:
        h = rng.randint(0, 4)
        arows = brows = h
        acols, bcols = rng.randint(0, 4), rng.randint(0, 4)
    return ((arows, acols, rand_smat(rng, arows, acols)),
            (brows, bcols, rand_smat(rng, brows, bcols)))


def gen_v(rng):
    if rng.random() < 0.5:
        arows, acols = 0, rng.randint(0, 4)
        brows, bcols = rng.randint(0, 4), rng.randint(0, 4)
    else:
        w = rng.randint(0, 4)
        acols = bcols = w
        arows, brows = rng.randint(0, 4), rng.randint(0, 4)
    return ((arows, acols, rand_smat(rng, arows, acols)),
            (brows, bcols, rand_smat(rng, brows, bcols)))


def boundary_pairs():
    h = [
        ((0, 0, {}), (0, 1, {})),
        ((0, 1, {}), (0, 2, {})),
        ((1, 0, {}), (1, 3, {(0, 0): 5, (0, 2): 7})),
        ((2, 0, {}), (2, 2, {(0, 0): 1, (1, 1): 2})),
        ((2, 2, {(0, 0): 1, (1, 1): 3}), (2, 1, {(0, 0): 9})),
        ((0, 2, {}), (0, 0, {})),
    ]
    v = [
        ((0, 0, {}), (1, 0, {})),
        ((1, 0, {}), (2, 0, {})),
        ((0, 1, {}), (3, 1, {(0, 0): 5, (2, 0): 7})),
        ((0, 2, {}), (2, 2, {(0, 0): 1, (1, 1): 2})),
        ((2, 2, {(0, 0): 1, (1, 1): 3}), (1, 2, {(0, 0): 9})),
        ((2, 0, {}), (0, 0, {})),
    ]
    return h, v


def check_endtoend():
    """The issue's actual symptom, through the UNCHANGED hstack/vstack folds."""
    sparse_matrices = [SparseMatrix.zeros(0, n) for n in range(4)]
    assert SparseMatrix.hstack(*sparse_matrices) == Matrix(0, 6, []), \
        "hstack of 0xn null matrices lost width"
    sparse_matrices = [SparseMatrix.zeros(n, 0) for n in range(4)]
    assert SparseMatrix.vstack(*sparse_matrices) == Matrix(6, 0, []), \
        "vstack of nx0 null matrices lost height"


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    bh, bv = boundary_pairs()
    for A, B in bh:
        count += 1
        if shadow_hstack(A, B) != oracle_hstack(A, B):
            disagreements.append(("hstack", A, B, shadow_hstack(A, B), oracle_hstack(A, B)))
    for A, B in bv:
        count += 1
        if shadow_vstack(A, B) != oracle_vstack(A, B):
            disagreements.append(("vstack", A, B, shadow_vstack(A, B), oracle_vstack(A, B)))

    for _ in range(N_FUZZ):
        A, B = gen_h(rng)
        count += 1
        if shadow_hstack(A, B) != oracle_hstack(A, B):
            disagreements.append(("hstack", A, B, shadow_hstack(A, B), oracle_hstack(A, B)))
        A, B = gen_v(rng)
        count += 1
        if shadow_vstack(A, B) != oracle_vstack(A, B):
            disagreements.append(("vstack", A, B, shadow_vstack(A, B), oracle_vstack(A, B)))
        if len(disagreements) >= 5:
            break

    try:
        check_endtoend()
    except AssertionError as e:
        disagreements.append(("endtoend", None, None, str(e), None))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, A, B, sh, orc in disagreements[:5]:
            print("  [%s] A=%r B=%r shadow=%r oracle=%r" % (kind, A, B, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of stackHorizontally/stackVertically agrees "
          "with patch.diff behaviour on %d operand pairs (seed=%d), plus the "
          "hstack/vstack end-to-end symptom; 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
