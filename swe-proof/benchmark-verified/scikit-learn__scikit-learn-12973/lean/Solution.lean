import Mathlib
-- imports-end

/-!
A linear-model estimator carries a configured boolean that decides whether the
input feature matrix is duplicated before the data-preparation step runs, or may
instead be reused in place. The fitting routine also accepts a per-call boolean of
the same meaning, so a caller can state the choice at fit time without rebuilding
the estimator.

The behavior modeled here is the contract between these two settings and the
single boolean actually delivered to the data-preparation step (the flag that
governs whether the feature matrix is duplicated). The per-call setting is
optional: when the caller supplies an explicit value it takes precedence; when the
caller supplies nothing, the estimator's configured value is used. Either way the
delivered flag is one definite boolean, and it is exactly the value the data-
preparation step receives.

We model the estimator by the only field that participates in this contract — its
configured duplicate-input boolean — together with the optional per-call boolean,
and the modeled result is the boolean delivered to the data-preparation step. A
faithful routine delivers the per-call value whenever one is supplied, and the
configured value otherwise.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The data-
-- preparation step and the path solver are not modeled; only the single boolean
-- delivered to the data-preparation step is, and that boolean is pure data threaded
-- through the routine. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The optional per-call duplicate-input boolean. `none` is the absent per-call
choice (the caller supplied nothing); `some b` is an explicit caller choice `b`. -/
abbrev CallChoice := Option Bool

/-- Resolve the duplicate-input boolean delivered to the data-preparation step:
the explicit per-call choice when one is present, otherwise the estimator's
configured value. -/
def resolveCopy (configured : Bool) (call : CallChoice) : Bool := call.getD configured
-- pure-end

-- post-conditions-start
/-- The boolean delivered to the data-preparation step equals the per-call choice
when the caller supplies one, and the estimator's configured value otherwise. This
fully pins the modeled result to the inputs: no configuration leaves the delivered
boolean free, and in particular an explicit per-call choice that differs from the
configured value must still be the one delivered. -/
def problem_spec_deliveredCopy (configured : Bool) (call : CallChoice) (result : Bool) : Prop :=
  result = call.getD configured
-- post-conditions-end

-- impl-start
def implementation_deliveredCopy (configured : Bool) (call : CallChoice) : Bool := Id.run do
  let mut copyX : CallChoice := call
  if copyX = none then
    copyX := some configured
  return copyX.getD configured
-- impl-end

-- proof-start
theorem correct_deliveredCopy :
    ∀ (configured : Bool) (call : CallChoice),
      problem_spec_deliveredCopy configured call
        (implementation_deliveredCopy configured call) := by
  intro configured call
  unfold problem_spec_deliveredCopy implementation_deliveredCopy
  cases call with
  | none => rfl
  | some b => rfl
-- proof-end
