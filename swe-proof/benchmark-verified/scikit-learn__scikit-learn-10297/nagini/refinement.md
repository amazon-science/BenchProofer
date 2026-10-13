# refinement.md — scikit-learn__scikit-learn-10297

The operation-by-operation correspondence between `model.py`'s implementation
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed** / **A-reference**), or
**I** (identical concrete operation). There are **no A steps** in this bundle:
both modelled behaviours are the *changed* code, modelled deeply, so no callee
is axiomatized and none is validated as an A-reference. The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The constructor site — `RidgeClassifierCV.__init__` (`ridge.py:1335`)

Gold hunk (the load-bearing behavioural change):
```
- def __init__(self, alphas=(0.1, 1.0, 10.0), fit_intercept=True,
-              normalize=False, scoring=None, cv=None, class_weight=None):
+ def __init__(self, alphas=(0.1, 1.0, 10.0), fit_intercept=True,
+              normalize=False, scoring=None, cv=None, class_weight=None,
+              store_cv_values=False):
      super(RidgeClassifierCV, self).__init__(
          alphas=alphas, fit_intercept=fit_intercept, normalize=normalize,
-         scoring=scoring, cv=cv)
+         scoring=scoring, cv=cv, store_cv_values=store_cv_values)
      self.class_weight = class_weight
```

| # | model.py impl op (`configure_classifier_cv`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `store_cv_values: bool` | the new `store_cv_values=False` constructor parameter | R | `bool` ↔ the boolean kwarg; default-value handling is irrelevant to the modelled behaviour (the spec is over a supplied value). |
| A2 | `cfg = EngineConfig(store_cv_values)` then `return cfg`; postcondition `Result().retain_values == store_cv_values` | `super().__init__(..., store_cv_values=store_cv_values)`, which runs `_BaseRidgeCV.__init__` setting `self.store_cv_values = store_cv_values` (`ridge.py:1098`) | R + I | building the engine configuration carrying the forwarded flag ↔ the base constructor storing it; `EngineConfig.retain_values` ↔ the engine's `store_cv_values` attribute (mapping.md §2). The forwarded value is the *same object* the caller passed — the identity the postcondition pins. |

`model_prepatch.py` reverts A2 to `EngineConfig(False)` — the pre-patch reality
where the kwarg is absent and the base default `store_cv_values=False` is used
regardless of the caller's request. It **fails** the postcondition
`Result().retain_values == store_cv_values` (it cannot prove `False == True`
when the caller asked for retention) — exactly the spec sensing the change
(G-DIFF).

## B. The retained-shape site — `_RidgeGCV.fit` retention branch, reached through the classifier

Unchanged engine code (`ridge.py:1077-1082`):
```
if self.store_cv_values:
    if len(y.shape) == 1:
        cv_values_shape = n_samples, len(self.alphas)
    else:
        cv_values_shape = n_samples, n_y, len(self.alphas)
    self.cv_values_ = cv_values.reshape(cv_values_shape)
```
reached after the classifier has label-binarized `y` into a 2-D matrix `Y`
(`RidgeClassifierCV.fit`, `ridge.py:1364-1376`, then `_BaseRidgeCV.fit` delegates
to `_RidgeGCV` with that 2-D `Y`). Because `Y` is always 2-D, the engine always
takes the `else` branch ⇒ `cv_values_` is always rank 3 `(n_samples, n_y, n_alphas)`.

| # | model.py impl op (`stored_cv_values`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if cfg.retain_values:` … `else: return None` | `if self.store_cv_values:` … (attribute only set when true) | I | the retention guard is the literal same boolean test on the forwarded flag. |
| B2 | `record = CvRecord(3, n_samples, n_targets, n_alphas)` | `cv_values_shape = n_samples, n_y, len(self.alphas)` (the `else`/2-D-target branch), `self.cv_values_ = cv_values.reshape(cv_values_shape)` | R | `CvRecord.rank/n_samples/n_targets/n_alphas` ↔ `cv_values_.ndim` and the three axes (mapping.md §2). The classifier always reaches the 3-axis branch because `Y` is label-binarized to 2-D; `n_targets` ↔ `n_y = Y.shape[1]` (1 for binary). |

This site is *not changed by the gold patch* — but it is the observable the F2P
test asserts, and it is only **reachable** once A2 forwards the flag. The
prepatch for B (`model_prepatch_2.py`) reverts B2 to the flattened 2-D
`(n_samples, n_alphas)` form (rank 2, the regressor's `len(y.shape)==1` branch,
wrong for a classifier whose targets are always an indicator matrix). It
**fails** the postcondition `Result().rank == 3` — the spec sensing that the
classifier's retained record must carry the always-present target axis (G-DIFF,
second independently-observable behaviour).

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. There is **no opaque callee** the proof depends on:
the changed operation (the constructor forwarding the flag, A2) is modelled
directly as the engine-config field assignment, and the downstream shape (B2)
is modelled directly as the rank-3 record. Consequently:

- the `# axioms-start/end` region is empty — no `@ContractOnly`;
- there is no A-reference deep model of an unchanged callee — G-AX is vacuous;
- `axiom_check.py` is a *reference witness* (it confirms the real post-patch
  estimator exhibits both modelled behaviours), not a soundness obligation the
  proof rests on.

## D. verify(model) ⇒ resolved

`configure_classifier_cv` verifies only if the engine configuration it returns
carries exactly the requested retention flag (A2). By R (`bool` ↔ kwarg,
`EngineConfig.retain_values` ↔ the engine `store_cv_values`) this is the gold
constructor's `super().__init__(..., store_cv_values=store_cv_values)`.
`stored_cv_values` verifies only if, when retention is on, it yields a rank-3
record with axes `(n_samples, n_targets, n_alphas)` (B2) — the shape the F2P
test asserts and the shape the engine produces for the classifier's always-2-D
target matrix. A model satisfying this spec, refined by the map above, is the
gold patch up to type refinement (there are no audited callees), and the gold
patch resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ); there is no axiom-soundness trust point because there are no
axioms.
