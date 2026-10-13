# refinement.md — django__django-11885

Maps every operation in `implementation_combineFastDeletes` to its `patch.diff`
counterpart in `Collector.collect` (`django/db/models/deletion.py`, the
`collect_related` fast-delete grouping). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed op
validated == real callee, **I** identical concrete op.

## Patch (post-patch fast-delete grouping)
```python
model_fast_deletes = defaultdict(list)
for related in get_candidate_relations_to_delete(model._meta):
    ...
    related_model = related.related_model
    if self.can_fast_delete(related_model, from_field=field):
        model_fast_deletes[related_model].append(field)
        continue
    ...
for related_model, related_fields in model_fast_deletes.items():
    batches = self.get_del_batches(new_objs, related_fields)
    for batch in batches:
        sub_objs = self.related_objects(related_model, related_fields, batch)
        self.fast_deletes.append(sub_objs)
```
The modeled value is the SCHEDULE of fast-delete operations: post-patch, one
combined entry per target table carrying all that table's join columns
(`model_fast_deletes.items()`), versus pre-patch one entry per relation.

## Operation correspondence
| # | Lean op (`implementation_combineFastDeletes`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut groups : List (Table × List Column) := []` | `model_fast_deletes = defaultdict(list)` | I | the grouping accumulator starts empty. |
| 2 | `for p in rels do` | `for related in get_candidate_relations_to_delete(model._meta): … if self.can_fast_delete(related_model, …): … append` | R | iterate over the fast-deletable relations in discovery order; each `p = (related_model, field.name)`. The `can_fast_delete`/`DO_NOTHING`/keep-parent gating is upstream and pre-filters `rels` (mapping.md). |
| 3 | `if groups.any (fun q => q.1 == p.1) then groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)` | `model_fast_deletes[related_model].append(field)` when `related_model` already a key | R | `defaultdict(list)` append to an existing key ↔ append the join column to the matching table's column list; insertion order of the key list preserved. |
| 4 | `else groups := groups ++ [(p.1, [p.2])]` | `model_fast_deletes[related_model].append(field)` when `related_model` is new | R | first occurrence of a table creates a new dict key at the end ↔ append a new `(table, [column])` entry at the end (first-discovery key order). |
| 5 | `return groups` | `for related_model, related_fields in model_fast_deletes.items(): … self.related_objects(related_model, related_fields, batch); self.fast_deletes.append(sub_objs)` | R | the materialized `.items()` (one combined op per table, columns in append order) ↔ returning `groups`. Each entry becomes ONE `self.related_objects(related_model, related_fields, …)` call combining all of that table's join columns (the `OR`-combined `Q(**{f__in})` predicate). |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — the relation selection enters as the `rels` data per
mapping.md). Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`. The shadow groups `(table, column)` pairs exactly as the
post-patch `defaultdict(list)` + `.items()` does (insertion-ordered keys,
append-ordered values); the oracle uses a real Python `defaultdict(list)`.

## Prepatch = the real bug
Pre-patch, the fast-delete branch did
`self.fast_deletes.append(sub_objs)` once per relation inside the
`for related … for batch …` loops — one bulk operation per cascading relation,
never combined by table. The prepatch impl
(`for p in rels do groups := groups ++ [(p.1, [p.2])]`) is exactly this: it emits
one singleton entry per relation and never merges relations that target the same
table. It therefore cannot satisfy `problem_spec_combineFastDeletes` whenever two
relations share a target table (`groupByTable` merges them into one entry, the
buggy impl keeps two) — precisely the case the FAIL_TO_PASS test
`test_fast_delete_combined_relationships` exercises (a `Referrer` referenced
through two cascading columns must be deleted by a SINGLE combined query, i.e.
`assertNumQueries(2)` rather than 3). The carried gold proof fails to typecheck
against the buggy impl (G-DIFF).
