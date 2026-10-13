import Mathlib
-- imports-end

/-!
Deciding whether to specially defer a test's teardown step when the interactive
post-mortem debugger is enabled.

A unit test belongs to a containing test class. Either the individual test or the
whole containing class may be marked as "skip" (so the test will not actually
run). Independently, the interactive post-mortem debugger may be enabled for the
run.

When the debugger is enabled, the framework normally intercepts the teardown step
so it can be replayed after the debugger prompt instead of immediately. This
special interception must only happen for a test that is actually going to run:
it must NOT happen when the test is skipped — and a test counts as skipped when
EITHER the test itself is marked skip OR its containing class is marked skip.

Desired behavior: the teardown step is specially deferred exactly when the
debugger is enabled AND the test is not skipped, where "skipped" holds if the
test itself is marked skip or its containing class is marked skip.

Inputs:
  * `pdbEnabled`        — the interactive post-mortem debugger is enabled;
  * `testItselfSkipped` — the individual test is marked skip;
  * `classSkipped`      — the containing test class is marked skip.

Result:
  * `deferTeardown`     — whether the teardown step is specially deferred.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether the
-- individual test, respectively its containing class, is marked skip is an
-- UNCHANGED observation whose boolean outcome enters directly as the plain
-- `testItselfSkipped` / `classSkipped` data; whether the debugger is enabled
-- enters as the plain `pdbEnabled` datum. The only modeled operation — combining
-- those observations into the deferral decision — is modeled directly over that
-- data, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled decision is a direct
-- boolean relation over the three observed inputs.
-- pure-end

-- post-conditions-start
/-- The deferral decision is fully pinned to the inputs: the teardown step is
specially deferred exactly when the debugger is enabled AND the test is not
skipped, where a test is skipped when the test itself is marked skip or its
containing class is marked skip. The single output component is therefore left
no freedom. -/
def problem_spec_deferTeardown
    (pdbEnabled testItselfSkipped classSkipped : Bool) (result : Bool) : Prop :=
  result = (pdbEnabled && !(testItselfSkipped || classSkipped))
-- post-conditions-end

-- impl-start
def implementation_deferTeardown
    (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
  let skipped := testItselfSkipped || classSkipped
  if pdbEnabled && !skipped then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_deferTeardown :
    ∀ (pdbEnabled testItselfSkipped classSkipped : Bool),
      problem_spec_deferTeardown pdbEnabled testItselfSkipped classSkipped
        (implementation_deferTeardown pdbEnabled testItselfSkipped classSkipped) := by
  intro pdbEnabled testItselfSkipped classSkipped
  unfold problem_spec_deferTeardown implementation_deferTeardown
  cases pdbEnabled <;> cases testItselfSkipped <;> cases classSkipped <;> rfl
-- proof-end
