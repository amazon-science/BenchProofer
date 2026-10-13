#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-14170.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the two Lean skeletons
(`implementation_yearBoundsDate`, `implementation_yearBoundsDatetime`) and diffs
them against the REAL patched callees

    django.db.backends.base.operations.BaseDatabaseOperations
        .year_lookup_bounds_for_date_field(value, iso_year)
        .year_lookup_bounds_for_datetime_field(value, iso_year)

over a discrete catalogue of (year, iso_year) cases plus >=1e5 randomized cases,
covering both the calendar branch (iso_year=False) and the ISO-8601
week-numbering branch (iso_year=True).

Bridge (mapping.md):
  * a date bound (a `datetime.date`) <-> its proleptic-Gregorian ordinal Int;
  * a datetime bound (a naive `datetime.datetime`, USE_TZ=False) <-> microseconds
    since the ordinal epoch = date.toordinal()*86400000000 + intraday micros.
The real callees apply `adapt_*field_value` (= str(...)) to each bound; the
shadow ordinals are mapped back to date/datetime objects and stringified the
same way so the comparison is on the serialized bounds the query actually uses.

Exit 0 iff zero disagreements. stdlib only; pinned seed.
"""
import datetime
import random
import sys

SEED = 20210323
N_RANDOM = 120_000  # >= 1e5
US_PER_DAY = 86400000000

# datetime range is [MINYEAR=1, MAXYEAR=9999]; value+1 must stay <= 9999, and
# fromisocalendar(value,1,1) may land in value-1, so keep value in [2, 9998].
YEAR_LO = 2
YEAR_HI = 9998


# ---- deep models (mirror Solution.lean `pure` region) -----------------------

def greg_jan1(y):
    """Ordinal of Jan 1st of year y (= datetime.date(y,1,1).toordinal())."""
    return 1 + 365 * (y - 1) + (y - 1) // 4 - (y - 1) // 100 + (y - 1) // 400


def greg_dec31(y):
    return greg_jan1(y + 1) - 1


def iso_year_start(y):
    jan4 = greg_jan1(y) + 3
    return jan4 - ((jan4 - 1) % 7)


# ---- Python shadows of the Lean implementations -----------------------------

def shadow_date(value, iso_year):
    """Returns (first_ordinal, second_ordinal)."""
    if iso_year:
        first = iso_year_start(value)
        second = iso_year_start(value + 1) - 1
    else:
        first = greg_jan1(value)
        second = greg_dec31(value)
    return (first, second)


def shadow_datetime(value, iso_year):
    """Returns (first_us, second_us)."""
    if iso_year:
        first = iso_year_start(value) * US_PER_DAY
        second = iso_year_start(value + 1) * US_PER_DAY - 1
    else:
        first = greg_jan1(value) * US_PER_DAY
        second = greg_jan1(value + 1) * US_PER_DAY - 1
    return (first, second)


# ---- bridge: shadow Int -> the same serialized bound the callee returns -----

def date_str_from_ordinal(o):
    return str(datetime.date.fromordinal(o))


def datetime_str_from_us(us):
    days, rem = divmod(us, US_PER_DAY)
    dt = datetime.datetime.fromordinal(days) + datetime.timedelta(microseconds=rem)
    return str(dt)


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(USE_TZ=False, DATABASES={}, INSTALLED_APPS=[])
        django.setup()
        from django.db.backends.base.operations import BaseDatabaseOperations
    except Exception as e:  # pragma: no cover
        print(f"status=error could not import Django: {e}")
        return 1

    ops = BaseDatabaseOperations(connection=None)

    rng = random.Random(SEED)
    cases = []
    # discrete catalogue: ISO-boundary years from the issue/tests + edges.
    discrete = [2, 3, 1900, 2013, 2014, 2015, 2016, 2017, 2019, 2020, 2021,
                2099, 2100, 9997, 9998]
    for y in discrete:
        cases.append((y, False))
        cases.append((y, True))
    # calendar branch is valid up to 9999 (ISO branch needs value+1 -> <=9998).
    cases.append((1, False))
    cases.append((1, True))
    cases.append((9999, False))
    for _ in range(N_RANDOM):
        iso_year = rng.choice([False, True])
        hi = YEAR_HI if iso_year else 9999
        y = rng.randint(YEAR_LO, hi)
        cases.append((y, iso_year))

    disagreements = 0
    checked = 0
    for value, iso_year in cases:
        # date
        real_d = ops.year_lookup_bounds_for_date_field(value, iso_year=iso_year)
        sf, ss = shadow_date(value, iso_year)
        exp_d = [date_str_from_ordinal(sf), date_str_from_ordinal(ss)]
        checked += 1
        if list(real_d) != exp_d:
            disagreements += 1
            if disagreements <= 5:
                print(f"DATE MISMATCH value={value} iso={iso_year}: "
                      f"real={real_d!r} shadow={exp_d!r}")
        # datetime
        real_dt = ops.year_lookup_bounds_for_datetime_field(value, iso_year=iso_year)
        df, ds = shadow_datetime(value, iso_year)
        exp_dt = [datetime_str_from_us(df), datetime_str_from_us(ds)]
        checked += 1
        if list(real_dt) != exp_dt:
            disagreements += 1
            if disagreements <= 5:
                print(f"DATETIME MISMATCH value={value} iso={iso_year}: "
                      f"real={real_dt!r} shadow={exp_dt!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
