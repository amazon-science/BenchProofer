# mapping.md — django__django-11265

## Symbol binding (file:line @ base_commit 21aa2a5e785eef1f47beb1c3760fdd7d8915ae09)

All code is in `django/db/models/sql/query.py`.

| Lean symbol | Python | location |
|---|---|---|
| `implementation_buildInnerQuery` / `problem_spec_buildInnerQuery` / `correct_buildInnerQuery` | the construction of the nested inner query inside `Query.split_exclude` (create a fresh `Query(self.model)`, carry the originating query's named relation definitions, apply the filter, drop ordering) | `query.py:1665-1669` @ base_commit (the `query = Query(self.model)` … `query.clear_ordering(True)` block); gold patch inserts `query._filtered_relations = self._filtered_relations` at line 1669 |
| `implementation_selectInnerJoin` / `problem_spec_selectInnerJoin` / `correct_selectInnerJoin` | the leading-join collapse decision inside `Query.trim_start` (whether the first join of the inner query can be trimmed, and which fields/alias are selected) | `query.py:2142-2156` @ base_commit (the `if self.alias_map[...].join_type != LOUTER:` … `else:` branch choosing `select_fields`/`select_alias`); gold patch replaces the guard with `first_join.join_type != LOUTER and not first_join.filtered_relation` |

## Modeled inputs

### buildInnerQuery — the inner-query construction in `split_exclude`

| Lean | Python reality | meaning |
|---|---|---|
| `selfModel : String` | `self.model` | the model the originating query is bound to; the inner query is `Query(self.model)` |
| `selfFilteredRelations : List (String × String)` | `self._filtered_relations` (an `OrderedDict alias -> FilteredRelation`) | the originating query's named filtered-relation definitions; modeled as alias→definition pairs |
| `filterExpr : String × String` | `filter_expr` (a `(lhs, rhs)` pair) | the filter clause applied to the inner query via `query.add_filter(filter_expr)` |

Output `result : InnerQuery`:

| Lean field | Python |
|---|---|
| `result.model` | the inner `Query`'s model (`Query(self.model)`) |
| `result.filteredRelations` | `query._filtered_relations` after construction — gold sets it to `self._filtered_relations` (pre-patch: left as the fresh `Query`'s empty default) |
| `result.appliedFilters` | the filter applied via `query.add_filter(filter_expr)`, paired with the `_filtered_relations` context present WHEN it was applied — `add_filter` resolves the clause against `query._filtered_relations`, so a clause referencing a named relation needs that relation already installed (the bug-critical ordering). Modeled as the singleton `[(filterExpr, filteredRelations-at-apply-time)]` |
| `result.orderingCleared` | the effect of `query.clear_ordering(True)` |

### selectInnerJoin — the leading-join collapse in `trim_start`

| Lean | Python reality | meaning |
|---|---|---|
| `firstJoin.keepsOuterRows : Bool` | `self.alias_map[lookup_tables[trimmed_paths + 1]].join_type == LOUTER` | the leading join is a LEFT OUTER join: collapsing it would drop rows with nothing on the inner side |
| `firstJoin.carriesRelationCondition : Bool` | `bool(first_join.filtered_relation)` | the leading join exists to apply a named relation's condition (a `Join.filtered_relation`); collapsing it would lose that restriction. **Pre-patch this observable is never consulted.** |
| `relatedFields : List (String × String)` | `join_field.related_fields` (pairs of `(near_field, far_field)`) | the join's related field pairs; `r[0]` is the near side, `r[1]` the far side |
| `aliasOriginal : String` | `lookup_tables[trimmed_paths]` | the alias of the leading join's source table (used when NOT collapsing) |
| `aliasCollapsed : String` | `lookup_tables[trimmed_paths + 1]` | the alias collapsed onto (used when collapsing) |

Output `result : JoinSelection`:

| Lean field | Python |
|---|---|
| `result.selectFields` | `select_fields` — `[r[0] for r in join_field.related_fields]` (collapse) or `[r[1] for r in join_field.related_fields]` (no collapse) |
| `result.selectAlias` | `select_alias` — `lookup_tables[trimmed_paths + 1]` (collapse) or `lookup_tables[trimmed_paths]` (no collapse) |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `self.model` (a model class) | `selfModel : String` | model identity ↦ its name string |
| `self._filtered_relations` OrderedDict | `selfFilteredRelations : List (String × String)` | `alias -> FilteredRelation` ↦ `(alias, definition-string)` pairs; equality is by the ordered pair list |
| `filter_expr` `(lhs, rhs)` | `filterExpr : String × String` | tuple ↦ pair of strings |
| `query._filtered_relations` after build | `result.filteredRelations` | identity on the pair-list model |
| `query.add_filter(filter_expr)` resolved against `query._filtered_relations` | `result.appliedFilters` | clause paired with the relation context at apply time; encodes that the filter resolves against the carried-over relations |
| `join_type == LOUTER` | `firstJoin.keepsOuterRows : Bool` | predicate ↦ Bool |
| `bool(first_join.filtered_relation)` | `firstJoin.carriesRelationCondition : Bool` | truthiness ↦ Bool |
| `join_field.related_fields` | `relatedFields : List (String × String)` | list of `(near, far)` field-name pairs |
| `select_fields`, `select_alias` | `result.selectFields`, `result.selectAlias` | identity on the field-name list / alias string |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** Both decisions are pure functions of observables
  already in hand at the decision point. `split_exclude` calls `Query(...)`,
  `add_filter`, `clear_ordering`, `trim_start` (UNCHANGED) and `trim_start` reads
  `self.alias_map`, `join_field.related_fields`, `lookup_tables` (UNCHANGED); their
  relevant outputs are taken as the model inputs. The decisions the patch CHANGES
  (carrying `_filtered_relations`; the `not first_join.filtered_relation` guard) are
  modeled DEEPLY (spelled out), so they are A-reference rows validated by G-CONF,
  never axiomatized (§0.7). `axiom_check.py` is a skip stub.
- **Flag dependency:** the leading-join decision depends on two booleans
  (`keepsOuterRows`, `carriesRelationCondition`); G-CONF fuzzes all four
  combinations. The inner-query decision has no flag dependency.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py`).
