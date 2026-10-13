#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11138 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the impl region itself contains no contract calls; the
Requires/Ensures live in separate regions). The @Pure helper
`normalised_walltime` copies over as a plain function. All model carriers are
plain ints/bools, so no PSeq shim is needed. There are no @ContractOnly
callees in this bundle.

ORACLE: the REAL repo function the model models per mapping.md section 1 —
`django.db.backends.sqlite3.base._sqlite_datetime_parse` (the in-process
read-side callback the FAIL_TO_PASS test drives on the SQLite engine). The
gate applies the diff to /testbed before this script runs; PYTHONPATH=
/testbed makes the patched module importable. This script never applies any
diff itself.

Type bridge (mapping.md section 2, identical to the one axiom_check.py
validates):
  * a stored naive datetime <-> integer wall-clock minutes since a fixed
    epoch (`stored`); the callee receives it as the DB's string form and the
    observable compared is the wall-clock minute value of the returned
    datetime (the quantity the date/time/extract lookups read);
  * a named zone <-> its integer UTC offset in minutes, extracted from the
    ACTUAL live datetime objects (the offset a tzinfo relabel attaches for
    the source zone — the pytz base/LMT subtlety honoured, not idealised —
    and the offset an astimezone conversion yields for the target zone);
  * `has_target` <-> a target-zone name is passed (not None);
  * `use_tz` <-> settings.USE_TZ; per mapping.md, with tz support active a
    connection-zone name is always supplied (never empty), and with it off
    both zone arguments are None — so the Requires
    (use_tz or not has_target) holds over the whole generated domain.

Inputs stay inside the model's successful-parse domain (well-formed datetime
strings), matching the model docstring. Sub-minute components are preserved
by the whole-minute zone offsets, so flooring both sides to minutes is an
exact comparison at the model's granularity.

>= 1e5 Requires-satisfying inputs: a structured boundary matrix (the F2P
instants, equal-zone identity, day-boundary crossings, tz support off, no
target requested) plus 100000 fuzz configurations over real zone names and a
12-year instant range. Pinned fuzz seed: 111380.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; hypothesis not needed) plus pytz,
which is the repo's own required dependency in this image.
"""
import datetime as _dt
import json
import random
import sys

SEED = 111380
N_FUZZ = 100_000

EPOCH = _dt.datetime(2000, 1, 1)


# --- pure helper from model.py, contracts stripped -----------------------

def normalised_walltime(stored, conn_off, target_off, has_target, use_tz):
    if not use_tz:
        return stored
    if not has_target:
        return stored
    return stored - conn_off + target_off


# --- the impl region of model.py, verbatim ---------------------------------

def local_walltime(stored, conn_off, target_off, has_target, use_tz):
    result = stored  # type: int
    if use_tz:
        # Reinterpret the stored wall clock in the connection time zone:
        # relabelling the zone moves the underlying instant by -conn_off.
        result = result - conn_off
        if has_target and target_off != conn_off:
            # Re-express that instant in the target zone: +target_off.
            result = result + target_off
        elif has_target:
            # Connection zone == target zone: no conversion. Restore the
            # untouched stored wall clock (relabel was a no-op observationally).
            result = result + conn_off
        else:
            # No target zone requested: leave the stored wall clock untouched.
            result = result + conn_off
    return result
    # (impl region ends)


# --- bridge helpers ---------------------------------------------------------

def _to_minutes(naive):
    return int((naive - EPOCH).total_seconds() // 60)


def _off_minutes(aware):
    return int(aware.utcoffset().total_seconds() // 60)


def bridge_offsets(pytz, base_naive, conn_name, target_name):
    """Extract the model's integer offsets from the ACTUAL live datetime
    operations (relabel to the connection zone; convert to the target zone),
    mirroring the abstraction axiom_check.py validates."""
    conn_off = 0
    target_off = 0
    if conn_name:
        relabelled = base_naive.replace(tzinfo=pytz.timezone(conn_name))
        conn_off = _off_minutes(relabelled)
        if target_name is not None and target_name != conn_name:
            converted = relabelled.astimezone(pytz.timezone(target_name))
            target_off = _off_minutes(converted)
        elif target_name is not None:
            # coinciding zone names: no conversion happens; offsets coincide.
            target_off = conn_off
    return conn_off, target_off


def check_one(parse_fn, pytz, settings, base_naive, conn_name, target_name,
              use_tz, with_micro=False):
    """Run the REAL patched callee on the string form of one stored instant
    and diff its returned wall-clock minutes against the shadow."""
    settings.USE_TZ = use_tz
    fmt = "%Y-%m-%d %H:%M:%S.%f" if with_micro else "%Y-%m-%d %H:%M:%S"
    stored_str = base_naive.strftime(fmt)
    real_dt = parse_fn(stored_str, target_name, conn_name)
    if real_dt is None:
        return ("DISAGREEMENT (unexpected None from a well-formed input)\n"
                "  stored=%r conn=%r target=%r use_tz=%r"
                % (stored_str, conn_name, target_name, use_tz))
    real_wall = _to_minutes(real_dt.replace(tzinfo=None))

    stored_min = _to_minutes(base_naive)
    conn_off, target_off = bridge_offsets(pytz, base_naive, conn_name,
                                          target_name)
    has_target = target_name is not None
    # precondition holds by domain construction:
    assert use_tz or not has_target
    shadow_wall = local_walltime(stored_min, conn_off, target_off,
                                 has_target, use_tz)
    pure_wall = normalised_walltime(stored_min, conn_off, target_off,
                                    has_target, use_tz)
    if real_wall != shadow_wall or real_wall != pure_wall:
        return ("DISAGREEMENT\n"
                "  stored=%r conn=%r target=%r use_tz=%r\n"
                "  bridge: stored_min=%d conn_off=%d target_off=%d "
                "has_target=%r\n"
                "  shadow=%d pure=%d real=%d (real dt=%r)"
                % (stored_str, conn_name, target_name, use_tz,
                   stored_min, conn_off, target_off, has_target,
                   shadow_wall, pure_wall, real_wall, real_dt))
    return None


def main():
    # Configure minimal settings BEFORE importing the backend modules; the
    # callee reads settings.USE_TZ through its parsing helper on every call.
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_TZ=True)
    import pytz
    # REAL patched repo function (the modeled callee, mapping.md section 1):
    from django.db.backends.sqlite3.base import _sqlite_datetime_parse

    zones = ["UTC", "Africa/Nairobi", "Asia/Bangkok", "America/Lima",
             "Africa/Lagos", "Asia/Kolkata", "Europe/Paris",
             "Australia/Sydney", "Asia/Kathmandu", "America/St_Johns"]

    checked = 0
    n_boundary = 0

    # --- boundary matrix -------------------------------------------------
    base_times = [
        _dt.datetime(2016, 1, 2, 3, 10, 11),    # F2P instant shape
        _dt.datetime(2016, 1, 2, 20, 10, 11),   # equal-zone F2P shape
        _dt.datetime(2016, 1, 1, 0, 0, 0),      # midnight
        _dt.datetime(2016, 1, 1, 23, 59, 59),   # day-boundary crossing
        _dt.datetime(2016, 6, 15, 12, 0, 0),
        _dt.datetime(2020, 12, 31, 21, 30, 0),
    ]
    for bt in base_times:
        for cz in zones:
            for tz in zones:
                errs = [check_one(_sqlite_datetime_parse, pytz, settings,
                                  bt, cz, tz, True),
                        check_one(_sqlite_datetime_parse, pytz, settings,
                                  bt, cz, tz, True, with_micro=True)]
                for err in errs:
                    if err:
                        print(err)
                        return 1
                checked += 2
                n_boundary += 2
            # tz support active, no target zone requested
            err = check_one(_sqlite_datetime_parse, pytz, settings,
                            bt, cz, None, True)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1
        # tz support off: both zone arguments absent
        err = check_one(_sqlite_datetime_parse, pytz, settings,
                        bt, None, None, False)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    # --- randomized fuzz (pinned seed) ------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        bt = EPOCH + _dt.timedelta(
            minutes=rng.randint(0, 12 * 365 * 24 * 60),
            seconds=rng.randint(0, 59))
        use_tz = rng.random() < 0.85
        if use_tz:
            cz = rng.choice(zones)
            tz = rng.choice(zones) if rng.random() < 0.85 else None
        else:
            cz = None
            tz = None
        err = check_one(_sqlite_datetime_parse, pytz, settings, bt, cz, tz,
                        use_tz, with_micro=rng.random() < 0.2)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (contract-stripped local_walltime) == real "
          "patched read-side normalisation callee on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
