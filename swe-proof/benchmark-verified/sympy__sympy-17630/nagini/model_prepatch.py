"""Twin-artifact model for sympy__sympy-17630.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic combination (a commutative sum, or a product) of terms is
  post-processed for the matrix-expression domain. Its terms are partitioned
  into matrix-valued terms and ordinary scalar terms, and a single combined
  expression is rebuilt for the matrix domain. The result is described only by
  two observable facets: how many matrix terms feed the rebuilt matrix-domain
  combination, and whether the rebuilt matrix-domain combination is fed a
  scalar coefficient term as one of its top-level arguments.

  (1) For a SUM with at least one matrix term, the rebuilt matrix-domain sum is
      formed from the matrix terms ALONE. No scalar coefficient is ever placed
      among its arguments: when the sum has no genuine scalar term, the empty
      collection of scalars must NOT be collapsed into the additive identity and
      injected as an argument. Consequently the rebuilt sum stays a matrix
      expression, so a sum of matrix terms remains in the matrix domain (and an
      all-zero such sum stays a matrix zero, not a bare scalar zero). When the
      sum does carry a genuine scalar term, that scalar is held apart from the
      matrix-domain sum, which is still formed from the matrix terms alone.

  (2) For a PRODUCT with at least one matrix term, any scalar coefficient is
      first absorbed into one of the matrix factors when an explicit matrix
      factor is present, leaving only matrix factors for the matrix-domain
      product; otherwise the scalar coefficient multiplies the matrix-domain
      product as its leading factor.

The combination is modelled by a minimal class carrying only the two touched
facets: ``matrix_arg_count`` (how many matrix terms feed the matrix-domain
combination) and ``scalar_arg_present`` (whether a scalar term sits among its
top-level arguments). The concrete term payloads are irrelevant to the
behaviour under specification.

Rebuilding the combination is a bounded, straight-line computation: the
post-processor MUST terminate and return its combination (a total-correctness
obligation, carried as MustTerminate in the precondition). An implementation
that diverges before returning would satisfy the value postconditions only
vacuously and would never deliver the rebuilt combination to the constructor
pipeline.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Combo:
    """The rebuilt matrix-domain combination, described by its two touched
    facets: the number of matrix terms it combines and whether a scalar
    coefficient term sits among its top-level arguments."""

    def __init__(self, matrix_arg_count: int, scalar_arg_present: bool) -> None:
        Requires(matrix_arg_count >= 0)
        # Constructing the combination terminates (a straight-line field
        # initialisation); takes the caller's termination obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.matrix_arg_count) and self.matrix_arg_count == matrix_arg_count)  # type: ignore
        Ensures(Acc(self.scalar_arg_present) and self.scalar_arg_present == scalar_arg_present)  # type: ignore
        self.matrix_arg_count = matrix_arg_count
        self.scalar_arg_present = scalar_arg_present


# axioms-start
# (no @ContractOnly axioms: the unchanged matrix-domain constructors and the
# scalar-collapse / scalar-absorb helpers contribute nothing to the touched
# facets beyond what the impl spells out deeply — see refinement.md
# A-reference rows. The axioms region is intentionally empty.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def postprocess(is_sum: bool, num_matrices: int, num_scalars: int,
                has_explicit_matrix: bool) -> Combo:
    """Rebuild the matrix-domain combination for a sum (``is_sum``) or a product
    of ``num_matrices`` matrix terms and ``num_scalars`` scalar terms; for a
    product, ``has_explicit_matrix`` records whether an explicit matrix factor is
    present to absorb a scalar coefficient. Pre-condition: at least one matrix
    term (the no-matrix case is handled before this point)."""
    # pre-conditions-start
    Requires(num_matrices >= 1)
    Requires(num_scalars >= 0)
    # Rebuilding the combination is a bounded, straight-line computation: the
    # post-processor MUST terminate and return its Combo (total correctness).
    # A diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver the rebuilt combination to the
    # constructor pipeline.
    Requires(MustTerminate(2))
    # post-conditions-end is below; this is the pre block
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().matrix_arg_count) and Acc(Result().scalar_arg_present))
    # The matrix-domain combination is always formed from exactly the matrix
    # terms (a product whose scalar is absorbed loses no matrix factor; a sum
    # never folds a scalar into the matrix-domain combination).
    Ensures(Result().matrix_arg_count == num_matrices)
    # (1) A SUM never receives a scalar coefficient among the matrix-domain
    # arguments — including when there is no genuine scalar term, where the
    # additive identity must NOT be collapsed in. The rebuilt sum therefore
    # stays a matrix expression.
    Ensures(Implies(is_sum, Result().scalar_arg_present == False))
    # (2) A PRODUCT keeps a scalar coefficient argument exactly when it has a
    # genuine scalar term that no explicit matrix factor can absorb.
    Ensures(Implies(not is_sum,
                    Result().scalar_arg_present
                    == (num_scalars > 0 and not has_explicit_matrix)))
    # post-conditions-end
    # impl-start
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
    # No genuine scalar term remains. Pre-patch: the empty scalar collection is
    # collapsed into the additive/multiplicative identity and injected as a
    # top-level argument of the rebuilt matrix-domain combination.
    if is_sum:
        # The additive identity is injected into the matrix-domain SUM and is
        # NOT dropped there — contaminating the rebuilt sum with a scalar zero.
        return Combo(num_matrices, True)
    # For a PRODUCT the injected multiplicative identity is the trivial
    # coefficient, dropped by the matrix-domain product — observably no scalar.
    return Combo(num_matrices, False)
    # impl-end
