# mapping.md — pydata__xarray-7393

## Symbol binding (file:line @ base_commit 41fef6f1352be994cd90056d47440fe9aa4c068f)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_arrayConvert` / `problem_spec_arrayConvert` / `correct_arrayConvert` | `PandasMultiIndexingAdapter.__array__` | `xarray/core/indexing.py:1533-1537` |
| `selfDtype : Dtype` | `self.dtype` (← `self._dtype`, the original numpy dtype the adapter was built with) | `indexing.py:1432-1434` (property), set at `1427-1430` |
| `dtypeArg : Option Dtype` | the `dtype: DTypeLike = None` parameter of `__array__` | `indexing.py:1533` |
| `level : Option Level` | `self.level` (`str \| None`) | set in `__init__`, `indexing.py:1531` |
| `rawArray : NpArray` | `self.array.get_level_values(self.level).values` — the raw value array of the selected level (pandas may have widened its dtype) | `indexing.py:1535` |
| `superArray : Dtype → NpArray` | `super().__array__(dtype)` = `PandasIndexingAdapter.__array__` as a function of the effective dtype | `indexing.py:1436-1444` |
| `effectiveDtype` (pure helper) | the `if dtype is None: dtype = self.dtype` default (added by the patch) | `indexing.py:1534-1535` (post-patch) |
| `castArray` (pure helper) | `np.asarray(<values>, dtype=dtype)` — re-present values at the requested dtype | `indexing.py:1536-1537` (post-patch) |

The modeled function is `PandasMultiIndexingAdapter.__array__`. It is the only
function whose behavior changes and the one observed by the FAIL_TO_PASS test
`test_restore_dtype_on_multiindexes[int32/float32]`: a Dataset coordinate of
dtype `int32`/`float32` is stacked into a MultiIndex level, and `.values.dtype`
must still report the original dtype (not the pandas-promoted `int64`/`float64`).

### What the function does (base_commit, buggy)

```python
def __array__(self, dtype: DTypeLike = None) -> np.ndarray:
    if self.level is not None:
        return self.array.get_level_values(self.level).values   # <-- raw, widened dtype
    else:
        return super().__array__(dtype)
```

Reading a MultiIndex level via `get_level_values(...).values` returns a numpy
array whose dtype has been promoted by pandas (e.g. `int32` → `int64`), even
though the underlying values are unchanged. The adapter, however, was built to
preserve the ORIGINAL dtype (it stores `self._dtype`). The level branch returned
the widened array verbatim, dropping the dtype the adapter tracks.

### What the patch changes

```python
def __array__(self, dtype: DTypeLike = None) -> np.ndarray:
    if dtype is None:
        dtype = self.dtype                       # default to the stored original dtype
    if self.level is not None:
        return np.asarray(
            self.array.get_level_values(self.level).values, dtype=dtype   # re-cast
        )
    else:
        return super().__array__(dtype)
```

Two coupled edits, both modeled deeply:
1. **`dtype` defaulting** — when no explicit dtype is requested, use the
   adapter's stored original dtype `self.dtype`. Modeled by `effectiveDtype
   selfDtype dtypeArg = dtypeArg.getD selfDtype`.
2. **level re-cast** — re-present the raw level values at the effective dtype via
   `np.asarray(..., dtype=dtype)`. Modeled by `castArray d rawArray.data`, which
   sets the result dtype to `d` and carries the (in-range) values through.

The `else` (non-level) branch is unchanged in observable behavior: it already
forwarded `dtype` to `super().__array__`, which itself defaults `None` to
`self.dtype` (`indexing.py:1437-1438`). Post-patch the defaulting happens one
level up, but the value handed to `super().__array__` is identical, so
`superArray (effectiveDtype selfDtype dtypeArg)` faithfully models both pre- and
post-patch behavior of that branch.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| a numpy dtype (`np.dtype('int32')`, …) | `Dtype` (`Nat`) | each distinct dtype ↔ a distinct `Nat`; only equality is observed (the F2P test compares `str(...dtype)`). |
| `self.level` (`str \| None`) | `level : Option Level` | `None ↔ none`; a level name ↔ `some n`. Only selected-vs-not and identity are observed. |
| `self.dtype` / `self._dtype` | `selfDtype : Dtype` | the adapter's stored original element dtype. |
| `dtype: DTypeLike = None` parameter | `dtypeArg : Option Dtype` | `None ↔ none`; an explicit dtype ↔ `some d`. |
| `self.array.get_level_values(level).values` | `rawArray : NpArray` | `rawArray.dtype` ↔ the widened dtype of the level values; `rawArray.data` ↔ the (dtype-independent) integer element values. |
| `np.asarray(values, dtype=d)` | `castArray d values` | result dtype `= d`; element values carried through unchanged (values are in range for the involved dtypes). |
| `super().__array__(dtype)` | `superArray : Dtype → NpArray` | the non-level conversion as a function of the effective dtype. |
| return value of `__array__` | `result : NpArray` | the produced numpy array, observed by dtype + values. |

The observable the F2P test pins is `result.dtype`. The fix's whole point is that
for a selected level, `result.dtype = effectiveDtype selfDtype dtypeArg`
(= `selfDtype` when no dtype is requested), NOT `rawArray.dtype`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** Both edits are modeled DEEPLY (`effectiveDtype`
  and `castArray` over the inputs; SPEC_GUIDE §3 — a deeply-modeled changed op is
  never axiomatized). No property of an external callee is consumed by the proof,
  so the `axioms` region declares no `axiom <callee>_prop` and **G-AX skips**.
- `self.array.get_level_values(self.level).values` (the level read) is
  **unchanged** by the patch — the patch only re-casts its result. Its output is
  taken as the modeled input `rawArray`; its production is not modeled (modeling
  only the touched behavior). It is exercised end-to-end by G-CONF.
- `super().__array__(dtype)` (`PandasIndexingAdapter.__array__`) is **unchanged**;
  taken as the modeled input `superArray`. The non-level branch is a pass-through
  whose observable behavior the patch does not alter (see above).
- **Flag dependency:** the discriminating behavior is gated on `self.level is not
  None`. G-CONF fuzzes both `level = some` and `level = none`, and both
  `dtypeArg = none` (the F2P path) and `dtypeArg = some d`.

## G-CONF fuzz seed

Pinned LCG seed: **7393** (see `conformance_check.py` `SEED`). Corpus: randomized
draws over (a) original dtype ∈ {int32, int64, float32, float64}; (b) explicit
dtype argument ∈ {None} ∪ the dtype set; (c) level selected vs not; (d) raw level
values drawn as small in-range integers with a widened dtype, crossed so the raw
dtype both does and does not coincide with the effective dtype, over ≥1e5 fuzzed
inputs. The R/I shadow of `implementation_arrayConvert` is diffed against an
in-process replica of the POST-PATCH `__array__` (dtype defaulting + level
re-cast) built directly on real `pandas.MultiIndex` / numpy. Hand-picked edge
cases pin the discriminating clause: a selected level whose raw values were
widened (int32 coordinate stacked into a MultiIndex), with `dtypeArg = None`.
