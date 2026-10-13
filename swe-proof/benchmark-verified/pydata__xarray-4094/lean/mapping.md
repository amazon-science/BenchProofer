# mapping.md — pydata__xarray-4094

## Symbol binding (@ base_commit a64cf2d5476e7bbda099b34c40b7be1880dbd39a)
- Modeled function: `DataArray.to_unstacked_dataset(self, dim, level=0)`
  — `xarray/core/dataarray.py:1900` (the changed loop is at `:1961-1963`).
- The single changed line (`xarray/core/dataarray.py:1962`):
  ```python
  -            data_dict[k] = self.sel({variable_dim: k}).squeeze(drop=True)
  +            data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)
  ```
- Surrounding (unchanged) context the loop depends on:
  - `idx = self.indexes[dim]`; `variables = idx.levels[level_number]`;
    `variable_dim = idx.names[level_number]` — produce the list of variable
    labels (`vars` in Lean) and the name of the level coordinate.
  - `return Dataset(data_dict)` — recombine the per-label slices into a dataset.
- Callee provenance (unchanged outside callees the fix uses):
  - `DataArray.sel(indexers, drop=...)` — `xarray/core/dataarray.py:1068`.
    `drop` defaults to `False`; when `True` the selected scalar coordinate
    (here `variable_dim`) is dropped instead of being retained as a scalar
    coordinate on the result.
  - `DataArray.squeeze(drop=True)` — `xarray/core/common.py:343` (inherited),
    removes length-1 dimensions. UNCHANGED by the patch (present on both sides).

## The bug
After `sel({variable_dim: k})` WITHOUT `drop=True`, each extracted slice keeps
`variable_dim` as a scalar coordinate equal to `k`. When `Dataset(data_dict)`
recombines the slices, each slice carries a *different* scalar value for
`variable_dim`, so xarray's merge sees conflicting values for that coordinate and
raises `MergeError`. With a single sample dimension there is nothing else for the
slices to align on, so the round-trip fails (issue MCVE). Adding `drop=True`
drops the `variable_dim` scalar coordinate from each slice, so recombination has
no conflict.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)
| Lean | Python |
|---|---|
| `κ` (variable label type) | a label `k` drawn from `idx.levels[level_number]` |
| `ν` (extracted slice type) | the `DataArray` slice stored as `data_dict[k]` |
| `vars : List κ` | `variables` (`idx.levels[level_number]`, iterated in order) |
| `extractSlice : Bool → κ → ν` | `λ mode k. self.sel({variable_dim: k}, drop=mode).squeeze(drop=True)` |
| `extractSlice true k` | `self.sel({variable_dim: k}, drop=True).squeeze(drop=True)` (post-patch) |
| `extractSlice false k` | `self.sel({variable_dim: k}).squeeze(drop=True)` (pre-patch / buggy) |
| `result : List (κ × ν)` | `data_dict` (the `{label: slice}` mapping → `Dataset(data_dict)`) |

The `mode : Bool` first argument of `extractSlice` models the `drop` keyword of
`sel`: `true ↔ drop=True` (label-removing extraction), `false ↔ drop=False`
(label-retaining extraction, the default). The fix is exactly the move from
`extractSlice false k` to `extractSlice true k`. `squeeze(drop=True)` is folded
into `extractSlice` (unchanged on both sides, never affects the discriminator).

## Callee provenance + flag dependency
- `extractSlice` is left UNIVERSALLY QUANTIFIED (no `opaque`/`axiom`); the proof
  consumes no property of it. The fix's behavioral content is entirely the
  `drop` mode that reaches each extraction, plus the order/structure of the
  result list. Recorded as an **A-reference** (refinement.md op #2), bound to the
  real `sel(...).squeeze(...)` callee in G-CONF — NOT axiomatized.
- Flag dependency: `sel`'s `drop` flag is the discriminator G-CONF must exercise;
  it builds the shadow with `drop=True` (the resolved mode) against the real
  patched `to_unstacked_dataset`.

## G-CONF fuzz seed
Pinned seed `4094` (`random.Random(4094)` / `np.random.RandomState(4094)`).
