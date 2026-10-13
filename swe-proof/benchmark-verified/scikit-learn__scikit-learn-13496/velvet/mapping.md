# mapping.md — scikit-learn__scikit-learn-13496

Binds `Solution.lean` symbols to the repo at
`base_commit = 3aefc834dce72e850bff48689bea3c7dff5f3fad`.

Repo file under change: `sklearn/ensemble/iforest.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `configureEnsemble (...)` | `IsolationForest.__init__(self, …)` — `sklearn/ensemble/iforest.py:167` | the modeled changed function: it assembles the keyword configuration passed to `super().__init__(...)` |
| `EnsembleConfig` | the keyword-argument bundle handed to `BaseBagging.__init__` via `super().__init__(...)` — `sklearn/ensemble/iforest.py:177` | the forwarded configuration |
| `cfg.warmStart` | `warm_start=warm_start` keyword in the `super().__init__(...)` call — **added by the patch** at `iforest.py:192` (post-patch) | the newly-forwarded incremental-fit reuse flag |
| `warmStart` (argument) | the `warm_start=False` parameter — **added by the patch** to the `__init__` signature at `iforest.py:179` (post-patch) | the caller-supplied flag |
| `nEstimators` / `cfg.nEstimators` | `n_estimators` param ↔ `n_estimators=n_estimators` keyword | already-forwarded entry (frame) |
| `maxSamples` / `cfg.maxSamples` | `max_samples` param ↔ `max_samples=max_samples` keyword | already-forwarded entry (frame) |
| `maxFeatures` / `cfg.maxFeatures` | `max_features` param ↔ `max_features=max_features` keyword | already-forwarded entry (frame) |
| `bootstrap` / `cfg.bootstrap` | `bootstrap` param ↔ `bootstrap=bootstrap` keyword | already-forwarded entry (frame) |
| `nJobs` / `cfg.nJobs` | `n_jobs` param ↔ `n_jobs=n_jobs` keyword | already-forwarded entry (frame) |
| `randomState` / `cfg.randomState` | `random_state` param ↔ `random_state=random_state` keyword | already-forwarded entry (frame) |
| `verbose` / `cfg.verbose` | `verbose` param ↔ `verbose=verbose` keyword | already-forwarded entry (frame) |

The behavior the patch enables — a warm refit REUSES the previous fit and APPENDS
new estimators (rather than rebuilding from scratch) — lives entirely in the
**unchanged** parent `BaseBagging._fit` (`sklearn/ensemble/bagging.py:246`, the
`if not self.warm_start or not hasattr(self, 'estimators_'): self.estimators_=[]`
/ `n_more_estimators = self.n_estimators - len(self.estimators_)` logic). That
algorithm is NOT modeled (directive 3 / SPEC_GUIDE §0.7: never re-model unchanged
library code as "the fix"). The patch is config plumbing: it exposes `warm_start`
and forwards it. The spec therefore pins the forwarding, and the prepatch (which
forwards the base default, ignoring the caller) fails on `cfg.warmStart =
warmStart`.

No callee is axiomatized: the constructor assembles its forwarded configuration
purely from its own arguments. There is therefore no `axiom_check.py` (G-AX
skip).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `warm_start : bool` (and `bootstrap : bool`) | `Bool` | `True ↔ true`, `False ↔ false`; exact |
| `n_estimators : int` | `Param` (= `Int`) handle | one distinct handle per distinct argument object; only IDENTITY (equality of forwarded value to supplied value) is observed |
| `max_samples : int \| float \| "auto"` | `Param` handle | the union value is opaque; the constructor forwards it untouched, so only identity matters |
| `max_features : int \| float` | `Param` handle | forwarded untouched; identity only |
| `n_jobs : int \| None` | `Param` handle | forwarded untouched; identity only |
| `random_state : int \| RandomState \| None` | `Param` handle | forwarded untouched; identity only |
| `verbose : int` | `Param` handle | forwarded untouched; identity only |
| the keyword bundle to `super().__init__` | `EnsembleConfig` structure | one field per forwarded entry; field value ↔ the keyword's value |

`Param` is `Int` purely as an injective handle for "the argument object as
forwarded": the constructor performs NO arithmetic or inspection on these
entries, it only passes them through, so identity is the entire observable.
`behaviour` and `contamination` (set as plain attributes, not forwarded to
`super().__init__`) are NOT in the forwarded bundle and so are out of the modeled
configuration; the patch does not touch them.

## 3. Callee provenance

None (no axioms, no deep-model references). The whole modeled behavior is the
constructor copying each of its arguments into the forwarded configuration.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **13496**. The R/I shadow is the forwarded
configuration assembled in Python from the constructor arguments; the oracle is
the patched `IsolationForest.__init__`'s observable effect — that
`IsolationForest(warm_start=v, …).warm_start == v` (and the other forwarded
entries land on the corresponding attributes / parent state), exercised by
constructing real estimators over fuzzed flag/argument combinations and reading
back the forwarded configuration. The discriminator is `warm_start`: pre-patch,
`IsolationForest(warm_start=True)` raises `TypeError` (the parameter does not
exist); post-patch it is accepted and forwarded.
