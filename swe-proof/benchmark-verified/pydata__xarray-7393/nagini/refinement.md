# refinement.md — pydata__xarray-7393

The operation-by-operation correspondence between `model.py`'s implementation
(the `materialize_level` impl region, the deep `effective_type` model, and the
value-copy loop) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change site — `PandasMultiIndexingAdapter.__array__` (`xarray/core/indexing.py:1533`, multi-index-level branch)

Gold hunk:
```
 def __array__(self, dtype: DTypeLike = None) -> np.ndarray:
+    if dtype is None:
+        dtype = self.dtype
     if self.level is not None:
-        return self.array.get_level_values(self.level).values
+        return np.asarray(
+            self.array.get_level_values(self.level).values, dtype=dtype
+        )
     else:
         return super().__array__(dtype)
```

The modeled function `materialize_level` covers the `self.level is not None`
branch — the only branch the patch's content changes (the `else` branch's
behaviour comes from the inherited `super().__array__`, which already applied
`if dtype is None: dtype = self.dtype` before this patch; the patch only hoists
that line so the new level branch can see it too). The F2P scenario
(`Dataset(...).stack(...)["bar"].values`) drives exactly this branch:
`stack` builds a `pd.MultiIndex`, the per-level adapter has `level is not None`,
and `.values` calls `__array__(dtype=None)`.

| # | model.py impl op (`materialize_level`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | param `requested: Optional[int]` | `dtype: DTypeLike = None` argument | R | element type ↔ opaque int code; `None` ↔ `None` (no requested type). mapping.md §2. |
| 2 | param `declared: int` | `self.dtype` (the adapter's tracked original element type, `self._dtype`) | R | element type ↔ opaque int code; `self.dtype` is the wrapper's declared type. mapping.md §1/§2. |
| 3 | param `storage_type: int` | the element type of `self.array.get_level_values(self.level).values` (the pandas-promoted storage type) | R | element type ↔ opaque int code; this is the wider type pandas promotes the level values to. mapping.md §2. |
| 4 | param `level_values: List[int]` | `self.array.get_level_values(self.level).values` (the per-label element VALUES) | R | the carried numeric values ↔ `List[int]`; read-only (fractional perm, directive 5) — materialising copies, never mutates them. mapping.md §2. |
| 5 | `dtype = requested; if dtype is None: dtype = declared` (i.e. `effective_type(requested, declared)`) | `if dtype is None: dtype = self.dtype` | I + R | the *exact same* conditional default-resolution (`I`), over the refined int-code carrier (`R`). `effective_type` is the deep `@Pure` spelling of this branch: requested if given, else declared — never `storage_type`. |
| 6 | `res = DenseArray(); res.etype = dtype; <copy level_values into res.values>` | `np.asarray(self.array.get_level_values(self.level).values, dtype=dtype)` | A-reference + R | `np.asarray(values, dtype=d)` builds a fresh dense array whose element type is `d` and whose values equal `values`. The model spells this out deeply (`res.etype = effective`, value-copy loop) over the int-code/`List[int]` carriers (`R`); the deep model is validated **== the real `np.asarray`** out-of-band by axiom_check.py / G-AX (`A-reference`), not consumed as an axiom. No `np_asarray` `@ContractOnly` exists. |
| 7 | `return res` | `return np.asarray(...)` | I | return the freshly built dense array. |

The discriminating content of the change — when no element type is requested,
the result's element type is the DECLARED type (`declared`), NOT the promoted
storage type (`storage_type`) — lives in step 5 (`effective_type(None, declared)
== declared`) feeding step 6 (`res.etype == effective_type(...)`). The pre-patch
code skipped the default-resolution and returned the raw promoted values, so its
result carried `storage_type`; `model_prepatch.py` reproduces that
(`res.etype = storage_type`) and **fails** the postcondition
`Result().etype == effective_type(requested, declared)` on every witness with
`storage_type != effective_type(...)` (e.g. `requested=None, declared=int32,
storage_type=int64`) — exactly the spec sensing the change (G-DIFF).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — resolving the element type and re-materialising the array with it —
is modeled **deeply** (`effective_type` + the `res.etype` assignment + the
value-copy loop), not hidden behind an axiom about the function under change.
There is no consumed `@ContractOnly` axiom. The only external building block,
`np.asarray(values, dtype=d)`, is **unchanged** by the patch and appears solely
as the **A-reference** that G-AX validates the deep model against (step 6).

## verify(model) ⇒ resolved

`materialize_level` verifies only if its result's element-type code equals
`effective_type(requested, declared)` — i.e. the requested type when given, else
the declared type, never the storage type (steps 5–6) — and only if the result's
values equal the input values (step 6 value-copy + the loop invariant). By R
(element type ↔ int code, values ↔ `List[int]`) and the A-reference (the deep
model == real `np.asarray`, G-AX), the verified function equals
`np.asarray(self.array.get_level_values(self.level).values, dtype=dtype)` with
`dtype` defaulted to `self.dtype` — i.e. the gold patch's multi-index-level
branch. The gold patch resolves (G-RESOLVE). The single trust point is axiom
soundness reduced to the A-reference check of §6 (this document, G-EQ; and
axiom_check.py, G-AX).
