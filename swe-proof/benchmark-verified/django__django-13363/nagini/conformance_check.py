#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13363 (nagini).

SHADOW: the impl regions of model.py `date_cast_tzname` / `time_cast_tzname`,
copied verbatim below with the contract calls stripped (the impl regions
themselves contain no contract calls; Requires/Ensures live in separate
regions). The @Pure helper `selected_tzname` copies over as a plain function
and is used as an internal cross-check of the shadow. All model carriers are
plain bools / Optional lists of ints, so no PSeq shim is needed. There are no
@ContractOnly callees in this bundle (the axioms region is empty).

ORACLE: the REAL patched repo functions the model models per mapping.md §1 —
`TruncDate.as_sql` and `TruncTime.as_sql`
(`django/db/models/functions/datetime.py`). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched module
importable. This script never applies any diff itself.

Observable: each as_sql computes a local time-zone name and passes it to an
UNCHANGED, deterministic backend cast-SQL routine
(`connection.ops.datetime_cast_date_sql` / `datetime_cast_time_sql`) together
with an lhs fragment that does not depend on the selection (mapping.md §3.2:
the emitted SQL differs iff that name differs). The check therefore drives the
real as_sql with a stub compiler (fixed lhs text) and a stub connection whose
ops record the name argument they receive — capturing exactly the modeled
quantity, the selected tzname.

Type bridge (mapping.md §2, identical to the one axiom_check.py validates):
  * a time-zone name `str` <-> `List[int]` of code points (None <-> None);
  * a supplied `tzinfo` object <-> its name, `tz.tzname(None)` (the
    name-of-a-time-zone lookup is the identity under the name abstraction);
  * `settings.USE_TZ` <-> `use_tz` (bool identity);
  * the ambient zone's name (a deterministic 0-ary read of process state) is
    read from the real repo's `timezone.get_current_timezone_name()` after
    activating a chosen zone, and fed to the shadow as `current_name`.

Input domain: the Requires are pure access permissions, so every
(use_tz, supplied-zone-or-None, ambient-zone) triple is Requires-satisfying.

>= 1e5 Requires-satisfying inputs: a boundary matrix (both use_tz values x
{no supplied zone + every zone} x every ambient zone, including
supplied == ambient and fixed-offset zones) plus 100000 fuzz triples.
Pinned fuzz seed: 13363. Each input exercises BOTH real functions (date and
time sites), so the number of shadow-vs-real comparisons is 2x the input
count.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random) plus pytz, the repo's own required
dependency in this image.
"""
import datetime as _dt
import json
import random
import sys

SEED = 13363
N_FUZZ = 100_000


# --- pure helper from model.py, contracts stripped ---------------------------

def selected_tzname(use_tz, tzinfo, current_name):
    if not use_tz:
        return None
    if tzinfo is not None:
        return tzinfo
    return current_name


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def date_cast_tzname(use_tz, tzinfo, current_name):
    tzname = None  # type: Optional[List[int]]
    if use_tz:
        if tzinfo is None:
            tzname = current_name
        else:
            tzname = tzinfo
    return tzname


def time_cast_tzname(use_tz, tzinfo, current_name):
    tzname = None  # type: Optional[List[int]]
    if use_tz:
        if tzinfo is None:
            tzname = current_name
        else:
            tzname = tzinfo
    return tzname


# --- oracle plumbing: drive the REAL patched as_sql methods ------------------

class _RecordingOps:
    """Stands in for the unchanged backend ops: records the time-zone name
    each cast routine receives (the modeled observable) and returns a dummy
    SQL string."""

    def __init__(self):
        self.date_tzname = "UNSET"
        self.time_tzname = "UNSET"

    def datetime_cast_date_sql(self, sql, tzname):
        self.date_tzname = tzname
        return "CAST_DATE"

    def datetime_cast_time_sql(self, sql, tzname):
        self.time_tzname = tzname
        return "CAST_TIME"


class _StubConnection:
    def __init__(self):
        self.ops = _RecordingOps()


class _StubCompiler:
    """Fixed lhs fragment: the lhs compilation does not depend on the
    time-zone selection (mapping.md §3.2), so a constant text isolates the
    modeled quantity."""

    def compile(self, node):
        return "LHS", []


def _to_pts(name):
    return None if name is None else [ord(ch) for ch in name]


def make_oracle():
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_TZ=True, TIME_ZONE='UTC',
                           INSTALLED_APPS=[], DATABASES={})
    import django
    django.setup()
    from django.db.models.functions.datetime import TruncDate, TruncTime
    from django.utils import timezone as dj_tz

    compiler = _StubCompiler()

    def oracle(use_tz, supplied_tz, ambient_tz):
        """Run BOTH real patched as_sql methods under the given process
        state; return (date_tzname, time_tzname, current_name) — the names
        the two cast routines received plus the ambient name read back from
        the repo (the shadow's current_name input)."""
        settings.USE_TZ = use_tz
        dj_tz.activate(ambient_tz)
        try:
            current_name = dj_tz.get_current_timezone_name()
            conn = _StubConnection()
            d = TruncDate('f', tzinfo=supplied_tz)
            sql, params = d.as_sql(compiler, conn)
            assert sql == "CAST_DATE" and params == [], (sql, params)
            t = TruncTime('f', tzinfo=supplied_tz)
            sql, params = t.as_sql(compiler, conn)
            assert sql == "CAST_TIME" and params == [], (sql, params)
            return conn.ops.date_tzname, conn.ops.time_tzname, current_name
        finally:
            dj_tz.deactivate()

    return oracle


# --- differential driver ------------------------------------------------------

def check_one(oracle, use_tz, supplied_tz, ambient_tz):
    """Diff shadow vs real on one (use_tz, supplied zone, ambient zone)
    configuration; return an error string on disagreement, else None."""
    real_date, real_time, current_name = oracle(use_tz, supplied_tz, ambient_tz)

    # Bridge: supplied zone -> its name (tzname(None), the identity under the
    # name abstraction); names -> code-point lists.
    supplied_name = None if supplied_tz is None else supplied_tz.tzname(None)
    tzinfo_pts = _to_pts(supplied_name)
    current_pts = _to_pts(current_name)

    shadow_date = date_cast_tzname(use_tz, tzinfo_pts, current_pts)
    shadow_time = time_cast_tzname(use_tz, tzinfo_pts, current_pts)
    # internal cross-check: both impls agree with the pure deep model
    assert shadow_date == selected_tzname(use_tz, tzinfo_pts, current_pts)
    assert shadow_time == selected_tzname(use_tz, tzinfo_pts, current_pts)

    real_date_pts = _to_pts(real_date)
    real_time_pts = _to_pts(real_time)

    if shadow_date != real_date_pts or shadow_time != real_time_pts:
        return ("DISAGREEMENT\n"
                "  use_tz=%r supplied=%r ambient=%r (current_name=%r)\n"
                "  shadow_date=%r real_date=%r\n"
                "  shadow_time=%r real_time=%r"
                % (use_tz, supplied_name, ambient_tz, current_name,
                   shadow_date, real_date, shadow_time, real_time))
    return None


def main():
    import pytz

    oracle = make_oracle()

    zone_names = [
        'UTC', 'America/New_York', 'Australia/Melbourne', 'Pacific/Auckland',
        'America/Sao_Paulo', 'Europe/London', 'Asia/Kolkata', 'Etc/GMT+5',
    ]
    named_zones = [pytz.timezone(zn) for zn in zone_names]
    fixed_zones = [
        _dt.timezone.utc,
        _dt.timezone(_dt.timedelta(hours=5, minutes=30)),
        _dt.timezone(_dt.timedelta(hours=-9), 'FIX-9'),
    ]
    supplied_pool = named_zones + fixed_zones
    ambient_pool = named_zones  # ambient zones come from activate(name-zone)

    checked = 0
    n_boundary = 0

    # --- boundary matrix: both use_tz values x (None + every supplied zone)
    #     x every ambient zone (includes supplied == ambient) ---------------
    for use_tz in (True, False):
        for supplied in [None] + supplied_pool:
            for ambient in ambient_pool:
                err = check_one(oracle, use_tz, supplied, ambient)
                if err:
                    print(err)
                    return 1
                checked += 1
                n_boundary += 1

    # --- randomized fuzz (pinned seed) --------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        use_tz = rng.random() < 0.7
        if rng.random() < 0.3:
            supplied = None
        else:
            supplied = rng.choice(supplied_pool)
        ambient = rng.choice(ambient_pool)
        err = check_one(oracle, use_tz, supplied, ambient)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impls (contract-stripped date/time cast "
          "tzname selection) == real patched as_sql selections on %d inputs "
          "(%d boundary + %d fuzz, seed %d; 2 real call sites per input)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
