# refinement.md — django__django-13315

The operation-by-operation correspondence between `model.py`'s implementation
(the `offered_options` impl region and the deep `dedup`/`occurs` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated == a real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The narrowing site — `apply_limit_choices_to_to_formfield` (`django/forms/models.py:98`)

Gold hunk (body):
```
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

| # | model.py impl op (`offered_options`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `matches: List[int]` — the raw matching stream (a row id once per satisfying join path) | the rows `formfield.queryset` yields under the restriction `limit_choices_to` evaluated across the join | R | `QuerySet` rows ↔ `List[int]` of pks; a satisfying join path ↔ an occurrence in `matches` (mapping.md §2). The pre-patch `complex_filter(limit_choices_to)` is exactly this raw stream (join added to the SELECT, one row per path). |
| A2 | `result` built as the duplicate-free image: prepend `matches[i-1]` iff it does not recur later (`not occurs(v, drop(i))`), i.e. `ToSeq(result) == dedup(ToSeq(matches))` | `formfield.queryset.filter(Exists(... ._base_manager.filter(complex_filter)))` | A-reference | the CHANGED operation is modelled **deeply**: `dedup` (the spelled-out front-recursive fold in the `pure` region) and the verified loop ARE the duplicate elimination. There is no consumed axiom. The deep model is validated **== the real semantics** out-of-band by G-AX (axiom_check.py): the gold path emits a base row iff some join path satisfies the restriction (`Exists`) and — being a correlated boolean subquery, not an outer join — emits it **at most once**, which is exactly `dedup` (membership preserved, no duplicate). mapping.md §4. |
| A3 | the membership/identity carried by `occurs(v, s)` and `int` equality | the row-identity the `Exists` subquery and `pk=OuterRef('pk')` correlation test (same base row) | R + A-reference | a row's identity ↔ its pk ↔ the `int`; `occurs` ↔ "this base row has a satisfying join path". G-AX checks `occurs` == real membership. |
| A4 | `result` returned (a fresh `List[int]`; `matches` left untouched, ensured at `Acc(...,1/2)`) | the narrowed `formfield.queryset` (a new queryset assigned to `formfield.queryset`) | R | the narrowing produces a fresh queryset (filter returns a new clone); the source matching stream is read-only. The F2P test reads the resulting rows via `assertCountEqual` (multiset/membership equality), which the pk-keyed `List[int]` carries. |

The discriminating content of the change — distinct rows vs. duplicate rows —
lives in `dedup` (model) ⇔ the `Exists()`-wrapping (real). The pre-patch
`complex_filter` returns the raw stream verbatim; `model_prepatch.py` reproduces
that (`ToSeq(result) == ToSeq(matches)`, no dedup) and **fails** the
postcondition `ToSeq(Result()) == dedup(ToSeq(matches))` whenever a row matched
along more than one join path — exactly the spec sensing the change (G-DIFF).

## B. The guard refinement — `is not None` → truthy

The gold patch also tightens the entry guard from `if limit_choices_to is not
None` to `if limit_choices_to`. This is a secondary refinement (an empty
restriction `{}` / `Q()` is now a no-op, leaving the queryset unchanged). It is
NOT exercised by the F2P test (`test_limit_choices_to_no_duplicates` always
supplies a non-empty restriction) and not a duplicate-related behaviour, so the
model does not contract it separately; the modeled function is entered exactly
on the path the F2P test exercises (a non-empty restriction producing a matching
stream). Tag for completeness: **I** on the "restriction present ⇒ narrow"
branch (both pre- and post-patch narrow when a non-empty restriction is given;
they differ only in HOW the narrowing dedups, which is site A). No separate
`model_prepatch_<k>` is needed because the only F2P-observable fixed behaviour
is the de-duplication (site A).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — collapsing the duplicate join-match stream to a duplicate-free set —
is modelled **deeply** (the spelled-out front-recursive fold `dedup` consumed in
`offered_options`, step A2, an **A-reference**), not hidden behind an axiom about
the operation under change. There is no consumed axiom: `complex_filter` (the
removed call) and `Exists`/`OuterRef`/`Q`/`_base_manager` (the new mechanism)
are NOT axiomatized — the spec depends only on their net observable effect
(distinct matching rows), which the deep model captures and G-AX validates.

## D. verify(model) ⇒ resolved

`offered_options` verifies only if its output equals the exact duplicate-free
image `dedup(ToSeq(matches))` (A2) — a wrong impl that leaves duplicates (the
bug), drops a genuinely-matching row, or invents a non-matching row fails the
structural equality (`dedup` is grounded in the input, not an opaque oracle, so
it cannot be echoed). By R (`QuerySet` rows ↔ `List[int]` of pks; the F2P test's
`assertCountEqual` is multiset/membership equality, carried by the pks) the
verified de-duplicator equals `formfield.queryset.filter(Exists(...))` on the
tested rows; by G-AX the deep model `dedup`/`occurs` equals the real distinct-
matching semantics the `Exists()`-wrapping realises (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited deep-model reference — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-
model soundness (G-AX) and refinement fidelity (this document, G-EQ).
