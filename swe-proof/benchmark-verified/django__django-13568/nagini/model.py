"""Twin-artifact model for django__django-13568.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model validation routine decides whether the designated login field of a
  user model satisfies the uniqueness obligation, and what diagnostic — if any —
  to emit when it does not.

  The login field is treated as SATISFYING the uniqueness obligation when EITHER
  of two independent guarantees holds:

    (a) the field itself carries a direct uniqueness guarantee; OR
    (b) the model declares at least one UNCONDITIONAL uniqueness constraint that
        ranges over EXACTLY the login field and no other field. A constraint
        guards uniqueness for the whole table only when it carries no predicate
        restricting the rows it applies to; a constraint that is qualified by
        such a predicate guarantees uniqueness only for the rows it selects and
        therefore does NOT discharge the obligation. A constraint spanning more
        than one field (a composite key) likewise does NOT discharge it, because
        it does not make the login field unique on its own.

  When neither guarantee holds the routine emits a diagnostic, and the SEVERITY
  of that diagnostic depends on the configured authentication regime: under the
  single default regime the diagnostic is a hard error; under any other regime
  it is a softer warning. When either guarantee holds, no diagnostic is emitted
  regardless of the regime.

The diagnostic outcome is modelled as a small integer code: 0 = no diagnostic,
1 = hard error, 2 = warning. The constraint list is modelled by three parallel
integer sequences of equal length: `span[k]` is the number of fields the k-th
constraint ranges over, `single[k]` is the single field identifier when the k-th
constraint spans exactly one field, and `total[k]` is 1 iff the k-th constraint
is unconditional (else 0). Field names are integer identifiers (the only
operation performed on them is equality). The existential search over the
constraint list is modelled deeply as a front-recursive predicate paired with a
verified loop.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


NO_DIAGNOSTIC = 0
HARD_ERROR = 1
WARNING = 2


# axioms-start
# (no axiomatized callees: the constraint-search behaviour is modelled deeply)
# axioms-end


# pure-start
@Pure
def covers(span: int, single: int, total: int, field: int) -> bool:
    """One constraint discharges the obligation for `field` iff it is
    unconditional (total == 1) and ranges over exactly that one field."""
    return total == 1 and span == 1 and single == field


@Pure
def any_covers(span: PSeq[int], single: PSeq[int], total: PSeq[int],
               field: int) -> bool:
    """Some constraint in the (parallel) sequences discharges the obligation
    for `field`. Front-recursive so a single unfold is available per loop step.
    The three sequences are read in lock-step at index 0, then recurse on the
    tails."""
    Requires(len(span) == len(single) and len(single) == len(total))
    if len(span) == 0:
        return False
    return (covers(span[0], single[0], total[0], field) or
            any_covers(span.drop(1), single.drop(1), total.drop(1), field))
# pure-end


def username_field_diagnostic(field_unique: bool,
                              c_span: List[int],
                              c_single: List[int],
                              c_total: List[int],
                              username_field: int,
                              default_regime: bool) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(c_span), 1 / 2))
    Requires(Acc(list_pred(c_single), 1 / 2))
    Requires(Acc(list_pred(c_total), 1 / 2))
    Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(c_span), 1 / 2))
    Ensures(Acc(list_pred(c_single), 1 / 2))
    Ensures(Acc(list_pred(c_total), 1 / 2))
    Ensures(len(c_span) == len(c_single) and len(c_single) == len(c_total))
    # The obligation is discharged exactly when the field is directly unique OR
    # some unconditional single-field constraint ranges over the login field.
    # No diagnostic in that case; otherwise the severity follows the regime.
    Ensures(Implies(field_unique or
                    any_covers(ToSeq(c_span), ToSeq(c_single),
                               ToSeq(c_total), username_field),
                    Result() == NO_DIAGNOSTIC))
    Ensures(Implies(not (field_unique or
                         any_covers(ToSeq(c_span), ToSeq(c_single),
                                    ToSeq(c_total), username_field)),
                    Result() == (HARD_ERROR if default_regime else WARNING)))
    # post-conditions-end
    # impl-start
    satisfied = field_unique
    if not satisfied:
        i = len(c_span)
        found = False
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(c_span), 1 / 2))
            Invariant(Acc(list_pred(c_single), 1 / 2))
            Invariant(Acc(list_pred(c_total), 1 / 2))
            Invariant(len(c_span) == len(c_single) and
                      len(c_single) == len(c_total))
            Invariant(0 <= i and i <= len(c_span))
            Invariant(found == any_covers(ToSeq(c_span).drop(i),
                                          ToSeq(c_single).drop(i),
                                          ToSeq(c_total).drop(i),
                                          username_field))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            sp = c_span[i - 1]
            sg = c_single[i - 1]
            tt = c_total[i - 1]
            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
            if tt == 1 and sp == 1 and sg == username_field:
                found = True
            i = i - 1
        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
        satisfied = found
    if satisfied:
        return NO_DIAGNOSTIC
    if default_regime:
        return HARD_ERROR
    return WARNING
    # impl-end
