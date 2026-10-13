"""Twin-artifact model for django__django-15252.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A migration-execution routine runs against ONE database connection. Before it
  records that migrations have been applied, it consults a bookkeeping table.
  Putting that bookkeeping table in place is an OBSERVABLE, SIDE-EFFECTING act
  (it issues schema statements against the connection) and is undesirable on a
  connection that is not supposed to hold the table — there it can create a
  table that is not wanted, or fail outright on a connection without the
  privilege to create one. The bookkeeping table exists only to support
  recording applied migrations, so the side effect is wanted only where there
  are migrations to record.

  Two observable effects of the routine are pinned by this specification:

    (A) the table-ensuring WRITE effect (it puts the bookkeeping table in
        place); and
    (B) a record-reading QUERY effect (it consults the recorded data while it
        assembles its result).

  The desired behaviour, per connection:

    * this connection has NO migrations to record: the routine must NOT perform
      the table-ensuring write effect. Moreover, if in that situation the
      bookkeeping table is not already in place, the routine must assemble its
      result WITHOUT issuing the record-reading query effect either (the table
      it would read does not exist, so the routine must not touch the
      connection at all on this path).

    * this connection's recording work is UNDETERMINED (yet to be computed) OR
      there ARE migrations to record: the routine puts the bookkeeping table in
      place (the write effect) when there are migrations to record, and in all
      these cases proceeds to assemble its result via the record-reading query
      effect, exactly as before.

  Reading back the observable effects:
    * the table-ensuring write effect occurred IF AND ONLY IF this connection
      was NOT determined to have no migrations to record;
    * the record-reading query effect occurred EXCEPT on the one path where the
      connection has no migrations to record AND the table is not already in
      place (there the routine assembles its result without touching the
      connection at all).

Modelling choices (Nagini fragment):
  * The executor is a minimal object carrying only the touched facets: a
    read-only flag for whether the bookkeeping table is already in place, a
    mutable flag recording whether the table-ensuring WRITE effect has occurred
    (it starts un-occurred), and a mutable flag recording whether the
    record-reading QUERY effect has occurred (it starts un-occurred).
  * The recording-work argument is an ``Optional[List[int]]``: ``None`` means
    "undetermined for this connection" (yet to be computed); a present list is
    the determined recording work, and ``len(...) == 0`` distinguishes the case
    where this connection has NO migrations to record. Only its presence and
    emptiness are observed (mapping.md §2), so a list of opaque integer record
    tokens is the faithful carrier.

The table-presence flag is read-only and held at fractional permission. The
two effect flags are genuinely mutated and held at full permission with their
exact post-state stated. There is no axiomatised callee: the table-ensuring
write, the table-presence query, and the record-reading result assembly are
each reduced to the observation this specification pins, and the decision over
those observations is the changed behaviour, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Executor:
    """Minimal executor object carrying only the touched facets.

    `table_present` — whether the bookkeeping table is already in place
        (read-only query result). `schema_ensured` — whether the table-ensuring
        WRITE effect has occurred (the observable write effect; starts False).
    `records_read` — whether the record-reading QUERY effect has occurred
        (the observable read effect; starts False).
    """

    def __init__(self, table_present: bool) -> None:
        # Terminates: three field assignments, no loop and no call. Level 2
        # leaves room beneath any obligated caller (migrate is at 6).
        Requires(MustTerminate(2))
        Ensures(Acc(self.table_present) and self.table_present == table_present)  # type: ignore
        Ensures(Acc(self.schema_ensured) and self.schema_ensured is False)        # type: ignore
        Ensures(Acc(self.records_read) and self.records_read is False)            # type: ignore
        self.table_present = table_present          # type: bool
        self.schema_ensured = False                 # type: bool
        self.records_read = False                   # type: bool


# axioms-start
# (no @ContractOnly axioms are consumed: the unchanged primitives this routine
# consults — querying whether the bookkeeping table is already in place, the
# table-ensuring write effect, and the record-reading result assembly — are
# each reduced to the boolean observation this specification pins. The decision
# over those observations is the changed behaviour and is modelled deeply in
# the impl region.)
# axioms-end


# pure-start
@Pure
def no_pending_records(pending: Optional[List[int]]) -> bool:
    # This connection has NO migrations to record: the argument is present (not
    # None) and conveys no recording work (a present, length-zero carrier). A
    # None argument is 'undetermined' (yet to be computed), NOT a determination
    # that there are none.
    Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 4)))
    return pending is not None and len(pending) == 0
# pure-end


def migrate(executor: Executor, pending: Optional[List[int]]) -> None:
    # pre-conditions-start
    # The table-presence flag is a read-only query result (fractional).
    Requires(Acc(executor.table_present, 1 / 2))
    # The two effect flags are mutated; full permission, and they start
    # un-occurred (no effect has happened yet on entry).
    Requires(Acc(executor.schema_ensured))
    Requires(executor.schema_ensured is False)
    Requires(Acc(executor.records_read))
    Requires(executor.records_read is False)
    # The recording-work argument is read-only (its presence/emptiness is
    # consulted, never mutated): fractional permission, required AND ensured.
    Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(executor.table_present, 1 / 2))
    Ensures(Acc(executor.schema_ensured))
    Ensures(Acc(executor.records_read))
    Ensures(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
    # The table-presence query is read-only: its result is unchanged.
    Ensures(executor.table_present == Old(executor.table_present))

    # (1) THE pinned behaviour: the table-ensuring WRITE effect occurred IF AND
    #     ONLY IF this connection was NOT determined to have no migrations to
    #     record. Equivalently, the write effect is skipped exactly when this
    #     connection has been determined to have no migrations to record
    #     (whether or not the table is already in place).
    Ensures(executor.schema_ensured == (not no_pending_records(pending)))

    # (2) The record-reading QUERY effect occurred EXCEPT on the single path
    #     where this connection has no migrations to record AND the table is not
    #     already in place — there the routine assembles its result without
    #     touching the connection at all (no write effect by (1), and no read
    #     effect here).
    Ensures(executor.records_read ==
            (not (no_pending_records(pending) and not Old(executor.table_present))))
    # On that no-touch path, neither effect occurs.
    Ensures(Implies(not executor.records_read, executor.schema_ensured is False))
    # post-conditions-end
    # impl-start
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
    # impl-end
