import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure decision over four scalar inputs: whether a per-row removal control
   is enabled at all, whether it is also offered on surplus rows, the optional
   ordinal position of the row, and how many rows are pre-populated. The widget
   that is ultimately attached once the decision is positive is a shared
   continuation that does not influence the decision, so nothing about it is
   assumed: no consumed axiom and no deep-model reference to a foreign callee. -/
-- axioms-end

-- pure-start
/- The outcome shape of the decision. A well-formed decision always yields a
   verdict (`Except.ok`). The single error constructor records the one outcome a
   correct decision must NEVER produce: the order comparison being attempted
   without an ordinal position to compare, which is undefined and must instead be
   treated as "no position precedes the threshold". A correct result is always a
   verdict, never this error. -/
inductive ControlErr where
  | positionComparisonUndefined
  deriving DecidableEq

/- The contribution of the position test: a present position counts only when it
   lies strictly below the pre-populated count; an absent position contributes
   nothing (it does not enable the control, and — crucially — it is NOT a reason
   to abandon the decision). This is the guarded form of the ordinal comparison
   (mapping.md §3; refinement.md §A). -/
def positionWithinInitial (position : Option Nat) (initialCount : Nat) : Bool :=
  match position with
  | some i => decide (i < initialCount)
  | none   => false

/- The desired decision: the removal control is offered exactly when it is
   enabled AND (it is offered on surplus rows OR the position lies within the
   pre-populated rows). With an absent position the inner test contributes
   nothing, so the decision reduces to "enabled AND offered-on-surplus". Every
   input yields a verdict (`Except.ok`); the decision never fails. -/
def shouldOfferDeletion (enabled offerOnExtra : Bool)
    (position : Option Nat) (initialCount : Nat) : Except ControlErr Bool :=
  Except.ok (enabled && (offerOnExtra || positionWithinInitial position initialCount))

@[grind] lemma shouldOfferDeletion_none (enabled offerOnExtra : Bool) (initialCount : Nat) :
    shouldOfferDeletion enabled offerOnExtra none initialCount
      = Except.ok (enabled && offerOnExtra) := by
  simp [shouldOfferDeletion, positionWithinInitial]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a per-row removal control should be offered on one row of a
   collection of repeated rows. All four inputs are read-only and unchanged by
   the decision (none is `mut`):
     * `enabled`      — whether the removal control is enabled for the collection;
     * `offerOnExtra` — whether it is also offered on surplus (non-prepopulated) rows;
     * `position`     — the row's ordinal position, or absent when the row has no
                        position (e.g. a standalone blank template row);
     * `initialCount` — how many rows are pre-populated.

   Desired behaviour: the control is offered exactly when it is enabled and
   either it is offered on surplus rows or the position lies strictly within the
   pre-populated rows. When the position is absent the order test contributes
   nothing and the decision must still produce a verdict — it reduces to
   "enabled and offered-on-surplus" — rather than being left undefined. The
   decision fully determines whether the control is subsequently attached. -/
method deletionFieldDecision (enabled : Bool) (offerOnExtra : Bool)
    (position : Option Nat) (initialCount : Nat)
    return (out : Except ControlErr Bool)
  ensures out = shouldOfferDeletion enabled offerOnExtra position initialCount
  ensures ∃ b, out = Except.ok b
  ensures position = none → out = Except.ok (enabled && offerOnExtra)
  do
    -- impl-start
    -- Pre-image skeleton: when the control is enabled and is not offered on
    -- surplus rows, the order comparison is attempted directly on the position
    -- WITHOUT first checking that a position is present. An absent position has
    -- nothing to compare, so this attempt is the undefined-comparison outcome
    -- the frozen spec forbids: the spec requires every input to yield a verdict
    -- (and an absent position to reduce to "enabled and offered-on-surplus"), so
    -- prove_correct MUST fail on that clause.
    let mut result : Except ControlErr Bool := Except.ok false
    if enabled = true then
      if offerOnExtra = true then
        result := Except.ok true
      else
        result := match position with
          | some i => Except.ok (decide (i < initialCount))
          | none   => Except.error ControlErr.positionComparisonUndefined
    else
      result := Except.ok false
    return result
    -- impl-end

prove_correct deletionFieldDecision by
  loom_solve <;>
    simp_all [shouldOfferDeletion, positionWithinInitial]
