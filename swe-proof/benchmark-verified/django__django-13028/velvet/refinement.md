# refinement.md — django__django-13028

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `checkFilterable` `do` block, plus the `nodeBad`/`anyBad` pure model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs, so G-EQ has only the overall correspondence
narrative to audit. Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The guard site — `check_filterable()` (`django/db/models/sql/query.py:1125`)

Gold hunk:
```
-        if not getattr(expression, 'filterable', True):
+        if (
+            hasattr(expression, 'resolve_expression') and
+            not getattr(expression, 'filterable', True)
+        ):
             raise NotSupportedError(...)
         if hasattr(expression, 'get_source_expressions'):
             for expr in expression.get_source_expressions():
                 self.check_filterable(expr)        # unchanged recursion
```

| # | Solution.lean impl op (`checkFilterable`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `nodes : List Node` | the operand tree rooted at `expression`, walked DFS | R | the set of all nodes `check_filterable` visits (root + transitive `get_source_expressions()`) ↔ `List Node` (mapping.md §2). Order is irrelevant: the observable is an order-independent OR over per-node guards. |
| A2 | `Node.filterable` / `Node.isOperand` field reads | `getattr(node,'filterable',True)` / `hasattr(node,'resolve_expression')` | R | attribute presence/value ↔ `Bool` field (mapping.md §2). G-CONF exercises both real builtins on nodes with/without each attribute. |
| A3 | `nodeBad n = n.isOperand && !n.filterable` | the post-patch guard `hasattr(...,'resolve_expression') and not getattr(...,'filterable',True)` | I | the changed per-node condition, modeled **identically**: the boolean structure (`isOperand AND NOT filterable`) is the patched `if`. This IS the operation the patch changed; it is modeled concretely, not behind an axiom. |
| A4 | `result = anyBad nodes`: the backward `while` fold OR-ing `nodeBad` over every node | the recursion `check_filterable` raises iff any visited node trips the guard | R + I | the unchanged DFS reduces to "does any visited node offend"; `anyBad`/`||` is that disjunction (R for the traversal shape, I for the `||`). G-CONF transliterates it and diffs against the real patched function. |
| A5 | `raised : Bool` return | `check_filterable` raises `NotSupportedError` (else returns `None`) | R | raise ↔ `raised = true`; the only observable of `check_filterable` is whether it raises (mapping.md §2). |

Discriminating content of the change — a non-filterable node is rejected ONLY
when it is also a query operand (`isOperand`) — lives in
`nodeBad n = n.isOperand && !n.filterable` (model) ⇔ the added
`hasattr(expression,'resolve_expression') and …` conjunct (real). The pre-patch
guard was `not getattr(expression,'filterable',True)` alone;
`Solution_prepatch.lean` reproduces that (`result := (!n.filterable) || result`)
and **fails** `raised = anyBad nodes` (G-DIFF), because for a node with
`isOperand = false, filterable = false` the prepatch yields `true` while
`nodeBad` yields `false` — exactly the F2P scenario (a model instance `e2` with
`filterable=False` and no `resolve_expression`).

## B. No second site

`check_filterable` is the only changed function; the recursion over
`get_source_expressions()` is byte-identical before and after the patch. There
is a single independently-observable fixed behavior (a non-operand
non-filterable value must not raise), exercised by one `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the per-node
guard — is modeled **identically** (`nodeBad`, step A3), not hidden behind an
axiom. There are no consumed axioms and no deep-model references: the changed
function calls no opaque callee whose contract the proof must assume (the two
attribute reads are Python builtins refined to `Node` fields, A2).

## D. verify(Solution) ⇒ resolved

`checkFilterable` verifies only if its output equals the exact per-node
disjunction with the conjoined operand guard (A3, A4). By R (tree ↔ `List Node`,
attribute ↔ `Bool` field, raise ↔ `raised`) the verified predicate equals "the
patched `check_filterable` raises" on the tested inputs; by G-CONF the R/I
transliteration of `anyBad`/`nodeBad` agrees with `patch.diff`'s raise-or-not
behaviour on ≥10⁵ fuzzed operand trees. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The only trust point is refinement fidelity
(this doc + G-CONF); there is no axiom-soundness trust point (no axioms).
