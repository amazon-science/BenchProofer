# mapping.md — django__django-11885

## Symbol binding (file:line @ base_commit 04ac9b45a3)
Modeled function: the scheduling of the *fast-delete* bulk operations inside the
cascade collector, `Collector.collect`, `django/db/models/deletion.py:214-250`
(the `collect_related` branch). The gold patch rewrites that branch so that the
relations which can be fast-deleted are accumulated by their related model into
`model_fast_deletes = defaultdict(list)` and then emitted as ONE combined
operation per related model (post-patch `deletion.py:225-243`,
`for related_model, related_fields in model_fast_deletes.items(): … fast_deletes.append(…)`).
Pre-patch, each fast-deletable relation appended its own queryset to
`self.fast_deletes` immediately, one per relation.

Lean modeled function name: `combineFastDeletes` (names the *behavior* — combine
the scheduled fast-delete operations — not a patched symbol; see G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `combineFastDeletes` (modeled scheduler) | the fast-delete accumulation+emission in `Collector.collect`, `deletion.py:214-250` (post-patch `:212-243`, the `model_fast_deletes` grouping) |
| input element `(table, column)` | one cascading relation: its `related.related_model` (target table) + `related.field` (the join column `field.name`), iterated over `get_candidate_relations_to_delete(model._meta)`, `deletion.py:217-221` |
| `rels` (input list) | the sequence of fast-deletable cascade relations, in discovery order, that reach the `self.fast_deletes.append(...)` path (`can_fast_delete(...)` true), `deletion.py:227-228` (pre) / `:223-224` (post `model_fast_deletes[related_model].append(field)`) |
| `groupByTable` / result | post-patch `model_fast_deletes` grouped by `related_model`, each emitted once via `self.related_objects(related_model, related_fields, batch)` → `self.fast_deletes.append(sub_objs)`, `deletion.py:236-239` (post) |
| `insertRelation` | one step of building `model_fast_deletes = defaultdict(list)`: `model_fast_deletes[related_model].append(field)`, `deletion.py:224` (post) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `related_model` identity (a model class; only `==` / dict-key identity observed) | `Table := Nat` (injective encoding of the distinct model identities) |
| `field` join column identity (`field.name`; only equality observed) | `Column := Nat` (injective encoding of distinct column identities) |
| ordered list of fast-deletable relations `[(related_model, field), …]` in `get_candidate_relations_to_delete` discovery order | `rels : List (Table × Column)` |
| `model_fast_deletes : defaultdict(list)` materialized via `.items()` (insertion order) into `[(related_model, [field, …]), …]` | `result : List (Table × List Column)` |
| `model_fast_deletes[m].append(f)` (insertion-ordered dict; first-seen key order; per-key append order) | `insertRelation acc m f` (append `f` to existing entry, else new entry at end) |

### Dict-insertion-order modeling note
Python ≥3.7 `dict` (and `defaultdict`) preserve key INSERTION order, and
`.items()` yields keys in first-insertion order; each key's `list` value
preserves append order. `groupByTable` mirrors this exactly: a new table is
appended at the END of the accumulator (first-discovery order of tables), and a
repeat table's column is appended to the END of that table's column list
(discovery order of columns). The Lean↔Python correspondence is therefore an
exact bijection on BOTH the key order and the per-key value order — not merely a
set equality. G-CONF compares the two legs as ordered lists.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `get_candidate_relations_to_delete`,
  `can_fast_delete`, and `related_objects` are NOT modeled: they determine WHICH
  relations are fast-deletable and in what order — that selection enters as the
  pre-filtered `rels` input. The modeled behavior is purely the grouping
  (`defaultdict(list)` accumulation + ordered emission), which is modeled deeply
  as `groupByTable` (an I/R op, not an axiom).
- Flag dependency: a relation reaches the fast-delete grouping iff
  `field.remote_field.on_delete == CASCADE` (not `DO_NOTHING`), not a kept-parent
  relation, and `self.can_fast_delete(related_model, from_field=field)` is true,
  `deletion.py:217-224` (post). These gates are upstream of the modeled scheduler;
  they shape the `rels` input and are not part of the modeled decision.

## G-LEAK
The problem_statement talks about combining fast delete queries by table with
`OR` (`DELETE FROM … WHERE … OR …`); it does NOT contain `defaultdict`,
`model_fast_deletes`, `related_objects`, `get_del_batches`, `can_fast_delete`,
`reduce`, `operator.or_`, `query_utils`, or `Collector.collect`. The spec view
uses only neutral behavioral vocabulary ("cascading relation", "target table",
"joined column", "grouped by their target table", "single bulk operation"). The
modeled-function identifier `combineFastDeletes` shares no patched def/class name
(`related_objects`, `get_del_batches`, `can_fast_delete`, `collect`) as a
substring. The word "combine"/"combined" and "fast delete" appear in the public
problem_statement title ("Combine fast delete queries"), so they are public.

## Pinned G-CONF fuzz seed
`11885`.
