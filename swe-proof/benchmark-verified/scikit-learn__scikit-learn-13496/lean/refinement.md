# refinement.md — operation correspondence (scikit-learn__scikit-learn-13496)

Maps every operation in `implementation_isolationForestInit` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof consumes an
axiom), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

The gold patch does three things: (1) documents `warm_start` in the class
docstring, (2) adds `warm_start=False` as a constructor parameter, (3) forwards
`warm_start=warm_start` into the `super().__init__(...)` call. (1) is pure
documentation with no runtime effect (not modeled). (2)+(3) are the behavioral
change: the flag becomes a stored configuration attribute holding the supplied
value. The parent `BaseBagging.__init__` then performs `self.warm_start =
warm_start` (an identity store), alongside the analogous identity stores for the
other forwarded parameters.

| # | impl op (Solution.lean) | patch.diff / repo counterpart | tag |
|---|---|---|---|
| 1 | `cfg.warmStart := warmStart` | `super().__init__(…, warm_start=warm_start, …)` → `self.warm_start = warm_start` (the fix) | I |
| 2 | `cfg.bootstrap := bootstrap` | `super().__init__(bootstrap=bootstrap, …)` → `self.bootstrap = bootstrap` | I |
| 3 | `cfg.bootstrapFeatures := false` | `super().__init__(bootstrap_features=False, …)` → `self.bootstrap_features = False` (hardcoded constant) | I |
| 4 | `cfg.oobScore := false` | parent default `oob_score=False`, never overridden by subclass → `self.oob_score = False` | I |
| 5 | `cfg.nEstimators := nEstimators` | `super().__init__(n_estimators=n_estimators, …)` → `self.n_estimators` (via BaseEnsemble) | R (Python `int` ↔ `Nat`) |
| 6 | `cfg.verbose := verbose` | `super().__init__(verbose=verbose, …)` → `self.verbose = verbose` | R (Python `int` ↔ `Nat`) |
| 7 | `cfg.behaviour := behaviour` | `self.behaviour = behaviour` (subclass assignment) | I (Python `str` ↔ `String`) |
| 8 | `cfg.maxSamples := maxSamples` | `super().__init__(max_samples=max_samples, …)` → `self.max_samples` | R (opaque value, identity store) |
| 9 | `cfg.contamination := contamination` | `self.contamination = contamination` (subclass assignment) | R (opaque value, identity store) |
| 10 | `cfg.maxFeatures := maxFeatures` | `super().__init__(max_features=max_features, …)` → `self.max_features` | R (opaque value, identity store) |
| 11 | `cfg.nJobs := nJobs` | `super().__init__(n_jobs=n_jobs, …)` → `self.n_jobs = n_jobs` | R (opaque value, identity store) |
| 12 | `cfg.randomState := randomState` | `super().__init__(random_state=random_state, …)` → `self.random_state` | R (opaque value, identity store) |

No op is A-consumed and none is A-reference: the constructor invokes no
unchanged callee whose internal behavior the proof must reason about — the parent
constructor's per-attribute work is itself a sequence of identity stores, modeled
field-for-field. Hence the axioms region is empty and `axiom_check.py` is a skip
stub.

The R legs are mechanically differential-tested by G-CONF against the real
post-patch `IsolationForest(**kwargs)` stored attributes. No changed op is
inexpressible.
