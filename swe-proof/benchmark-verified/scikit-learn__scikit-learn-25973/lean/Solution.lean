import Mathlib
-- imports-end

/-!
A routine that performs a preset number of independent evaluations, where every
evaluation must consult the SAME shared collection of items.

The collection is supplied by a source. That source may only support being read
once (`oneShot = true`): after a single traversal it yields nothing further. A
source that can be read repeatedly (`oneShot = false`) returns the whole
collection every time it is consulted.

Required behaviour: every one of the `numEvals` evaluations observes the
COMPLETE collection — even when the source is single-traversal. The number of
evaluations is otherwise unconstrained, and the result must contain exactly one
observation per evaluation.

Modeled with the collection as `List Nat`, a boolean recording whether the
source is single-traversal, and the evaluation count as `Nat`. The result is the
sequence of collections actually observed, one per evaluation, in order.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the collection contents are taken
-- as the input `folds`, and the obligation to make every evaluation observe the
-- complete collection is modeled deeply (the result is pinned element-wise).
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the modeled behaviour is a direct
-- relation between the inputs and the observed-collection sequence.
-- pure-end

-- post-conditions-start
/-- Specification of the repeated-evaluation routine.

* The result records exactly one observation per evaluation (`length = numEvals`).
* Every observation is the COMPLETE collection `folds`.

The single-traversal flag `oneShot` does NOT appear on the right-hand side: the
observed collections are independent of it — a single-traversal source must be
handled so that no observation is ever short. -/
def problem_spec_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat)
    (result : List (List Nat)) : Prop :=
  result.length = numEvals ∧ (∀ s ∈ result, s = folds)
-- post-conditions-end

-- impl-start
def implementation_repeatedEvaluations
    (folds : List Nat) (oneShot : Bool) (numEvals : Nat) : List (List Nat) := Id.run do
  -- Capture the collection into a reusable value once, before any evaluation
  -- runs, so that it can be consulted again regardless of whether its source
  -- supports only a single traversal. `oneShot` is therefore never consulted.
  let shared := folds
  let mut observed : List (List Nat) := []
  for _ in [0:numEvals] do
    observed := observed ++ [shared]
  return observed
-- impl-end

-- proof-start
theorem correct_repeatedEvaluations :
    ∀ (folds : List Nat) (oneShot : Bool) (numEvals : Nat),
      problem_spec_repeatedEvaluations folds oneShot numEvals
        (implementation_repeatedEvaluations folds oneShot numEvals) := by
  intro folds oneShot numEvals
  -- Helper: the desugared loop body, generalized over the accumulator, just
  -- appends one copy of `folds` per iteration, i.e. `replicate length folds`.
  have helper : ∀ (xs : List Nat) (acc : List (List Nat)),
      (forIn xs acc (fun _ r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [folds]))) : Id _)
        = acc ++ List.replicate xs.length folds := by
    intro xs
    induction xs with
    | nil => intro acc; show acc = acc ++ List.replicate 0 folds; simp
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn as (acc ++ [folds]) _ : Id _) = _
      rw [ih]
      simp [List.replicate_succ, List.append_assoc]
  -- The implementation reduces to `List.replicate numEvals folds`.
  have key : implementation_repeatedEvaluations folds oneShot numEvals
      = List.replicate numEvals folds := by
    unfold implementation_repeatedEvaluations
    simp only [Id.run, Std.Range.forIn_eq_forIn_range']
    rw [show (do
        let r ← forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds]))
        pure r : Id (List (List Nat))) = forIn (List.range' 0 [:numEvals].size) [] fun _ r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [folds])) from rfl]
    rw [helper]
    simp [Std.Range.size]
  rw [problem_spec_repeatedEvaluations, key]
  refine ⟨by simp, ?_⟩
  intro s hs
  exact List.eq_of_mem_replicate hs
-- proof-end
