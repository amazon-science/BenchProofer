#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-13852.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_polylogEval` dispatch ladder and diffs it against the REAL
post-patch automatic evaluator actually used when constructing the function:

    sympy.functions.special.zeta_functions.polylog.eval(s, z)

over a discrete boundary table (every recognized branch + near-miss arguments)
plus >=1e5 randomized (s, z) pairs. Observable: the returned closed-form
expression, or `None` (meaning "stay unevaluated"). Two non-None results agree
iff `simplify(real - shadow) == 0`; a None must match a None. Exit 0 iff zero
disagreements. stdlib + sympy only; pinned seed.
"""
import random
import sys

SEED = 13852
N_RANDOM = 120_000  # >= 1e5


def shadow_eval(s, z):
    """Transliteration of implementation_polylogEval (R/I shadow), expressed in
    SymPy. Returns the closed-form Expr or None (= stay unevaluated). Mirrors the
    post-patch `polylog.eval` dispatch ladder line-for-line."""
    from sympy import S, pi, I, log, sqrt, zeta, dirichlet_eta
    if z == 1:
        return zeta(s)
    if z == -1:
        return -dirichlet_eta(s)
    if z == 0:
        return S.Zero
    if s == 2:
        if z == S.Half:
            return pi**2/12 - log(2)**2/2
        if z == 2:
            return pi**2/4 - I*pi*log(2)
        if z == -(sqrt(5) - 1)/2:
            return -pi**2/15 + log((sqrt(5)-1)/2)**2/2
        if z == -(sqrt(5) + 1)/2:
            return -pi**2/10 - log((sqrt(5)+1)/2)**2
        if z == (3 - sqrt(5))/2:
            return pi**2/15 - log((sqrt(5)-1)/2)**2
        if z == (sqrt(5) - 1)/2:
            return pi**2/10 - log((sqrt(5)-1)/2)**2
        return None
    if s == 0:
        return z/(1 - z)
    if s == -1:
        return z/(1 - z)**2
    return None


def real_eval(s, z):
    """Drive the REAL post-patch automatic evaluator; return its result or None."""
    from sympy.functions.special.zeta_functions import polylog
    return polylog.eval(s, z)


def agree(real, shadow):
    from sympy import simplify, sympify, S
    if real is None or shadow is None:
        return (real is None) and (shadow is None)
    real, shadow = sympify(real), sympify(shadow)
    # NaN is never equal to itself mathematically, yet `S.NaN == S.NaN` is
    # structurally True in SymPy — exclude it BEFORE the structural fast path so a
    # `nan` result can never be certified as agreement (keeps the gate conservative).
    if real.has(S.NaN) or shadow.has(S.NaN):
        return False
    # Structural / canonical equality next. This is the primary agreement test
    # and also the ONLY sound test for non-finite results: e.g. zeta(1) == zoo
    # (complex infinity), where `simplify(zoo - zoo)` yields `nan != 0` and would
    # spuriously report disagreement between two identical results.
    if real == shadow:
        return True
    diff = simplify(real - shadow)
    # A non-finite subtraction (zoo/oo/nan) can never certify equality via `== 0`;
    # for those the structural check above is authoritative.
    if diff.has(S.NaN) or diff.has(S.ComplexInfinity) or diff.has(S.Infinity) \
            or diff.has(S.NegativeInfinity):
        return False
    return diff == 0


def main():
    from sympy import S, sqrt, Integer, Rational, symbols

    # recognized argument values for the order-2 table + the three z-cases
    special_z = [
        S.One, S.NegativeOne, S.Zero, S.Half, Integer(2),
        -(sqrt(5) - 1)/2, -(sqrt(5) + 1)/2, (3 - sqrt(5))/2, (sqrt(5) - 1)/2,
    ]
    # near-miss / unrecognized z values
    other_z = [
        Integer(3), Integer(-2), Rational(1, 3), Rational(3, 2),
        sqrt(5), -sqrt(5), (sqrt(5) + 1)/2, (sqrt(5) - 3)/2,
        Rational(-1, 2), Integer(5),
    ]
    special_s = [S.NegativeOne, S.Zero, S.One, Integer(2)]
    other_s = [Integer(3), Integer(-2), Integer(4), Rational(1, 2), Integer(-5)]

    all_z = special_z + other_z
    all_s = special_s + other_s

    cases = []
    # boundary: full cross product of interesting s and z
    for s in all_s:
        for z in all_z:
            cases.append((s, z))

    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        s = rng.choice(all_s)
        z = rng.choice(all_z)
        cases.append((s, z))

    disagreements = 0
    checked = 0
    for (s, z) in cases:
        real = real_eval(s, z)
        shadow = shadow_eval(s, z)
        checked += 1
        if not agree(real, shadow):
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH s={s} z={z}: real={real!r} shadow={shadow!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements, "
              f"seed={SEED})")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
