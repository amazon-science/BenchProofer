"""Twin-artifact model for pydata__xarray-4094.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A stacked collection is reconstructed back into its original group of named
  members. The collection arranges several named members along one shared axis
  whose tick labels are PAIRS: each tick pairs a member identifier with one
  position label. The reconstruction, for each member identifier `k`, takes the
  slice of the axis whose member-identifier component equals `k`, and combines
  the per-member slices into one collection that must equal the original group.

  A per-member slice is taken by the selection under a flag `discard`. The
  annotation it carries for its member is `carried(discard, position)` -- a value
  determined by that one taking, the same function of `discard` for every member.
  The
  combination step combines the per-member slices into one collection. It
  inspects the annotation each slice carries -- over the members' (pairwise
  distinct) positions, under the SAME selection -- and succeeds, returning the
  members' values verbatim, iff every member carries the same value for that
  shared-name annotation; otherwise it is rejected.

  Desired roundtrip property: the reconstruction recovers every member's value
  verbatim, and the recovered collection is the OUTPUT of the combination over
  the members' positions (it cannot be produced any other way -- the
  reconstruction must go through the combination, which is rejected unless the
  per-member slices carry one common shared-name annotation).

Modelling: the members are indexed `0..n-1`. `data[k]` is the value carried by
member `k`; the reconstruction recovers it verbatim. The position label paired
with member `k` is `resid[k]`, pairwise distinct across members in the shape this
bundle pins. The selection callee `carried(discard, position)` gives the
annotation a slice carries. The combination callee `assemble` combines the
per-member slices: it inspects the annotations the slices carry over the members'
distinct positions under the SAME selection -- `carried_seq(discard, resid)` --
succeeds iff they are all equal (`all_equal`), returns each member's value
verbatim, and grants the `combined_collection` token marking its output. The
reconstruction's result must hold that token, so the combination is mandatory.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def shared_value() -> int:
    """The single annotation value common to every slice when the selection
    yields no distinguishing per-member annotation. A single constant, identical
    across all members. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(True)


@Pure
@ContractOnly
def carried(discard: bool, position: int) -> int:
    """Selection callee. The annotation value a per-member slice carries for its
    position, as a function of the selection's `discard` flag and the member's
    `position` label: the member's own position label when `discard` is false,
    the single shared value common to every slice when `discard` is true.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(not discard, Result() == position))
    Ensures(Implies(discard, Result() == shared_value()))


# Abstract token marking THE VERY OBJECT that was PRODUCED BY the combination
# step over the members' positions: a capability `assemble` grants on its output
# object and that nothing else can fabricate. It is keyed by the object itself
# (a reference), not by its value, so a value-equal collection built anywhere
# else does not hold it. The reconstruction's result must hold it, so the result
# can only be the output of the combination itself (the combination can neither
# be bypassed nor laundered through a value-equal copy). Provenance + executable
# soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def combined_collection(collection: List[int], positions: PSeq[int]) -> bool:
    pass


@ContractOnly
def assemble(slices: List[int], resid: List[int], discard: bool) -> List[int]:
    """Combination callee that combines the per-member slices into one
    collection. The slices were taken under the flag `discard` and the members
    sit at the pairwise-distinct positions `resid` (the position state intrinsic
    to the slices). The combination inspects the annotation each slice carries
    under that selection -- `carried_seq(discard, resid)` -- and REQUIRES that
    they agree across members (`all_equal`). A shared-name annotation carrying
    two different values is a conflict and the combination is rejected (its
    precondition is violated). On success it returns each member's value verbatim
    and grants the `combined_collection` token on its output over `resid`.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(slices), 1 / 2))
    Requires(Acc(list_pred(resid), 1 / 2))
    Requires(len(resid) == len(slices))
    # the positions intrinsic to the slices are pairwise distinct (the shape this
    # bundle pins) -- not a separate all-equal list the caller can fabricate.
    Requires(distinct_residuals(ToSeq(resid)))
    # the combination is rejected unless the annotations the slices carry under
    # this selection agree across members.
    Requires(all_equal(carried_seq(discard, ToSeq(resid))))
    Ensures(Acc(list_pred(slices), 1 / 2))
    Ensures(Acc(list_pred(resid), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(slices))
    Ensures(ToSeq(Result()) == ToSeq(slices))
    # the output OBJECT is marked as the combination's product over these
    # positions (the token sits on the returned reference itself).
    Ensures(combined_collection(Result(), ToSeq(resid)))
# axioms-end


# pure-start
@Pure
def distinct_residuals(resid: PSeq[int]) -> bool:
    """The members occupy pairwise-distinct position labels -- the shape this
    bundle pins, where each member sits at its own position. (When the slices
    carry that position annotation, distinctness is exactly what makes two
    members disagree on it; it also rules out a fabricated all-equal position
    list.)"""
    return Forall(int, lambda i:
        (Forall(int, lambda j:
            (Implies(0 <= i and i < j and j < len(resid),
                     resid[i] != resid[j]),
             [[resid[i], resid[j]]])),
         []))


@Pure
def all_equal(xs: PSeq[int]) -> bool:
    """The per-slice annotations agree -- the combination succeeds iff the
    shared-name annotation carries one common value across all members. Defined
    by adjacent equality (head equals the next entry and the tail is all-equal),
    equivalent for a sequence to every entry being equal. With pairwise-distinct
    positions and at least two members, the members' own positions are NOT
    all-equal (entries 0 and 1 differ), while the single shared value IS."""
    if len(xs) <= 1:
        return True
    return xs[0] == xs.drop(1)[0] and all_equal(xs.drop(1))


@Pure
def carried_seq(discard: bool, positions: PSeq[int]) -> PSeq[int]:
    """The annotation each slice carries over a sequence of member positions:
    element-wise `carried(discard, .)`. Front-recursive (no contract, so it
    unfolds one level per loop step -- the canonical sequence-fold pattern)."""
    if len(positions) == 0:
        return PSeq(0).take(0)
    return PSeq(carried(discard, positions[0])) + carried_seq(discard, positions.drop(1))
# pure-end


def lemma_carried_len(discard: bool, positions: PSeq[int]) -> None:
    """Lemma: the annotation list has one entry per member:
    `len(carried_seq(discard, positions)) == len(positions)`. Induction on the
    front-recursive fold."""
    Ensures(len(carried_seq(discard, positions)) == len(positions))
    if len(positions) > 0:
        lemma_carried_len(discard, positions.drop(1))


def lemma_carried_all_equal(positions: PSeq[int]) -> None:
    """Lemma: when the selection yields the single shared annotation
    (`discard` true), the annotation list is all-equal:
    `all_equal(carried_seq(True, positions))`. Every entry is the one shared
    value, so adjacent entries agree. Proved by induction on the front-recursive
    fold; phrased with concat indexing / drop only, never PSeq-literal equality
    (which Nagini cannot derive from element equality)."""
    Ensures(all_equal(carried_seq(True, positions)))
    lemma_carried_len(True, positions)
    if len(positions) > 1:
        lemma_carried_all_equal(positions.drop(1))
        lemma_carried_len(True, positions.drop(1))
        Assert(len(carried_seq(True, positions)) == len(positions))
        Assert(carried_seq(True, positions)[0] == carried(True, positions[0]))
        Assert(carried_seq(True, positions).drop(1) ==
               carried_seq(True, positions.drop(1)))
        Assert(carried_seq(True, positions.drop(1))[0] ==
               carried(True, positions.drop(1)[0]))
        Assert(carried(True, positions[0]) == shared_value())
        Assert(carried(True, positions.drop(1)[0]) == shared_value())


def to_unstacked(n: int, data: List[int], resid: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(Acc(list_pred(data), 1 / 2))
    Requires(Acc(list_pred(resid), 1 / 2))
    Requires(len(data) == n)
    Requires(len(resid) == n)
    # at least two members so a shared position annotation has two values to
    # disagree over (the shape this bundle pins)
    Requires(n >= 2)
    # the members sit at pairwise-distinct positions, so a position annotation
    # carried under a shared name would carry conflicting values
    Requires(distinct_residuals(ToSeq(resid)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(data), 1 / 2))
    Ensures(Acc(list_pred(resid), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the reconstruction recovers each member's value verbatim (the roundtrip is
    # the identity)
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == ToSeq(data))
    # the recovered collection IS the output object of the combination over the
    # members' distinct positions -- it holds the object-keyed token only the
    # combination grants on its own output, so the reconstruction can neither
    # bypass the combination (whose guard is rejected unless every per-member
    # slice carries one common shared-name annotation) nor substitute a
    # value-equal copy that never went through it.
    Ensures(combined_collection(Result(), ToSeq(resid)))
    # post-conditions-end
    # impl-start
    # one selection flag drives the whole reconstruction: each per-member slice
    # is taken under the SAME `discard`, which fixes the annotation it carries
    # over the members' positions; the combination reads exactly those
    # annotations over those same positions -- there is no separate annotation
    # the impl can supply, and the result must be the combination's output.
    # Pre-patch skeleton: the selection does NOT discard the per-member position
    # annotation (the default selection behaviour), so each slice carries its own
    # distinct position; with members at distinct positions these conflict and the
    # combination is rejected.
    discard = False
    data_dict = []  # type: List[int]
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(data), 1 / 2))
        Invariant(Acc(list_pred(resid), 1 / 2))
        Invariant(Acc(list_pred(data_dict)))
        Invariant(0 <= i and i <= n)
        Invariant(len(data) == n)
        Invariant(len(resid) == n)
        Invariant(len(data_dict) == n - i)
        Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
        Invariant(distinct_residuals(ToSeq(resid)))
        # invariants-end
        # take member i-1's slice under `discard`, recovering its value verbatim.
        selected = data[i - 1]
        data_dict = [selected] + data_dict
        i = i - 1
    Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
    Assert(ToSeq(data).drop(0) == ToSeq(data))
    # under this selection each slice carries its own distinct position, so the
    # annotations do NOT agree across members and the combination is rejected.
    lemma_carried_all_equal(ToSeq(resid))
    Assert(distinct_residuals(ToSeq(resid)))
    Assert(len(resid) == len(data_dict))
    # combine the slices under the SAME `discard` over the members' distinct
    # positions; the result is the combination's output (holding its token).
    result = assemble(data_dict, resid, discard)
    return result
    # impl-end
