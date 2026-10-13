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
  -- pre-patch reduction: the mask and weights are combined with the SAME boolean
  -- contraction that the underlying array routine uses for boolean inputs — a
  -- disjunction over the per-position conjunctions. The total therefore saturates
  -- at "is there any kept, set position" (one unit) instead of counting them.
  let mut acc : Bool := false
  for (m, w) in mask.zip weights do
    if m && w then
      acc := acc || true
  if acc = false then
    return none
  return some 1
-- impl-end

-- proof-start
theorem correct_sumOfWeights : ∀ (mask weights : List Bool),
    mask.length = weights.length →
    problem_spec_sumOfWeights mask weights
      (implementation_sumOfWeights mask weights) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
