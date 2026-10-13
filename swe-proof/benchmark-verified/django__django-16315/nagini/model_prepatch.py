"""Twin-artifact model for django__django-16315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a batch insertion is configured to resolve row conflicts by updating a
  set of requested fields keyed on a set of requested conflict fields, the
  conflict-resolution clause that is handed to the backend must refer to each
  requested field by its configured *storage identifier* (the column the field
  is stored under), NOT by the field's in-memory attribute name.

  Each requested field is named by the caller; the schema resolves that name to
  the field it designates. A field's storage identifier equals its declared
  storage-column override when one is configured, and equals the field's own
  name otherwise. Two requested fields therefore produce DIFFERENT identifiers
  exactly when their storage-column overrides (or names, absent an override)
  differ -- never merely because the caller spelled the request differently.

  The list produced for the backend has the same length and order as the list
  of requested names, and element i is the storage identifier of the field that
  the i-th requested name designates.

A field is modelled as a minimal record carrying only the two touched
attributes: its name and its storage identifier (its column). The schema's
name->field resolution (the unchanged lookup) is modelled deeply as a registry
of parallel name/column lists; resolving a name yields the column registered
against the matching name. Identifiers are modelled as ints (the discriminator
is which identifier is selected, name vs column, not its textual content).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axioms are consumed: the name->column resolution is the
# UNCHANGED schema lookup, modelled deeply as a registry of parallel
# name/column lists -- it is not an opaque callee whose Ensures the proof
# relies upon. See refinement.md / mapping.md for the A-reference provenance.)
# axioms-end


# pure-start
@Pure
def name_present(name: int, names: PSeq[int]) -> bool:
    """True iff some registry slot carries field-name ``name``. Front-recursive
    (one unfold per skipped slot); total (no precondition)."""
    if len(names) == 0:
        return False
    if names[0] == name:
        return True
    return name_present(name, names.drop(1))


@Pure
def column_for(name: int, names: PSeq[int], columns: PSeq[int]) -> int:
    """Storage identifier the requested ``name`` designates: walk the registry
    name/column slots in parallel and return the column of the first slot whose
    name matches. Front-recursive and TOTAL (the empty guard never fires under a
    well-formed registry with the name present, but keeps the function free of a
    length precondition so it composes cleanly inside contracts)."""
    if len(names) == 0 or len(columns) == 0:
        return 0
    if names[0] == name:
        return columns[0]
    return column_for(name, names.drop(1), columns.drop(1))
# pure-end


def conflict_columns(requested: List[int], field_names: List[int],
                     field_columns: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(requested), 1 / 2))
    Requires(Acc(list_pred(field_names), 1 / 2))
    Requires(Acc(list_pred(field_columns), 1 / 2))
    # the registry is well-formed (one column per declared field) ...
    Requires(len(field_columns) == len(field_names))
    # ... and every requested name designates a declared field (the lookup the
    # schema performs without error).
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(requested),
        name_present(ToSeq(requested)[k], ToSeq(field_names)))))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(requested), 1 / 2))
    Ensures(Acc(list_pred(field_names), 1 / 2))
    Ensures(Acc(list_pred(field_columns), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Same length and order as the requested-name list.
    Ensures(len(Result()) == len(requested))
    # Element i is the storage identifier the i-th requested name designates
    # (its column), NOT the requested name itself.
    Ensures(Forall(int, lambda k: Implies(
        0 <= k and k < len(requested),
        ToSeq(Result())[k] == column_for(
            ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(requested):
        # invariants-start
        Invariant(Acc(list_pred(requested), 1 / 2))
        Invariant(Acc(list_pred(field_names), 1 / 2))
        Invariant(Acc(list_pred(field_columns), 1 / 2))
        Invariant(len(field_columns) == len(field_names))
        Invariant(0 <= i and i <= len(requested))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < len(requested),
            name_present(ToSeq(requested)[k], ToSeq(field_names)))))
        Invariant(Acc(list_pred(result)) and len(result) == i)
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            ToSeq(result)[k] == column_for(
                ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
        Invariant(MustTerminate(len(requested) - i + 1))
        # invariants-end
        # the i-th requested name is registered (instantiate the Forall):
        Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
        # resolve the requested name to a declared field, then take its column.
        col = lookup(requested[i], field_names, field_columns)
        result = result + [col]
        Assert(ToSeq(result)[i] == col)
        i = i + 1
    return result
    # impl-end


def lookup(name: int, field_names: List[int], field_columns: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(field_names), 1 / 4))
    Requires(Acc(list_pred(field_columns), 1 / 4))
    Requires(len(field_columns) == len(field_names))
    Requires(name_present(name, ToSeq(field_names)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field_names), 1 / 4))
    Ensures(Acc(list_pred(field_columns), 1 / 4))
    Ensures(Result() == column_for(name, ToSeq(field_names), ToSeq(field_columns)))
    # post-conditions-end
    # impl-start
    j = 0
    while j < len(field_names):
        # invariants-start
        Invariant(Acc(list_pred(field_names), 1 / 4))
        Invariant(Acc(list_pred(field_columns), 1 / 4))
        Invariant(len(field_columns) == len(field_names))
        Invariant(0 <= j and j <= len(field_names))
        # the name is still present in the unscanned suffix, and the column it
        # designates over the whole registry equals the column it designates
        # over that suffix (no earlier slot matched).
        Invariant(name_present(name, ToSeq(field_names).drop(j)))
        Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                  column_for(name, ToSeq(field_names).drop(j),
                             ToSeq(field_columns).drop(j)))
        Invariant(MustTerminate(len(field_names) - j + 1))
        # invariants-end
        # one front-unfold of name_present/column_for over the suffix at j:
        Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
        Assert(ToSeq(field_columns).drop(j)[0] == field_columns[j])
        Assert(ToSeq(field_names).drop(j).drop(1) == ToSeq(field_names).drop(j + 1))
        Assert(ToSeq(field_columns).drop(j).drop(1) == ToSeq(field_columns).drop(j + 1))
        if field_names[j] == name:
            # PRE-PATCH BUG: the identifier handed to the backend is the matched
            # field's in-memory NAME, not its storage column. When a field
            # declares a storage-column override (column != name) this is the
            # wrong identifier and the produced clause references a column the
            # schema does not have.
            return field_names[j]
        # no match here -> the suffix's answer is the answer of the next suffix
        Assert(name_present(name, ToSeq(field_names).drop(j + 1)))
        j = j + 1
    # unreachable: name_present guarantees a match before j == len
    Assert(False)
    return 0
    # impl-end
