import Mathlib
-- imports-end

/-!
Reassembling a full-length coordinate vector from a reduced one.

A reduced view of a coordinate system keeps only some of the axes of a larger
underlying system. Going back from the reduced view to the underlying system
requires rebuilding a full-length coordinate vector: the underlying system has
`worldNDim` axes, of which a sorted subset `worldKeep` is retained by the view.

To rebuild the full vector, walk the underlying axes in order. For each axis:

* if the axis is one of the kept axes, take the next value from the supplied
  reduced vector (`inputs`), consuming those values left-to-right;
* otherwise the axis is omitted from the reduced view, so its value is not
  supplied by the caller — fill it with the reference value for that axis,
  read from a per-axis reference vector `slicedOut` indexed by the underlying
  axis number.

The result is a vector of length `worldNDim`: every kept axis carries the
corresponding supplied value, and every omitted axis carries its reference
value. The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the reassembly is spelled
-- out concretely as positional placement of supplied values into kept axes and
-- reference values into the omitted axes. The reference vector is taken as an
-- input (it is produced upstream and is not part of the reassembly itself).
-- axioms-end

-- pure-start
-- No additional pure helpers are needed; the predicate is stated directly with
-- list length and positional (`getD`) lookups.
-- pure-end

-- post-conditions-start
/-- The reassembled vector `result` has one entry per underlying axis:

* it has length `worldNDim`;
* every omitted axis (`iworld < worldNDim` with `iworld ∉ worldKeep`) carries the
  reference value `slicedOut.getD iworld`;
* the `c`-th kept axis (`worldKeep.getD c`, for `c < worldKeep.length`) carries
  the `c`-th supplied value `inputs.getD c`.

Together these pin every position of `result`. -/
def problem_spec_assemble (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut result : List Int) : Prop :=
  result.length = worldNDim ∧
  (∀ iworld, iworld < worldNDim → iworld ∉ worldKeep →
      result.getD iworld 0 = slicedOut.getD iworld 0) ∧
  (∀ c, c < worldKeep.length →
      result.getD (worldKeep.getD c 0) 0 = inputs.getD c 0)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: omitted axes are filled with the constant `1`
-- instead of their reference value, so the reassembled vector no longer agrees
-- with the reference coordinate on the omitted axes.
def implementation_assemble (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut : List Int) : List Int := Id.run do
  let mut result : List Int := []
  let mut iworldCurr : Nat := 0
  for iworld in [0:worldNDim] do
    if iworld ∈ worldKeep then
      result := result ++ [inputs.getD iworldCurr 0]
      iworldCurr := iworldCurr + 1
    else
      result := result ++ [(1 : Int)]
  return result
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (the
-- constant `1` on omitted axes contradicts the `result … = slicedOut …` clause
-- whenever the reference value there is not `1`).
theorem correct_assemble :
    ∀ (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int),
      worldKeep.Sorted (· < ·) →
      (∀ i ∈ worldKeep, i < worldNDim) →
      inputs.length = worldKeep.length →
      slicedOut.length = worldNDim →
      problem_spec_assemble worldNDim worldKeep inputs slicedOut
        (implementation_assemble worldNDim worldKeep inputs slicedOut) := by
  sorry
-- proof-end
