import Mathlib
-- imports-end

/-!
Provisioning the bookkeeping table that records applied migration work.

Before a batch of migration operations runs, the system may need to provision a
small bookkeeping table whose rows record which migrations have already been
applied. Provisioning that table is only appropriate when there is migration
work to record.

The batch of work to perform is described by `plannedOps`:

  * `none` — the caller asks the routine to compute the batch itself;
  * `some []` — the caller explicitly states there is nothing to do;
  * `some (_ :: _)` — the caller supplies a non-empty batch of work.

`tableExists` says whether the bookkeeping table is already present.

The desired behavior:

  * When the caller explicitly supplies an empty batch (`some []`), the
    bookkeeping table must NOT be provisioned. If, in addition, the table is
    absent, the routine short-circuits and returns a project state that includes
    no already-applied migrations.
  * Otherwise (there is work to record, or the batch is left for the routine to
    compute) the bookkeeping table is provisioned and the routine proceeds
    through its unchanged remainder, yielding that remainder's project state.

The two observable components are whether provisioning was performed and which
project state is returned.
-/

-- axioms-start
-- No UNCHANGED outside callee needs an `opaque` signature here. The two inputs
-- the routine branches on (the planned batch and whether the bookkeeping table
-- is present) enter as plain data, and the only operation performed — the
-- guarded decision about whether to provision the table and whether to
-- short-circuit — is modeled directly (below). The construction of the returned
-- project states (the short-circuit state, and the state produced by the
-- unchanged remainder) is represented by structural carriers in the `pure`
-- region rather than abstracted behind a consumed axiom. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A single planned migration operation, reduced to an opaque identity (only
the shape of the batch — empty / non-empty / absent — is ever observed). -/
abbrev PlannedOp := Nat

/-- The project state the routine yields. Two distinguishable shapes are
relevant:

* `projectState includesApplied` — a freshly built project state, carrying the
  already-applied migrations iff `includesApplied` is `true`. The short-circuit
  path returns `projectState false` (a state with no applied migrations).
* `continuationResult plannedOps` — the project state produced by the routine's
  unchanged remainder for the given batch. It is left as an opaque structural
  carrier because that remainder is not touched by the behavior under
  specification. -/
inductive State where
  | projectState (includesApplied : Bool) : State
  | continuationResult (plannedOps : Option (List PlannedOp)) : State
deriving DecidableEq

/-- The two observable components of the routine's outcome:

* `provisionedTable` — whether the bookkeeping-table provisioning step was
  performed;
* `state` — the project state returned. -/
structure Outcome where
  provisionedTable : Bool
  state : State
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The outcome is pinned, in both components, to the inputs:

* an explicitly empty batch with the table absent ⇒ no provisioning and the
  short-circuit no-applied state;
* an explicitly empty batch with the table present ⇒ no provisioning, then the
  unchanged remainder's state for the empty batch;
* any other batch (absent, or non-empty) ⇒ provisioning is performed, then the
  unchanged remainder's state for that batch. -/
def problem_spec_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool)
    (result : Outcome) : Prop :=
  if plannedOps = some [] then
    if tableExists then
      result = { provisionedTable := false, state := State.continuationResult (some []) }
    else
      result = { provisionedTable := false, state := State.projectState false }
  else
    result = { provisionedTable := true, state := State.continuationResult plannedOps }
-- post-conditions-end

-- impl-start
def implementation_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
  -- Pre-fix behavior: the bookkeeping table is always provisioned up front,
  -- unconditionally, before any work is considered.
  let mut provisioned := false
  provisioned := true
  -- the routine's unchanged remainder produces the project state.
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
-- impl-end

-- proof-start
theorem correct_provisionRecordsTable :
    ∀ (plannedOps : Option (List PlannedOp)) (tableExists : Bool),
      problem_spec_provisionRecordsTable plannedOps tableExists
        (implementation_provisionRecordsTable plannedOps tableExists) := by
  intro plannedOps tableExists
  unfold problem_spec_provisionRecordsTable implementation_provisionRecordsTable
  by_cases h : plannedOps = some []
  · simp only [h, if_true]
    by_cases ht : tableExists = true
    · simp [ht]
    · simp [ht]
  · simp only [h, if_false]
-- proof-end
