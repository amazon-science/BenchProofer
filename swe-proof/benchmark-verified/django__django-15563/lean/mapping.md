# mapping.md — django__django-15563

## Instance
Multi-table-inheritance (MTI) `update()` with several parents targets ancestor
rows by the *child* primary key instead of each non-PK-chain ancestor's own
primary key, so the wrong rows (and wrong table) are updated. Gold patch fixes
the pre-select to gather one identifier column per non-PK-chain ancestor and a
per-ancestor identifier map, then filters each ancestor's UPDATE by its own
identifiers.

## Symbol binding (file:line @ base_commit)
- `SQLUpdateCompiler.pre_sql_setup`
  — `django/db/models/sql/compiler.py:1838` (the `query.add_fields(...)` line
  changed at :1838 and the ident-gathering loop at :1853–1857).
- `UpdateQuery.get_related_updates`
  — `django/db/models/sql/subqueries.py:124` (filter line at :137).
- `query.related_ids` field — `django/db/models/sql/subqueries.py:63`.

The two edited functions implement a single observable behavior: which
identifiers target each ancestor's update. They are collapsed into ONE Lean
triple, `relatedTargetIds`, whose data flow composes:
(a) `pre_sql_setup` deciding which selected column each ancestor reads from
(`add_fields([pk] + extra ancestor pks)` + `related_ids_index`), and
(b) `get_related_updates` reading `related_ids[model]` per ancestor.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
| Python | Lean | notes |
|---|---|---|
| ancestor model object (`related`) | `Nat` (the ancestor's identity/tag) | only identity matters; `==` is the model-equality used as the dict key |
| `self.query.related_updates` (ordered dict, keys = ancestors) | `ancestors : List Nat` | iteration order = insertion order; keys, in order |
| `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` | `sharesPrimaryKey : Nat → Bool` | True ⇔ a PK chain to the ancestor exists ⇒ child PK == ancestor PK ⇒ reuse column 0 |
| rows returned by `execute_sql(MULTI)` (each `r` a tuple; `r[0]` = child pk, `r[i]` = i-th selected ancestor pk) | `rows : List (List Int)` | one inner list per result row; column index = select position |
| `fields = [meta.pk.name] + [ancestor pks...]` select layout | column numbering: child pk = 0; non-sharing ancestors numbered 1.. in encounter order | `columnAssignment` reproduces `related_ids_index` |
| `related_ids` = `defaultdict(list)`; per-ancestor id lists | `result : List (Nat × List Int)` | `(ancestor, ids)` pairs, ancestor order preserved |
| `query.add_filter("pk__in", related_ids[model])` per ancestor in `get_related_updates` | the second loop pairing each ancestor with its column's ids | `get_related_updates` iterates `related_updates` (same order) |

## Column-assignment correspondence (`related_ids_index`)
Gold builds `fields=[pk]`, then for each `related` ancestor:
- PK-chain holds → `related_ids_index.append((related, 0))` (reuse pk column).
- else → `related_ids_index.append((related, len(fields)))`, `fields.append(ancestor pk)`.

`len(fields)` at that moment is exactly the next dedicated column: `1` for the
first non-sharing ancestor, `2` for the second, etc. This is precisely
`columnAssignment sharesPrimaryKey ancestors 1`.

## Callee provenance / axioms
- No consumed axiom and no opaque callee. The query infrastructure
  (`add_fields`, `execute_sql`, `add_filter`, `get_path_to_parent`) is NOT
  reimplemented; its *outputs* are the abstracted inputs `rows`,
  `sharesPrimaryKey`, and `ancestors`. The fix is purely the index/selection
  bookkeeping over those, which is modeled deeply (R/I). Hence `axiom_check.py`
  is a skip stub.

## Flag dependency
`sharesPrimaryKey a` corresponds to the `all(... .primary_key ...)` predicate
over the join path; it is the only branch condition and is fuzzed over both
truth values in conformance_check.py.

## G-CONF fuzz seed
`pinned_seed = 15563`.
