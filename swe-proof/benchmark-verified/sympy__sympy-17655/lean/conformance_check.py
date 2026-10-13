#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_scaleByFactor
against the patch.diff behaviour (post-patch left scalar-by-point multiply).

The impl region is NOT all-A-tagged (it has I/R structure: an accumulator loop
over the coordinate list). The single A-reference op (the per-coordinate scaling
`x * factor`) is realised by the REAL repo callee `Point.__mul__` — exactly what
the post-patch left-multiply delegates to. The shadow reconstructs the loop body
element-wise; the `patched` oracle runs the REAL post-patch behaviour (the gold
`__rmul__`, which forwards to `__mul__`). We assert zero disagreements over
>=10^5 fuzzed inputs.

Runs in-container against the repo's own sympy. exit 0 iff zero disagreements.
"""
import os
import random
import sys
from fractions import Fraction

# Run against the repo sympy (worktree / container repo root on sys.path).
sys.path.insert(0, os.environ.get("REPO_ROOT", os.getcwd()))

from sympy import Rational, Point, simplify  # noqa: E402

SEED = 17655          # pinned in mapping.md
N = 120_000           # >= 10^5


def _apply_gold_patch():
    """Install the gold fix: Point gains __rmul__ forwarding to __mul__.
    This is byte-for-byte the patch.diff behaviour."""
    def __rmul__(self, factor):
        """Multiply a factor by point's coordinates."""
        return self.__mul__(factor)
    Point.__rmul__ = __rmul__


def to_rat(fr: Fraction):
    return Rational(fr.numerator, fr.denominator)


def shadow(factor_fr: Fraction, coord_frs):
    """R/I shadow of implementation_scaleByFactor.

    acc := []; for x in coords: acc += [x * factor]; return some acc.
    The A-reference op (coordinate scaling) is realised by the REAL callee
    Point.__mul__ applied coordinate-wise via the same scalar multiply."""
    factor = to_rat(factor_fr)
    acc = []
    for x_fr in coord_frs:
        # one coordinate scaled by the factor: exactly the comprehension body of
        # Point.__mul__, `simplify(x*factor)` (the A-reference op).
        acc.append(simplify(to_rat(x_fr) * factor))
    return tuple(acc)


def patched(factor_fr: Fraction, coord_frs):
    """Independent oracle: the REAL post-patch left-multiply
    `factor * Point(coords)` (gold __rmul__ -> __mul__)."""
    factor = to_rat(factor_fr)
    pt = Point([to_rat(x) for x in coord_frs], evaluate=False)
    res = pt.__rmul__(factor)  # the gold __rmul__ (forwards to __mul__)
    return tuple(res.args)


def rand_frac(rng):
    num = rng.randint(-50, 50)
    den = rng.choice([1, 1, 1, 2, 3, 4, 5, 7, 10])
    return Fraction(num, den)


def main() -> int:
    _apply_gold_patch()
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    fixed = [
        (Fraction(5), [Fraction(1), Fraction(1)]),            # 5 * Point(1,1)
        (Fraction(5), [Fraction(1), Fraction(1), Fraction(1)]),  # 3D
        (Fraction(0), [Fraction(7), Fraction(-3)]),
        (Fraction(-2), [Fraction(0), Fraction(0)]),
        (Fraction(1, 5), [Fraction(1), Fraction(1)]),
        (Fraction(11, 10), [Fraction(1), Fraction(2)]),
    ]
    cases = fixed + [
        (rand_frac(rng),
         # Point requires >= 2 coordinates.
         [rand_frac(rng) for _ in range(rng.randint(2, 4))])
        for _ in range(N)
    ]

    for factor, coords in cases:
        got = shadow(factor, coords)
        want = patched(factor, coords)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((factor, coords, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for f, c, g, w in examples:
            print(f"  factor={f} coords={c} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
