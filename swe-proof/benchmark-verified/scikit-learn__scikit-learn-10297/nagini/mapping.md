# mapping.md — scikit-learn__scikit-learn-10297

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b90661d6a46aa3619d3eec94d5281f5888add501`, states the type
abstraction, and records callee provenance. There are **no axioms** (the
`# axioms-start/end` region is empty): both modelled behaviours are the
*changed* code, modelled deeply, so there is nothing to over-approximate.

Repo file under change: `sklearn/linear_model/ridge.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `configure_classifier_cv(store_cv_values)` | `RidgeClassifierCV.__init__` — `sklearn/linear_model/ridge.py:1335` (the changed `__init__`/`super().__init__(...)` hunk) | the modelled changed function: the classifier constructor that must accept and forward the retention flag |
| `EngineConfig` (`.retain_values`) | the cross-validation engine configuration carried by `_BaseRidgeCV` / `_RidgeGCV` — the `store_cv_values` attribute set in `_BaseRidgeCV.__init__` (`ridge.py:1091,1098`) and read in `_RidgeGCV.fit` (`ridge.py:1077`) | minimal class with only the touched field (the retention flag forwarded down the constructor chain) |
| `stored_cv_values(cfg, n_samples, n_targets, n_alphas)` | the retention branch of `_RidgeGCV.fit` (`ridge.py:1077-1082`) as reached through the classifier, composed with the classifier's label-binarization of `y` into a 2-D target matrix (`RidgeClassifierCV.fit`, `ridge.py:1364-1376`) | the modelled downstream observable: the shape of the retained `cv_values_` the F2P test asserts |
| `CvRecord` (`.rank`, `.n_samples`, `.n_targets`, `.n_alphas`) | the `cv_values_` ndarray and its `.shape` (`ridge.py:1082`, surfaced via `_BaseRidgeCV.fit` `ridge.py:1128`) | minimal class abstracting only the array's rank and three axis lengths |

The pre-patch repo symbol the change fixes (for the refinement audit, not
referenced from the consumer spec view): `RidgeClassifierCV.__init__` at
`ridge.py:1335-1340`, whose signature lacks `store_cv_values` and whose
`super().__init__(...)` call (`ridge.py:1337-1339`) omits it — so the base
default `store_cv_values=False` (`ridge.py:1091`) is always used and a caller
requesting retention either gets a `TypeError` (unexpected kwarg) or, with the
kwarg silently dropped, never has `cv_values_` populated.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `store_cv_values` constructor argument (`bool`) | `store_cv_values: bool` | identity |
| the engine's `store_cv_values` attribute set down the constructor chain (`_BaseRidgeCV.__init__` → `_RidgeGCV`) | `EngineConfig.retain_values: bool` | identity on the boolean flag; the only field of the engine config the change touches |
| `self.cv_values_` ndarray (or its absence when retention is off) | `Optional[CvRecord]` | `None` ↔ attribute not set / retention disabled; a `CvRecord` ↔ the populated array |
| `cv_values_.ndim` | `CvRecord.rank: int` | identity |
| `cv_values_.shape == (n_samples, n_targets, n_alphas)` | `(CvRecord.n_samples, CvRecord.n_targets, CvRecord.n_alphas)` | per-axis identity; `n_targets` ↔ `n_y = Y.shape[1]`, the number of columns of the label-binarized target matrix |

The classifier always label-binarizes `y` into a 2-D indicator matrix `Y`
(`LabelBinarizer(pos_label=1, neg_label=-1)`, `ridge.py:1364-1365`) before
delegating to `_BaseRidgeCV.fit`. Hence inside `_RidgeGCV.fit` the engine always
sees `len(y.shape) != 1`, takes the `cv_values_shape = n_samples, n_y, len(alphas)`
branch (`ridge.py:1081`), and `cv_values_` is **always rank 3** for the
classifier — including the binary case, where `n_y = 1`. This is exactly the
F2P assertion `r.cv_values_.shape == (n_samples, n_targets, n_alphas)` with
`n_targets = 1` for the binary input.

## 3. Callee provenance / G-AX

There are **no `@ContractOnly` axioms and no A-reference deep models of an
unchanged callee**. Both `configure_classifier_cv` and `stored_cv_values` model
the *changed* behaviour directly (kind R/I refinements only — see
refinement.md). G-AX is therefore vacuous (no axiom to check against a real
callee).

`axiom_check.py` is nonetheless provided as a **reference soundness witness**:
it imports the real (post-patch) `sklearn.linear_model.RidgeClassifierCV`,
exercises it on the F2P-style boundary inputs (binary and multilabel targets,
several `alphas` lengths) plus randomized fuzz, and asserts that the two
modelled behaviours hold of the real estimator: (1) the constructor accepts
`store_cv_values` and the engine ends up configured with the requested flag
(`estimator.store_cv_values == store_cv_values`); (2) when retention is on,
`cv_values_.ndim == 3` and `cv_values_.shape == (n_samples, n_targets, n_alphas)`.
It imports only `numpy` and `sklearn` (the repo under test) — no
construction-only helpers — and exits 0 iff every observation matches the model.
