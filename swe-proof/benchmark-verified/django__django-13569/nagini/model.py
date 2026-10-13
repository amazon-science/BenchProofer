"""Twin-artifact model for django__django-13569.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the columns that an ORDER BY clause contributes to a GROUP BY clause are
  assembled, each ordering term offers the set of grouping columns it depends
  on. A term that selects rows in a *non-deterministic* order — an order that
  is not a function of any stored column — depends on NO column, and must
  therefore contribute NOTHING to the grouping.

  Concretely, two behaviours are pinned:

    (1) The grouping columns offered by a single non-deterministic ordering
        term are EMPTY. A deterministic ordering term over a stored column
        still offers exactly that one column.

    (2) The grouping columns gathered from a whole list of ordering terms are
        the concatenation, in order, of the columns each term offers, with
        reference terms (those already represented in the selected columns)
        skipped. Because a non-deterministic term offers nothing, no such term
        ever appears among the gathered grouping columns — so an aggregation
        accompanied by a non-deterministic ordering is grouped exactly as it
        would be without that ordering.

An ordering term is modelled as a minimal record exposing only the touched
fields: whether it is non-deterministic, whether it is a reference into the
already-selected columns, and the identity of the single stored column a
deterministic term depends on. A list of terms is carried by index-aligned
`List[int]`; the gathered grouping columns are a `List[int]` of column
identities, specified via `PSeq[int]`.

No callee is axiomatized: the per-term column contribution and its gathering
are modelled deeply. The default per-term contribution (a deterministic term
offers its one column) is the unchanged base behaviour; the non-deterministic
term offering nothing is the behaviour under change, modelled directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the per-term grouping-column contribution and its
# gathering over an ordering list are pure data-flow, modelled deeply.
# axioms-end


# pure-start
@Pure
def offered_cols(is_nondet: int, colid: int) -> PSeq[int]:
    """The grouping columns a single ordering term offers.

    A non-deterministic ordering term (is_nondet != 0) depends on no stored
    column, so it offers the empty sequence. A deterministic term offers
    exactly the one stored column it depends on."""
    if is_nondet != 0:
        return PSeq(0).take(0)
    return PSeq(colid)


@Pure
def gathered(nondet: PSeq[int], ref: PSeq[int], cols: PSeq[int]) -> PSeq[int]:
    """Grouping columns gathered from a whole list of ordering terms.

    Front-recursive on the sequence structure (drop the head, recurse on the
    tail) so a single unfold is available per loop step: the head term (unless
    it is a reference) offers `offered_cols`, prepended to the columns gathered
    from the tail. The three index-aligned sequences are consumed in lockstep;
    the recursion stops as soon as any of them is exhausted (in use they are of
    equal length, so this is precisely 'all terms consumed')."""
    if len(nondet) == 0 or len(ref) == 0 or len(cols) == 0:
        return PSeq(0).take(0)
    if ref[0] != 0:
        return gathered(nondet.drop(1), ref.drop(1), cols.drop(1))
    return offered_cols(nondet[0], cols[0]) + gathered(
        nondet.drop(1), ref.drop(1), cols.drop(1))
# pure-end


def random_group_by_cols(colid: int) -> List[int]:
    """The grouping columns offered by a single non-deterministic ordering
    term whose own column identity is `colid`."""
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A non-deterministic ordering term offers NO grouping column.
    Ensures(len(Result()) == 0)
    Ensures(ToSeq(Result()) == offered_cols(1, colid))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    return result
    # impl-end


def group_by_columns_for_ordering(nondet: List[int], ref: List[int],
                                  cols: List[int]) -> List[int]:
    """Gather, in order, the grouping columns offered by a list of ordering
    terms. `nondet[k]`/`ref[k]`/`cols[k]` describe term k: whether it is
    non-deterministic, whether it is a reference into the selected columns
    (then skipped), and its own column identity."""
    # pre-conditions-start
    Requires(Acc(list_pred(nondet), 1 / 2))
    Requires(Acc(list_pred(ref), 1 / 2))
    Requires(Acc(list_pred(cols), 1 / 2))
    Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(nondet), 1 / 2))
    Ensures(Acc(list_pred(ref), 1 / 2))
    Ensures(Acc(list_pred(cols), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == gathered(ToSeq(nondet), ToSeq(ref),
                                         ToSeq(cols)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(nondet)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        # `result` already holds the columns gathered from the tail [i, n).
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
        # unfolding `gathered` on it takes the recursive branch. Link the list
        # values to the head elements of the dropped tails so the unfold's
        # internal head reads agree with the branch taken below.
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] != 0:
            # A reference term offers nothing: gathered(tail j) == gathered(i).
            result = result
        elif nondet[i - 1] != 0:
            contributed = random_group_by_cols(cols[i - 1])
            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
            # both arguments are non-zero, so both are the empty sequence.
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   offered_cols(1, cols[i - 1]))
            result = contributed + result
        else:
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   PSeq(cols[i - 1]))
            result = [cols[i - 1]] + result
        i = i - 1
    return result
    # impl-end
