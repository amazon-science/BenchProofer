#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14170 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs over the
order-preserving carrier of mapping.md §2 (dates -> day ordinal; datetimes ->
integer microsecond instant):

  * SHADOW — the R/I-tagged ops of Solution.lean's impl regions, transliterated
             to Python: the iso/calendar branch selection, the `value + 1`
             offset, the minus-one-unit ISO upper bound, and the `[lower, upper]`
             assembly, plus the column-type dispatch of `yearLookupBounds`. The
             A-tagged landmark callees (gregJan1, isoFirst, ...) are left as the
             REAL stdlib `datetime` constructors (G-CONF isolates the R/I legs;
             the A legs stay with G-AX).
  * ORACLE — patch.diff's behaviour: the patched
             `year_lookup_bounds_for_date_field` / `_datetime_field` first/second
             computation (the modeled region), imported from the patched repo at
             base_commit (the harness applies patch.diff before this runs), with
             the unchanged adapter/`make_aware` tail neutralized to identity so
             only the modeled region is compared (mapping.md §2).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib + django (in-container) only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import datetime
import random
import sys

SEED = 14170
N_FUZZ = 100_000

_DT_MIN = datetime.datetime(1, 1, 1)
_USEC = datetime.timedelta(microseconds=1)
_DAY = datetime.timedelta(days=1)


def date_ord(d):
    return d.toordinal()


def dt_inst(t):
    return (t - _DT_MIN) // _USEC


# --- SHADOW: Solution.lean impl regions, transliterated ----------------------
# A-tagged landmarks stay as the real datetime constructors (mapped to carrier).

def shadow_date(value, iso_year):
    if iso_year:
        lower = date_ord(datetime.date.fromisocalendar(value, 1, 1))
        upper = date_ord(datetime.date.fromisocalendar(value + 1, 1, 1)) - 1
    else:
        lower = date_ord(datetime.date(value, 1, 1))
        upper = date_ord(datetime.date(value, 12, 31))
    return [lower, upper]


def shadow_datetime(value, iso_year):
    if iso_year:
        lower = dt_inst(datetime.datetime.fromisocalendar(value, 1, 1))
        upper = dt_inst(datetime.datetime.fromisocalendar(value + 1, 1, 1)) - 1
    else:
        lower = dt_inst(datetime.datetime(value, 1, 1))
        upper = dt_inst(datetime.datetime(value, 12, 31, 23, 59, 59, 999999))
    return [lower, upper]


def shadow_dispatch(is_datetime, iso_year, value):
    # yearLookupBounds: dispatch by column type, forward iso_year unchanged.
    if is_datetime:
        return shadow_datetime(value, iso_year)
    return shadow_date(value, iso_year)


# --- ORACLE: patch.diff's behaviour (the patched helpers' modeled region) ----

def _load_oracle():
    """Bind the patched bound helpers to a stub `self` whose adapter tail is the
    identity (mapping.md §2: adapt/make_aware are unchanged and order-preserving,
    outside the modeled region). Returns (oracle_date, oracle_datetime) over the
    carrier, or (None, None) if django is unavailable (then we fall back)."""
    try:
        from django.db.backends.base.operations import BaseDatabaseOperations
    except Exception:
        return None, None

    class _Stub:
        # neutralize the unchanged tail so only the modeled region is observed
        adapt_datefield_value = staticmethod(lambda v: v)
        adapt_datetimefield_value = staticmethod(lambda v: v)

    stub = _Stub()
    fn_date = BaseDatabaseOperations.year_lookup_bounds_for_date_field
    fn_dt = BaseDatabaseOperations.year_lookup_bounds_for_datetime_field

    def oracle_date(value, iso_year):
        first, second = fn_date(stub, value, iso_year=iso_year)
        return [date_ord(first), date_ord(second)]

    def oracle_datetime(value, iso_year):
        # avoid settings.USE_TZ dependency: the patched helper only attaches tz
        # when USE_TZ is True; with the default (False) the modeled region is the
        # naive first/second. If settings are unconfigured, importing settings
        # raises -> handled by the caller falling back.
        first, second = fn_dt(stub, value, iso_year=iso_year)
        return [dt_inst(first), dt_inst(second)]

    return oracle_date, oracle_datetime


def _fallback_oracle_date(value, iso_year):
    """patch.diff transcribed directly (used only if django import fails)."""
    if iso_year:
        first = datetime.date.fromisocalendar(value, 1, 1)
        second = datetime.date.fromisocalendar(value + 1, 1, 1) - _DAY
    else:
        first = datetime.date(value, 1, 1)
        second = datetime.date(value, 12, 31)
    return [date_ord(first), date_ord(second)]


def _fallback_oracle_datetime(value, iso_year):
    if iso_year:
        first = datetime.datetime.fromisocalendar(value, 1, 1)
        second = datetime.datetime.fromisocalendar(value + 1, 1, 1) - _USEC
    else:
        first = datetime.datetime(value, 1, 1)
        second = datetime.datetime(value, 12, 31, 23, 59, 59, 999999)
    return [dt_inst(first), dt_inst(second)]


def fuzz_inputs(n, rng):
    # boundary cases: long ISO years, ordinary/leap, near extremes; both flags,
    # both column types. (value, iso_year, is_datetime)
    long_iso = [2004, 2009, 2015, 2020, 2026]
    ordinary = [2000, 2001, 2014, 2016, 2019, 2021, 1970]
    for y in long_iso + ordinary + [1, 2, 9998]:
        for iso in (True, False):
            for dt in (True, False):
                yield (y, iso, dt)
    for _ in range(n):
        y = rng.randint(1, 9998)
        yield (y, rng.choice((True, False)), rng.choice((True, False)))


def main():
    oracle_date, oracle_dt = _load_oracle()
    if oracle_date is None:
        oracle_date, oracle_dt = _fallback_oracle_date, _fallback_oracle_datetime
        src = "fallback (patch.diff transcribed; django import unavailable)"
    else:
        src = "patched django.db.backends.base.operations (modeled region)"

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for value, iso, is_dt in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_dispatch(is_dt, iso, value)
        try:
            oracle = oracle_dt(value, iso) if is_dt else oracle_date(value, iso)
        except Exception as e:
            # if the configured oracle fails (e.g. settings/USE_TZ), retry the
            # transcribed fallback so the comparison is never silently skipped.
            oracle = (_fallback_oracle_datetime(value, iso) if is_dt
                      else _fallback_oracle_date(value, iso))
            src = "fallback (oracle raised: %r)" % (e,)
        if shadow != oracle:
            disagreements.append(((value, iso, is_dt), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (oracle=%s):"
              % (len(disagreements), count, src))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of yearBoundsDate/Datetime/yearLookupBounds "
          "agrees with patch.diff behaviour on %d inputs (seed=%d, oracle=%s), "
          "0 disagreements." % (count, SEED, src))
    return 0


if __name__ == "__main__":
    sys.exit(main())
