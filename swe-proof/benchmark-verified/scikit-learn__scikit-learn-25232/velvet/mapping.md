# mapping.md — scikit-learn__scikit-learn-25232

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f7eea978097085a6781a0e92fc14ba7712a52d75`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled callee.

Repo file under change: `sklearn/impute/_iterative.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initialFillStatistics (fillValue : Option Rat) (nFeatures : Nat)` | `IterativeImputer._initial_imputation(self, X, in_fit)` — `sklearn/impute/_iterative.py:567` (constant-strategy init branch, body lines 612-620 post-patch) | the modeled changed function: it constructs the initial constant imputer and the per-feature initial fill values it yields |
| `constantFill (fillValue : Option Rat) (nFeatures : Nat)` *(callee stub — A-consumed)* | `SimpleImputer(strategy="constant", fill_value=…).fit(X).statistics_` — `sklearn/impute/_base.py:363` (`fit`, dense-numerical branch `_dense_fit` line 477, constant case lines 530-533) | unchanged imperative callee: the constant-strategy fit whose `statistics_` are the per-feature initial fill values |
| `resolveFill (v : Option Rat)` | the default-resolution `fill_value = self.fill_value if not None else 0` — `sklearn/impute/_base.py:394-400` (numerical case) | pure spec: the concrete constant used per feature |

The configured constant lives on the imputer as `self.fill_value`
(`sklearn/impute/_iterative.py:336` post-patch, set from the new `__init__`
parameter `fill_value` at line 314); `nFeatures` ↔ `X.shape[1]`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX uses (G-CONF is skipped, §4) to translate values between
the Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `fill_value` (the configured constant) for **numerical** data — a Python number or `None` | `Option Rat` | `None` ↔ `none`; a numerical value `v` ↔ `some q` with `q` the exact rational of `v`. The F2P test uses the integer `100`; the issue's headline case is numerical (`fill_value=0` default). |
| `statistics_` (`ndarray` of shape `(n_features,)`), constant strategy | `List Rat` | `arr` ↔ the list of its entries in feature order; `len(arr) == n_features`. Under constant strategy every entry is identical (`np.full`). |
| `n_features` = `X.shape[1]` | `Nat` | identity on non-negative integers |
| `np.full(n, c)` | `List.replicate n c` | `np.full(n, c)[i] == c` for all `i < n` ↔ `(List.replicate n c).get i = c` |

**Scope of the model.** The bundle models the **numerical** constant-fill case
the F2P test and the issue exercise (the issue's compatibility note is about
numerical estimators). The string/object branch (`fill_value="missing_value"`)
and `np.nan` are out of the modeled domain; `resolveFill`'s default is the
numerical `0`. mapping.md §3 records that G-AX fuzzes only numerical inputs.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `constantFill` ↔ SimpleImputer constant-strategy fit (A-consumed)
**Callee:** `sklearn.impute.SimpleImputer(strategy="constant",
fill_value=<v>).fit(X)`, then `.statistics_`. This is an **unchanged** imperative
callee (the patch does not touch `_base.py`); the caller `_initial_imputation`
merely forwards the new `fill_value` into its constructor. Modeled by the `:|`
choice stub `constantFill`, sound by construction.

**Encoded property (weakest sufficient, directive 7):** for numerical dense `X`
with `n_features` columns, the fitted `statistics_` is the length-`n_features`
constant vector whose value is the resolved fill — `self.fill_value` when set,
else the numerical default `0`:

```
statistics_ == np.full(n_features, fill_value if fill_value is not None else 0)
```

i.e. `constantFill fillValue nFeatures = List.replicate nFeatures (resolveFill
fillValue)`. We do NOT pin anything about other strategies, the string branch,
or transform-time behavior — only the contract the caller consumes.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `SimpleImputer` with
`strategy="constant"` on numerical dense matrices, over boundary fill values
(`None`, `0`, `100`, negatives, large) and randomized fuzz (fill value × shape ×
data), asserting `statistics_` equals `[resolveFill(fill_value)] * n_features`
every time. Imports only `sklearn.impute` + `numpy`. Exit 0 iff sound.

### 3.2 Flag dependency
The constant vector arises **only** under `strategy == "constant"` (other
strategies compute data-dependent statistics). `IterativeImputer` reaches this
branch when `initial_strategy == "constant"` (`_iterative.py:611-620`,
`strategy=self.initial_strategy`). G-AX fixes `strategy="constant"` so it fuzzes
the configuration the modeled behavior lives in (SPEC_GUIDE §3, flag-dependent
callees). The F2P test sets `initial_strategy="constant"`, `max_iter=0`.

## 4. G-CONF — skipped (conf_skip = true)
The impl region of the modeled changed function `initialFillStatistics` is a
single call to the A-consumed callee `constantFill` with the forwarded
`fillValue` — it is **all-A-tagged**, with no R/I computational content to
transliterate and differentially test against `patch.diff`. Per SPEC_GUIDE §4.1,
`meta.json conf_skip=true` and `conformance_check.py` exits `status=skip`. The
soundness of the A leg is covered by G-AX (axiom_check.py §3.1); the necessity of
forwarding the configured constant (vs the default) is pinned by G-DIFF (the
prepatch passes `none` and fails the `resolveFill fillValue` clause).
