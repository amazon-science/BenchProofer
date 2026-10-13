"""Twin-artifact model for sympy__sympy-13615.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Removing the members of one set from a finite collection of elements, when
  membership of an element cannot always be decided.  For each element of the
  finite collection a three-valued membership oracle reports one of:

      * DEFINITELY-IN  - the element is certainly a member of the set being
        removed;
      * DEFINITELY-OUT - the element is certainly NOT a member;
      * UNDECIDED       - membership cannot be settled (e.g. the element is a
        free placeholder whose value is unknown).

  The result partitions the elements into TWO collections, preserving the
  original order within each:

      * the DEFINITELY-OUT elements form a concrete finite collection - they
        are known to survive the removal;
      * the UNDECIDED elements are NOT discarded and NOT asserted to survive;
        they are carried in a separate, still-pending collection that records
        that their membership is unresolved.

  The DEFINITELY-IN elements appear in neither collection.  The essential
  property: an element whose membership is UNDECIDED must never be placed in
  the concrete "survivors" collection, because doing so would silently assert a
  fact (that it is not a member) that has not been established; it belongs only
  to the pending collection.

Elements are modelled as opaque integer handles; the membership oracle is an
unchanged deterministic pure callee over those handles, collapsed to the three
verdicts {DEFINITELY_OUT=0, DEFINITELY_IN=1, UNDECIDED=2} (axioms region).  The
two output collections are returned as a pair of `List[int]`; the specification
of each is carried by `PSeq[int]` via `ToSeq`, as the order-preserving
sub-selection of the input by verdict (the front-recursive folds `keep_out` /
`keep_undecided`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


DEFINITELY_OUT = 0
DEFINITELY_IN = 1
UNDECIDED = 2


# axioms-start
@Pure
@ContractOnly
def verdict(el: int) -> int:
    """The unchanged membership oracle, as a deterministic map over element
    handles collapsed to three verdicts: 0 = DEFINITELY-OUT (certainly not a
    member), 1 = DEFINITELY-IN (certainly a member), 2 = UNDECIDED (membership
    cannot be settled).  Only totality + the three-value range is relied upon:
    every element is classified into exactly one verdict, and the impl reads the
    SAME verdict the spec folds read (determinism).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(0 <= Result() and Result() <= 2)
# axioms-end


# pure-start
@Pure
def keep_out(s: PSeq[int]) -> PSeq[int]:
    """Order-preserving sub-selection of the elements whose verdict is
    DEFINITELY-OUT.  Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if verdict(s[0]) == DEFINITELY_OUT:
        return PSeq(s[0]) + keep_out(s.drop(1))
    return keep_out(s.drop(1))


@Pure
def keep_undecided(s: PSeq[int]) -> PSeq[int]:
    """Order-preserving sub-selection of the elements whose verdict is
    UNDECIDED.  Front-recursive (one unfold per loop step)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if verdict(s[0]) == UNDECIDED:
        return PSeq(s[0]) + keep_undecided(s.drop(1))
    return keep_undecided(s.drop(1))
# pure-end


def complement_finite(other: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(other), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(other), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The survivors collection (component 0) is EXACTLY the DEFINITELY-OUT
    # elements, in order.
    Ensures(ToSeq(Result()[0]) == keep_out(ToSeq(other)))
    # The pending collection (component 1) is EXACTLY the UNDECIDED elements,
    # in order.
    Ensures(ToSeq(Result()[1]) == keep_undecided(ToSeq(other)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    undecided = []  # type: List[int]
    i = len(other)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(Acc(list_pred(undecided)))
        Invariant(0 <= i and i <= len(other))
        # invariants-end
        e = other[i - 1]
        v = verdict(e)
        # Pre-patch skeleton: every element that is NOT DEFINITELY-IN is placed
        # in the concrete survivors collection -- the UNDECIDED elements are
        # treated as if their membership had been resolved to "not a member",
        # and the pending collection is never populated.
        if v != DEFINITELY_IN:
            out = [e] + out
        i = i - 1
    return out, undecided
    # impl-end
