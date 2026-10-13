#!/usr/bin/env python3
"""G-CONF for django__django-14792.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_getTimezoneName` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`django.utils.timezone._get_timezone_name`, over >=1e5 fuzzed inputs.
Zero disagreements => exit 0.

Type bijection (mapping.md):
  tzLabel <-> timezone.tzname(None)  (str | None)
  tzStr   <-> str(timezone)          (str)
  result  <-> return value           (str)

We exercise the differential test on two fronts:
  (1) REAL time-zone objects (the F2P examples: datetime fixed-offset with and
      without name, pytz named/fixed, zoneinfo named/fixed). For each object we
      read its (tzname(None), str(.)) observables, feed them to the shadow, and
      compare to the real helper's return value.
  (2) SYNTHETIC (Option str, str) pairs probing the none / some "" / some
      nonempty boundaries against a faithful reference oracle.

stdlib-only (plus Django/pytz/zoneinfo already in /testbed); no hypothesis.
"""
import os
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=True,
        TIME_ZONE="UTC",
        DATABASES={},
        INSTALLED_APPS=[],
    )
    django.setup()

import datetime

from django.utils import timezone as tzmod

_real = tzmod._get_timezone_name  # the patched helper


def shadow(tz_label, tz_str):
    """R/I transliteration of implementation_getTimezoneName (Lean).

    tz_label: str | None  (the optional short label, tzname(None))
    tz_str:   str         (the full textual form, str(timezone))
    """
    name = tz_str
    if tz_label is not None:
        if tz_label != "":
            name = tz_label
    return name


def ref_oracle(tz_label, tz_str):
    """Faithful Python reference of `tzname(None) or str(timezone)` for the
    synthetic leg: `or` selects the left operand iff it is truthy."""
    return tz_label or tz_str


def real_objects():
    """Real time-zone objects (the F2P set) + a fixed-offset sweep."""
    objs = []
    objs.append(datetime.timezone(datetime.timedelta(hours=10)))
    objs.append(datetime.timezone(datetime.timedelta(hours=10), name="Etc/GMT-10"))
    objs.append(datetime.timezone.utc)
    for h in range(-12, 15):
        objs.append(datetime.timezone(datetime.timedelta(hours=h)))
        objs.append(datetime.timezone(datetime.timedelta(hours=h),
                                      name="Custom/%d" % h))
    try:
        import pytz
        for nm in ("Europe/Madrid", "Etc/GMT-10", "Etc/GMT+5", "America/New_York",
                   "UTC", "Asia/Bangkok"):
            objs.append(pytz.timezone(nm))
        objs.append(pytz.utc)
    except Exception:
        pass
    try:
        import zoneinfo
        for nm in ("Europe/Madrid", "Etc/GMT-10", "Etc/GMT+5", "America/New_York",
                   "UTC", "Asia/Bangkok"):
            objs.append(zoneinfo.ZoneInfo(nm))
    except Exception:
        try:
            from backports import zoneinfo  # type: ignore
            for nm in ("Europe/Madrid", "Etc/GMT-10", "UTC"):
                objs.append(zoneinfo.ZoneInfo(nm))
        except Exception:
            pass
    return objs


def main():
    rng = random.Random(14792)  # pinned seed (mapping.md)
    disagreements = 0
    first = None
    checked = 0

    # --- leg 1: real time-zone objects ------------------------------------
    objs = real_objects()
    for _ in range(20000):
        tz = rng.choice(objs)
        try:
            label = tz.tzname(None)
        except Exception:
            label = None
        full = str(tz)
        got_shadow = shadow(label, full)
        got_real = _real(tz)
        checked += 1
        if got_shadow != got_real:
            disagreements += 1
            if first is None:
                first = ("realobj", repr(tz), label, full, got_real, got_shadow)

    # --- leg 2: synthetic (Option str, str) pairs -------------------------
    LABELS = [None, "", "+10", "-05", "Etc/GMT-10", "UTC", "x", "  ", "0"]
    STRS = ["Europe/Madrid", "+10", "America/New_York", "", "UTC", "tz", "fallback"]

    def rand_label(r):
        if r.random() < 0.3:
            return None
        if r.random() < 0.3:
            return ""
        return r.choice(LABELS[2:]) if r.random() < 0.6 else _rand_str(r)

    N = 100_000
    for _ in range(N):
        label = rand_label(rng)
        full = rng.choice(STRS) if rng.random() < 0.7 else _rand_str(rng)
        got_shadow = shadow(label, full)
        got_ref = ref_oracle(label, full)
        checked += 1
        if got_shadow != got_ref:
            disagreements += 1
            if first is None:
                first = ("synthetic", label, full, got_ref, got_shadow)

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" %
              (disagreements, checked, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % checked)
    return 0


def _rand_str(r):
    n = r.randint(0, 6)
    alpha = "abcEFG_/+-0123 "
    return "".join(r.choice(alpha) for _ in range(n))


if __name__ == "__main__":
    sys.exit(main())
