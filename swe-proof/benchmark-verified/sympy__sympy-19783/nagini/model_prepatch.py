"""Twin-artifact model for sympy__sympy-19783.

Behaviour under specification (stated as desired behaviour, not as an edit):

Two binary-product operations on symbolic quantum expressions must absorb the
identity element on both sides.

  (1) Multiplying the identity element on the LEFT by an expression collapses
      to that expression whenever the expression is an operator-like factor
      (a plain operator, the identity itself, or a Hermitian-conjugate factor);
      for any other (e.g. scalar) factor the product is left as an unevaluated
      symbolic product of the two operands. In particular a Hermitian-conjugate
      factor on the right is absorbed, exactly like a plain operator factor.

  (2) Multiplying a Hermitian-conjugate factor on the LEFT by an expression
      collapses to that conjugate factor whenever the expression is the
      identity element; for any other factor the product is left as an
      unevaluated symbolic product of the two operands.

Together these make the identity element a two-sided unit on Hermitian-
conjugate factors: identity*conjugate == conjugate*identity == conjugate.

Each operand is modelled by an integer "kind" tag classifying which family of
symbolic expression it belongs to (operator / identity / conjugate / other);
the membership predicates mirror the real type tests. A product is modelled by
a small ``Product`` record stating whether it stayed an unevaluated symbolic
product and, when it collapsed, the kind of the single surviving operand. The
two operations are read-only on their operands (they construct fresh results),
so the operand records are held at fractional permission.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (No external/unchanged callee is consumed as an axiom. The classification
#  predicates and the product construction are modelled deeply below; their
#  agreement with the real type tests / product is validated by axiom_check.py
#  as A-reference, not consumed.)
# axioms-end


# pure-start
# Operand kind tags (the family a symbolic factor belongs to):
#   0  a plain operator factor                 (operator-like, not a conjugate)
#   1  the identity element                    (operator-like)
#   2  a Hermitian-conjugate factor            (NOT operator-like)
#   3  any other factor (scalar / symbol / ...)(neither)

@Pure
def is_kind(k: int) -> bool:
    """A valid operand kind tag."""
    return 0 <= k and k <= 3


@Pure
def is_operator_like(k: int) -> bool:
    """The operand belongs to the operator family (a plain operator or the
    identity element). The conjugate family is deliberately excluded here."""
    Requires(is_kind(k))
    return k == 0 or k == 1


@Pure
def is_identity(k: int) -> bool:
    """The operand is the identity element."""
    Requires(is_kind(k))
    return k == 1


@Pure
def is_conjugate(k: int) -> bool:
    """The operand is a Hermitian-conjugate factor."""
    Requires(is_kind(k))
    return k == 2
# pure-end


class Product:
    """The result of one binary-product step.

    ``is_mul`` is True when the step left an unevaluated symbolic product of
    two operands (whose kinds are ``left_kind`` and ``right_kind``); it is
    False when the step collapsed to a single surviving operand, whose kind is
    ``result_kind``.
    """

    def __init__(self, is_mul: bool, result_kind: int,
                 left_kind: int, right_kind: int) -> None:
        # pre-conditions-start
        Requires(is_kind(result_kind))
        Requires(is_kind(left_kind))
        Requires(is_kind(right_kind))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_mul) and self.is_mul is is_mul)         # type: ignore
        Ensures(Acc(self.result_kind) and self.result_kind == result_kind)  # type: ignore
        Ensures(Acc(self.left_kind) and self.left_kind == left_kind)        # type: ignore
        Ensures(Acc(self.right_kind) and self.right_kind == right_kind)     # type: ignore
        # post-conditions-end
        self.is_mul = is_mul
        self.result_kind = result_kind
        self.left_kind = left_kind
        self.right_kind = right_kind


def identity_mul(other_kind: int) -> Product:
    """Identity element on the LEFT times an operand of kind ``other_kind``."""
    # pre-conditions-start
    Requires(is_kind(other_kind))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().is_mul) and Acc(Result().result_kind))
    Ensures(Acc(Result().left_kind) and Acc(Result().right_kind))
    # The two operands of this step: identity (kind 1) on the left, the given
    # operand on the right. Recorded unconditionally.
    Ensures(Result().left_kind == 1 and Result().right_kind == other_kind)
    # The product collapses to the right operand exactly when the right operand
    # is operator-like OR a conjugate factor; otherwise it is left unevaluated.
    Ensures(Result().is_mul ==
            (not (is_operator_like(other_kind) or is_conjugate(other_kind))))
    # The surviving operand of the collapse is the right operand: when the step
    # collapses (is_mul False) the result equals exactly that operand.
    Ensures(Result().result_kind == other_kind)
    # post-conditions-end
    # impl-start
    # PRE-PATCH (site 1): only operator-like operands are absorbed; a conjugate
    # factor on the right is NOT absorbed and falls through to an unevaluated
    # product, so identity*conjugate stays unsimplified.
    if is_operator_like(other_kind):
        return Product(False, other_kind, 1, other_kind)
    return Product(True, other_kind, 1, other_kind)
    # impl-end


def dagger_mul(other_kind: int) -> Product:
    """Hermitian-conjugate factor (kind 2) on the LEFT times an operand of kind
    ``other_kind``."""
    # pre-conditions-start
    Requires(is_kind(other_kind))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().is_mul) and Acc(Result().result_kind))
    Ensures(Acc(Result().left_kind) and Acc(Result().right_kind))
    # The two operands of this step: the conjugate factor (kind 2) on the left,
    # the given operand on the right. Recorded unconditionally.
    Ensures(Result().left_kind == 2 and Result().right_kind == other_kind)
    # The product collapses to the (conjugate) left operand exactly when the
    # right operand is the identity element; otherwise it is left unevaluated.
    Ensures(Result().is_mul == (not is_identity(other_kind)))
    # The surviving operand of the collapse is the conjugate factor (kind 2):
    # when the step collapses (is_mul False) the result equals that operand.
    Ensures(Result().result_kind == 2)
    # post-conditions-end
    # impl-start
    if is_identity(other_kind):
        return Product(False, 2, 2, other_kind)
    return Product(True, 2, 2, other_kind)
    # impl-end
