# mapping.md — django__django-11265

Binds `Solution.lean` symbols to the repo at
`base_commit = 21aa2a5e785eef1f47beb1c3760fdd7d8915ae09`.

Repo file under change: `django/db/models/sql/query.py`. The fix has two
hunks, in two methods of `django.db.models.sql.query.Query`:

1. `split_exclude(self, filter_expr, can_reuse, names_with_path)` —
   `query.py:1645` (added line at `:1669`); the inner subquery built to rewrite
   a negated N-to-many lookup must inherit the originating query's
   filtered-relation registry.
2. `trim_start(self, names_with_path)` — `query.py:2118` (changed guard at
   `:2143`); the leading-join trimming guard must also refuse to trim a join
   introduced by a named filtered relation.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `inheritedFilteredRelations (outerRelations : List Name)` | the `query = Query(self.model)` construction inside `split_exclude` (`query.py:1668`), and the added line `query._filtered_relations = self._filtered_relations` (`query.py:1669`) | the modeled changed behaviour at site 1: the registry the inner subquery recognises |
| `outerRelations` | `self._filtered_relations` of the originating `Query` (the dict `{alias: FilteredRelation}` maintained at `query.py:231,1388`) | FREE INPUT: the named filtered relations the originating query recognises |
| `out` (return of `inheritedFilteredRelations`) | the inner `query._filtered_relations` after the added assignment | the registry the subquery recognises |
| `resolves recognised name isField` | `Query.names_to_path` / `solve_lookup_type` name resolution (`query.py:1389`, the `FieldError`-raising path; `query.py:667,1418` consult `self._filtered_relations`) | pure spec: whether a lookup name resolves — directly if it names a model field, else only if recognised as a filtered relation |
| `canRemoveLeadingJoin (preservesUnmatchedRows) (carriesOwnFilter)` | the leading-join trimming guard in `trim_start` (`query.py:2143`, changed) | the modeled changed behaviour at site 2: whether the first inner join may be trimmed |
| `preservesUnmatchedRows` | `self.alias_map[lookup_tables[trimmed_paths + 1]].join_type == LOUTER` (`query.py:2143`; `LOUTER = 'LEFT OUTER JOIN'`, `sql/constants.py:27`) | FREE INPUT: whether the leading join is a LEFT OUTER JOIN (preserves rows with nothing on the outer side) |
| `carriesOwnFilter` | `first_join.filtered_relation` truthiness (`query.py:2147` post-patch; `Join.filtered_relation`, `sql/datastructures.py:59`) | FREE INPUT: whether the leading join was introduced by a named filtered relation and so carries its own filter condition |
| `out` (return of `canRemoveLeadingJoin`) | whether the `if …:` branch that trims the join (`self.unref_alias(...)`, `select_fields = [r[0] …]`) is taken (`query.py:2144-2152`) | the trim decision |
| `joinRemovable preservesUnmatchedRows carriesOwnFilter` | the post-patch guard expression `first_join.join_type != LOUTER and not first_join.filtered_relation` (`query.py:2147`) | pure spec: the trim condition |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self._filtered_relations` : a `dict {alias: FilteredRelation}` | `List Name` (`Name := Nat`) | the registry is observed only by which aliases (names) it RECOGNISES; `dict` keys ↔ list elements; `name in self._filtered_relations` ↔ `name ∈ outerRelations`. Concrete `FilteredRelation` objects (values) are never inspected by the modeled decision, only the key set. Assignment `query._filtered_relations = self._filtered_relations` ↔ `out = outerRelations` (same recognised set). |
| a filtered-relation alias, e.g. `'book_alice'` | `Name := Nat` | a present alias; the guard observes only presence/recognition, never its spelling. |
| `join.join_type == LOUTER` (a `str` compared to `'LEFT OUTER JOIN'`) | `Bool` (`preservesUnmatchedRows`) | `true` ↔ the join is a LEFT OUTER JOIN; `false` ↔ any other join type (e.g. `INNER JOIN`). `join_type != LOUTER` ↔ `! preservesUnmatchedRows`. |
| `first_join.filtered_relation` (a `FilteredRelation` or `None`) | `Bool` (`carriesOwnFilter`) | `true` ↔ truthy (`not None`): the join was built from a named filtered relation and carries its filter; `false` ↔ `None`. `not first_join.filtered_relation` ↔ `! carriesOwnFilter`. |
| "the lookup name resolved (no `FieldError`)" | `Prop` (`resolves …`) | `resolves recognised name isField` ↔ `names_to_path` returns instead of raising `FieldError`: a model-field name (`isField = true`) resolves directly; a filtered-relation name resolves iff `name ∈ recognised`. |
| "the leading join was trimmed" | `Bool` (`out` of `canRemoveLeadingJoin`) | `true` ↔ the `if first_join.join_type != LOUTER and not first_join.filtered_relation:` branch taken (`unref_alias`, narrowed `select_fields`); `false` ↔ the `else` branch (join kept). |

`Name` is modeled as `Nat` because the registry is observed only through
membership/recognition (`∈`), never the underlying `FilteredRelation` value;
those values flow untouched through the unchanged join-construction and
SQL-compilation machinery.

## 3. Callee provenance

No axioms and no A-reference deep models.

- **Site 1 (`split_exclude`).** The unchanged machinery the inherited registry
  feeds into — `query.add_filter(...)`, `names_to_path`, `solve_lookup_type`,
  `trim_start`, and ultimately SQL compilation — is NOT altered by the fix. The
  patch adds exactly one assignment (`query._filtered_relations =
  self._filtered_relations`); it does not change how the registry is consulted.
  The originating query's registry is the **free input** `outerRelations`. The
  spec claims only that the subquery recognises the SAME set, so a name in it
  resolves there — holding for EVERY value of `outerRelations`. Nothing to check
  against a real callee → **no G-AX**.
- **Site 2 (`trim_start`).** The unchanged machinery — `alias_map`,
  `unref_alias`, `get_extra_restriction`, `set_select` — is not altered; the
  patch only strengthens the trim GUARD with the extra conjunct `and not
  first_join.filtered_relation`. The two join properties are **free inputs**
  (`preservesUnmatchedRows`, `carriesOwnFilter`); the spec is a pure boolean
  decision over them, holding for every value. Nothing to check → **no G-AX**.
- The CHANGED ops (site 1's registry inheritance, site 2's strengthened guard)
  are modeled **deeply** as the list copy and the boolean expression
  (I/R-tagged, refinement.md). No outside contract is consumed.

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub (`meta.json conf_skip=true`).

The fix's only DISCRIMINATING observable is the **queryset result** — the rows
returned by `Author.objects.annotate(book_alice=FilteredRelation(...)).exclude(
book_alice__isnull=False)` — together with a side effect at site 1 (whether a
`FieldError` is raised). Both materialize only against a **live Django ORM + a
real database**: a configured model layer, a SQL compiler, and a populated
database against which the generated subquery actually runs. To observe "the
annotation resolved in the subquery" / "the filtered-relation join's filter was
preserved" one must execute the F2P integration test itself
(`test_with_exclude`), not a DB-free transliteration this gate could fuzz over
≥10⁵ inputs.

There is no DB-free, input-dependent R/I shadow to differential-test:

- Site 1's modeled op is a registry copy (`out = outerRelations`); its only
  consequence (a lookup resolving instead of raising `FieldError`) is a property
  of the unchanged downstream resolver running against a live query — not a value
  this gate computes.
- Site 2's modeled op is a 2-bit boolean decision over two free inputs
  (`preservesUnmatchedRows`, `carriesOwnFilter`); whether trimming that join
  actually changes the returned rows depends on the rest of the live query and
  the database contents, which a pure shadow cannot reproduce.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the modeled op's only discriminating
observable is a result/side effect on a live ORM + DB with no DB-free R/I
shadow, set `meta.json conf_skip=true` and ship a `status=skip` stub (precedent:
django__django-11451, django__django-11179). Soundness of the modeled behaviour
is carried instead by **G-VERIFY** (the spec provably forces both
`out = outerRelations` with every inherited name resolving, and the full
two-conjunct trim guard) and **G-DIFF** (the two prepatches, each reverting one
site, fail on exactly the discriminating clause — refinement.md §C).

## 5. Notes

The single FAIL_TO_PASS entry `test_with_exclude` exercises BOTH fixed
behaviours at once: without site 1 the test errors with `FieldError` (the
annotation name is unresolvable in the subquery); with site 1 but without site 2
the test returns the wrong rows (the filtered-relation join is trimmed and its
filter dropped). Hence two independently-observable fixed behaviours → two
modeled functions + two prepatches (`Solution_prepatch.lean` reverts site 1,
`Solution_prepatch_2.lean` reverts site 2). The gold-verbatim `patch.diff`
applies both hunks and resolves (G-RESOLVE).

`outerRelations`, `preservesUnmatchedRows`, `carriesOwnFilter` are all read-only
inputs — none is declared `mut` (directive 5): each modeled routine reads its
inputs and produces a fresh value, mutating nothing it is handed.
