# mapping.md — django__django-11087

## 1. Symbol binding (file:line @ base_commit 8180ffba21)
Modeled function: the related-object field-selection decision introduced into
`Collector.collect`, `django/db/models/deletion.py:209-224` (the `collect_related`
branch). The gold patch rewrites the `elif sub_objs:` arm (line 223 pre-patch)
into an `else:` arm that, before invoking the on_delete handler, restricts the
related-objects queryset to its referenced fields unless a `select_related` is in
effect or deletion signals are connected for the related model.

Lean modeled function name: `collectFieldSelection` (deliberately neutral — it
names the *behavior* "decide the field selection for the collected sub-objects",
not the patched symbol; see §7).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `collectFieldSelection` (modeled decision) | `Collector.collect` field-selection arm, `deletion.py:220-224` (post-patch `:225-243`) |
| `guardA` | `sub_objs.query.select_related` (truthiness), `deletion.py:233` (post) |
| `guardB` | `self._has_signal_listeners(related_model)`, `deletion.py:233` (post); helper added at `:120-124` = `pre_delete.has_listeners(model) or post_delete.has_listeners(model)` |
| `pkColumn` | `related_model._meta.pk.attname` — the related model's identifying column (for an inherited child this is the parent-link attname, e.g. `mtibase_ptr_id`) |
| `allFields` | every concrete column of the related model (the whole row): `[f.attname for f in related_model._meta.concrete_fields]` |
| `defaultColumns` | the columns the INCOMING `sub_objs` loads if it is handed on untouched — the compiled select list of the queryset `self.related_objects(related, batch)` returned at `deletion.py:225` (post). Equal to `allFields` only when that queryset carries no deferral state; a related model whose `_base_manager` defers a column arrives with fewer |
| `skippedNames` | `sub_objs.query.deferred_loading[0]` when `deferred_loading[1]` is `True` (the "these are deferred" flag), else `[]`. The RAW stored strings, in the namespace the caller of `.defer()` used (`Query.add_deferred_loading`, `sql/query.py:1938-1957`) — see §4 |
| `candidateRelations` | `get_candidate_relations_to_delete(related_model._meta)`, each entry contributing `rel.field.foreign_related_fields` target attnames, `deletion.py:236-239` (post) |
| `referencedColumns` | `set(chain.from_iterable((rf.attname for rf in rel.field.foreign_related_fields) for rel in get_candidate_relations_to_delete(...)))`, `deletion.py:236-239` (post) |
| `restrictionNames` | the field-name set `.only(*tuple(referenced_fields))` actually ends up requesting: `field_names.difference(existing)` in `Query.add_immediate_loading` when the incoming queryset is in the defer state, `sql/query.py:1959-1981` |
| `loadedColumns` | what `sub_objs.only(*referenced_fields)` actually loads: `allFields` when the request is left empty (a zero-arg `.only()` is a no-op — `Query.deferred_to_data` returns early on an empty field-name set, `sql/query.py:656`), otherwise `request ∪ {pk}` (`deferred_to_data` seeds `must_include` with `orig_opts.pk`, `sql/query.py:660`) |
| result | the column set the SELECT for the collected sub-objects will load: what `sub_objs.only(*referenced_fields)` selects on the restricted branch, and what the untouched `sub_objs` selects otherwise |

The two guard flags are bound HERE and nowhere in the spec view: the spec view
takes them as opaque `Bool` inputs and says nothing about what makes either hold
(§7).

## 2. Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `bool` truthiness of `sub_objs.query.select_related` | `guardA : Bool` |
| `bool` result of `_has_signal_listeners(related_model)` | `guardB : Bool` |
| every concrete column attname (whole row) — a `list[str]` | `allFields : List String` |
| the incoming queryset's compiled select list — a `set[str]` of attnames | `defaultColumns : List String` |
| `sub_objs.query.deferred_loading[0] if …[1] else set()` — a `set[str]` of raw stored names | `skippedNames : List String` |
| `get_candidate_relations_to_delete(...)` → per relation the tuple of `rf.attname` of its `foreign_related_fields` — a `list[list[str]]` | `candidateRelations : List (List String)` |
| `set(chain.from_iterable(...))` (referenced attnames, deduplicated) | `referencedColumns candidateRelations = candidateRelations.flatten.dedup : List String` |
| `referenced.difference(deferred_names)` | `restrictionNames skippedNames candidateRelations` |
| `related_model._meta.pk.attname` — a `str` | `pkColumn : String` |
| the column set `sub_objs.only(*referenced)` selects — a `set[str]` | `loadedColumns pkColumn allFields skippedNames candidateRelations : List String` |
| selected column set (the SELECT's column list) | `result : List String` |

## 3. Measured carrier states (the shadowed spread)
Each row is a real Django model at `base_commit` with the gold patch applied, the
seven observables read off the real `sub_objs` at the arm, and the column list of
the SELECT the cascade actually emitted (rows 1-6: a real `Origin.objects.…
.delete()` with `connection.queries` parsed; rows 7-9 and 11-13: the real
`.only(*referenced)` compiled through `SQLCompiler.pre_sql_setup`). "old" is the
model this bundle shipped before the panel repair.

| # | carrier state | guards (A,B) | allFields | defaultColumns | skippedNames | referenced | REAL load | model | old model | branch |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | base manager defers the referenced column (`defer('unique_field')`) | (F,F) | id,large_field,origin_id,unique_field | id,large_field,origin_id | unique_field | unique_field | **all four** | all four | id,unique_field ✗ | restricted, request emptied |
| 2 | no prior deferral | (F,F) | id,large_field,origin_id,unique_field | (all four) | — | unique_field | id,unique_field | id,unique_field | id,unique_field | restricted, non-empty |
| 3 | prior deferral misses the referenced column (`defer('large_field')`) | (F,F) | id,large_field,origin_id,unique_field | id,origin_id,unique_field | large_field | unique_field | id,unique_field | id,unique_field | id,unique_field | restricted, non-empty |
| 4 | receivers registered AND the referenced column deferred | (F,T) | id,large_field,origin_id,unique_field | id,large_field,origin_id | unique_field | unique_field | **id,large_field,origin_id** | id,large_field,origin_id | all four ✗ | pass-through |
| 5 | receivers registered, no prior deferral | (F,T) | id,large_field,origin_id,unique_field | (all four) | — | unique_field | all four | all four | all four | pass-through |
| 6 | nothing points at the model (generic-relation owner, so not fast-deletable), a column deferred | (F,F) | big,id,origin_id | id,origin_id | big | — | big,id,origin_id | big,id,origin_id | big,id,origin_id | restricted, empty gather |
| 7 | referenced column is an FK column, deferred by FIELD NAME (`defer('origin')`) | (F,F) | big,id,origin_id,u | big,id,u | **origin** | **origin_id** | id,origin_id | id,origin_id | id,origin_id | restricted, raw-name miss |
| 8 | the same column deferred by ATTNAME (`defer('origin_id')`) | (F,F) | big,id,origin_id,u | big,id,u | origin_id | origin_id | **big,id,origin_id,u** | big,id,origin_id,u | id,origin_id ✗ | restricted, request emptied |
| 9 | prior state is an immediate-loading one (`only('large_field')`) | (F,F) | id,large_field,origin_id,unique_field | id,large_field | — (flag is immediate) | unique_field | id,unique_field | id,unique_field | id,unique_field | restricted, prior state replaced |
| 10 | model that IS fast-deletable | (F,F) | big,id,origin_id | id,origin_id | big | — | *no SELECT* | — | — | arm not reached (out of domain) |
| 11 | two relations target two different non-pk columns and the fetch already skips ONE of them (`defer('a')`) | (F,F) | a,b,big,id | b,big,id | **a** | a,b | **b,id** | b,id | a,b,id ✗ | restricted, PARTIAL overlap |
| 12 | the identifying column itself is already skipped (`defer('id')`) | (F,F) | a,b,big,id | (all four) | **id** | a,b | **a,b,id** | a,b,id | a,b,id | restricted, pk skipped yet retained |
| 13 | the skip set COVERS the whole referenced set (`defer('a','b')`) | (F,F) | a,b,big,id | big,id | a,b | a,b | **a,b,big,id** | a,b,big,id | a,b,id ✗ | restricted, request emptied |

Rows 1, 4, 8, 11 and 13 are where the pre-repair model was unfaithful; rows 7 and
8 together are the type-bridge edge (§4). Row 10 is outside the modeled domain:
the fast-delete branch is taken before the arm, so no column choice is made.

Rows 11-13 separate the two roles the skip reduction plays, which no single-column
referenced set can distinguish. With two referenced columns and one of them
skipped (row 11) the request stays non-empty but SHRINKS: the real fetch loads
`{b,id}`, so the reduction applies to the request itself and not merely to the
decision whether to restrict at all — a model that used the reduced set only for
the emptiness test and then loaded the unreduced `{a,b}` would predict `{a,b,id}`,
which the real query does not load. Row 12 is the opposite interaction: the
identifying column is in the skip set, and the real fetch loads it anyway
(`{a,b,id}`), because `add_immediate_loading` REPLACES the defer state
(`sql/query.py:1971-1980`, flag set `False`) and `deferred_to_data` then seeds
`must_include` with `orig_opts.pk` (`sql/query.py:660`). So the retention of
`pkColumn` in `loadedColumns` is unconditional, exactly as the real callee has it.
Row 13 is the boundary between 11 and 1: once the skip covers every referenced
name the request is empty and the whole row comes back, skipped columns included.

Beyond those, the shadow was compared against the real machinery exhaustively:
five model shapes (flat, custom identity column, leaf, and both halves of an MTI
pair) × every subset of already-deferred names × every subset of requested
columns, plus chained prior states (defer-then-defer and only-then-defer):
33,856 comparisons, 0 disagreements, covering all three legs
(restricted-non-empty 7,364; restricted-empty 1,100; pass-through 25,392).
`conformance_check.py` runs a superset of this as G-CONF (124,255 comparisons in
four legs, one of which is real cascade deletes).

## 4. `.only(...)` is not the identity on its argument
The value the bundle models is the column set the SELECT LOADS, so the model must
account for what `QuerySet.only()` does to the set it is handed *and* to the
deferral state the incoming queryset already carries, rather than assuming it
loads exactly the set it was given. Four behaviours, all measured against the
real callee at `base_commit`:

  * `.only(*cols)` with a non-empty REQUEST loads `request ∪ {pk.attname}`. The pk
    is retained whether or not a relation points at it: `Query.deferred_to_data`
    seeds `must_include` with `orig_opts.pk` (`sql/query.py:660`). This is NOT a
    corner case — a relation declared `to_field='unique_field'` targets a non-pk
    column, so `referenced_fields` legitimately excludes the pk. Live check on
    `Target(unique_field unique)` + `Ref FK(to_field='unique_field')`:
    `referenced_fields == {'unique_field'}` and the cascade SELECT is
    `SELECT "target"."id", "target"."unique_field" FROM "target" WHERE ...`.
    The retention is UNCONDITIONAL: it survives even a fetch that had been told
    to leave the identifying column out, because `add_immediate_loading` replaces
    the defer state wholesale (it stores `(request, False)`, `query.py:1971-1980`)
    and the `must_include` seed then runs on the fresh state. Measured (§3 row
    12): with `defer('id')` in force and `referenced == {a,b}` the compiled select
    is `{a,b,id}`. So `loadedColumns` conses `pkColumn` on with no exception for a
    skipped `pkColumn`, which is what the real callee does.
  * `.only()` with a ZERO-length request is a NO-OP and the whole row is loaded:
    `add_immediate_loading` stores an empty field-name set (`query.py:1959-1981`)
    and `deferred_to_data` returns early on it (`query.py:656`). Reachable
    whenever nothing points at the related model, e.g. a cascade leaf that still
    cannot be fast-deleted (§3 row 6).
  * the REQUEST is not the referenced set. When the incoming queryset is in the
    DEFER state, `add_immediate_loading` requests
    `field_names.difference(existing)` (`query.py:1971-1976`): names already
    deferred are dropped from the request. So a referenced column that was
    already deferred does not come back, and if that empties the request the
    `.only()` degenerates into the no-op above and the WHOLE ROW is loaded —
    including the deferred column (§3 rows 1, 8, 13). `restrictionNames` models
    this step; `loadedColumns` composes it with the two above. The difference is
    taken on the REQUEST itself and is not merely consulted to decide whether to
    restrict at all: with two referenced columns and one of them deferred the
    request shrinks to the other one and the load is `{other} ∪ {pk}` (§3 row 11,
    measured `{b,id}`). That partial-overlap state is the only one that
    distinguishes `restrictionNames` from a model that uses the reduction just as
    an emptiness test.
  * the difference is a RAW STRING difference, over the names as the caller of
    `.defer()` wrote them — `deferred_loading` stores them unresolved. The
    referenced set is in the ATTNAME namespace, so `defer('origin')` does NOT
    cancel a referenced `origin_id` while `defer('origin_id')` does (§3 rows 7
    and 8, both measured). Those two carrier states defer the SAME column and
    have the same `defaultColumns` (`big,id,u`), yet their restricted loads
    differ — `id,origin_id` against the whole row — purely by the lexical form of
    the stored name. `skippedNames` is therefore bound to the raw stored names
    and `restrictionNames` filters lexically; a bridge that "helpfully" resolved
    skip names to attnames would predict the whole row for row 7, which the real
    query does not load.
  * on the pass-through branch the arm hands `sub_objs` on UNTOUCHED, so the load
    is that queryset's own select list — `defaultColumns`, which is the whole row
    only when nothing had been deferred (§3 rows 4, 5).

`loadedColumns` and the `defaultColumns` binding model exactly these behaviours,
so the postcondition states what the real callee GUARANTEES about the loaded
column set rather than an idealised "loads exactly the referenced set".

## 5. Set vs list modeling note
The real code builds a Python `set` of referenced attnames and passes it to
`.only(*tuple(...))`. A SELECT's column choice is *membership-determined* — the
column ordering and any duplicate suppression are exactly what a set gives. We
model the gather as `List.flatten` (= `chain.from_iterable`) followed by
`List.dedup` (= `set(...)` membership-dedup, keeping first occurrence), and the
request reduction as `List.filter` (= `set.difference`). G-CONF bridges this by
comparing as **sets** (`set(shadow) == set(oracle)`), so the Lean list↔Python set
bijection is sound: both sides agree on the *set* of columns, which is the column
choice `.only(...)` consumes.

## 6. Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `get_candidate_relations_to_delete`
  and `foreign_related_fields` enter as DATA: their observable output (the
  per-relation list of target attnames) is supplied as the `candidateRelations`
  input. The gather operation itself (`chain.from_iterable` + `set`) is modeled
  deeply as `flatten` + `dedup` (an I/R op, not an axiom), and the request
  reduction (`set.difference`) as `filter`.
- The deferred-loading machinery `.only()` dispatches to is modeled by its
  observable result rather than assumed: the three steps that stand between the
  gathered set and the loaded columns (`add_immediate_loading`'s difference,
  `deferred_to_data`'s empty-set early return, and its `must_include` pk seed)
  each have their own leg in `loadedColumns`, and each is pinned by its own
  G-PBT reject case (`weak-ignore-skipped`, `weak-restrict-to-nothing`,
  `weak-drop-pk`), as are the two ways those legs interact
  (`weak-referenced-unfiltered` for the reduction applying to the request rather
  than only to the emptiness test, `weak-drop-pk-when-skipped` for the retention
  outliving a skipped identifying column).
- Flag dependency: the restriction fires iff `not (sub_objs.query.select_related
  or _has_signal_listeners(related_model))`. `_has_signal_listeners` is the new
  helper = `pre_delete.has_listeners or post_delete.has_listeners` (note: the
  `m2m_changed` disjunct from `can_fast_delete` is intentionally NOT part of the
  related-model signal check — only pre/post delete gate the optimization).
  Modeled as the two opaque Bools `guardA`, `guardB`.

## 7. G-LEAK
The `problem_statement` does NOT contain `select_related`, `pre_delete`,
`post_delete`, `has_listeners`, `can_fast_delete`, `only`, `defer`, `referenced`,
or `signal`, so nothing in the spec view may name or describe either guard
condition. It does contain, in the reporter's own words, a cascade `.delete()`
whose SELECT fetches "a field … that is not actually needed for the `.delete()`
(it's not a primary key etc)", the full column lists of the offending SELECTs, and
the request that Django "shouldn't be fetching that field regardless". What the
spec view discloses is bounded by that:

  * the modeled decision (which columns the fetch for the collected objects
    loads), the referenced/target columns, and the retention of the identifying
    column — all present in the statement ("not a primary key etc");
  * the two guard conditions as UNINTERPRETED flags named `guardA`, `guardB`. The
    spec view states only that under either of them no restriction is applied,
    and says explicitly that "what makes either of them hold is not part of this
    decision". Their bindings live in §1 of this file, which is not part of the
    spec view.

Residual disclosure, stated plainly so an auditor can weigh it: the spec view does
reveal that the decision is parameterized by TWO suppression flags, because the
signature has two `Bool` binders and the postcondition partitions on
`guardA = false ∧ guardB = false`. That is a shape, not a content: a solver who
reads it learns that some pair of conditions suppresses the narrowing, and learns
nothing about which conditions those are, so it cannot direct them to
`sub_objs.query.select_related` or to a receiver check on the related model — the
facts the audit demonstrated are decisive for the F2P. The two honest ways to hide
even the shape would be to drop the flags from the signature (which deletes the
carve-out obligation entirely, making the spec satisfiable by an impl that
narrows unconditionally — i.e. it would introduce a G-PANEL-1 hole and contradict
the real callee) or to restrict the domain to `guardA = false ∧ guardB = false`
(which narrows the modeled decision away from the arm the patch actually edits and
would fail G-PANEL-2 on the suppressed branch). Both trade a bounded structural
disclosure for an unsound or unfaithful spec, so this revision keeps the binders
and strips the interpretation.

An earlier revision of the spec named them `selectRelated` and `hasSignals` and
narrated their meaning ("whether the fetch … already pulls in further relations
eagerly", "whether deletion-time receivers are registered for the related
model … so the receivers see every column"). A solver could not have written
either line from the statement, and together they reconstruct the patch's guard
verbatim; that is the leak this revision removes. The obligation survives intact:
the postcondition still pins the result by full value on both sides of the guard
partition, so the discriminating behaviour is still specified — only the
attribution of the guards to repo concepts is gone.

The modeled-function identifier `collectFieldSelection` shares no patched
def/class name (`_has_signal_listeners`, `can_fast_delete`, `collect`,
`get_candidate_relations_to_delete`) as a substring, and neither
`restrictionNames` nor `defaultColumns`/`skippedNames` names a repo symbol
(`add_immediate_loading`, `deferred_loading`, `deferred_to_data`, `only`,
`defer`).

## 8. Pinned G-CONF fuzz seed
`11087`.
