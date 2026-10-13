"""Twin-artifact model for django__django-12039.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A column reference is rendered as a piece of DDL text by joining a base token
  (the quoted column, optionally already carrying a trailing operator-class
  keyword) with an optional ordering suffix. The ordering suffix is a string
  that is EITHER empty (the default, ascending order) OR a non-empty keyword
  (e.g. the descending-order keyword).

  The desired join behaviour:

    * When the suffix is non-empty, the rendered text is the base token, then a
      single separating space, then the suffix — so the suffix keyword is set
      off from the base token by exactly one space and never fuses with the
      last base code point.

    * When the suffix is empty, the rendered text is the base token EXACTLY:
      no separator and no trailing space are appended.

  Two sites perform this same join. They differ only in their base token:
  one joins the quoted column alone; the other joins the quoted column already
  combined with an operator-class keyword. Both must obey the join behaviour
  above.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The join
is the changed operation and is modelled DEEPLY as the spelled-out conditional
concatenation (`joined`); there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: the rendered text is modelled deeply as a conditional
#  concatenation of expressible pieces. The base token of each site is an
#  opaque already-assembled code-point list — the quoted column, or the quoted
#  column already combined with an operator-class keyword — passed in as input.)
# axioms-end


# pure-start
@Pure
def sep() -> int:
    """The separator code point placed between the base token and a non-empty
    suffix (a single space, U+0020)."""
    return 32


@Pure
def joined(base: PSeq[int], suffix: PSeq[int]) -> PSeq[int]:
    """The rendered text for one column reference: the base token joined with
    the ordering suffix. A non-empty suffix is set off by exactly one separator
    space; an empty suffix contributes nothing (the base token is returned
    unchanged, with no trailing separator)."""
    if len(suffix) == 0:
        return base
    return base + PSeq(32) + suffix
# pure-end


def render_column(base: List[int], suffix: List[int]) -> List[int]:
    """Site 1: the base token is the quoted column alone."""
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(suffix), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(suffix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text is the deep conditional concatenation.
    Ensures(ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)))
    # When the suffix is empty, the result is the base token exactly: no
    # trailing separator, same length as the base.
    Ensures(Implies(len(suffix) == 0, ToSeq(Result()) == ToSeq(base)))
    # When the suffix is non-empty, the base token is preserved as a prefix and
    # the code point that immediately follows it is the separator space (so the
    # suffix keyword never fuses with the last base code point).
    Ensures(Implies(len(suffix) > 0, ToSeq(Result()).take(len(base)) == ToSeq(base)))
    Ensures(Implies(len(suffix) > 0, ToSeq(Result())[len(base)] == sep()))
    Ensures(Implies(len(suffix) > 0,
                    ToSeq(Result()).drop(len(base) + 1) == ToSeq(suffix)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        Invariant(MustTerminate(len(base) - j + 1))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # PRE-PATCH SKELETON (site 1): the suffix is concatenated directly onto the
    # base token with no separating space, unconditionally — so a non-empty
    # suffix keyword fuses with the last base code point.
    k = 0
    while k < len(suffix):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(suffix), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(suffix))
        Invariant(ToSeq(result) == ToSeq(base) + ToSeq(suffix).take(k))
        Invariant(MustTerminate(len(suffix) - k + 1))
        # invariants-end
        result.append(suffix[k])
        k = k + 1
    Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
    return result
    # impl-end


def render_column_with_opclass(base: List[int], suffix: List[int]) -> List[int]:
    """Site 2: the base token is the quoted column already combined with an
    operator-class keyword. The join behaviour is identical to site 1."""
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(suffix), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(suffix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text is the deep conditional concatenation.
    Ensures(ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)))
    # When the suffix is empty, the result is the base token exactly: no
    # trailing separator, same length as the base.
    Ensures(Implies(len(suffix) == 0, ToSeq(Result()) == ToSeq(base)))
    # When the suffix is non-empty, the base token is preserved as a prefix and
    # the code point that immediately follows it is the separator space.
    Ensures(Implies(len(suffix) > 0, ToSeq(Result()).take(len(base)) == ToSeq(base)))
    Ensures(Implies(len(suffix) > 0, ToSeq(Result())[len(base)] == sep()))
    Ensures(Implies(len(suffix) > 0,
                    ToSeq(Result()).drop(len(base) + 1) == ToSeq(suffix)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        Invariant(MustTerminate(len(base) - j + 1))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # only append a separator + suffix when the suffix is non-empty
    Assert(len(ToSeq(suffix)) == len(suffix))
    if len(suffix) > 0:
        result.append(sep())
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
        k = 0
        while k < len(suffix):
            # invariants-start
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(suffix), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(suffix) > 0)
            Invariant(0 <= k and k <= len(suffix))
            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
            Invariant(MustTerminate(len(suffix) - k + 1))
            # invariants-end
            result.append(suffix[k])
            k = k + 1
        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(len(ToSeq(suffix)) == len(suffix))
        Assert(len(ToSeq(suffix)) != 0)
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    else:
        Assert(len(ToSeq(suffix)) == 0)
        Assert(ToSeq(result) == ToSeq(base))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    return result
    # impl-end
