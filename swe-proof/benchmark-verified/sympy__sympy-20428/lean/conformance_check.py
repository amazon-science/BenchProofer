#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-20428.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_nonzero` skeleton and diffs it against the REAL patched callee
`ExpressionDomain.Expression.__bool__` over a curated catalogue of symbolic
expressions plus >=1e5 randomized draws.

  observable: bool(EX(expr)) -- the truthiness (nonzero) test of an EX domain
  element wrapping `expr`.
    - mathematically-zero value (expr.is_zero is True)  -> False (falsy)
    - everything else (is_zero False or None)           -> True  (truthy)

Bridge (mapping.md): for each real expr,
    is_math_zero    = (expr.is_zero is True)
    is_literal_zero = bool(expr == 0)
The shadow is `not is_math_zero` and must equal `bool(EX(expr))`.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240626
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_nonzero -------------------------------

def shadow_nonzero(is_literal_zero, is_math_zero):
    # transliteration of problem_spec_nonzero / implementation_nonzero:
    #   result = not isMathZero    (isLiteralZero is irrelevant to the result)
    return not is_math_zero


def main():
    from sympy import S, Symbol, sqrt, Rational, Integer
    from sympy.polys.domains import EX

    x = Symbol("x")
    y = Symbol("y")

    # Catalogue spanning the three-valued is_zero domain:
    #   - syntactic 0            (is_zero True,  == 0 True)
    #   - nonzero literals       (is_zero False, == 0 False)
    #   - math-zero, non-literal (is_zero True,  == 0 False)   <-- the bug case
    #   - undetermined symbolic  (is_zero None,  == 0 False)
    catalogue = [
        S(0), Integer(0), S.Zero,
        S(1), S(-1), S(5), S(-7), Rational(3, 4), Rational(-2, 9),
        sqrt(2), 1 + sqrt(2), x, y, x + y, x * y, x + 1, x - x + y,
        # mathematically zero but not syntactically the atom 0:
        sqrt(2) ** 2 - 2,
        (x + 1) ** 2 - x ** 2 - 2 * x - 1,
        sqrt(8) - 2 * sqrt(2),
        x - x,
        Rational(1, 3) + Rational(2, 3) - 1,
        (sqrt(3) + 1) * (sqrt(3) - 1) - 2,
        # the issue's coefficient shape (nested radicals summing to zero):
        sqrt(9165) * 0 + (24201 + 253 * sqrt(9165)) - 24201 - 253 * sqrt(9165),
    ]

    def flags_and_real(expr):
        e = EX(expr)
        is_math_zero = (expr.is_zero is True)
        is_literal_zero = bool(expr == 0)
        real = bool(e)                       # the REAL patched __bool__
        return is_literal_zero, is_math_zero, real

    disagreements = 0
    checked = 0
    # cache real observation per expr identity (srepr) so 1e5 draws stay fast
    cache = {}

    def check(expr):
        nonlocal disagreements, checked
        key = repr(expr)
        if key not in cache:
            cache[key] = flags_and_real(expr)
        is_lit, is_math, real = cache[key]
        exp = shadow_nonzero(is_lit, is_math)
        checked += 1
        if real != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH expr={expr!r} is_lit={is_lit} is_math={is_math} "
                      f"real={real!r} shadow={exp!r}")
        # invariant check (mapping.md precondition): literal zero => math zero
        if is_lit and not is_math:
            disagreements += 1
            if disagreements <= 5:
                print(f"PRECOND-VIOLATION expr={expr!r} literal-zero but not math-zero")

    # full catalogue sweep
    for expr in catalogue:
        check(expr)

    # randomized draws: random sums/products/differences of catalogue atoms,
    # including deliberately-cancelling combinations to hit the math-zero branch
    atoms = [S(0), S(1), S(2), S(-3), sqrt(2), sqrt(3), sqrt(5), x, y,
             Rational(1, 2), Rational(2, 3), 24201 + 253 * sqrt(9165)]
    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        r = rng.random()
        if r < 0.30:
            a = rng.choice(atoms)
            expr = a - a                      # guaranteed math-zero, often non-literal
        elif r < 0.55:
            a = rng.choice(atoms)
            b = rng.choice(atoms)
            expr = (a + b) - a - b            # cancelling
        elif r < 0.80:
            a = rng.choice(atoms)
            b = rng.choice(atoms)
            expr = a + b
        else:
            a = rng.choice(atoms)
            b = rng.choice(atoms)
            expr = a * b
        check(expr)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
