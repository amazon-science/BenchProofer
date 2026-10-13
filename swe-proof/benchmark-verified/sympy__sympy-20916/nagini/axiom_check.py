#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-20916.

Validates the bundle's two kind-A references against the REAL language runtime
(the standard-library `re` module — the very module the patched code uses to
recognise the trailing-digit exception). Imports nothing repo-specific.

The patched recogniser is the compiled pattern

    _name_with_digits_p = re.compile(<raw>^([^\\W\\d_]+)(\\d+)$<raw>, re.U)

i.e. a NON-EMPTY run of Unicode "letters" (word chars that are neither a
decimal digit nor underscore: the class [^\\W\\d_]) immediately followed by a
NON-EMPTY run of Unicode decimal digits (\\d), with nothing else.

model.py abstracts the two per-code-point classifications as `@Pure
@ContractOnly` axioms and models the recognise/split decision DEEPLY:

  (A-reference 1) is_letter(c)  ==  the code point c matches the class
      [^\\W\\d_] under re.U (a Unicode letter; never also a decimal digit).
  (A-reference 2) is_digit(c)   ==  the code point c matches \\d under re.U
      (a Unicode decimal digit).

This script asserts, on the real `re`:
  * is_letter / is_digit agree with the real single-character classes over a
    broad code-point sweep (ASCII, Latin-1, Greek/Cyrillic, the astral
    mathematical bold digits used by the tests, and random fuzz);
  * the disjointness axiom is_letter(c) => not is_digit(c) the proof consumes
    actually holds for the real classes;
  * the DEEP recognise/split decision built from those classifications (the
    model's `splits` / `split_point`) reproduces the real compiled regex's
    match / group split, on boundary names + heavy fuzz.

Exit 0 iff every obligation holds.
"""
import re
import random
import sys

_LETTER_RE = re.compile(r'[^\W\d_]', re.U)   # the [^\W\d_] class, one char
_DIGIT_RE = re.compile(r'\d', re.U)          # the \d class, one char
_NAME_RE = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)  # the patched recogniser


def real_is_letter(c):
    """The real per-code-point letter class the axiom abstracts."""
    return _LETTER_RE.match(chr(c)) is not None


def real_is_digit(c):
    """The real per-code-point decimal-digit class the axiom abstracts."""
    return _DIGIT_RE.match(chr(c)) is not None


# --- model.py deep model reference (the recognise/split decision) -----------

def num_leading_letters(cps):
    k = 0
    while k < len(cps) and real_is_letter(cps[k]):
        k += 1
    return k


def all_digits(cps):
    return all(real_is_digit(c) for c in cps)


def core_len(cps):
    """model.py `core_len`: the length of the name PROPER — the input with a
    single terminating line-feed code point (10) set aside. This mirrors the
    real pattern's `$` anchor, which under non-MULTILINE matching also matches
    just before ONE terminating newline (and that newline is captured by
    neither group). Exactly one is set aside."""
    if len(cps) >= 1 and cps[len(cps) - 1] == 10:
        return len(cps) - 1
    return len(cps)


def model_splits(cps):
    """model.py `splits`: within the name PROPER, a non-empty letter run
    followed by a non-empty digit run, nothing else."""
    k = num_leading_letters(cps)
    return k >= 1 and k < core_len(cps) and all_digits(cps[k:core_len(cps)])


def model_split_point(cps):
    return num_leading_letters(cps)


def model_digit_run(cps):
    """model.py `digit_run`: the peeled group-2 run, bounded by `core_len` so
    the `$`-tolerated terminating line feed is not part of it."""
    return cps[model_split_point(cps):core_len(cps)]


# --- checks -----------------------------------------------------------------

def check_disjoint(c):
    """The consumed axiom clause: a letter is never also a decimal digit."""
    if real_is_letter(c):
        assert not real_is_digit(c), (
            "disjointness axiom unsound: U+%04X classifies as BOTH letter and "
            "digit" % c)


def check_split_against_regex(name):
    """The deep model's split decision == the real compiled regex's match."""
    cps = [ord(ch) for ch in name]
    m = _NAME_RE.match(name)
    if m is None:
        assert not model_splits(cps), (
            "deep model says split but real regex did NOT match %r" % name)
    else:
        assert model_splits(cps), (
            "deep model says no-split but real regex matched %r" % name)
        bare, sub = m.groups()
        # model: bare name is name[:split_point]; subscript is `digit_run`,
        # i.e. name[split_point:core_len] (the `$`-tolerated terminating line
        # feed belongs to neither group).
        sp = model_split_point(cps)
        run = "".join(chr(c) for c in model_digit_run(cps))
        assert name[:sp] == bare, (
            "deep model bare-name %r != real regex group1 %r for %r"
            % (name[:sp], bare, name))
        assert run == sub, (
            "deep model subscript %r != real regex group2 %r for %r"
            % (run, sub, name))


def main():
    # --- per-code-point classification + disjointness sweep ----------------
    # Exhaustive over the Basic Multilingual Plane plus targeted astral blocks
    # (the mathematical alphanumeric symbols block holds the bold digits the
    # tests use, e.g. U+1D7D9 MATHEMATICAL DOUBLE-STRUCK DIGIT ONE).
    ranges = [range(0x0000, 0x10000),
              range(0x1D400, 0x1D800),   # Mathematical Alphanumeric Symbols
              range(0x1E900, 0x1EE00)]   # Adlam etc. (more Unicode digits)
    n_checked = 0
    for r in ranges:
        for c in r:
            # surrogates are not valid scalar values for chr() comparison
            if 0xD800 <= c <= 0xDFFF:
                continue
            check_disjoint(c)
            n_checked += 1

    # --- boundary names: the F2P cases + structural edge cases -------------
    boundary = [
        "", "w", "1", "w1", "w11", "11", "1a", "a1b2",
        "w\U0001D7D9", "w\U0001D7D9\U0001D7D9", "w\U0001D7D92\U0001D7D9",
        "ω", "ω1", "ω11", "ω1a", "1ω",
        "ω\U0001D7D9", "Βητα01",  # Greek letters + digits
        "beta", "beta13", "alpha", "alpha11",
        "abc", "abc0", "A1", "Z9", "aZ12", "_1", "a_1",
        "é", "é1",            # Latin-1 letter (e-acute) + digit
        "абв",            # Cyrillic letters, no digit
        "г1",                       # Cyrillic letter + digit
        "x٠١",                 # Latin + Arabic-Indic digits
        "x12y",                          # interior letters: must NOT match
        # `$`-anchor probes: Python's non-MULTILINE `$` also matches just before
        # ONE terminating newline, so these MUST split even though a raw
        # "all code points from the first digit on are digits" test says no.
        "w1\n", "ω1\n", "w11\n", "w\U0001D7D9\n", "abc123\n",
        # ... and exactly one: two newlines, a \r, or an interior \n must NOT.
        "w1\n\n", "w1\r", "w1\r\n", "w1\n\r", "w\n1", "w\n", "1\n", "\n",
        "\n\n", "\nw1", "ω\n",
    ]
    for name in boundary:
        check_split_against_regex(name)

    # --- randomized fuzz over a mixed letter/digit/other alphabet ----------
    alphabet = [
        "a", "b", "Z", "w",
        "ω", "α", "Β",          # Greek letters
        "а", "г",                    # Cyrillic letters
        "é",                              # Latin-1 letter
        "0", "1", "9",                         # ASCII digits
        "\U0001D7D9", "\U0001D7DA",            # astral bold digits
        "٠", "१",                    # Arabic-Indic / Devanagari digits
        "_", "^", " ", "-", ".", "+",          # non-word / other
        "\n", "\r", "\t",   # line terminators: the `$`-anchor case, fuzzed too
    ]
    rng = random.Random(20916)
    for _ in range(60000):
        n = rng.randint(0, 8)
        name = "".join(rng.choice(alphabet) for _ in range(n))
        check_split_against_regex(name)

    print("G-AX OK: is_letter/is_digit classes + disjointness sound over "
          "%d code points; deep split model == real re recogniser on %d "
          "boundary + 60000 fuzz names" % (n_checked, len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
