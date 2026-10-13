# refinement.md — scikit-learn__scikit-learn-14629

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`gatherLabels` `do` block and the `gatheredLabels` deep model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed** /
**A-reference** (axiomatized / deeply-modeled callee), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A leg + this narrative are audited by **G-EQ**. `patch.diff` is the gold
patch **verbatim** (G-RESOLVE).

## A. The class-label record site — `MultiOutputClassifier.fit` (`sklearn/multioutput.py:300`)

Gold hunk (the behavior-bearing line the patch adds):
```
+   def fit(self, X, Y, sample_weight=None):
+       super().fit(X, Y, sample_weight)
+       self.classes_ = [estimator.classes_ for estimator in self.estimators_]
+       return self
```
After the unchanged parent fit has produced the per-target sub-model list
(`self.estimators_`), the override records one class-label collection per
sub-model, in sub-model order, as `self.classes_`.

| # | Solution.lean impl op (`gatherLabels`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | input `submodels : List Submodel` | `self.estimators_` after `super().fit(...)` | A-consumed (as precondition) | the **unchanged** parent `MultiOutputEstimator.fit` (mapping.md §3). Its post-state — a list of fitted sub-models, one per target, each exposing `.classes_` — IS the modeled method's input. Consumed as the typed input; G-AX validates the real callee meets it (length `n_outputs`, each `.classes_` present, no raise). |
| A2 | `s.labels` for one element | `estimator.classes_` of one sub-model | I + R | read the touched field. The ndarray of class labels ↔ `List Int` (mapping.md §2); the read is concrete (I). No axiom: it is plain input data the patch merely collects. |
| A3 | the backward `while` fold building `result = gatheredLabels submodels` (one `s.labels` entry per sub-model, in order) | the list comprehension `[estimator.classes_ for estimator in self.estimators_]` | I | the comprehension is the per-sub-model expansion of `estimators_`; `gatheredLabels` (front-recursive) is its deep model. Python list order ↔ Lean list order (mapping.md §2). |
| A4 | `out = gatheredLabels submodels` and `out.length = submodels.length` | the assigned `self.classes_` (a `list`, one entry per sub-model) | R | the result `list` ↔ `List (List Int)` bijection; `len(self.classes_) == n_outputs` ↔ `out.length = submodels.length` (the F2P length + per-entry observations). |

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — recording the
per-target labels — is modeled **concretely** (the `gatheredLabels` fold over the
input, steps A2/A3, I ops). The only modeled callee, the parent `fit` (A1), is
an **unchanged** callee whose post-state is consumed as the typed input; no axiom
is asserted about `MultiOutputClassifier.fit` itself, and no `.classes_` value is
pinned to an oracle (it flows from the input carrier `submodels`, per SPEC_GUIDE
§0 directive 8).

The second gold hunk — the whitespace dedent of `raise ValueError("invalid
order")` in `_BaseChain.fit` — changes no observable behavior (mapping.md §1) and
is **not modeled**; it carries through `patch.diff` verbatim with no refinement
row.

## C. verify(Solution) ⇒ resolved

`gatherLabels` verifies only if its output is `gatheredLabels submodels` (A3)
over the full sub-model list (A1), with one entry per sub-model (A4). By R
(`estimators_` list ↔ `List Submodel`, `classes_` array ↔ `List Int`, result
`list` ↔ `List (List Int)`) the verified record is exactly
`[e.classes_ for e in estimators_]`, in order, with `len == n_outputs` — which is
exactly what the F2P test `test_multi_output_classes_[estimator1]` asserts
(`isinstance list`, `len == n_outputs`, elementwise `assert_array_equal`). The
prepatch never records the entries (result stays empty), so it fails BOTH
postconditions (G-DIFF) — mirroring the pre-fix `AttributeError: 'classes_'`. By
G-AX the real parent fit produces `estimators_` of length `n_outputs` with each
`.classes_` present and never raises; by G-CONF the I/R transliteration agrees
with `patch.diff`'s behavior on ≥10⁵ checks. Therefore a model satisfying this
spec, refined per the map above, is the gold patch up to type refinement, and
the gold patch resolves (G-RESOLVE).
