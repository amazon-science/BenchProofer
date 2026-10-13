# mapping.md — pydata__xarray-3095

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1757dffac2fa493d7b9a074b84cf8c830a706688`, states the type
abstraction, and gives the provenance of the deep-model reference (no consumed
axiom in this bundle).

Repo files under change: `xarray/core/indexing.py`, `xarray/core/variable.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `IndexWrapper` (class) | `PandasIndexAdapter` — `xarray/core/indexing.py:1229` | the index wrapper holding `array` + `_dtype`; minimal class with only the touched facts |
| `IndexWrapper.__init__(array_kind, stored_dtype)` | `PandasIndexAdapter.__init__(self, array, dtype=None)` — `xarray/core/indexing.py:1232` | wrapper construction + its dtype-determination |
| `IndexWrapper.stored_dtype` field | `PandasIndexAdapter._dtype` — set at `indexing.py:1244` | the element-type the wrapper reports (its `.dtype` property, `indexing.py:1246`) |
| `IndexWrapper.array_kind` field | the dtype that `__init__` would RE-DERIVE from the `array` argument when `dtype is None` (`indexing.py:1234-1243`, the `array.dtype` / object-fallback branches) | the lossy re-derivation source |
| `derive_dtype(array_kind, given_dtype)` *(deep model — A-reference)* | `PandasIndexAdapter.__init__`'s dtype block (`indexing.py:1234-1244`): `if dtype is None: ... else: dtype = np.dtype(dtype)` (the `else` branch is added by the patch) | pure spec: the element-type a freshly built wrapper reports |
| `adapter_copy(self, deep)` | `PandasIndexAdapter.copy(self, deep=True)` — ADDED by the patch (`indexing.py`, new method after `__repr__`) | the modeled changed function: duplicate the wrapper preserving the original dtype |

The second gold hunk, `IndexVariable.copy` (`xarray/core/variable.py:1920`,
body line 1944-1952), is the CALLER that the fix rewires from the inlined
`PandasIndexAdapter(self._data.array.copy(deep=True))` (which dropped the dtype)
to `self._data.copy(deep=deep)` (the new `adapter_copy`). It contributes no new
modeled function — its observable behaviour is exactly "the duplicate's dtype
equals the original's", which `adapter_copy` already pins. The F2P regression
test exercises this caller end-to-end; G-AX (axiom_check.py F3) validates it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a numpy/pandas `dtype` (`np.dtype('<U3')`, `np.dtype('O')`, `int64`, …) | `int` element-type code | distinct dtypes ↔ distinct codes; `np.dtype('O')` ↔ `OBJECT_DTYPE`; dtype equality ↔ code equality |
| `dtype=None` argument (the "re-derive" sentinel) | `NO_DTYPE = -1` | `dtype is None` ↔ `given_dtype == NO_DTYPE` |
| `self.array` (a `pandas.Index`, possibly object-dtype after the round trip) | summarised by `array_kind` = the dtype that would be re-derived from it | the only fact the dtype-determination reads is the re-derivable dtype; the buffer contents are not observed by the modeled behaviour |
| the `deep` flag (copy vs share the buffer) | `deep: bool` (carried, not constrained) | `deep` controls buffer identity only; it does NOT affect the reported dtype, so the dtype contract is independent of `deep`. The buffer-copy effect (`self.array.copy(deep=True)` vs `self.array`) is an R-refinement of the unobserved buffer, not part of the tested dtype behaviour. |

`array_kind != stored_dtype` is exactly the fixed-width-text case: a `<U*`
wrapper stores `stored_dtype = <U*` while its `array` (a pandas object-Index)
re-derives to `OBJECT_DTYPE`. For numeric dtypes the two agree.

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `derive_dtype` + `adapter_copy` deep model ↔ real `PandasIndexAdapter` (A-reference)

There is **no consumed `@ContractOnly` axiom**. The changed behaviour is modelled
**deeply**:

* `derive_dtype(array_kind, given)` encodes `PandasIndexAdapter.__init__`'s
  dtype-determination: a supplied `dtype` is used verbatim (post-patch
  `else: dtype = np.dtype(dtype)`), otherwise the dtype is re-derived from the
  buffer. Source (`indexing.py:1232-1244` @ base_commit; the `else` branch is the
  patch's added line):
  ```python
  def __init__(self, array, dtype=None):
      self.array = utils.safe_cast_to_index(array)
      if dtype is None:
          if isinstance(array, pd.PeriodIndex):     dtype = np.dtype('O')
          elif hasattr(array, 'categories'):        dtype = array.categories.dtype
          elif not utils.is_valid_numpy_dtype(array.dtype): dtype = np.dtype('O')
          else:                                     dtype = array.dtype
      else:                                         dtype = np.dtype(dtype)   # patch
      self._dtype = dtype
  ```
* `adapter_copy(self, deep)` encodes the patch's new `PandasIndexAdapter.copy`:
  ```python
  def copy(self, deep=True):
      array = self.array.copy(deep=True) if deep else self.array
      return PandasIndexAdapter(array, self._dtype)   # original dtype carried over
  ```
  i.e. the duplicate's reported dtype equals `self._dtype` — the original's
  stored dtype — regardless of what re-deriving from `array` would give.

**The lossy re-derivation (the crux).** `safe_cast_to_index`
(`xarray/core/utils.py:69`) casts a fixed-width-text array to a `pandas.Index`,
which pandas stores as **object** dtype. So when the pre-patch caller did
`PandasIndexAdapter(self._data.array.copy(deep=True))` with `dtype=None`, the
re-derivation `array.dtype` (the object-dtype pandas Index) hit the
`is_valid_numpy_dtype`/`else` path and yielded **object** — casting `<U*` to
`object`. `is_valid_numpy_dtype` is `xarray/core/utils.py:236`.

**Soundness/faithfulness check (G-AX).** `axiom_check.py` runs the REAL
`PandasIndexAdapter` and `IndexVariable.copy`:
* F1 — a supplied dtype is preserved by the real `__init__`; re-deriving
  (`dtype=None`) from a COPY of a text adapter's pandas-Index `array` collapses
  to object (the lossy step is real, and `array_kind != stored_dtype` genuinely
  holds for text);
* F2 — `PandasIndexAdapter.copy(deep=D)` reports the same dtype as the original
  for text/int/float/datetime and `deep ∈ {True, False}` (== model's
  `Result() == Old(self.stored_dtype)`);
* F3 — the F2P regression: `IndexVariable.copy(deep=True/False)` on a `<U*`
  index preserves the dtype (does NOT cast to object).
Imports only `numpy`/`pandas`/`xarray` — the exact libraries the patched code
uses, present in the evaluation container. Exit 0 iff every obligation holds.
