#!/usr/bin/env python3
"""G-AX for django__django-13363 — validate the A-reference bijection.

The bundle consumes NO callee axiom (`#print axioms correct_*` reports none; the
casts are I-tagged and applied identically on both sides). The one A-reference is
the modeling decision that `self.tzinfo` is faithfully represented by the zone
NAME the UNCHANGED callee `timezone._get_timezone_name(self.tzinfo)` extracts —
i.e. `requestedZone : Option String` carries exactly that name, and the modeled
extraction is the identity on it.

This check runs the REAL callees in-container and asserts:
  (1) for every candidate tzinfo, `_get_timezone_name(tz)` returns a non-empty
      string equal to the zone name we use to model it (`get_tzname` then surfaces
      exactly that string under USE_TZ when tzinfo is supplied);
  (2) `get_current_timezone_name()` returns the ambient zone name (the value our
      model feeds in as `currentZone`), and `get_tzname()` returns it when no
      tzinfo is supplied under USE_TZ;
  (3) under `USE_TZ = False`, `get_tzname()` is `None` regardless of tzinfo
      (the `conversionZoneName` `none` branch).

stdlib-only (pytz ships with the testbed). exit 0 iff sound.
"""
import json
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

ZONE_NAMES = [
    "UTC", "America/New_York", "Australia/Melbourne", "US/Pacific",
    "Europe/Paris", "Asia/Kolkata", "America/Sao_Paulo", "Pacific/Kiritimati",
]


def fail(msg):
    print(json.dumps({"status": "fail", "reason": msg}))
    return 1


def main() -> int:
    if pytz is None:
        return fail("pytz unavailable in container")

    current = timezone.get_current_timezone_name()
    if not isinstance(current, str) or not current:
        return fail(f"get_current_timezone_name() not a non-empty str: {current!r}")

    for cls in (TruncDate, TruncTime):
        # (3) USE_TZ off => no conversion zone, regardless of tzinfo.
        settings.USE_TZ = False
        for zn in (None, "America/New_York"):
            tz = None if zn is None else pytz.timezone(zn)
            if cls(F("x"), tzinfo=tz).get_tzname() is not None:
                settings.USE_TZ = False
                return fail(f"{cls.__name__}: USE_TZ off but get_tzname()!=None ({zn})")

        settings.USE_TZ = True
        # (2) no tzinfo => ambient name.
        if cls(F("x"), tzinfo=None).get_tzname() != current:
            settings.USE_TZ = False
            return fail(f"{cls.__name__}: USE_TZ on, no tzinfo, get_tzname()!=ambient")

        # (1) tzinfo supplied => the extracted zone name, and that is what models it.
        for zn in ZONE_NAMES:
            tz = pytz.timezone(zn)
            extracted = timezone._get_timezone_name(tz)
            if not isinstance(extracted, str) or not extracted:
                settings.USE_TZ = False
                return fail(f"_get_timezone_name({zn}) not a non-empty str: {extracted!r}")
            got = cls(F("x"), tzinfo=tz).get_tzname()
            if got != extracted:
                settings.USE_TZ = False
                return fail(f"{cls.__name__}: get_tzname()={got!r} != extracted {extracted!r} ({zn})")

    settings.USE_TZ = False
    print(json.dumps({
        "status": "ok",
        "reason": "A-reference validated: _get_timezone_name extracts the zone "
                  "name that models self.tzinfo; get_tzname surfaces requested "
                  "zone over ambient under USE_TZ, and None when USE_TZ is off",
        "zones_checked": ZONE_NAMES,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
