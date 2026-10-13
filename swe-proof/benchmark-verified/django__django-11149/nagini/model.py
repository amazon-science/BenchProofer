"""Twin-artifact model for django__django-11149.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administrative interface renders an editable sub-collection that belongs to
  an automatically generated link table standing between two principal records.
  Such a link table carries no permissions of its own, so the four authorisation
  decisions for it — may the actor create, modify, remove, or merely inspect an
  entry — are derived from the permissions the actor holds on the *target*
  record that the link points to.

  The actor's authorisation is a set of held permission codes for the target
  record.  Two of those codes are significant here: an INSPECT code and a MODIFY
  code (distinct codes). The decisions are:

    (1) inspect is permitted exactly when the actor holds EITHER the inspect code
        OR the modify code for the target (modify subsumes inspect);

    (2) create, modify, and remove are EACH permitted exactly when the actor
        holds the MODIFY code for the target — holding only the inspect code must
        NOT permit any of them.

  Equivalently, every decision asks whether the actor holds ANY of a small list
  of required codes for the target record: the inspect decision requires
  {inspect, modify}; each of create / modify / remove requires {modify} alone.
  An actor granted inspect-only therefore gets a read-only collection.

The actor's held codes are modelled as ``PSet[int]``; a required-code list is a
``PSeq[int]``; holding a code is set membership; "holds any required code" is the
existential over the required list.  Each decision is the corresponding
``bool``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: a decision is a membership/any query over the actor's
# held permission codes, modelled deeply over PSet[int] / PSeq[int]. The code
# construction and the per-code membership test are unchanged callees refined to
# integer codes / set membership, not axioms the proof consumes — see
# refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def holds_any(held: PSet[int], required: PSeq[int]) -> bool:
    """The actor holds AT LEAST ONE of the required codes for the target record.
    This is the existential over the required-code list of the per-code holding
    test (set membership)."""
    return Exists(int, lambda j: 0 <= j and j < len(required) and required[j] in held)
# pure-end


def target_decision(held: PSet[int], required: PSeq[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    # The decision must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition
    # only vacuously by never returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # The decision is TRUE iff the actor holds any of the required codes.
    Ensures(Result() == holds_any(held, required))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(required):
        # invariants-start
        Invariant(Acc(set_pred(held), 1 / 2))
        Invariant(0 <= i and i <= len(required))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(required) - i.
        Invariant(MustTerminate(len(required) - i))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i, not (required[k] in held))))
        # invariants-end
        if required[i] in held:
            return True
        i = i + 1
    return False
    # impl-end


def inline_inspect_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Inspect is permitted iff the actor holds the inspect OR the modify code.
    Ensures(Result() == ((inspect_code in held) or (modify_code in held)))
    # post-conditions-end
    # impl-start
    required = PSeq(inspect_code, modify_code)
    return target_decision(held, required)
    # impl-end


def inline_create_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Create is permitted iff the actor holds the MODIFY code; the inspect code
    # alone must NOT permit it.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end


def inline_modify_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Modify is permitted iff the actor holds the MODIFY code.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end


def inline_remove_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(18))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Remove is permitted iff the actor holds the MODIFY code.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end
