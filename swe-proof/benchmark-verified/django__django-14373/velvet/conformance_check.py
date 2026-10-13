#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-14373.

Refutes the R/I refinement leg: the modeled four-character full-year rendering
(`fourDigitString(year)` from Solution.lean's `fourDigitYear`) against the
patched source line.

ORACLE CHOICE — why we transliterate the source line instead of running the
real method:
  The patched method `DateFormat.Y` lives on a `DateFormat` object built around a
  `datetime.date`/`datetime`, whose `.year` is bounded to 1..9999 by the stdlib
  constructor (MINYEAR..MAXYEAR). The behavior under test is the pure rendering
  of the year into a four-character zero-padded decimal. Per the worker prompt,
  the ORACLE is the patched source expression transliterated VERBATIM:
      '%04d' % self.data.year
  (from the gold-patched django/utils/dateformat.py, method `Y`). The SHADOW is
  the modeled formula from Solution.lean's `fourDigitYear` post-image
  (`fourDigitString(year)`), bridged to a Python `str` via mapping.md (the Lean
  `List Char` is the character list of the rendered string).

  We differential-test SHADOW vs ORACLE EXHAUSTIVELY over every year 0..9999
  (the full `require`/stdlib-constructible domain), plus the issue/F2P boundary
  years and a fuzz pass within that domain. Exit 0 iff zero disagreements.
  stdlib only.

  No callee is abstracted: the rendering is modeled in full, so there is no
  axiom and no axiom_check.py.
"""
import random
import sys

SEED = 14373
N_FUZZ = 200_000
# The modeled domain is `require year ≤ 9999`, matching the real datetime year
# range (MINYEAR=1 .. MAXYEAR=9999). The R/I claim is exact on that domain.
MAX_YEAR = 9999


def _digit_char(d):
    """digitChar from Solution.lean: ASCII for the decimal digit (d % 10)."""
    return chr(48 + d % 10)


def four_digit_string(n):
    """fourDigitString from Solution.lean: thousands, hundreds, tens, ones
    digit of n, as a 4-character string (the bridge of the Lean `List Char`)."""
    return (_digit_char(n // 1000 % 10) + _digit_char(n // 100 % 10) +
            _digit_char(n // 10 % 10) + _digit_char(n % 10))


def shadow(year):
    """fourDigitYear transliterated: the modeled full-year rendering.
    Mirrors `fourDigitString year` exactly."""
    return four_digit_string(year)


def oracle(year):
    """The patched source expression, transliterated verbatim from
    django/utils/dateformat.py (gold-patched `DateFormat.Y`):
        '%04d' % self.data.year
    Here `self.data.year` is the year input."""
    return '%04d' % year


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(range(0, MAX_YEAR + 1))     # exhaustive over 0..9999
    cases += [1, 999, 1000, 1999, 42, 476, 9, 99, 100, 2021, 9999]  # issue/F2P
    for _ in range(N_FUZZ):
        cases.append(rng.randint(0, MAX_YEAR))

    for year in cases:
        count += 1
        s = shadow(year)
        o = oracle(year)
        if s != o:
            disagreements.append((year, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of fourDigitYear agrees with the patched source "
          "line `'%%04d' %% year` on %d years (exhaustive 0..9999 + issue/F2P "
          "boundaries + fuzz, seed=%d), 0 disagreements. No axioms."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
