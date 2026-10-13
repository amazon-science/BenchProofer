# refinement.md — django__django-11734

The operation-by-operation correspondence between `model.py`'s implementation
(the two contracted functions `rebind_into_inner_subquery` and
`normalize_only_concrete_value`, plus the pure helpers `is_query_expression`,
`target_level`, `resolved_level_in_inner`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (proof uses an
axiom's `Ensures`), **A-reference** (a deep model validated == the real callee
by `axiom_check.py` / G-AX, NOT consumed), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

This bundle consumes **no axiom** (no `@ContractOnly`): both modelled
behaviours are pure integer/boolean decisions, fully expressible. The
query-expression/level semantics they rest on are validated against the real
Django objects by G-AX as **A-reference** rows.

## A. The inner-subquery re-anchor — `Query.split_exclude` (`query.py:1685`)

Gold hunk:
```
  filter_lhs, filter_rhs = filter_expr
- if isinstance(filter_rhs, F):
+ if isinstance(filter_rhs, OuterRef):
+     filter_expr = (filter_lhs, OuterRef(filter_rhs))
+ elif isinstance(filter_rhs, F):
      filter_expr = (filter_lhs, OuterRef(filter_rhs.name))
```

| # | model.py impl op (`rebind_into_inner_subquery`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rhs_kind: int ∈ {value, local, outer}` | the value `filter_rhs` (a plain value, an `F`, or an `OuterRef`) | R | object kind ↔ int tag (mapping.md §1, §2). `OuterRef` is a subclass of `F`, so the gold tests `isinstance(.., OuterRef)` first, then `isinstance(.., F)`; the model's three disjoint tags capture exactly the three branches (plain value → neither). |
| A2 | `if rhs_kind == kind_value(): return 0` | no rewrite of `filter_expr` (the implicit else: plain value untouched) | I/R | a plain value is carried in unchanged: zero `OuterRef` hops. |
| A3 | `if rhs_kind == kind_local(): return 1` | `elif isinstance(filter_rhs, F): filter_expr = (filter_lhs, OuterRef(filter_rhs.name))` | R | re-anchoring an `F` as `OuterRef(name)` = one outward `OuterRef` hop. By G-AX (mapping.md §3.2) `OuterRef(name).resolve_expression()` is a `ResolvedOuterRef`, i.e. the originally-local reference (level +1 in the inner subquery) now denotes the original query (level 0): `resolved_level_in_inner(local)=1`, `target_level(local)=0`, `1 − 1 == 0`. |
| A4 | `return 1` (the `kind_outer` branch) | `if isinstance(filter_rhs, OuterRef): filter_expr = (filter_lhs, OuterRef(filter_rhs))` | R | re-anchoring an `OuterRef` as `OuterRef(filter_rhs)` = one outward `OuterRef` hop, wrapping the OuterRef in a further OuterRef. By G-AX (mapping.md §3.2) `OuterRef(OuterRef(name)).resolve_expression()` returns the inner unresolved `OuterRef` (preserving one outward level), so the reference (level -1, one out from the original query) is preserved rather than collapsing onto the original query: `resolved_level_in_inner(outer)=0`, `target_level(outer)=-1`, `0 − 1 == -1`. |

The discriminating content of site A — an `OuterRef` right-hand side must get
**one extra outward hop**, not zero — lives in the post-condition
`resolved_level_in_inner(rhs_kind) − Result() == target_level(rhs_kind)` for
`kind_outer`. `model_prepatch.py` reproduces the pre-patch behaviour (`OuterRef`
carried in with **zero** hops) and **fails** exactly this clause (G-DIFF). This
is the bug the F2P test `test_subquery_exclude_outerref` observes: without the
extra hop the outer reference resolves onto the generated inner subquery instead
of the outer query.

## B. The normalise-only-concrete-value guard — `RelatedLookupMixin.get_prep_lookup` (`related_lookups.py:103`)

Gold hunk:
```
- if not isinstance(self.lhs, MultiColSource) and self.rhs_is_direct_value():
+ if not isinstance(self.lhs, MultiColSource) and not hasattr(self.rhs, 'resolve_expression'):
      # If we get here, we are dealing with single-column relations.
      self.rhs = get_normalized_value(self.rhs, self.lhs)[0]
```

| # | model.py impl op (`normalize_only_concrete_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `rhs_kind: int` | `self.rhs` (plain value / `F` / `OuterRef`) | R | as A1. |
| B2 | `return not is_query_expression(rhs_kind)` | `not hasattr(self.rhs, 'resolve_expression')` (the `not isinstance(self.lhs, MultiColSource)` conjunct is the single-column-relation guard, orthogonal to the right-hand-side decision and held fixed) | R / A-reference | `is_query_expression(kind)` ⇔ `hasattr(self.rhs, 'resolve_expression')`: True for `F`/`OuterRef`, False for a plain value. Validated against real objects by G-AX (mapping.md §3.1). So normalisation runs iff the right-hand side is a plain concrete value. |

The discriminating content of site B — a query expression (an `F` or an
`OuterRef`) must **not** be normalised — lives in
`Ensures(Result() == (not is_query_expression(rhs_kind)))`. `model_prepatch_2.py`
reproduces the pre-patch predicate `self.rhs_is_direct_value()` =
`not hasattr(self.rhs, 'as_sql')`, which is `True` for every relevant kind
(`F`/`OuterRef` lack `as_sql`), i.e. it normalises all three; it **fails**
exactly this clause (G-DIFF).

## C. The auto-field special-case removal — `AutoField.get_prep_value` (`fields/__init__.py:2335`)

Gold hunk (removal):
```
- def get_prep_value(self, value):
-     from django.db.models.expressions import OuterRef
-     return value if isinstance(value, OuterRef) else super().get_prep_value(value)
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | (no node) | deletion of `AutoField.get_prep_value` | I | this method existed solely to let an `OuterRef` pass through the auto-field's value preparation unharmed. With site B, an `OuterRef` is no longer treated as a direct value and so never reaches a related field's `get_prep_value` at all — the special case becomes unreachable dead code and is removed. It changes no reachable behaviour beyond site B, so it has no independently-observable fixed behaviour and no separate `model_prepatch`. (Its safety is *implied by* site B's `normalize_only_concrete_value` returning `False` for `kind_outer`.) |

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — the inner-subquery re-anchor (site A) and the normalise guard
(site B) — are modelled **deeply** as integer/boolean decisions whose semantics
are validated against the real `OuterRef`/`F`/`ResolvedOuterRef` objects by
G-AX (A-reference, mapping.md §3); there is **no `@ContractOnly` axiom** the
proof consumes, hence no dead axiom. The auto-field removal (site C) is an
identical concrete deletion of code rendered unreachable by site B.

## E. verify(model) ⇒ resolved

`rebind_into_inner_subquery` verifies only if an `OuterRef` right-hand side
receives exactly the extra outward hop that preserves its denoted query level
(site A, post-condition over `target_level`/`resolved_level_in_inner`), and
`normalize_only_concrete_value` verifies only if a query expression is excluded
from value normalisation (site B). By R (object kind ↔ int tag, hop ↔
`OuterRef` wrapping) and by G-AX (the level arithmetic == real
`OuterRef.resolve_expression`; the classification == real
`hasattr(resolve_expression)`), the verified decisions equal the gold patch's
two edits on the tested inputs, and the third edit (site C) is the safe
removal those edits make unreachable. The gold patch resolves (G-RESOLVE). The
trust point is exactly refinement fidelity (this document, G-EQ) plus the
A-reference fidelity G-AX confirms; there is no axiom-soundness trust point
because no axiom is consumed.
