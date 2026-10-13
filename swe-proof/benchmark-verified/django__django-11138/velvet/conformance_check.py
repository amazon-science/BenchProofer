#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11138 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`buildTzAdjustedExpr` / `tzAdjustedExpr`) transliterated to
              Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Bool` ↔ `settings.USE_TZ`).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.backends.mysql.operations.DatabaseOperations
               ._convert_field_to_tz` applied at base_commit (the real
              correctness oracle, G-RESOLVE). It reads `settings.USE_TZ` and
              `self.connection.timezone_name` (the stored zone) and emits the
              `CONVERT_TZ(...)` wrapping, or the field expression verbatim.

The impl region has NO A-tagged content (no axiomatized callees), so the shadow
is pure R/I. They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django
(already installed). The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

SEED = 11138
N_FUZZ = 100_000


def shadow_build(active, expr, query_zone, stored_zone):
    """buildTzAdjustedExpr transliterated: the per-input string computation of
    tzAdjustedExpr (mapping.md §2). `active` is settings.USE_TZ; `expr` is the
    field expression; `query_zone`/`stored_zone` are the target/source zones."""
    if active and stored_zone != query_zone:
        return "CONVERT_TZ(%s, '%s', '%s')" % (expr, stored_zone, query_zone)
    return expr


def _make_oracle():
    """Build the ORACLE callable around the patched MySQL _convert_field_to_tz.

    The method reads only `settings.USE_TZ` and `self.connection.timezone_name`,
    so we attach a minimal fake connection and toggle settings.USE_TZ per call.
    Importing the module exercises the *patched* repo source (the harness has
    applied patch.diff at base_commit before this runs)."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_TZ=True, TIME_ZONE='UTC')
    from django.db.backends.mysql.operations import DatabaseOperations

    class _FakeConn:
        def __init__(self):
            self.timezone_name = 'UTC'

    ops = DatabaseOperations.__new__(DatabaseOperations)
    ops.connection = _FakeConn()

    def oracle(active, expr, query_zone, stored_zone):
        settings.USE_TZ = active
        ops.connection.timezone_name = stored_zone
        return ops._convert_field_to_tz(expr, query_zone)

    return oracle


def rand_zone(rng):
    zones = [
        'UTC', 'Europe/Paris', 'Africa/Nairobi', 'Asia/Bangkok',
        'America/New_York', 'Australia/Sydney', 'Etc/GMT+5', 'GMT',
    ]
    return rng.choice(zones)


def rand_expr(rng):
    cols = ['`my_model`.`dt`', '`t`.`field_name`', 'col', '`a`.`b`.`c`',
            'DATE(`x`)', '`my_datetime_field`']
    return rng.choice(cols)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): support on/off crossed with
    # zones equal/different, mirroring the issue's two scenarios.
    yield (True, '`m`.`dt`', 'Europe/Paris', 'Europe/Paris')   # equal -> verbatim
    yield (True, '`m`.`dt`', 'Europe/Paris', 'UTC')            # differ -> wrap
    yield (False, '`m`.`dt`', 'Europe/Paris', 'UTC')           # support off -> verbatim
    yield (False, '`m`.`dt`', 'Europe/Paris', 'Europe/Paris')  # support off, equal
    yield (True, '`m`.`dt`', 'Africa/Nairobi', 'Africa/Nairobi')
    yield (True, '`m`.`dt`', 'America/New_York', 'Asia/Bangkok')
    for _ in range(n):
        active = rng.random() < 0.7
        expr = rand_expr(rng)
        query_zone = rand_zone(rng)
        # ~40% of the time make the two zones identical to exercise the skip leg
        stored_zone = query_zone if rng.random() < 0.4 else rand_zone(rng)
        yield (active, expr, query_zone, stored_zone)


def main():
    rng = random.Random(SEED)
    oracle = _make_oracle()
    disagreements = []
    count = 0
    for active, expr, query_zone, stored_zone in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_build(active, expr, query_zone, stored_zone)
        orc = oracle(active, expr, query_zone, stored_zone)
        if shadow != orc:
            disagreements.append((active, expr, query_zone, stored_zone, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for a, e, q, s, sh, orc in disagreements:
            print("  active=%r expr=%r query=%r stored=%r shadow=%r oracle=%r"
                  % (a, e, q, s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildTzAdjustedExpr agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
