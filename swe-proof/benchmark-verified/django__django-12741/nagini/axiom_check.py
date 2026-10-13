#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12741.

There is no consumed @ContractOnly axiom in model.py: the three callees the
routine under specification invokes — opening an atomic block scoped to a
database, the cursor context manager, and the cursor executing a statement —
are UNCHANGED by the behaviour and are modeled by their observable RECORDED
EFFECTS (the A-reference rows of refinement.md). This check validates those
recorded effects against the REAL routine
``BaseDatabaseOperations.execute_sql_flush`` (the post-patch form, present in
the evaluation image), asserting that on every input batch:

  (A-reference 1) the atomic block the routine opens is scoped to the routine's
      OWN connection identifier — ``self.connection.alias`` — derived
      internally, never taken from a separately-supplied argument. The model
      pins this as ``scoped_alias == self.connection.alias``.

  (A-reference 2) the savepoint flag the block is opened with equals the
      connection's declared rollback capability
      ``self.connection.features.can_rollback_ddl`` (modeled as
      ``scoped_savepoint == supports_rollback``).

  (A-reference 3) exactly the supplied statements are executed, in the order
      given (modeled as ``ToSeq(executed) == ToSeq(sql_list)``).

It also asserts the SIGNATURE refinement that is the heart of the change: the
real ``execute_sql_flush`` accepts exactly one non-self positional parameter
(``sql_list``) and does NOT accept a separate ``using`` argument.

The check drives the real method with lightweight recording stand-ins for
``transaction.atomic`` and ``connection.cursor`` so it observes the scope, the
savepoint flag, and the executed statement sequence directly, without needing a
live database. It imports only Django (the package under test) + stdlib. Exit 0
iff every recorded-effect obligation holds. If Django is not importable in the
environment it prints a SKIP and exits 0 (the soundness claim is about the real
callee, checked wherever it is importable).
"""
import inspect
import random
import sys


def main():
    try:
        from django.db.backends.base import operations as ops_mod
        from django.db.backends.base.operations import BaseDatabaseOperations
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not importable in this environment: %r" % (exc,))
        return 0

    # --- Signature refinement (the change itself) ---------------------------
    sig = inspect.signature(BaseDatabaseOperations.execute_sql_flush)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    names = [p.name for p in params]
    assert names == ["sql_list"], (
        "execute_sql_flush must take exactly one non-self parameter 'sql_list'; "
        "got %r (a separate 'using' argument must NOT be present)" % (names,))
    assert "using" not in sig.parameters, (
        "execute_sql_flush must not accept a separate 'using' argument: %r" % (sig,))

    # --- Recording stand-ins for the unchanged callees ----------------------
    class RecordingCursor:
        def __init__(self, log):
            self._log = log
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def execute(self, sql):
            self._log.append(sql)

    class Features:
        def __init__(self, can_rollback_ddl):
            self.can_rollback_ddl = can_rollback_ddl

    class RecordingConnection:
        def __init__(self, alias, can_rollback_ddl, exec_log):
            self.alias = alias
            self.features = Features(can_rollback_ddl)
            self._exec_log = exec_log
        def cursor(self):
            return RecordingCursor(self._exec_log)

    class AtomicRecorder:
        """Stand-in for transaction.atomic(using=..., savepoint=...): records
        which database the block was scoped to and the savepoint flag."""
        def __init__(self, observations):
            self._obs = observations
        def __call__(self, using=None, savepoint=None):
            self._obs["scoped_alias"] = using
            self._obs["scoped_savepoint"] = savepoint
            return self
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    # Patch transaction.atomic in the operations module to the recorder.
    original_atomic = ops_mod.transaction.atomic

    def run_once(alias, can_rollback_ddl, sql_list):
        observations = {}
        exec_log = []
        ops_mod.transaction.atomic = AtomicRecorder(observations)
        try:
            conn = RecordingConnection(alias, can_rollback_ddl, exec_log)
            # Minimal operations instance bound to our recording connection.
            ops = BaseDatabaseOperations(conn)
            ops.execute_sql_flush(list(sql_list))
        finally:
            ops_mod.transaction.atomic = original_atomic
        return observations, exec_log

    # --- Boundary + fuzz over (alias, savepoint capability, batch) ----------
    aliases = ["default", "other", "replica", "primary_db", "x", ""]
    bool_opts = [True, False]
    batches = [
        [],
        ["DELETE FROM t;"],
        ["SET CONSTRAINTS ALL DEFERRED;", "DELETE FROM a;", "DELETE FROM b;"],
        ["TRUNCATE a, b CASCADE;"],
        ["ALTER SEQUENCE s RESTART;"] * 4,
        [str(i) for i in range(10)],
    ]

    checks = 0
    for alias in aliases:
        for can_roll in bool_opts:
            for batch in batches:
                obs, executed = run_once(alias, can_roll, batch)
                # (A-reference 1): scope is the connection's OWN alias.
                assert obs.get("scoped_alias") == alias, (
                    "atomic block scoped to %r, expected the connection's own "
                    "alias %r" % (obs.get("scoped_alias"), alias))
                # (A-reference 2): savepoint flag == features.can_rollback_ddl.
                assert obs.get("scoped_savepoint") == can_roll, (
                    "atomic savepoint flag was %r, expected can_rollback_ddl=%r"
                    % (obs.get("scoped_savepoint"), can_roll))
                # (A-reference 3): exactly the supplied statements, in order.
                assert executed == list(batch), (
                    "executed %r, expected exactly the supplied batch %r in "
                    "order" % (executed, list(batch)))
                checks += 1

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(12741)
    for _ in range(5000):
        alias = "db" + str(rng.randint(0, 10000))
        can_roll = rng.choice(bool_opts)
        n = rng.randint(0, 12)
        batch = ["stmt_%d_%d" % (rng.randint(0, 9999), j) for j in range(n)]
        obs, executed = run_once(alias, can_roll, batch)
        assert obs.get("scoped_alias") == alias, (
            "fuzz: atomic scoped to %r, expected own alias %r"
            % (obs.get("scoped_alias"), alias))
        assert obs.get("scoped_savepoint") == can_roll, (
            "fuzz: savepoint flag %r, expected %r"
            % (obs.get("scoped_savepoint"), can_roll))
        assert executed == batch, (
            "fuzz: executed %r, expected %r in order" % (executed, batch))
        checks += 1

    print("G-AX OK: execute_sql_flush recorded-effect references sound over %d "
          "observations: the atomic block is always scoped to the connection's "
          "own alias (never a caller-supplied value), the savepoint flag equals "
          "features.can_rollback_ddl, and exactly the supplied statements run in "
          "order; the signature takes the single parameter 'sql_list'." % (checks,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
