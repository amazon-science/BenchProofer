# mapping.md — pydata__xarray-6992

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 45c0a114e2b7b27b83c9618bc05b36afac82183c`, states the type
abstraction, and gives the provenance of the deep model that G-AX validates.

Repo files under change: `xarray/core/dataset.py`, `xarray/core/indexes.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `promote_to_index(...)` | `Dataset.set_index` — `xarray/core/dataset.py:3968` (post-state recomputation, body lines 4028-4106) | modeled changed function (site 1): the name-collection recomputation that turns names into a dimension index |
| `teardown_index(...)` | `Dataset.reset_index` — `xarray/core/dataset.py:4108` (post-state recomputation, body lines 4142-4182) | modeled changed function (site 2): the name-collection recomputation that removes an index, splitting each affected name into dropped / converted (to a base variable) / replacement-index fates |
| `well_formed(variables, coord_names, indexes, index_repr)` | the structural invariant of a `Dataset` that `DataVariables.__len__` (`xarray/core/dataset.py:367-368`) relies on | pure spec: the container is well-formed (the three subset clauses) |
| `subset(a, b)` | `set` subset (`a <= b` / `a - b == ∅`) used throughout the two methods | pure spec helper |
| `disjoint(a, b)` | the disjointness of the three teardown fates (`drop_variables`, the converted base vars, the replacement index coords) in `reset_index` | pure spec helper |

The pre-patch repo symbols and the supporting callee (audited, not referenced
from the consumer spec view):
* `DataVariables.__len__` (`dataset.py:367`): `len(self._dataset._variables) -
  len(self._dataset._coord_names)`; goes negative — the reported
  `ValueError: __len__() should return >= 0` — exactly when `_coord_names` is
  not a subset of `_variables`.
* `PandasIndex.keep_levels` (`indexes.py:705`): the helper the multi-index
  teardown path calls; the gold also patches it to rename the surviving single
  level to the dimension name. Its effect on the name collections (a renamed
  replacement index coordinate) is captured by `new_index_vars` in
  `teardown_index` and exercised by axiom_check.py.
* `Index.get_all_coords` (`indexes.py:1111`): returns all coordinate names that
  share an index; used to compute the displaced index coordinates
  (`displaced_index_coords`) in `set_index` and the torn-down coordinates
  (`dropped_coords`) in `reset_index`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self._variables` (`dict[Hashable, Variable]`) | `variables0: PSet[int]` of name ids | a name `k` ↔ an integer id; `k in self._variables` ↔ `id(k) in variables0`; the model tracks only the KEY SET (membership), which is all `DataVariables.__len__` and the repr-breaking invariant observe |
| `self._coord_names` (`set[Hashable]`) | `coord_names0: PSet[int]` | name-set membership; the repo's `self._coord_names - set(drop_variables) | set(new_variables)` ↔ `(coord_names0 - drop_variables) + new_variables_all` |
| `self._indexes` (`dict[Hashable, Index]`) keyset | `indexes0: PSet[int]` | the names that carry an index; `{k for k,v in self._indexes.items() if k not in drop_indexes}` ↔ `indexes0 - displaced_index_coords` etc. |
| the array KIND `isinstance(self._variables[k], IndexVariable)` | `index_repr0: PSet[int]` | a coordinate is in `index_repr` iff its stored array is an `IndexVariable` (the index-backed representation); `.to_base_variable()` conversion ↔ removing the name from `index_repr` |
| `var_names` (the names promoted to the new index) | `promoted_names: PSet[int]` | the `all_var_names` accumulated in the gold `set_index` loop |
| `idx_vars` (the new index's coordinate variables) | `new_index_vars: PSet[int]` | the keys of `new_variables` produced by `PandasIndex/PandasMultiIndex.create_variables`; always a superset of the promoted names |
| `current_coord_names` / `index_coord_names` (the displaced pre-existing index coords) | `displaced_index_coords: PSet[int]` | `get_all_coords(dim)` ∪ `get_all_coords(k)` for promoted `k`, restricted to existing index coords |
| the names whose index is reset AND whose stored array is removed | `dropped_coords: PSet[int]` | `drop_or_convert`'s `drop_variables.update(var_names)` (drop=True) plus `drop_variables.add(index.dim)` / `drop_variables.update(keep_level_vars)` (the multi-index dim coord and reduced level coords) in `reset_index` |
| the index coords re-added as PLAIN (base) variables (kept array, no index) | `converted_coords: PSet[int]` | `drop_or_convert`'s else branch: `new_variables.update({k: self._variables[k].to_base_variable() for k in var_names})` (drop=False). They stay in `variables`/`coord_names` but leave `indexes`/`index_repr` — the F2P `converted` assertions (`reset[name].variable == ds[name].variable.to_base_variable()`) |

Names are integer ids because the methods perform only set membership / union /
difference / equality on them — never any character-level operation. `dict`
values (the `Variable` objects) are irrelevant to the bug and to the tested
invariant; only the KEY SETS and the per-name index-backed KIND matter, so each
collection is a `PSet[int]`.

### Read-only inputs (directive 5)
Every input collection (`variables0`, `coord_names0`, `indexes0`,
`index_repr0`, `new_index_vars`, `promoted_names`, `displaced_index_coords`,
`dropped_coords`) is a `PSet[int]` — an **immutable Viper value**, not an
aliasable heap object. The model's set operations (`+`, `-`) always produce
fresh values and never mutate an argument; there is no permission to grant or
withhold and no mutation channel a wrong implementation could exploit to satisfy
the postcondition vacuously (the failure mode directive 5 guards against for
heap predicates). Read-only-ness is therefore structural here, exactly as for
the `PSeq[int]` carriers in the string-modeling exemplars. The result is a fresh
`bool`; no input is referenced in the postcondition as an output carrier.

## 3. Deep model provenance (A-reference — checked by G-AX / axiom_check.py)

There is **no `@ContractOnly` axiom** in this bundle: the changed behaviour is
the recomputation of the four name collections, which is modelled DEEPLY as set
algebra over `PSet[int]`. The deep model is the impl of `promote_to_index` /
`teardown_index` plus the `well_formed` predicate; it is validated **==** the
real callees `Dataset.set_index` / `Dataset.reset_index` out-of-band by
axiom_check.py (G-AX), not consumed as an axiom.

**Real callees & the property validated.** `Dataset.set_index`
(`dataset.py:3968`) and `Dataset.reset_index` (`dataset.py:4108`) recompute
`variables`, `coord_names` and `indexes` and pass them to
`_replace_with_new_dims`. The structural invariant a well-formed `Dataset`
must satisfy — and that `DataVariables.__len__` (`dataset.py:367`) depends on —
is

  `indexes ⊆ coord_names ⊆ variables`  and  `index_repr ⊆ indexes`,

so that `len(variables) - len(coord_names) >= 0` and no coordinate is left in
the index-backed representation without a live index. axiom_check.py builds the
FAIL_TO_PASS input datasets, runs the REAL `set_index`/`reset_index`, reads the
four collections from the result (`_variables`, `_coord_names`, `_indexes`
keysets and `isinstance(v, IndexVariable)` for the kind — a DIRECT structural
read, no value proxy / double-mask), and asserts (a) the real result is
well-formed and (b) the model's set algebra predicts the real result's
collections **EXACTLY on all four collections for EVERY scenario** — including
every drop / convert / rename case. The three teardown channels are derived
STRUCTURALLY from the real input/output (`dropped = variables_in -
variables_out`; `new_index_vars = indexes_out - indexes_in`; `converted =
(indexes_in - indexes_out) - dropped - new_index_vars`), not back-derived to
force a pass; there is NO well-formedness-only relaxation and NO skip-guard (the
earlier WF-only relaxation on the `drop=False`/convert cases was the masked
soundness gap, now removed). Verified: RC 0 on the gold callees; RC 1 on the
prepatch callees (crashes with the issue's `ValueError: __len__() should return
>= 0`), confirming the check is genuinely discriminating. Exit 0 iff sound. It
imports only the standard library and `xarray` (the package under test).

**Flag / configuration dependencies.** None. The behaviour does not depend on
any keyword default beyond `errors="ignore"` already encoded in the displaced /
dropped derivation; the `drop` keyword of `reset_index` is exercised in both
`True` and `False` settings by the F2P grid.
