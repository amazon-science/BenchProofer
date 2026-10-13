# refinement.md — django__django-11490

The operation-by-operation correspondence between `model.py`'s implementation
(the `columns_for_subquery` impl region and the deep `detached_copy` /
`with_columns` models — neutral behavioral names, directive 6) and `patch.diff`
(the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The combinator-compilation site — `get_combinator_sql()` (`django/db/models/sql/compiler.py:410`, body lines 426-433)

Gold hunk (`compiler.py`, inside the `for compiler in compilers:` loop):
```
                 if not compiler.query.values_select and self.query.values_select:
+                    compiler.query = compiler.query.clone()
                     compiler.query.set_values((
                         *self.query.extra_select,
                         *self.query.values_select,
                         *self.query.annotation_select,
                     ))
```

The modelled function `columns_for_subquery(cached, outer_select)` is the
faithful skeleton of the body of this `if` branch, which is reached exactly when
the component sub-compiler's query has no column list of its own
(`not compiler.query.values_select`) and the outer query restricts the columns
(`self.query.values_select` non-empty). `cached` ↔ `compiler.query` (the reused
component sub-query); `outer_select` ↔ the outer query's chosen column tuple
`(*extra_select, *values_select, *annotation_select)`.

| # | model.py impl op (`columns_for_subquery`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `cached: Query` with model fields `cached.columns`, `cached.leading`, `cached.trailing` (each `List[int]`) and `cached.state: int` | `compiler.query`, a `django.db.models.sql.query.Query`, with its `values_select` tuple, the ordered keys of its `extra_select` and `annotation_select` views, and the rest of its accumulated per-query state (the `where` clause and the two derived-column definition dicts) | R | the reused component sub-query modelled with its three touched column families (`columns` ↔ `values_select`; `leading` ↔ `extra_select` keys, emitted ahead of the query's own columns and consulted FIRST in the classification; `trailing` ↔ `annotation_select` keys, emitted after) plus an opaque token `state` abstracting the REST of the accumulated state; each family ↔ `List[int]` of column codes (mapping.md §1, §2). Held at fractional permission (directive 5) — under the fix the shared query is read-only. |
| A2 | parameter `outer_select: List[int]`, `len(outer_select) > 0` | the outer column tuple `(*self.query.extra_select, *self.query.values_select, *self.query.annotation_select)`, non-empty because the branch requires `self.query.values_select` | R | the chosen column tuple ↔ `List[int]`; the branch guard `self.query.values_select` non-empty ↔ `len(outer_select) > 0` (mapping.md §2). |
| A3 | branch guard `len(cached.columns) == 0` (a precondition; the branch is entered only here) | `if not compiler.query.values_select` | R | "the component has no column list of its own" ↔ empty model `columns` / empty repo `values_select` (an empty tuple is falsy) (mapping.md §2). Note the guard constrains ONLY the component's own column list: a component exposing any number of derived columns is in domain, which the battery's `cfs-admissibility` case witnesses. |
| A4 | `private = detached_copy(cached)` | `compiler.query = compiler.query.clone()` — **the FIX** | A-reference | the added `.clone()` call is modelled DEEPLY by `detached_copy` (the spelled-out three-loop copy in the impl region): it returns a FRESH, DISTINCT object (`Result() is not cached`, and each of the three containers `is not` the original's) whose three column families copy the original's — in particular both derived families arrive **un-narrowed** — and which CARRIES the original's accumulated state (`Result().state == cached.state`, the opaque token abstracting the where clause and the two definition dicts), without mutating the original (`cached.columns` left empty, both families and `cached.state` unchanged). The state-carry clause is what distinguishes a clone from a brand-new blank query: an impl that builds a fresh `Query` and merely matches the column selection CANNOT satisfy `Result().state == cached.state` and is rejected. There is no consumed `clone` axiom — the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py leg E) runs the real `Query.clone()` and asserts distinctness, independent containers AND independent select masks, the un-narrowed family carry, the where/extra/annotation state carry, and that a later `set_values` on the copy never narrows the original (mapping.md §3.1). |
| A5 | `with_columns(private, outer_select)` | `compiler.query.set_values((...))` (now invoked on the cloned `compiler.query`) | A-reference | the unchanged `set_values` is modelled DEEPLY by `with_columns` (model.py). It does **not** record the chosen list verbatim: it CLASSIFIES each requested name against the derived columns the query exposes at that moment and NARROWS both families, which is exactly the callee's partition at `query.py:2050-2062` (`field_names` / `extra_names` / `annotation_names`, then `set_extra_mask` / `set_annotation_mask`, then `values_select = tuple(field_names)`). The three model equations `q.columns == own_columns(fields, leading, trailing)`, `q.leading == kept_leading(leading, fields)`, `q.trailing == kept_trailing(trailing, fields, leading)` are that partition read back through the `extra_select` / `annotation_select` properties, with the third argument of `kept_trailing` encoding that the `extra` test comes first. The callee's `field_names = list(fields)` shortcut (guarded by `not self.extra and not self.annotations`, `query.py:2046-2048`) is the degenerate case of the same equations, so no case split is needed. The accumulated state is untouched (`q.state == Old(q.state)`): only `values_select` and the two masks are rebound. G-AX validates all of this on the real callee — legs A (1423 pristine shapes), B (1844 already-narrowed ones), D (a name in both families is claimed by the leading one) — and leg C records why an empty chosen list is excluded by precondition rather than claimed (mapping.md §3.2). |
| A6 | `return private` (the per-compilation query carrying the classified column selection) | the loop continues with `compiler` now holding the cloned query; `compiler.as_sql()` then renders SQL from that private query's three families | R | the column selection carried into the rest of the compilation is the private copy's, not the shared sub-query's; the rendered column order is `extra_select` keys ++ `values_select` ++ `annotation_select` keys, which is the model's `leading ++ columns ++ trailing` (mapping.md §2, and the differential G-CONF shadow checks exactly that rendered order). |

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it drops step **A4** (the
`.clone()`) exactly as the pre-patch branch did, applying the chosen list
directly to the reused `compiler.query` and continuing with it:
```
with_columns(cached, outer_select)   # mutate the SHARED sub-query in place
return cached
```
With the byte-identical frozen spec it **fails** verification:
`model_prepatch.py:473 — The precondition of method with_columns might not hold.
There might be insufficient permission to access q.columns.` The spec
holds the shared `cached` sub-query at fractional (read-only) permission
(directive 5) — under the fix it is never mutated — so the pre-patch's in-place
mutation of the shared query cannot be expressed without violating the
read-only contract. Equivalently, the postconditions
`Ensures(len(cached.columns) == 0)`, `Ensures(ToSeq(cached.leading) ==
Old(ToSeq(cached.leading)))` (and the same for `trailing`) and
`Ensures(Result() is not cached)` pin exactly the aliasing break the fix
introduces; the pre-patch mutates and returns the shared object, contradicting
all of them.

This is precisely the behaviour the F2P test observes
(`test_union_with_values`): after `qs1.union(qs1).values_list('name', 'order',
'id').get()`, a second `qs1.union(qs1).values_list('order').get()` must yield
`(2,)`. The two evaluations reuse the SAME component sub-query object
(`combined_queries = (qs1.query, ...)`); the pre-patch's first evaluation
mutated that shared query's `values_select` to `('name','order','id')`, so the
guard `not compiler.query.values_select` skipped the second evaluation's
`('order',)` and the wrong column list was used. The clone leaves the shared
query untouched so the second evaluation's list takes effect — exactly what the
spec's "shared sub-query unchanged + result reflects the current `outer_select`"
postconditions enforce.

The spec also senses the second wrong-fix family: replacing the per-compilation
query with a brand-new blank object instead of a copy. Such an impl can satisfy
the aliasing clauses (the shared query is untouched and the result is distinct)
but drops the sub-query's accumulated state — in the repo, its `where` filters
and its `extra` / `annotations` definitions — so sibling tests that exercise a
compound query WITH that state produce wrong rows. The model pins this via the
opaque state token: `Ensures(Result().state == cached.state)` cannot be met by a
freshly constructed object whose token is unrelated to `cached.state`, only by a
copy carried from `cached` (mirroring `clone()`'s whole-`__dict__` copy).

And it senses a third family, the one the classification in A5 exists for: an
impl that applies the chosen list MORE THAN ONCE to the working object (or
applies it to an object whose families were already narrowed). Because the
partition is taken against the families exposed at that moment, a second
application classifies against the narrowed view, and every requested name that
resolved to a derived column dropped by the first application is then taken for
one of the query's own columns. The spec's oracle is a function of the SHARED
sub-query's UN-narrowed families
(`own_columns(outer_select, cached.leading, cached.trailing)` and the two
`kept_*` clauses), so only a single application to a faithful copy reaches it.
This is not a hypothetical: it is the audited counterexample. A rival that first
narrowed the working object to the LAST entry of the chosen list and only then
applied the full list verified against the earlier revision of this spec — that
revision's only functional claim was the unconditional `ToSeq(Result().columns)
== ToSeq(outer_select)`, which the second application satisfies, so the first
one looked like dead code — while its patch did NOT resolve: FAIL_TO_PASS 1/1
passed but PASS_TO_PASS failed 2/23,
`queries.test_qs_combinators.QuerySetSetOperationTests.test_union_with_extra_and_values_list`
and `test_union_with_two_annotated_values_list`. In the real callee that first
application is not dead: it narrows both select masks to the single name, so the
second one classifies against the narrowed families. G-AX leg F measures the
underlying fact on the real callee: on 984 of 984 shapes a second application
never reaches the single-application outcome. Two battery cases pin the family
at the verifier level — `cfs-narrow-then-full` carries the audited body verbatim
(and now fails on the `own_columns` clause), and `cfs-double-application`
carries the reverse order. The order is itself the control: with the
applications reversed the earlier spec would already have rejected the rival, so
only the audited order witnesses the hole this repair closed.

Termination is likewise pinned: every contracted function carries a
`MustTerminate` obligation (loops consume it with a strictly-decreasing
measure), so no impl can satisfy the postconditions vacuously by diverging.

### B.1 A known proof-strength limitation (recorded, not hidden)

Applying the SAME chosen list twice is, semantically, idempotent: for every
`x ∈ fields`, `x` is in `kept_leading(L, fields)` iff `x ∈ L`, and likewise for
the trailing family, so
`own_columns(fields, L∩fields, (T∩fields)\L) == own_columns(fields, L, T)`
and both narrowings are already fixpoints. An implementation that calls
`with_columns(private, outer_select)` twice therefore agrees with the gold on
every input. Nagini/Z3 does not discharge that idempotence lemma from the
back-recursive `@Pure` definitions, so such a rival is REJECTED on the
`own_columns` clause. This is a proof-strength limitation of the verifier, not a
behavioural distinction the spec intends: the spec is *stronger than necessary*
on exactly that one shape. It is recorded here rather than papered over, and it
is deliberately NOT a battery case (asserting `expect: reject` for a rival whose
patch resolves would claim a behavioural difference that does not exist). The
gate-relevant direction is unaffected: a "too strong" shape cannot make a wrong
implementation verify, and the spec's positive controls (an extra intermediate
copy; guard-inverted classification loops; a hoisted loop bound) all verify.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — inserting the `.clone()` that detaches the per-compilation query
from the reused/shared sub-query — is modelled **deeply** (`detached_copy`, an
**A-reference** spelled out as a fresh object with three copied containers, step
A4), not hidden behind an axiom about the function under change: there is no
consumed `clone` axiom. The companion `with_columns` (step A5) is also an
**A-reference** (an unchanged callee the branch already invoked pre-patch — the
repo `Query.set_values`), and its classification/narrowing law is spelled out by
the three `@Pure` functions and re-derived by the three loops in its impl
region. There are **no A-consumed axioms** in this bundle. G-AX validates both
deep models against the real `Query.clone()` / `Query.set_values()`.

## D. verify(model) ⇒ resolved

`columns_for_subquery` verifies only if it

  * (A4) detaches via a fresh, distinct object with three independent containers
    that copies — and does not mutate, in particular does not narrow — the
    shared sub-query, AND carries its accumulated state token (so a blank
    replacement object is excluded, not just an in-place mutation); and
  * (A5/A6) yields a query whose three column families are exactly the chosen
    list CLASSIFIED against the shared sub-query's UN-narrowed derived families
    — `own_columns(outer_select, cached.leading, cached.trailing)`,
    `kept_leading(cached.leading, outer_select)`,
    `kept_trailing(cached.trailing, outer_select, cached.leading)` — with that
    state intact.

The second bullet is what makes the first insufficient on its own: it fixes the
outcome as a function of the SHARED object's state, so neither a verbatim
assignment of `outer_select` (which ignores the derived families) nor a repeated
application (which classifies against a narrowed view) can satisfy it.

By R (the `Query`; `values_select` ↔ `columns`; the `extra_select` /
`annotation_select` key orders ↔ `leading` / `trailing`; the remaining
accumulated state ↔ the opaque `state` token; the branch guard; the outer column
tuple) the verified path equals the gold branch
`compiler.query = compiler.query.clone(); compiler.query.set_values((...))` on
the tested inputs, and the rendered column order `extra_select ++ values_select
++ annotation_select` equals the model's `leading ++ columns ++ trailing`. By
G-AX the real `Query.clone()` returns a distinct object copying all three
families un-narrowed with independent masks AND the where/extra/annotation
state, without mutating the original (the A-reference of A4), and the real
`Query.set_values()` performs exactly the modelled classification and narrowing
while preserving that state, on pristine and on already-narrowed queries alike
(the A-reference of A5). G-CONF closes the same loop differentially at the
rendered-SQL level: the contract-stripped impl region and the real patched
compound-query branch agreed on 105456 compilation checks with 0
disagreements, over inputs that carry `extra` entries and annotations, so the
classification is checked against reality and not only against the model's own
`@Pure` functions.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness / deep-model fidelity (G-AX, G-CONF) and refinement fidelity (this
document, G-EQ).
