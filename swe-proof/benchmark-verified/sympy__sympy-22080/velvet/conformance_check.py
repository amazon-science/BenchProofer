#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-22080 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`printNegatedFactor`) transliterated to Python: classify the
              single negated factor into its OperandKind, look up `opWeight`,
              compare to `negLevel`, and assemble `renderNeg`. The recursive
              printing of the inner factor (the unchanged callee that produces
              `inner`) is A-tagged: the shadow uses the REAL renderer for it
              (`pycode(factor)`), NOT a model — G-CONF isolates the R/I leg
              (the wrap decision + assembly), leaving the A leg to G-AX.

  * ORACLE  — `patch.diff`'s behaviour: the patched code printer's actual output
              for the negated expression, `pycode(-e)` (the real correctness
              oracle, G-RESOLVE).

They must agree on every Requires-satisfying input (an expression whose negation
is a single negated factor — sign '-' with exactly one numerator factor, the
branch the change touches). Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container against the patched repo; stdlib + sympy only. The fuzz seed
is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy import (symbols, Mod, sin, cos, tan, exp, Symbol, Integer, Mul,
                   UnevaluatedExpr)
from sympy.printing.pycode import pycode
from sympy.codegen.rewriting import create_expand_pow_optimization

SEED = 22080
N_FUZZ = 100_000

# --- the R/I shadow: Solution.lean opWeight/needsParen/renderNeg -------------
_OP_WEIGHT = {
    "atomic": 2000,
    "power": 120,
    "funcCall": 140,
    "modOp": 100,
    "mulCluster": 99,
}
_NEG_LEVEL = 110


def classify(factor):
    """Map the single numerator factor to its OperandKind by the same shape
    distinctions Solution.lean's spec view names (mapping.md §2). Returns None
    for a shape outside the modeled set (out of Requires)."""
    tname = type(factor).__name__
    if tname == "UnevaluatedExpr":
        # precedence(UnevaluatedExpr(e)) == precedence(e) - 0.5 (repo
        # precedence.py::precedence_UnevaluatedExpr), so a single
        # UnevaluatedExpr wrapper carries its INNER expression's
        # binding-strength class: the wrap test is `precedence <= 55` and no
        # modeled strength lies in (55, 55.5] (nearest above is Pow = 60), so
        # one -0.5 shift never crosses the threshold. Classify by the inner
        # expression (mapping.md §2). NESTED wrappers accumulate -0.5 per
        # level and could eventually cross 55 (e.g. depth 10 around a Pow),
        # so depth >= 2 is out of the modeled Requires.
        inner = factor.args[0]
        if type(inner).__name__ == "UnevaluatedExpr":
            return None
        return classify(inner)
    if tname == "Mod":
        return "modOp"
    if factor.is_Pow:
        return "power"
    if factor.is_Mul:
        return "mulCluster"
    if factor.is_Function:
        return "funcCall"
    if factor.is_Atom:
        return "atomic"
    return None


def shadow_render(kind, inner):
    """renderNeg kind inner, transliterated. `inner` is the REAL renderer's
    printing of the factor (the A-tagged unchanged callee)."""
    if _OP_WEIGHT[kind] <= _NEG_LEVEL:          # needsParen
        return "-(" + inner + ")"
    return "-" + inner


def oracle_render(e):
    """patch.diff's behaviour: the patched printer's output for -e."""
    return pycode(-e)


def _factor_of_negation(e):
    """If -e is a single negated factor (sign '-', one numerator factor), return
    that factor; else None (input outside the changed branch's Requires)."""
    c, m = (-e).as_coeff_Mul()
    if not (c.is_number and c.is_negative):
        return None
    args = Mul.make_args(m)
    if len(args) != 1:
        return None
    return args[0]


def fuzz_inputs(n, rng):
    x, y, z = symbols("x y z")
    a, b = symbols("a b")
    opt = create_expand_pow_optimization(4)
    syms = [x, y, z, a, b]
    # boundary cases first
    yield Mod(x, y)
    yield Mod(y, z)
    yield Mod(x, 2)
    yield x
    yield x ** y
    yield x ** 2
    yield sin(x)
    yield cos(y)
    yield exp(x)
    yield opt(x ** 2)
    yield opt(x ** 3)
    yield opt(x ** 4)
    # UnevaluatedExpr carries its inner expression's strength minus 0.5
    # (precedence_UnevaluatedExpr) — the panel counterexamples and kin:
    yield UnevaluatedExpr(x ** 2)          # 59.5 > 55: NOT wrapped ('-x**2')
    yield UnevaluatedExpr(sin(x))          # 69.5 > 55: NOT wrapped
    yield UnevaluatedExpr(x)               # 999.5 > 55: NOT wrapped
    yield UnevaluatedExpr(x * y)           # 49.5 <= 55: wrapped
    yield UnevaluatedExpr(Mod(x, y))       # 49.5 <= 55: wrapped
    # nested wrappers (depth >= 2) are out of the modeled Requires — skipped:
    yield UnevaluatedExpr(UnevaluatedExpr(x ** 2))
    builders = [
        lambda: rng.choice(syms),
        lambda: rng.choice(syms) ** rng.choice(syms + [Integer(2), Integer(3)]),
        lambda: rng.choice([sin, cos, tan, exp])(rng.choice(syms)),
        lambda: Mod(rng.choice(syms), rng.choice(syms)),
        lambda: opt(rng.choice(syms) ** rng.choice([2, 3, 4])),
        lambda: UnevaluatedExpr(rng.choice([
            rng.choice(syms),
            rng.choice(syms) ** rng.choice([2, 3]),
            rng.choice([sin, cos, tan, exp])(rng.choice(syms)),
            Mod(rng.choice(syms), rng.choice(syms)),
            rng.choice(syms) * rng.choice(syms),
        ])),
    ]
    for _ in range(n):
        yield rng.choice(builders)()


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    for e in fuzz_inputs(N_FUZZ, rng):
        factor = _factor_of_negation(e)
        if factor is None:
            skipped += 1
            continue
        kind = classify(factor)
        if kind is None:
            skipped += 1
            continue
        count += 1
        inner = pycode(factor)            # A-tagged: real renderer for the inner
        shadow = shadow_render(kind, inner)
        oracle = oracle_render(e)
        if shadow != oracle:
            disagreements.append((e, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for e, sh, orc in disagreements:
            print("  expr=%r shadow=%r oracle=%r" % (e, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of printNegatedFactor agrees with patch.diff "
          "behaviour on %d single-negated-factor inputs (seed=%d, %d "
          "out-of-Requires skipped), 0 disagreements." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
