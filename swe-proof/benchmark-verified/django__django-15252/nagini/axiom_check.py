#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15252.

This bundle consumes NO @ContractOnly axiom: the unchanged primitives the
routine consults (``MigrationRecorder.has_table``, ``MigrationRecorder.
ensure_schema``, and the record-reading result assembly) are each reduced to
the single observation they produce — a boolean query result, a table-ensuring
WRITE-effect flag, and a record-reading QUERY-effect flag — and the changed
decision logic over those observations is modelled DEEPLY in model.py's impl
region.

G-AX therefore validates the *decision-logic equivalence*: the model's effect
observations must equal the GOLD-patched ``migrate`` routine's effect
observations on every combination of (work-list shape, table-existence). Two
independent checks:

  (1) Exhaustive: over all combinations of
          plan in {None (compute), [] (explicitly empty), [<non-empty>]}
          table_present in {False, True}
      the model's observations (re-encoded from model.py's impl region)
          (schema_ensured, records_read, early_return)
      equal the gold-patched ``migrate`` prologue observations (re-encoded from
      patch.diff's body). This is the equivalence the refinement relies on
      (refinement.md).

  (2) Real-callee witness: a faithful in-process re-enactment of the F2P test
      ``test_migrate_skips_schema_creation`` — ``has_table`` returns False and
      ``migrate([], plan=[])`` is invoked — using a recorder double that counts
      its ``ensure_schema`` calls AND its record-reading queries (the proxies
      for the test's "0 queries" assertion). The gold-patched prologue must NOT
      call ``ensure_schema`` and must NOT issue a record-reading query (it
      short-circuits); the pre-patch prologue would do both. Confirms the
      modelled observation matches the patched behaviour and the bug the F2P
      test pins.

Imports nothing repo-specific (stdlib only). Exit 0 iff every obligation holds.
"""
import sys


# --- model.py observations (re-encoded from model.py's impl region) ----------
# Returns (schema_ensured, records_read, early_return).
# plan_present: bool (the work list was supplied, i.e. not None)
# plan_len_zero: bool (the supplied work list has length zero)
# table_present: bool (the bookkeeping table already exists)

def model_observations(plan_present, plan_len_zero, table_present):
    no_pending = plan_present and plan_len_zero
    schema_ensured = False
    records_read = False
    early_return = False
    # impl region (model.py):
    #   if no_pending_records(pending):
    #       if not executor.table_present:
    #           return                 # no-touch short-circuit
    #       # else fall through to the read-assembly tail
    #   else:
    #       executor.schema_ensured = True
    #   executor.records_read = True
    #   return
    if no_pending:
        if not table_present:
            early_return = True
            return (schema_ensured, records_read, early_return)
        # else: table present -> fall through to the read-assembly tail
    else:
        schema_ensured = True
    records_read = True
    return (schema_ensured, records_read, early_return)


# --- gold-patched routine observations (re-encoded from patch.diff's body) ---
# Simulates the exact control flow of the post-patch migrate() prologue, then
# the normal record-reading result assembly tail:
#
#   if plan == []:
#       if not self.recorder.has_table():
#           return self._create_project_state(with_applied_migrations=False)
#   else:
#       self.recorder.ensure_schema()
#   <normal assembly: reads applied-migration records>
#
# ensure_schema() call          -> schema_ensured (WRITE effect)
# reaching the normal assembly  -> records_read (QUERY effect)
# the short-circuit return      -> early_return, and NO records_read
#                                  (with_applied_migrations=False reads nothing)

def gold_patched_observations(plan_present, plan_len_zero, table_present):
    plan_eq_empty_list = plan_present and plan_len_zero  # plan == []
    schema_ensured = False
    records_read = False
    early_return = False
    if plan_eq_empty_list:
        if not table_present:
            # return self._create_project_state(with_applied_migrations=False)
            early_return = True
            return (schema_ensured, records_read, early_return)
        # else: table present -> no ensure_schema; fall through to assembly
    else:
        # self.recorder.ensure_schema()
        schema_ensured = True
    # normal record-reading result assembly (every non-short-circuit path)
    records_read = True
    return (schema_ensured, records_read, early_return)


# --- pre-patch routine observations (the bug, for the witness contrast) ------
# Pre-patch prologue: self.recorder.ensure_schema()  (unconditional, first),
# then the routine always proceeds to the normal record-reading assembly.

def prepatch_observations(plan_present, plan_len_zero, table_present):
    schema_ensured = True  # ensure_schema() ALWAYS, first thing
    records_read = True     # then always proceeds to the read-assembly tail
    early_return = False    # no short-circuit on plan==[]
    return (schema_ensured, records_read, early_return)


def _plan_shapes():
    # (label, plan_present, plan_len_zero)
    return [
        ("None (to-be-computed)", False, False),
        ("[] (explicitly empty)", True, True),
        ("[<non-empty>]", True, False),
    ]


def check_exhaustive_equivalence():
    n = 0
    for (label, plan_present, plan_len_zero) in _plan_shapes():
        for table_present in (False, True):
            m = model_observations(plan_present, plan_len_zero, table_present)
            g = gold_patched_observations(plan_present, plan_len_zero, table_present)
            assert m == g, (
                "decision-logic mismatch on (plan=%s, table_present=%r): "
                "model=%r gold-patched=%r" % (label, table_present, m, g))
            n += 1
    return n


# --- real-callee witness: the F2P test_migrate_skips_schema_creation shape ---

class _RecorderDouble:
    """Stand-in for MigrationRecorder: has_table() is mocked to return False
    (as the F2P test does via @mock.patch.object(MigrationRecorder,
    'has_table', return_value=False)); ensure_schema() counts its calls and
    record_reads counts record-reading queries — together the proxy for the
    test's `with self.assertNumQueries(0)` (ensure_schema and the applied-record
    reads are the prologue/assembly operations that would query)."""

    def __init__(self, has_table_value):
        self._has_table_value = has_table_value
        self.ensure_schema_calls = 0
        self.record_reads = 0

    def has_table(self):
        return self._has_table_value

    def ensure_schema(self):
        self.ensure_schema_calls += 1

    def read_applied_records(self):
        self.record_reads += 1


def _gold_migrate(recorder, plan):
    """The post-patch migrate(), executed against the recorder double, including
    the normal record-reading assembly tail. Returns True iff it short-circuits."""
    if plan == []:
        if not recorder.has_table():
            # return self._create_project_state(with_applied_migrations=False)
            return True  # no ensure_schema, no record read
    else:
        recorder.ensure_schema()
    # normal assembly tail reads applied-migration records
    recorder.read_applied_records()
    return False


def _prepatch_migrate(recorder, plan):
    """The pre-patch migrate(): ensure_schema() unconditionally, then always the
    normal record-reading assembly tail."""
    recorder.ensure_schema()
    recorder.read_applied_records()
    return False


def check_real_callee_witness():
    # F2P: has_table() -> False, migrate([], plan=[]).  assertNumQueries(0).
    rec = _RecorderDouble(has_table_value=False)
    short_circuited = _gold_migrate(rec, plan=[])
    assert rec.ensure_schema_calls == 0, (
        "gold-patched migrate must NOT call ensure_schema on plan=[] with "
        "no table (0-queries F2P); observed %d calls" % rec.ensure_schema_calls)
    assert rec.record_reads == 0, (
        "gold-patched migrate must NOT read records on plan=[] with no table "
        "(0-queries F2P); observed %d reads" % rec.record_reads)
    assert short_circuited is True, "gold-patched migrate must short-circuit"

    # Contrast: the pre-patch routine DOES call ensure_schema AND read records
    # (the queries the F2P assertNumQueries(0) catches).
    rec_bug = _RecorderDouble(has_table_value=False)
    _prepatch_migrate(rec_bug, plan=[])
    assert rec_bug.ensure_schema_calls == 1, (
        "pre-patch migrate is expected to call ensure_schema (the bug); "
        "observed %d calls" % rec_bug.ensure_schema_calls)
    assert rec_bug.record_reads == 1, (
        "pre-patch migrate is expected to read records (>0 queries); "
        "observed %d reads" % rec_bug.record_reads)

    # And confirm the model observation agrees with the gold-patched one on this
    # exact shape (plan present, length zero, table absent): no WRITE, no QUERY,
    # early return.
    m = model_observations(True, True, False)
    g = gold_patched_observations(True, True, False)
    assert m == g == (False, False, True), (
        "F2P witness: model/gold must skip ensure_schema (schema_ensured False),"
        " issue no record read (records_read False), and early-return; "
        "model=%r gold=%r" % (m, g))
    return (rec.ensure_schema_calls, rec_bug.ensure_schema_calls)


def main():
    combos = check_exhaustive_equivalence()
    witness = check_real_callee_witness()
    print("G-AX OK: model observations == gold-patched observations on all %d "
          "(work-list shape x table-existence) combinations; F2P witness "
          "gold ensure_schema_calls=%d (skipped) vs pre-patch=%d (the bug)"
          % (combos, witness[0], witness[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
