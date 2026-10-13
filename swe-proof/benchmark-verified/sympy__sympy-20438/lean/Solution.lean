import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed as an axiom: the enumeration of the product's
-- tuples and the membership test against the candidate collection are modeled
-- DEEPLY below (`productSet` / `List.contains`), so there is no `opaque` callee
-- and no consumed `_prop` axiom here. (A-reference rows, G-AX validated.)
-- axioms-end

-- pure-start
/-- Enumeration of all tuples of a finite product of finite integer collections.
The product is given by its list of factors; the result lists every tuple
obtained by choosing one element from each factor in order (the cartesian
product, front-recursive on the factor list). An empty factor list has the
single empty tuple. -/
def productSet : List (List Int) → List (List Int)
  | [] => [[]]
  | f :: fs => f.flatMap (fun a => (productSet fs).map (fun rest => a :: rest))
-- pure-end

-- post-conditions-start
/-- The subset test of a finite product of finite integer collections against a
finite collection of integer tuples. The verdict is *determined* (`some _`): it
is `some true` exactly when every tuple of the product is a member of the
candidate collection, and `some false` otherwise. (`none` would denote an
undetermined verdict, which the determined membership test never yields on this
finite collection domain.) -/
def problem_spec_isSubset
    (factors : List (List Int)) (candidate : List (List Int)) (result : Option Bool) : Prop :=
  result = some ((productSet factors).all (fun x => candidate.contains x))
-- post-conditions-end

-- impl-start
def implementation_isSubset
    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
  let mut acc := true
  for x in productSet factors do
    acc := acc && candidate.contains x
  return some acc
-- impl-end

-- proof-start
theorem correct_isSubset : ∀ (factors : List (List Int)) (candidate : List (List Int)),
    problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
  intro factors candidate
  unfold problem_spec_isSubset implementation_isSubset
  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
  have hfold : ∀ (xs : List (List Int)) (b : Bool),
      Id.run (forIn xs b (fun x r =>
        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
        = xs.foldl (fun r x => r && candidate.contains x) b := by
    intro xs
    induction xs with
    | nil => intro b; rfl
    | cons a as ih =>
      intro b
      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
  -- the accumulating `&&`-fold equals `b && List.all`
  have hall : ∀ (xs : List (List Int)) (b : Bool),
      xs.foldl (fun r x => r && candidate.contains x) b
        = (b && xs.all (fun x => candidate.contains x)) := by
    intro xs
    induction xs with
    | nil => intro b; simp
    | cons a as ih =>
      intro b
      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
  -- `pure …` form (definitionally equal), then discharge with the helpers
  show some (Id.run (forIn (productSet factors) true (fun x r =>
        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
  rw [hfold, hall, Bool.true_and]
-- proof-end
