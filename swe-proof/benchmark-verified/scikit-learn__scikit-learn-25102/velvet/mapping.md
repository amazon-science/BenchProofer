# mapping.md — scikit-learn__scikit-learn-25102

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f9a1cf072da9d7375d6c2163f68a6038b13b310f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo files under change: `sklearn/feature_selection/_base.py`, `sklearn/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `projectColumns (cols : List (Int × Bool))` | `SelectorMixin._transform(self, X)` — `sklearn/feature_selection/_base.py:92` | the modeled changed function: project a 2D container down to the masked-in columns |
| `keptCol (p : Int × Bool)` | the per-column contribution of `_safe_indexing(X, mask, axis=1)` (`sklearn/utils/__init__.py:285`, the post-patch column projector) | pure spec: a kept column contributes its own element type; a dropped column contributes nothing |
| `selectMasked (cols : List (Int × Bool))` *(deep model — A-reference)* | the column-wise masked projection `X[:, mask]` performed by `_safe_indexing(X, mask, axis=1)` post-patch (`_pandas_indexing` `X.iloc[:, key]` for a DataFrame; `X[:, mask]` for ndarray) | pure spec: the ordered subsequence of the masked-in columns' element types, each preserved; deep model of the projector, validated `selectMasked == real projection` by axiom_check.py (G-AX) |

### 1.1 Why `_transform` is the seat of the observable behavior
The two F2P tests
(`test_base.py::test_output_dataframe`,
`test_feature_select.py::test_dataframe_output_dtypes`) both assert, for a
pandas-output selector, that **each retained output column has the same dtype as
the corresponding input column** (`output.dtypes[name] == X.dtypes[name]`).
The gold patch achieves this with two cooperating edits:

* `BaseEstimator._validate_data` (`sklearn/base.py:495`) gains a
  `cast_to_ndarray` flag; `SelectorMixin.transform`
  (`sklearn/feature_selection/_base.py:68`) sets `cast_to_ndarray=not preserve_X`
  so that, when the configured output is pandas and `X` is a DataFrame, `X` is
  **not** coerced to a homogeneous ndarray before selection.
* `SelectorMixin._transform` (`sklearn/feature_selection/_base.py:92`) replaces
  the ndarray-only `X[:, safe_mask(X, mask)]` with
  `_safe_indexing(X, mask, axis=1)`, a container-preserving column projection
  (and adds a DataFrame-aware empty-output path `X.iloc[:, :0]`).

Pre-patch, `transform` always coerced `X` through `check_array`/`safe_mask`
into a single homogeneous ndarray; every retained column was therefore emitted
with one common element type (the homogeneous default), losing per-column
dtypes — exactly the issue's `float16`/`category` → `float64` collapse. The
**single observable behavioral change** is: *the projected output preserves each
retained column's own element type, in input order, instead of homogenizing
them.* That is what `projectColumns` / `selectMasked` pin.

The `cast_to_ndarray` plumbing in `base.py` is the mechanism that lets the
DataFrame reach `_transform` uncoerced; it carries no observable behavior of its
own beyond enabling the preserved-dtype projection (see refinement.md §B). It is
not separately modeled — the spec pins the end-to-end observable (preserved
per-column types), which is false unless both edits are present.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a 2D pandas DataFrame `X` with `n` columns | `List (Int × Bool)` of length `n`, in column order | the `i`-th list element models the `i`-th column |
| a single column's dtype/identity `X.dtypes[i]` | the `Int` first component `p.1` | each distinct dtype ↔ a distinct integer code; equality of codes ↔ equality of dtypes (the only relation the F2P tests observe via `==`) |
| the selection mask bit for column `i` (`mask[i]`) | the `Bool` second component `p.2` | `True` ↔ column retained, `False` ↔ dropped |
| `_safe_indexing(X, mask, axis=1)` result's per-column dtypes, in order | `selectMasked cols : List Int` | the ordered list of retained columns' dtype codes; `len` ↔ `.length`; column concat ↔ `List` `++`; empty selection ↔ `[]` |
| the pre-patch ndarray path `np.asarray(X)[:, mask]` per-column dtypes | every kept column emitted as one homogeneous code | models the dtype collapse: the bug's `keptCol` would be `[homogeneous]`, not `[p.1]` |

Only the **dtype identity per column** and **which columns are kept, in order**
are observable to the F2P assertions (`output.dtypes[name] == X.dtypes[name]`
and `output.columns == [...]`); the cell values, index, and shape[0] are
unchanged by selection and are not part of the modeled behavior. The carrier is
`List (Int × Bool)` because the operation is per-column.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `selectMasked` deep model ↔ the real masked column projection (A-reference)
**Callee:** the post-patch column projector
`_safe_indexing(X, mask, axis=1)` (`sklearn/utils/__init__.py:285`), which for a
DataFrame dispatches to `_pandas_indexing` → `X.iloc[:, mask]` (boolean mask),
and the DataFrame empty path `X.iloc[:, :0]` when no column is selected. The
changed projection operation is modeled **deeply** by `selectMasked` (with
`keptCol`) in the `pure` region; there is **no consumed projection axiom**.

Key behavioral fact validated by G-AX: selecting a boolean mask of columns from
a DataFrame returns, in input order, exactly the masked-in columns with each
column's **own dtype preserved** — `out.dtypes == X.dtypes[mask]` and
`out.columns == X.columns[mask]`. This is what `selectMasked cols` (a
front-recursive concatenation of `keptCol p = if p.2 then [p.1] else []`)
encodes. Empty selection yields a 0-column frame (`X.iloc[:, :0]`), i.e. `[]`.

**Flag dependency:** the preserved-dtype path is taken only when the configured
output is pandas AND `X` is a DataFrame (`preserve_X = hasattr(X, "iloc") and
output_config_dense == "pandas"`, then `cast_to_ndarray=not preserve_X`). G-AX
exercises the DataFrame + pandas-output configuration (where the modeled
behavior lives) and also records the contrast with the homogenizing ndarray
path. mapping.md §1.1.

**Soundness check (G-AX):** `axiom_check.py` builds real pandas DataFrames with
heterogeneous per-column dtypes (`float16`, `float32`, `float64`, `category`,
`int64`, `bool`, …), applies the real `_safe_indexing(X, mask, axis=1)` (and the
empty path) under boolean masks (boundary masks + 20 000 randomized fuzz masks),
and asserts (a) the resulting per-column dtypes, in order, equal the deep model
`selectMasked` over the dtype-coded columns (A-reference), and (b) the contrast
that the pre-patch ndarray path collapses them to one homogeneous dtype (so the
modeled change is real, not vacuous). Imports `pandas`/`numpy` + the real
`sklearn.utils._safe_indexing`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25102`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `keptCol`/`selectMasked` (R/I-tagged ops) to Python over the real
container type (a pandas DataFrame), and diffs the per-column output dtypes
against the **patched** `SelectorMixin._transform` behaviour (the real oracle,
applied at base_commit with patch.diff). There is no A-tagged callee left
symbolic in the impl region (the projection is modeled deeply, all R/I), so
`conf_skip=false`.

**Domain of the fuzz universe (the modeled function's precondition).**
`_transform` only ever runs on an `X` that `transform`/`fit` first passed through
`_validate_data` (numeric coercion under `accept_sparse`). A pandas frame mixing
a string `category` column with a `bool` column is *rejected* by that validation
(`ValueError: Cannot cast object dtype to float64`, verified in-container), so it
never reaches `_transform` and lies outside the modeled behavior. Both G-CONF
(`conformance_check.py`) and the G-AX *non-vacuity contrast* therefore range over
the dtype set `{float16, float32, float64, int64, int32, category}` — every
combination of which co-validates, matching the F2P scenario (mixed float
precisions + string `category`). This is a precondition restriction, not a
weakening of the projection contract: the deep-model soundness loop in G-AX still
ranges over the *full* dtype universe (incl. `bool`/`category`) because it calls
the real `_safe_indexing(X, mask, axis=1)` directly, which projects columns with
no numeric coercion. Note: `np.asarray` of a non-numeric frame yields an `object`
ndarray, so the pre-patch ndarray-collapse contrast is only meaningful over the
numeric dtypes (the issue's own `float16/float64 → float64` collapse).
