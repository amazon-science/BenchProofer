#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-15349.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_toRotationMatrix` skeleton (the R/I per-entry arithmetic) and
diffs it against the REAL patched `Quaternion.to_rotation_matrix` over a discrete
boundary catalogue plus >=1e5 randomized draws.

  observable: every entry of `q.to_rotation_matrix()` (3x3) and
  `q.to_rotation_matrix((x, y, z))` (4x4), for fuzzed rational quaternions `q`
  (with nonzero norm) and rational points `(x, y, z)`.

Shadow (transliteration of implementation_toRotationMatrix /
problem_spec_toRotationMatrix), s = 1/(a^2+b^2+c^2+d^2):
    m00 = 1 - 2s(c^2+d^2)   m01 = 2s(bc - da)   m02 = 2s(bd + ca)
    m10 = 2s(bc + da)       m11 = 1 - 2s(b^2+d^2) m12 = 2s(cd - ba)  # gold sign
    m20 = 2s(bd - ca)       m21 = 2s(cd + ba)   m22 = 1 - 2s(b^2+c^2)
    (4x4) m{i}3 = coord{i} - x*m{i}0 - y*m{i}1 - z*m{i}2 ; row3 = (0,0,0,1)

Exact rational arithmetic via fractions.Fraction (the test entries are exact
rationals, matching the Lean `Rat` model). Exit 0 iff zero disagreements.
stdlib-only fuzzing (pinned seed).
"""
import random
import sys
from fractions import Fraction as F


SEED = 15349
N_RANDOM = 120_000  # >= 1e5


def shadow(a, b, c, d, point):
    """Python shadow of implementation_toRotationMatrix using exact Fractions.
    Returns a dict {(i, j): value}. `point` is None or (x, y, z)."""
    s = F(1, 1) / (a * a + b * b + c * c + d * d)
    m00 = 1 - 2 * s * (c * c + d * d)
    m01 = 2 * s * (b * c - d * a)
    m02 = 2 * s * (b * d + c * a)
    m10 = 2 * s * (b * c + d * a)
    m11 = 1 - 2 * s * (b * b + d * d)
    m12 = 2 * s * (c * d - b * a)   # gold sign
    m20 = 2 * s * (b * d - c * a)
    m21 = 2 * s * (c * d + b * a)
    m22 = 1 - 2 * s * (b * b + c * c)
    M = {(0, 0): m00, (0, 1): m01, (0, 2): m02,
         (1, 0): m10, (1, 1): m11, (1, 2): m12,
         (2, 0): m20, (2, 1): m21, (2, 2): m22}
    if point is None:
        return M
    x, y, z = point
    rows = [(m00, m01, m02), (m10, m11, m12), (m20, m21, m22)]
    coord = (x, y, z)
    for i in range(3):
        r0, r1, r2 = rows[i]
        M[(i, 3)] = coord[i] - x * r0 - y * r1 - z * r2
    M[(3, 0)] = F(0); M[(3, 1)] = F(0); M[(3, 2)] = F(0); M[(3, 3)] = F(1)
    return M


def gen_quat(rng, small):
    lo, hi = (-3, 3) if small else (-9, 9)
    den = (1, 2, 3, 4, 5) if small else (1, 2, 3, 4, 5, 6, 7)
    while True:
        comps = [F(rng.randint(lo, hi), rng.choice(den)) for _ in range(4)]
        if sum(x * x for x in comps) != 0:
            return comps


def gen_point(rng, small):
    lo, hi = (-3, 3) if small else (-9, 9)
    den = (1, 2, 3) if small else (1, 2, 3, 4, 5)
    return tuple(F(rng.randint(lo, hi), rng.choice(den)) for _ in range(3))


def main():
    from sympy import Quaternion, Rational, nsimplify

    def to_sympy(fr):
        return Rational(fr.numerator, fr.denominator)

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    cases = []
    # deterministic boundary catalogue (rational analogues of the issue example)
    boundary_quats = [
        (F(1, 2), F(1, 2), F(0), F(0)),       # b only, a=b
        (F(1, 2), F(0), F(0), F(1, 2)),       # d only (docstring example shape)
        (F(1), F(0), F(0), F(0)),             # identity
        (F(1, 3), F(-2, 5), F(7, 4), F(1, 2)),
        (F(2), F(1), F(-1), F(3)),
    ]
    for q in boundary_quats:
        cases.append((q, None))
        cases.append((q, (F(1), F(1), F(1))))
        cases.append((q, (F(0), F(0), F(0))))

    for k in range(N_RANDOM):
        small = (k % 3 == 0)
        q = tuple(gen_quat(rng, small))
        point = None if (k % 2 == 0) else gen_point(rng, small)
        cases.append((q, point))

    for q, point in cases:
        a, b, c, d = q
        Q = Quaternion(to_sympy(a), to_sympy(b), to_sympy(c), to_sympy(d))
        if point is None:
            real = Q.to_rotation_matrix()
        else:
            real = Q.to_rotation_matrix(tuple(to_sympy(t) for t in point))
        exp = shadow(a, b, c, d, point)

        n = 3 if point is None else 4
        if real.rows != n or real.cols != n:
            disagreements += 1
            if disagreements <= 5:
                print(f"SHAPE MISMATCH q={q} point={point} "
                      f"got=({real.rows},{real.cols}) want={n}x{n}")
            continue
        for i in range(n):
            for j in range(n):
                want = exp[(i, j)]
                got = real[i, j]
                # got is a sympy Rational; compare exactly
                got_f = F(int(got.p), int(got.q))
                checked += 1
                if got_f != want:
                    disagreements += 1
                    if disagreements <= 5:
                        print(f"MISMATCH q={q} point={point} i={i} j={j}: "
                              f"real={got_f} shadow={want}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
