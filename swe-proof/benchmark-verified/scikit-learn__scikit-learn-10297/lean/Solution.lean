import Mathlib
-- imports-end

/-!
Building a cross-validated ridge *classifier* estimator's stored configuration
from its constructor options.

A `RidgeClassifierCV` estimator is configured once, at construction time, from a
set list of options:

  * `alphas`        — the sequence of regularization strengths to try;
  * `fitIntercept`  — whether an intercept term is fitted;
  * `normalize`     — whether the regressors are normalized before fitting;
  * `scoring`       — an optional scorer selection (absent ⇒ default scoring);
  * `cv`            — an optional cross-validation splitter selection (absent ⇒
                      the efficient leave-one-out / Generalized Cross-Validation);
  * `classWeight`   — an optional per-class weighting selection;
  * `storeCvValues` — whether the per-alpha cross-validation values are retained
                      (in the `cv_values_` attribute) after fitting; this option
                      is only meaningful together with `cv` absent.

Construction is pure bookkeeping: every supplied option is recorded, verbatim,
into the estimator's stored configuration, so that a later fit honours it. In
particular the retention selection `storeCvValues` offered to the constructor
must be the one actually recorded — it must not be silently dropped or forced to
its default. The desired behaviour is therefore that the stored configuration
reproduces, field for field, exactly the options the constructor was given.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- configuration step (recording each supplied option into the estimator's
-- stored configuration, including the delegation to the shared base
-- initializer) is modeled structurally as field storage, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The stored configuration of a cross-validated ridge classifier estimator,
restricted to the options recorded at construction time. Identity-only options
(`scoring`, `cv`, `classWeight`) are modeled as `Option Nat` (an injective
encoding of the distinct selections; absence ↔ `none`). Regularization strengths
are modeled as `Rat` (only their stored identity is observed at construction). -/
structure ClassifierCVConfig where
  alphas : List Rat
  fitIntercept : Bool
  normalize : Bool
  scoring : Option Nat
  cv : Option Nat
  classWeight : Option Nat
  storeCvValues : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The stored configuration reproduces, field for field, exactly the options the
constructor was given. Every component is pinned to its corresponding input — in
particular the cross-validation-values retention selection `storeCvValues` is
recorded as supplied, never dropped or forced to a default. -/
def problem_spec_initClassifierCV
    (alphas : List Rat) (fitIntercept normalize : Bool)
    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
    (result : ClassifierCVConfig) : Prop :=
  result.alphas = alphas ∧
  result.fitIntercept = fitIntercept ∧
  result.normalize = normalize ∧
  result.scoring = scoring ∧
  result.cv = cv ∧
  result.classWeight = classWeight ∧
  result.storeCvValues = storeCvValues
-- post-conditions-end

-- impl-start
def implementation_initClassifierCV
    (alphas : List Rat) (fitIntercept normalize : Bool)
    (scoring cv classWeight : Option Nat) (storeCvValues : Bool)
    : ClassifierCVConfig := Id.run do
  -- Delegate to the shared base initializer: record the regularization grid,
  -- the intercept/normalize flags, the scorer and splitter selections, and the
  -- cross-validation-values retention selection.
  let mut cfg : ClassifierCVConfig :=
    { alphas := alphas, fitIntercept := fitIntercept, normalize := normalize,
      scoring := scoring, cv := cv, storeCvValues := storeCvValues,
      classWeight := none }
  -- Record the per-class weighting selection on top of the base configuration.
  cfg := { cfg with classWeight := classWeight }
  return cfg
-- impl-end

-- proof-start
theorem correct_initClassifierCV :
    ∀ (alphas : List Rat) (fitIntercept normalize : Bool)
      (scoring cv classWeight : Option Nat) (storeCvValues : Bool),
      problem_spec_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues
        (implementation_initClassifierCV alphas fitIntercept normalize scoring cv classWeight storeCvValues) := by
  intro alphas fitIntercept normalize scoring cv classWeight storeCvValues
  unfold problem_spec_initClassifierCV implementation_initClassifierCV
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
