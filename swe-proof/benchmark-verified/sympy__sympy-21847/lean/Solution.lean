import Mathlib
-- imports-end

/-!
Selecting monomials of sufficient total degree.

A monomial over a given list of variables is described by its exponent vector:
the per-variable powers, one entry per variable. The *total degree* of such a
monomial is the sum of its exponents.

Given a list of candidate monomials (each as an exponent vector) and a minimum
total degree `minDegree`, the desired behaviour is to keep exactly those
candidates whose total degree is at least `minDegree`, leaving the others out,
and preserving the order in which the candidates were presented.

In particular a candidate is kept on the basis of its *total* degree — the
combined contribution of all its variables — not on the basis of any single
variable's contribution. So a candidate that spreads its degree across several
variables is kept whenever its total degree reaches the threshold, even if no
individual variable does.
-/

-- axioms-start
-- (no unchanged callee needs an opaque declaration: the candidate monomials —
-- already reduced to their exponent vectors — are the input to the modeled
-- selection step, and the total-degree test is modeled directly.)
-- axioms-end

-- pure-start
-- (no additional pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The selected monomials are exactly the candidates whose total degree (the
sum of the exponent vector) is at least `minDegree`, in their original order.

This pins the result completely: a candidate is in the result iff its total
degree meets the threshold, and the relative order of kept candidates is the
order they appeared in. -/
def problem_spec_selectMonomials
    (minDegree : Nat) (candidates : List (List Nat)) (result : List (List Nat)) :
    Prop :=
  result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum))
-- post-conditions-end

-- impl-start
def implementation_selectMonomials
    (minDegree : Nat) (candidates : List (List Nat)) : List (List Nat) :=
  Id.run do
    let mut acc := []
    for powers in candidates do
      if minDegree ≤ powers.sum then
        acc := acc ++ [powers]
    return acc
-- impl-end

-- proof-start
theorem selectMonomials_forIn_eq
    (minDegree : Nat) (candidates : List (List Nat)) (init : List (List Nat)) :
    Id.run (forIn candidates init (fun powers r =>
      if minDegree ≤ powers.sum then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ [powers]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield r)))
      = init ++ candidates.filter (fun powers => decide (minDegree ≤ powers.sum)) := by
  induction candidates generalizing init with
  | nil => simp only [Id.run, List.forIn_nil, List.filter_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : minDegree ≤ a.sum
    · simp [h, ih, List.append_assoc]
    · simp [h, ih]

theorem correct_selectMonomials :
    ∀ (minDegree : Nat) (candidates : List (List Nat)),
      problem_spec_selectMonomials minDegree candidates
        (implementation_selectMonomials minDegree candidates) := by
  intro minDegree candidates
  unfold problem_spec_selectMonomials implementation_selectMonomials
  simp only [Id.run]
  have := selectMonomials_forIn_eq minDegree candidates []
  simp only [Id.run] at this
  rw [this]
  simp
-- proof-end
