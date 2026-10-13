#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_encodeParams
against the patch.diff behaviour (the post-patch str/bytes branch of
`requests.models.RequestEncodingMixin._encode_params`).

The impl region is R/I (one I op: `return data`), so this runs a real fuzz.
The shadow reproduces the Lean impl op-for-op:
  return data            # I: the str/bytes payload is returned unchanged
We diff against an independent reconstruction of the patched Python branch
(`return data`) over >=10^5 fuzzed Datum inputs (text and binary values,
including non-ASCII content and empty).

A Datum is bridged via mapping.md:
  Datum.text   s  <->  a Python `str`   (s = list of code points)
  Datum.binary b  <->  a Python `bytes` (b = list of byte values 0..255)

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 2931           # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(datum):
    """R/I shadow of implementation_encodeParams: the identity on Datum.
    `datum` is a tagged tuple ('text', str) | ('binary', bytes)."""
    return datum


def patched_branch(datum):
    """Independent reconstruction of the post-patch str/bytes branch:
        if isinstance(data, (str, bytes)):
            return data
    The branch is the identity; we model it as such over the bridged value,
    preserving the kind tag (str vs bytes)."""
    kind, value = datum
    # `return data` returns the same object unchanged: same kind, same content.
    return (kind, value)


def random_text(rng):
    n = rng.randint(0, 20)
    # mix of ASCII and non-ASCII code points (non-ASCII is what crashed pre-patch)
    cps = []
    for _ in range(n):
        if rng.random() < 0.5:
            cps.append(rng.randint(0, 127))
        else:
            cps.append(rng.randint(128, 0x10FFFF))
            # avoid surrogate range for a valid str
            if 0xD800 <= cps[-1] <= 0xDFFF:
                cps[-1] = 0x20
    return ("text", "".join(chr(c) for c in cps))


def random_binary(rng):
    n = rng.randint(0, 20)
    return ("binary", bytes(rng.randint(0, 255) for _ in range(n)))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        ("text", ""),
        ("binary", b""),
        ("text", "foo"),
        ("binary", b"foo"),
        ("text", "ööö"),                 # non-ASCII text
        ("binary", "ööö".encode("utf-8")),  # the F2P payload (non-ASCII bytes)
        ("binary", bytes([0, 127, 128, 255])),
        ("text", "test=foo"),
        ("binary", b"test=foo"),
    ]
    cases = fixed + [
        (random_text(rng) if rng.random() < 0.5 else random_binary(rng))
        for _ in range(N)
    ]

    for datum in cases:
        got = shadow(datum)
        want = patched_branch(datum)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((datum, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for d, g, w in examples:
            print(f"  datum={d!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
