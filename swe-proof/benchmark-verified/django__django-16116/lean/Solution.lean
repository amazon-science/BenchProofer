import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The command consults three
-- already-decided inputs — whether model changes were detected, whether the
-- run was requested in verification-only mode, and whether it should merge into
-- the latest migration — all modeled as plain parameters. The two file-emitting
-- procedures are unchanged side-effecting steps whose only relevant observable is
-- WHETHER they ran on this invocation; that is recorded by a Boolean field, so
-- nothing is abstracted behind a callee. The proof agent may add `_prop` axioms
-- only if it gets stuck.
-- axioms-end

-- pure-start
/-- The observable effects of one run of the migration-creation command on the
"changes" decision. `wroteToLast` records that the run emitted output by merging
into the latest existing migration; `wroteNew` records that it emitted output as a
fresh migration file; `exitCode` records the process exit status the run requests
(`none` = normal completion, `some n` = terminate immediately with status `n`). -/
structure CommandEffect where
  /-- The run merged its output into the latest existing migration. -/
  wroteToLast : Bool
  /-- The run emitted its output as a fresh migration file. -/
  wroteNew : Bool
  /-- The exit status the run requests, if it terminates early. -/
  exitCode : Option Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Behavior the command must exhibit on the "changes" decision.

* When no model changes were detected, nothing is emitted and the run completes
  normally.
* When changes were detected and the run is in verification-only mode, the run
  must terminate immediately with a non-zero status and emit nothing — it reports
  the missing migrations without producing any migration output.
* Otherwise the run emits exactly one form of migration output — merged into the
  latest migration when merge mode is requested, a fresh migration file
  otherwise — and completes normally.

Every effect field is pinned for every combination of inputs, so the requested
exit status and the two emit-flags are each fully determined. -/
def problem_spec_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) (result : CommandEffect) : Prop :=
  if !hasChanges then
    result.wroteToLast = false ∧ result.wroteNew = false ∧ result.exitCode = none
  else if checkOnly then
    result.wroteToLast = false ∧ result.wroteNew = false ∧ result.exitCode = some 1
  else
    result.wroteToLast = mergeIntoLast ∧
    result.wroteNew = (!mergeIntoLast) ∧
    result.exitCode = none
-- post-conditions-end

-- impl-start
/-- Decide the effects of a run from the three already-determined inputs. With no
detected changes there is nothing to do. Otherwise, when the run is in
verification-only mode it requests an immediate non-zero exit before any output is
emitted; only when it is NOT in that mode does it emit migration output — merging
into the latest migration when requested, a fresh migration file otherwise. -/
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff
-- impl-end

-- proof-start
theorem correct_processChanges :
    ∀ (hasChanges checkOnly mergeIntoLast : Bool),
    problem_spec_processChanges hasChanges checkOnly mergeIntoLast
      (implementation_processChanges hasChanges checkOnly mergeIntoLast) := by
  intro hasChanges checkOnly mergeIntoLast
  unfold problem_spec_processChanges implementation_processChanges
  cases hasChanges <;> cases checkOnly <;> cases mergeIntoLast <;>
    simp [Id.run, bind, pure]
-- proof-end
