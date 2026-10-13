# mapping.md — pydata__xarray-6992

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 45c0a114e2b7b27b83c9618bc05b36afac82183c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one deep-model reference.

Repo files under change: `xarray/core/dataset.py` (the `reset_index` and
`set_index` methods) and `xarray/core/indexes.py` (`PandasMultiIndex.keep_levels`).

The bundle models the **`reset_index`** name-set bookkeeping — the site the
issue's MVCE exercises (`…reset_index("z", drop=True)` produces a container whose
`len(_variables) - len(_coord_names)` goes negative, raising
`ValueError: __len__() should return >= 0`). `set_index` and `keep_levels` are
the same bug's siblings; their fix is the same structural rule (every name
dropped from variables is dropped from coordinates too, and a reduced single
level is renamed to the dimension), recorded in §1 / §4 as in-scope sibling
sites covered by the modeled invariant.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `dropIndexNameSets (isMulti dim levels R V C dropF)` | `Dataset.reset_index` — `xarray/core/dataset.py:4108` (bookkeeping body lines 4142–4182 pre-patch) | the modeled changed function: recompute the `(variables, coord_names, indexes)` name-sets after resetting one index |
| `computeNameSets …` *(pure spec)* | the post-patch bookkeeping of `reset_index` (`dataset.py:4142–4221` post-patch) | pure reference: the name-sets the fixed operation must produce |
| `NameSets {vars, coords, idxs}` | the three name-collections `_variables` / `_coord_names` / `_indexes` keys of the resulting `Dataset` | the touched fields of the rich `Dataset` object (structure with only the relevant fields) |
| `filterOut drop xs` | the `{k … for k … if k not in drop_*}` / `set - drop_variables` dict/set-difference idioms | pure spec: order-preserving removal of dropped names |
| *(deep model, A-reference)* `levels` = the index footprint passed in | `self.xindexes.get_all_coords(name)` — `xarray/core/indexes.py:1111` | the UNCHANGED neighbour that reports an index's full coordinate set `{dim} ∪ levels`; validated == real by axiom_check.py (G-AX) |
| `subsetPreserved` (theorem) | the structural property `DataVariables.__len__` (`dataset.py:367`) needs: `_coord_names ⊆ _variables` so `len(_variables) - len(_coord_names) ≥ 0` | the invariant whose violation is the reported bug |

The single-level-reduction rename (kept level coordinate renamed to the
dimension name) is the behaviour of `PandasMultiIndex.keep_levels`
(`xarray/core/indexes.py:705`, changed hunk `index.rename(self.dim)` at line
720) as consumed by `reset_index`; it is modeled DEEPLY inside `computeNameSets`
(the `keepLevels.length == 1` branch emits `newVars := [dim]`, `newIdx := [dim]`
and drops the old kept-level name) and is refuted against the real operation by
conformance_check.py (G-CONF), NOT axiomatized.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a coordinate / variable / index **name** (a `Hashable`, in practice `str`) | Lean `String` | opaque identifier; equality and membership only |
| `self._variables` keys (a `dict` keyset) | `V : List String` | order-preserving keyset; `len` ↔ `.length`; `k in vars` ↔ `k ∈ V` |
| `self._coord_names` (a `set[Hashable]`) | `C : List String` | membership only; the bug is `len(C) > len(V)` ↔ `¬(C ⊆ V)` |
| `self._indexes` keys after the op | `out.idxs : List String` | order-preserving keyset of the surviving/new indexes |
| `dims_or_levels` (the requested reset names) | `R : List String` | the request; `name in dims_or_levels` ↔ `R.contains name` |
| `isinstance(index, PandasMultiIndex)` | `isMulti : Bool` | the index being reset is a multi-index |
| the index's dimension name `index.dim` | `dim : String` | the dimension coordinate of the reset index |
| the index's level coordinate names `index.index.names` ( = footprint minus the multi-index dim) | `levels : List String` | for a non-multi index, `levels = []` and `dim` is its sole coordinate |
| the `drop=True/False` flag | `dropF : Bool` | `drop=True` ⇒ discard de-indexed coords; `drop=False` ⇒ convert them to base variables (kept in `vars`, removed from `coords`) |
| `Variable.to_base_variable()` (IndexVariable→Variable) | identity on the name | conversion changes the variable's *type*, not its name; the name-set bookkeeping (what this bundle models) is unaffected — the converted coord stays in `vars`, leaves `coords` |

`set`/`dict-keyset` carriers are modeled as `List String`: duplicate-freeness is
irrelevant to the membership predicates the invariant `coords ⊆ vars` and the
F2P assertions (`name not in reset.variables`, `len(obj.xindexes)`) observe, so a
plain `List String` with `∈`/`filter` semantics is a faithful, total model.

## 3. The fixed-vs-buggy bookkeeping (what the proof pins)

The post-patch `reset_index` computes (`dataset.py` post-patch):

```
drop_indexes  : set = the index footprint(s)          # which indexes vanish
drop_variables: set                                   # names removed from BOTH variables and coords
new_variables : dict                                  # rebuilt index vars / converted base vars
...
variables   = {k:v for k,v in self._variables if k not in drop_variables} | new_variables
coord_names = self._coord_names - drop_variables       # <-- the fix: subtract from coords too
return self._replace_with_new_dims(variables, coord_names, indexes)
```

The **pre-patch** code (the bug) computed `coord_names = set(new_variables) |
self._coord_names` — it only ever *added* to `coord_names` and never subtracted
the de-indexed names, so coordinate names could outnumber variable names and
`DataVariables.__len__` went negative. `Solution_prepatch.lean` reproduces this
(`coord2 := C ++ newVars`, never shrinking) and FAILS `out = computeNameSets …`
(G-DIFF).

`computeNameSets`'s eight `(isMulti, branch, dropF)` cases were checked against
the `test_reset_index_drop_convert` parametrization
(`test_dataset.py`, F2P) for a 2-level `MultiIndex` on `("foo","bar")` over
dim `x`:

| arg | drop | dropped | converted | renamed | computeNameSets branch |
|---|---|---|---|---|---|
| `foo` | F | — | — | `bar→x` | multi, 1 kept level (`bar`), dropF=F |
| `foo` | T | `foo` | — | `bar→x` | multi, 1 kept level, dropF=T |
| `x` | F | `x` | `foo,bar` | — | multi, dim requested ⇒ whole index goes, dropF=F |
| `x` | T | `x,foo,bar` | — | — | multi, dim requested, dropF=T |
| `[foo,bar]` | F | `x` | `foo,bar` | — | multi, 0 kept levels ⇒ whole index goes, dropF=F |
| `[foo,bar]` | T | `x,foo,bar` | — | — | multi, 0 kept levels, dropF=T |
| `[x,foo]` | F | `x` | `foo,bar` | — | multi, dim requested, dropF=F |
| `[foo,x]` | T | `x,foo,bar` | — | — | multi, dim requested, dropF=T |

(In each "dim requested or 0 kept" row the dimension variable `x` is always
dropped and the levels are dropped/converted; the rename row is the 1-kept-level
case, the only one emitting `newVars := [dim]`/`newIdx := [dim]`.)

## 4. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 4.1 `levels` footprint ↔ `Indexes.get_all_coords` (A-reference)
**Callee:** `xarray.core.indexes.Indexes.get_all_coords(key, errors=...)`
(`indexes.py:1111`), UNCHANGED by the patch. For an index keyed by `name` it
returns the dict of *all* coordinate variables sharing that index — i.e. the
full footprint `{dim} ∪ {level coordinate names}`. The model feeds this footprint
in as `dim` (the multi-index dimension) plus `levels` (the level coordinate
names); `drop_indexes`/`idx_var_names` in the real code is exactly this set.

**Soundness check (G-AX):** `axiom_check.py` builds real `xarray.Dataset`s
carrying single- and multi-indexes (boundary shapes: 1-level, 2-level, 3-level
multi-indexes, plain `PandasIndex`, repeated/disjoint indexes) plus randomized
fuzz, and asserts for every index key that
`set(get_all_coords(name)) == {index.dim} ∪ set(level names)` — i.e. the
footprint the model assumes equals the real callee's report. Imports only
`xarray`/`pandas`/`numpy` (in-container). Exit 0 iff sound.

### 4.2 No consumed axioms
There is no `axiom` whose `ensures` the proof consumes. The changed bookkeeping
(the `coord_names - drop_variables` rule, the rename of a reduced single level,
the drop-vs-convert split) is modeled deeply by `computeNameSets` and refuted
against the real patched `reset_index` by G-CONF (§5).

## 5. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`6992`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`computeNameSets` to Python over the real `Dataset` type: it constructs a real
`xarray.Dataset` for each fuzzed (index-shape, request, drop-flag) triple, runs
the patched `reset_index` (oracle, gold applied in-container), and compares the
oracle's resulting `(set(ds._variables), set(ds._coord_names),
list(ds._indexes))` name-sets against the shadow `computeNameSets` prediction
(bridged by §2). The A-tagged footprint callee `get_all_coords` is left as the
real repo callee inside the shadow (A leg stays with G-AX). Exit 0 iff zero
disagreements over ≥10⁵ inputs.
