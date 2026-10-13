import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The startup routine performs two observable effects
--  — emitting the progress announcement and invoking the system-check routine —
--  whose mere occurrence (not their internal result) is what the behavior pins.
--  Each occurrence is modeled directly as a boolean state write, not behind a
--  consumed callee contract. The unchanged check routine whose invocation the
--  `checked` flag records asserts nothing about its return value, so there is no
--  axiom to validate against a real callee.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A development server's startup routine may perform system checks before it
   begins serving. Performing them has two outwardly observable effects: a
   progress announcement is emitted to the operator, and the system-check
   routine is invoked.

   The desired behavior: a single request flag controls whether these checks are
   performed. When the operator asks to skip the checks, BOTH effects must be
   suppressed — no announcement is emitted and the check routine is not invoked.
   When the operator does not ask to skip them, BOTH effects must occur — the
   announcement is emitted and the check routine is invoked. The two effects are
   governed together by the one flag; neither may occur independently of the
   other.

   `skipChecks` is the read-only request flag (not `mut`): the routine decides
   based on it and never alters it (directive 5). `announced` and `checked` are
   the two effect observables, each false on entry (these effects have not yet
   happened at this point in startup) and genuinely written by the routine
   (declared `mut`); their post-states are pinned exactly — each is true iff the
   checks were not skipped (directive 5: every reachable frame pinned exactly). -/
method runStartupChecks (skipChecks : Bool) (mut announced : Bool) (mut checked : Bool)
    return (unit : Unit)
  require announced = false
  require checked = false
  ensures announced = (!skipChecks)
  ensures checked = (!skipChecks)
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: the routine performs BOTH effects
    -- unconditionally — it consults no request flag, so the checks always run.
    -- The frozen spec requires both observables to be `!skipChecks`, so when the
    -- operator requests a skip (`skipChecks = true`) the spec demands they stay
    -- false; this skeleton sets them true, so prove_correct MUST fail on both
    -- post-conditions.
    announced := true
    checked := true
    return ()
    -- impl-end

prove_correct runStartupChecks by
  loom_solve
