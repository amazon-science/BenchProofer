import Mathlib
-- imports-end

/-!
Two modeled steps, each observed on its own. A step is given what one slot holds
on the `source` side and yields what the corresponding slot holds on the
`result` side once the step is done.

At each step the `result` slot must end up holding exactly what the `source`
slot holds: the same token when the source slot holds one, and nothing when it
holds nothing. Consequently the result slot holds a token exactly when the
source slot does.

The two steps are modeled and observed separately, so a correct rendering of one
does not discharge the other.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the modeled
-- observable is plain data, so there is no callee contract to state.
-- axioms-end

-- pure-start
/-- What a slot holds: `none` = nothing; `some t` = the token `t`. Modeled
equality is equality of what is held. -/
abbrev Slot := Option Nat

/-- Whether a slot holds a token. -/
def isPresent (s : Slot) : Bool := s.isSome
-- pure-end

-- post-conditions-start
/-- First step: the `result` slot holds exactly what the `source` slot holds —
the same token when the source slot holds one, and nothing when it holds
nothing. Consequently the result slot holds a token exactly when the source slot
does. -/
def problem_spec_stepA (source : Slot) (result : Slot) : Prop :=
  result = source ∧ isPresent result = isPresent source
-- post-conditions-end

-- impl-start
def implementation_stepA (source : Slot) : Slot := Id.run do
  let mut out : Slot := source
  return out
-- impl-end

-- proof-start
theorem correct_stepA : ∀ (source : Slot),
    problem_spec_stepA source (implementation_stepA source) := by
  intro source
  unfold problem_spec_stepA implementation_stepA
  exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Second step, carrying the same obligation on its own pair of slots: the
`result` slot holds exactly what the corresponding `source` slot holds. Modeled
separately because it is observed independently of the first step. -/
def problem_spec_stepB (source : Slot) (result : Slot) : Prop :=
  result = source ∧ isPresent result = isPresent source
-- post-conditions-end

-- impl-start
def implementation_stepB (source : Slot) : Slot := Id.run do
  let mut out : Slot := source
  return out
-- impl-end

-- proof-start
theorem correct_stepB : ∀ (source : Slot),
    problem_spec_stepB source (implementation_stepB source) := by
  intro source
  unfold problem_spec_stepB implementation_stepB
  exact ⟨rfl, rfl⟩
-- proof-end
