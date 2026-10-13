"""Twin-artifact model for pydata__xarray-6744.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A one-dimensional moving-window object can be traversed one element at a
  time. The i-th step exposes the contiguous block of the underlying sequence
  that the windowed reduction assigns to position i, given by a half-open
  index range [begin_i, end_i) into that sequence of length n. The block must
  be the SAME block the vectorised windowed reduction uses for position i, so
  that traversing element by element reproduces the vectorised result exactly.

  The window has a constant size w (w > 0) and a justification mode:

    * When the window is NOT centred, position i ends just past index i:
      end_i = i + 1, so the block looks back over the w entries ending at i.

    * When the window IS centred, position i is shifted forward so the block is
      symmetric about i. The forward shift is exactly ceil(w / 2): the block for
      position i ends at end_i = i + ceil(w / 2). (For w = 1 this collapses to
      the non-centred case, end_i = i + 1, since ceil(1/2) = 1.)

  In both modes the block begins w entries before its end but is clamped at the
  beginning of the sequence: begin_i = max(0, end_i - w). The justification mode
  is therefore observable ONLY through this forward shift of the block ends; the
  shift must depend on whether the window is centred, and must equal ceil(w / 2)
  when it is.

The underlying sequence length n, the window size w and the centred flag are
the only inputs that determine the index ranges; the ranges are plain integers,
so the model is exact integer arithmetic (no type refinement of the carrier).
There are no axiomatized callees: the index computation is the changed
operation and is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the index computation under specification is the
#  changed operation and is modelled deeply below; the underlying sequence
#  slicing it feeds is the unchanged caller, not a callee of this operation.)
# axioms-end


# pure-start
@Pure
def end_shift(w: int, center: bool) -> int:
    """Forward shift of every block end. Centred windows shift by ceil(w / 2)
    (so the block is symmetric about its position); otherwise by 1 (the block
    ends at its position)."""
    Requires(w > 0)
    Ensures(Result() >= 1)
    Ensures(Implies(not center, Result() == 1))
    Ensures(Implies(center, Result() == (w + 1) // 2))
    if center:
        return (w + 1) // 2
    return 1


@Pure
def end_at(i: int, w: int, center: bool) -> int:
    """End (exclusive) of the block at position i."""
    Requires(w > 0)
    Ensures(Result() == i + end_shift(w, center))
    return i + end_shift(w, center)


@Pure
def begin_at(i: int, w: int, center: bool) -> int:
    """Start (inclusive) of the block at position i: w entries before its end,
    clamped to the start of the sequence."""
    Requires(w > 0)
    Ensures(Result() >= 0)
    Ensures(Implies(end_at(i, w, center) - w >= 0, Result() == end_at(i, w, center) - w))
    Ensures(Implies(end_at(i, w, center) - w < 0, Result() == 0))
    raw = end_at(i, w, center) - w
    if raw > 0:
        return raw
    return 0


@Pure
def ends_from(j: int, n: int, w: int, center: bool) -> PSeq[int]:
    """The block ends for positions j, j+1, ..., n-1 in order. Front-recursive
    so callers get a single unfold per step."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Ensures(len(Result()) == n - j)
    if j == n:
        return PSeq(0).take(0)
    return PSeq(end_at(j, w, center)) + ends_from(j + 1, n, w, center)


@Pure
def begins_from(j: int, n: int, w: int, center: bool) -> PSeq[int]:
    """The block starts for positions j, j+1, ..., n-1 in order. Front-recursive
    so callers get a single unfold per step."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Ensures(len(Result()) == n - j)
    if j == n:
        return PSeq(0).take(0)
    return PSeq(begin_at(j, w, center)) + begins_from(j + 1, n, w, center)


@Pure
def ends_unfold(j: int, n: int, w: int, center: bool) -> bool:
    """Lemma: a single front-unfold of the block-end fold."""
    Requires(w > 0)
    Requires(0 <= j and j < n)
    Ensures(Result())
    Ensures(ends_from(j, n, w, center)
            == PSeq(end_at(j, w, center)) + ends_from(j + 1, n, w, center))
    return True


@Pure
def begins_unfold(j: int, n: int, w: int, center: bool) -> bool:
    """Lemma: a single front-unfold of the block-start fold."""
    Requires(w > 0)
    Requires(0 <= j and j < n)
    Ensures(Result())
    Ensures(begins_from(j, n, w, center)
            == PSeq(begin_at(j, w, center)) + begins_from(j + 1, n, w, center))
    return True


@Pure
def ends_index_lemma(j: int, m: int, n: int, w: int, center: bool) -> bool:
    """Lemma: the m-th entry of the block-end fold from j is the end of
    position j+m. Proven by front-recursion mirroring ends_from."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Requires(0 <= m and m < n - j)
    Ensures(Result())
    Ensures(ends_from(j, n, w, center)[m] == end_at(j + m, w, center))
    if m == 0:
        return True
    return ends_index_lemma(j + 1, m - 1, n, w, center)


@Pure
def begins_index_lemma(j: int, m: int, n: int, w: int, center: bool) -> bool:
    """Lemma: the m-th entry of the block-start fold from j is the start of
    position j+m. Proven by front-recursion mirroring begins_from."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Requires(0 <= m and m < n - j)
    Ensures(Result())
    Ensures(begins_from(j, n, w, center)[m] == begin_at(j + m, w, center))
    if m == 0:
        return True
    return begins_index_lemma(j + 1, m - 1, n, w, center)
# pure-end


def block_ends(n: int, w: int, center: bool) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(w > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == ends_from(0, n, w, center))
    # Each block end is its position shifted forward by end_shift(w, center):
    # the centred shift ceil(w/2) is what makes the traversal centre-justified.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           ends_index_lemma(0, i, n, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           Result()[i] == end_at(i, w, center)),
                                    [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    shift = end_shift(w, center)
    stops = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(stops)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(ends_unfold(k - 1, n, w, center))
        stops = [shift + (k - 1)] + stops
        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
        k = k - 1
    return stops
    # impl-end


def block_begins(n: int, w: int, center: bool) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(w > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == begins_from(0, n, w, center))
    # Each block begins w entries before its end, clamped to 0. Because the end
    # carries the justification shift, the start is centre-aware too.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           begins_index_lemma(0, i, n, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           Result()[i] == begin_at(i, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n, Result()[i] >= 0),
                                   [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    shift = end_shift(w, center)
    starts = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(starts)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(starts) == begins_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(begins_unfold(k - 1, n, w, center))
        raw = (shift + (k - 1)) - w
        if raw > 0:
            starts = [raw] + starts
        else:
            starts = [0] + starts
        Assert(starts[0] == begin_at(k - 1, w, center))
        Assert(ToSeq(starts) == PSeq(begin_at(k - 1, w, center)) + begins_from(k, n, w, center))
        k = k - 1
    return starts
    # impl-end
