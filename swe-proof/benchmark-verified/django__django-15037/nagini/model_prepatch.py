"""Twin-artifact model for django__django-15037.

Behaviour under specification (stated as desired behaviour, not as an edit):

A column that participates in a relationship to another table is rendered as a
relational model field. The introspected facts about one such column are:

  * whether the relationship is one-to-one (a unique or primary-key relation)
    rather than a plain many-to-one relationship;
  * the name of the column it references in the other table (the referenced
    column);
  * the name of the other table, and the name of the table being introspected;
  * the primary-key column of the other table, if that table has one.

The result records three decisions:

  (1) the relation kind: one-to-one exactly when the relation is unique/primary;
  (2) whether the related target is the table itself (the referenced table name
      equals the current table name);
  (3) whether an explicit referenced-column qualifier must be emitted, and which
      column it names. The qualifier is required exactly when the relationship
      is the plain many-to-one kind AND the other table has a primary-key column
      AND that primary-key column is NOT the referenced column; in that case the
      qualifier names the referenced column. A one-to-one relation, a referenced
      table without a primary key, or a relationship that already targets the
      other table's primary key needs no qualifier — and then the result's
      qualifier column is empty (the canonical representation of an absent
      qualifier: in reality no qualifier value exists at all in that case).

Column and table names are modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); name equality is carried by `PSeq[int]` via
`ToSeq`. The other table's primary-key column is the (unchanged) introspected
fact `other_pk_column`, an `Optional[List[int]]` (None when there is no primary
key); its provenance and out-of-band soundness check live in mapping.md /
axiom_check.py (an A-reference, not a consumed axiom).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axiom is consumed by the proof. The other table's
#  primary-key column name is taken directly as the introspected
#  `other_pk_column` input and validated against reality out-of-band by
#  axiom_check.py / G-AX — an A-reference, see refinement.md and mapping.md.)
# axioms-end


# pure-start
@Pure
def names_equal(a: List[int], b: List[int]) -> bool:
    """Two column/table names are equal iff their code-point sequences match."""
    Requires(Acc(list_pred(a), 1 / 4))
    Requires(Acc(list_pred(b), 1 / 4))
    return ToSeq(a) == ToSeq(b)


@Pure
def qualifier_required(unique_or_pk: bool, referenced_column: List[int],
                       other_pk_column: Optional[List[int]]) -> bool:
    """The referenced-column qualifier is required exactly for a plain
    many-to-one relationship whose other table has a (non-empty) primary-key
    column name that is not the referenced column."""
    Requires(Acc(list_pred(referenced_column), 1 / 4))
    Requires(Implies(other_pk_column is not None,
                     Acc(list_pred(other_pk_column), 1 / 4)))
    return (not unique_or_pk) and other_pk_column is not None and \
        len(other_pk_column) > 0 and \
        ToSeq(other_pk_column) != ToSeq(referenced_column)
# pure-end


class RelationField:
    """Carrier of the three decisions about one relational column.

    `qualifier_column` names the emitted qualifier when `needs_qualifier` is
    True, and is empty when `needs_qualifier` is False (the canonical
    representation of an absent qualifier).
    """

    def __init__(self) -> None:
        Ensures(Acc(self.is_one_to_one) and Acc(self.rel_to_self) and
                Acc(self.needs_qualifier) and Acc(self.qualifier_column))
        Ensures(self.is_one_to_one is False and self.rel_to_self is False)
        Ensures(self.needs_qualifier is False)
        Ensures(Acc(list_pred(self.qualifier_column)) and len(self.qualifier_column) == 0)
        self.is_one_to_one = False  # type: bool
        self.rel_to_self = False  # type: bool
        self.needs_qualifier = False  # type: bool
        self.qualifier_column = []  # type: List[int]


def relation_field(unique_or_pk: bool,
                   referenced_column: List[int],
                   referenced_table: List[int],
                   table_name: List[int],
                   other_pk_column: Optional[List[int]]) -> RelationField:
    # pre-conditions-start
    Requires(Acc(list_pred(referenced_column), 1 / 2))
    Requires(Acc(list_pred(referenced_table), 1 / 2))
    Requires(Acc(list_pred(table_name), 1 / 2))
    Requires(Implies(other_pk_column is not None,
                     Acc(list_pred(other_pk_column), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs are returned at the same fractional permission.
    Ensures(Acc(list_pred(referenced_column), 1 / 2))
    Ensures(Acc(list_pred(referenced_table), 1 / 2))
    Ensures(Acc(list_pred(table_name), 1 / 2))
    Ensures(Implies(other_pk_column is not None,
                    Acc(list_pred(other_pk_column), 1 / 2)))
    # The freshly produced result object is fully owned.
    Ensures(Acc(Result().is_one_to_one) and Acc(Result().rel_to_self) and
            Acc(Result().needs_qualifier) and Acc(Result().qualifier_column))
    Ensures(Acc(list_pred(Result().qualifier_column)))
    # (1) relation kind: one-to-one iff unique/primary.
    Ensures(Result().is_one_to_one == unique_or_pk)
    # (2) target is the table itself iff the referenced table is the current one.
    Ensures(Result().rel_to_self == names_equal(referenced_table, table_name))
    # (3) the referenced-column qualifier is emitted exactly when required,
    #     and when emitted it names the referenced column.
    Ensures(Result().needs_qualifier ==
            qualifier_required(unique_or_pk, referenced_column, other_pk_column))
    Ensures(Implies(Result().needs_qualifier,
                    ToSeq(Result().qualifier_column) == ToSeq(referenced_column)))
    #     when NOT required, no qualifier value exists in reality (the to_field
    #     key is absent), so the column is pinned to the canonical empty value —
    #     an impl must not smuggle a value into the absent case.
    Ensures(Implies(not Result().needs_qualifier,
                    len(Result().qualifier_column) == 0))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the relation kind and the self-vs-other target are
    # decided, but no referenced-column qualifier is ever emitted — the
    # referenced column from the relation is discarded.
    out = RelationField()
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    return out
    # impl-end
