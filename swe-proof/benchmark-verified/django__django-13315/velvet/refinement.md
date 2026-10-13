# refinement.md — django__django-13315

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectEligible` `do` block and the deep `keepMatching`/`keep` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs would be mechanically refuted by **G-CONF**; here G-CONF is SKIPPED
(`conf_skip = true`, mapping.md §4 — no DB-free oracle for the queryset
narrowing), so the R/I legs' soundness is carried by **G-VERIFY** + **G-DIFF**,
audited narratively by **G-EQ**. `patch.diff` is the gold patch **verbatim**
(applies at `base_commit`, resolves — G-RESOLVE).

## A. The constraint-application step — `apply_limit_choices_to_to_formfield`

Gold hunk (pre-patch → post-patch):
```python
- if limit_choices_to is not None:
-     formfield.queryset = formfield.queryset.complex_filter(limit_choices_to)
+ if limit_choices_to:
+     complex_filter = limit_choices_to
+     if not isinstance(complex_filter, Q):
+         complex_filter = Q(**limit_choices_to)
+     complex_filter &= Q(pk=OuterRef('pk'))
+     # Use Exists() to avoid potential duplicates.
+     formfield.queryset = formfield.queryset.filter(
+         Exists(formfield.queryset.model._base_manager.filter(complex_filter)),
+     )
```

| # | Solution.lean impl op (`selectEligible`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rows : List Candidate` | `formfield.queryset` (candidate collection) | R | `QuerySet` ↔ `List Candidate`; pk ↔ `id`; join multiplicity ↔ `witnesses` (mapping.md §2). |
| A2 | `keep c = if c.witnesses > 0 then [c.id] else []` (the per-candidate emit, folded by the loop) | `filter(Exists(... _base_manager.filter(complex_filter)))` | I | the `Exists()` subquery emits each candidate **once iff** at least one related row matches — exactly `[c.id]` when `witnesses > 0`, else `[]`. The changed narrowing op is modeled deeply (spelled-out `keep`/`keepMatching`), not behind an axiom. |
| A3 | `complex_filter`/`Q(**...)`/`&= Q(pk=OuterRef('pk'))` assembly | (constructs the eligibility predicate) | R | this machinery only re-expresses the SAME match predicate the pre-patch `complex_filter` used (mapping.md §3); modeled as `witnesses` = count of matching related rows, shared by both impls. No behavioral node of its own in `out`. |
| A4 | result `out = keepMatching rows` (the in-order fold), returned | `formfield.queryset = <narrowed>` assignment | R | the narrowed collection's observable content is its sequence of option identities; "offered k times" ↔ `c.id` occurs k times (mapping.md §2). The fix pins k ∈ {0,1}. |

Discriminating content of the change — an eligible candidate is offered **once**,
not once per join witness — lives in `keep c = [c.id]` (single occurrence) ⇔ the
`Exists()` correlated subquery (presence test, not join expansion). The pre-patch
`complex_filter` join emitted the candidate `witnesses` times;
`Solution_prepatch.lean` reproduces that with `List.replicate c.witnesses c.id`
and **fails** `out = keepMatching rows` on any candidate with `witnesses ≥ 2`
(G-DIFF) — precisely the duplicate-options bug.

## B. No A (axiom) steps, no kind-3

Every step is R or I. There is no consumed `axiom` and no A-reference deep model
of an outside callee: the modeled behavior is entirely the per-candidate
emit-multiplicity of the narrowing, and its two endpoints (the join vs the
`Exists()` subquery) are abstracted to `witnesses` ↦ `keep`. The one operation
that genuinely *changed* — the narrowing's emission multiplicity — is modeled
deeply (`keep`/`keepMatching`), not hidden behind an axiom about the function
under change. No *changed-op-inexpressible* (kind-3) step.

This is why there is no `axiom_check.py` (no axioms / A-references to validate)
and why G-CONF is skipped (no DB-free R/I shadow of a live queryset narrowing —
mapping.md §4): the deeply-modeled content is data flow whose endpoints are not
executable without a live DB. Soundness rests on G-VERIFY + G-DIFF.

## C. verify(Solution) ⇒ resolved

`selectEligible` verifies only if `out = keepMatching rows` — i.e. each eligible
candidate (`witnesses > 0`) contributes its identity **exactly once**, in order,
and ineligible candidates contribute nothing. This is precisely what the F2P
test `test_limit_choices_to_no_duplicates` demands: with `limit_choices_to`
spanning two joins, the form's candidate options must contain each matching
character once (`assertCountEqual(form.fields[...].queryset, [marley, threepwood])`),
not duplicated by the join cardinality.

By the R bijection (mapping.md §2) the verified result corresponds to the patched
narrowing: eligible ⇒ offered once (the `Exists()` presence test); ineligible ⇒
omitted. The prepatch impl (`List.replicate c.witnesses c.id`) emits each
eligible candidate once per witness — exactly the gold pre-patch
`complex_filter` inner join. It fails the `out = keepMatching rows` clause
(G-DIFF), which is the observable of the duplicate-options bug. No trust points
beyond the type bijection: there are no axioms, and G-CONF's absence is justified
by the live-DB nature of the narrowing (mapping.md §4), carried by G-VERIFY +
G-DIFF as in the django__django-13089 precedent.
