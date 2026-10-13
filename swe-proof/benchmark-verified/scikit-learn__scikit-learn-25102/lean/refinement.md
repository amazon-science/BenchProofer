# refinement.md — scikit-learn__scikit-learn-25102

Maps every operation in `implementation_transform` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `transform` (`SelectorMixin.transform` ∘ `SelectorMixin._transform`)

Post-patch repo code (`patch.diff`):
```python
def transform(self, X):
    output_config_dense = _get_output_config("transform", estimator=self)["dense"]
    preserve_X = hasattr(X, "iloc") and output_config_dense == "pandas"
    X = self._validate_data(X, dtype=None, accept_sparse="csr",
                            force_all_finite=..., cast_to_ndarray=not preserve_X,
                            reset=False)
    return self._transform(X)

def _transform(self, X):
    mask = self.get_support()
    if not mask.any():
        ...warn...
        if hasattr(X, "iloc"):
            return X.iloc[:, :0]
        return np.empty(0, dtype=X.dtype).reshape((X.shape[0], 0))
    return _safe_indexing(X, mask, axis=1)
```

Lean impl (`implementation_transform`):
```lean
def implementation_transform
    (isDataFrame outputPandas : Bool)
    (cols : List Column) (nRows commonDtype : Nat) (mask : List Bool)
    : TransformResult := Id.run do
  let keepNative := isDataFrame && outputPandas
  let mut block := cols
  if !keepNative then
    block := castAll cols commonDtype
  let selected := selectByMask block mask
  if !(mask.any id) then
    return { cols := [], nRows := nRows }
  return { cols := selected, nRows := nRows }
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `isDataFrame : Bool` | `hasattr(X, "iloc")` | **R** | duck-type test that the input is a native tabular container (pandas DataFrame). Truthiness ↔ `isDataFrame`. |
| 2 | `outputPandas : Bool` | `_get_output_config("transform", estimator=self)["dense"] == "pandas"` | **R** | configured dense-output container is the native one (set via `set_output(transform="pandas")`). |
| 3 | `cols : List Column` (name+dtype) | the input DataFrame columns and their per-column `.dtypes` | **R** | each column label ↔ a distinct `Nat` identity, each dtype ↔ a distinct `Nat` identity; only equality observed (matches `assert dtype == X.dtypes[name]`). |
| 4 | `commonDtype : Nat` | the single homogeneous numpy dtype produced by `check_array` when the DataFrame is cast to an ndarray | **R** | the one dtype every column collapses to under ndarray conversion; in general ≠ the per-column dtypes (the whole content of the bug). |
| 5 | `mask : List Bool` | `self.get_support()` boolean support mask (one flag per input column) | **R** | per-column selection vector. Unchanged by the patch; an input to the modeled step. |
| 6 | `let keepNative := isDataFrame && outputPandas` | `preserve_X = hasattr(X, "iloc") and output_config_dense == "pandas"` | **I** | the preserve-the-container predicate — both conditions must hold, exactly the patch's `and`. |
| 7 | `if !keepNative then block := castAll cols commonDtype` | `X = self._validate_data(..., cast_to_ndarray=not preserve_X, ...)` (the `cast_to_ndarray=True` path → `check_array` homogenisation) | **I** (deep model of the changed op) | **the fixed decision.** When the container is NOT preserved, the input is homogenised to one common dtype before selection (`castAll cols commonDtype` = every column's `dtype := commonDtype`). When preserved, `block := cols` keeps each column's own dtype. This `if` is the patch's `cast_to_ndarray` gate. |
| 8 | `let selected := selectByMask block mask` | `_safe_indexing(X, mask, axis=1)` (post-patch) | **I** (deep model of the changed op) | by-flag column selection preserving the container: keep column `i` iff `mask[i]`, in input order. `selectByMask = (cols.zip mask).filterMap (keep if flag)` mirrors masked column indexing exactly. |
| 9 | `if !(mask.any id) then return { cols := [], nRows := nRows }` | `if not mask.any(): ... return X.iloc[:, :0]` (DataFrame branch) / `np.empty(0).reshape((X.shape[0], 0))` | **I** | the no-features-selected special case: zero columns, row count (index) preserved. `X.iloc[:, :0]` keeps the row index; `selectByMask block mask = []` already holds when every flag is false, so the early return agrees with the general clause and pins `nRows`. |
| 10 | `return { cols := selected, nRows := nRows }` | the returned reduced container (`output.dtypes`, `output.shape[0]`) | **R** | the modeled observable: surviving columns (name+dtype, input order) and row count. Row count is preserved by selection (`directive 5` frame: `nRows` pinned to the input). |

The impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched preserve-or-homogenise-then-select behavior.

## Soundness check (verify ⟹ correct)

- `problem_spec_transform` pins BOTH output components EXACTLY (directive 5 /
  frame): `nRows` equals the input row count, and `cols` equals the by-flag
  selection taken from either the columns-as-given (under `isDataFrame &&
  outputPandas`) or the homogenised block (otherwise). No output component is
  left unconstrained. The postcondition is grounded entirely in the inputs
  (`cols`, `mask`, `commonDtype`, the two gate booleans) — no ungrounded oracle
  (directive 8); the only way to satisfy it is to perform the modeled
  preserve-or-homogenise decision then the by-flag selection.
- The prepatch impl ALWAYS homogenises (`block := castAll cols commonDtype`,
  with no `keepNative` branch) — exactly the missing-`cast_to_ndarray`-flag bug.
  It violates the spec on the discriminating clause `isDataFrame && outputPandas
  = true` whenever some SELECTED column's original dtype differs from
  `commonDtype` (the generic mixed-dtype case): post-patch that column keeps its
  own dtype, prepatch it carries `commonDtype`. On such an input
  `selectByMask cols mask ≠ selectByMask (castAll cols commonDtype) mask`, so the
  carried gold proof cannot close (G-DIFF / G-PANEL).
- This is precisely what the FAIL_TO_PASS tests exercise: `test_output_dataframe`
  and `test_dataframe_output_dtypes` build a DataFrame with mixed per-column
  dtypes (`float32`, `category`, `float64`), request pandas output, run a
  feature-selection `transform`, and assert each output column's dtype equals the
  input column's dtype. Pre-patch every output column is `float64` (the
  homogenised common dtype), failing the assertion; post-patch each surviving
  column keeps its original dtype. The `step=0` case (no features selected) is the
  `mask.any() == False` branch and checks the index/row count is preserved.
- G-CONF confirms the R/I shadow == an in-process replica of the patched behavior
  over hand-picked edge cases (empty column lists, all-false / all-true masks,
  identity-vs-shifted common dtype, every `(isDataFrame, outputPandas)` combo)
  plus ≥10⁵ fuzzed inputs.

## Axioms

None consumed and none referenced: the changed operations (the
preserve-or-homogenise decision and the by-flag column selection) are modeled
deeply over the input columns and the selection vector, so there is no `opaque`
callee, no consumed `axiom`, and no A-reference. `axiom_check.py` is a skip stub
and G-AX skips.
