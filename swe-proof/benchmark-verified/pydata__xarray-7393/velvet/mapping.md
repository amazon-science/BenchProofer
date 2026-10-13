# mapping.md — pydata__xarray-7393

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 41fef6f1352be994cd90056d47440fe9aa4c068f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `xarray/core/indexing.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `arrayDispatch (adapter : Int) (dtype : Option Dtype)` | `PandasMultiIndexingAdapter.__array__(self, dtype=None)` — `xarray/core/indexing.py:1530` | the modeled changed function (materialize a multi-index level view as a numpy array) |
| `recordedDtype` *(opaque — A-reference)* | the view's recorded element dtype `self.dtype` (property at `xarray/core/indexing.py:1432`, returns `self._dtype` set in `PandasIndexingAdapter.__init__`, `indexing.py:1422-1430`) | pure spec: the data type the view promises to expose |
| `isComponent` *(opaque — A-reference)* | `self.level is not None` — `xarray/core/indexing.py:1532` | pure spec: whether the view exposes a single named level of the multi-index |
| `componentValues` *(opaque — A-reference)* | `self.array.get_level_values(self.level).values` — `xarray/core/indexing.py:1534` @ base_commit | pure spec: the stored values of the exposed level, tagged with their *native* (storage) dtype |
| `toDtype` *(opaque — A-reference)* | `np.asarray(<values>, dtype=dtype)` — the `np.asarray(...)` cast the patch adds (`indexing.py` post-patch) | pure spec: retag/convert an array to a requested dtype |
| `baseMaterialize` *(opaque — A-reference)* | `super().__array__(dtype)` — `PandasIndexingAdapter.__array__`, `xarray/core/indexing.py:1435` (resolves `dtype=None → self.dtype` internally, then `np.asarray(array.values, dtype=dtype)`) | pure spec: the non-level materialization path |
| `arrayMaterialize` | the post-patch `__array__` control flow (default-resolve `dtype`, branch on the level, cast the level values) | pure spec: outcome of the whole materialization |
| `MatArray` | a materialized `np.ndarray` (the two touched observations: its `elems` content + its `dtype`) | the produced array |
| `Dtype` (`abbrev Int`) | a numpy dtype object (`np.dtype`) | an opaque comparable dtype handle |

The pre-patch behaviour the change repairs (refinement audit only, not in the
consumer spec view): at base_commit the level branch returns
`self.array.get_level_values(self.level).values` **directly** — an array tagged
with pandas' native (often promoted, e.g. int64/float64) dtype, NOT the view's
recorded `self.dtype` (e.g. int32/float32). The post-patch code defaults
`dtype` to `self.dtype` and wraps the level values in `np.asarray(..., dtype=dtype)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the adapter/view instance `self` | `adapter : Int` | opaque handle; only the observations `recordedDtype adapter`, `isComponent adapter`, `componentValues adapter` are consulted — never decomposed. G-CONF bridges by replaying each real view and reading the observations. |
| the optional `dtype=None` argument | `dtype : Option Dtype` | `None ↔ Option.none`; an explicit `np.dtype d ↔ Option.some ⟨d⟩`. The default-resolution `dtype.getD (recordedDtype adapter)` ↔ the patch's `if dtype is None: dtype = self.dtype`. |
| a numpy dtype object `np.dtype` | `Dtype = Int` | opaque comparable handle; the dispatch never decomposes a dtype, only resolves a default and compares the produced array's dtype. G-CONF/G-AX compare `str(dtype)` for equality. |
| a materialized `np.ndarray` | `MatArray` (`elems : List Int`, `dtype : Dtype`) | the only observation the issue + F2P test make is the result's `.dtype` (`str(foo["bar"].values.dtype) == dtype`); `elems` records that element content rides through unchanged. G-CONF compares `(dtype, content)`. |
| `np.asarray(a, dtype=d)` | `toDtype a d` | retag/convert to dtype `d`; on the integer/float values at play this preserves content and sets `.dtype == d`. |
| `super().__array__(dtype)` (`PandasIndexingAdapter`) | `baseMaterialize adapter dtype` | the inherited non-level path; resolves `None → self.dtype` internally. |

This is a control-flow + dtype-tagging bundle; no string/float *precision*
modeling is needed — dtype identity (not numeric precision) is the behaviour.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

All five modeled callees are **UNCHANGED** by the patch — the patch only adds a
default-resolution line and wraps the level values in an `np.asarray(...,
dtype=...)` cast; it does not redefine `self.dtype`, `self.level`,
`get_level_values`, `np.asarray`, or `super().__array__`. They are modeled
`opaque`; the facts the modeled control flow relies on are the **A-reference**
facts G-AX validates. There is **no consumed axiom** to over-claim (directive 7).

### 3.1 `componentValues` ↔ `self.array.get_level_values(self.level).values` (A-reference)
The stored values of the exposed level, tagged with the underlying storage's
native dtype. The KEY fact making the change non-vacuous (and the bug real):
this native dtype may DIFFER from the view's recorded `self.dtype` — pandas
`MultiIndex.get_level_values` promotes integer levels to int64 and float levels
to float64, so for an int32/float32 recorded dtype the level values come back as
int64/float64. G-AX asserts: there exists (and the issue's exact case is) a view
whose `componentValues` native dtype ≠ `recordedDtype` — so the retag in the
component branch genuinely changes the observable dtype.

### 3.2 `toDtype` ↔ `np.asarray(values, dtype=d)` (A-reference)
The retag/convert callee. A-reference fact G-AX validates: `np.asarray(a,
dtype=d)` yields an array whose `.dtype == d` (and preserves element content for
the integer/float values at play). This is what makes `toDtype (componentValues
adapter) d` have dtype exactly `d` = the resolved recorded/requested dtype.

### 3.3 `recordedDtype` / `isComponent` / `baseMaterialize` (A-reference)
`recordedDtype` = `self.dtype` (the dtype recorded at construction, e.g. the
int32 the coordinate was created with). `isComponent` = `self.level is not None`
(True for a per-level multi-index adapter, the only kind the issue builds).
`baseMaterialize` = `super().__array__(dtype)`, the inherited path used when the
view is the whole composite index, which already resolves `None → self.dtype`
internally and casts — so the non-level path was never buggy and the change is
confined to the level branch.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL adapters in-container.
It builds, for each of several dtypes (int32, float32, int16, uint8, float16,
and the int64/float64 controls), a stacked (multi-index) coordinate exactly as
the issue does, reaches into the level `PandasMultiIndexingAdapter`, and asserts
(a) its recorded `self.dtype` equals the requested dtype; (b) the **native**
dtype of `self.array.get_level_values(self.level).values` is the promoted
storage dtype, which DIFFERS from the recorded dtype for the sub-64-bit cases
(so the retag is load-bearing); (c) `np.asarray(values, dtype=self.dtype).dtype
== self.dtype` with content preserved; (d) the inherited `super().__array__`
already returns the recorded dtype. Imports only numpy / pandas / xarray (the
repo under test). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7393`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds replays
the unchanged observations (`recordedDtype`, `isComponent`, `componentValues`,
`baseMaterialize`, all A-reference → real repo objects) and transliterates the
NEW control flow (default-resolve `dtype`; on the level branch retag the level
values to the resolved dtype via `np.asarray`; else delegate to `super`). The
oracle is the gold-patched `PandasMultiIndexingAdapter.__array__` itself, called
on the same view + `dtype` argument; both are compared on `(str(result.dtype),
result.tolist())`.
