# refinement.md — django__django-11400

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `orderedChoices` and `restrictedChoices` `do` blocks) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no A legs** in this
bundle — every step is R or I (§C). `patch.diff` is the gold patch **verbatim**
(G-RESOLVE).

## A. The ordering-selection kernel — `Field.get_choices` / `ForeignObjectRel.get_choices`

The patch adds, in both `get_choices` bodies, a guard around the materialization:

```
+ qs = <manager>.<filter/all>()
+ if ordering:
+     qs = qs.order_by(*ordering)
  return (blank_choice if include_blank else []) + [ ... for x in qs ]
```

i.e. order by the requested `ordering` only when it is non-empty; otherwise leave
the manager's intrinsic default ordering (`Meta.ordering`) in place. Pre-patch,
`.order_by(*ordering)` ran unconditionally, so an empty `ordering` cleared the
default. `orderedChoices` models the ordering-specification selection; the
subsequent materialization is the unchanged shared continuation (mapping.md §3).

| # | Solution.lean impl op (`orderedChoices`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `defaultOrdering : List String` (read-only, not `mut`) | the manager's intrinsic `Meta.ordering` that survives when `ordering` is falsy | R | ordering-spec tuple ↔ `List String` (mapping.md §2); read-only ⇒ no `mut`, directive 5. |
| A2 | param `requested : List String` (read-only, not `mut`) | the `ordering` kwarg of `get_choices` | R | same bijection; read-only. |
| A3 | `let mut ordering := defaultOrdering` | the manager value carrying `Meta.ordering` before the guard | I | start from the default ordering specification. |
| A4 | `ordering := if requested.isEmpty then ordering else requested` | `if ordering: qs = qs.order_by(*ordering)` | I | `requested.isEmpty` ↔ falsy `ordering` (mapping.md §2). Non-empty ⇒ adopt `requested`; empty ⇒ keep the default. This is the entire changed decision. |
| A5 | `return ordering`; `ensures out = effectiveOrdering defaultOrdering requested` | hand `qs` (ordered by the selected spec) to the unchanged materialization | R + I | the returned ordering specification is exactly what `.order_by` / iteration then consumes; that continuation is unchanged and shared (mapping.md §3), so equality of the selected spec ⇒ equality of materialized output. |

The forward (`Field.get_choices`) and reverse (`ForeignObjectRel.get_choices`)
hunks are the SAME selection over different managers
(`rel_model._default_manager.complex_filter(limit_choices_to)` vs
`self.related_model._default_manager.all()`); both are A1–A5 under the same
kernel. G-CONF exercises both sites.

## B. The value-restricted call site — `RelatedOnlyFieldListFilter.field_choices`

Gold hunk (`django/contrib/admin/filters.py`):
```
- return field.get_choices(include_blank=False, limit_choices_to={'pk__in': pk_qs})
+ ordering = self.field_admin_ordering(field, request, model_admin)
+ return field.get_choices(include_blank=False, limit_choices_to={'pk__in': pk_qs}, ordering=ordering)
```
The new `field_admin_ordering` helper (extracted from `RelatedFieldListFilter`)
returns the related admin's configured ordering, or `()` when none. The restricted
site now feeds that ordering into the SAME `get_choices` kernel.

| # | Solution.lean impl op (`restrictedChoices`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `defaultOrdering : List String` | the related model's intrinsic `Meta.ordering` | R | ordering-spec ↔ `List String`. |
| B2 | param `adminOrdering : List String` | `ordering = self.field_admin_ordering(...)` (admin-configured ordering, `()` if none) | R | ordering-spec ↔ `List String`; the configured ordering. |
| B3 | `let out ← orderedChoices defaultOrdering adminOrdering` | `field.get_choices(..., ordering=ordering)` | I | callee-under-spec: the configured ordering is passed as `requested` to the shared kernel. `prove_correct` discharges via `orderedChoices_correct` (mapping.md §3), no axiom. |
| B4 | `return out`; `ensures out = effectiveOrdering defaultOrdering adminOrdering` | the kernel's result returned | R + I | composition of A1–A5 at this site; the configured ordering plays the role of `requested`. |

`restrictedChoices` adds **no R/I op beyond `orderedChoices`** — it is the method
composition. So driving `get_choices` over many `requested`/`ordering` values
mechanically covers the R/I content of both modeled methods (G-CONF).

## C. No A legs, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom and no A-reference**: the one
operation that genuinely changed — guarding `.order_by(*ordering)` by emptiness
of `ordering` — is modeled **directly** by `effectiveOrdering` + the `do` block
(steps A3–A4), an I/R decision over the two input sequences, not hidden behind an
axiom about the function under change (directive 7). The downstream
materialization (`.order_by` + iteration) is **unchanged and shared** across both
branches, so it is neither consumed nor deep-modeled (mapping.md §3); modeling it
would be a dead axiom. Hence no `axiom_check.py` and G-AX skips.

## D. Two independently-fixed behaviors ⇒ two prepatches

The patch corrects two independently observable behaviors, each with its own
failing prepatch (G-DIFF, one per behavior):

* **`Solution_prepatch_1.lean`** — the `get_choices` guard itself: pre-patch
  `let ordering := requested` drives the materialization with `requested`
  unconditionally. When `requested` is empty this clears the intrinsic default
  ordering instead of preserving it. Fails `out = effectiveOrdering …` on the
  `requested = []` clause (the discriminating goal:
  `requested = [] → defaultOrdering = []`). Mirrors the unconditional
  `.order_by(*ordering)` and the `RelatedFieldListFilter`-with-`Meta.ordering`
  F2P tests (`test_get_choices_default_ordering`,
  `RelatedFieldListFilter ordering respects Model.ordering.`).

* **`Solution_prepatch_2.lean`** — the `RelatedOnlyFieldListFilter` plumbing:
  pre-patch `let out ← orderedChoices defaultOrdering []` routes an EMPTY ordering
  through the kernel (the omitted `ordering` kwarg), so the admin-configured
  ordering is silently discarded. Fails `out = effectiveOrdering defaultOrdering
  adminOrdering` whenever `adminOrdering` is non-empty. Mirrors the omitted
  `ordering=` kwarg and the F2P tests
  `RelatedOnlyFieldListFilter ordering respects ModelAdmin.ordering.` /
  `… respects Meta.ordering.`.

## E. verify(Solution) ⇒ resolved

`orderedChoices` verifies only if its output equals `effectiveOrdering
defaultOrdering requested` — i.e. exactly the requested ordering when non-empty,
and the intrinsic default when empty (A4–A5). By R (ordering-spec ↔ `List String`)
the verified kernel equals the patched `if ordering:` guard on every ordering
value; the unchanged materialization, applied to equal ordering specifications,
yields equal ordered choices (mapping.md §3). `restrictedChoices` composes the
same kernel at the value-restricted site (B3). By G-CONF the R/I transliteration
agrees with `patch.diff`'s real patched forward + reverse `get_choices` over
≥10⁵ inputs. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The single trust point is refinement fidelity (this doc, G-EQ + G-CONF); there is
no axiom-soundness trust point (no axioms).
