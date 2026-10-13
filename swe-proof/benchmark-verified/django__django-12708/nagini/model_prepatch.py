"""Twin-artifact model for django__django-12708.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A schema-altering operation removes a composite secondary index that was
  declared over a tuple of columns. The database may carry several constraints
  on those same columns at once; each constraint is characterised by two
  independent boolean attributes reported by introspection:

    * `is_index`  -- the constraint is (or is backed by) a secondary index;
    * `is_unique` -- the constraint enforces uniqueness.

  A composite UNIQUE constraint is reported as BOTH an index and unique
  (`is_index` and `is_unique`); a plain composite index is reported as an index
  that is not unique (`is_index` and not `is_unique`).

  The removal must target exactly the plain (non-unique) composite indexes and
  must NOT pick up a uniqueness-enforcing constraint that happens to share the
  same columns. Concretely, the set of constraints selected for removal is
  exactly those that are an index AND are not unique. The operation is
  well-defined (selects a single constraint, so no ambiguous-removal error)
  precisely when exactly one such non-unique index exists on the columns, even
  in the presence of a co-located unique constraint.

  `selected_for_removal` returns the number of constraints the removal selects.
  Its value is exactly the count of non-unique indexes among the candidate
  constraints -- so a co-located unique constraint is never included in the
  removal selection.

Each candidate constraint is modelled by a small integer code carrying the two
attribute bits (`is_index` = bit 0, `is_unique` = bit 1); the candidate set is a
`List[int]` of such codes, with the specification carried over `PSeq[int]` via
`ToSeq`. The two reference counts are spelled out deeply as front-recursive
folds, paired with a matching loop. Markers (machine-parsed) delimit the
spec / proof / impl regions; provenance binding to the repository is in
mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axiom: the selection filter is modelled deeply as a fold over
# the candidate codes. The unchanged introspection callee that produces the
# attribute bits is an A-reference, validated == the real callee out-of-band by
# axiom_check.py / G-AX -- see refinement.md and mapping.md.)
# axioms-end


# pure-start
@Pure
def is_index(code: int) -> bool:
    """Whether a candidate constraint is (backed by) a secondary index:
    bit 0 of its attribute code."""
    return code % 2 == 1


@Pure
def is_unique(code: int) -> bool:
    """Whether a candidate constraint enforces uniqueness: bit 1 of its
    attribute code."""
    return (code // 2) % 2 == 1


@Pure
def selects(code: int) -> bool:
    """The removal filter for a composite index: a candidate is selected iff it
    is an index AND is not unique. A co-located unique constraint (index AND
    unique) is therefore NOT selected."""
    return is_index(code) and not is_unique(code)


@Pure
def keeps_any_index(code: int) -> bool:
    """The broader filter that selects every index regardless of uniqueness
    (an index, unique or not) -- the reference for the over-broad selection
    that the contract forbids."""
    return is_index(code)


@Pure
def count_selected(s: PSeq[int]) -> int:
    """Number of candidate codes the removal filter selects: the count of
    non-unique indexes. Front-recursive so a single unfold is available per
    loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    rest = count_selected(s.drop(1))
    if selects(s[0]):
        return 1 + rest
    return rest


@Pure
def count_any_index(s: PSeq[int]) -> int:
    """Number of candidate codes that are any index (unique or not) -- the
    reference for the over-broad selection that the contract forbids."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    rest = count_any_index(s.drop(1))
    if keeps_any_index(s[0]):
        return 1 + rest
    return rest
# pure-end


def selected_for_removal(constraints: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(constraints), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(constraints), 1 / 2))
    # The number selected for removal is exactly the count of non-unique
    # indexes among the candidate constraints; a co-located unique constraint
    # is never included.
    Ensures(Result() == count_selected(ToSeq(constraints)))
    Ensures(Result() >= 0 and Result() <= len(constraints))
    # post-conditions-end
    # impl-start
    selected = 0
    i = len(constraints)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(constraints), 1 / 2))
        Invariant(0 <= i and i <= len(constraints))
        Invariant(selected == count_any_index(ToSeq(constraints).drop(i)))
        Invariant(selected >= 0 and selected <= len(constraints) - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        code = constraints[i - 1]
        Assert(ToSeq(constraints).drop(i - 1)[0] == code)
        Assert(ToSeq(constraints).drop(i - 1).drop(1) == ToSeq(constraints).drop(i))
        if is_index(code):
            selected = selected + 1
        i = i - 1
    return selected
    # impl-end
