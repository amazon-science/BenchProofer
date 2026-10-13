#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-22080.

The model's two deep encodings are A-references (validated == the real callees,
not consumed as axioms). This script runs the REAL sympy code-style printer and
its precedence machinery (in the patched / gold-resolved container) and asserts
that every observation matches the model in `model.py`:

  (A-reference 1) `remainder_operand_level()` (model.py) == the binding
      strength the real `precedence` table assigns to a remainder/modulo node:
        precedence(Mod(a, b)) == PRECEDENCE["Mul"].

  (A-reference 2) the single-factor leading-minus parenthesization
      (`negated_single_operand_enclosed` / `leading_minus_cutoff` / `encloses`,
      model.py) == the real printer's behaviour:
        * the threshold the renderer applies for the one negated factor is
          0.5*(PRECEDENCE["Pow"] + PRECEDENCE["Mul"]) -- strictly between
          multiplication and exponentiation; and
        * the printer wraps the factor iff its own precedence is <= that
          threshold (the default, non-strict `parenthesize` predicate).

The check is performed at the STRUCTURAL level the model decides (does the
rendered text wrap the operand in parentheses?), computed from each operand's
REAL precedence and compared against the REAL printer output -- no value-proxy
double-mask. The three FAIL_TO_PASS rendering cases are exercised explicitly and
the script fails loudly if any is skipped.

Imports only `sympy` -- the project under test, the very code the gold patch
edits. Exit 0 iff every obligation holds.
"""
import sys

from sympy import Mod, symbols, sin, cos, Mul, Pow, Add, ccode, Symbol
from sympy.printing.pycode import PythonCodePrinter
from sympy.printing.precedence import PRECEDENCE, precedence
from sympy.codegen.rewriting import optimize, create_expand_pow_optimization

# --- model.py reference encodings (kept in lock-step with the spec) ----------

PREC_ADD = 40
PREC_MUL = 50
PREC_POW = 60
PREC_FUNC = 70


def model_leading_minus_cutoff():
    """model.py leading_minus_cutoff(): integer midpoint of Mul and Pow."""
    return (PREC_POW + PREC_MUL) // 2  # 55


def model_encloses(operand_strength, threshold, strict):
    """model.py wraps(): wrap iff binds strictly weaker, or (non-strict) equal."""
    if operand_strength < threshold:
        return True
    if not strict:
        return operand_strength <= threshold
    return False


def model_negated_single_operand_enclosed(factor_strength):
    """model.py negated_single_operand_enclosed()."""
    return model_encloses(factor_strength, model_leading_minus_cutoff(), False)


# --- helpers -----------------------------------------------------------------

def is_parenthesized(rendered, inner):
    """Did the printer wrap `inner` in parentheses inside `rendered`?
    We detect the parenthesized form `(inner)` vs the bare `inner`."""
    return ("(" + inner + ")") in rendered


def main():
    x, y = symbols('x y')
    i = Symbol('i', integer=True)
    p = PythonCodePrinter()

    # ---- constants sanity: the model's named strengths match the real table.
    assert PRECEDENCE["Add"] == PREC_ADD, PRECEDENCE["Add"]
    assert PRECEDENCE["Mul"] == PREC_MUL, PRECEDENCE["Mul"]
    assert PRECEDENCE["Pow"] == PREC_POW, PRECEDENCE["Pow"]
    assert PRECEDENCE["Func"] == PREC_FUNC, PRECEDENCE["Func"]

    # ---- A-reference 1: remainder/modulo binding strength == Mul. -----------
    real_mod_strength = precedence(Mod(x, y))
    assert real_mod_strength == PREC_MUL, (
        "remainder strength A-reference unsound: precedence(Mod) gave %r, "
        "model says %r" % (real_mod_strength, PREC_MUL))
    # ... and the model's structural consequences hold against the real value.
    assert PREC_ADD < real_mod_strength < PREC_POW, real_mod_strength

    # ---- A-reference 2a: the unary-minus threshold the real printer applies
    #      is strictly between multiplication and exponentiation. -------------
    real_threshold = 0.5 * (PRECEDENCE["Pow"] + PRECEDENCE["Mul"])
    assert PRECEDENCE["Mul"] < real_threshold < PRECEDENCE["Pow"], real_threshold
    # the model's integer midpoint reproduces the real threshold exactly.
    assert model_leading_minus_cutoff() == real_threshold, (
        "unary-minus threshold A-reference unsound: real %r, model %r"
        % (real_threshold, model_leading_minus_cutoff()))

    # ---- A-reference 2b: for every realistic operand strength, the model's
    #      wrap decision == the real printer's, checked structurally on a
    #      genuine single-factor leading-minus rendering. ---------------------
    #
    # Build one negated single-numerator-factor expression per strength class:
    #   remainder operand  (strength 50)  -> -Mod(x, y)
    #   product   operand  (strength 50)  -> ccode-expanded -x**4  (Mul factor)
    #   power     operand  (strength 60)  -> -x**3
    #   function  operand  (strength 70)  -> -sin(x)
    cases = []

    # remainder operand: structural check on PythonCodePrinter output.
    rendered = p.doprint(-Mod(x, y))
    factor_strength = precedence(Mod(x, y))
    observed_wrap = is_parenthesized(rendered, "x % y")
    cases.append(("-Mod(x,y)", rendered, factor_strength, observed_wrap, "x % y"))

    # power operand: -x**3  (factor Pow, strength 60, must stay bare).
    rendered = p.doprint(-x**3)
    factor_strength = precedence(x**3)
    observed_wrap = is_parenthesized(rendered, "x**3")
    cases.append(("-x**3", rendered, factor_strength, observed_wrap, "x**3"))

    # function operand: -sin(x)  (factor Function, strength 70, must stay bare).
    rendered = p.doprint(-sin(x))
    factor_strength = precedence(sin(x))
    observed_wrap = is_parenthesized(rendered, "math.sin(x)")
    cases.append(("-sin(x)", rendered, factor_strength, observed_wrap,
                  "math.sin(x)"))

    for name, rendered, strength, observed_wrap, inner in cases:
        predicted = model_negated_single_operand_enclosed(strength)
        assert predicted == observed_wrap, (
            "single-factor wrap A-reference unsound on %s: factor strength %r, "
            "model predicts wrap=%r, real printer rendered %r (wrap=%r)"
            % (name, strength, predicted, rendered, observed_wrap))

    # product operand via the C printer pow-expansion path (factor is an
    # unevaluated Mul of strength 50, must be wrapped): structural on ccode.
    cc = lambda e: ccode(optimize(e, [create_expand_pow_optimization(4)]))
    rendered = cc(-x**4)
    assert is_parenthesized(rendered, "x*x*x*x"), (
        "product-factor wrap A-reference unsound: ccode(-x**4 expanded) = %r, "
        "model requires the product factor (strength 50 <= 55) wrapped"
        % rendered)
    # the inner product's real precedence is indeed 50 and the model wraps it.
    assert model_negated_single_operand_enclosed(PREC_MUL) is True

    # ---- The three FAIL_TO_PASS rendering observations, asserted verbatim. ---
    f2p = []

    # test_PythonCodePrinter
    assert p.doprint(-Mod(x, y)) == '-(x % y)', p.doprint(-Mod(x, y))
    f2p.append("doprint(-Mod(x,y)) == '-(x % y)'")
    assert p.doprint(Mod(-x, y)) == '(-x) % y', p.doprint(Mod(-x, y))
    f2p.append("doprint(Mod(-x,y)) == '(-x) % y'")
    assert p.doprint(Mod(x, 2)) == 'x % 2', p.doprint(Mod(x, 2))
    f2p.append("doprint(Mod(x,2)) == 'x % 2'  (regression guard)")

    # test_create_expand_pow_optimization
    assert cc(-x**4) == '-(x*x*x*x)', cc(-x**4)
    f2p.append("ccode(-x**4) == '-(x*x*x*x)'")
    assert cc(x**4 - x**2) == '-(x*x) + x*x*x*x', cc(x**4 - x**2)
    f2p.append("ccode(x**4 - x**2) == '-(x*x) + x*x*x*x'")
    assert cc(x**i - x**2) == 'pow(x, i) - (x*x)', cc(x**i - x**2)
    f2p.append("ccode(x**i - x**2) == 'pow(x, i) - (x*x)'")

    if len(f2p) != 6:
        print("G-AX FAIL: not all FAIL_TO_PASS rendering cases exercised")
        return 1

    print("G-AX OK: remainder strength == PRECEDENCE['Mul']; unary-minus "
          "threshold strictly between Mul and Pow and == model midpoint; "
          "single-factor wrap decision == real printer on %d strength classes; "
          "all 6 FAIL_TO_PASS rendering observations verbatim."
          % len(cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
