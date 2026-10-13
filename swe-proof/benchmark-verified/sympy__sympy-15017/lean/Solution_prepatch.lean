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
-- PRE-PATCH (buggy) skeleton: the dimensions are folded with multiplication,
-- but only when there is at least one dimension; with no dimensions the count
-- is special-cased to zero instead of the empty product one. So a scalar
-- (rank-0) array is reported as having zero elements.
def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  match shape with
  | [] => return 0
  | d :: ds =>
    let mut acc := d
    for x in ds do
      acc := acc * x
    return acc
-- impl-end

-- proof-start
theorem correct_arraySize :
    ∀ (shape : List Nat),
      problem_spec_arraySize shape (implementation_arraySize shape) := by
  sorry
-- proof-end
