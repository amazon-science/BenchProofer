#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14170.

Executes the REAL standard-library date/datetime constructors that the gold
patch calls and asserts that every kind-A axiom in model.py over-approximates
them, i.e. that each axiomatized endpoint constructor really has the
membership meaning the model relies on, in its own carrier:

  DAY carrier (date-typed columns, ordinals via .toordinal()):
  (A) cal_jan1(year) == date(year, 1, 1).toordinal()
      cal_dec31(year) == date(year, 12, 31).toordinal()
      and the closed ordinal interval [cal_jan1(year), cal_dec31(year)] is
      EXACTLY the set of day-ordinals whose proleptic-Gregorian calendar year
      is `year`.
  (B) iso_jan1(year) == date.fromisocalendar(year, 1, 1).toordinal()
      and the closed ordinal interval [iso_jan1(year), iso_jan1(year+1) - 1]
      is EXACTLY the set of day-ordinals whose ISO-8601 week-numbering year
      is `year`.

  INSTANT carrier (datetime-typed columns, integer microseconds since
  datetime.min — a strictly order-preserving bijection):
  (C) dt_jan1(year)  == instant of datetime(year, 1, 1)
      dt_dec31(year) == instant of datetime(year, 12, 31, 23, 59, 59, 999999)
      and [dt_jan1(year), dt_dec31(year)] is EXACTLY calendar year `year` in
      instant space: dt_dec31(year) + 1 == dt_jan1(year + 1), and the
      endpoints' datetimes carry year `year`.
  (D) dt_iso_jan1(year) == instant of datetime.fromisocalendar(year, 1, 1)
      and [dt_iso_jan1(year), dt_iso_jan1(year+1) - 1] is EXACTLY ISO year
      `year` in instant space; the patch's `- timedelta(microseconds=1)`
      upper endpoint is dt_iso_jan1(year+1) - 1.

  Cross-carrier consistency: each dt_* landmark's instant lies on the very
  day its day-carrier counterpart names (instant // USECS_PER_DAY maps
  dt_jan1 -> cal_jan1, dt_iso_jan1 -> iso_jan1, dt_dec31 -> cal_dec31), and
  the day carrier and instant carrier are genuinely DIFFERENT value spaces
  (their numerals never collide on the tested years), so routing a datetime
  lookup to the date endpoints is observably wrong.

The two calendars disagree on the late-December / early-January boundary days
(a December day may belong to the next ISO year, a January day to the previous
ISO year) — exactly the days the FAIL_TO_PASS boundary test probes, so the
check exercises those boundaries explicitly.

Imports only the standard library (`datetime`) — the same module the gold patch
calls (`datetime.date`, `datetime.date.fromisocalendar`, `datetime.datetime`,
`datetime.datetime.fromisocalendar`).  Exit 0 iff every obligation holds.
"""
import datetime
import random
import sys

ONE_DAY = datetime.timedelta(days=1)
ONE_USEC = datetime.timedelta(microseconds=1)
DT_MIN = datetime.datetime(1, 1, 1)
USECS_PER_DAY = 24 * 60 * 60 * 1000000


# --- the axiomatized stdlib callees, as model.py declares them ---------------

def cal_jan1(year):
    return datetime.date(year, 1, 1).toordinal()


def cal_dec31(year):
    return datetime.date(year, 12, 31).toordinal()


def iso_jan1(year):
    return datetime.date.fromisocalendar(year, 1, 1).toordinal()


def dt_inst(t):
    """Naive datetime -> integer microsecond instant since datetime.min."""
    return (t - DT_MIN) // ONE_USEC


def dt_jan1(year):
    return dt_inst(datetime.datetime(year, 1, 1))


def dt_dec31(year):
    return dt_inst(datetime.datetime(year, 12, 31, 23, 59, 59, 999999))


def dt_iso_jan1(year):
    return dt_inst(datetime.datetime.fromisocalendar(year, 1, 1))


def cal_year_of(ordinal):
    return datetime.date.fromordinal(ordinal).year


def iso_year_of(ordinal):
    return datetime.date.fromordinal(ordinal).isocalendar()[0]


def dt_of_inst(inst):
    return DT_MIN + inst * ONE_USEC


# --- the membership checks (day carrier) --------------------------------------

def check_calendar_year(year):
    """[cal_jan1(year), cal_dec31(year)] is exactly calendar year `year`."""
    lo = cal_jan1(year)
    hi = cal_dec31(year)
    assert lo <= hi, "calendar interval empty for %d" % year
    # endpoints lie in the year ...
    assert cal_year_of(lo) == year, "cal_jan1(%d) not in year" % year
    assert cal_year_of(hi) == year, "cal_dec31(%d) not in year" % year
    # ... and the day just outside each endpoint lies in an adjacent year
    if lo - 1 >= 1:
        assert cal_year_of(lo - 1) == year - 1, "below cal_jan1(%d) wrong" % year
    assert cal_year_of(hi + 1) == year + 1, "above cal_dec31(%d) wrong" % year
    # full membership sweep across the whole year plus a margin on each side
    for d in range(max(1, lo - 5), hi + 6):
        in_interval = (lo <= d <= hi)
        in_year = (cal_year_of(d) == year)
        assert in_interval == in_year, (
            "calendar membership mismatch year=%d ordinal=%d "
            "(interval=%s, year_of=%d)" % (year, d, in_interval, cal_year_of(d)))


def check_iso_year(year):
    """[iso_jan1(year), iso_jan1(year+1)-1] is exactly ISO year `year`."""
    lo = iso_jan1(year)
    hi = iso_jan1(year + 1) - 1
    assert lo <= hi, "ISO interval empty for %d" % year
    assert iso_year_of(lo) == year, "iso_jan1(%d) not in ISO year" % year
    assert iso_year_of(hi) == year, "ISO last(%d) not in ISO year" % year
    if lo - 1 >= 1:
        assert iso_year_of(lo - 1) == year - 1, "below iso_jan1(%d) wrong" % year
    assert iso_year_of(hi + 1) == year + 1, "above iso last(%d) wrong" % year
    for d in range(max(1, lo - 5), hi + 6):
        in_interval = (lo <= d <= hi)
        in_year = (iso_year_of(d) == year)
        assert in_interval == in_year, (
            "ISO membership mismatch year=%d ordinal=%d "
            "(interval=%s, iso_year_of=%d)"
            % (year, d, in_interval, iso_year_of(d)))


# --- the membership checks (instant carrier) -----------------------------------

def check_dt_calendar_year(year):
    """[dt_jan1(year), dt_dec31(year)] is exactly calendar year `year` in
    microsecond-instant space."""
    lo = dt_jan1(year)
    hi = dt_dec31(year)
    assert lo <= hi, "dt calendar interval empty for %d" % year
    assert dt_of_inst(lo).year == year, "dt_jan1(%d) not in year" % year
    assert dt_of_inst(hi).year == year, "dt_dec31(%d) not in year" % year
    # exactness: the very next instant is the next year's first instant
    assert hi + 1 == dt_jan1(year + 1), (
        "dt_dec31(%d)+1 != dt_jan1(%d)" % (year, year + 1))
    if lo - 1 >= 0:
        assert dt_of_inst(lo - 1).year == year - 1, "below dt_jan1(%d) wrong" % year
    assert dt_of_inst(hi + 1).year == year + 1, "above dt_dec31(%d) wrong" % year
    # the real callee identities (documented meaning)
    assert lo == dt_inst(datetime.datetime(year, 1, 1))
    assert hi == dt_inst(datetime.datetime(year, 12, 31, 23, 59, 59, 999999))


def check_dt_iso_year(year):
    """[dt_iso_jan1(year), dt_iso_jan1(year+1)-1] is exactly ISO year `year`
    in instant space; the patch's `- timedelta(microseconds=1)` upper endpoint
    equals dt_iso_jan1(year+1) - 1."""
    lo = dt_iso_jan1(year)
    hi = dt_iso_jan1(year + 1) - 1
    assert lo <= hi, "dt ISO interval empty for %d" % year
    assert dt_of_inst(lo).isocalendar()[0] == year, (
        "dt_iso_jan1(%d) not in ISO year" % year)
    assert dt_of_inst(hi).isocalendar()[0] == year, (
        "dt ISO last(%d) not in ISO year" % year)
    assert dt_of_inst(hi + 1).isocalendar()[0] == year + 1, (
        "above dt ISO last(%d) wrong" % year)
    if lo - 1 >= 0:
        assert dt_of_inst(lo - 1).isocalendar()[0] == year - 1, (
            "below dt_iso_jan1(%d) wrong" % year)
    # the gold patch's upper-endpoint arithmetic, replayed on the real callee
    real_upper = datetime.datetime.fromisocalendar(year + 1, 1, 1) - ONE_USEC
    assert dt_inst(real_upper) == hi, (
        "datetime fromisocalendar(%d+1)-1usec != dt_iso_jan1(%d+1)-1"
        % (year, year))


def check_carriers_consistent(year):
    """Each instant landmark lies on the day its day-carrier counterpart
    names, and the two carriers are genuinely different value spaces."""
    # instant -> day consistency (the instant's calendar day IS the landmark day)
    assert dt_of_inst(dt_jan1(year)).date().toordinal() == cal_jan1(year)
    assert dt_of_inst(dt_dec31(year)).date().toordinal() == cal_dec31(year)
    assert dt_of_inst(dt_iso_jan1(year)).date().toordinal() == iso_jan1(year)
    # distinct carriers: a day ordinal never equals the corresponding instant
    # (instants are ~8.64e10 per day), so date/datetime routing is observable.
    assert dt_jan1(year) != cal_jan1(year), (
        "day and instant carriers collide at %d — routing would be invisible"
        % year)


def check_calendars_disagree(year):
    """The two calendars' intervals genuinely differ — the wrong calendar's
    endpoints misclassify the boundary days (the heart of the bug)."""
    cal_lo, cal_hi = cal_jan1(year), cal_dec31(year)
    iso_lo, iso_hi = iso_jan1(year), iso_jan1(year + 1) - 1
    # Equivalent intervals would make the calendar choice irrelevant; over the
    # tested span they must differ at least at one endpoint.
    assert (cal_lo, cal_hi) != (iso_lo, iso_hi), (
        "calendar and ISO intervals coincide for %d — bug would be invisible"
        % year)
    assert (dt_jan1(year), dt_dec31(year)) != (
        dt_iso_jan1(year), dt_iso_jan1(year + 1) - 1), (
        "dt calendar and ISO intervals coincide for %d" % year)


def check_f2p_boundaries():
    """Replays the FAIL_TO_PASS boundary days: the ISO-year filter must select
    exactly the rows whose ISO year matches, which the (buggy) calendar bounds
    would get wrong.  Replayed in BOTH carriers (the F2P model field is a
    DateTimeField; the date-field bounds share the same day choice)."""
    days = {
        "week_52_day_2014": datetime.date(2014, 12, 27),    # ISO year 2014
        "week_1_day_2014_2015": datetime.date(2014, 12, 31),  # ISO year 2015
        "week_53_day_2015": datetime.date(2015, 12, 31),    # ISO year 2015
    }
    expected_iso = {"week_52_day_2014": 2014,
                    "week_1_day_2014_2015": 2015,
                    "week_53_day_2015": 2015}
    for name, d in days.items():
        assert iso_year_of(d.toordinal()) == expected_iso[name], (
            "F2P day %s ISO year wrong" % name)

    # filter(iso_year=2015) via ISO bounds selects the two ISO-2015 rows
    lo, hi = iso_jan1(2015), iso_jan1(2016) - 1
    selected = {n for n, d in days.items() if lo <= d.toordinal() <= hi}
    assert selected == {"week_1_day_2014_2015", "week_53_day_2015"}, (
        "ISO bounds for 2015 select wrong rows: %s" % selected)

    # The buggy CALENDAR bounds for 2015 would drop the Dec-31-2014 row, which
    # is precisely the regression the fix removes.
    clo, chi = cal_jan1(2015), cal_dec31(2015)
    buggy = {n for n, d in days.items() if clo <= d.toordinal() <= chi}
    assert "week_1_day_2014_2015" not in buggy, (
        "expected calendar bounds to (wrongly) exclude the Dec-31-2014 row")
    assert buggy != selected, "calendar and ISO selections must differ on F2P"

    # filter(iso_year__lte=2014) selects exactly the ISO-2014 row
    hi_2014 = iso_jan1(2015) - 1
    selected_lte = {n for n, d in days.items() if d.toordinal() <= hi_2014}
    assert selected_lte == {"week_52_day_2014"}, (
        "iso_year__lte=2014 selects wrong rows: %s" % selected_lte)

    # INSTANT carrier: the F2P rows are datetimes (14:30:50.000321); the same
    # membership must hold via the dt_* bounds — this is the actual F2P field
    # type (DateTimeField start_datetime).
    stamps = {n: datetime.datetime(d.year, d.month, d.day, 14, 30, 50, 321)
              for n, d in days.items()}
    dlo, dhi = dt_iso_jan1(2015), dt_iso_jan1(2016) - 1
    dsel = {n for n, t in stamps.items() if dlo <= dt_inst(t) <= dhi}
    assert dsel == {"week_1_day_2014_2015", "week_53_day_2015"}, (
        "dt ISO bounds for 2015 select wrong rows: %s" % dsel)
    dclo, dchi = dt_jan1(2015), dt_dec31(2015)
    dbuggy = {n for n, t in stamps.items() if dclo <= dt_inst(t) <= dchi}
    assert "week_1_day_2014_2015" not in dbuggy, (
        "expected dt calendar bounds to (wrongly) exclude the Dec-31-2014 row")
    assert dbuggy != dsel, "dt calendar and ISO selections must differ on F2P"


def main():
    # Boundary + representative years, including the F2P years and leap years
    # and years whose ISO week 1 starts in the previous December.
    years = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021,
             1, 100, 1000, 1999, 2000, 2400, 9998]
    for y in years:
        check_calendar_year(y)
        check_iso_year(y)
        check_dt_calendar_year(y)
        check_dt_iso_year(y)
        check_carriers_consistent(y)
        check_calendars_disagree(y)

    # Randomized fuzz over the supported proleptic-Gregorian range.
    rng = random.Random(14170)
    for _ in range(2000):
        y = rng.randint(2, 9998)
        check_calendar_year(y)
        check_iso_year(y)
        check_dt_calendar_year(y)
        check_dt_iso_year(y)
        check_carriers_consistent(y)

    check_f2p_boundaries()

    print("G-AX OK: cal_jan1/cal_dec31/iso_jan1 (day carrier) + "
          "dt_jan1/dt_dec31/dt_iso_jan1 (microsecond-instant carrier) endpoint "
          "axioms sound — each interval is exactly its year under its own "
          "calendar in its own carrier over %d named + 2000 fuzz years; "
          "carriers consistent and distinct; F2P ISO boundaries reproduced in "
          "both carriers." % len(years))
    return 0


if __name__ == "__main__":
    sys.exit(main())
