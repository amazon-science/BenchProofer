"""Twin-artifact model for django__django-14351.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test groups by a list of columns. The columns it contributes are
  the columns of its left-hand operand, followed by the columns contributed by
  its right-hand operand WHEN the right-hand operand is itself a column-bearing
  sub-expression (a nested query) rather than a plain literal collection.

  The subtlety this contract pins: a nested query that carries NO explicitly
  chosen output columns must, in this grouping position, contribute EXACTLY ONE
  column — its identity (primary-key) column — not the whole set of columns it
  would otherwise expose by default. Concretely, before reading the nested
  query's grouping columns the operation first normalises such a query so that
  its only output column is the identity column; only then are those columns
  appended. A nested query that already carries explicitly chosen output
  columns is left untouched and contributes exactly those chosen columns.

The left operand's columns are modelled as a read-only ``List[int]`` of column
identifiers. The nested query is modelled as a minimal mutable object carrying
only the touched facets: whether it has explicit output columns, the columns it
would expose by default, the explicit output columns it currently carries, and
its identity-column identifier. Its unchanged grouping-column reader and the
two unchanged normalisation primitives (clear-output-columns,
add-identity-column) are axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NestedQuery:
    def __init__(self, has_fields: bool, default_cols: PSeq[int],
                 explicit_cols: PSeq[int], pk_col: int) -> None:
        Ensures(Acc(self.has_fields) and self.has_fields == has_fields)          # type: ignore
        Ensures(Acc(self.default_cols) and self.default_cols is default_cols)    # type: ignore
        Ensures(Acc(self.explicit_cols) and self.explicit_cols is explicit_cols) # type: ignore
        Ensures(Acc(self.pk_col) and self.pk_col == pk_col)                      # type: ignore
        self.has_fields = has_fields
        self.default_cols = default_cols
        self.explicit_cols = explicit_cols
        self.pk_col = pk_col


# axioms-start
@Pure
@ContractOnly
def nested_group_by_cols(q: NestedQuery) -> PSeq[int]:
    """The unchanged grouping-column reader of the nested query (the callee the
    operation invokes but does not change). When the query carries explicit
    output columns it exposes exactly those chosen columns; otherwise it exposes
    its full default column set. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(Acc(q.has_fields, 1 / 2) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols, 1 / 2) and Acc(q.pk_col, 1 / 2))
    Ensures(Implies(q.has_fields, Result() == q.explicit_cols))
    Ensures(Implies(not q.has_fields, Result() == q.default_cols))


@ContractOnly
def clear_output_columns(q: NestedQuery) -> None:
    """Unchanged normalisation primitive: drop every chosen output column. The
    query is left with no explicit output columns. Touches only the explicit
    output-column facet."""
    Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(not q.has_fields)
    Ensures(q.default_cols == Old(q.default_cols))
    Ensures(q.pk_col == Old(q.pk_col))


@ContractOnly
def add_identity_column(q: NestedQuery) -> None:
    """Unchanged normalisation primitive: set the query's chosen output columns
    to be exactly its identity column. Afterwards the query carries explicit
    output columns, and those columns are exactly its identity column. Touches
    only the explicit output-column facet."""
    Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(q.has_fields)
    Ensures(q.explicit_cols == PSeq(q.pk_col))
    Ensures(q.pk_col == Old(q.pk_col))
    Ensures(q.default_cols == Old(q.default_cols))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def membership_group_by_cols(lhs_cols: List[int], rhs_is_query: bool,
                             rhs: NestedQuery) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lhs_cols), 1 / 2))
    Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lhs_cols), 1 / 2))
    Ensures(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The identity column and the default-column set are never invented or
    # dropped by the operation.
    Ensures(rhs.pk_col == Old(rhs.pk_col))
    Ensures(rhs.default_cols == Old(rhs.default_cols))
    # When the right operand is a plain literal collection (no grouping columns
    # of its own) the result is exactly the left operand's columns.
    Ensures(Implies(not rhs_is_query, ToSeq(Result()) == ToSeq(lhs_cols)))
    # When the right operand is a column-bearing nested query that already has
    # explicit output columns, it is left UNTOUCHED and contributes exactly
    # those explicit columns — whatever they are (not forced to the identity
    # column). The contribution is grounded in the query's own explicit-column
    # carrier, never an injected sentinel.
    Ensures(Implies(rhs_is_query and Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + Old(rhs.explicit_cols)))
    # The discriminating clause: a column-bearing nested query that carries NO
    # explicit output columns contributes EXACTLY ONE column — its identity
    # column — never its full default column set.
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + PSeq(rhs.pk_col)))
    # PRODUCED-BY (anti-fabrication): a field-less nested query must be left in
    # the normalised post-state — explicit output columns present and equal to
    # exactly the identity column — and the contributed columns must be the
    # reader's output on that post-state, not a fabricated constant.
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    rhs.has_fields and rhs.explicit_cols == PSeq(rhs.pk_col)))
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + nested_group_by_cols(rhs)))
    # FRAME (anti-gratuitous-mutation): the field-less normalisation is the ONLY
    # branch on which the nested query is touched. A plain literal right operand
    # is never a query to normalise, and a nested query that already carries
    # explicitly chosen output columns is left untouched — both its
    # explicit-column carrier and its explicit-columns flag are preserved.
    Ensures(Implies(not (rhs_is_query and not Old(rhs.has_fields)),
                    rhs.has_fields == Old(rhs.has_fields)))
    Ensures(Implies(not (rhs_is_query and not Old(rhs.has_fields)),
                    rhs.explicit_cols == Old(rhs.explicit_cols)))
    # post-conditions-end
    # impl-start
    orig_default = rhs.default_cols  # type: PSeq[int]
    orig_explicit = rhs.explicit_cols  # type: PSeq[int]
    orig_had_fields = rhs.has_fields  # type: bool
    orig_pk = rhs.pk_col  # type: int
    cols = list(lhs_cols)  # type: List[int]
    if rhs_is_query:
        # PRE-PATCH: the membership test inherits the generic reader, which
        # appends the nested query's grouping columns WITHOUT first normalising
        # a query that has no explicit output columns. A field-less nested query
        # therefore contributes its full default column set, not just its
        # identity column.
        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
        i = 0
        while i < len(rhs_cols):
            # invariants-start
            Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
            Invariant(rhs.has_fields == orig_had_fields)
            Invariant(rhs.default_cols == orig_default)
            Invariant(rhs.explicit_cols == orig_explicit)
            Invariant(rhs.pk_col == orig_pk)
            Invariant(rhs_cols == nested_group_by_cols(rhs))
            Invariant(Acc(list_pred(cols)))
            Invariant(Acc(list_pred(lhs_cols), 1 / 2))
            Invariant(0 <= i and i <= len(rhs_cols))
            Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
            Invariant(MustTerminate(len(rhs_cols) - i + 1))
            # invariants-end
            cols.append(rhs_cols[i])
            i = i + 1
    return cols
    # impl-end
