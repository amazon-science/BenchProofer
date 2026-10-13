import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. The element-wise
-- multiply-and-accumulate reduction (the array contraction used to combine the
-- not-null mask with the weights) is modeled DEEPLY below (`zipDot`/`sowSpec`),
-- so there is no `opaque` callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- Element-wise combine-and-accumulate of a not-null mask with a sequence of
boolean weights, evaluated in integer arithmetic: each position contributes `1`
exactly when both its mask flag and its weight are set, and `0` otherwise; the
contributions are summed in input order (a front-recursive fold). -/
def zipDot : List (Bool × Bool) → Int
  | [] => 0
  | (m, w) :: rest => (if m && w then 1 else 0) + zipDot rest

/-- Aggregate weight associated with the retained (not-null) entries. It is the
integer-valued accumulation of the per-position contributions; a total of `0` is
treated as the absence of a valid aggregate (`none`), every positive total is
reported as `some` of that total. -/
def sowSpec (mask weights : List Bool) : Option Int :=
  let s := zipDot (mask.zip weights)
  if s = 0 then none else some s
-- pure-end

-- post-conditions-start
/-- The result is the aggregate weight of the entries kept by the not-null mask:
each kept position whose weight is set adds one unit, the units are summed in
integer arithmetic over the paired sequences, and a total of zero is reported as
the absence of a valid aggregate. -/
def problem_spec_sumOfWeights
    (mask weights : List Bool) (result : Option Int) : Prop :=
  result = sowSpec mask weights
-- post-conditions-end

-- impl-start
def implementation_sumOfWeights (mask weights : List Bool) : Option Int := Id.run do
  let mut acc : Int := 0
  for (m, w) in mask.zip weights do
    if m && w then
      acc := acc + 1
  if acc = 0 then
    return none
  return some acc
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation loop equals the front-recursive `zipDot`
fold, offset by the initial accumulator value. Generalized over `init` so the
induction goes through. -/
theorem fold_helper (xs : List (Bool × Bool)) (init : Int) :
    Id.run (forIn xs init (fun x r =>
      if (x.1 && x.2) = true then pure (ForInStep.yield (r + 1))
      else pure (ForInStep.yield r))) = init + zipDot xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, zipDot, add_zero]; rfl
  | cons a as ih =>
    obtain ⟨m, w⟩ := a
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (m && w) = true
    · simp only [h, if_true, ih, zipDot]; ring
    · simp only [Bool.not_eq_true] at h
      simp only [h, Bool.false_eq_true, if_false, ih, zipDot]; ring

theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
    mask.length = weights.length →
    problem_spec_sumOfWeights mask weights
      (implementation_sumOfWeights mask weights) := by
  intro mask weights _
  unfold problem_spec_sumOfWeights implementation_sumOfWeights sowSpec
  have hf := fold_helper (mask.zip weights) 0
  simp only [Id.run, zero_add, bind, pure] at hf ⊢
  rw [hf]
-- proof-end
