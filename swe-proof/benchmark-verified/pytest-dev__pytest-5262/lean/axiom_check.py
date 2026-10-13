#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model `stripBinary` against the REAL
builtin the post-patch property delegates to, `str.replace("b", "")`.

The proof consumes NO callee axiom (axioms region empty), but the mode-string
transformation is an A-reference (refinement.md row 4): the Lean `stripBinary`
(drop every 'b', keep the rest in order) is asserted to agree, string-by-string,
with the real builtin on boundaries + fuzz. This guards the deep model against
drift from the real transformation.

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import sys

SEED = 5262


def strip_binary_model(s: str) -> str:
    """The Lean `stripBinary`: keep every character except 'b', in order."""
    return "".join(c for c in s if c != "b")


def main() -> int:
    rng = random.Random(SEED)

    # Boundary strings: realistic modes + edges.
    fixed = ["", "b", "bb", "rb+", "rb", "wb", "wb+", "ab", "r", "w", "a",
             "rt", "abracadabra", "+b", "xb", "no_b_here", "\U0001f600b",
             "\x00b\x00", "B"]  # capital B must NOT be stripped

    # Mode-flavoured + arbitrary code-point fuzz.
    modey = "rwaxt+bB0123_"
    cases = list(fixed)
    for _ in range(50_000):
        n = rng.randint(0, 16)
        cs = []
        for _ in range(n):
            if rng.random() < 0.5:
                cs.append(rng.choice(modey))
            else:
                cp = rng.randint(0, 0x10ffff)
                if 0xd800 <= cp <= 0xdfff:   # surrogates can't appear in str ops
                    cp = 0x41
                cs.append(chr(cp))
        cases.append("".join(cs))

    mismatches = 0
    examples = []
    for s in cases:
        want = s.replace("b", "")   # REAL builtin
        got = strip_binary_model(s)
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append((s, got, want))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs str.replace('b', '')")
        for s, g, w in examples:
            print(f"  in={s!r} model={g!r} real={w!r}")
        return 1

    print(f"G-AX OK: stripBinary == str.replace('b', '') on all probes "
          f"(seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
