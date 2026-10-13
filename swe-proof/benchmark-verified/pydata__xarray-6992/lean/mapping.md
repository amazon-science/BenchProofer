# mapping.md — pydata__xarray-6992

## Symbol binding (file:line @ base_commit 45c0a114)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_resetIndexCoords` | `Dataset.reset_index` (coordinate/variable/index bookkeeping) | `xarray/core/dataset.py:4108–4182` (post-patch `:4108–…`) |
| `removeAll xs ys` | set-difference `{k … if k not in <set>}` dict/coord-name comprehensions | `dataset.py` reset_index assembly |
| `ResetResult.coordNames` | `coord_names` passed to `_replace_with_new_dims` | `dataset.py:4222` (post-patch) |
| `ResetResult.varNames` | keys of `variables` dict | `dataset.py:4217–4221` |
| `ResetResult.indexNames` | keys of `indexes` dict | `dataset.py:4214` |
| (A-reference) per-name index coord set | `self.xindexes.get_all_coords(name)` | `xarray/core/indexes.py:1111–1140` |

## Modeled function

`Dataset.reset_index(dims_or_levels, drop)` — restricted to the domain where
every reset target is a **single (non-multi) dimension index** whose only
associated coordinate is the target name itself (i.e.
`get_all_coords(name) == {name}` and the index is a plain `PandasIndex`, not a
`PandasMultiIndex`). This is the domain of the MVCE's final reset and of the
F2P `test_reset_index_drop_dims` / single-index assertions in
`test_reset_index` / `test_reset_index_keep_attrs`.

In that domain the loop body reduces to:

```
idx_var_names = {name}             # get_all_coords(name)
drop_indexes  |= {name}
# else-branch of the multi/non-multi switch: drop_or_convert({name})
if drop:  drop_variables |= {name}
else:     new_variables[name] = base var   # convert, name retained
```

followed by the post-patch final assembly:

```
indexes      = {k:v in self._indexes if k not in drop_indexes}
variables    = {k:v in self._variables if k not in drop_variables}; variables.update(new_variables)
coord_names  = self._coord_names - drop_variables
```

## Type bijection (used by G-CONF / G-AX)

| Lean | Python |
|---|---|
| `String` (a coordinate/variable/dimension name) | a `Hashable` dataset key (coordinate name) |
| `List String` `varNames` | ordered keys of `Dataset._variables` |
| `List String` `coordNames` | `Dataset._coord_names` (a set; order via `_variables`) |
| `List String` `indexNames` | keys of `Dataset._indexes` |
| `List String` `resetNames` | normalized `dims_or_levels` |
| `Bool drop` | `drop` keyword arg |
| `removeAll xs ys = xs.filter (¬ ys.contains ·)` | `{k for k in xs if k not in set(ys)}` (order-preserving) |

G-CONF anchors fidelity by constructing real `xr.Dataset`s whose coordinates are
exactly dimension coordinates (each its own single `PandasIndex`), calling the
real (gold-patched) `reset_index`, and reading
`set(result._coord_names)`, `set(result._variables)`, `set(result.xindexes)`.

## Callee provenance + flag deps

- `xindexes.get_all_coords(name, errors="ignore")` — UNCHANGED callee. In the
  modeled domain (single dimension index) it returns exactly `{name}`. Modeled
  DEEPLY as the literal `{name}` singleton (A-reference, not a consumed axiom).
- `to_base_variable()` — UNCHANGED callee; in the convert branch it changes the
  variable *kind* (IndexVariable → Variable) but NOT its name, so it is identity
  on the name-set abstraction (documented; no separate axiom consumed).
- `drop` flag: governs the drop-vs-convert branch (`drop_or_convert`). G-CONF
  fuzzes both `drop=True` and `drop=False`.

## Set abstraction + input-domain assumptions (faithfulness)

- **Duplicate-free name collections.** A real `Dataset`'s `_variables`,
  `_coord_names`, `_indexes` keys are duplicate-free (they are dict keys / a set).
  The Lean model uses `List String` with `removeAll = List.filter`, which on
  `Nodup` inputs corresponds EXACTLY to set difference and preserves `Nodup`.
  G-CONF therefore reads the real object via `set(...)` and compares against a
  set-based shadow — the list order/multiplicity of the Lean model is immaterial
  to the modeled result, and the list model faithfully refines the set
  abstraction the bijection above declares.
- **Reset-target domain.** `reset_index` first raises on any target not in
  `self._indexes`, so every `name ∈ resetNames` is a live index name; in the
  plain-single-index slice `name` is also a dimension coordinate, hence present
  in `_variables` and `_coord_names`. This is exactly the condition under which
  the pre-patch `set(new_variables) | self._coord_names` collapse leaves the
  dropped name lingering in `coord_names` (the bug). `conformance_check.py`
  (`build_dataset` + `domain_ok`) constructs only datasets meeting this
  condition, so the differential test exercises the discriminating branch.

## Domain restriction (faithfulness scope)

The multi-index level branch (`isinstance(index, PandasMultiIndex)` →
`keep_levels` / `droplevel` / level renaming) is OUT of the modeled domain. It is
a separate behavior over the pandas MultiIndex level machinery; the modeled
single-index branch is the discriminating slice that exhibits the reported
invariant violation (the MVCE's terminal `reset_index("z", drop=True)` produces
single indices). Recorded in meta.json `modeled_domain`.

## Pinned G-CONF fuzz seed

`SEED = 6992` (also hard-coded in conformance_check.py).
