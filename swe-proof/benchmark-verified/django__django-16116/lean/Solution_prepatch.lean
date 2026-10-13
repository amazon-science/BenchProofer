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
/-- Pre-patch behavior: when changes were detected, the run ALWAYS emits migration
output first — merging into the latest migration when requested, a fresh migration
file otherwise — and only afterwards, in verification-only mode, requests a
non-zero exit. So in verification-only mode it still produces migration output
where none should be emitted. -/
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  if checkOnly then
    return { eff with exitCode := some 1 }
  return eff
-- impl-end

-- proof-start
theorem correct_processChanges :
    ∀ (hasChanges checkOnly mergeIntoLast : Bool),
    problem_spec_processChanges hasChanges checkOnly mergeIntoLast
      (implementation_processChanges hasChanges checkOnly mergeIntoLast) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
