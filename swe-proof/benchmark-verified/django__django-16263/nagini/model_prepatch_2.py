"""Twin-artifact model for django__django-16263.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A row-count over a query that already carries some annotated columns must
  return the same count as the same query without those annotated columns, and
  emitted query must not carry annotated columns that nothing in the count
  refers to. Two decisions realise this:

  (1) WHETHER the count must be computed over a derived (inner) query because of
      the pre-existing annotated columns. Only the annotated columns that are
      actually SELECTED by the query participate in this decision; an annotated
      column that the query merely keeps as a private alias (never selected)
      does not participate. Among the selected annotated columns, one forces the
      derived-query form only when it actually summarises rows (it is itself a
      row-summary, or such a summary is exercised by a retained filter); a
      selected column that summarises nothing and is not filtered on must NOT,
      by itself, force the derived form. (Other independent reasons for a
      derived query — slicing, distinctness, set operations, explicit grouping —
      are out of scope of this decision.)

  (2) WHICH pre-existing annotated columns remain referenced by the inner query
      when a derived query IS used. Only the annotated columns that the count's
      own expressions actually refer to may remain; every other pre-existing
      annotated column is dropped. An annotated column's name is kept exactly
      when it is one of the count's own names OR it is referred to (transitively)
      by one of the count's expressions. The names referred to by an expression
      are the union of the names referred to by its sub-expressions, with a bare
      reference contributing its own referent.

The query's annotated columns are modelled by minimal parallel carriers over
`List[int]` of name/reference codes, a per-column selected flag, and a per-column
summary flag (Nagini bans `str` indexing and cannot carry the live ORM objects).
The reference-gathering fold and the two decisions are spelled out deeply over
those carriers; the equality of the fold to the real reference-gatherer is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Both decisions are bounded scans over finite carriers and MUST terminate and
actually deliver their answer (a total-correctness obligation, carried as
MustTerminate in each precondition): Nagini verifies partial correctness by
default, so without the obligation a diverging implementation (e.g. an
endless loop before the return) would satisfy every Ensures vacuously while
never returning the decision to its caller.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. Both decisions and the reference-gathering fold are pure
# structural logic over the annotated-column carriers, modelled deeply. The deep
# reference fold (`collect_refs`) is validated == the real recursive
# reference-gatherer out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
@Pure
def any_selected_summary(selected: PSeq[int], summ: PSeq[int]) -> bool:
    """True iff some pre-existing annotated column is BOTH selected by the query
    AND carries a row-summary, i.e. for some index k both `selected[k]` and
    `summ[k]` are non-zero. Front-recursive so a single unfold is available per
    loop step; the two carriers are stepped in lock-step. Total over any pair of
    lengths (both guards) so no equal-length precondition is needed at recursion
    or at the postcondition call site; the carriers are equal-length by the
    decision's own Requires."""
    if len(selected) == 0 or len(summ) == 0:
        return False
    return (selected[0] != 0 and summ[0] != 0) or any_selected_summary(
        selected.drop(1), summ.drop(1)
    )


@Pure
def collect_refs(tree: PSeq[int]) -> PSeq[int]:
    """References reachable from an expression, modelled as the sequence of all
    reference leaves in the expression's flattened tree. A node carrying a
    positive code is a bare reference contributing its referent and is a LEAF
    (its own referent only — its source is not descended into, matching the real
    leaf reference-gatherer); a node coded 0 is a non-referencing sub-expression
    contributing nothing but whose children are still folded. The references of
    a composite expression are the union (here, concatenation; membership is what
    the decision observes) of its sub-expressions' references. Front-recursive
    for a single unfold per step."""
    if len(tree) == 0:
        return PSeq(0).take(0)
    if tree[0] != 0:
        return PSeq(tree[0]) + collect_refs(tree.drop(1))
    return collect_refs(tree.drop(1))


@Pure
def seq_contains(s: PSeq[int], x: int) -> bool:
    """Membership of a code in a sequence. Front-recursive."""
    if len(s) == 0:
        return False
    return s[0] == x or seq_contains(s.drop(1), x)
# pure-end


def existing_summary_forces_derived(
    selected: List[int], summ: List[int], filter_summary: int
) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(selected), 1 / 2))
    Requires(Acc(list_pred(summ), 1 / 2))
    Requires(len(selected) == len(summ))
    # TERMINATION: deciding the derived-query form is one bounded backward
    # pass over the finite carriers and must actually ANSWER. Nagini verifies
    # partial correctness by default, so without this obligation a diverging
    # implementation (e.g. `while True: pass` before the return) satisfies
    # every Ensures vacuously; the real decision always returns to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(selected), 1 / 2))
    Ensures(Acc(list_pred(summ), 1 / 2))
    # The derived form is forced exactly when some SELECTED pre-existing
    # annotated column carries a row-summary OR a retained filter does. A column
    # that is not selected does NOT participate, and a selected column that is
    # not a row-summary does NOT by itself force the derived form.
    Ensures(
        Result()
        == (
            any_selected_summary(ToSeq(selected), ToSeq(summ))
            or filter_summary != 0
        )
    )
    # post-conditions-end
    # impl-start
    found = False
    i = len(selected)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(selected), 1 / 2))
        Invariant(Acc(list_pred(summ), 1 / 2))
        Invariant(len(selected) == len(summ))
        Invariant(0 <= i and i <= len(selected))
        Invariant(len(ToSeq(selected).drop(i)) == len(ToSeq(summ).drop(i)))
        Invariant(
            found
            == any_selected_summary(ToSeq(selected).drop(i), ToSeq(summ).drop(i))
        )
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        s = selected[i - 1]
        m = summ[i - 1]
        Assert(ToSeq(selected).drop(i - 1)[0] == s)
        Assert(ToSeq(selected).drop(i - 1).drop(1) == ToSeq(selected).drop(i))
        Assert(ToSeq(summ).drop(i - 1)[0] == m)
        Assert(ToSeq(summ).drop(i - 1).drop(1) == ToSeq(summ).drop(i))
        Assert(len(ToSeq(selected).drop(i - 1)) == len(ToSeq(summ).drop(i - 1)))
        # any_selected_summary(drop(i-1)) unfolds to its head bit OR the tail
        # (== drop(i)); this links the loop body's update to the fold.
        Assert(
            any_selected_summary(
                ToSeq(selected).drop(i - 1), ToSeq(summ).drop(i - 1)
            )
            == (
                (s != 0 and m != 0)
                or any_selected_summary(
                    ToSeq(selected).drop(i), ToSeq(summ).drop(i)
                )
            )
        )
        if s != 0 and m != 0:
            found = True
        i = i - 1
    # At exit i == 0: drop(0) is the full sequence, so the invariant gives
    # found == any_selected_summary(full). Surface the length equality the
    # postcondition's own call needs.
    Assert(ToSeq(selected).drop(0) == ToSeq(selected))
    Assert(ToSeq(summ).drop(0) == ToSeq(summ))
    Assert(len(ToSeq(selected)) == len(ToSeq(summ)))
    return found or filter_summary != 0
    # impl-end


def inner_column_kept(alias: int, added: List[int], ref_tree: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(added), 1 / 2))
    Requires(Acc(list_pred(ref_tree), 1 / 2))
    # TERMINATION: the keep-or-prune decision is two bounded backward passes
    # over the finite name/reference carriers and must actually ANSWER.
    # Without this obligation a diverging implementation satisfies every
    # Ensures vacuously; the real keep-or-prune computation always returns
    # its verdict for each name.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(added), 1 / 2))
    Ensures(Acc(list_pred(ref_tree), 1 / 2))
    # A pre-existing annotated column's name is retained in the inner query
    # exactly when it is one of the count's own names OR it is referred to by one
    # of the count's expressions (per the reachable-reference fold).
    Ensures(
        Result()
        == (
            seq_contains(ToSeq(added), alias)
            or seq_contains(collect_refs(ToSeq(ref_tree)), alias)
        )
    )
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy, decision #2): every pre-existing annotated column is kept
    # in the inner query regardless of whether the count's own expressions refer
    # to it; no dropping of unreferenced columns is performed.
    return True
    # impl-end
