import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A bounded sequence of refinement passes is driven by a per-pass flag telling
   whether that pass still produced a change. The summary observation reported
   after the whole sequence is: did the sequence run out of its pass budget while
   changes were still happening? That holds exactly when the budget is positive
   AND every pass inside the budget still reported a change, so the sequence
   never settled. With a zero budget no pass runs, nothing changes, and the
   reported value must be `false`. -/
def settledThrough (flags : List Bool) (limit : Nat) : Bool :=
  decide (∀ j, j < limit → flags[j]! = true)

def overBudget (flags : List Bool) (limit : Nat) : Bool :=
  decide (0 < limit) && settledThrough flags limit

@[grind] lemma settledThrough_iff (flags : List Bool) (limit : Nat) :
    settledThrough flags limit = true ↔ ∀ j, j < limit → flags[j]! = true := by
  simp [settledThrough]

@[grind] lemma overBudget_iff (flags : List Bool) (limit : Nat) :
    overBudget flags limit = true ↔ (0 < limit ∧ ∀ j, j < limit → flags[j]! = true) := by
  simp [overBudget, settledThrough]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method passBudgetExceeded (flags : List Bool) (limit : Nat) return (out : Bool)
  require limit ≤ flags.length
  ensures out = overBudget flags limit
  do
    -- impl-start
    -- Pre-image skeleton: the summary flag is left UNPINNED before the bounded
    -- loop (modeled here as the unconstrained pre-loop value `true`). When the
    -- budget is zero the loop never runs and that stale value is returned —
    -- the referenced-before-assignment bug. The frozen spec requires `false`
    -- in the zero-budget case, so `prove_correct` MUST fail on the exit clause.
    let mut exhausted := true
    let mut i := 0
    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
      invariant i ≤ limit
      invariant 0 < i → exhausted = flags[i - 1]!
      invariant ∀ j, j + 1 < i → flags[j]! = true
      done_with exhausted = overBudget flags limit
      decreasing limit - i
    do
      exhausted := flags[i]!
      i := i + 1
    return exhausted
    -- impl-end

prove_correct passBudgetExceeded by
  loom_solve
