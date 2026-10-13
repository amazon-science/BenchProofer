import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The behaviour under specification is a pure control-flow decision;
-- it calls no callee whose contract the proof must assume. The two facts the
-- gate observes — whether there is work to record, and whether the backing
-- store already exists — enter the model as plain boolean inputs, and the two
-- effects it governs are tracked as boolean observations of the step. There is
-- therefore nothing to axiomatise (mapping.md §3, refinement.md §C).
-- axioms-end

-- pure-start
/- The observable outcome of the step's preparation phase:
   `ensured`   — whether the side effect that materialises the bookkeeping store
                 is performed during this step;
   `earlyExit` — whether the step short-circuits, producing its result without
                 running the remainder of the procedure.
   These are exactly the two observations the behaviour is judged on
   (mapping.md §1). -/
structure GateOutcome where
  ensured   : Bool
  earlyExit : Bool
deriving Repr, Inhabited, DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- The preparation phase of the step, parameterised by the two facts it
   consults:
     `hasWork`  — there is at least one item to record this step;
     `storePresent` — the bookkeeping store already exists.
   The desired behaviour, stated as direct relations on the inputs (no opaque
   oracle):
   * the store-materialising effect runs exactly when there IS work to record;
   * the step short-circuits exactly when there is NO work to record and the
     store is absent — i.e. nothing would be recorded and nothing must be
     created on its behalf. -/
method recordStoreGate (hasWork : Bool) (storePresent : Bool) return (r : GateOutcome)
  ensures r.ensured   = hasWork
  ensures r.earlyExit = (!hasWork && !storePresent)
  do
    -- impl-start
    -- Pre-image skeleton: the store-materialising effect is performed
    -- unconditionally on every step, and the step never short-circuits.
    -- The frozen spec requires the effect to run only when there is work
    -- (and to short-circuit on the empty/absent case), so prove_correct
    -- MUST fail on both `ensures` clauses.
    let mut ensured   : Bool := false
    let mut earlyExit : Bool := false
    ensured := true
    return ⟨ensured, earlyExit⟩
    -- impl-end

prove_correct recordStoreGate by
  loom_solve
