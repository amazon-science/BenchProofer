import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decision being modeled
-- consumes only DATA produced by surrounding helpers: the set of candidate
-- constraint identifiers discovered for the target columns, the canonical
-- identifier that the schema generator assigns to a composite-uniqueness
-- constraint, and two capability flags. Those values are taken as free inputs
-- (the spec is universally quantified over them), so the result is correct for
-- every possible value a real helper could return — strictly stronger than any
-- axiom. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The candidate identifiers, after narrowing.

When the operation removes a uniqueness constraint, the backend permits several
uniqueness constraints to coexist over the same columns, and the canonical
identifier the schema generator would assign is among the candidates, the
candidate set is reduced to exactly that canonical identifier. Otherwise the
candidate set is left untouched. -/
def narrowedNames (candidates : List String) (isUnique allowsMultiple : Bool)
    (defaultName : String) : List String :=
  if isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧
      defaultName ∈ candidates then
    [defaultName]
  else
    candidates
-- pure-end

-- post-conditions-start
/-- Selecting the single constraint identifier to drop.

`result` is `Except.error ()` exactly when the (possibly narrowed) candidate set
does not contain exactly one identifier — the operation cannot decide and signals
an error. Otherwise `result` is `Except.ok n`, where `n` is that single
identifier. The candidates are narrowed first (see `narrowedNames`), so that a
duplicate uniqueness constraint coexisting over the same columns no longer forces
an error when the canonical identifier can be singled out. -/
def problem_spec_selectUniqueToDrop (candidates : List String)
    (isUnique allowsMultiple : Bool) (defaultName : String)
    (result : Except Unit String) : Prop :=
  let names := narrowedNames candidates isUnique allowsMultiple defaultName
  (names.length = 1 → result = Except.ok names.headI) ∧
  (names.length ≠ 1 → result = Except.error ())
-- post-conditions-end

-- impl-start
def implementation_selectUniqueToDrop (candidates : List String)
    (isUnique allowsMultiple : Bool) (defaultName : String) :
    Except Unit String := Id.run do
  let mut names := candidates
  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
    names := [defaultName]
  if names.length != 1 then
    return Except.error ()
  return Except.ok names.headI
-- impl-end

-- proof-start
theorem correct_selectUniqueToDrop :
    ∀ (candidates : List String) (isUnique allowsMultiple : Bool)
      (defaultName : String),
      problem_spec_selectUniqueToDrop candidates isUnique allowsMultiple defaultName
        (implementation_selectUniqueToDrop candidates isUnique allowsMultiple defaultName) := by
  intro candidates isUnique allowsMultiple defaultName
  have hcond : (isUnique && !candidates.isEmpty && allowsMultiple && candidates.contains defaultName) = true ↔
      (isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates) := by
    simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff,
      List.contains_eq_mem, ne_eq, and_assoc, decide_eq_true_eq]
  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop narrowedNames
  simp only [Id.run]
  by_cases h : isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates
  · rw [if_pos h, if_pos (hcond.mpr h)]
    refine ⟨fun _ => rfl, fun hlen => ?_⟩
    simp at hlen
  · rw [if_neg h, if_neg (fun hh => h (hcond.mp hh))]
    by_cases hlen : candidates.length = 1
    · rw [if_neg (by simp [hlen])]
      exact ⟨fun _ => rfl, fun hne => absurd hlen hne⟩
    · rw [if_pos (by simp [hlen])]
      exact ⟨fun he => absurd he hlen, fun _ => rfl⟩
-- proof-end
