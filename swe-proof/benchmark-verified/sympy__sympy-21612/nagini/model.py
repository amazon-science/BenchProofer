"""Twin-artifact model for sympy__sympy-21612.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A quotient is rendered as a numerator followed by a sequence of denominator
  factors joined by the division operator. To keep the rendered text from being
  misread as iterated left-to-right division, each denominator factor that is
  itself a *composite* reciprocal must be wrapped in brackets; a factor that is
  a single atomic symbol is left bare.

  A denominator factor is "composite" exactly when BOTH of the following hold:

    (1) the reciprocated quantity is built from more than one part (its part
        count differs from one); and
    (2) that quantity's structural form is a multiplicative or a power form
        (i.e. a product of factors, or a base raised to an exponent) rather
        than a bare atom.

  When both hold the factor is bracketed; otherwise it is not. The decision is
  taken independently for every denominator factor, and the result is the list
  of per-factor bracket flags in factor order.

Each denominator factor is modelled as a minimal class carrying only the two
touched facets used by the decision: the part count of the reciprocated
quantity (a non-negative int) and an integer tag for its structural form
(0 = atomic, 1 = product, 2 = power). The element payload is irrelevant to the
bracketing behaviour under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Factor:
    """A single denominator factor, abstracted to the two facets the bracketing
    decision inspects: ``parts`` (the part count of the reciprocated quantity)
    and ``form`` (its structural form tag: 0 atomic, 1 product, 2 power)."""

    def __init__(self, parts: int, form: int) -> None:
        Requires(parts >= 0 and form >= 0)
        Ensures(Acc(self.parts) and self.parts == parts)   # type: ignore
        Ensures(Acc(self.form) and self.form == form)       # type: ignore
        self.parts = parts
        self.form = form


# axioms-start
# (no @ContractOnly axioms: the structural-form test and the part-count test
#  the decision performs are modelled deeply as integer/boolean reasoning over
#  the abstracted facets — see refinement.md, all rows are R or I.)
# axioms-end


# pure-start
@Pure
def is_composite_form(form: int) -> bool:
    """A structural form is composite when it is a product (1) or a power (2).
    A bare atom (0) is not composite. This is the form test used by the
    bracketing decision."""
    return form == 1 or form == 2


@Pure
def needs_brackets(parts: int, form: int) -> bool:
    """A denominator factor is bracketed exactly when its reciprocated quantity
    has more than one part AND its form is composite."""
    return parts != 1 and is_composite_form(form)
# pure-end


def bracket_flags(factors: List[Factor]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
        [[factors[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
        [[factors[k]]])))
    Ensures(Acc(list_pred(Result())))
    # One flag per factor, in factor order.
    Ensures(len(Result()) == len(factors))
    # Each flag is the per-factor bracketing decision: bracket exactly when the
    # reciprocated quantity has more than one part and a composite (product or
    # power) form.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Result()[k] == needs_brackets(factors[k].parts, factors[k].form)),
        [[Result()[k]], [factors[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = 0
    while i < len(factors):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
            Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
            [[factors[k]]])))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(factors))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == needs_brackets(factors[k].parts, factors[k].form)),
            [[result[k]], [factors[k]]])))
        Invariant(MustTerminate(len(factors) - i + 1))
        # invariants-end
        f = factors[i]
        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
        result.append(flag)
        i = i + 1
    return result
    # impl-end
