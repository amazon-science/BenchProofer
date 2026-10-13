#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14170 (nagini).

SHADOW: the impl regions of model.py (date_field_year_range,
datetime_field_year_range, year_lookup_range), copied verbatim below with the
contract calls (Requires/Ensures) stripped.  The model's carrier is plain int
(day ordinals / microsecond instants), so no PSeq shim is needed; List[int]
is a plain Python list.  The six @ContractOnly axiom callees (cal_jan1,
cal_dec31, iso_jan1, dt_jan1, dt_dec31, dt_iso_jan1) are realized by the REAL
standard-library constructors they axiomatize, exactly as mapping.md section 1
binds them (same realization as axiom_check.py).

ORACLE: the REAL patched repo functions the model models per mapping.md:
  * BaseDatabaseOperations.year_lookup_bounds_for_date_field(value, iso_year)
  * BaseDatabaseOperations.year_lookup_bounds_for_datetime_field(value, iso_year)
  * YearLookup.year_lookup_bounds(connection, year)  (the dispatch)
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the patched modules are importable.

Type bridge (mapping.md section 2):
  * a date endpoint  <-> its .toordinal() day ordinal;
  * a naive datetime endpoint <-> (t - datetime.min) // timedelta(microseconds=1);
  * the iso_year kwarg <-> the week_numbering / lhs_is_week_numbering bool;
  * DateTimeField-vs-not output_field <-> is_datetime_field bool;
  * adapt_datefield_value / adapt_datetimefield_value render each endpoint as
    a driver-ready string of the SAME day/instant (mapping.md models them as
    the identity on the carrier); the bridge parses that rendering back with
    fromisoformat before projecting onto the carrier.
Settings are configured with USE_TZ=False so the timezone make-aware step
(also modeled as identity on the instant) is a no-op.  The dispatch oracle is
driven through real ExtractIsoYear / ExtractYear lhs instances over a Value
with a DateTimeField / DateField output_field, so the isinstance decisions the
model's two booleans abstract are the real ones.

Input domain: the model's Requires is True; the real callees operate on years
where every endpoint constructor is defined, i.e. 1 <= year <= 9998 (the
week-numbering upper endpoint consults year+1, and year 9999's final instant
is the maximum representable).  Generation stays inside that operating domain.

>= 1e5 Requires-satisfying inputs: an EXHAUSTIVE sweep of all 9998 valid years
x both calendar flags for both field-level functions and both dispatch
routings (79,984 comparisons), plus 25,000 fuzz dispatch draws.
Pinned fuzz seed: 14170.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib only (plus the repo under test).
"""
import datetime
import json
import random
import sys
import types

SEED = 14170
N_FUZZ = 25_000
YEAR_MIN, YEAR_MAX = 1, 9998

DT_MIN = datetime.datetime(1, 1, 1)
ONE_USEC = datetime.timedelta(microseconds=1)


# --- the axiomatized stdlib callees, realized as mapping.md binds them --------

def cal_jan1(year):
    return datetime.date(year, 1, 1).toordinal()


def cal_dec31(year):
    return datetime.date(year, 12, 31).toordinal()


def iso_jan1(year):
    return datetime.date.fromisocalendar(year, 1, 1).toordinal()


def _dt_inst(t):
    """Naive datetime -> integer microsecond instant since datetime.min."""
    return (t - DT_MIN) // ONE_USEC


def dt_jan1(year):
    return _dt_inst(datetime.datetime(year, 1, 1))


def dt_dec31(year):
    return _dt_inst(datetime.datetime(year, 12, 31, 23, 59, 59, 999999))


def dt_iso_jan1(year):
    return _dt_inst(datetime.datetime.fromisocalendar(year, 1, 1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def date_field_year_range(value, week_numbering):
    if week_numbering:
        first = iso_jan1(value)
        second = iso_jan1(value + 1) - 1
    else:
        first = cal_jan1(value)
        second = cal_dec31(value)
    return [first, second]


def datetime_field_year_range(value, week_numbering):
    if week_numbering:
        first = dt_iso_jan1(value)
        second = dt_iso_jan1(value + 1) - 1
    else:
        first = dt_jan1(value)
        second = dt_dec31(value)
    return [first, second]


def year_lookup_range(is_datetime_field, lhs_is_week_numbering, year):
    if is_datetime_field:
        bounds = datetime_field_year_range(year, lhs_is_week_numbering)
    else:
        bounds = date_field_year_range(year, lhs_is_week_numbering)
    return bounds


# --- bridge: driver-ready endpoint rendering -> model carrier -----------------

def day_ordinal(v):
    """A date-field endpoint (str rendering or date) -> day ordinal."""
    if isinstance(v, str):
        v = datetime.date.fromisoformat(v)
    if isinstance(v, datetime.datetime):
        v = v.date()
    return v.toordinal()


def usec_instant(v):
    """A datetime-field endpoint (str rendering or datetime) -> instant."""
    if isinstance(v, str):
        v = datetime.datetime.fromisoformat(v)
    return _dt_inst(v)


def main():
    import django
    from django.conf import settings
    settings.configure(USE_TZ=False)
    django.setup()

    from django.db.backends.base.operations import BaseDatabaseOperations
    from django.db.models import DateField, DateTimeField, Value
    from django.db.models.functions import ExtractIsoYear, ExtractYear
    from django.db.models.lookups import YearLookup

    ops = BaseDatabaseOperations(connection=None)
    conn = types.SimpleNamespace(ops=ops)

    # Real lhs instances for the dispatch oracle: the extraction kind and the
    # column field kind are the two runtime facts the model's booleans map to.
    def make_lhs(is_datetime_field, week_numbering):
        field = DateTimeField() if is_datetime_field else DateField()
        extract_cls = ExtractIsoYear if week_numbering else ExtractYear
        return extract_cls(Value(None, output_field=field))

    lhs_of = {(dt, wk): make_lhs(dt, wk)
              for dt in (False, True) for wk in (False, True)}

    checked = [0]

    def fail(label, args, shadow, real):
        print("DISAGREEMENT (%s)\n  input=%r\n  shadow=%r\n  real=%r"
              % (label, args, shadow, real))
        return 1

    def check_date_field(year, wk):
        shadow = date_field_year_range(year, wk)
        real = ops.year_lookup_bounds_for_date_field(year, iso_year=wk)
        real_b = [day_ordinal(v) for v in real]
        checked[0] += 1
        if shadow != real_b:
            return fail("date field", (year, wk), shadow, real_b)
        return 0

    def check_datetime_field(year, wk):
        shadow = datetime_field_year_range(year, wk)
        real = ops.year_lookup_bounds_for_datetime_field(year, iso_year=wk)
        real_b = [usec_instant(v) for v in real]
        checked[0] += 1
        if shadow != real_b:
            return fail("datetime field", (year, wk), shadow, real_b)
        return 0

    def check_dispatch(is_dt, wk, year):
        shadow = year_lookup_range(is_dt, wk, year)
        self_ns = types.SimpleNamespace(lhs=lhs_of[(is_dt, wk)])
        real = YearLookup.year_lookup_bounds(self_ns, conn, year)
        bridge = usec_instant if is_dt else day_ordinal
        real_b = [bridge(v) for v in real]
        checked[0] += 1
        if shadow != real_b:
            return fail("dispatch", (is_dt, wk, year), shadow, real_b)
        return 0

    # Exhaustive sweep of the whole operating domain (subsumes every boundary:
    # first/last valid years, leap years, years whose week 1 starts in the
    # prior December, and the years the behaviour tests probe).
    for year in range(YEAR_MIN, YEAR_MAX + 1):
        for wk in (False, True):
            if check_date_field(year, wk):
                return 1
            if check_datetime_field(year, wk):
                return 1
            for is_dt in (False, True):
                if check_dispatch(is_dt, wk, year):
                    return 1

    # Fuzz: random dispatch draws over the same domain, pinned seed.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        year = rng.randint(YEAR_MIN, YEAR_MAX)
        is_dt = rng.random() < 0.5
        wk = rng.random() < 0.5
        if check_dispatch(is_dt, wk, year):
            return 1

    print("G-CONF OK: shadow impl == real endpoint/dispatch functions on %d "
          "inputs (exhaustive %d-year sweep x flags + %d fuzz, seed %d)."
          % (checked[0], YEAR_MAX - YEAR_MIN + 1, N_FUZZ, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
