"""Twin-artifact model for sympy__sympy-22080.

Behaviour under specification (stated as desired behaviour, not as an edit):

When a value-carrying expression is rendered as source code and the rendering
carries a leading minus sign in front of a single operand, the printed text must
parse back to the same value. Whether that one operand needs to be enclosed in
parentheses is decided by comparing how tightly the operand itself re-binds in
the target syntax against a constant cut-off applied to such a leading-minus
rendering. The result-determining contract is purely observable:

  (1) The enclose/leave-bare decision is monotone in how tightly the operand
      re-binds: an operand that re-binds no more tightly than the cut-off is
      enclosed in parentheses; an operand that re-binds more tightly is left
      bare. (The generic "enclose iff the operand does not re-bind strictly
      tighter than its context" rule.)

  (2) A "%"/remainder operand re-binds exactly as tightly as a "*"/product
      operand, and the cut-off applied to a leading-minus single operand sits
      above that level but below a "**"/power operand. Consequently a
      remainder operand and a product operand are both enclosed, while a power
      operand and a function-call operand are left bare. In particular a
      leading-minus remainder operand is enclosed, so e.g. negating a "%"
      expression renders as "-(... % ...)" rather than "-... % ..." and parses
      back to the negated remainder.

The re-binding levels are modelled as small ordered integers (additive <
multiplicative < power < function-call) — just an order-preserving carrier for
the comparisons the contract makes; nothing depends on their exact values, only
on the ordering, so an integer carrier is exact (refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axiom is consumed. The re-binding-level ordering and the
#  enclose-in-parentheses rule are modelled deeply in the pure region below and
#  are validated == the real renderer's observable rendering out-of-band by
#  axiom_check.py / G-AX -- A-references, not consumed axioms.)
# axioms-end


# pure-start
@Pure
def level_additive() -> int:
    # re-binding level of an additive ("+"/"-") operand
    return 40


@Pure
def level_multiplicative() -> int:
    # re-binding level of a multiplicative ("*"/"%") operand
    return 50


@Pure
def level_power() -> int:
    # re-binding level of a power ("**") operand
    return 60


@Pure
def level_function() -> int:
    # re-binding level of a function-call operand
    return 70


@Pure
def encloses(operand_level: int, cutoff: int, strict: bool) -> bool:
    """The generic enclose-in-parentheses predicate: a rendered operand is
    enclosed iff it re-binds strictly more loosely than its context, or (in the
    non-strict mode used by default) exactly as loosely. Monotone decreasing in
    `operand_level`."""
    if operand_level < cutoff:
        return True
    if not strict:
        return operand_level <= cutoff
    return False


@Pure
def leading_minus_cutoff() -> int:
    """The cut-off applied to the single operand of a leading-minus rendering.
    It sits above the multiplicative level and below the power level, so a
    leading-minus product- or remainder-level operand is enclosed while a power
    operand need not be -- which is what makes the rendering parse back to the
    intended value."""
    Ensures(level_multiplicative() < Result() and Result() < level_power())
    return (level_power() + level_multiplicative()) // 2
# pure-end


def remainder_operand_level() -> int:
    """The re-binding level of a "%"/remainder operand.

    A remainder operand re-binds exactly as tightly as a "*"/product operand --
    and therefore more loosely than the leading-minus cut-off (so a leading-minus
    remainder operand is enclosed, item (2) above)."""
    # pre-conditions-start
    # total-correctness obligation: the level lookup must actually deliver an
    # answer. The verifier is partial-correctness by default, so without this
    # a diverging body would satisfy the value contract vacuously; the real
    # operation always returns.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # re-binds exactly as tightly as a multiplicative operand ...
    Ensures(Result() == level_multiplicative())
    # ... hence more loosely than a power and more tightly than an additive op.
    Ensures(level_additive() < Result() and Result() < level_power())
    # post-conditions-end
    # impl-start
    return level_multiplicative()
    # impl-end


def negated_single_operand_enclosed(operand_level: int) -> bool:
    """Whether the single operand of a leading-minus rendering is enclosed in
    parentheses, as a function of that operand's own re-binding level.

    The decision compares the operand against the leading-minus cut-off, in the
    default (non-strict) mode.
    """
    # pre-conditions-start
    Requires(level_additive() <= operand_level
             and operand_level <= level_function())
    # total-correctness obligation: the enclose/leave-bare decision must
    # actually be delivered (no diverging body satisfying the value contract
    # vacuously); the real decision procedure always returns.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # the operand is enclosed exactly per the generic rule against the
    # leading-minus cut-off (the default, non-strict mode).
    Ensures(Result() == encloses(operand_level, leading_minus_cutoff(), False))
    # consequences the issue demands, pinned independently of the cut-off's
    # exact value (they hold for ANY cut-off above multiplicative and below
    # power level):
    #   a product / additive / remainder operand (level <= multiplicative) is
    #   enclosed;
    Ensures(Implies(operand_level <= level_multiplicative(), Result() == True))
    #   a power / function operand (level >= power) stays bare.
    Ensures(Implies(operand_level >= level_power(), Result() == False))
    # post-conditions-end
    # impl-start
    return encloses(operand_level, leading_minus_cutoff(), False)
    # impl-end


def negated_remainder_is_enclosed() -> bool:
    """A worked instance: composing the two modelled obligations on a
    leading-minus remainder operand yields an enclosing (so "-(... % ...)"
    parses back correctly).

    Note: this composite is illustrative, not the locus of discrimination. The
    two obligations are each pinned by the standalone functions above
    (`remainder_operand_level` pins the remainder level; `negated_single_
    operand_enclosed` pins the enclose decision against the cut-off), and each
    is what a deviating implementation fails. The result here is a concrete
    `True` consequence and is not load-bearing for sensing the change."""
    # pre-conditions-start
    # total-correctness obligation for the composite: it must deliver its
    # answer. The strictly larger measure (2 > 1) lets it invoke the two
    # standalone obligations above without leaking its own.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == True)
    # post-conditions-end
    # impl-start
    s = remainder_operand_level()
    return negated_single_operand_enclosed(s)
    # impl-end
