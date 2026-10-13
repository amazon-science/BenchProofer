import Mathlib
-- imports-end

/-!
Returning a log-capture threshold to its prior value at the end of a test.

A log-capture facility keeps a numeric *threshold* level: the minimum severity of
records it retains. A fresh facility starts at some initial threshold. During a
single test the threshold may be raised any number of times, each raise naming a
new level. Independently of how the named loggers are managed, the facility must
itself remember enough to undo its own threshold changes when the test ends.

The rule for the end of a test is:

* if the threshold was never raised during the test, it is left exactly as it was
  created;
* otherwise it is returned to the value it held immediately *before* the most
  recent raise — i.e. the threshold in effect just prior to the last change, not
  the last value it was raised to.

The observable modeled here is the capture threshold in effect after the test has
ended. Pinning it this way guarantees that a test which raises the threshold does
not leave that raised threshold in place afterwards: the facility is rolled back
to the threshold that preceded its last raise (and, when a test raises the
threshold exactly once from its created value, all the way back to that created
value), rather than being left at the level the test most recently asked for.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The threshold
-- lifecycle — recording, on each raise, the threshold in effect just before it,
-- and re-applying the last such record when the test ends — is modeled DEEPLY
-- over the observable inputs (the initial threshold and the ordered sequence of
-- raised levels), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Fold one test's sequence of threshold raises into the facility's end-of-test
state, a pair `(currentThreshold, recordedThreshold)`. Each raise records the
threshold currently in effect (`some current`) and then moves the current
threshold to the newly named level. Starting from `(initialLevel, none)`, after
all raises `recordedThreshold` is `none` exactly when no raise happened. -/
def captureLevelState (initialLevel : Int) (levels : List Int) : Int × Option Int :=
  levels.foldl (fun st lvl => (lvl, some st.1)) (initialLevel, none)

/-- The capture threshold in effect after the test ends: the recorded threshold
if any raise happened (the value held just before the last raise), otherwise the
threshold the facility was created with. -/
def restoredCaptureLevel (initialLevel : Int) (levels : List Int) : Int :=
  match (captureLevelState initialLevel levels).2 with
  | some s => s
  | none   => (captureLevelState initialLevel levels).1
-- pure-end

-- post-conditions-start
/-- After the test ends the capture threshold equals the value dictated by the
end-of-test rule: the threshold held just before the most recent raise, or the
created threshold when no raise occurred. -/
def problem_spec_captureLevel
    (initialLevel : Int) (levels : List Int) (result : Int) : Prop :=
  result = restoredCaptureLevel initialLevel levels
-- post-conditions-end

-- impl-start
def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do
  -- Pre-patch behavior: the facility raises its threshold on every change but
  -- keeps no record of the threshold in effect beforehand, so the end-of-test
  -- step has nothing to re-apply and the threshold is left at the LAST level it
  -- was raised to (the created threshold only when no raise happened).
  let mut handler := initialLevel
  for lvl in levels do
    handler := lvl
  return handler
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). It does NOT
-- close against this impl: when the threshold was raised, the spec demands the
-- value held just before the LAST raise, while this impl returns the last raised
-- value itself — so the discriminating clause (any test with ≥1 raise whose final
-- pre-raise threshold differs from the last raised level) is unprovable.
theorem correct_captureLevel :
    ∀ (initialLevel : Int) (levels : List Int),
      problem_spec_captureLevel initialLevel levels
        (implementation_captureLevel initialLevel levels) := by
  intro initialLevel levels
  unfold problem_spec_captureLevel implementation_captureLevel restoredCaptureLevel captureLevelState
  have h : ∀ (init : Int × Option Int),
      (forIn levels init (fun lvl r =>
        (pure (ForInStep.yield (lvl, some r.1)) : Id (ForInStep (Int × Option Int)))))
      = levels.foldl (fun st lvl => (lvl, some st.1)) init := by
    induction levels with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons, List.foldl_cons]
      exact ih (a, some init.1)
  show (Id.run (do let r ← forIn levels (initialLevel, none) (fun lvl r =>
        (pure (ForInStep.yield (lvl, some r.1)) : Id (ForInStep (Int × Option Int)))); pure _) : Int) = _
  rw [h]
  rfl
-- proof-end
