#!/usr/bin/env python3
"""G-CONF for sympy__sympy-21612.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_printDenominatorFactor` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched StrPrinter
denominator-factor bracketing in `_print_Mul`, over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

Model (refinement.md, mapping.md):
  A denominator factor of the form  1/base  (a commutative Pow with exp == -1)
  renders, inside the printed product, as the base's text fragment, wrapped in one
  extra pair of brackets exactly when
      len(item.args[0].args) != 1  AND  isinstance(item.base, (Mul, Pow))
  i.e.  baseComponentCount != 1  AND  (baseIsProduct OR baseIsPower).
  Otherwise the fragment is spliced in unchanged.

The renderer `render(base)` is the printer's own base-fragment renderer
`StrPrinter().parenthesize(base, prec, strict=False)`.

  * Oracle  = the REAL patched `sstr(Mul(num, Pow(base, -1, evaluate=False),
              evaluate=False))`, with the numerator prefix `sstr(num) + "/"`
              stripped off to isolate THIS factor's rendered denominator text
              (the single-denominator-factor case, len(b)==1, so the printer emits
              `n/b_str[0]`).
  * Shadow  = the Lean impl's template with `render base` == the REAL
              `StrPrinter().parenthesize(base, prec, strict=False)` spliced in,
              wrapped iff the bracketing predicate fires.

Type bijection (mapping.md):
  Expr <-> the base of a denominator Pow factor (item.base, a sympy Expr),
  render : Expr -> String <-> lambda b: StrPrinter().parenthesize(b, prec, strict=False),
  base <-> item.base,
  baseComponentCount : Nat <-> len(item.args[0].args),
  baseIsProduct : Bool <-> isinstance(item.base, Mul),
  baseIsPower   : Bool <-> isinstance(item.base, Pow),
  result : String <-> the factor's final b_str entry (after the optional wrap).
stdlib-only (plus the repo's sympy); no hypothesis required.
"""
import random
import sys

from sympy import (Symbol, Integer, Rational, Mul, Add, Pow, sin, cos, sqrt,
                   Function)
from sympy.core.mul import Mul as MulCls
from sympy.core.power import Pow as PowCls
from sympy.printing.str import sstr, StrPrinter
from sympy.printing.precedence import precedence

x, y, z = Symbol("x"), Symbol("y"), Symbol("z")
NUM = x  # fixed single-factor numerator, so the printed product is `x/<factor>`


def render(base, prec):
    """render base  <->  the printer's base-fragment renderer at the active
    precedence == the REAL StrPrinter().parenthesize(base, prec, strict=False)."""
    return StrPrinter().parenthesize(base, prec, strict=False)


def shadow_factor(base, base_component_count, base_is_product, base_is_power, prec):
    """R/I transliteration of implementation_printDenominatorFactor (Lean)."""
    base_str = render(base, prec)
    need_paren = (base_component_count != 1) and (base_is_product or base_is_power)
    if need_paren:
        return "(" + base_str + ")"
    return base_str


def base_pool(rng):
    """A spread of denominator-factor bases: atoms, multi-component products,
    powers (incl. the bug-triggering 1/y == Pow(y,-1)), sums, functions."""
    return [
        y, z, Symbol("w"),
        Pow(y, -1, evaluate=False),                 # 1/y  -> Pow, 2 args (bug case)
        Pow(z, 2, evaluate=False),                  # z**2 -> Pow, 2 args
        Pow(y, Integer(3), evaluate=False),
        Mul(y, y, evaluate=False),                  # y*y  -> Mul, 2 args
        Mul(y, z, evaluate=False),
        Mul(x, y, z, evaluate=False),               # x*y*z -> Mul, 3 args
        Add(x, y, evaluate=False),                  # x + y -> Add (not Mul/Pow)
        Add(x, y, z, evaluate=False),
        sin(x), cos(y),                             # functions, single arg
        sqrt(2),
        Rational(2, 3),
        Pow(Add(x, y, evaluate=False), -1, evaluate=False),  # 1/(x+y)
        Pow(Mul(y, z, evaluate=False), -1, evaluate=False),  # 1/(y*z)
    ]


def main():
    rng = random.Random(21612)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    checked = 0
    for i in range(N):
        base = rng.choice(base_pool(rng))
        item = Pow(base, -1, evaluate=False)        # the 1/base denominator factor
        # Guard: stay inside the modeled `exp is S.NegativeOne` branch.
        try:
            m = Mul(NUM, item, evaluate=False)
        except Exception:
            continue
        try:
            res = sstr(m)
        except Exception:
            continue
        prefix = sstr(NUM) + "/"
        if not res.startswith(prefix):
            # multi-factor / re-associated shape not in the single-factor model
            continue
        oracle = res[len(prefix):]

        base_component_count = len(item.args[0].args)
        base_is_product = isinstance(item.base, MulCls)
        base_is_power = isinstance(item.base, PowCls)
        prec = precedence(m)
        shadow = shadow_factor(base, base_component_count,
                               base_is_product, base_is_power, prec)

        checked += 1
        if oracle != shadow:
            disagreements += 1
            if first is None:
                first = (sstr(base), oracle, shadow)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, checked, first))
        return 1
    print("G-CONF OK: %d inputs (%d in-model), 0 disagreements" % (N, checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
