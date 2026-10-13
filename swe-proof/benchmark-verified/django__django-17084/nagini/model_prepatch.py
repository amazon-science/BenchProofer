"""Twin-artifact model for django__django-17084.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single-row aggregation is evaluated over a set of aggregate
  expressions, it must be computed inside a wrapping subquery whenever any of
  several conditions holds. Among the conditions is this one: if any aggregate
  references a previously-defined annotation that itself contains a windowed
  (OVER-clause) expression, the aggregation MUST be wrapped — an aggregate may
  not be evaluated directly over a window result. Symmetrically (and
  unchanged), referencing an annotation that is a correlated subquery also
  forces wrapping. The remaining wrap-forcing conditions (grouping, slicing,
  pre-existing aggregation, qualification, distinctness, set combination) are
  collapsed into a single flag here.

  Concretely: the wrap decision is the disjunction of (a) any-referenced-
  annotation-contains-a-window, (b) any-referenced-annotation-is-a-subquery,
  and (c) the collapsed remaining conditions. Each of (a) and (b) is the
  order-independent OR over the per-referenced-annotation flags.

The per-reference flag lists are modelled as `List[bool]`; each disjunction is
spelled out deeply as a front-recursive `@Pure` OR-fold (`any_referenced_flag`),
validated == Python's `any(...)` reduction out-of-band by axiom_check.py
(G-AX). No consumed axiom: the changed operation is the disjunction itself,
modelled directly.

Deciding the wrap is a bounded computation — it reads each per-reference flag
once and MUST actually deliver its verdict to the caller (a total-correctness
obligation, carried as MustTerminate in the precondition). An implementation
that diverges before returning would satisfy the value postcondition only
vacuously and would never hand the aggregation pipeline its decision.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none consumed — the changed operation is the OR-reduction, modelled deeply
#  below as a front-recursive @Pure fold and validated against Python's any(...)
#  by axiom_check.py as an A-reference.)
# axioms-end


# pure-start
@Pure
def any_referenced_flag(flags: PSeq[bool]) -> bool:
    """The order-independent OR-reduction over a per-referenced-annotation flag
    sequence: True iff at least one referenced annotation carries the flag.
    Front-recursive so a single unfold is available per loop step. Models
    Python's `any(flags)`."""
    if len(flags) == 0:
        return False
    return flags[0] or any_referenced_flag(flags.drop(1))
# pure-end


def requires_subquery_wrap(
    window_flags: List[bool],
    subquery_flags: List[bool],
    other_forces_wrap: bool,
) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(window_flags), 1 / 2))
    Requires(Acc(list_pred(subquery_flags), 1 / 2))
    # TERMINATION: the wrap decision must actually ANSWER — it is a bounded
    # computation (one read per flag). Nagini is a partial-correctness verifier
    # by default, so without this obligation a non-terminating implementation
    # (e.g. an endless loop before returning) satisfies the value postcondition
    # vacuously; the real decision always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window_flags), 1 / 2))
    Ensures(Acc(list_pred(subquery_flags), 1 / 2))
    # The wrap decision is exactly the disjunction of the three terms; the
    # window term (a) and the subquery term (b) are the OR over the per-
    # referenced-annotation flags, and (c) is the collapsed remainder.
    Ensures(Result() == (
        any_referenced_flag(ToSeq(window_flags))
        or any_referenced_flag(ToSeq(subquery_flags))
        or other_forces_wrap
    ))
    # Discriminating consequence: a single window-containing reference forces
    # the wrap regardless of the subquery flags and the collapsed remainder.
    Ensures(Implies(
        any_referenced_flag(ToSeq(window_flags)),
        Result(),
    ))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON (the bug): the wrap decision never accounts for a
    # referenced annotation that contains a windowed expression. Only the
    # subquery term is accumulated; the window term is absent from the
    # disjunction, so an aggregate over a window-containing annotation is not
    # wrapped.
    sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
    refs_subquery = False
    j = len(subquery_flags)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(0 <= j and j <= len(subquery_flags))
        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
        # Discharge of the caller's MustTerminate(2): measure j.
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
        refs_subquery = subquery_flags[j - 1] or refs_subquery
        j = j - 1
    Assert(refs_subquery == any_referenced_flag(sseq))
    return other_forces_wrap or refs_subquery
    # impl-end
