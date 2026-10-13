# mapping.md — scikit-learn__scikit-learn-14629

## Symbol binding (base_commit 4aded39b5663d943f6a4809abacfa9cae3d7fb6a)

- Modeled function: `MultiOutputClassifier.fit` — **added** by the gold patch at
  `sklearn/multioutput.py:328` (post-patch). At base_commit no `fit` override
  exists on `MultiOutputClassifier` (`sklearn/multioutput.py:319` class body jumps
  straight from `__init__` to `predict_proba`), so `fit` is inherited from
  `MultiOutputEstimator.fit` (`sklearn/multioutput.py:124`).
- Behavior modeled: the post-`super().fit()` body
  `self.classes_ = [estimator.classes_ for estimator in self.estimators_]`
  (`sklearn/multioutput.py:347` post-patch) and its observable effect — the
  `classes_` attribute becomes a defined, queryable per-target view.
- Callee `super().fit(X, Y, sample_weight)` = `MultiOutputEstimator.fit`
  (`sklearn/multioutput.py:124`). It sets `self.estimators_` to the ordered list
  of fitted per-target sub-models (`multioutput.py:167-170`). This is an
  UNCHANGED callee; its result (the fitted sub-model list) enters the model as
  the input carrier `subModels`. Each sub-model `estimator.classes_` is a
  per-target attribute set by the underlying classifier's own `fit`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| `self.estimators_` : list of fitted sub-models | `subModels : List SubModel` |
| `estimator.classes_` : 1-D array of distinct class labels | `SubModel.classLabels : List Int` (label values modeled as `Int`) |
| `self.classes_` after fit : list of per-target label arrays | `Option (List (List Int))` — `some` = attribute defined, `none` = absent (AttributeError) |
| `[estimator.classes_ for estimator in self.estimators_]` | `subModels.map (·.classLabels)` |
| pre-patch: `self.classes_` undefined → `AttributeError` | `none` |

`classes_` label values are modeled as `Int` (a class label is an opaque,
order-irrelevant identifier; `Int` is a faithful, decidable stand-in — the spec
only collects them, never inspects their values).

## Callee provenance + flag deps

- `super().fit` (`MultiOutputEstimator.fit`): UNCHANGED, result enters as data
  (`subModels`). NOT axiomatized (its output is the input carrier). No flag
  dependency affects the modeled collection.
- `sample_weight` parameter: forwarded to `super().fit`; does not affect the
  per-target class-label collection. Not modeled (only `super().fit`'s
  `estimators_` result matters).
- No A-consumed axiom and no A-reference: the collection
  `[e.classes_ for e in estimators_]` is modeled deeply as `List.map`.

## G-CONF fuzz seed

Pinned seed: `14629`. Fuzz domain: lists of 0..16 sub-models, each carrying a
0..12-length list of `Int` class labels (values in [-100,100], duplicates and
empties allowed). ≥1e5 cases.
