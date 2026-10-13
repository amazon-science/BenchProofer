import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The combined predicate is
-- modeled DEEPLY at the level of its boolean semantics: the disjunction of the
-- operands, the count of true operands, the parity/equality test on that count,
-- and the final conjunction are all reproduced concretely as ordinary boolean
-- and arithmetic operations rather than axiomatized. The proof agent may add
-- `_prop` axioms only if it gets genuinely stuck.
-- axioms-end

-- pure-start
/-- The number of operands whose condition holds, taken over the list of operand
truth values. -/
def countTrue (cs : List Bool) : Nat :=
  (cs.filter (fun b => b)).length
-- pure-end

-- post-conditions-start
/-- Boolean semantics of the combined predicate built from a list of operand
truth values `cs`. The combined predicate must be true exactly when an odd number
of the operands are true (the meaning of an n-ary exclusive-or). The whole output
is pinned to this single parity relation on the inputs; nothing is left free. -/
def problem_spec_xorFallback (cs : List Bool) (result : Bool) : Prop :=
  result = (countTrue cs % 2 == 1)
-- post-conditions-end

-- impl-start
def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
  -- Disjunction of every operand condition.
  let mut lhs := false
  for c in cs do
    lhs := lhs || c
  -- Sum of one-per-true-operand contributions.
  let mut rhsSum : Nat := 0
  for c in cs do
    if c then
      rhsSum := rhsSum + 1
  -- Test on the running sum: with more than two operands the parity of the sum
  -- is taken before comparing to one; otherwise the sum is compared directly.
  let mut rhs := false
  if cs.length > 2 then
    rhs := (rhsSum % 2 == 1)
  else
    rhs := (rhsSum == 1)
  return lhs && rhs
-- impl-end


-- proof-start
theorem correct_xorFallback :
    ∀ (cs : List Bool),
    problem_spec_xorFallback cs (implementation_xorFallback cs) := by
  have hsum : ∀ (l : List Bool) (n : Nat),
      List.foldl (fun r c => if c = true then r + 1 else r) n l = n + countTrue l := by
    intro l
    induction l with
    | nil => intro n; simp [countTrue]
    | cons a t ih => intro n; cases a <;> simp [countTrue, List.filter, List.foldl, ih] <;> omega
  have hor : ∀ (l : List Bool) (b : Bool),
      List.foldl (fun r c => r || c) b l = (b || decide (0 < countTrue l)) := by
    intro l
    induction l with
    | nil => intro b; simp [countTrue]
    | cons a t ih =>
      intro b
      rw [List.foldl_cons, ih (b || a)]
      cases a <;> simp [countTrue, List.filter]
  intro cs
  simp only [problem_spec_xorFallback, implementation_xorFallback, Id.run]
  simp only [bind, pure]
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl, List.forIn_yield_eq_foldl]
  rw [hor, hsum]
  simp only [Nat.zero_add]
  have hle : countTrue cs ≤ cs.length := List.length_filter_le _ _
  split
  · rcases Nat.eq_zero_or_pos (countTrue cs) with h | h
    · simp [h]
    · simp [decide_eq_true h]
  · rename_i hlen
    have h2 : countTrue cs ≤ 2 := by omega
    interval_cases hc : countTrue cs <;> simp

-- proof-end
