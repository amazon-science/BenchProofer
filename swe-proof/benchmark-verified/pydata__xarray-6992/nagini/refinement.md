# refinement.md — pydata__xarray-6992

The operation-by-operation correspondence between `model.py`'s implementation
(the `promote_to_index` and `teardown_index` impl regions, and the `well_formed`
deep model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model is validated == the real callee by axiom_check.py
/ G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, recomputes the dataset's name collections so that the result is
well-formed exactly as the gold patch does, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE). There are **no `@ContractOnly`
axioms**, hence no A-consumed rows: the whole change is modelled deeply as set
algebra (A-reference) over `PSet[int]`.

Carrier refinement used by every row (mapping.md §2): each dict/set name
collection ↔ `PSet[int]` of name ids; Python set `|`/`-`/`<=`/`in` ↔ PSet
`+`/`-`/`subset`/`in`; the array KIND `isinstance(v, IndexVariable)` ↔
membership in `index_repr`. All such steps are **R**.

## A. Site 1 — `set_index` (`xarray/core/dataset.py:3968`)

Gold hunks rewrite the post-state recomputation. Key lines (paraphrased to the
collections that matter):

```
- drop_variables: list = []           ;  maybe_drop_indexes: list = []
+ drop_indexes: set = set()           ;  drop_variables: set = set()
+ all_var_names: set = set()
  ...
- maybe_drop_indexes += list(current_coord_names) + var_names
- drop_variables += var_names
+ all_var_names.update(var_names); drop_variables.update(var_names)
+ all_index_coord_names = set(index_coord_names) ∪ (per-name get_all_coords)
+ drop_indexes.update(all_index_coord_names)
+ drop_variables.update(all_index_coord_names)
  ...
+ # re-add deindexed coordinates (convert to base variables)
+ for k in drop_variables:
+     if k not in new_variables and k not in all_var_names and k in self._coord_names:
+         new_variables[k] = self._variables[k].to_base_variable()
  ...
- indexes_ = {k:v for ... if k not in maybe_drop_indexes}
+ indexes_ = {k:v for ... if k not in drop_indexes}
- coord_names = self._coord_names - set(drop_variables) | set(new_variables)
+ coord_names = self._coord_names - drop_variables | set(new_variables)
```

| # | model.py impl op (`promote_to_index`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `drop_variables = promoted_names + displaced_index_coords` | `drop_variables.update(var_names)` then `drop_variables.update(all_index_coord_names)` | R + I | union of the promoted names and the displaced pre-existing index coords; the gold's two `update`s on a `set` ↔ one PSet union. The pre-patch dropped only `var_names` (it is `promoted_names` alone — see G-DIFF). |
| A2 | `readd = (drop_variables - new_index_vars) - promoted_names` | the `for k in drop_variables: if k not in new_variables and k not in all_var_names and k in self._coord_names` filter (`new_variables[k] = ...to_base_variable()`) | R | the set-builder `{k ∈ drop_variables : k ∉ new_variables ∧ k ∉ promoted}` ↔ set differences; `all_var_names == promoted_names`, `new_variables` keys ⊇ `new_index_vars`. (The `k ∈ self._coord_names` conjunct is subsumed: the proof only needs the index-backed-conversion clause, and a re-added name is conservatively a coordinate; see D.) |
| A3 | `new_variables_all = new_index_vars + readd` | `new_variables` after `idx_vars` ∪ the re-added base variables | R | the result's added variables: the new index coords plus the converted (de-indexed) coordinates. |
| A4 | `indexes_out = (indexes0 - displaced_index_coords) + new_index_vars` | `indexes_ = {k:v ... if k not in drop_indexes}; indexes_.update(new_indexes)` | R | `drop_indexes == displaced_index_coords` (the gold accumulates exactly the displaced index coords into `drop_indexes`); update with the new index ↔ union. |
| A5 | `index_repr_out = (index_repr0 - readd) + new_index_vars` | the kind of each stored array: a re-added coordinate is stored via `.to_base_variable()` (leaves the index-backed kind); the new index coords are `IndexVariable`s | R | `to_base_variable()` ↔ removing `readd` names from `index_repr`; the new index coords ↔ adding `new_index_vars`. |
| A6 | `variables_out = (variables0 - drop_variables) + new_variables_all` | `variables = {k:v ... if k not in drop_variables}; variables.update(new_variables)` | R + I | drop then update ↔ difference then union. |
| A7 | `coord_names_out = (coord_names0 - drop_variables) + new_variables_all` | `coord_names = self._coord_names - drop_variables | set(new_variables)` | R + I | the gold's exact set expression. |
| A8 | `return well_formed(...)` (the three subset clauses) | `return self._replace_with_new_dims(variables, coord_names, indexes_)` | R | `_replace_with_new_dims` constructs a `Dataset`; the verified postcondition is the structural invariant the constructed `Dataset` (and `DataVariables.__len__`) requires. |

## B. Site 2 — `reset_index` (`xarray/core/dataset.py:4108`)

Gold hunks (collections that matter):

```
- drop_indexes: list = []     ;  drop_variables: list = []
+ drop_indexes: set = set()   ;  drop_variables: set = set()
  ...
- drop_indexes += list(self.xindexes.get_all_coords(name))
+ idx_var_names = set(self.xindexes.get_all_coords(name)); drop_indexes.update(idx_var_names)
+ def drop_or_convert(var_names):
+     if drop:   drop_variables.update(var_names)           # -> dropped_coords
+     else:      new_variables.update({k: self._variables[k].to_base_variable()
+                                      for k in var_names})  # -> converted_coords (keeps array, leaves index)
  ... (multi-index: keep_levels/create_variables -> new_indexes/new_variables = new_index_vars;
       drop_variables.add(index.dim) and reduced level coords -> dropped_coords) ...
  indexes = {k:v ... if k not in drop_indexes}; indexes.update(new_indexes)
  variables = {k:v ... if k not in drop_variables}; variables.update(new_variables)
- coord_names = set(new_variables) | self._coord_names
+ coord_names = self._coord_names - drop_variables
- return self._replace(variables, coord_names=coord_names, indexes=indexes)
+ return self._replace_with_new_dims(variables, coord_names=coord_names, indexes=indexes)
```

The three name fates: `drop_variables` accumulates the **dropped** names (leave
all four collections); `new_variables` accumulates BOTH the **converted** base
variables (drop=False) and the **replacement** index coords; `drop_indexes`
removes every torn-down name from the index map. The model's `converted_coords`
is exactly the names `new_variables` re-adds as base variables, and
`new_index_vars` is the names it re-adds as `IndexVariable`s.

The gold splits each affected name into THREE disjoint fates via the
`drop_or_convert` helper (drop=True → `drop_variables.update`; drop=False →
`new_variables.update({k: ...to_base_variable()})`) plus the `drop_variables.add`
/ `drop_variables.update(keep_level_vars)` of the multi-index dimension and
reduced-level coords. The model mirrors this with three disjoint input channels:
`dropped_coords` (lose the array entirely), `converted_coords` (keep the array as
a plain variable, leave the index), and `new_index_vars` (a freshly created
replacement index coord). The four collection equalities are pinned over all
three channels.

| # | model.py impl op (`teardown_index`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `dropped_coords` (input channel) | `drop_or_convert`'s `drop_variables.update(var_names)` (drop=True) + `drop_variables.add(index.dim)` + `drop_variables.update(keep_level_vars)` (reduced level coords) | R | the names whose stored array is removed entirely; accumulated into the gold's `drop_variables` set. |
| B2 | `converted_coords` (input channel) | `drop_or_convert`'s else branch: `new_variables.update({k: self._variables[k].to_base_variable() for k in var_names})` (drop=False) | R | the index coordinates re-added as PLAIN (base) variables — they keep their stored array but leave the index and the index-backed kind. `.to_base_variable()` ↔ removing the name from `index_repr` while retaining it in `variables`/`coord_names`. This is the convert channel that the previous single-`dropped_coords` model could NOT express (the soundness gap fixed here). |
| B3 | `new_index_vars` (input channel) | `new_indexes`/`new_variables` from `idx.create_variables(keep_level_vars)` (the surviving multi-index sub-index) | R | the freshly created replacement index coords; `IndexVariable`s, so they enter all four collections. (When a multi-index reduces to a single index the surviving level is renamed to the dimension via `keep_levels` → `index.rename(self.dim)`; at the name-set level that is the existing dimension name surviving, see §C.) |
| B4 | `indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars` | `indexes = {k:v ... if k not in drop_indexes}; indexes.update(new_indexes)` | R | `drop_indexes ⊇ dropped_coords ∪ converted_coords` (every torn-down name leaves the index, whether dropped or converted); update with replacement index ↔ union. |
| B5 | `index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars` | dropped names lose their array; converted names become base variables (`to_base_variable`); replacement coords are `IndexVariable`s | R | array-kind bookkeeping: BOTH dropped and converted names leave the index-backed kind. |
| B6 | `variables_out = (variables0 - dropped_coords) + new_index_vars` | `variables = {k:v ... if k not in drop_variables}; variables.update(new_variables)` | R + I | only the dropped names leave `variables`; the converted names are re-added by `new_variables.update(base_vars)`, so they STAY. |
| B7 | `coord_names_out = (coord_names0 - dropped_coords) + new_index_vars` | `coord_names = self._coord_names - drop_variables` (then the replacement + converted coords are coordinates via `_replace_with_new_dims`) | R + I | **the heart of the fix:** the pre-patch unioned the replacement index onto the ORIGINAL coord names WITHOUT subtracting the dropped names (`set(new_variables) | self._coord_names`), so a torn-down coordinate stayed named with no stored array. `model_prepatch.py` reproduces exactly this (`coord_names0 + new_index_vars`) and FAILS the `coord_names` equality + the `subset(coord_names_out, variables_out)` clause (G-DIFF). A converted name is NOT subtracted here (it keeps its array), so it stays a coordinate — matching the F2P `converted` assertions. |
| B8 | `return well_formed(...)` | `return self._replace_with_new_dims(...)` | R | as A8; the gold switches `_replace` → `_replace_with_new_dims` precisely so the recomputed `coord_names` is honoured. |

## C. The keep_levels hunk (`xarray/core/indexes.py:705`)

```
- return PandasIndex(index, self.dim, coord_dtype=self.level_coords_dtype[index.name])
+ return PandasIndex(index.rename(self.dim), self.dim, coord_dtype=self.level_coords_dtype[index.name])
```

This renames the surviving single level coordinate to the dimension name when a
multi-index reduces to a single index. Its effect on the name collections — the
replacement index coordinate is the dimension name — is captured abstractly by
`new_index_vars` in `teardown_index` (a replacement index coord with a stored
array). Its concrete renaming is a value-level detail outside the
name-collection invariant; axiom_check.py asserts well-formedness on these
multi-index-reduction scenarios (`reset_index(["foo"])`, etc.) and does not
force an exact name-set prediction where a level is renamed (mapping.md §3).
No model op corresponds to a *changed* inexpressible operation: this is an
**R** abstraction of the replacement-index name into `new_index_vars`.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is **R** or **I**; the changed behaviour (the recomputation of
the four name collections that restores `coord_names ⊆ variables` and
`index_repr ⊆ indexes`) is modelled **deeply** as set algebra over `PSet[int]`
— an **A-reference** validated `== ` the real `set_index` / `reset_index` by
axiom_check.py (G-AX), NOT hidden behind an axiom about the function under
change. There is no `@ContractOnly` axiom and therefore no A-consumed row.

The convert-to-base step of `reset_index` (`drop_or_convert`'s else branch,
`to_base_variable()`) is a **value-distinguishable** name-collection effect: a
converted coordinate STAYS in `variables`/`coord_names` but LEAVES
`indexes`/`index_repr`. It is therefore expressible as a value-level
postcondition and is modelled DEEPLY via the dedicated `converted_coords`
channel (B2/B5/B6) — the mirror of site-1's `readd` channel. (A previous
single-`dropped_coords` model could not separate a converted from a dropped name
and was a soundness gap; the three-channel teardown closes it. This is NOT a
control-flow effect invisible to the value abstraction — the four name
collections differ between the convert and the drop case — so no capability
token / `Exsures` is needed.)

The `k ∈ self._coord_names` conjunct of the A2 re-add guard is conservatively
dropped from `readd`: keeping it would only SHRINK `readd`, and the proof needs
`readd` to be exactly the set the index-backed-conversion clause removes;
because every member of `displaced_index_coords` is an index coordinate (hence a
coordinate, `displaced ⊆ indexes0 ⊆ coord_names0`), the conjunct is always true
on the names `readd` selects, so the model and gold compute the same set. This
is an R-faithful simplification, not a behaviour change.

## E. verify(model) ⇒ resolved

`teardown_index` verifies only if (i) `coord_names_out ⊆ variables_out` (B7),
which holds iff dropped names are removed from BOTH the variables and the
coordinate set — exactly the gold's `coord_names = self._coord_names -
drop_variables`; and (ii) `index_repr_out ⊆ indexes_out` with the converted
names removed from index/repr but RETAINED in variables/coord (B2/B5/B6) — exactly
the gold's `to_base_variable()` conversion. A wrong impl that treats a converted
coordinate as dropped (removing it from `variables` too) violates the pinned
`variables_out` equality; one that leaves it index-backed violates the
`index_repr_out` equality. `promote_to_index` verifies only if `index_repr_out ⊆
indexes_out` (A5/A4), which holds iff displaced coordinates are converted out of
the index-backed representation — exactly the gold's "re-add deindexed
coordinates" loop. The pre-patch skeletons (`model_prepatch.py` for B7,
`model_prepatch_2.py` for the A5 clause) fail these clauses, so the frozen spec
senses both fixed behaviours (G-DIFF). By R (set-collection ↔ PSet, mapping.md §2)
the verified recomputation equals the gold's, and by G-AX the deep model equals
the real callees EXACTLY on all four collections for every FAIL_TO_PASS scenario
(A-reference; the convert case is now pinned, not WF-only). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this document, G-EQ) plus the A-reference validation (G-AX);
there is no axiom-soundness trust point because there is no axiom.

## F. Counterexample evidence (the closed hole)

Six same-spec wrong impls of `teardown_index` were re-encoded and run through the
adversary `weakness` check; NONE verifies (each NOT-A-COUNTEREXAMPLE):
(1) treat converted names as dropped (the verdict's D1/D4 counterexample — the
converted coordinate vanishes from `variables`); (2) the base-commit
`coord_names = coord_names0 + new_index_vars` (no subtraction); (3) leave
converted names index-backed (no conversion); (4) converted leave `index_repr`
but stay in `indexes`; (5) identity (drop nothing); (6) spurious converted name
re-added to `indexes`. A structurally-different CORRECT impl (combined
`gone_idx = dropped ∪ converted`, reversed union operand order, named
intermediates) VERIFIES (positive control). This proves the spec admits no wrong
implementation of the modelled behaviour.
