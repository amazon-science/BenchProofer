#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-11445.

The changed operation is the per-line recognition that decides how many leading
lines of a document belong to the leading header block. model.py models this
operation DEEPLY (the @Pure `is_header_line` / `first_boundary` predicate over
code-point sequences, named here `is_header_line` to match model.py); it is NOT
hidden behind a consumed @ContractOnly axiom. This script validates that deep
model as an **A-reference**: it executes the REAL recogniser the gold patch
uses —

    re.compile(Body.patterns['field_marker']).match(line)

(`Body` from `docutils.parsers.rst.states`, the exact construction the patch
introduces) — and asserts that the deep model agrees with it on every input in
the modelled domain (boundary corpus + randomized fuzz).

Modelled domain (documented in mapping.md / refinement.md / model.py docstring):
a line is a sequence of Unicode code points NOT containing (a) the back-slash
escape character U+005C, nor (b) a newline U+000A or carriage-return U+000D.
  (a) The docutils field-marker grammar treats `\\` as an escape introducer
      (`\\.` consumes the next code point); the bundle does not model that
      escape.
  (b) The grammar's `$` anchor matches just before a trailing `\n`, so the real
      recogniser accepts e.g. `':a:\\n'` while the deep model (which treats a
      newline as an ordinary trailing code point) rejects it; the bundle does
      not model line-terminator semantics.
Neither restriction bites the inputs in scope: the modeled lines are the
individual lines a document is already split into (so they carry no embedded
newline/CR), and the header/role/heading lines never place a back-slash before
the closing colon. The fuzz alphabet therefore excludes back-slash, newline,
and carriage-return; the boundary corpus covers the F2P/P2P test lines and the
bug-discriminating role-as-heading line.

Imports nothing repo-specific: `re`/`random` are stdlib and `docutils` is the
third-party library the gold patch itself imports. Exit 0 iff the deep model
equals the real recogniser on every checked input.
"""
import random
import re
import sys

from docutils.parsers.rst.states import Body

# The exact recogniser the gold patch constructs and calls.
FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])

COLON = 58      # ':'
SPACE = 32      # ' '
BACKTICK = 96   # '`'
BACKSLASH = 92  # '\'  -- excluded from the modelled domain
NEWLINE = 10    # '\n' -- excluded from the modelled domain
CR = 13         # '\r' -- excluded from the modelled domain


# --- model.py deep model, transcribed in lock-step ---------------------------

def first_boundary(line, k):
    n = len(line)
    if k >= n:
        return n
    if line[k] == COLON and (k == n - 1
                             or line[k + 1] == SPACE
                             or line[k + 1] == BACKTICK):
        return k
    return first_boundary(line, k + 1)


def is_header_line(line):
    """Deep model from model.py (pure region), over a list of code points."""
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


# --- the check ---------------------------------------------------------------

def real_match(s):
    """The real docutils recogniser the gold patch calls, as a bool."""
    return bool(FIELD_NAME_RE.match(s))


def check_line(s):
    cps = [ord(ch) for ch in s]
    # Guard: every checked line must lie in the modelled domain (no back-slash,
    # no newline / carriage-return). The boundary corpus and fuzz alphabet are
    # both constructed to satisfy this; assert it so a future edit cannot
    # silently widen the check outside the domain the deep model claims.
    assert BACKSLASH not in cps and NEWLINE not in cps and CR not in cps, (
        "check_line called outside the modelled domain on %r" % (s,))
    model = is_header_line(cps)
    real = real_match(s)
    assert model == real, (
        "is_header_line deep model unsound on %r: docutils field_marker "
        "recogniser gives %r, deep model gives %r" % (s, real, model))


def main():
    # --- boundary corpus: the exact F2P / P2P test lines ---------------------
    corpus = [
        # real bibliographic field lines (must be field markers)
        ":title: test of SphinxFileInput",
        ":author: Sphinx team",
        # the bug discriminator: a role used as a section heading. The closing
        # colon is followed by a back-quote, NOT a space -> NOT a field line.
        ":mod:`foo`",
        ":mod:`mypackage2`",
        # body lines from the tests (never field markers)
        "----------",
        "",
        "hello",
        "hello Sphinx world",
        "Sphinx is a document generator",
        # additional adversarial boundaries over the grammar's corners
        ":a:",            # :name: at end of line
        ":a: ",           # :name: followed by a space
        ":a: x",          # :name: followed by space then text
        ":a:x",           # closing colon followed by non-space, non-backtick
        ": bad:",         # space right after the leading colon
        "::bad:",         # colon right after the leading colon
        ":x::y: z",       # internal colon (followed by non-space) then field
        ":x:`y`: z",      # earlier boundary colon (followed by backtick) wins
        ":= : x:",        # space before a candidate closing colon
        ":name with spaces: value",
        ":ref:`x` and more",
        "not a field line at all",
        ":",
        "::",
        ":a",
    ]
    for s in corpus:
        check_line(s)

    # --- randomized fuzz over the modelled domain ----------------------------
    # Alphabet biased toward the code points that drive the grammar: colon,
    # space, back-quote, tab, word chars, and the rST symbol set -- but NEVER
    # the back-slash, newline, or carriage-return (all outside the modelled
    # domain; see the module docstring).
    alphabet = list(" :`\tabxyz_-09.\"'!#=()/@[]~{}|+,;")
    assert "\\" not in alphabet
    assert "\n" not in alphabet and "\r" not in alphabet
    rng = random.Random(11445)
    n_fuzz = 200000
    for _ in range(n_fuzz):
        length = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(length))
        check_line(s)

    print("G-AX OK: is_header_line deep model == docutils field_marker "
          "recogniser on %d boundary + %d fuzz inputs (back-slash-free, "
          "newline-free domain)" % (len(corpus), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
