#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12155.

Executes the REAL stdlib callee (`inspect.cleandoc`) on inputs (boundary cases
over the indentation/blank-line behaviour, plus randomized fuzzing) and asserts
that every observation matches the deep model, as encoded in Solution.lean.

The one kind-A check:

  (A-reference) the deep model `clean_doc_model` (mirror of Solution.lean's
      `cleanDocModel` / `pure` region) == the real `inspect.cleandoc`. The
      changed normalization operation is modeled DEEPLY, not behind a consumed
      axiom; G-AX validates that deep model against the real callee:

        - split on '\\n';
        - margin = min over leading-space counts of the lines AFTER the first
          that have content (None if none);  <-- the behavioral fix
        - lstrip the first line; remove `margin` leading chars from the rest
          (leave them if margin is None);
        - drop trailing then leading blank lines;
        - rejoin with '\\n'.

Domain (mapping.md §2.1): `inspect.cleandoc` first does `doc.expandtabs()`, so
the modeled domain is the post-expandtabs, '\\n'-separated, space-indented text
that real Python docstrings reduce to. Fuzzing stays inside that domain (no raw
tabs / '\\r' / other Unicode spaces); inputs outside it are not claimed.

Imports nothing repo-specific: `inspect` is the Python standard library — the
same module the gold patch calls. Exit 0 iff every obligation holds.
"""
import inspect
import random
import sys


# --- Solution.lean `pure` region, transliterated (kept in lock-step) ---------

def _leading_spaces(line):
    n = 0
    for ch in line:
        if ch == ' ':
            n += 1
        else:
            break
    return n


def _strip_leading_spaces(line):
    i = 0
    while i < len(line) and line[i] == ' ':
        i += 1
    return line[i:]


def _has_content(line):
    return len(_strip_leading_spaces(line)) > 0


def _split_lines(text):
    return text.split('\n')


def _common_indent(lines):
    margin = None
    for l in lines:
        if _has_content(l):
            ind = _leading_spaces(l)
            margin = ind if margin is None else min(margin, ind)
    return margin


def _dedent_lines(margin, lines):
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


def clean_doc_model(text):
    """Reference implementation of Solution.lean's deep model `cleanDocModel`."""
    lines = _split_lines(text)
    margin = _common_indent(lines[1:])
    dedented = _dedent_lines(margin, lines)
    trimmed = _drop_leading_blank(_drop_trailing_blank(dedented))
    return '\n'.join(trimmed)


# --- the check ---------------------------------------------------------------

def check_reference(s):
    """Assert the deep model clean_doc_model(s) == the REAL inspect.cleandoc(s)."""
    observed = inspect.cleandoc(s)            # real callee
    expected = clean_doc_model(s)             # deep model
    assert observed == expected, (
        "clean_doc_model deep model unsound on %r: inspect.cleandoc gave %r, "
        "deep model gives %r" % (s, observed, expected))


def main():
    # --- boundary cases ---------------------------------------------------
    boundary = [
        "",
        "firstline\n\n    second line",   # the F2P input
        "a\n    b\n    c",                # first line col 0, body indented (the fix)
        "    a\n    b\n    c",            # uniform indent including first
        "a\nb\nc",
        "   ",                            # all blank
        " ",
        "\n",
        "\n\n\na\nb",                     # leading blank lines
        "a\n\n\n",                        # trailing blank lines
        "  \n  a\n  b\n  ",              # surrounding blanks + indent
        "single",
        "x\n  y\n    z",                  # ragged indentation
        "      ",
        "a\n  \n  b",                     # blank middle line (no content) ignored
        "  a\n    b\n  c",
        "no_indent_first\n        big indent body",
    ]
    for s in boundary:
        check_reference(s)

    # --- randomized fuzz over the modeled domain --------------------------
    rng = random.Random(12155)
    # ordinary printables + space + newline (newline weighted to make multi-line)
    alphabet = list("abAB12. ") + [" ", "\n", "\n"]
    for _ in range(200000):
        n = rng.randint(0, 26)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_reference(s)

    print("G-AX OK: clean_doc_model deep model (== inspect.cleandoc) sound on "
          "%d boundary + 200000 fuzz inputs" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
