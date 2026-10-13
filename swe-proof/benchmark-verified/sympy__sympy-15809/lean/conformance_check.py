#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-15809.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_min` / `implementation_max` skeletons (an R fold over comparable
extended-real args, starting from the neutral element `oo` / `-oo`) and diffs it
against the REAL patched `sympy.Min` / `sympy.Max` over a deterministic boundary
catalogue plus >=1e5 randomized draws.

Type bijection (mapping.md): finite arg <-> Rational; `oo` <-> S.Infinity;
`-oo` <-> S.NegativeInfinity. Empty arg list is the key fixed behavior:
shadow returns the neutral element (oo / -oo), and so must the real function.

Shadow (transliteration of implementation_min / implementation_max):
    min: acc = oo;  for x in args: acc = sympy.Min(acc, x);  return acc
    max: acc = -oo; for x in args: acc = sympy.Max(acc, x);  return acc
Both reduce all-comparable args to the same value the real Min/Max produce; the
empty case yields the identity, which is exactly the deleted-guard fix.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 15809
N_RANDOM = 120_000  # >= 1e5


def main():
    from sympy import Min, Max, Rational, S, oo

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def gen_arg(rng):
        r = rng.random()
        if r < 0.10:
            return S.Infinity
        if r < 0.20:
            return S.NegativeInfinity
        if r < 0.55:
            return Rational(rng.randint(-50, 50))
        q = rng.randint(1, 9)
        return Rational(rng.randint(-50, 50), q)

    def gen_args(rng):
        # oversample length 0 and 1 (the R/I discriminating legs)
        r = rng.random()
        if r < 0.20:
            n = 0
        elif r < 0.45:
            n = 1
        else:
            n = rng.randint(2, 6)
        return [gen_arg(rng) for _ in range(n)]

    # deterministic boundary catalogue first (the F2P assertions)
    boundary = [
        [],                                   # Min()==oo, Max()==-oo
        [Rational(3)],                        # Min(x)==x
        [S.Infinity],
        [S.NegativeInfinity],
        [Rational(1), Rational(2), Rational(3)],
        [Rational(3), Rational(2), Rational(1)],
        [S.Infinity, S.NegativeInfinity],
        [Rational(-7), S.Infinity, Rational(4)],
    ]
    cases = list(boundary)
    for _ in range(N_RANDOM):
        cases.append(gen_args(rng))

    for args in cases:
        # shadow reductions
        smin = S.Infinity
        for x in args:
            smin = Min(smin, x)
        smax = S.NegativeInfinity
        for x in args:
            smax = Max(smax, x)
        real_min = Min(*args)
        real_max = Max(*args)
        checked += 2
        if real_min != smin:
            disagreements += 1
            if disagreements <= 5:
                print(f"MIN MISMATCH args={args} real={real_min} shadow={smin}")
        if real_max != smax:
            disagreements += 1
            if disagreements <= 5:
                print(f"MAX MISMATCH args={args} real={real_max} shadow={smax}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
