"""Twin-artifact model for sympy__sympy-20801.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Equality of an exact floating value against an already-sympified operand is
  determined by WHAT the operand is. The operand falls into one of a small
  number of kinds, and the equality verdict is determined by that kind:

    * a logical truth value (one of the two symbolic booleans) is NEVER equal to
      a floating value: the result is False, irrespective of the floating
      value — in particular a floating value that happens to be zero is still
      unequal to either symbolic boolean;
    * an irrational named constant is never equal to a floating value (False);
    * a rational named constant, a rational number, or another floating value
      compares by the numeric-equality decision proper to that kind;
    * any other numeric operand compares by the numeric-equality decision;
    * an operand that is none of the above (neither a number nor a logical truth
      value) is equal to the floating value exactly when the floating value is
      zero and the operand is falsy; otherwise the result is False.

The operand is abstracted by an integer kind code over these cases; two further
observations of the operand are carried explicitly: its truth value, and, for
the numeric kinds, the numeric-equality decision (a sub-decision proper to each
numeric kind, supplied as an opaque boolean). The floating value itself is
abstracted by whether it is zero. The result is the equality verdict.

The equality decision MUST terminate (a total-correctness obligation, carried
as MustTerminate in the precondition): the real dispatch is a bounded,
loop-free decision that always returns a verdict. Nagini verifies partial
correctness by default, so without the obligation a diverging implementation
(`while True: pass`) would satisfy every value postcondition vacuously — yet
its real counterpart is a Float.__eq__ that hangs every equality test and
does NOT resolve the instance.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def is_truth_value(kind: int) -> bool:
    """The operand is a symbolic logical truth value (kind 0)."""
    return kind == 0


@Pure
def is_irrational_const(kind: int) -> bool:
    """The operand is an irrational named constant (kind 1)."""
    return kind == 1


@Pure
def is_numeric_kind(kind: int) -> bool:
    """The operand is one of the numeric kinds whose verdict is the
    numeric-equality decision: a rational named constant, another floating
    value, a rational number, or any other number (kinds 2..5)."""
    return kind == 2 or kind == 3 or kind == 4 or kind == 5


@Pure
def is_other_kind(kind: int) -> bool:
    """The operand is none of the above: neither a number nor a logical truth
    value (kind 6)."""
    return kind == 6
# pure-end


def float_equals(self_is_zero: bool, kind: int, other_truthy: bool,
                 numeric_eq: bool) -> bool:
    # pre-conditions-start
    # `kind` ranges over the seven cases the dispatch distinguishes.
    Requires(0 <= kind and kind <= 6)
    # TERMINATION (total correctness): the real Float.__eq__ dispatch is a
    # bounded, loop-free decision — it always returns a verdict. Nagini
    # verifies partial correctness by default, so without this obligation a
    # diverging impl (`while True: pass`) satisfies every value postcondition
    # VACUOUSLY yet its real counterpart hangs every Float equality test
    # (the F2P run times out) and does not resolve. Any loop now needs a
    # decreasing measure; a bare infinite loop is rejected.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # A symbolic logical truth value is never equal to a floating value, even a
    # zero one — the verdict is False regardless of self_is_zero / other_truthy.
    Ensures(Implies(is_truth_value(kind), Result() == False))
    # An irrational named constant is never equal to a floating value.
    Ensures(Implies(is_irrational_const(kind), Result() == False))
    # The numeric kinds defer to the numeric-equality decision proper to them.
    Ensures(Implies(is_numeric_kind(kind), Result() == numeric_eq))
    # An otherwise-uncategorised operand can match only a zero floating value,
    # and then the verdict is the negation of the operand's truth value; a
    # non-zero floating value is unequal to it.
    Ensures(Implies(is_other_kind(kind) and self_is_zero,
                    Result() == (not other_truthy)))
    Ensures(Implies(is_other_kind(kind) and not self_is_zero,
                    Result() == False))
    # post-conditions-end
    # impl-start
    if self_is_zero:
        return not other_truthy
    if kind == 0:
        return False
    if kind == 1:
        return False
    if kind == 2:
        return numeric_eq
    if kind == 3:
        return numeric_eq
    if kind == 4:
        return numeric_eq
    if kind == 5:
        return numeric_eq
    return False
    # impl-end
