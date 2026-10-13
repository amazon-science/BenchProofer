import Mathlib
-- imports-end

/-!
Recording how long the final refit of the best model takes.

A hyper-parameter search procedure, after selecting the best parameter setting,
optionally refits a single best model on the whole dataset. Callers want to know
how long that final refit took (so they can report the cost of the search
separately from the cost of refitting). The procedure reads a wall-clock value
immediately before the final refit begins and again immediately after it
finishes, and exposes the elapsed duration as an observable.

This observable is produced ONLY when the final refit is performed. When refit is
disabled no final model is fit, so there is no duration to report and the
observable is absent.

We model the produced observable directly:

  * `refitEnabled` — whether the final refit is performed;
  * `startClock`   — the wall-clock value read immediately before the refit;
  * `endClock`     — the wall-clock value read immediately after the refit;
  * `result`       — the reported refit duration: `some (endClock - startClock)`
                     when the refit is performed, and `none` (no observable) when
                     it is not.

The reported duration is exactly `endClock - startClock` — the identical
subtraction the procedure performs — for EVERY pair of readings, with no side
condition relating them. (On a real, monotonically advancing wall clock
`startClock ≤ endClock`, so the reported duration is never negative in
practice; the recording itself does not depend on that.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two
-- wall-clock readings that bracket the refit are environment-provided values,
-- modeled directly as the rational inputs `startClock` / `endClock`; the
-- selection and fitting of the best model are unchanged operations whose only
-- modeled effect is that they occur between the two readings (the elapsed time).
-- No `opaque`/`axiom` callee contract is therefore needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The reported refit duration is the elapsed wall-clock between the reading
taken immediately before the refit and the reading taken immediately after it,
exposed exactly when the refit is performed, and absent otherwise. -/
def problem_spec_refitTiming
    (refitEnabled : Bool) (startClock endClock : ℚ) (result : Option ℚ) : Prop :=
  result = (if refitEnabled then some (endClock - startClock) else none)
-- post-conditions-end

-- impl-start
def implementation_refitTiming
    (refitEnabled : Bool) (startClock endClock : ℚ) : Option ℚ := Id.run do
  let mut refitDuration : Option ℚ := none
  if refitEnabled then
    let s := startClock
    -- (the best model is refit on the whole dataset between the two readings)
    let e := endClock
    refitDuration := some (e - s)
  return refitDuration
-- impl-end

-- proof-start
theorem correct_refitTiming :
    ∀ (refitEnabled : Bool) (startClock endClock : ℚ),
      problem_spec_refitTiming refitEnabled startClock endClock
        (implementation_refitTiming refitEnabled startClock endClock) := by
  intro refitEnabled startClock endClock
  unfold problem_spec_refitTiming implementation_refitTiming
  cases refitEnabled <;> rfl
-- proof-end
