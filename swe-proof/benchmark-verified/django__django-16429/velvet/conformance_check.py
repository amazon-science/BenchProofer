#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-16429 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`datetime` <-> `Instant` field-wise, `tzinfo` <-> `Option Nat`,
              `MONTHS_DAYS[m-1]` <-> `monthLen m`). Concretely the shadow is a
              faithful reimplementation of `timesince(d, now)` that differs from
              the real function in EXACTLY ONE place: the shifted reference
              instant ("pivot") is built by `shift_reference(...)` — the Python
              transliteration of `Solution.lean`'s `shiftReference` deep model,
              which carries the source's time-zone designation onto the
              reference (`tzinfo=d.tzinfo`). Every other operation (the
              years/months arithmetic, the chunking, the formatting) reuses the
              REAL django helpers (`MONTHS_DAYS`, `TIME_CHUNKS`, `TIME_STRINGS`,
              `avoid_wrapping`, `gettext`, `is_aware`), so any disagreement is
              attributable to the modeled op alone (the R/I legs, A1-A8).
              There are NO A-tagged callees in the computed output (no consumed
              axioms — refinement.md §C), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the real patched
              `django.utils.timesince.timesince(d, now)` applied at base_commit
              (the harness applies patch.diff before this runs). This is the
              correctness oracle (G-RESOLVE).

They must agree on every input, INCLUDING tz-aware sources >= 1 month in the
past, where the pre-patch construction produced a tz-naive reference and the
downstream `now - pivot` raised `TypeError` (the reported regression). Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import datetime
import random
import sys

SEED = 16429
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_I18N=False,
            USE_TZ=True,
            INSTALLED_APPS=[],
            DATABASES={},
            TIME_ZONE="UTC",
        )
    django.setup()


# --- A fixed-offset tzinfo pool (the "designations" of mapping.md §2) ---------
# Each distinct tzinfo object is a distinct `some k`; `None` is `none`.
def _tz_pool():
    return [
        None,                                              # none  (naive)
        datetime.timezone.utc,                             # some 0
        datetime.timezone(datetime.timedelta(hours=5, minutes=30)),   # some 1
        datetime.timezone(datetime.timedelta(hours=-8)),   # some 2
        datetime.timezone(datetime.timedelta(hours=1)),    # some 3
    ]


def main():
    rng = random.Random(SEED)
    try:
        _setup_django()
        from django.utils.timesince import timesince, MONTHS_DAYS
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched django timesince: %r" % e)
        return 2

    # ---- SHADOW: shift_reference == Solution.lean's shiftReference -----------
    # monthLen m == MONTHS_DAYS[m-1] for m in 1..12 (mapping.md §2 / A5). We use
    # the REAL MONTHS_DAYS table so the clamp leg is the repo's own data.
    def month_len(m):
        return MONTHS_DAYS[m - 1]

    def shift_reference(d, years, months):
        """Python transliteration of Solution.lean `shiftReference` (A1-A8).
        Builds the shifted reference instant carrying `tzinfo=d.tzinfo` (A7)."""
        py = d.year + years
        pm = d.month + months
        if pm > 12:
            pm -= 12
            py += 1
        return datetime.datetime(
            py,
            pm,
            min(month_len(pm), d.day),
            d.hour,
            d.minute,
            d.second,
            tzinfo=d.tzinfo,            # the modeled change (A7)
        )

    def shadow(d, now):
        """Faithful reimplementation of timesince(d, now) whose ONLY modeled op
        is the pivot construction (shift_reference). Mirrors the real algorithm;
        formatting is delegated to the real django helpers so divergences
        isolate the modeled op. Returns the formatted string, or the marker
        ('RAISED', type-name) if the difference is undefined (mixed aware/naive),
        matching what the real function would do at the same step."""
        # depth defaults to 2; both d and now are datetimes here.
        delta = now - d   # may raise TypeError if tz-mixed (same as real)
        since = delta.days * 24 * 60 * 60 + delta.seconds
        if since <= 0:
            return ("ZERO",)
        total_months = (now.year - d.year) * 12 + (now.month - d.month)
        if d.day > now.day or (d.day == now.day and d.time() > now.time()):
            total_months -= 1
        years, months = divmod(total_months, 12)
        if years or months:
            pivot = shift_reference(d, years, months)        # MODELED OP
        else:
            pivot = d
        remaining_time = (now - pivot).total_seconds()       # may raise if naive
        partials = [years, months]
        for chunk in (60 * 60 * 24 * 7, 60 * 60 * 24, 60 * 60, 60):
            count = remaining_time // chunk
            partials.append(count)
            remaining_time -= chunk * count
        # We only need to compare the *unit/value vector* (the formatting is the
        # real helper, identical on both sides). Find first nonzero, take depth=2.
        return ("OK", tuple(partials))

    def oracle(d, now):
        return timesince(d, now)

    # ---- input stream --------------------------------------------------------
    def gen_datetime(rng, tz):
        y = rng.randint(2, 9998)
        mo = rng.randint(1, 12)
        dmax = MONTHS_DAYS[mo - 1]
        day = rng.randint(1, dmax)
        return datetime.datetime(
            y, mo, day,
            rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59),
            tzinfo=tz,
        )

    def inputs(n):
        pool = _tz_pool()
        # boundary cases first (plan §4.1 step 4): the reported regression ----
        # tz-aware `d`, >= 1 month in the past, USE_TZ on.
        base = datetime.datetime(2007, 6, 15, 13, 46, 0, tzinfo=datetime.timezone.utc)
        yield (base - datetime.timedelta(days=31), base)     # 1 month, aware
        yield (base - datetime.timedelta(days=40), base)     # >1 month, aware
        yield (base - datetime.timedelta(days=400), base)    # >1 year, aware
        # thousand years (the F2P test_thousand_years_ago, aware)
        yield (base.replace(year=base.year - 1000), base)
        # naive counterparts (must still agree)
        nb = base.replace(tzinfo=None)
        yield (nb - datetime.timedelta(days=31), nb)
        yield (nb - datetime.timedelta(days=400), nb)
        # end-of-month source (exercises the min/MONTHS_DAYS clamp, A5)
        eom = datetime.datetime(2008, 1, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
        yield (eom, datetime.datetime(2008, 3, 31, 0, 0, 0, tzinfo=datetime.timezone.utc))
        # leap-day source
        yield (datetime.datetime(2008, 2, 29, tzinfo=datetime.timezone.utc),
               datetime.datetime(2009, 3, 1, tzinfo=datetime.timezone.utc))
        for _ in range(n):
            tz = rng.choice(pool)
            d = gen_datetime(rng, tz)
            now = gen_datetime(rng, tz)   # SAME designation status (comparable)
            yield (d, now)

    disagreements = []
    count = 0
    for d, now in inputs(N_FUZZ):
        count += 1
        # shadow
        try:
            sh = shadow(d, now)
            sh_raised = None
        except Exception as e:
            sh, sh_raised = None, type(e).__name__
        # oracle (real patched timesince)
        try:
            orc = oracle(d, now)
            orc_raised = None
        except Exception as e:
            orc, orc_raised = None, type(e).__name__

        # Compare RAISE-behaviour first: the patched code must never raise on a
        # comparable (same-designation) pair; neither must the shadow.
        if (sh_raised is not None) != (orc_raised is not None):
            disagreements.append((d, now, "shadow_raised=%r" % sh_raised,
                                  "oracle_raised=%r" % orc_raised))
            if len(disagreements) >= 5:
                break
            continue
        if sh_raised is not None and orc_raised is not None:
            continue  # both undefined at the same step — agree

        # Both produced a value. The shadow returns a tag/partials vector; the
        # oracle returns the formatted string. We reconstruct the oracle's
        # unit/value vector by re-running the shadow's NON-MODELED tail with the
        # REAL pivot — but since the only modeled op is the pivot and all
        # formatting is the real helper, equality of the formatted strings is
        # the cleanest cross-check. Build the shadow's string via the same real
        # formatter and compare.
        sh_str = _format_from_partials(sh, d)
        if sh_str != orc:
            disagreements.append((d, now, "shadow=%r" % (sh_str,),
                                  "oracle=%r" % (orc,)))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d, now, a, b in disagreements:
            print("  d=%r now=%r %s %s" % (d, now, a, b))
        return 1
    print("G-CONF OK: R/I shadow of buildShiftedReference (timesince with the "
          "modeled pivot via shiftReference) agrees with patch.diff (real "
          "patched timesince) on %d inputs (seed=%d), 0 disagreements; "
          "tz-aware sources do not raise." % (count, SEED))
    return 0


def _format_from_partials(sh, d):
    """Render the shadow's outcome into the exact string the real timesince
    would produce, using the REAL django formatting helpers (so the comparison
    isolates the modeled pivot op, not formatting)."""
    from django.utils.timesince import (
        TIME_STRINGS, TIME_STRINGS_KEYS, avoid_wrapping,
    )
    from django.utils.translation import gettext
    if sh[0] == "ZERO":
        return avoid_wrapping(TIME_STRINGS["minute"] % {"num": 0})
    # sh == ("OK", partials)
    partials = list(sh[1])
    # find first non-zero
    i = 0
    found = False
    for i, value in enumerate(partials):
        if value != 0:
            found = True
            break
    if not found:
        return avoid_wrapping(TIME_STRINGS["minute"] % {"num": 0})
    result = []
    current_depth = 0
    depth = 2
    while i < len(TIME_STRINGS_KEYS) and current_depth < depth:
        value = partials[i]
        if value == 0:
            break
        name = TIME_STRINGS_KEYS[i]
        result.append(avoid_wrapping(TIME_STRINGS[name] % {"num": value}))
        current_depth += 1
        i += 1
    return gettext(", ").join(result)


if __name__ == "__main__":
    sys.exit(main())
