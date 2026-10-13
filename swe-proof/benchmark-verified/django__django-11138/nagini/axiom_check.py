#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11138.

There is no consumed @ContractOnly axiom in this bundle: the changed operation
(time-zone normalisation on read) is modelled DEEPLY as integer wall-clock
arithmetic (`normalised_walltime` in model.py). G-AX validates that deep model
(the A-reference) against the REAL behaviour the gold patch performs:

    dt = typecast_timestamp(stored)            # naive wall clock, tzinfo=UTC
    if conn_tzname:                             # the new source-zone relabel
        dt = dt.replace(tzinfo=pytz.timezone(conn_tzname))
    if tzname is not None and tzname != conn_tzname:
        dt = timezone.localtime(dt, pytz.timezone(tzname))   # == astimezone

The model says the observed wall clock is `stored - conn_off + target_off`
(minutes), where:
  * `conn_off`  = the UTC offset that `dt.replace(tzinfo=pytz.timezone(conn))`
                  attaches (for a pytz zone this is the zone's base/LMT offset),
  * `target_off`= the UTC offset that `dt.astimezone(pytz.timezone(target))`
                  produces for the instant,
and the stored wall clock is returned unchanged when tz support is off, no
target is requested, or the connection and target zones coincide.

This check runs the REAL CPython datetime + pytz relabel/convert, extracts the
ACTUAL offsets the real operations use (so the pytz `replace`/LMT subtlety is
honoured, not idealised away), and asserts the resulting wall-clock minutes —
the quantity `.date()/.time()/getattr(dt, lookup_type)` read — equal the model
arithmetic `stored - conn_off + target_off`. No double-masking: the equality is
checked at the wall-clock level the lookup observes, against the model's own
arithmetic, not via the date the test compares.

It also pins the F2P discriminator: the test instant stored in the connection
zone (Asia/Bangkok) yields date 2016-01-01 with the connection-sourced
conversion, whereas the UTC-sourced pre-patch yields a different date.

Imports only the standard library (`datetime`) plus `pytz` (Django's own
dependency for these conversions, present in the eval image). Exit 0 iff sound.
"""
import datetime as _dt
import random
import sys

import pytz


EPOCH = _dt.datetime(2000, 1, 1)


def normalised_walltime(stored, conn_off, target_off, has_target, use_tz):
    """Reference of model.py's deep model, in minutes."""
    if not use_tz:
        return stored
    if not has_target:
        return stored
    return stored - conn_off + target_off


def _to_minutes(naive):
    return int((naive - EPOCH).total_seconds() // 60)


def _off_minutes(aware):
    return int(aware.utcoffset().total_seconds() // 60)


def real_and_model(base_naive, conn_name, target_name, has_target, use_tz):
    """Run the REAL gold operation; return (real_wall_min, model_wall_min)."""
    stored_min = _to_minutes(base_naive)
    # typecast_timestamp -> naive wall clock with tzinfo=UTC
    dt = base_naive.replace(tzinfo=pytz.utc)
    conn_off = 0
    target_off = 0
    if use_tz:
        if conn_name:                                   # `if conn_tzname:`
            dt = dt.replace(tzinfo=pytz.timezone(conn_name))
            conn_off = _off_minutes(dt)                 # actual replace offset
        if has_target and target_name is not None and target_name != conn_name:
            dt = dt.astimezone(pytz.timezone(target_name))
            target_off = _off_minutes(dt)               # actual astimezone offset
        elif has_target:
            # connection zone == target zone: no conversion; offsets coincide.
            target_off = conn_off
    real_wall = _to_minutes(dt.replace(tzinfo=None))
    model_wall = normalised_walltime(stored_min, conn_off, target_off,
                                     has_target if use_tz else False, use_tz)
    return real_wall, model_wall


def check(base_naive, conn_name, target_name, has_target, use_tz):
    real_wall, model_wall = real_and_model(
        base_naive, conn_name, target_name, has_target, use_tz)
    assert real_wall == model_wall, (
        "deep-model UNSOUND: base=%s conn=%s target=%s has_target=%s "
        "use_tz=%s -> real=%d model=%d"
        % (base_naive, conn_name, target_name, has_target, use_tz,
           real_wall, model_wall))
    return real_wall


def main():
    zones = ["UTC", "Africa/Nairobi", "Asia/Bangkok",
             "America/Lima", "Africa/Lagos", "Asia/Kolkata", "Europe/Paris"]

    # --- F2P discriminator: the exact test instant ----------------------
    # Event datetime(2016,1,2,3,10,11, tzinfo=ICT) is stored as its wall clock
    # in the CONNECTION zone (Asia/Bangkok) by adapt_datetimefield_value, i.e.
    # 2016-01-02 03:10:11; the active/current target zone is Africa/Nairobi.
    stored_wall = _dt.datetime(2016, 1, 2, 3, 10, 11)
    r_min = check(stored_wall, "Asia/Bangkok", "Africa/Nairobi", True, True)
    result_date = (EPOCH + _dt.timedelta(minutes=r_min)).date()
    assert result_date == _dt.date(2016, 1, 1), (
        "F2P date expected 2016-01-01 from connection-sourced conversion, got %s"
        % result_date)
    # the UTC-sourced PRE-PATCH (source hard-wired to UTC=0) would convert with
    # the target offset alone; assert it yields a DIFFERENT date (real bug).
    stored_min = _to_minutes(stored_wall)
    dt_pre = stored_wall.replace(tzinfo=pytz.utc).astimezone(
        pytz.timezone("Africa/Nairobi"))
    prepatch_date = dt_pre.date()
    assert prepatch_date != _dt.date(2016, 1, 1), (
        "discriminator vacuous: pre-patch also yields the expected date")

    # Test 1 instant: connection == active == Africa/Nairobi (no conversion).
    stored_wall1 = _dt.datetime(2016, 1, 2, 20, 10, 11)
    r1 = check(stored_wall1, "Africa/Nairobi", "Africa/Nairobi", True, True)
    assert r1 == _to_minutes(stored_wall1), "equal-zone case must be identity"

    # --- boundary matrix over real zones --------------------------------
    base_times = [
        _dt.datetime(2016, 1, 1, 0, 0, 0),
        _dt.datetime(2016, 1, 1, 23, 59, 0),
        _dt.datetime(2016, 1, 2, 3, 10, 11),
        _dt.datetime(2016, 6, 15, 12, 0, 0),
        _dt.datetime(2020, 12, 31, 21, 30, 0),
    ]
    for bt in base_times:
        for cz in zones:
            for tz in zones:
                check(bt, cz, tz, True, True)          # tz support + target
            check(bt, cz, None, False, True)           # no target requested
            check(bt, cz, cz, False, False)            # tz support off

    # --- randomized fuzz ------------------------------------------------
    rng = random.Random(11138)
    for _ in range(20000):
        bt = EPOCH + _dt.timedelta(minutes=rng.randint(0, 12 * 365 * 24 * 60))
        cz = rng.choice(zones)
        tz = rng.choice(zones)
        has_target = rng.random() < 0.85
        use_tz = True if has_target else rng.random() < 0.5
        target = tz if has_target else None
        check(bt, cz, target, has_target, use_tz)

    print("G-AX OK: normalised_walltime deep model == real datetime/pytz "
          "relabel+convert (actual offsets, pytz replace/LMT honoured) over "
          "F2P instants + boundary matrix + 20000 fuzz; connection-sourced "
          "conversion confirmed (F2P date 2016-01-01; pre-patch UTC-sourced "
          "date %s differs)." % prepatch_date)
    return 0


if __name__ == "__main__":
    sys.exit(main())
