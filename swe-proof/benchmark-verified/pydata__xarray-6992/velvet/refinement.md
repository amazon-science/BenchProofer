# refinement.md — pydata__xarray-6992

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`dropIndexNameSets` `do` block, computing the post-reset name-sets via the deep
model `computeNameSets`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-reference** (a deep model
validated == the real callee by G-AX), **A-consumed** (proof uses an axiom's
`ensures` — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg + this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — `Dataset.reset_index` name-set bookkeeping

The gold patch rewrites the `(variables, coord_names, indexes)` bookkeeping of
`reset_index` (`xarray/core/dataset.py:4108`). The bug: pre-patch
`coord_names = set(new_variables) | self._coord_names` only ever GREW the
coordinate name-set, so de-indexed names stayed coordinates while leaving
`_variables`, making `len(_variables) - len(_coord_names)` (`DataVariables.
__len__`, `dataset.py:367`) negative → `ValueError: __len__() should return >=
0`. The fix subtracts the dropped names from BOTH sets
(`coord_names = self._coord_names - drop_variables`) and renames a reduced
single level to its dimension.

| # | Solution.lean impl op (`dropIndexNameSets`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `isMulti, dim, levels, R, V, C, dropF : Bool/String/List String` | `self` (its `_variables`, `_coord_names`, `_indexes`), `dims_or_levels`, `drop`, the reset index's type/dim/levels | R | name-sets ↔ `List String`; flags ↔ `Bool`; mapping.md §2. All read-only (directive 5): the method declares no `mut` params and builds fresh sets; `ensures` pins `out` only, leaving `V`/`C`/… unconstrained-but-unmutated by construction (functional). |
| A2 | `dim`, `levels` = the index footprint `{dim} ∪ levels` | `self.xindexes.get_all_coords(name)` (`indexes.py:1111`), `index.dim`, `index.index.names` | A-reference | UNCHANGED neighbouring callee; the footprint the model consumes is validated == the real callee by axiom_check.py (G-AX, mapping.md §4.1). |
| A3 | non-multi branch: `dropF ? mk [dim] [] [] : mk [] [dim] []` | `else: drop_or_convert(idx_var_names)` with `idx_var_names = {dim}`, then `coord_names = _coord_names - drop_variables` | I | single index: its sole coord `dim` is dropped (drop) or kept as a base variable but removed from coords (convert); no index survives. Concrete list bookkeeping, transliterated by G-CONF. |
| A4 | multi, ≥1 kept level, dim not requested, exactly 1 kept: `dropF ? mk (keep++reset) [dim] [dim] : mk keep ([dim]++reset) [dim]` | `keep_level_vars` size-1 path: `keep_levels` → `PandasIndex(index.rename(self.dim), …)` (`indexes.py:720`), `if not isinstance(idx, PandasMultiIndex): drop_variables.update(keep_level_vars)`, `drop_or_convert(reset levels)` | I | the single-level-reduction RENAME (kept level coord → `dim`): old kept-level name removed from vars/coords, new coord `dim` added, surviving index keyed `[dim]`. Modeled deeply; refuted vs real by G-CONF. |
| A5 | multi, ≥1 kept level, dim not requested, >1 kept: `dropF ? mk reset keep (keep++[dim]) : mk [] (keep++reset) (keep++[dim])` | `keep_level_vars` size>1 path: rebuilt `PandasMultiIndex` on kept levels (names unchanged), `drop_or_convert(reset levels)` | I | multi-index rebuilt on the kept levels; surviving index keys = kept levels **plus the dimension** `dim` (empirically `idxs = keep ∪ {dim}`; mapping.md §3 probe row `reset 'a'` → `[b,c,x]`). Deep, transliterated by G-CONF. |
| A6 | multi, dim requested OR 0 kept: `dropF ? mk (dim::levels) [] [] : mk [dim] levels []` | the `else` of `index.dim not in dims_or_levels and keep_level_vars`: `drop_variables.add(index.dim)`, `drop_or_convert(level_names)`, no surviving index | I | whole multi-index removed: dimension variable always dropped; levels dropped (drop) or converted to base vars (convert, kept in vars / removed from coords). Deep, transliterated by G-CONF. |
| A7 | `mk dv nv ni = {vars := filterOut dv V ++ nv, coords := filterOut dv C, idxs := ni}` | `variables = {k:v for … if k not in drop_variables} | new_variables`; `coord_names = self._coord_names - drop_variables`; `indexes = {… not in drop_indexes} | new_indexes` | I | THE FIX: the same drop-set `dv` (`= drop_variables`) is subtracted from BOTH `V` and `C` (`filterOut dv V`, `filterOut dv C`), restoring `coords ⊆ vars` (`subsetPreserved`). `nv` ↔ `new_variables`; `ni` ↔ surviving + new index keys. |

`drop_or_convert(var_names)` (gold helper): `drop=True` → `drop_variables.update`
(removed from both sets); `drop=False` → `new_variables.update(base_vars)` (the
converted base variables, kept in vars, absent from `coord_names` after the
subtraction). The model's drop-vs-convert is exactly the `dropF` split in A3–A6.

## B. The sibling sites — `set_index`, `keep_levels`

`patch.diff` also fixes `Dataset.set_index` (`dataset.py:3968`) and
`PandasMultiIndex.keep_levels` (`indexes.py:705`). Both are the SAME structural
defect and the SAME fix as A: a name dropped from variables must be dropped from
coordinates (`set_index`'s `coord_names = self._coord_names - drop_variables |
set(new_variables)` with the symmetric `drop_variables` set), and a reduced
single level is renamed to the dimension (`keep_levels`'s `index.rename(self.
dim)`, consumed by `reset_index` A4). They are NOT separately modeled methods:
the modeled invariant `subsetPreserved` (every dropped name leaves both sets) and
the A4 rename ARE the property they enforce. No separate failing prepatch is
required for them — a prepatch must keep the spec byte-identical (G-DIFF), and
site A's prepatch already exercises the shared "coords never shrinks" bug that is
the issue's reported failure (the MVCE goes through `reset_index`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
name-set recomputation, including the single-level rename — is modeled **deeply**
(`computeNameSets`, the `subsetPreserved` theorem), not hidden behind an axiom
about the function under change. There are **no consumed axioms**. The only
kind-A obligation is the **A-reference** on the UNCHANGED `get_all_coords`
footprint (A2), validated by G-AX.

## D. verify(Solution) ⇒ resolved

`dropIndexNameSets` verifies only if `out = computeNameSets …` in every branch
(A3–A7), which (i) subtracts the de-indexed names from BOTH the variable and
coordinate sets — so `subsetPreserved` makes `coords ⊆ vars` hold for ALL inputs,
exactly the property `DataVariables.__len__` needs to stop returning negative
(the issue) — and (ii) renames a reduced single level to its dimension (A4). By R
(name-sets ↔ `List String`, set/list bridge, `to_base_variable` name-preserving)
the verified bookkeeping equals the gold patch's `(variables, coord_names,
indexes)` recomputation; by G-AX the footprint input equals the real
`get_all_coords` (A-reference); by G-CONF the R/I transliteration agrees with the
patched `reset_index`'s name-sets on ≥10⁵ inputs (every footprint subset × both
drop flags, exhaustively, over single / 2-level / 3-level indexes). The pre-patch
skeleton (`coord2 := C ++ newVars`, never shrinking) FAILS `out = computeNameSets`
(G-DIFF) on the discriminating coords clause — the actual bug. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited footprint callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
