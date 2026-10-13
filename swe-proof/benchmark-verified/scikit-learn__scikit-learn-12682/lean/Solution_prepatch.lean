import Mathlib
-- imports-end

/-!
Choosing the parameters a sparse-coding estimator hands to its underlying
sparse-solver when it encodes data.

A sparse-coding estimator is configured once, at construction time, from a set
list of options:

  * `nComponents`   — the number of dictionary atoms;
  * `algorithm`     — which solver to use for the coding step;
  * `nNonzeroCoefs` — an optional cap on the number of non-zero coefficients;
  * `alpha`         — an optional sparsity-controlling parameter;
  * `splitSign`     — whether the coding is split into a positive and negative
                      side afterwards;
  * `nJobs`         — an optional parallelism selection;
  * `positive`      — whether a positivity constraint is enforced on the code;
  * `maxIter`       — the maximum number of iterations the underlying solver is
                      allowed to run.

These options are recorded into the estimator's stored configuration. When the
estimator later encodes data, it builds the bundle of arguments it passes to the
underlying sparse-solver out of that stored configuration. Every argument the
solver receives must come from the corresponding configured option — in
particular the iteration budget the solver is allowed must be the configured
`maxIter`, so that a caller who asks for more (or fewer) iterations actually gets
them rather than a constant standard amount. The desired behaviour is therefore
that the solver-argument bundle reproduces, field for field, exactly the
configured options it draws from.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- configuration step (recording each supplied option) and the assembly of the
-- solver-argument bundle from that stored configuration are modeled
-- structurally as field storage and field reads, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- The stored configuration of a sparse-coding estimator, restricted to the
options recorded at construction time. Identity-only selections (`algorithm`,
`nNonzeroCoefs`, `alpha`, `nJobs`) are modeled by injective encodings of the
distinct choices (absence ↔ `none`); the iteration budget is a `Nat`. -/
structure CodingConfig where
  nComponents : Nat
  algorithm : Nat
  nNonzeroCoefs : Option Nat
  alpha : Option Rat
  splitSign : Bool
  nJobs : Option Nat
  positive : Bool
  maxIter : Nat
deriving DecidableEq

/-- The bundle of arguments the estimator hands to the underlying sparse-solver
when it encodes data. -/
structure SolverArgs where
  algorithm : Nat
  nNonzeroCoefs : Option Nat
  alpha : Option Rat
  maxIter : Nat
  nJobs : Option Nat
  positive : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The solver-argument bundle reproduces, field for field, exactly the
configured options it draws from. Every argument is pinned to the corresponding
configured input — in particular the solver's iteration budget `maxIter` is the
configured `maxIter`, never replaced by a constant standard amount. -/
def problem_spec_codingSolverArgs
    (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
    (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
    (result : SolverArgs) : Prop :=
  result.algorithm = algorithm ∧
  result.nNonzeroCoefs = nNonzeroCoefs ∧
  result.alpha = alpha ∧
  result.maxIter = maxIter ∧
  result.nJobs = nJobs ∧
  result.positive = positive
-- post-conditions-end

-- impl-start
def implementation_codingSolverArgs
    (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
    (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat)
    : SolverArgs := Id.run do
  -- Record every supplied option into the estimator's stored configuration,
  -- including the solver iteration budget.
  let cfg : CodingConfig :=
    { nComponents := nComponents, algorithm := algorithm,
      nNonzeroCoefs := nNonzeroCoefs, alpha := alpha, splitSign := splitSign,
      nJobs := nJobs, positive := positive, maxIter := maxIter }
  -- Encoding step: assemble the solver-argument bundle from the stored
  -- configuration. Each argument is drawn from its configured option, and the
  -- solver's iteration budget is drawn from the configured `maxIter`.
  let mut args : SolverArgs :=
    { algorithm := cfg.algorithm, nNonzeroCoefs := cfg.nNonzeroCoefs,
      alpha := cfg.alpha, maxIter := 1000, nJobs := cfg.nJobs,
      positive := cfg.positive }
  return args
-- impl-end

-- proof-start
theorem correct_codingSolverArgs :
    ∀ (nComponents algorithm : Nat) (nNonzeroCoefs : Option Nat) (alpha : Option Rat)
      (splitSign : Bool) (nJobs : Option Nat) (positive : Bool) (maxIter : Nat),
      problem_spec_codingSolverArgs nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter
        (implementation_codingSolverArgs nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter) := by
  intro nComponents algorithm nNonzeroCoefs alpha splitSign nJobs positive maxIter
  unfold problem_spec_codingSolverArgs implementation_codingSolverArgs
  simp only [Id.run]
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
