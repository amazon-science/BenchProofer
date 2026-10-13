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
-- Pre-patch (buggy) skeleton: a migration that stands in for others records
-- ONLY the identifiers it stands in for and omits its own identifier; only a
-- migration that stands in for nothing records its own identifier.
def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do
  let mut recorded : List MigrationId := []
  if mig.replaces ≠ [] then
    for r in mig.replaces do
      recorded := recorded ++ [r]
  else
    recorded := recorded ++ [(mig.appLabel, mig.name)]
  return recorded
-- impl-end

-- proof-start
theorem correct_unapplyMigration : ∀ mig : Migration,
    problem_spec_unapplyMigration mig (implementation_unapplyMigration mig) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
