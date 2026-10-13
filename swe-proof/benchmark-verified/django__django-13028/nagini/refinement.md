# refinement.md — django__django-13028

The operation-by-operation correspondence between `model.py`'s implementation
(the `check_operands` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`/`Exsures`, and
**A-reference**, where a deep model is validated == the real callee/behaviour by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The guard site — `Query.check_filterable` (`django/db/models/sql/query.py:1125`)

Gold hunk (lines 1126–1131):
```
     def check_filterable(self, expression):
         """Raise an error if expression cannot be used in a WHERE clause."""
-        if not getattr(expression, 'filterable', True):
+        if (
+            hasattr(expression, 'resolve_expression') and
+            not getattr(expression, 'filterable', True)
+        ):
             raise NotSupportedError(
                 expression.__class__.__name__ + ' is disallowed in the filter '
                 'clause.'
             )
```
The unchanged tail (lines 1132–1134) recurses the SAME guard into every
sub-operand:
```
         if hasattr(expression, 'get_source_expressions'):
             for expr in expression.get_source_expressions():
                 self.check_filterable(expr)
```

| # | model.py impl op (`check_operands`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `is_expr: List[int]`, `permitted: List[int]` | the `expression` argument of `check_filterable` (plus the operands it transitively reaches via `get_source_expressions`) | R | the operand tree ↔ its **flattened guard-walk carriers** (mapping.md §2): one `(is_expr[i], permitted[i])` pair per operand visited, in the guard's recursion order. `is_expr[i]` ↔ `hasattr(operand_i, 'resolve_expression')`; `permitted[i]` ↔ `getattr(operand_i, 'filterable', True)` (absent ⇒ `True` ⇒ 1). The only observable of the pinned behaviour is which outcome the guard produces (accept vs. reject), a function of these two per-operand booleans. |
| A2 | the loop `while i < len(is_expr): ...` over all visited operands | the recursion: top-level call on `expression` plus `for expr in expression.get_source_expressions(): self.check_filterable(expr)` (lines 1132–1134, UNCHANGED) | R + I | the guard applies the SAME screen to the operand and every nested operand. The flattened pre-order walk (mapping.md §2) collapses that recursion into one loop over the carriers; observationally identical — the guard raises iff SOME visited operand is disallowed. The recursion structure is unchanged by the patch (A-reference: axiom_check.py validates the flattened model decision == the real recursive guard). |
| A3 | `if is_expr[i] == 1 and permitted[i] == 0: raise OperandNotAllowed()` | `if hasattr(expression, 'resolve_expression') and not getattr(expression, 'filterable', True): raise NotSupportedError(...)` | R + I | the patched disallow test. The added `hasattr(expression, 'resolve_expression')` conjunct ↔ `is_expr[i] == 1`; `not getattr(expression, 'filterable', True)` ↔ `permitted[i] == 0` (mapping.md §2). The conjunction (`and`) is identical control flow. `OperandNotAllowed` ↔ `NotSupportedError` (mapping.md §1; a builtin/db exception in an `Exsures` crashes the translator, so a user-defined stand-in is used — observationally the same raise). The message-string construction is the rejection payload, not observed by the accept/reject behaviour the F2P tests assert. |

The discriminating content of the change — a not-permitted operand is rejected
**only when it is also a query-expression operand** (`hasattr(...,
'resolve_expression')`), so a plain data operand that merely exposes a
`filterable=False` marker passes through — lives in the `is_expr[i] == 1 and`
conjunct of `check_operands` (model) ⇔ the added `hasattr(expression,
'resolve_expression') and` conjunct (real). The pre-patch test screened only the
marker; `model_prepatch.py` reproduces that (drops the `is_expr[i] == 1 and`
conjunct, raising on `permitted[i] == 0` alone) and **fails** verification on the
exceptional postcondition

  `Exsures(OperandNotAllowed, Exists k. is_expr[k]==1 and permitted[k]==0)`

— because on a plain-data not-permitted operand (`is_expr=0, permitted=0`) it
raises, yet the spec's `Exsures` requires the existence of a *query-expression*
not-permitted operand, which need not hold. That is exactly the spec sensing the
change (G-DIFF). It is also the exact F2P observation: filtering by a model
instance whose own field is named `filterable` with value `False`
(`Author.objects.filter(extra=self.e2)`) must NOT raise `NotSupportedError`,
because that instance is plain data (no `resolve_expression`), not an expression.

## B. No consumed axioms; the recursion is an A-reference

There is **no `@ContractOnly` axiom the proof consumes** — the guard's decision
is a self-contained conjunction over two per-operand integer observations,
modelled deeply. The one piece modelled *abstractly* is the operand-tree →
flattened-carrier collapse of the unchanged recursion (step A2), validated as an
**A-reference** by `axiom_check.py` (G-AX): a faithful in-Python reference of the
post-patch guard (the conjunction + the recursive `get_source_expressions` walk)
is run over an exhaustive boundary space + 20 000 fuzz operand trees and the REAL
`Query.check_filterable` over representative operands, asserting its accept/reject
decision equals `model_rejects(flatten(tree))` (the model predicate over the
flattened carriers) in every case — including the F2P plain-data case
(`filterable=False`, no `resolve_expression` ⇒ ACCEPT) and the
query-expression-not-permitted case (⇒ REJECT).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The operation that genuinely
*changed* — gating the disallow on the operand actually being a query expression
— is modelled **directly** by the `is_expr[i] == 1 and` conjunct in
`check_operands` (step A3). The function under change (`check_filterable`) is the
modelled function itself, not axiomatized; the only abstraction (the unchanged
recursive walk) is an A-reference, G-AX-validated. There is no A-consumed axiom
and no opaque oracle in the postcondition: the accept/reject outcome is pinned to
expressible structural predicates over the actual input carriers (an existential
conjunction over `is_expr`/`permitted`), so the result is *produced by* the
modelled branch, never *echoed* from a constant.

## D. verify(model) ⇒ resolved

`check_operands` verifies only if it raises `OperandNotAllowed` exactly when some
visited operand is BOTH a query-expression operand and not-permitted
(`Exsures` existential conjunction), and returns normally exactly when no such
operand exists (the universal `not (is_expr[k]==1 and permitted[k]==0)`
postcondition). By R (`expression`+sub-operands ↔ flattened
`(is_expr, permitted)` carriers; `hasattr(..., 'resolve_expression')` ↔
`is_expr==1`; `not getattr(..., 'filterable', True)` ↔ `permitted==0`;
`NotSupportedError` ↔ `OperandNotAllowed`) the verified guard equals the
post-patch `check_filterable` on the tested operands; by G-AX (A-reference) the
flattened model decision equals the real recursive guard's decision. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited recursion abstraction — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
abstraction soundness (G-AX) and refinement fidelity (this document, G-EQ).
