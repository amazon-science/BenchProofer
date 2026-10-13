import Mathlib
-- imports-end

/-!
Assembling the list of validators attached to a string-valued field.

A string field may declare an optional maximum length. Independent of that, the
field already carries a list of validators (those provided for its type together
with any supplied explicitly). During construction the field augments that list
with a length-bound validator that enforces the declared maximum length.

A length-bound validator is only meaningful when an actual maximum length is
declared: it carries the declared bound and compares candidate values against it.
When no maximum length is declared there is no bound to enforce, so a length-bound
validator carrying an absent bound would be inoperable. Accordingly, the
length-bound validator is appended exactly when — and only when — a maximum
length is declared; the incoming validators are preserved unchanged, in
order, in every case.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- length-bound validator's construction is the operation governed here, so it is
-- modeled structurally (its presence/absence in the list and the bound it
-- carries); no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A validator attached to a field.
* `basic tag` — any validator whose internal behavior is irrelevant here; `tag`
  distinguishes distinct such validators.
* `lengthBound limit` — a validator that enforces a maximum length, carrying that
  length as `limit`. A `lengthBound none` carries no usable bound. -/
inductive Validator where
  | basic (tag : Nat)
  | lengthBound (limit : Option Int)
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The resulting validator list is the incoming list of validators with a
length-bound validator appended exactly when a maximum length is declared. When a
maximum length `n` is declared, the appended validator carries the bound `n`; when
none is declared, nothing is appended. In both cases the incoming validators are
preserved unchanged and in order as a prefix. -/
def problem_spec_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) (result : List Validator) : Prop :=
  result = base ++ (match maxLength with
                    | none   => []
                    | some n => [Validator.lengthBound (some n)])
-- post-conditions-end

-- impl-start
def implementation_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
  let mut validators := base
  -- Always attaches the length-bound validator, even when no maximum length is
  -- declared; the attached validator then carries an absent bound.
  validators := validators ++ [Validator.lengthBound maxLength]
  return validators
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: when no maximum length is declared (`maxLength = none`),
-- the impl yields `base ++ [Validator.lengthBound none]` while the spec requires
-- `base` unchanged.
theorem correct_buildFieldValidators :
    ∀ (maxLength : Option Int) (base : List Validator),
      problem_spec_buildFieldValidators maxLength base
        (implementation_buildFieldValidators maxLength base) := by
  intro maxLength base
  unfold problem_spec_buildFieldValidators implementation_buildFieldValidators
  cases maxLength <;> simp [Id.run] <;> rfl
-- proof-end
