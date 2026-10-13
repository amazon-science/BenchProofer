"""Twin-artifact model for sphinx-doc__sphinx-9367.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A parenthesized expression sequence is rendered back to its source-like
  textual form from the textual renderings of its individual members. The
  rendering is delimited by an opening U+0028 `(` and a closing U+0029 `)`;
  the member renderings are separated from one another by the two-code-point
  sequence U+002C U+0020 (`, `).

  The number of members determines the surface form:
    * an empty sequence renders as the bare pair of parentheses `()`;
    * a sequence of exactly ONE member renders as that one member followed by a
      trailing U+002C `,` before the closing parenthesis, so the single-member
      form is textually distinguishable from a merely parenthesized expression;
    * a sequence of two or more members renders as the separator-joined members
      with no trailing separator.

The textual rendering of an individual member is produced by an unchanged
recursive helper; this model takes each member's rendering as a given
code-point sequence (the member renderings are the input carrier) and specifies
only the surrounding assembly, which is the behaviour under change.

The assembly is a bounded, straight-line computation over finitely many
member renderings: it MUST terminate and return its rendered text (a
total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges before returning would satisfy the value
postcondition only vacuously and would never deliver the rendering.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a sequence of member renderings is a `List[PSeq[int]]` whose pure
view is `PSeq[PSeq[int]]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the member renderings are inputs; the assembly under
# specification is modelled deeply by the pure region below.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def sep() -> PSeq[int]:
    """The member separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


@Pure
def join_sep(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """Separator-joined concatenation of member renderings: between every two
    adjacent members a single `, ` is inserted, with none before the first or
    after the last. Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return empty_seq()
    if len(s) == 1:
        return s[0]
    return s[0] + sep() + join_sep(s.drop(1))


@Pure
def render_seq(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """The full parenthesized rendering of the member-rendering sequence `s`.

    Empty -> `()`; a single member -> that member with a trailing comma inside
    the parentheses; two or more members -> the separator-joined members inside
    the parentheses."""
    if len(s) == 0:
        return PSeq(40, 41)                        # '()'
    if len(s) == 1:
        return PSeq(40) + s[0] + PSeq(44, 41)      # '(' + e0 + ',)'
    return PSeq(40) + join_sep(s) + PSeq(41)       # '(' + join + ')'
# pure-end


def render_tuple(elts: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(elts), 1 / 2))
    # TERMINATION: the assembly must actually ANSWER — parenthesizing and
    # joining finitely many member renderings is a bounded computation
    # (str.join over a finite list plus concatenations). Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. an endless loop before the return)
    # satisfies the value postcondition vacuously while sharing the spec; the
    # real visit_Tuple always returns its rendered text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elts), 1 / 2))
    # The result is exactly the parenthesized rendering of the member
    # renderings, with the empty / single / multi surface forms pinned.
    Ensures(Result() == render_seq(ToSeq(elts)))
    # post-conditions-end
    # impl-start
    es = ToSeq(elts)  # type: PSeq[PSeq[int]]
    n = len(elts)
    if n == 0:
        return PSeq(40, 41)
    elif n == 1:
        return PSeq(40) + es[0] + PSeq(44, 41)
    else:
        joined = empty_seq()  # type: PSeq[int]
        i = n
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(elts), 1 / 2))
            Invariant(es == ToSeq(elts))
            Invariant(n == len(elts))
            Invariant(n >= 2)
            Invariant(0 <= i and i <= n)
            Invariant(joined == join_sep(es.drop(i)))
            # The loop consumes the termination obligation: i is the strictly
            # decreasing, bounded-below measure.
            Invariant(MustTerminate(i))
            # invariants-end
            e = es[i - 1]
            Assert(es.drop(i - 1)[0] == e)
            Assert(es.drop(i - 1).drop(1) == es.drop(i))
            if i == n:
                joined = e
            else:
                joined = e + sep() + joined
            i = i - 1
        return PSeq(40) + joined + PSeq(41)
    # impl-end
