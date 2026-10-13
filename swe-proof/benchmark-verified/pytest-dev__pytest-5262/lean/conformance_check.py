#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_mode against
the patch.diff behaviour (the post-patch `mode` property).

The impl region is NOT all-A-tagged (it has I/R structure), so this runs a real
fuzz. The single A-reference op (the per-character drop of the binary indicator)
is left as the REAL builtin `str.replace("b", "")` — exactly what the post-patch
property calls. The shadow therefore reproduces the post-patch behaviour
op-for-op; we assert zero disagreements vs an independent reconstruction of the
patched property over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 5262           # pinned in mapping.md
N = 120_000           # >= 10^5

# Mode-flavoured characters oversampled so the discriminating clause ('b') and
# realistic mode strings are hit hard.
MODEY = list("rwaxt+b")
ORDINARY = [chr(c) for c in (
    list(range(0x20, 0x7f)) +          # printable ASCII
    [0x00, 0x09, 0x0a, 0x0d, 0xa0, 0x2028, 0x2029, 0x1f600, 0x10ffff]
)]
ALPHABET = MODEY * 6 + ORDINARY


def shadow(buffer_mode: str) -> str:
    """R/I shadow of implementation_mode.

    acc := []; for c in buffer_mode: if c != 'b': acc += c; return acc.
    The A-reference op (drop every 'b') is realised by the REAL builtin
    str.replace('b', '') on the whole string, i.e. the post-patch transform.
    """
    return buffer_mode.replace("b", "")


def patched_mode(buffer_mode: str) -> str:
    """Independent reconstruction of the post-patch property behaviour:
    `self.buffer.mode.replace("b", "")`."""
    acc = []
    for c in buffer_mode:
        if c != "b":
            acc.append(c)
    return "".join(acc)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (realistic mode strings + edges).
    fixed = ["", "b", "rb+", "rb", "wb", "wb+", "ab", "r", "w", "a", "rt",
             "bbb", "abracadabra", "+b", "xb", "\U0001f600b", "no_b_here"]
    cases = fixed + [
        "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 24)))
        for _ in range(N)
    ]

    for t in cases:
        got = shadow(t)
        want = patched_mode(t)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((t, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for t, g, w in examples:
            print(f"  in={t!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
