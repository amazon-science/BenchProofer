#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-17630 (nagini).

SHADOW: the impl region of model.py `postprocess`, copied verbatim below
with the contract calls stripped; `Combo` copies over with its contract
lines removed. There are no @Pure helpers and no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
the closure ``_postprocessor`` returned by
``sympy.matrices.expressions.matexpr.get_postprocessor(cls)``. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable. The closure is invoked directly on
duck-typed expressions exposing ``.args`` (exactly the boundary the real
constructor pipeline hands it), built from pools of distinct matrix symbols,
at most one explicit dense matrix, at most one zero matrix, and scalar terms
that survive constructor flattening (symbols and non-unit numbers) — i.e.
the closure's reachable input domain.

Facet bridge (mapping.md sections 1-2): the model's Combo facets are read
off the real run at the two documented observation points.
  * matrix_arg_count — "the matrix terms fed into mat_class(...)": the
    module-level matrix-domain constructors are wrapped with recording
    proxies that DELEGATE to the real classes; the first construction per
    invocation is the post-processor's own, and the count of matrix-valued
    arguments fed to it is the facet. (Later canonicalisation may merge
    terms; the facet is the fed splat.)
  * scalar_arg_present — "a scalar term sits among the rebuilt
    combination's top-level arguments": read from the same fed splat, with
    one bridge rule from the model's own impl comment — a product's
    multiplicative identity (the collapse of an EMPTY scalar collection,
    which the product constructor drops) is not a scalar argument; any
    other non-matrix argument is. A sum's genuine scalar held apart from
    the matrix node is never fed to it and does not count.

Input domain: the model requires num_matrices >= 1 and num_scalars >= 0;
every generated expression carries at least one matrix term. Distinct
matrix symbols per expression keep the input inside the post-flatten domain
the real pipeline feeds the closure (the constructor merges duplicate
terms before post-processing). Boundary: the full grid over is_sum x
num_matrices 1..4 x num_scalars 0..2 x explicit-matrix presence x
zero-matrix presence x scalar kinds. Fuzz: random draws until >= 1e5
invocations. Pinned seed: 17630.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + sympy (the repo under test) only.
"""
import json
import random
import sys

SEED = 17630
N_TARGET = 100000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

class Combo:
    def __init__(self, matrix_arg_count, scalar_arg_present):
        self.matrix_arg_count = matrix_arg_count
        self.scalar_arg_present = scalar_arg_present


def postprocess(is_sum, num_matrices, num_scalars, has_explicit_matrix):
    if num_scalars > 0:
        if not is_sum:
            # Product with a scalar coefficient: absorb it into an explicit
            # matrix factor when one is present, leaving only matrix factors.
            absorbed = has_explicit_matrix  # type: bool
            if absorbed:
                return Combo(num_matrices, False)
            # No explicit matrix to absorb into: the scalar coefficient leads
            # the matrix-domain product.
            return Combo(num_matrices, True)
        else:
            # Sum with a genuine scalar term: the scalar is held apart; the
            # matrix-domain sum is formed from the matrix terms alone.
            return Combo(num_matrices, False)
    # No genuine scalar term remains.
    if is_sum:
        # Build the matrix-domain sum from the matrix terms alone; do NOT
        # collapse the empty scalar collection into the additive identity and
        # inject it as an argument.
        return Combo(num_matrices, False)
    # Product with no scalar term: the matrix-domain product is the matrix
    # factors alone (the empty scalar collection collapses to the multiplicative
    # identity, which the product constructor drops — no scalar argument).
    return Combo(num_matrices, False)
    # impl-end


# --- driver --------------------------------------------------------------------

class DuckExpr(object):
    """Duck-typed expression exposing .args — the closure's input boundary."""

    def __init__(self, args):
        self.args = tuple(args)


def main():
    from sympy import (Add, Mul, MatrixSymbol, ZeroMatrix, Integer, Rational,
                       Symbol, ImmutableDenseMatrix)
    from sympy.matrices.expressions import matexpr
    from sympy.matrices.expressions.matexpr import MatrixExpr

    real_MatAdd = matexpr.MatAdd
    real_MatMul = matexpr.MatMul

    fed = {"first": None}

    def rec_matadd(*args, **kw):
        if fed["first"] is None:
            fed["first"] = args
        return real_MatAdd(*args, **kw)

    def rec_matmul(*args, **kw):
        if fed["first"] is None:
            fed["first"] = args
        return real_MatMul(*args, **kw)

    matexpr.MatAdd = rec_matadd
    matexpr.MatMul = rec_matmul

    pp_add = matexpr.get_postprocessor(Add)
    pp_mul = matexpr.get_postprocessor(Mul)

    # pools
    mat_syms = [MatrixSymbol("M%d" % i, 2, 2) for i in range(6)]
    explicit_pool = [ImmutableDenseMatrix([[1, 2], [3, 4]]),
                     ImmutableDenseMatrix([[0, 1], [-2, 5]])]
    zero = ZeroMatrix(2, 2)
    scalar_pool = [Symbol("x"), Symbol("y"), Integer(2), Integer(3),
                   Integer(-5), Rational(3, 2)]

    from sympy import S

    def real_facets(is_sum, terms):
        """Run the REAL patched closure; return the two facets read off the
        splat fed to the matrix-domain constructor, or raise."""
        fed["first"] = None
        (pp_add if is_sum else pp_mul)(DuckExpr(terms))
        if fed["first"] is None:
            raise RuntimeError("post-processor never constructed the "
                               "matrix-domain combination")
        count = sum(1 for a in fed["first"] if isinstance(a, MatrixExpr))
        # bridge: a product's multiplicative identity is the collapse of an
        # EMPTY scalar collection, which the constructor drops — not a
        # scalar argument. Any other non-matrix fed argument is one.
        scalar = any(not isinstance(a, MatrixExpr)
                     and not (not is_sum and a == S.One)
                     for a in fed["first"])
        return count, scalar

    def build_terms(rng, is_sum, n_syms, n_scalars, use_explicit, use_zero):
        mats = list(rng.sample(mat_syms, n_syms))
        if use_explicit:
            mats.append(rng.choice(explicit_pool))
        if use_zero:
            mats.append(zero)
        scalars = list(rng.sample(scalar_pool, n_scalars))
        terms = mats + scalars
        rng.shuffle(terms)
        num_matrices = len(mats)
        has_explicit = use_explicit and not is_sum and n_scalars > 0
        # has_explicit_matrix is the Mul absorb discriminator: an explicit
        # (non-abstract) matrix factor is present to absorb the scalar
        return terms, num_matrices, has_explicit

    def check(rng, is_sum, n_syms, n_scalars, use_explicit, use_zero):
        terms, num_matrices, _ = build_terms(rng, is_sum, n_syms, n_scalars,
                                             use_explicit, use_zero)
        has_explicit = bool(use_explicit)
        shadow = postprocess(is_sum, num_matrices, n_scalars,
                             has_explicit)
        desc = ("is_sum=%r terms=%r (num_matrices=%d num_scalars=%d "
                "has_explicit=%r)" % (is_sum, terms, num_matrices,
                                      n_scalars, has_explicit))
        try:
            real_count, real_scalar = real_facets(is_sum, terms)
        except Exception as e:
            return ("DISAGREEMENT on %s:\n  shadow Combo = (%d, %r)\n"
                    "  real post-processor raised %r"
                    % (desc, shadow.matrix_arg_count,
                       shadow.scalar_arg_present, e))
        if (shadow.matrix_arg_count != real_count
                or bool(shadow.scalar_arg_present) != bool(real_scalar)):
            return ("DISAGREEMENT on %s:\n  shadow Combo = (%d, %r)\n"
                    "  real facets  = (%d, %r)"
                    % (desc, shadow.matrix_arg_count,
                       shadow.scalar_arg_present, real_count, real_scalar))
        return None

    rng = random.Random(SEED)
    checked = 0

    # boundary grid
    for is_sum in (True, False):
        for n_syms in (1, 2, 3, 4):
            for n_scalars in (0, 1, 2):
                for use_explicit in (False, True):
                    for use_zero in (False, True):
                        err = check(rng, is_sum, n_syms, n_scalars,
                                    use_explicit, use_zero)
                        if err:
                            print(err)
                            return 1
                        checked += 1

    # fuzz
    while checked < N_TARGET:
        is_sum = rng.random() < 0.5
        n_syms = rng.randint(1, 5)
        n_scalars = rng.randint(0, 3)
        use_explicit = rng.random() < 0.3
        use_zero = rng.random() < 0.2
        err = check(rng, is_sum, n_syms, n_scalars, use_explicit, use_zero)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched matrix-domain "
          "post-processor facets on %d invocations (seed %d); "
          "0 disagreements." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
