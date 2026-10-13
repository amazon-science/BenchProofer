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
-- PRE-PATCH (buggy) skeleton: the candidate is kept on the basis of its LARGEST
-- single exponent reaching the threshold, instead of its total degree. A
-- candidate that spreads its degree across several variables (so its largest
-- single exponent is below the threshold while its total degree meets it) is
-- wrongly dropped.
def implementation_selectMonomials
    (minDegree : Nat) (candidates : List (List Nat)) : List (List Nat) :=
  Id.run do
    let mut acc := []
    for powers in candidates do
      if minDegree ≤ powers.foldr Nat.max 0 then
        acc := acc ++ [powers]
    return acc
-- impl-end

-- proof-start
-- Carried gold proof body: it closes against the correct (post-patch) impl,
-- which filters by the total degree (`powers.sum`). Against the pre-patch impl
-- above — which filters by the largest single exponent (`powers.foldr Nat.max
-- 0`) — the `h2 := rfl` bridge from the desugared loop body to the sum-keyed
-- `select_helper` form does not hold, so the proof fails to typecheck (G-DIFF).
theorem select_helper (minDegree : Nat) (xs : List (List Nat))
    (init : List (List Nat)) :
    (Id.run (forIn xs init (fun powers acc =>
      (if minDegree ≤ powers.sum then ForInStep.yield (acc ++ [powers])
       else ForInStep.yield acc : Id (ForInStep (List (List Nat)))))))
    = init ++ xs.filter (fun powers => decide (minDegree ≤ powers.sum)) := by
  induction xs generalizing init with
  | nil => simp only [List.filter_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.filter_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : minDegree ≤ a.sum
    · simp only [h, if_true, ih, decide_true]
      simp [List.append_assoc]
    · simp only [h, if_false, ih, decide_false]
      simp

theorem correct_selectMonomials :
    ∀ (minDegree : Nat) (candidates : List (List Nat)),
      problem_spec_selectMonomials minDegree candidates
        (implementation_selectMonomials minDegree candidates) := by
  intro minDegree candidates
  unfold problem_spec_selectMonomials implementation_selectMonomials
  have h2 : (Id.run (do
      let r ← forIn candidates [] fun powers acc =>
        (if minDegree ≤ powers.sum then (do pure PUnit.unit; pure (ForInStep.yield (acc ++ [powers])))
         else (do pure PUnit.unit; pure (ForInStep.yield acc)) : Id (ForInStep (List (List Nat))))
      pure r) : List (List Nat))
    = Id.run (forIn candidates [] fun powers acc =>
        (if minDegree ≤ powers.sum then ForInStep.yield (acc ++ [powers])
         else ForInStep.yield acc : Id (ForInStep (List (List Nat))))) := rfl
  show (Id.run _ : List (List Nat)) = _
  rw [h2, select_helper]
  simp
-- proof-end
