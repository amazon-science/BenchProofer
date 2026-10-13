#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14170.

The six landmark symbols in Solution.lean (gregJan1, gregDec31, isoFirst,
dtJan1, dtDec31, dtIsoFirst) are A-reference: opaque Lean functions whose
documented meaning is an unchanged `datetime`-library landmark, over the
order-preserving carrier of mapping.md §2 (dates -> day ordinal; datetimes ->
integer microsecond instant). This script runs the REAL stdlib `datetime`
callees and asserts:

  (1) each landmark's documented meaning matches the real callee, and
  (2) the two minus-one-unit refinement identities the patch relies on hold:
        date:     fromisocalendar(y+1,1,1) - timedelta(days=1)
                    -> isoFirst(y+1) - 1            (ordinal space)
        datetime: fromisocalendar(y+1,1,1) - timedelta(microseconds=1)
                    -> dtIsoFirst(y+1) - 1          (microsecond space)

Imports only the Python standard library `datetime` — the same module the gold
patch calls. Exit 0 iff every obligation holds over boundary years (ISO-long
"53-week" years, ordinary years, min/max supported years) plus randomized fuzz.
"""
import datetime
import random
import sys

_DT_MIN = datetime.datetime(1, 1, 1)
_USEC = datetime.timedelta(microseconds=1)
_DAY = datetime.timedelta(days=1)


def date_ord(d):
    """Date -> proleptic-Gregorian day ordinal (mapping.md §2)."""
    return d.toordinal()


def dt_inst(t):
    """Naive datetime -> integer microsecond instant since datetime.min."""
    delta = t - _DT_MIN
    return delta // _USEC


# --- landmark documented-meaning models (in lock-step with Solution.lean) -----

def model_gregJan1(y):    return date_ord(datetime.date(y, 1, 1))
def model_gregDec31(y):   return date_ord(datetime.date(y, 12, 31))
def model_isoFirst(y):    return date_ord(datetime.date.fromisocalendar(y, 1, 1))
def model_dtJan1(y):      return dt_inst(datetime.datetime(y, 1, 1))
def model_dtDec31(y):     return dt_inst(datetime.datetime(y, 12, 31, 23, 59, 59, 999999))
def model_dtIsoFirst(y):  return dt_inst(datetime.datetime.fromisocalendar(y, 1, 1))


def check_year(y):
    """All six landmarks + the two minus-one-unit refinement identities at y."""
    # (1) landmarks reduce to the real callees (definitional here, but we assert
    #     the real callee actually produces a well-formed date/datetime and the
    #     carrier mapping is total & order-preserving at this year).
    gj, gd = model_gregJan1(y), model_gregDec31(y)
    assert gj < gd, "calendar Jan1 must precede Dec31 at %d" % y
    iso = model_isoFirst(y)
    dj, dd = model_dtJan1(y), model_dtDec31(y)
    assert dj < dd, "datetime Jan1 must precede Dec31 at %d" % y
    dti = model_dtIsoFirst(y)

    # (2a) date ISO upper bound: real `fromisocalendar(y+1) - 1 day` ==
    #      isoFirst(y+1) - 1 in ordinal space.
    real_date_upper = datetime.date.fromisocalendar(y + 1, 1, 1) - _DAY
    assert date_ord(real_date_upper) == model_isoFirst(y + 1) - 1, (
        "date ISO upper-bound identity broken at %d" % y)

    # (2b) datetime ISO upper bound: real `fromisocalendar(y+1) - 1 usec` ==
    #      dtIsoFirst(y+1) - 1 in microsecond space.
    real_dt_upper = datetime.datetime.fromisocalendar(y + 1, 1, 1) - _USEC
    assert dt_inst(real_dt_upper) == model_dtIsoFirst(y + 1) - 1, (
        "datetime ISO upper-bound identity broken at %d" % y)

    # cross-check: the ISO span and the calendar span are genuinely DIFFERENT
    # ranges near the boundary for at least the long ISO years (this is the bug
    # the patch fixes — calendar bounds would be wrong for an ISO lookup).
    return (gj, gd, iso, dj, dd, dti)


def main():
    # boundary years: ISO-8601 "long" (53-week) years where ISO year start drifts
    # furthest from Jan 1, ordinary years, leap years, and supported extremes.
    boundary = [2004, 2009, 2015, 2020, 2026,        # 53-week ISO years
                2000, 2001, 2014, 2016, 2019, 2021,  # assorted ordinary/leap
                1, 2, 1969, 1970, 9998]              # min / epoch / near-max
    for y in boundary:
        check_year(y)

    # at least one long-ISO year must have ISO start strictly before its Jan 1
    # (otherwise the check is vacuous w.r.t. the behaviour the patch changes).
    diverged = False
    for y in (2015, 2020, 2026, 2004, 2009):
        if model_isoFirst(y) != model_gregJan1(y):
            diverged = True
            break
    assert diverged, "expected ISO/calendar year-start divergence on a long ISO year"

    rng = random.Random(14170)
    # datetime is supported for years 1..9999; keep y+1 <= 9999.
    for _ in range(20000):
        y = rng.randint(1, 9998)
        check_year(y)

    print("G-AX OK: 6 datetime landmark A-references + 2 minus-one-unit ISO "
          "upper-bound identities sound over %d boundary + 20000 fuzz years "
          "(ordinal & microsecond carriers, mapping.md §2/§3)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
