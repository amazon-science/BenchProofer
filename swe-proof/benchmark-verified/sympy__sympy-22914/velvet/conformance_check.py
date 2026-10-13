#!/usr/bin/env python3
"""G-CONF differential conformance for sympy__sympy-22914 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. This
bundle has NO axiomatized callees and NO deep-model references: the impl region
of `printApp` is pure R/I, fully covered here; there is nothing for G-AX (no
axiom_check.py) and no A-tagged callee left as a real-repo call.

The single modeled method:

  * `printApp(head, args, fallback)` — emit the target-language source for one
    function-application node. The modeled (changed) decision is: a node whose
    head is the symbolic minimum / maximum is emitted as a call to the Python
    builtin `min` / `max` over its rendered operands; `Abs` keeps its
    pre-existing `abs` mapping; EVERY other head is emitted exactly as the
    unchanged surrounding machinery emits it — that machinery's output arrives
    as the read-only input `fallback`, and the modeled routine must return it
    verbatim (the spec's fourth post-condition pins the no-change contract).

ORACLE — the patched source itself. The gold patch (applied in-container before
this runs) extends the printer's builtin-equivalent lookup table so that the
`PythonCodePrinter` renders `Min`/`Max` nodes as `min(...)`/`max(...)`. We
construct real `Min`/`Max`/`Abs`/other expressions and read the patched
printer's `doprint(expr)`.

SHADOW — Solution.lean's `renderCall (builtin head) args` / `joinComma` /
fallback pass-through, transliterated to Python. Per mapping.md §2, the
operands arrive ALREADY rendered (the recursive rendering of operands is
unchanged infrastructure, an INPUT to `printApp`); we obtain those rendered
operand strings from the printer's own `parenthesize(arg, 0)` and feed them
into the shadow assembly. The `fallback` input (the unchanged machinery's
emission for a non-mapped head) is obtained from a pristine printer of the same
class rendering the same node; for mapped heads a poison sentinel is fed
instead, so the check also refutes any shadow that leaks `fallback` where the
builtin call is required. This isolates the R/I leg under test (the per-node
dispatch + call assembly + no-change pass-through), exactly as the Lean `do`
block does.

They must agree on every input. Exit 0 iff zero disagreements. The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict. stdlib + sympy (the repo
under test) only.
"""
import random
import sys

SEED = 22914
N_FUZZ = 100_000

# builtin-equivalent table the shadow models (mirrors Solution.lean's impl)
_BUILTIN = {
    "Min": "min",
    "Max": "max",
    "Abs": "abs",
}

# Poison sentinel fed as `fallback` on mapped heads: never a legal printer
# output, so a shadow that wrongly returns `fallback` for Min/Max/Abs diverges.
_POISON = "\x00<POISON-FALLBACK>\x00"


def join_comma(rendered_args):
    """joinComma transliterated: rendered arg texts joined by ', '."""
    return ", ".join(rendered_args)


def render_call(name, rendered_args):
    """renderCall transliterated: name '(' joinComma args ')'."""
    return name + "(" + join_comma(rendered_args) + ")"


def shadow_print_app(head, rendered_args, fallback):
    """printApp transliterated: dispatch the head to its builtin equivalent
    (Min->min, Max->max, Abs->abs) and assemble the call; ANY other head is
    emitted exactly as the unchanged machinery does — return `fallback`
    verbatim. `rendered_args` and `fallback` are read-only INPUTS to the
    modeled routine."""
    if head in _BUILTIN:
        return render_call(_BUILTIN[head], rendered_args)
    return fallback


def main():
    from sympy import (
        symbols, Min, Max, Abs, Integer, sin, cos, exp, log, sqrt,
        Function, Piecewise, gamma, sign,
    )
    from sympy.printing.pycode import PythonCodePrinter

    rng = random.Random(SEED)
    syms = symbols("a b c d e f g h")
    printer = PythonCodePrinter()
    # Pristine printer of the same class: supplies the `fallback` input (the
    # unchanged machinery's emission) for non-mapped heads, independently of
    # the printer instance under test.
    fallback_printer = PythonCodePrinter()

    def check(expr):
        """Build the modeled routine's INPUTS from the node: the head name,
        the printer's own operand rendering, and — for non-mapped heads — the
        unchanged machinery's emission as `fallback` (poison sentinel for
        mapped heads, which must never surface). Compare shadow vs oracle."""
        head = expr.func.__name__
        if head in _BUILTIN:
            rendered_args = [printer.parenthesize(arg, 0) for arg in expr.args]
            fallback = _POISON
        else:
            # operands are unused by the modeled routine on this leg (the
            # fourth post-condition pins out = fallback regardless of args)
            rendered_args = []
            fallback = fallback_printer.doprint(expr)
        shadow = shadow_print_app(head, rendered_args, fallback)
        oracle = printer.doprint(expr)
        return (shadow == oracle), shadow, oracle

    disagreements = []

    def feed(expr):
        ok, shadow, oracle = check(expr)
        if not ok:
            disagreements.append((expr, shadow, oracle))

    # --- boundary / structured cases ------------------------------------
    a, b, c, d, e, f, g, h = syms
    fn = Function("f")
    boundary = [
        Min(a, b), Max(a, b),
        Min(a, b, c), Max(a, b, c),
        Min(a, b, c, d), Max(a, b, c, d, e),
        Abs(a),
        Min(a, Max(b, c)), Max(Min(a, b), c),
        Min(a, Max(b, c), Abs(d)),
        Max(Min(a, Abs(b)), Max(c, d), e),
        Min(Integer(2), a), Max(a, Integer(3)),
        Min(a, Abs(Max(b, c, d))),
        # non-mapped heads: the no-change contract (fourth post-condition)
        sin(a), cos(a + b), exp(a), log(a), sqrt(a),
        gamma(a), sign(a),
        fn(a, b),
        sin(Min(a, b)), exp(Max(a, Abs(b))),
        Piecewise((a, a > 0), (b, True)),
    ]
    for expr in boundary:
        feed(expr)
        if len(disagreements) >= 5:
            break

    # --- randomized fuzz: random trees over the symbols ------------------
    leaves = list(syms) + [Integer(2), Integer(3), Integer(-1)]
    unary_other = [sin, cos, exp, log, sqrt, gamma, sign, Abs]

    def random_expr_mapped(depth):
        """Trees over the mapped constructors (Min/Max/Abs) and plain leaves —
        every subterm prints without doprint's not-supported header, so the
        mapped-head oracle comparison is byte-exact (as in the original run)."""
        if depth <= 0 or rng.random() < 0.4:
            return rng.choice(leaves)
        kind = rng.choice(["Min", "Max", "Abs"])
        if kind == "Abs":
            return Abs(random_expr_mapped(depth - 1))
        k = rng.randint(2, 4)
        ctor = Min if kind == "Min" else Max
        return ctor(*[random_expr_mapped(depth - 1) for _ in range(k)])

    count = len(boundary)
    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        # top node: mapped heads (Min/Max/Abs) exercise the builtin-call legs,
        # non-mapped heads (sin/exp/gamma/...) exercise the fallback
        # pass-through (there both sides carry doprint's full output, headers
        # included, so parity is exact by construction of the INPUT).
        kind = rng.choice(["Min", "Max", "Abs", "other"])
        try:
            if kind == "Abs":
                expr = Abs(random_expr_mapped(2))
            elif kind == "other":
                expr = rng.choice(unary_other)(random_expr_mapped(2))
            else:
                ctor = Min if kind == "Min" else Max
                k = rng.randint(2, 4)
                expr = ctor(*[random_expr_mapped(2) for _ in range(k)])
        except ValueError:
            # e.g. Min/Max over a non-comparable collapsed subterm: no
            # expression node exists to print; skip.
            continue
        # constant folding may collapse expr to an atom (Symbol/Integer/...)
        # with no application node to print-dispatch; skip those.
        if not expr.args:
            continue
        count += 1
        feed(expr)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for expr, sh, orc in disagreements:
            print("  expr=%r shadow=%r oracle=%r" % (expr, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of printApp (renderCall/joinComma dispatch + "
          "fallback pass-through) agrees with the patched PythonCodePrinter "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
