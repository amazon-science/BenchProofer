#!/usr/bin/env python3
"""G-CONF for sympy__sympy-14531.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_printRelational` / `implementation_printLimit`
(the Lean impls, transliterated op-for-op per refinement.md) against the REAL
patched StrPrinter routines `_print_Relational` and `_print_Limit`, over >=1e5
fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md):
  * A relational application in the operator-tag (charmap) branch — Eq / Ne —
    renders as  relName(lhs, rhs)  where relName is the textual operator tag and
    lhs/rhs are the two operand subexpressions, EACH rendered at the printer's
    ACTIVE formatting profile.
  * A limit renders as  Limit(e, z, z0)  (default direction) or
    Limit(e, z, z0, dir='dir')  (non-default direction), with every component
    rendered at the ACTIVE formatting profile.

The renderer `render(settings, sub)` is the printer's own NESTED subexpression
printer at the active profile: what `self._print(sub)` produces when called from
inside a container's `_print_*` method. That is NOT the same function as the
top-level `sstr(sub, **settings)`: `Printer._print` tracks a recursion depth
(`_print_level`), and `StrPrinter._print_Float` with the default
`full_prec="auto"` strips trailing zeros exactly when `_print_level > 1` (nested)
— e.g. nested Float(1.5) renders '1.5' while top-level sstr gives
'1.50000000000000'. The abstract Lean `Settings` therefore denotes the display
options TOGETHER WITH the rendering context (nested vs top-level); `render` is
realized here as a fresh StrPrinter at the active options whose `_print_level`
is pre-bumped to the container's frame, so the nested call sees level >= 2 —
byte-for-byte what the real container's `self._print(sub)` computes.

  * Oracle  = the REAL patched `sstr(expr, **settings)` (dispatches to
              `_print_Relational` / `_print_Limit`).
  * Shadow  = the Lean impl's template with `render settings <sub>` == the REAL
              nested `self._print(<sub>)` at the active options spliced into
              each subexpression position.

Type bijection (mapping.md):
  Settings <-> (StrPrinter settings dict, rendering context); active profile =
    (the caller's options dict, NESTED context),
  render : Settings -> Expr -> String  <->  nested_print(s, e) below,
  settings <-> the ACTIVE profile, relName <-> charmap[expr.rel_op] (str),
  lhs/rhs/e/z/z0/dir <-> the operand subexpressions (sympy Expr),
  dirIsDefault <-> (str(dir) == "+"),  result <-> rendered string.
stdlib-only (plus the repo's sympy); no hypothesis required.
"""
import random
import sys

from sympy import (Symbol, Rational, Integer, Float, Eq, Ne, Limit, sqrt, sin,
                   cos, Mul, Add, Pow)
from sympy.printing.str import sstr, StrPrinter

# charmap operator tags for the modeled relational branch (str.py _print_Relational).
REL_BRANCH = {Eq: "Eq", Ne: "Ne"}

x, y, z = Symbol("x"), Symbol("y"), Symbol("z")


def render(settings, sub):
    """render settings sub  <->  the printer's NESTED subexpression renderer at
    the active profile == what the REAL `self._print(sub)` computes when invoked
    from inside a container's `_print_*` method. The container's own `_print`
    frame has already pushed `_print_level` to 1, so the nested call runs at
    level >= 2; we reproduce that by pre-bumping a fresh printer's level."""
    p = StrPrinter(settings)
    p._print_level = 1  # the container's own frame; nested sub renders at >= 2
    return p._print(sub)


def shadow_relational(settings, rel_name, lhs, rhs):
    """R/I transliteration of implementation_printRelational (Lean)."""
    return rel_name + "(" + render(settings, lhs) + ", " + render(settings, rhs) + ")"


def shadow_limit(settings, dir_is_default, e, zv, z0, direction):
    """R/I transliteration of implementation_printLimit (Lean)."""
    if dir_is_default:
        return ("Limit(" + render(settings, e) + ", " + render(settings, zv) + ", "
                + render(settings, z0) + ")")
    else:
        return ("Limit(" + render(settings, e) + ", " + render(settings, zv) + ", "
                + render(settings, z0) + ", dir='" + render(settings, direction) + "')")


# Subexpression pool: a spread of atoms / compounds whose rendering is sensitive
# to sympy_integers (rationals), to the nested-vs-top-level context (Floats with
# full_prec="auto": trailing-zero stripping depends on _print_level), and whose
# nesting exercises the delegation.
def atom_pool():
    return [
        x, y, z,
        Rational(1, 2), Rational(2, 3), Rational(7, 2), Rational(-3, 4),
        Integer(5), Integer(-2), Integer(0),
        Float(1.5), Float(0.25), Float(-2.75), x + Float(1.5),
        x ** Rational(2, 3), x + Rational(1, 2), x * Rational(3, 5),
        sqrt(2), sin(x), cos(y), x * y, x + y, x ** 2,
        Rational(10, 7) * x + Rational(1, 3),
    ]


DIRECTIONS = [Symbol("x"), Integer(1)]  # used only as the `dir` slot for Limit


def rand_expr(rng):
    pool = atom_pool()
    e = rng.choice(pool)
    # occasionally build a small compound to deepen nesting
    if rng.random() < 0.3:
        e = e + rng.choice(pool)
    if rng.random() < 0.2:
        e = e * rng.choice(pool)
    return e


def main():
    rng = random.Random(14531)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        settings = {"sympy_integers": rng.choice([True, False])}
        if rng.random() < 0.5:
            # ---- relational branch (Eq / Ne) ----
            cls = rng.choice([Eq, Ne])
            rel_name = REL_BRANCH[cls]
            lhs = rand_expr(rng)
            rhs = rand_expr(rng)
            try:
                expr = cls(lhs, rhs, evaluate=False)
            except Exception:
                continue
            # Only the charmap branch is modeled: rel_op must be == or != .
            if getattr(expr, "rel_op", None) not in ("==", "!="):
                continue
            o = sstr(expr, **settings)
            s = shadow_relational(settings, rel_name, lhs, rhs)
        else:
            # ---- limit branch ----
            e = rand_expr(rng)
            zv = rng.choice([x, y, z])
            z0 = rand_expr(rng)
            # default-direction "+" vs an explicit other direction "-"
            if rng.random() < 0.5:
                expr = Limit(e, zv, z0, dir="+")
                dir_is_default = True
                direction = Symbol("+")
            else:
                expr = Limit(e, zv, z0, dir="-")
                dir_is_default = False
                direction = expr.args[3]
            # confirm our default selection matches the real predicate str(dir)=="+"
            real_default = (str(expr.args[3]) == "+")
            if real_default != dir_is_default:
                dir_is_default = real_default
            o = sstr(expr, **settings)
            s = shadow_limit(settings, dir_is_default, e, zv, z0, expr.args[3])
        if o != s:
            disagreements += 1
            if first is None:
                first = (settings, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
