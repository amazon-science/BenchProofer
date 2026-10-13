#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14792 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`resolveZoneLabel`) transliterated to Python over the real repo
              input (a `tzinfo` object), via the mapping.md §2 bijection:
              a `tzinfo` ↔ its two observable labels `(tz.tzname(None), str(tz))`;
              `Option (List Char)` ↔ `None`/`str`; the emptiness test `s ≠ []`
              ↔ Python string truthiness. There are NO A-tagged callees in the
              impl region (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `django.utils.timezone._get_timezone_name` applied at base_commit
              (the harness applies the gold patch before this runs).

They must agree on the returned label for every input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django
(+ pytz, and zoneinfo when present) only. The fuzz seed is pinned (mapping.md
§4) for a deterministic verdict.
"""
import datetime
import random
import string
import sys

SEED = 14792
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean resolveZoneLabel, transliterated ----------

def observe_short(tz):
    """mapping.md §2: shortLabel = tz.tzname(None).  None ↔ none; str ↔ some."""
    return tz.tzname(None)


def observe_full(tz):
    """mapping.md §2: fullLabel = str(tz).  Always a str."""
    return str(tz)


def shadow_resolve(tz):
    """resolveZoneLabel (observe_short tz) (observe_full tz), transliterated.
    Branch order EXACTLY as Solution.lean's impl:
        match shortLabel with
        | none   => return fullLabel
        | some s => if s ≠ [] then s else fullLabel
    `none` ↔ short is None; `s ≠ []` ↔ a non-empty Python str (truthiness)."""
    short = observe_short(tz)
    full = observe_full(tz)
    if short is None:                      # none branch
        return full
    else:                                  # some s branch
        return short if short != "" else full


def oracle_resolve(tz):
    """patch.diff's behaviour: the REAL patched _get_timezone_name."""
    from django.utils.timezone import _get_timezone_name
    return _get_timezone_name(tz)


# --- corpus: tzinfo objects spanning the short/full agreement & divergence ---

def boundary_tzs():
    out = []
    # datetime.timezone: tzname(None) and str() always coincide; named & unnamed
    for h in (0, 1, 5, 10, -10, 14, -12):
        out.append(datetime.timezone(datetime.timedelta(hours=h)))
        out.append(datetime.timezone(datetime.timedelta(hours=h), name="Etc/GMT-%d" % h))
    out.append(datetime.timezone.utc)
    # an explicitly empty-named fixed offset: tzname(None) == '' (falsy) -> full
    out.append(datetime.timezone(datetime.timedelta(0), name=""))
    try:
        import pytz
        for z in ("Europe/Madrid", "Etc/GMT-10", "Etc/GMT+10", "America/Chicago",
                  "UTC", "Asia/Kolkata", "Pacific/Kiritimati"):
            out.append(pytz.timezone(z))
        out.append(pytz.utc)
    except Exception:
        pass
    try:
        import zoneinfo
        for z in ("Europe/Madrid", "Etc/GMT-10", "Etc/GMT+10", "America/Chicago",
                  "UTC", "Asia/Kolkata"):
            out.append(zoneinfo.ZoneInfo(z))
    except Exception:
        pass
    return out


_PYTZ_ZONES = []
_ZI_ZONES = []
try:
    import pytz as _pytz
    _PYTZ_ZONES = list(_pytz.all_timezones)
except Exception:
    _pytz = None
try:
    import zoneinfo as _zoneinfo
    _ZI_ZONES = sorted(_zoneinfo.available_timezones())
except Exception:
    _zoneinfo = None


def rand_tz(rng):
    kind = rng.randint(0, 3)
    if kind == 0:
        mins = rng.randint(-23 * 60, 23 * 60 + 59)
        return datetime.timezone(datetime.timedelta(minutes=mins))
    if kind == 1:
        mins = rng.randint(-23 * 60, 23 * 60 + 59)
        name = "".join(rng.choice(string.ascii_letters + "/-+_0123456789")
                       for _ in range(rng.randint(0, 12)))
        try:
            return datetime.timezone(datetime.timedelta(minutes=mins), name=name)
        except Exception:
            return datetime.timezone(datetime.timedelta(minutes=mins))
    if kind == 2 and _PYTZ_ZONES:
        return _pytz.timezone(rng.choice(_PYTZ_ZONES))
    if kind == 3 and _ZI_ZONES:
        return _zoneinfo.ZoneInfo(rng.choice(_ZI_ZONES))
    # fallback if pytz/zoneinfo absent
    return datetime.timezone(datetime.timedelta(minutes=rng.randint(-720, 840)))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(tz):
        nonlocal count
        count += 1
        try:
            shadow = shadow_resolve(tz)
        except Exception as e:
            shadow = "SHADOW-EXC:%r" % e
        try:
            oracle = oracle_resolve(tz)
        except Exception as e:
            oracle = "ORACLE-EXC:%r" % e
        if shadow != oracle:
            disagreements.append((repr(tz), shadow, oracle))

    for tz in boundary_tzs():
        check(tz)

    for _ in range(N_FUZZ):
        check(rand_tz(rng))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tz, sh, orc in disagreements:
            print("  tz=%s shadow=%r oracle=%r" % (tz, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveZoneLabel agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
