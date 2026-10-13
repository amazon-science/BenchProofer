# mapping.md — scikit-learn__scikit-learn-14710

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 4b6273b87442a4437d8b3873ea3022ae163f4fdf`, states the type
abstraction (the Lean↔Python bijection used by G-CONF), records callee
provenance, and pins the fuzz seed.

Repo file under change:
`sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py`.
Changed method:
`BaseHistGradientBoosting._check_early_stopping_scorer(self, X_binned_small_train,
y_small_train, X_binned_val, y_val)` (`gradient_boosting.py:423`; the touched
statements are the two scorer-input preparations at `:429–435` post-patch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepareScorerTargets (isClf, labels, y)` | the per-site preparation of the target argument handed to `self.scorer_(self, X, ·)` inside `_check_early_stopping_scorer` — `gradient_boosting.py:429–435` | the modeled changed behavior: produce the target sequence the scorer is scored against |
| `isClf : Bool` | `is_classifier(self)` — `sklearn/base.py:632` (`self._estimator_type == "classifier"`); constant within a single `fit` call | whether the estimation task is classification (vs regression) |
| `labels : List Int` | `self.classes_` — the original class-label table set by the classifier's `_encode_y` (`gradient_boosting.py:1029`, `label_encoder.classes_`); for a regressor it is unused | the table of original class labels, indexed by integer code |
| `y : List Int` | the integer-coded target argument at the site: `y_small_train` (train site, `:430`) / `y_val` (validation site, `:435`) | the target codes, one integer code per sample |
| `gather labels y` | `self.classes_[y.astype(int)]` (the post-patch fancy-index lookup, `:428`/`:434`) | the per-code index→label lookup, in order |
| `out : List Int` | the target value actually passed as the 3rd argument of `self.scorer_(self, X, out)` | the prepared targets the scorer scores against |

No callee is consumed as a contract. The index→label lookup is the ordinary
NumPy fancy-index operation `classes_[codes]`, modeled deeply as `gather`
(`idxs.map (table[·])`); see §3.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the repo's NumPy types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `is_classifier(self)` (bool) | `isClf : Bool` | `True ↔ true`, `False ↔ false`. Within one `fit` it is constant; the spec treats it as a free input bit and pins both legs. |
| `self.classes_` — 1-D array of the original class labels, length `n_classes` | `labels : List Int` | the ordered label table; `classes_[k] ↔ labels[k]`. The label values' *concrete* type (str / object / int) is irrelevant to the bug — only that codes are mapped THROUGH this table; modeled as `Int` standing for an opaque label identity (mapping G-CONF uses `int` labels, see §4). `n_classes ↔ labels.length`. |
| `y_small_train` / `y_val` — 1-D array of integer class codes (`Y_DTYPE` floats holding integers `0 … n_classes-1`), one per sample | `y : List Int` | `len ↔ .length`; `y[j] ↔ y[j]` as an integer code; `y.astype(int)[j] ↔ y[j].toNat` (codes are non-negative, `0 ≤ code < n_classes`, captured by the `require`). Order and count are sample order and sample count. |
| `self.classes_[y.astype(int)]` — NumPy fancy index | `gather labels y = y.map (labels[·.toNat]!)` | element-wise lookup, order- and count-preserving: result[j] = `classes_[int(y[j])]` ↔ `labels[y[j].toNat]`. |
| target argument of `self.scorer_(self, X, ·)` | `out : List Int` | identity on the prepared sequence; the scorer reads it positionally. |

The `require ∀ i ∈ y, 0 ≤ i ∧ i.toNat < labels.length` is the Lean frame of the
real invariant that every code is a valid index into `classes_` — guaranteed by
the classifier's `_encode_y` (`LabelEncoder().fit_transform` emits codes
`0 … n_classes-1`, `gradient_boosting.py:1027-1030`). It keeps the deep model
`labels[·.toNat]!` total and faithful (no out-of-range `getElem!` default).

`X_binned_small_train` / `X_binned_val` are NOT modeled: the patch does not
touch them and they are not part of the changed target-preparation observable
(the scorer reads `out` positionally as `y_true`). They are read-only and absent
from the carrier — the directive-5 frame is vacuous for them.

## 3. Callee provenance

`gather` ← `self.classes_[y.astype(int)]`, the NumPy advanced (fancy) indexing
of the label table by the integer code array. This is a **deep model of an
ordinary total operation**, not a borrowed callee contract:

- It is the index→element lookup `result[j] = table[codes[j]]`, modeled exactly
  as `y.map (fun i => labels[i.toNat]!)`. Its full behavior is spelled out in
  the `pure` region; nothing about it is left to an axiom.
- It is therefore **neither A-consumed nor A-reference**: there is no
  axiomatized callee whose contract the proof imports, and there is no opaque
  unchanged-callee map to validate against a real callee. The whole operation
  is concrete (an **I** op under the R type bijection — see refinement.md).
- Consequently there is **no `axiom_check.py`** for this bundle (no axiom and no
  A-reference deep model to validate): G-AX is `skip`. (Same disposition as the
  django-12050 exemplar, whose per-element map is likewise modeled and has no
  axiom_check.) The `.astype(int)` coercion is captured by `.toNat` under the
  `require` that codes are non-negative in range.

The unchanged callee `self.scorer_(self, X, ·)` is **out of scope**: the patch
does not change it, and the bug/fix is entirely in what target sequence is
*passed* to it. We model only the prepared argument `out`, not the scoring; so
no scorer axiom is needed or claimed (over-claiming an opaque scorer would be a
dead axiom — SPEC_GUIDE §0.7).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14710`**. The R/I
shadow transliterates `gather`/the `isClf` branch to Python over the real
carriers (`classes_` a NumPy array, `y` an integer-code array), and the oracle
is the **real post-patch expression** `classes_[y.astype(int)]` (classifier leg)
/ `y` unchanged (regressor leg) — exercised in-process with NumPy, no sklearn
estimator / Docker needed. It fuzzes `n_classes`, code arrays (including the
empty array, repeated codes, all-same, and full-range boundaries), and both the
classifier and regressor legs. Labels are drawn as distinct integers (the label
*identity* is what the lookup preserves; using `int` labels lets the differential
compare values directly). Exit 0 iff zero disagreements.
