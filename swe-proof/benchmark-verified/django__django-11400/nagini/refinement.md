# refinement.md — django__django-11400

The operation-by-operation correspondence between `model.py`'s implementation
(`related_choice_rows`, `reverse_choice_rows`, the `copy_rows` helper, and the
`reordered` / `apply_order_by` axioms) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-consumed** (the proof uses this
axiom's `Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. `Field.get_choices` ↔ `related_choice_rows`
(`django/db/models/fields/__init__.py:809`)

Gold hunk (the data-row branch):
```
+        qs = rel_model._default_manager.complex_filter(limit_choices_to)
+        if ordering:
+            qs = qs.order_by(*ordering)
         return (blank_choice if include_blank else []) + [
-            (choice_func(x), str(x))
-            for x in rel_model._default_manager.complex_filter(limit_choices_to).order_by(*ordering)
+            (choice_func(x), str(x)) for x in qs
         ]
```

| # | model.py impl op (`related_choice_rows`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `base: List[int]` | `rel_model._default_manager.complex_filter(limit_choices_to)` (the base queryset, in base-manager / `Meta.ordering` order) | R | the base row sequence ↔ `List[int]` of row identities; `complex_filter` is unchanged and order-preserving (mapping.md §2). |
| A2 | parameter `ordering: List[int]` | the `ordering` field-name tuple | R | only emptiness is observed: `len(ordering)==0` ↔ `ordering == ()` (mapping.md §2). |
| A3 | `if len(ordering) > 0:` | `if ordering:` | I | truthiness of a tuple ↔ `len > 0`; both branch on "is an explicit ordering supplied". |
| A4 | `qs = apply_order_by(base, ordering)` (non-empty branch) | `qs = qs.order_by(*ordering)` | A-consumed | the unchanged `QuerySet.order_by(*ordering)` callee, captured by the `apply_order_by`/`reordered` axioms (mapping.md §3.1); the proof consumes `ToSeq(qs) == reordered(...)`. |
| A5 | `return copy_rows(base)` (empty branch) | `qs` stays `= ..._default_manager.complex_filter(...)` (no reorder), then materialized | I / R | when no ordering is supplied the base queryset is used unchanged; `copy_rows` is the order-preserving materialization of the same rows (the result list comprehension over `qs`). |
| A6 | result `List[int]` (row order) | `[...blank...] + [(choice_func(x), str(x)) for x in qs]` | R | the discriminating observable is the row ORDER, carried by `Result()`; the `(pk, str)` projection and the untouched blank prefix are order-preserving and elided (mapping.md §2). |

## B. `ForeignObjectRel.get_choices` ↔ `reverse_choice_rows`
(`django/db/models/fields/reverse_related.py:117`)

Gold hunk:
```
+        qs = self.related_model._default_manager.all()
+        if ordering:
+            qs = qs.order_by(*ordering)
         return (blank_choice if include_blank else []) + [
-            (x.pk, str(x)) for x in self.related_model._default_manager.order_by(*ordering)
+            (x.pk, str(x)) for x in qs
         ]
```

The correspondence is the same as §A, site-for-site, with `base` ↔
`self.related_model._default_manager.all()` and the projection `(x.pk, str(x))`.
Tags B1..B6 = A1..A6 verbatim (R / R / I / A-consumed / I / R). This is the
identical control-flow fix at a second site; `reverse_choice_rows` is its own
contracted function so the spec senses it independently (G-DIFF:
`model_prepatch_2.py` reverts only this site and fails only here).

## C. The admin-filter pass-through sites (no separate model)
(`django/contrib/admin/filters.py`)

Gold hunks: `RelatedFieldListFilter.field_admin_ordering(...)` is factored out of
`field_choices`, and `RelatedOnlyFieldListFilter.field_choices(...)` is changed
to forward `ordering=self.field_admin_ordering(...)` into
`field.get_choices(...)`. These sites change NO ordering semantics — they only
compute an `ordering` value and THREAD it into `get_choices`, whose behaviour is
modeled by §A. The admin F2P tests observe the same row-order fix through
`get_choices`. There is no model-impl operation here beyond "pass `ordering` to
`related_choice_rows`", which is already the A2/A4/A5 plumbing of §A. No kind-3
step, no separate contracted function (it would add zero discriminating power).

## D. No kind-3 (unexpressible-changed-op) steps
Every step above is R, A-consumed, or I. The one operation the patch turns on —
"reorder only when an explicit ordering is supplied; otherwise leave the base
order intact" — is expressed DIRECTLY as the `if len(ordering) > 0` branch over
the axiomatized `reordered`/`apply_order_by` callee. There is no axiom about the
function under change (`get_choices` itself is the function under spec, not an
axiom); the only consumed axiom covers the UNCHANGED `QuerySet.order_by` callee.
Its soundness — in particular its deliberate SILENCE on `reordered(base, [])` —
is audited by G-AX (axiom_check.py runs the real `order_by`).

## E. The prepatch and the discriminating clause (G-DIFF)
`model_prepatch.py` reverts both sites to the pre-patch unconditional reorder
(`return apply_order_by(base, ordering)`), mirroring the gold's removed
`...complex_filter(...).order_by(*ordering)` / `..._default_manager.order_by(*ordering)`.
With an empty `ordering` the result becomes `reordered(base, [])`, which the
axiom does NOT tie to `base`, so the postcondition
`Implies(len(ordering)==0, ToSeq(Result()) == ToSeq(base))` is unprovable — the
spec senses the bug at BOTH sites. `model_prepatch_2.py` reverts ONLY the
reverse-related site and fails only there, witnessing the second site's
independent observability.

## F. verify(model) ⇒ resolved
`related_choice_rows` / `reverse_choice_rows` verify only if, on an empty
ordering, the result equals the base order exactly (A5/B5 via `copy_rows`), and
on a non-empty ordering it equals the requested reordering (A4/B4 via the
axiom). By the R type-refinements (base queryset ↔ `base`, order-preserving
projection, untouched blank prefix) the verified row order equals the gold
patch's `qs` row order at each site; by G-AX the real `QuerySet.order_by` meets
the `reordered` axiom (uninterpreted: no length/set/multiset relation to the
base, and silent on the empty case). The admin
sites (C) inherit this through `get_choices`. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
one audited callee — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
