# mapping.md — django__django-13315

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 36bc47069ce071e80c8129500de3b8664d2058a7`, states the type
abstraction, and records why this bundle consumes no `@ContractOnly` axiom.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `offered_options(matches)` | `apply_limit_choices_to_to_formfield(formfield)` — `django/forms/models.py:98` (body lines 100-103) | the modeled changed function: it narrows `formfield.queryset` by `get_limit_choices_to()` and must expose duplicate-free options |
| `dedup(s)` *(deep model)* | the duplicate-elimination semantics the patch introduces — `formfield.queryset.filter(Exists(... ._base_manager.filter(complex_filter)))` (`django/forms/models.py:111-115` post-patch) | pure spec: the duplicate-free image of the raw matching stream |
| `occurs(v, s)` | "this row identifier is among the matched rows" — the membership the `Exists()` subquery tests | pure spec helper: sequence membership |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view):
`formfield.queryset.complex_filter(limit_choices_to)` (`models.py:103`), which —
when `limit_choices_to` spans a relational join — adds the join to the SELECT and
returns one row per satisfying join path, i.e. the raw matching stream WITH
duplicates. `QuerySet.complex_filter` is `django/db/models/query.py:968`
(`add_q` / `_filter_or_exclude`, no DISTINCT).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `formfield.queryset` (a `QuerySet` of related-model rows), observed only through which rows it yields and with what multiplicity | `List[int]` of row identifiers (primary keys) | the queryset's yielded rows ↔ the list elements; a row's primary key ↔ its `int`; row equality ↔ `int` equality (the F2P test compares with `assertCountEqual`, i.e. multiset/membership equality, so identity is carried by the pk) |
| the raw matching pass — applying `limit_choices_to` across the join (`complex_filter` adds the join, one output row per satisfying join path) | the input `matches: List[int]` (a row id repeats once per satisfying join path) | a satisfying join path for row `r` ↔ an occurrence of `r` in `matches`; number of duplicates of `r` ↔ number of join paths matching `r` |
| the offered options (`formfield.queryset` after the narrowing) | the returned `List[int]` | yielded rows ↔ list elements; the gold patch's `Exists()`-wrapping yields each matching row at most once ↔ the list is duplicate-free |
| `str`/`Q`/`dict`/`OuterRef`/`Exists`/`_base_manager` machinery (`Q(**limit_choices_to)`, `complex_filter &= Q(pk=OuterRef('pk'))`, `Exists(... ._base_manager.filter(...))`) | omitted (collapsed into the dedup semantics) | this machinery is the MECHANISM by which the patch obtains the distinct matching rows; its observable net effect on the queryset's contents is exactly "the duplicate-free set of rows that satisfy `limit_choices_to`", which is what `dedup`/`occurs` encode. The F2P test observes only the resulting rows (`assertCountEqual`), not the SQL. |

Nagini bans richer object graphs (`QuerySet`, `Q`, expression trees), so the
carrier is `List[int]` and the specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Why no consumed axiom (no `@ContractOnly`)

The operation that CHANGED is the collection-level behaviour: the offered
options must be the **duplicate-free** image of the join-matching stream rather
than the raw stream. That behaviour is modelled **deeply** — the front-recursive
fold `dedup` (with the membership helper `occurs`) IS the duplicate elimination,
and `offered_options` is verified to compute exactly it. There is no unchanged
library callee whose `Ensures` the proof consumes:

- `complex_filter` is the pre-patch call being REPLACED, not a callee the new
  code relies on — axiomatizing it is forbidden (it is the changed operation).
- `Exists` / `OuterRef` / `Q` / `_base_manager.filter` are the MECHANISM the
  patch uses to realise the dedup at the SQL layer; the spec does not depend on
  any contract of theirs, only on their net observable effect (distinct rows),
  which the deep model `dedup` captures directly.

Consequently this bundle ships no `@ContractOnly` axiom and no A-consumed /
A-reference row in refinement.md. `axiom_check.py` instead validates the
**behavioural fact the deep model rests on** against real runtime semantics
(below), per the no-axiom convention (cf. django__django-13158).

## 4. Deep-model soundness check (G-AX, no axioms)

`axiom_check.py` reconstructs, in-process and DB-free, the two query semantics
the twin contrasts and asserts the deep model is faithful to them:

1. **The dedup semantics the gold patch realises.** The gold path wraps the
   join filter in `Exists(... ._base_manager.filter(complex_filter))` and
   filters the field's queryset by it: a base row is emitted iff at least one
   join path satisfies the restriction, and — because `Exists` is a per-row
   correlated subquery rather than a join in the outer SELECT — it is emitted
   **at most once**. `axiom_check.py` reproduces this as: from a raw matching
   stream (row id once per satisfying join path), the offered options are
   `{r : r matched at least once}` with each `r` once. It asserts this equals
   the model's `dedup` reference (membership preserved, no duplicate) over
   boundary + randomized fuzz multisets, and that the model's `occurs` reference
   equals real membership.

2. **The pre-patch duplicate semantics.** `complex_filter` over a join returns
   the raw stream verbatim (one row per join path) — `axiom_check.py` asserts
   the raw stream still carries the duplicates whenever a row matched along more
   than one join path, which is exactly what `model_prepatch.py` reproduces and
   what its failing clause `ToSeq(Result()) == dedup(ToSeq(matches))` rejects.

Imports only the standard library; it asserts pure set/multiset relations over
the modelled `List[int]` carrier (no DB connection, no settings, no SQL needed —
the contrast is "raw join-match stream" vs "its distinct image", which is a
collection fact). Exit 0 iff every obligation holds.

Provenance for the SQL semantics: `QuerySet.filter` /
`django.db.models.expressions.Exists` (`django/db/models/expressions.py:1139`)
— `Exists` is a `Subquery` used as a boolean correlated predicate, so it
restricts membership of the outer rows without multiplying them; gold patch
comment: "Use Exists() to avoid potential duplicates."
