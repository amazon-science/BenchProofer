# refinement.md — django__django-11885

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`combineByTable` `do` block plus the deep `combined`/`combineInto` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs would be mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); here G-CONF is SKIPPED (`conf_skip = true`, mapping.md §4 — the combined
fast-delete plan has no DB-free oracle), so the R/I legs' soundness is carried by
**G-VERIFY** + **G-DIFF**, audited narratively by **G-EQ**. There are **no A
legs** in this bundle: the changed function's new grouping behavior is modeled
deeply over its read-only input stream `relations`, and the callees involved
(`get_candidate_relations_to_delete`, `can_fast_delete`) are unchanged and only
supply / filter that stream (mapping.md §3). So there are no axioms, no
`axiom_check.py`, and G-AX is a skip.

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`, resolves —
G-RESOLVE).

## A. The fast-delete combining step — `Collector.collect` (`deletion.py:174`)

Gold hunks (`deletion.py:214–271` post-patch): introduce `model_fast_deletes =
defaultdict(list)`; for each fast-deletable candidate relation, instead of
immediately appending its own queryset to `self.fast_deletes`, append the
relation's `field` under its `related_model` key; after the candidate loop,
for each `(related_model, related_fields)` group issue ONE combined
`related_objects(related_model, related_fields, batch)` and append it once.

| # | Solution.lean impl op (`combineByTable`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `relations : List Relation` (read-only, not `mut`) | the sequence of fast-deletable candidate relations surfaced by `get_candidate_relations_to_delete(model._meta)` and admitted by `can_fast_delete(related_model, from_field=field)` | R | stream-of-relations ↔ `List Relation` via the row bijection `(related_model, field) ↔ (fst, snd)` (mapping.md §2). `relations` is read-only: the loop never mutates it (directive 5 — no `mut` on `relations`, frame is implicit). |
| A2 | `let mut result : List TableGroup := []` | `model_fast_deletes = defaultdict(list)` | I | initialize the order-preserving per-table accumulator empty. |
| A3 | loop body `result := combineInto result e.1 e.2` for each `e` in stream order | `model_fast_deletes[related_model].append(field)` (executed for each fast-deletable relation) | I | one order-preserving keyed grouping per relation; `combineInto` = "fresh table appended in first-encounter order carrying `[field]`, existing table keeps its place and appends `field`" is exactly `defaultdict(list)` `[k].append(v)` semantics. mapping.md §2. |
| A4 | `return result` (= `combined relations` by the loop invariant) | `for related_model, related_fields in model_fast_deletes.items(): … self.fast_deletes.append(sub_objs)` | I + R | reading the dict out in insertion order ↔ `result` in first-encounter order; the `out = combined relations` postcondition pins the read-out to the table-grouped collapse. Each group becomes one `self.fast_deletes` entry / one combined `DELETE … WHERE … OR …` (R, the columns-list ↔ `TableGroup.snd`; one combined query per group). |
| A5 | `ensures (out.map Prod.fst).Nodup` | the F2P property: no target table is fast-deleted by more than one query (`assertNumQueries(2)`) | I | dict keys are unique ⇒ `.items()` yields each table once ⇒ one combined query per table; the deep model proves `combined_nodup`. This is the discriminating clause the prepatch violates. |

Discriminating content of the change — N candidate relations on the same table
issue **one** combined query (post-patch) vs **N** separate queries (pre-patch).
It lives in `out = combined relations` together with `(out.map Prod.fst).Nodup`.
The pre-patch skeleton (`Solution_prepatch.lean`) emits each relation as its own
singleton-column group raw (`result := result ++ [(e.1, [e.2])]`, i.e.
`out = relations.map (fun e => (e.1, [e.2]))`), so for any stream with a repeated
table it has `out ≠ combined relations` AND `¬ (out.map Prod.fst).Nodup` —
`prove_correct` **fails on both** clauses (G-DIFF). This is exactly the pre-patch
`batches = self.get_del_batches(new_objs, field); … self.fast_deletes.append(
sub_objs)` per relation (one query per FK, never combined).

## B. The unchanged callees — `get_candidate_relations_to_delete`, `can_fast_delete` (no axiom)

`get_candidate_relations_to_delete(...)` and `can_fast_delete(...)` are **not
changed in their selection behavior** by the patch (the only `can_fast_delete`
edit, `type(objs)` → `objs._meta.model`, lets it accept a model class as input —
mapping.md §3 — it does not change *which* relations are admitted), and neither
is axiomatized. Their sole role is producing / filtering the relation stream that
is the read-only input `relations`. There is therefore no consumed axiom and no
A-reference deep model of a callee — `combined` is a deep model of the **changed
function's own** new grouping behavior, not of a callee. (mapping.md §3.)

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — replacing the
per-relation immediate `fast_deletes.append` with an order-preserving
group-by-table accumulation read out once at the end — is modeled **deeply** by
`combineInto`/`combined` and the verified `while` loop (steps A2–A5), not hidden
behind any axiom. No row is A. The sibling signature follow-throughs
(`related_objects`, `get_del_batches` taking a list; the `defaultdict`
refactors of `__init__`/`add`/`add_field_update`; the admin override) are
mechanical R/I re-expressions of the same data (mapping.md §3), not changed
behaviors with their own observable.

## D. verify(Solution) ⇒ resolved

`combineByTable` verifies only if `out = combined relations` (A4) and
`(out.map Prod.fst).Nodup` (A5). By R (`(related_model, field) ↔ Relation`,
stream ↔ `List Relation`, `defaultdict(list)` ↔ order-preserving table→columns
map, mapping.md §2) the verified `out` equals the post-patch fast-delete plan on
every relation stream the real candidate enumerator can produce; one group ↔ one
combined query. G-CONF is skipped (mapping.md §4: the plan→SQL→roundtrip-count
observable needs a live DB and the full Collector machinery — no DB-free shadow),
so refinement fidelity here is carried by G-VERIFY + G-DIFF and audited by G-EQ.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axioms (G-AX skip); the single trust point is refinement fidelity (this doc,
G-EQ), carried as in the django__django-13315 / django__django-13089 precedent.
