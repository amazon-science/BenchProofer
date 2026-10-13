# refinement.md — django__django-11265

The operation-by-operation correspondence between `model.py`'s two implemented
functions and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model is validated == a real callee by G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This change has **two independently-fixed behaviours** (two hunks in
`django/db/models/sql/query.py`), modeled as two contracted functions; there is
one verification-failing `model_prepatch_<k>.py` per behaviour (G-DIFF). There
are **no `@ContractOnly` axioms** and **no A-reference deep models of external
callees**: both behaviours are Django-internal data-flow/control-flow, spelled
out as pure logic. Hence no `axiom_check.py`.

## A. Site 1 — propagate the relation registry into the exclusion subquery

Gold hunk (`split_exclude`, `query.py:1668-1669`):
```
  query = Query(self.model)
+ query._filtered_relations = self._filtered_relations
  query.add_filter(filter_expr)
```

Model function: `propagate_relation_registry(outer_relations, referenced_alias)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `outer_relations: List[int]` | `self._filtered_relations` (a `dict` alias→FilteredRelation, `query.py:231`) | R | dict-of-aliases ↔ `List[int]` of alias tokens; `name in self._filtered_relations` ↔ `tok in ToSeq(outer_relations)` (mapping.md §2). |
| A2 | param `referenced_alias: int` with `Requires(referenced_alias in ToSeq(outer_relations))` | the annotation alias the exclude refers to (e.g. `'book_alice'`), declared on the outer query by `.annotate(book_alice=FilteredRelation(...))` | R + I | the F2P scenario annotates the alias on the outer query, so it is a member of the outer registry; an `int` token stands for the alias string. |
| A3 | the loop building `result` so that `ToSeq(result) == ToSeq(outer_relations)`, returned | `query._filtered_relations = self._filtered_relations` (assignment of the outer dict to the freshly-created inner `Query`'s registry) | I (under R) | the freshly-created `Query` starts with `_filtered_relations == {}` (`__init__`, `query.py:231`); the added line makes the inner registry equal the outer one. Modeled as returning a list equal to `outer_relations` — same content, so the same alias-membership facts. |
| A4 | postcondition `referenced_alias in ToSeq(Result())` | `query.add_filter(filter_expr)` → `names_to_path` resolving the alias without `FieldError` (`query.py:1669,1418,1448`) | I (under R) | `names_to_path` resolves `name` iff `name in self._filtered_relations` (`query.py:1418`), else raises `FieldError` (`query.py:1448`). Membership of the alias in the inherited registry IS resolvability — exactly what the F2P `test_with_exclude` requires (no FieldError). |

The discriminating content of site 1 — *propagating* the registry vs leaving it
empty — lives in `ToSeq(Result()) == ToSeq(outer_relations)` and its corollary
`referenced_alias in ToSeq(Result())`. `model_prepatch_1.py` reproduces the
fresh-empty registry (`return []`) and **fails** both clauses (G-DIFF).

## B. Site 2 — keep a filtered-relation leading join in the subquery

Gold hunk (`trim_start`, `query.py:2145`):
```
- if self.alias_map[lookup_tables[trimmed_paths + 1]].join_type != LOUTER:
+ first_join = self.alias_map[lookup_tables[trimmed_paths + 1]]
+ if first_join.join_type != LOUTER and not first_join.filtered_relation:
      ... (trim the leading join: unref alias, add extra_restriction) ...
```

Model function: `subquery_retained_filters(join_type, is_filtered_relation,
leading_filter, other_filters)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `join_type: int`, compared to `LOUTER()` | `first_join.join_type` compared to `LOUTER` (`query.py:2145`; `Join.join_type`, `datastructures.py:51`) | R | the join-kind string `'LEFT OUTER JOIN'`/`'INNER JOIN'` ↔ the `LOUTER()`/`INNER()` int tokens; only the equality `== LOUTER` is observed (mapping.md §2). |
| B2 | param `is_filtered_relation: bool` | `bool(first_join.filtered_relation)` (the `Join.filtered_relation` field, `datastructures.py:59`; `None`/falsy on a non-filtered join) | R | `not first_join.filtered_relation` ↔ `not is_filtered_relation`. |
| B3 | guard `may_trim_leading_join(...) == (join_type != LOUTER() and not is_filtered_relation)` deciding whether `leading_filter` is dropped | the `if` guard `first_join.join_type != LOUTER and not first_join.filtered_relation` deciding whether the leading join is collapsed | I (under R) | identical boolean structure; the added `not first_join.filtered_relation` conjunct ↔ the `not is_filtered_relation` conjunct. |
| B4 | result list: `leading_filter` kept iff not trimmable; `other_filters` always retained; pinned by value | collapsing the leading join removes it (and its filtered-relation ON-clause condition, `datastructures.py:89-90`) from the subquery FROM; keeping it preserves that condition (`query.py:2145-2158`) | I (under R) | `leading_filter ∈ Result()` ↔ "the leading join's filter condition stays in effect"; `other_filters` (downstream conditions) are untouched by the trim decision. |

The discriminating content of site 2 — a filtered-relation INNER join must NOT
be collapsed, or its ON-clause filter is silently dropped (the wrong-rows
symptom) — lives in `Implies(is_filtered_relation, ToSeq(Result()) ==
PSeq(leading_filter) + ToSeq(other_filters))`. `model_prepatch_2.py` reproduces
the pre-patch guard (`if join_type == LOUTER()` only — i.e. trim whenever not
LOUTER, ignoring the filtered relation) and **fails** that clause (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. Both changed operations are Django-internal:
registry propagation (site 1, a dict copy ↔ a list-equality) and an internal
trim decision (site 2, a boolean conjunction). Neither calls an unchanged opaque
library callee whose contract the proof consumes, so there is **no consumed
axiom** and **no A-reference deep model of an external callee** — hence no
`axiom_check.py`. The constants `LOUTER`/`INNER` are abstract tokens whose
concrete string values are immaterial (only `== LOUTER` is observed).

## D. verify(model) ⇒ resolved

`propagate_relation_registry` verifies only if its output carries every outer
alias, so the referenced alias resolves in the subquery (no FieldError) — site 1
(A3/A4). `subquery_retained_filters` verifies only if a filtered-relation leading
join's condition is preserved (never collapsed) — site 2 (B3/B4). By R (dict ↔
`List[int]` registry; join-kind string ↔ token; `Join.filtered_relation` ↔
bool) the two verified functions are the two gold hunks up to type refinement.
The gold patch resolves (G-RESOLVE). The only trust point is refinement fidelity
(this document, G-EQ); there are no axioms (no G-AX surface).
