"""Twin-artifact model for sympy__sympy-18763.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A renderer assembles a "restriction" layout from two already-rendered
  fragments: an inner BODY fragment and a CONDITION fragment. The assembled
  output is a constant surrounding layout in which the BODY is enclosed in its
  own matched delimiter pair so that it reads as ONE self-contained group,
  independent of whatever operator structure the body fragment carries. Element
  for element the result is:

      <open-layout> <open-delim> BODY <close-delim> <mid-layout> CONDITION <tail>

  where the four surrounding literals (`open-layout`, `open-delim` directly
  before the body, `close-delim` directly after it, `mid-layout`, `tail`) are
  constants. The body fragment therefore always appears bracketed by its
  own matched delimiter pair; a bare body that is dropped straight into the
  layout without that pair is NOT acceptable, because the surrounding layout's
  scaling delimiters would then bind to only part of a compound body.

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried over ``PSeq[int]`` via ``ToSeq``. The
literal layout fragments are spelled out as their ASCII code points in the
``pure`` region.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The two fragments BODY and CONDITION are
# already-rendered inputs; the operation under specification is purely the
# constant surrounding layout that assembles them. That layout — including the matched
# delimiter pair enclosing the body — is spelled out DEEPLY below as the pure
# constants and the `assembled` model, so there is no callee to axiomatize.)
# axioms-end


# pure-start
@Pure
def open_layout() -> PSeq[int]:
    # r'\left. '  -> the constant opening of the restriction layout
    return PSeq(92, 108, 101, 102, 116, 46, 32)


@Pure
def open_delim() -> PSeq[int]:
    # r'\left('   -> the scaling open delimiter placed directly before the body
    return PSeq(92, 108, 101, 102, 116, 40)


@Pure
def close_delim() -> PSeq[int]:
    # r'\right)'  -> the scaling close delimiter placed directly after the body
    return PSeq(92, 114, 105, 103, 104, 116, 41)


@Pure
def mid_layout() -> PSeq[int]:
    # r' \right|_{\substack{ '  -> layout between the body group and condition
    return PSeq(32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32)


@Pure
def tail() -> PSeq[int]:
    # r' }}'  -> the constant closing of the layout
    return PSeq(32, 125, 125)


@Pure
def assembled(body: PSeq[int], cond: PSeq[int]) -> PSeq[int]:
    """The fully assembled layout: the body enclosed in its own matched
    delimiter pair, dropped into the constant surrounding layout together with
    the condition fragment."""
    return (open_layout() + open_delim() + body + close_delim()
            + mid_layout() + cond + tail())
# pure-end


def format_restriction(body: List[int], cond: List[int]) -> List[int]:
    """Assemble the restriction layout from the already-rendered body and
    condition fragments, enclosing the body in its own matched delimiter pair."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    Requires(Acc(list_pred(cond), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(cond), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the result is exactly the constant layout with the body enclosed in its
    # matched delimiter pair (this is the load-bearing behavioural clause)
    Ensures(ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond)))
    # structural consequences that pin the body's enclosing delimiter pair:
    # the open delimiter sits immediately before the body, the close delimiter
    # immediately after it.
    Ensures(len(Result()) == len(open_layout()) + len(open_delim())
            + len(body) + len(close_delim()) + len(mid_layout())
            + len(cond) + len(tail()))
    Ensures(ToSeq(Result()).take(len(open_layout()) + len(open_delim()))
            == open_layout() + open_delim())
    Ensures(ToSeq(Result()).drop(len(open_layout()) + len(open_delim()))
            .take(len(body)) == ToSeq(body))
    Ensures(ToSeq(Result()).drop(len(open_layout()) + len(open_delim())
            + len(body)).take(len(close_delim())) == close_delim())
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # open-layout
    result = result + [92, 108, 101, 102, 116, 46, 32]
    # the body fragment, copied verbatim, dropped straight into the layout with
    # NO enclosing delimiter pair (the earlier behaviour without the pair)
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == open_layout() + ToSeq(body).take(i))
        # invariants-end
        result.append(body[i])
        i = i + 1
    # mid-layout
    result = result + [32, 92, 114, 105, 103, 104, 116, 124, 95, 123,
                       92, 115, 117, 98, 115, 116, 97, 99, 107, 123, 32]
    # the condition fragment, copied verbatim
    j = 0
    while j < len(cond):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(cond))
        Invariant(ToSeq(result) == open_layout() + ToSeq(body)
                  + mid_layout() + ToSeq(cond).take(j))
        # invariants-end
        result.append(cond[j])
        j = j + 1
    # tail
    result = result + [32, 125, 125]
    return result
    # impl-end
