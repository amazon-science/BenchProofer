# mapping.md — scikit-learn__scikit-learn-14710

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4b6273b87442a4437d8b3873ea3022ae163f4fdf`, states the type
abstraction, and gives the provenance of the kind-A obligation.

Repo file under change:
`sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `primary_score_target(is_clf, labels, target)` | the FIRST scored-target preparation in `BaseHistGradientBoosting._check_early_stopping_scorer` — the value passed as `y_small_train` to `self.scorer_(self, X_binned_small_train, y_small_train)` (`gradient_boosting.py:423-431`, the `train_score_.append` hunk) | modeled changed site #1 (always scored) |
| `secondary_score_target(use_secondary, is_clf, labels, target)` | the SECOND scored-target preparation in the same method — the value passed as `y_val` to `self.scorer_(self, X_binned_val, y_val)`, guarded by `self._use_validation_data` (`gradient_boosting.py:433-436`, the `validation_score_.append` hunk) | modeled changed site #2 (held-out / validation) |
| `is_clf` (bool param) | `is_classifier(self)` (`gradient_boosting.py:10` import; gold's guard at the two new lines). `is_classifier(est)` ⇔ `est._estimator_type == "classifier"` (`sklearn/base.py`). True exactly for `HistGradientBoostingClassifier`. | abstracts the classifier/regressor dispatch |
| `use_secondary` (bool param) | `self._use_validation_data` (`gradient_boosting.py:433`) | abstracts whether the held-out path is taken |
| `labels` (`List[int]`) | `self.classes_` — set by `_encode_y` via `LabelEncoder().classes_` (`gradient_boosting.py:1027-1029`); the sorted distinct original class values | the label table |
| `target` (`List[int]`) | `y_small_train` / `y_val` — the internally-held targets, which are the LabelEncoder-encoded integer indices (`encoded_y = label_encoder.fit_transform(y)`, `gradient_boosting.py:1028`; subsampled by `_get_small_trainset`, `gradient_boosting.py:417`; split into train/val) | the internal target indices |
| `decode_one(labels, x)` *(deep model — A-reference)* | the gold's `self.classes_[... .astype(int)]` numpy fancy-index, one element (`gradient_boosting.py:430,435` post-patch) | pure spec: decode one index → original class value |
| `in_index_range(labels, t)` | the standing invariant of a LabelEncoder-encoded target: every code is in `0 .. n_classes-1` (`gradient_boosting.py:1027-1030`) | pure spec: validity of the index target |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.classes_` — a numpy array of distinct original class values (str / object / numeric) | `labels: List[int]` | original class value at table position `k` ↔ `labels[k]`. The EXACT original value type is irrelevant to the tested behaviour (which observes only *representation consistency* between the scored target and `predict`'s output); the bijection abstracts each distinct original value to a distinct int. Length and the index→value map are preserved. |
| `y_small_train` / `y_val` — numpy int arrays of encoded class indices (`Y_DTYPE` floats holding integers `0..k-1`) | `target: List[int]` | `target[i]` = the integer class index of sample `i`; `.astype(int)` in the gold is the identity on these (already integral). |
| `self.classes_[y.astype(int)]` — numpy fancy indexing (whole-array gather) | element-wise: `Result()[i] == decode_one(labels, target[i]) == labels[target[i]]` | numpy advanced integer indexing gathers `out[i] = classes_[idx[i]]`; modeled deeply as the per-element gather. |
| `is_classifier(self)` / `self._use_validation_data` | `bool` params | direct. |
| `self.scorer_(self, X, y)` | not modeled | the unchanged consumer. The bug is solely about the REPRESENTATION of `y` handed to it; the spec pins that representation (`labels[target[i]]` vs `target[i]`). The scorer never appears in the contract — modeling it would over-specify. |

`numpy` arrays / `str` class values are banned-or-awkward in Nagini, so the
carrier is `List[int]` throughout; the specification is phrased over `PSeq[int]`
via `ToSeq`.

## 3. Kind-A obligation (checked by G-AX / axiom_check.py)

### 3.1 `decode_one` deep model ↔ `classes_[target.astype(int)]` (A-reference)

**Real operation:** numpy advanced integer indexing
`self.classes_[y_small_train.astype(int)]` (and `... y_val ...`) — the gold's
two new lines. There is **no `@ContractOnly` axiom** the proof consumes: the
changed gather is modeled DEEPLY by the `@Pure` `decode_one` (and its assembly
into the element-wise postcondition). The deep model is validated equal to the
real operation out-of-band by `axiom_check.py` (G-AX):

- `classes_[idx]` (numpy) gathers `out[i] = classes_[idx[i]]`; `decode_one`
  encodes exactly `labels[t[i]]` for the in-range indices a LabelEncoded target
  always supplies (`in_index_range`).
- Soundness witness also covers the **round trip**: for `encoded =
  LabelEncoder().fit_transform(y)` with `classes_ = LabelEncoder().classes_`,
  `classes_[encoded] == y`. This is exactly why decoding the internal index
  target places it in the SAME (original) representation as
  `HistGradientBoostingClassifier.predict`, which returns
  `self.classes_[encoded_classes]` (`gradient_boosting.py:983`). With both the
  scorer's `y_true` and `predict`'s `y_pred` in the original domain,
  `accuracy_score` no longer compares str against float (the issue's crash).

**Provenance:** `_encode_y` (`gradient_boosting.py:1022-1034`) uses
`sklearn.preprocessing.LabelEncoder` (imported at `gradient_boosting.py:16`):
`encoded_y = label_encoder.fit_transform(y)`, `self.classes_ =
label_encoder.classes_`. `LabelEncoder` maps the sorted unique values to
`0..k-1` and `classes_[code]` inverts it. Docs:
https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.LabelEncoder.html

**Soundness check (G-AX):** `axiom_check.py` runs the REAL numpy fancy-index
and the REAL `LabelEncoder` (the very objects the patched code uses) on 6
boundary + 20000 fuzz gathers and on string + numeric round-trip targets
(including the issue's `['x']*50 + ['y']*50`), asserting (1) the deep model
agrees with `classes_[idx]` element-wise and (2) the encode/decode round trip is
the identity. Exit 0 iff sound. Imports only `numpy` and
`sklearn.preprocessing.LabelEncoder` — the same library the gold patch relies
on; nothing benchmark-private.

The flag dependency: numpy advanced indexing has no configuration knob here;
`.astype(int)` is the identity on the already-integral codes (`Y_DTYPE` floats
holding `0..k-1`). G-AX exercises this exact path.
