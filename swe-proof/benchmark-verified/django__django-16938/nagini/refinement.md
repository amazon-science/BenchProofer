# refinement.md — django__django-16938

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_pk_iterator` impl region, the helper transitions `reset_select_
related` / `only_pk`, the deep predicate `ill_formed`) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, proof uses the axiom's `Ensures`, and
**A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The python serializer site — `queryset_iterator` (`django/core/serializers/python.py:81-82`)

Gold hunk:
```
  def queryset_iterator(obj, field):
-     return getattr(obj, field.name).only("pk").iterator()
+     return (
+         getattr(obj, field.name).select_related().only("pk").iterator()
+     )
```

| # | model.py impl op (`build_pk_iterator`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `base: Fetch` | `getattr(obj, field.name)` (the related m2m collection queryset) | R | the accessor's result queryset ↔ `Fetch`; its baked-in `select_related` request is the arbitrary `base.restricted`/`base.requested` the precondition admits (mapping.md §1, §2). |
| A2 | `cleared = clear_specific_request(base)` | `.select_related()` (no args) — **the added call, the fix** | A-reference | `select_related()` with no args sets `query.select_related = True` (a bool), so `restricted` becomes False (`Result().restricted == False`). The unchanged callee is modeled DEEPLY as the state transition; validated == real `QuerySet.select_related()` by G-AX (mapping.md §3.1). |
| A3 | `narrowed = only_pk(cleared, pk)` | `.only("pk")` | A-reference | `only("pk")` narrows the projection to the single pk field (`Result().loaded == {pk}`), eager-co-selection request unchanged. Unchanged callee modeled deeply; validated == real `QuerySet.only` by G-AX (mapping.md §3.2). |
| A4 | `return narrowed` | `.iterator()` then `return` | R | `iterator()` only changes the fetch strategy, not the well-formedness facets; the `FieldError` is raised during SQL setup, which `iterator()` does not alter (mapping.md §2). Modeled as the identity on the carried facets. |

## B. The xml serializer site — `queryset_iterator` (`django/core/serializers/xml_serializer.py:157-158`)

Gold hunk: **byte-identical** to §A (same nested helper, other backend):
```
  def queryset_iterator(obj, field):
-     return getattr(obj, field.name).only("pk").iterator()
+     return (
+         getattr(obj, field.name).select_related().only("pk").iterator()
+     )
```

The two sites are the same edit to the same helper; `build_pk_iterator` models
both. The R/A-reference map of §A applies verbatim to §B (one modeled function
stands for the two identical sites — mapping.md §1). No second
`model_prepatch_<k>` is needed: the two hunks fix the *same* behaviour (a
pk-only m2m reference fetch erroring under a custom-manager `select_related`),
so a single failing prepatch witnesses both (see §D).

## C. The discriminating change and the deep model `ill_formed`

The well-formedness obligation lives in the deep predicate `ill_formed`
(model.py pure region), the model of the unchanged evaluation-time check
`select_related_descend` (mapping.md §3.3). `build_pk_iterator` `Ensures(not
ill_formed(Result()...))`: the built fetch never errors, for ANY `base`,
including one whose accessor baked in a restricted `select_related` request
(`base.restricted == True`, `base.requested` naming an adjacent field that the
pk-only projection excludes). That guarantee holds **only** because A2 resets
`restricted` to False before A3 narrows the projection.

- **Post-patch (model.py):** `clear_specific_request` ⇒ `Result().restricted ==
  False` ⇒ `ill_formed` is vacuously False ⇒ postcondition holds. Verifies.
- **Pre-patch (`model_prepatch.py`):** omit A2 (`narrowed = only_pk(base, pk)`),
  mirroring the pre-patch `getattr(...).only("pk")`. Now `Result().restricted ==
  base.restricted` and `Result().loaded == {pk}`; for a `base` with
  `restricted == True` and a `requested` field ∉ `{pk}`, `ill_formed` is True,
  so the postcondition `not ill_formed(...)` **fails** — exactly the spec
  sensing the bug (G-DIFF). Confirmed: `model_prepatch.py` fails on
  `build_pk_iterator`'s `not ill_formed(...)` clause.

This is precisely the issue's `FieldError` ("cannot be both deferred and
traversed using select_related at the same time"): G-AX exhibits it on the real
ORM for the pre-patch chain and its absence for the post-patch chain (§3.3).

### C.1 Input-grounding of the result (no answer-echo)

`build_pk_iterator` additionally `Ensures(Result().requested == base.requested)`
and `only_pk` / `clear_specific_request` each thread `requested` through
unchanged (`Result().requested is q.requested`). This grounds the result in the
read-only `base` input: the built fetch addresses the **same** member set the
owning collection's accessor yields — the build neither fabricates nor discards
the underlying record set. This is what the behavioural F2P tests check (m2m
membership/order: `test_serialize_prefetch_related_m2m` asserts the exact m2m
row list). Without it the spec was satisfiable by an impl that discards `base`
and returns a constant `Fetch(False, {pk}, {pk})` — verified-but-unresolved
(it would refine to a patch that returns the wrong row set, failing the m2m F2P
tests). With the grounding, the two postconditions together pin the result to
exactly `Fetch(False, base.requested, {pk})` — the gold-chain output — for every
`base`: a restriction-preserving impl fails `not ill_formed(...)` on a worst-case
restricted `base`, and a base-discarding impl fails `requested == base.requested`.
The grounding is a structural relation on the actual input carrier `base`
(directive 8), not an opaque oracle the impl could echo.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The operation that genuinely *changed* —
inserting `.select_related()` to reset the eager-co-selection request before the
pk-only projection — is modeled **deeply** (`clear_specific_request` + the
`ill_formed` predicate it neutralizes), not hidden behind an axiom about the
function under change. There is **no consumed `@ContractOnly` axiom**
(A-consumed): the proof depends on no opaque contract. The three deep models
(`clear_specific_request`, `only_pk`, `ill_formed`) are **A-reference**: each is
validated == its real unchanged Django callee (`QuerySet.select_related()`,
`QuerySet.only`, `select_related_descend`) by `axiom_check.py` / G-AX.

## E. verify(model) ⇒ resolved

`build_pk_iterator` verifies only if its result is well-formed for every base
(`not ill_formed`, A2's reset) AND is a pk-only projection (`loaded == {pk}`,
A3). By R (QuerySet ↔ `Fetch`, `iterator()`/`getattr` identities) the verified
build equals `getattr(obj, field.name).select_related().only("pk").iterator()`
on the tested inputs; by G-AX the deep models equal the real callees
(A-reference), so the built real query raises no `FieldError` and selects only
the pk — exactly what the gold patch produces. The F2P tests
(`test_serialize_only_pk`, `test_serialize_prefetch_related_m2m`, the basic
serialization tests now exercising a `Topic` m2m whose manager uses
`select_related`) pass post-gold and fail pre-patch (FieldError). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom/deep-model soundness
(G-AX) and refinement fidelity (this document, G-EQ).
