#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18763 (nagini).

SHADOW: the impl region of model.py's `format_restriction`, copied VERBATIM
below with the contract calls (Invariant; Requires/Ensures live outside the
impl region) stripped. The @Pure helpers from the pure region (`open_layout`,
`open_delim`, `close_delim`, `mid_layout`, `tail`, `assembled`) copy over as
plain functions for completeness; `PSeq`/`ToSeq` become immutable-tuple shims.
There are no @ContractOnly callees and no axioms in this bundle.

ORACLE: the REAL patched repo function per mapping.md — the LaTeX renderer
method for a substitution/restriction object on the LaTeX printer class in
the printing module (the gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed). Called directly on real substitution
objects.

Type bridge (mapping.md section 2): the repo carriers are `str` values; the
model carriers are `List[int]` / `PSeq[int]` of Unicode code points, mapped
via `ord`/`chr` per character. The model's inputs `body` and `cond` are the
outputs of UNCHANGED callees (the inner-expression rendering and the joined
variable=point rendering, both locals of the real method built before the
final layout assembly). Each test case is realized by building a real
substitution object, deriving those two fragment carriers from it with the
real unchanged callees exactly as the method's own locals are built, feeding
their code points to the shadow, and comparing the shadow's output code
points against the real method's output on the same object.

Input domain: exactly the model's Requires — any pair of code-point lists,
as reachable through real substitution objects. The mix over-represents
interesting regimes: single and multiple substituted variables, compound
bodies (sums, products, powers, applied functions, derivatives) whose
rendering carries operator structure, bodies/points whose renderings contain
backslash commands, braces, subscripts and greek letters, and numeric /
rational / symbolic / compound points.

>= 1e5 Requires-satisfying inputs: hand-picked boundary cases + randomized
fuzz to a total of 100000+. Pinned fuzz seed: 202608.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from typing import List

SEED = 202608
N_TOTAL = 100_000


# --- shims for the sequence carrier -----------------------------------------

class _Seq(tuple):
    """Immutable code-point sequence with the small slice API the pure
    helpers use. `+` on tuples already matches PSeq concatenation."""
    def take(self, n):
        return _Seq(self[:n])

    def drop(self, n):
        return _Seq(self[n:])


def PSeq(*items):
    """Immutable sequence literal."""
    return _Seq(items)


def ToSeq(lst):
    """Immutable snapshot of a list's contents."""
    return _Seq(lst)


# --- @Pure helpers from model.py, contracts stripped -------------------------

def open_layout():
    return PSeq(92, 108, 101, 102, 116, 46, 32)


def open_delim():
    return PSeq(92, 108, 101, 102, 116, 40)


def close_delim():
    return PSeq(92, 114, 105, 103, 104, 116, 41)


def mid_layout():
    return PSeq(32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32)


def tail():
    return PSeq(32, 125, 125)


def assembled(body, cond):
    """The fully assembled layout: the body enclosed in its own matched
    delimiter pair, dropped into the constant surrounding layout together with
    the condition fragment."""
    return (open_layout() + open_delim() + body + close_delim()
            + mid_layout() + cond + tail())


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def format_restriction(body, cond):
    result = []  # type: List[int]
    # open-layout
    result = result + [92, 108, 101, 102, 116, 46, 32]
    # open-delim (matched pair, before the body)
    result = result + [92, 108, 101, 102, 116, 40]
    # the body fragment, copied verbatim
    i = 0
    while i < len(body):
        result.append(body[i])
        i = i + 1
    # close-delim (matched pair, after the body)
    result = result + [92, 114, 105, 103, 104, 116, 41]
    # mid-layout
    result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                       92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
    # the condition fragment, copied verbatim
    j = 0
    while j < len(cond):
        result.append(cond[j])
        j = j + 1
    # tail
    result = result + [32, 125, 125]
    return result


# --- differential driver ------------------------------------------------------

def _dec(cps):
    return "".join(chr(c) for c in cps)


def check_case(printer, subs_obj):
    """Run shadow and oracle on one real substitution object; return an
    error string on disagreement, else None."""
    expr, old, new = subs_obj.args
    # Input carriers, derived by the real UNCHANGED callees exactly as the
    # method's own locals are built (mapping.md section 1): the rendered
    # inner-expression fragment and the joined variable=point fragment.
    latex_expr = printer._print(expr)
    latex_old = (printer._print(e) for e in old)
    latex_new = (printer._print(e) for e in new)
    latex_subs = r'\\ '.join(
        e[0] + '=' + e[1] for e in zip(latex_old, latex_new))
    body = [ord(ch) for ch in latex_expr]
    cond = [ord(ch) for ch in latex_subs]
    shadow = format_restriction(body, cond)
    try:
        real = printer._print_Subs(subs_obj)
    except Exception as exc:  # in-domain input must not raise
        return ("DISAGREEMENT (oracle raised)\n  input: body=%r cond=%r"
                "\n  shadow: %r\n  real raised %s: %s"
                % (latex_expr, latex_subs, _dec(shadow),
                   type(exc).__name__, exc))
    if _dec(shadow) != real:
        return ("DISAGREEMENT\n  input: body=%r cond=%r"
                "\n  shadow: %r\n  real:   %r"
                % (latex_expr, latex_subs, _dec(shadow), real))
    return None


def main():
    # REAL patched repo class (mapping.md section 1) — importable
    # from /testbed once the gate has applied the patch.
    from sympy.printing.latex import LatexPrinter
    from sympy import (Symbol, Integer, Rational, Function, Derivative,
                       Subs, pi, sqrt, sin, exp)

    printer = LatexPrinter()
    rng = random.Random(SEED)

    x, y, z = Symbol("x"), Symbol("y"), Symbol("z")
    a1 = Symbol("a_1")
    alpha = Symbol("alpha")
    lam = Symbol("lambda")
    f = Function("f")
    g = Function("g")

    # Variable pools for the substituted-variable tuple (no duplicates
    # within one tuple; every variable also appears in the body so the
    # object is well-formed across versions).
    var_pool = [x, y, z, a1, alpha, lam]

    # Point pool: numeric / rational / symbolic / compound replacement
    # values, several with structured renderings (fractions, radicals,
    # applied functions, greek letters).
    point_pool = [Integer(0), Integer(1), Integer(-1), Integer(2),
                  Integer(7), Integer(10) ** 6,
                  Rational(1, 2), Rational(-5, 3),
                  x, y, z, alpha, pi,
                  x + 1, 2 * y, -z, x * y, x ** 2,
                  sqrt(Integer(2)), sin(x), exp(y), f(x), x / y]

    def build_body(vs, extra_depth):
        """A body expression over the chosen variables (guaranteeing each
        appears), with optional extra structure layered on top."""
        e = vs[0]
        for v in vs[1:]:
            op = rng.randrange(3)
            if op == 0:
                e = e + v
            elif op == 1:
                e = e - v
            else:
                e = e * v
        for _ in range(extra_depth):
            op = rng.randrange(6)
            if op == 0:
                e = e + rng.choice([Integer(1), Integer(-2), Rational(1, 3)])
            elif op == 1:
                e = e * rng.choice([Integer(2), Integer(-1), pi])
            elif op == 2:
                e = e ** 2
            elif op == 3:
                e = f(e)
            elif op == 4:
                e = sin(e)
            else:
                e = e / rng.choice([Integer(2), y + 1])
        return e

    checked = 0

    # --- boundary inputs ------------------------------------------------------
    boundary = [
        # single variable, atomic body: rendered body carries no structure
        Subs(x, x, Integer(1)),
        # compound additive body: the regime where enclosing the body in its
        # own matched pair is observable
        Subs(-x + y, x, Integer(1)),
        Subs(x + y, x, Integer(0)),
        # multiplication-by-constant body
        Subs(3 * x, x, Integer(2)),
        # two and three substituted variables
        Subs(x + y, (x, y), (Integer(1), Integer(2))),
        Subs(x * y * z, (x, y, z), (Integer(1), Integer(2), Integer(3))),
        # points that are themselves compound expressions
        Subs(x + y, (x, y), (y + 1, x ** 2)),
        # applied-function and derivative bodies
        Subs(f(x), x, Integer(0)),
        Subs(Derivative(f(x), x), x, Integer(0)),
        Subs(Derivative(f(x, y), x, y), (x, y), (Integer(0), Integer(1))),
        # renderings with backslash commands / braces / subscripts
        Subs(alpha + a1, (alpha, a1), (Rational(1, 2), sqrt(Integer(2)))),
        Subs(lam ** 2, lam, pi),
        # nested substitution object as the body
        Subs(Subs(x + y, x, Integer(1)), y, Integer(2)),
        # rational / power / fraction bodies
        Subs(x / y, (x, y), (Integer(1), Integer(2))),
        Subs(x ** (y + 1), (x, y), (Integer(2), Integer(3))),
        Subs(sin(x) * exp(y), (x, y), (pi, Integer(0))),
        Subs(g(x, y), (x, y), (f(x), g(y, z))),
    ]
    for obj in boundary:
        err = check_case(printer, obj)
        if err:
            print(err)
            return 1
        checked += 1

    # --- randomized fuzz to >= N_TOTAL -----------------------------------------
    n_fuzz = N_TOTAL - checked
    for _ in range(n_fuzz):
        nvars = rng.randint(1, 3)
        vs = rng.sample(var_pool, nvars)
        depth = rng.randrange(3)
        body_expr = build_body(vs, depth)
        pts = [rng.choice(point_pool) for _ in range(nvars)]
        obj = Subs(body_expr, tuple(vs), tuple(pts))
        err = check_case(printer, obj)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched restriction-layout renderer "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
