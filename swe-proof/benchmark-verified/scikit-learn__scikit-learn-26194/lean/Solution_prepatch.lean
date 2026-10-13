import Mathlib
-- imports-end

/-!
Building the threshold vector returned by the receiver-operating-characteristic
routine.

The routine first computes, from the scores, a vector of decreasing distinct
score values together with the false/true-positive counts at each of them. An
extra leading position is then prepended to the threshold vector so that the
plotted curve starts at the origin `(0, 0)`: this leading position stands for the
operating point at which no instance is predicted positive.

Because that leading position corresponds to "predict nothing positive", any
finite score is strictly below it; the value placed there is therefore the
positive-infinity sentinel `+∞`. The remaining entries of the returned vector are
exactly the decreasing score thresholds, unchanged.

So the returned threshold vector is the positive-infinity sentinel followed by the
decreasing finite score thresholds.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decreasing
-- finite score thresholds produced upstream (and any optional thinning of them)
-- enter as the grounded input `ts`; the modeled behavior is purely the
-- construction of the returned threshold vector from `ts`. No `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- A returned threshold value: either a finite score threshold (`finite q`) or
the positive-infinity sentinel (`posInf`) placed at the leading "predict nothing
positive" position. (Faithful refinement of a float threshold, whose only
non-finite value used here is `+∞`.) -/
inductive Thr where
  | posInf
  | finite (q : ℚ)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The returned threshold vector is the positive-infinity sentinel followed by
the decreasing finite score thresholds `ts`, in order. The leading entry is the
sentinel and every later entry equals the corresponding input threshold. -/
def problem_spec_rocCurveThresholds
    (ts : List ℚ) (result : List Thr) : Prop :=
  result = Thr.posInf :: ts.map Thr.finite
-- post-conditions-end

-- impl-start
def implementation_rocCurveThresholds (ts : List ℚ) : List Thr := Id.run do
  let mut out := ts.map Thr.finite
  out := Thr.finite (ts.headD 0 + 1) :: out
  return out
-- impl-end

-- proof-start
theorem correct_rocCurveThresholds :
    ∀ (ts : List ℚ),
      problem_spec_rocCurveThresholds ts
        (implementation_rocCurveThresholds ts) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
