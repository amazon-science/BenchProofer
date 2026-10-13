"""Twin-artifact model for scikit-learn__scikit-learn-13328.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the robust linear-regression estimator is fitted, the training feature
  matrix is first run through the input-validation step, which coerces it to a
  concrete element representation. Later, the gradient computation forms the
  *negation* of the rows of the (validated) feature matrix that are not
  treated as outliers.

  Element-wise negation of the validated matrix is well-defined for a
  floating-point element representation but RAISES for a logical (true/false)
  element representation: forming the negation is an operation that can FAIL,
  and whether it fails is determined by the element representation, not by the
  element values (the negated values would be identical either way). The
  desired behaviour is therefore:

    For ANY input element representation that the caller may supply -- including
    the logical (true/false) representation -- fitting must SUCCEED: the
    negation step must actually run to completion without raising. Concretely,
    the validation step must produce a validated matrix whose element
    representation supports negation, so that the subsequent gradient step is
    actually performed (not skipped, not raised) for every input.

The feature matrix is modelled as a `List[int]` of element values (the rows
selected for the squared-loss gradient, flattened), together with an integer
"element representation" tag. Three representations are modelled: the logical
representation `REP_LOGICAL == 0`, the integral representation
`REP_INTEGRAL == 1`, and the floating representation `REP_FLOATING == 2`.

`validated_rep` is the (deeply-modelled) representation produced by the
validation step, parameterised by whether a floating representation was
requested of the validator. `validate_matrix` is the validation step itself:
the only way to establish -- via the unforgeable capability token
`matrix_rep(input_rep, rep)` -- what element representation the matrix
ACTUALLY has after validation. `negate_rows` is the gradient step: the
negation operation that can only be performed when the matrix ACTUALLY HAS
(token-evidenced) a representation that supports negation (its precondition
can raise otherwise), which returns the element-wise negation, and which --
as evidence that the negation was ACTUALLY carried out for this input on
these very rows -- grants the unforgeable capability token
`negation_performed(input_rep, rows)`.
`fit_robust_regressor` is the modelled fitting routine: it validates then
negates, and its contract requires, for EVERY input representation, both the
element-wise negation result AND the `negation_performed` token for its own
rows -- so a verifying implementation must have actually run the negation
step on the caller's own rows, on a matrix whose ACTUAL representation
supports negation (which is only possible after validation coerced it to a
negation-supporting representation), for every input including the logical
one.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# Unforgeable capability token marking that the negation step was ACTUALLY
# CARRIED OUT, for a matrix that originated from the input representation
# `input_rep`, ON EXACTLY the row collection `rows` (the very selected
# row-slice the gradient step negates -- the reference itself, not merely
# something with equal contents). It is an abstract `@ContractOnly
# @Predicate` with NO body, so nothing can `Fold` it into existence: the ONLY
# producer is `negate_rows`'s postcondition (below), and `negate_rows` can
# only be entered with token evidence (`matrix_rep`) that the matrix ACTUALLY
# has a representation for which `supports_negation` holds. The token
# therefore certifies a control-flow effect -- "the negation ran to
# completion for this input, on these rows, rather than raising" -- that no
# value-level postcondition can witness (the negated values are identical
# whether the negation raises or not). Binding the `rows` reference into the
# token means it cannot be earned by negating some OTHER row collection (an
# empty stand-in, a copy, ...) while the caller's own rows are handled by a
# different route. `fit_robust_regressor`'s postcondition requires this token
# for its own `input_rep` and its own row collection, so the negation step is
# mandatory and cannot be inlined/bypassed. Provenance + soundness check:
# mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def negation_performed(input_rep: int, rows: List[int]) -> bool:
    pass


# Unforgeable capability token stating that the matrix originating from the
# input representation `input_rep` ACTUALLY HAS the element representation
# `rep` at this point -- i.e. the validation step ran on it and produced a
# matrix of representation `rep`. Abstract `@ContractOnly @Predicate` with NO
# body, so nothing can `Fold` it into existence: the ONLY producer is
# `validate_matrix`'s postcondition (below). It exists so the representation
# tag handed to the negation step CANNOT BE FABRICATED: without it, an
# implementation could pass an arbitrary negation-supporting tag while the
# matrix it negates still has a representation for which the negation is
# undefined -- claiming a success the operation would not deliver. Provenance
# + soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def matrix_rep(input_rep: int, rep: int) -> bool:
    pass


@ContractOnly
def validate_matrix(input_rep: int, request_floating: bool) -> int:
    """The input-validation step: the routine the fitting code runs the
    feature matrix through before any gradient work, parameterised by whether
    a floating representation is requested of it. Its result is the element
    representation of the VALIDATED matrix -- exactly the deep model
    `validated_rep` (validated == the real validation callee out-of-band by
    axiom_check.py / G-AX) -- and it grants the unforgeable
    `matrix_rep(input_rep, Result())` token: the evidence that the matrix now
    ACTUALLY HAS that representation (the sole producer of that token).
    Element values are preserved by the validation coercion (identity on the
    modelled value carrier), so no value payload is threaded through."""
    Requires(0 <= input_rep and input_rep <= 2)
    # The validated representation is exactly the deeply-modelled one.
    Requires(MustTerminate(2))
    Ensures(Result() == validated_rep(input_rep, request_floating))
    # Evidence that the matrix ACTUALLY has representation Result() now.
    Ensures(matrix_rep(input_rep, Result()))


@ContractOnly
def negate_rows(input_rep: int, rep: int, row_values: List[int]) -> List[int]:
    """The gradient negation step (the downstream numpy unary `-` on the
    validated row-slice). It is an operation that CAN RAISE: it can only be
    carried out when the representation the matrix ACTUALLY has at this point
    supports negation. Both halves of that claim are demanded as evidence:
    the unforgeable `matrix_rep(input_rep, rep)` token (the matrix really has
    representation `rep` -- only the validation step can grant it) and
    `supports_negation(rep)` (negation is defined for that representation).
    On success it returns the element-wise negation of the selected rows AND
    grants the `negation_performed(input_rep, row_values)` token, the
    evidence that the negation actually ran for a matrix originating from
    `input_rep` on exactly these row values (the sole producer of that token).
    Provenance + executable soundness check: mapping.md / axiom_check.py (the
    value model `negated` and the definedness model `supports_negation` are
    validated == numpy)."""
    Requires(Acc(list_pred(row_values), 1 / 2))
    # The matrix must ACTUALLY have representation `rep` here: unforgeable
    # evidence from the validation step, so the tag cannot be fabricated.
    Requires(matrix_rep(input_rep, rep))
    # The negation can only be performed when that actual representation
    # supports it (numpy `-` raises on a logical representation otherwise).
    Requires(supports_negation(rep))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(row_values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the element-wise negation of the selected rows.
    Ensures(ToSeq(Result()) == negated(ToSeq(row_values)))
    # Evidence that the negation was ACTUALLY performed for `input_rep` on
    # exactly this row collection.
    Ensures(negation_performed(input_rep, row_values))
# axioms-end


# pure-start
@Pure
def supports_negation(rep: int) -> bool:
    """True iff element-wise negation is defined for the element
    representation `rep`. The logical (true/false) representation does not
    support negation (the operation raises); integral and floating
    representations do."""
    return rep != 0  # REP_LOGICAL == 0


@Pure
def validated_rep(input_rep: int, request_floating: bool) -> int:
    """The element representation of the matrix produced by validation, given
    the input representation `input_rep` and whether a floating representation
    was requested of the validator.

    - If a floating representation is requested, every input representation is
      coerced to the floating representation (`REP_FLOATING == 2`).
    - Otherwise the input representation is preserved unchanged (a logical
      input stays logical, an integral input stays integral, etc.).
    """
    if request_floating:
        return 2  # REP_FLOATING
    return input_rep


@Pure
def negated(vals: PSeq[int]) -> PSeq[int]:
    """Element-wise negation of the whole sequence. Front-recursive over
    `PSeq` (recurses on `vals.drop(1)`) so a single unfold is available to
    callers per loop step."""
    if len(vals) == 0:
        return PSeq(0).take(0)
    return PSeq(-vals[0]) + negated(vals.drop(1))
# pure-end


def fit_robust_regressor(input_rep: int, row_values: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(row_values), 1 / 2))
    # The input element representation is one of the three modelled kinds;
    # in particular it MAY be the logical representation (REP_LOGICAL == 0).
    Requires(0 <= input_rep and input_rep <= 2)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(row_values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Fitting returns the element-wise negation of the selected rows (the result
    # is pinned to a structural function of the input, not an oracle).
    Ensures(ToSeq(Result()) == negated(ToSeq(row_values)))
    # AND, for EVERY input representation including the logical one, the negation
    # step must have ACTUALLY been performed (it must run, not raise) ON THESE
    # VERY row values: the result must carry the
    # `negation_performed(input_rep, row_values)` token. Because that
    # token is only granted by the negation step for the rows it actually
    # serviced -- and the negation step is only reachable with token evidence
    # that the matrix ACTUALLY has a negation-supporting representation, itself
    # only grantable by the validation step -- this forces the validation to
    # coerce a logical input before the (mandatory, non-bypassable) negation of
    # the caller's own rows. No implementation can satisfy this without doing
    # the coercion, for the logical input too.
    Ensures(negation_performed(input_rep, row_values))
    # post-conditions-end
    # impl-start
    # Validation: request a floating representation so that the subsequent
    # negation is well-defined regardless of the input representation.
    rep = validate_matrix(input_rep, True)
    result = negate_rows(input_rep, rep, row_values)
    return result
    # impl-end
