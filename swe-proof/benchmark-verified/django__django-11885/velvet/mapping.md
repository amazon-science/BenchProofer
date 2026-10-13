# mapping.md — django__django-11885

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 04ac9b45a34440fa447feb6ae934687aacbfc5f4`, states the type
abstraction (the Lean↔Python bijection), records callee provenance, and explains
why G-CONF is skipped.

Repo files under change: `django/db/models/deletion.py` (the behavioral change)
and `django/contrib/admin/utils.py` (a mechanical signature follow-through; see
§3). Changed function modeled: `Collector.collect`
(`django/db/models/deletion.py:174`; the touched step is the candidate-relation
fast-delete pass, `deletion.py:214–250` pre-patch / `deletion.py:215–271`
post-patch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineByTable (relations : List Relation)` | the fast-delete pass inside `Collector.collect` — `django/db/models/deletion.py:214–250` | the modeled changed behavior: build the per-table fast-delete plan, one combined entry per target table |
| `relations : List Relation` | the sequence of candidate relations that take the fast-delete path, in `get_candidate_relations_to_delete(model._meta)` enumeration order — `deletion.py:216` | the read-only input the grouping is computed from; one element per fast-deletable relation |
| `Relation.fst : Int` | the relation's target table (`related.related_model`) — `deletion.py:226` | the table a fast-delete entry will query |
| `Relation.snd : Int` | the relation's referencing column (`related.field`) — `deletion.py:220` | the column on that table whose match selects rows to delete |
| `out : List TableGroup` | the fast-delete plan: the sequence of `(table, [columns])` entries appended to `self.fast_deletes` for fast-deletable relations | the observable: which tables are queried, how many times, and which columns each query combines |
| `TableGroup.snd : List Int` | the list of columns combined into one query for a table (`related_fields`) — post-patch `deletion.py:268` | the columns OR-combined in a single `DELETE … WHERE col1 … OR colN` |

No callee is axiomatized. The candidate-relation enumerator
(`get_candidate_relations_to_delete`) and the eligibility test (`can_fast_delete`)
are unchanged; their only relevant effect is determining WHICH relations reach
the fast-delete path and in what order — that selected sequence is the read-only
input `relations`. The grouping primitive (the `model_fast_deletes` accumulation
and read-out) is modeled DEEPLY as `combined`/`combineInto`; there is no consumed
`axiom` declaration and no A-reference deep model of an outside callee.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the sequence of fast-deletable candidate relations | `List Relation` | enumeration order ↔ list order; an empty pass ↔ `[]`; per-relation iteration ↔ `List` traversal |
| a relation's target table (`related.related_model`) | `Relation.fst : Int` | the model class identity ↔ a stable `Int`; "same table" ↔ equal `Int` |
| a relation's referencing column (`related.field`) | `Relation.snd : Int` | the field identity ↔ a stable `Int` |
| the per-table accumulator `model_fast_deletes` (a `defaultdict(list)`), keyed by table | `List TableGroup` (order-preserving table → columns map) | `groups[table].append(col)` ↔ `combineInto gs table col`; reading `.items()` in insertion order ↔ the list in first-encounter order |
| one entry appended to `self.fast_deletes` | one `TableGroup` element of `out` | one fast-delete entry per group ⇒ "table queried k times" ↔ `table` occurring k times in `out.map Prod.fst`; the fix pins k = 1 per fast-deletable table |
| the columns OR-combined in one `DELETE … WHERE col1 … OR colN` | the `List Int` carried by a `TableGroup` | every referencing column for that table, in first-encounter order |

The upstream guards that decide eligibility — `field.remote_field.on_delete ==
DO_NOTHING` (skip), `keep_parents and related.model in parents` (skip), and
`can_fast_delete(related_model, from_field=field)` (take the fast path) — select
WHICH relations enter `relations`; both pre- and post-patch apply the identical
guards, so the modeled behavior begins at the grouping of the already-selected
fast-deletable relations. The behavior the F2P test observes — N relations on one
table issuing 1 combined query instead of N — is entirely in HOW the selected
relations are grouped before being turned into queries, which `combined` pins.

## 3. Callee / sibling-edit provenance

No callee is axiomatized. The supporting edits in the gold patch are mechanical
follow-throughs of the grouping, not independent behaviors, and carry no separate
spec node:

* `related_objects(related, objs)` → `related_objects(related_model,
  related_fields, objs)` (`deletion.py:252`, and the admin override
  `django/contrib/admin/utils.py:185`): the query builder now takes a *list* of
  columns and OR-combines them (`reduce(operator.or_, Q(col__in=objs) …)`); this
  is the per-group query construction whose multiplicity is captured by one
  `TableGroup`. R-tagged (a list of columns ↔ `TableGroup.snd`).
* `get_del_batches(objs, field)` → `get_del_batches(objs, fields)`
  (`deletion.py:162`): batching now reads a list of column names; batch sizing is
  observationally unchanged for the F2P case. R-tagged.
* `__init__` `self.data`/`field_updates`/`dependencies` switched to
  `defaultdict` (`deletion.py:67–79`) and the `add`/`add_field_update`
  `setdefault` simplifications: pure refactors of mapping construction with
  identical observable contents; not modeled (no behavioral change). I-tagged.
* `can_fast_delete`: `model = type(objs)` → `model = objs._meta.model`
  (`deletion.py:139`): lets `can_fast_delete` accept a *model class* (so the
  fast-delete decision is made per related model before fetching sub-objects);
  enables grouping. R-tagged (it changes the eligibility *input*, not the modeled
  grouping output).

None of these is axiomatized or deep-modeled as an A-reference of a stdlib
callee: the property the fix changes is *one combined query per target table
instead of one per relation*, captured exactly by `out = combined relations`
together with `(out.map Prod.fst).Nodup`.

## 4. G-CONF — SKIPPED (conf_skip = true)

There is no pure, DB-free R/I shadow to differential-test. The operation the
control flow performs — turning the selected fast-deletable relations into the
`self.fast_deletes` plan and ultimately into SQL `DELETE … WHERE … OR …`
statements — only has observable behavior relative to a live relational backend
plus the full `Collector`/ORM-metadata machinery:

* the combined-vs-separate query multiplicity is observed only by executing the
  compiled SQL and counting roundtrips, i.e. the F2P test's
  `assertNumQueries(2)` against real tables; there is no pure, DB-free way to
  produce the `(related_model, field)` candidate stream that drives the grouping.
* reproducing the bug-triggering case (a model with two CASCADE foreign keys to
  the same table — `SecondReferrer.referrer` and `SecondReferrer.other_referrer`
  → `Referrer`) requires standing up the model graph, `get_candidate_relations_
  to_delete`, `can_fast_delete`, the base managers, and a DB connection — i.e.
  the F2P integration test itself
  (`test_fast_delete_combined_relationships`), not a fuzzed pure
  transliteration this gate can drive.

The abstraction the spec pins (a `(table, column)` stream ↦ one combined group
per table, `combined`) IS the modeled content; there is no DB-free oracle that
produces that stream to diff against. Therefore `meta.json conf_skip = true` and
`conformance_check.py` is a `status=skip` stub (exit 0). Soundness of the modeled
grouping is carried by **G-VERIFY** (the fold provably emits each target table
exactly once, accumulating all its columns) and **G-DIFF** (the prepatch, which
emits one singleton group per relation, fails exactly the `out = combined
relations` and `(out.map Prod.fst).Nodup` clauses on any input referencing one
table twice — the un-combined-queries bug the issue reports). This mirrors the
django__django-13315 / django__django-13089 precedent (a live-DB control-flow
change with no DB-free shadow).

## 5. No fuzz seed

G-CONF is skipped (conf_skip = true), so no fuzz seed is consumed. There are no
axioms, so no G-AX seed either.
