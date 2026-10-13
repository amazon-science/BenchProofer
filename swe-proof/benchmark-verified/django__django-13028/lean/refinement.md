# refinement.md — django__django-13028

Operation correspondence between `implementation_checkFilterable`
(+ `implementation_checkFilterableAny`) in `Solution.lean` and `patch.diff`
(`Query.check_filterable`). Tags: **R** type refinement, **A-consumed** proof
uses axiom property, **A-reference** deep model validated == real callee (G-AX),
**I** identical concrete op.

| # | Lean op (impl) | patch.diff / Python op | tag | justification |
|---|---|---|---|---|
| 1 | `match e with \| .mk q f children` | the `expression` argument; its three touched facets | **R** | object → `Expr` bijection (mapping.md). Only `resolve_expression`-presence, `filterable`, and `get_source_expressions()` are observed. |
| 2 | `if q && !f then return true` | `if (hasattr(expression, 'resolve_expression') and not getattr(expression, 'filterable', True)): raise NotSupportedError(...)` | **R** + **I** | `q` ⇔ `hasattr(...,'resolve_expression')`; `!f` ⇔ `not getattr(...,'filterable',True)` (attribute-absence default `True` folded into `f`, mapping.md). `raise` ⇔ result `true` (R: exception↔Bool). The `&&` short-circuit conjunction is the identical control op (I) — this is the line the fix changes. |
| 3 | `return implementation_checkFilterableAny children` | `if hasattr(expression,'get_source_expressions'): for expr in expression.get_source_expressions(): self.check_filterable(expr)` | **R** + **I** | the `hasattr` guard + the loop are refined to recursion over `children` (object lacking the method ⇒ `children = []`, mapping.md). Reaching here ⇔ no rejection yet ⇒ result is whatever the children produce. |
| 4 | `…Any [] => false` | loop completes with no `check_filterable` having raised ⇒ normal return | **I** | empty child list raises nothing. |
| 5 | `…Any (c :: cs) => implementation_checkFilterable c \|\| …Any cs` | `for expr in ...: self.check_filterable(expr)` — first child that raises aborts the loop and propagates | **R** + **I** | observable result is "does it raise"; `||` (left-to-right short-circuit) faithfully models the loop where the first raising child terminates iteration. |

No op is changed-inexpressible. The whole decision is modeled structurally.

## Axioms
None. `check_filterable` calls only `getattr`/`hasattr`/`get_source_expressions`
and recurses on itself; none is an unchanged external callee whose behavior the
proof must assume. ⇒ no A-consumed, no A-reference rows; `axiom_check.py` is a
skip stub.

## conf_skip
`false` — the impl region is R/I-tagged (no A-tagged callees), so G-CONF
mechanically differential-tests the full R/I shadow against `patch.diff`.
