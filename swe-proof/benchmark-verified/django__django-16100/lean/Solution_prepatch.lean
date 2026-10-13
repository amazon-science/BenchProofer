import Mathlib
-- imports-end

/-!
A bulk-edit view processes a sequence of pending record updates. Each pending
update applies a sequence of writes to the shared data store and may fail
(raise). The desired behaviour is all-or-nothing: if every pending update
applies cleanly the store reflects all of them; if any update fails, the store
is observed in exactly its original state and the failure is reported.

The model abstracts each pending update as a single state-transition
`σ → Except E σ`: it either yields the next store state (the update committed)
or reports a failure value. `result = (storeState, maybeFailure)` records the
observable store state together with whether a failure propagated.
-/

-- axioms-start
-- No unchanged callee is axiomatized: each pending update is modeled deeply as
-- an input state-transition, so there is no consumed axiom and no opaque decl.
-- axioms-end

-- pure-start
/-- Apply a sequence of state-transitions front-to-back, short-circuiting on the
first failure. Returns the final state if all succeed, else the first failure. -/
def applyAll {σ E : Type} (s0 : σ) (steps : List (σ → Except E σ)) : Except E σ :=
  steps.foldl (fun acc f => acc.bind f) (Except.ok s0)
-- pure-end

-- post-conditions-start
def problem_spec_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) (result : σ × Option E) : Prop :=
  match applyAll s0 steps with
  | .ok sf    => result = (sf, none)
  | .error e  => result = (s0, some e)
-- post-conditions-end

-- impl-start
def implementation_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) : σ × Option E := Id.run do
  let mut s := s0
  for f in steps do
    match f s with
    | .ok s'   => s := s'
    | .error e => return (s, some e)
  return (s, none)
-- impl-end

-- proof-start
theorem correct_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) :
    problem_spec_changelistView s0 steps
      (implementation_changelistView s0 steps) := by
  sorry
-- proof-end

#print axioms correct_changelistView
