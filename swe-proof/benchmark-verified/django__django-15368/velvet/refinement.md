# refinement.md — django__django-15368

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`routeOperands` `do` block and the deep `wrapPlan` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (here absent) A legs and this narrative are audited by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The routing site — `QuerySet.bulk_update` inner loop (`django/db/models/query.py:668-675`)

Gold hunk (import line 20 + the predicate at line 673):
```
- from django.db.models.expressions import Case, Expression, F, Ref, Value, When
+ from django.db.models.expressions import Case, F, Ref, Value, When
  ...
  for obj in batch_objs:
      attr = getattr(obj, field.attname)
-     if not isinstance(attr, Expression):
+     if not hasattr(attr, 'resolve_expression'):
          attr = Value(attr, output_field=field)
      when_statements.append(When(pk=obj.pk, then=attr))
```

| # | Solution.lean impl op (`routeOperands`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `attrs : List AttrVal` | the sequence of `attr = getattr(obj, field.attname)` over `batch_objs` | R | each `obj`'s assignment value ↔ one `AttrVal ⟨isDbExpr, strictMatch⟩` (mapping.md §2). G-CONF bridges by constructing the real value and reading the two predicates. |
| A2 | per element, output bit `! a.isDbExpr` (i.e. `wrapPlan attrs`) | `if not hasattr(attr, 'resolve_expression'): attr = Value(attr, output_field=field)` | R + I | the changed predicate `hasattr(attr,'resolve_expression')` ↔ `AttrVal.isDbExpr` (R; mapping.md §2). The decision `wrap ⇔ ! isDbExpr` and the per-element walk are **I** (concrete, transliterated by G-CONF). This is the discriminating op. |
| A3 | (no node) — `Value(attr, output_field=field)` wrapping, `When(pk=…, then=attr)`, `Case(...)`, optional `Cast`, emitted SQL | `query.py:674-682` | I (shared continuation) | UNCHANGED on both branches; reached identically regardless of the routing bit. The model abstracts each element's outcome to the single observable bit "was it wrapped as a literal" (A2's output); the construction that consumes that bit is not modeled because the patch does not touch it. G-CONF observes its end-to-end effect (resolved-on-DB vs stored-as-literal). |

Discriminating content of the change — a value that **is** a database-side
expression but is **not** a subclass of the coarse `Expression` base (in this
repo, a plain field reference `F('name')`: `isDbExpr=True`, `strictMatch=False`)
— is routed `! isDbExpr = false` (applied directly) by the spec, vs the pre-patch
`! strictMatch = true` (wrapped as a literal, freezing its surface form). This
single bit lives in `wrapPlan`'s `! a.isDbExpr` (model) ⇔ the
`not hasattr(attr,'resolve_expression')` guard (real). `Solution_prepatch.lean`
reproduces the pre-patch `isinstance(attr, Expression)` predicate
(`! a.strictMatch`) and **fails** `out = wrapPlan attrs` — specifically the loop
body leaves the goal `strictMatch = isDbExpr`, unprovable exactly at the `F`
witness (G-DIFF).

## B. No additional change sites

The patch is a single behavioural change at one site (plus the now-unused
`Expression` import it drops). There is no second independently-observable fixed
behavior, hence one `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The one operation that genuinely *changed* — the routing
predicate — is modeled **directly** (the `! isDbExpr` bit of `wrapPlan`, step A2,
R + I), not hidden behind an axiom about the function under change. There is **no
consumed axiom and no A-reference**: the surrounding `Value`/`When`/`Case`/`Cast`/
SQL machinery (step A3) is the unchanged shared continuation, so it is not
contracted (it would be a dead axiom) and not deep-modeled (it did not change).
The only soundness obligation is the **R** type bijection of mapping.md §2 — that
`isDbExpr`/`strictMatch` equal the real predicates and that `! isDbExpr` is the
real post-patch wrap decision — which G-AX checks against the real value classes
(`axiom_check.py`).

## D. verify(Solution) ⇒ resolved

`routeOperands` verifies only if its per-element output equals `! isDbExpr`
(A2) — i.e. a database-side expression is applied directly and everything else is
wrapped as a literal. By R (`attr ↔ AttrVal`, predicate ↔ field bijection,
mapping.md §2) the verified routing equals the post-patch
`not hasattr(attr,'resolve_expression')` decision on the assignment values
`bulk_update` receives; by the shared continuation (A3) the downstream `When`/
`Case`/SQL emission is identical to gold; by G-AX the bijection is real (the
witness `F('name')` exhibits the strict gap and routes correctly) and by G-CONF
the R/I transliteration of `wrapPlan` agrees with `patch.diff`'s end-to-end
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF) plus the R bijection's reality (G-AX); there are no axiom-soundness trust
points because there are no axioms.
