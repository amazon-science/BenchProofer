#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-20488.

The bundle models ONE routine: sanitising a value range `(lo, hi)` before it is
handed to a display norm (mapping.md). The soundness-critical decision the patch
changes is the lower-bound guard when a logarithmic scale is in use:

    post-patch:  if logScale and lo <= 0:  lo = floor

Pre-patch the guard was `lo < 0` (strict), so an exact-zero lower bound under a
log scale slipped through untouched and broke the log scale. The upper bound is
never modified.

ORACLE = faithful in-process replica of the POST-PATCH guard. SHADOW =
op-for-op transliteration of `implementation_boundedRange` (Solution.lean impl
region), per refinement.md. All legs are R (exact-rational refinement of float
bounds); there is no A-tagged op, so conf_skip = false.

stdlib-only. Pinned seed: 20488 (also in mapping.md).
"""
import random
import sys
from fractions import Fraction

SEED = 20488
N = 120_000


# --- ORACLE: faithful replica of the POST-PATCH sanitisation ------------------
def oracle(log_scale, floor, lo, hi):
    s_lo, s_hi = lo, hi
    if log_scale and s_lo <= 0:
        s_lo = floor
    return (s_lo, s_hi)


# --- SHADOW of implementation_boundedRange (the R leg) ------------------------
# Mirrors Solution.lean impl region exactly: take the lower bound, leave the
# upper bound, clamp the lower bound to floor iff logScale and lo <= 0.
def shadow(log_scale, floor, lo, hi):
    s_lo = lo
    s_hi = hi
    if log_scale and s_lo <= 0:
        s_lo = floor
    return (s_lo, s_hi)


def disagree(log_scale, floor, lo, hi):
    got = oracle(log_scale, floor, lo, hi)
    want = shadow(log_scale, floor, lo, hi)
    if got != want:
        return (log_scale, floor, lo, hi, got, want)
    return None


def _edge_cases():
    f = Fraction(1, 10**8)  # a positive epsilon-like floor
    cases = [
        # F2P scenario: log scale, exact-zero lower bound -> must clamp to floor
        (True, f, Fraction(0), Fraction(10**20)),
        # log scale, negative lower bound -> clamp
        (True, f, Fraction(-1), Fraction(10**20)),
        # log scale, strictly positive lower bound -> pass through
        (True, f, Fraction(1), Fraction(10**20)),
        # no log scale, non-positive lower bound -> pass through untouched
        (False, f, Fraction(0), Fraction(5)),
        (False, f, Fraction(-3), Fraction(5)),
        # no log scale, positive lower bound -> pass through
        (False, f, Fraction(2), Fraction(5)),
        # log scale, lower bound equal to floor (positive) -> pass through
        (True, f, f, Fraction(5)),
    ]
    return cases


def _rand_rat(rng):
    num = rng.randint(-1000, 1000)
    den = rng.randint(1, 1000)
    return Fraction(num, den)


def _rand_case(rng):
    log_scale = rng.random() < 0.5
    floor = Fraction(rng.randint(1, 1000), rng.randint(1, 10**6))  # strictly > 0
    lo = _rand_rat(rng)
    hi = _rand_rat(rng)
    # bias some cases to exact zero lower bound
    if rng.random() < 0.15:
        lo = Fraction(0)
    return log_scale, floor, lo, hi


def main() -> int:
    checked = 0
    for c in _edge_cases():
        d = disagree(*c)
        if d:
            print(f"DISAGREE edge: oracle={d[4]} shadow={d[5]} case={d[:4]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        c = _rand_case(rng)
        d = disagree(*c)
        if d:
            print(f"DISAGREE fuzz: oracle={d[4]} shadow={d[5]} case={d[:4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
