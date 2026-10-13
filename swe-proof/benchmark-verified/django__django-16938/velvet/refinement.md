# refinement.md — django__django-16938

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`queryIterPlan` `do` block plus the deep-model transformers in the `pure`
region) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (the proof uses an axiom's
`ensures`), **A-reference** (a deep model validated == its real callee by G-AX),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** — here there is no R/I data
content, so G-CONF is a principled **skip** (§B). The A legs and this narrative
are audited by **G-AX** + **G-EQ**/**G-PANEL**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The relation-iterator site — `queryset_iterator` (two backends)

Gold hunk (identical at `django/core/serializers/python.py:81` and
`django/core/serializers/xml_serializer.py:158`):
```
- return getattr(obj, field.name).only("pk").iterator()
+ return (
+     getattr(obj, field.name).select_related().only("pk").iterator()
+ )
```

The change inserts a no-argument `.select_related()` before `.only("pk")`.
`Solution.lean` models the load plan the closure assembles for the relation's
default queryset `getattr(obj, field.name)` — call it `q`.

| # | Solution.lean impl op (`queryIterPlan`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `q : QState` | `getattr(obj, field.name)` — the relation's default queryset, with whatever related selection its manager arrived with | R | `queryset.query.select_related` (∈ {False, True, dict}) ↔ `RelatedPlan`; the immediate-load mask ↔ `QState.immediate` (mapping.md §2). The custom-manager case of the issue arrives as `RelatedPlan.restricted [...]`. |
| A2 | `let q1 := selectAllRelated q` (`related := .unrestricted`) | the inserted `.select_related()` (no args) | A-reference | the no-arg `QuerySet.select_related()` resets `query.select_related = True` — the boolean (unrestricted) form, so `restricted = isinstance(..., dict)` becomes `False`. Modeled deeply as `selectAllRelated`; G-AX validates the effect against the real callee (mapping.md §3.1). |
| A3 | `let q2 := loadOnlyPk q1` (`immediate := some ["pk"]`) | `.only("pk")` | A-reference | `QuerySet.only("pk")` restricts the immediate-load mask to the primary key, deferring the rest. Modeled deeply as `loadOnlyPk`; G-AX validates against the real callee (mapping.md §3.2). |
| A4 | `return q2` | `.iterator()` — produces the iterator that triggers SQL compilation of the plan | I | the iterator merely evaluates the assembled plan `q2`; the observable correctness fact is whether compiling `q2` is refused (`planRejected`). The terminal `.iterator()` adds no plan state. |

The discriminating content of the change lives in the postconditions, which
must hold for **every** input plan `q` — including a restricted one naming a
deferred relation (`RelatedPlan.restricted ["master"]`, the issue's custom
manager):
* `ensures planRejected out = false` — the assembled plan is never refused;
* `ensures isRestricted out.related = false` — the related selection is reset to
  unrestricted, which is *why* the deferral can no longer collide;
* `ensures out.immediate = some ["pk"]` — the primary-key-only optimisation is
  preserved (the change must not regress the `test_serialize_only_pk` /
  `assertNumQueries` expectations).

`Solution_prepatch.lean` reproduces the pre-patch skeleton — `loadOnlyPk q`
WITHOUT the `selectAllRelated q` step — and **fails** `planRejected out = false`
and `isRestricted out.related = false` (G-DIFF): with `q.related` left as
`restricted ["master"]` and `q.immediate = some ["pk"]`, the relation `"master"`
is deferred while still traversed, so `planRejected = true`.

## B. G-CONF — principled skip (no R/I content)

`conformance_check.py` exits with `status=skip` (`meta.json conf_skip = true`).
G-CONF mechanically refutes the **R** and **I** legs by transliterating those
ops to Python and diffing against `patch.diff`'s behaviour over fuzzed inputs.
For this bundle there is no R/I *content* to transliterate:

* The value-carrying impl ops A2/A3 (`selectAllRelated`, `loadOnlyPk`) are both
  **A-reference** state transformers standing for unchanged queryset callees
  (`.select_related()`, `.only("pk")`). Per plan §4.1 step 1, G-CONF leaves
  A-tagged callees as the real repo callee and does NOT transliterate them.
* What remains after removing the A legs is the `planRejected` predicate (itself
  an A-reference model of `select_related_descend`'s raise condition) over those
  transformers — a control/predicate skeleton with no cross-language *data*
  carrier (no `str`/`list`/`dict` value) to sample. This is the §4.1
  "impl region is all-A-tagged ⇒ status=skip" case.

The full cross-language weight therefore falls on **G-AX** (each A-reference
callee validated against the real Django queryset machinery —
`select_related()`, `only("pk")`, and `select_related_descend`'s verdict, in
both the restricted-dict and unrestricted-boolean configurations) and on
**G-EQ**/**G-PANEL**.

## B2. Termination semantics (spec-strengthening, audit repair)

The bundle uses `loom.semantics.termination "total"` (`TotalCorrectness`), not
`"partial"`. A prior audit (G-PANEL-1) exhibited a same-spec counterexample
under partial correctness: because partial correctness constrains only
terminating executions, a diverging implementation discharges every `ensures`
vacuously — the spec admitted it even though the three postconditions fully
determine the output plan `{unrestricted, some ["pk"]}`. The real closure body
(`getattr(obj, field.name).select_related().only("pk").iterator()`) is a
straight-line chain of queryset-builder calls that always terminates, so total
correctness is the faithful semantics: it rejects every diverging impl while
the verified straight-line impl here is loop-free and unaffected. The
`set_option`/`open` lines are part of the frozen spec view shared
byte-identical by both twins (same_spec holds; the prepatch still fails on
exactly `ensures isRestricted out.related = false` / `ensures planRejected out
= false`, G-DIFF unchanged).

## B3. Spec tightness — the postconditions pin the output extensionally

The three postconditions determine the output plan **uniquely**:
`isRestricted out.related = false` forces `out.related = .unrestricted` (the
only `RelatedPlan` constructor with `isRestricted = false`), and
`out.immediate = some ["pk"]` pins the mask, so `out = {unrestricted,
some ["pk"]}` exactly; `planRejected out = false` is then implied. Consequences
for the adversarial audits (G-EQ / G-PANEL-1):

* A genuinely **wrong** impl — one whose faithful refined patch would NOT
  resolve — cannot verify against this spec: producing any other plan violates
  a postcondition, and (under the `total` semantics of §B2) diverging is
  rejected too. Wrong-impl attacks are expected to FAIL verification; that is
  the evidence of spec strength.
* Conversely, every same-spec impl that **does** verify returns the identical
  pinned plan and is therefore extensionally the gold behaviour. In particular
  the two builder steps `selectAllRelated` / `loadOnlyPk` **commute** (each
  writes a disjoint `QState` field), so reorderings, duplications, or a direct
  literal return of `{unrestricted, some ["pk"]}` all verify AND their faithful
  patches resolve — such variants are positive-control material demonstrating
  non-vacuity, not counterexamples of weakness: there is no wrong behaviour
  left for the spec to admit.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* is the
*insertion of a call* (`.select_related()`) into the closure — a control/data
composition change, modeled directly by the added `selectAllRelated` step (A2)
in the `do` block. The callees themselves are unchanged stdlib/ORM machinery,
modeled deeply as A-references; there is no consumed axiom about the function
under change. No operation is hidden behind an opaque oracle: the postconditions
are structural predicates on the input plan carrier (`planRejected`,
`isRestricted`, `immediate`), dischargeable only by actually resetting the
related selection and restricting the immediate load (SPEC_GUIDE §0.8).

## D. verify(Solution) ⇒ resolved

`queryIterPlan` verifies only if, for ANY input plan, the assembled plan is
never refused (`planRejected out = false`), the related selection is left
unrestricted (`isRestricted out.related = false`), and the primary-key-only mask
is preserved (`out.immediate = some ["pk"]`). By R (`queryset.query.*` ↔
`QState`, mapping.md §2) and the A-reference soundness of `selectAllRelated` /
`loadOnlyPk` / `planRejected` (G-AX), the verified plan equals the one the gold
patch's `getattr(...).select_related().only("pk").iterator()` assembles, whose
SQL compilation does not raise `FieldError` for the custom-manager m2m relation
of the issue — exactly the condition the F2P serializer tests
(`test_serialize_only_pk`, `test_serialize_prefetch_related_m2m`,
`test_serialize_no_only_pk_with_natural_keys`, and the basic serialization
tests over the new `topics` m2m field with its `select_related` manager) require.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ).
