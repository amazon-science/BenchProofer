"""Twin-artifact model for sympy__sympy-15809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lattice reduction (the associative-commutative fold that selects an extreme
  element from a collection of comparable operands) is a TOTAL operation over
  every operand collection its stages can carry through — INCLUDING the EMPTY
  collection. The construction proceeds in stages over the operands:

    * A single pre-filter SCANS the operands in collection order and stops at
      the FIRST operand that is decisive for the whole reduction. Exactly which
      event the scan meets first determines the outcome:

        - if that operand is not comparable within the lattice's order, the
          whole reduction fails with a non-comparable-operand error;
        - if that operand is the lattice's absorbing element (its annihilator),
          the whole reduction collapses to that annihilator.

      An operand that is neither is passed over and the scan continues. Because
      one scan has one first decisive event, AT MOST ONE of the two can fire on
      any given collection: whichever the scan reaches first wins, and the other
      is never observed even when such an operand also occurs later in the
      collection. (The empty collection contains no operand, so the scan meets
      neither event and can never reject it nor collapse it.)

    * The operands the scan passed over are then reduced to a canonical set by
      a pass that COMPARES survivors AGAINST ONE ANOTHER. That pass is PARTIAL,
      and it makes a DIFFERENT observation than the scan: the scan judges each
      operand ON ITS OWN, so an operand it passes over can still fail to compare
      against another survivor — and then this pass yields no canonical set at
      all, propagating its own comparison failure, and the whole reduction fails
      with a reduction-undefined error. A collection whose scan already decided
      the outcome never reaches this pass. The empty collection reduces to the
      empty set (a pass with nothing to compare cannot fail).

    * If the canonical set is empty, the reduction returns the lattice's
      IDENTITY element (the neutral element of the fold — the value an empty
      fold must yield). If it has a single member, the reduction returns that
      member. Otherwise the reduction returns the assembled aggregate.

  The behaviour pinned here: the reduction of the EMPTY operand collection
  RETURNS NORMALLY and yields the lattice identity element — it is never
  rejected. (For the maximum the identity is negative infinity; for the
  minimum it is positive infinity — the neutral element each empty fold must
  return.) More generally, whenever the canonical operand set is empty the
  result is exactly the identity element, whatever caused the set to be empty.
  In contrast, the two failures above are UNCHANGED and remain obligatory on the
  collections that reach them: a reduction whose scan meets a non-comparable
  operand FIRST is STILL rejected with the non-comparable-operand error, and one
  that reaches the canonical-set pass and cannot compare its survivors STILL
  fails with the reduction-undefined error. Comparability of every operand the
  scan reaches, and reducibility of the survivors it passes over, remain
  preconditions of every NON-empty reduction. Neither failure can happen on the
  empty collection: it has no operand for the scan to reach and nothing for the
  reduction pass to compare.

The operand collection is modelled as ``List[int]`` (each operand abstracted to
an opaque int; the reduction observes only collection cardinality, WHICH of the
two decisive scan events fires first (if either), whether the canonical-set pass
is defined, and the canonical-set cardinality, not operand payloads). The
lattice's identity and annihilator elements are distinct opaque int sentinels
passed in. The four unchanged pre-reduction observations — the two decisive
outcomes of the ordered scan, the definedness of the canonical-set pass and the
cardinality it yields — are axiomatized at their weakest sufficient contracts
(an empty collection triggers neither scan event, is reducible, and reduces to
the empty set; the two scan events are mutually exclusive because one ordered
scan has one first decisive event; and a canonical cardinality exists only where
that pass is defined). Each rejection is a user-defined exception class
(a builtin exception in an ``Exsures`` crashes the Nagini translator; mapping.md
§2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class EmptyReductionRejected(Exception):
    """Signals that the reduction rejected its operand collection for being
    empty. Stands in for the `ValueError` a stale implementation raises on an
    empty collection; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2). The pinned behaviour FORBIDS this on the empty
    collection."""


class NonComparableOperand(Exception):
    """Signals that the reduction rejected its operand collection because the
    ordered pre-filter scan met an operand that is not comparable within the
    lattice's order. Stands in for the `ValueError` the unchanged scan raises on
    such an operand; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2). This rejection is REQUIRED exactly when the
    non-comparable event is the scan's FIRST decisive event."""


class ReductionUndefined(Exception):
    """Signals that the reduction failed because the canonical-set pass, reached
    with the operands the scan passed over, could not compare them against one
    another and propagated its own comparison failure instead of yielding a
    canonical set. Stands in for whatever error that unchanged pass propagates
    (mapping.md §2); a builtin exception in an `Exsures` crashes the Nagini
    translator. This failure is REQUIRED exactly when the scan is clean, no
    absorbing operand collapses the reduction, and the pass is undefined."""


# axioms-start
@Pure
@ContractOnly
def has_noncomparable_operand(operands: List[int]) -> bool:
    """Unchanged ordered pre-filter scan, non-comparable outcome: whether the
    scan over the operands in collection order meets a NON-COMPARABLE operand as
    its FIRST decisive event. This is NOT "the collection contains a
    non-comparable operand": a collection may carry one and still not be
    rejected, because the scan stops earlier at an absorbing operand and
    collapses instead. The only property the proof consumes is that an EMPTY
    collection has no operand for the scan to reach, so this event can never
    fire on it. Weakest sufficient contract; provenance + executable soundness
    check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, not Result()))


@Pure
@ContractOnly
def has_absorbing_operand(operands: List[int]) -> bool:
    """Unchanged ordered pre-filter scan, absorbing outcome: whether the scan
    over the operands in collection order meets the lattice's ABSORBING element
    (the annihilator that collapses the whole reduction) as its FIRST decisive
    event. As above this is NOT mere containment: an absorbing operand that the
    scan never reaches — because it stops earlier at a non-comparable operand —
    does not collapse the reduction. The properties the proof consumes: an EMPTY
    collection has no operand for the scan to reach, so this event can never fire
    on it; and it is EXCLUSIVE with the non-comparable event, since one ordered
    scan has exactly one first decisive event. Weakest sufficient contract;
    provenance + executable soundness check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, not Result()))
    Ensures(Implies(Result(), not has_noncomparable_operand(operands)))


@Pure
@ContractOnly
def canonical_reduction_defined(operands: List[int]) -> bool:
    """Unchanged canonical-set pass, DEFINEDNESS outcome: whether that pass
    yields a canonical set at all, rather than propagating a comparison failure
    over the survivors the scan passed over. It is a different observation from
    the scan's per-operand one: the scan judges each operand ALONE, this pass
    compares survivors AGAINST ONE ANOTHER, so an operand the scan passes over
    can still be one this pass cannot place. Vacuously true on a collection whose
    scan already decided the outcome, since the pass is then never reached. The
    only property the proof consumes is that an EMPTY collection leaves this pass
    nothing to compare, so it cannot fail on it. Weakest sufficient contract;
    provenance + executable soundness check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Ensures(Implies(len(operands) == 0, Result()))


@Pure
@ContractOnly
def canonical_count(operands: List[int]) -> int:
    """Unchanged canonical-set reduction: the number of operands surviving the
    redundancy-removal/normalisation pass. PARTIAL — a canonical cardinality
    exists only where that pass is defined, which is why the definedness axiom
    above guards this one's `Requires`: a pass that propagated a comparison
    failure produced no canonical set and so has no count to report. Where it is
    defined the properties the proof consumes are: the count is never negative,
    and an EMPTY collection reduces to the empty canonical set (count 0).
    Weakest sufficient contract; provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(operands), 1 / 4))
    Requires(canonical_reduction_defined(operands))
    Ensures(Result() >= 0)
    Ensures(Implies(len(operands) == 0, Result() == 0))
# axioms-end


# pure-start
# (no module-level pure helpers required: the reduction's result selection is
# concrete control flow over the canonical-set cardinality, stated directly.)
# pure-end


def lattice_reduce(operands: List[int], identity: int, zero: int,
                   single: int, aggregate: int) -> int:
    # pre-conditions-start
    # The operand collection is read, not mutated (fractional permission).
    Requires(Acc(list_pred(operands), 1 / 2))
    # The four possible NORMAL outcomes are distinct values, so each
    # postcondition clause pins exactly one branch (the identity branch is the
    # discriminating one): identity (empty canonical set), zero (absorbing
    # operand seen), single (one survivor), aggregate (many survivors).
    Requires(identity != zero and identity != single and identity != aggregate)
    Requires(zero != single and zero != aggregate and single != aggregate)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operands), 1 / 2))
    # On every collection the stages can carry through — the scan's first
    # decisive event is not the non-comparable one, AND the canonical-set pass is
    # defined (vacuously so when the scan already decided the outcome) — the
    # reduction is TOTAL: it always returns one of the four outcomes and never
    # raises. Returning normally on the empty collection is therefore guaranteed:
    # by their axioms the empty collection has no non-comparable first event and
    # is reducible, and no Exsures below admits a rejection there.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and canonical_reduction_defined(operands),
                    Result() == identity or Result() == zero
                    or Result() == single or Result() == aggregate))
    # An absorbing operand collapses the reduction to the annihilator (among
    # comparable operands).
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and has_absorbing_operand(operands),
                    Result() == zero))
    # The discriminating clause: when the canonical operand set is empty (the
    # scan decided nothing and the canonical-set pass is defined) the result is
    # the IDENTITY element. The empty operand collection is the primary witness
    # (no non-comparable operand, no absorbing operand, reducible, empty
    # canonical set), so the reduction of the empty collection returns normally
    # and yields identity. The count is read only under the definedness
    # antecedent, which is that observation's precondition.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) == 0,
                            Result() == identity)))
    Ensures(Implies(len(operands) == 0, Result() == identity))
    # A single survivor is returned as itself; many survivors aggregate.
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) == 1,
                            Result() == single)))
    Ensures(Implies(not has_noncomparable_operand(operands)
                    and not has_absorbing_operand(operands)
                    and canonical_reduction_defined(operands),
                    Implies(canonical_count(operands) >= 2,
                            Result() == aggregate)))
    # A NORMAL return is admissible ONLY when the scan's first decisive event is
    # not the non-comparable one: equivalently, a reduction whose scan meets a
    # non-comparable operand FIRST MUST be rejected (it can never return a
    # value). This OBLIGATES the rejection on that path — the Exsures below only
    # grants PERMISSION to raise; this postcondition forbids the alternative
    # (silently returning a value), which is exactly what the unchanged scan
    # forbids. It does NOT obligate a rejection merely because a non-comparable
    # operand occurs somewhere in the collection: when the scan stops earlier at
    # an absorbing operand the reduction collapses to the annihilator instead,
    # and the exclusivity axiom above makes that path provable.
    Ensures(not has_noncomparable_operand(operands))
    # The mirror obligation for the canonical-set pass: a NORMAL return is
    # admissible only when the scan already decided the outcome (the absorbing
    # event fired, so the pass is never reached) or that pass is DEFINED. So a
    # reduction that reaches the pass and cannot compare its survivors can never
    # return a value either; it MUST propagate the reduction-undefined failure.
    # The Exsures below only grants permission to raise it — this clause forbids
    # the alternative, which is exactly what the unchanged pass forbids.
    Ensures(has_absorbing_operand(operands)
            or canonical_reduction_defined(operands))
    # The read permission to the operand collection is returned on the
    # exceptional path too (the collection is never mutated).
    Exsures(NonComparableOperand, Acc(list_pred(operands), 1 / 2))
    Exsures(ReductionUndefined, Acc(list_pred(operands), 1 / 2))
    # A reduction whose scan meets a non-comparable operand first is REJECTED
    # with the non-comparable-operand error — comparability of every operand the
    # scan reaches is a precondition of every non-empty reduction, and the
    # unchanged scan still enforces it. (The empty collection has no operand, so
    # this is never raised on it; the axiom's empty-collection property
    # guarantees that.)
    Exsures(NonComparableOperand, has_noncomparable_operand(operands))
    # A reduction whose scan is clean and uncollapsed, and whose canonical-set
    # pass then cannot compare the survivors against one another, FAILS with the
    # reduction-undefined error — reducibility of the survivors the scan passes
    # over is a precondition of every non-empty reduction, and the unchanged pass
    # still enforces it. This failure is admissible ONLY on that exact class: not
    # where the scan rejects (the clause above owns that path), not where an
    # absorbing operand collapses the reduction before the pass is reached, and
    # never on the empty collection, which by the definedness axiom leaves the
    # pass nothing to compare.
    Exsures(ReductionUndefined, not has_noncomparable_operand(operands)
            and not has_absorbing_operand(operands)
            and not canonical_reduction_defined(operands))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (stale): the reduction REJECTS the empty operand collection up
    # front, raising instead of falling through to the empty-canonical-set
    # branch that yields the identity element. Nagini reports the postcondition
    # `Implies(len(operands) == 0, Result() == identity)` (and the totality
    # clause, whose only admitted failures are the two the Exsures clauses
    # name) unprovable: on the empty collection the function raises a rejection
    # the spec does not admit rather than returning the identity element.
    if len(operands) == 0:
        raise EmptyReductionRejected()
    if has_noncomparable_operand(operands):
        raise NonComparableOperand()
    if has_absorbing_operand(operands):
        return zero
    if not canonical_reduction_defined(operands):
        raise ReductionUndefined()
    count = canonical_count(operands)  # type: int
    if count == 0:
        return identity
    if count == 1:
        return single
    return aggregate
    # impl-end
