#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_expandYear
against the patch.diff behaviour (the post-patch two-digit-year expansion block
of parse_http_date).

The impl region is entirely I/R content (integer arithmetic, no A-tagged op), so
this runs a real fuzz. The shadow reproduces the Lean impl's control flow
op-for-op:

    y = year                                  # let mut y := year
    if year < 100:                            # if year < 100 then
        current_century = current_year - (current_year % 100)
        if year - (current_year % 100) > 50:  # roll back to the past century
            y = y + current_century - 100
        else:
            y = y + current_century
    return y                                  # return y

The patched side is an independent reconstruction of the POST-patch block exactly
as written in patch.diff (operating on the `year` variable in place).

We assert zero disagreements over >=10^5 fuzzed (year, current_year) inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 11848          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(year: int, current_year: int) -> int:
    """R/I shadow of implementation_expandYear."""
    y = year
    if year < 100:
        current_century = current_year - (current_year % 100)
        if year - (current_year % 100) > 50:
            y = y + current_century - 100
        else:
            y = y + current_century
    return y


def patched_block(year: int, current_year: int) -> int:
    """Independent reconstruction of the POST-patch block from patch.diff."""
    if year < 100:
        current_century = current_year - (current_year % 100)
        if year - (current_year % 100) > 50:
            # year that appears to be more than 50 years in the future are
            # interpreted as representing the past.
            year += current_century - 100
        else:
            year += current_century
    return year


def main() -> int:
    rng = random.Random(SEED)

    # Deterministic boundary cases first (incl. the exact F2P discriminators
    # drawn from the regression test: (current_year, two-digit year, expected)).
    fixed = [
        (69, 2019), (70, 2019), (94, 2019),   # utcnow 2019: 2069, 1970, 1994
        (70, 2020), (71, 2020),               # utcnow 2020: 2070, 1971
        (0, 2048), (99, 2048),                # utcnow 2048: 2000, 1999
        (0, 2000), (50, 2000), (51, 2000),    # pivot edges at century start
        (49, 2049), (50, 2049), (51, 2049),
        (99, 1999), (0, 2099),
        (100, 2020), (1994, 2020), (2069, 2020),  # already-full years: unchanged
        (50, 2100), (50, 1900),               # other centuries
    ]

    cases = list(fixed)
    for _ in range(N):
        # two-digit years dominate (the modeled branch); also sample full years.
        if rng.random() < 0.85:
            year = rng.randint(0, 99)
        else:
            year = rng.randint(100, 4000)
        current_year = rng.randint(1, 4000)
        cases.append((year, current_year))

    disagreements = 0
    examples = []
    for year, current_year in cases:
        got = shadow(year, current_year)
        want = patched_block(year, current_year)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((year, current_year, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for y, cy, g, w in examples:
            print(f"  year={y} current_year={cy} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
