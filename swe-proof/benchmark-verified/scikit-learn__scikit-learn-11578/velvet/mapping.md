# mapping.md — scikit-learn__scikit-learn-11578

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = dd69361a0d9c6ccde0d2353b00b86e0e7541a3e3`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one deep-model reference.

Repo file under change: `sklearn/linear_model/logistic.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `probabilityMethodForScoring (requested : MultiClass)` | `_log_reg_scoring_path(...)` — `sklearn/linear_model/logistic.py:774` (changed line **925**) | the modeled changed function: which probability method scores the held-out fold |
| `MultiClass` (`ovr` \| `multinomial`) | the `multi_class` argument of `_log_reg_scoring_path` (and of `LogisticRegression`) — `logistic.py:780` | the requested multiclass mode |
| `ProbaMethod` (`ovrNormalize` \| `softmax`) | the two branches of `LogisticRegression.predict_proba` — `logistic.py:1343` (`ovr`) / `:1353` (`softmax`) | the probability-estimation method the scored estimator applies |
| `probaMethodOf` *(deep model — A-reference)* | `LogisticRegression.predict_proba` mode-selection — `logistic.py:1343-1353`, reached via `scoring(log_reg, X_test, y_test)` at `logistic.py:958` | pure spec: the probability method an estimator with a given `multi_class` uses; deep model of the **unchanged** callee `predict_proba`, validated `probaMethodOf == predict_proba`-branch by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): the constructor call `LogisticRegression(fit_intercept=fit_intercept)`
(`logistic.py:925`), which omits `multi_class` and so takes the class default
`multi_class='ovr'` — the scoring estimator's mode is pinned to `ovr` regardless
of the requested mode. The patch makes it `LogisticRegression(multi_class=multi_class)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `multi_class` string `'ovr'` / `'multinomial'` | `MultiClass.ovr` / `MultiClass.multinomial` | `'ovr'` ↔ `.ovr`; `'multinomial'` ↔ `.multinomial`. (These two are the admissible values `_check_solver_option` permits; `logistic.py:927-933` raises `ValueError` on anything else, so the domain is exactly these two.) |
| which `predict_proba` branch the scored estimator takes | `ProbaMethod.ovrNormalize` / `ProbaMethod.softmax` | the `if self.multi_class == "ovr"` branch (`_predict_proba_lr`, the per-class logistic + cross-class normalization) ↔ `.ovrNormalize`; the `else` branch (`softmax(decision_2d)`) ↔ `.softmax`. Observed as the identity of the branch taken, which fixes the probability values and hence any probabilistic score. |
| the dropped `fit_intercept=fit_intercept` constructor kwarg | (omitted — observationally inert here) | The scored estimator never reads `self.fit_intercept`: `_log_reg_scoring_path` assigns `log_reg.coef_` / `log_reg.intercept_` **directly** from the path coefficients (`logistic.py:945-952`), and `decision_function` (`base.py:227`) computes `X·coefᵀ + intercept_` from those attributes, never from `fit_intercept`. So removing the kwarg from the constructor does not change any score. Recorded as R (identity); see refinement.md §B. |

## 3. Callee provenance — the deep-model reference (A-reference, G-AX)

### 3.1 `probaMethodOf` deep model ↔ `LogisticRegression.predict_proba` mode selection
**Callee:** `LogisticRegression.predict_proba` (`sklearn/linear_model/logistic.py:1318`),
reached through the scorer call `scoring(log_reg, X_test, y_test)` at
`logistic.py:958`. For a probabilistic scorer (e.g. `neg_log_loss`) the score is
a function of `log_reg.predict_proba(X_test)`, whose mode selection is:

```python
def predict_proba(self, X):
    ...
    if self.multi_class == "ovr":
        return super(LogisticRegression, self)._predict_proba_lr(X)   # OvR normalize
    else:
        decision = self.decision_function(X)
        ...
        return softmax(decision_2d, copy=False)                       # softmax
```

So the probability method is a pure function of the estimator's `multi_class`:
`'ovr' → ovrNormalize`, anything else → `softmax`. `_log_reg_scoring_path`
restricts the estimator's mode to `{'ovr','multinomial'}`, so the model
`probaMethodOf` (`.ovr → .ovrNormalize`, `.multinomial → .softmax`) is exactly
this selection on the reachable domain. This is the **unchanged** callee whose
behavior the fix relies on; it is modeled DEEPLY (not consumed as an axiom), so
it is an **A-reference**, validated against the real callee by G-AX.

**Why the change is observable only through a probabilistic scorer.** The patch
threads the requested mode into the estimator that is handed to the scorer. The
decision scores themselves are identical across modes (the coefficients are
fixed by the path; `decision_function` is mode-independent), so a non-probabilistic
scorer (accuracy, etc.) is unaffected. Only a scorer that calls `predict_proba`
(`neg_log_loss`) sees the OvR-normalize vs softmax difference — which is why the
sole behavioral F2P case is `neg_log_loss-multiclass_agg_list3`.

**Soundness check (G-AX):** `axiom_check.py` constructs a real
`LogisticRegression` with each `multi_class ∈ {'ovr','multinomial'}`, fits/sets
its coefficients, and asserts that the branch `predict_proba` actually takes
(softmax vs OvR-normalize, distinguished by comparing `predict_proba` against an
independent recomputation of each formula from `decision_function`) matches
`probaMethodOf` on boundary + fuzzed coefficient matrices. Imports only the repo
(`sklearn`) + numpy. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11578`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds is the
transliteration of `probabilityMethodForScoring` (`requested ↦ probaMethodOf
requested`); the oracle is the REAL patched `_log_reg_scoring_path` run
in-container, instrumented (via a probe scorer that records which
`predict_proba` branch the handed-in estimator takes) to observe the probability
method actually used to score the fold. They must agree for both modes, over
10⁵ fuzzed dataset shapes/seeds (confirming the method selection is
dataset-independent — a pure function of the requested mode).

**Invocation nuance (mirrors `LogisticRegressionCV.fit`).** `_log_reg_scoring_path`
is driven differently per mode by its real caller (`logistic.py` ~1645): for
`'multinomial'` it is called once with `pos_class=None` (the path fits the full
multinomial model); for `'ovr'` it is called once **per class** with
`pos_class=<that class>`. With >2 classes, `logistic_regression_path` raises
`ValueError('To fit OvR, use the pos_class argument')` unless `pos_class` is
supplied (`logistic.py:604-609`). So the oracle, in `'ovr'` mode, supplies a
`pos_class` (the first training class) — exactly one leg of the per-class OvR
loop. The scored estimator's `multi_class` (and hence the observed probability
method) is identical across legs and independent of which `pos_class` is chosen,
so one leg faithfully witnesses the OvR behaviour. In `'multinomial'` mode
`pos_class=None`, as the real caller does.
