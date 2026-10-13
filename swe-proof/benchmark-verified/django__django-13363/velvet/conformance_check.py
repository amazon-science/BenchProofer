#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-13363 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`dateCastZoneName` / `timeCastZoneName`, the transliteration of
              `resolveZoneName`) over the *real* repo types, via the mapping.md
              bijection (`Bool` ↔ `settings.USE_TZ`; `Option String` ↔ the
              nullable zone name `str | None`). The two opaque zone-name
              sub-callees — the ambient-zone name `get_current_timezone_name()`
              and the explicit-zone name `_get_timezone_name(tzinfo)` — are
              R-mapped: we render them with the real callees and feed the
              resulting strings to the shadow.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.models.functions.datetime.TruncDate.as_sql` and
              `TruncTime.as_sql` applied at base_commit (the real correctness
              oracle, G-RESOLVE). Each computes the `tzname` it threads into the
              backend cast callee (`datetime_cast_date_sql` /
              `datetime_cast_time_sql`); we intercept that callee to capture the
              exact `tzname` argument — the single value the gold change alters.

The surrounding `as_sql` (compile lhs, build cast SQL, return) is UNCHANGED and
the cast callee is deterministic in `tzname`, so capturing the `tzname` argument
observes exactly the changed behaviour. `get_tzname` is modeled DEEPLY by
`resolveZoneName` (an A-reference checked by G-AX); here the shadow substitutes
no axiom — it transliterates the control flow and consumes the rendered
sub-callee values — so this leg is pure R/I.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django +
pytz (already installed). The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 13363
N_FUZZ = 100_000

ZONE_KEYS = ['UTC', 'America/New_York', 'Europe/Paris', 'Asia/Bangkok',
             'Australia/Sydney', 'Africa/Nairobi', 'America/Sao_Paulo',
             'Pacific/Auckland', 'Etc/GMT+5', 'Asia/Kolkata']


def shadow_resolve(tz_aware, explicit_zone, current_zone):
    """resolveZoneName transliterated to Python (Solution.lean pure region):
    when zone-awareness is on, an explicitly-supplied zone wins over the ambient
    zone; off => no zone name. `explicit_zone is None` ↔ Lean `none`."""
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
    from django.db.models.functions.datetime import TruncDate, TruncTime
    from django.utils import timezone
    import pytz

    captured = {}

    class _FakeCompiler:
        def compile(self, node):
            return ("inner_sql", [])

    class _FakeOps:
        def datetime_cast_date_sql(self, lhs, tzname):
            captured["tzname"] = tzname
            return "CAST_DATE(%s)" % lhs

        def datetime_cast_time_sql(self, lhs, tzname):
            captured["tzname"] = tzname
            return "CAST_TIME(%s)" % lhs

    class _FakeConn:
        def __init__(self):
            self.ops = _FakeOps()

    compiler = _FakeCompiler()
    conn = _FakeConn()

    def oracle_tzname(cls, tz_aware, explicit_key, current_key):
        """Run the patched as_sql; return the captured `tzname` argument."""
        settings.USE_TZ = tz_aware
        timezone.activate(pytz.timezone(current_key))
        node = cls.__new__(cls)
        # `lhs` is a read-only property on Transform (returns
        # get_source_expressions()[0]); seed the backing list with one opaque
        # node — it is only handed to our fake compiler.compile, never inspected.
        node.source_expressions = [object()]
        node.tzinfo = pytz.timezone(explicit_key) if explicit_key else None
        captured.clear()
        node.as_sql(compiler, conn)
        timezone.deactivate()
        return captured.get("tzname")

    def shadow_tzname(tz_aware, explicit_key, current_key):
        """R/I shadow: render the opaque zone-name sub-callees, then
        resolveZoneName. Uses the SAME real name renderers as the repo."""
        timezone.activate(pytz.timezone(current_key))
        current_zone = timezone.get_current_timezone_name()
        explicit_zone = (timezone._get_timezone_name(pytz.timezone(explicit_key))
                         if explicit_key else None)
        timezone.deactivate()
        return shadow_resolve(tz_aware, explicit_zone, current_zone)

    def fuzz_inputs(n, rng):
        utc, other = 'UTC', 'America/New_York'
        # boundary cases first (plan §4.1 step 4)
        yield (True, None, utc)        # aware, no explicit -> ambient
        yield (True, other, utc)       # aware, explicit differs -> explicit (the bug)
        yield (True, other, other)     # aware, explicit == ambient
        yield (True, utc, other)       # aware, explicit == UTC
        yield (False, None, utc)       # not aware -> None
        yield (False, other, utc)      # not aware, explicit present -> still None
        for _ in range(n):
            tz_aware = rng.random() < 0.7
            current_key = rng.choice(ZONE_KEYS)
            explicit_key = None if rng.random() < 0.45 else rng.choice(ZONE_KEYS)
            yield (tz_aware, explicit_key, current_key)

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for tz_aware, explicit_key, current_key in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_tzname(tz_aware, explicit_key, current_key)
        od = oracle_tzname(TruncDate, tz_aware, explicit_key, current_key)
        ot = oracle_tzname(TruncTime, tz_aware, explicit_key, current_key)
        if shadow != od:
            disagreements.append(("TruncDate", tz_aware, explicit_key,
                                  current_key, shadow, od))
        if shadow != ot:
            disagreements.append(("TruncTime", tz_aware, explicit_key,
                                  current_key, shadow, ot))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for which, a, e, c, sh, orc in disagreements:
            print("  %s aware=%r explicit=%r current=%r shadow=%r oracle=%r"
                  % (which, a, e, c, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of dateCastZoneName/timeCastZoneName agrees "
          "with patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
