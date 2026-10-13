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
  -- pre-patch behavior: no subset rule for this combination of carriers exists,
  -- so the per-tuple membership computation is never performed and the verdict
  -- falls through to the generic, undetermined answer.
  let _ := factors
  let _ := candidate
  return none
-- impl-end

-- proof-start
theorem correct_isSubset : ∀ (factors : List (List Int)) (candidate : List (List Int)),
    problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
