#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-13480.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Differential-tests the modeled observable — the dispatch
in the additive-argument branch of the hyperbolic-cotangent evaluator — against
the REAL patched `coth`.

Modeled observable (mapping.md): given an additive argument `arg` whose split
`x, m = _peeloff_ipi(arg)` has a NONZERO multiple part `m` (the `if m:` branch),
the branch returns
    coth(x)   if coth(m) is S.ComplexInfinity
    tanh(x)   otherwise
and always completes (never raises). This is exactly `implementation_cothReduce`
under the bijection
    Except.ok v  <->  the branch returns v
    cothFn       <->  coth   (A-reference, unchanged callee)
    tanhFn       <->  tanh   (A-reference, unchanged callee)
    complexInfinity <-> S.ComplexInfinity.

Shadow (transliteration of implementation_cothReduce, fed the real split):
    x, m = _peeloff_ipi(arg)            # the unchanged surrounding split
    cothm = coth(m)
    shadow = coth(x) if cothm is S.ComplexInfinity else tanh(x)
Real side: coth(arg)  — the full patched evaluator, which routes additive args
with nonzero `m` through exactly this branch.

We assert (a) coth(arg) == shadow (the dispatch is faithful) and (b) coth(arg)
never raised (it always completes — the property the fix restores). Inputs are
chosen so the argument is an Add with a nonzero half-period multiple, exercising
both dispatch legs.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 13480
N_RANDOM = 120_000  # >= 1e5


def main():
    from sympy import (coth, tanh, S, I, pi, Symbol, Rational, log, sqrt,
                       Integer)
    from sympy.functions.elementary.hyperbolic import _peeloff_ipi

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    a = Symbol('a', real=True)
    b = Symbol('b', positive=True)
    # real "rest" terms x; kept symbolic/transcendental so coth(x)/tanh(x) stay
    # in canonical form and the argument is a genuine Add not collapsing to a
    # Number or a pure imaginary multiple.
    bases = [a, b, a + b, log(2), log(3), sqrt(2), Rational(3, 2),
             Integer(2), a + 1, b + log(2)]

    def gen_case(rng):
        x = rng.choice(bases)
        # k positive integer: even -> coth(m) is ComplexInfinity (true leg),
        # odd -> coth(m) == 0 (false leg). Both legs oversampled. Positive
        # multiples keep the argument out of the negative-coefficient
        # recursion that precedes the additive branch, so the real evaluator is
        # guaranteed to route through exactly the modeled branch.
        k = rng.randint(1, 24)
        m = Rational(k) * I * pi / 2
        return x, m

    # deterministic boundary catalogue (the F2P assertions + minimal legs).
    # F2P #1: coth(log(tan(2))) == coth(log(-tan(2))); the split yields
    #   x = log(-tan(2)), m = I*pi (even -> true leg -> coth(x)).
    # F2P #2: coth(1 + I*pi/2) == tanh(1); split x = 1, m = I*pi/2 (odd ->
    #   false leg -> tanh(1)).
    from sympy import tan
    boundary = [
        (log(-tan(2)), I * pi),
        (Integer(1), I * pi / 2),
        (a, I * pi),
        (a, I * pi / 2),
        (b, 2 * I * pi),
        (b, 3 * I * pi / 2),
        (log(2), I * pi),
        (sqrt(2), 5 * I * pi / 2),
    ]

    cases = list(boundary)
    for _ in range(N_RANDOM):
        cases.append(gen_case(rng))

    for x, m in cases:
        arg = x + m
        if not arg.is_Add:
            continue
        # the unchanged surrounding split; only the `if m:` branch is in scope
        xs, ms = _peeloff_ipi(arg)
        if ms == 0:
            continue
        # shadow: transliteration of implementation_cothReduce on the real split
        cothm = coth(ms)
        shadow = coth(xs) if cothm is S.ComplexInfinity else tanh(xs)
        # real patched evaluator over the whole argument
        try:
            real = coth(arg)
        except Exception as e:  # the fix's guarantee: never raises here
            disagreements += 1
            if disagreements <= 5:
                print(f"RAISED arg={arg}: {type(e).__name__}: {e}")
            checked += 1
            continue
        checked += 1
        if real != shadow:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH arg={arg} real={real} shadow={shadow}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
