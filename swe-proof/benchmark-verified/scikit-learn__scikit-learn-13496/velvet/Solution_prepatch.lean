import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constructor under spec only assembles the
--  configuration it forwards to the base ensemble machinery out of its own
--  arguments; it consults no callee whose contract the proof depends on. The
--  downstream incremental-vs-fresh fitting that consumes this configuration is
--  unchanged library behavior and is not re-modeled here.)
-- axioms-end

-- pure-start
/- A single forwarded constructor argument, modeled as an opaque handle: the
   constructor passes it through to the base ensemble configuration verbatim, so
   the only property that matters is that its IDENTITY is preserved. The concrete
   Python value it stands for may be an int, a float, the string "auto", `None`,
   or a random-state object; the bijection (mapping.md §2) maps each such value
   to a distinct handle and forwarding to handle equality. -/
abbrev Param := Int

/- The configuration an ensemble estimator's constructor assembles and hands to
   its base ensemble machinery, abstracted to the entries the constructor
   forwards from its own arguments:

   * `nEstimators`  — how many base estimators the ensemble targets;
   * `maxSamples`   — the per-estimator sample budget;
   * `maxFeatures`  — the per-estimator feature budget;
   * `bootstrap`    — whether per-estimator subsets are drawn with replacement;
   * `warmStart`    — the incremental-fit reuse flag: when on, a subsequent fit
                      reuses the previous fit and adds more estimators rather
                      than building a fresh ensemble;
   * `nJobs`        — the parallelism handle;
   * `randomState`  — the randomness handle;
   * `verbose`      — the verbosity handle. -/
structure EnsembleConfig where
  nEstimators : Param
  maxSamples : Param
  maxFeatures : Param
  bootstrap : Bool
  warmStart : Bool
  nJobs : Param
  randomState : Param
  verbose : Param
deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the configuration an ensemble estimator's constructor forwards to its
   base ensemble machinery.

   Desired behavior: every entry the constructor carries is forwarded EXACTLY as
   supplied by the caller. In particular the incremental-fit reuse flag is one of
   the forwarded entries: the caller's choice of that flag (default off) is
   propagated into the configuration verbatim, so that downstream fitting reuses
   the previous fit and adds more estimators when it is on, and builds a fresh
   ensemble when it is off. Exposing this flag must NOT disturb any of the entries
   already forwarded: the targeted estimator count, the sample and feature
   budgets, the replacement flag, and the parallelism / randomness / verbosity
   handles each continue to equal the corresponding argument.

   All arguments are read-only (none is `mut`): the constructor reads each
   argument and assembles a configuration, mutating no input (directive 5). Each
   forwarded argument is modeled as an opaque handle (`Param`) whose identity the
   forwarding preserves; the two genuine booleans are carried as `Bool`
   (mapping.md §2). -/
method configureEnsemble
    (nEstimators : Param) (maxSamples : Param) (maxFeatures : Param)
    (bootstrap : Bool) (nJobs : Param) (randomState : Param) (verbose : Param)
    (warmStart : Bool)
    return (cfg : EnsembleConfig)
  ensures cfg.nEstimators = nEstimators
  ensures cfg.maxSamples = maxSamples
  ensures cfg.maxFeatures = maxFeatures
  ensures cfg.bootstrap = bootstrap
  ensures cfg.nJobs = nJobs
  ensures cfg.randomState = randomState
  ensures cfg.verbose = verbose
  ensures cfg.warmStart = warmStart
  do
    -- impl-start
    -- Pre-image skeleton: the incremental-fit reuse flag is NOT among the entries
    -- the constructor forwards; the configuration always receives the base
    -- machinery's default (reuse OFF), ignoring the caller's argument. This MUST
    -- fail the spec whenever the caller requests the flag ON.
    return { nEstimators := nEstimators, maxSamples := maxSamples,
             maxFeatures := maxFeatures, bootstrap := bootstrap,
             warmStart := false, nJobs := nJobs,
             randomState := randomState, verbose := verbose }
    -- impl-end

prove_correct configureEnsemble by
  loom_solve
