# refinement.md — operation correspondence (django__django-15732)

Maps every op in `implementation_selectUniqueToDrop` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The modeled function is the constraint-selection decision in
`_delete_composed_index`. The patch inserts a narrowing block before the
"len != 1" check; everything else on this path is unchanged. The candidate
identifiers (`self._constraint_names(...)` output) and the canonical identifier
(`str(self._unique_constraint_name(..., quote=False))`) are taken as FREE inputs,
so the spec is quantified over all values any real helper could return — no axiom.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut names := candidates` | `constraint_names = self._constraint_names(...)` (value flows into the new block) | I | the discovered candidate list; its source helper is unchanged and its output is a free input |
| 2 | `if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then names := [defaultName]` | the NEW block: `if constraint_kwargs.get("unique") is True and constraint_names and self.connection.features.allows_multiple_constraints_on_same_fields: ... if default_name in constraint_names: constraint_names = [default_name]` | I | line-for-line skeleton of the four-way guard + reduction. `constraint_names` (a nonempty list) ↔ `!names.isEmpty`; `default_name in constraint_names` ↔ `names.contains defaultName`; `constraint_names = [default_name]` ↔ `names := [defaultName]` |
| 3 | `defaultName` (free input) | `default_name = str(self._unique_constraint_name(model._meta.db_table, columns, quote=False))` | R | the canonical identifier; modeled as its `String` value (R: rendered-name ↔ `String`). The patch-introduced helper's rendering algorithm is an I/R wrapper, not graded behavior; its output is a free input, not axiomatized |
| 4 | `if names.length != 1 then return Except.error ()` | `if len(constraint_names) != 1: raise ValueError("Found wrong number ...")` | I | the wrong-number guard; `raise ValueError` ↔ `Except.error ()` (R: exception ↔ `Except`) |
| 5 | `return Except.ok names.headI` | `self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))` | I | selecting the single identifier `constraint_names[0]` ↔ `names.headI`; the downstream SQL rendering + execute are identity wrappers on the selected identifier (mapping.md), not modeled |

No A-consumed rows (axioms region empty). No A-reference rows: nothing is
modeled deeply against a real callee — the helpers' outputs are free inputs, so
G-AX is a skip stub (no axiom and no deep model to validate). No
changed-inexpressible op.

The discriminating clause is row 2 (the narrowing block). The prepatch impl
omits it entirely, so on an input where `candidates` has length ≠ 1 but narrows
to length 1 (e.g. `candidates = ["a","b"]`, `isUnique = true`, `allowsMultiple =
true`, `defaultName = "a"`) the frozen `problem_spec` requires `Except.ok "a"`
while the buggy impl returns `Except.error ()`. Its `correct_selectUniqueToDrop`
therefore cannot close. That is the G-DIFF signal, and it mirrors the issue's
"Found wrong number (2) of constraints" failure.
