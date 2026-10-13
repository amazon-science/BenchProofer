import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the coordinate-wise scaling
-- operation that this behavior delegates to is modeled DEEPLY (a front-recursive
-- fold over the coordinate list, below) rather than axiomatized, so its real
-- reference implementation is validated as an A-reference by G-AX. The proof
-- agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Front-recursive specification fold: scale each coordinate of a point by the
given scalar factor, preserving coordinate order. This is exactly the
coordinate-wise scaling operation a point already supports when the scalar is on
the right. -/
def scaleSpec (factor : Rat) : List Rat → List Rat
  | [] => []
  | x :: xs => (x * factor) :: scaleSpec factor xs
-- pure-end

-- post-conditions-start
/-- Multiplying a scalar `factor` by a point (given by its coordinate list)
succeeds and yields the point whose coordinates are each scaled by `factor`,
matching the result of scaling the same point by the same scalar. The result is
`some scaled` — a well-defined point — never an undefined/error result. -/
def problem_spec_scaleByFactor
    (factor : Rat) (coords : List Rat) (result : Option (List Rat)) : Prop :=
  result = some (scaleSpec factor coords)
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy) skeleton: scaling a scalar by a point on the LEFT is not
defined, so the operation does not produce a point — it yields an undefined/error
result (`none`) rather than the scaled point. -/
def implementation_scaleByFactor
    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do
  return none
-- impl-end

-- proof-start
theorem correct_scaleByFactor : ∀ (factor : Rat) (coords : List Rat),
    problem_spec_scaleByFactor factor coords
      (implementation_scaleByFactor factor coords) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
