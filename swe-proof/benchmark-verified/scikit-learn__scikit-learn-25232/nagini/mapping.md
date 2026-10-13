# mapping.md — scikit-learn__scikit-learn-25232

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f7eea978097085a6781a0e92fc14ba7712a52d75`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sklearn/impute/_iterative.py` (the `IterativeImputer`
class). The unchanged callee lives in `sklearn/impute/_base.py` (the
`SimpleImputer` class).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initial_constant_fill(requested, n_features)` | the first-round constant initialization in `IterativeImputer._initial_imputation` — construct `SimpleImputer(strategy=self.initial_strategy, …)` and read `self.initial_imputer_.statistics_` (`sklearn/impute/_iterative.py:565` def, `:613-616` the constructor call) | the modeled changed behaviour: the per-feature constant array installed for the constant strategy |
| `requested` (parameter) | `IterativeImputer.fill_value` (the new attribute, gold `self.fill_value = fill_value` after `:324`), forwarded as the `SimpleImputer(fill_value=self.fill_value)` argument in `_initial_imputation` (gold add inside `:613` constructor) | the user-supplied replacement value |
| `n_features` (parameter) | `X.shape[1]` — the feature column count of the data fitted at `_initial_imputation` time | the number of features |
| `constant_statistics(requested, n_features)` *(axiom — A-consumed)* | `SimpleImputer.fit` + `SimpleImputer._dense_fit` constant branch — `sklearn/impute/_base.py:363` (`fit`), `:394-400` (default resolution), `:530-533` (`return np.full(X.shape[1], fill_value, dtype=X.dtype)`) | the **unchanged** single-pass imputer's constant-strategy result the changed code calls |
| `resolved_value(requested)` | the default-resolution inside `SimpleImputer.fit` — `if self.fill_value is None: fill_value = 0` for numerical data (`sklearn/impute/_base.py:394-400`) | pure spec helper: the value the unchanged callee actually uses |

The pre-patch repo state the change fixes (for the refinement audit, not
referenced from the consumer spec view): `IterativeImputer.__init__` has **no**
`fill_value` parameter (so `self.fill_value` does not exist), and
`_initial_imputation` constructs `SimpleImputer(...)` **without** a `fill_value`
argument (`sklearn/impute/_iterative.py:613-616` pre-patch), so the inner
imputer defaults `fill_value` to `None` → `0` for numerical data.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `fill_value` (a `None`-or-numerical-value, default `None`) | `Optional[int]` | `None` ↔ `None`; a numerical value ↔ its integer (the FAIL_TO_PASS value is `100`, exact-integral). Precision is **not** the behaviour — the test asserts exact equality (`assert_array_equal(statistics_, fill_value)`), so an integer carrier is faithful (refinement.md A1). |
| `X.shape[1]` (feature count, a non-negative int) | `n_features: int` with `Requires(n_features >= 0)` | identity |
| `statistics_` (ndarray of shape `(n_features,)`, dtype float, all entries equal) | `List[int]` of length `n_features` | `statistics_.shape[0]` ↔ `len(result)`; `statistics_[j]` ↔ `result[j]`; equal numeric entry ↔ equal int |

`numpy` ndarrays and floats are banned/uninteresting here: the tested behaviour
is integer-exact array equality, so the carrier is `List[int]`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `constant_statistics` ↔ `SimpleImputer(strategy="constant")` (A-consumed)
**Callee:** `sklearn.impute.SimpleImputer` with `strategy="constant"`, the
unchanged single-pass imputer the iterative imputer constructs for its first
round. Source (`sklearn/impute/_base.py`, base_commit):

```python
# SimpleImputer.fit  (:394)
if self.fill_value is None:
    if X.dtype.kind in ("i", "u", "f"):
        fill_value = 0
    else:
        fill_value = "missing_value"
else:
    fill_value = self.fill_value
...
# SimpleImputer._dense_fit, constant branch  (:530)
elif strategy == "constant":
    # for constant strategy, self.statistics_ is used to store
    # fill_value in each column
    return np.full(X.shape[1], fill_value, dtype=X.dtype)
```

So for numerical data the installed `statistics_` is `np.full(n_features, v)`
where `v = fill_value if fill_value is not None else 0`. The axiom encodes
exactly the weakest sufficient contract:

  `len(result) == n_features`, and for every feature `j`,
  `result[j] == resolved_value(requested)` with `resolved_value(None) == 0`,
  `resolved_value(v) == v`.

The axiom is the **unchanged** callee's contract; the gold change is solely
*which* value is propagated into it (`fill_value=self.fill_value` vs omitting
it). It does **not** axiomatize the function under change.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `SimpleImputer`
constant strategy on numerical data over requested values
`{None, 0, ±1, ±100, 7, 42, 999, -3}` × feature counts `{1,2,3,4,8,16}` and
asserts `statistics_.shape[0] == n_features` and every `statistics_[j]` equals
`resolved_value(requested)`. It additionally drives the REAL
`IterativeImputer(initial_strategy="constant", fill_value=…, max_iter=0)`
end-to-end (the A-reference observation: the value is *carried through* to
`initial_imputer_.statistics_`), reproducing the FAIL_TO_PASS
`fill_value=100 → statistics_ == 100`. It imports only the public scikit-learn
API and numpy — the package under test. Exit 0 iff sound.
