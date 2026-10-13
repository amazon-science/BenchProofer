# mapping.md — symbol binding & type bijection (django__django-12708)

## Modeled function
- **Lean** `implementation_dropComposedIndex :
  List DbConstraint → List String → Except Nat String`
- **Python** `BaseDatabaseSchemaEditor._delete_composed_index`
  — `django/db/backends/base/schema.py:402-416 @ 447980e7` — as reached through
  the deletion branch of `alter_index_together`
  (`schema.py:394-396 @ 447980e7`):
  ```python
  for fields in olds.difference(news):
      self._delete_composed_index(model, fields, {'index': True, 'unique': False},
                                  self.sql_delete_index)
  ```

The modeled function is the constraint-selection core of `_delete_composed_index`
specialized to the index-removal call site. `_delete_composed_index` computes the
table column list for `fields`, calls `self._constraint_names(model, columns,
exclude=meta_constraint_names|meta_index_names, **constraint_kwargs)` to find the
constraint names matching those columns under the keyword filters, and then
enforces "exactly one": if `len(constraint_names) != 1` it raises
`ValueError("Found wrong number (%s) of constraints …")`, otherwise it deletes
`constraint_names[0]`.

`_constraint_names` (`schema.py:1142-1170 @ 447980e7`) iterates the table's
introspected `constraints` (a `name -> infodict` dict from
`connection.introspection.get_constraints`), keeps a constraint when its
`columns` equal the requested columns AND each provided keyword flag
(`unique`/`index`/…) equals the corresponding `infodict` value, and drops any
name in `exclude`. The call site passes `index=True` pre-patch and
`index=True, unique=False` post-patch.

The patch's effect is entirely in the `constraint_kwargs` dict handed to
`_delete_composed_index` at the index-removal call site: pre-patch `{'index':
True}`, post-patch `{'index': True, 'unique': False}`. The modeled function
folds that selection (the `_constraint_names` filter + the exactly-one count)
into one `Except`-returning routine; the keyword filter set is the modeled
behavior.

## Why the bug happens (mechanism, kept out of the spec view)
On every supported backend, a multi-column `unique_together` constraint is
reported by `get_constraints` with BOTH `unique=True` and `index=True` (e.g.
SQLite `PRAGMA index_list` sets `index=True` for the unique index —
`django/db/backends/sqlite3/introspection.py:387-394 @ 447980e7`). When a
`unique_together` and an `index_together` exist over the SAME columns, the
pre-patch `{'index': True}` filter therefore matches BOTH names, so
`len(constraint_names) == 2` and `_delete_composed_index` raises ValueError. The
post-patch `unique=False` flag excludes the unique constraint, leaving exactly
the index. This is the F2P scenario
`test_alter_index_together_remove_with_unique_together`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| one entry of `get_constraints(...)` (`name`, `infodict`) | `DbConstraint` | only the inspected components are modeled |
| `name` (dict key) | `DbConstraint.name : String` | the constraint name |
| `infodict['columns']` (`list[str]`) | `DbConstraint.columns : List String` | already in the converter-normalized order; compared by `==` |
| `infodict['index']` (`bool`) | `DbConstraint.isIndex : Bool` | True for both ordinary and unique indexes on the backends in scope |
| `infodict['unique']` (`bool`) | `DbConstraint.isUnique : Bool` | True for a unique constraint/index over the columns |
| `name in (meta_constraint_names \| meta_index_names)` | `DbConstraint.excluded : Bool` | the per-constraint membership in the `exclude` set passed by `_delete_composed_index` (constraints/indexes declared in `Meta.constraints`/`Meta.indexes`) |
| requested `columns` for `fields` | `cols : List String` | `[model._meta.get_field(f).column for f in fields]`, identifier-converted |
| `constraint_names` list (post-filter) | `dropCandidateNames constraints cols : List String` | the filtered, order-preserving name list |
| `len(constraint_names)==1 → delete names[0]` | `Except.ok (dropCandidateNames …).head!` | the single name to drop |
| `len(constraint_names)!=1 → raise ValueError(n)` | `Except.error (dropCandidateNames …).length` | the rejected count `n` carried as the error payload |

The modeled keyword filter is exactly `columns == cols ∧ index=True ∧
unique=False ∧ name ∉ exclude` (post-patch). The other `_constraint_names`
keyword arms (`primary_key`, `check`, `foreign_key`, `type_`) are `None` at this
call site and so are identity filters; they are not modeled (only the touched
flags are projected, per SPEC_GUIDE §2).

## Callee provenance
- `_constraint_names` is the UNCHANGED callee that performs the filter. The patch
  does NOT change it; it changes the `constraint_kwargs` dict at the call site.
  Its filtering semantics are modeled DEEPLY as `isDropCandidate` /
  `dropCandidateNames` (a total filter over the projected constraint list), so it
  is an **A-reference** validated by G-AX against the real `_constraint_names`,
  NOT a consumed axiom. Nothing is axiomatized.
- `get_constraints` (introspection) is the data source; its `index`/`unique`/
  `columns` projection is the input carrier `List DbConstraint`. It is not a
  callee the changed function reasons about beyond reading those fields.
- The exactly-one count check and the ValueError are concrete control flow
  modeled as the `Except Nat String` result (I/R).
- The axioms region of Solution.lean is empty; `axiom_check.py` is a skip stub.

## Flag dependency
The discriminator is the `unique` flag: the candidate set must require
`unique=False`. The fuzzer must include constraints with every combination of
`(isIndex, isUnique)` over the same columns — in particular the
`index=True ∧ unique=True` (unique_together) constraint that the pre-patch filter
wrongly admits — plus `excluded` constraints over the same columns.

## G-CONF fuzz seed
Pinned seed: **12708**. ≥10^5 fuzzed `(constraints, cols)` inputs over small
random tables with overlapping columns and all `(isIndex, isUnique, excluded)`
combinations, including the unique+index-over-same-columns case.
