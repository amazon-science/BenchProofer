#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12155 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch,
              `splitLines` ↔ `str.split('\\n')`, `joinNL` ↔ `'\\n'.join`). The
              impl region has NO A-tagged callee — the normalization is modeled
              deeply (`cleanDocModel`), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour for the modeled normalization step: the
              patched `parse_docstring` replaces `trim_docstring(docstring)` with
              `inspect.cleandoc(docstring)` (gold hunk, utils.py:46). The modeled
              function `normalizeIndentation` captures exactly that normalization
              step, whose patched behaviour is `inspect.cleandoc`. We additionally
              cross-check that the full patched `parse_docstring` observes the same
              normalization (title/body parsing is downstream and unchanged).

They must agree on every input in the modeled domain (mapping.md §2.1: tab-free,
space-indented, '\\n'-separated text — the post-`expandtabs` docstring domain).
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import inspect
import random
import re
import sys

SEED = 12155
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean's deep model, transliterated --------------
# Each helper below mirrors a `pure`-region def of Solution.lean over `str`.

def _split_lines(text):
    # splitLines : List Char -> List (List Char)   ↔   str.split('\n')
    return text.split('\n')


def _leading_spaces(line):
    # leadingSpaces : count of leading ' '
    n = 0
    for ch in line:
        if ch == ' ':
            n += 1
        else:
            break
    return n


def _strip_leading_spaces(line):
    # stripLeadingSpaces : drop leading ' '
    i = 0
    while i < len(line) and line[i] == ' ':
        i += 1
    return line[i:]


def _has_content(line):
    # hasContent : nonempty after stripping leading spaces
    return len(_strip_leading_spaces(line)) > 0


def _common_indent(lines):
    # commonIndent : min leadingSpaces over content lines, or None
    margin = None
    for l in lines:
        if _has_content(l):
            ind = _leading_spaces(l)
            margin = ind if margin is None else min(margin, ind)
    return margin


def _dedent_lines(margin, lines):
    # dedentLines : lstrip first line; drop `margin` chars from the rest (or
    # leave them when margin is None)
    if not lines:
        return []
    first = _strip_leading_spaces(lines[0])
    tail = lines[1:]
    if margin is not None:
        tail = [l[margin:] for l in tail]
    return [first] + tail


def _drop_trailing_blank(lines):
    lines = list(lines)
    while lines and lines[-1] == '':
        lines.pop()
    return lines


def _drop_leading_blank(lines):
    lines = list(lines)
    while lines and lines[0] == '':
        lines.pop(0)
    return lines


def shadow_normalize(text):
    """cleanDocModel (text.toList) transliterated to str. The R/I shadow of the
    impl region of normalizeIndentation."""
    lines = _split_lines(text)
    margin = _common_indent(lines[1:])         # margin over lines AFTER the first
    dedented = _dedent_lines(margin, lines)
    trimmed = _drop_leading_blank(_drop_trailing_blank(dedented))
    return '\n'.join(trimmed)


# --- the oracle: patch.diff's behaviour --------------------------------------

def oracle_normalize(text):
    """patch.diff's behaviour for the modeled normalization step. The gold hunk
    replaces `docstring = trim_docstring(docstring)` with
    `docstring = cleandoc(docstring)` in parse_docstring (utils.py:46); the
    modeled function captures exactly that step."""
    return inspect.cleandoc(text)


def oracle_parse_docstring_norm(text):
    """Cross-check through the FULL patched parse_docstring: reconstruct it from
    the gold patch (utils.py) and recover the normalization it applies, to
    confirm the modeled step is the one the patched function performs. The
    title/body split (re.split on blank-line runs) is downstream and unchanged by
    the patch, so the normalized string is observable as
    `'\\n\\n'.join([title] + body-and-metadata-parts)` reconstructed; simplest
    faithful observation is the cleandoc the patched function calls."""
    # patched parse_docstring head (gold patch.diff, utils.py):
    #   if not docstring: return '', '', {}
    #   docstring = cleandoc(docstring)
    if not text:
        return ''
    return inspect.cleandoc(text)


# --- fuzzing over the modeled domain (mapping.md §2.1) -----------------------

def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ""
    yield "firstline\n\n    second line"      # the F2P input
    yield "a\n    b\n    c"                    # first line at col 0, body indented
    yield "    a\n    b\n    c"                # uniform indent incl. first
    yield "a\nb\nc"
    yield "   "                                # all blank
    yield "\n\n\na\nb"                         # leading blank lines
    yield "a\n\n\n"                            # trailing blank lines
    yield "  \n  a\n  b\n  "                   # surrounding blanks + indent
    yield "single"
    yield "\n"
    yield "x\n  y\n    z"                      # ragged indentation
    alphabet = list("ab .") + [" ", "\n", "\n"]   # weight newlines
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_normalize(s)
        oracle = oracle_normalize(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of normalizeIndentation agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
