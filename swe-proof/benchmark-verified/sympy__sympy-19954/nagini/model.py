"""Twin-artifact model for sympy__sympy-19954.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of candidate systems is maintained as several PARALLEL lists of
  equal length: the k-th entry of every list together describes the k-th
  candidate (its block partition, its numbering, its representative set). When,
  while scanning the candidates, some of them are found to be subsumed by a
  newly discovered candidate, those subsumed candidates must be discarded.

  Discarding is driven by a single removal decision per index, recorded as a
  boolean removal flag for each position (flag = True at position i means the
  i-th candidate is to be discarded). The desired behaviour is that EVERY
  parallel list is pruned by exactly the same per-position decision, taken from
  one consistent snapshot of the positions:

    * a candidate survives in the output iff its removal flag is False;
    * the survivors keep their original relative order;
    * because the very same flag list governs all three parallel lists, the
      three results stay perfectly aligned: they have equal length, and the
      k-th surviving entry of each output comes from the same original position.

  The result of pruning is fully determined by the input lists together with
  the single removal-flag list, and is independent of any order in which the
  positions are visited; every flagged position is discarded from all three
  lists and no other position is.

The candidate descriptors are modelled as opaque integer identities in
`List[int]` (Nagini has no set/partition type; the identity of each entry is all
that the pruning observes). The specification is carried by `PSeq[int]` /
`PSeq[bool]` via `ToSeq`. The pruning is modelled DEEPLY as the per-position
mask filter `filtered`; there is no external callee and therefore no consumed
axiom — `filtered` / `kept` are the spelled-out semantics of the operation, and
axiom_check.py validates them against real Python list-comprehension semantics
out-of-band (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callee: the changed operation is pure list pruning, modelled
# deeply by the `filtered` / `kept` folds in the pure region.)
# axioms-end


# pure-start
@Pure
def kept(flag: PSeq[bool]) -> int:
    """Number of positions that SURVIVE pruning: the count of False flags.
    Front-recursive so one unfold is available per loop step."""
    if len(flag) == 0:
        return 0
    return (0 if flag[0] else 1) + kept(flag.drop(1))


@Pure
def filtered(xs: PSeq[int], flag: PSeq[bool]) -> PSeq[int]:
    """Prune `xs` by the per-position flag: keep `xs[i]` iff `flag[i]` is False,
    survivors in original order. Front-recursive (single auto-unfold per step).
    The whole pruning behaviour is this function applied with ONE shared flag to
    every parallel list."""
    Requires(len(xs) == len(flag))
    if len(xs) == 0:
        return PSeq(0).take(0)
    if flag[0]:
        return filtered(xs.drop(1), flag.drop(1))
    return PSeq(xs[0]) + filtered(xs.drop(1), flag.drop(1))
# pure-end


def prune_parallel(blocks: List[int], nums: List[int], reps: List[int],
                   flag: List[bool]) -> Tuple[List[int], List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(blocks), 1 / 2))
    Requires(Acc(list_pred(nums), 1 / 2))
    Requires(Acc(list_pred(reps), 1 / 2))
    Requires(Acc(list_pred(flag), 1 / 2))
    # The lists are parallel: every list has the same length as the flag list.
    Requires(len(blocks) == len(flag))
    Requires(len(nums) == len(flag))
    Requires(len(reps) == len(flag))
    Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
    Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
    Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(blocks), 1 / 2))
    Ensures(Acc(list_pred(nums), 1 / 2))
    Ensures(Acc(list_pred(reps), 1 / 2))
    Ensures(Acc(list_pred(flag), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    # The parallel inputs are read-only and preserved: their lengths still
    # match the flag list, so the filter below is well-formed.
    Ensures(len(ToSeq(blocks)) == len(ToSeq(flag)))
    Ensures(len(ToSeq(nums)) == len(ToSeq(flag)))
    Ensures(len(ToSeq(reps)) == len(ToSeq(flag)))
    # Each parallel list is pruned by exactly the same per-position flag.
    Ensures(ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag)))
    Ensures(ToSeq(Result()[1]) == filtered(ToSeq(nums), ToSeq(flag)))
    Ensures(ToSeq(Result()[2]) == filtered(ToSeq(reps), ToSeq(flag)))
    # Consequently the three results stay perfectly aligned: equal length, each
    # equal to the number of surviving (False-flagged) positions.
    Ensures(len(Result()[0]) == kept(ToSeq(flag)))
    Ensures(len(Result()[1]) == kept(ToSeq(flag)))
    Ensures(len(Result()[2]) == kept(ToSeq(flag)))
    Ensures(len(Result()[0]) == len(Result()[1]))
    Ensures(len(Result()[1]) == len(Result()[2]))
    # post-conditions-end
    # impl-start
    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    i = len(flag)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(blocks), 1 / 2))
        Invariant(Acc(list_pred(nums), 1 / 2))
        Invariant(Acc(list_pred(reps), 1 / 2))
        Invariant(Acc(list_pred(flag), 1 / 2))
        Invariant(Acc(list_pred(out_blocks)))
        Invariant(Acc(list_pred(out_nums)))
        Invariant(Acc(list_pred(out_reps)))
        Invariant(len(blocks) == len(flag))
        Invariant(len(nums) == len(flag))
        Invariant(len(reps) == len(flag))
        Invariant(0 <= i and i <= len(flag))
        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
                                                ToSeq(flag).drop(i)))
        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
                                              ToSeq(flag).drop(i)))
        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
                                              ToSeq(flag).drop(i)))
        # The survivor count tracks `kept` over the still-unprocessed suffix,
        # so at i == 0 every output has length kept(ToSeq(flag)).
        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        b = blocks[i - 1]
        n = nums[i - 1]
        r = reps[i - 1]
        f = flag[i - 1]
        # the (i-1)-th position is the head of the suffix beginning at i-1;
        # dropping it leaves the suffix beginning at i.
        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
        Assert(ToSeq(nums).drop(i - 1)[0] == n)
        Assert(ToSeq(reps).drop(i - 1)[0] == r)
        Assert(ToSeq(flag).drop(i - 1)[0] == f)
        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
        if f:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        else:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        i = i - 1
    res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
    return res
    # impl-end
