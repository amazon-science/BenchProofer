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
    | .error e => return (s0, some e)
  return (s, none)
-- impl-end


-- proof-start
/-- Explicit recursion mirroring the imperative loop body: `s0` is the fixed
rollback state, `acc` is the mutable loop state. On the first `.error` the loop
returns `(s0, some e)`; if all succeed it returns `(finalAcc, none)`. -/
def loopRec {σ E : Type} (s0 acc : σ) : List (σ → Except E σ) → σ × Option E
  | [] => (acc, none)
  | f :: rest =>
    match f acc with
    | .ok acc' => loopRec s0 acc' rest
    | .error e => (s0, some e)

theorem impl_eq_loopRec {σ E : Type} (s0 : σ) (steps : List (σ → Except E σ)) :
    implementation_changelistView s0 steps = loopRec s0 s0 steps := by
  have key : ∀ (acc : σ),
      (Id.run do
        let mut s := acc
        for f in steps do
          match f s with
          | .ok s'   => s := s'
          | .error e => return (s0, some e)
        return (s, none)) = loopRec s0 acc steps := by
    intro acc
    induction steps generalizing acc with
    | nil => rfl
    | cons f rest ih =>
      simp only [List.forIn_cons, Id.run, bind, pure, loopRec]
      cases hf : f acc with
      | ok s' => exact ih s'
      | error e => rfl
  unfold implementation_changelistView
  exact key s0

theorem applyAll_cons_step {σ E : Type} (acc : σ) (f : σ → Except E σ)
    (rest : List (σ → Except E σ)) :
    applyAll acc (f :: rest) =
      (match f acc with
       | .ok acc' => applyAll acc' rest
       | .error e => .error e) := by
  cases h : f acc with
  | ok acc' => simp [applyAll, List.foldl_cons, Except.bind, h]
  | error e =>
    simp only [applyAll, List.foldl_cons, Except.bind, h]
    induction rest with
    | nil => rfl
    | cons g gs ih => simpa using ih

theorem foldl_bind_error {σ E : Type} (e : E) (rest : List (σ → Except E σ)) :
    List.foldl (fun acc g => acc.bind g) (Except.error e) rest = Except.error e := by
  induction rest with
  | nil => rfl
  | cons g gs ih => simpa using ih

theorem loopRec_eq_closed {σ E : Type} (s0 acc : σ) (steps : List (σ → Except E σ)) :
    loopRec s0 acc steps =
      (match applyAll acc steps with
       | .ok sf   => (sf, none)
       | .error e => (s0, some e)) := by
  induction steps generalizing acc with
  | nil => simp [loopRec, applyAll]
  | cons f rest ih =>
    rw [applyAll_cons_step]
    show (match f acc with
          | .ok acc' => loopRec s0 acc' rest
          | .error e => (s0, some e)) = _
    cases h : f acc with
    | ok acc' => exact ih acc'
    | error e => rfl

theorem correct_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) :
    problem_spec_changelistView s0 steps
      (implementation_changelistView s0 steps) := by
  unfold problem_spec_changelistView
  rw [impl_eq_loopRec, loopRec_eq_closed]
  cases h : applyAll s0 steps with
  | ok sf => rfl
  | error e => rfl

-- proof-end

#print axioms correct_changelistView
