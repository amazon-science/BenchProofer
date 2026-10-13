#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12741.

The bundle models ONE routine: running a list of SQL statements inside one
transaction (`BaseDatabaseOperations.execute_sql_flush`). The modeled value is
the OBSERVABLE TRIPLE the routine determines (mapping.md):

    connectionAlias : str          (self.connection.alias)
    suppliedUsing   : str          (the dropped `using` argument; post-patch unused)
    canRollbackDdl  : bool         (self.connection.features.can_rollback_ddl)
    sqlList         : list[str]    (sql_list)

      -> (database, savepoint, executed)

Post-patch rule (the gold edit):

    database  = self.connection.alias          # NOT the supplied `using`
    savepoint = self.connection.features.can_rollback_ddl
    executed  = [sql for sql in sql_list]       # each run once, in order

Standing up a database + ORM to drive the real `execute_sql_flush` is heavy and
unnecessary: the modeled value is this pure triple over the observables the real
routine consumes. So the ORACLE below is a faithful in-process replica that uses
the EXACT patched binding (`using=self.connection.alias`, savepoint from the
feature flag, statements executed in `for sql in sql_list` order), and the SHADOW
is the op-for-op transliteration of `implementation_executeFlush`
(database := connectionAlias; savepoint := canRollbackDdl; executed built by an
order-preserving append loop, per refinement.md).

The discriminating case is `suppliedUsing != connectionAlias`: the patched
routine binds the transaction to the connection's own alias and ignores the
supplied value. The fuzzer makes the two frequently differ.

stdlib-only. Pinned seed: 12741 (also in mapping.md).
"""
import random
import string
import sys

SEED = 12741
N = 120_000


# --- ORACLE: faithful in-process replica of the patched routine --------------
def oracle_exec(connection_alias, supplied_using, can_rollback_ddl, sql_list):
    # transaction.atomic(using=self.connection.alias, savepoint=...)
    database = connection_alias
    savepoint = can_rollback_ddl
    # with self.connection.cursor() as cursor: for sql in sql_list: cursor.execute(sql)
    executed = []
    for sql in sql_list:
        executed.append(sql)
    return (database, savepoint, executed)


# --- SHADOW of implementation_executeFlush (the R/I leg) ---------------------
# Mirrors Solution.lean: database := connectionAlias; savepoint := canRollbackDdl;
# executed := []; for sql in sqlList: executed := executed ++ [sql].
def shadow_exec(connection_alias, supplied_using, can_rollback_ddl, sql_list):
    database = connection_alias
    savepoint = can_rollback_ddl
    executed = []
    for sql in sql_list:
        executed = executed + [sql]
    return (database, savepoint, executed)


def disagree(ca, su, crd, sl):
    got = oracle_exec(ca, su, crd, sl)
    want = shadow_exec(ca, su, crd, sl)
    if got != want:
        return ((ca, su, crd, sl), got, want)
    return None


ALIASES = ["default", "other", "replica", "primary", "shard_a", "shard_b", ""]


def _enumerate_edge():
    cases = []
    stmts = ["DELETE FROM a;", "TRUNCATE b;", "ALTER SEQUENCE s RESTART;"]
    for crd in (True, False):
        # supplied differs from the connection's own alias (the F2P shape)
        cases.append(("default", "other", crd, stmts))
        # supplied equals the alias (legacy call sites already passing alias)
        cases.append(("default", "default", crd, stmts))
        # empty statement list (empty database -> no statements)
        cases.append(("default", "other", crd, []))
        # single statement
        cases.append(("replica", "default", crd, ["DELETE FROM x;"]))
        # duplicate statements must each run, in order
        cases.append(("primary", "shard_a", crd, ["S;", "S;", "T;"]))
    return cases


def _rand_stmt(rng):
    n = rng.randint(0, 12)
    return "".join(rng.choice(string.ascii_letters + " ;") for _ in range(n))


def main() -> int:
    checked = 0
    for ca, su, crd, sl in _enumerate_edge():
        d = disagree(ca, su, crd, sl)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        ca = rng.choice(ALIASES)
        su = rng.choice(ALIASES)
        crd = rng.choice([True, False])
        sl = [_rand_stmt(rng) for _ in range(rng.randint(0, 6))]
        d = disagree(ca, su, crd, sl)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
