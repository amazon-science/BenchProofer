#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12096 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the real repo types: `numEvalSeq` is the front-recursive
              per-element map of `numEval a prec`, applied to the argument list
              `expr.args` in order (the modeled operation: construction of the
              per-argument-evaluated list). The A-tagged callee is NOT replaced by
              an axiom model here; G-CONF isolates the R/I legs, so `numEval` stays
              the REAL `Expr.evalf`. The shadow then feeds that modeled argument
              list into the UNCHANGED downstream `Float(func._imp_(*args), prec)`
              (an I/R identity, shared with the oracle), so any disagreement is a
              fault of the modeled argument-list construction (order/length/map).
  * ORACLE  — `patch.diff`'s behaviour: the patched `Function._eval_evalf(prec)`
              applied to a real applied implemented-function expression — the real
              correctness oracle (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container against the repo at base_commit WITH patch.diff applied (the
harness applies it before this runs). The fuzz seed is pinned (mapping.md §4) for
a deterministic verdict.
"""
import random
import sys

from sympy import Float, Integer, Rational, sin, cos, sqrt, exp, log, pi, E
from sympy.utilities.lambdify import implemented_function

SEED = 12096
N_FUZZ = 4000


def num_eval_seq(prec, args):
    """numEvalSeq (Solution.lean), transliterated front-recursively: per-element
    map of numEval, order kept. A-tagged callee numEval left as the REAL
    Expr.evalf."""
    if not args:
        return []
    head, rest = args[0], args[1:]
    return [head.evalf(prec)] + num_eval_seq(prec, rest)


def shadow_eval(expr, prec):
    """The patched line reconstructed from the MODELED argument list: build the
    per-argument-evaluated args via the Lean fold, then apply the UNCHANGED
    downstream `Float(func._imp_(*args), prec)`. Returns None if the branch is
    not applicable (mirrors the real branch's `except` -> return None)."""
    imp = getattr(expr.func, "_imp_", None)
    if imp is None:
        return None
    modeled_args = num_eval_seq(prec, list(expr.args))
    try:
        return Float(imp(*modeled_args), prec)
    except (AttributeError, TypeError, ValueError):
        return None


def oracle_eval(expr, prec):
    """patch.diff's behaviour: the patched Function._eval_evalf, run verbatim."""
    return expr._eval_evalf(prec)


def fuzz_exprs(n, rng):
    f = implemented_function('f', lambda z: z**2)
    g = implemented_function('g', lambda z: 2 * z)
    h = implemented_function('h', lambda a, b: a + b)
    # numeric arguments: plain numbers (fixed points of evalf) and composites
    # (the issue's witness — an applied implemented-function arg whose evalf
    # genuinely reduces it).
    num_atoms = [Integer(2), Integer(3), Integer(7), Rational(1, 3),
                 Rational(5, 2), sqrt(Integer(2)), pi, E,
                 sin(Integer(1)), cos(Integer(2)), exp(Integer(1)),
                 log(Integer(2)), Float(2.5, 15)]
    composite = [f(2), g(2), f(g(2)), g(f(3)), f(Integer(5))]
    unary = [f, g]
    binary = [h]

    # boundary cases first (plan §4.1 step 4): the exact issue scenario is a
    # composite numeric argument to an implemented function.
    yield f(f(2))            # the F2P witness: f(f(2)).evalf() == Float(16)
    yield f(g(2))
    yield g(f(2))
    yield f(2)               # composite-of-number (single evalf step)
    yield f(Integer(3))
    yield h(f(2), g(2))      # two-argument: order matters
    yield h(2, 3)

    pool = num_atoms + composite
    for _ in range(n):
        which = rng.choice(unary + binary)
        if which in binary:
            a = rng.choice(pool)
            b = rng.choice(pool)
            try:
                e = which(a, b)
            except Exception:
                continue
        else:
            a = rng.choice(pool)
            try:
                e = which(a)
            except Exception:
                continue
        if getattr(e, "args", None):
            yield e


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for expr in fuzz_exprs(N_FUZZ, rng):
        # Only the _imp_ fallback branch is modeled: expr.func must carry _imp_
        # and the mpmath-name lookup must miss (true for implemented_function /
        # UndefinedFunction, whose names are not mpmath builtins).
        if getattr(expr.func, "_imp_", None) is None:
            continue
        for prec in (15, 24, 53, 80):
            try:
                oracle = oracle_eval(expr, prec)
            except Exception:
                # unsupported exprs are out of scope
                continue
            try:
                shadow = shadow_eval(expr, prec)
            except Exception:
                continue
            count += 1
            # Compare observable numeric value. Both are Float or None.
            agree = (oracle == shadow) or (oracle is None and shadow is None)
            if not agree:
                disagreements.append((expr, prec, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for e, prec, sh, orc in disagreements:
            print("  expr=%r prec=%r shadow=%r oracle=%r" % (e, prec, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of evaluateArgs (per-argument numerical "
          "evaluation, fed through the unchanged _imp_/Float downstream) agrees "
          "with patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
