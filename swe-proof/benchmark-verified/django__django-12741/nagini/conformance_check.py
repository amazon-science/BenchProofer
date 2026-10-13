#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12741 (nagini).

SHADOW: the impl region of model.py `execute_statement_batch`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant) stripped, running on
plain-Python twins of the model's `Connection` / `DatabaseOperations` classes
(their __init__ bodies copied verbatim minus contracts). The impl region is
plain Python over ints/bools/lists, so it executes directly — no
transliteration. There are no @Pure helpers and no @ContractOnly callees in
this model.

ORACLE: the REAL patched repo routine the model models per mapping.md —
`django.db.backends.base.operations.BaseDatabaseOperations.execute_sql_flush`.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable. The routine is driven
exactly as in axiom_check.py: a recording stand-in replaces
`transaction.atomic` in the operations module (capturing which database the
atomic block was scoped to and its savepoint flag), and a recording
connection/cursor captures the ordered statement sequence executed. This
isolates precisely the modeled observable behaviour: (scope of the block,
savepoint flag, executed statement sequence) for a given
(connection identifier, rollback capability, statement batch) triple.

Type bridge (mapping.md section 2): the repo's database alias is a `str`
observed only by identity; the model carries it as an opaque `int`. The repo's
SQL statements are `str`s observed only by being executed in order; the model
carries them as opaque `int` tokens. Both are bridged by the injective maps
alias_str / stmt_str below (int -> distinct str); identity and order are
preserved in both directions, which is exactly what the model relies on. The
capability flag is `bool` on both sides. The model's `caller_alias` field
stands for an externally-supplied identifier that the post-change routine does
not consume; it is fuzzed independently and passed only to the shadow (the
real routine's signature has no such parameter — asserted by G-AX).

Input domain: the Requires of `execute_statement_batch` are pure access
permissions, so every (alias, supports_rollback, caller_alias, sql_list)
tuple over ints/bool/int-lists is Requires-satisfying. Boundary cases cover
zero/negative/large identifiers, empty/singleton/duplicate-heavy batches, and
both capability values; the fuzz layer randomizes all four components.

>= 1e5 Requires-satisfying inputs: 192 boundary cases + 100000 fuzz tuples.
Pinned fuzz seed: 12741.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib only.
"""
import random
import sys

SEED = 12741
N_FUZZ = 100_000


# --- plain-Python twins of the model classes (contract calls stripped) -------

class Connection:
    def __init__(self, alias, supports_rollback, caller_alias):
        self.alias = alias                       # the connection's own database identifier
        self.supports_rollback = supports_rollback # declared rollback-savepoint capability
        self.caller_alias = caller_alias         # a database identifier supplied externally (caller-threaded)
        self.scoped_alias = 0                    # recorder: database the atomic block ran under
        self.scoped_savepoint = False            # recorder: savepoint flag the block opened with
        self.executed = []                       # recorder: statements executed, in order


class DatabaseOperations:
    def __init__(self, connection):
        self.connection = connection


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def execute_statement_batch(self, sql_list):
    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed


# --- type bridge: opaque int identifiers <-> distinct strings ----------------

def alias_str(n):
    return "alias_%d" % (n,)


def stmt_str(n):
    return "stmt_%d" % (n,)


def main():
    try:
        from django.db.backends.base import operations as ops_mod
        from django.db.backends.base.operations import BaseDatabaseOperations
    except Exception as exc:
        print("G-CONF ERROR: cannot import the repo module under test: %r" % (exc,))
        return 1

    # Recording stand-ins for the real routine's environment (same technique
    # as axiom_check.py): capture the observable effects the model records.
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

    original_atomic = ops_mod.transaction.atomic

    def oracle_once(alias_int, can_roll, batch_ints):
        observations = {}
        exec_log = []
        ops_mod.transaction.atomic = AtomicRecorder(observations)
        try:
            conn = RecordingConnection(alias_str(alias_int), can_roll, exec_log)
            ops = BaseDatabaseOperations(conn)
            ops.execute_sql_flush([stmt_str(t) for t in batch_ints])
        finally:
            ops_mod.transaction.atomic = original_atomic
        return observations, exec_log

    def shadow_once(alias_int, can_roll, caller_int, batch_ints):
        conn = Connection(alias_int, can_roll, caller_int)
        ops = DatabaseOperations(conn)
        execute_statement_batch(ops, list(batch_ints))
        return conn

    def check_one(alias_int, can_roll, caller_int, batch_ints):
        conn = shadow_once(alias_int, can_roll, caller_int, batch_ints)
        obs, executed = oracle_once(alias_int, can_roll, batch_ints)
        # (1) scope of the atomic block, bridged through alias_str.
        shadow_scope = alias_str(conn.scoped_alias)
        real_scope = obs.get("scoped_alias")
        # (2) savepoint flag.
        shadow_sp = conn.scoped_savepoint
        real_sp = obs.get("scoped_savepoint")
        # (3) executed sequence, bridged through stmt_str elementwise.
        shadow_exec = [stmt_str(t) for t in conn.executed]
        if (shadow_scope != real_scope or shadow_sp is not real_sp
                or shadow_exec != executed):
            print("DISAGREEMENT")
            print("  input: alias=%r supports_rollback=%r caller_alias=%r "
                  "sql_list=%r" % (alias_int, can_roll, caller_int, batch_ints))
            print("  shadow: scoped_alias=%r (bridged %r) scoped_savepoint=%r "
                  "executed=%r (bridged %r)"
                  % (conn.scoped_alias, shadow_scope, shadow_sp,
                     conn.executed, shadow_exec))
            print("  repo:   scoped_alias=%r scoped_savepoint=%r executed=%r"
                  % (real_scope, real_sp, executed))
            return False
        return True

    checks = 0

    # --- boundary layer -------------------------------------------------
    boundary_aliases = [0, 1, -1, 2, 7, 10**9, -(10**9), 12741]
    boundary_batches = [
        [],
        [0],
        [1],
        [-5],
        [3, 3, 3],
        [1, 2, 3, 4, 5],
        list(range(10)),
        [10**9, -(10**9), 0],
        [12741] * 6,
        [5, 4, 3, 2, 1, 0],
        [2, 2, 1, 1, 2],
        list(range(50)),
    ]
    for alias in boundary_aliases:
        for can_roll in (True, False):
            for batch in boundary_batches:
                # exercise caller identifiers both equal and unequal to alias
                caller = alias if (checks % 2 == 0) else alias + 1
                if not check_one(alias, can_roll, caller, batch):
                    return 1
                checks += 1

    # --- fuzz layer (pinned seed) ----------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        alias = rng.randint(-10**6, 10**6)
        can_roll = rng.random() < 0.5
        caller = rng.randint(-10**6, 10**6)
        n = rng.randint(0, 16)
        batch = [rng.randint(-10**6, 10**6) for _ in range(n)]
        if not check_one(alias, can_roll, caller, batch):
            return 1
        checks += 1

    print("G-CONF OK: shadow == patched repo routine over %d inputs "
          "(scope of the atomic block, savepoint flag, and executed statement "
          "sequence all agree; seed=%d)" % (checks, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
