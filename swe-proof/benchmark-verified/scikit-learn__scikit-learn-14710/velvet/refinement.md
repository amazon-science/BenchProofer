# refinement.md — scikit-learn__scikit-learn-14710

Operation-by-operation correspondence between `Solution.lean`'s `prepareScorerTargets`
impl region and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. `patch.diff` is the gold patch
**verbatim** (applies at `base_commit = 4b6273b8…`, makes the harness
`resolved` — G-RESOLVE).

## A. The scorer-target preparation — `_check_early_stopping_scorer`

Gold hunk (both the train site and the validation site):
```python
+        if is_classifier(self):
+            y_small_train = self.classes_[y_small_train.astype(int)]
         self.train_score_.append(
             self.scorer_(self, X_binned_small_train, y_small_train)
         )
         if self._use_validation_data:
+            if is_classifier(self):
+                y_val = self.classes_[y_val.astype(int)]
             self.validation_score_.append(
                 self.scorer_(self, X_binned_val, y_val)
             )
```

The two inserted statements are the SAME transformation applied to the two
target sequences (`y_small_train`, `y_val`) handed to `self.scorer_`. A single
`method` models that one transformation; both sites are instances of it (it is
called once per site in the real code). `prepareScorerTargets(isClf, labels, y)`
is the value passed as the scorer's `y_true` argument.

| # | Solution.lean impl op (`prepareScorerTargets`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `isClf : Bool` | `is_classifier(self)` | R | bool ↔ `Bool` (mapping.md §2); `_estimator_type == "classifier"`. Constant within a `fit`; pinned on both legs. |
| A2 | param `labels : List Int` | `self.classes_` | R | the 1-D class-label table ↔ `List Int`; `classes_[k] ↔ labels[k]`, `n_classes ↔ labels.length` (mapping.md §2). |
| A3 | param `y : List Int` | `y_small_train` (train) / `y_val` (val) | R | integer-code target array ↔ `List Int`; `y.astype(int)[j] ↔ y[j].toNat` under the in-range `require`. |
| A4 | `if isClf then … else …` | the two `if is_classifier(self):` guards | I | the branch on the task kind; the classification arm transforms, the regression arm does not. Concrete control flow, transliterated by G-CONF. |
| A5 | classifier arm: `return gather labels y` = `y.map (labels[·.toNat]!)` | `y… = self.classes_[y….astype(int)]` then passed to the scorer | I (R-bridged) | the per-code index→label lookup; `classes_[codes]` (NumPy fancy index) ↔ `gather labels y` element-wise, order- and count-preserving (mapping.md §2/§3). The load-bearing fix: codes mapped back to original labels before scoring. Ordinary total operation, modeled deeply — not a borrowed callee, so I, not A. |
| A6 | regression arm: `return y` | no insertion: `y…` passed to the scorer unchanged | I | when not a classifier the gold inserts nothing; the target reaches the scorer as-is ↔ `out = y`. The directive-5 read-only frame: nothing added/dropped/reordered. |

Discriminating content of the change — on a classification task the scorer's
`y_true` is `classes_[y.astype(int)]` (original labels) and NOT the raw integer
codes `y` — lives in `ensures isClf = true → out = gather labels y` (model) ⇔
the `if is_classifier(self): y = self.classes_[y.astype(int)]` insertion (real).
The pre-patch passed the raw codes `y` to a scorer comparing against original
class predictions (the issue's `TypeError` on string targets);
`Solution_prepatch.lean` reproduces that (`return y` on both legs) and **fails**
`isClf = true → out = gather labels y` (G-DIFF) whenever a code differs from the
label it stands for.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that changed — substituting the integer
codes by their original labels before scoring — is the ordinary table lookup
`classes_[codes]`, modeled **deeply** (`gather`, the spelled-out element-wise
map, step A5, an **I** op under the R type bijection), not hidden behind an
axiom about the function under change. There is **no consumed axiom** and **no
A-reference**: nothing is borrowed from an axiomatized callee and there is no
opaque unchanged-callee map to validate (mapping.md §3) — hence no
`axiom_check.py` and G-AX is `skip`. The unchanged callee `self.scorer_` is out
of scope (the fix changes only what is *passed* to it), so no scorer axiom is
introduced.

## C. Single fixed behavior ⇒ one prepatch

The two inserted statements are the SAME transformation at two sites
(train-score and validation-score); they are one independently-fixed behavior
(decode classifier targets before scoring). One `Solution_prepatch.lean` (the
no-decode skeleton, `return y`) exercises that discriminator. The validation
site differs only by being guarded behind `self._use_validation_data`; it
applies the identical transformation, so it needs no separate failing prepatch
(a prepatch must keep the spec byte-identical, G-DIFF — and the spec already
pins the shared transformation). The F2P test
`test_string_target_early_stopping[None]` drives the train+val scorer path with
`n_iter_no_change=10`, exactly the site this models.

## D. verify(Solution) ⇒ resolved

`prepareScorerTargets` verifies only if both `ensures` hold:
* `isClf = true → out = gather labels y` — on a classification task the prepared
  targets are exactly the per-code lookups through `labels`: the integer codes
  are mapped back to the original class labels before scoring, so the scorer
  compares `y_true` and `y_pred` from the same domain (no `TypeError` /
  category mismatch). This is precisely the behavior the issue + the F2P test
  `test_string_target_early_stopping` demand.
* `isClf = false → out = y` — on a regression task nothing is inserted; the
  read-only targets pass through unchanged (the directive-5 frame and the
  PASS_TO_PASS regression behavior the patch must not disturb).

By the R bijection (`is_classifier ↔ isClf`, `classes_ ↔ labels`, integer-code
array ↔ `y`, fancy index ↔ `gather`) the verified result corresponds to the
patched sites: `self.classes_[y.astype(int)]` for a classifier, `y` otherwise.
By G-CONF the R/I transliteration of `gather`/the branch agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs across both legs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axiom trust
points (no consumed axiom, no A-reference); the only trust point is the
refinement fidelity of this doc (G-EQ + G-CONF).
