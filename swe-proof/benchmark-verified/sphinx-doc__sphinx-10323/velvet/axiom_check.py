#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10323.

Executes the REAL repo callees that the modeled function delegates to and asserts
that every observation matches the deep models encoded in Solution.lean. The three
boundary filters are UNCHANGED by the gold patch (only their order in the
`filters` list changes); each is modeled DEEPLY (not behind a consumed axiom), so
G-AX validates each deep model against the real routine.

  (A-reference) `removeIndent` (Solution.lean `removeIndent`/`removeIndentLine`,
      pure region) == the real `dedent_lines(lines, k)` for an integer k:
        line ↦ line[k:], with the special case that an emptied line that
        originally ended in '\\n' keeps a lone '\\n' (the "keep CRLF" branch).
  (A-reference) `addPrefix` == the real `LiteralIncludeReader.prepend_filter`:
        a non-empty prepend inserts `prepend + '\\n'` at the front.
  (A-reference) `addSuffix` == the real `LiteralIncludeReader.append_filter`:
        a non-empty append appends `append + '\\n'` at the end.

Imports the repo module `sphinx.directives.code` (the same module the gold patch
edits). The filters' BODIES are identical pre/post patch, so this check is valid
at base_commit and after the patch. Exit 0 iff every obligation holds.
"""
import logging
import random
import sys

# `dedent_lines` emits a "non-whitespace stripped by dedent" warning through the
# sphinx logger when a dedent crosses non-space text; that diagnostic does not
# alter the returned lines (what the model and F2P test observe), so silence it.
logging.disable(logging.CRITICAL)

from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader, dedent_lines


# --- Solution.lean `pure` region, transliterated (kept in lock-step) ---------

def remove_indent_line(n, line):
    """removeIndentLine n line."""
    dropped = line[n:]
    if dropped == '' and line.endswith('\n'):
        return '\n'
    return dropped


def remove_indent(n, lines):
    """removeIndent : None leaves lines untouched; int k maps each line."""
    if n is None:
        return list(lines)
    return [remove_indent_line(n, l) for l in lines]


def add_prefix(prefix_text, lines):
    """addPrefix."""
    if prefix_text == '':
        return list(lines)
    return [prefix_text + '\n'] + list(lines)


def add_suffix(suffix_text, lines):
    """addSuffix."""
    if suffix_text == '':
        return list(lines)
    return list(lines) + [suffix_text + '\n']


# --- real-callee adapters ----------------------------------------------------

def _reader(options):
    """A LiteralIncludeReader with the given options, used only to exercise its
    bound prepend_filter / append_filter (the filenames/file are never read)."""
    return LiteralIncludeReader('unused.txt', dict(options), Config({}, {}))


def real_dedent(k, lines):
    # the body of dedent_filter for an integer dedent value: dedent_lines(lines, k)
    return dedent_lines(list(lines), k)


def real_prepend(prefix_text, lines):
    opts = {} if prefix_text == '' else {'prepend': prefix_text}
    return _reader(opts).prepend_filter(list(lines))


def real_append(suffix_text, lines):
    opts = {} if suffix_text == '' else {'append': suffix_text}
    return _reader(opts).append_filter(list(lines))


# --- the checks --------------------------------------------------------------

def check_dedent_reference(k, lines):
    observed = real_dedent(k, lines)
    expected = remove_indent(k, lines)
    assert observed == expected, (
        "removeIndent deep model unsound for dedent=%r on %r: real dedent_lines "
        "gave %r, deep model gives %r" % (k, lines, observed, expected))


def check_prepend_reference(prefix_text, lines):
    observed = real_prepend(prefix_text, lines)
    expected = add_prefix(prefix_text, lines)
    assert observed == expected, (
        "addPrefix deep model unsound for prepend=%r on %r: real prepend_filter "
        "gave %r, deep model gives %r" % (prefix_text, lines, observed, expected))


def check_append_reference(suffix_text, lines):
    observed = real_append(suffix_text, lines)
    expected = add_suffix(suffix_text, lines)
    assert observed == expected, (
        "addSuffix deep model unsound for append=%r on %r: real append_filter "
        "gave %r, deep model gives %r" % (suffix_text, lines, observed, expected))


def _rand_line(rng):
    n = rng.randint(0, 8)
    body = "".join(rng.choice(list(" \tabXY{}<>")) for _ in range(n))
    return body + ('\n' if rng.random() < 0.85 else '')


def main():
    # --- boundary bodies --------------------------------------------------
    bodies = [
        [],
        [''],
        ['\n'],
        ['  \n'],
        ['      <plugin>\n'],
        ['  def baz():\n', '      pass\n', '\n'],
        ['    a\n', '    b\n', '    c\n'],
        ['x\n', '  y\n', '    z\n'],
        ['ab'],                       # no trailing newline
        [' ', '  ', '   '],           # short lines, no newline
        ['\n', '\n'],                 # blank lines kept
        ['        deep\n', 'x\n'],
    ]

    # --- removeIndent (A-reference) over integer dedents -------------------
    for body in bodies:
        for k in range(0, 9):
            check_dedent_reference(k, body)

    # --- addPrefix / addSuffix (A-reference) -------------------------------
    prefixes = ['class Foo:', '      <plugin>', '#', 'a b', ' leading', '']
    suffixes = ['# comment', '</plugin>', '', ' trailing', 'z']
    for body in bodies:
        for p in prefixes:
            check_prepend_reference(p, body)
        for s in suffixes:
            check_append_reference(s, body)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(10323)
    chars = list(" \tabXY{}<>:#")
    for _ in range(20000):
        body = [_rand_line(rng) for _ in range(rng.randint(0, 6))]
        check_dedent_reference(rng.randint(0, 10), body)
        p = "".join(rng.choice(chars) for _ in range(rng.randint(0, 10)))
        if rng.random() < 0.15:
            p = ''
        check_prepend_reference(p, body)
        s = "".join(rng.choice(chars) for _ in range(rng.randint(0, 10)))
        if rng.random() < 0.15:
            s = ''
        check_append_reference(s, body)

    print("G-AX OK: removeIndent (== dedent_lines), addPrefix (== prepend_filter) "
          "and addSuffix (== append_filter) deep models sound on %d boundary "
          "bodies + 20000 fuzz configurations" % len(bodies))
    return 0


if __name__ == "__main__":
    sys.exit(main())
