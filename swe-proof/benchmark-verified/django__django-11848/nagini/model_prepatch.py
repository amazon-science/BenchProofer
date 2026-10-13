"""Twin-artifact model for django__django-11848.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A two-digit calendar year (0..99), taken from a legacy date stamp, must be
  expanded to a full four-digit year RELATIVE TO A REFERENCE YEAR. The rule,
  per the HTTP date specification:

    * the expanded year shares the same last two digits as the two-digit input;
    * it lies in the reference year's century when that places it no more than
      fifty years ahead of the reference year;
    * a value that would otherwise fall MORE THAN fifty years in the future of
      the reference year is instead taken to mean the most recent past year with
      those same last two digits (i.e. it rolls back one century).

  Equivalently, writing `c` for the reference year's last two digits and
  `base` for its century start (reference year minus `c`): the result is
  `input + base` when `input - c <= 50`, and `input + base - 100` otherwise.

The reference year is supplied by the (unchanged) wall-clock source the caller
consults; it is modelled here as an explicit parameter `reference_year`. The
whole computation is exact integer arithmetic.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axioms: the changed operation is exact integer arithmetic,
# modelled deeply in the `pure` region below. The reference year is an explicit
# integer parameter standing in for the unchanged wall-clock source — see
# mapping.md / axiom_check.py for its provenance and soundness check.)
# axioms-end


# pure-start
@Pure
def century_start(reference_year: int) -> int:
    """The start of the reference year's century (reference year with its last
    two digits cleared)."""
    return reference_year - (reference_year % 100)


@Pure
def resolved_year(two_digit_year: int, reference_year: int) -> int:
    """The full year a two-digit year denotes relative to `reference_year`:
    same last two digits, placed in the reference century unless that would be
    more than fifty years ahead — in which case the previous century is used."""
    Requires(reference_year >= 0)
    if two_digit_year - (reference_year % 100) > 50:
        return two_digit_year + century_start(reference_year) - 100
    return two_digit_year + century_start(reference_year)
# pure-end


def expand_two_digit_year(two_digit_year: int, reference_year: int) -> int:
    # pre-conditions-start
    # A genuine two-digit year, and a real (four-digit) reference calendar year.
    Requires(0 <= two_digit_year and two_digit_year < 100)
    Requires(reference_year >= 1000)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the reference-relative expansion of the input.
    Ensures(Result() == resolved_year(two_digit_year, reference_year))
    # It preserves the last two digits of the input.
    Ensures(Result() % 100 == two_digit_year)
    # It is never more than fifty years ahead of the reference year ...
    Ensures(Result() - reference_year <= 50)
    # ... and never more than (49 years + most of a century) behind it, i.e. the
    # chosen year is the most recent one with those last two digits that is not
    # excessively future.
    Ensures(reference_year - Result() < 150)
    # post-conditions-end
    # impl-start
    # Pre-patch (buggy) skeleton: a FIXED cut-off at 70 that ignores the
    # reference year entirely (0..69 -> 2000s, 70..99 -> 1900s).
    if two_digit_year < 70:
        result = two_digit_year + 2000
    else:
        result = two_digit_year + 1900
    return result
    # impl-end
