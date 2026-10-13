# mapping.md — pydata__xarray-4695

## Symbol binding (file:line @ base_commit 51ef2a66c4e0896eab7d2b03e3dfb3963e338e3c)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_labelSelection` / `problem_spec_labelSelection` / `correct_labelSelection` | `_LocIndexer.__getitem__` (the construction of the underlying `.sel(...)` call from the indexer mapping `key`) | `xarray/core/dataarray.py:194-199` |
| `SelArgs` (pure helper) | the argument bundle handed to `DataArray.sel(indexers, method, tolerance, drop, **indexers_kwargs)` | `xarray/core/dataarray.py:1118-1125` (the `sel` signature) |
| `Label` (pure helper, `:= String`) | a single tick-label value supplied for one dimension (the dict *value*) | label-agnostic; routing never inspects the value |
| `canonicalSelArgs` (pure helper) | the argument bundle the POST-PATCH line builds: the whole mapping passed positionally as `indexers`, all optional parameters left at their defaults | `xarray/core/dataarray.py:199` (post-patch) |

## What the function does (base_commit)

`_LocIndexer.__getitem__` resolves the user's `.loc[...]` key into a dict
`key : {dim_name → label}` (the `not is_dict_like` branch expands a positional
indexer and zips it with `self.data_array.dims`; a dict key is used as-is). It
then delegates to the data array's label-based selection:

```python
def __getitem__(self, key) -> "DataArray":
    if not utils.is_dict_like(key):
        labels = indexing.expanded_indexer(key, self.data_array.ndim)
        key = dict(zip(self.data_array.dims, labels))
    return self.data_array.sel(**key)        # <-- base_commit (buggy)
```

The selection routine has the signature

```python
def sel(self, indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs):
    indexers = either_dict_or_kwargs(indexers, indexers_kwargs, "sel")
    ...
```

Splatting the mapping with `**key` turns every dimension name into a *keyword
argument*. A dimension whose name collides with one of the reserved keyword
parameters — `method`, `tolerance`, `drop` (and `indexers`) — therefore binds to
that parameter instead of landing in `indexers_kwargs`. The issue's
`dict(dim1=..., method=...)` binds `method="a"`, which is later validated as a
fill method and raises `ValueError: Invalid fill method`. Only dimension names
that do *not* collide reach `indexers_kwargs` and are used as selectors.

### The fix

```python
return self.data_array.sel(key)              # post-patch
```

The mapping is passed *positionally* as `indexers`. `either_dict_or_kwargs`
returns it verbatim (no `**` expansion), so every dimension — including one named
`method`/`tolerance`/`drop` — is used as a selector, and no optional parameter is
ever populated from the mapping.

## Lean modeling

The patched line constructs the call to the (unchanged) selection routine. We
model its observable output as the **argument bundle** `SelArgs`:

- `indexers : List (String × Label)` — the dimension→label pairs that become the
  selection mapping (the `indexers` argument);
- `method`, `tolerance`, `drop : Option Label` — the optional matching parameters
  (`none` = left at default / not supplied from the mapping).

`canonicalSelArgs key` is the post-patch bundle: `indexers := key`, every optional
parameter `none`. The post-patch impl returns exactly this. The pre-patch
(`Solution_prepatch.lean`) impl mirrors `**key` splatting: it iterates the mapping
and routes any entry whose name is a reserved keyword parameter (`method` /
`tolerance` / `drop`) into that slot, dropping it from `indexers`; non-colliding
entries accumulate into `indexers`. For any mapping containing such a name the
two bundles differ, so the carried-over gold proof cannot close (G-DIFF).

The downstream selection routine (`sel`) is UNCHANGED by the patch and out of
scope; the fix lives entirely in how its arguments are built. Correct argument
construction ⟹ correct selection, because `sel` is correct given the right
arguments.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| the indexer mapping `key` (`{dim → label}`) | `List (String × Label)` | dict ↔ association list; key string ↔ `String`, value ↔ `Label` |
| a single tick-label value | `Label` (`:= String`) | label modeled by its representation; routing is value-agnostic |
| the `indexers` argument finally passed to `sel` | `SelArgs.indexers` | identity (association list) |
| `method` keyword argument | `SelArgs.method : Option Label` | `None`/absent ↔ `none`; supplied label ↔ `some` |
| `tolerance` keyword argument | `SelArgs.tolerance : Option Label` | `None`/absent ↔ `none`; supplied label ↔ `some` |
| `drop` keyword argument | `SelArgs.drop : Option Label` | default ↔ `none`; supplied label ↔ `some` |

The reserved keyword-parameter names modeled as collision-prone are
`{"method", "tolerance", "drop"}` — the keyword-only matching parameters of the
selection routine, which the issue demonstrates (`method`). A dimension literally
named `"indexers"` additionally triggers a positional/keyword `ValueError`; that
pathological case is outside the modeled scope and noted here for completeness —
the spec already discriminates the demonstrated bug.

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The fix is the construction of
  the selection arguments, modeled DEEPLY and structurally over the input mapping
  (`canonicalSelArgs`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed decision. The `axioms` region is empty; **G-AX skips**.
- `either_dict_or_kwargs` (the routine that, post-patch, returns the positional
  mapping verbatim) and the downstream `sel` body are UNCHANGED and orthogonal to
  the fix; their behavior is not separately modeled — the spec pins the full
  `SelArgs` bundle that is handed to them.

## G-CONF fuzz seed

Pinned LCG seed: **4695** (see `conformance_check.py` `SEED`). Corpus: randomized
indexer mappings over dimension names drawn from a pool that includes the
reserved keyword-parameter names (`method`, `tolerance`, `drop`) and ordinary
names, with random label values, plus hand-picked edge cases: the F2P mapping
(`{dim1 → ..., method → ...}`), mappings with `tolerance`/`drop` names, and
collision-free mappings. The R/I shadow of `implementation_labelSelection` is
diffed against an in-process replica of the POST-PATCH construction
(`canonicalSelArgs`) over ≥1e5 fuzzed inputs.
