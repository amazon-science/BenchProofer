"""Twin-artifact model for django__django-14089.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An insertion-ordered collection of distinct elements supports enumeration in
  BOTH directions. Forward enumeration visits the elements in the order they
  were inserted; backward enumeration visits exactly the same elements in the
  opposite order. Concretely, the backward enumeration of the collection is the
  reversal of its forward enumeration: its first element is the collection's
  last element, its second element is the collection's second-to-last, and so
  on, so that element k of the backward enumeration is element (n-1-k) of the
  forward enumeration for a collection of n elements. Backward enumeration is a
  one-shot traversal (an iterator) and leaves the collection itself unchanged.

The ordered contents are modelled as `List[int]` of element keys in insertion
order (the collection stores distinct keys preserving their insertion order).
The specification is carried by the pure sequence theory `PSeq[int]`: `rev` is
the sequence-reversal the backward enumeration must equal. No callee is
axiomatized: the reversal is membership/structure logic over the input,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def rev(s: PSeq[int]) -> PSeq[int]:
    """The reversal of a sequence: the reversal of its tail followed by its
    head. Front-recursive (one unfold per element) so a backward impl loop that
    appends the head each step can discharge it."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return rev(s.drop(1)) + PSeq(s[0])
# pure-end


def reverse_order(elements: List[int]) -> List[int]:
    # pre-conditions-start
    # The collection's ordered contents are read-only: producing the backward
    # enumeration mutates nothing it is given, so the input is required AND
    # ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(elements), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elements), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The backward enumeration is exactly the reversal of the forward
    # enumeration: same elements, opposite order, same length. This pins the
    # discriminating behaviour — a traversal that preserves (rather than
    # reverses) the order, or drops/duplicates elements, cannot satisfy it.
    Ensures(ToSeq(Result()) == rev(ToSeq(elements)))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: no distinct backward enumeration is provided, so the
    # traversal hands back the elements in their forward (insertion) order.
    result = []  # type: List[int]
    i = len(elements)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elements), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(elements))
        Invariant(ToSeq(result) == ToSeq(elements).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = elements[i - 1]
        Assert(ToSeq(elements).drop(i - 1)[0] == e)
        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))
        result = [e] + result
        i = i - 1
    return result
    # impl-end
