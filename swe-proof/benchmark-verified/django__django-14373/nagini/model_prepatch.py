"""Twin-artifact model for django__django-14373.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A calendar year (a positive integer in the supported range) is rendered as
  its decimal representation in a CONSTANT FOUR-CHARACTER field, left-padded
  with the zero digit when the value has fewer than four significant digits. So a
  one-, two- or three-digit year still produces exactly four characters, the
  leading positions carrying '0', while a four-digit year produces its own
  four digits. Concretely the rendered field is

      <thousands><hundreds><tens><units>

  where each position holds the ASCII decimal digit for that place value of the
  year; for a year below 1000 the high positions are the zero digit, never
  dropped. Every character of the result is an ASCII decimal digit and the four
  place-value digits, read most-significant first, reconstruct the year exactly.

Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
zero-padded constant-width decimal rendering is the changed operation and is
modelled DEEPLY as the spelled-out place-value digit decomposition; there is
no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: the constant-width zero-padded decimal rendering is
#  modelled deeply as a place-value digit decomposition of expressible pieces.)
# axioms-end


# pure-start
@Pure
def digit(d: int) -> int:
    """The ASCII code point of a single decimal digit value 0..9."""
    Requires(0 <= d and d <= 9)
    Ensures(48 <= Result() and Result() <= 57)
    Ensures(Result() == 48 + d)
    return 48 + d


@Pure
def thousands(year: int) -> int:
    """Thousands place value of a four-digit-range year."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return year // 1000


@Pure
def hundreds(year: int) -> int:
    """Hundreds place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return (year // 100) % 10


@Pure
def tens(year: int) -> int:
    """Tens place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return (year // 10) % 10


@Pure
def units(year: int) -> int:
    """Units place value."""
    Requires(0 <= year and year <= 9999)
    Ensures(0 <= Result() and Result() <= 9)
    return year % 10


@Pure
def four_field(year: int) -> PSeq[int]:
    """The four-character zero-padded decimal field for a supported year: the
    ASCII digits of the thousands, hundreds, tens and units place values, most
    significant first. Always four code points; leading zeros are retained."""
    Requires(0 <= year and year <= 9999)
    Ensures(len(Result()) == 4)
    return PSeq(digit(thousands(year)),
                digit(hundreds(year)),
                digit(tens(year)),
                digit(units(year)))
# pure-end


def render_year(year: int) -> List[int]:
    # pre-conditions-start
    Requires(1 <= year and year <= 9999)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The rendered field is the deep place-value decomposition.
    Ensures(ToSeq(Result()) == four_field(year))
    # Constant width: exactly four characters regardless of magnitude — this is
    # the zero-padding guarantee that distinguishes a sub-1000 year from its
    # bare significant digits.
    Ensures(len(Result()) == 4)
    # Every character is an ASCII decimal digit.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
                                           48 <= Result()[k] and Result()[k] <= 57),
                                    [[Result()[k]]])))
    # The four place-value digits, most significant first, reconstruct the year.
    Ensures((Result()[0] - 48) * 1000
            + (Result()[1] - 48) * 100
            + (Result()[2] - 48) * 10
            + (Result()[3] - 48) == year)
    # The leading (thousands) position is exactly the thousands digit, which for
    # any year below 1000 is the zero digit and is never dropped.
    Ensures(Result()[0] == 48 + year // 1000)
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the year is rendered by its bare decimal value, whose
    # most-significant leading-zero positions are not carried — a sub-1000 year
    # yields fewer than four characters.
    result = []  # type: List[int]
    started = False
    d3 = thousands(year)
    if d3 > 0:
        result.append(digit(d3))
        started = True
    d2 = hundreds(year)
    if started or d2 > 0:
        result.append(digit(d2))
        started = True
    d1 = tens(year)
    if started or d1 > 0:
        result.append(digit(d1))
        started = True
    d0 = units(year)
    result.append(digit(d0))
    return result
    # impl-end
