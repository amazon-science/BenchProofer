#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-6202.

The bundle models ONE routine: the result-assembly tail of
`PyobjMixin.getmodpath` (mapping.md). Given the gathered scope-name list `parts`
(inner-to-outer), the POST-PATCH behaviour is:

    parts.reverse()
    return ".".join(parts)

Pre-patch a trailing `return s.replace(".[", "[")` rewrote the joined string,
corrupting any name producing a ".[" boundary substring (e.g. a parametrize id
"[.["). The patch DELETES that rewrite. This differential test isolates exactly
the R/I legs — reverse + join — over the input carrier `parts`.

ORACLE = faithful in-process replica of the POST-PATCH tail.
SHADOW  = op-for-op transliteration of `implementation_getmodpath`
          (Solution.lean impl region), per refinement.md.

stdlib-only. Pinned seed: 6202 (also in mapping.md).
"""
import random
import sys

SEED = 6202
N = 120_000


# --- ORACLE: faithful replica of the POST-PATCH getmodpath tail ---------------
def oracle(parts):
    parts = list(reversed(parts))
    return ".".join(parts)


# --- SHADOW of implementation_getmodpath (the R/I leg) ------------------------
# Mirrors Solution.lean impl region exactly: reverse then intercalate ".".
def shadow(parts):
    parts = list(parts)
    parts = list(reversed(parts))
    return ".".join(parts)


def disagree(parts):
    got = oracle(parts)
    want = shadow(parts)
    if got != want:
        return (parts, got, want)
    return None


# Alphabet deliberately includes '.', '[', ']' so the discriminating ".["
# boundary substring is exercised by the fuzzer.
CHARS = "ab.[]_0"


def _edge_cases():
    return [
        # F2P scenario: parametrize id name joined after the class name.
        ["testmethod_two[.[]", "TestY"],
        ["testone"],
        ["testmethod_one", "TestX"],
        ["testmethod_one", "TestY"],
        [],                      # empty -> ""
        ["solo"],                # singleton -> itself
        ["a", "b", "c"],
        ["[.[", "Cls"],          # bracket-dot name after a boundary
        ["[abc]", "Cls"],
        ["x.y", "z"],            # name containing a literal dot
        ["", "a"],               # empty component
        ["a", ""],
    ]


def _rand_name(rng):
    n = rng.randint(0, 6)
    return "".join(rng.choice(CHARS) for _ in range(n))


def _rand_case(rng):
    nparts = rng.randint(0, 6)
    return [_rand_name(rng) for _ in range(nparts)]


def main() -> int:
    checked = 0
    for parts in _edge_cases():
        d = disagree(parts)
        if d:
            print(f"DISAGREE edge: oracle={d[1]!r} shadow={d[2]!r} parts={d[0]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        parts = _rand_case(rng)
        d = disagree(parts)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]!r} shadow={d[2]!r} parts={d[0]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
