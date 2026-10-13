import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two modeled functions are changed functions
--  whose new logic is a pure boolean combination of their inputs, modeled
--  DEEPLY. The skip-mark test is observed only through its boolean result and
--  is itself a modeled (changed) function called by the deferral decision, so
--  it is bound as a sub-method — callee-under-spec — not as an axiom about an
--  unchanged callee. Hence no G-AX.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: each decision is a closed boolean expression.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A test (or the class that contains it) may bear a mark requesting that it be
   skipped. This query reports whether that skip mark is present. The mark's
   presence is observed as a single boolean; the query reads it and mutates
   nothing it is handed (directive 5). Input and result are `Bool`. -/
method markedSkipped (skipMarked : Bool) return (out : Bool)
  ensures out = skipMarked
  do
    -- impl-start
    return skipMarked
    -- impl-end

prove_correct markedSkipped by
  loom_solve

/- When a test is executed under the interactive post-mortem debugger, the
   framework defers that test's teardown so the test instance's state survives
   for inspection at the debugger prompt instead of being cleaned up first. This
   deferral is a special accommodation for the debugger and is applied only to
   ordinary (non-asynchronous) tests — an asynchronous test is driven entirely
   by its own framework and never has its teardown deferred by this mechanism.

   Crucially, the deferral must NOT apply to a test that is being skipped: a
   skipped test's teardown must never be deferred (and thereby run), exactly as
   when the debugger is not in use. Whether the debugger is active, whether the
   test is asynchronous, and whether the test bears a skip mark are observed as
   three DISTINCT read-only booleans, because the decision must discriminate a
   skipped test under the debugger (teardown NOT deferred) from a non-skipped
   one under the debugger (teardown deferred). The query mutates nothing it is
   handed (directive 5). The result is `true` exactly when teardown is deferred. -/
method teardownPostponed (asyncTest : Bool) (debuggerActive : Bool) (skipMarked : Bool) return (postpone : Bool)
  ensures postpone = (!asyncTest && debuggerActive && !skipMarked)
  do
    -- impl-start
    -- Pre-image: teardown was deferred for ANY non-asynchronous test whenever
    -- the debugger was active, with no exception for a skip-marked test. This
    -- skeleton omits the skip exclusion, so the deferred teardown of a skipped
    -- test under the debugger later runs. It MUST fail the frozen spec whenever
    -- a skip-marked test is run under the debugger.
    let decision := !asyncTest && debuggerActive
    return decision
    -- impl-end

prove_correct teardownPostponed by
  loom_solve
