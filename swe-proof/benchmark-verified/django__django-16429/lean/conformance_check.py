#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16429.

The bundle models ONE function: the `pivot` datetime construction inside
`timesince` (`django/utils/timesince.py`, the `if years or months:` branch). Its
Lean implementation (`implementation_anchor`) assembles a "reference instant"
shifted from the starting instant `d` by `years` years and `months` months,
field by field:

    anchor_year  = d.year + years
    anchor_month = d.month + months
    if anchor_month > 12: anchor_month -= 12; anchor_year += 1
    result = Instant(year=anchor_year, month=anchor_month,
                     day=min(month_length(anchor_month), d.day),
                     hour=d.hour, minute=d.minute, second=d.second,
                     offset=d.offset)          # <-- carries d's timezone designation

This script transliterates that R/I impl into Python (`shadow_pivot`) and
differential-tests it against the ORACLE: a faithful in-process FIELD-LEVEL
replica of the post-patch pivot construction (the patched `datetime.datetime(...,
tzinfo=d.tzinfo)` call):

    pivot_year = d.year + years
    pivot_month = d.month + months
    if pivot_month > 12: pivot_month -= 12; pivot_year += 1
    pivot = (pivot_year, pivot_month,
             min(MONTHS_DAYS[pivot_month - 1], d.day),
             d.hour, d.minute, d.second,
             d.tzinfo)                          # post-fix: tzinfo carried over

We do NOT construct real `datetime.datetime` objects: the real constructor would
reject out-of-range field combinations (e.g. day clamping is exactly what avoids
that downstream), and the modeled value is a pure field assembly. Instead both
sides operate on the SAME observable inputs the construction consumes
(mapping.md): the seven fields of `d` plus `years`/`months`. The timezone
designation is modeled as an integer offset in seconds or `None` (naive) — the
patch's only behavioral change is that the pivot now carries `d`'s designation
rather than `None`, so the differential is most discriminating on the `offset`
field.

stdlib-only; pinned seed 16429 (also recorded in mapping.md).
"""
import sys

SEED = 16429
N = 120_000

MONTHS_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def month_length(m):
    # mirrors Lean `monthLength`: table lookup for 1..12, fallback 31.
    if 1 <= m <= 12:
        return MONTHS_DAYS[m - 1]
    return 31


# --- ORACLE: the post-patch pivot construction, faithful field-level replica ---
# Returns the seven observable output fields of the pivot, INCLUDING the
# carried-over timezone designation (tzinfo=d.tzinfo).  `offset` is None for a
# naive datetime, else the fixed UTC offset in seconds.
def oracle_pivot(year, month, day, hour, minute, second, offset, years, months):
    pivot_year = year + years
    pivot_month = month + months
    if pivot_month > 12:
        pivot_month -= 12
        pivot_year += 1
    return (
        pivot_year,
        pivot_month,
        min(MONTHS_DAYS[pivot_month - 1], day),
        hour,
        minute,
        second,
        offset,            # post-fix: pivot carries d's timezone designation
    )


# --- shadow of implementation_anchor (the R/I leg) ---------------------------
# Mirrors Solution.lean field for field.
def shadow_pivot(year, month, day, hour, minute, second, offset, years, months):
    anchor_year = year + years
    anchor_month = month + months
    if anchor_month > 12:
        anchor_month -= 12
        anchor_year += 1
    return (
        anchor_year,
        anchor_month,
        min(month_length(anchor_month), day),
        hour,
        minute,
        second,
        offset,            # offset := d.offset
    )


def disagree(args):
    got = oracle_pivot(*args)
    want = shadow_pivot(*args)
    if got != want:
        return (args, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked cases exercising the timezone designation, roll-over, and clamp."""
    cases = []
    # naive (offset None) -- the base-commit-style designation:
    cases.append((2000, 1, 15, 10, 30, 0, None, 0, 1))
    # aware (offset some k) -- the USE_TZ=True case the patch fixes:
    cases.append((2000, 1, 15, 10, 30, 0, 0, 0, 1))          # UTC
    cases.append((2000, 1, 15, 10, 30, 0, 3600, 1, 0))       # +1h
    cases.append((2000, 1, 15, 10, 30, 0, -18000, 2, 3))     # -5h
    # December roll-over (pivot_month > 12):
    cases.append((2023, 11, 30, 0, 0, 0, 0, 0, 3))           # 11 + 3 = 14 -> 2, year+1
    cases.append((2023, 12, 31, 23, 59, 59, 7200, 5, 1))     # 12 + 1 = 13 -> 1, year+1
    # day clamping into a short month (Jan 31 -> Feb has 28):
    cases.append((2021, 1, 31, 12, 0, 0, None, 0, 1))        # -> month 2, day min(28,31)=28
    cases.append((2021, 3, 31, 12, 0, 0, 0, 0, 1))           # -> month 4 (30), day 30
    # 1000-years interval analogue (large years):
    cases.append((1023, 8, 14, 13, 46, 0, 0, 1000, 0))
    return cases


def main() -> int:
    checked = 0

    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        year = 1 + (next(rnd) % 4000)        # 1..4000
        month = 1 + (next(rnd) % 12)         # 1..12
        day = 1 + (next(rnd) % 31)           # 1..31
        hour = next(rnd) % 24
        minute = next(rnd) % 60
        second = next(rnd) % 60
        # offset: None ~1/3 of the time, else a signed second offset.
        r = next(rnd) % 3
        if r == 0:
            offset = None
        else:
            offset = (next(rnd) % 50401) - 25200   # -7h .. +7h in seconds
        years = next(rnd) % 6                # 0..5
        months = next(rnd) % 12              # 0..11
        d = disagree((year, month, day, hour, minute, second, offset, years, months))
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
