#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12155.

The bundle models the indentation-normalization step the patched code performs
on a docstring before it is parsed (mapping.md). Pre-patch this was a hand-rolled
`trim_docstring`; the patch replaces it with the standard-library PEP 257
docstring cleaner. The modeled value is exactly the normalized block of lines.

The ORACLE is the REAL patched callee, `inspect.cleandoc`, run in-process. The
SHADOW is the op-for-op transliteration of `implementation_normalizeIndent` /
`normalizeIndentSpec` (per refinement.md), operating on the line-list carrier.

Bridge (mapping.md): a Python `str` docstring `s` is carried into the model as
`s.expandtabs().split('\n')` — a list of lines, each a list of characters — and
the normalized line-list is rejoined with '\n'. The real cleaner also expands
tabs and works per line, so comparing `'\n'.join(shadow_lines)` against
`inspect.cleandoc(s)` is the faithful end-to-end differential.

FAITHFULNESS NOTE (fix of the prior audit's Role-3 defect): `inspect.cleandoc`
uses Python `str.lstrip()` / the `not line` blank test, which act on the FULL
whitespace set (`str.isspace()` — space, `\t \n \r \v \f`, the ASCII file/group
separators, U+0085, NBSP, and the Unicode space separators), NOT the ASCII space
alone. The Lean model mirrors this via `isSpaceChar` over `whitespaceCodes`
(exactly those 29 code points). The fuzz alphabet below therefore includes
non-space whitespace (`\r \f \v \xa0`, a separator) so real, reachable inputs
(CRLF docstrings, form-feed page breaks, NBSP-led lines) are exercised.

This genuinely tests:
  * the F2P behavior: a block whose FIRST line is flush-left but whose later
    lines are indented must have the later lines dedented (the bug kept them);
  * non-space whitespace treated as whitespace (CRLF / formfeed / NBSP);
  * blocks with a fully-blank tail / lead (trailing & leading empty-line drop);
  * blank-but-nonempty lines not contributing to the common margin nor dropped;
  * the no-following-non-blank-line case (margin = none -> lines untouched).

stdlib-only. Pinned seed: 20240629 (also in mapping.md).
"""
import inspect
import random
import sys

SEED = 20240629
N = 120_000

# The whitespace code points Python's str.isspace()/str.lstrip() recognize.
# Mirrors `whitespaceCodes` in Solution.lean exactly.
WS = frozenset(c for c in range(0x110000) if chr(c).isspace())


# --- ORACLE: the REAL patched callee --------------------------------------
def oracle(s):
    return inspect.cleandoc(s)


# --- SHADOW of implementation_normalizeIndent (the R/I leg) ----------------
# Mirrors Solution.lean operating on lines = s.expandtabs().split('\n'):
#   isSpaceChar c   = ord(c) in WS
#   leadingWs l     = len(takewhile isSpaceChar)
#   lstripWs l      = l with leading whitespace removed
#   isBlank l       = lstripWs l == ''
#   margin          = min leadingWs over non-blank lines[1:], or None
#   out0            = [lstripWs lines[0]] ++ (lines[1:] dedented by margin)
#   out             = dropLeadingEmpty (dropTrailingEmpty out0)   (empty == '')
def _leading_ws(l):
    n = 0
    for c in l:
        if ord(c) in WS:
            n += 1
        else:
            break
    return n


def _lstrip_ws(l):
    return l[_leading_ws(l):]


def _is_blank(l):
    return _lstrip_ws(l) == ''


def _margin(rest):
    m = None
    for line in rest:
        if not _is_blank(line):
            ind = _leading_ws(line)
            m = ind if m is None else min(m, ind)
    return m


def shadow(s):
    lines = s.expandtabs().split('\n')
    rest = lines[1:]
    m = _margin(rest)
    if not lines:
        out = []
    else:
        first = _lstrip_ws(lines[0])
        if m is None:
            tail = rest
        else:
            tail = [l[m:] for l in rest]
        out = [first] + tail
    # drop completely empty lines from end, then from start
    while out and out[-1] == '':
        out.pop()
    while out and out[0] == '':
        out.pop(0)
    return '\n'.join(out)


def disagree(s):
    o = oracle(s)
    sh = shadow(s)
    if o != sh:
        return (s, o, sh)
    return None


EDGE = [
    'firstline\n\n    second line',   # F2P
    '',
    'hi\n\n  ',
    '  \n  x\n    y',
    '\n\n  a\n   b\n',
    'x',
    '   x',
    'a\n\n\n',
    '\n',
    '   \n   ',
    'title\n    indented\n        more',
    '\tfirst\n\tsecond',               # tabs -> expandtabs
    'a\n  \n  b',                       # blank-but-spaces middle line
    'only first indented\n',
    # non-space whitespace reachable inputs (the fixed defect):
    'Title line.\r\n\r\n    Body indented.\r\n',   # CRLF docstring
    'Summary.\n\x0c\n    Detail.',                 # form-feed page break
    '\x0c leading formfeed',                       # leading formfeed
    'line\n\xa0nbsp',                              # NBSP-led line
    'a\n\x0b\n    b',                              # vertical-tab blank line
    'head\n\x1c\n    tail',                        # ASCII file separator
]

# Alphabet includes non-space whitespace so the full lstrip/blank semantics is
# exercised, not just the ASCII space (the masked-bug fix).
CHARS = [' ', ' ', ' ', '\t', '\r', '\x0c', '\x0b', '\xa0', '\x1c',
         ' ', ' ', 'a', 'b', 'X', '.', ':', '`', '-', '\n', '\n']


def main() -> int:
    checked = 0
    for s in EDGE:
        d = disagree(s)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.randint(0, 24)
        s = ''.join(rng.choice(CHARS) for _ in range(n))
        d = disagree(s)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
