#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-11445 (nagini).

Runs IN-CONTAINER with the gold patch already applied by the gate
(PYTHONPATH=/testbed). The bundle models ONE changed computation
(mapping.md §1): the leading field-block scan inside
`sphinx.util.rst.prepend_prolog` — the number of leading lines of a document
that the per-line recogniser accepts, i.e. the value `pos` reaches before the
insertion arithmetic runs.

SHADOW: the impl region of model.py, copied VERBATIM below with contracts
stripped (the model IS Python). `PSeq` becomes a plain tuple shim providing
`.drop(n)`; the @Pure helpers (`first_boundary`, `is_header_line`,
`leading_header_count`) copy over as plain functions; the proof-only lemma
calls (`lfc_reaches`, `lfc_all_markers`) become no-ops (they are ghost code:
their bodies only re-derive facts, they compute nothing).

REAL: `sphinx.util.rst.prepend_prolog` from the patched repo, driven on a
`StringList` copy of the document with a sentinel one-line prolog; the
observed scan length is recovered from where the sentinel lands (the splice
inserts a blank separator line before the prolog exactly when the scan length
is positive, so sentinel index i maps to length max(i - 1, 0)).

BRIDGE (mapping.md §2): a line `str` maps to a sequence of Unicode code
points (`ord`), the document to a sequence of such sequences. Modeled domain
restriction (mapping.md §2, refinement.md §A): lines contain no back-slash
(escape introducer the deep model does not model) and no newline /
carriage-return (line-terminator semantics the deep model does not model);
the fuzz alphabet and boundary corpus stay inside that domain, and every
checked line is asserted to.

Inputs: a boundary corpus of documents shaped like the F2P/P2P fixtures plus
100000 fuzzed documents (>= 1e5 total). Pinned seed: 114450.
Exit 0 iff zero disagreements; a disagreement prints the document and both
scan lengths and exits 1. stdlib only (plus the repo under test).
"""
import random
import sys

SEED = 114450
N_FUZZ = 100_000


# --- PSeq shim ----------------------------------------------------------------

class PSeqShim(tuple):
    """Plain-tuple stand-in for nagini's PSeq: indexing, len, and drop(n)."""

    def drop(self, n):
        return PSeqShim(self[n:])


def Assert(x):  # stripped contract call (kept callable so the impl region
    pass        # could be pasted with its Assert lines; those lines are
                # stripped below anyway)


def lfc_reaches(doc, p):
    """Ghost lemma from model.py: proof-only, computes nothing. No-op."""
    pass


def lfc_all_markers(doc):
    """Ghost lemma from model.py: proof-only, computes nothing. No-op."""
    pass


# --- model.py pure region, verbatim with contracts stripped --------------------

COLON = 58     # ':'
SPACE = 32     # ' '
BACKTICK = 96  # '`'


def first_boundary(line, k):
    if k >= len(line):
        return len(line)
    if line[k] == COLON and (k == len(line) - 1
                             or line[k + 1] == SPACE
                             or line[k + 1] == BACKTICK):
        return k
    return first_boundary(line, k + 1)


def is_header_line(line):
    if len(line) < 2:
        return False
    if line[0] != COLON:
        return False
    if line[1] == COLON or line[1] == SPACE:
        return False
    b = first_boundary(line, 2)
    if b >= len(line):
        return False
    if line[b - 1] == SPACE:
        return False
    return b == len(line) - 1 or line[b + 1] == SPACE


def leading_header_count(doc):
    if len(doc) == 0:
        return 0
    if not is_header_line(doc[0]):
        return 0
    return 1 + leading_header_count(doc.drop(1))


# --- model.py impl region, verbatim with contracts stripped --------------------
# (Invariant(...) lines and the trailing Assert stripped; the ghost lemma
#  calls remain as the no-ops defined above.)

def count_leading_header_lines(content):
    pos = 0
    while pos < len(content) and is_header_line(content[pos]):
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    lfc_all_markers(content)
    return pos
    # impl-end (verbatim copy ends here)


# --- bridge: str lines -> code-point sequences ----------------------------------

BACKSLASH = 92  # outside the modeled domain
NEWLINE = 10    # outside the modeled domain
CR = 13         # outside the modeled domain


def to_model_doc(body):
    doc = []
    for s in body:
        cps = tuple(ord(ch) for ch in s)
        assert BACKSLASH not in cps and NEWLINE not in cps and CR not in cps, (
            "input outside the modeled domain: %r" % (s,))
        doc.append(PSeqShim(cps))
    return PSeqShim(doc)


def shadow_pos(body):
    return count_leading_header_lines(to_model_doc(body))


# --- the REAL patched repo function ---------------------------------------------

from docutils.statemachine import StringList  # noqa: E402
from sphinx.util.rst import prepend_prolog    # noqa: E402

# One sentinel line; its characters are outside the fuzz alphabet and it never
# equals a corpus line, so it occurs exactly once in the spliced output.
SENTINEL = "<conf-check-sentinel-11445>"


def real_pos(body):
    """Observed leading field-block length: run the real patched
    prepend_prolog with a one-line sentinel prolog and recover the scan
    length from where the sentinel lands (a blank separator precedes it
    exactly when the length is positive)."""
    assert SENTINEL not in body
    sl = StringList(list(body), source="<conf>")
    prepend_prolog(sl, SENTINEL)
    out = list(sl)
    assert out.count(SENTINEL) == 1, out
    i = out.index(SENTINEL)
    return i - 1 if i > 0 else 0


# --- input generation ------------------------------------------------------------
# Alphabet excludes back-slash, newline, carriage-return (modeled domain) and
# the sentinel's angle brackets.
ALPHABET = list(" :`\tabxyz_-09.\"'!#=()/@[]~{}|+,;")
assert "\\" not in ALPHABET and "\n" not in ALPHABET and "\r" not in ALPHABET
assert "<" not in ALPHABET and ">" not in ALPHABET


def rand_line(rng):
    length = rng.randint(0, 14)
    if rng.random() < 0.6:
        # bias toward colon-leading lines to exercise the recogniser
        return ":" + "".join(rng.choice(ALPHABET) for _ in range(length))
    return "".join(rng.choice(ALPHABET) for _ in range(length))


def rand_body(rng):
    n = rng.randint(0, 6)
    return [rand_line(rng) for _ in range(n)]


BOUNDARY_DOCS = [
    # F2P-shaped: a role used as a first-line heading, then body
    [":mod:`foo`", "-" * 10, "", "hello"],
    [":mod:`mypackage2`", "-" * 17, "", "content"],
    # F2P-shaped: real field lines, then a role heading
    [":title: test of SphinxFileInput", ":author: Sphinx team", "",
     ":mod:`foo`", "----------", "", "hello"],
    # P2P-shaped: field lines then plain body
    [":title: test of SphinxFileInput", ":author: Sphinx team", "",
     "hello Sphinx world", "Sphinx is a document generator"],
    ["hello Sphinx world", "Sphinx is a document generator"],
    # degenerate / edge documents
    [],
    [""],
    [":a:"],
    [":a: "],
    [":a:x"],
    [": bad:", "body"],
    ["::bad:", "body"],
    [":x::y: z", "body"],
    [":x:`y`: z", "body"],
    [":a:", ":b: v", ":c:", "body"],      # multi-line all-field prefix
    [":a:", ":b: v", ":c:"],              # entire document is field lines
    [":ref:`x` and more", "text"],
    [":name with spaces: value", "text"],
    [":= : x:", "text"],
    [":", "::", ":a"],
]


def main():
    rng = random.Random(SEED)
    checked = 0
    bad = []

    def check(body):
        nonlocal checked
        s = shadow_pos(body)
        r = real_pos(body)
        checked += 1
        if s != r:
            bad.append((body, r, s))
            return False
        return True

    for body in BOUNDARY_DOCS:
        check(body)

    for _ in range(N_FUZZ):
        check(rand_body(rng))
        if len(bad) >= 5:
            break

    if bad:
        print("G-CONF FAIL: %d disagreement(s) over %d checked documents"
              % (len(bad), checked))
        for body, r, s in bad:
            print("  doc=%r real_pos=%d shadow_pos=%d" % (body, r, s))
        return 1

    print("G-CONF pass: 0 disagreements over %d documents "
          "(%d boundary + %d fuzz, seed=%d): shadow of the contract-stripped "
          "impl region == real patched leading-scan length"
          % (checked, len(BOUNDARY_DOCS), checked - len(BOUNDARY_DOCS), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
