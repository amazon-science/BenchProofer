# refinement.md — django__django-15563

Maps every operation in `implementation_relatedTargetIds` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed**, **A-reference**,
**I** (identical concrete op). The single Lean triple composes the two gold edits
(`pre_sql_setup` column selection + `get_related_updates` per-ancestor filter).

| # | Lean op (impl) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `let mut nextCol := 1` | `fields = [meta.pk.name]` (next select column index = `len(fields)` = 1) | R | child pk occupies column 0; next dedicated column starts at 1. `Nat` ↔ Python list length. |
| 2 | `let mut assignment := []` | `related_ids_index = []` | R | accumulator for `(ancestor, column)` pairs ↔ `(related, index)` tuples. |
| 3 | `for ancestor in ancestors do` | `for related in self.query.related_updates:` | I | iterate ancestors in insertion order. |
| 4 | `if sharesPrimaryKey ancestor` | `if all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` | R | the PK-chain predicate ↔ `sharesPrimaryKey : Nat → Bool` (mapping.md). |
| 5 | `assignment := assignment ++ [(ancestor, 0)]` | `related_ids_index.append((related, 0))` | I | reuse child pk column 0. |
| 6 | else `assignment ++ [(ancestor, nextCol)]` | `related_ids_index.append((related, len(fields)))` | R | `nextCol` ↔ `len(fields)` at append time. |
| 7 | `nextCol := nextCol + 1` | `fields.append(related._meta.pk.name)` | R | appending a select field bumps the next column index by 1. (`query.add_fields(fields)` materializes the select; modeled as the column layout `rows` already follows.) |
| 8 | `for ac in assignment do` | `for parent, index in related_ids_index` (gathering) + `get_related_updates` loop (consuming) | I | iterate the per-ancestor column assignment. |
| 9 | `result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]` | `related_ids[parent].extend(r[index] for r in rows)` then per-ancestor `add_filter("pk__in", self.related_ids[model])` | R | read column `ac.2` from each row ↔ `r[index]`; the resulting id list is the ancestor's `pk__in` target. `r.getD i 0` ↔ `r[index]` (rows are well-formed; default never taken for valid columns). |

## Preconditions (correct_ binder, SPEC_GUIDE §1)
The theorem assumes two facts the surrounding machinery guarantees, making the
abstracted inputs faithful to the Python (they do NOT weaken `problem_spec`,
which remains an exact equality):
- `ancestors.Nodup` — `related_updates` is keyed by distinct model objects, so
  the ancestor list has no duplicate keys.
- `∀ r ∈ rows, r.length = 1 + (#non-sharing ancestors)` — `pre_sql_setup`
  selects exactly `[pk] + [one pk per non-PK-chain ancestor]`, so every result
  row carries precisely those columns; `r.getD i 0`'s default is never reached
  for a gathered column index `i`. (This closes the row-shape gap that `getD`
  alone would otherwise leave; the discriminating MTI witness satisfies both.)

Notes:
- The gold also keeps the child-pk path (`idents`/`r[0]`) for the main query's
  `pk__in`; that path is unchanged behavior and not part of the *ancestor*
  targeting being fixed, so it is not modeled (it is the `meta.pk` column 0 that
  PK-chain ancestors reuse — captured by op 5).
- No A (axiom) rows: the fix is bookkeeping over abstracted inputs; every op is
  R or I. `conf_skip = false`; G-CONF differential-tests the full R/I shadow.
- No changed-inexpressible op.

## Prepatch (the actual bug)
`Solution_prepatch.lean` gathers only the child pk column (`r[0]`) and reuses it
for every ancestor — exactly base `pre_sql_setup` (`query.add_fields([pk])`;
`self.query.related_ids = idents`) feeding base `get_related_updates`
(`add_filter("pk__in", self.related_ids)`). On any input with a non-sharing
ancestor whose own pk column differs from column 0 it violates
`problem_spec_relatedTargetIds` (validated: a discriminating MTI input makes the
post-patch impl satisfy and the prepatch impl refute the spec). Its
`correct_relatedTargetIds` is therefore unclosable → G-DIFF fails as required.
