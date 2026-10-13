#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_toBytestring
against the patch.diff behaviour (post-patch `make_bytes`).

The impl region is all I/R (no A-tagged op), so this runs a real fuzz. The
shadow reproduces the Lean impl's 4-way `match value` dispatch op-for-op; the
unchanged `encode` callee is realised by the real `str.encode(charset)`. We
assert zero disagreements against an independent reconstruction of the patched
`make_bytes` over >=10^5 fuzzed PyValue inputs.

A PyValue is fuzzed as a tagged tuple mirroring the Lean constructors:
  ("bytes", b)            -> bytes object b
  ("memoryview", b, r)    -> memoryview over b (its repr/str is ignored by post-patch)
  ("str", s)              -> str s
  ("other", obj)          -> arbitrary non-str/bytes object

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 11133          # pinned in mapping.md
N = 120_000           # >= 10^5

CHARSETS = ["utf-8", "latin-1", "ascii", "utf-16"]


def shadow(charset: str, value):
    """R/I shadow of implementation_toBytestring: 4-way match on the value kind.

    bytesV/memoryviewV return the underlying bytes; strV/otherV encode the
    text under charset (the unchanged `encode` callee)."""
    kind = value[0]
    if kind == "bytes":
        return value[1]                       # return b
    if kind == "memoryview":
        return value[1]                       # return underlying bytes b
    if kind == "str":
        return value[1].encode(charset)       # encode charset s
    # other
    return str(value[1]).encode(charset)      # encode charset text


def patched_make_bytes(charset: str, value):
    """Independent reconstruction of the POST-patch make_bytes body."""
    kind = value[0]
    if kind == "bytes":
        v = value[1]
    elif kind == "memoryview":
        v = memoryview(value[1])
    elif kind == "str":
        v = value[1]
    else:
        v = value[1]
    # post-patch body:
    if isinstance(v, (bytes, memoryview)):
        return bytes(v)
    if isinstance(v, str):
        return bytes(v.encode(charset))
    return str(v).encode(charset)


def rand_bytes(rng):
    return bytes(rng.randint(0, 255) for _ in range(rng.randint(0, 24)))


def rand_str(rng):
    # ASCII-ish so it encodes under every charset (incl. ascii/latin-1)
    return "".join(chr(rng.randint(0x20, 0x7e)) for _ in range(rng.randint(0, 24)))


def rand_other(rng):
    # non-str/non-bytes objects whose str() is ASCII-safe
    return rng.choice([
        rng.randint(-10_000, 10_000),
        rng.random() * 1000,
        rng.choice([True, False, None]),
        rng.randint(0, 5),
    ])


def rand_value(rng):
    # oversample the memoryview constructor (the discriminating case)
    k = rng.randint(0, 9)
    if k <= 3:
        return ("memoryview", rand_bytes(rng), rand_str(rng))
    if k <= 5:
        return ("bytes", rand_bytes(rng))
    if k <= 7:
        return ("str", rand_str(rng))
    return ("other", rand_other(rng))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (incl. the exact F2P input).
    fixed = [
        ("utf-8", ("memoryview", b"memoryview", "<memory at 0x7f00>")),
        ("utf-8", ("memoryview", b"", "<memory at 0x0>")),
        ("utf-8", ("memoryview", b"\x00\x01\xff", "view")),
        ("utf-8", ("bytes", b"My Content")),
        ("utf-8", ("bytes", b"")),
        ("utf-8", ("str", "My Content")),
        ("latin-1", ("str", "abc")),
        ("ascii", ("other", 12345)),
        ("utf-16", ("other", None)),
    ]
    cases = fixed + [
        (rng.choice(CHARSETS), rand_value(rng)) for _ in range(N)
    ]

    for charset, value in cases:
        got = shadow(charset, value)
        want = patched_make_bytes(charset, value)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((charset, value, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for cs, v, g, w in examples:
            print(f"  charset={cs} in={v!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
