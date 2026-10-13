"""Twin-artifact model for django__django-11163.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A record exposes an ordered collection of attributes, each with a name and an
  editability flag. Projecting the record yields the ordered list of attribute
  names that survive three independent filters:

    1. Editability: only editable attributes may appear.
    2. An OPTIONAL restriction list. Supplying a list (which may be EMPTY) is a
       deliberate choice that restricts the projection to exactly the listed
       names; an attribute survives this filter iff its name is a member of the
       list. NOT supplying a list (the absent / `None` case, which is DISTINCT
       from supplying the empty list) imposes no restriction at all. In
       particular, supplying the empty list lets NO attribute through, whereas
       not supplying one lets every (otherwise-surviving) attribute through.
    3. An OPTIONAL removal list. A removal list is consulted only when it is
       both present and non-empty; an attribute is removed iff its name is a
       member of such a list. An absent OR empty removal list removes nothing.

  The result preserves the source order and contains each surviving name with
  the multiplicity it had in the source.

  Projecting is TOTAL over this domain: for every record, and for every
  combination of the two optional lists, the projected list is actually
  DELIVERED — the operation runs to completion and hands back a result. No
  admissible input is left unanswered, so the projection above is the answer
  that is really produced rather than one that merely could not be refuted.

The two optional lists are modelled as `Optional[List[int]]` of name codes
(absent ~ `None`, distinguished from the empty list). The record's attribute
names and editability flags are modelled as two equal-length parallel
`List[int]` streams (a name code per attribute; a 0/non-0 editability flag per
attribute), the streams already aligned to the record's attribute order. The
projection is carried by the pure sequence theory `PSeq[int]` as a per-attribute
fold. No callee is axiomatized: the behaviour is membership/structure logic over
the inputs, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff name code `x` occurs in sequence `s`. Front-recursive so a
    single unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def passes_restriction(allowed: Optional[List[int]], n: int) -> bool:
    """The restriction filter. An ABSENT list (`None`) imposes no restriction
    and every name passes; a PRESENT list (empty or not) restricts to members,
    so a name passes iff it is a member. The empty list therefore passes
    nothing, while absence passes everything."""
    Requires(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 4)))
    if allowed is None:
        return True
    return contains(ToSeq(allowed), n)


@Pure
def is_removed(blocked: Optional[List[int]], n: int) -> bool:
    """The removal filter. Consulted only when the list is present AND
    non-empty; then a name is removed iff it is a member. Absent or empty
    removes nothing."""
    Requires(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 4)))
    if blocked is None:
        return False
    return len(blocked) > 0 and contains(ToSeq(blocked), n)


@Pure
def projection(names: PSeq[int], edit: PSeq[int],
               allowed: Optional[List[int]], blocked: Optional[List[int]]) -> PSeq[int]:
    """The projected name sequence: the front-to-back concatenation of each
    attribute's name, kept iff the attribute is editable, passes the
    restriction filter, and is not removed. Front-recursive (one unfold per
    attribute) so the backward impl loop can discharge it."""
    Requires(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 8)))
    Requires(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 8)))
    if len(names) == 0 or len(edit) == 0:
        return PSeq(0).take(0)
    if edit[0] != 0 and passes_restriction(allowed, names[0]) and not is_removed(blocked, names[0]):
        return PSeq(names[0]) + projection(names.drop(1), edit.drop(1), allowed, blocked)
    return projection(names.drop(1), edit.drop(1), allowed, blocked)
# pure-end


def project_record(names: List[int], edit: List[int],
                   allowed: Optional[List[int]], blocked: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    # All inputs are read-only: the projection mutates nothing it is given, so
    # each is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(edit), 1 / 2))
    Requires(len(names) == len(edit))
    Requires(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
    Requires(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
    # The projected list must actually be DELIVERED. This termination
    # obligation makes the contract TOTAL over the admissible domain: an
    # operation that never hands a result back cannot satisfy the value clause
    # below only vacuously. Projecting a finite record under two optional
    # lists is bounded work, so every admissible input is answered.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(edit), 1 / 2))
    Ensures(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
    Ensures(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the per-attribute projection: every surviving name
    # in source order, with source multiplicity. This pins the discriminating
    # behaviour — a present-but-empty restriction list yields the empty result,
    # while an absent list yields all editable, non-removed names.
    Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(names)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(edit), 1 / 2))
        Invariant(len(names) == len(edit))
        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(result) ==
                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        n = names[i - 1]
        e = edit[i - 1]
        Assert(ToSeq(names).drop(i - 1)[0] == n)
        Assert(ToSeq(edit).drop(i - 1)[0] == e)
        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
        # Pre-patch skeleton: the restriction list is consulted under truthiness
        # (present AND non-empty) instead of presence, so a present-but-empty
        # restriction list is treated as no restriction and lets every editable,
        # non-removed name through.
        keep_restr = allowed is None or len(allowed) == 0 or contains(ToSeq(allowed), n)
        if e != 0 and keep_restr and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result
    # impl-end
