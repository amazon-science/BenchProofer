#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-10097.

The changed operation is modelled DEEPLY in model.py: the acceptance predicate
``accepts`` (built from ``is_uchar`` / ``body_ok`` / ``colons``) decides whether
a URL authentication segment (the text before the terminating ``@``) is
well-formed. There is NO consumed ``@ContractOnly`` axiom; instead the deep
model is an **A-reference** that must equal the REAL compiled matcher — the
post-patch ``URLValidator`` regex group ``[^\\s:@/]+(?::[^\\s:@/]*)?`` compiled
with ``re.IGNORECASE`` (the flag the validator uses).

This script compiles that exact matcher (a fragment of the gold-patch regex),
runs it on boundary cases over the four forbidden classes (whitespace, ``":"``,
``"@"``, ``"/"``) and their mixtures plus randomized fuzz, and asserts that for
every input the deep model decides acceptance identically to a FULL match of
the real compiled group. ``\\s`` is Unicode-aware, so the alphabets explicitly
include the ENTIRE Unicode-whitespace block (the ASCII run plus the C1 and
separator code points ``0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028,
0x2029, 0x202f, 0x205f, 0x3000``) — the exact class on whose boundary the
deep model and the real matcher could diverge — alongside ASCII separators,
ordinary text, and non-whitespace non-separator code points (astral emoji,
accented letter, bullet).

Imports nothing repo-specific: ``re`` is the Python standard library — the same
engine the gold patch's compiled regex uses. Exit 0 iff every obligation holds.
"""
import re
import random
import sys

# The REAL matcher: the user:pass authentication group from the post-patch
# URLValidator regex, compiled exactly as the validator compiles it
# (re.IGNORECASE). The surrounding "(?:...@)?" wrapper makes the segment
# optional and consumes a trailing "@"; the acceptance question this bundle
# models is "does the part before that @ form a well-formed segment", which is
# precisely a full match of the inner group below.
USERINFO = re.compile(r'[^\s:@/]+(?::[^\s:@/]*)?', re.IGNORECASE)

# The FULL Unicode-whitespace set (Python `\s` under default UNICODE flags) +
# the three RFC-1738 separators, as code points, kept in lock-step with
# model.py's is_whitespace / is_uchar. This is the same 29-code-point set the
# real `\s` matches in the pinned eval container (Python 3.5) — verified
# in-container.
_WS = (set(range(9, 14)) | {32}
       | set(range(0x1c, 0x20)) | {0x85, 0xa0, 0x1680}
       | set(range(0x2000, 0x200b)) | {0x2028, 0x2029, 0x202f, 0x205f, 0x3000})
_SEP_COLON = 58
_SEP_AT = 64
_SEP_SLASH = 47


def is_uchar(c):
    """model.py is_uchar: not whitespace (the full Unicode `\\s` set),
    ':', '@' or '/'."""
    return c not in _WS and c != _SEP_COLON and c != _SEP_AT and c != _SEP_SLASH


def accepts_model(s):
    """Reference implementation of model.py's deep model ``accepts`` over the
    code points of ``s`` (non-empty; only authentication chars apart from at
    most one separator colon; does not begin with that colon)."""
    cps = [ord(ch) for ch in s]
    if len(cps) == 0:
        return False
    if cps[0] == _SEP_COLON:
        return False
    ncolon = 0
    good = True
    for c in cps:
        if c == _SEP_COLON:
            ncolon += 1
        elif not is_uchar(c):
            good = False
    return good and ncolon <= 1


def accepts_real(s):
    """The real compiled matcher's verdict: a FULL match of the userinfo group
    over the whole segment (the group must consume the entire segment for the
    wrapper '(?:...@)?' to attach the following '@')."""
    return USERINFO.fullmatch(s) is not None


def check(s):
    model = accepts_model(s)
    real = accepts_real(s)
    assert model == real, (
        "deep model `accepts` unsound on %r: real compiled matcher gave %r, "
        "deep model gives %r" % (s, real, model))


def main():
    # The FULL Unicode-whitespace block as literal characters — the class on
    # whose boundary the deep model and the real `\s`-based matcher could
    # diverge. EVERY whitespace code point must appear in the fuzz alphabet.
    ws_extra = [chr(c) for c in sorted(_WS) if c not in (9, 10, 11, 12, 13, 32)]
    forbidden = [':', '@', '/', ' ', '\t', '\n', '\r', '\x0b', '\x0c'] + ws_extra
    ordinary = ['a', 'Z', '0', '9', '-', '.', '%', '4', '8', '2', 'f',
                '!', '$', '&', "'", '(', ')', '*', '+', ',', ';', '=', '~', '_']

    boundary = [""]
    boundary += forbidden                        # each forbidden char alone
    boundary += [c + c for c in forbidden]        # doubled
    boundary += ['foo' + c for c in forbidden]    # embedded after a user run
    boundary += ['foo' + c + 'bar' for c in forbidden]  # embedded mid-segment
    boundary += ['foo:ba' + c + 'r' for c in forbidden]  # in the password run
    boundary += ordinary[:8]                      # plain user runs
    # The discriminating cases from the issue / test data:
    boundary += [
        "foo", "foo:bar", "foo:bar:baz",
        "foo/bar", "foo@bar", "foo:bar@baz", "foo:bar/baz",
        ":pass", ":", "user:", "a:b",
        "-.~_!$&'()*+,;=%40:80%2f",          # the new valid encoded segment
        "-.~_!$&'()*+,;=:%40:80%2f::::::",   # the now-invalid old segment
        "m=foo", "m=foo@example.com",
        # explicit non-ASCII-whitespace witnesses from the issue's class:
        "foo\xa0bar", "foo bar", "user　pass", " x",
    ]
    for s in boundary:
        check(s)

    # Programmatic per-code-point boundary sweep: for EVERY Unicode-whitespace
    # code point, assert the deep model and the real matcher agree both when it
    # stands alone and when it is embedded in an otherwise-valid user run. This
    # is the class the previous fuzz alphabet provably could not reach.
    for c in sorted(_WS):
        ch = chr(c)
        check(ch)
        check("foo" + ch)
        check("foo" + ch + "bar")
        check("foo:b" + ch + "ar")

    # Randomized fuzz over ASCII separators + the full Unicode-whitespace block
    # + ordinary text.
    rng = random.Random(10097)
    alphabet = forbidden + ordinary
    for _ in range(60000):
        n = rng.randint(0, 12)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check(s)

    # Second sweep adds non-whitespace, non-separator code points (astral
    # emoji, accented letter, bullet) which both the real matcher and the model
    # treat as authentication characters — exercising the model's claim that
    # any non-whitespace non-separator code point passes — while still drawing
    # from the full Unicode-whitespace block.
    safe_extra = ['\U0001F600', 'é', '•']
    alphabet2 = forbidden + ordinary + safe_extra
    for _ in range(40000):
        n = rng.randint(0, 10)
        s = "".join(rng.choice(alphabet2) for _ in range(n))
        check(s)

    print("G-AX OK: deep model `accepts` == real compiled userinfo matcher "
          "[^\\s:@/]+(?::[^\\s:@/]*)? on %d boundary + full Unicode-whitespace "
          "per-codepoint sweep + 100000 fuzz inputs; "
          "0 mismatches." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
