# refinement.md — django__django-11265

Operation-by-operation correspondence between `Solution.lean`'s two `do` blocks
(`inheritedFilteredRelations`, `canRemoveLeadingJoin`) and `patch.diff` (the gold
patch, two hunks in `django/db/models/sql/query.py`). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — none here), or **I** (identical
concrete op). EVERY step is R, A, or I. No kind-3 (changed-inexpressible) ops.

The R/I legs would normally be mechanically refuted by **G-CONF**; for this
bundle they cannot be (conf_skip=true, §D below) and are carried by G-VERIFY +
G-DIFF instead. There are no A legs.

`patch.diff` is the gold patch **verbatim** (applies at base_commit, resolves —
G-RESOLVE).

## A. Site 1 — `split_exclude` inherits the filtered-relation registry

Gold hunk (`query.py`, in `split_exclude`):
```
         # Generate the inner query.
         query = Query(self.model)
+        query._filtered_relations = self._filtered_relations
         query.add_filter(filter_expr)
```

| # | Solution.lean impl op (`inheritedFilteredRelations`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `outerRelations : List Name` | `self._filtered_relations` (the originating query's registry dict) | **R** | `dict {alias: FilteredRelation}` ↔ `List Name`: observed only by recognised key set (mapping.md §2). Free input — unchanged by the fix. |
| A2 | `let out := outerRelations` | `query._filtered_relations = self._filtered_relations` (the added line) | **I** | identical concrete op: the freshly-built inner subquery's registry is set to the originating query's registry. Python reference assignment of the dict ↔ Lean `out = outerRelations` (same recognised set; mapping.md §2). This is the CHANGED op, modeled deeply as the list copy. |
| A3 | `return out` | the subquery `query` carrying the inherited registry feeds `query.add_filter(...)` / `names_to_path` (`query.py:1670`, UNCHANGED) | **R** | the downstream resolver is unchanged; the spec's second clause `∀ n ∈ outerRelations, resolves out n false` states the consequence — a lookup naming an inherited relation now resolves in the subquery instead of raising `FieldError`. `names_to_path` not raising ↔ `resolves` (mapping.md §2). |

## B. Site 2 — `trim_start` keeps filtered-relation joins

Gold hunk (`query.py`, in `trim_start`):
```
-        if self.alias_map[lookup_tables[trimmed_paths + 1]].join_type != LOUTER:
+        first_join = self.alias_map[lookup_tables[trimmed_paths + 1]]
+        if first_join.join_type != LOUTER and not first_join.filtered_relation:
             select_fields = [r[0] for r in join_field.related_fields]
```

| # | Solution.lean impl op (`canRemoveLeadingJoin`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `preservesUnmatchedRows : Bool` | `self.alias_map[lookup_tables[trimmed_paths + 1]].join_type == LOUTER` | **R** | the join's `join_type == LOUTER` predicate ↔ `Bool` (mapping.md §2). Free input — the alias_map lookup is unchanged. |
| B2 | parameter `carriesOwnFilter : Bool` | `first_join.filtered_relation` truthiness | **R** | `FilteredRelation or None` ↔ `Bool` by truthiness (mapping.md §2). Free input — the attribute is set by unchanged join-construction code. |
| B3 | `let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)` | `first_join.join_type != LOUTER and not first_join.filtered_relation` | **I** + **R** | the CHANGED op, modeled deeply: Python `!=`/`and`/`not` ↔ Lean `!`/`&&`/`!` over the bool bijection. `join_type != LOUTER` ↔ `! preservesUnmatchedRows`; `not first_join.filtered_relation` ↔ `! carriesOwnFilter`. The pre-patch guard lacked the second conjunct. |
| B4 | `return out` | whether the trim branch (`unref_alias(...)`, narrowed `select_fields`, `:2148-2152`) is taken vs. the `else` (join kept) | **R** | the branch taken ⟺ the gate boolean (mapping.md §2). The trim/keep machinery in both branches is unchanged; only the guard deciding between them changed. |

## C. Independently-fixed behaviours & the prepatches (G-DIFF)

The single F2P test `test_with_exclude` exercises BOTH fixed behaviours; each is
independently observable and each gets its own failing prepatch with the
byte-identical spec:

- **`Solution_prepatch.lean`** (site 1 reverted): the inner subquery is built
  with an EMPTY registry (`let out := []`), the pre-patch state — the subquery
  does not recognise the originating query's filtered relations, so a lookup
  naming one fails to resolve (the `FieldError` the issue's traceback shows).
  The frozen spec demands `out = outerRelations` and that every inherited name
  resolves, so `prove_correct` fails on exactly:
  ```
  case «ensures_1: ∀ n, n ∈ outerRelations → resolves out n false»
  ⊢ ∀ n ∈ outerRelations, resolves [] n false        -- unprovable: registry dropped
  case «ensures_2: out = outerRelations»
  ⊢ [] = outerRelations                               -- unprovable
  ```
- **`Solution_prepatch_2.lean`** (site 2 reverted): the trim guard considers
  ONLY `! preservesUnmatchedRows` (`let out := (! preservesUnmatchedRows)`), the
  pre-patch guard — a leading inner join from a filtered relation
  (`preservesUnmatchedRows = false`, `carriesOwnFilter = true`) is judged
  removable and its filter is silently dropped (the wrong rows the hints'
  maintainer discussion reports). The frozen spec demands the full two-conjunct
  `joinRemovable`, so `prove_correct` fails on exactly:
  ```
  case «ensures_1: out = joinRemovable preservesUnmatchedRows carriesOwnFilter»
  ⊢ (!preservesUnmatchedRows) = joinRemovable preservesUnmatchedRows carriesOwnFilter
  ```
  (false at `preservesUnmatchedRows = false, carriesOwnFilter = true`).

Both prepatches fail; G-DIFF passes. Both hunks are required for the test: site 1
fixes the error, site 2 fixes the result — a verifying impl reverting either
would refine to a non-resolving patch, which is why both are modeled (directive
4, verify ⟹ correct).

## D. No kind-3; G-CONF conf_skip=true

Every step is R, A, or I. The two operations that genuinely *changed* — the
registry inheritance (A2, **I**) and the strengthened trim guard (B3, **I**+**R**)
— are modeled **deeply** as the list copy and the boolean expression, not hidden
behind axioms. There are no consumed axioms: the unchanged downstream machinery
(name resolution, join construction, SQL compilation) is folded into free inputs
(`outerRelations`, `preservesUnmatchedRows`, `carriesOwnFilter`), about which the
spec claims nothing beyond their use in the modeled decision — so there is
nothing for G-AX.

`conformance_check.py` is a documented `status=skip` stub: the only
discriminating observable is the queryset result / `FieldError` on a live Django
ORM + database — there is no DB-free, input-dependent R/I shadow to
differential-test (mapping.md §4). Soundness is carried by G-VERIFY (the spec
provably forces `out = outerRelations` with every inherited name resolving, and
the full two-conjunct trim guard) and G-DIFF (the two prepatches fail exactly the
discriminating clauses). Precedent: django__django-11451, django__django-11179.
