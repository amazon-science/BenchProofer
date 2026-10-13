"""Twin-artifact model for sympy__sympy-21596.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A base domain of integer indices is filtered against two given index
  collections: a "keep" collection and a "drop" collection. An index k of the
  base domain belongs to the result if and only if k is a member of the keep
  collection AND k is not a member of the drop collection. The decision is made
  independently for each individual index against the two collections; an index
  is retained only on its own membership in the keep collection, so an
  arbitrary base index that is absent from the keep collection is necessarily
  excluded from the result. The result preserves the order of the base domain.

  The filtering is carried out in two ordered steps, each applied to the base
  domain in turn:

    1. an intersection step that keeps an index only if it is a member of the
       keep collection (the "keep" filter); then
    2. a difference step, applied to the result of step 1, that removes an index
       if it is a member of the drop collection (the "drop" filter).

  Applying the two steps in this order is exactly equivalent to deciding each
  index by both collections at once: the index belongs to the final result iff
  it survives both filters. The location at which each collection is applied is
  pinned individually -- the keep collection at the intersection step, the drop
  collection at the difference step.

The base domain, the keep collection, and the drop collection are each
modelled as `List[int]`. Membership and the resulting selection are carried by
the pure sequence theory `PSeq[int]`.

Markers (machine-parsed) delimit the spec / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed axioms: the keep/drop index collections are taken as given
# inputs; the per-index selection of the base domain against them is modelled
# deeply below.)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], v: int) -> bool:
    """Membership of v in the sequence s, front-recursive so a single unfold
    is available per recursive step."""
    if len(s) == 0:
        return False
    return s[0] == v or contains(s.drop(1), v)


@Pure
def survives(v: int, keep: PSeq[int], drop: PSeq[int]) -> bool:
    """An index v is retained iff it is a member of the keep collection and not
    a member of the drop collection. The decision is made per individual
    index."""
    return contains(keep, v) and not contains(drop, v)


@Pure
def kept_seq(base: PSeq[int], keep: PSeq[int], drop: PSeq[int]) -> PSeq[int]:
    """The retained subsequence of base: those indices that are retained,
    keeping the order of base. Front-recursive so a single unfold is available
    per loop step."""
    if len(base) == 0:
        return PSeq(0).take(0)
    if survives(base[0], keep, drop):
        return PSeq(base[0]) + kept_seq(base.drop(1), keep, drop)
    return kept_seq(base.drop(1), keep, drop)


@Pure
def keep_filter(base: PSeq[int], keep: PSeq[int]) -> PSeq[int]:
    """Step 1 (intersection with the keep collection): the subsequence of base
    whose indices are members of the keep collection, keeping the order of
    base. Front-recursive so a single unfold is available per loop step."""
    if len(base) == 0:
        return PSeq(0).take(0)
    if contains(keep, base[0]):
        return PSeq(base[0]) + keep_filter(base.drop(1), keep)
    return keep_filter(base.drop(1), keep)


@Pure
def drop_filter(seq: PSeq[int], drop: PSeq[int]) -> PSeq[int]:
    """Step 2 (difference with the drop collection): the subsequence of seq
    whose indices are NOT members of the drop collection, keeping the order of
    seq. Front-recursive so a single unfold is available per loop step."""
    if len(seq) == 0:
        return PSeq(0).take(0)
    if not contains(drop, seq[0]):
        return PSeq(seq[0]) + drop_filter(seq.drop(1), drop)
    return drop_filter(seq.drop(1), drop)


# pure-end


def collect_real_indices(base: List[int], keep: List[int],
                         drop: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(keep), 1 / 2))
    Requires(Acc(list_pred(drop), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(keep), 1 / 2))
    Ensures(Acc(list_pred(drop), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is EXACTLY the retained subsequence of the base domain: an
    # index is retained iff it is a member of the keep collection and not a
    # member of the drop collection. This pins membership precisely -- a base
    # index that is absent from the keep collection is necessarily absent from
    # the result, which is exactly the behaviour the issue demands.
    Ensures(ToSeq(Result()) ==
            kept_seq(ToSeq(base), ToSeq(keep), ToSeq(drop)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(drop), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(result) ==
                  kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = base[i - 1]
        Assert(ToSeq(base).drop(i - 1)[0] == c)
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        if survives(c, ToSeq(keep), ToSeq(drop)):
            result = [c] + result
        i = i - 1
    return result
    # impl-end


def collect_real_indices_two_step(base: List[int], keep: List[int],
                                  drop: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(keep), 1 / 2))
    Requires(Acc(list_pred(drop), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(keep), 1 / 2))
    Ensures(Acc(list_pred(drop), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Step 1 produces exactly the keep filter of the base domain (intersection
    # with the keep collection); the final result is the drop filter applied to
    # THAT (difference with the drop collection). The two collections are pinned
    # to their own steps: keep at the intersection, drop at the difference -- so
    # the result is the exact ordered composition of the two filters, each
    # index being decided by its own membership at each step.
    Ensures(ToSeq(Result()) ==
            drop_filter(keep_filter(ToSeq(base), ToSeq(keep)), ToSeq(drop)))
    # post-conditions-end
    # impl-start
    # Step 1: intersection with the keep collection (base_set &= keep-roots).
    kept = []  # type: List[int]
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(kept)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(kept) ==
                  keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = base[i - 1]
        Assert(ToSeq(base).drop(i - 1)[0] == c)
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        if contains(ToSeq(keep), c):
            kept = [c] + kept
        i = i - 1

    # Step 2: difference with the drop collection (base_set -= drop-roots),
    # applied to the result of step 1.
    result = []  # type: List[int]
    j = len(kept)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(drop), 1 / 2))
        Invariant(Acc(list_pred(kept), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(kept))
        Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
        Invariant(ToSeq(result) ==
                  drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        d = kept[j - 1]
        Assert(ToSeq(kept).drop(j - 1)[0] == d)
        Assert(ToSeq(kept).drop(j - 1).drop(1) == ToSeq(kept).drop(j))
        if not contains(ToSeq(drop), d):
            result = [d] + result
        j = j - 1

    return result
    # impl-end
