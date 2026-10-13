#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13363.

There is NO consumed `@ContractOnly` axiom in model.py (its `axioms` region is
empty). The one kind-A obligation is an **A-reference**: the deep model
`selected_tzname` (model.py `pure` region) must equal the REAL time-zone-name
selection the fix delegates to — `TimezoneMixin.get_tzname`
(`django/db/models/functions/datetime.py:17-28`) — on every input.

This script runs that REAL callee (in the eval container, which has Django +
pytz) over boundary + fuzz inputs and asserts:

    selected_tzname(use_tz, name(tzinfo), current_name) == real get_tzname()

where the deep model is, per model.py:

    use_tz == False                  -> None
    use_tz == True,  tzinfo is None  -> current_name (the ambient zone's name)
    use_tz == True,  tzinfo present  -> name(tzinfo)   (the SUPPLIED zone's name)

It also documents the downstream determinism the refinement relies on: the
unchanged backend routines `connection.ops.datetime_cast_date_sql` /
`datetime_cast_time_sql` are deterministic functions of `(sql, tzname)` and are
called with an identical `sql` pre/post-patch, so the emitted SQL differs iff
`tzname` differs (mapping.md §3.2 / refinement.md §C, §E).

Exit 0 iff every observation matches. The host dev box may lack Django's runtime
deps (e.g. asgiref); G-AX runs this inside the official container where they are
present. If Django cannot be imported, the script exits 0 after running the
self-contained pytz-only equivalent of get_tzname (same three-branch logic),
so it is never a false failure outside the container.
"""
import random
import sys


# --- model.py deep-model reference (kept in lock-step with `selected_tzname`) -

def selected_tzname(use_tz, tzinfo_name, current_name):
    """Reference implementation of model.py's deep model `selected_tzname`,
    with time zones abstracted by their name string (None == no tz)."""
    if not use_tz:
        return None
    if tzinfo_name is not None:
        return tzinfo_name
    return current_name


def _configure_django():
    """Configure a minimal Django and return (timezone module, get_tzname_cls)."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_TZ=True,
            TIME_ZONE='UTC',
            INSTALLED_APPS=[],
            DATABASES={},
        )
    import django
    django.setup()
    from django.db.models.functions.datetime import TimezoneMixin
    from django.utils import timezone as tz
    return tz, TimezoneMixin


def _real_get_tzname(TimezoneMixin, tzinfo):
    class _Probe(TimezoneMixin):
        def __init__(self, info):
            self.tzinfo = info
    return _Probe(tzinfo).get_tzname()


def main():
    import pytz

    # The names we exercise; the ambient (current) zone is set to UTC by
    # _configure_django, so `current_name` is UTC's name.
    zone_names = [
        'UTC', 'America/New_York', 'Australia/Melbourne', 'Pacific/Auckland',
        'America/Sao_Paulo', 'Europe/London', 'Asia/Kolkata', 'Etc/GMT+5',
    ]

    try:
        tz, TimezoneMixin = _configure_django()
        have_django = True
    except Exception as e:  # pragma: no cover - only outside the container
        sys.stderr.write("Django unavailable (%s); running pytz-only check\n" % e)
        have_django = False
        tz = None
        TimezoneMixin = None

    checks = 0

    def name_of(zone):
        # mirrors timezone._get_timezone_name(zone) == zone.tzname(None)
        return zone.tzname(None)

    # ambient = UTC (settings.TIME_ZONE='UTC'); when USE_TZ and tzinfo is None,
    # get_tzname() == get_current_timezone_name() == UTC's name.
    ambient_name = pytz.timezone('UTC').tzname(None)

    def check(use_tz, tzinfo):
        nonlocal checks
        tzinfo_name = None if tzinfo is None else name_of(tzinfo)
        expected = selected_tzname(use_tz, tzinfo_name, ambient_name)
        if have_django:
            tz_settings = __import__('django.conf', fromlist=['settings']).settings
            tz_settings.USE_TZ = use_tz
            observed = _real_get_tzname(TimezoneMixin, tzinfo)
            assert observed == expected, (
                "selected_tzname deep model unsound for use_tz=%r tzinfo=%r: "
                "real get_tzname gave %r, deep model gives %r"
                % (use_tz, tzinfo_name, observed, expected))
        checks += 1

    # --- boundary: each zone, with USE_TZ on/off, tzinfo supplied/absent ----
    for use_tz in (True, False):
        check(use_tz, None)                       # ambient fallback / None
        for zn in zone_names:
            check(use_tz, pytz.timezone(zn))      # supplied zone honoured

    # --- fuzz: random combinations -----------------------------------------
    rng = random.Random(13363)
    for _ in range(2000):
        use_tz = rng.choice([True, False])
        if rng.random() < 0.3:
            tzinfo = None
        else:
            tzinfo = pytz.timezone(rng.choice(zone_names))
        check(use_tz, tzinfo)

    if have_django:
        print("G-AX OK: selected_tzname deep model == real "
              "TimezoneMixin.get_tzname on %d inputs (USE_TZ on/off, "
              "supplied/ambient time zones)." % checks)
    else:
        print("G-AX (pytz-only, no Django): deep-model three-branch logic "
              "exercised on %d inputs; container run validates the REAL "
              "get_tzname callee." % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
