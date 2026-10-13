#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-20801.

This bundle consumes NO `@ContractOnly` axiom: the modeled function's behaviour
is the dispatch over the operand's kind, modeled DEEPLY (spelled out in
model.py's `float_equals` over a kind code plus the operand's truth value and a
per-kind numeric-equality decision). There is no unchanged opaque callee whose
`Ensures` the proof relies on.

What G-AX validates here is the DEEP MODEL itself (an A-reference): for each
operand kind the model distinguishes, the real `Float.__eq__` of the post-patch
repository agrees with the model's verdict, when the model is fed the SAME
observations the real code reads (the operand's kind, its truth value, and the
numeric-equality sub-decision the real code computes for the numeric kinds).

Concretely, for a battery of representative operands it:

  * classifies the operand into the model's kind code (0..6);
  * computes `other_truthy` = bool(other) and `numeric_eq` = the kind-proper
    numeric comparison the real code performs (delegated `other.__eq__(self)`
    for the rational kinds, exact mpf compare for the float / other-number
    kinds);
  * runs the model's `float_equals(self_is_zero, kind, other_truthy,
    numeric_eq)`;
  * runs the REAL `Float.__eq__` (i.e. `self == other` and the swapped form);
  * asserts the model verdict equals the real verdict — in particular for the
    truth-value kind it asserts the verdict is False even when the float is
    zero, which is the behaviour the issue demands.

It imports only `sympy` (the repository under test) and the standard library.
Exit 0 iff every observation matches the model.

G-AX INVOCATION: this script models the *fixed* `Float.__eq__`, so it must run
on the POST-PATCH worktree (apply_gold=True). At base_commit it correctly FAILS,
because the base repository is the buggy code the gold patch corrects.
"""
import sys


# --- model.py reference dispatch (kept in lock-step with float_equals) -------

def model_float_equals(self_is_zero, kind, other_truthy, numeric_eq):
    if kind == 0:
        return False
    if kind == 1:
        return False
    if kind in (2, 3, 4, 5):
        return numeric_eq
    if self_is_zero:
        return not other_truthy
    return False


def classify(self, other):
    """Reproduce the model's kind code from the operand, reading exactly the
    facets the real dispatch reads (mapping.md §1)."""
    from sympy.logic.boolalg import Boolean
    if isinstance(other, Boolean):
        return 0
    if getattr(other, "is_NumberSymbol", False):
        if getattr(other, "is_irrational", False):
            return 1          # named constant known irrational (is_irrational True)
        return 2              # named constant not known irrational (is_irrational
                              # False or None, e.g. Catalan/EulerGamma) -> delegates
    if getattr(other, "is_Float", False):
        return 3              # another floating value (mpf compare)
    if getattr(other, "is_Rational", False):
        return 4              # rational number (delegates)
    if getattr(other, "is_Number", False):
        return 5              # any other number (mpf compare)
    return 6                  # none of the above


def numeric_decision(self, other, kind):
    """The kind-proper numeric-equality sub-decision the real code computes for
    the numeric kinds (an unchanged sub-decision; the model carries its result
    opaquely). Computed from the real operands so the check is faithful."""
    import mpmath.libmp as mlib
    if kind in (2, 4):
        # named constant not known irrational / rational number: delegate to
        # other.__eq__.
        return bool(other.__eq__(self))
    if kind == 3:
        # another floating value: exact mpf compare.
        return self._mpf_ == other._mpf_
    if kind == 5:
        # any other number: compare mpf tuples at self's precision.
        ompf = other._as_mpf_val(self._prec)
        return bool(mlib.mpf_eq(self._mpf_, ompf))
    return False


def check(self, other):
    kind = classify(self, other)
    self_is_zero = (not self)
    other_truthy = bool(other)
    numeric_eq = numeric_decision(self, other, kind)
    modeled = model_float_equals(self_is_zero, kind, other_truthy, numeric_eq)
    real = bool(self.__eq__(other))
    assert modeled == real, (
        "deep dispatch model unsound for self=%r other=%r (kind=%d, "
        "self_is_zero=%s, other_truthy=%s, numeric_eq=%s): model=%s real=%s"
        % (self, other, kind, self_is_zero, other_truthy, numeric_eq,
           modeled, real))
    return kind


def main():
    from sympy import S, Float, Integer, Rational, pi, E, GoldenRatio
    from sympy import Catalan, EulerGamma
    from sympy import sqrt, Symbol, I, Tuple, oo, zoo, nan

    # A battery of (self_float, operand) pairs covering every kind, including
    # the discriminating truth-value-vs-zero case the issue is about.
    selves = [Float(0.0), Float(0), Float(2.0), Float(-3.5), Float(1),
              Float("0.1", 3), Float(1e10)]
    operands = [
        S.true, S.false,                 # kind 0 (truth values)
        pi, E,                           # kind 1 (irrational named const)
        GoldenRatio,                     # kind 1 (irrational named const)
        Catalan, EulerGamma,             # kind 2 (NumberSymbol, is_irrational is None -> delegates)
        Integer(0), Integer(2), Integer(-3),  # kind 4 (rational number)
        Rational(1, 2), Rational(7, 2),  # kind 4
        Float(0.0), Float(2.0), Float(-3.5),  # kind 3 (float)
        oo, -oo, nan,                    # kind 5 (other number: is_Number, not Float/Rational)
        sqrt(2),                         # kind 6 (not is_Number)
        I, zoo,                          # kind 6 (not is_Number)
        Symbol("x"),                     # kind 6 (not a number)
        Tuple(1, 2),                     # kind 6
    ]

    seen_kinds = set()
    n = 0
    for s in selves:
        for o in operands:
            seen_kinds.add(check(s, o))
            n += 1

    # Explicit witnesses of the four assertions the issue/test names.
    assert (S(0.0) == S.false) is False
    assert (S.false == S(0.0)) is False
    assert (S(0) == S.false) is False
    assert (S.false == S(0)) is False
    # And the truth-value kind is False even for a zero float (model kind 0
    # path, self_is_zero=True): the heart of the fix.
    assert model_float_equals(True, 0, bool(S.false), False) is False
    assert model_float_equals(True, 0, bool(S.true), False) is False

    print("G-AX OK: deep dispatch model == real Float.__eq__ on %d operand "
          "pairs covering kinds %s; 4 issue witnesses hold; no consumed axiom"
          % (n, sorted(seen_kinds)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
