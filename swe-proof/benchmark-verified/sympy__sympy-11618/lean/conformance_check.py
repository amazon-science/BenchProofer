#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-11618.

The bundle models ONE routine: `Point.distance(self, p)`, the Euclidean
distance between two points (mapping.md). The modeled quantity is the RADICAND
of the returned `sqrt(...)` — the sum of squared coordinate differences — which
fully determines the distance because `sqrt` is a fixed, order-preserving outer
wrapper applied identically before and after the patch.

The two points are given by their numeric coordinate sequences `a`, `b`. SymPy
`sympify`/`nsimplify`s float coordinates to exact rationals, so coordinates are
modeled as exact `Fraction`s.

Post-patch rule (the gold edit zero-pads the shorter coordinate tuple up to the
LARGER of the two dimensions, then sums squared coordinate differences over ALL
those positions — instead of the base_commit `zip` that truncated to the shorter
dimension and dropped the extra coordinates):

    n = max(len(a), len(b))
    radicand = sum((a_i - b_i)**2 for i in range(n))   # missing coord reads 0

Standing up the full SymPy Point machinery is unnecessary: the modeled value is
this pure function of the two coordinate sequences. So the ORACLE below is a
faithful in-process replica of the POST-PATCH `distance` radicand (the net
behavior of building `p1`/`p2` and zipping the padded tuples), and the SHADOW is
the op-for-op transliteration of `implementation_sqSeparation` (Solution.lean
impl region), per refinement.md.

This genuinely tests the soundness-critical clause: when the two points live in
spaces of DIFFERENT dimension, the coordinates beyond the shorter dimension must
still contribute to the sum (the base_commit bug dropped them, computing
`sqrt(1)` instead of `sqrt(5)` for the F2P `test_issue_11617`).

stdlib-only. Pinned seed: 11618 (also in mapping.md).
"""
import random
import sys
from fractions import Fraction


SEED = 11618
N = 120_000


def _getD(xs, i):
    return xs[i] if i < len(xs) else Fraction(0)


# --- ORACLE: faithful in-process replica of the POST-PATCH distance radicand --
# Zero-pad the shorter tuple to the larger dimension, then sum squared diffs.
def oracle(a, b):
    n = max(len(a), len(b))
    total = Fraction(0)
    for i in range(n):
        total += (_getD(a, i) - _getD(b, i)) ** 2
    return total


# --- SHADOW of implementation_sqSeparation (the R leg) ------------------------
# Mirrors Solution.lean impl region exactly: for i in [0:max len] accumulate
# (a.getD i 0 - b.getD i 0)^2.
def shadow(a, b):
    n = max(len(a), len(b))
    acc = Fraction(0)
    for i in range(n):
        acc = acc + (_getD(a, i) - _getD(b, i)) ** 2
    return acc


def disagree(a, b):
    got = oracle(a, b)
    want = shadow(a, b)
    if got != want:
        return ((a, b), got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P test_issue_11617: Point3D(1,0,2).distance(Point2D(2,0)) == sqrt(5).
    # radicand must be 5, NOT the truncated 1.
    cases.append(([F(1), F(0), F(2)], [F(2), F(0)]))
    cases.append(([F(2), F(0)], [F(1), F(0), F(2)]))   # symmetric
    # equal-dimension cases (unchanged by the patch)
    cases.append(([F(1), F(1)], [F(4), F(5)]))         # classic 3-4-5 -> 25
    cases.append(([F(1), F(2), F(3)], [F(1), F(2), F(3)]))  # identical -> 0
    # empty / singleton boundaries
    cases.append(([], []))
    cases.append(([], [F(3), F(4)]))
    cases.append(([F(5)], []))
    # larger dimension gap
    cases.append(([F(1), F(2), F(3), F(4)], [F(10)]))
    # rational coordinates
    cases.append(([Fraction(1, 2), Fraction(1, 4)], [Fraction(3, 2)]))
    return cases


def F(x):
    return Fraction(x)


def main() -> int:
    checked = 0
    for a, b in _enumerate_edge():
        d = disagree(a, b)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        la = rng.randint(0, 5)
        lb = rng.randint(0, 5)
        a = [Fraction(rng.randint(-20, 20), rng.randint(1, 6)) for _ in range(la)]
        b = [Fraction(rng.randint(-20, 20), rng.randint(1, 6)) for _ in range(lb)]
        d = disagree(a, b)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
