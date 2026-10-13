# mapping.md — scikit-learn__scikit-learn-25232

## Instance summary
`IterativeImputer` could not accept a user-chosen constant for the first-round
imputation. When the initial strategy is `"constant"`, the inner imputer that
produces the round-zero fill values was always built with the *default* constant
(0 for numerical data), so a user-supplied constant was ignored. The fix forwards
the user constant into that inner imputer so the per-feature fill statistic equals
the user constant.

## Modeled function (symbol binding @ base_commit f7eea978097085a6781a0e92fc14ba7712a52d75)
We model the round-zero constant-fill computation that the patch makes
user-controllable.

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_initial_fill` | `IterativeImputer._initial_imputation` (constant init path) | `sklearn/impute/_iterative.py:565` |
| inner fit (constant branch) | `SimpleImputer._dense_fit` constant case → `np.full(X.shape[1], fill_value)` | `sklearn/impute/_base.py:530-533` |
| default-fill rule (None→0) | `SimpleImputer.fit` numerical default | `sklearn/impute/_base.py:394-400` |
| transform fill | `SimpleImputer.transform` (replace missing by per-column statistic) | `sklearn/impute/_base.py:535-` |
| **changed op** (forward the constant) | gold patch line `fill_value=self.fill_value` in the inner-imputer construction | `sklearn/impute/_iterative.py` patch hunk @625 |

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| `X : ndarray (n_samples, n_features)` of finite floats | `X : Array (Array Rat)` (rectangular; `X.size` rows, `X[0]!.size` cols) |
| `missing_values` sentinel (numeric) | `missingValues : Rat` |
| `fill_value` (numeric or None) | `fillValue : Option Rat` (`none` = default) |
| `statistics_ : ndarray (n_features,)` | `result.statistics : Array Rat` |
| `X_filled : ndarray (n_samples, n_features)` | `result.xFilled : Array (Array Rat)` |

`effFill fillValue = fillValue.getD 0` ↔ SimpleImputer's numerical default
(`fill_value if fill_value is not None else 0`).

## Scope / honest limitations (numerical-constant path)
- Only the `initial_strategy="constant"` path is modeled — the only behavior the
  issue and the FAIL_TO_PASS test exercise. Mean/median/most_frequent statistics
  are NOT modeled (the patch does not change them).
- `fill_value` is modeled over numerical (non-NaN) values via `Rat`. The repo also
  permits `np.nan`/string fills; NaN/string are out of the `Rat` model. The
  discriminating behavior (the user constant reaches the per-feature fill) is fully
  captured for numerical constants, which is what the F2P test checks.
- Under `"constant"` the fit never produces NaN statistics, so the
  `keep_empty_features`/`valid_mask` column-dropping in `_initial_imputation` is a
  no-op on this path; we model the unmasked result. Recorded so G-CONF/G-AX fuzz
  rectangular numerical matrices with the constant strategy.
- Matrices are assumed rectangular (precondition in `correct_initial_fill`).

## Callee provenance + flag deps
- `SimpleImputer` constant fit+transform is an UNCHANGED callee, **deep-modeled**
  (A-reference): the fill loop + transform loop spell out its constant-strategy
  behavior; validated `== real callee` by conformance against the real
  `SimpleImputer(strategy="constant", ...)`. Flag dependency: the modeled behavior
  holds only under `strategy="constant"` (recorded so the harness fixes that flag).
- No A-consumed axiom: nothing opaque is assumed; the proof discharges the deep
  model directly. `axiom_check.py` is therefore a skip stub.

## G-CONF fuzz seed (pinned)
`seed = 25232` (numpy default_rng). Inputs: rectangular `Rat`/float matrices
`n_features ∈ [1,6]`, `n_samples ∈ [1,10]`, `missing_values ∈ {-1, 0, 7}`,
`fill_value ∈ {None} ∪ small integers/rationals`, strategy fixed `"constant"`.
