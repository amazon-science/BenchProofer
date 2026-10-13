#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7440.

This bundle consumes NO axiom: the registration key is the term text itself
(modelled deeply as the verbatim copy in model.py's impl), and the CONTRAST
operation it must not apply — ASCII case folding — is also modelled deeply by
the pure fold `casefold` in model.py's pure region.

The single kind-A obligation is therefore an A-reference: the deep model
`casefold` must equal the real per-character lower-casing that the pre-patch
code applied (`termtext.lower()`, i.e. CPython `str.lower()`) on the input
domain the change is about — glossary term text, which is ordinary (ASCII)
identifier-like text. We validate:

  (1) For every ASCII code point 0..127, `casefold`'s per-character map
      `fold_cp` agrees with `str.lower()`: the upper-case Latin letters
      'A'..'Z' (65..90) fold to +32, every other ASCII code point is unchanged.
      (This is exactly model.py's `fold_cp`.)

  (2) On boundary + randomized ASCII strings, the whole-sequence deep model
      `casefold(s)` equals `[ord(c) for c in s.lower()]`.

  (3) The discriminating witness of the fix: for any term text carrying an
      upper-case ASCII letter, the case-preserving registration (identity) and
      the case-folding `casefold` DIFFER — so the spec's verbatim postcondition
      genuinely separates the fixed behaviour from the buggy one.

`casefold` is restricted to the ASCII domain by construction (`fold_cp` only
touches 65..90); the provenance note in mapping.md records that glossary terms
in the tested domain are ASCII, so the ASCII fold is the relevant lower-casing.
Imports nothing repo-specific (only the standard library). Exit 0 iff sound.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def fold_cp(c):
    """Reference of model.py's `fold_cp`: ASCII A-Z (65..90) -> +32, else id."""
    if 65 <= c <= 90:
        return c + 32
    return c


def casefold(codepoints):
    """Reference of model.py's deep model `casefold`, as a list of code points."""
    return [fold_cp(c) for c in codepoints]


# --- the checks --------------------------------------------------------------

def check_fold_cp_matches_lower():
    """(1) Per-character: fold_cp agrees with str.lower() on every ASCII point.

    str.lower() of a single ASCII character is a single ASCII character, so the
    code-point comparison is well defined."""
    for c in range(128):
        ch = chr(c)
        low = ch.lower()
        assert len(low) == 1, (
            "ASCII lower of %r is not single-char: %r" % (ch, low))
        observed = ord(low)                  # real callee str.lower()
        expected = fold_cp(c)                # deep model fold_cp
        assert observed == expected, (
            "fold_cp unsound at code point %d (%r): str.lower gave %d, "
            "model gives %d" % (c, ch, observed, expected))


def check_casefold_reference(s):
    """(2) Whole-sequence: casefold(s) == [ord(c) for c in s.lower()]."""
    observed = [ord(ch) for ch in s.lower()]          # real callee
    expected = casefold([ord(ch) for ch in s])        # deep model
    assert observed == expected, (
        "casefold deep model unsound on %r: str.lower gave %r, "
        "model gives %r" % (s, observed, expected))


def check_fix_discriminates(s):
    """(3) Registration (identity) differs from casefold iff s has an upper
    ASCII letter — the spec's verbatim postcondition separates fixed vs buggy."""
    cps = [ord(ch) for ch in s]
    has_upper = any(65 <= c <= 90 for c in cps)
    differs = (casefold(cps) != cps)
    assert differs == has_upper, (
        "discrimination witness wrong on %r: has_upper=%s differs=%s"
        % (s, has_upper, differs))


def main():
    # (1) exhaustive over the ASCII domain
    check_fold_cp_matches_lower()

    # (2)/(3) boundary cases over the tested term-text shapes
    boundary = [
        "",
        "term1", "term2", "TERM2", "MySQL", "mysql",
        "term3", "term4",
        "A", "Z", "a", "z", "0", " ", ":", "-", "_",
        "ABCXYZ", "abcxyz", "AbCdEf",
        "Joe", "HTTP", "Http", "http",
        "term with spaces", "Term With Spaces",
        "ls -l", "--option", "Option-Name",
    ]
    for s in boundary:
        check_casefold_reference(s)
        check_fix_discriminates(s)

    # (2)/(3) randomized fuzz over an ASCII alphabet (the term-text domain)
    rng = random.Random(7440)
    alphabet = [chr(c) for c in range(32, 127)]
    for _ in range(20000):
        n = rng.randint(0, 20)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_casefold_reference(s)
        check_fix_discriminates(s)

    print("G-AX OK: casefold deep model (== ASCII str.lower) sound over the "
          "full 128-point ASCII domain + %d boundary + 20000 fuzz inputs; "
          "case-preserving registration differs from the fold exactly on "
          "upper-case ASCII input" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
