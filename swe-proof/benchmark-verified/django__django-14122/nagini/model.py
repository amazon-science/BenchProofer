"""Twin-artifact model for django__django-14122.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A grouping-key list is assembled for an aggregating query. It is built from
  several contributing sources, each yielding zero or more grouping-column
  tokens that are appended in order:

    * the selected-column source contributes its tokens unconditionally;
    * the result-ordering source contributes the tokens of its entries, but
      only those entries that are NOT mere back-references to an
      already-grouped selected column (a back-referenced entry is skipped,
      because its column is already part of the grouping key);
    * a trailing source contributes its tokens unconditionally.

  The discriminating behaviour: the result-ordering source contributes to the
  grouping key ONLY when the ordering was explicitly requested for this query.
  When the ordering is merely the model's DEFAULT ordering — a presentation
  preference, not part of the aggregation request — its entries must NOT be
  folded into the grouping key, because doing so would split the aggregation
  into spurious groups. So with a default (implicit) ordering active the
  grouping key is exactly the selected-column tokens followed by the trailing
  tokens, with no ordering tokens at all.

Each contributing token is modelled as an `int` identifier; the carrier of a
token list is `List[int]`, and the specification is carried over `PSeq[int]`
via `ToSeq`. The conditional inclusion is the changed operation and is
modelled DEEPLY as the spelled-out fold; there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: every contributing source's token list and the
#  conditional inclusion are expressible directly over PSeq[int].)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    return PSeq(0).take(0)


@Pure
def order_contrib(cols: PSeq[int], refs: PSeq[int]) -> PSeq[int]:
    """The grouping tokens contributed by the result-ordering source: the token
    of each entry that is NOT a back-reference, in order. `refs[k] != 0` marks
    entry k as a back-reference (skipped); `refs[k] == 0` keeps it.

    Back-recursive (recurses on the leading prefix and appends the last entry's
    contribution) so that extending the processed prefix by one entry — the
    direction a forward accumulating loop grows — is a single unfold. Defined
    for `len(cols) == len(refs)`."""
    Requires(len(cols) == len(refs))
    if len(cols) == 0:
        return empty_seq()
    if refs[len(refs) - 1] != 0:
        return order_contrib(cols.take(len(cols) - 1), refs.take(len(refs) - 1))
    return (order_contrib(cols.take(len(cols) - 1), refs.take(len(refs) - 1))
            + PSeq(cols[len(cols) - 1]))
# pure-end


def assemble_grouping_key(select_cols: List[int], order_cols: List[int],
                   order_is_backref: List[int], trailing_cols: List[int],
                   ordering_was_requested: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(select_cols), 1 / 2))
    Requires(Acc(list_pred(order_cols), 1 / 2))
    Requires(Acc(list_pred(order_is_backref), 1 / 2))
    Requires(Acc(list_pred(trailing_cols), 1 / 2))
    # The ordering source carries one ref-flag per entry.
    Requires(len(order_cols) == len(order_is_backref))
    Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(select_cols), 1 / 2))
    Ensures(Acc(list_pred(order_cols), 1 / 2))
    Ensures(Acc(list_pred(order_is_backref), 1 / 2))
    Ensures(Acc(list_pred(trailing_cols), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
    # When the ordering was explicitly requested, the result-ordering source
    # folds its NON-back-reference tokens into the grouping key, between the
    # selected-column tokens and the trailing tokens.
    Ensures(Implies(
        ordering_was_requested,
        ToSeq(Result())
        == ToSeq(select_cols)
        + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
        + ToSeq(trailing_cols)))
    # Discriminating clause: when the ordering is the model's DEFAULT ordering
    # (not explicitly requested), NONE of its tokens enter the grouping key —
    # the key is exactly the selected-column tokens followed by the trailing
    # tokens.
    Ensures(Implies(
        not ordering_was_requested,
        ToSeq(Result()) == ToSeq(select_cols) + ToSeq(trailing_cols)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # selected-column source (unconditional)
    s = 0
    while s < len(select_cols):
        # invariants-start
        Invariant(Acc(list_pred(select_cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= s and s <= len(select_cols))
        Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
        Invariant(MustTerminate(len(select_cols) - s + 1))
        # invariants-end
        result.append(select_cols[s])
        s = s + 1
    Assert(ToSeq(result) == ToSeq(select_cols))
    # result-ordering source (only when the ordering was explicitly requested)
    if ordering_was_requested:
        Assert(order_contrib(ToSeq(order_cols).take(0),
                             ToSeq(order_is_backref).take(0)) == empty_seq())
        k = 0
        while k < len(order_cols):
            # invariants-start
            Invariant(Acc(list_pred(select_cols), 1 / 2))
            Invariant(Acc(list_pred(order_cols), 1 / 2))
            Invariant(Acc(list_pred(order_is_backref), 1 / 2))
            Invariant(len(order_cols) == len(order_is_backref))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= k and k <= len(order_cols))
            Invariant(ToSeq(result)
                      == ToSeq(select_cols)
                      + order_contrib(ToSeq(order_cols).take(k),
                                      ToSeq(order_is_backref).take(k)))
            Invariant(MustTerminate(len(order_cols) - k + 1))
            # invariants-end
            is_ref = order_is_backref[k]
            col = order_cols[k]
            # Extending the processed prefix by entry k is a single back-unfold
            # of order_contrib: take(k+1) is take(k) with one more entry, and
            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
            Assert(ToSeq(order_cols).take(k + 1)
                   == ToSeq(order_cols).take(k) + PSeq(col))
            Assert(ToSeq(order_is_backref).take(k + 1)
                   == ToSeq(order_is_backref).take(k) + PSeq(is_ref))
            Assert(ToSeq(order_cols).take(k + 1).take(k) == ToSeq(order_cols).take(k))
            Assert(ToSeq(order_is_backref).take(k + 1).take(k) == ToSeq(order_is_backref).take(k))
            Assert(ToSeq(order_cols).take(k + 1)[k] == col)
            Assert(ToSeq(order_is_backref).take(k + 1)[k] == is_ref)
            Assert(order_contrib(ToSeq(order_cols).take(k + 1),
                                 ToSeq(order_is_backref).take(k + 1))
                   == order_contrib(ToSeq(order_cols).take(k),
                                    ToSeq(order_is_backref).take(k))
                   + (empty_seq() if is_ref != 0 else PSeq(col)))
            if is_ref == 0:
                result.append(col)
            k = k + 1
        Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
        Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
    # trailing source (unconditional)
    t = 0
    while t < len(trailing_cols):
        # invariants-start
        Invariant(Acc(list_pred(select_cols), 1 / 2))
        Invariant(Acc(list_pred(order_cols), 1 / 2))
        Invariant(Acc(list_pred(order_is_backref), 1 / 2))
        Invariant(len(order_cols) == len(order_is_backref))
        Invariant(Acc(list_pred(trailing_cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= t and t <= len(trailing_cols))
        Invariant(Implies(
            ordering_was_requested,
            ToSeq(result)
            == ToSeq(select_cols)
            + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
            + ToSeq(trailing_cols).take(t)))
        Invariant(Implies(
            not ordering_was_requested,
            ToSeq(result)
            == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
        Invariant(MustTerminate(len(trailing_cols) - t + 1))
        # invariants-end
        result.append(trailing_cols[t])
        t = t + 1
    Assert(ToSeq(trailing_cols).take(len(trailing_cols)) == ToSeq(trailing_cols))
    return result
    # impl-end
