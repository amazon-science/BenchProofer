"""Twin-artifact model for django__django-16032.

Behaviour under specification (stated as desired behaviour, not as an edit):

A query value used on the right-hand side of a membership filter against a
related column carries a single boolean property — call it
``restricted_to_explicit_columns`` — that records whether the query's selected
output columns have been *explicitly* restricted by a column-projection call
(the operation that pins the SELECT list to a chosen set of names). The three
operations modelled here must keep that property faithful:

  (1) Projecting a query onto a chosen set of columns restricts its selected
      output to exactly that set AND establishes the property as true. The
      projection also re-derives the internal expression-tracking structure
      for the newly-chosen columns; because the chosen columns are ordinary
      output columns (never auxiliary expressions), that structure is left
      empty afterwards — projection clears it.

  (2) Attaching auxiliary derived expressions to a query — both the kind that
      adds a returned column and the kind that adds a helper column that is not
      itself returned — may populate the query's internal expression-tracking
      structure, but it must NOT, on its own, establish the property. Whether
      the output columns were explicitly restricted depends only on whether a
      projection (operation 1) has occurred, never on the presence of auxiliary
      expressions. So combining the two kinds of auxiliary expressions still
      leaves the property false on a query that was never projected.

  (3) Preparing such a query as the right-hand side of the membership filter:
      when the property is false (the right-hand side was never projected) and
      the comparison is not already against a unique-key column, the right-hand
      side is narrowed to the single relevant column. That narrowing is exactly
      operation (1): afterwards the selected output is that one column, the
      property is true, and the expression-tracking structure is cleared. When
      the property is already true, or the comparison is against a unique-key
      column, the right-hand side is left untouched.

A query is modelled as a minimal object exposing only the touched state: the
boolean property, the list of explicitly-selected column ids, and a boolean
recording whether the internal expression-tracking structure has been
materialized (the structure whose mere presence must no longer be mistaken for
an explicit projection). No callee is axiomatized: the behaviour is pure
object/state logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Query:
    def __init__(self) -> None:
        Ensures(Acc(self.restricted_to_explicit_columns))  # type: ignore
        Ensures(Acc(self.selected_columns) and Acc(list_pred(self.selected_columns)))  # type: ignore
        Ensures(Acc(self.aux_expr_materialized))           # type: ignore
        Ensures(self.restricted_to_explicit_columns is False)  # type: ignore
        Ensures(len(self.selected_columns) == 0)           # type: ignore
        Ensures(self.aux_expr_materialized is False)       # type: ignore
        self.restricted_to_explicit_columns = False  # type: bool
        self.selected_columns = []  # type: List[int]
        self.aux_expr_materialized = False  # type: bool


# axioms-start
# No consumed axioms: the three operations are pure object/state logic, modelled
# deeply. The underlying field-clearing/selection primitives the operations build
# on are validated against their real semantics out-of-band by axiom_check.py
# (G-AX) as A-reference observations, not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def project_columns(q: Query, column: int) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (1) the selected output is restricted to exactly the chosen column ...
    Ensures(len(q.selected_columns) == 1)
    Ensures(q.selected_columns[0] == column)
    # ... AND the explicit-projection property is established as true.
    Ensures(q.restricted_to_explicit_columns is True)
    # ... AND the auxiliary expression-tracking structure is re-derived for the
    # chosen (ordinary, non-auxiliary) columns: it ends up empty — cleared.
    Ensures(q.aux_expr_materialized is False)
    # post-conditions-end
    # impl-start
    q.selected_columns = []
    q.selected_columns = [column]
    q.restricted_to_explicit_columns = True
    # projection re-derives the expression-tracking structure for the chosen
    # ordinary columns, which leaves it empty.
    q.aux_expr_materialized = False
    # impl-end


def attach_auxiliary_expressions(q: Query) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (2) auxiliary expressions (returned + non-returned kinds) materialize the
    # internal expression-tracking structure ...
    Ensures(q.aux_expr_materialized is True)
    # ... but they leave the explicit-projection property and the selected
    # output exactly as they were: presence of auxiliary expressions is NOT an
    # explicit projection.
    Ensures(q.restricted_to_explicit_columns == Old(q.restricted_to_explicit_columns))
    Ensures(ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns)))
    # post-conditions-end
    # impl-start
    # attaching the returned-column kind and the non-returned (helper) kind
    # materializes the auxiliary expression-tracking structure; it touches no
    # other state.
    q.aux_expr_materialized = True
    # impl-end


def prepare_in_rhs(q: Query, target_column: int, target_is_unique_key: bool) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (3) narrowing happens exactly when the rhs was never explicitly projected
    # and the comparison is not against a unique-key column: afterwards the
    # selected output is that one column, the property is true, and — because
    # narrowing IS the projection operation (1) — the auxiliary
    # expression-tracking structure is cleared.
    Ensures(
        Implies(
            (not Old(q.restricted_to_explicit_columns)) and (not target_is_unique_key),
            len(q.selected_columns) == 1
            and q.selected_columns[0] == target_column
            and (q.restricted_to_explicit_columns is True)
            and (q.aux_expr_materialized is False),
        )
    )
    # when narrowing does NOT happen the rhs is left untouched (including the
    # auxiliary expression-tracking structure).
    Ensures(
        Implies(
            Old(q.restricted_to_explicit_columns) or target_is_unique_key,
            q.restricted_to_explicit_columns == Old(q.restricted_to_explicit_columns)
            and ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns))
            and q.aux_expr_materialized == Old(q.aux_expr_materialized),
        )
    )
    # post-conditions-end
    # impl-start
    if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
        # PRE-PATCH (related_lookups.py): the rhs was narrowed by clearing its
        # select clause and then re-adding the single column to the SELECT set
        # directly. That set the selected output but did NOT establish the
        # explicit-projection property (it bypassed the projection operation,
        # so it neither set the property nor re-derived/cleared the auxiliary
        # expression-tracking structure).
        q.selected_columns = []
        q.selected_columns = [target_column]
    # impl-end
