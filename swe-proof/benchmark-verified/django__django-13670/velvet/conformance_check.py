#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13670.

Refutes the R/I refinement leg: the modeled two-character short-year rendering
(`twoDigitString(year % 100)` from Solution.lean's `twoDigitYear`) against the
patched source line.

ORACLE CHOICE — why we transliterate the source line instead of running the
real method:
  The patched method `DateFormat.y` lives on a `DateFormat` object built around a
  `datetime.date`/`datetime`, whose `.year` is bounded to 1..9999 by the stdlib
  constructor. The behavior under test is the pure rendering of the year into a
  two-character decimal. Per the worker prompt, the ORACLE is the patched source
  expression transliterated VERBATIM:
      '%02d' % (self.data.year % 100)
  (from the gold-patched django/utils/dateformat.py, method `y`). The SHADOW is
  the modeled formula from Solution.lean's `twoDigitYear` post-image
  (`twoDigitString(year % 100)`), bridged to a Python `str` via mapping.md (the
  Lean `List Char` is the character list of the rendered string).

  We differential-test SHADOW vs ORACLE EXHAUSTIVELY over every year 0..9999
  (the full stdlib-constructible range and then some), plus a fuzz pass over a
  wider range to exercise the `% 100` reduction. Exit 0 iff zero disagreements.
  stdlib only.

  No callee is abstracted: the rendering is modeled in full, so there is no
  axiom and no axiom_check.py.
"""
import random
import sys

SEED = 13670
N_FUZZ = 200_000
MAX_FUZZ_YEAR = 10_000_000


def _digit_char(d):
    """digitChar from Solution.lean: ASCII for the decimal digit (d % 10)."""
    return chr(48 + d % 10)


def two_digit_string(n):
    """twoDigitString from Solution.lean: tens digit then ones digit of n%100,
    as a 2-character string (the bridge of the Lean `List Char`)."""
    return _digit_char(n // 10 % 10) + _digit_char(n % 10)


def shadow(year):
    """twoDigitYear transliterated: the modeled short-year rendering.
    Mirrors `twoDigitString (year % 100)` exactly."""
    return two_digit_string(year % 100)


def oracle(year):
    """The patched source expression, transliterated verbatim from
    django/utils/dateformat.py (gold-patched `DateFormat.y`):
        '%02d' % (self.data.year % 100)
    Here `self.data.year` is the year input."""
    return '%02d' % (year % 100)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(range(0, 10_000))          # exhaustive over 0..9999
    cases += [123, 5, 2099, 1900, 476, 42, 4, 99, 100, 0, 9, 10, 1000]  # issue/F2P
    for _ in range(N_FUZZ):
        cases.append(rng.randint(0, MAX_FUZZ_YEAR))

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
    print("G-CONF OK: R/I shadow of twoDigitYear agrees with the patched source "
          "line `'%%02d' %% (year %% 100)` on %d years (exhaustive 0..9999 + "
          "issue/F2P boundaries + fuzz, seed=%d), 0 disagreements. No axioms."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
