"""Twin-artifact model for django__django-10880.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A set-reducing query function renders to a SQL fragment of the shape

      NAME(<modifier><operands>)

  where NAME is the function keyword, <operands> is the rendered argument text,
  and <modifier> is an optional leading keyword that selects the
  duplicate-eliminating mode. When that mode is requested the modifier keyword
  must be SEPARATED from the operand text by a delimiter, so the keyword token
  does not fuse with the first operand token (which would make the fragment a
  single unintended identifier). When the mode is NOT requested the modifier is
  empty and the operands follow the opening delimiter directly.

  Concretely: with the duplicate-eliminating mode on, the rendered fragment is

      NAME + "(" + KEYWORD + SEP + operands + ")"

  i.e. the keyword DISTINCT is immediately followed by a single space before the
  operands; the code point that directly follows the keyword inside the rendered
  fragment is the separator, never the first operand code point.

Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
fragment assembly (a template substitution) is the changed operation and is
modelled DEEPLY as the spelled-out concatenation; there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: the assembled fragment is modelled deeply as a
#  concatenation of expressible pieces.)
# axioms-end


# pure-start
@Pure
def kw_distinct() -> PSeq[int]:
    """The duplicate-eliminating modifier keyword 'DISTINCT' as code points."""
    # D, I, S, T, I, N, C, T
    return PSeq(68, 73, 83, 84, 73, 78, 67, 84)


@Pure
def sep() -> int:
    """The delimiter code point between a modifier keyword and the operands
    (a single space, U+0020)."""
    return 32


@Pure
def open_paren() -> PSeq[int]:
    return PSeq(40)   # '('


@Pure
def close_paren() -> PSeq[int]:
    return PSeq(41)   # ')'


@Pure
def modifier(distinct: bool) -> PSeq[int]:
    """The leading modifier piece placed directly after the opening delimiter:
    when the duplicate-eliminating mode is requested it is the keyword followed
    by the separator; otherwise it is empty."""
    if distinct:
        return kw_distinct() + PSeq(sep())
    return PSeq(0).take(0)


@Pure
def fragment(function: PSeq[int], operands: PSeq[int], distinct: bool) -> PSeq[int]:
    """The whole rendered SQL fragment: NAME ( <modifier> <operands> )."""
    return function + open_paren() + modifier(distinct) + operands + close_paren()
# pure-end


def render_fragment(function: List[int], operands: List[int], distinct: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(function), 1 / 2))
    Requires(Acc(list_pred(operands), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(function), 1 / 2))
    Ensures(Acc(list_pred(operands), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered fragment is the deep template substitution.
    Ensures(ToSeq(Result()) == fragment(ToSeq(function), ToSeq(operands), distinct))
    # Structural separation guarantee: when the duplicate-eliminating mode is
    # requested, the keyword DISTINCT is present right after the opening
    # delimiter and the code point that immediately follows the keyword inside
    # the fragment is the separator (a space) — so the keyword token never
    # fuses with the first operand code point.
    Ensures(Implies(
        distinct,
        ToSeq(Result()).take(len(function) + 1 + len(kw_distinct())).drop(len(function) + 1)
        == kw_distinct()))
    Ensures(Implies(
        distinct,
        ToSeq(Result())[len(function) + 1 + len(kw_distinct())] == sep()))
    # Without the mode, the operands follow the opening delimiter directly (no
    # modifier is inserted).
    Ensures(Implies(
        not distinct,
        ToSeq(Result()) == ToSeq(function) + open_paren() + ToSeq(operands) + close_paren()))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # NAME
    j = 0
    while j < len(function):
        # invariants-start
        Invariant(Acc(list_pred(function), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(function))
        Invariant(ToSeq(result) == ToSeq(function).take(j))
        Invariant(MustTerminate(len(function) - j + 1))
        # invariants-end
        result.append(function[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(function))
    # opening delimiter
    result.append(40)
    Assert(ToSeq(result) == ToSeq(function) + open_paren())
    # modifier
    if distinct:
        result.append(68)
        result.append(73)
        result.append(83)
        result.append(84)
        result.append(73)
        result.append(78)
        result.append(67)
        result.append(84)
        result.append(32)
        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
    else:
        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
    # operands
    k = 0
    while k < len(operands):
        # invariants-start
        Invariant(Acc(list_pred(function), 1 / 2))
        Invariant(Acc(list_pred(operands), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(operands))
        Invariant(ToSeq(result)
                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
        Invariant(MustTerminate(len(operands) - k + 1))
        # invariants-end
        result.append(operands[k])
        k = k + 1
    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
    # closing delimiter
    result.append(41)
    return result
    # impl-end
