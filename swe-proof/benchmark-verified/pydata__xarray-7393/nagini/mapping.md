# mapping.md — pydata__xarray-7393

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 41fef6f1352be994cd90056d47440fe9aa4c068f`, states the type
abstraction, and gives the provenance of the one A-reference deep model.

Repo file under change: `xarray/core/indexing.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `materialize_level(requested, declared, storage_type, level_values)` | `PandasMultiIndexingAdapter.__array__(self, dtype)` — `xarray/core/indexing.py:1533` (multi-index-level branch, body line 1535) | the modeled changed function (materialise one selected level into a dense array) |
| `requested` | the `dtype: DTypeLike = None` argument of `__array__` | the caller-requested element type (`None` ⇒ no request) |
| `declared` | `self.dtype` ⇒ `self._dtype` (the adapter's tracked original element type), defined by `PandasIndexingAdapter.dtype` property — `xarray/core/indexing.py:1432-1434`, set in `__init__` — `xarray/core/indexing.py:1424-1430` | the wrapper's declared element type |
| `storage_type` | the element type (`.dtype`) of `self.array.get_level_values(self.level).values` | the (possibly wider) element type pandas promotes the per-level values to |
| `level_values` | `self.array.get_level_values(self.level).values` (the per-label element values) | read-only values copied into the materialised array |
| `effective_type(requested, declared)` *(deep helper)* | the `if dtype is None: dtype = self.dtype` default-resolution introduced by the patch (`xarray/core/indexing.py:1534-1535` post-patch) | pure spec: requested type if given, else declared type |
| `DenseArray` (etype + values) | the `np.ndarray` returned by `np.asarray(values, dtype=dtype)` (post-patch `xarray/core/indexing.py:1536-1538`) | the freshly materialised dense array (its `.dtype` ↔ `etype`, its elements ↔ `values`) |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): the multi-index-level branch returned
`self.array.get_level_values(self.level).values` directly
(`xarray/core/indexing.py:1535` pre-patch) — i.e. the pandas-promoted storage
array, with no element-type resolution, so `.values` exposed the promoted
(wider) element type. The `else` (`self.level is None`) branch is unchanged in
content (it delegates to `super().__array__`, which already applies the
`if dtype is None: dtype = self.dtype` default) and is outside the modeled
function.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| numpy element type (`np.dtype`, e.g. `int32`, `int64`, `float32`) | opaque `int` code | distinct element types ↔ distinct int codes; `None` (no requested type) ↔ Python `None` via `Optional[int]` |
| the per-label element values `...get_level_values(...).values` | `List[int]` | the carried numeric content; values are equal before/after materialisation for the widening casts the issue covers (int→wider-int, float→wider-float preserve every value) — the F2P tests observe only the `.dtype`, and the value content is unchanged. |
| `np.ndarray` result of `np.asarray(values, dtype=d)` | `DenseArray` (fields `etype: int`, `values: List[int]`) | `.dtype` ↔ `etype`; the array elements ↔ `values`; a freshly constructed array ↔ a freshly constructed `DenseArray` (full permission). |
| `if dtype is None: dtype = self.dtype` | `effective_type(requested, declared)` / the `if dtype is None: dtype = declared` impl branch | identical conditional, refined carrier. |

`str`/array indexing of the numpy element type is not needed; element types are
opaque int codes and the array content is `List[int]`.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `DenseArray` construction + `effective_type` deep model ↔ `np.asarray(values, dtype=d)` (A-reference)
**Building block:** `numpy.asarray(a, dtype=d)` — returns an array with element
type exactly `d` and the same element values as `a` (a copy when the dtype
differs). Docs: https://numpy.org/doc/stable/reference/generated/numpy.asarray.html.
The patch calls it as `np.asarray(self.array.get_level_values(self.level).values,
dtype=dtype)` where `dtype` has been defaulted to `self.dtype` when the caller
passed `None`.

The changed materialisation operation is modeled **deeply** by `effective_type`
(the element-type resolution) plus the `res.etype = effective` assignment and
the value-copy loop in `materialize_level`. There is **no `np_asarray` axiom**
the proof consumes; the deep model is validated equal to the real callee
out-of-band:

  * `effective_type(requested, declared)` == `requested if requested is not None
    else declared` — i.e. the result element type is the requested type if
    given, else the declared type, never the (wider) `storage_type`;
  * the result values equal the input values.

This is exactly what `np.asarray(values, dtype=effective)` produces, and is the
single behavioural change the F2P tests observe (the materialised element type
round-trips the original/declared type instead of leaking the promoted storage
type).

**Soundness check (G-AX):** `axiom_check.py` (a) runs real `np.asarray(...,
dtype=effective)` on deliberately PROMOTED storage arrays (declared int32 /
float32 / int16 / int8 etc. whose storage is int64 / float64) across all
requested/None combinations and asserts the result element type equals the
effective type (requested if given, else declared) and the values are carried
through unchanged; and (b) drives the FAIL_TO_PASS end-to-end scenario with the
real xarray — `Dataset(coords={...narrow dtype...}).stack(...)["bar"].values` —
**in whichever state the instance image is in**. The orchestrator may run the
script at the base commit or after `git apply`-ing the gold
(`run_in_container(..., apply_gold=True)`); since the declared-dtype round trip
only holds once the change is applied, the check DETECTS the regime from the
real behaviour on the canonical int32 example and asserts the matching
obligation: under the applied regime the produced `.values.dtype` equals the
declared dtype for every narrow element type (the A-reference obligation); under
the base regime the narrow integer dtypes are still promoted to a wider type
(the bug the `model_prepatch` skeleton reproduces — confirming the discriminator
`declared != storage_type` is real) while the carried values are unchanged. The
value-preservation half of the A-reference is asserted in both regimes, so the
check is meaningful and exits 0 in either container state (and never silently
passes a state it cannot judge). Imports only `numpy`/`xarray` (the package the
gold patch edits) + stdlib. Exit 0 iff sound.
