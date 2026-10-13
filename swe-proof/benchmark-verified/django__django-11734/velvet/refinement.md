# refinement.md — django__django-11734

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the two `do` blocks `comparisonNormalizesAsValue` and `subqueryTargetResolution`,
plus the deep `resolveInSubquery` model) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. Site 1 — the comparison-target guard (`related_lookups.py:104`)

Gold hunk:
```
- if not isinstance(self.lhs, MultiColSource) and self.rhs_is_direct_value():
+ if not isinstance(self.lhs, MultiColSource) and not hasattr(self.rhs, 'resolve_expression'):
```
(`rhs_is_direct_value()` = `not hasattr(self.rhs, 'as_sql')`, `lookups.py:98`.)

Modeled by `comparisonNormalizesAsValue (lhsSpansMultipleColumns) (t)`.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `lhsSpansMultipleColumns : Bool` | `isinstance(self.lhs, MultiColSource)` | R | `MultiColSource` ↔ `lhsSpansMultipleColumns = true` (mapping.md §2). |
| A2 | `t : Target` | the runtime kind of `self.rhs` | R | `OuterRef`/`F`/plain ↔ `outerRef`/`localRef`/`directValue` (mapping.md §2). |
| A3 | `targetIsExpression = match t with .directValue => false ǀ _ => true` (= `isExpression t`) | `hasattr(self.rhs, 'resolve_expression')` | I | identical concrete guard: the post-patch predicate is exactly "is the target a query expression". `OuterRef`/`F` have `resolve_expression`; plain values don't (mapping.md §2). G-CONF transliterates and compares against the real `hasattr`. |
| A4 | `out = (!lhsSpansMultipleColumns) && (!targetIsExpression)` (= `normalizesAsValue …`) | `not isinstance(...) and not hasattr(...)` | I | the whole guard, identical. The result decides whether the direct-value normalization branch runs. |

Discriminating content: an `outerRef` target has `isExpression = true`, so
`normalizesAsValue _ outerRef = false` — it is NOT normalized as a value. The
pre-patch guard used `rhs_is_direct_value()` (`not hasattr(rhs,'as_sql')`), which
is **true** for an `OuterRef` (no `as_sql`), so the old code WRONGLY normalized
it. `Solution_prepatch.lean` reproduces that (`targetIsDirectlyRenderable=false`
⇒ output `true` for `outerRef`) and **fails** `out = normalizesAsValue …`
(G-DIFF), on the `t = outerRef` case.

## B. Site 2 — the subquery rebind (`query.py:1705-1707`)

Gold hunk:
```
- if isinstance(filter_rhs, F):
+ if isinstance(filter_rhs, OuterRef):
+     filter_expr = (filter_lhs, OuterRef(filter_rhs))
+ elif isinstance(filter_rhs, F):
      filter_expr = (filter_lhs, OuterRef(filter_rhs.name))
```

Modeled by `subqueryTargetResolution (t)` = `resolveInSubquery (rebind t)`.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `t : Target` | `filter_rhs` runtime kind | R | as A2 (mapping.md §2). |
| B2 | `b = match t with .outerRef => .outerKeepingDepth ǀ .localRef => .outerByName ǀ .directValue => .unchanged` (= `rebind t`) | the post-patch `if/elif/else` rebind | I | identical dispatch: `OuterRef(filter_rhs)` (re-wrap) ↔ `outerKeepingDepth`; `OuterRef(filter_rhs.name)` ↔ `outerByName`; no rebind (carry through) ↔ `unchanged`. mapping.md §2. |
| B3 | `r = match b with …` (= `resolveInSubquery b`) | the UNCHANGED `resolve_expression` consulted later when the subquery runs | A-reference | how the rebound rhs resolves inside the subquery is the unchanged `OuterRef`/`ResolvedOuterRef.resolve_expression` semantics, modeled deeply and validated `== real callee` by G-AX. mapping.md §3.2. |

Discriminating content: for `t = outerRef`, post-patch `rebind = outerKeepingDepth`
⇒ `resolveInSubquery = staysOuter` (the rewrapped `OuterRef(OuterRef(name))`
peels one layer and stays an outer reference — usable in the subquery). Pre-patch
there was no `OuterRef` branch, so an `OuterRef` filter_rhs fell through to the
`F` branch (`OuterRef` IS an `F` subclass) and was rebound `outerByName` ⇒
`resolvesLocally` — a `ResolvedOuterRef` that raises `ValueError` when the
subquery is built. `Solution_prepatch_2.lean` reproduces that (`outerRef =>
outerByName`) and **fails** `out = resolveInSubquery (rebind t)` (G-DIFF), on
`t = outerRef`.

## C. The third gold hunk — `AutoField.get_prep_value` removal (no spec leg)

Gold also deletes `AutoField.get_prep_value` (`fields/__init__.py:2335-2337`).
Empirically the F2P test passes with sites 1+2 alone (mapping.md §0, §5): once
site 1 no longer coerces an `OuterRef` into a value, this override is never
reached with an `OuterRef` and the gold patch removes it as dead-code cleanup.
It changes no F2P/P2P-observable behavior, carries no spec clause, and is neither
an axiom nor a refinement leg — it rides along in `patch.diff` (gold verbatim)
for G-RESOLVE / PASS_TO_PASS only.

## D. No kind-3 (inexpressible-changed-op) steps

Every modeled step is R, A-reference, or I. The two operations that genuinely
*changed* — the site-1 guard predicate and the site-2 rebind dispatch — are
modeled **identically** (I), not hidden behind an axiom. The only A leg is the
**unchanged** downstream `resolve_expression` (B3, A-reference), validated by
G-AX. There is no consumed axiom and no inexpressible changed op.

## E. verify(Solution) ⇒ resolved

`comparisonNormalizesAsValue` verifies only if its output equals
`normalizesAsValue` (so an `outerRef` is NOT normalized as a value, A3/A4);
`subqueryTargetResolution` verifies only if its output equals
`resolveInSubquery (rebind t)` (so an `outerRef` rebinds to `outerKeepingDepth`
and resolves `staysOuter`, B2/B3). By R (mapping.md §2) these are exactly the two
post-patch decisions the gold makes for an `OuterRef` comparison target inside
`exclude()`/`~Q()`. By G-AX the deep model `resolveInSubquery` equals the real
`resolve_expression` (A-reference). By G-CONF the I transliterations of both
guards agree with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited callee — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: A-reference soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
