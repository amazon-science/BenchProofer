#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-26194.

The bundle models ONE behavior: the threshold-vector construction at the end of
`roc_curve` (mapping.md). The decreasing finite score thresholds produced upstream
by `_binary_clf_curve` (optionally thinned by `drop_intermediate`) are UNCHANGED
by the patch and orthogonal to the fix, so they enter as the grounded input `ts`
(a list of decreasing rationals; the real repo always supplies a non-empty one,
but the modeled construction is total — `np.r_[np.inf, []]` is `[inf]`). The
modeled value is the returned threshold vector built from `ts`.

Post-patch construction (the gold edit): the returned vector is the
positive-infinity sentinel followed by the finite score thresholds:

    thresholds = np.r_[np.inf, thresholds]      # -> [INF] + ts

Standing up numpy / the full roc_curve machinery to drive the real construction is
unnecessary: the modeled value is this pure prepend over the upstream thresholds.
So the ORACLE below is a faithful in-process replica of the POST-PATCH
construction, and the SHADOW is the op-for-op transliteration of
`implementation_rocCurveThresholds` (Solution.lean impl region), per
refinement.md.

A threshold entry is represented as the string "INF" for the np.inf sentinel
(Lean `Thr.posInf`) or as a Fraction for a finite value (Lean `Thr.finite q`),
matching the mapping.md bijection. This genuinely tests the soundness-critical
clause: the leading entry must be the INF sentinel (the F2P `np.isinf(thresholds[0])`),
not a finite `max(y_score)+1`.

stdlib-only. Pinned seed: 26194 (also in mapping.md).
"""
import random
import sys
from fractions import Fraction

SEED = 26194
N = 120_000

INF = "INF"  # Lean Thr.posInf / np.inf sentinel


# --- ORACLE: faithful in-process replica of the POST-PATCH construction -------
# thresholds = np.r_[np.inf, thresholds]
def oracle(ts):
    return [INF] + [Fraction(t) for t in ts]


# --- SHADOW of implementation_rocCurveThresholds (the R/I legs) ---------------
# Mirrors Solution.lean impl region exactly:
#   out := ts.map Thr.finite ; out := Thr.posInf :: out ; return out
def shadow(ts):
    out = [Fraction(t) for t in ts]   # ts.map Thr.finite
    out = [INF] + out                 # Thr.posInf :: out
    return out


def disagree(ts):
    got = oracle(ts)
    want = shadow(ts)
    if got != want:
        return (ts, got, want)
    return None


def _edge_cases():
    cases = []
    # empty tail: the construction is total; np.r_[np.inf, []] == [inf]
    cases.append([])
    # docstring example threshold tail (decreasing scores)
    cases.append([Fraction(8, 10), Fraction(4, 10), Fraction(35, 100), Fraction(1, 10)])
    # F2P drop_intermediate tails
    cases.append([Fraction(1), Fraction(7, 10), Fraction(0)])
    cases.append([Fraction(1), Fraction(9, 10), Fraction(7, 10), Fraction(6, 10), Fraction(0)])
    # singleton
    cases.append([Fraction(1, 2)])
    # head > 1 (would expose the pre-patch max+1 defect, but here only structure tested)
    cases.append([Fraction(5), Fraction(2), Fraction(0)])
    # head <= 1 (probability estimates)
    cases.append([Fraction(99, 100), Fraction(50, 100), Fraction(1, 100)])
    # negative / wide score scale
    cases.append([Fraction(18, 10), Fraction(-3), Fraction(-50)])
    return cases


def _rand_ts(rng):
    n = rng.randint(1, 30)
    # generate distinct decreasing rationals
    vals = set()
    while len(vals) < n:
        vals.add(Fraction(rng.randint(-1000, 1000), rng.choice([1, 2, 4, 5, 10, 100])))
    return sorted(vals, reverse=True)


def main() -> int:
    checked = 0
    for ts in _edge_cases():
        d = disagree(ts)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} ts={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        ts = _rand_ts(rng)
        d = disagree(ts)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} ts={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
