#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-11445.

Executes the REAL line-classifier the gold patch uses
(`re.compile(docutils.parsers.rst.states.Body.patterns['field_marker'])`) on a
boundary battery plus randomized fuzzing, and asserts that every observation
matches the deep model `isMetadataLine` / `metaScan` from Solution.lean's `pure`
region (transliterated below).

The one kind-A check:

  (A-reference) the deep model `is_metadata_line` (port of Solution.lean's
      `isMetadataLine`) == the real `FIELD_NAME_RE.match(line) is not None`.
      The changed classifier is modeled DEEPLY, not behind a consumed axiom;
      G-AX validates that deep model against the real callee over the grammar's
      full input space.

The real pattern (docutils, the same module the gold patch imports):

    Body.patterns['field_marker'] == r':(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)'

`re.match` anchors at the start of the line, so a leading cross-reference role
marker such as ':mod:`foo`' returns None (rejected) — the discriminator the
issue turns on — while a genuine field name such as ':author: x' matches.

Imports only stdlib `re` and `docutils` (already present in the instance image).
Exit 0 iff every obligation holds.
"""
import random
import re
import sys

from docutils.parsers.rst.states import Body

FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])


def real_match(line: str) -> bool:
    """The REAL post-patch classifier: FIELD_NAME_RE.match(line) is not None."""
    return FIELD_NAME_RE.match(line) is not None


# --- port of Solution.lean's deep model (pure region) ------------------------
# metaScan : List Char -> Char -> Bool   (iterative; tail-recursive in Lean)
def meta_scan(cs, prev):
    while True:
        if not cs:
            return False
        c, rest = cs[0], cs[1:]
        if c == ':':
            if not rest:
                return prev != ' '
            d = rest[0]
            if d == ' ':
                return prev != ' '
            elif d == '`':
                return False
            else:
                cs, prev = rest, c
                continue
        elif c == '\\':
            if not rest:
                return False
            ds = rest[1:]
            prev = rest[0] if rest else ' '   # cs.headD ' ' with cs = rest
            cs = ds
            continue
        else:
            cs, prev = rest, c
            continue


def is_metadata_line(line: str) -> bool:
    """Port of Solution.lean's isMetadataLine over a Python str."""
    cs = list(line)
    if len(cs) < 2:
        return False
    a, b = cs[0], cs[1]
    if a == ':' and b != ':' and b != ' ':
        return meta_scan(cs[1:], ':')
    return False


def check(line: str) -> None:
    obs = real_match(line)        # real callee
    model = is_metadata_line(line)  # deep model
    assert obs == model, (
        "isMetadataLine deep model unsound on %r: FIELD_NAME_RE.match gave %r, "
        "deep model gives %r" % (line, obs, model))


def main() -> int:
    # --- boundary battery -------------------------------------------------
    boundary = [
        "", ":", "::", ":a", ":a:", ":a: ", ":a: b",
        ":title: test of SphinxFileInput",
        ":author: Sphinx team",
        ":mod:`foo`",                 # the bug: a leading role marker
        ":mod:`mypackage2`",          # the F2P-test heading line
        "----------", "-" * 10, "hello", "",
        ":role:`x`", ":a:`x`", ":a:b:", ":a::b: ", ": :",
        ":a : ", ":a  :  ", ":a\\: b:", ":a\\ : ",
        ":x:", ":x: y", ":`x`:", ":a`b:", ":a`b: ",
        ":внешний:", ":a-b: c", ":a_b: c", ":123: x",
        ":a:\t", ":a: \t", ":\\: :", ":a\\:b: c",
    ]
    for s in boundary:
        check(s)

    # --- randomized fuzz over the grammar-relevant alphabet ---------------
    rng = random.Random(11445)
    alphabet = list(":\\` abcXYZ._0123") + ["é", "\t"]
    N = 200_000
    for _ in range(N):
        n = rng.randint(0, 14)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check(s)

    print("G-AX OK: isMetadataLine deep model (== FIELD_NAME_RE.match, the real "
          "docutils field_marker classifier) sound on %d boundary + %d fuzz "
          "lines" % (len(boundary), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())
