"""Twin-artifact model for django__django-7530.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A pre-flight check consults a per-database routing policy with one
  (group, member) pair for every member that should be examined for a given
  group. The project keeps a flat roster of members; each member belongs to
  exactly one group. The roster is two aligned streams: `owner[k]` is the
  group of the k-th member and `member[k]` is that member's identifier.

  When the examined members for a group `target` are gathered, the gathered
  sequence must be EXACTLY the members that belong to `target`, in roster
  order: a member is gathered iff its recorded group equals `target`. No member
  of a different group is offered for this group (which would feed the routing
  policy a combination that does not exist — a member of one group presented
  under a different group's label), and no member belonging to `target` is
  omitted.

Members and groups are modelled as `List[int]` identifiers; the specification is
carried by the pure sequence theory `PSeq[int]`. The selection is modelled
DEEPLY as a front-recursive membership filter (`gathered`); nothing is consumed
as an axiom — the real roster lookup is validated == this deep model by
axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The members-for-a-group selection is the
#  operation under specification; it is modelled DEEPLY in the `pure` region and
#  the verified impl as the spelled-out membership filter over the roster, and
#  validated == the real roster lookup by axiom_check.py / G-AX as an
#  A-reference. Nothing here is consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def gathered(owner: PSeq[int], member: PSeq[int], target: int) -> PSeq[int]:
    """The members belonging to `target`, in roster order: the front-to-back
    concatenation of each member kept iff its recorded group equals `target`.
    Front-recursive so a single unfold is available per loop step."""
    if len(owner) == 0 or len(member) == 0:
        return PSeq(0).take(0)
    if owner[0] == target:
        return PSeq(member[0]) + gathered(owner.drop(1), member.drop(1), target)
    return gathered(owner.drop(1), member.drop(1), target)
# pure-end


def members_for_group(owner: List[int], member: List[int], target: int) -> List[int]:
    # pre-conditions-start
    # The roster is read-only: gathering members mutates nothing it is given,
    # so each stream is required AND ensured at fractional permission
    # (directive 5). The two streams are aligned one entry per member.
    Requires(Acc(list_pred(owner), 1 / 2))
    Requires(Acc(list_pred(member), 1 / 2))
    Requires(len(owner) == len(member))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(owner), 1 / 2))
    Ensures(Acc(list_pred(member), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The gathered sequence is EXACTLY the members belonging to `target`, in
    # roster order. This pins the discriminating behaviour: every gathered
    # member is one whose group is `target` (soundness — no foreign-group member
    # is offered under this group's label) and every member of `target` is
    # present (completeness).
    Ensures(ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(owner)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(owner), 1 / 2))
        Invariant(Acc(list_pred(member), 1 / 2))
        Invariant(len(owner) == len(member))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(owner))
        Invariant(ToSeq(result) ==
                  gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        o = owner[i - 1]
        m = member[i - 1]
        Assert(ToSeq(owner).drop(i - 1)[0] == o)
        Assert(ToSeq(member).drop(i - 1)[0] == m)
        Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
        Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
        if o == target:
            result = [m] + result
        i = i - 1
    return result
    # impl-end
