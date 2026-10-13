#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12155 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Requires/Ensures/Invariant/Assert removed) and the @Pure
helpers copied over as plain functions. PSeq/ToSeq are shimmed by a small
tuple subclass providing take/drop/+; no @ContractOnly callees exist in this
bundle (the axioms region is empty).

ORACLE: the REAL patched repo callee the model models per mapping.md §1 —
the docstring-normalisation function bound in the patched
`django.contrib.admindocs.utils` module (`cleandoc`). It is fetched from that
module (PYTHONPATH=/testbed, gold patch already applied by the gate), so the
import itself is patch-dependent: the pre-patch module has no such binding.

Type bridge (mapping.md §2): a docstring str <-> a List[int] with one entry
per line of `docstring.expandtabs().split('\\n')` — a non-blank line maps to
its leading-whitespace count (>= 0), a blank (empty/whitespace-only) line to
the marker -1. Inputs are generated as concrete strings and summarised into
the carrier; the shadow runs on the summary, the real callee on the string,
and the real output string is summarised back to its per-line profile.

Bridge for the out-of-carrier post-step (mapping.md §3.1): the real callee
additionally pops leading/trailing lines that are EMPTY after the transform —
an unchanged post-step declared outside the carrier. The bridge simulates
exactly those pops on the shadow's output: a line is empty after the
transform iff (first line) it was blank, or (subsequent line) it was blank
and its concrete width does not exceed the removed amount. Whitespace-only
residue lines are NOT popped (they are non-empty strings), matching the real
callee's emptiness test. The joined-empty-output artifact ('' splits to
['']) is normalised to the empty profile on both sides via the '' check.

Input domain: any docstring str (the modeled function's Requires demands only
list access over the summary; the carrier image is exactly the summaries the
generator produces). Boundary set covers empty/single-line/all-blank inputs,
the failing-test shape (non-blank first line + indented body), blank-first
Django style, tabs, whitespace-only lines both shorter and longer than the
removed amount, and trailing/leading blank runs; fuzz mixes blank widths,
indents 0..12, tab/space indentation, and 0..8 lines.

>= 1e5 Requires-satisfying inputs: 26 boundary + 100000 fuzz docstrings.
Pinned fuzz seed: 12155.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 12155
N_FUZZ = 100_000


# --- PSeq/ToSeq shim (pure-sequence theory over plain tuples) ----------------

class Seq(tuple):
    def take(self, n):
        return Seq(tuple(self)[:n])

    def drop(self, n):
        return Seq(tuple(self)[n:])

    def __add__(self, other):
        return Seq(tuple(self) + tuple(other))


def PSeq(*xs):
    return Seq(xs)


def ToSeq(lst):
    return Seq(lst)


# --- @Pure helpers from model.py, decorators + contracts stripped ------------

def NO_AMOUNT():
    return -1


def min_indent_from(eff, k):
    if k >= len(eff):
        return NO_AMOUNT()
    rest = min_indent_from(eff, k + 1)
    if eff[k] >= 0:
        if rest < 0 or eff[k] < rest:
            return eff[k]
        return rest
    return rest


def clamp_margin(m):
    if m >= 0:
        return m
    return 0


def remove_margin(s, margin):
    if len(s) == 0:
        return PSeq(0).take(0)
    head = s[0] - margin
    if s[0] < 0:
        head = -1
    return PSeq(head) + remove_margin(s.drop(1), margin)


def first_line(x):
    if x < 0:
        return -1
    return 0


def dedented(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(first_line(s[0])) + remove_margin(
        s.drop(1), clamp_margin(min_indent_from(s, 1)))


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def dedent_block(eff):
    result = []  # type: List[int]
    n = len(eff)
    if n == 0:
        return result
    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
    i = n
    while i > 1:
        c = eff[i - 1]
        if c < 0:
            result = [-1] + result
        else:
            result = [c - margin] + result
        i = i - 1
    first = eff[0]
    if first < 0:
        result = [-1] + result
    else:
        result = [0] + result
    return result


# --- carrier bridges ----------------------------------------------------------

def to_eff(docstring):
    """Input summary: per-line leading-whitespace amounts (mapping.md §2)."""
    eff = []
    for line in docstring.expandtabs().split('\n'):
        content = len(line.lstrip())
        eff.append(-1 if content == 0 else len(line) - content)
    return eff


def profile_of(text):
    """Output summary of a concrete normalised string. '' means the line list
    emptied out (join of zero lines), i.e. the empty profile."""
    if text == "":
        return []
    out = []
    for line in text.split('\n'):
        content = len(line.lstrip())
        out.append(-1 if content == 0 else len(line) - content)
    return out


def shadow_profile_after_post_step(docstring, eff, shadow_out):
    """Apply the out-of-carrier post-step (mapping.md §3.1) to the shadow's
    output: pop leading/trailing lines that are EMPTY strings after the
    transform. Emptiness is decided from the concrete line widths and the
    amount the shadow removed — whitespace-only residue stays (non-empty)."""
    lines = docstring.expandtabs().split('\n')
    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
    flags = [eff[0] == -1]  # first line: all leading whitespace removed
    for i in range(1, len(lines)):
        if eff[i] == -1:
            flags.append(len(lines[i]) <= margin)
        else:
            flags.append(False)  # content survives the removal
    keep = list(range(len(lines)))
    while keep and flags[keep[-1]]:
        keep.pop()
    while keep and flags[keep[0]]:
        keep.pop(0)
    return [shadow_out[i] for i in keep]


def check_case(real_normalize, docstring):
    eff = to_eff(docstring)
    shadow_out = dedent_block(eff)
    expected = shadow_profile_after_post_step(docstring, eff, shadow_out)
    real_out = real_normalize(docstring)
    observed = profile_of(real_out)
    if observed != expected:
        return ("DISAGREEMENT\n  docstring=%r\n  eff=%r\n"
                "  shadow=%r (post-step profile %r)\n  real=%r (profile %r)"
                % (docstring, eff, shadow_out, expected, real_out, observed))
    return None


def boundary_cases():
    return [
        "",                                   # empty
        "oneliner",                           # single non-blank line
        "   leading spaces only line",        # single indented line
        "firstline\n\n    second line",       # failing-test shape
        "\n    First line empty.\n\n    Second.\n",   # blank-first style
        "title\n\n    metadata: x",
        "a\n  b\n    c",
        "   a\n  b",
        "x\n\ty\n\t\tz",                      # tabs (expanded)
        "no body\n",
        "\n\n\n",                             # all blank (empty lines)
        "   \n  \n ",                         # all blank (whitespace-only)
        "head\n    indented body\nflush body",
        "\n    a\n      b\n    c\n",
        "t\n  \n    body",                    # blank narrower than the amount
        "t\n      \n    body",                # blank wider than the amount
        "t\n    body\n  ",                    # trailing whitespace residue
        "t\n    body\n\n\n",                  # trailing empty run
        "\n\nt\n    body",                    # leading empty run
        "  \nt\n    body",                    # leading whitespace-only line
        " ",                                  # single whitespace-only line
        "\n",
        "a\nb",                               # flush body, nothing to remove
        "  a\n\n  ",                          # body all blank
        "t\n\tb\n        c",                  # tab vs spaces mix
        "t\n            deep\n    shallow",
    ]


def fuzz_docstring(rng):
    nlines = rng.randint(0, 8)
    snippets = ["x", "ab", "q w", "...", "metadata: y", ":m:`z`", "end."]
    lines = []
    for _ in range(nlines):
        kind = rng.randint(0, 3)
        indent = (" " * rng.randint(0, 12) if rng.randint(0, 3)
                  else "\t" * rng.randint(0, 2))
        if kind == 0:
            lines.append("")                          # empty -> blank
        elif kind == 1:
            lines.append(indent)                      # whitespace -> blank
        else:
            lines.append(indent + rng.choice(snippets))
    s = "\n".join(lines)
    if rng.randint(0, 3) == 0:
        s += "\n"
    return s


def main():
    from django.contrib.admindocs import utils as admindocs_utils
    real_normalize = getattr(admindocs_utils, "cleandoc", None)
    if real_normalize is None:
        print("ERROR: patched normalisation callee not bound in "
              "django.contrib.admindocs.utils (is the patch applied?)")
        return 2

    checked = 0
    for s in boundary_cases():
        err = check_case(real_normalize, s)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(real_normalize, fuzz_docstring(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (contract-stripped dedent_block) == real "
          "patched normalisation callee on %d docstrings (%d boundary + %d "
          "fuzz, seed %d)." % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
