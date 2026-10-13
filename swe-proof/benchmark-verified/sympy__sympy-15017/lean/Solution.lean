import Mathlib
-- imports-end

/-!
The number of elements held by an N-dimensional array.

An N-dimensional array has a shape: a finite list of non-negative dimension
sizes (for example a 2×3 array has shape `[2, 3]`). The number of elements the
array contains is the product of its dimension sizes. A rank-0 array — one with
no dimensions at all, i.e. a scalar — therefore holds a single element, matching
the convention that an empty product is one.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the dimension sizes are
-- the inputs, and the element count is their product, modeled directly.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required.)
-- pure-end

-- post-conditions-start
/-- The element count is exactly the product of the dimension sizes. The product
of the empty list is one, so a scalar (no dimensions) has a single element; for
any list of dimensions the count is pinned to their product. -/
def problem_spec_arraySize (shape : List Nat) (result : Nat) : Prop :=
  result = shape.prod
-- post-conditions-end

-- impl-start
def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    acc := acc * d
  return acc
-- impl-end

-- proof-start
theorem correct_arraySize :
    ∀ (shape : List Nat),
      problem_spec_arraySize shape (implementation_arraySize shape) := by
  intro shape
  unfold problem_spec_arraySize implementation_arraySize
  have h : ∀ (acc : Nat) (l : List Nat),
      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
        = l.foldl (· * ·) acc := by
    intro acc l
    induction l generalizing acc with
    | nil => rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih, List.foldl_cons]
  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
  rw [h]
  rw [List.prod_eq_foldl]
-- proof-end
