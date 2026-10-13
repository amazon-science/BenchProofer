#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_twoDigitYear
against the patch.diff behaviour (post-patch `DateFormat.y`).

The impl region is all I/R (no A-tagged callee), so this runs a real fuzz. The
shadow reproduces the Lean impl op-for-op: reduce the year modulo 100, take the
tens and units decimal digits, and render each as its ASCII character. We assert
zero disagreements vs an independent reconstruction of the patched function
(`'%02d' % (year % 100)`) over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13670          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(year: int) -> str:
    """R/I shadow of implementation_twoDigitYear.

    r := year % 100; tens := r // 10; ones := r % 10;
    return digitChar(tens) + digitChar(ones), where digitChar(d) = chr(48 + d).
    """
    r = year % 100
    tens = r // 10
    ones = r % 10
    return chr(48 + tens) + chr(48 + ones)


def patched_y(year: int) -> str:
    """Independent reconstruction of the post-patch django DateFormat.y():
    `'%02d' % (self.data.year % 100)`."""
    return '%02d' % (year % 100)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary / issue cases first.
    fixed = [0, 1, 4, 9, 10, 42, 76, 99, 100, 101, 123, 476, 999,
             1000, 1999, 2000, 2021, 9999]
    cases = list(fixed)
    # Oversample the below-1000 range (where the fix is observable) ...
    cases += [rng.randint(0, 999) for _ in range(N // 2)]
    # ... plus the full realistic datetime year range and beyond.
    cases += [rng.randint(1, 9999) for _ in range(N // 2)]

    for y in cases:
        got = shadow(y)
        want = patched_y(y)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((y, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for y, g, w in examples:
            print(f"  year={y!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
