#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for mwaskom__seaborn-3069.

The bundle models ONE computation: the per-axis finalization decision added to
`Plotter._finalize_figure` (`seaborn/_core/plot.py`). Its Lean implementation
(`implementation_nominalAxis`) turns four observations about an axis —

    isY       : is this the vertical ("y") axis?
    isNominal : does the axis carry a Nominal/categorical scale?
    hasLimit  : did the user pin an explicit limit on the axis?
    nticks    : number of major tick marks (= number of categories)

— into two decisions: whether the grid is forced off, and whether the axis
extent is pinned (and to what (lo, hi)). The post-patch repo code:

    if isinstance(self._scales.get(axis_key), Nominal):
        axis_obj.grid(False, which="both")
        if axis_key not in p._limits:
            nticks = len(axis_obj.get_major_ticks())
            lo, hi = -.5, nticks - .5
            if axis == "y":
                lo, hi = hi, lo
            set_lim = getattr(ax, f"set_{axis}lim")
            set_lim(lo, hi, auto=None)

This script transliterates the R/I impl into Python (`shadow_axis`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch decision. Decisions are represented as
`(grid_hidden: bool, fixed_limit: (lo, hi) | None)`; coordinates are exact
half-integers represented as Python `Fraction` so the comparison is exact (the
Lean model uses `ℚ`).

We do NOT stand up matplotlib / the full Plot pipeline (heavy, and the modeled
value is a pure four-input decision). Both legs are total functions over
(isY, isNominal, hasLimit, nticks). The edge set enumerates the cross-product of
the three booleans with a curated boundary tick-count set — it contains the
discriminating nominal cases on both x and y axes — and the fuzz loop then
samples >=1e5 random tuples.

stdlib-only. Pinned seed: 3069 (also recorded in mapping.md).
"""
import sys
from fractions import Fraction

SEED = 3069
N = 120_000

# Boundary tick counts: empty axis, single category, the small counts the F2P
# tests use (3), and larger counts.
BOUNDARY_NTICKS = (0, 1, 2, 3, 5, 10, 100)


# --- ORACLE: the post-patch behavior, faithful in-process replica ----------
def oracle_axis(isY, isNominal, hasLimit, nticks):
    grid_hidden = False
    fixed_limit = None
    if isNominal:
        grid_hidden = True
        if not hasLimit:
            lo, hi = Fraction(-1, 2), Fraction(nticks) - Fraction(1, 2)
            if isY:
                lo, hi = hi, lo
            fixed_limit = (lo, hi)
    return (grid_hidden, fixed_limit)


# --- shadow of implementation_nominalAxis (the R/I leg) --------------------
# Mirrors Solution.lean branch-for-branch.
def shadow_axis(isY, isNominal, hasLimit, nticks):
    grid_hidden = False
    fixed_limit = None
    if isNominal:
        grid_hidden = True
        if not hasLimit:
            lo = Fraction(-1, 2)
            hi = Fraction(nticks) - Fraction(1, 2)
            if isY:
                fixed_limit = (hi, lo)
            else:
                fixed_limit = (lo, hi)
    return (grid_hidden, fixed_limit)


def disagree(isY, isNominal, hasLimit, nticks):
    got = oracle_axis(isY, isNominal, hasLimit, nticks)
    want = shadow_axis(isY, isNominal, hasLimit, nticks)
    if got != want:
        return ((isY, isNominal, hasLimit, nticks), got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # Edge set = three booleans x boundary tick counts (exhaustive over the
    # curated boundary set; contains the discriminating nominal cases for both
    # the x axis and the inverted y axis).
    for isY in (False, True):
        for isNominal in (False, True):
            for hasLimit in (False, True):
                for nticks in BOUNDARY_NTICKS:
                    d = disagree(isY, isNominal, hasLimit, nticks)
                    if d:
                        print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
                        print("status=fail")
                        return 1
                    checked += 1

    # Random fuzz over (isY, isNominal, hasLimit, nticks).
    rnd = _lcg(SEED)
    for _ in range(N):
        isY = (next(rnd) & 1) == 1
        isNominal = (next(rnd) & 1) == 1
        hasLimit = (next(rnd) & 1) == 1
        nticks = next(rnd) % 256  # 0..255 categories
        d = disagree(isY, isNominal, hasLimit, nticks)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
