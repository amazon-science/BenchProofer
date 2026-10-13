# refinement.md — django__django-17084

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `wrappedEvaluationDecisionM` `do` block, the deep `referencesWindow` /
`aggregateUsesWindow` model, and the `wrappedEvaluationDecision` guard) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (a deep model validated == the real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs would be mechanically refuted by **G-CONF**; here the impl region's
operands are resolvable only against a live ORM query graph, so there is no
DB-free shadow to fuzz — `conf_skip=true` (see §C and mapping.md §4). The A legs
+ this narrative are audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The wrapping-subquery decision — `Query.get_aggregation` (`django/db/models/sql/query.py:402-457`)

Gold hunks (the three additions):
```
+ refs_window = False                                            # line 406
  ...
+ refs_window |= any(                                            # lines 423-426
+     getattr(self.annotations[ref], "contains_over_clause", True)
+     for ref in aggregate.get_refs()
+ )
  ...
+ or refs_window                                                 # line 457 (in the if-disjunction)
```

| # | Solution.lean impl op (`wrappedEvaluationDecisionM`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `aggregates : List (List Bool)` | the resolved per-aggregate `get_refs()` window flags, gathered over the `for alias, aggregate_expr in aggregate_exprs.items()` loop | R | each annotation's `getattr(…, "contains_over_clause", True)` (`bool`) ↔ `Bool`; one aggregate's `get_refs()` flag set ↔ inner `List Bool`; the aggregate sequence ↔ outer list (mapping.md §2). |
| A2 | parameter `priorConditions : Bool` | `isinstance(self.group_by, tuple) or self.is_sliced or has_existing_aggregation or refs_subquery or qualify or self.distinct or self.combinator` | R | the unchanged structural disjunction collapsed to its truthiness (mapping.md §2); the patch touches none of these operands. |
| A3 | `acc := aggregateUsesWindow refs \|\| acc` inside the backward `while` (so `acc = referencesWindow aggregates`) | `refs_window \|= any(getattr(self.annotations[ref], "contains_over_clause", True) for ref in aggregate.get_refs())`, accumulated across the loop | I | concrete, transliterated op: `\|=` over `bool` ↔ `\|\|`; `any(... for ref in get_refs())` ↔ `refs.any (fun b => b)` = `aggregateUsesWindow refs`. The whole-loop accumulation is the OR-fold `referencesWindow` (the front-recursive deep model, pure region), realized by the verified backward loop + drop-step lemma. |
| A4 | `return priorConditions \|\| acc` | `if (… or refs_window):` — the new `or refs_window` disjunct appended to the existing disjunction | I | concrete: `or` ↔ `\|\|`; `acc` is `refs_window` after the loop; the value pinned by `wrappedEvaluationDecision priorConditions aggregates`. |

Discriminating content of the change — the wrapping decision must additionally
fire when a requested aggregate references a window-using annotation — lives in
the `referencesWindow aggregates` disjunct of `wrappedEvaluationDecision` (model)
⇔ the `or refs_window` step (real). The pre-patch code omits this disjunct
entirely; `Solution_prepatch.lean` reproduces that (its loop never accumulates a
window flag, so it cannot maintain `acc = referencesWindow (aggregates.drop i)`)
and **fails** the invariant exactly when some aggregate uses a window function
(G-DIFF).

## B. No consumed axioms / no A-reference deep models of outside callees

The decision is a pure boolean function of already-resolved metadata. The
machinery that produces that metadata — `aggregate.get_refs()`,
`self.annotations[ref]`, and each annotation's `contains_over_clause`
(`expressions.py:246-250`; `Window.contains_over_clause = True`,
`BaseExpression.contains_over_clause = False`) — is UNCHANGED by the patch and is
read identically by both branches. It is shared context, not a contract the
proof consumes. There is therefore no `axiom` declaration, no A-consumed row, and
no A-reference deep model of an outside callee. `referencesWindow` /
`aggregateUsesWindow` are deep models of the *changed* accumulation itself (the
`refs_window` fold), tagged **I** above, not models of an unchanged callee.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — adding the
window-reference disjunct to the wrapping decision — is modeled **deeply** (the
spelled-out OR-fold `referencesWindow` over per-aggregate `aggregateUsesWindow`,
steps A3/A4), not hidden behind an axiom about the function under change.

## D. G-CONF skip rationale

The R/I ops above (A3/A4) are concrete and fuzzable in principle, but their
*operands* (A1: each aggregate's resolved `get_refs()` window flags; A2: the
structural conditions) are produced only by `aggregate_expr.resolve_expression`
against a live ORM query graph. The bug-vs-fix discriminator — an aggregate that
references a `Window`-based annotation while no prior structural condition holds
— is reproducible only by the F2P integration test itself, not as a pure DB-free
shadow. Hence `conf_skip=true`; soundness is carried by G-VERIFY + G-DIFF
(mapping.md §4). This is the django__django-13033 / -13315 precedent.
