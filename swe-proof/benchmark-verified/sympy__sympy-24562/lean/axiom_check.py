#!/usr/bin/env python3
"""G-AX — validate the single A-reference op (decval: decimal digit string ->
integer) against the REAL behaviour it models: Python's integer parsing of the
same digit string (`int(q)`), which is what the post-patch constructor uses to
read the divisor argument.

decval is modeled deeply as the left-fold `acc*10 + d` over the digit list,
most-significant digit first. We assert it equals `int("".join(digits))` on
boundary + fuzz digit strings. stdlib-only; exit 0 iff sound.
"""
import random
import sys

SEED = 24562          # pinned in mapping.md
N = 50_000


def decval(digits):
    """Reference impl mirroring the Lean `decval` left-fold."""
    acc = 0
    for d in digits:
        acc = acc * 10 + d
    return acc


def main() -> int:
    rng = random.Random(SEED)
    violations = 0
    examples = []

    boundary = [
        [0], [1], [9],
        [1, 0, 0],         # "100"
        [0, 5],            # leading zero
        [9, 9, 9, 9],
        [1, 2, 3, 4, 5],
        [0, 0, 0],
    ]
    cases = boundary + [
        [rng.randint(0, 9) for _ in range(rng.randint(1, 6))]
        for _ in range(N)
    ]

    for digits in cases:
        got = decval(digits)
        want = int("".join(str(d) for d in digits))
        if got != want:
            violations += 1
            if len(examples) < 10:
                examples.append((digits, got, want))

    if violations:
        print(f"G-AX FAIL: {violations} violations")
        for ds, g, w in examples:
            print(f"  digits={ds} decval={g} int()={w}")
        return 1

    print(f"G-AX OK: decval == int(digit string) on {len(cases)} probes "
          f"(seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
