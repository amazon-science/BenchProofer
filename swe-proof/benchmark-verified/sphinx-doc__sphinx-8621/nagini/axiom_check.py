#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8621.

The keystroke split is the changed operation; it is modelled DEEPLY in model.py
as the front-recursive fold `kparts` (a code point splits the text only when it
is flanked by a character on both sides; a flanked run of blank space collapses
into a single separator token).  There is NO consumed `@ContractOnly` axiom.
This script validates that deep model AGAINST the real callee -- the post-patch
regular expression that the gold patch installs:

    re.compile(r'(?<=.)(-|\\+|\\^|\\s+)(?=.)').split(text)

The check is the single kind-A obligation of this bundle:

  (A-reference) the deep model `kparts(codepoints, lead=False)` == the real
      `re.compile(NEW_PATTERN).split(text)` over the WHOLE modelled domain.

Modelled domain (enforced as a `Requires` clause in model.py, recorded in
mapping.md / refinement.md): printable ASCII, code points 32..126.  The only
blank-space character in that range is the ordinary space ' ' (32), so blank
runs are runs of spaces and the engine's `.`-vs-newline subtlety never arises.
This domain CONTAINS every FAIL_TO_PASS and PASS_TO_PASS test string (including
the blank-run case `M-x  M-s`), so the verified guarantee covers them.

Imports nothing repo-specific: `re` is the Python standard library -- the same
module the gold patch calls.  Exit 0 iff every obligation holds.
"""
import random
import re
import sys

# The exact post-patch pattern installed by patch.diff (gold).
NEW_PATTERN = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')

_SEP = {45, 43, 94}  # '-', '+', '^'
_SPACE = 32          # the only blank-space code point in printable ASCII


def is_sep(c):
    return c in _SEP


def is_space(c):
    return c == _SPACE


def in_domain(c):
    """The modelled domain: printable ASCII, code points 32..126."""
    return 32 <= c <= 126


def kparts(s, lead):
    """Reference reimplementation of model.py's deep model `kparts`, on a tuple
    of code points; returns a tuple of parts (each a tuple of code points).

    A flanked single separator '- + ^' is its own one-char token; a flanked
    blank space opens a blank token that merges with a following flanked blank
    space (the `\\s+` run-merging); any other code point is prepended to the
    first part of the split of the remainder."""
    n = len(s)
    if n == 0:
        return ((),)
    if n == 1:
        return (tuple(s),)
    c = s[0]
    if lead and is_sep(c):
        return ((), (c,)) + kparts(s[1:], True)
    if lead and is_space(c):
        rest = kparts(s[1:], True)
        if n >= 3 and is_space(s[1]):
            # next code point is a flanked blank space -> rest already opens a
            # blank token (rest[0] empty keystroke, rest[1] blank token): merge.
            return ((),) + ((c,) + rest[1],) + rest[2:]
        return ((), (c,)) + rest
    rest = kparts(s[1:], True)
    return ((c,) + rest[0],) + rest[1:]


def split_model(text):
    """The deep model rendered back as a list of substrings, for direct
    comparison with re.split."""
    cps = tuple(ord(ch) for ch in text)
    parts = kparts(cps, False)
    return [''.join(chr(c) for c in p) for p in parts]


def check_split_reference(text):
    """Assert the deep model == the REAL post-patch regex split on `text`."""
    assert all(in_domain(ord(ch)) for ch in text), \
        "test input outside modelled domain: %r" % (text,)
    observed = NEW_PATTERN.split(text)          # real callee (gold pattern)
    expected = split_model(text)                # deep model
    assert observed == expected, (
        "kparts deep model unsound on %r: real re.split gave %r, "
        "deep model gives %r" % (text, observed, expected))


# Every FAIL_TO_PASS and PASS_TO_PASS keystroke string the test suite feeds to
# the changed split (all are printable ASCII, in the modelled domain).
F2P_P2P_INPUTS = [
    "Alt+^",       # FAIL_TO_PASS: -> ['Alt', '+', '^']
    "-",           # FAIL_TO_PASS: -> ['-']
    "space",       # PASS_TO_PASS: -> ['space']
    "Control+X",   # PASS_TO_PASS: -> ['Control', '+', 'X']
    "M-x  M-s",    # PASS_TO_PASS (blank run!): -> ['M','-','x','  ','M','-','s']
]


def main():
    seps = ['-', '+', '^']
    space = [' ']
    letters = ['a', 'B', 'Z', '3', '9', 'x', 'S', 'h', 'i', 'f', 't',
               'C', 'o', 'n', 'r', 'l', 'A', 'M', 's', 'X']

    # --- the literal F2P / P2P discriminators must hold exactly -------------
    assert split_model("-") == ["-"], split_model("-")
    assert split_model("Alt+^") == ["Alt", "+", "^"], split_model("Alt+^")
    assert split_model("M-x  M-s") == ["M", "-", "x", "  ", "M", "-", "s"], \
        split_model("M-x  M-s")
    for t in F2P_P2P_INPUTS:
        check_split_reference(t)

    # --- boundary cases over the printable-ASCII domain (incl. blank runs) --
    boundary = [""]
    boundary += seps + space                          # each separator alone
    boundary += [c + c for c in seps + space]         # doubled separator/space
    boundary += [a + b for a in seps + space for b in seps + space]  # adj pairs
    boundary += [
        "Shift-+", "Alt+^", "Control+X", "Control-x", "space",
        "-x", "x-", "+a", "a+", "^z", "z^",
        " x", "x ", " x ", "a b", "a  b", "a   b", "  a", "a  ",
        "a- b", "a -b", "a - b", "a-  -b", "-  -", "  -  ",
        "a-+b", "a-b-c", "Ctrl-Alt-Del", "X", "ab",
        "----", "+-^", "^-+", "a^^b", "Shift-^-+",
        "M-x  M-s", "x x x", "ab  cd  ef",
    ]
    for t in boundary:
        check_split_reference(t)

    # --- randomized fuzz over the WHOLE printable-ASCII domain --------------
    # Includes the blank space (32) so blank-run merging is exercised, plus a
    # tail of arbitrary printable-ASCII code points to cover every character
    # the real callee can branch on within the modelled domain.
    rng = random.Random(8621)
    common = [ord(c) for c in (seps + space + letters)]
    for _ in range(200000):
        n = rng.randint(0, 14)
        cps = []
        for _ in range(n):
            if rng.random() < 0.55:
                cps.append(rng.choice(common))
            else:
                cps.append(rng.randint(32, 126))   # any printable ASCII
        t = "".join(chr(c) for c in cps)
        check_split_reference(t)

    print("G-AX OK: kparts deep model (== real re.compile(NEW).split) sound on "
          "%d boundary + 200000 fuzz inputs over the printable-ASCII domain "
          "(blank runs included); all FAIL_TO_PASS/PASS_TO_PASS keystroke "
          "strings confirmed, including the blank-run case 'M-x  M-s'."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
