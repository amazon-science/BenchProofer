#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15252 (nagini).

SHADOW: the impl region of model.py's ``migrate``, copied VERBATIM below with
only the contract calls (Requires / Ensures) stripped. The one @Pure helper
``no_pending_records`` copies over as a plain function; the ``Executor``
constructor copies over with its Ensures stripped (three plain boolean
fields). There are no @ContractOnly callees (mapping.md section 3: no
consumed axioms).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 -- ``django.db.migrations.executor.MigrationExecutor.migrate``.
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH to the testbed, so the import resolves to the patched module.
Each probe runs the real ``migrate`` and reads back exactly the three
observations mapping.md section 2 pins:

  * ``table_present``  -- controlled by the probe: the recorder's
    ``has_table()`` answer (a read-only boolean query result);
  * ``schema_ensured`` -- whether the recorder's ``ensure_schema()`` (the
    table-ensuring WRITE effect) was invoked during the call;
  * ``records_read``   -- whether execution reached the normal record-reading
    result assembly (mapping.md: True on every path that reaches the normal
    tail; False only on the early return that assembles the result without
    touching the connection). Observed by aborting the real tail at its
    first statement (``migration_plan``) with a sentinel exception: the
    sentinel fires iff the tail was reached; a normal return means the
    early-return path ran.

The primary oracle instruments the two consulted recorder primitives (the
same reduction mapping.md section 3 documents, and the same shape the F2P
observation uses); the surrounding ``migrate`` body is the real patched
code, unmodified. A secondary END-TO-END check additionally runs the real
``migrate`` against a REAL sqlite database (real recorder, real introspection,
real schema editor; call-through counting wrappers only) on all six
canonical work-list-shape x table-existence combinations, including the
zero-write / zero-read observation on the no-touch path.

TYPE BRIDGE (mapping.md section 2): the model's work-list carrier is
``Optional[List[int]]`` -- only presence (``is None``) and emptiness
(``== []``) are ever observed. It lowers to the repo's ``plan`` keyword:
``None`` -> ``None``; a list of n integer tokens -> a list of n real
``(Migration, backwards?)`` tuples (token parity supplies the backwards
flag; the tokens are opaque, as documented). ``table_present`` needs no
bridge (bool -> bool).

INPUT PLAN (>= 1e5 Requires-satisfying inputs): every (Optional[List[int]],
bool) pair satisfies the precondition. Boundary shapes (None, the empty
list, singletons of varied token values, duplicate tokens, long lists,
extreme token magnitudes) each crossed with both table states, plus 100000
random fuzz pairs over shape {None, empty, non-empty} x length 0..12 x
token range x both table states. Pinned fuzz seed: 15252. Exit 0 iff zero
disagreements; on disagreement prints the input and both outputs and exits
1. stdlib only.
"""
import json
import random
import sys

SEED = 15252
N_FUZZ = 100000


# --- shadow Executor: model.py's minimal class, Ensures stripped -------------

class Executor(object):
    def __init__(self, table_present):
        self.table_present = table_present          # type: bool
        self.schema_ensured = False                 # type: bool
        self.records_read = False                   # type: bool


# --- pure region of model.py, contracts stripped ------------------------------

def no_pending_records(pending):
    # This connection has NO migrations to record: the argument is present (not
    # None) and conveys no recording work (a present, length-zero carrier). A
    # None argument is 'undetermined' (yet to be computed), NOT a determination
    # that there are none.
    return pending is not None and len(pending) == 0


# --- impl region of model.py, verbatim, contract calls stripped ---------------

def migrate(executor, pending):
    if no_pending_records(pending):
        if not executor.table_present:
            # No migrations to record and no table present: assemble the result
            # without touching the connection (no write, no read).
            return
        # Table already present: fall through to the read-assembly path below;
        # no write effect on this branch.
    else:
        executor.schema_ensured = True
    executor.records_read = True
    return


def shadow_observe(pending, table_present):
    ex = Executor(table_present)
    migrate(ex, pending)
    return (ex.schema_ensured, ex.records_read)


# --- oracle: the real patched repo function -----------------------------------

def _django_setup():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


class _TailReached(Exception):
    """Sentinel: the real migrate proceeded past its prologue into the
    record-reading result assembly (whose first statement is a
    migration_plan computation on every non-early-return path)."""


class _Oracle(object):
    """Runs the REAL patched MigrationExecutor.migrate per probe, with the
    two consulted recorder primitives replaced by the observation doubles
    mapping.md section 3 documents (has_table -> the controlled boolean;
    ensure_schema -> an invocation flag), and the tail aborted at its first
    statement so each of >=1e5 probes stays cheap."""

    def __init__(self):
        from django.db.migrations.executor import MigrationExecutor
        from django.db.migrations import Migration
        self._ex = MigrationExecutor(None)
        self._flags = {"ensure": False, "table": False}
        flags = self._flags

        class RecorderDouble(object):
            def has_table(self):
                return flags["table"]

            def ensure_schema(self):
                flags["ensure"] = True

        self._ex.recorder = RecorderDouble()

        def _abort_tail(*args, **kwargs):
            raise _TailReached()

        self._ex.migration_plan = _abort_tail
        # reusable real Migration instances for the plan bridge (the tokens
        # are opaque per mapping.md; elements are never consulted before the
        # sentinel point)
        self._mig_fwd = Migration("0001_tok", "bridgeapp")
        self._mig_bwd = Migration("0002_tok", "bridgeapp")

    def bridge_plan(self, pending):
        """Optional[List[int]] -> the repo plan argument."""
        if pending is None:
            return None
        return [((self._mig_bwd, True) if tok % 2 else (self._mig_fwd, False))
                for tok in pending]

    def observe(self, pending, table_present):
        self._flags["ensure"] = False
        self._flags["table"] = table_present
        plan = self.bridge_plan(pending)
        try:
            self._ex.migrate([], plan=plan)
            tail_reached = False   # early return: result assembled with no
            #                        record-reading query
        except _TailReached:
            tail_reached = True
        return (self._flags["ensure"], tail_reached)


# --- secondary end-to-end oracle: real sqlite DB, call-through wrappers -------

def real_db_check():
    """Run the real patched migrate against a REAL sqlite database on all six
    canonical combinations. Counting wrappers call through to the real
    recorder methods; nothing is stubbed. Non-empty plans use all-forwards
    dummy migrations absent from the (empty) graph, so the real tail runs to
    completion without applying anything. Returns an error string or None."""
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations import Migration
    from django.db.migrations.recorder import MigrationRecorder

    def set_table(present):
        rec = MigrationRecorder(connection)
        if present and not rec.has_table():
            rec.ensure_schema()
        elif not present and rec.has_table():
            with connection.schema_editor() as editor:
                editor.delete_model(rec.Migration)

    for pending in (None, [], [3], [4, 6]):
        plan = (None if pending is None
                else [(Migration("000%d_e2e" % (i + 1), "e2eapp"), False)
                      for i in range(len(pending))])
        for table_present in (False, True):
            set_table(table_present)
            ex = MigrationExecutor(connection)
            counts = {"ensure": 0, "reads": 0}
            rec = ex.recorder
            real_ensure = rec.ensure_schema
            real_applied = rec.applied_migrations

            def ensure_schema(_r=real_ensure, _c=counts):
                _c["ensure"] += 1
                return _r()

            def applied_migrations(_r=real_applied, _c=counts):
                _c["reads"] += 1
                return _r()

            rec.ensure_schema = ensure_schema
            rec.applied_migrations = applied_migrations
            ex.migrate([], plan=plan)
            real_obs = (counts["ensure"] > 0, counts["reads"] > 0)
            shadow_obs = shadow_observe(pending, table_present)
            if real_obs != shadow_obs:
                return ("E2E DISAGREEMENT at pending=%r table_present=%r:\n"
                        "  shadow (schema_ensured, records_read) = %r\n"
                        "  real   (ensure invoked, records read) = %r"
                        % (pending, table_present, shadow_obs, real_obs))
            if pending == [] and not table_present:
                # the no-touch path must leave the bookkeeping table absent
                if MigrationRecorder(connection).has_table():
                    return ("E2E DISAGREEMENT at pending=[] table_present="
                            "False: the real run left the bookkeeping table "
                            "present (a write effect the shadow forbids)")
    return None


# --- input generation ----------------------------------------------------------

BOUNDARY_PENDING = [
    None,                    # undetermined work list
    [],                      # determined: nothing to record (the trigger)
    [0], [1], [2], [-1],     # singletons, both parities, negative token
    [0, 0], [1, 1],          # duplicate tokens
    [0, 1], [1, 0],          # mixed parities
    list(range(10)),
    [10 ** 9], [-10 ** 9],   # extreme token magnitudes
    [7] * 50,
    list(range(200)),        # long work list
]


def main():
    _django_setup()

    err = real_db_check()
    if err:
        print(err)
        return 1

    oracle = _Oracle()
    checked = 0

    def check(pending, table_present):
        shadow = shadow_observe(pending, table_present)
        real = oracle.observe(pending, table_present)
        if shadow != real:
            return ("DISAGREEMENT at pending=%r table_present=%r:\n"
                    "  shadow (schema_ensured, records_read) = %r\n"
                    "  real   (ensure invoked, tail reached) = %r"
                    % (pending, table_present, shadow, real))
        return None

    for pending in BOUNDARY_PENDING:
        for flag in (False, True):
            err = check(pending, flag)
            if err:
                print(err)
                return 1
            checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        shape = rng.random()
        if shape < 0.25:
            pending = None
        elif shape < 0.5:
            pending = []
        else:
            n = rng.randint(1, 12)
            pending = [rng.randint(-10 ** 6, 10 ** 6) for _ in range(n)]
        table_present = rng.random() < 0.5
        err = check(pending, table_present)
        if err:
            print(err)
            return 1
        checked += 1

    print("PASS: shadow == real patched migrate observations on %d inputs "
          "(%d boundary x 2 + %d fuzz; pinned seed %d) plus 8 end-to-end "
          "real-database combinations; 0 disagreements."
          % (checked, len(BOUNDARY_PENDING), N_FUZZ, SEED))
    print(json.dumps({"status": "pass", "checked": checked,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
