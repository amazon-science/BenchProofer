#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10323 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`assembleBlock`)
              transliterated to Python over the *real* repo types via the
              mapping.md bijection (`List (List Char)` ↔ `List[str]` keeping
              per-line '\\n'; `Option Nat` ↔ int-or-None for `dedent`; `List Char`
              ↔ str for `prepend`/`append`). The composition is
                  joinLines (addSuffix (addPrefix (removeIndent indent body)))
              i.e. indentation removal on the BODY FIRST, then prepend, then
              append, then ''.join. The impl region has NO A-tagged callee in its
              COMPUTATION (the three filters are modeled deeply, R/I here and
              A-reference-checked by G-AX), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the real patched
              `LiteralIncludeReader.read()` run on a temp file holding the body,
              with the same dedent/prepend/append options. The harness applies
              patch.diff before this runs, so `read()` uses the fixed filter
              order (dedent before prepend/append).

They must agree on every input in the modeled domain (mapping.md §2: a list of
'\\n'-terminated body lines, integer-or-absent dedent, str-or-absent
prepend/append; no 'tab-width', no auto-dedent=None, no selection options — those
are upstream/unchanged and abstracted into `body`). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only (plus the
repo's own sphinx). The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import logging
import os
import random
import sys
import tempfile

# `dedent_lines` emits a "non-whitespace stripped by dedent" warning that does not
# alter the returned lines; silence it so the verdict line is the only output.
logging.disable(logging.CRITICAL)

from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader

SEED = 10323
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean's impl region, transliterated -------------

def remove_indent_line(n, line):
    dropped = line[n:]
    if dropped == '' and line.endswith('\n'):
        return '\n'
    return dropped


def remove_indent(n, lines):
    # removeIndent : None leaves lines untouched; int k maps each line
    if n is None:
        return list(lines)
    return [remove_indent_line(n, l) for l in lines]


def add_prefix(prefix_text, lines):
    if prefix_text == '':
        return list(lines)
    return [prefix_text + '\n'] + list(lines)


def add_suffix(suffix_text, lines):
    if suffix_text == '':
        return list(lines)
    return list(lines) + [suffix_text + '\n']


def join_lines(lines):
    return ''.join(lines)


def shadow_assemble(body, prefix_text, suffix_text, indent):
    """assembleBlock (body, prefixText, suffixText, indent) transliterated. The
    R/I shadow of the impl region: dedent the body FIRST, then prepend/append."""
    trimmed = remove_indent(indent, body)
    with_head = add_prefix(prefix_text, trimmed)
    with_tail = add_suffix(suffix_text, with_head)
    return join_lines(with_tail)


# --- the oracle: patch.diff's behaviour via the real patched read() ----------

def oracle_assemble(body, prefix_text, suffix_text, indent):
    """patch.diff's behaviour: the real patched LiteralIncludeReader.read() with
    the same options, over a temp file holding `body`. `read_file` reads the file
    with splitlines(True), reproducing `body` line-for-line (no 'tab-width'); the
    patched filter order then applies dedent -> prepend -> append -> ''.join."""
    options = {}
    if indent is not None:
        options['dedent'] = indent
    if prefix_text != '':
        options['prepend'] = prefix_text
    if suffix_text != '':
        options['append'] = suffix_text
    fd, name = tempfile.mkstemp(suffix='.txt')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(''.join(body))
        reader = LiteralIncludeReader(name, options, Config({}, {}))
        content, _ = reader.read()
        return content
    finally:
        os.unlink(name)


# --- fuzzing over the modeled domain (mapping.md §2) -------------------------

def _rand_body(rng):
    n = rng.randint(0, 6)
    lines = []
    for _ in range(n):
        k = rng.randint(0, 10)
        s = "".join(rng.choice(list(" abXY{}<>:#")) for _ in range(k))
        # the body comes from splitlines(True); every line but possibly the last
        # keeps its '\n'. Model that: newline on all but maybe the final line.
        lines.append(s + '\n')
    # occasionally drop the trailing newline of the last line (EOF without \n)
    if lines and rng.random() < 0.3:
        lines[-1] = lines[-1].rstrip('\n')
    return lines


def _rand_opt_text(rng):
    # str-or-absent: '' models absence (unchanged_required forbids an empty value)
    if rng.random() < 0.25:
        return ''
    k = rng.randint(1, 12)
    return "".join(rng.choice(list(" abXY{}<>:#")) for _ in range(k))


def _rand_dedent(rng):
    # int-or-absent; None (auto textwrap.dedent) is outside the modeled domain
    if rng.random() < 0.3:
        return None
    return rng.randint(0, 10)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    # the F2P scenario: body = literal.inc lines 9-11, dedent 2, prepend/append
    yield (['  def baz():\n', '      pass\n', '\n'], 'class Foo:', '# comment', 2)
    yield (['      <plugin>\n', '        <groupId>x</groupId>\n'], '      <plugin>', '', None)
    yield ([], 'p', 's', 2)                       # empty body
    yield ([''], '', '', 0)                        # single empty line, no options
    yield (['\n'], 'p', '', 1)                     # blank line kept
    yield (['    a\n', '    b\n'], '', '', 4)       # exact dedent
    yield (['  x\n'], '', '', 5)                    # over-dedent (line shorter)
    yield (['ab'], 'p', 's', None)                  # no dedent, no trailing nl
    yield (['    a\n'], 'keep me', 'keep me too', 2)  # prepend/append survive dedent
    yield (['  a\n', '  b\n'], 'a b', '', None)
    for _ in range(n):
        yield (_rand_body(rng), _rand_opt_text(rng), _rand_opt_text(rng),
               _rand_dedent(rng))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for body, p, s, d in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_assemble(body, p, s, d)
        oracle = oracle_assemble(body, p, s, d)
        if shadow != oracle:
            disagreements.append((body, p, s, d, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for body, p, s, d, sh, orc in disagreements:
            print("  body=%r prepend=%r append=%r dedent=%r shadow=%r oracle=%r"
                  % (body, p, s, d, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of assembleBlock agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
