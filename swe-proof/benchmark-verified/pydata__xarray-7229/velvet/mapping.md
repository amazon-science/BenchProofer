# mapping.md — pydata__xarray-7229

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3aa75c8d00a4a2d4acf10d80f76b937cadb666b7`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of every callee the modeled function leans on.

Repo file under change: `xarray/core/computation.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rebuildAttrs` (method) | the metadata-propagation logic of `where(cond, x, y, keep_attrs)` for the `keep_attrs is True` configuration — `xarray/core/computation.py:1775` (the `where` function; metadata handling at body lines 1860-1866 pre-patch, the post-call rebuild block post-patch) | the modeled changed function: how the result's per-level metadata is filled from the second argument `x` |
| `lookupAttrs` (pure) | `getattr(getattr(x, <name>, None), "attrs", {})` — the by-name attribute selection from `x` used at every level of the post-patch rebuild (`computation.py` post-patch, the `result[v]` / `result[c]` loops) | pure spec: the metadata of the equally-named member of a source, empty when absent |
| `rebuiltCoord` (pure) | `result[c].attrs = getattr(getattr(x, c, None), "attrs", {})` for `c in getattr(result, "coords", [])` (post-patch) | pure spec: the rebuilt metadata of one output coordinate level |
| `rebuiltVar` (pure) | `result[v].attrs = getattr(getattr(x, v, None), "attrs", {})` for `v in data_vars`, plus the promotion branch `result[x.name].attrs = getattr(x, "attrs", {})` (post-patch) | pure spec: the rebuilt metadata of one output variable level |
| `rebuiltGlobal` (pure) | `result.attrs = getattr(x, "attrs", {})` (ordinary branch) / `result.attrs = {}` (promotion branch) (post-patch) | pure spec: the rebuilt global metadata token |
| `apply_ufunc(...)` result skeleton | `apply_ufunc(duck_array_ops.where, cond, x, y, …)` — `computation.py:1866` | the unchanged callee that produces the *combined values and the level NAMES*; its per-level metadata is then overwritten. Modeled as the `resVars`/`resCoords`/`promote` inputs (provenance §3.1). |

The pre-patch construct the change removes (refinement audit only — NOT in the
consumer spec view): the closure `keep_attrs = lambda attrs, context:
getattr(x, "attrs", {})` (`computation.py:1860-1863`), passed into
`apply_ufunc`, which applies that single global-metadata callback to **every**
output level — global, data variables, AND coordinates — clobbering coordinate
metadata. The fix deletes the closure and rebuilds metadata per level by name
*after* the call.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the
Lean value domain and the live xarray objects. A wrong entry surfaces as
spurious G-CONF disagreements (the falsifiability the plan §4 trust statement
relies on).

| repo reality | Lean carrier | bijection |
|---|---|---|
| an xarray result object (`Dataset` / `DataArray`) reduced to the metadata the op touches | `Obj` | `result` ↔ `⟨gattrs, vars, coords⟩`; the global `result.attrs` ↔ `gattrs`; each member of `result.data_vars` ↔ one `vars` entry; each member of `result.coords` ↔ one `coords` entry |
| one named metadata level (a variable or coordinate of an object) | `Lvl` | `(name, attrs-mapping)` ↔ `⟨name, attrs⟩`; the **name** is a stable identifier (a hashable label) interned to a `Nat`; the **attrs** is the level's metadata `dict` interned to a `Nat` (distinct dicts ⇒ distinct tokens; the empty dict `{}` ⇒ `0`) |
| `getattr(obj, "attrs", {})` (a missing attribute / scalar) | the token `0` | a scalar `x` (no `.attrs`) or an absent member yields the empty mapping `0`; `lookupAttrs` returns `0` for an unmatched name, matching `getattr(..., None)` → `getattr(None, "attrs", {})` |
| `isinstance(y, Dataset) and not isinstance(x, Dataset)` (the promotion case) | `promote : Bool` | the flag that selects the special-case branch: global metadata reset to `{}` (`0`), only the `x.name` variable filled from `x.attrs` |
| `x.name` (the name a promoted single-variable `x` carries) | `xName : Nat` | the interned label of `x` in the promotion branch |
| `getattr(x, "attrs", {})` (x's global metadata) | `xGAttrs : Nat` | x's top-level metadata token |
| x's variables / coordinates (the metadata source) | `xVars` / `xCoords : Array Lvl` | the named metadata levels of the second argument `x` |
| the combined result's variables / coordinates produced by `apply_ufunc` | `resVars` / `resCoords : Array Lvl` | the output skeleton's named levels (names fixed by the value combination; metadata is what the op overwrites) |

The metadata-interning bijection is order-insensitive equality of mappings: two
levels carry equal metadata iff their Python `dict`s are `==`. The checks
(§3, §4) compare the *observable* per-level `.attrs` dicts directly, so the
`Nat` interning is an implementation detail of the model, never observed.

## 3. Callee provenance (kind-R / kind-I — checked by G-CONF)

> **No axioms.** This bundle consumes no axioms and references no deep-model
> callee, so it ships **no `axiom_check.py`** and **G-AX skips**. The only
> callees in scope are `apply_ufunc` (unchanged → an R-input skeleton, §3.1) and
> the Python builtin `getattr(..., "attrs", {})` (an I op, §3.2). The operation
> the patch changes — the per-level by-name metadata rebuild — IS the behavior
> under repair, whose only real embodiment is the *patched* `xr.where`; that is
> **G-CONF**'s oracle (G-CONF applies the gold patch). G-AX runs the *unpatched*
> repo, where coordinate metadata is (buggily) the global token, so it cannot and
> must not be used to validate the fixed behavior.

### 3.1 `apply_ufunc` result skeleton (unchanged callee, R-modeled inputs)
**Callee:** `xarray.apply_ufunc(duck_array_ops.where, cond, x, y, join="exact",
dataset_join="exact", dask="allowed", keep_attrs=keep_attrs)`
(`computation.py:1866`). This callee is **unchanged** by the patch (the gold
edit only stops passing the metadata-callback closure and instead rebuilds
metadata afterwards). It produces the result's *values* and its *level names*
(`result.data_vars`, `result.coords`) and an output *type* (`Dataset` /
`DataArray`). The model takes these as the inputs `resVars`, `resCoords`, and
the `promote` flag — it does not re-derive them. There is **no axiom** about
`apply_ufunc`: the modeled change is *only* the subsequent per-level metadata
rebuild, which is spelled out deeply in `rebuiltCoord` / `rebuiltVar` /
`rebuiltGlobal` (the `pure` region) and the verified `do` block.

The names produced by `apply_ufunc` are independent of `keep_attrs` (it controls
metadata only), so the result skeleton (`resVars`, `resCoords`, `promote`) is the
**same** for the buggy pre-patch and the fixed post-patch — the only difference
is which metadata each level ends with. This is what makes the pre-patch a valid
twin: identical skeleton inputs, divergent per-level metadata.

### 3.2 `getattr(..., "attrs", {})` selection (kind-R, the modeled operation)
The changed operation is the **by-name metadata selection** the fix introduces:
- coordinates: `result[c].attrs = getattr(getattr(x, c, None), "attrs", {})` — modeled by `rebuiltCoord` / `lookupAttrs`;
- variables: `result[v].attrs = getattr(getattr(x, v, None), "attrs", {})` — modeled by `rebuiltVar` (ordinary branch);
- global: `result.attrs = getattr(x, "attrs", {})` — modeled by `rebuiltGlobal`;
- promotion: `result.attrs = {}` and `result[x.name].attrs = getattr(x, "attrs", {})` — modeled by `rebuiltGlobal promote=true` + `rebuiltVar promote=true`.

`getattr` is the Python builtin (semantics fixed by the language, not the repo);
the selection is modeled deeply as I/R legs, not axiomatized. There is **no
consumed axiom** and **no A-reference** in this bundle: the `axioms` region is
empty and there is no `axiom_check.py`.

**Soundness check (G-CONF, not G-AX):** the fix's per-level by-name metadata
rebuild is validated by `conformance_check.py`, which runs **with the gold patch
applied** and diffs the R/I shadow (`lookupAttrs`/`rebuiltCoord`/`rebuiltVar`/
`rebuiltGlobal`) against the patched `xr.where(..., keep_attrs=True)` output over
the F2P boundary matrix plus the pinned fuzz corpus (100007 inputs, exit 0 iff
zero disagreements). G-AX is **not** applicable here: it executes the *unpatched*
repo, in which the bug (coord metadata = x's global token) is still present, so
it would contradict the fixed behavior. The bundle therefore omits
`axiom_check.py` and G-AX skips.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7229`** so the
consumer-side verdict (§11.3) is reproducible. The shadow it builds
transliterates `rebuiltGlobal` / `rebuiltVar` / `rebuiltCoord` / `lookupAttrs`
(all R-tagged ops) to Python over the real xarray types and diffs the resulting
per-level `.attrs` dicts against the patched `xr.where` behaviour (the oracle).
There are no A-tagged callees inside the computed output, so the shadow is pure
R/I and `conf_skip=false`.
