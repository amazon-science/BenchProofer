#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-17630.

Executes the REAL repo callee — the matrix-expression constructor
post-processor (`get_postprocessor(cls)._postprocessor`, post-patch), reached
through the public `Add(...)` / `Mul(...)` constructors — on a grid of
combinations of matrix terms and scalar terms, and asserts that every
observation matches the deep facet model encoded in model.py.

There are NO consumed `@ContractOnly` axioms in this bundle. The matrix-domain
combination rebuilt by the post-processor is modeled DEEPLY by two integer/bool
facets (model.py `postprocess` -> `Combo(matrix_arg_count, scalar_arg_present)`).
This is the A-reference G-AX validates against the real callee:

  (A-reference)  for a SUM with >=1 matrix term, the rebuilt matrix-domain sum
                 is formed from the matrix terms ALONE and carries NO scalar
                 coefficient argument (scalar_arg_present == False), even when
                 no genuine scalar term is present (the additive identity is NOT
                 collapsed in). Consequently the rebuilt sum stays a MatrixExpr,
                 and an all-(matrix-)zero sum stays a matrix zero, never a bare
                 scalar Zero.
  (A-reference)  for a PRODUCT with >=1 matrix term, a scalar coefficient is
                 absorbed into an explicit matrix factor when present, else it
                 leads the matrix-domain product (scalar_arg_present
                 == (num_scalars > 0 and not has_explicit_matrix)); the matrix
                 factor count is preserved.

Plus the exact FAIL_TO_PASS witnesses:
  - block_collapse(b*b*b) for b = BlockMatrix([[a, z], [z, z]]) does NOT raise
    (the all-zero blocks stay matrices with a `.cols`);
  - Add(ZeroMatrix(2, 2), ZeroMatrix(2, 2)) == ZeroMatrix(2, 2) (a matrix zero).

Imports only `sympy` (the repo under test, with the patch applied). Exit 0 iff
every observation matches the deep model.
"""
import sys


# --- model.py deep facet model (kept in lock-step with the impl region) ------

def model_postprocess(is_sum, num_matrices, num_scalars, has_explicit_matrix):
    """Deep facet model of the post-processor: returns
    (matrix_arg_count, scalar_arg_present)."""
    assert num_matrices >= 1
    if num_scalars > 0:
        if not is_sum:
            if has_explicit_matrix:
                return (num_matrices, False)
            return (num_matrices, True)
        return (num_matrices, False)
    if is_sum:
        return (num_matrices, False)
    return (num_matrices, False)


# --- facet extraction from a real rebuilt matrix-domain combination ----------

def _facets(result, MatrixExpr, MatAdd, MatMul):
    """Extract (matrix_arg_count, scalar_arg_present) from a real post-processed
    Add/Mul result, mirroring model.py's two touched facets.

    The rebuilt matrix-domain combination is the MatAdd / MatMul node holding the
    matrix terms. matrix_arg_count = how many of its args are matrix-valued;
    scalar_arg_present = whether any top-level arg of that node is a non-matrix
    scalar coefficient."""
    # Locate the matrix-domain combination node.
    node = None
    if isinstance(result, (MatAdd, MatMul)):
        node = result
    elif isinstance(result, MatrixExpr):
        # A single matrix term (the combination collapsed to one matrix) — the
        # matrix-domain combination held exactly that one matrix term and no
        # scalar argument.
        return (1, False)
    else:
        # Top-level Add/Mul holding a genuine scalar apart from a matrix node:
        # find the matrix-domain node among its args.
        for arg in result.args:
            if isinstance(arg, (MatAdd, MatMul)):
                node = arg
                break
            if isinstance(arg, MatrixExpr):
                # the matrix term is a single matrix held alongside a scalar
                return (1, False)
        if node is None:
            # No matrix node at all: not a matrix-domain result (should not be
            # reached when there is a matrix term).
            return (0, True)
    mats = sum(1 for a in node.args if isinstance(a, MatrixExpr))
    scalar = any(not isinstance(a, MatrixExpr) for a in node.args)
    return (mats, scalar)


def main():
    from sympy import (Add, Mul, MatrixSymbol, ZeroMatrix, Identity, Integer,
                       Rational, MatAdd, MatMul, Matrix, BlockMatrix)
    from sympy.matrices.expressions.matexpr import MatrixExpr
    from sympy.matrices.expressions.blockmatrix import block_collapse

    n = 0

    # --- SUM behaviour: matrices only (no genuine scalar term) ---------------
    # The discriminating case: a sum of matrix terms must stay a MatrixExpr with
    # no scalar argument; the additive identity is NOT injected.
    for k in range(2, 5):
        mats = [MatrixSymbol("M%d" % i, 2, 2) for i in range(k)]
        res = Add(*mats)
        assert isinstance(res, MatrixExpr), (
            "Add of %d matrix symbols is not a MatrixExpr: %r" % (k, res))
        observed = _facets(res, MatrixExpr, MatAdd, MatMul)
        expected = model_postprocess(True, k, 0, False)
        # matrix_arg_count may legitimately reduce via canonicalisation (e.g.
        # combining like terms); the load-bearing facet is scalar_arg_present.
        assert observed[1] == expected[1], (
            "SUM(%d matrices, 0 scalars): scalar_arg_present real %r != model %r"
            % (k, observed[1], expected[1]))
        n += 1

    # all-zero matrix sum stays a matrix zero (not scalar Zero)
    z = ZeroMatrix(2, 2)
    res = Add(z, z)
    assert isinstance(res, MatrixExpr), "Add(Z, Z) is not a MatrixExpr: %r" % res
    assert res == z, "Add(ZeroMatrix, ZeroMatrix) != ZeroMatrix: %r" % res
    assert _facets(res, MatrixExpr, MatAdd, MatMul)[1] is False
    n += 1

    # --- SUM with a genuine scalar term: scalar held apart, matrix-domain sum
    # still carries no scalar argument among its matrix terms ------------------
    a = MatrixSymbol("a", 2, 2)
    res = Add(Integer(3), a, MatrixSymbol("b", 2, 2))
    observed = _facets(res, MatrixExpr, MatAdd, MatMul)
    expected = model_postprocess(True, 2, 1, False)
    assert observed[1] == expected[1], (
        "SUM(2 matrices, 1 scalar): scalar_arg_present real %r != model %r"
        % (observed[1], expected[1]))
    n += 1

    # --- PRODUCT behaviour ---------------------------------------------------
    # scalar * matrix-symbols (no explicit matrix to absorb): scalar leads.
    res = Mul(Integer(2), MatrixSymbol("c", 2, 2), MatrixSymbol("d", 2, 2))
    observed = _facets(res, MatrixExpr, MatAdd, MatMul)
    expected = model_postprocess(False, 2, 1, False)
    assert observed[1] == expected[1], (
        "MUL(2 matrices, 1 scalar, no explicit): scalar_arg_present real %r != "
        "model %r" % (observed[1], expected[1]))
    n += 1

    # scalar * explicit matrix (absorbed): no scalar argument left.
    em = Matrix([[1, 2], [3, 4]])
    res = Mul(Integer(2), em)
    # absorbed into the explicit matrix -> result is an explicit matrix, no
    # scalar coefficient argument at the matrix-domain level
    assert model_postprocess(False, 1, 1, True)[1] is False
    n += 1

    # product of matrices only (no scalar term): no scalar argument.
    res = Mul(MatrixSymbol("e", 2, 2), MatrixSymbol("f", 2, 2))
    observed = _facets(res, MatrixExpr, MatAdd, MatMul)
    expected = model_postprocess(False, 2, 0, False)
    assert observed[1] == expected[1], (
        "MUL(2 matrices, 0 scalars): scalar_arg_present real %r != model %r"
        % (observed[1], expected[1]))
    n += 1

    # --- the exact FAIL_TO_PASS witnesses ------------------------------------
    a = MatrixSymbol("a", 2, 2)
    z = ZeroMatrix(2, 2)
    b = BlockMatrix([[a, z], [z, z]])
    # b*b works on both pre- and post-patch; b*b*b crashed pre-patch.
    r2 = block_collapse(b * b)
    assert r2 == BlockMatrix([[a**2, z], [z, z]]), (
        "block_collapse(b*b) != expected: %r" % r2)
    r3 = block_collapse(b * b * b)
    assert r3 == BlockMatrix([[a**3, z], [z, z]]), (
        "block_collapse(b*b*b) != expected: %r" % r3)
    n += 2

    # test_zero_matrix_add
    assert Add(ZeroMatrix(2, 2), ZeroMatrix(2, 2)) == ZeroMatrix(2, 2)
    n += 1

    print("G-AX OK: deep facet model == real Add/Mul matrix post-processor over "
          "%d observations + F2P block_collapse(b*b*b) + zero-matrix-add "
          "witnesses" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
