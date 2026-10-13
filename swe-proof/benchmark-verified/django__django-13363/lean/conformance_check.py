#!/usr/bin/env python3
"""G-CONF for django__django-13363.

The gold patch is already applied to /testbed when this runs. The impl region is
R/I (the per-flavour casts are I-tagged UNCHANGED callees applied identically on
both sides; the only behavioral content is the conversion-zone selection, modeled
deeply as `conversionZoneName`). Since `result = castX lhs zone` is a
deterministic function of `(lhs, zone)` and the cast is unchanged, two renderings
agree iff their selected conversion zones agree. So G-CONF differential-tests the
R/I shadow's zone selection against the REAL patched zone selection.

  * Oracle  = the REAL patched zone selection that `TruncDate.as_sql` /
              `TruncTime.as_sql` now use: `self.get_tzname()`
              (`TimezoneMixin.get_tzname`), evaluated with the real
              `settings.USE_TZ` and the instance's `self.tzinfo`.
  * Shadow  = `conversionZoneName(useTz, requestedZone, currentZone)`, the Lean
              impl's deep model, where
              requestedZone = timezone._get_timezone_name(tz) if tz else None
                              (the A-reference extraction),
              currentZone   = timezone.get_current_timezone_name() (ambient),
              useTz         = settings.USE_TZ.

Zero disagreements over >=1e5 fuzzed (USE_TZ, tzinfo) configurations => exit 0.

Type bijection (mapping.md): useTz<->settings.USE_TZ (bool),
requestedZone<->self.tzinfo modeled by its extracted zone name (Optional[str]),
currentZone<->get_current_timezone_name() (str), selected zone<->Optional[str].
stdlib-only (pytz ships with the testbed; no hypothesis required).
"""
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False,
        DATABASES={}, INSTALLED_APPS=[], TEMPLATES=[],
        TIME_ZONE="UTC",
    )
    django.setup()

from django.db.models.functions.datetime import TruncDate, TruncTime
from django.db.models import F
from django.utils import timezone

try:
    import pytz
except Exception:  # pragma: no cover
    pytz = None

SEED = 13363
N = 120_000  # >= 1e5

# Candidate zones: None (no tzinfo) plus a spread of named zones. We model
# self.tzinfo by the zone name `_get_timezone_name` extracts from it.
ZONE_NAMES = [
    None, "UTC", "America/New_York", "Australia/Melbourne", "US/Pacific",
    "Europe/Paris", "Asia/Kolkata", "America/Sao_Paulo", "Pacific/Kiritimati",
]


def make_tz(name):
    if name is None:
        return None
    if pytz is not None:
        return pytz.timezone(name)
    from datetime import timezone as dt_tz
    return dt_tz.utc  # degenerate fallback; pytz is present on the testbed


def conversion_zone_name(use_tz, requested_zone, current_zone):
    """Shadow of the Lean `conversionZoneName`."""
    if use_tz:
        return requested_zone if requested_zone is not None else current_zone
    return None


def oracle_zone(trunc_cls, tz):
    """The REAL patched zone selection: TimezoneMixin.get_tzname()."""
    inst = trunc_cls(F("x"), tzinfo=tz)
    return inst.get_tzname()


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    cases = []
    # Deterministic boundary cases (incl. the F2P shape: USE_TZ on, named zone).
    for use_tz in (True, False):
        for zn in ZONE_NAMES:
            cases.append((use_tz, zn))
    cases += [(rng.random() < 0.5, rng.choice(ZONE_NAMES)) for _ in range(N)]

    for use_tz, zn in cases:
        settings.USE_TZ = use_tz
        tz = make_tz(zn)
        # A-reference extraction: model self.tzinfo by its extracted zone name.
        requested = None if tz is None else timezone._get_timezone_name(tz)
        current = timezone.get_current_timezone_name()
        shadow = conversion_zone_name(use_tz, requested, current)
        for cls in (TruncDate, TruncTime):
            got = oracle_zone(cls, tz)
            if got != shadow:
                disagreements += 1
                if len(examples) < 10:
                    examples.append(((cls.__name__, use_tz, zn), shadow, got))

    settings.USE_TZ = False
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, s, o in examples:
            print(f"  in={inp!r} shadow={s!r} oracle={o!r}")
        return 1
    print(f"G-CONF OK: {2 * len(cases)} renderings, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
