#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13031.

Executes the REAL repo callees (`SparseMatrix.row_join`, `SparseMatrix.col_join`)
on a grid of operand shapes CROSSED WITH a payload catalogue — including every
degenerate zero-row / zero-column case, the exact FAIL_TO_PASS stacking chains,
and the incompatible-shape rejection — and asserts that every observation matches
the deep model encoded in model.py.

There are NO consumed `@ContractOnly` axioms in this bundle. The single opaque
sub-operation — the unchanged element merge's net effect on the result SHAPE and
on the HELD-CELL population — is modeled DEEPLY as integer arithmetic over five
facets; this is the A-reference G-AX validates:

  (A-reference)  row_join(a, b).shape == (a.rows, a.cols + b.cols)   [accumulate
                 columns]  on the compatible / degenerate-normalisation path;
                 col_join(a, b).shape == (a.rows + b.rows, a.cols)   [transpose];
                 ShapeError raised exactly on the incompatible path.

  (content)      held(join(a, b)) == held(a) + held(b) on every returning path,
                 including the degenerate-normalisation one: concatenation carries
                 both operands' held cells over and invents none.

  (placement)    the held cells of `a` keep their coordinates and those of `b`
                 are offset along the concatenation axis ONLY:
                   row_join: rsum' == rsum(a) + rsum(b)
                             csum' == csum(a) + csum(b) + a.cols * held(b)
                   col_join: the transpose.
                 Shape and count alone cannot see a permutation of the cells;
                 these two index sums can, so the operand payloads are VARIED
                 (empty, dense, patterned, and every value class below) and the
                 observation is not vacuous.

  (degenerate-normalisation)  a 0-shared-dimension operand whose orthogonal
                 dimension disagrees is normalised to the other's, then summed:
                 row_join: a.cols == 0 and a.rows != b.rows ->
                     result.shape == (b.rows, b.cols)  and the result holds b's
                     cells AT THEIR OWN COORDINATES (offset a.cols == 0)
                 col_join: a.rows == 0 and a.cols != b.cols -> the transpose.

RETENTION PREDICATE. `held` is the population of cells the repo's own retention
predicate keeps: a cell is held exactly when its value TESTS TRUE (`if value:` /
`if v:`, sympy/matrices/sparse.py:58, 66, 76, 87 in the constructor and :1002 /
:1210 in the merge loops). It is NOT "unequal to zero": for a sympy object the
two predicates SPLIT (`S.false`, `Eq(1, 2)`, `EmptySet()`, `FiniteSet()` all test
false while comparing unequal to 0). `_check_predicate_splits` below MEASURES
that the catalogue really reaches that splitting class and that the deep model
would be FALSE of the repo under the rejected reading, so the choice of predicate
is recorded as a fact rather than assumed. A cell whose truth value is
INDETERMINATE (e.g. `x > 0`) has no sparse image at all: the model's carrier
cannot represent it and the real callee refuses it with `TypeError`, which
`_check_domain_boundary` measures.

Imports only `sympy` (the repo under test, with the patch applied). Exit 0 iff
every observation matches the deep model.
"""
import sys


# --- model.py deep model (kept in lock-step with the impl regions) ------------

class _Mismatch(Exception):
    pass


def model_concat_right(a, b):
    """Deep model of concat_right over the 5-facet carrier
    (rows, cols, held, rsum, csum) -> same, or raises _Mismatch."""
    (ar, ac, ah, ars, acs) = a
    (br, bc, bh, brs, bcs) = b
    if ac == 0 and ar != br:
        # the normalisation rebuild: Mat(b.rows, 0, 0, 0, 0), then recurse
        return model_concat_right((br, 0, 0, 0, 0), b)
    if ar != br:
        raise _Mismatch()
    return (ar, ac + bc, ah + bh, ars + brs, acs + bcs + ac * bh)


def model_concat_below(a, b):
    """Deep model of concat_below: the exact transpose."""
    (ar, ac, ah, ars, acs) = a
    (br, bc, bh, brs, bcs) = b
    if ar == 0 and ac != bc:
        return model_concat_below((0, bc, 0, 0, 0), b)
    if ac != bc:
        raise _Mismatch()
    return (ar + br, ac, ah + bh, ars + brs + ar * bh, acs + bcs)


def held_cells(m):
    """The coordinates of the cells `m` HOLDS, under the repo's own retention
    predicate (value TESTS TRUE), read through the PUBLIC element accessor so a
    dense and a sparse operand are measured identically."""
    return [(i, j) for i in range(m.rows) for j in range(m.cols) if m[i, j]]


def facets(m):
    """matrix -> (rows, cols, held, rsum, csum)."""
    cells = held_cells(m)
    return (m.rows, m.cols, len(cells),
            sum(i for (i, j) in cells), sum(j for (i, j) in cells))


def facets_nonzero(m):
    """The REJECTED reading of `held` ("unequal to zero"), kept as an executable
    control so `_check_predicate_splits` can demonstrate the two differ."""
    cells = [(i, j) for i in range(m.rows) for j in range(m.cols)
             if m[i, j] != 0]
    return (m.rows, m.cols, len(cells),
            sum(i for (i, j) in cells), sum(j for (i, j) in cells))


# --- operands: shape x payload class ------------------------------------------

def value_classes(S, Eq, sqrt, EmptySet, FiniteSet, oo, nan, zoo):
    """payload class -> cell values. `falsy` is the class on which "tests true"
    and "unequal to zero" DISAGREE."""
    return {
        "empty":   [],
        "int":     [1, -7, 3, 5, 2, -2, 11],
        "exotic":  [S.Half, sqrt(2), S.Pi, oo, nan, zoo, S.true],
        "falsy":   [S.false, Eq(1, 2), EmptySet(), FiniteSet()],
        "mixed":   [1, S.false, S.Half, Eq(1, 2), -7, EmptySet(), S.true,
                    FiniteSet(), oo],
    }


def operand(SparseMatrix, Matrix, r, c, vals, dense=False):
    """A (r x c) operand carrying a deterministic pattern drawn from `vals`.
    An `empty` class gives the all-zero operand; every other class puts real
    cells in, at coordinates that vary with (i, j) so the index sums are
    non-trivial. A dense operand is built from a flat list, so a falsy cell
    really is present and really does reach the merge's `if v:` filter."""
    present = {}
    if vals:
        for i in range(r):
            for j in range(c):
                if (i + 3 * j) % 4 != 1:
                    present[(i, j)] = vals[(i + 2 * j) % len(vals)]
    if not present:
        return (Matrix if dense else SparseMatrix).zeros(r, c)
    if dense:
        flat = [0] * (r * c)
        for (i, j) in present:
            flat[i * c + j] = present[(i, j)]
        return Matrix(r, c, flat)
    return SparseMatrix(r, c, dict(present))


# --- the checks against the REAL callees --------------------------------------

def _check(model, method_name, ShapeError, a, b, label):
    """One observation: the deep model vs the real callee, on shape AND on the
    held-cell population AND on where those cells landed."""
    fa, fb = facets(a), facets(b)
    try:
        expected = model(fa, fb)
    except _Mismatch:
        expected = None
    if expected is None:
        raised = False
        try:
            getattr(a, method_name)(b)
        except ShapeError:
            raised = True
        assert raised, (
            "%s(%r, %r) [%s]: model rejects but the real callee did not raise"
            % (method_name, fa, fb, label))
        return
    res = getattr(a, method_name)(b)
    got = facets(res)
    assert got == expected, (
        "%s(a=%r, b=%r) [%s]: real (rows,cols,held,rsum,csum) %r != deep model %r"
        % (method_name, fa, fb, label, got, expected))


def _check_predicate_splits(SparseMatrix, Matrix, classes):
    """MEASURE that the catalogue reaches the class on which the two candidate
    retention predicates differ, and that under the REJECTED one the deep model
    would be FALSE of the real callee. Without this the choice of `held` would be
    an unexamined assumption; with it, the failure of the alternative is a
    recorded observation."""
    splits = 0
    refuted = 0
    vals = classes["falsy"]
    for r in (1, 2, 3):
        for c in (1, 2, 3):
            for dense in (False, True):
                m = operand(SparseMatrix, Matrix, r, c, vals, dense)
                if facets(m) != facets_nonzero(m):
                    splits += 1
                # ...and the model, fed the rejected reading of the SAME
                # operands, disagrees with the real callee:
                zero = SparseMatrix.zeros(r, 0)
                real = facets(zero.row_join(m))
                alt = model_concat_right(facets_nonzero(zero),
                                         facets_nonzero(m))
                if alt != real:
                    refuted += 1
    assert splits > 0, (
        "the payload catalogue never produced a matrix on which 'tests true' "
        "and 'unequal to zero' differ, so G-AX certifies nothing about the "
        "value axis")
    assert refuted > 0, (
        "the deep model could not be refuted under the rejected 'unequal to "
        "zero' reading, so `held` is not pinned by this check")
    return splits, refuted


def _check_domain_boundary(SparseMatrix, Matrix):
    """MEASURE the carrier's domain boundary: a cell whose truth value is
    INDETERMINATE has no held/not-held answer, so the abstraction is undefined on
    it — and the real callee likewise refuses instead of returning. Model and
    repo agree that such a value is not representable."""
    from sympy import Symbol
    from sympy.matrices import MutableSparseMatrix
    x = Symbol('x')
    m = Matrix(1, 1, [x > 0])
    probes = [
        ("abstraction", lambda: facets(m)),
        ("sparse image", lambda: MutableSparseMatrix(m)),
        ("row_join", lambda: SparseMatrix.zeros(1, 0).row_join(m)),
        ("col_join", lambda: SparseMatrix.zeros(0, 1).col_join(m)),
    ]
    for (label, fn) in probes:
        refused = False
        try:
            fn()
        except TypeError:
            refused = True
        assert refused, (
            "indeterminate-truth cell: %s did NOT refuse, so the domain "
            "boundary recorded in mapping.md is wrong" % label)
    return len(probes)


def main():
    from sympy import (SparseMatrix, Matrix, S, Eq, sqrt, EmptySet, FiniteSet,
                       oo, nan, zoo)
    from sympy.matrices.common import ShapeError

    classes = value_classes(S, Eq, sqrt, EmptySet, FiniteSet, oo, nan, zoo)
    names = sorted(classes)

    # --- (0) the retention predicate and the domain boundary -----------------
    splits, refuted = _check_predicate_splits(SparseMatrix, Matrix, classes)
    n_boundary = _check_domain_boundary(SparseMatrix, Matrix)

    # --- (1) shape grid {0..3}^4 x payload class x sparse/dense `other` ------
    dims = range(0, 4)
    n = 0
    for ar in dims:
        for ac in dims:
            for br in dims:
                for bc in dims:
                    for cname in names:
                        vals = classes[cname]
                        for dense in (False, True):
                            a = operand(SparseMatrix, Matrix, ar, ac, vals)
                            b = operand(SparseMatrix, Matrix, br, bc, vals,
                                        dense)
                            _check(model_concat_right, "row_join", ShapeError,
                                   a, b, cname)
                            _check(model_concat_below, "col_join", ShapeError,
                                   a, b, cname)
                            n += 2

    # --- (2) placement-sensitive larger shapes ------------------------------
    for (ar, ac, br, bc) in [(4, 6, 4, 9), (3, 2, 3, 5), (2, 4, 2, 1),
                             (5, 5, 5, 5), (7, 1, 7, 6), (4, 0, 4, 6),
                             (0, 6, 4, 6), (17, 0, 4, 6)]:
        for cname in names:
            vals = classes[cname]
            a = operand(SparseMatrix, Matrix, ar, ac, vals)
            b = operand(SparseMatrix, Matrix, br, bc, vals)
            _check(model_concat_right, "row_join", ShapeError, a, b, cname)
            a = operand(SparseMatrix, Matrix, ac, ar, vals)
            b = operand(SparseMatrix, Matrix, bc, br, vals)
            _check(model_concat_below, "col_join", ShapeError, a, b, cname)
            n += 2

    # --- (3) the exact FAIL_TO_PASS stacking chains -------------------------
    hs = [SparseMatrix.zeros(0, k) for k in range(4)]
    got = SparseMatrix.hstack(*hs)
    assert got.shape == (0, 6), "hstack chain shape %r != (0, 6)" % (got.shape,)
    assert got == Matrix(0, 6, []), "hstack chain != Matrix(0, 6, [])"

    vs = [SparseMatrix.zeros(k, 0) for k in range(4)]
    got = SparseMatrix.vstack(*vs)
    assert got.shape == (6, 0), "vstack chain shape %r != (6, 0)" % (got.shape,)
    assert got == Matrix(6, 0, []), "vstack chain != Matrix(6, 0, [])"

    # --- (4) a non-degenerate chain, folded through the deep model -----------
    for cname in names:
        vals = classes[cname]
        parts = [operand(SparseMatrix, Matrix, 2, k, vals) for k in range(4)]
        acc = facets(parts[0])
        for p in parts[1:]:
            acc = model_concat_right(acc, facets(p))
        assert facets(SparseMatrix.hstack(*parts)) == acc, (
            "hstack chain [%s] folded deep model %r != real %r"
            % (cname, acc, facets(SparseMatrix.hstack(*parts))))
        parts = [operand(SparseMatrix, Matrix, k, 2, vals) for k in range(4)]
        acc = facets(parts[0])
        for p in parts[1:]:
            acc = model_concat_below(acc, facets(p))
        assert facets(SparseMatrix.vstack(*parts)) == acc, (
            "vstack chain [%s] folded deep model %r != real %r"
            % (cname, acc, facets(SparseMatrix.vstack(*parts))))
        n += 2

    # --- (5) type preservation (the original P2P guard) ----------------------
    a = SparseMatrix(((1, 0), (0, 1)))
    b = SparseMatrix(((2, 0), (0, 2)))
    assert type(a.row_join(b)) == type(a)
    assert type(a.col_join(b)) == type(a)

    # --- (6) the F2P CONTENT case: joining onto an operand that holds nothing
    # --- reproduces the other operand IN FULL AND IN PLACE (== b), not a null
    # --- matrix of b's shape and not b's cells relocated.
    from sympy.matrices import MutableSparseMatrix, MutableDenseMatrix
    e = MutableSparseMatrix([])
    f = MutableDenseMatrix([1, 2])
    rj = e.row_join(f)
    assert facets(rj) == model_concat_right(facets(e), facets(f)), (
        "F2P row_join: real %r != deep model %r"
        % (facets(rj), model_concat_right(facets(e), facets(f))))
    assert rj == f, "F2P row_join: result != b (content discarded)"
    cj = e.col_join(f)
    assert facets(cj) == model_concat_below(facets(e), facets(f)), (
        "F2P col_join: real %r != deep model %r"
        % (facets(cj), model_concat_below(facets(e), facets(f))))
    assert cj == f, "F2P col_join: result != b (content discarded)"
    n += 2

    print("G-AX OK: deep 5-facet model (shape + held-cell count + both held-cell "
          "index sums) == real SparseMatrix.row_join/col_join over %d operand "
          "observations spanning %d payload classes (incl. the falsy-but-unequal-"
          "to-zero class) and sparse/dense operands, + F2P hstack/vstack chains + "
          "folded non-degenerate chains + F2P content case + type preservation; "
          "the retention predicate split from the unequal-to-zero reading on %d "
          "operand(s) and refuted the model under that reading %d time(s); the "
          "indeterminate-truth domain boundary holds on %d probes."
          % (n, len(classes), splits, refuted, n_boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
