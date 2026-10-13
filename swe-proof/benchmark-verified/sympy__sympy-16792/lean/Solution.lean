import Mathlib
-- imports-end

/-!
Computing the index-bound metadata of a procedure argument when the procedure's
argument order is pinned by the caller and the argument does not otherwise occur
in the procedure body.

A scalar argument carries no index bounds (it is a single value). An
array-valued argument — one whose value has a shape (a sequence of axis sizes) —
must instead carry, for each of its axes, the inclusive index range
`(0, size - 1)`. This index-bound metadata is what later determines whether the
argument is emitted as a pointer/array rather than a plain scalar in the
generated signature.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (a Boolean branch and an element-wise map over a
-- shape).
-- axioms-end

-- pure-start
/-- The inclusive index range for each axis of a shape: an axis of `size` spans
indices `0 … size - 1`, modeled as the bound pair `(0, size - 1)`. -/
def boundsOf (shape : List Int) : List (Int × Int) :=
  shape.map (fun d => ((0 : Int), d - 1))
-- pure-end

-- post-conditions-start
/-- The argument's index-bound metadata is the per-dimension bound list of its
shape when the argument is array-valued, and the empty list (no bounds, i.e. a
scalar) otherwise. -/
def problem_spec_arrayArgBounds (isArrayLike : Bool) (shape : List Int)
    (result : List (Int × Int)) : Prop :=
  result = (if isArrayLike then boundsOf shape else [])
-- post-conditions-end

-- impl-start
def implementation_arrayArgBounds (isArrayLike : Bool) (shape : List Int) :
    List (Int × Int) := Id.run do
  let mut metadata : List (Int × Int) := []
  if isArrayLike then
    metadata := boundsOf shape
  else
    metadata := []
  return metadata
-- impl-end

-- proof-start
theorem correct_arrayArgBounds :
    ∀ (isArrayLike : Bool) (shape : List Int),
      problem_spec_arrayArgBounds isArrayLike shape
        (implementation_arrayArgBounds isArrayLike shape) := by
  intro isArrayLike shape
  unfold problem_spec_arrayArgBounds implementation_arrayArgBounds
  cases isArrayLike <;> rfl
-- proof-end
