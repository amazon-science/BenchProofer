"""Twin-artifact model for django__django-15280.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a collection of child rows has been fetched for a set of parent rows,
  each child must be linked back to the parent it belongs to so that walking
  from the child to that parent needs no further fetch. Each child carries a
  single slot that remembers the parent it is linked to; that slot is either
  EMPTY or already holds a parent.

  The pinned behaviour is what may write that slot. A child whose slot is
  already populated keeps its existing parent untouched: an earlier, more
  specific link (for instance one established by a separately fetched
  child-to-parent collection) is authoritative and must survive. Only a child
  whose slot is still EMPTY is linked to the parent supplied for it by the
  current collection.

  Concretely, for each child in the collection: if its slot was already
  populated, after the operation it still holds the very same parent it held
  before; if its slot was empty, after the operation it holds exactly the parent
  supplied for that child, and is no longer empty. No populated slot is ever
  overwritten.

Each child is modelled by two parallel integer lists: `slot_full[i]` is 1 iff
child i's parent slot was already populated, and `slot_value[i]` is the parent
identifier stored there (a non-negative id, or the sentinel -1 when empty). The
parent supplied for child i by the current collection is `supplied[i]` (a
non-negative id). The operation mutates the children's slots; `supplied` and the
record of which slots were initially populated are read-only.

The per-child resulting parent is the deep model `linked_parent`; no callee is
axiomatized (the slot test and the slot write are spelled out directly).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The slot-occupancy test and the slot write are ordinary
# concrete operations modelled directly; the behaviour under specification — a
# populated slot is preserved, an empty slot receives the supplied parent — is
# pinned by the pure `linked_parent` map below and the verified loop, not behind
# a @ContractOnly. G-EQ audits the refinement to the real descriptor code.)
# axioms-end


# pure-start
@Pure
def linked_parent(was_full: int, old_value: int, supplied: int) -> int:
    """The parent a child's slot holds after the operation.

    If the slot was already populated (`was_full == 1`) it keeps its prior
    parent `old_value` unchanged; otherwise it receives the parent `supplied`
    for that child by the current collection."""
    if was_full == 1:
        return old_value
    return supplied
# pure-end


def link_children_to_parents(slot_full: List[int],
                             slot_value: List[int],
                             supplied: List[int]) -> None:
    # pre-conditions-start
    # The children's slots are mutated, so full permission on `slot_value`.
    Requires(Acc(list_pred(slot_value)))
    # The record of which slots were initially populated and the supplied
    # parents are read-only: fractional permission, required AND ensured, so no
    # implementation can satisfy a postcondition vacuously by overwriting them.
    Requires(Acc(list_pred(slot_full), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    # The three lists describe the same collection of children.
    Requires(len(slot_full) == len(slot_value))
    Requires(len(supplied) == len(slot_value))
    # `slot_full` is a 0/1 occupancy flag per child.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                            slot_full[k] == 0 or slot_full[k] == 1),
                                    [[slot_full[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(slot_value)))
    Ensures(Acc(list_pred(slot_full), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    # The collection shape is preserved.
    Ensures(len(slot_value) == Old(len(slot_value)))
    Ensures(len(slot_value) == len(slot_full))
    Ensures(len(slot_value) == len(supplied))
    # Per child: a populated slot keeps its prior parent; an empty slot now
    # holds the parent supplied for that child. No populated slot is overwritten.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(slot_value),
                slot_value[k] == linked_parent(slot_full[k],
                                               Old(slot_value[k]),
                                               supplied[k])),
        [[slot_value[k]]])))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(slot_value):
        # invariants-start
        Invariant(Acc(list_pred(slot_value)))
        Invariant(Acc(list_pred(slot_full), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(len(slot_value) == Old(len(slot_value)))
        Invariant(len(slot_value) == len(slot_full))
        Invariant(len(slot_value) == len(supplied))
        Invariant(0 <= i and i <= len(slot_value))
        # Children already processed satisfy the per-child guarantee.
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                    slot_value[k] == linked_parent(slot_full[k],
                                                   Old(slot_value[k]),
                                                   supplied[k])),
            [[slot_value[k]]])))
        # Children not yet processed still hold their original parent.
        Invariant(Forall(int, lambda k: (
            Implies(i <= k and k < len(slot_value),
                    slot_value[k] == Old(slot_value[k])),
            [[slot_value[k]]])))
        Invariant(MustTerminate(len(slot_value) - i + 1))
        # invariants-end
        # Pre-patch skeleton: the slot is written unconditionally, with no test
        # of whether it was already populated. A populated slot is therefore
        # overwritten with the parent supplied by the current collection,
        # discarding any earlier, more specific link.
        slot_value[i] = supplied[i]
        i = i + 1
    # impl-end
