import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
   pure data-flow over the capture fixture's own retained level state. The level
   register it controls is modeled directly (its `set` is an assignment and its
   observation is a read — mapping.md §2), so there is no consumed axiom and no
   deep-model reference to a foreign callee (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The retained state of a log-capture fixture, restricted to the part that
   governs the capture level:
   * `level`       — the capture level currently in effect;
   * `savedLevel`  — the level to be reinstated when the test ends, if one was
                     recorded (`none` until a level is set during the test). -/
structure FixtureState where
  level : Int
  savedLevel : Option Int
deriving DecidableEq, Inhabited, Repr

/- Construction: a freshly-created fixture is in effect at the ambient level
   `lvl0` and has recorded nothing to reinstate yet. -/
def initState (lvl0 : Int) : FixtureState :=
  { level := lvl0, savedLevel := none }

/- Setting the capture level during a test: record the level currently in effect
   as the one to reinstate at the end of the test, then move to the requested
   level. Recording is unconditional (the level in effect *right now* is what a
   later set should be undone back to), so a second set within the same test
   records the level the first set established. -/
def setLevelState (st : FixtureState) (lvl : Int) : FixtureState :=
  { level := lvl, savedLevel := some st.level }

/- End of test: if a level was recorded for reinstatement, return to it;
   otherwise leave the fixture as-is. This is what makes a level set during the
   test not leak into the next test. -/
def restoreState (st : FixtureState) : FixtureState :=
  match st.savedLevel with
  | some v => { st with level := v }
  | none   => st

/- The level a fixture is left in after a set-then-end-of-test cycle is exactly
   the ambient level it started at: whatever was set during the test is undone.
   This is the property the issue demands. -/
@[grind] lemma restore_after_set (lvl0 lvl : Int) :
    (restoreState (setLevelState (initState lvl0) lvl)).level = lvl0 := by
  simp [initState, setLevelState, restoreState]
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Construction step: a new fixture starts at the ambient level and has nothing
   recorded to reinstate. -/
method initStep (lvl0 : Int) return (st : FixtureState)
  ensures st = initState lvl0
  do
    -- impl-start
    pure { level := lvl0, savedLevel := none }
    -- impl-end

prove_correct initStep by
  loom_solve <;> simp_all [initState]

/- Level-set step: record the level in effect for later reinstatement, then move
   to the requested level. The recorded value is precisely the level the fixture
   was at when the set happened. -/
method setLevelStep (st : FixtureState) (lvl : Int) return (st' : FixtureState)
  ensures st' = setLevelState st lvl
  do
    -- impl-start
    pure { level := lvl, savedLevel := some st.level }
    -- impl-end

prove_correct setLevelStep by
  loom_solve <;> simp_all [setLevelState]

/- End-of-test step: reinstate the recorded level if one was recorded, else
   leave the fixture unchanged. -/
method restoreStep (st : FixtureState) return (st' : FixtureState)
  ensures st' = restoreState st
  do
    -- impl-start
    match st.savedLevel with
    | some v => pure { st with level := v }
    | none   => pure st
    -- impl-end

prove_correct restoreStep by
  loom_solve <;> simp_all [restoreState]

/- The full lifecycle the issue is about: a fresh fixture at ambient level
   `lvl0`, a level set to `lvl` during the test, then the end-of-test cleanup.
   The resulting level is back at `lvl0` — the set is undone, so it cannot leak
   into a subsequent test. -/
method runLifecycle (lvl0 : Int) (lvl : Int) return (out : FixtureState)
  ensures out = restoreState (setLevelState (initState lvl0) lvl)
  ensures out.level = lvl0
  do
    -- impl-start
    let st0 ← initStep lvl0
    let st1 ← setLevelStep st0 lvl
    let st2 ← restoreStep st1
    return st2
    -- impl-end

prove_correct runLifecycle by
  loom_solve
