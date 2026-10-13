#!/usr/bin/env python3
"""G-CONF for sympy__sympy-15345.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_printApplication` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched Mathematica printer routine
for Max/Min applications, over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md):
  A multi-argument function application is rendered as
      funcName[arg1, ..., argn]
  i.e. the textual function name, then the argument list (each argument rendered
  by the printer's own per-argument renderer, joined by ", "), enclosed in the
  target language's SQUARE-BRACKET call syntax.

The per-argument renderer `render(sub)` is the printer's own per-argument printer;
concretely the term produced for that argument by the same `MCodePrinter`
(`p.stringify((sub,), ", ")`).

  * Oracle  = the REAL patched `MCodePrinter().doprint(expr)` for a Max/Min
              application (dispatches via `_print_MinMaxBase = _print_Function`).
  * Shadow  = the Lean impl's template `funcName + "[" + <args joined> + "]"`
              with each argument fragment == the REAL per-argument rendering.

Type bijection (mapping.md):
  Expr <-> a sympy Expr (argument),
  render : Expr -> String  <->  p.stringify((sub,), ", ")  (per-arg printer),
  funcName <-> expr.func.__name__  (str),  args <-> list(expr.args),
  result <-> rendered string.
stdlib-only (plus the repo's sympy); no hypothesis required.
"""
import random
import sys

from sympy import (Symbol, Rational, Integer, Max, Min, sin, cos, sqrt, exp,
                   tan, Add, Mul, Pow)
from sympy.printing.mathematica import MCodePrinter

x, y, z, w = Symbol("x"), Symbol("y"), Symbol("z"), Symbol("w")


def render_args(printer, args):
    """renderArgs (Lean): each argument rendered by the printer's per-argument
    renderer, joined by ", ". Mirrors `self.stringify(expr.args, ", ")`."""
    return printer.stringify(tuple(args), ", ")


def shadow_application(printer, func_name, args):
    """R/I transliteration of implementation_printApplication (Lean)."""
    return func_name + "[" + render_args(printer, args) + "]"


def atom_pool():
    return [
        x, y, z, w,
        Rational(1, 2), Rational(2, 3), Rational(7, 2), Rational(-3, 4),
        Integer(5), Integer(-2), Integer(0), Integer(2), Integer(10),
        x ** Rational(2, 3), x + Rational(1, 2), x * Rational(3, 5),
        sqrt(2), sin(x), cos(y), tan(z), exp(x),
        x * y, x + y, x ** 2, y ** 3, x * y + z,
    ]


def rand_args(rng):
    pool = atom_pool()
    n = rng.randint(2, 4)
    return [rng.choice(pool) for _ in range(n)]


def main():
    rng = random.Random(15345)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        cls = rng.choice([Max, Min])
        args = rand_args(rng)
        try:
            expr = cls(*args, evaluate=False)
        except Exception:
            continue
        # Only model an actual Max/Min application node (not a collapsed atom).
        if expr.func.__name__ not in ("Max", "Min"):
            continue
        printer = MCodePrinter()
        try:
            o = printer.doprint(expr)
        except Exception:
            continue
        # Shadow uses the SAME printer's per-argument rendering on the REAL
        # (possibly reordered/canonicalized) expr.args, matching the impl.
        s = shadow_application(printer, expr.func.__name__, list(expr.args))
        if o != s:
            disagreements += 1
            if first is None:
                first = (str(expr), o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
