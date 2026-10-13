# mapping.md — pydata__xarray-4094

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a64cf2d5476e7bbda099b34c40b7be1880dbd39a`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo file under change: `xarray/core/dataarray.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `toComponents (selDim, sampleCoords, vars)` | `DataArray.to_unstacked_dataset(self, dim, level=0)` — `xarray/core/dataarray.py:1901` (the per-component build loop, body lines 1962–1967) | the modeled changed function: reassemble a combined array into its labeled components |
| `vars : List String` | `variables = idx.levels[level_number]` — `dataarray.py:1959` (the component labels in the stacked MultiIndex level) | the ordered component labels iterated by `for k in variables` (`dataarray.py:1963`) |
| `selDim : String` | `dim` — the `to_unstacked_dataset(self, dim, ...)` argument (`dataarray.py:1901`), i.e. the stacked dimension being indexed (e.g. `"y"`) | the transient selector label: `self.sel({variable_dim: k})` selects a point along dimension `dim`, leaving a scalar coordinate **named `dim`** behind on each component unless `drop=True` removes it. (The selection KEY is `variable_dim`, but the residual coordinate is named after the indexed dimension `dim` — confirmed by axiom_check.py / G-AX.) |
| `sampleCoords : List String` | the coordinate names shared by every extracted component (the `sample_dims` carried through `to_stacked_array`, e.g. `["x"]`) | the per-component coordinate-name set that must survive extraction unchanged |
| `sliceCoords selDim sampleCoords keep` *(deep model — A-reference)* | `self.sel({variable_dim: k}, drop=…).squeeze(drop=True)` — `dataarray.py:1964` | pure spec: the coordinate-name set carried by one extracted component; `keep=false` ⇔ `drop=True` (selector label discarded), `keep=true` ⇔ default `drop=False` (selector label retained). Validated against the real extractor by axiom_check.py (G-AX), NOT consumed as an axiom |
| `expectedComponents sampleCoords vars` *(pure)* | the `data_dict` built by the loop, then `return Dataset(data_dict)` (`dataarray.py:1962–1967`) | pure spec: each label paired with the coordinate-name set its component carries |

The flag that this change toggles is the `drop` keyword of `DataArray.sel`
(`xarray/core/dataarray.py`, `sel(..., drop=False)` by default). `drop=True`
discards the scalar coordinate created by the point-selection on `variable_dim`;
`drop=False` (pre-patch) leaves it behind as a residual scalar coordinate.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the component labels `variables` (a pandas `Index` of `object`/`str`) | `List String` (`vars`) | label `k` ↔ its name string; order preserved; `len(variables)` ↔ `vars.length` |
| the level name `variable_dim` (a `str`) | `String` (`selDim`) | identity on the name string |
| the shared sample coordinate names | `List String` (`sampleCoords`) | each coordinate's name ↔ its string; set membership ↔ `List` membership |
| one extracted component `self.sel({variable_dim:k}, drop=…).squeeze(drop=True)` | `(k, coordNames)` where `coordNames : List String` | the component is abstracted to its **set of coordinate NAMES** — the only feature the bug affects and the F2P roundtrip observes (a residual `variable_dim` scalar coordinate is what causes the `MergeError` on reassembly). Data values, dtypes, and dim sizes are unchanged by `drop` and are out of scope. |
| `data_dict : dict[label -> DataArray]` then `Dataset(data_dict)` | `List (String × List String)` | `dict` key set ↔ `out.map Prod.fst`; one entry per label, in iteration order. `Dataset(...)` is conflict-free iff no two components carry conflicting values for a shared coordinate name — which the spec enforces by `selDim ∉ p.2` for every component. |

Modeling rationale: the observable that the gold patch changes is purely **which
coordinate names ride along on each extracted component**. With the default
(`drop=False`), the point-selection on `variable_dim` leaves a scalar coordinate
named `variable_dim` (`selDim`) on every component; when the single non-sample
dimension is the stacked one, `squeeze(drop=True)` cannot remove it (it is a
0-d coordinate, not a size-1 dimension), so all components share a conflicting
`selDim` coordinate and `Dataset(data_dict)` raises `MergeError`. `drop=True`
removes that scalar coordinate at selection time, so each component carries only
`sampleCoords` and reassembly succeeds. The Lean model abstracts each component
to its coordinate-name list; the bug is exactly `selDim ∈ coords` vs not.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `sliceCoords` deep model ↔ `DataArray.sel(..., drop).squeeze(drop=True)` (A-reference)
**Callee:** `xarray.DataArray.sel({variable_dim: k}, drop=<flag>).squeeze(drop=True)`
(`xarray/core/dataarray.py:1964`). The component-extraction operation whose
behaviour the change toggles is modeled **deeply** by `sliceCoords` (pure
region); there is **no consumed axiom**. `sliceCoords` returns the set of
coordinate NAMES the extracted component carries:

- `keep = false` (gold, `drop=True`): the result is exactly `sampleCoords` — the
  transient selector label `selDim` is discarded.
- `keep = true` (pre-patch, `drop=False`): the result is `sampleCoords ++ [selDim]`
  — the selector label persists as a residual scalar coordinate.

**Soundness check (G-AX):** `axiom_check.py` constructs, in the real
SWE-Bench instance container, single-dimension stacked DataArrays (the GH4094
shape) plus randomized fuzz variants, runs the REAL
`stacked.sel({variable_dim:k}, drop=flag).squeeze(drop=True)` for `flag ∈
{True, False}`, and asserts:
- (A-reference, gold leg) with `drop=True`, the extracted component's coordinate
  names == `sampleCoords` (i.e. `sliceCoords … false`), and `selDim` is absent;
- (discriminator, pre-patch leg) with `drop=False`, the extracted component's
  coordinate names == `sampleCoords ++ [selDim]` (i.e. `sliceCoords … true`),
  and `selDim` is present — confirming the pre-patch model is faithful to the
  buggy behaviour;
- (roundtrip) with `drop=True`, reassembling `Dataset(data_dict)` succeeds and is
  `identical` to the original Dataset, whereas with `drop=False` it raises
  `MergeError`.

Imports only `numpy`/`xarray` (the repo under test). Exit 0 iff every obligation
holds.

### 3.2 Flag dependency
The behaviour modeled is dependent on the `drop` keyword of `DataArray.sel`
(default `False`). G-AX fuzzes BOTH configurations (`drop=True` = gold,
`drop=False` = pre-patch) so the discriminator is exercised, per SPEC_GUIDE §3
flag-dependent-callee guidance.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`4094`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`sliceCoords`/`expectedComponents` (R/I-tagged ops) to Python — extracting each
component's coordinate names with the gold `drop=True` semantics — and compares,
over single-dim and multi-dim stacked-array shapes, against the ORACLE: the real
patched `DataArray.to_unstacked_dataset` run at `base_commit` with `patch.diff`
applied, observed through each rebuilt component's coordinate-name set. There is
no A-tagged op in the impl region (`sliceCoords` is the A-reference deep model,
which G-CONF transliterates as an I-op), so `conf_skip = false`.
