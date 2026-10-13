"""Twin-artifact model for django__django-16429.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A human-readable elapsed-time string is computed by first shifting the source
  moment forward by a whole number of years and months to an intermediate
  reference moment, then measuring the leftover span between the current moment
  and that reference. The current moment is established with the SAME
  time-zone disposition as the source moment: it is offset-aware exactly when
  the source moment is offset-aware, and offset-naive otherwise.

  The leftover span is the difference between the current moment and the
  intermediate reference moment, in that order (the current moment minus the
  reference moment). That difference is only well-defined when the two operands
  share a time-zone disposition: subtracting an offset-naive moment from an
  offset-aware one (or vice versa) is undefined. The measured span is consumed
  downstream to render the residual portion of the elapsed-time string, so the
  behaviour observes BOTH the constructed reference moment and the measured
  span; the span's magnitude is abstract here, but which ordered pair of
  moments it measures is observed.

  Therefore the intermediate reference moment built from the source's calendar
  and clock fields must carry the SAME time-zone disposition as the source
  moment, so that — the current moment already agreeing with the source — the
  leftover-span difference is well-defined for every source moment, whether
  offset-aware or offset-naive.

A moment is modelled as a minimal class carrying only the touched fields: the
calendar/clock components (ints) and a time-zone disposition. The disposition
is modelled as `Optional[int]`: an offset (in minutes) when offset-aware, and
`None` when offset-naive (Nagini bans real `tzinfo` objects; only the
aware/naive distinction and the carried offset are observed here). The
difference of two moments is modelled as a domain-restricted operation that is
defined only when both operands share a disposition and whose value is the
abstract ordered span of exactly those two operands.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Moment:
    def __init__(self, year: int, month: int, day: int, hour: int,
                 minute: int, second: int, tz: Optional[int]) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.year) and self.year == year)        # type: ignore
        Ensures(Acc(self.month) and self.month == month)     # type: ignore
        Ensures(Acc(self.day) and self.day == day)           # type: ignore
        Ensures(Acc(self.hour) and self.hour == hour)        # type: ignore
        Ensures(Acc(self.minute) and self.minute == minute)  # type: ignore
        Ensures(Acc(self.second) and self.second == second)  # type: ignore
        Ensures(Acc(self.tz) and self.tz is tz)              # type: ignore
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz = tz


# pure-start
@Pure
def is_offset_aware(tz: Optional[int]) -> bool:
    """A disposition is offset-aware exactly when an offset is carried."""
    return tz is not None


@Pure
def same_disposition(a: Optional[int], b: Optional[int]) -> bool:
    """Two moments share a disposition when they are both offset-aware or both
    offset-naive. This is exactly the condition under which their difference is
    defined."""
    return is_offset_aware(a) == is_offset_aware(b)
# pure-end


# axioms-start
# The leftover-span measure between two moments, as an ABSTRACT (uninterpreted)
# quantity: moment_span(a, b) names the value of the ordered difference
# "a minus b". Its magnitude is deliberately unconstrained (no numeric value is
# pinned inside this slice), but the value is a function of the two operands IN
# ORDER — the difference of a and b is not interchangeable with the difference
# of b and a, nor with the difference of any other pair of moments.
@Pure
@ContractOnly
def moment_span(a: Moment, b: Moment) -> int:
    Requires(Acc(a.tz, 1 / 2))
    Requires(Acc(b.tz, 1 / 2))


# The guarded leftover-span difference of two moments. Its load-bearing content
# is twofold: (1) the DOMAIN restriction — the difference is defined only when
# the two operands share a time-zone disposition (an aware/naive mix is
# undefined); (2) the VALUE claim — the returned value is exactly the abstract
# ordered span of its two operands, moment_span(now, pivot), i.e. the current
# moment minus the reference moment, so a caller must invoke the difference on
# precisely that ordered pair to obtain the measured span.
#
# This is an A-reference: the domain rule and the ordered-difference semantics
# are the real moment-subtraction behaviour, validated == this contract by
# axiom_check.py (G-AX). The behaviour under specification ensures the
# intermediate reference moment shares the source's disposition so the domain
# restriction is always honoured.
@ContractOnly
def well_defined_diff(now: Moment, pivot: Moment) -> int:
    Requires(Acc(now.tz, 1 / 2))
    Requires(Acc(pivot.tz, 1 / 2))
    Requires(same_disposition(now.tz, pivot.tz))
    Requires(MustTerminate(6))
    Ensures(Acc(now.tz, 1 / 2))
    Ensures(Acc(pivot.tz, 1 / 2))
    Ensures(Result() == moment_span(now, pivot))
# axioms-end


def pivot_remaining(d: Moment, now: Moment,
                    pivot_year: int, pivot_month: int,
                    pivot_day: int) -> Tuple[Moment, int]:
    # pre-conditions-start
    # `d` is the read-only source moment.
    Requires(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
    Requires(Acc(d.hour, 1 / 2) and Acc(d.minute, 1 / 2) and Acc(d.second, 1 / 2))
    Requires(Acc(d.tz, 1 / 2))
    # `now` is the read-only current moment, established to agree with `d` on
    # its time-zone disposition (offset-aware iff `d` is).
    Requires(Acc(now.tz, 1 / 2))
    Requires(same_disposition(now.tz, d.tz))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(d.year, 1 / 2) and Acc(d.month, 1 / 2) and Acc(d.day, 1 / 2))
    Ensures(Acc(d.hour, 1 / 2) and Acc(d.minute, 1 / 2) and Acc(d.second, 1 / 2))
    Ensures(Acc(d.tz, 1 / 2))
    Ensures(Acc(now.tz, 1 / 2))
    # The intermediate reference moment is the source advanced to the supplied
    # calendar position (year/month/day), carrying the source's clock fields
    # unchanged and, crucially, the source's time-zone disposition — so the
    # leftover-span difference against the current moment is well-defined and
    # measures only the residual span beyond that advanced position.
    Ensures(Acc(Result()[0].year) and Result()[0].year == pivot_year)
    Ensures(Acc(Result()[0].month) and Result()[0].month == pivot_month)
    Ensures(Acc(Result()[0].day) and Result()[0].day == pivot_day)
    Ensures(Acc(Result()[0].hour) and Result()[0].hour == d.hour)
    Ensures(Acc(Result()[0].minute) and Result()[0].minute == d.minute)
    Ensures(Acc(Result()[0].second) and Result()[0].second == d.second)
    Ensures(Acc(Result()[0].tz))
    Ensures(Result()[0].tz is d.tz)
    # The measured leftover span is the ordered difference "current moment
    # minus the constructed reference moment" — this pins WHICH difference the
    # behaviour measures (its operands and their order), while leaving the
    # abstract magnitude to the difference operation itself.
    Ensures(Result()[1] == moment_span(now, Result()[0]))
    # post-conditions-end
    # impl-start
    pivot = Moment(
        pivot_year,
        pivot_month,
        pivot_day,
        d.hour,
        d.minute,
        d.second,
        d.tz,
    )
    # The leftover span: requires now and pivot share a disposition. This call
    # is provable only because pivot carries d.tz and now agrees with d; it
    # measures the ordered difference of the current moment and the reference
    # moment, which is returned alongside the constructed reference moment.
    remaining = well_defined_diff(now, pivot)
    return pivot, remaining
    # impl-end
