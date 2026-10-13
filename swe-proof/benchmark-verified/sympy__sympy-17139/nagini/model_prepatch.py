"""Twin-artifact model for sympy__sympy-17139.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A node transformer rewrites a power of a designated base function
  (``base ** exponent``) into an equivalent trigonometric form, but only when
  the exponent is an ordinary real number on which the ordering predicates
  ``exponent < 0`` and ``exponent > max`` are meaningful. The ordering of a
  symbolic quantity against a real bound is only defined when that quantity is
  itself real; ordering a genuinely complex (non-real) quantity against a real
  number is undefined and must never be attempted.

  Therefore, for a power whose exponent is NOT real, the transformer must leave
  the node unchanged and must not evaluate any ordering of that exponent. Only
  for a real exponent may the transformer test the sign / magnitude of the
  exponent and then dispatch on its integer magnitude.

  For an in-range real exponent the dispatch reproduces the established rewrite
  selection: the first-power magnitude is left unchanged and the squared case is
  special (its own form); the fourth-power case is always rewritten. For the
  remaining magnitudes, when the caller admits every even power (``pow`` false)
  only an even magnitude is rewritten while an odd magnitude is left unchanged;
  when the caller restricts to perfect powers (``pow`` true) the magnitude is
  rewritten exactly when it is a perfect power, otherwise the node is left
  unchanged.

The exponent is modelled by a minimal carrier class with the two touched
attributes: whether it is real, and (when real) its integer value. The two
ordering predicates against the exponent are unchanged library operations whose
SAFE DOMAIN is the real exponents; they are axiomatized (`@Pure @ContractOnly`)
with that domain as their precondition, mirroring that the real comparison
raises a TypeError on a non-real operand. The perfect-power test on the integer
magnitude is likewise an unchanged library predicate, modelled as an
(A-reference) pure callee validated against the real predicate. The transformer
dispatch itself is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Expon:
    """The exponent of the power node under inspection: only the two attributes
    the transformer touches are modelled.

      - ``real``  : the exponent is a real quantity (its ordering against a real
                    bound is defined). For a genuinely complex exponent this is
                    False and no ordering may be evaluated.
      - ``value`` : the integer magnitude used by the rewrite dispatch; only
                    meaningful (and only read) when ``real`` holds.
    """

    def __init__(self, real: bool, value: int) -> None:
        self.real = real      # type: bool
        self.value = value    # type: int
        Ensures(Acc(self.real) and Acc(self.value))
        Ensures(self.real == real and self.value == value)


# axioms-start
@Pure
@ContractOnly
def order_lt_zero(e: Expon) -> bool:
    """The ordering predicate ``exponent < 0``. This is an UNCHANGED library
    operation; its safe (non-raising) domain is the real exponents, so it is
    Required real. (Provenance + executable soundness check: mapping.md /
    axiom_check.py.) On a real exponent it is True iff the exponent value is
    negative."""
    Requires(Acc(e.real, 1 / 4) and Acc(e.value, 1 / 4))
    Requires(e.real)
    Ensures(Result() == (e.value < 0))


@Pure
@ContractOnly
def order_gt_max(e: Expon, m: int) -> bool:
    """The ordering predicate ``exponent > max``. Unchanged library operation;
    safe domain is the real exponents (Required real). On a real exponent it is
    True iff the exponent value exceeds the bound ``m``."""
    Requires(Acc(e.real, 1 / 4) and Acc(e.value, 1 / 4))
    Requires(e.real)
    Ensures(Result() == (e.value > m))


@Pure
@ContractOnly
def is_perfect_power(n: int) -> bool:
    """Whether the non-negative integer magnitude ``n`` is a perfect power
    (some integer base raised to an integer exponent >= 2). Unchanged library
    predicate; modelled as a pure callee whose value is validated against the
    real predicate (A-reference, axiom_check.py / G-AX). For the even, non-2,
    non-4 magnitudes the dispatch keys on it; the only fact the proof needs is
    that it is a deterministic function of ``n`` (the dispatch branches on its
    boolean value), which `@Pure` already guarantees, so no value is claimed
    here beyond that."""
    Requires(n >= 0)
# axioms-end


# pure-start
# (no module-level pure helpers required)
# pure-end


def transform_power(is_target: bool, exp: Expon, max: int, pow: bool) -> int:
    """Inspect a node and report which rewrite branch fires, as a result code:

        0  -> the node is returned UNCHANGED
        1  -> rewritten via the squared-base case (exponent magnitude == 2)
        2  -> rewritten via the general power case

    ``is_target`` is whether the node is a power of the designated base
    function (only such nodes are eligible). ``pow`` selects whether only
    magnitudes that are perfect powers are admitted among the even cases. The
    exponent ``exp`` is read only; its ordering may be evaluated solely when it
    is real.
    """
    # pre-conditions-start
    Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
    Requires(max >= 4)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
    # A non-eligible node is unchanged.
    Ensures(Implies(not is_target, Result() == 0))
    # The discriminating guarantee: a power with a NON-REAL exponent is left
    # unchanged (no ordering of that exponent is ever attempted).
    Ensures(Implies(is_target and not exp.real, Result() == 0))
    # A real, negative, or over-large exponent leaves the node unchanged.
    Ensures(Implies(is_target and exp.real and exp.value < 0, Result() == 0))
    Ensures(Implies(is_target and exp.real and exp.value > max, Result() == 0))
    # A real first-power magnitude is left unchanged.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 1, Result() == 0))
    # The squared-base case rewrites via the squared form (result code 1).
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 2, Result() == 1))
    # The fourth-power case is always rewritten (code 2), independent of ``pow``.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 4, Result() == 2))
    # When every even power is admitted (``pow`` false), an in-range magnitude
    # other than the first-power, squared and fourth-power cases is rewritten
    # exactly when it is even; an odd magnitude is left UNCHANGED.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and not pow
        and exp.value % 2 == 1, Result() == 0))
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and not pow
        and exp.value % 2 == 0, Result() == 2))
    # Under ``pow`` an in-range magnitude other than the first-power, squared and
    # fourth-power cases is rewritten exactly when it is a perfect power,
    # otherwise (whatever its parity) it is left UNCHANGED.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and pow
        and is_perfect_power(exp.value), Result() == 2))
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and pow
        and not is_perfect_power(exp.value), Result() == 0))
    # The result is always one of the three branch tags.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # post-conditions-end
    # impl-start
    if not is_target:
        return 0
    if order_lt_zero(exp) == True:
        return 0
    if order_gt_max(exp, max) == True:
        return 0
    if exp.value == 1:
        return 0
    if exp.value == 2:
        return 1
    else:
        if exp.value == 4:
            return 2
        elif not pow:
            if exp.value % 2 == 1:
                return 0
            return 2
        else:
            if not is_perfect_power(exp.value):
                return 0
            return 2
    # impl-end
