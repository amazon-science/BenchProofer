"""Twin-artifact model for django__django-12754.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a newly introduced record kind inherits from an existing parent record
  kind, creating the child kind must be sequenced AFTER any field of the parent
  whose name the child re-declares has been withdrawn from the parent. Otherwise
  the two kinds would momentarily both own a field of the same name, which is
  not allowed for an inheriting kind.

  Concretely, three name-sets describe one parent: the names the parent owned
  in the prior state (``parent_before``), the names it owns in the target state
  (``parent_after``), and the names the child declares (``child``). A parent
  field name must be withdrawn-before-the-child precisely when it was owned by
  the parent before, is no longer owned by the parent after (i.e. it was
  withdrawn), AND is re-declared by the child (a clash). For each such name the
  child's creation gains an ordering prerequisite on that name's withdrawal; no
  other name contributes a prerequisite.

Field names are modelled as integer identifiers (the only operations performed
on them are set membership and equality — never any character-level operation);
the parent's target names and the child's names are ``PSet[int]``; the candidate
names iterated are the parent's prior names as a ``PSeq[int]``; the emitted
prerequisites are the ``List[int]`` filtered subsequence of qualifying names.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. The qualifying-name selection is a set
# difference-then-intersection, modelled DEEPLY over PSet[int] / PSeq[int]: a
# name qualifies iff it is in the parent's prior names, absent from the parent's
# target names, and present in the child's names. The underlying set operations
# (membership, difference, intersection) are unchanged primitives refined to
# PSet membership, not axioms the proof consumes — see refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def qualifies(name: int, parent_after: PSet[int], child: PSet[int]) -> bool:
    """A candidate parent field name (already known to be a prior parent name)
    needs withdrawing-before-the-child exactly when it is no longer owned by the
    parent after (withdrawn) and is re-declared by the child (a clash)."""
    Requires(Acc(set_pred(parent_after), 1 / 4))
    Requires(Acc(set_pred(child), 1 / 4))
    return (not (name in parent_after)) and (name in child)


@Pure
def selected(candidates: PSeq[int], parent_after: PSet[int],
             child: PSet[int]) -> PSeq[int]:
    """The prerequisites for one parent: the subsequence of the parent's prior
    field names that qualify (withdrawn-from-parent AND re-declared-by-child),
    in candidate order. Front-recursive so a single unfold is available to the
    loop."""
    Requires(Acc(set_pred(parent_after), 1 / 4))
    Requires(Acc(set_pred(child), 1 / 4))
    if len(candidates) == 0:
        return PSeq(0).take(0)
    if qualifies(candidates[0], parent_after, child):
        return PSeq(candidates[0]) + selected(candidates.drop(1), parent_after, child)
    return selected(candidates.drop(1), parent_after, child)
# pure-end


def removed_base_field_prereqs(candidates: PSeq[int], parent_after: PSet[int],
                               child: PSet[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(set_pred(parent_after), 1 / 2))
    Requires(Acc(set_pred(child), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(parent_after), 1 / 2))
    Ensures(Acc(set_pred(child), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The emitted prerequisites are exactly the qualifying candidate names, in
    # candidate order: the deep set difference-then-intersection.
    Ensures(ToSeq(Result()) == selected(candidates, parent_after, child))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(candidates)
    while i > 0:
        # invariants-start
        Invariant(Acc(set_pred(parent_after), 1 / 2))
        Invariant(Acc(set_pred(child), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(candidates))
        Invariant(ToSeq(result) == selected(candidates.drop(i), parent_after, child))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = candidates[i - 1]
        Assert(candidates.drop(i - 1)[0] == c)
        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
        if (not (c in parent_after)) and (c in child):
            result = [c] + result
        i = i - 1
    return result
    # impl-end
