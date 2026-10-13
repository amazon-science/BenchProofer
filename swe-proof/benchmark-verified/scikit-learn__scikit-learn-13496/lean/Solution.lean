import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the constructor only forwards
-- and stores its arguments (each parent assignment is an identity store), so the
-- behavior is modeled DIRECTLY as record-field assignment rather than
-- axiomatized. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The settable configuration an outlier-ensemble estimator stores at
construction time. The five value-carrying parameters that the constructor only
passes through (never inspecting them) are modeled as type variables, since the
constructor stores them by identity. -/
structure EnsembleConfig (Sample Contam Feat Jobs Rand : Type) where
  nEstimators : Nat
  maxSamples : Sample
  contamination : Contam
  maxFeatures : Feat
  bootstrap : Bool
  bootstrapFeatures : Bool
  oobScore : Bool
  warmStart : Bool
  nJobs : Jobs
  behaviour : String
  randomState : Rand
  verbose : Nat
-- pure-end

-- post-conditions-start
/-- The constructed configuration stores every supplied parameter by identity:
the incremental-refit flag is held exactly as the caller supplied it, the
sample-replacement flag and the verbosity / tree-count / strategy / state values
are stored unchanged, and the two configuration flags that this estimator never
exposes are held at their default values (feature subsampling off, out-of-bag
scoring off). Every output component is pinned to its input — no field is left
free. -/
def problem_spec_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool)
    (result : EnsembleConfig Sample Contam Feat Jobs Rand) : Prop :=
  result.warmStart = warmStart ∧
  result.bootstrap = bootstrap ∧
  result.bootstrapFeatures = false ∧
  result.oobScore = false ∧
  result.nEstimators = nEstimators ∧
  result.maxSamples = maxSamples ∧
  result.contamination = contamination ∧
  result.maxFeatures = maxFeatures ∧
  result.nJobs = nJobs ∧
  result.behaviour = behaviour ∧
  result.randomState = randomState ∧
  result.verbose = verbose
-- post-conditions-end

-- impl-start
def implementation_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool) :
    EnsembleConfig Sample Contam Feat Jobs Rand := Id.run do
  -- forward the bagging parameters to the parent constructor, exposing the
  -- incremental-refit flag so it is stored as supplied
  let mut cfg : EnsembleConfig Sample Contam Feat Jobs Rand := {
    nEstimators := nEstimators,
    maxSamples := maxSamples,
    contamination := contamination,
    maxFeatures := maxFeatures,
    bootstrap := bootstrap,
    bootstrapFeatures := false,
    oobScore := false,
    warmStart := warmStart,
    nJobs := nJobs,
    behaviour := behaviour,
    randomState := randomState,
    verbose := verbose }
  return cfg
-- impl-end

-- proof-start
theorem correct_isolationForestInit
    {Sample Contam Feat Jobs Rand : Type}
    (nEstimators : Nat) (maxSamples : Sample) (contamination : Contam)
    (maxFeatures : Feat) (bootstrap : Bool) (nJobs : Jobs) (behaviour : String)
    (randomState : Rand) (verbose : Nat) (warmStart : Bool) :
    problem_spec_isolationForestInit nEstimators maxSamples contamination
      maxFeatures bootstrap nJobs behaviour randomState verbose warmStart
      (implementation_isolationForestInit nEstimators maxSamples contamination
        maxFeatures bootstrap nJobs behaviour randomState verbose warmStart) := by
  unfold problem_spec_isolationForestInit implementation_isolationForestInit
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
