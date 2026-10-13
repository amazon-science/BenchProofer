# mapping.md — scikit-learn__scikit-learn-14629

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4aded39b5663d943f6a4809abacfa9cae3d7fb6a`, states the type
abstraction, and gives the provenance of every callee.

Repo file under change: `sklearn/multioutput.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `gather_output_classes(estimators)` | the body added to `MultiOutputClassifier.fit` — the line `self.classes_ = [estimator.classes_ for estimator in self.estimators_]` (post-patch `sklearn/multioutput.py:347`) | the modeled changed behaviour: build the per-output class-label list of a fitted multi-output classifier |
| `Estimator` (field `cls_vals`) | one fitted single-output sub-estimator stored in `self.estimators_` (`sklearn/multioutput.py:167-171`), carrying its own fitted `classes_` attribute | minimal object exposing only the touched read-only facet (its fitted class labels), modelled as a pure label-sequence value |
| `est_vals(e)` (`@Pure`, returns `PSeq[int]`) | a sub-estimator's `classes_` attribute read (e.g. `RandomForestClassifier.classes_`, the unique class labels for that output), viewed by VALUE | pure accessor for one output's class-label sequence; its element values are the discriminator (matching the test's `assert_array_equal`) |
| `estimators` (`List[Estimator]`) | `self.estimators_` — the list of fitted sub-estimators set by `MultiOutputEstimator.fit` (`sklearn/multioutput.py:167-171`) | the read-only input the gathering iterates over |
| `Result()` (`List[PSeq[int]]`) | `self.classes_` — the attribute the new `fit` sets | the produced per-output class-label list; element `i` is the label sequence of sub-estimator `i`, compared by VALUE |

The pre-patch repo state (for the refinement audit, not referenced from the
consumer spec view): `MultiOutputClassifier` (`sklearn/multioutput.py:300`) has
**no `fit` override** and inherits `MultiOutputEstimator.fit`
(`sklearn/multioutput.py:124-171`), which sets `self.estimators_` but never sets
`self.classes_`. So `classes_` is absent on a fitted `MultiOutputClassifier`
(the observed `AttributeError`).

### 1.1 The unchanged fitting step (`super().fit`)
The added `MultiOutputClassifier.fit` first calls
`super().fit(X, Y, sample_weight)` (`MultiOutputEstimator.fit`), which fits one
sub-estimator per target column and stores them in `self.estimators_`; each
sub-estimator `estimators_[i]` ends up with its own fitted `classes_`. This
fitting step is **unchanged** by the patch. The model takes the already-fitted
`estimators` list as input (each `Estimator` already carries its `cls_vals`,
the class labels its output learned), exactly mirroring the post-`super().fit()`
program state at the point the new line runs. No `@ContractOnly` axiom is needed:
the model does not re-derive the sub-estimators' class labels, it only gathers
the per-output labels that already exist — the operation the patch adds.

### 1.2 The cosmetic second hunk (behaviour-neutral, not modeled)
The gold patch contains a second hunk in `_BaseChain.fit`
(`sklearn/multioutput.py:422-423`): the single statement
`raise ValueError("invalid order")` inside an `elif` body is dedented from 16
spaces to its correct 12-space indentation. As the sole statement in that `elif`
body, the over-indentation was syntactically valid and behaviourally identical
(the raise fires exactly when the `elif` matches, either way). It is a
whitespace-only PEP8 cleanup with **no observable effect** and **no test**; it is
therefore NOT modeled (there is no behaviour to pin). It is recorded as a
cosmetic-`I` row in refinement.md so the refinement audit covers every diff line.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.estimators_` — a Python `list` of fitted sub-estimator objects | `estimators: List[Estimator]` | `estimators_[i]` ↔ `estimators[i]`; `len(estimators_)` ↔ `len(estimators)` (both equal `Y.shape[1]`, the number of outputs `n_outputs`). The list is read-only here (the gathering does not mutate it). |
| one sub-estimator `estimators_[i]` | `Estimator` object with one read-only facet `cls_vals` | only the touched attribute (`classes_`) is exposed; `estimators_[i].classes_` viewed by value ↔ `estimators[i].cls_vals`. |
| `estimators_[i].classes_` — a numpy array of unique class labels for output `i` | `PSeq[int]` (the pure value of `est_vals(estimators[i])`) | the F2P test compares the per-output labels with `assert_array_equal`, i.e. by **value** (element-for-element), NOT by object identity. So the model carries each output's labels as a pure label-sequence VALUE: the unique class-label codes for output `i` ↔ `est_vals(estimators[i])`. Whether the real comprehension stores the array *reference* (as the gold does) or a value-equal *copy* is below the tested observable — both yield the same per-output label values, so both are admitted. |
| `self.classes_` — the new Python `list` built by the comprehension | `Result(): List[PSeq[int]]` | `self.classes_[i]` ↔ `Result()[i]`; `len(self.classes_)` ↔ `len(Result())`. The comprehension creates a fresh outer list whose element `i` carries the labels of `estimators_[i].classes_` — captured by `Result()[i] == est_vals(estimators[i])` (element-wise value equality, the tested property). |
| the `list` builtin type test `isinstance(estimator.classes_, list)` in the F2P test | `Result()` typed `List[PSeq[int]]` | the model's result is a Nagini list, mirroring that `self.classes_` is a Python `list` (the comprehension's result), satisfying the `isinstance(..., list)` assertion. |

No `str`/`float` modelling is needed: the observable is *which* class labels sit
at each output position (by value) and *how many* there are — both integer/
sequence structure. The choice of **value equality** (not object identity)
matches the F2P discriminator exactly: `test_multi_output_classes_[estimator1]`
asserts `assert_array_equal(estimator_classes, expected_classes)`, a value
comparison, and the only cited downstream consumer
(`cross_val_predict → _enforce_prediction_order`) uses `classes_` by value. A
value-correct fix (e.g. storing copies) resolves the issue and is admitted; an
over-strong identity pin would wrongly reject it (the original too-strong defect,
now fixed).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

**None.** There is no `@ContractOnly` axiom. The added behaviour
(`self.classes_ = [estimator.classes_ for estimator in self.estimators_]`) is a
pure per-element gathering over an already-fitted list, modelled **deeply** and
verified directly. The unchanged `super().fit` that produces `estimators_` is
not re-derived (the model takes the fitted list as input), so no callee is
axiomatized and there is no A-reference deep-model equivalence to check.

`axiom_check.py` therefore validates the *behavioural claim* rather than an
axiom: it runs the real, patched `MultiOutputClassifier.fit` in-container on a
multi-output classification problem and asserts the three properties the spec
pins — `self.classes_` is a `list`, `len(self.classes_) == len(estimators_)`,
and `np.array_equal(self.classes_[i], estimators_[i].classes_)` for every output
`i` (per-output **value** equality, exactly the F2P test's `assert_array_equal`
discriminator) — exactly the structural guarantees `gather_output_classes`
proves under the type refinement of §2 (`Result()[i] == est_vals(estimators[i])`).
It imports only `sklearn` + `numpy` (the patched module and its hard dependency),
nothing test-specific.
