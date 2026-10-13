# mapping.md — scikit-learn__scikit-learn-14629

Symbol binding, the Lean↔Python type bijection (used by G-CONF and G-AX), callee
provenance + flag dependencies, and the pinned G-CONF fuzz seed.

Cold provenance: spec derived only from `problem_statement`, the gold `patch`,
and the repo source at `base_commit`
(`4aded39b5663d943f6a4809abacfa9cae3d7fb6a`).

## 1. The change

Gold patch, `sklearn/multioutput.py`:

```
class MultiOutputClassifier(MultiOutputEstimator, ClassifierMixin):
    def __init__(self, estimator, n_jobs=None):
        super().__init__(estimator, n_jobs)

+   def fit(self, X, Y, sample_weight=None):
+       ...docstring...
+       super().fit(X, Y, sample_weight)
+       self.classes_ = [estimator.classes_ for estimator in self.estimators_]
+       return self
```

The fitted multi-target classifier previously exposed no per-target
class-label collection (the meta-estimator inherited the parent fit, which sets
only the per-target sub-model list). The fix overrides fit so that, after the
parent fit has produced the per-target sub-model list, it records one
class-label collection per sub-model, in sub-model order.

The F2P observation (`test_multi_output_classes_[estimator1]`):
```python
estimator.fit(X, y)
assert isinstance(estimator.classes_, list)
assert len(estimator.classes_) == n_outputs
for got, exp in zip(classes, estimator.classes_):
    assert_array_equal(got, exp)
```
i.e. the recorded collection is a list, has one entry per target, and the
i-th entry equals the i-th sub-model's class-label array.

### Second gold hunk — NOT modeled (cosmetic)

```
-                raise ValueError("invalid order")
+            raise ValueError("invalid order")
```
A pure-whitespace dedent of the sole statement in an `elif` suite in
`_BaseChain.fit`. Python execution is identical for both indentations (one
statement, consistently indented within its block); it raises the same
`ValueError` on the same condition. No observable behavior changes, and no F2P
or P2P test exercises a difference. It is therefore **not modeled** in
Solution.lean. `patch.diff` carries it verbatim (gold) so the patch applies and
resolves; it has no refinement row beyond this note.

## 2. Symbol binding & the type bijection

| Lean symbol (Solution.lean) | Python symbol @ base_commit | location |
|---|---|---|
| method `gatherLabels` | the changed-behavior fragment of `MultiOutputClassifier.fit`: `self.classes_ = [estimator.classes_ for estimator in self.estimators_]` (the assignment the patch adds) | `sklearn/multioutput.py:300` (class), patch hunk @ line 327 |
| param `submodels : List Submodel` | `self.estimators_` — the per-target fitted sub-model list produced by `super().fit(...)` (the unchanged parent `MultiOutputEstimator.fit`, `sklearn/multioutput.py:124`) | `sklearn/multioutput.py:167` (set in parent fit) |
| `Submodel.labels : List Int` | `estimator.classes_` of one per-target sub-model — the integer class-label array the underlying base classifier learned | attribute set by the base estimator's own `fit`; read at the patch line |
| result `out : List (List Int)` | `self.classes_` after the patched fit (a Python `list` of the per-sub-model `classes_` arrays) | patch line |

Type bijection:
- Python `list` of objects each exposing `.classes_` ↔ Lean `List Submodel`,
  where only the touched field (`classes_`) is modeled, as `labels`.
- one sub-model's `classes_` ndarray of class labels ↔ `List Int` (the F2P /
  tested case uses integer labels from `make_multilabel_classification` /
  `RandomForestClassifier`; the spec's discriminating content is the per-target
  STRUCTURE — one entry per sub-model, in order, elementwise equal — not the
  label dtype).
- the result Python `list` `self.classes_` ↔ Lean `List (List Int)`; list order
  ↔ list order (no reordering; the comprehension preserves `estimators_` order).
- `len(self.estimators_) == n_outputs` ↔ `submodels.length`.

## 3. Callees & provenance

- **`super().fit(X, Y, sample_weight)`** — the UNCHANGED parent
  `MultiOutputEstimator.fit` (`sklearn/multioutput.py:124`). It sets
  `self.estimators_` to the list of per-target fitted sub-models
  (`len == y.shape[1] == n_outputs`), each a fitted classifier exposing a
  `.classes_` array. The patch does NOT change it. Its post-state IS the
  modeled method's input (`submodels`): an **A-consumed-as-precondition** callee.
  G-AX validates this assumption against the real callee (axiom_check.py): a real
  fitted `MultiOutputClassifier` has `estimators_` a list of length `n_outputs`,
  each `estimators_[i].classes_` an array, and fit does not raise.
- **`estimator.classes_`** — reading one sub-model's class-label array. UNCHANGED
  attribute (the base estimator's fit sets it). Modeled concretely as the
  `Submodel.labels` field (an **I** op: read the touched field). No axiom: the
  value is plain input data the patch only collects, so axiomatizing it would be
  a dead/over-claimed axiom (SPEC_GUIDE §0 directive 7).

No flag dependencies. (`sample_weight` is threaded straight into `super().fit`
and never touches the changed assignment.)

## 4. G-CONF fuzz seed

Pinned seed: **14629**. Differential fuzz = 100000 synthetic `estimators_`
inputs (each a list of mock sub-models with random integer `.classes_` arrays);
oracle = the patch expression `[e.classes_ for e in estimators_]`; shadow = the
Lean `gatheredLabels` transliteration. Plus a real-sklearn grounding leg
(`MultiOutputClassifier(RandomForestClassifier(n_estimators=2))` on fuzzed
multilabel data) asserting the patched `clf.classes_ == [e.classes_ for e in
clf.estimators_]` (deep array equality), `isinstance list`, length `n_outputs`.
