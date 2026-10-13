"""Twin-artifact model for sphinx-doc__sphinx-10466.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A translatable message accumulates a record of every place it occurs while a
  document set is scanned. Each occurrence carries a source identity and a line
  number, i.e. a comparable position. The same position can be recorded more
  than once (a message may be emitted repeatedly from the very same place), and
  occurrences arrive in scan order, which need not be sorted.

  When the catalogue is later enumerated for output, the sequence of positions
  reported for a message must be the CANONICAL position list: every distinct
  recorded position appears exactly once (no position is repeated) and the
  positions are listed in ascending order. Equivalently, the reported list is
  the ORDERED SET of the recorded positions: the deduplicated, strictly
  ascending arrangement of exactly the positions that were recorded. This makes
  the reported list independent of how many times, and in what order, a position
  happened to be recorded.

A recorded occurrence's position (a source identity together with a line
number) is modelled by a single integer key under the order-preserving,
equality-preserving identification of comparable positions with integers
(mapping.md). The recorded positions are a `List[int]`; the canonical reported
list is a `List[int]`. The specification is carried deeply by a pure
ordered-set construction (`dedup_sort`) over `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the deduplicate-and-sort behaviour is the operation
# under specification and is modelled deeply, not behind an axiom.)
# axioms-end


# pure-start
@Pure
def ins(x: int, s: PSeq[int]) -> PSeq[int]:
    """Insert `x` into `s` just before the first element that is not below it,
    dropping `x` if it already occurs there. On a strictly-sorted `s` this is
    ordered-set insertion. Total (no quantified precondition) and front-
    recursive over `s` (one unfold per element)."""
    if len(s) == 0:
        return PSeq(x)
    if x < s[0]:
        return PSeq(x) + s
    if x == s[0]:
        return s
    return PSeq(s[0]) + ins(x, s.drop(1))


@Pure
def dedup_sort(s: PSeq[int]) -> PSeq[int]:
    """The ordered set of `s`: deduplicated and strictly ascending. Built by
    inserting the last element into the ordered set of the prefix, so the
    enumeration loop (which appends one recorded position at a time) tracks it
    with the invariant `result == dedup_sort(prefix)`."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return ins(s[len(s) - 1], dedup_sort(s.take(len(s) - 1)))
# pure-end


def insert_sorted(xs: List[int], key: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the impl computes exactly the pure ordered-set insertion.
    Ensures(ToSeq(Result()) == ins(key, ToSeq(xs)))
    # post-conditions-end
    # impl-start
    # Scan front-to-back, emitting each element until the slot for `key` is
    # found. The loop invariant peels `ins` one element at a time off the unseen
    # suffix `drop(j)` (matching `ins`'s own front recursion), so no auxiliary
    # sequence lemma is needed: the full answer always equals what has been
    # emitted, followed by the insertion into the remaining suffix.
    out = []  # type: List[int]
    j = 0
    placed = False  # type: bool
    while j < len(xs):
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(xs))
        # not yet placed: the answer is `out` followed by `ins` of the suffix.
        Invariant(Implies(not placed,
                          ins(key, ToSeq(xs)) == ToSeq(out) + ins(key, ToSeq(xs).drop(j))))
        # placed: the answer is `out` followed by the suffix copied verbatim.
        Invariant(Implies(placed,
                          ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
        Invariant(MustTerminate(len(xs) - j + 1))
        # invariants-end
        cur = xs[j]
        # `ins`/`drop` unfold once on the suffix whose head is `cur`.
        Assert(ToSeq(xs).drop(j) == PSeq(cur) + ToSeq(xs).drop(j + 1))
        Assert(len(ToSeq(xs).drop(j)) > 0 and ToSeq(xs).drop(j)[0] == cur)
        if placed:
            out = out + [cur]
        elif cur < key:
            out = out + [cur]
        elif cur > key:
            # `ins(key, suffix) == [key] + suffix`; emit `key` then `cur`.
            out = out + [key]
            out = out + [cur]
            placed = True
        else:
            # `cur == key`: `ins(key, suffix) == suffix`; `key` already present.
            out = out + [cur]
            placed = True
        j = j + 1
    Assert(ToSeq(xs).drop(j) == ToSeq(xs).drop(len(xs)))
    Assert(ToSeq(xs).drop(len(xs)) == PSeq(0).take(0))
    if not placed:
        # the suffix is empty: `ins(key, [])== [key]`.
        out = out + [key]
    return out
    # impl-end


def canonical_positions(recorded: List[int]) -> List[int]:
    # pre-conditions-start
    # The recorded-positions list is read-only here (enumeration never mutates
    # it); fractional permission, required and ensured, so no caller can satisfy
    # a postcondition vacuously by overwriting the input.
    Requires(Acc(list_pred(recorded), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(recorded), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reported list is exactly the ordered set of the recorded positions:
    # the deduplicated, strictly ascending arrangement of exactly what was
    # recorded.
    Ensures(ToSeq(Result()) == dedup_sort(ToSeq(recorded)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(recorded):
        # invariants-start
        Invariant(Acc(list_pred(recorded), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(recorded))
        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
        Invariant(MustTerminate(len(recorded) - i + 1))
        # invariants-end
        key = recorded[i]
        Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
        Assert(ToSeq(recorded).take(i + 1)[i] == key)
        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
        result = insert_sorted(result, key)
        i = i + 1
    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
    return result
    # impl-end
