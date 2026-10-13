"""Twin-artifact model for sphinx-doc__sphinx-8265.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When rendering source text back from a parsed expression, two related kinds
  of compound expression have a precise textual shape:

  (1) A parenthesised group of comma-separated members renders, when it has at
      least one member, as the comma-and-space join of the already-rendered
      members enclosed in matching round brackets: an opening '(' , the members
      separated by ', ', and a closing ')'.  An empty group renders as the two
      characters '()'.

  (2) An indexing expression renders as the already-rendered base, an opening
      square bracket '[', the rendered index body, and a closing square bracket
      ']'.  When the index is itself a non-empty group of comma-separated
      members with no spread/unpacking member, its body is the bare comma-and-
      space join of those members WITHOUT any surrounding round brackets, so an
      index of several members reads as `base[m0, m1, ...]`.  For every other
      index the body is the index's own rendering verbatim.

  Together these guarantee that a parenthesised group standing on its own keeps
  its round brackets, while the same kind of group used as an index does not
  acquire a redundant inner pair of round brackets.

Strings are modelled as `List[int]` / `PSeq[int]` of Unicode code points
(Nagini bans `str` indexing); a list of already-rendered members is a
`PSeq[PSeq[int]]`.  The comma-and-space join is modelled DEEPLY as a front-
recursive fold (`join_comma`, separator ', ' == code points 44, 32); its
equality to the real `', '.join(...)` callee is checked out-of-band by
axiom_check.py (G-AX), NOT consumed as an axiom.  Each member's own rendering
and the non-group index rendering are unchanged upstream computations taken as
inputs (already-rendered `PSeq[int]`), so no callee axiom is consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the comma-and-space join is modelled deeply
#  below as `join_comma` and validated == the real ', '.join callee out-of-band
#  by axiom_check.py / G-AX.  Member renderings are unchanged upstream inputs.)
# axioms-end


# pure-start
@Pure
def join_comma(parts: PSeq[PSeq[int]]) -> PSeq[int]:
    """The comma-and-space join of a sequence of rendered members: parts[0]
    then, for each later member, ', ' (code points 44, 32) followed by that
    member.  Front-recursive (one unfold per member) so a backward impl loop
    can discharge the value equality.  The empty list joins to the empty
    sequence; a single member joins to itself."""
    if len(parts) == 0:
        return PSeq(0).take(0)
    if len(parts) == 1:
        return parts[0]
    return (parts[0] + PSeq(44, 32)) + join_comma(parts.drop(1))
# pure-end


def tuple_render(elts: PSeq[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    # No precondition: a group may have zero or more members.
    # pre-conditions-end
    # post-conditions-start
    # A non-empty group is the comma-and-space join of its members enclosed in
    # matching round brackets '(' ... ')'.  An empty group is exactly '()'.
    Ensures(Implies(len(elts) > 0,
                    Result() == (PSeq(40) + join_comma(elts)) + PSeq(41)))
    Ensures(Implies(len(elts) == 0, Result() == PSeq(40, 41)))
    # post-conditions-end
    # impl-start
    if len(elts) > 0:
        body = join_comma(elts)  # type: PSeq[int]
        result = (PSeq(40) + body) + PSeq(41)  # type: PSeq[int]
    else:
        result = PSeq(40, 41)
    return result
    # impl-end


def subscript_render(value: PSeq[int], elts: PSeq[PSeq[int]],
                     index_is_member_group: bool, slice_rendered: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    # `index_is_member_group` records that the index is a non-empty group of members with
    # no spread/unpacking member; `elts` then carries the rendered members.
    Requires(Implies(index_is_member_group, len(elts) > 0))
    # pre-conditions-end
    # post-conditions-start
    # The base, then '[' , the index body, then ']'.  When the index is a simple
    # group the body is the BARE comma-and-space join of the members (no inner
    # round brackets); otherwise the body is the index's own rendering verbatim.
    Ensures(Implies(index_is_member_group,
                    Result() == ((value + PSeq(91)) + join_comma(elts)) + PSeq(93)))
    Ensures(Implies(not index_is_member_group,
                    Result() == ((value + PSeq(91)) + slice_rendered) + PSeq(93)))
    # post-conditions-end
    # impl-start
    if index_is_member_group:
        body = join_comma(elts)  # type: PSeq[int]
    else:
        body = slice_rendered
    result = ((value + PSeq(91)) + body) + PSeq(93)  # type: PSeq[int]
    return result
    # impl-end
