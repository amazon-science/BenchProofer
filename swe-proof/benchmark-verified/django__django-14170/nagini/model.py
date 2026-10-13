"""Twin-artifact model for django__django-14170.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A year lookup that compares a stored date/datetime against a looked-up year
  is answered by a range comparison against the two endpoints of that year,
  rather than by extracting the year of every row.  The two endpoints must be
  the first and last day/instant of the *same* notion of year that the lookup
  uses:

    * an ordinary year lookup uses the proleptic-Gregorian calendar year, whose
      endpoints are January 1 and December 31 of that year (for a date-typed
      column: those days; for a datetime-typed column: the first and the last
      microsecond instant of those days);
    * a week-numbering (ISO-8601) year lookup uses the ISO week-numbering year,
      whose first day/instant is the first day/instant of its week 1 and whose
      last day/instant is the one immediately before the first day/instant of
      the next week-numbering year.

  The endpoint pair must therefore bound EXACTLY the days (resp. instants)
  belonging to the requested year under the matching calendar (this is the
  membership the range comparison reproduces; see the constructor contracts
  and mapping.md).  Because the two calendars disagree near the year boundary,
  the endpoints of the calendar a lookup uses are the ones that bound
  precisely its days/instants.

  The lookup decides which calendar applies from the kind of year being
  extracted on its left-hand side: a week-numbering extraction selects the
  ISO endpoints, anything else the calendar endpoints.  The field kind decides
  which VALUE SPACE the endpoints live in: a date-typed column is bounded by
  whole days, a datetime-typed column by microsecond instants — the two are
  different carriers, so a datetime lookup must be answered with instant
  endpoints and a date lookup with day endpoints.  Both the calendar decision
  and the field kind are forwarded to the endpoint computation.

Dates are modelled as their integer day-ordinal and datetimes as their integer
microsecond instant since the epoch datetime.min (Nagini has no date type;
both encodings are strictly order-preserving bijections, see mapping.md §2).
The endpoint constructors are unchanged stdlib callees, axiomatized (kind A);
their exact membership meaning — that each [lower, upper] interval is
precisely one year under its own calendar in its own carrier, the calendars
disagreeing on the late-December / early-January boundary the tests probe —
is validated against the real standard library out of band (axiom_check.py /
G-AX), as recorded in mapping.md.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def cal_jan1(year: int) -> int:
    """Day-ordinal of January 1 of `year` (date(year, 1, 1).toordinal()).
    Lower endpoint of the proleptic-Gregorian calendar year: the smallest
    day-ordinal whose calendar year is `year`.  Unchanged stdlib callee;
    the day-membership meaning is validated by G-AX.  Provenance: mapping.md."""


@Pure
@ContractOnly
def cal_dec31(year: int) -> int:
    """Day-ordinal of December 31 of `year` (date(year, 12, 31).toordinal()).
    Upper endpoint of the calendar year: the largest day-ordinal whose calendar
    year is `year`, so [cal_jan1(year), cal_dec31(year)] is exactly that
    calendar year.  Unchanged stdlib callee.  Provenance: mapping.md."""


@Pure
@ContractOnly
def iso_jan1(year: int) -> int:
    """Day-ordinal of the first day of ISO-8601 week-numbering year `year`
    (date.fromisocalendar(year, 1, 1).toordinal()).  It is the smallest
    day-ordinal whose ISO year is `year`; the next ISO year begins at
    iso_jan1(year + 1), so [iso_jan1(year), iso_jan1(year + 1) - 1] is exactly
    ISO year `year`.  Unchanged stdlib callee; the day-membership meaning is
    validated by G-AX.  Provenance: mapping.md."""


@Pure
@ContractOnly
def dt_jan1(year: int) -> int:
    """Microsecond instant of datetime(year, 1, 1) — the FIRST instant of
    calendar year `year` (instants counted from datetime.min, mapping.md §2).
    Lower endpoint of the calendar year in instant space: the smallest instant
    whose calendar year is `year`.  Unchanged stdlib callee; the
    instant-membership meaning is validated by G-AX.  Provenance: mapping.md."""


@Pure
@ContractOnly
def dt_dec31(year: int) -> int:
    """Microsecond instant of datetime(year, 12, 31, 23, 59, 59, 999999) — the
    LAST instant of calendar year `year`: the largest instant whose calendar
    year is `year`, so [dt_jan1(year), dt_dec31(year)] is exactly that calendar
    year in instant space (dt_dec31(year) + 1 == dt_jan1(year + 1)).  Unchanged
    stdlib callee; validated by G-AX.  Provenance: mapping.md."""


@Pure
@ContractOnly
def dt_iso_jan1(year: int) -> int:
    """Microsecond instant of datetime.fromisocalendar(year, 1, 1) — the first
    instant of ISO-8601 week-numbering year `year`.  It is the smallest instant
    whose ISO year is `year`; the next ISO year begins at dt_iso_jan1(year + 1),
    so [dt_iso_jan1(year), dt_iso_jan1(year + 1) - 1] is exactly ISO year
    `year` in instant space.  Unchanged stdlib callee; the instant-membership
    meaning is validated by G-AX.  Provenance: mapping.md."""
# axioms-end


# pure-start
@Pure
def date_lower(value: int, week_numbering: bool) -> int:
    """Lower DAY endpoint for a date-typed column, selected by the calendar
    the lookup uses: the first day of the ISO year when week-numbering,
    otherwise of the calendar year."""
    if week_numbering:
        return iso_jan1(value)
    return cal_jan1(value)


@Pure
def date_upper(value: int, week_numbering: bool) -> int:
    """Upper DAY endpoint for a date-typed column: the last day of the ISO
    year (the day before the next ISO year's first day) when week-numbering,
    otherwise the last day of the calendar year."""
    if week_numbering:
        return iso_jan1(value + 1) - 1
    return cal_dec31(value)


@Pure
def dt_lower(value: int, week_numbering: bool) -> int:
    """Lower INSTANT endpoint for a datetime-typed column: the first instant
    of the ISO year when week-numbering, otherwise of the calendar year."""
    if week_numbering:
        return dt_iso_jan1(value)
    return dt_jan1(value)


@Pure
def dt_upper(value: int, week_numbering: bool) -> int:
    """Upper INSTANT endpoint for a datetime-typed column: the instant one
    microsecond before the next ISO year's first instant when week-numbering,
    otherwise the last instant of the calendar year."""
    if week_numbering:
        return dt_iso_jan1(value + 1) - 1
    return dt_dec31(value)


@Pure
def lookup_lower(is_datetime_field: bool, value: int, week_numbering: bool) -> int:
    """Lower endpoint the whole lookup must produce: instants for a
    datetime-typed column, days for a date-typed one — the field kind selects
    the CARRIER, the week-numbering flag the calendar."""
    if is_datetime_field:
        return dt_lower(value, week_numbering)
    return date_lower(value, week_numbering)


@Pure
def lookup_upper(is_datetime_field: bool, value: int, week_numbering: bool) -> int:
    """Upper endpoint the whole lookup must produce (see lookup_lower)."""
    if is_datetime_field:
        return dt_upper(value, week_numbering)
    return date_upper(value, week_numbering)
# pure-end


def date_field_year_range(value: int, week_numbering: bool) -> List[int]:
    # pre-conditions-start
    Requires(True)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The two endpoints are exactly the first/last DAY of the requested year
    # under the calendar the lookup uses (calendar vs. ISO week-numbering).
    Ensures(Result()[0] == date_lower(value, week_numbering))
    Ensures(Result()[1] == date_upper(value, week_numbering))
    # post-conditions-end
    # impl-start
    if week_numbering:
        first = iso_jan1(value)
        second = iso_jan1(value + 1) - 1
    else:
        first = cal_jan1(value)
        second = cal_dec31(value)
    return [first, second]
    # impl-end


def datetime_field_year_range(value: int, week_numbering: bool) -> List[int]:
    # pre-conditions-start
    Requires(True)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The two endpoints are exactly the first/last INSTANT of the requested
    # year — the microsecond-instant carrier, NOT the day carrier: a datetime
    # column is bounded by instants, not by whole days.
    Ensures(Result()[0] == dt_lower(value, week_numbering))
    Ensures(Result()[1] == dt_upper(value, week_numbering))
    # post-conditions-end
    # impl-start
    if week_numbering:
        first = dt_iso_jan1(value)
        second = dt_iso_jan1(value + 1) - 1
    else:
        first = dt_jan1(value)
        second = dt_dec31(value)
    return [first, second]
    # impl-end


def year_lookup_range(is_datetime_field: bool, lhs_is_week_numbering: bool, year: int) -> List[int]:
    # pre-conditions-start
    Requires(True)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    # The calendar is decided by the kind of year extracted on the lhs, the
    # VALUE SPACE (day vs. instant) by the field kind; both must be forwarded
    # to the endpoint computation.  Routing a datetime field to the date
    # endpoints (or vice versa) violates this postcondition: the two carriers
    # are distinct.
    Ensures(Result()[0] == lookup_lower(is_datetime_field, year, lhs_is_week_numbering))
    Ensures(Result()[1] == lookup_upper(is_datetime_field, year, lhs_is_week_numbering))
    # post-conditions-end
    # impl-start
    if is_datetime_field:
        bounds = datetime_field_year_range(year, lhs_is_week_numbering)
    else:
        bounds = date_field_year_range(year, lhs_is_week_numbering)
    return bounds
    # impl-end
