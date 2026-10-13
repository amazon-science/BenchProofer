# refinement.md — operation correspondence (django__django-12708)

Maps every op in `implementation_dropComposedIndex` to its `patch.diff`
counterpart (the post-patch index-removal call into `_delete_composed_index`).
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch behavior under spec is the index-removal selection:
```python
# alter_index_together, deletion branch (the changed call site):
self._delete_composed_index(model, fields, {'index': True, 'unique': False},
                            self.sql_delete_index)
# _delete_composed_index (unchanged body it flows into):
columns = [model._meta.get_field(field).column for field in fields]
constraint_names = self._constraint_names(
    model, columns, exclude=meta_constraint_names | meta_index_names,
    index=True, unique=False)          # <-- the post-patch kwargs
if len(constraint_names) != 1:
    raise ValueError("Found wrong number (%s) of constraints …" % len(constraint_names))
self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))
```

| # | Lean impl op | patch.diff / callee counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut names := []` | `constraint_names = []` inside `_constraint_names` | I | accumulator init for the filtered name list |
| 2 | `for c in constraints do` | `for name, infodict in constraints.items():` | R | iterate the introspected constraint dict; modeled as an ordered `List DbConstraint` (mapping.md bijection). Dict iteration order is the table/introspection order, matched by the list order |
| 3 | `if isDropCandidate cols c then names := names ++ [c.name]` | the `_constraint_names` keyword filter with `index=True, unique=False` + `exclude`: `columns == cols ∧ index ∧ ¬unique ∧ name ∉ exclude` | A-reference | the UNCHANGED `_constraint_names` filter, modeled DEEPLY as `isDropCandidate`. The post-patch `unique=False` arm IS the `(!c.isUnique)` conjunct — the discriminating clause. Validated == real callee by G-AX, not axiomatized |
| 4 | `if names.length != 1 then return Except.error names.length` | `if len(constraint_names) != 1: raise ValueError(len(...))` | R | the exactly-one count check; the raised ValueError ↔ `Except.error n` carrying the rejected count `n` |
| 5 | `return Except.ok names.head!` | `self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))` | R | the single selected name to delete ↔ `Except.ok names[0]`. The SQL execution effect is refined to "the name that is dropped" (the observable selection); `sql`/`_delete_constraint_sql` are downstream of the modeled selection |

No A-consumed rows: nothing is consumed as an opaque-callee axiom; the axioms
region is empty. The only callee whose behavior matters (`_constraint_names`) is
modeled deeply (row 3, A-reference) and G-AX-checked against the real callee. No
changed op is left inexpressible.

## The discriminating op (G-DIFF signal)
Row 3's `(!c.isUnique)` conjunct is the patch. `Solution_prepatch.lean` drops it
(its loop body is `if (c.columns == cols) && c.isIndex && (!c.excluded)`),
exactly mirroring the pre-patch `{'index': True}` kwargs. On the F2P input — a
table carrying BOTH a unique constraint and an ordinary index over the same
columns (both introspected with `isIndex=True`; the unique one also
`isUnique=True`) — the candidate set is:
- post-patch (Solution): `{the index}` → length 1 → `Except.ok` the index name;
- pre-patch (prepatch): `{the index, the unique}` → length 2 → `Except.error 2`.

So the carried gold proof body (which proves the spec by reducing the loop to
`dropCandidateNames` and discharging both `length = 1` / `length ≠ 1` branches)
cannot close `correct_dropComposedIndex` for the prepatch: the buggy impl returns
`Except.error 2` where the spec (built from the `(!isUnique)`-filtered
`dropCandidateNames`) demands `Except.ok` of the single index name. That is the
G-DIFF discriminator.

## G-CONF (R/I legs)
The impl region is not all-A-tagged (rows 1,2,4,5 are R/I; row 3 is a deeply
modeled A-reference that is itself executable). `conformance_check.py` builds the
Python R/I shadow of the impl — with the row-3 filter reconstructed exactly as
the post-patch `_constraint_names` keyword filter — and differential-tests it
against an independent reconstruction of the patched selection over ≥10^5 fuzzed
`(constraints, cols)` inputs (seed 12708, mapping.md). `conf_skip=false`.
