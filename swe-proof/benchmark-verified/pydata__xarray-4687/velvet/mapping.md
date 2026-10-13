# mapping.md — pydata__xarray-4687

`spec_provenance: cold` (derived from problem_statement + gold patch + repo
source at `base_commit = d3b6aa6d8b997df115a53c001d00222a0f92f63a`).

## 1. Modeled function (symbol binding @ base_commit)

| model symbol | repo symbol | file:line @ base_commit |
|---|---|---|
| `selectByCondition` | `xarray.core.computation.where` | `xarray/core/computation.py:1729` |

The repo `where(cond, x, y)` returns, elementwise, values from `x` where `cond`
is true and from `y` otherwise (via `apply_ufunc(duck_array_ops.where, …)`), and
— pre-patch — produces a result whose attribute mapping is always empty. The
gold patch adds a `keep_attrs` parameter governing whether the result keeps the
attribute mapping of `x` (its second positional operand).

## 2. Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | notes |
|---|---|---|
| `cond` (bool array, 1-D) | `cond : List Bool` | one entry per cell |
| `x` (numeric array, 1-D) | `x : List Int` | the "true" operand values |
| `y` (numeric array, 1-D) | `y : List Int` | the "false" operand values |
| `x.attrs` (`dict`) | `xAttrs : List (String × String)` | association list; `{}` ↔ `[]` |
| `keep_attrs` arg (`None`/`True`/`False`) | `keepAttributes : Option Bool` | `None↔none`, `True↔some true`, `False↔some false` |
| `_get_keep_attrs(default=False)` return | `globalKeepDefault : Bool` | the resolved global option value |
| result `DataArray` | `WhereResult` structure | `.values : List Int`, `.attrs : List (String × String)` |
| result `.values` | `out.values` | elementwise selection |
| result `.attrs` | `out.attrs` | `xAttrs` if kept, else `[]` |

Modeling rationale: the gold change is purely about attribute propagation and
the boolean/option flag governing it; the cell values are computed by an
**unchanged** callee. Numeric cells are modeled as `Int` (the elementwise
select copies a value unchanged — its dtype/precision is irrelevant to the
modeled branch; `np.where` selection is order/identity, never arithmetic).
1-D lists model the shape that the F2P test exercises (`dims="x"`); broadcasting
is orthogonal to the attrs fix and is not modeled (the unchanged callee owns it).

## 3. Callee provenance + flag dependencies

| callee | changed? | handling | gate |
|---|---|---|---|
| `duck_array_ops.where(cond, x, y)` (→ `np.where`) | NO | deep model `whereSelect` (front-recursive elementwise select) — **A-reference** | G-AX: `whereSelect == np.where` over equal-length int arrays |
| `_get_keep_attrs(default=False)` (`xarray/core/options.py:107`) | NO | its return modeled as the boolean input `globalKeepDefault` — **R** (callee-result-as-input) | G-CONF bridges: real call returns `globalKeepDefault` |
| `apply_ufunc(… keep_attrs=…)` attrs merge (`merge_attrs`, `xarray/core/merge.py:516`) | NO (consumer of the new flag) | modeled by the result `.attrs` predicate: kept iff the resolved flag is truthy; `keep_attrs=True` ⇒ the gold lambda `attrs[1]` ⇒ `x.attrs` | G-CONF (R/I shadow vs patch.diff) |

**Flag dependency (the heart of the fix).** Attribute propagation is governed by
the *resolved* keep flag:
- `keep_attrs is None` → resolved to `_get_keep_attrs(default=False)` (under
  default global options this is `False`);
- resolved-truthy (`keep_attrs=True`, or global option `True`) → the gold
  combiner `lambda attrs, context: attrs[1]` returns `attrs[1]` = the attribute
  mapping of the **second positional operand** `x` (objs order is `cond, x, y`);
- resolved-falsy (`False`) → `merge_attrs(..., "drop")` returns `{}` (empty).

So `out.attrs = if (keepAttributes.getD globalKeepDefault) then xAttrs else []`.
G-AX fuzzes `np.where` for the value leg; G-CONF fuzzes the full attrs decision
against the gold patch over `None/True/False × empty/non-empty attrs`.

## 4. G-CONF fuzz seed

`seed = 4687` (pinned; used by conformance_check.py).
