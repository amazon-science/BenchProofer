#!/usr/bin/env python3
"""G-CONF differential conformance for sympy__sympy-13091.

Refutes the R/I refinement leg: the modeled equality verdict (`eqResult`), the
`==` operator dispatch (`resolveEq`), and inequality (`neResult`) from
Solution.lean, over the finite input space `Operand × Verdict`.

ORACLE CHOICE — why we transliterate the patched protocol instead of driving
`Basic.__eq__`/`__ne__` end-to-end:
  The fix is to CPython's rich-comparison dispatch: `__eq__` returns the
  `NotImplemented` singleton for a foreign operand, and `__ne__` negates the
  `==` OPERATOR (which delegates to the operand's reflected `__eq__`) rather than
  the raw `__eq__` method. Driving the real `Basic`/`Number` objects would require
  constructing sympy instances and a foreign companion class whose reflected
  `__eq__` returns each of True / False / NotImplemented — which is exactly the
  `Foo`/`Bar` scaffolding the F2P tests already build. Rather than re-run sympy's
  whole comparison stack to read back one boolean, the ORACLE is the PATCHED
  protocol transliterated VERBATIM from the post-image of `__eq__`/`__ne__` plus
  the documented CPython `==` dispatch
  (https://docs.python.org/3/reference/datamodel.html#object.__eq__). The SHADOW
  is the modeled `eqResult`/`resolveEq`/`neResult` from Solution.lean.

  We differential-test SHADOW vs ORACLE over the full finite input space
  (Operand × Verdict = 9 combinations) plus seeded fuzz. Exit 0 iff zero
  disagreements. stdlib only.
"""
import random
import sys

SEED = 13091
N_FUZZ = 100_000

# The three operand shapes (mapping.md §2): _sympify rejects it / sympifies-equal
# / sympifies-but-differs.
OPERANDS = ["foreign", "matchingEqual", "matchingUnequal"]

# The three comparison outcomes: True / False / NotImplemented singleton.
VERDICTS = ["isTrue", "isFalse", "undecided"]

IS_TRUE, IS_FALSE, UNDECIDED = "isTrue", "isFalse", "undecided"


# ---- SHADOW: transliterated from Solution.lean's pure region ----------------

def shadow_eqResult(operand):
    """`eqResult : Operand -> Verdict` (Solution.lean)."""
    return {
        "foreign": UNDECIDED,
        "matchingEqual": IS_TRUE,
        "matchingUnequal": IS_FALSE,
    }[operand]


def shadow_resolveEq(selfV, reflectedV):
    """`resolveEq : Verdict -> Verdict -> Bool` (Solution.lean)."""
    if selfV == IS_TRUE:
        return True
    if selfV == IS_FALSE:
        return False
    # selfV == UNDECIDED: delegate to the reflected verdict.
    if reflectedV == IS_TRUE:
        return True
    if reflectedV == IS_FALSE:
        return False
    return False  # both undecided -> identity fallback -> False


def shadow_eq(operand, reflectedV):
    """The `==` operator decision (equalityCompare post-image)."""
    return shadow_resolveEq(shadow_eqResult(operand), reflectedV)


def shadow_ne(operand, reflectedV):
    """The `!=` operator decision (inequalityCompare post-image): neResult."""
    return not shadow_resolveEq(shadow_eqResult(operand), reflectedV)


# ---- ORACLE: the PATCHED protocol, transliterated verbatim ------------------

# A sentinel object standing in for Python's NotImplemented (so we exercise the
# real `not NotImplemented is False` trap that motivated behaviour B).
NotImpl = object()


def py_dunder_eq(operand):
    """Post-image `__eq__`: returns a bool, or NotImpl for a foreign operand.

        try: other = _sympify(other)
        except SympifyError: return NotImplemented   # was: return False
        ... return self._hashable_content() == other._hashable_content()
    """
    if operand == "foreign":
        return NotImpl                  # patched line
    if operand == "matchingEqual":
        return True
    return False                        # matchingUnequal: type/content mismatch


def reflected_to_pyobj(reflectedV):
    """The foreign operand's reflected `__eq__(self)` outcome as a Python value."""
    if reflectedV == IS_TRUE:
        return True
    if reflectedV == IS_FALSE:
        return False
    return NotImpl


def py_operator_eq(operand, reflectedV):
    """CPython `a == b` dispatch (datamodel rich comparison).

    Try a.__eq__(b); if NotImplemented, try b.__eq__(a) (the reflected verdict);
    if that is also NotImplemented, fall back to identity `a is b`, which is False
    for the distinct objects in the tests.
    """
    left = py_dunder_eq(operand)
    if left is not NotImpl:
        return bool(left)
    right = reflected_to_pyobj(reflectedV)
    if right is not NotImpl:
        return bool(right)
    return False                        # identity fallback


def py_operator_ne(operand, reflectedV):
    """Post-image `__ne__`: `return not self == other`.

    Note it negates the OPERATOR (py_operator_eq), not `not py_dunder_eq(...)`
    (which would do `not NotImplemented` -> False, the pre-patch bug).
    """
    return not py_operator_eq(operand, reflectedV)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    combos = [(o, v) for o in OPERANDS for v in VERDICTS]            # 9 exhaustive
    combos += [(rng.choice(OPERANDS), rng.choice(VERDICTS))          # + fuzz
               for _ in range(N_FUZZ)]

    for operand, reflectedV in combos:
        count += 1
        # behaviour A + dispatch: the `==` operator result.
        if shadow_eq(operand, reflectedV) != py_operator_eq(operand, reflectedV):
            disagreements.append(("==", operand, reflectedV,
                                  shadow_eq(operand, reflectedV),
                                  py_operator_eq(operand, reflectedV)))
        # behaviour B: the `!=` operator result.
        if shadow_ne(operand, reflectedV) != py_operator_ne(operand, reflectedV):
            disagreements.append(("!=", operand, reflectedV,
                                  shadow_ne(operand, reflectedV),
                                  py_operator_ne(operand, reflectedV)))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of the NotImplemented-aware ==/!= dispatch "
          "agrees with the patched protocol on %d inputs (9 exhaustive + fuzz, "
          "seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
