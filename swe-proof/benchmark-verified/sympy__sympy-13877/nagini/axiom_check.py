#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13877.

Validates the single kind-A obligation of the bundle:

  (A-reference) the deep model `is_genuinely_zero` (model.py pure region) equals
      the REAL mathematical zero test the fix introduces,
      `_is_zero_after_expand_mul(x)  ==  (expand_mul(x) == 0)`
      (sympy/matrices/matrices.py post-patch, wrapping sympy.core.function.
      expand_mul). model.py encodes each column entry as an integer status code
      (mapping.md §2):
          code == 0   -> a literal/atomic zero            (is_genuinely_zero True)
          code  > 0   -> a genuinely non-zero expression  (is_genuinely_zero False)
          code  < 0   -> a *pseudo-zero*: structurally non-trivial yet exactly
                         zero (e.g. p/q with numerator expanding to
                         0)                                (is_genuinely_zero True)
      For every representative SymPy entry of each class we run the REAL callee
      and assert it agrees with `is_genuinely_zero(code)`:
          is_genuinely_zero(code) == (expand_mul(entry) == 0)

  We ALSO confirm the bug-distinguishing fact the spec hinges on: the pre-patch
  test (Python truthiness `bool(entry)`, i.e. `entry != 0` structurally) and the
  fixed test DISAGREE exactly on the pseudo-zero class — pseudo-zeros are
  truthy (so the old `_find_pivot` would wrongly accept them) yet vanish after
  expand_mul (so the fixed finder correctly rejects them). This is the witness
  that the modeled discriminator is the real one.

Imports nothing repo-specific beyond `sympy` itself — the very package the gold
patch lives in. Exit 0 iff every obligation holds.
"""
import sys

from sympy import symbols, expand_mul, S, Integer, sqrt, sin, cos, exp


def _is_zero_after_expand_mul(x):
    """The exact real callee added by the gold patch."""
    return expand_mul(x) == 0


def is_genuinely_zero_model(code):
    """Reference implementation of model.py's deep model `is_genuinely_zero`."""
    return code <= 0


def struct_truthy_real(x):
    """The pre-patch pivot test: Python truthiness `if val:` on a SymPy expr.
    A SymPy zero is falsy; any structurally non-trivial expression is truthy."""
    return bool(x)


def main():
    a, b = symbols('a b')

    # (code, entry, human label)
    cases = []

    # --- code 0 : literal / atomic zeros (vanish; falsy) ------------------
    cases += [
        (0, S.Zero, "S.Zero"),
        (0, Integer(0), "Integer(0)"),
        (0, a - a, "a - a (auto-simplifies to 0)"),
        (0, a * b - b * a, "a*b - b*a (commutative auto-cancel to 0)"),
    ]

    # --- code > 0 : genuinely non-zero entries (do not vanish; truthy) ----
    cases += [
        (1, a, "a"),
        (2, Integer(5), "Integer(5)"),
        (3, a + 1, "a + 1"),
        (4, a * b, "a*b"),
        (5, a ** 2 + 1, "a**2 + 1"),
        (6, sqrt(2), "sqrt(2)"),
        (7, sin(a) + 1, "sin(a) + 1"),
        (8, Integer(-3), "Integer(-3)"),          # negative VALUE, non-zero
    ]

    # --- code < 0 : pseudo-zeros: structurally non-trivial, expand to 0 ---
    # These are the issue's actual bug class: unevaluated products / quotients
    # whose numerator expands to zero over a NON-zero denominator (the shape of
    # a Bareiss elimination entry (pivot*x - y*z)/cumm with cumm != 0). They are
    # bool-truthy (the old _find_pivot accepts them) yet expand_mul(...) == 0
    # (the fix rejects them).
    pz1 = a * (a + 1) - a ** 2 - a                      # == 0 after expand_mul
    pz2 = (a + 1) * (a - 1) - a ** 2 + 1                # == 0 after expand_mul
    # Realistic Bareiss-entry shape: numerator expands to 0 over a non-zero
    # denominator (a prior, genuinely non-zero pivot). The numerator is the
    # issue's own vanishing expression.
    pz3 = (2 * a ** 2 - a * (2 * a + 3) + 3 * a) / (a + 1)
    pz4 = (a * (a + 1) - a ** 2 - a) / a                # 0 / a  (a != 0 pivot)
    cases += [
        (-1, pz1, "a*(a+1) - a**2 - a"),
        (-2, pz2, "(a+1)*(a-1) - a**2 + 1"),
        (-3, pz3, "(2a^2 - a(2a+3) + 3a)/(a+1) [issue numerator / nonzero denom]"),
        (-4, pz4, "(a*(a+1) - a**2 - a)/a [vanishing numerator / nonzero pivot]"),
    ]

    n_pseudo = 0
    for code, entry, label in cases:
        real_zero = _is_zero_after_expand_mul(entry)        # REAL fixed test
        model_zero = is_genuinely_zero_model(code)          # deep model
        assert bool(real_zero) == bool(model_zero), (
            "A-reference UNSOUND on %s: expand_mul-zero=%r but model "
            "is_genuinely_zero(code=%d)=%r" % (label, bool(real_zero), code,
                                               bool(model_zero)))

        # Class-specific structural witnesses.
        if code == 0:
            assert struct_truthy_real(entry) == False, (
                "%s should be falsy (literal zero)" % label)
        elif code > 0:
            assert struct_truthy_real(entry) == True and not real_zero, (
                "%s should be a genuine non-zero (truthy, not expand-zero)"
                % label)
        else:  # pseudo-zero
            n_pseudo += 1
            # The crux: truthy (old test accepts) yet expand-zero (fix rejects).
            assert struct_truthy_real(entry) == True, (
                "%s pseudo-zero must be bool-truthy (so the pre-patch "
                "_find_pivot would wrongly accept it)" % label)
            assert real_zero == True, (
                "%s pseudo-zero must vanish after expand_mul (so the fixed "
                "finder rejects it)" % label)
            # And the two predicates genuinely disagree here:
            assert struct_truthy_real(entry) != (not real_zero), (
                "%s: pre-patch and fixed pivot tests must DISAGREE on a "
                "pseudo-zero" % label)

    assert n_pseudo >= 3, "need >= 3 distinct pseudo-zero witnesses"

    print("G-AX OK: deep model is_genuinely_zero == real expand_mul(x)==0 on "
          "%d entries (%d pseudo-zero witnesses where the pre-patch truthiness "
          "test and the fixed expansion test disagree)." %
          (len(cases), n_pseudo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
