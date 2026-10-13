# refinement.md — django__django-11265

Operation correspondence between the two implementations and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real behavior by
G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. Both decisions are modeled DEEPLY over the
observables in hand. Every row is **R**, **A-reference**, or **I**. The R/I/
A-reference legs are differential-tested by G-CONF; G-AX is a skip stub.

## What the gold patch changes (`django/db/models/sql/query.py`)

Two coupled edits, both addressing `exclude(...)` over an annotated
`FilteredRelation`:

1. **`split_exclude` — carry the named relation definitions onto the inner query**
   (insertion at the inner-query construction):
   ```python
   query = Query(self.model)
   query._filtered_relations = self._filtered_relations   # <-- added
   query.add_filter(filter_expr)
   query.clear_ordering(True)
   ```
   Without this, a filter that references a named filtered-relation alias cannot
   be resolved inside the freshly-built inner query (the `FieldError` in the
   issue).

2. **`trim_start` — do not collapse a leading join that carries a relation
   condition** (guard strengthened):
   ```python
   # pre-patch:
   if self.alias_map[lookup_tables[trimmed_paths + 1]].join_type != LOUTER:
   # post-patch:
   first_join = self.alias_map[lookup_tables[trimmed_paths + 1]]
   if first_join.join_type != LOUTER and not first_join.filtered_relation:
   ```
   An INNER join created for a filtered relation carries the relation's condition;
   collapsing it into a plain column select would drop that condition, producing
   wrong results.

## `implementation_buildInnerQuery` ↔ the patched `split_exclude` block

The construction is modeled compositionally — `freshInnerQuery`,
`withFilteredRelations`, `addFilter`, `clearOrdering` applied IN THE PATCH ORDER —
so the sequencing the bug is about is observable: `addFilter` snapshots the
relation context present when the filter is applied. A filter applied before the
relations are carried over resolves against `[]` (exactly the `FieldError` the
issue reports), which the spec rejects.

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `selfModel`, `selfFilteredRelations`, `filterExpr` | `self.model`, `self._filtered_relations`, `filter_expr` | R | observables at the construction point (mapping.md bijection) |
| `freshInnerQuery selfModel` | `query = Query(self.model)` (fresh query: empty `_filtered_relations`, no filters, ordering not yet cleared) | I | a fresh inner query bound to the same model |
| `withFilteredRelations query selfFilteredRelations` | `query._filtered_relations = self._filtered_relations` (**the added line**) | A-reference | the EDITED op: carry the named relation definitions onto the inner query BEFORE the filter is applied; validated == real assignment by G-CONF |
| `addFilter query filterExpr` (records `(filterExpr, query.filteredRelations)`) | `query.add_filter(filter_expr)` | R | applying the filter clause; `add_filter` (UNCHANGED) resolves the clause against `query._filtered_relations` as it stands — modeled as recording the clause paired with the relation context present at this point (the bug-critical sequencing) |
| `clearOrdering query` | `query.clear_ordering(True)` | R | dropping any ordering; modeled as the boolean effect |

## `implementation_selectInnerJoin` ↔ the patched `trim_start` block

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `firstJoin.keepsOuterRows`, `firstJoin.carriesRelationCondition`, `relatedFields`, `aliasOriginal`, `aliasCollapsed` | `join_type == LOUTER`, `bool(first_join.filtered_relation)`, `join_field.related_fields`, `lookup_tables[trimmed_paths]`, `lookup_tables[trimmed_paths + 1]` | R | observables at the decision point |
| `let canCollapse := (!keepsOuterRows) && (!carriesRelationCondition)` | `first_join.join_type != LOUTER and not first_join.filtered_relation` (**the edited guard**) | A-reference | the EDITED decision: collapse only when the join keeps no outer rows AND carries no relation condition; validated == real guard by G-CONF |
| `if canCollapse then return {selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed}` | `select_fields = [r[0] for r in join_field.related_fields]; select_alias = lookup_tables[trimmed_paths + 1]` (the `if` branch) | I | collapse: near-side names against the collapsed alias |
| `else return {selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal}` | `select_fields = [r[1] for r in join_field.related_fields]; select_alias = lookup_tables[trimmed_paths]` (the `else` branch) | I | no collapse: far-side names against the original alias |

The unref/extra-restriction side effects inside the collapse branch
(`self.unref_alias(...)`, `self.where.add(extra_restriction, AND)`) are unchanged
by the patch and not observable in the modeled `select_fields`/`select_alias`
output; they are outside the modeled decision (the patch only changes whether the
branch is TAKEN, which is exactly `canCollapse`).

## Independently-observable behaviors (G-DIFF)

Two prepatch variants, one per coupled edit; each carries the gold proof body
(supplied by the proof agent), which fails to close on its discriminating clause:

- **`Solution_prepatch.lean`** — omits `withFilteredRelations`, so the filter is
  applied to a query with no named relations. Fails `correct_buildInnerQuery`
  whenever `selfFilteredRelations ≠ []`: the spec demands
  `result.filteredRelations = selfFilteredRelations` AND
  `result.appliedFilters = [(filterExpr, selfFilteredRelations)]`, but the buggy
  impl yields `filteredRelations = []` and an applied-filter entry resolved against
  `[]`. This is the FAIL_TO_PASS behavior (`test_with_exclude`: the inner query of
  an excluded annotated FilteredRelation must know the relation definition when the
  filter is resolved).

- **`Solution_prepatch_2.lean`** — collapses the leading join whenever it keeps no
  outer rows, ignoring `carriesRelationCondition`
  (`canCollapse := !keepsOuterRows`). Fails `correct_selectInnerJoin` whenever the
  join keeps no outer rows but DOES carry a relation condition
  (`keepsOuterRows = false`, `carriesRelationCondition = true`): the spec demands
  `canCollapse = false` (far-side names, original alias), but the buggy impl
  collapses (near-side names, collapsed alias). This isolates the
  `not first_join.filtered_relation` guard.

Both variants keep the spec view byte-identical to `Solution.lean` (the edits are
inside the elided `impl` regions).
