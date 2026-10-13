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
-- Pre-patch (buggy) skeleton: the candidate set is NEVER narrowed. When two
-- uniqueness constraints coexist over the same columns the candidate set has
-- length 2, so the operation always errors instead of singling out the canonical
-- constraint — the bug from the issue ("Found wrong number (2) of constraints").
def implementation_selectUniqueToDrop (candidates : List String)
    (isUnique allowsMultiple : Bool) (defaultName : String) :
    Except Unit String := Id.run do
  let names := candidates
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
  -- Carries the gold proof obligation; UNCLOSABLE against the buggy impl because
  -- on a narrowing input (e.g. candidates of length 2 with the canonical name
  -- present) the spec requires `Except.ok defaultName` but the buggy impl returns
  -- `Except.error ()`. (G-DIFF)
  intro candidates isUnique allowsMultiple defaultName
  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop narrowedNames
  sorry
-- proof-end
