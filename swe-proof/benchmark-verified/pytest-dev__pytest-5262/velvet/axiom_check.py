#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5262.

This bundle has NO consumed axiom. The one changed string operation — removing
the binary-stream marker from a mode descriptor — is modeled DEEPLY in
Solution.lean as the per-code-point fold `stripped` / `stripStep`, rather than
hidden behind an axiom about a callee. That deep model is an **A-reference**:
G-AX validates it against the REAL CPython string substitution it transliterates,
`str.replace("b", "")`, over boundary cases and randomized fuzzing.

  (A-reference) the deep model `stripped` (Solution.lean pure region) == the real
      `str.replace("b", "")`:
        'b'(98) -> removed (contributes nothing)
        every other code point -> identity, order preserved.

Imports nothing repo-specific: `str.replace` is a Python builtin — the same
operation the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys


def stripped(codepoints):
    """Reference implementation of Solution.lean's deep model `stripped`, as a
    list of code points: drop every 'b' (98), keep all others in order."""
    out = []
    for c in codepoints:
        if c == 98:            # ord('b')
            continue           # stripStep 'b' = []
        out.append(c)          # stripStep c = [c]
    return out


def check_strip_reference(s):
    """Assert the deep model stripped(s) == the REAL str.replace('b', '')."""
    observed = [ord(ch) for ch in s.replace("b", "")]        # real callee
    expected = stripped([ord(ch) for ch in s])               # deep model
    assert observed == expected, (
        "stripped deep model unsound on %r: str.replace('b','') gave %r, "
        "deep model gives %r" % (s, observed, expected))


def main():
    # --- boundary cases ------------------------------------------------------
    boundary = [
        "",                  # empty descriptor
        "b", "bb", "bbb",    # marker only (must collapse to empty)
        "r", "w", "a",       # text descriptors, no marker -> unchanged
        "r+", "w+", "a+",
        "rb", "wb", "ab",    # binary descriptors
        "rb+", "wb+", "ab+", # the exact mode the issue reports (rb+)
        "br", "bw", "b+",    # marker in non-trailing position
        "rbrb", "bxbxb",     # interleaved markers
        "+", "+b", "b+b",
        "B", "Rb", "rB",     # uppercase 'B' must NOT be stripped (case-sensitive)
        "0b", "b0",
    ]
    for s in boundary:
        check_strip_reference(s)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(5262)
    # alphabet weighted toward mode-descriptor code points, plus 'b'/'B' and
    # ordinary chars so we exercise the case-sensitivity boundary and overlap.
    alphabet = list("rwab+xtUB0 ") + ["b", "b", "b"] + ["é", "•"]
    for _ in range(20000):
        n = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_strip_reference(s)

    print("G-AX OK: stripped deep model (== str.replace('b','')) sound on %d "
          "boundary + 20000 fuzz descriptors; no consumed axioms."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
