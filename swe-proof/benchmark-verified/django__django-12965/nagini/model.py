"""Twin-artifact model for django__django-12965.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A whole-table row removal (a removal whose selection has no extra joined
  tables and therefore references only the primary table) must be emitted as a
  direct single-table removal — it must NOT be wrapped in a self-referential
  subquery over the same table.

  The decision is governed by an "exactly one active table" predicate over the
  removal's table-reference bookkeeping. Before that predicate is read, the
  primary table must be ensured present in the bookkeeping (its reference count
  made positive). With the primary table accounted for and no additional joined
  tables active, the number of active tables is exactly one, so the predicate
  holds and the direct single-table form is chosen; the subquery form is taken
  only when more than one table is active.

The removal's table-reference bookkeeping is modelled as a minimal object
carrying only the two touched aggregate quantities: whether the primary table
is currently accounted for (its reference count positive), and how many
additional joined tables are currently active. "Ensuring the primary table is
present" and the "exactly one active table" count are spelled out directly;
there is no opaque library callee whose unchanged behaviour the proof relies
on, so this bundle consumes no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TableRefs:
    def __init__(self, primary_present: bool, extra_active: int) -> None:
        Requires(extra_active >= 0)
        Ensures(Acc(self.primary_present) and self.primary_present is primary_present)  # type: ignore
        Ensures(Acc(self.extra_active) and self.extra_active == extra_active)  # type: ignore
        self.primary_present = primary_present
        self.extra_active = extra_active


# axioms-start
# (no axioms: the decision is pure table-reference bookkeeping, modelled
#  directly; there is no unchanged opaque callee the proof depends on)
# axioms-end


# pure-start
@Pure
def active_tables(primary_present: bool, extra_active: int) -> int:
    """Number of active tables: the primary table (one when accounted for) plus
    the additional joined tables that are currently active."""
    Requires(extra_active >= 0)
    Ensures(Result() >= extra_active)
    Ensures(Result() == (1 if primary_present else 0) + extra_active)
    return (1 if primary_present else 0) + extra_active
# pure-end


def references_single_table(query: TableRefs) -> bool:
    # pre-conditions-start
    Requires(Acc(query.primary_present))
    Requires(Acc(query.extra_active))
    Requires(query.extra_active >= 0)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # The primary table is ensured present before the count is read, so its
    # reference count is positive regardless of the entry state.
    Ensures(Acc(query.primary_present))
    Ensures(Acc(query.extra_active))
    Ensures(query.extra_active == Old(query.extra_active))
    Ensures(query.primary_present is True)
    # The predicate is true exactly when, with the primary table accounted for,
    # no additional joined tables are active.
    Ensures(Result() == (active_tables(query.primary_present, query.extra_active) == 1))
    Ensures(Result() == (query.extra_active == 0))
    # post-conditions-end
    # impl-start
    query.primary_present = True
    return active_tables(query.primary_present, query.extra_active) == 1
    # impl-end


def delete_uses_subquery(query: TableRefs) -> bool:
    # pre-conditions-start
    Requires(Acc(query.primary_present))
    Requires(Acc(query.extra_active))
    Requires(query.extra_active >= 0)
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(query.primary_present))
    Ensures(Acc(query.extra_active))
    Ensures(query.extra_active == Old(query.extra_active))
    # A whole-table removal (no additional joined tables active) emits the
    # direct single-table form: no self-referential subquery is used.
    Ensures(Result() == (query.extra_active != 0))
    Ensures(Implies(Old(query.extra_active) == 0, Result() is False))
    # post-conditions-end
    # impl-start
    if references_single_table(query):
        return False
    return True
    # impl-end
