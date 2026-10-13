#!/usr/bin/env python3
r"""G-AX executable soundness check for django__django-13363.

Validates the ONE kind-A obligation of this bundle: the deep-model reference
`resolveZoneName` (Solution.lean pure region) == the REAL unchanged callee
`django.db.models.functions.datetime.TimezoneMixin.get_tzname`.

`get_tzname` is the method the gold patch newly delegates to (it is NOT itself
changed by the patch — the bug was that `TruncDate.as_sql` / `TruncTime.as_sql`
ignored it). Its behaviour is:

    tzname = None
    if settings.USE_TZ:
        if self.tzinfo is None:
            tzname = timezone.get_current_timezone_name()   # ambient zone name
        else:
            tzname = timezone._get_timezone_name(self.tzinfo)  # explicit zone name
    return tzname

i.e. exactly the deep model

    resolveZoneName(tz_aware, explicit_zone, current_zone) =
        None                           if not tz_aware
        current_zone                   if tz_aware and explicit_zone is None
        explicit_zone                  if tz_aware and explicit_zone is not None

where `current_zone = get_current_timezone_name()` (the ambient zone's rendered
name) and `explicit_zone = _get_timezone_name(self.tzinfo)` (the supplied zone's
rendered name) or None when no `tzinfo` was supplied.

We exercise the REAL `get_tzname` over the cross product of {USE_TZ on/off} ×
{explicit zone present/absent} × many ambient/explicit zone pairs (boundary +
fuzz) and assert it equals the model on every observation.

Imports only `django.*` (the repo's own modules, in-container) + `pytz`. Exit 0
iff every obligation holds.
"""
import random
import sys

SEED = 13363
N_FUZZ = 20_000


def model_resolve(tz_aware, explicit_zone, current_zone):
    """resolveZoneName, the Solution.lean deep model (pure region)."""
    if tz_aware:
        if explicit_zone is None:
            return current_zone
        return explicit_zone
    return None


def _bootstrap_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
            TIME_ZONE="UTC",
        )
    import django
    django.setup()


def main():
    _bootstrap_django()
    from django.conf import settings
    from django.db.models.functions.datetime import TimezoneMixin
    from django.utils import timezone
    import pytz

    zone_keys = ['UTC', 'America/New_York', 'Europe/Paris', 'Asia/Bangkok',
                 'Australia/Sydney', 'Africa/Nairobi', 'America/Sao_Paulo',
                 'Pacific/Auckland', 'Etc/GMT+5', 'Asia/Kolkata']

    # The REAL callee, bound directly off the unchanged mixin.
    get_tzname = TimezoneMixin.get_tzname

    def observe(tz_aware, explicit_key, current_key):
        """Run the REAL get_tzname; return (real, model_expected)."""
        settings.USE_TZ = tz_aware
        timezone.activate(pytz.timezone(current_key))
        holder = TimezoneMixin()
        holder.tzinfo = pytz.timezone(explicit_key) if explicit_key else None
        real = get_tzname(holder)
        # the deep model's inputs, computed from the SAME real name renderers:
        current_zone = timezone.get_current_timezone_name()
        explicit_zone = (timezone._get_timezone_name(holder.tzinfo)
                         if holder.tzinfo is not None else None)
        expected = model_resolve(tz_aware, explicit_zone, current_zone)
        timezone.deactivate()
        return real, expected

    checks = 0

    def assert_match(tz_aware, explicit_key, current_key):
        nonlocal checks
        real, expected = observe(tz_aware, explicit_key, current_key)
        assert real == expected, (
            "resolveZoneName deep model unsound for "
            "USE_TZ=%r explicit=%r current=%r: real get_tzname=%r model=%r"
            % (tz_aware, explicit_key, current_key, real, expected))
        checks += 1

    # --- boundary cases ------------------------------------------------------
    for cur in zone_keys:
        # USE_TZ off: always None, regardless of explicit zone.
        assert_match(False, None, cur)
        assert_match(False, 'America/New_York', cur)
        # USE_TZ on, no explicit zone: ambient zone name.
        assert_match(True, None, cur)
        # USE_TZ on, explicit zone present: the explicit name (the fix).
        for exp in zone_keys:
            assert_match(True, exp, cur)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        tz_aware = rng.random() < 0.7
        cur = rng.choice(zone_keys)
        explicit_key = None if rng.random() < 0.45 else rng.choice(zone_keys)
        assert_match(tz_aware, explicit_key, cur)

    print("G-AX OK: resolveZoneName deep model (== real TimezoneMixin.get_tzname) "
          "sound on %d observations (boundary + %d fuzz, seed=%d)."
          % (checks, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
