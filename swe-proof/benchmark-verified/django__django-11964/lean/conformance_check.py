#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_memberStr
against the patch.diff behaviour (post-patch `Choices.__str__`).

The impl region is NOT all-A-tagged (it has R/I structure plus one A-reference),
so this runs a real fuzz. The A-reference op (the textual conversion of the
member's underlying value) is left as the REAL callee `str(value)` — exactly
what the post-patch `__str__` calls. The shadow therefore reproduces the
post-patch behaviour op-for-op; we assert zero disagreements vs an independent
reconstruction of the patched method (a real `enum.Enum` subclass whose
`__str__` returns `str(self.value)`) over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import enum
import random
import sys

SEED = 11964          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(value):
    """R/I shadow of implementation_memberStr.

    return pyStr(m.value); the A-reference op pyStr is realised by the REAL
    callee str(value), i.e. the post-patch conversion.
    """
    return str(value)


def patched_member_str(value):
    """Independent reconstruction of the post-patch django Choices.__str__:
    build a real enum member carrying `value` and a `__str__` returning
    str(self.value), then take str(member)."""
    class _Choices(enum.Enum):
        def __str__(self):
            return str(self.value)
    member = _Choices("M", {"M": value})["M"]  # one-member functional enum
    return str(member)


def rand_value(rng):
    """A fuzzed member value: text (str) or integral (int)."""
    if rng.random() < 0.5:
        # text value: random unicode string incl. empty
        n = rng.randint(0, 12)
        return "".join(chr(rng.randint(0x20, 0x2fff)) for _ in range(n))
    else:
        # integral value: negatives, zero, large
        return rng.randint(-10**6, 10**6)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (mirror the F2P enums' value kinds).
    fixed = ["first", "second", "FR", "SO", "M", "F", "X", "",
             1, 2, 3, 4, 0, -1, 100, 999999]
    cases = fixed + [rand_value(rng) for _ in range(N)]

    for v in cases:
        got = shadow(v)
        want = patched_member_str(v)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((v, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for v, g, w in examples:
            print(f"  value={v!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
