# refinement.md — django__django-11885

The operation-by-operation correspondence between `model.py`'s implementation
(the `combined_fast_delete_count` impl region and the deep `distinct_count`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee/operation by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The combine-by-related-table site — `Collector.collect` (`django/db/models/deletion.py:174`)

Gold hunk (the fast-delete planning in the `collect_related` body):
```
-                batches = self.get_del_batches(new_objs, field)
-                for batch in batches:
-                    sub_objs = self.related_objects(related, batch)
-                    if self.can_fast_delete(sub_objs, from_field=field):
-                        self.fast_deletes.append(sub_objs)        # one per candidate
-                    else:
-                        ...
+        model_fast_deletes = defaultdict(list)
+        for related in get_candidate_relations_to_delete(model._meta):
+            ...
+            related_model = related.related_model
+            if self.can_fast_delete(related_model, from_field=field):
+                model_fast_deletes[related_model].append(field)
+                continue
+            ...
+        for related_model, related_fields in model_fast_deletes.items():
+            batches = self.get_del_batches(new_objs, related_fields)
+            for batch in batches:
+                sub_objs = self.related_objects(related_model, related_fields, batch)
+                self.fast_deletes.append(sub_objs)                 # one per distinct model
```

| # | model.py impl op (`combined_fast_delete_count`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `related_tables: List[int]` (one int identity per fast-removable candidate relation) | the ordered run of fast-removable candidate `related` relations whose `related_model` keys `model_fast_deletes` | R | each candidate relation ↔ its `related_model` identity (mapping.md §2). The fast-removability filter (`can_fast_delete(related_model, ...)` true) is the membership condition for being a candidate; the model takes the already-filtered run as input, matching the gold's `if can_fast_delete(...): model_fast_deletes[related_model].append(field)` branch. |
| A2 | `count` accumulates `+1` exactly when the current identity does not occur later in the run (`not contains(ToSeq(related_tables).drop(i), table)`) — i.e. one increment per FIRST occurrence of each distinct identity | `model_fast_deletes[related_model].append(field)` creates a new dict KEY exactly the first time `related_model` is seen; later columns of the same model extend the existing key's list without adding a group | R + A-reference | the per-first-occurrence increment IS the grouping: a `defaultdict(list)` has one key per distinct `related_model`. The deep model `distinct_count` (the spelled-out fold in the `pure` region) computes that key count; G-AX validates `distinct_count(ids) == len(model_fast_deletes)` against the real `collections.defaultdict(list)` grouping (mapping.md §3.1). There is no consumed axiom — the grouping is modelled deeply. |
| A3 | `Result()` = `count` = `distinct_count(ToSeq(related_tables))` | the number of `self.fast_deletes.append(sub_objs)` executed in the `for related_model, related_fields in model_fast_deletes.items()` loop = `len(model_fast_deletes)` | R + A-reference | one removal appended per `model_fast_deletes` entry = one per distinct related model. The model's `Result()` equals that count (A-reference, §3.1). This is the cardinality the F2P `assertNumQueries(2)` observes (one combined removal for `SecondReferrer` over both FKs + one for `Referrer` itself). |

The discriminating content of the change — combining N candidate relations on
one related table into ONE removal rather than N — lives in step A2/A3:
`Result() == distinct_count(...)` (counting distinct tables) vs. the pre-patch
one-removal-per-candidate. `model_prepatch.py` reproduces the pre-patch shape
(increment once per candidate, `count == len(related_tables)`) and **fails** the
postcondition `Result() == distinct_count(ToSeq(related_tables))` exactly when a
table recurs — which is the F2P case `related_tables == [r, r]` (two FKs of
`SecondReferrer` to `Referrer`): prepatch yields 2, spec demands
`distinct_count == 1`. That is the spec sensing the change (G-DIFF).

## B. Coordinated unchanged-shape steps in the same patch (not modelled count-bearing)

The gold patch also performs supporting edits that change query *content* but
not the *number* of removals the model pins:

| # | patch.diff op | tag | justification |
|---|---|---|---|
| B1 | `related_objects(related, objs)` → `related_objects(related_model, related_fields, objs)`; predicate `**{"%s__in" % related.field.name: objs}` → `reduce(operator.or_, Q(**{'%s__in' % rf.name: objs}) for rf in related_fields)` (`deletion.py:252`) and the matching `NestedObjects.related_objects` override (`admin/utils.py:185`) | R | signature/shape refinement carrying a *list* of referencing fields and OR-combining their predicates. It is invoked once per group (one combined query), so it produces exactly the per-distinct-model removal count modelled in §A; the predicate value is not observed by the F2P `assertNumQueries`. |
| B2 | `get_del_batches(objs, field)` → `get_del_batches(objs, fields)` (`field.name` → `[f.name for f in fields]`) (`deletion.py:162`) | R | same batch-sizing over a list of fields; does not change the number of groups/removals. |
| B3 | `can_fast_delete`: `model = type(objs)` → `model = objs._meta.model`; called with the `related_model` rather than a fetched `sub_objs` queryset (`deletion.py:126,222`) | I/R | the fast-removability decision is made on the related model up front (so candidacy is decided before fetching), the same predicate the model treats as the input filter (A1). No count is introduced. |
| B4 | `self.data`/`field_updates`/`dependencies` switched to `defaultdict(...)`, `add`/`add_field_update`/`add` body simplified accordingly (`deletion.py:65-118`) | I | pure container-default refactor; observationally identical (`setdefault(k, default)` ≡ `defaultdict` access). No behavioural change, no count. |

These steps are part of the shipped gold patch and are validated by G-RESOLVE
(the gold patch resolves: F2P + all P2P pass). They carry no count the model
pins, so they are type-refinement / identical-shape steps, not consumed axioms
or A-references of the modelled cardinality.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — collapsing per-candidate removals into one-per-distinct-related-table
— is modelled **deeply** (the spelled-out distinct-identity fold `distinct_count`
consumed in `combined_fast_delete_count`, step A2/A3, an **A-reference**), not
hidden behind an axiom about the function under change: there is no consumed
`@ContractOnly` axiom. The `defaultdict(list)` grouping the new code uses appears
only as the **A-reference** that G-AX validates the deep model against
(mapping.md §3.1).

## D. verify(model) ⇒ resolved

`combined_fast_delete_count` verifies only if its result equals the number of
distinct related tables `distinct_count(ToSeq(related_tables))` (A2/A3) — i.e.
one combined removal per distinct related model. By R (each candidate ↔ its
`related_model` identity; the `defaultdict` key count ↔ `distinct_count`) the
verified count equals `len(model_fast_deletes)` = the number of fast-delete
querysets the gold `collect` appends for the fast-removable candidates; by G-AX
the deep model `distinct_count` equals that real grouping count (A-reference).
The coordinated unchanged-shape steps (§B) preserve that count and are confirmed
by G-RESOLVE. Therefore a model satisfying this spec, refined by the map above,
issues the same number of combined fast-delete removals as the gold patch on the
tested inputs — and the gold patch resolves (G-RESOLVE; the F2P
`test_fast_delete_combined_relationships` expects `assertNumQueries(2)`). The
trust points are exactly the two of PLAN §1.1: axiom/reference soundness (G-AX)
and refinement fidelity (this document, G-EQ).
