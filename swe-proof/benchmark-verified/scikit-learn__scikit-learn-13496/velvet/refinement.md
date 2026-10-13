# refinement.md — scikit-learn__scikit-learn-13496

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`configureEnsemble` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** /
**A-reference**), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
narrative is audited by **G-EQ**. Claim: any impl verifying against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed function — `IsolationForest.__init__` (`sklearn/ensemble/iforest.py:167`)

The gold patch is pure configuration plumbing across three hunks:

1. a docstring entry documenting `warm_start` (no behavior);
2. the signature gains `warm_start=False`;
3. the `super().__init__(...)` call gains `warm_start=warm_start`.

```
@@ def __init__(self, …
-                 verbose=0):
+                 verbose=0,
+                 warm_start=False):
         super().__init__(
             …
             max_features=max_features,
+            warm_start=warm_start,
             n_jobs=n_jobs, …)
```

The constructor's only behavior is to forward each argument into the keyword
bundle handed to `super().__init__`. The patch ADDS `warm_start` to both the
accepted arguments and the forwarded bundle.

| # | Solution.lean impl op (`configureEnsemble`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `return { …, warmStart := warmStart, … }` (the `warmStart` field) | `warm_start=warm_start` keyword added to `super().__init__(...)` | R | the changed op: the caller's flag is forwarded verbatim. `bool ↔ Bool` (R, mapping.md §2). This is the field that discriminates the fix (G-DIFF). |
| A2 | `nEstimators := nEstimators` | `n_estimators=n_estimators` | R + I | already-forwarded entry; `int` handle ↔ `Param`, forwarded untouched. Frame: unchanged by the patch, must still equal its argument (directive 5). |
| A3 | `maxSamples := maxSamples` | `max_samples=max_samples` | R + I | already-forwarded; identity-only handle. Frame. |
| A4 | `maxFeatures := maxFeatures` | `max_features=max_features` | R + I | already-forwarded; identity-only handle. Frame. |
| A5 | `bootstrap := bootstrap` | `bootstrap=bootstrap` | R + I | already-forwarded; `bool ↔ Bool`. Frame. |
| A6 | `nJobs := nJobs` | `n_jobs=n_jobs` | R + I | already-forwarded; identity-only handle. Frame. |
| A7 | `randomState := randomState` | `random_state=random_state` | R + I | already-forwarded; identity-only handle. Frame. |
| A8 | `verbose := verbose` | `verbose=verbose` | R + I | already-forwarded; identity-only handle. Frame. |

The docstring hunk has no behavioral op and so no refinement row.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — adding
`warm_start` to the forwarded configuration — is modeled **directly** as the
`warmStart` field of the returned `EnsembleConfig` (a concrete struct field, tag
R), not hidden behind an axiom. There is **no A-consumed axiom and no
A-reference** in this bundle.

Critically, the incremental-fit ALGORITHM the flag controls (warm refit reuses
the previous fit and appends new estimators; cold refit rebuilds) lives in the
**unchanged** parent `BaseBagging._fit` and is deliberately NOT modeled
(SPEC_GUIDE §0.3 skeleton-faithfulness, §0.7 never re-model unchanged library
code as the fix). The patch does not touch that algorithm; it only plumbs the
flag through. Modeling the algorithm would be unfaithful to the actual diff.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The real `IsolationForest.__init__` is a straight-line
constructor that always terminates and returns the assembled keyword bundle,
and the F2P test observes the constructed estimator, so total correctness is
the faithful semantics. Partial correctness would admit a same-spec
implementation that diverges (an infinite loop vacuously satisfies every
`ensures`) — a wrong impl the tests would fail — so it would leave the spec
too weak.

## C. verify(Solution) ⇒ resolved

`configureEnsemble` verifies only if the forwarded configuration equals the
caller's arguments field-by-field — in particular `cfg.warmStart = warmStart`,
the flag the patch newly forwards. By R (`bool ↔ Bool`; each opaque argument
forwarded by identity) the verified constructor produces exactly the keyword
bundle the gold `super().__init__(...)` call produces. By G-CONF the R/I shadow
(the forwarded configuration assembled in Python) agrees with the patched
`IsolationForest.__init__`'s observable forwarding on ≥10⁵ fuzzed inputs.

The frame discipline (A2–A8 each `ensures cfg.x = x`) guarantees exposing the new
flag does not silently disturb an already-forwarded entry — the directive-5
analogue of pinning the unchanged frame.

`Solution_prepatch.lean` reproduces the pre-patch reality: the flag is NOT
forwarded, so the configuration receives the base machinery's default (reuse
OFF), modeled as `warmStart := false`. It **fails** `cfg.warmStart = warmStart`
(G-DIFF) at exactly the `warmStart = true` case — which is precisely what the
F2P test `test_iforest_warm_start` exercises: it constructs
`IsolationForest(warm_start=True)`, fits, increments `n_estimators`, refits, and
asserts the prior trees are preserved (`clf.estimators_[0] is tree_1`) and the
forest grows to 20. With the flag not forwarded (pre-patch raises `TypeError` at
construction; conceptually the configuration carries reuse OFF), that behavior is
unreachable. The downstream reuse is the unchanged parent's job once the flag
arrives; the bug the patch fixes is purely that the flag never arrived.
