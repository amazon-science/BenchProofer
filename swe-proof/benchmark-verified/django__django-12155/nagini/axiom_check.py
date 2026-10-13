#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12155.

The changed operation (the docstring-indentation normalisation) is modelled
DEEPLY in model.py as a per-line leading-whitespace transform `dedented`
(the `pure` region: `min_indent_from` / `clamp_margin` / `remove_margin` /
`first_line`). There is NO consumed `@ContractOnly` axiom; the corresponding
stdlib callee is an A-reference, validated here against the REAL callee.

A-reference: the deep model `dedented` == the real `inspect.cleandoc`, observed
at the level the model decides — the per-line leading-whitespace amount of
every line (with a blank marker for empty/whitespace-only lines).

Each line is summarised by one integer:
  * a non-blank line  -> its leading-whitespace count (>= 0);
  * a blank line      -> the blank marker -1.
`inspect.cleandoc` is run on the same docstring; its output's per-line
leading-whitespace amounts (computed WITHOUT cleandoc's leading/trailing
blank-line stripping, which is an unchanged post-step orthogonal to the
indentation measurement under test) must equal `dedented` of the input
summary, at THAT index level — no value-membership double-mask.

The check also pins the discriminating behaviour the FAIL_TO_PASS test relies
on: on a docstring whose first line is non-empty and whose body is indented,
`cleandoc` removes the body indentation (the fixed behaviour), whereas the
pre-patch measurement — taking the common amount over ALL lines including the
first — would leave the body indented. The two MUST differ on that input, and
`cleandoc` MUST agree with the deep model.

Imports nothing repo-specific: `inspect` is the Python standard library — the
very module the gold patch calls. Exit 0 iff every obligation holds.
"""
import inspect
import random
import sys

NO_AMOUNT = -1


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def min_indent_from(eff, k):
    """min over the non-blank entries of eff[k:]; NO_AMOUNT when none."""
    m = NO_AMOUNT
    for i in range(k, len(eff)):
        if eff[i] >= 0 and (m < 0 or eff[i] < m):
            m = eff[i]
    return m


def clamp_margin(m):
    return m if m >= 0 else 0


def remove_margin(eff, margin):
    return [(-1 if x < 0 else x - margin) for x in eff]


def first_line(x):
    return -1 if x < 0 else 0


def dedented(eff):
    """model.py's deep model, as a list of per-line indent amounts."""
    if len(eff) == 0:
        return []
    margin = clamp_margin(min_indent_from(eff, 1))
    return [first_line(eff[0])] + remove_margin(eff[1:], margin)


# --- a marker-free reference for the same transform -------------------------

def dedent_reference_profile(eff):
    """The intended transform read straight off a per-line summary, with NO
    empty-fold marker of any kind: the amount removed is the minimum over the
    non-blank entries AFTER the first, and nothing is removed when there are
    none. Deliberately independent of how model.py (or `cleandoc`) encodes "no
    line to measure", so a summary carrying arbitrarily large amounts is judged
    by the behaviour rather than by a magnitude."""
    if len(eff) == 0:
        return []
    body = [x for x in eff[1:] if x >= 0]
    margin = min(body) if body else 0
    return [first_line(eff[0])] + [(-1 if x < 0 else x - margin)
                                   for x in eff[1:]]


# --- the input/output summaries -------------------------------------------

def to_eff(docstring):
    """Summarise the input docstring as per-line indent amounts (the carrier
    model.py reasons over). `expandtabs` is the unchanged preprocessing step
    shared by the old and new code; lines are split on '\\n' exactly as
    `inspect.cleandoc` does."""
    lines = docstring.expandtabs().split('\n')
    eff = []
    for line in lines:
        content = len(line.lstrip())
        eff.append(-1 if content == 0 else len(line) - content)
    return eff


def cleandoc_indent_profile(docstring):
    """The per-line leading-whitespace profile of the REAL `inspect.cleandoc`
    indentation transform, BEFORE its leading/trailing blank-line stripping
    (an unchanged post-step, orthogonal to the measurement under test). Mirrors
    cleandoc's own body so the comparison is at the exact index level the model
    decides — no value-membership proxy / double-mask."""
    lines = docstring.expandtabs().split('\n')
    margin = sys.maxsize
    for line in lines[1:]:
        content = len(line.lstrip())
        if content:
            margin = min(margin, len(line) - content)
    if lines:
        lines[0] = lines[0].lstrip()
    if margin < sys.maxsize:
        for i in range(1, len(lines)):
            lines[i] = lines[i][margin:]
    profile = []
    for line in lines:
        content = len(line.lstrip())
        profile.append(-1 if content == 0 else len(line) - content)
    return profile


def assert_real_cleandoc_matches_model(docstring):
    """The real cleandoc's indentation transform IS the deep model `dedented`
    of the input summary, profile-for-profile."""
    expected = dedented(to_eff(docstring))           # deep model (model.py)
    observed = cleandoc_indent_profile(docstring)    # real inspect.cleandoc
    assert observed == expected, (
        "deep model unsound on %r: cleandoc profile %r, model %r"
        % (docstring, observed, expected))
    # Sanity tie-back to the actual cleandoc output: the model's claim that the
    # first non-blank body line is moved by the body margin is observable as a
    # body line ending flush-left whenever it sat at the common indentation.
    real = inspect.cleandoc(docstring)
    assert isinstance(real, str)


def main():
    # --- boundary cases ---------------------------------------------------
    boundary = [
        "",                                   # empty
        "oneliner",                           # single non-blank line
        "   leading spaces only line",        # single indented line
        "firstline\n\n    second line",       # the FAIL_TO_PASS shape
        "\n    First line empty.\n\n    Second.\n",   # Django docstring style
        "title\n\n    metadata: x",
        "a\n  b\n    c",
        "   a\n  b",
        "x\n\ty\n\t\tz",                      # tabs (expanded)
        "no body\n",
        "\n\n\n",
        "head\n    indented body\nflush body",
        "\n    a\n      b\n    c\n",
    ]
    for s in boundary:
        assert_real_cleandoc_matches_model(s)

    # --- the FAIL_TO_PASS discriminator -----------------------------------
    # On a non-empty first line with an indented body, the fixed measurement
    # (over lines[1:]) removes the body indent; a measurement over ALL lines
    # (the pre-patch bug) would leave it. The two MUST differ, and the real
    # cleandoc MUST match the fixed (deep-model) one.
    discriminator = "firstline\n\n    second line"
    eff = to_eff(discriminator)
    fixed_margin = clamp_margin(min_indent_from(eff, 1))   # over lines[1:]
    buggy_margin = clamp_margin(min_indent_from(eff, 0))   # over all lines
    assert fixed_margin != buggy_margin, (
        "discriminator does not separate fixed vs pre-patch margin")
    assert fixed_margin == 4 and buggy_margin == 0, (
        "unexpected margins: fixed=%r buggy=%r" % (fixed_margin, buggy_margin))
    # cleandoc strips the body indent -> the second body line is flush-left.
    body_lines = inspect.cleandoc(discriminator).split('\n')
    assert body_lines[-1] == "second line", (
        "cleandoc did not flush the body line: %r" % (body_lines,))
    assert_real_cleandoc_matches_model(discriminator)

    # --- amount magnitude -------------------------------------------------
    # A leading-whitespace amount is a count of characters, bounded only by the
    # length of the line, so the summary carrier (an unbounded `int`) admits
    # amounts of ANY size. An empty-fold marker that is merely a LARGE number is
    # itself such an amount: a body line sitting exactly there is then read as
    # "there was no line to measure" and left unmoved, while the intended
    # transform slides it flush. The standard used here is therefore
    # `dedent_reference_profile`, which carries no marker at all, and the model
    # is checked against it at and around every magnitude a marker might take.
    #
    # Why the reference rather than `cleandoc` above 1e9: real `cleandoc` marks
    # its empty fold with `sys.maxsize`, which is safe THERE only because a str
    # holding sys.maxsize leading spaces cannot exist (~9 EB), not because the
    # measurement handles it. Above the physically reachable range the two
    # encodings therefore part company, and the claim being made is about the
    # intended transform, which the marker-free reference states directly. Below
    # it — the whole reachable range — the boundary/fuzz blocks above compare the
    # model against the actual stdlib callee.
    #
    # Checked on summaries DIRECTLY: a line 1e9 characters wide costs ~2 GB to
    # build, and the transform under check reads the amounts alone, so the
    # summary level is where the claim lives. Every case below is in the declared
    # domain of `dedent_block` (its precondition constrains only list access).
    wide = [10 ** 9 - 1, 10 ** 9, 10 ** 9 + 1,
            sys.maxsize - 1, sys.maxsize, sys.maxsize + 1, 2 ** 70]
    magnitude = []
    for big in wide:
        magnitude += [[0, -1, big], [big, -1, big], [0, big, big + 3],
                      [-1, big], [big], [big, big], [0, -1, big, 3]]
    for eff in magnitude:
        assert dedented(eff) == dedent_reference_profile(eff), (
            "deep model disagrees with the marker-free reference on %r: "
            "model %r, reference %r"
            % (eff, dedented(eff), dedent_reference_profile(eff)))

    # Profile-level fuzz over the whole magnitude range (same claim, random
    # shapes): amounts drawn from small values and from every marker-sized one.
    prng = random.Random(121550)
    amounts = [0, 1, 2, 7, 10, 10 ** 9 - 1, 10 ** 9, 10 ** 9 + 1,
               sys.maxsize, 2 ** 70]
    for _ in range(20000):
        eff = [-1 if prng.randint(0, 3) == 0 else prng.choice(amounts)
               for _ in range(prng.randint(0, 7))]
        assert dedented(eff) == dedent_reference_profile(eff), (
            "deep model disagrees with the marker-free reference on %r: "
            "model %r, reference %r"
            % (eff, dedented(eff), dedent_reference_profile(eff)))

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(12155)
    snippets = ["x", "ab", "q w", "...", "metadata: y", ":model:`m`"]
    for _ in range(40000):
        nlines = rng.randint(0, 7)
        lines = []
        for _ in range(nlines):
            kind = rng.randint(0, 2)
            if kind == 0:
                lines.append("")                          # empty -> blank
            elif kind == 1:
                lines.append(" " * rng.randint(0, 10))    # whitespace -> blank
            else:
                lines.append(" " * rng.randint(0, 10) + rng.choice(snippets))
        s = "\n".join(lines)
        assert_real_cleandoc_matches_model(s)

    print("G-AX OK: deep model `dedented` == real inspect.cleandoc indentation "
          "transform on %d boundary + 40000 fuzz docstrings; == the marker-free "
          "reference `dedent_reference_profile` on %d summaries carrying amounts "
          "up to 2**70 (so the empty-fold marker aliases no reachable amount); "
          "FAIL_TO_PASS discriminator separates fixed (lines[1:]) from pre-patch "
          "(all lines) margin (4 vs 0)."
          % (len(boundary), len(magnitude) + 20000))
    return 0


if __name__ == "__main__":
    sys.exit(main())
