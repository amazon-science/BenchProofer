"""Twin-artifact model for sympy__sympy-13757.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A product of two symbolic operands is resolved by a constant, side-agnostic
  rule that selects which operand contributes the result; that selection rule
  is not itself the subject of the desired behaviour. The result is either a
  fully-computed polynomial product or an unsimplified product expression,
  depending on which operand the rule selects.

  The desired behaviour: the product of a generic symbolic expression and a
  polynomial must come out fully computed (the polynomial product) regardless
  of which side the polynomial is written on. In particular the product with
  the generic expression written on the left must agree with the product with
  the polynomial written on the left — both must be the computed polynomial
  product, not an unsimplified expression.

The operand attributes that the constant selection rule reads are modelled as
interpreted real numbers (verified with `--float-encoding=real`): the selection
turns on the strict order of two reals, so they are kept as genuine, distinct
reals rather than faked with ints. Each operand is modelled by the two attributes
the rule and the observable outcome read — one real attribute and a boolean for
whether its contribution is the computed polynomial product — passed directly.
The constant selection rule is modelled deeply (it is unchanged); its provenance and
executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
def default_priority() -> float:
    """The selection attribute a generic symbolic expression carries (a constant
    baseline value common to ordinary expressions)."""
    Ensures(Result() == 10.0)
    return 10.0
# axioms-end


# pure-start
@Pure
def resolved_by_right(self_priority: float, other_priority: float,
                      other_has_handler: bool) -> bool:
    """The constant (unchanged) selection rule, as a pure predicate: the second
    operand contributes the result exactly when it is able to (the boolean) AND
    its selection attribute is strictly greater than the first operand's;
    otherwise the first operand contributes. Side-agnostic and not modified."""
    return other_has_handler and other_priority > self_priority
# pure-end


def product_is_evaluated(self_priority: float, self_evaluates: bool,
                         other_priority: float, other_evaluates: bool,
                         other_has_handler: bool) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is the contribution of whichever operand the constant selection
    # rule picks; the outcome is the computed polynomial product exactly when
    # the selected operand's contribution is itself the computed product. The
    # observable is thus produced by the selection, so it cannot report
    # "computed" unless the operand that actually contributes is the one that
    # computes the product.
    Ensures(Result() == (other_evaluates if resolved_by_right(
        self_priority, other_priority, other_has_handler)
        else self_evaluates))
    # post-conditions-end
    # impl-start
    if resolved_by_right(self_priority, other_priority, other_has_handler):
        return other_evaluates
    return self_evaluates
    # impl-end


def polynomial_priority() -> float:
    # pre-conditions-start
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # A polynomial's selection attribute is strictly greater than the baseline
    # value an ordinary expression carries, by a margin no smaller than the
    # resolution of the runtime scalar carrier at the baseline's magnitude
    # (1e-15 at a baseline of 10.0). A margin-free strict order over the
    # interpreted reals would admit attribute values whose distance above the
    # baseline lies beneath that resolution; such a value collapses onto the
    # baseline when materialized as the executable's finite-precision scalar,
    # the comparison becomes a tie, and the selection rule no longer picks the
    # polynomial's (computing) contribution. The margin guarantees the strict
    # order survives materialization, so the selection rule picks the
    # polynomial for the product covered by the desired behaviour.
    Ensures(Result() >= default_priority() + 1e-15)
    # post-conditions-end
    # impl-start
    # PRE-PATCH: a polynomial carries the same baseline selection attribute an
    # ordinary expression does, rather than one strictly greater, so the
    # selection rule never picks the polynomial's computing contribution for the
    # product covered by the desired behaviour.
    return 10.0
    # impl-end


def generic_times_polynomial() -> bool:
    # pre-conditions-start
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # The required behaviour: the product of a generic expression and a
    # polynomial comes out as the computed polynomial product (reported True).
    # The impl below does not assert this constant directly; it derives the
    # value by running the constant selection rule on the two operands' modelled
    # attributes, and that derivation reaches True only because the polynomial's
    # attribute strictly exceeds the baseline. The discriminating property is
    # carried by polynomial_priority's postcondition, which is where the change
    # under specification lives.
    Ensures(Result() == True)
    # post-conditions-end
    # impl-start
    # The generic operand carries the baseline selection attribute, and its own
    # contribution to a product with a polynomial is NOT the computed product
    # (it would leave an unsimplified expression) -> left_evaluates False.
    left_priority = default_priority()
    left_evaluates = False
    # The polynomial operand is able to contribute (the boolean is True), its
    # contribution IS the computed product (right_evaluates True), and it
    # carries the polynomial selection attribute.
    right_priority = polynomial_priority()
    right_evaluates = True
    # Had the two operands carried the same attribute (no strict order, so the
    # first operand contributes), the outcome would be the unsimplified
    # expression: the generic operand does not itself compute the product. This
    # pins the generic operand as non-computing, so the computed result below is
    # attributable to the polynomial being selected, not to the generic operand.
    Assert(product_is_evaluated(left_priority, left_evaluates,
                                left_priority, right_evaluates, True)
           == False)
    # With the polynomial's attribute strictly greater and it being able to
    # contribute, the selection rule picks the polynomial and the product comes
    # out computed.
    return product_is_evaluated(left_priority, left_evaluates,
                                right_priority, right_evaluates, True)
    # impl-end
