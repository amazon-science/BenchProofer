# refinement.md — django__django-13012

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`groupingColumns` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — none here), or **I**
(identical concrete op). The R/I legs are mechanically refuted by **G-CONF**
(`conformance_check.py`, §4.1); the narrative is audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The grouping-columns site — `ExpressionWrapper.get_group_by_cols` (added)

Gold hunk (`django/db/models/expressions.py`, added inside class
`ExpressionWrapper`):
```
+ def get_group_by_cols(self, alias=None):
+     return self.expression.get_group_by_cols(alias=alias)
```

| # | Solution.lean impl op (`groupingColumns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `selfCol : GroupCol` | `self` (the wrapping expression instance) | R | an expression's grouping identity ↔ `GroupCol` (mapping.md §2). Used by the model only to state what the result must NOT be (its own identity), never returned. |
| A2 | free input `innerCols : List GroupCol` | `self.expression.get_group_by_cols(alias=alias)` — the wrapped inner expression's columns for the **requested** context | R + directive-7 free input | the delegated unchanged callee's result (mapping.md §3). `list` ↔ `List`, expression object ↔ `GroupCol` by identity. Owed no contract; the spec holds for every value of it. G-CONF derives it identically. |
| A3 | free inputs `innerHasAggregate`, `innerColsDefaultContext` | `self.contains_aggregate`, `self.expression.get_group_by_cols()` (no alias) | R + directive-7 free input | the observations the pre-patch inherited rule branched on; present so the prepatch skeleton is expressible while the spec stays byte-identical (G-DIFF). The gold impl ignores them. |
| A4 | `result := innerCols`; `return result` | `return self.expression.get_group_by_cols(alias=alias)` | I | identical concrete op: the wrapping expression returns exactly the wrapped expression's grouping columns for the same context. Transliterated and identity-compared by G-CONF. |

Discriminating content of the change — a transparent wrapping expression must
contribute its inner expression's columns for the requested context
(`out = innerCols`), **not** stand in for them with its own identity (the base
`[self]` rule for a non-aggregating expression) and **not** re-query its sources
with the context dropped (the base aggregate rule). `Solution_prepatch.lean`
reproduces the inherited base rule (`if innerHasAggregate then
innerColsDefaultContext else [selfCol]`) and **fails** `out = innerCols`
(G-DIFF): for a non-aggregating constant inner, the base returns `[selfCol]` (a
non-empty singleton) where the spec demands `innerCols` (empty for a constant);
for an aggregating inner it returns the context-dropped column list.

## B. No axioms, no deep-model references

The only callee the changed function touches — the wrapped inner expression's own
`get_group_by_cols` — is UNCHANGED by the patch and merely *forwarded to*. It is
modeled as the free input `innerCols` (directive 7): the spec is owed no contract
about it and holds for every value, so there is nothing to axiomatize and no G-AX
check. The pinned behaviour is a property of the **caller** (it forwards
faithfully), grounded structurally in the relation `out = innerCols` between the
result and the actual delegated input — not an ungrounded oracle (directive 8).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that changed — adding the transparent
delegation — is expressed directly (`out = innerCols`, step A4, an **I** op under
the `List`/identity refinement). Nothing is hidden behind an axiom about the
function under change.

## D. verify(Solution) ⇒ resolved

`groupingColumns` verifies only if its output equals the wrapped inner
expression's grouping columns for the requested context (`out = innerCols`, A4).
By R (`list ↔ List`, expression-object ↔ `GroupCol` by identity) the verified
operation equals `return self.expression.get_group_by_cols(alias=alias)` — the
gold hunk — on every input. By G-CONF the R/I transliteration of the model agrees
with `patch.diff`'s behaviour through the real patched method on ≥10⁵ inputs
(identity-compared). The two F2P tests assert exactly this: a wrapped constant
contributes `[]` (its inner `Value` contributes none) and a wrapped transform
contributes the inner transform's column — both are `out = innerCols`. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement, and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (G-AX n/a).
