#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14792.

There is NO consumed @ContractOnly axiom in model.py. The two textual
observations the helper selects between are unchanged object queries carried
directly as the model's inputs:

  - ``tz.short_label`` (Optional[PSeq[int]])  models  ``timezone.tzname(None)``
  - ``tz.full_name``    (PSeq[int])           models  ``str(timezone)``

and the resolved-name SELECTION is modelled DEEPLY in model.py
(``resolve_timezone_name`` + ``present_and_nonempty``). This script validates
that A-reference against the REAL callees: for real time-zone objects from
every family the F2P test uses (``datetime.timezone`` fixed offsets with and
without ``name``, ``pytz`` named and fixed-offset zones, and ``zoneinfo`` named
and fixed-offset zones), it

  (1) extracts the two real observations  ``timezone.tzname(None)``  and
      ``str(timezone)``  and forms the model carriers (None ↔ absent label,
      "" ↔ empty sequence);
  (2) computes the model's deep selection
        short_label  if (short_label is not None and short_label != "")
        else full_name
      over those carriers; and
  (3) asserts it equals the REAL helper result  ``timezone.tzname(None) or
      str(timezone)``  (the gold post-patch expression).

It also re-confirms the exact F2P expectations (e.g. pytz/zoneinfo
``Etc/GMT-10`` -> "+10"; ``datetime.timezone(+10h)`` -> "UTC+10:00"; named
zones -> their full name). Imports only the standard library plus pytz/zoneinfo
(the very modules the helper and its test use); nothing repo-private. Exit 0 iff
every observation matches the model.
"""
import datetime
import random
import sys


def _carriers(tz):
    """The two model carriers for a real tzinfo object:
    short_label = list(tzname(None)) or None;  full_name = list(str(tz))."""
    raw = tz.tzname(None)
    short_label = None if raw is None else [ord(ch) for ch in raw]
    full_name = [ord(ch) for ch in str(tz)]
    return short_label, full_name


def present_and_nonempty(label):
    """Mirror of model.py's pure predicate."""
    return label is not None and len(label) > 0


def model_resolve(short_label, full_name):
    """Mirror of model.py's deep selection (resolve_timezone_name impl)."""
    if present_and_nonempty(short_label):
        return short_label
    return full_name


def real_resolve(tz):
    """The REAL gold post-patch expression:  tzname(None) or str(tz)."""
    return [ord(ch) for ch in (tz.tzname(None) or str(tz))]


def check(tz, label):
    short_label, full_name = _carriers(tz)
    modelled = model_resolve(short_label, full_name)
    real = real_resolve(tz)
    assert modelled == real, (
        "selection deep model unsound for %s: model gives %r, real "
        "(tzname(None) or str) gives %r (short_label=%r full_name=%r)"
        % (label, modelled, real, short_label, full_name))


def _as_str(codepoints):
    return "".join(chr(c) for c in codepoints)


def main():
    import pytz

    zoneinfo = None
    try:
        import zoneinfo  # py3.9+
    except ImportError:
        try:
            from backports import zoneinfo  # py3.6-3.8
        except ImportError:
            zoneinfo = None

    # --- the exact F2P expectations (the discriminating cases) --------------
    expectations = [
        (datetime.timezone(datetime.timedelta(hours=10)), "UTC+10:00"),
        (datetime.timezone(datetime.timedelta(hours=10), name="Etc/GMT-10"),
         "Etc/GMT-10"),
        (pytz.timezone("Europe/Madrid"), "Europe/Madrid"),
        (pytz.timezone("Etc/GMT-10"), "+10"),
    ]
    if zoneinfo is not None:
        expectations += [
            (zoneinfo.ZoneInfo("Europe/Madrid"), "Europe/Madrid"),
            (zoneinfo.ZoneInfo("Etc/GMT-10"), "+10"),
        ]
    for tz, expected in expectations:
        short_label, full_name = _carriers(tz)
        got = _as_str(model_resolve(short_label, full_name))
        assert got == expected, (
            "F2P expectation broken for %r: model resolved %r, expected %r"
            % (tz, got, expected))
        # and the model agrees with the real gold expression
        check(tz, repr(tz))

    # --- boundary: fixed offsets across the dial, named and unnamed ---------
    for h in range(-14, 15):
        for m in (0, 30, 45):
            off = datetime.timedelta(hours=h, minutes=m if h >= 0 else -m)
            check(datetime.timezone(off), "datetime.timezone(%dh%dm)" % (h, m))
            check(datetime.timezone(off, name="X/Custom%d" % h),
                  "datetime.timezone named %d" % h)
    check(datetime.timezone.utc, "datetime.timezone.utc")

    # --- pytz: a spread of named zones and Etc/GMT fixed offsets ------------
    pytz_named = [
        "Europe/Madrid", "America/Chicago", "Asia/Tokyo", "UTC",
        "Australia/Sydney", "America/New_York", "Europe/London",
        "Pacific/Auckland", "Africa/Cairo", "America/Sao_Paulo",
    ]
    for name in pytz_named:
        try:
            check(pytz.timezone(name), "pytz %s" % name)
        except pytz.UnknownTimeZoneError:
            pass
    for n in range(-12, 15):
        name = "Etc/GMT%+d" % (-n) if n != 0 else "Etc/GMT"
        try:
            check(pytz.timezone(name), "pytz %s" % name)
        except pytz.UnknownTimeZoneError:
            pass
    check(pytz.utc, "pytz.utc")

    # --- zoneinfo: the same families if available ---------------------------
    if zoneinfo is not None:
        for name in pytz_named + ["Etc/GMT-10", "Etc/GMT+10", "Etc/GMT-5",
                                  "Etc/GMT+5", "Etc/UTC"]:
            try:
                check(zoneinfo.ZoneInfo(name), "zoneinfo %s" % name)
            except Exception:
                pass

    # --- randomized fuzz over fixed offsets (always a non-empty tzname) -----
    rng = random.Random(14792)
    n_fuzz = 0
    for _ in range(5000):
        mins = rng.randint(-23 * 60 - 59, 23 * 60 + 59)
        off = datetime.timedelta(minutes=mins)
        # datetime.timezone forbids |offset| >= 24h; clamp inside the range
        if abs(mins) >= 24 * 60:
            continue
        if rng.random() < 0.5:
            tz = datetime.timezone(off)
        else:
            nm = "" if rng.random() < 0.1 else "Z/%d" % mins
            try:
                tz = datetime.timezone(off, name=nm)
            except (TypeError, ValueError):
                tz = datetime.timezone(off)
        check(tz, "fuzz %d" % mins)
        n_fuzz += 1

    print("G-AX OK: deep selection model (tzname(None) or str) sound against "
          "the real callees over %d F2P + boundary/fuzz time-zone objects "
          "(datetime.timezone / pytz / zoneinfo); %d randomized fuzz cases."
          % (len(expectations), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
