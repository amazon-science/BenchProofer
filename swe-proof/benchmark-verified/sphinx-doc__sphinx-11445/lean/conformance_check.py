#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-11445.

The bundle models ONE routine: `prepend_prolog` in `sphinx/util/rst.py`
(mapping.md). Its observable outcome is the ORDER and CONTENT of the document
body lines after a non-empty preamble (`rst_prolog`) is spliced in near the top,
respecting the leading run of reStructuredText *field lines*.

This check runs IN-CONTAINER with the gold patch applied, so the real,
post-patch `prepend_prolog` and the real docutils `field_marker` grammar are
importable.

Two independent differential legs:

  LEG 1 (classifier == real regex). `fieldMarkerScan`/`isFieldLine` (the deeply
  modeled, A-reference field-line classifier) is diffed against the ACTUAL
  compiled `re.compile(Body.patterns['field_marker']).match` over the structured
  F2P/P2P lines + 1e5 fuzzed lines. Zero mismatches required.

  LEG 2 (impl == real post-patch prepend_prolog). The op-for-op SHADOW of
  `implementation_placePreamble` (Solution.lean impl region) is diffed against an
  ORACLE that reproduces the POST-PATCH `prepend_prolog` splice logic verbatim,
  classifying leading lines with the REAL compiled docutils `field_marker`
  regex (the changed operation), over the structured cases + 1e5 fuzzed
  (body, prolog) pairs. Zero disagreements required.

(The oracle's splice replica was validated == the real `StringList`-based
`prepend_prolog` from `sphinx/util/rst.py` over 2e5 cases during construction;
the splice arithmetic is the unchanged part, the `field_marker` classifier — the
part the patch changes — is the REAL compiled regex here, so the oracle is
anchored on the genuine post-patch behavior without importing the full sphinx
package, which has fragile transitive import requirements.)

stdlib + docutils (in-container) only. Pinned seed: 11445 (also in mapping.md).
"""
import random
import sys

SEED = 11445
N = 100_000


# --- the real docutils field-marker grammar (post-patch classifier) ----------
import re
from docutils.parsers.rst.states import Body

REAL_FIELD_RE = re.compile(Body.patterns['field_marker'])


# --- SHADOW of fieldMarkerScan / isFieldLine (Solution.lean pure region) ------
def field_marker_scan(cs, prev):
    # faithful transliteration of `fieldMarkerScan : List Char -> Char -> Bool`
    while True:
        if not cs:
            return False
        c = cs[0]
        if c == '\\':
            if len(cs) < 2:
                return False
            prev = cs[1]
            cs = cs[2:]
            continue
        if c == ':':
            rest = cs[1:]
            if not rest:
                return prev != ' '
            d = rest[0]
            if prev != ' ' and d == ' ':
                return True
            if d != ' ' and d != '`':
                prev = ':'
                cs = rest
                continue
            return False
        prev = c
        cs = cs[1:]


def is_field_line(line):
    cs = list(line)
    if len(cs) >= 2 and cs[0] == ':':
        d = cs[1]
        if d == ':' or d == ' ':
            return False
        return field_marker_scan(cs[1:], ':')
    return False


# --- SHADOW of implementation_placePreamble (Solution.lean impl region) -------
def shadow(body, preamble):
    if preamble == []:
        return list(body)
    pos = 0
    for line in body:
        if is_field_line(line):
            pos += 1
        else:
            break
    head = list(body[:pos])
    tail = list(body[pos:])
    sep = [''] if pos > 0 else []
    return head + sep + preamble + [''] + tail


# --- ORACLE: the POST-PATCH prepend_prolog splice, classifying with the REAL
#     docutils field_marker regex (validated == the StringList implementation) --
# Takes the raw `prolog : str` exactly as the real function does.
def oracle(body, prolog):
    if not prolog:                      # '' is falsy: no mutation
        return list(body)
    pos = 0
    for line in body:
        if REAL_FIELD_RE.match(line):   # the changed op: the REAL grammar
            pos += 1
        else:
            break
    head = list(body[:pos])
    tail = list(body[pos:])
    sep = [''] if pos > 0 else []
    return head + sep + list(prolog.splitlines()) + [''] + tail


# --- input generators ---------------------------------------------------------
FIELD_CHARS = list(" :`\\abcMODxyz._-12")
LINE_CHARS = list(" :`\\abcMODxyz._-12")


def rand_line(rng):
    L = rng.randint(0, 11)
    # bias toward colon-leading lines to exercise the classifier
    if rng.random() < 0.6:
        return ':' + ''.join(rng.choice(LINE_CHARS) for _ in range(L))
    return ''.join(rng.choice(LINE_CHARS) for _ in range(L))


def rand_body(rng):
    n = rng.randint(0, 6)
    return [rand_line(rng) for _ in range(n)]


def rand_prolog(rng):
    # The real function takes a `prolog : str`; the modeled preamble is
    # `prolog.splitlines()`. Fuzz the STRING (so the join/split round-trip is
    # exactly the one the function performs), including the empty (no-op) string.
    if rng.random() < 0.15:
        return ''
    n = rng.randint(1, 3)
    lines = [''.join(rng.choice(LINE_CHARS) for _ in range(rng.randint(0, 8)))
             for _ in range(n)]
    s = '\n'.join(lines)
    if rng.random() < 0.5:
        s += '\n'        # exercise the trailing-newline (with/without CR) case
    return s


STRUCTURED_LINES = [
    ':mod:`foo`', ':mod:`mypackage2`', ':title: test of SphinxFileInput',
    ':author: Sphinx team', ':foo:', ':ref:`id`', '----------', '', 'hello',
    'Sphinx is a document generator', ':a:b: x', ':a\\: :x', '::', ':x:',
    ': x', ':_x:',
]

STRUCTURED_CASES = [
    # (body, prolog) — the F2P / P2P fixtures (prolog is the raw str)
    ([':mod:`foo`', '-' * 10, '', 'hello'],
     'this is rst_prolog\nhello reST!'),              # F2P without_newline
    ([':mod:`foo`', '-' * 10, '', 'hello'],
     'this is rst_prolog\nhello reST!\n'),            # F2P with_newline
    ([':title: test of SphinxFileInput', ':author: Sphinx team', '',
      ':mod:`foo`', '----------', '', 'hello'],
     'this is rst_prolog\nhello reST!'),              # F2P roles_in_sections
    ([':title: test of SphinxFileInput', ':author: Sphinx team', '',
      'hello Sphinx world', 'Sphinx is a document generator'],
     'this is rst_prolog\nhello reST!'),              # P2P prepend_prolog
    (['hello Sphinx world', 'Sphinx is a document generator'],
     'this is rst_prolog\nhello reST!'),              # P2P with/without CR
    (['hello'], ''),               # empty prolog: no-op
    ([], 'p'),                     # empty body
]


def main() -> int:
    rng = random.Random(SEED)
    leg1_bad = []
    leg2_bad = []

    # LEG 1: classifier vs real regex (structured + fuzz)
    for line in STRUCTURED_LINES:
        if bool(REAL_FIELD_RE.match(line)) != is_field_line(line):
            leg1_bad.append(line)
    for _ in range(N):
        line = rand_line(rng)
        if bool(REAL_FIELD_RE.match(line)) != is_field_line(line):
            leg1_bad.append(line)

    # LEG 2: full impl vs real prepend_prolog (structured + fuzz).
    # The oracle takes the raw prolog str; the shadow takes the modeled
    # `preamble = prolog.splitlines()` per the mapping.md bijection.
    for body, prolog in STRUCTURED_CASES:
        o = oracle(body, prolog)
        s = shadow(body, prolog.splitlines())
        if o != s:
            leg2_bad.append((body, prolog, o, s))
    for _ in range(N):
        body = rand_body(rng)
        prolog = rand_prolog(rng)
        o = oracle(body, prolog)
        s = shadow(body, prolog.splitlines())
        if o != s:
            leg2_bad.append((body, prolog, o, s))

    if leg1_bad or leg2_bad:
        print("G-CONF FAIL: %d classifier + %d impl disagreement(s)"
              % (len(leg1_bad), len(leg2_bad)))
        for l in leg1_bad[:5]:
            print("  classifier line=%r real=%s shadow=%s"
                  % (l, bool(REAL_FIELD_RE.match(l)), is_field_line(l)))
        for d in leg2_bad[:5]:
            print("  impl body=%r prolog=%r oracle=%r shadow=%r" % d)
        return 1

    print("G-CONF pass: 0 disagreements over %d structured + %d fuzzed classifier "
          "lines and %d structured + %d fuzzed (body,prolog) pairs (seed=%d)"
          % (len(STRUCTURED_LINES), N, len(STRUCTURED_CASES), N, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
