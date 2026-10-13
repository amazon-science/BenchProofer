#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8056.

Executes the REAL stdlib string callees the gold patch calls — `str.split(",")`
and `str.strip()` — on boundary inputs and randomized fuzzing, and asserts that
the two DEEP MODELS in Solution.lean's `pure` region agree with them
code-point-for-code-point. The changed string operations are modeled deeply
(no consumed axiom); G-AX validates each deep model against its real callee:

  (A-reference) `splitOnComma(s)` == `s.split(",")`
      str.split with an EXPLICIT separator keeps every piece, including empty
      ones between adjacent separators and at the ends, and returns [s] when
      there is no comma. (The run-collapsing/stripping behaviour is only the
      no-argument str.split, which the patch does not use.)

  (A-reference) `stripWs(s)` == `s.strip()`
      str.strip() with no argument trims leading/trailing whitespace over the
      FULL Unicode whitespace set (every code point c with chr(c).isspace()):
      the ASCII whitespace, the FS/GS/RS/US separator controls, NEL, NBSP, and
      the Unicode space/line/paragraph separators. The deep model `isWs`
      enumerates exactly that set (mapping.md §3.2); the fuzz alphabet includes
      every one of those code points so the deep model and the real callee are
      compared across the whole trimmed set (incl. U+00A0, the divergence a
      prior faithfulness audit found in the old ASCII-only model).

Imports only the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

# The FULL whitespace set the deep model `stripWs` trims (mapping.md §3.2):
# exactly the code points Python's no-arg str.strip() removes, enumerated with
# explicit escapes (no invisible literals).
_WS = ("\t\n\x0b\x0c\r"                      # ASCII whitespace controls
       "\x1c\x1d\x1e\x1f"                    # FS/GS/RS/US separator controls
       " \x85\xa0\u1680"                      # space, NEL, NBSP, ogham space
       "\u2000\u2001\u2002\u2003\u2004\u2005"  # en quad .. four-per-em space
       "\u2006\u2007\u2008\u2009\u200a"        # six-per-em .. hair space
       "\u2028\u2029\u202f\u205f\u3000")       # LS, PS, NNBSP, MMSP, ideographic
# Cross-check the enumeration against the real callee's own notion of
# whitespace over the whole Unicode range (must be EXACTLY equal).
assert set(_WS) == {chr(c) for c in range(0x110000) if chr(c).isspace()}, \
    "stripWs ws-set must equal the full str.strip() whitespace set"


def split_on_comma(s):
    """Reference implementation of Solution.lean's deep model `splitOnComma`,
    front-recursive, as a list of strings."""
    if s == "":
        return [""]
    c, cs = s[0], s[1:]
    if c == ",":
        return [""] + split_on_comma(cs)
    rest = split_on_comma(cs)
    if rest == []:        # unreachable (split_on_comma never returns []) — mirrors the Lean match arm
        return [c]
    return [c + rest[0]] + rest[1:]


def strip_ws(s):
    """Reference implementation of Solution.lean's deep model `stripWs`:
    drop leading and trailing chars in the enumerated `isWs` whitespace set
    (the full str.strip() set)."""
    i, j = 0, len(s)
    while i < j and s[i] in _WS:
        i += 1
    while j > i and s[j - 1] in _WS:
        j -= 1
    return s[i:j]


def check_split(s):
    assert split_on_comma(s) == s.split(","), (
        "splitOnComma deep model unsound on %r: str.split(',') gave %r, "
        "deep model gives %r" % (s, s.split(","), split_on_comma(s)))


def check_strip(s):
    assert strip_ws(s) == s.strip(), (
        "stripWs deep model unsound on %r: str.strip() gave %r, deep model "
        "gives %r" % (s, s.strip(), strip_ws(s)))


def main():
    # --- boundary inputs ---------------------------------------------------
    boundary = [
        "",
        "x1",
        "x1, x2",                 # the F2P case
        "x1,x2,x3",
        ",", ",,", "a,", ",a", "a,,b",
        "  x1  ",
        "\t x1 \n",
        " a , b , c ",
        "*args, **kwargs",
        "x1, x2 ",
        " ",
        "no_comma_here",
        "trailing,",
        ",leading",
        "a, b,c ,d",
        "x1,\xa0x2",              # NBSP after comma (the audit's divergence input)
        "\xa0x\xa0",              # NBSP at both ends
        "\x85x2",                 # NEL leading
        "\u2003a,\u2009b\u3000",  # em space / thin space / ideographic space
        "\u200bx",                # ZWSP is NOT whitespace -- must be kept
        "\u2028a\u2029,\u2028b",  # line/paragraph separators around a comma
    ]
    for s in boundary:
        check_split(s)
        check_strip(s)
        # composite: every comma-piece, stripped (the A4 expansion)
        for piece in s.split(","):
            check_strip(piece)

    # --- randomized fuzz over the declared domain --------------------------
    rng = random.Random(8056)
    letters = list("abcdefghijklmnopqrstuvwxyz0123456789_*")
    alphabet = list(_WS) + [","] + letters
    for _ in range(50000):
        n = rng.randint(0, 30)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_split(s)
        check_strip(s)
        for piece in s.split(","):
            check_strip(piece)

    print("G-AX OK: splitOnComma == str.split(',') and stripWs == str.strip() "
          "(deep models) sound on %d boundary + 50000 fuzz inputs over the "
          "full str.strip() whitespace set (incl. U+00A0 and the other "
          "non-ASCII whitespace code points)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
