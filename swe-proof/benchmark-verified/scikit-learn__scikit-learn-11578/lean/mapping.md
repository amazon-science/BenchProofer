# mapping.md — scikit-learn__scikit-learn-11578

## Symbol binding (file:line @ base_commit dd69361a0d9c6ccde0d2353b00b86e0e7541a3e3)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_scoringProbs` / `problem_spec_scoringProbs` / `correct_scoringProbs` | the per-candidate probability-estimate selection inside `_log_reg_scoring_path` (the scoring model built at L925 and used at L958, whose `predict_proba` regime is the modeled observable) | `sklearn/linear_model/logistic.py:774` (def), `:925` (changed line), `:958` (use) |
| `parseMode` / `ProbMode` | the `multi_class` string → `predict_proba` branch selector (`LogisticRegression.predict_proba`: `if self.multi_class == "ovr": _predict_proba_lr else softmax`) | `sklearn/linear_model/logistic.py:1318` (`predict_proba`, branch at 1343–1353) |
| `softmaxRow` / `softmaxRow` matrix (A-reference) | `sklearn.utils.extmath.softmax` (the multinomial-regime transform) | `sklearn/utils/extmath.py:588` |
| `ovrRow` (A-reference) | `LinearClassifierMixin._predict_proba_lr` (logistic per score, then row-normalise) | `sklearn/linear_model/base.py:280` |
| (scores feed) | `decision_function` produces the real-valued score rows that are this model's input | `sklearn/linear_model/base.py:227` |

## The gold edit

`logistic.py:925`
```
-    log_reg = LogisticRegression(fit_intercept=fit_intercept)
+    log_reg = LogisticRegression(multi_class=multi_class)
```
The scoring model was constructed WITHOUT carrying over the requested
`multi_class`, so it defaulted to `multi_class='ovr'`; its `predict_proba`
therefore always used the one-vs-rest transform even when `'multinomial'` was
requested. The fix carries the requested mode into the scoring model, so the
reported probability estimates use the requested regime.

Note on `fit_intercept`: at the changed call site `fit_intercept` is only used by
the constructor to decide whether `coef_`/`intercept_` are split out of `w`; the
function sets those attributes manually immediately afterward (L944–950), so
dropping `fit_intercept=` from the constructor does not change observable
behavior. The observable that the F2P test pins is the `predict_proba` regime,
governed solely by `multi_class`. The model therefore tracks `multi_class`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean |
|---|---|
| `multi_class` string | `String` (→ `ProbMode` via `parseMode`; `"multinomial"`→multinomial, else ovr) |
| one decision-function row `np.ndarray[float]` (per-sample scores) | `List ℝ` |
| one candidate's decision matrix `np.ndarray[float] shape (n_samples,n_classes)` | `List (List ℝ)` |
| list of candidate matrices (one per `C`/coef set) | `List (List (List ℝ))` |
| `predict_proba` output matrix | `List (List ℝ)` (rows in input order) |
| `softmax(row)` | `softmaxRow` |
| `_predict_proba_lr` row-normalise | `ovrRow` |

Floats are modeled as Mathlib `ℝ` (genuinely real-valued transforms;
`noncomputable`, spec/impl only — SPEC_GUIDE §2). The F2P test compares with
`assert_array_almost_equal`, so G-AX/G-CONF compare within float tolerance.

## Callee provenance + flag deps

- `softmax` (extmath): pure; no flags. Subtracts per-row max for stability then
  exponentiate + row-normalise; mathematically equal to plain
  `exp(x)/sum(exp(x))` (the Lean `softmaxRow`). A-reference, G-AX validated.
- `_predict_proba_lr` (base): pure given `coef_`/`intercept_`; for the 2-D
  decision case it is `sigmoid(x)` per entry then row-normalise (the Lean
  `ovrRow`). A-reference, G-AX validated.
- Selection branch in `predict_proba` keys ONLY on `self.multi_class` (the
  `"ovr"` literal vs everything else). Modeled by `parseMode`. R/I, G-CONF.

## G-CONF fuzz seed

Pinned seed: **11578** (in conformance_check.py and axiom_check.py).
