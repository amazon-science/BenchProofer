# refinement.md — pydata__xarray-7233

Operation-by-operation correspondence between `implementation_retainedCoordNames`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `should_be_coords`
computation inside `Coarsen.construct`). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let common := reshapedDims.filter (fun d => priorCoordNames.contains d)` | `set(window_dim) & set(self.obj.coords)` | R |
| 2 | `let result := common ++ priorCoordNames` | `(set(window_dim) & set(self.obj.coords)) \| set(self.obj.coords)` | R |
| 3 | `return result` | `should_be_coords = …` (handed to `set_coords`) | R |

Notes:

- **Every step is R — no A, no I.** The changed op is a pure set expression over
  two name collections (`set(window_dim)`, `set(self.obj.coords)`); SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled changed op, so it is modeled DEEPLY as a
  filter (the set intersection / common names) followed by an append (the set
  union). The `axioms` region is empty; **G-AX skips**.
- **R, not I:** the Python objects are Python `set`s; the Lean carrier is
  `List String` compared by MEMBERSHIP per the mapping.md bijection
  (`set(a) & set(b)` ↔ `a.filter (· ∈ b)`; `s1 | s2` ↔ `xs1 ++ xs2`; both
  compared as sets — order and multiplicity carry no downstream meaning because
  `set_coords` consumes a set). This is a genuine type refinement of `set[str]`
  to a membership-characterized `List String`, hence R.
- **The fix itself** is step 2: pre-patch the result is just `common`
  (`set(window_dim) & set(self.obj.coords)`), which drops every prior coordinate
  name that is not itself a reshaped dimension (the demoted non-dimensional
  coordinate, e.g. `day`). Post-patch the prior coordinate set is unioned back in,
  so the coordinate set is preserved in full. The pre-patch impl
  (`Solution_prepatch.lean`) keeps `let result := common` — the actual bug — and
  its carried gold proof fails to typecheck against the membership spec (G-DIFF):
  the `mpr` direction cannot show `name ∈ priorCoordNames → name ∈ common`.
- **G-CONF** mechanically refutes the R legs: a faithful in-process replica of
  the post-patch `should_be_coords` expression
  (`(set(window_dim) & set(coords)) | set(coords)`) is diffed AS A SET against the
  impl shadow (`filter` then `++`, compared as sets) over ≥1e5 fuzzed name-list
  pairs. No A legs.
