# mapping.md — pydata__xarray-4695

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 51ef2a66c4e0896eab7d2b03e3dfb3963e338e3c`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
Python argument-binding semantics the deep model is validated against).

Repo file under change: `xarray/core/dataarray.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `forward_axis_names(names, values)` | `_LocIndexer.__getitem__(self, key)` — `xarray/core/dataarray.py:194` (changed line 198) | the *axis-forwarding* aspect of the modeled changed function: which mapping entries reach the underlying selector as axis indexers |
| `bound_reserved_option(names, values)` | `_LocIndexer.__getitem__(self, key)` — same site, same line | the *reserved-option* aspect of the same one-line change: what value the underlying selector's reserved option (`method`) ends up bound to |
| `RESERVED_NAME()` | a reserved keyword-parameter name of `DataArray.sel` — `method` (`xarray/core/dataarray.py:1118`, signature line 1121) | pure spec: the axis-name id that collides with a reserved option name |
| `DEFAULT_OPTION()` | `DataArray.sel`'s default for `method` — `None` (`xarray/core/dataarray.py:1121`, `method: str = None`) | pure spec: the unset sentinel of the reserved option |
| `option_after_namekeyed(names, values)` | the value `method` would receive under `sel(**key)` keyword binding (the pre-fix routing) | pure spec: name-keyed routing of a colliding axis into the reserved slot; used only by the pre-patch skeletons |

The single changed line:

```
- return self.data_array.sel(**key)     # pre-fix: splat the mapping into kwargs
+ return self.data_array.sel(key)       # fix:    pass the mapping positionally
```

`key` is the dict `{dim_name: label}` built (when `key` is not yet dict-like)
from `dict(zip(self.data_array.dims, labels))`, or the user-supplied dict
directly. `DataArray.sel` has the signature

```
sel(self, indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs)
```

(`xarray/core/dataarray.py:1118-1124`). The dispatch helper that merges the
positional `indexers` with the keyword `indexers_kwargs` is
`xarray.core.utils.either_dict_or_kwargs` (`xarray/core/utils.py:254-273`),
which returns `pos_kwargs` if given, else `kw_kwargs`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the indexer mapping `key: Dict[Hashable, Any]` | a parallel pair `names: List[int]`, `values: List[int]` (`len(names) == len(values)`) | `names[k]` ↔ the k-th dimension name (`Hashable` → opaque int id); `values[k]` ↔ that dimension's label selector (opaque int id ≥ 0); insertion order ↔ list order |
| dimension name `"method"` (or any reserved-option name) | `RESERVED_NAME() == 7` | the one axis-name id that equals a reserved keyword-parameter name of `sel` |
| `method=None` default of `sel` | `DEFAULT_OPTION() == -1` | the unset sentinel; distinct from every label-selector value (selectors are `>= 0`), so it cannot be confused with a forwarded value |
| the axis indexers `sel` actually receives (after `either_dict_or_kwargs`) | the `List[int]` returned by `forward_axis_names` (the forwarded axis-name sequence) | positional forwarding ⇒ the whole mapping; keyword splat ⇒ the mapping minus reserved-named entries |
| the value bound to `sel`'s `method` parameter | the `int` returned by `bound_reserved_option` | positional forwarding ⇒ `None` (`DEFAULT_OPTION`); keyword splat ⇒ the colliding entry's value |

`dict`/`str` keys/iteration are banned/awkward in Nagini, so the mapping is
carried as two parallel `List[int]` and the specification is phrased over
`PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom** in this bundle. The changed
operation — how the indexer mapping is *routed* to the underlying selector — is
the very thing the patch fixes, so it is modelled **deeply** (the verified
loops in `forward_axis_names` / `bound_reserved_option` and the pure
`option_after_namekeyed`), and validated against the **real Python
argument-binding semantics** out-of-band.

**Reference behaviour:** Python's call semantics for
`sel(indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs)`
under the dispatch helper `either_dict_or_kwargs`:

* `sel(key)` (the **gold** call) binds `key` to the positional `indexers`
  parameter; `indexers_kwargs` is empty; `either_dict_or_kwargs(key, {}, …)`
  returns `key`. So **every** mapping entry is an axis indexer and the reserved
  options (`method`/`tolerance`/`drop`) keep their defaults — independent of any
  collision between a dimension name and an option name.
* `sel(**key)` (the **pre-fix** call) splats the mapping into keywords. An entry
  whose name equals a reserved parameter (`method`, `tolerance`, `drop`) binds
  to that parameter; the rest land in `indexers_kwargs`. `indexers` is `None`,
  so `either_dict_or_kwargs(None, indexers_kwargs, …)` returns
  `indexers_kwargs` — the mapping **minus** the reserved-named entries — and the
  reserved option is **polluted** with the colliding entry's value. (In the
  issue, dimension `method='a'` becomes the fill-`method` of pandas
  `Index.get_loc`, which rejects `'a'`.)

**Provenance:** `xarray/core/dataarray.py:1118-1124` (the `sel` signature with
`method`/`tolerance`/`drop` defaults); `xarray/core/utils.py:254-273`
(`either_dict_or_kwargs`); CPython call semantics for `**`-unpacking into a
function with explicit keyword parameters + `**kwargs`
(https://docs.python.org/3/reference/expressions.html#calls). The reserved
names that collide are exactly `sel`'s non-mapping parameters.

**Soundness check (G-AX):** `axiom_check.py` builds a `sel`-shaped callee with
this exact signature and a faithful local copy of `either_dict_or_kwargs`, then
asserts on boundary mappings (including the issue's `{'dim1':'x','method':'a'}`,
an axis literally named `method`, and all three reserved names colliding) plus
20 000 randomized fuzz mappings that: the positional call forwards the whole
mapping and leaves all reserved options at their defaults (== model.py's
`forward_axis_names`/`bound_reserved_option`), while the keyword-splat call
drops reserved-named axes and binds them to the option slots (== the pre-patch
skeletons / `option_after_namekeyed`). It imports nothing repo-specific. Exit 0
iff the deep model is faithful.
