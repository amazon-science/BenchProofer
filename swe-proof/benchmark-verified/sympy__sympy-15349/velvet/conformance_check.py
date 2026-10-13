#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15349 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`sFactor` / `rotMatrix` / `toOrientationMatrix`) transliterated
              to Python over EXACT rational arithmetic (`fractions.Fraction`),
              via the mapping.md bijection (`Rat` ↔ SymPy `Rational`;
              `Option (Rat×Rat×Rat)` ↔ `None` / `(x,y,z)`; `List (List Rat)` ↔
              the matrix rows, row-major). The scaling factor is the exact
              reciprocal of the sum of squared components (the sqrt of
              `q.norm()**-2` cancels — mapping.md §3.1).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sympy.algebras.quaternion.Quaternion.to_rotation_matrix` applied
              at base_commit (the real correctness oracle, G-RESOLVE), read back
              as a row-major list of exact rationals.

There are no A-tagged callees (the operation is closed-form arithmetic), so the
shadow is pure R/I (`conf_skip = false`). They must agree on every
Requires-satisfying input (nonzero quaternion, i.e. a²+b²+c²+d² != 0), for BOTH
the no-point 3×3 form and the with-point 4×4 form. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib + sympy only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
from fractions import Fraction as F


SEED = 15349
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean sFactor/rotMatrix, transliterated ----------
def s_factor(a, b, c, d):
    """sFactor a b c d = (a^2+b^2+c^2+d^2)^{-1}, exact (mapping.md §3.1)."""
    return F(1, 1) / (a * a + b * b + c * c + d * d)


def shadow_rot_matrix(a, b, c, d, v):
    """rotMatrix a b c d v: the closed-form orientation matrix, transliterated
    component-for-component from Solution.lean (the patched m12 sign: c*d-b*a)."""
    s = s_factor(a, b, c, d)
    m00 = 1 - 2 * s * (c * c + d * d)
    m01 = 2 * s * (b * c - d * a)
    m02 = 2 * s * (b * d + c * a)
    m10 = 2 * s * (b * c + d * a)
    m11 = 1 - 2 * s * (b * b + d * d)
    m12 = 2 * s * (c * d - b * a)          # patched: minus sign
    m20 = 2 * s * (b * d - c * a)
    m21 = 2 * s * (c * d + b * a)
    m22 = 1 - 2 * s * (b * b + c * c)
    if v is None:
        return [[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]]
    x, y, z = v
    m03 = x - x * m00 - y * m01 - z * m02
    m13 = y - x * m10 - y * m11 - z * m12
    m23 = z - x * m20 - y * m21 - z * m22
    return [[m00, m01, m02, m03], [m10, m11, m12, m13],
            [m20, m21, m22, m23], [F(0), F(0), F(0), F(1)]]


def oracle_rot_matrix(a, b, c, d, v):
    """patch.diff's behaviour: the patched Quaternion.to_rotation_matrix, read
    back as a row-major list of exact Fractions so it is directly comparable to
    the shadow. Importing exercises the *patched* repo source (the harness
    applies patch.diff at base_commit before this runs)."""
    from sympy import Quaternion, Rational

    def rat(fr):
        return Rational(fr.numerator, fr.denominator)

    q = Quaternion(rat(a), rat(b), rat(c), rat(d))
    if v is None:
        M = q.to_rotation_matrix()
    else:
        x, y, z = v
        M = q.to_rotation_matrix((rat(x), rat(y), rat(z)))
    out = []
    for i in range(M.rows):
        row = []
        for j in range(M.cols):
            r = Rational(M[i, j])           # exact rational entry
            row.append(F(int(r.p), int(r.q)))
        out.append(row)
    return out


def rand_quat(rng):
    """A nonzero rational quaternion (a²+b²+c²+d² != 0)."""
    while True:
        comps = [F(rng.randint(-6, 6), rng.randint(1, 4)) for _ in range(4)]
        if sum(x * x for x in comps) != 0:
            return comps


def rand_point(rng):
    return tuple(F(rng.randint(-5, 5), rng.randint(1, 3)) for _ in range(3))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    # the F2P fixed example q1 = Quaternion(1,2,3,4), both forms
    yield (F(1), F(2), F(3), F(4), None)
    yield (F(1), F(2), F(3), F(4), (F(1), F(1), F(1)))
    # the issue's example family with rational stand-ins for cos/sin (b*a != 0
    # so the m12 sign is exercised): q = (a, b, 0, 0)
    yield (F(3, 5), F(4, 5), F(0), F(0), None)
    yield (F(3, 5), F(4, 5), F(0), F(0), (F(1), F(1), F(1)))
    yield (F(1), F(1), F(0), F(0), None)
    # unit and axis quaternions
    yield (F(1), F(0), F(0), F(0), None)
    yield (F(0), F(0), F(0), F(1), None)
    yield (F(1), F(1), F(1), F(1), None)
    yield (F(1), F(1), F(1), F(1), (F(0), F(0), F(0)))
    for _ in range(n):
        a, b, c, d = rand_quat(rng)
        v = None if rng.random() < 0.5 else rand_point(rng)
        yield (a, b, c, d, v)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for a, b, c, d, v in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_rot_matrix(a, b, c, d, v)
        oracle = oracle_rot_matrix(a, b, c, d, v)
        if shadow != oracle:
            disagreements.append((a, b, c, d, v, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for a, b, c, d, v, sh, orc in disagreements:
            print("  q=(%s,%s,%s,%s) v=%r shadow=%r oracle=%r"
                  % (a, b, c, d, v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of toOrientationMatrix (closed-form rational "
          "rotMatrix) agrees with patch.diff behaviour on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
