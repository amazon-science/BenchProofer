import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The decision modeled here consumes two unchanged helpers
   purely for their boolean results (whether an interactive debugger is active,
   and whether a unit / its enclosing group carries the skip marker). Those
   results are taken directly as the `Bool` inputs of the modeled decision — an
   R-identity refinement validated against the real helpers by G-CONF, not an
   axiom (mapping.md §3). There is no module-level `axiom` and no `:|` stub. -/
-- axioms-end

-- pure-start
/- Whether to postpone a test's post-run cleanup step.

   When an interactive debugger is active we want to postpone the cleanup so the
   debugger can inspect the instance state before it is torn down. But cleanup
   must be postponed ONLY for tests that are actually going to run: a test that
   is being skipped must not have its cleanup postponed, because a postponed
   cleanup would then be forced to run out of band — and that is undefined for a
   skipped test.

   A test counts as skipped when it is skipped directly OR when the enclosing
   group it belongs to is skipped; both must suppress the postponement. -/
def shouldDefer (debuggerActive unitSkipped groupSkipped : Bool) : Bool :=
  debuggerActive && !(unitSkipped || groupSkipped)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for a single test about to be executed, whether its post-run cleanup
   step is postponed so an active interactive debugger can inspect state.

   Desired behaviour: postpone the cleanup exactly when the debugger is active
   AND the test is not being skipped, where "skipped" covers both the test being
   skipped directly and its enclosing group being skipped. If either form of
   skip applies, the cleanup must NOT be postponed even when the debugger is
   active (a postponed cleanup for a skipped test would otherwise be forced to
   run and fail). -/
method shouldDeferCleanup (debuggerActive : Bool) (unitSkipped : Bool) (groupSkipped : Bool)
    return (out : Bool)
  ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
  do
    -- impl-start
    -- Pre-image skeleton: only the unit's own skip marker is consulted; the
    -- enclosing group's skip marker is ignored. The frozen spec requires a
    -- group-skipped test to also suppress postponement, so on
    -- (debuggerActive = true, unitSkipped = false, groupSkipped = true) this
    -- returns `true` where the spec demands `false` — prove_correct MUST fail.
    let skipped : Bool := unitSkipped
    if debuggerActive && !skipped then
      return true
    else
      return false
    -- impl-end

prove_correct shouldDeferCleanup by
  loom_solve <;>
    cases debuggerActive <;> cases unitSkipped <;> cases groupSkipped <;>
      simp_all [shouldDefer]
