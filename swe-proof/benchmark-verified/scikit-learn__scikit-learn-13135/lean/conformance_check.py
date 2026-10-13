#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-13135.

The bundle models ONE behavior (mapping.md): the cluster-centers -> bin-edges
computation in the `kmeans` branch of `KBinsDiscretizer.fit`. Given the cluster
centers, the column min and the column max, the post-patch routine produces the
bin edges as:

    centers.sort()
    bin_edges = (centers[1:] + centers[:-1]) * 0.5     # consecutive midpoints
    bin_edges = np.r_[col_min, bin_edges, col_max]

The ORACLE below is a faithful in-process replica of the POST-PATCH gold code
(numpy semantics, computed in exact rationals via fractions.Fraction so float
rounding cannot mask a disagreement). The SHADOW is the op-for-op transliteration
of `implementation_binEdges` (Solution.lean impl region), per refinement.md:
`cs.mergeSort (<=)` then `colMin :: (midpoints cs ++ [colMax])`.

`centers` here is an INPUT (produced upstream by the unchanged KMeans routine,
which the patch does not touch); we fuzz it directly. No callee is axiomatized
(G-AX = skip).

stdlib-only. Pinned seed: 13135 (also in mapping.md).
"""
import random
import sys
from fractions import Fraction

SEED = 13135
N = 120_000


# --- ORACLE: faithful replica of the POST-PATCH gold computation --------------
def oracle(centers, col_min, col_max):
    cs = sorted(centers)                      # centers.sort()  (ascending)
    mids = [(cs[i] + cs[i + 1]) / 2 for i in range(len(cs) - 1)]  # (c[1:]+c[:-1])*0.5
    return [col_min] + mids + [col_max]       # np.r_[col_min, mids, col_max]


# --- SHADOW of implementation_binEdges (the R legs) ---------------------------
def midpoints(cs):
    # mirrors the Lean `midpoints` fold: midpoints (a::b::rest) = (a+b)/2 :: ...
    out = []
    i = 0
    while i + 1 < len(cs):
        out.append((cs[i] + cs[i + 1]) / 2)
        i += 1
    return out


def shadow(centers, col_min, col_max):
    cs = sorted(centers)                      # cs.mergeSort (<=)
    return [col_min] + midpoints(cs) + [col_max]


def disagree(centers, col_min, col_max):
    got = oracle(centers, col_min, col_max)
    want = shadow(centers, col_min, col_max)
    if got != want:
        return ((centers, col_min, col_max), got, want)
    return None


def _enumerate_edge():
    F = Fraction
    cases = []
    # F2P-shaped: already-sorted ascending centers
    cases.append(([F(1), F(2), F(3), F(5)], F(0), F(10)))
    # the bug trigger: UNSORTED centers must still yield monotone edges
    cases.append(([F(5), F(1), F(3), F(2)], F(0), F(10)))
    # descending
    cases.append(([F(9), F(7), F(4), F(1)], F(0), F(10)))
    # duplicates
    cases.append(([F(2), F(2), F(2)], F(0), F(5)))
    # single center -> no interior midpoints
    cases.append(([F(3)], F(0), F(10)))
    # empty centers (degenerate) -> just [col_min, col_max]
    cases.append(([], F(0), F(10)))
    # negative / fractional centers
    cases.append(([F(-3, 2), F(5, 4), F(-7, 3), F(11, 8)], F(-5), F(5)))
    return cases


def main() -> int:
    checked = 0
    for centers, lo, hi in _enumerate_edge():
        d = disagree(centers, lo, hi)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        k = rng.randint(0, 8)
        centers = [Fraction(rng.randint(-50, 50), rng.randint(1, 8))
                   for _ in range(k)]
        lo = Fraction(rng.randint(-60, -10))
        hi = Fraction(rng.randint(10, 60))
        d = disagree(centers, lo, hi)
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
