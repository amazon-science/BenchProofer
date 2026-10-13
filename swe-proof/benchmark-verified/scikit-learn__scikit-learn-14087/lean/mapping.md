# mapping.md — scikit-learn__scikit-learn-14087

## Instance
- repo: `scikit-learn/scikit-learn`
- base_commit: `a5743ed36fbd3fbc8e351bdab16561fbfca7dfa1`
- modeled file: `sklearn/linear_model/logistic.py` — the `refit=False` branch of
  `LogisticRegressionCV.fit` (the per-class summary loop).
- F2P tests (newly passing):
  `test_LogisticRegressionCV_no_refit[ovr-l2]`,
  `test_LogisticRegressionCV_no_refit[multinomial-l2]`,
  `test_LogisticRegressionCV_no_refit[auto-l2]`
- pinned G-CONF fuzz seed: **14087**

## What the fix does (issue + gold patch)
A cross-validation estimator, when it does **not** refit a final model
(`refit=False`), iterates over the classes and fills two per-class summary lists:
the chosen inverse-regularization strength and the chosen penalty mixing ratio. It
also averages the per-fold coefficient estimates into the model coefficients. The
gold patch fixes two independent decisions in this loop.

```python
# logistic.py  (LogisticRegressionCV.fit, refit=False branch)
best_indices = np.argmax(scores, axis=1)
if self.multi_class == 'ovr':                 # PRE  (decision 1: raw configured)
if multi_class == 'ovr':                      # POST (resolved/effective)
    w = np.mean([coefs_paths[i, best_indices[i], :] ...], axis=0)
else:
    w = np.mean([coefs_paths[:, i, best_indices[i], :] ...], axis=0)
...
best_indices_C = best_indices % len(self.Cs_)
self.C_.append(np.mean(self.Cs_[best_indices_C]))

best_indices_l1 = best_indices // len(self.Cs_)            # PRE  (decision 2: always)
self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
                                                           # POST:
if self.penalty == 'elasticnet':
    best_indices_l1 = best_indices // len(self.Cs_)
    self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
else:
    self.l1_ratio_.append(None)
```

### Decision 1 — coefficient-aggregation layout (`chooseLayout`)
The two coefficient-averaging branches index `coefs_paths` with a different number
of leading axes: the `ovr` branch indexes `coefs_paths[i, best_indices[i], :]`
(3-D layout), the other indexes `coefs_paths[:, i, best_indices[i], :]` (4-D
layout). The branch must be chosen by the **effective** multiclass strategy — the
local `multi_class` variable produced by `_check_multi_class(self.multi_class,
solver, len(classes))` at logistic.py:2004, which always resolves `'auto'` (and
the binary special-case) to a concrete `'ovr'`/`'multinomial'`.

Pre-patch the branch was selected from the **raw configured** attribute
`self.multi_class`, which can still be `'auto'`. For `self.multi_class='auto'`
(the default) on a multiclass problem, `self.multi_class == 'ovr'` is False, so the
4-D branch ran on a `coefs_paths` that — because the effective strategy resolved to
`'ovr'` (non-elasticnet → the reshape at logistic.py:2102 gives a 3-D per-class
layout) — has only 3 indexable axes → `IndexError: too many indices for array`
(the issue's traceback). The fix uses the resolved `multi_class`.

### Decision 2 — mixing-ratio entry (`ratioEntry`)
`l1_ratios_` (logistic.py:1971/1978) is the requested mixing-ratio list ONLY when
`penalty == 'elasticnet'`; otherwise it is the singleton `[None]`. Pre-patch the
loop always computed `np.mean(l1_ratios_[best_indices_l1])`; for a non-elasticnet
penalty that means `np.mean([None][...])`, recording a meaningless value (and, in
the F2P configuration, the absence of an `l1_ratios` array is exactly what the new
tests exercise). The fix appends the computed mean only under `elasticnet`, and
appends `None` otherwise.

## Symbol binding
| Lean symbol | Python | provenance (file:line @ base) |
|---|---|---|
| `implementation_chooseLayout` | the `if multi_class == 'ovr'` coefficient-averaging branch choice | logistic.py:2173 (post: `multi_class`) |
| `implementation_ratioEntry` | the `self.l1_ratio_.append(...)` entry recorded per class | logistic.py:2183-2184 (post: the `if self.penalty == 'elasticnet'` guard) |
| `EffStrategy.perClass` / `.joint` | effective `multi_class` value `'ovr'` / `'multinomial'` | logistic.py:2004 (`_check_multi_class`) |
| `ReqStrategy.perClass` / `.joint` / `.autoStrategy` | raw `self.multi_class` `'ovr'` / `'multinomial'` / `'auto'` | logistic.py:1932 |
| `AggLayout.perClassLayout` / `.jointLayout` | the 3-D (`coefs_paths[i, ...]`) / 4-D (`coefs_paths[:, i, ...]`) averaging branch | logistic.py:2174 / 2177 |
| `combinedPenalty` | `self.penalty == 'elasticnet'` | logistic.py:2181 (post guard) |
| `ratio` | `np.mean(l1_ratios_[best_indices_l1])`, the computed mixing-ratio mean | logistic.py:2183-2184 |
| result `Option ℚ` | the value appended to `self.l1_ratio_` (a number, or `None`) | logistic.py:2184 / 2185 |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)
- multiclass strategy strings ↔ the `EffStrategy`/`ReqStrategy` constructors:
  `'ovr' ↔ perClass`, `'multinomial' ↔ joint`, `'auto' ↔ autoStrategy`
  (`autoStrategy` is a *request* only — the effective value is always concrete).
- aggregation branch ↔ `AggLayout`: the `ovr`/3-D branch ↔ `perClassLayout`, the
  other/4-D branch ↔ `jointLayout`.
- `self.penalty == 'elasticnet'` (a `Bool`) ↔ `combinedPenalty`.
- the appended mixing-ratio mean (a Python `float`/`None`) ↔ `Option ℚ`: a recorded
  number ↔ `some q`, the recorded `None` ↔ `none`. The exact numeric value of the
  mean is produced by the unchanged argmax/index/mean arithmetic and is irrelevant
  to BOTH decisions — only its presence/absence is decided by the fix — so it is
  carried as the abstract free input `ratio : ℚ`.

## Callee provenance + flag deps
- **No consumed axiom; no opaque callee.** Both modeled decisions are pure
  control-flow predicates over inputs that the unchanged upstream code computes
  (`_check_multi_class` → effective strategy; the penalty attribute; the
  argmax/index/mean → the candidate `ratio`). Those inputs enter each
  `problem_spec` as universally-quantified free variables, so each theorem is
  proved for ALL their values and consumes no callee property. There is therefore
  no A-consumed row and no A-reference deep model — `axiom_check.py` is a skip
  stub.
- **Flag dependency (decision 1):** the branch hinges on the *effective*
  `multi_class`, which differs from the raw `self.multi_class` exactly when the
  request is `'auto'` or the binary special-case fires. G-CONF drives
  `self.multi_class ∈ {'ovr','multinomial','auto'}` so the `'auto'`-resolves-to-
  `'ovr'` discriminator (the issue's crash config) is exercised.
- **Flag dependency (decision 2):** the entry hinges on `self.penalty ==
  'elasticnet'`. G-CONF drives `penalty ∈ {'l2','elasticnet'}` so both the
  `some ratio` and the `none` branches are observed against the real fit.

## G-CONF fuzz seed
Seed **14087**. G-CONF is a real differential test (`conf_skip=false`): it grounds
the Python shadow of each Lean impl against the REAL patched `fit` over the
`{l2,elasticnet} × {ovr,multinomial,auto}` config grid (observing `l1_ratio_`
presence/absence for `ratioEntry`, and no-IndexError + `coef_.shape` for
`chooseLayout`), then fuzzes the shadow against the gold-patch decision
transliteration over ≥1e5 inputs.
