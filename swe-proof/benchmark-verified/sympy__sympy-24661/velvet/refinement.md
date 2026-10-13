# refinement.md — sympy__sympy-24661

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `rewriteComparison` `do` block, plus the deep `rewriteCompare`/`relOf`
models in the `pure` region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** /
**A-reference** (none in this bundle), or **I** (identical concrete op). EVERY
step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The new comparison clause — `EvaluateFalseTransformer.visit_Compare`

Gold hunk (added method + its operator dict):
```
+    relational_operators = {
+        ast.NotEq: 'Ne', ast.Lt: 'Lt', ast.LtE: 'Le',
+        ast.Gt: 'Gt', ast.GtE: 'Ge', ast.Eq: 'Eq'
+    }
+    def visit_Compare(self, node):
+        if node.ops[0].__class__ in self.relational_operators:
+            sympy_class = self.relational_operators[node.ops[0].__class__]
+            right = self.visit(node.comparators[0])
+            left = self.visit(node.left)
+            new_node = ast.Call(
+                func=ast.Name(id=sympy_class, ctx=ast.Load()),
+                args=[left, right],
+                keywords=[ast.keyword(arg='evaluate', value=ast.NameConstant(value=False, ...))],
+                ...)
+            return new_node
+        return node
```

| # | Solution.lean impl op (`rewriteComparison` / `rewriteCompare` / `relOf`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `k : CompareKind` | `node.ops[0].__class__` | R | the leading comparison-operator class ↔ `CompareKind` (mapping.md §2). Only `ops[0]` is consulted, exactly as the patch. |
| A2 | param `visit : Node → Node` applied to `l`, `r` | `self.visit(node.left)`, `self.visit(node.comparators[0])` | R | the unchanged recursive operand rewrite ↔ a free total `Node → Node` (mapping.md §3); the spec relies on no property of it. |
| A3 | params `l`, `r : Node` | `node.left`, `node.comparators[0]` (pre-rewrite operands) | R | operand sub-expressions ↔ `Node` (mapping.md §2). |
| A4 | `relOf k` (the `Option RelKind` lookup) | `node.ops[0].__class__ in self.relational_operators` and the dict value `sympy_class` | I | `relOf` IS the membership test + class-name lookup, modeled deeply (the dict has exactly the six supported keys); `none` ⇔ operator absent. |
| A5 | `some rk ⇒ Node.relation rk false (visit l) (visit r)` | the `ast.Call(Name(sympy_class), [left, right], keywords=[evaluate=False])` constructor | I + R | a supported comparison becomes the matching relation class applied to the two rewritten operands; the `evaluate=False` keyword ↔ `built = false` (R, mapping.md §2). Modeled deeply — no axiom about the relation constructor. |
| A6 | `none ⇒ Node.comparison k l r` | the trailing `return node` (the unmodified `ast.Compare`) | I | an unsupported comparison kind is returned exactly as received. |

## B. The discriminating content — what the spec senses

The bug: pre-patch, `EvaluateFalseTransformer` had **no** `visit_Compare` clause,
so a parsed comparison expression (`1 < 2`, `1 == 2`, …) was left as an ordinary
`ast.Compare` node. With `evaluate=False` requested, the comparison is still
*evaluated* downstream — `parse_expr('1 < 2', evaluate=False)` returns the
truth value `True` instead of the held relation `Lt(1, 2, evaluate=False)`.

Post-patch, a supported comparison is rebuilt as the matching SymPy relational
constructor (`Lt`/`Le`/`Gt`/`Ge`/`Eq`/`Ne`) applied to the rewritten operands
with `evaluate=False`, so the result survives as a symbolic relation.

The frozen spec pins, for each supported `k`, `out = .relation <Rel> false
(visit l) (visit r)` (the matching class AND the unevaluated flag).
`Solution_prepatch.lean` reproduces the pre-patch skeleton (the comparison falls
through unchanged: `out = .comparison k l r`) and **fails** verification on
exactly those clauses — confirmed unsolved goals at `ensures_3..ensures_8` (the
six `k = … → out = .relation …`) and `ensures_9` (`out = rewriteCompare …`), for
each supported operator. The states diverge precisely on the supported
comparison operators the F2P `test_issue_24288` exercises (`1<2`, `1<=2`, `1>2`,
`1>=2`, `1!=2`, `1==2`). An unsupported comparison kind (`.other`) verifies in
both (the patch's `return node` is behaviour-preserving there).

This is one independently-fixed behaviour (relationalize a comparison under
`evaluate=False`) observed across the six operator variants sharing the
identical corrected decision; a single `Solution_prepatch.lean` carries all six
failing clauses against the byte-identical frozen spec (G-DIFF requires
`same_spec`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — turning a supported
comparison into the matching **unevaluated** relation constructor — is modeled
**deeply** (the `relOf`/`rewriteCompare` dispatch + the `built = false` flag,
A4/A5), not hidden behind an axiom about a function under change. There are **no
consumed axioms and no A-references**: the only callee, `visit` (the recursive
operand rewrite), is UNCHANGED by the patch and is abstracted as a free input
with no relied-on property (mapping.md §3), so nothing requires G-AX validation.

## D. verify(Solution) ⇒ resolved

`rewriteComparison` verifies only if its output equals the exact modeled
decision: for each supported operator, the matching relation constructor applied
to the rewritten operands and held unevaluated (`built = false`, A5), and the
original comparison preserved for an unsupported operator (A6). By R (the
operator-class / relation-name / node / `evaluate=False`↔`built` bijections,
mapping.md §2) the verified rewrite equals the gold-patched `visit_Compare`'s
returned node on every comparison, and by G-CONF the R/I transliteration of
`relOf`/`rewriteCompare` agrees with the patched node-shape decision on the full
finite operator space + fuzz (seed 24661, 0 disagreements). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (G-AX skips).
