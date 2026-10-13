#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16429 (nagini).

SHADOW: the impl region of model.py's ``pivot_remaining``, copied VERBATIM
below with only the contract calls (Requires/Ensures) stripped, together with
the ``Moment`` carrier class (contract lines stripped from its constructor)
and the @Pure helpers ``is_offset_aware`` / ``same_disposition`` (kept as an
internal cross-check of the shadow's domain guard). The one @ContractOnly
callee, ``well_defined_diff``, is delegated to the REAL operation the model
maps it to (mapping.md section 1): the ordered stdlib ``datetime``
subtraction ``(now - pivot).total_seconds()`` — the very expression the
patched code executes — applied to the bridged operands, so its definedness
(aware/naive compatibility) and its ordered value are the real semantics,
not a re-implementation.

ORACLE: the REAL patched repo flow per mapping.md section 1 — the
year/month-shifted reference construction and leftover-span measurement
inside ``django.utils.timesince.timesince`` (the ``if years or months:``
branch). The gate applies patch.diff to /testbed before this script runs and
sets PYTHONPATH=/testbed, so ``import django`` resolves to the patched tree.
Each probe calls the whole patched ``timesince(d, now, depth=...)`` and
compares its rendered string (or raised exception class) against the string
obtained by feeding the SHADOW's measured span into the UNCHANGED downstream
rendering (replicated here verbatim from the module, using the real module's
own ``TIME_CHUNKS`` / ``TIME_STRINGS`` / ``TIME_STRINGS_KEYS`` constants and
the real ``avoid_wrapping`` / ``gettext`` helpers). The rendered string is a
faithful observation of the modeled pair: the residual units are integer
quotients of the measured span, and the span in turn depends on every pivot
field, so any drift in the shadow's constructed reference moment (calendar
position, clock fields, or time-zone disposition) or in the span's operand
order shows up either as a different string or as a definedness mismatch
(one side raising where the other succeeds).

TYPE BRIDGE (mapping.md section 2): a ``datetime.datetime`` maps to a
``Moment`` with the same int year/month/day/hour/minute/second and
``tz: Optional[int]`` — ``None`` for an offset-naive value, the UTC offset
in minutes for an offset-aware one. The bridge back builds
``datetime.timezone(timedelta(minutes=tz))`` for an int disposition and no
tzinfo for ``None``. Probes use microsecond-0 datetimes (the carrier does
not observe sub-second fields). The harness derives the shadow's
``pivot_year`` / ``pivot_month`` / ``pivot_day`` arguments with the same
unchanged front computation the repo performs (the whole-month count and the
day clamp are not under change; the clamp table is imported from the real
module), and only counts probes that actually reach the modeled branch
(a whole number of years/months elapsed), which is exactly the domain where
``pivot_remaining`` is invoked.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary probes (naive and
aware sources over many fixed offsets including the extremes, month-length
clamping at short months and leap-February, month-index wraparound, same-day
clock-order adjustment, zero residual spans, second-level residuals,
millennium-scale spans, differing aware offsets between the two moments)
each crossed with depths 1-3, plus randomized fuzz until 100000 total
branch-reaching probes are checked. Pinned fuzz seed: 16429. Exit 0 iff
zero disagreements; on disagreement prints the input and both outputs and
exits 1. stdlib only.
"""
import datetime
import random
import sys

SEED = 16429
TARGET_CHECKS = 100000


# --- type bridge: Moment <-> datetime.datetime --------------------------------

def tz_of(dt):
    """datetime -> disposition carrier: None when naive, offset-minutes when
    aware (the documented Optional[int] abstraction)."""
    off = dt.utcoffset()
    if off is None:
        return None
    return int(off.total_seconds() // 60)


def tz_back(tz):
    """Disposition carrier -> tzinfo argument for the reverse bridge."""
    if tz is None:
        return None
    return datetime.timezone(datetime.timedelta(minutes=tz))


def moment_to_datetime(m):
    return datetime.datetime(m.year, m.month, m.day, m.hour, m.minute,
                             m.second, tzinfo=tz_back(m.tz))


# --- Moment carrier + pure region of model.py, contract lines stripped --------

class Moment:
    def __init__(self, year, month, day, hour, minute, second, tz):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz = tz


def is_offset_aware(tz):
    """A disposition is offset-aware exactly when an offset is carried."""
    return tz is not None


def same_disposition(a, b):
    """Two moments share a disposition when they are both offset-aware or both
    offset-naive."""
    return is_offset_aware(a) == is_offset_aware(b)


# --- @ContractOnly callee: the REAL ordered difference ------------------------

def well_defined_diff(now, pivot):
    """Delegated to the real operation the model binds it to: the stdlib
    datetime subtraction of exactly this ordered operand pair (mapping.md
    section 1). Definedness (it raises on an aware/naive mix) and the ordered
    value are the real semantics."""
    return (moment_to_datetime(now) - moment_to_datetime(pivot)).total_seconds()


# --- impl region of model.py, verbatim with contract calls stripped -----------

def pivot_remaining(d, now, pivot_year, pivot_month, pivot_day):
    pivot = Moment(
        pivot_year,
        pivot_month,
        pivot_day,
        d.hour,
        d.minute,
        d.second,
        d.tz,
    )
    remaining = well_defined_diff(now, pivot)
    return pivot, remaining


# --- oracle plumbing -----------------------------------------------------------

def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False)
    django.setup()


def front_derivation(d, now):
    """The UNCHANGED computation ahead of the modeled branch (whole-month
    count, its day/clock adjustment, and the shifted calendar position with
    the real module's day-clamp table). Returns None when the modeled branch
    is not reached for this input."""
    from django.utils.timesince import MONTHS_DAYS

    delta = now - d
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        return None
    total_months = (now.year - d.year) * 12 + (now.month - d.month)
    if d.day > now.day or (d.day == now.day and d.time() > now.time()):
        total_months -= 1
    years, months = divmod(total_months, 12)
    if not (years or months):
        return None
    pivot_year = d.year + years
    pivot_month = d.month + months
    if pivot_month > 12:
        pivot_month -= 12
        pivot_year += 1
    pivot_day = min(MONTHS_DAYS[pivot_month - 1], d.day)
    return years, months, pivot_year, pivot_month, pivot_day


def render_tail(years, months, remaining_time, depth):
    """The UNCHANGED downstream rendering (residual-unit decomposition and
    string assembly), replicated on the real module's constants and helpers.
    This lifts the shadow's measured span into the same observable space as
    the whole-function oracle output."""
    from django.utils.html import avoid_wrapping
    from django.utils.timesince import (
        TIME_CHUNKS, TIME_STRINGS, TIME_STRINGS_KEYS,
    )
    from django.utils.translation import gettext

    time_strings = TIME_STRINGS
    partials = [years, months]
    for chunk in TIME_CHUNKS:
        count = remaining_time // chunk
        partials.append(count)
        remaining_time -= chunk * count
    i = 0
    for i, value in enumerate(partials):
        if value != 0:
            break
    else:
        return avoid_wrapping(time_strings["minute"] % {"num": 0})
    result = []
    current_depth = 0
    while i < len(TIME_STRINGS_KEYS) and current_depth < depth:
        value = partials[i]
        if value == 0:
            break
        name = TIME_STRINGS_KEYS[i]
        result.append(avoid_wrapping(time_strings[name] % {"num": value}))
        current_depth += 1
        i += 1
    return gettext(", ").join(result)


def run_side(fn):
    """Run one side; observable is (\"ok\", string) or (\"err\", exc class)."""
    try:
        return ("ok", str(fn()))
    except Exception as e:  # a definedness mismatch is a compared observable
        return ("err", type(e).__name__)


# --- differential driver -------------------------------------------------------

def check_one(d, now, depth):
    """Compare shadow-composed and real outputs for one (d, now, depth).
    Returns (checked?, error-string-or-None)."""
    from django.utils.timesince import timesince

    front = front_derivation(d, now)
    if front is None:
        return False, None  # modeled branch not reached: out of scope
    years, months, py, pm, pd = front

    d_m = Moment(d.year, d.month, d.day, d.hour, d.minute, d.second, tz_of(d))
    now_m = Moment(now.year, now.month, now.day, now.hour, now.minute,
                   now.second, tz_of(now))
    # internal cross-check of the pure-region domain guard: the generated
    # pair always satisfies the precondition
    assert same_disposition(now_m.tz, d_m.tz), "generator broke the domain"

    def shadow_side():
        pivot_m, remaining = pivot_remaining(d_m, now_m, py, pm, pd)
        return render_tail(years, months, remaining, depth)

    shadow = run_side(shadow_side)
    real = run_side(lambda: timesince(d, now, depth=depth))
    if shadow != real:
        return True, (
            "DISAGREEMENT at d=%r now=%r depth=%d\n"
            "  (pivot args: year=%d month=%d day=%d)\n"
            "  shadow (impl region + real ordered diff) = %r\n"
            "  real (patched timesince)                 = %r"
            % (d, now, depth, py, pm, pd, shadow, real))
    return True, None


# --- input generation ----------------------------------------------------------

def _tz(minutes):
    return datetime.timezone(datetime.timedelta(minutes=minutes))


def boundary_pairs():
    """(d, now) probe pairs; every pair shares a disposition."""
    DT = datetime.datetime
    TD = datetime.timedelta
    pairs = []
    # plain naive / aware month-and-more spans over a spread of offsets,
    # including the extreme representable offsets and a zero offset
    offsets = [None, 0, 60, -60, 330, -480, 540, 765, -720, 1439, -1439]
    for off in offsets:
        tzi = tz_back(off)
        d = DT(2023, 3, 1, 12, 30, 45, tzinfo=tzi)
        pairs.append((d, d + TD(days=32)))
        pairs.append((d, d + TD(days=365)))
        pairs.append((d, d + TD(days=400, seconds=59)))
    # differing aware offsets between the two moments
    pairs.append((DT(2022, 1, 10, 6, 0, 0, tzinfo=_tz(120)),
                  DT(2023, 4, 2, 21, 15, 5, tzinfo=_tz(-300))))
    pairs.append((DT(2020, 7, 4, 0, 0, 0, tzinfo=_tz(-1439)),
                  DT(2021, 9, 1, 23, 59, 59, tzinfo=_tz(1439))))
    # day clamp: source day 31 landing on short reference months
    pairs.append((DT(2023, 1, 31, 8, 0, 0), DT(2023, 3, 1, 9, 0, 0)))
    pairs.append((DT(2023, 1, 31, 8, 0, 0, tzinfo=_tz(0)),
                  DT(2023, 3, 1, 9, 0, 0, tzinfo=_tz(0))))
    pairs.append((DT(2023, 3, 31, 8, 0, 0), DT(2023, 5, 1, 0, 0, 0)))
    pairs.append((DT(2023, 5, 31, 23, 59, 59), DT(2023, 7, 4, 0, 0, 0)))
    # leap-day source, reference lands in a non-leap February
    pairs.append((DT(2020, 2, 29, 12, 0, 0), DT(2021, 3, 15, 12, 0, 0)))
    pairs.append((DT(2020, 2, 29, 12, 0, 0, tzinfo=_tz(60)),
                  DT(2021, 3, 15, 12, 0, 0, tzinfo=_tz(60))))
    # month-index wraparound past year end
    pairs.append((DT(2023, 8, 15, 3, 4, 5), DT(2024, 3, 20, 6, 7, 8)))
    pairs.append((DT(2023, 12, 31, 23, 0, 0, tzinfo=_tz(-90)),
                  DT(2024, 2, 2, 1, 0, 0, tzinfo=_tz(-90))))
    # same-day clock-order adjustment on the whole-month count
    pairs.append((DT(2023, 1, 15, 18, 0, 0), DT(2023, 3, 15, 6, 0, 0)))
    pairs.append((DT(2023, 1, 15, 6, 0, 0), DT(2023, 3, 15, 18, 0, 0)))
    pairs.append((DT(2023, 1, 15, 12, 0, 0), DT(2023, 3, 15, 12, 0, 0)))
    # zero residual: exact whole years / months
    pairs.append((DT(2000, 6, 15, 10, 20, 30), DT(2010, 6, 15, 10, 20, 30)))
    pairs.append((DT(2000, 6, 15, 10, 20, 30, tzinfo=_tz(0)),
                  DT(2000, 8, 15, 10, 20, 30, tzinfo=_tz(0))))
    # second-level residuals just past a whole month
    pairs.append((DT(2023, 4, 10, 0, 0, 0), DT(2023, 5, 10, 0, 0, 59)))
    pairs.append((DT(2023, 4, 10, 0, 0, 30), DT(2023, 5, 10, 0, 1, 29)))
    # millennium-scale spans, naive and aware
    pairs.append((DT(1000, 1, 1, 0, 0, 0), DT(2023, 5, 5, 12, 0, 0)))
    pairs.append((DT(1000, 1, 1, 0, 0, 0, tzinfo=_tz(0)),
                  DT(2023, 5, 5, 12, 0, 0, tzinfo=_tz(0))))
    pairs.append((DT(1, 1, 1, 0, 0, 0), DT(9999, 12, 31, 23, 59, 59)))
    return pairs


def main():
    _setup_django()

    checked = 0
    boundary_checked = 0

    for d, now in boundary_pairs():
        for depth in (1, 2, 3):
            did, err = check_one(d, now, depth)
            if err:
                print(err)
                return 1
            if did:
                checked += 1
                boundary_checked += 1

    rng = random.Random(SEED)
    attempts = 0
    max_attempts = TARGET_CHECKS * 4
    while checked < TARGET_CHECKS and attempts < max_attempts:
        attempts += 1
        year = rng.randint(1, 6000)
        month = rng.randint(1, 12)
        # weight month-end days heavily to stress the clamp
        day = rng.choice([rng.randint(1, 28), 28, 29, 30, 31])
        try:
            d = datetime.datetime(year, month, day,
                                  rng.randint(0, 23), rng.randint(0, 59),
                                  rng.randint(0, 59))
        except ValueError:
            continue  # day out of range for the month
        aware = rng.random() < 0.6
        if aware:
            d = d.replace(tzinfo=_tz(rng.choice(
                [0, 0, 60, -60, 330, -480, 765, 1439, -1439,
                 rng.randint(-1439, 1439)])))
        # span: bias toward the smallest whole-month region, with a long tail
        bucket = rng.random()
        if bucket < 0.4:
            days = rng.randint(25, 70)
        elif bucket < 0.8:
            days = rng.randint(70, 5000)
        else:
            days = rng.randint(5000, 1000000)
        now = d + datetime.timedelta(days=days, seconds=rng.randint(0, 86399))
        if now.year > 9999:
            continue
        if aware and rng.random() < 0.5:
            # an aware pair need not share an offset, only the disposition
            now = now.astimezone(_tz(rng.randint(-1439, 1439)))
        now = now.replace(microsecond=0)
        depth = rng.choice([1, 2, 2, 3])
        did, err = check_one(d, now, depth)
        if err:
            print(err)
            return 1
        if did:
            checked += 1

    if checked < TARGET_CHECKS:
        print("ERROR: only %d branch-reaching probes generated" % checked)
        return 1

    print("PASS: shadow impl == real patched repo flow on %d probes "
          "(%d boundary-derived + %d fuzz), pinned seed %d, 0 disagreements"
          % (checked, boundary_checked, checked - boundary_checked, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)"}'
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
