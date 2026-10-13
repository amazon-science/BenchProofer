#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-14539.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). It differential-tests the R/I content of the Lean
`implementation_peelTrailingPunct` skeleton against the behaviour of the gold
`patch.diff`.

Modeled operation: a single application of the trailing-punctuation peel block
that the patch edits inside `django.utils.html.urlize`'s `trim_punctuation`
helper. Given a token `middle` and an accumulator `trail`, it unescapes the
token, measures the run of trailing punctuation on the DECODED view, and moves
exactly that many characters off the END of the ORIGINAL token into the front of
the accumulator.

A-reference (mapping.md): the Lean `decode` is the real repo callee
`html.unescape`; BOTH the shadow and the patched reference call it directly, so
the A-leg is exercised with the real decoder. The R/I content under test is the
slicing arithmetic (`punctuation_count`, `middle[-pc:]`, `middle[:-pc]`).

Reference = the EXACT patched Python lines (verbatim from patch.diff). Shadow =
the transliteration of the Lean impl. Exit 0 iff zero disagreements over a
discrete catalogue + >=1e5 fuzzed tokens (incl. HTML-escaped sequences, the bug
trigger). stdlib only; pinned seed.
"""
import html
import random
import sys

SEED = 20210619
N_RANDOM = 120_000  # >= 1e5
TRAILING_PUNCTUATION_CHARS = '.,:;!'


# ---- reference: the EXACT patched behaviour (verbatim from patch.diff) ------

def reference_patched(middle, trail):
    """One application of the patched trailing-punctuation block. Returns
    (middle, trail, trimmed_something). Mirrors the gold patch lines 1:1."""
    trimmed_something = False
    middle_unescaped = html.unescape(middle)
    stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)
    if middle_unescaped != stripped:
        punctuation_count = len(middle_unescaped) - len(stripped)
        trail = middle[-punctuation_count:] + trail
        middle = middle[:-punctuation_count]
        trimmed_something = True
    return middle, trail, trimmed_something


# ---- shadow: transliteration of implementation_peelTrailingPunct ------------

def rstrip_punct(cs):
    return cs.rstrip(TRAILING_PUNCTUATION_CHARS)


def drop_right_n(cs, n):
    # Lean dropRightN: cs.take(len - n); for n=0 this is the whole string.
    return cs[:len(cs) - n]


def take_right_n(cs, n):
    # Lean takeRightN: cs.drop(len - n); for n=0 this is "".
    return cs[len(cs) - n:]


def shadow_peel(token, tail_punct):
    decoded = html.unescape(token)          # A-reference: real decoder
    stripped = rstrip_punct(decoded)
    trimmed = False
    if decoded != stripped:
        punct_count = len(decoded) - len(stripped)
        tail_punct = take_right_n(token, punct_count) + tail_punct
        token = drop_right_n(token, punct_count)
        trimmed = True
    return token, tail_punct, trimmed


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # discrete catalogue: incl. the issue's exact trigger and entity variants.
    discrete = [
        ('google.com/?q=1&lt', ''),
        ('google.com/?q=1&lt!', ''),
        ('google.com/?q=1&lt!!!', '! and'),
        ('a.b.c...', ''),
        ('&amp;!!', 'X'),
        ('end;;', ''),
        ('plain', ''),
        ('no.dots.here', ''),
        ('x', ''),
        ('foo&gt;.', 'bar'),
        ('a&lt;&gt;;', ''),
        ('trailing:::', 'tail'),
    ]
    cases = list(discrete)

    alphabet = list('abcXY./')
    entities = ['&lt', '&gt', '&amp', '&lt;', '&gt;', '&amp;', '&#60', '&#x3C;']
    punct = list(TRAILING_PUNCTUATION_CHARS)

    def rand_token():
        parts = []
        for _ in range(rng.randint(1, 8)):
            r = rng.random()
            if r < 0.35:
                parts.append(rng.choice(entities))
            elif r < 0.6:
                parts.append(rng.choice(punct))
            else:
                parts.append(rng.choice(alphabet))
        return ''.join(parts)

    for _ in range(N_RANDOM):
        cases.append((rand_token(), rng.choice(['', '!', 'tail', '. and see.'])))

    for token, tail in cases:
        # The patched code only runs this block when there IS trailing
        # punctuation on the decoded view (the surrounding `if`); but it is also
        # safe (no-op) otherwise, and the Lean spec/impl cover both, so compare
        # unconditionally.
        exp = reference_patched(token, tail)
        got = shadow_peel(token, tail)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH token={token!r} tail={tail!r}: "
                      f"ref={exp!r} shadow={got!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
