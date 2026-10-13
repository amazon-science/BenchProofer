#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15345 (nagini).

SHADOW: the impl region of model.py's `print_lattice_call`, copied VERBATIM
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
`PSeq` becomes an immutable-tuple shim carrying the tiny `.take`/`.drop`/`+`
API the impl uses; the @Pure helpers it consults (`lbracket`/`rbracket`/`sep`)
copy over as plain functions. There is no @ContractOnly callee.

ORACLE: the REAL patched repo function per mapping.md —
`MCodePrinter._print_Function` (`sympy/printing/mathematica.py`), the method
the lattice-operator printing is bound to post-patch, reached whenever the
applied function's name is recognised in the printer's `known_functions`
table. The gate applies patch.diff to /testbed before this script runs
(PYTHONPATH=/testbed), so the import below sees the patched module.

Type bridge (mapping.md section 2): the model carries strings as PSeq[int]
of Unicode code points and the operand list as PSeq[PSeq[int]] of the
operands' ALREADY-RENDERED surface forms. The bridge derivation for one real
application `expr`:
  name     = the recognised target name for `expr.func.__name__` from the
             printer's `known_functions` table (first entry whose condition
             accepts the args — the same selection the real method performs;
             this is input derivation, the model takes `name` as given),
  operands = [printer.parenthesize(a, 0) for a in expr.args] — the per-operand
             rendering, which is UNCHANGED machinery the model takes as given.
             The printer renders some atoms (e.g. floats) depth-sensitively
             (full precision only at the outermost level under the default
             "auto" setting), so the bridge derives each operand at the SAME
             print depth the oracle path renders it at: depth 0 when the
             modeled method is called directly, depth 1 when the oracle is the
             printer's full dispatch (which enters the method one level down).
Both are converted to code-point tuples via ord(); the real output string is
converted the same way for an exact code-point comparison.

Input domain: the model Requires len(operands) > 0, so every driven
application carries >= 1 argument. Arities:
  - the two n-ary lattice names accept any argument tuple (their table
    conditions are variadic), driven both as unevaluated applications (full
    control of arity/order) and as genuine evaluated Max/Min nodes
    (end-to-end through the printer's dispatch, exercising the post-patch
    method binding);
  - the remaining recognised names carry the single argument their table
    conditions accept.
Argument pool mixes symbols, integers (incl. negatives), rationals, floats,
sums/products/powers, and nested applications whose rendered forms contain
", ", "[", "]" — stressing the separator-join against operands that already
contain separator-lookalike text.

>= 1e5 Requires-satisfying inputs: hand-picked boundary cases + fuzz to
100000+ total. Pinned fuzz seed: 153450.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 153450
N_TOTAL = 100_000


# --- shim for the sequence carrier -------------------------------------------

class _Seq(tuple):
    """Immutable code-point sequence with the tiny slice API the impl uses."""
    def take(self, n):
        return _Seq(self[:n])

    def drop(self, n):
        return _Seq(self[n:])

    def __add__(self, other):
        return _Seq(tuple(self) + tuple(other))


def PSeq(*items):
    """Immutable sequence literal."""
    return _Seq(items)


# --- @Pure helpers from model.py the impl consults, contracts stripped -------

def lbracket():
    # '[' : the opening application delimiter of the surface syntax.
    return 91


def rbracket():
    # ']' : the closing application delimiter of the surface syntax.
    return 93


def sep():
    # ', ' : a comma followed by a single space, the operand separator.
    return PSeq(44, 32)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def print_lattice_call(name, operands):
    # body := the ", "-joined operand list (front-recursive fold, built back
    # to front so each step unfolds `joined` once).
    body = PSeq(0).take(0)  # type: PSeq[int]
    i = len(operands)
    while i > 0:
        if i == len(operands):
            # last operand: a single-element tail, no trailing separator.
            body = operands[i - 1]
        else:
            # at least two operands remain, so `joined` unfolds once.
            body = operands[i - 1] + sep() + body
        i = i - 1
    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
    return result


# --- code-point bridge --------------------------------------------------------

def to_cps(s):
    return [ord(ch) for ch in s]


def to_seq(s):
    return _Seq(ord(ch) for ch in s)


# --- differential driver --------------------------------------------------------

def recognised_name(printer, expr):
    """The target name the printer's table recognises this application as:
    the first entry whose condition accepts the argument tuple. This mirrors
    the real method's own selection and is pure input derivation — the model
    takes `name` as a given sequence."""
    for cond, cand in printer.known_functions[expr.func.__name__]:
        if cond(*expr.args):
            return cand
    return None


def rendered_operands(printer, expr, depth):
    """The per-operand already-rendered surface forms (mapping.md section 2:
    given inputs, unchanged machinery), derived at the print depth the oracle
    path renders them at — some atoms render depth-sensitively, so the bridge
    must match the oracle's depth exactly."""
    old = printer._print_level
    printer._print_level = depth
    try:
        return [printer.parenthesize(a, 0) for a in expr.args]
    finally:
        printer._print_level = old


def check_app(printer, expr, real_out=None):
    """Diff shadow vs real on one recognised application. `real_out` lets the
    caller supply the full-dispatch rendering (doprint, which enters the
    method one print level down) for genuine lattice nodes; by default the
    modeled method is called directly at depth 0. Returns an error string on
    disagreement, else None."""
    name_str = recognised_name(printer, expr)
    if name_str is None:
        return None  # not in the modeled (recognised) domain
    operand_strs = rendered_operands(printer, expr,
                                     0 if real_out is None else 1)
    shadow = print_lattice_call(
        to_seq(name_str), _Seq(to_seq(s) for s in operand_strs))
    try:
        real = real_out if real_out is not None else printer._print_Function(expr)
    except Exception as exc:  # in-domain input must not raise
        return ("DISAGREEMENT (oracle raised)\n  input: %r (name=%r, operands=%r)"
                "\n  shadow: %r\n  real raised %s: %s"
                % (expr, name_str, operand_strs,
                   "".join(chr(c) for c in shadow), type(exc).__name__, exc))
    if list(shadow) != to_cps(real):
        return ("DISAGREEMENT\n  input: %r (name=%r, operands=%r)"
                "\n  shadow: %r\n  real:   %r"
                % (expr, name_str, operand_strs,
                   "".join(chr(c) for c in shadow), real))
    return None


def main():
    # REAL patched printer (mapping.md section 1) — importable from /testbed.
    from sympy.printing.mathematica import MCodePrinter, mathematica_code
    from sympy import (Symbol, symbols, Integer, Rational, Float, Function,
                       Max, Min, sin, cos)
    from sympy.functions.elementary.miscellaneous import MinMaxBase

    printer = MCodePrinter()

    # The recognised names, split by the arity their table conditions accept:
    # the two n-ary lattice names (variadic conditions) vs the unary rest.
    nary_names = [nm for nm, pairs in printer.known_functions.items()
                  if nm[0].isupper()]
    unary_names = [nm for nm in printer.known_functions if nm not in nary_names]
    assert sorted(nary_names) == ["Max", "Min"], nary_names
    nary_fns = {nm: Function(nm) for nm in nary_names}

    x, y, z, a, b = symbols("x y z a b")
    w = symbols("w", positive=True)

    # Argument pool: rendered forms cover plain names, signs, '/', '.',
    # operators with spaces, and nested applications containing ", "/brackets.
    pool = [x, y, z, a, b, w,
            Integer(0), Integer(2), Integer(-3), Integer(10 ** 12),
            Rational(3, 7), Rational(-1, 2), Float(2.5), Float(-0.125),
            sin(x), cos(y), sin(x + y),
            x + y, x - y, 2 * x, x * y * z, x ** 2, x ** -1, -x,
            nary_fns["Max"](x, Integer(2)),        # rendered form contains ", "
            nary_fns["Min"](a, b, z),
            Symbol("longVariableName42"), Symbol("x1"), Symbol("_u")]
    pool_rendered = [printer.parenthesize(p, 0) for p in pool]
    assert any(", " in s for s in pool_rendered)
    assert any("[" in s and "]" in s for s in pool_rendered)

    checked = 0
    fails = []

    def run_case(expr, real_out=None):
        err = check_app(printer, expr, real_out)
        if err:
            print(err)
            fails.append(err)
        return 1

    # --- boundary inputs -------------------------------------------------------
    # single-operand applications (the Requires lower bound), every recognised
    # unary name, small/large arities, duplicate and comma-carrying operands.
    for nm in unary_names:
        for arg in (x, Integer(2), sin(x), x + y):
            checked += run_case(Function(nm)(arg))
    for nm in nary_names:
        F = nary_fns[nm]
        checked += run_case(F(x))                       # arity 1
        checked += run_case(F(x, y))
        checked += run_case(F(y, x))                    # order preserved as given
        checked += run_case(F(x, x, x))                 # duplicates
        checked += run_case(F(*[pool[i % len(pool)] for i in range(8)]))
        checked += run_case(F(nary_fns["Max"](x, y), z))  # nested ", " operand
    if fails:
        return 1

    # --- end-to-end witnesses through the printer's full dispatch --------------
    # Genuine evaluated lattice nodes route through the post-patch method
    # binding; the oracle here is the printer's public entry point.
    for expr in (Max(x, Integer(2)), Max(x, y, z), Min(y, z),
                 Max(x, Rational(1, 2), Integer(-3)), Min(sin(x), y)):
        assert isinstance(expr, MinMaxBase), expr
        checked += run_case(expr, real_out=printer.doprint(expr))
    assert mathematica_code(Max(x, Integer(2))) == printer.doprint(Max(x, Integer(2)))
    if fails:
        return 1

    # --- randomized fuzz to >= N_TOTAL ------------------------------------------
    rng = random.Random(SEED)
    n_pool = len(pool)
    while checked < N_TOTAL:
        mode = checked % 10
        if mode < 6:
            # n-ary lattice application, unevaluated: full control of
            # arity (1..8) and operand order.
            F = nary_fns[rng.choice(nary_names)]
            args = [pool[rng.randrange(n_pool)]
                    for _ in range(rng.randint(1, 8))]
            checked += run_case(F(*args))
        elif mode < 8:
            # a recognised unary application over the pool.
            nm = rng.choice(unary_names)
            checked += run_case(Function(nm)(pool[rng.randrange(n_pool)]))
        else:
            # a genuine evaluated lattice node through full dispatch
            # (evaluation may collapse it below arity 2 or fold constants;
            # keep only surviving lattice nodes — others leave the domain).
            cls = Max if rng.random() < 0.5 else Min
            args = [pool[rng.randrange(n_pool)]
                    for _ in range(rng.randint(2, 5))]
            try:
                expr = cls(*args)
            except ValueError:
                continue  # e.g. comparison of special values; out of domain
            if not isinstance(expr, MinMaxBase):
                continue
            checked += run_case(expr, real_out=printer.doprint(expr))
        if fails:
            return 1

    print("G-CONF OK: shadow impl == real patched recognised-application "
          "rendering on %d inputs (boundary + end-to-end witnesses + fuzz, "
          "seed %d)." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
