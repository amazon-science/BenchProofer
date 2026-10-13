"""Twin-artifact model for sphinx-doc__sphinx-7462.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When rendering a parsed comma-separated group of members back into a textual
  form, the group has a well-defined shape for EVERY number of members,
  including zero. Two rendering surfaces are specified:

  (1) A token rendering, producing a sequence of display tokens. A group of one
      or more already-rendered members is the members in order with a single
      separator token ', ' between consecutive members (no trailing separator).
      A group of NO members renders as exactly two tokens: an opening round
      bracket '(' followed by a closing round bracket ')'.

  (2) A text rendering, producing a character string. A group of one or more
      already-rendered members is the comma-and-space join of those members
      (separator ', ' == code points 44, 32). A group of NO members renders as
      exactly the two characters '(' ')'.

  In both surfaces the empty group is total: it has a defined two-symbol
  rendering rather than degenerating (an empty join, or a removal of a
  non-existent trailing separator).

Strings/token texts are modelled as `List[int]` / `PSeq[int]` of Unicode code
points (Nagini bans `str` indexing). A list of already-rendered members is a
`PSeq[PSeq[int]]`. Each member's own rendering is an unchanged upstream
computation taken as an already-rendered input, so no callee axiom is consumed:
the comma-and-space join is modelled DEEPLY as a front-recursive fold
(`join_comma`) and validated == the real `', '.join(...)` callee out-of-band by
axiom_check.py (G-AX); the token separator/bracket symbols are concrete.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the comma-and-space join is modelled deeply
#  below as `join_comma` and validated == the real ', '.join callee out-of-band
#  by axiom_check.py / G-AX. Member renderings are unchanged upstream inputs.)
# axioms-end


# pure-start
@Pure
def sep_token() -> PSeq[int]:
    # the single separator token ', ' (code points 44, 32)
    return PSeq(44, 32)


@Pure
def open_paren() -> PSeq[int]:
    # the opening round-bracket symbol '(' (code point 40)
    return PSeq(40)


@Pure
def close_paren() -> PSeq[int]:
    # the closing round-bracket symbol ')' (code point 41)
    return PSeq(41)


@Pure
def join_tokens(parts: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Token-level join: the members in order with a single separator token
    ', ' between consecutive members. Front-recursive (one unfold per member)
    so a backward impl loop can discharge the value equality. The empty list
    joins to the empty token sequence; a single member joins to itself."""
    if len(parts) == 0:
        return PSeq(open_paren()).take(0)
    if len(parts) == 1:
        return PSeq(parts[0])
    return (PSeq(parts[0]) + PSeq(sep_token())) + join_tokens(parts.drop(1))


@Pure
def join_comma(parts: PSeq[PSeq[int]]) -> PSeq[int]:
    """Character-level comma-and-space join: parts[0] then, for each later
    member, ', ' (code points 44, 32) followed by that member. Front-recursive
    (one unfold per member). The empty list joins to the empty sequence; a
    single member joins to itself."""
    if len(parts) == 0:
        return PSeq(0).take(0)
    if len(parts) == 1:
        return parts[0]
    return (parts[0] + sep_token()) + join_comma(parts.drop(1))
# pure-end


def tuple_tokens(elts: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # No precondition: a group may have zero or more members.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # A non-empty group is the members joined by the single ', ' separator
    # token. An empty group is exactly the two tokens '(' then ')'.
    Ensures(Implies(len(elts) > 0, Result() == join_tokens(elts)))
    Ensures(Implies(len(elts) == 0,
                    Result() == PSeq(open_paren(), close_paren())))
    # post-conditions-end
    # impl-start
    if len(elts) > 0:
        result = join_tokens(elts)  # type: PSeq[PSeq[int]]
    else:
        result = PSeq(open_paren(), close_paren())
    return result
    # impl-end


def tuple_text(elts: PSeq[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    # No precondition: a group may have zero or more members.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # A non-empty group is the comma-and-space join of its members. An empty
    # group is exactly the two characters '(' ')'.
    Ensures(Implies(len(elts) > 0, Result() == join_comma(elts)))
    Ensures(Implies(len(elts) == 0, Result() == PSeq(40, 41)))
    # post-conditions-end
    # impl-start
    if len(elts) > 0:
        result = join_comma(elts)  # type: PSeq[int]
    else:
        result = PSeq(40, 41)
    return result
    # impl-end
