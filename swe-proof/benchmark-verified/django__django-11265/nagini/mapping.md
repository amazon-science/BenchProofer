# mapping.md — django__django-11265

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 21aa2a5e785eef1f47beb1c3760fdd7d8915ae09`, states the type
abstraction, and records callee provenance. Repo file under change:
`django/db/models/sql/query.py`.

There are **no `@ContractOnly` axioms** in this bundle: both modeled behaviours
are pure data-flow / control-flow over abstract registry and join tokens, spelled
out in full. No unchanged opaque library callee's contract is consumed, so there
is no `axiom_check.py` (nothing external to validate).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `propagate_relation_registry(outer_relations, referenced_alias)` | `split_exclude(self, filter_expr, can_reuse, names_with_path)` — `django/db/models/sql/query.py:1645` (body line 1668-1669) | modeled changed function (site 1): the inner subquery built for an exclude over an N-to-many relation must carry the outer query's filtered-relation registry so the exclude's referenced alias resolves |
| `subquery_retained_filters(join_type, is_filtered_relation, leading_filter, other_filters)` | `trim_start(self, names_with_path)` — `django/db/models/sql/query.py:2098` (body line 2145) | modeled changed function (site 2): the decision whether the inner query's leading join may be trimmed, and the consequence for that join's filter condition |
| `LOUTER` | `django.db.models.sql.constants.LOUTER` (`'LEFT OUTER JOIN'`), `query.py:2145` | int token for the left-outer join kind |
| `INNER` | `django.db.models.sql.constants.INNER` (`'INNER JOIN'`) | int token for the inner join kind |

## 2. Type abstraction (R-refinements)

### Site 1 — `split_exclude`
| repo reality | model carrier | bijection |
|---|---|---|
| `self._filtered_relations` — a `dict` mapping annotation alias → `FilteredRelation` (set in `Query.__init__`, `query.py:231`; resolved in `names_to_path`, `query.py:1418`) | `outer_relations: List[int]` — the list of declared relation-alias tokens | each annotated relation alias (e.g. `'book_alice'`) ↔ an `int` token; `name in self._filtered_relations` ↔ `tok in ToSeq(outer_relations)`; the new inner query's `_filtered_relations` (`{}` pre-patch) ↔ the model's `Result()` list |
| `query = Query(self.model)` then `query._filtered_relations = self._filtered_relations` (added line) | constructing and returning the inner registry equal to the outer's | the freshly-created `Query`'s `_filtered_relations` starts `{}` (`__init__` line 231); the patch overwrites it with the outer's dict (a shared reference). Modeled as returning a list equal to `outer_relations`. |
| `query.add_filter(filter_expr)` → `names_to_path` resolving the alias (`query.py:1669,1418,1448`) | the requirement `referenced_alias in ToSeq(Result())` | `names_to_path` resolves `name` only if `name in self._filtered_relations` (else `FieldError`, `query.py:1448`). Resolvability ↔ the alias being a member of the inner registry. |

### Site 2 — `trim_start`
| repo reality | model carrier | bijection |
|---|---|---|
| `first_join = self.alias_map[lookup_tables[trimmed_paths + 1]]` — the inner query's leading join (`query.py`, a `Join`/`BaseTable` in `datastructures.py:26/142`) | `join_type: int` + `is_filtered_relation: bool` | `first_join.join_type` (`'LEFT OUTER JOIN'`/`'INNER JOIN'`) ↔ `join_type` (`LOUTER`/`INNER` tokens); `bool(first_join.filtered_relation)` (the `Join.filtered_relation` field, `datastructures.py:59`; `None` on a `BaseTable`/non-filtered join) ↔ `is_filtered_relation` |
| `join_field.get_extra_restriction(...)` added to `self.where` only when the leading join is trimmed; otherwise the leading join (and its `filtered_relation` ON-clause condition, `datastructures.py:89-90`) stays in the FROM clause and its filter remains in effect (`query.py:2145-2158`) | `leading_filter: int` (the leading join's filter-condition token) + `other_filters: List[int]` (downstream conditions, always retained); `Result(): List[int]` is the set of filter conditions still in effect on the subquery | trimming the leading join removes it (and thus its filtered-relation ON condition) from the subquery; not trimming keeps it. `leading_filter ∈ Result()` ↔ "the leading join's filter condition is preserved on the subquery". |
| `if self.alias_map[...].join_type != LOUTER:` (pre-patch trim guard) → `if first_join.join_type != LOUTER and not first_join.filtered_relation:` (post-patch) | trim-the-leading-join decision = `join_type != LOUTER and not is_filtered_relation` | the patch ANDs in `not first_join.filtered_relation`: an INNER join coming from a filtered relation must NOT be trimmed, or its ON-clause filter is silently dropped (the bug's wrong-rows symptom) |

`str`/dict/object indexing is banned/awkward in Nagini, so registries and
condition sets are carried as `List[int]` of opaque tokens and the
specification is phrased over `PSeq[int]` via `ToSeq`. Booleans (`is_filtered_relation`)
and the two join-kind tokens are concrete.

## 3. Callee provenance

None. Both sites are modeled deeply; no `@ContractOnly` is consumed and no deep
model stands in for an external callee (no A-reference). The behaviour pinned is
entirely Django-internal registry propagation (site 1) and an internal trim
decision (site 2), both spelled out as pure logic. The constants `LOUTER`/`INNER`
are abstract tokens (their concrete string values are immaterial; only the
equality `join_type == LOUTER` is observed), bound above for the audit trail.
