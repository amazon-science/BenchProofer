"""Twin-artifact model for django__django-12273.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An instance keeps its attribute values in a slot store. One slot is the
  identity slot (the value returned and accepted as the instance's identity).
  Some other slots are "linked identity" slots: they hold the identity value of
  a related ancestor record and, structurally, must always agree with the
  instance's own identity for the record to denote the same logical row.

  Assigning a new identity value to the instance must keep this agreement:
  after the assignment the identity slot holds the new value AND every linked
  identity slot that is genuinely a distinct linked slot (present, and not the
  identity slot itself) also holds the new value. Every unrelated slot keeps
  its previous value.

  This is what lets a fresh identity (e.g. clearing the identity to request a
  brand-new record) take effect across every level of an ancestor chain instead
  of silently keeping the linked slots pointing at the original record.

The instance store is modelled as a `List[int]` of slot values (Nagini bans
attribute reflection). The set of linked-identity slots and which of them are
active (present and distinct from the identity slot) is carried by read-only
metadata lists. The specification is phrased over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
# pure-end


def assign_identity(store: List[int], target: List[int], active: List[int],
                    pk_idx: int, value: int) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(store)))
    Requires(Acc(list_pred(target), 1 / 2))
    Requires(Acc(list_pred(active), 1 / 2))
    Requires(len(active) == len(target))
    Requires(0 <= pk_idx and pk_idx < len(store))
    # each linked slot indexes a real store slot
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                            0 <= target[j] and target[j] < len(store)),
                                     [[target[j]]])))
    # an active linked slot is a distinct slot (not the identity slot itself)
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                            Implies(active[j] == 1, target[j] != pk_idx)))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(store)))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(active), 1 / 2))
    Ensures(len(store) == Old(len(store)))
    # the identity slot takes the new value
    Ensures(store[pk_idx] == value)
    # every active linked slot also takes the new value
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(target) and j < len(active) and
                                           0 <= target[j] and target[j] < len(store),
                                           Implies(active[j] == 1, store[target[j]] == value)),
                                    [[target[j]]])))
    # every other slot is unchanged
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and i != pk_idx and
                                           Forall(int, lambda j: (Implies(0 <= j and j < len(target) and j < len(active),
                                                                          Implies(active[j] == 1, target[j] != i)))),
                                           store[i] == Old(store[i])),
                                    [[store[i]]])))
    # post-conditions-end
    # impl-start
    # Pre-image behaviour: the assignment touches only the identity slot and
    # never propagates the value to the linked identity slots.
    store[pk_idx] = value
    # impl-end
