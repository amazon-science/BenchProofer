"""Twin-artifact model for sympy__sympy-16766.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An element-access expression — a named carrier subscripted by one or more
  index expressions — is rendered to its source-like Python textual form from
  the rendering of its carrier name and the renderings of its individual index
  expressions. The rendering is the carrier name, immediately followed by an
  opening U+005B `[`, then the index renderings separated from one another by
  the two-code-point sequence U+002C U+0020 (`, `), then a closing U+005D `]`.
  There is no separator before the first index or after the last, and the
  rendering carries no other surrounding text.

  An element-access expression always has at least one index, so the bracketed
  index list is never empty.

The carrier name and the rendering of each index expression are produced by
unchanged helpers; this model takes the carrier name and the index renderings
as given code-point sequences (they are the input carriers) and specifies only
the surrounding assembly, which is the behaviour under change.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a sequence of index renderings is a `List[PSeq[int]]` whose pure
view is `PSeq[PSeq[int]]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the carrier name and the index renderings are inputs; the
# assembly under specification is modelled deeply by the pure region below.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def sep() -> PSeq[int]:
    """The index separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


@Pure
def join_sep(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """Separator-joined concatenation of index renderings: between every two
    adjacent indices a single `, ` is inserted, with none before the first or
    after the last. Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return empty_seq()
    if len(s) == 1:
        return s[0]
    return s[0] + sep() + join_sep(s.drop(1))


@Pure
def render_indexed(name: PSeq[int], idx: PSeq[PSeq[int]]) -> PSeq[int]:
    """The full rendering of an element-access expression with carrier name
    `name` and index renderings `idx`: the name, then `[`, then the
    separator-joined index renderings, then `]`. No surrounding text."""
    return name + PSeq(91) + join_sep(idx) + PSeq(93)   # name + '[' + join + ']'
# pure-end


def print_indexed(name: List[int], index_renderings: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(index_renderings), 1 / 2))
    # An element-access expression always carries at least one index.
    Requires(len(index_renderings) >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(index_renderings), 1 / 2))
    # The result is exactly the bracketed, separator-joined rendering of the
    # index renderings prefixed by the carrier name — with no other text.
    Ensures(Result() == render_indexed(ToSeq(name), ToSeq(index_renderings)))
    # post-conditions-end
    # impl-start
    nm = ToSeq(name)                  # type: PSeq[int]
    idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]
    n = len(index_renderings)
    joined = empty_seq()              # type: PSeq[int]
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(index_renderings), 1 / 2))
        Invariant(nm == ToSeq(name))
        Invariant(idx == ToSeq(index_renderings))
        Invariant(n == len(index_renderings))
        Invariant(n >= 1)
        Invariant(0 <= i and i <= n)
        Invariant(joined == join_sep(idx.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = idx[i - 1]
        Assert(idx.drop(i - 1)[0] == e)
        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))
        if i == n:
            joined = e
        else:
            joined = e + sep() + joined
        i = i - 1
    return nm + PSeq(91) + joined + PSeq(93)
    # impl-end
