# refinement.md — scikit-learn__scikit-learn-14629

The operation-by-operation correspondence between `model.py`'s implementation
(the `gather_output_classes` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed** / **A-reference**), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural change — the new `MultiOutputClassifier.fit`

Gold hunk (the load-bearing additions; the new docstring is omitted, it carries
no behaviour):
```
+    def fit(self, X, Y, sample_weight=None):
+        ...
+        super().fit(X, Y, sample_weight)
+        self.classes_ = [estimator.classes_ for estimator in self.estimators_]
+        return self
```

| # | model.py impl op (`gather_output_classes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `estimators: List[Estimator]` | `self.estimators_` at the point the new line runs | R | `self.estimators_` (a Python `list` of fitted sub-classifier objects) ↔ `List[Estimator]`; `estimators[i]` ↔ `estimators_[i]` (mapping.md §2). The model takes the already-fitted list as input, exactly the post-`super().fit()` program state. |
| A2 | (no node) | `super().fit(X, Y, sample_weight)` | I | the fitting step is UNCHANGED by the patch — it is the same inherited `MultiOutputEstimator.fit` before and after. It establishes the `estimators_` precondition the model assumes (each `estimators_[i]` carries its fitted `classes_`); it is not part of the modeled change and computes nothing the gathering re-derives, so it is an identical pre-existing operation (not an axiom). (mapping.md §1.1.) |
| A3 | `est_vals(estimators[i])` read (the touched facet, by value) | `estimator.classes_` (the comprehension's per-iteration field read) | R | `estimators_[i].classes_` viewed by value ↔ `est_vals(estimators[i])` (`= estimators[i].cls_vals`, a `PSeq[int]`): only the touched attribute is exposed; the labels are carried by VALUE because the tested observable (`assert_array_equal`) is value, not identity (mapping.md §2). |
| A4 | `result.append(est_vals(estimators[i]))` in index order `i = 0 .. len-1`, returning `result` | `[estimator.classes_ for estimator in self.estimators_]` | R + I | the list comprehension is exactly an in-order append of each `estimator.classes_` onto a fresh list; iteration order over `self.estimators_` is its index order. The model's loop is the same fresh-list, in-order construction, appending each sub-estimator's class-label VALUE. The `for estimator in self.estimators_` iteration ↔ `while i < len(estimators)` index walk is the canonical R refinement of Python list iteration to index iteration; the append of the per-output labels is I. The model pins value (not identity), so it faithfully covers both the gold (stores the array reference) and any value-equal fix (stores a copy) — both yield identical per-output label values, the tested property. |
| A5 | `Result()` (a `List[PSeq[int]]`) | `self.classes_ = [...]` then `return self` | R | the produced list is bound to `self.classes_`; `self.classes_[i]` ↔ `Result()[i]`, `len(self.classes_)` ↔ `len(Result())`. `return self` surfaces the populated attribute. The F2P test reads `estimator.classes_` (== this `self.classes_`); `isinstance(self.classes_, list)` holds because the comprehension yields a `list`, mirrored by `Result(): List[PSeq[int]]`; the per-output `assert_array_equal` is mirrored by `Result()[i] == est_vals(estimators[i])`. |

The discriminating content of the change — that `self.classes_` is *populated
at all*, with one entry per output, each entry carrying the genuine per-output
class labels — lives in the two postconditions
`len(Result()) == len(estimators)` and
`Forall k: Result()[k] == est_vals(estimators[k])` (element-wise value
equality). The pre-patch wrapper had no `fit` override and never set `classes_`;
`model_prepatch.py` reproduces that (the gathering omitted, `result == []`) and
**fails** the postcondition `len(Result()) == len(estimators)` for any fitted
wrapper (≥1 output) — exactly the spec sensing the change (G-DIFF). The pre-patch
`AttributeError` is the real-world manifestation of "this collection is
unpopulated", and the F2P test `test_multi_output_classes_[estimator1]` asserts
precisely `isinstance(classes_, list)`, `len(classes_) == n_outputs`, and
per-output `assert_array_equal(estimator_classes, classes_[i])` — a **value**
comparison, pinned by A4/A5 + the two postconditions. The postcondition pins the
WEAKEST property the F2P test + the cited downstream consumer actually
discriminate on (per-output label VALUE), not object identity: identity is not
observed by any test or consumer here, so pinning it would wrongly reject a
correct value-equal fix (the original too-strong defect, now corrected).

## B. The cosmetic second hunk — `_BaseChain.fit` indentation (kind I, not modeled)

Gold hunk:
```
         elif sorted(self.order_) != list(range(Y.shape[1])):
-                raise ValueError("invalid order")
+            raise ValueError("invalid order")
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (none) | dedent the sole statement of an `elif` body from 16 to 12 spaces | I (cosmetic) | a whitespace-only PEP8 cleanup. As the only statement in that `elif` body, the over-indentation was syntactically valid and executes identically (the raise fires exactly when the `elif` matches, before and after). It changes no control or data flow, has no observable effect, and is covered by no test. There is no behaviour to pin, so it is not modeled; it is recorded here so every diff line is accounted for. It is an identical operation up to insignificant whitespace. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or cosmetic-I. The one operation that genuinely
*changed* — building the per-output class-label collection — is modeled
**deeply** (the verified index loop that appends each sub-classifier's class
labels, by value, in order), not hidden behind an axiom. There is **no consumed
axiom and no A-reference**: the model does not call or re-derive the unchanged
fitting step (`super().fit`), it takes its result (`estimators`) as a typed
input, so there is no opaque callee to axiomatize and no deep model to validate
against a real callee. `axiom_check.py` (G-AX) therefore checks the
*behavioural claim* directly: the real, patched `fit` produces a `classes_` that
is a `list`, has one entry per sub-estimator, and whose entry `i` is
**value-equal** (`np.array_equal`) to `estimators_[i].classes_` — the same
property the F2P test observes.

## D. verify(model) ⇒ resolved

`gather_output_classes` verifies only if it returns a list with exactly one
entry per fitted sub-classifier (A4, postcondition (1)) and only if entry `i`
carries the genuine class labels of sub-classifier `i`, element-for-element
(A4/A3, postcondition (2), `Result()[k] == est_vals(estimators[k])`). By R
(`self.estimators_` ↔ `List[Estimator]`, `estimator.classes_` by value ↔
`est_vals`, list comprehension ↔ index loop, `self.classes_` ↔ `Result()`) the
verified gathering equals
`self.classes_ = [estimator.classes_ for estimator in self.estimators_]` on the
fitted state the unchanged `super().fit` (A2, I) produces, on the tested
observable. Hence a model satisfying this spec, refined by the map above, agrees
with the gold patch on every F2P-discriminated property up to type refinement —
and the gold patch resolves (G-RESOLVE: F2P
`test_multi_output_classes_[estimator1]` passes; the cosmetic hunk B1 is
behaviour-neutral so the P2P set is preserved). The spec pins value equality —
the weakest property the F2P test (`assert_array_equal`) and the cited consumer
discriminate on — so it admits the gold (stores references) and any value-equal
fix (stores copies) while rejecting every wrong impl (empty / dropped / reordered
/ shifted / constant entries all fail `len` or per-position value). The only
trust point is refinement fidelity (this document, G-EQ); there is no
axiom-soundness trust point because there is no axiom.
