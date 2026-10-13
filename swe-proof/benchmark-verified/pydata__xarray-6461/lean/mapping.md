# mapping.md — pydata__xarray-6461

## Symbol binding (base_commit 851dadeb0338403e5021c3fbe80cbc9127ee672d)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_whereAttrs` / `problem_spec_whereAttrs` | the `keep_attrs is True` attribute-resolution path of `where(cond, x, y, keep_attrs)` | `xarray/core/computation.py:1743-1845` (the `keep_attrs is True` block at `1829-1832`, plus its consumption inside `apply_ufunc`) |
| `objs := [cond, x, y].filter (·.isDarray)` | `objs = _all_of_type(args, DataArray)` — the labelled-array arguments in positional order | `apply_dataarray_vfunc` `computation.py:281`; `_all_of_type` at `computation.py:52-54`; here `args == (cond, x, y)` |
| the `keep_attrs is True` callback | `keep_attrs = lambda attrs, context: getattr(x, "attrs", {})` (the **fixed** line) | `computation.py:1832` |
| `if objs = [] then Except.ok none` | `merge_attrs(variable_attrs=[], …)` returns `None` (`if not variable_attrs: return None`) — the callback is never called | `xarray/core/merge.py:604-611`, invoked at `computation.py:311` |
| `Except.ok (some (attrsOf x))` | `merge_attrs([o.attrs for o in objs], combine_attrs=<callback>)` → `callback(variable_attrs, context)` → `getattr(x, "attrs", {})` | `merge.py:610` (`if callable(combine_attrs): return combine_attrs(...)`); callback body at `computation.py:1832` |

### Why `attrsOf x` is exactly `getattr(x, "attrs", {})`
The fixed callback ignores its `attrs`/`context` parameters entirely and returns
`getattr(x, "attrs", {})`: the attribute dict of the second positional argument
`x` if `x` is a labelled array (has an `.attrs`), or `{}` if `x` is a scalar
(no `.attrs`). That is precisely `attrsOf x` (`.darray a => a | .scalar => []`).

### Control flow of `keep_attrs is True` through `apply_ufunc`
`where` sets `keep_attrs` to the callback, then calls `apply_ufunc(..., cond, x,
y, keep_attrs=callback)`. `apply_ufunc` keeps a *callable* `keep_attrs` as-is
(the `isinstance(keep_attrs, bool)` branch at `computation.py:1132` does not fire
for a lambda), threads it as `combine_attrs` into `apply_dataarray_vfunc`, which
computes `objs = _all_of_type(args, DataArray)` and calls
`merge_attrs([x.attrs for x in objs], combine_attrs=callback)`. `merge_attrs`
short-circuits to `None` when `objs == []` (nothing to merge); otherwise it
invokes the callback, which returns `x`'s attrs. The result becomes the output
object's `.attrs`. This is the entire behavior the F2P test observes.

## Type bijection (G-CONF uses this)

| Python | Lean | notes |
|---|---|---|
| an argument that is a `DataArray` with attribute dict `d` | `Arg.darray d` | `d : List (String × String)` association list of `.attrs` |
| an argument that is a Python scalar (`int`/`float`/…) | `Arg.scalar` | no `.attrs` attribute |
| `_all_of_type((cond,x,y), DataArray)` | `[cond,x,y].filter (·.isDarray)` | order-preserving filter to the labelled args |
| `getattr(a, "attrs", {})` | `attrsOf a` | dict ↔ assoc list |
| `merge_attrs(...) is None` (no arrays) | `Except.ok none` | the "nothing to merge" outcome |
| `merge_attrs(...)` returns dict `d` | `Except.ok (some d)` | resolved attribute dict |
| (prepatch only) `IndexError` from `attrs[1]` | `Except.error ()` | out-of-range lookup raised |

A dict is compared by its key/value *set* (xarray attrs are an unordered
mapping); the shadow normalizes both sides to a sorted item list.

## Callee provenance / flag deps

The `keep_attrs is True` path is the only modeled configuration (the issue and
the F2P test exercise exactly `keep_attrs=True`). The `keep_attrs is None`
default-resolution (`_get_keep_attrs`) and the non-`True` callable/str paths are
outside the modeled behavior and not represented. No unchanged callee is
axiomatized: both `_all_of_type` (positional filter) and the `merge_attrs`
empty/callable short-circuit are modeled deeply. → no `opaque`/`axiom` decls;
`axiom_check.py` is a skip stub.

## G-CONF fuzz seed (pinned)

`seed = 6461` (used in `conformance_check.py`). Dimensions fuzzed: each of
`cond, x, y` independently a scalar or a `DataArray` with a random small attr
dict; `keep_attrs=True`; ≥10⁵ cases. Oracle = the patched `xr.where(...).attrs`
vs. the shadow of `implementation_whereAttrs`.
