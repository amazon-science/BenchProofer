#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12741 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`runBatch`)
              transliterated to Python over the real repo types, via the
              mapping.md bijection (`Connection.ownAlias` ↔ a str alias;
              `sqlList` ↔ a list[str]). The modeled operation opens the scoped
              batch under the connection's OWN identifier and replays the
              statement list unchanged, in order. `suppliedKey` (the identifier
              handed in alongside the statements) is read-only and does NOT
              enter the result.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `BaseDatabaseOperations.execute_sql_flush(sql_list)` at base_commit
              with the gold patch applied, invoked against a fake connection
              whose `.alias` we control and with `transaction.atomic` / the
              cursor stubbed to RECORD the two observables the modeled slice
              exposes — the `using=` key the scope is opened under and the
              statements replayed through the cursor. This is the real
              correctness oracle (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + django only. The fuzz seed is pinned (mapping.md §4).
"""
import contextlib
import random
import sys

SEED = 12741
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean runBatch, transliterated ------------------
def shadow_run(conn_alias, supplied_key, sql_list):
    """`runBatch` transliterated: open the scope under the connection's OWN
    identifier (`conn.ownAlias`), replay the statement list unchanged. The
    supplied key is deliberately unused (directive 5)."""
    opened_under = conn_alias              # out.1 = conn.ownAlias
    replayed = list(sql_list)              # out.2 = sqlList
    return (opened_under, replayed)


# --- the oracle: patch.diff's real behaviour ---------------------------------
def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={},
            INSTALLED_APPS=[],
            USE_TZ=False,
        )
    django.setup()


class _RecordingCursor:
    def __init__(self, sink):
        self._sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._sink.append(sql)


class _FakeFeatures:
    can_rollback_ddl = False


class _FakeConnection:
    """Minimal stand-in for the BaseDatabaseWrapper the ops object is bound to.
    Carries its OWN identifier (`alias`) — exactly the field the patched code
    sources the `using=` key from."""
    def __init__(self, alias, executed_sink):
        self.alias = alias
        self.features = _FakeFeatures()
        self._executed = executed_sink

    def cursor(self):
        return _RecordingCursor(self._executed)


def oracle_run(conn_alias, supplied_key, sql_list):
    """ORACLE: the REAL patched execute_sql_flush. We record the `using=` key the
    patched body opens `transaction.atomic` under, and the statements it replays.
    `supplied_key` is NOT passed (the patched signature dropped it) — its only
    role here is to confirm the oracle, like the shadow, is independent of it."""
    from django.db.backends.base.operations import BaseDatabaseOperations
    from django.db.backends.base import operations as ops_mod

    executed = []
    conn = _FakeConnection(conn_alias, executed)
    ops = BaseDatabaseOperations(conn)

    captured = {}

    @contextlib.contextmanager
    def _recording_atomic(using=None, savepoint=True):
        captured["using"] = using
        yield

    real_atomic = ops_mod.transaction.atomic
    ops_mod.transaction.atomic = _recording_atomic
    try:
        # Patched signature: execute_sql_flush(self, sql_list).
        ops.execute_sql_flush(list(sql_list))
    finally:
        ops_mod.transaction.atomic = real_atomic

    return (captured.get("using"), executed)


def fuzz_inputs(n, rng):
    aliases = ["default", "other", "replica", "test_default", "", "db-1",
               "ConnAlias", "x", "primary", "蓝色"]
    sql_atoms = [
        "DELETE FROM t;", "TRUNCATE \"app_model\";", "SET FOREIGN_KEY_CHECKS=0;",
        "ALTER SEQUENCE s RESTART;", "", "SELECT 1;", "DELETE FROM \"a b\";",
    ]
    # boundary cases first (plan §4.1 step 4)
    yield ("default", "default", [])
    yield ("default", "default", ["DELETE FROM t;"])
    yield ("default", "other", ["DELETE FROM t;"])      # supplied_key != alias
    yield ("other", "default", ["A;", "B;", "C;"])       # supplied_key != alias
    yield ("", "nonempty", ["X;"])
    yield ("alias-with-unicode-蓝", "default", ["蓝;"])
    for _ in range(n):
        a = rng.choice(aliases)
        k = rng.choice(aliases)              # supplied key, often != alias
        m = rng.randint(0, 6)
        sql = [rng.choice(sql_atoms) for _ in range(m)]
        yield (a, k, sql)


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for conn_alias, supplied_key, sql_list in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_run(conn_alias, supplied_key, sql_list)
        oracle = oracle_run(conn_alias, supplied_key, sql_list)
        # Compare the two observables: opened-under identifier and replayed list.
        if list(shadow[1]) != list(oracle[1]) or shadow[0] != oracle[0]:
            disagreements.append(((conn_alias, supplied_key, sql_list),
                                  shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of runBatch agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
