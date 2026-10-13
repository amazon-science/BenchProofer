#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model (coordinate-wise scaling) against
the REAL repo callee that the post-patch behaviour delegates to, `Point.__mul__`.

The proof consumes NO callee axiom (axioms region empty), but the per-coordinate
scaling is an A-reference (refinement.md): the Lean `scaleSpec` (each coordinate
`x` mapped to `x * factor`, order preserved) is asserted to agree, coordinate by
coordinate, with the REAL `Point.__mul__` (which the gold `__rmul__` forwards to)
on boundaries + fuzz. This guards the deep model against drift from the real op.

Runs in-container against the repo's own sympy. exit 0 iff the property holds on
every observation.
"""
import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.environ.get("REPO_ROOT", os.getcwd()))

from sympy import Rational, Point  # noqa: E402

SEED = 17655


def to_rat(fr: Fraction):
    return Rational(fr.numerator, fr.denominator)


def model_scale(factor_fr: Fraction, coord_frs):
    """The Lean `scaleSpec factor coords` — each coordinate scaled, in order."""
    factor = to_rat(factor_fr)
    return tuple(to_rat(x) * factor for x in coord_frs)


def rand_frac(rng):
    num = rng.randint(-100, 100)
    den = rng.choice([1, 1, 1, 2, 3, 4, 5, 6, 7, 10, 100])
    return Fraction(num, den)


def main() -> int:
    rng = random.Random(SEED)

    fixed = [
        (Fraction(5), [Fraction(1), Fraction(1)]),
        (Fraction(5), [Fraction(1), Fraction(1), Fraction(1)]),
        (Fraction(0), [Fraction(7), Fraction(-3)]),
        (Fraction(-2), [Fraction(0), Fraction(0)]),
        (Fraction(1, 5), [Fraction(1), Fraction(1)]),
        (Fraction(11, 10), [Fraction(1), Fraction(2)]),
    ]
    cases = fixed + [
        # Point requires >= 2 coordinates.
        (rand_frac(rng), [rand_frac(rng) for _ in range(rng.randint(2, 4))])
        for _ in range(40_000)
    ]

    mismatches = 0
    examples = []
    for factor_fr, coord_frs in cases:
        factor = to_rat(factor_fr)
        pt = Point([to_rat(x) for x in coord_frs], evaluate=False)
        real = tuple(pt.__mul__(factor).args)   # REAL callee Point.__mul__
        got = model_scale(factor_fr, coord_frs)
        if got != real:
            mismatches += 1
            if len(examples) < 10:
                examples.append((factor_fr, coord_frs, got, real))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs Point.__mul__")
        for f, c, g, r in examples:
            print(f"  factor={f} coords={c} model={g} real={r}")
        return 1

    print(f"G-AX OK: scaleSpec == Point.__mul__ coordinate-wise on all probes "
          f"(seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
