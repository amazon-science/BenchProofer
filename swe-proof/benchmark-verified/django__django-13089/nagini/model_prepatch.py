"""Twin-artifact model for django__django-13089.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A maintenance routine, after asking the store for the boundary record that
  marks how far to prune, must decide whether to issue the prune operation.
  The store's answer is an OPTIONAL row: either a present row (whose first
  column is the boundary key) or the ABSENT answer (no row at all) when the
  store has nothing to report.

  The routine must consult the boundary key ONLY when a row is actually
  present. When the answer is absent, the routine performs no prune and yields
  "no boundary" — it must never reach into an absent row to read a column.
  When a row IS present, the prune is issued against that row's first column,
  which becomes the produced boundary key.

The optional row is modelled as `Optional[List[int]]` of column values (absent
~ `None`, distinguished from a present, non-empty row). A present row always
has at least its boundary column, so reading the first column is well defined
only in the present case. The produced boundary key is `Optional[int]`: absent
exactly when the row is absent (no prune issued), otherwise the row's first
column. No callee is axiomatized: the behaviour is optional-row / membership
logic over the input, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
# pure-end


def boundary_for_prune(row: Optional[List[int]]) -> Optional[int]:
    # pre-conditions-start
    # The fetched row is read-only: it is never mutated, so it is required AND
    # ensured at fractional permission (directive 5). A present row carries at
    # least its boundary column; an absent row carries nothing.
    Requires(Implies(row is not None, Acc(list_pred(row), 1 / 2)))
    Requires(Implies(row is not None, len(row) > 0))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(row is not None, Acc(list_pred(row), 1 / 2)))
    Ensures(Implies(row is not None, len(row) > 0))
    # No boundary key is produced exactly when the row is absent: an absent row
    # issues no prune, a present row does. This is the discriminating clause —
    # the absent case must yield None without touching a column.
    Ensures((Result() is None) == (row is None))
    # When a row is present, the produced boundary key is exactly its first
    # column (the value the prune is bound to). Grounded in the actual input.
    Ensures(Implies(row is not None, Result() == row[0]))
    # post-conditions-end
    # impl-start
    last = row[0]
    return last
    # impl-end
