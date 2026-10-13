import Mathlib
-- imports-end

/-!
Deferring a test case's teardown when running under an interactive debugger.

When a `unittest`-style test case is executed, its teardown step is normally run
immediately after the test body. When the interactive post-mortem debugger option
is active, the framework instead *postpones* teardown: it stores the bound
teardown method aside and temporarily replaces it with a no-op, so that the
instance state is still intact when the debugger prompt opens after a failure.

This postponement should only ever be arranged when teardown is actually going to
run for this test:

* a test case driven entirely by the asynchronous framework path arranges no such
  postponement;
* a test case that has been marked to skip has no teardown to debug, so its
  teardown must NOT be postponed (postponing it would arrange for a stored
  teardown to be invoked explicitly later, even though the test was skipped);
* only a non-asynchronous, non-skipped test case, run while the debugger option
  is active, has its teardown postponed.

The decision modeled here is exactly: was teardown postponement arranged for this
test case?
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- modeled structurally over the observable conditions of the test case (whether
-- it is driven by the asynchronous path, whether the interactive-debugger option
-- is active, and whether the case has been marked to skip), each of which enters
-- as a plain Boolean observation, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Whether teardown postponement is arranged for a test case, as a function of
its observable conditions:

* `isAsync` — the case is driven entirely by the asynchronous framework path;
* `usePdb` — the interactive post-mortem debugger option is active;
* `skipped` — the case has been marked to skip.

Postponement is arranged exactly for a non-asynchronous, non-skipped case while
the debugger option is active. -/
def teardownDeferralRule (isAsync usePdb skipped : Bool) : Bool :=
  !isAsync && usePdb && !skipped
-- pure-end

-- post-conditions-start
/-- The postponement decision for the test case is exactly the rule: it is
arranged only for a non-asynchronous, non-skipped case while the debugger option
is active. In particular a skipped case never has its teardown postponed. -/
def problem_spec_deferTeardown
    (isAsync usePdb skipped : Bool) (result : Bool) : Prop :=
  result = teardownDeferralRule isAsync usePdb skipped
-- post-conditions-end

-- impl-start
def implementation_deferTeardown
    (isAsync usePdb skipped : Bool) : Bool := Id.run do
  if isAsync then
    -- asynchronous path: the framework runs the case directly; no postponement
    return false
  -- synchronous path: arrange postponement under the debugger option, without
  -- consulting whether the case was marked to skip
  if usePdb then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_deferTeardown :
    ∀ (isAsync usePdb skipped : Bool),
      problem_spec_deferTeardown isAsync usePdb skipped
        (implementation_deferTeardown isAsync usePdb skipped) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
