#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11099.

Two trust points are checked against the REAL Python `re` engine — the same
engine the patched code uses — on boundary cases plus randomized fuzzing.

  (A-consumed) the single-code-point membership axioms `permitted_ascii` /
      `permitted_unicode` (model.py axioms region). Each axiom's Ensures pins
      only a handful of code points; G-AX asserts the REAL character class
      `[\\w.@+-]` agrees with EVERY pinned clause, under the matching regex
      flags:
        * permitted_ascii  -> flags=re.ASCII  (the ASCII validator's `flags`)
        * permitted_unicode-> flags=0         (the Unicode validator's `flags`)
      The axioms are deliberately the WEAKEST sufficient contract (they pin only
      the points the proof needs: line-feed/space excluded; a few letters,
      digit, '-', '.' included). G-AX confirms none of those pinned facts is
      stronger than the real class.

  (A-reference) the DEEP model of the changed acceptance decision. model.py
      specifies acceptance as

          accept(value) == (len(value) >= 1 and all_permitted(value))

      i.e. the value is non-empty and EVERY code point — the last one included —
      is admissible. G-AX asserts this deep model equals the REAL, FIXED
      validator regex `^[\\w.@+-]+\\Z` (with the matching flags), and that it
      DISAGREES with the pre-patch regex `^[\\w.@+-]+$` exactly on values whose
      only offence is a single trailing line feed (the behaviour the issue
      reports and the F2P tests add).

Imports only the standard library (`re`); nothing repo-specific. Django's
validator is `re.search(pattern, str(value))`; `search` with a leading `^`
anchor is equivalent to `fullmatch` for these end-anchored patterns, and we use
`search` to mirror the real call exactly. Exit 0 iff every obligation holds.
"""
import re
import random
import sys

LF = 10  # U+000A line feed

# Real character class and the two validator flag regimes.
_ASCII_CLS = re.compile(r'[\w.@+-]', re.ASCII)
_UNI_CLS = re.compile(r'[\w.@+-]', 0)

# Pre-patch (buggy) and post-patch (fixed) validator regexes, per regime.
_ASCII_BUGGY = re.compile(r'^[\w.@+-]+$', re.ASCII)
_ASCII_FIXED = re.compile(r'^[\w.@+-]+\Z', re.ASCII)
_UNI_BUGGY = re.compile(r'^[\w.@+-]+$', 0)
_UNI_FIXED = re.compile(r'^[\w.@+-]+\Z', 0)


# --- model.py axiom Ensures clauses, transcribed -----------------------------
# permitted_ascii: (codepoint, required membership)
_ASCII_AXIOM = {10: False, 32: False, 97: True, 65: True, 48: True,
                45: True, 46: True}
# permitted_unicode: (codepoint, required membership)
_UNI_AXIOM = {10: False, 32: False, 97: True, 233: True, 48: True,
              45: True, 46: True}


def _real_member(cls, c):
    """True iff code point c is in the real character class `[\\w.@+-]`."""
    return cls.fullmatch(chr(c)) is not None


def _real_accept(rx, value):
    """The real validator decision: accepts iff rx.search(str) matches."""
    return rx.search("".join(chr(c) for c in value)) is not None


def check_membership_axioms():
    for c, required in _ASCII_AXIOM.items():
        got = _real_member(_ASCII_CLS, c)
        assert got == required, (
            "permitted_ascii axiom unsound at cp=%d: real class membership %r, "
            "axiom Ensures %r" % (c, got, required))
    for c, required in _UNI_AXIOM.items():
        got = _real_member(_UNI_CLS, c)
        assert got == required, (
            "permitted_unicode axiom unsound at cp=%d: real class membership "
            "%r, axiom Ensures %r" % (c, got, required))


# --- model.py deep acceptance model, transcribed -----------------------------

def _admissible(cls, c):
    return _real_member(cls, c)


def _deep_accept(cls, value):
    """model.py: accept(value) == (len>=1 and every code point admissible)."""
    if len(value) < 1:
        return False
    return all(_admissible(cls, c) for c in value)


def check_deep_model(cls, fixed_rx, buggy_rx, value):
    deep = _deep_accept(cls, value)
    fixed = _real_accept(fixed_rx, value)
    assert deep == fixed, (
        "deep acceptance model != real FIXED regex on %r: deep=%r fixed=%r"
        % (value, deep, fixed))
    # And: deep model (== fixed) differs from the buggy regex iff the value's
    # only offence is a single trailing line feed.
    buggy = _real_accept(buggy_rx, value)
    if deep != buggy:
        assert (len(value) >= 1 and value[-1] == LF
                and _deep_accept(cls, value[:-1])), (
            "deep/buggy disagreement on %r is NOT a lone-trailing-LF case "
            "(deep=%r buggy=%r)" % (value, deep, buggy))


def main():
    check_membership_axioms()

    # Boundary code points spanning both regimes and the discriminating LF.
    special = [LF, 13, 32, ord('.'), ord('@'), ord('+'), ord('-'), ord('_'),
               ord('a'), ord('Z'), ord('0'), ord('9'), ord("'"), 233, 8203,
               160, 8211, ord(' ')]

    def fuzz_values(n, max_len, alphabet, rng):
        for _ in range(n):
            k = rng.randint(0, max_len)
            yield [rng.choice(alphabet) for _ in range(k)]

    rng = random.Random(11099)
    alphabet = special + [ord(ch) for ch in "glennGLEnNjeanmarc"]

    # Explicit boundary values (mirror the F2P additions and intent).
    boundary = [
        [], [LF], [ord('a')], [ord('a'), LF], [ord('a'), LF, LF],
        [ord('a'), LF, ord('b')], list(b"glenn"), list(b"jean-marc"),
        list(b"jean marc"), [ord('a'), ord('.'), ord('@'), ord('+'),
                             ord('-'), LF],
        [ord(c) for c in "trailingnewline"] + [LF],
        [ord(c) for c in "René"], [ord(c) for c in "أحمد"],
    ]
    for v in boundary:
        check_deep_model(_ASCII_CLS, _ASCII_FIXED, _ASCII_BUGGY, v)
        check_deep_model(_UNI_CLS, _UNI_FIXED, _UNI_BUGGY, v)

    for v in fuzz_values(20000, 12, alphabet, rng):
        check_deep_model(_ASCII_CLS, _ASCII_FIXED, _ASCII_BUGGY, v)
        check_deep_model(_UNI_CLS, _UNI_FIXED, _UNI_BUGGY, v)

    # A wide single-code-point sweep so membership disagreements anywhere are
    # caught (admissibility must agree element-wise with the real class).
    for c in range(0, 0x2100):
        v = [ord('a'), c]
        check_deep_model(_ASCII_CLS, _ASCII_FIXED, _ASCII_BUGGY, v)
        check_deep_model(_UNI_CLS, _UNI_FIXED, _UNI_BUGGY, v)

    print("G-AX OK: membership axioms (permitted_ascii/permitted_unicode) sound "
          "on every pinned clause; deep acceptance model == real FIXED regex "
          "over %d boundary + 20000 fuzz + 0x2100 single-cp-sweep inputs in "
          "both flag regimes; deep/buggy disagreements are exactly the "
          "lone-trailing-line-feed case." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
