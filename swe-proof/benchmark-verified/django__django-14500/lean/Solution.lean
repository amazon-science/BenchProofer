import Mathlib
-- imports-end

/-!
Rolling back a migration that stands in for (replaces) a set of earlier
migrations.

A migration carries its own identifier (an application label together with a
migration name) and, optionally, a list of identifiers of the earlier
migrations it stands in for. When such a migration is rolled back, the rollback
must record, as no-longer-applied, every identifier the migration represents:
both each identifier it stands in for AND the migration's own identifier. A
migration that stands in for nothing records only its own identifier.

The behavior is stated abstractly as the ordered sequence of identifiers
recorded as no-longer-applied; the implementation and correctness proof are
supplied separately.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the operation under spec
-- merely decides WHICH identifiers are recorded as no-longer-applied and in
-- what order. The recording sink itself (which removes an identifier from the
-- applied set) is unchanged and order-independent, so its effect is modeled as
-- collecting the ordered argument sequence; nothing about it is assumed.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A migration identifier: an application label paired with a migration name. -/
abbrev MigrationId := String × String

/-- The pieces of a migration the rollback reads: its own identifier and the
list of identifiers it stands in for (empty when it stands in for nothing). -/
structure Migration where
  appLabel : String
  name : String
  replaces : List MigrationId
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered sequence of identifiers recorded as
no-longer-applied: each identifier the migration stands in for, in order,
followed by the migration's own identifier. (When the migration stands in for
nothing, this is just its own identifier.) -/
def problem_spec_unapplyMigration (mig : Migration) (result : List MigrationId) : Prop :=
  result = mig.replaces ++ [(mig.appLabel, mig.name)]
-- post-conditions-end

-- impl-start
def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
  let mut recorded : List MigrationId := []
  if mig.replaces ≠ [] then
    for r in mig.replaces do
      recorded := recorded ++ [r]
  recorded := recorded ++ [(mig.appLabel, mig.name)]
  return recorded
-- impl-end

-- proof-start
/-- The `forIn` loop, generalized over the accumulator, collects the visited
identifiers in order: it appends `xs` to the initial accumulator. -/
private theorem unapplyMigration_forIn (xs : List MigrationId) (init : List MigrationId) :
    Id.run (forIn xs init (fun r acc => (ForInStep.yield (acc ++ [r])))) = init ++ xs := by
  induction xs generalizing init with
  | nil => simp [Id.run, pure]
  | cons a as ih =>
    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; simp

theorem correct_unapplyMigration : ∀ mig : Migration,
    problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
  intro mig
  unfold problem_spec_unapplyMigration implementation_unapplyMigration
  simp only [Id.run]
  by_cases h : mig.replaces ≠ []
  · rw [if_pos h]
    -- bridge the desugared `do` body to the clean `forIn` form of the helper
    have h2 : (do
        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do
            pure PUnit.unit
            pure (ForInStep.yield (r_1 ++ [r]))
        pure PUnit.unit
        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))
      = Id.run (forIn mig.replaces ([] : List MigrationId)
          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl
    rw [h2, unapplyMigration_forIn]; simp
  · rw [if_neg h]
    push_neg at h
    rw [h]; rfl
-- proof-end
