# refinement.md — pydata__xarray-6992

Operation-by-operation correspondence between `implementation_resetIndexCoords`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `Dataset.reset_index`
coordinate/variable/index bookkeeping), restricted to the modeled domain
(mapping.md): each reset target is a **plain single dimension index** whose only
associated coordinate is the target name itself. Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `for name in resetNames do …` | `for name in dims_or_levels:` | I |
| 2 | `dropIndexes := dropIndexes ++ [name]` | `idx_var_names = set(self.xindexes.get_all_coords(name)); drop_indexes.update(idx_var_names)` — in the plain-index domain `get_all_coords(name) == {name}` | A-reference |
| 3 | `if drop then dropVariables := dropVariables ++ [name]` | else-branch of the multi/non-multi switch: `drop_or_convert(idx_var_names)` → `if drop: drop_variables.update(var_names)` else `new_variables.update({k: self._variables[k].to_base_variable() …})` (name retained as ordinary variable) | R |
| 4 | `indexNames := removeAll c.indexNames dropIndexes` | `indexes = {k: v for k, v in self._indexes.items() if k not in drop_indexes}` | R |
| 5 | `varNames := removeAll c.varNames dropVariables` | `variables = {k: v for k, v in self._variables.items() if k not in drop_variables}; variables.update(new_variables)` — in the plain-index domain `new_variables` (the converted base vars) reuse the SAME names already in `variables` when `drop=False`, and are absent when `drop=True`, so the variable-NAME set is `varNames \ dropVariables` either way | R |
| 6 | `coordNames := removeAll c.coordNames dropVariables` | `coord_names = self._coord_names - drop_variables` (the gold fix; passed to `_replace_with_new_dims`) | R |

Notes:

- **Op 2 is the one A-reference:** the *per-name index coordinate set*
  `self.xindexes.get_all_coords(name)` is an UNCHANGED callee. In the modeled
  plain-dimension-index domain it returns exactly `{name}`; the impl models this
  DEEPLY as the literal singleton `[name]`, so it is an A-reference (validated
  `== real callee` by G-AX), NOT a consumed `axiom` the proof depends on. The
  `axioms` region ships no `opaque`/`axiom` declaration.
- **`to_base_variable()` is identity on names** (op 3, `drop=False`): it changes
  the variable *kind* (IndexVariable → base Variable) but not its name, so on the
  name-collection abstraction it is the identity. No axiom consumed.
- **The fix itself is op 6.** Pre-patch, the final coordinate set was rebuilt as
  `set(new_variables) | self._coord_names`; for a plain dimension index
  `new_variables` re-adds no NEW name, so the dropped name was never removed from
  the coordinate set — it lingered as a coordinate while its variable was gone,
  producing `_coord_names ⊋ _variables` (the reported `__len__() should return
  >= 0` / broken-repr symptom). `Solution_prepatch.lean` re-introduces this bug
  by setting `coordNames := c.coordNames` (the original set, unsubtracted),
  exactly mirroring the pre-patch `set(new_variables) | self._coord_names`
  collapse in the plain-index domain. Only the `coordNames` output component
  differs pre/post — that is the discriminating clause the spec pins (directive
  5 frame).
- **No dead axioms; no A-consumed legs.** The changed decision (the coordinate
  set) is modeled deeply, per SPEC_GUIDE §3.
- **G-CONF** mechanically refutes the R legs: it stands up REAL `xr.Dataset`s
  whose coordinates are plain dimension coordinates (each its own `PandasIndex`),
  applies the gold patch, calls the real `reset_index`, and diffs
  `set(result._coord_names)` / `set(result._variables)` / `set(result.xindexes)`
  against the shadow of the impl over ≥1e5 fuzzed inputs.
- **Domain restriction:** the `PandasMultiIndex` level-manipulation branch
  (`keep_levels` / level renaming / `drop_or_convert(level_names)`) is OUT of the
  modeled domain (mapping.md). The modeled single-index branch is the
  discriminating slice that exhibits the reported invariant violation.
