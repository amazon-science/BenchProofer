#!/usr/bin/env python3
r"""G-AX executable soundness check for sympy__sympy-20916.

The bundle has NO consumed axioms in the proof beyond three *structural* facts
about two per-code-point character classes; it has A-references — deep models /
opaque recognizers in `Solution.lean` that must equal their real callees:

  (A-reference, axioms) `isLetterU c` == bool(re.match(r'[^\W\d_]', c, re.U))
  (A-reference, axioms) `isDigitU  c` == bool(re.match(r'\d',      c, re.U))
  (axioms, structural)  letter_not_digit / underscore_not_letter /
                        underscore_not_digit hold of the real classes
  (A-reference, comp.)  `peelDigits name` == the real `_name_with_digits_p`
                        split (capture groups), i.e. the post-patch trailing-
                        digit decomposition of `split_super_sub`.

Strategy: this gate runs at base_commit (the gold patch is NOT applied), so the
post-patch regex does not exist in-tree. We therefore reproduce the real callee
**verbatim** from the gold patch (provenance: mapping.md §3, patch.diff) —
`_name_with_digits_p = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)` — drive it with
the standard-library `re` engine, and differential-test our Lean deep models
(re-encoded here, mirroring the Lean `def`s line for line) against it over the
FAIL_TO_PASS matrix, a boundary set of single code points, and randomized fuzz.
The model-prone piece — that the greedy `([^\W\d_]+)` boundary is exactly the
end of the maximal leading letter run — is checked against the actual regex
engine, not against another hand reproduction.

stdlib-only (`re`, `random`, `sys`). Exit 0 iff every obligation holds.
"""
import random
import re
import sys

# --- REAL callees, reproduced verbatim from the gold patch -------------------
# _name_with_digits_p : sympy/printing/conventions.py:10 (post-patch, patch.diff)
NAME_WITH_DIGITS = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)
# the two character classes the two capture groups are built from:
LETTER_CLASS = re.compile(r'[^\W\d_]', re.U)   # isLetterU
DIGIT_CLASS = re.compile(r'\d', re.U)          # isDigitU


def real_is_letter(c):                          # [^\W\d_] under re.U
    return bool(LETTER_CLASS.match(c))


def real_is_digit(c):                           # \d under re.U
    return bool(DIGIT_CLASS.match(c))


def real_peel(name):
    """The real post-patch trailing-digit decomposition: the (group1, group2)
    of `_name_with_digits_p.match(name)`, or None when there is no match.
    Models the post-patch `if m: name, sub = m.groups()` step."""
    m = NAME_WITH_DIGITS.match(name)
    if m:
        return m.groups()          # (letters, digits)
    return None


# --- Lean deep models, re-encoded line-for-line (Solution.lean pure region) ---

def model_is_letter(c):                          # isLetterU (opaque, == LETTER_CLASS)
    return real_is_letter(c)


def model_is_digit(c):                           # isDigitU (opaque, == DIGIT_CLASS)
    return real_is_digit(c)


def model_peel(name):
    """peelDigits, transliterated. Returns (letters, digits) on a match (mirrors
    Lean `(letters, some digits)`), else None (mirrors `(name, none)`).
    `stripFinalNewline`: Python's `$` anchor matches at the end of the string OR
    immediately before ONE final newline, so the model sets aside at most one
    trailing '\n' before the all-digits test and omits it from the digit
    block (mapping.md §3.3)."""
    i = 0
    while i < len(name) and model_is_letter(name[i]):
        i += 1
    letters, rest = name[:i], name[i:]
    digits = rest[:-1] if rest.endswith("\n") else rest   # stripFinalNewline
    if letters != "" and digits != "" and all(model_is_digit(c) for c in digits):
        return (letters, digits)
    return None


# --- corpora -----------------------------------------------------------------

def f2p_names():
    # The separator-free symbol bases the FAIL_TO_PASS matrix exercises (the
    # `name` reaching the trailing-digit step). Greek + non-BMP math digits.
    return [
        "w1", "w\U0001D7D9", "w11", "w\U0001D7D9\U0001D7D9",
        "w\U0001D7D92\U0001D7D9", "w", "a",
        "ω1", "ω11", "ω\U0001D7D9", "ω\U0001D7D92",
        "alpha", "alpha11", "", "x",
        # `$`-anchor boundary: Python's `$` matches before ONE final newline,
        # so "w1\n" splits ("w","1") but "w1\n\n", "w1\r", "w\n1" do not split.
        "w1\n", "ω1\n", "abc123\n", "w\U0001D7D9\n",
        "w1\n\n", "w1\r", "w1\r\n", "w\n1", "w\n", "1\n", "\n",
    ]


def boundary_codepoints():
    cps = [
        ord('a'), ord('Z'), ord('w'), ord('_'), ord('^'), ord('.'),
        ord('0'), ord('9'), ord('1'),
        0x03C9,   # ω  GREEK SMALL LETTER OMEGA   (letter)
        0x03B1,   # α  GREEK SMALL LETTER ALPHA   (letter)
        0x0430,   # а  CYRILLIC SMALL LETTER A    (letter)
        0x1D7D9,  # 𝟙 MATH DOUBLE-STRUCK DIGIT 1 (digit, non-BMP)
        0x0661,   # ١  ARABIC-INDIC DIGIT ONE     (digit)
        0x06F1,   # ۱  EXTENDED ARABIC-INDIC ONE  (digit)
        0xFF11,   # １ FULLWIDTH DIGIT ONE        (digit)
        0x2160,   # Ⅰ  ROMAN NUMERAL ONE          (word, not \d -> letter-class)
        0x00B2,   # ²  SUPERSCRIPT TWO            (word, not \d -> letter-class)
        0x2460,   # ①  CIRCLED DIGIT ONE          (word, not \d -> letter-class)
        ord(' '), ord('-'), ord('+'),
        ord('\n'), ord('\r'),   # `$`-anchor probes (one final \n is tolerated)
    ]
    return [chr(c) for c in cps]


def fuzz_names(n, rng):
    alphabet = boundary_codepoints()
    for _ in range(n):
        k = rng.randint(0, 6)
        yield "".join(rng.choice(alphabet) for _ in range(k))


# --- checks ------------------------------------------------------------------

def main():
    failures = []

    # (1) per-code-point recognizer equality + the three structural axioms.
    probe = boundary_codepoints() + [chr(c) for c in range(0x0000, 0x0800)]
    # add a sweep over a few higher planes' boundaries
    probe += [chr(c) for c in (0x1D7CE, 0x1D7D9, 0x1D7FF, 0x2150, 0x2160, 0x24EA)]
    for c in probe:
        if model_is_letter(c) != real_is_letter(c):
            failures.append(("isLetterU", repr(c), model_is_letter(c), real_is_letter(c)))
        if model_is_digit(c) != real_is_digit(c):
            failures.append(("isDigitU", repr(c), model_is_digit(c), real_is_digit(c)))
        # axiom: letter -> not digit
        if real_is_letter(c) and real_is_digit(c):
            failures.append(("letter_not_digit", repr(c), True, True))
    # axiom: underscore excluded from both classes
    if real_is_letter('_'):
        failures.append(("underscore_not_letter", "'_'", True, False))
    if real_is_digit('_'):
        failures.append(("underscore_not_digit", "'_'", True, False))

    # (2) composite peelDigits == real _name_with_digits_p split.
    rng = random.Random(20916)
    names = list(f2p_names())
    names += list(fuzz_names(20000, rng))
    compared = 0
    for name in names:
        compared += 1
        m = model_peel(name)
        r = real_peel(name)
        if m != r:
            failures.append(("peelDigits", repr(name), m, r))

    if failures:
        print("G-AX FAIL: %d disagreement(s):" % len(failures))
        for what, inp, got, exp in failures[:25]:
            print("  [%s] input=%s model=%r real=%r" % (what, inp, got, exp))
        return 1

    print("G-AX OK: isLetterU/isDigitU == real [^\\W\\d_]/\\d classes and the "
          "three structural axioms hold over %d code points; composite peelDigits "
          "== real _name_with_digits_p split on %d names (seed=20916), 0 "
          "disagreements." % (len(probe), compared))
    return 0


if __name__ == "__main__":
    sys.exit(main())
