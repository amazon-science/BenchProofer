# refinement.md — scikit-learn__scikit-learn-14710

The operation-by-operation correspondence between `model.py`'s implementation
(`primary_score_target` / `secondary_score_target`, plus the deep `decode_one`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## Gold patch (both hunks)

```
 def _check_early_stopping_scorer(self, X_binned_small_train, y_small_train,
                                  X_binned_val, y_val):
     ...
+    if is_classifier(self):
+        y_small_train = self.classes_[y_small_train.astype(int)]
     self.train_score_.append(
         self.scorer_(self, X_binned_small_train, y_small_train)
     )
     if self._use_validation_data:
+        if is_classifier(self):
+            y_val = self.classes_[y_val.astype(int)]
         self.validation_score_.append(
             self.scorer_(self, X_binned_val, y_val)
         )
```

Two structurally independent edit sites (the train target and the validation
target), each an `if is_classifier(self): y = self.classes_[y.astype(int)]`
inserted before the value is handed to `self.scorer_`. They are modeled as two
functions, `primary_score_target` (train) and `secondary_score_target`
(validation), with two failing prepatch variants (one per site).

## A. Site #1 — train target (`primary_score_target` ↔ first gold hunk)

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `is_clf: bool` | `is_classifier(self)` | R | `is_classifier(est) == (est._estimator_type == "classifier")` is a pure boolean dispatch; abstracted to a `bool` (mapping.md §1, §2). |
| A2 | param `labels: List[int]` | `self.classes_` | R | the LabelEncoder class table; each distinct original value ↔ a distinct int (mapping.md §2). |
| A3 | param `target: List[int]` | `y_small_train` | R | the internal LabelEncoded integer index target; numpy int array ↔ `List[int]` (mapping.md §2). |
| A4 | `if is_clf:` branch | `if is_classifier(self):` | I | identical boolean dispatch. |
| A5 | the classifier result is `result[i] == labels[target[i]]` (the spelled-out per-element gather, proven by the loop and `decode_one`) | `y_small_train = self.classes_[y_small_train.astype(int)]` | A-reference | the changed gather is modeled **deeply**: `decode_one` (model.py `pure` region) and the verified loop ARE the per-element gather `labels[target[i]]`. There is no consumed gather axiom. The deep model is validated **== the real numpy fancy-index** `classes_[idx]` out-of-band: G-AX (axiom_check.py) runs the real numpy gather + real `LabelEncoder` and asserts `decode_one`-assembly == `classes_[idx]` and that `classes_[encoded] == y` (round trip). `.astype(int)` is the identity on the integral codes (mapping.md §3.1). |
| A6 | the non-classifier branch returns `target` unchanged (`out == target`) | (no transform; `y_small_train` passed as-is) | I | when not a classifier the gold does not touch the target; the regressor passthrough is the identical no-op. |
| A7 | `Result()` (a `List[int]`) is the value the contract pins as handed to the scorer | `y_small_train` passed to `self.scorer_(self, X_binned_small_train, y_small_train)` | R | the spec pins the *representation* of the scorer's `y_true`; `self.scorer_(...)` is the unchanged consumer (mapping.md §2) and is not re-modeled. |

## B. Site #2 — validation target (`secondary_score_target` ↔ second gold hunk)

Identical refinement to site A, under the additional guard
`use_secondary ↔ self._use_validation_data` (R, the `if self._use_validation_data:`
block). Rows B1–B7 mirror A1–A7; A5's A-reference (the deep gather model vs the
real `classes_[y_val.astype(int)]`) is the load-bearing one.

| # | model.py construct | patch.diff op | tag |
|---|---|---|---|
| B0 | `Requires(use_secondary)` + param | `if self._use_validation_data:` | R |
| B1–B7 | as A1–A7, on `y_val` | second gold hunk | R / I / A-reference |

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R, I, or A-reference. The one operation that genuinely *changed* —
inserting the index→label gather before scoring — is modeled **deeply** (the
spelled-out per-element `decode_one` gather consumed in both contracted
functions, A5/B-A5, an **A-reference**), not hidden behind an axiom about a
changed function. There is **no consumed axiom** (`axioms` region is empty):
the only library object involved (numpy fancy indexing / `LabelEncoder`) is the
A-reference the deep model is validated against by G-AX, never a `@ContractOnly`
the proof depends on. No dead axiom is shipped.

## D. The discriminator and the prepatch failures (G-DIFF)

The behavioural delta is: for a classifier, the scored target is decoded to the
original class value (`labels[target[i]]`) rather than left as the internal
index (`target[i]`). The spec senses it through the postcondition
`Implies(is_clf, Result()[i] == decode_one(labels, target[i]))`, which forces
`labels[target[i]]` whenever `target[i] != labels[target[i]]` (the generic
case — distinct original labels are not equal to their positions).

- `model_prepatch.py` reverts **site #1**: the classifier branch forwards
  `target[i]` undecoded → the loop invariant carrying
  `result[k] == decode_one(labels, target[k])` is not preserved, so the
  postcondition is unprovable. **Fails** (G-DIFF), spec byte-identical.
- `model_prepatch_2.py` reverts **site #2** identically. **Fails** on the
  validation site's invariant. Spec byte-identical.

Both reproduce the real pre-patch behaviour, in which `_check_early_stopping_scorer`
passed the integer-encoded target straight to a scorer whose `predict` returns
original-domain labels — the type mismatch the issue reports (`'<' not supported
between instances of 'str' and 'float'`).

## E. verify(model) ⇒ resolved

Each contracted function verifies only if its classifier output equals the
exact per-element decode `labels[target[i]]` (A5) and its non-classifier output
is the identity (A6). By R (`is_classifier`/`classes_`/`y` ↔ bool/`List[int]`,
`.astype(int)` identity) and by G-AX (the deep model == the real numpy gather,
and `classes_[encoded] == y` so both scorer arguments share the original
representation), a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited A-reference — and the gold
patch resolves the F2P test `test_string_target_early_stopping[None]`
(G-RESOLVE). The trust points are the two of PLAN §1.1: the A-reference
soundness (G-AX) and the refinement fidelity (this document, G-EQ).
