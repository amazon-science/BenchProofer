"""Twin-artifact model for django__django-14434.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deferred schema statement that constrains the columns of a table records,
  for its column-bearing part, the IDENTIFIER of the table those columns belong
  to together with the set of constrained columns. The query "does this part
  constrain column C of table T?" is answered by comparing the recorded table
  identifier against the queried table identifier BY VALUE and testing C for
  membership in the recorded column set.

  The desired guarantee: after building the column-bearing part of a unique
  constraint over a table named ``db_table`` with column set ``columns``,

    * for every ``c`` in ``columns``, the part constrains column ``c`` of table
      ``db_table`` (returns ``True``);
    * for any ``c`` NOT in ``columns``, or any other table name, the part does
      NOT constrain it (returns ``False``);
    * the companion table query for ``db_table`` returns ``True``.

  For the value comparison to succeed, the table recorded against the columns
  must be the same plain identifier the rest of the system names the table by.

A table identifier is modelled as ``List[int]`` of code points (Nagini bans
``str`` indexing); the constrained column set is modelled as a ``PSeq[int]`` of
column-identifier codes. The column-bearing part is a minimal class carrying
only the touched facets: the recorded table identifier, the constrained column
set, and a flag stating whether the recorded identifier is a plain name
(value-comparable to a queried name) or an opaque holder (which never
value-equals a plain name). One unchanged callee — membership of a column code
in the recorded set — is modelled deeply over the sequence (front-recursive),
validated out of band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ConstraintPart:
    """The column-bearing part of a deferred statement, restricted to its
    observed facets. ``plain`` records whether ``table`` is a plain table name
    (value-comparable to a queried name) or an opaque holder (never value-equal
    to a plain name); ``table`` is the recorded table identifier; ``columns`` is
    the constrained column set as a sequence of column-identifier codes."""

    def __init__(self, plain: bool, table: List[int], columns: PSeq[int]) -> None:
        Requires(Acc(list_pred(table), 1 / 2))
        Requires(MustTerminate(1))
        Ensures(Acc(self.plain) and self.plain == plain)            # type: ignore
        Ensures(Acc(self.table) and self.table is table)            # type: ignore
        Ensures(Acc(list_pred(self.table), 1 / 2))                  # type: ignore
        Ensures(Acc(self.columns) and self.columns == columns)      # type: ignore
        self.plain = plain
        self.table = table
        self.columns = columns


# axioms-start
# (no @ContractOnly axioms: the only callee — membership of a column code in
# the recorded column set — is modelled deeply by the front-recursive @Pure
# `member` below and validated == real membership by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def member(c: int, cols: PSeq[int]) -> bool:
    """Whether the column code ``c`` occurs in the column set ``cols``.
    Front-recursive over ``PSeq`` so a single unfold is available to callers."""
    if len(cols) == 0:
        return False
    return cols[0] == c or member(c, cols.drop(1))


@Pure
def constrains_column(plain: bool, table: PSeq[int], cols: PSeq[int],
                      q_table: PSeq[int], q_col: int) -> bool:
    """The column query on a column-bearing part: the recorded table identifier
    must be a plain name AND value-equal the queried table identifier, and the
    queried column code must be a member of the recorded column set. An opaque
    holder (``plain == False``) never value-equals a plain queried name."""
    return plain and table == q_table and member(q_col, cols)


@Pure
def constrains_table(table: PSeq[int], q_table: PSeq[int]) -> bool:
    """The table query on a part holding a table identifier: the recorded
    identifier value-equals the queried one."""
    return table == q_table
# pure-end


def build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart:
    # pre-conditions-start
    Requires(Acc(list_pred(db_table), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().plain) and Acc(Result().table) and Acc(Result().columns))
    # The recorded table identifier IS the constraint's table name (the
    # db_table the caller passed); the read-only half-permission flows through.
    Ensures(Result().table is db_table)
    Ensures(Acc(list_pred(Result().table), 1 / 2))
    # The recorded column set is exactly the constraint's column set.
    Ensures(Result().columns == columns)
    # The discriminating guarantee: every column the constraint constrains is
    # reported for THIS table, by value.
    Ensures(Forall(int, lambda c: (
        Implies(member(c, columns),
                constrains_column(Result().plain, ToSeq(Result().table),
                                  Result().columns, ToSeq(db_table), c)),
        [[member(c, columns)]])))
    # A column NOT constrained, or a different table name, is NOT reported —
    # the query stays a faithful conjunction, not a constant True.
    Ensures(Forall(int, lambda c: (
        Implies(not member(c, columns),
                not constrains_column(Result().plain, ToSeq(Result().table),
                                      Result().columns, ToSeq(db_table), c)),
        [[member(c, columns)]])))
    # The companion table query holds for this table (the part identifies the
    # constraint's own table).
    Ensures(constrains_table(ToSeq(Result().table), ToSeq(db_table)))
    # post-conditions-end
    # impl-start
    # Record an opaque table holder (not value-comparable to a plain name)
    # against the columns, instead of the plain table name.
    part = ConstraintPart(False, db_table, columns)  # type: ConstraintPart
    return part
    # impl-end
