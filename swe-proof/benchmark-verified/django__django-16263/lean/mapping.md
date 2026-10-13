# mapping.md — django__django-16263

Cold construction (`spec_provenance: cold`): derived from `problem_statement`,
the gold `patch`, the `test_patch`, and the real source at
`base_commit 321ecb40f4da842926e1bc07e11df4aabe53ca4b`.

## Modeled function

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_countPlan` / `problem_spec_countPlan` / `correct_countPlan` | the count/aggregate query-planning decision inside `Query.get_aggregation` | `django/db/models/sql/query.py:438-547` |

The FAIL_TO_PASS tests (`AggregateAnnotationPruningTests`) observe the SQL a
`.count()` produces over a queryset carrying extra annotations/aliases:
- `test_unused_aliased_aggregate_pruned` — an aliased `Count` (added via
  `.alias(...)`, **not** selected): exactly one `SELECT` (no wrapping subquery),
  alias name absent from SQL.
- `test_non_aggregate_annotation_pruned` — a selected non-aggregate annotation
  (`Lower("name")`): exactly one `SELECT` (no wrapping subquery), name absent.
- `test_unreferenced_aggregate_annotation_pruned` — a selected aggregate
  annotation (`Count("authors")`) that nothing references: **two** `SELECT`s
  (subquery required) but the annotation alias absent from the SQL (pruned).

These two observable behaviors are exactly the two decisions the bundle models:
(1) **whether a wrapping subquery is needed** and (2) **which already-present
annotations survive into the emitted query**.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Lean | Python |
|---|---|
| `Ann` | one entry `(alias, annotation)` of `Query.annotation_select` |
| `Ann.aliasName : String` | the alias (dict key) |
| `Ann.selected : Bool` | the alias is in the *selected* annotation set (`annotation_select`); a `.alias(...)` clause is present in `annotations` but **not** `annotation_select`, so `selected = false` |
| `Ann.containsAggregate : Bool` | `getattr(annotation, "contains_aggregate", True)` |
| `Ann.containsOverClause : Bool` | `getattr(annotation, "contains_over_clause", True)` |
| `Ann.added : Bool` | alias ∈ `added_aggregate_names` (the summary aggregate(s) `get_count`/`aggregate` injected, e.g. `__count`) |
| `Ann.refs : List String` | `annotation.get_refs()` — the alias names this expression references (post-patch `Ref.get_refs` / `BaseExpression.get_refs` / `WhereNode.get_refs`) |
| `QState.groupByTuple : Bool` | `isinstance(self.group_by, tuple)` |
| `QState.isSliced : Bool` | `self.is_sliced` |
| `QState.distinct : Bool` | `self.distinct` |
| `QState.combinator : Bool` | `self.combinator` (truthy) |
| `QState.postGroupFilter : Bool` | `any(self.where.split_having_qualify()[1:])` (HAVING / QUALIFY filters) |
| `Plan.useSubquery : Bool` | the `if (... ) :` branch in `get_aggregation` is taken (an `AggregateQuery` subquery is built) |
| `Plan.keptExisting : List String` | the already-present aliases still materialised in the inner query's `annotation_select_mask` after masking |

### Post-patch decision modeled (the spec)

```
existing = { (alias, ann) in annotation_select : alias not in added_aggregate_names }
has_existing_aggregation =
    any( contains_aggregate or contains_over_clause  for ann in existing )
    or any( where.split_having_qualify()[1:] )
useSubquery = group_by_tuple or is_sliced or has_existing_aggregation
              or distinct or combinator
# inside the subquery branch the inner mask starts at annotation_select
# (set_annotation_mask(self.annotation_select)); the ref-based REBUILD of the
# mask lives inside `if not inner_query.distinct:` and is therefore SKIPPED for
# distinct queries (re-masking would alter the distinct row set):
if distinct:
    # mask stays at annotation_select: every materialised existing clause
    # survives (verified vs patched worktree: LOWER(...) AS "name_lower"
    # remains in the inner SELECT of a .distinct().count(); final
    # set_annotation_mask trace = {'name_lower'} after the summary moves out)
    keptExisting = [ a.alias for a in anns if (not a.added) and a.selected ]
else:
    # the inner annotation mask is rebuilt from the added aggregates' own
    # names plus their get_refs():
    addedMask = ⋃ { name } ∪ added[name].get_refs()  for name in added_aggregate_names
    # set_annotation_mask(addedMask) REPLACES the inner mask, so a carried
    # clause survives iff its alias is in addedMask — irrespective of whether
    # it was materialised (selected). Hence this keep-set filters on
    # (not added), NOT on selected: an aliased, non-selected clause referenced
    # by an added aggregate is kept inside the subquery.
    keptExisting = [ a.alias for a in anns if (not a.added) and a.alias in addedMask ]
# (when no subquery is needed, no existing annotation is materialised at all)
```

### 2026-08 G-PANEL-2 repair note

The original spec applied the ref-based keep-set unconditionally inside the
subquery branch. G-PANEL-2 exhibited the divergence: with `distinct=True` and a
selected non-aggregate annotation (`name_lower`) unreferenced by the added
`total`, the real repo KEEPS `name_lower` (the masking block is guarded by
`if not inner_query.distinct:`), while the spec demanded `keptExisting = []`.
The spec/impl/oracle now branch on `distinct` exactly as the real code does
(re-verified empirically on a /tmp checkout at base_commit + gold patch:
distinct keeps the full `annotation_select` mask; sliced/combinator non-distinct
queries still prune to the ref-rebuilt mask).

`existing` is keyed off `annotation_select` (post-patch), **not** `annotations`
(pre-patch). This is why an *aliased* `Count` (in `annotations` but absent from
`annotation_select`, modeled `selected=false`) does not appear in `existing` and
therefore forces neither a subquery nor masking.

## Callee provenance + flag deps

- `get_refs()` (`Ref.get_refs`, `BaseExpression.get_refs`, `WhereNode.get_refs`)
  is **introduced by the patch** — it is part of the fixed behavior, so it is
  modeled deeply as the `Ann.refs` field (an A-reference validated by G-CONF),
  never an axiom.
- `contains_aggregate` / `contains_over_clause` are unchanged attributes read via
  `getattr(..., default=True)`; modeled as the boolean fields `containsAggregate`
  / `containsOverClause`. The `default=True` (missing-attribute) case is the
  conservative "treat as aggregate" behavior and is exercised by the fuzzer.
- `where.split_having_qualify()` is unchanged; only the truthiness of its
  post-WHERE components matters here, modeled as `postGroupFilter`.

No callee is consumed as an `axiom <callee>_prop`: every quantity the decision
reads is data on the modeled carrier, and the decision is spelled out directly.

## G-CONF fuzz seed

Pinned seed: **16263** (also in `conformance_check.py`).
