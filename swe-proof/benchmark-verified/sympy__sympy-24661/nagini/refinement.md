# refinement.md — sympy__sympy-24661

The operation-by-operation correspondence between `model.py`'s implementation
(the `rewrite_comparison` impl region, with the pure `is_relational` / `rel_class_of`
mappings) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** if the proof uses the
axiom's `Ensures`; **A-reference** if a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change — `EvaluateFalseTransformer.visit_Compare` (new method)

Gold hunk (`sympy/parsing/sympy_parser.py`, added inside the class):
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
+            new_node = ast.Call(func=ast.Name(id=sympy_class, ctx=ast.Load()),
+                                args=[left, right],
+                                keywords=[ast.keyword(arg='evaluate',
+                                          value=ast.NameConstant(value=False, ...))],
+                                starargs=None, kwargs=None)
+            return new_node
+        return node
```

| # | model.py impl op (`rewrite_comparison`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `node: Compare` (`op`, `left`, `right`) | `node` (an `ast.Compare`) | R | `ast.Compare` ↔ `Compare`; `node.ops[0].__class__` ↔ `op` (int code), `node.left`↔`left`, `node.comparators[0]`↔`right` (mapping.md §2). |
| A2 | guard `if is_relational(node.op)` | `if node.ops[0].__class__ in self.relational_operators` | R | dict-membership over the six relational `ast` classes ↔ `is_relational(op)` over the six operator codes `{0..5}`. The dict is a frozen module-level constant; membership is faithfully the predicate (mapping.md §2 last row). |
| A3 | `sympy_class = rel_class_of(node.op)` | `sympy_class = self.relational_operators[node.ops[0].__class__]` | R | the dict lookup ↔ `rel_class_of`: each (key,value) pair `ast.Lt→'Lt'`, `ast.LtE→'Le'`, `ast.Gt→'Gt'`, `ast.GtE→'Ge'`, `ast.NotEq→'Ne'`, `ast.Eq→'Eq'` ↔ `OP_*→REL_*`. The SymPy class-name *string* is refined to the `int` constructor code (`str` carrier banned in Nagini). |
| A4 | `right = node.right`; `left = node.left` | `right = self.visit(node.comparators[0])`; `left = self.visit(node.left)` | I + R | the recursive `self.visit(...)` is the identity on the operands the F2P test exercises (integer-literal operands have no dedicated visitor in `EvaluateFalseTransformer`, so `generic_visit` returns them unchanged — see row C). The model carries operand *identity and left/right order*, which is exactly what the spec pins **unconditionally on both branches** (`Result().left is node.left and Result().right is node.right`): a produced call carries the operands in source order, and the unchanged non-relational node keeps its own operands (the real code returns `node` itself, operands included). |
| A5 | `Node(True, sympy_class, False, left, right, node.op)`; `return new_node` | `new_node = ast.Call(func=ast.Name(id=sympy_class), args=[left, right], keywords=[evaluate=False]); return new_node` | R | the produced `ast.Call` ↔ `Node` with `is_call==True`: `result.func.id` (constructor name) ↔ `rel_class`; `args==[left,right]` ↔ `left`/`right` in order; the `evaluate=False` keyword ↔ `evaluate==False` (mapping.md §2). |
| A6 | `return Node(False, REL_NONE, False, ...)` | `return node` (the unchanged `ast.Compare`) | R | the non-relational branch returns the comparison node unchanged ↔ `Node` with `is_call==False`, `rel_class==REL_NONE`, and — pinned unconditionally by the spec — `op`, `left`, `right` all preserved (`Result().op == node.op`, `Result().left is node.left`, `Result().right is node.right`): "unchanged" means operator AND operands intact, exactly `return node`. (When the rewritten tree compiles, an unchanged `ast.Compare` collapses to a `bool` — the pre-patch behaviour for *all* operators, and post-patch only for non-relational ones.) |

The discriminating content of the change — converting a comparison into a
**symbolic-comparison call with `evaluate=False`** rather than leaving a bare
comparison that collapses to a truth value — lives in the postconditions
`Result().is_call == is_relational(node.op)` and `Result().evaluate == False`
(the produced symbolic-comparison call never evaluates). The pre-patch
code has no `visit_Compare`, so the comparison node is returned unchanged for
every operator; `model_prepatch.py` reproduces that (`return Node(False, …)`
unconditionally) and **fails** the postcondition
`Result().is_call == is_relational(node.op)` on the relational branch — exactly
the spec sensing the change (G-DIFF). The operator→constructor bijection
(`rel_class_of`) is pinned per-operator, so an impl that converts but with the
wrong constructor (e.g. `Lt`→`Gt`) also fails.

## B. No consumed axiom; the rewrite is the A-reference

There is **no `@ContractOnly` axiom** in this bundle. The comparison rewrite is
a pure, fully-expressible AST transformation; it invokes no unchanged external
callee whose behaviour the proof assumes. The model's operator→constructor
correspondence and produced-node shape ARE the deep model of `visit_Compare`,
and are validated **== the real callee** out-of-band:

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `rel_class_of` / `is_relational` + the produced `Node` shape | the real `relational_operators` table + the `ast.Call` `visit_Compare` builds | A-reference | `axiom_check.py` (G-AX) runs the REAL post-patch `EvaluateFalseTransformer.visit_Compare`: it asserts the real `relational_operators` dict has exactly the six keys mapping to the six constructor names of `rel_class_of`, that each of `1<2,1<=2,1>2,1>=2,1!=2,1==2` rewrites to an `ast.Call` to the matching SymPy constructor with `evaluate=False` in left/right order, and that non-relational comparisons (`in`/`is`/…) are returned unchanged. NOT a consumed axiom — the proof verifies standalone over the model classes. |

## C. The recursive `self.visit` operand calls (row A4 detail)

`visit_Compare` calls `self.visit(node.left)` / `self.visit(node.comparators[0])`
on the operands. `EvaluateFalseTransformer` only overrides `visit_BinOp`,
`visit_Call`, and `visit_Compare`; for any other node type (e.g. an integer
literal `ast.Constant`/`ast.Num`, the operands in the F2P test
`test_issue_24288`) `ast.NodeTransformer.generic_visit` returns the node
unchanged. So on the tested inputs `self.visit(operand)` **is** the identity,
which the model encodes by passing `node.left`/`node.right` through unchanged
and pinning `Result().left is node.left and Result().right is node.right`.
(Were an operand itself a comparison or a binop, `visit` would recurse — but
the property "the comparison becomes a symbolic-comparison call of the right
constructor with `evaluate=False`" is independent of that recursion, which the
opaque `Expr` carrier captures: the recursion is *applied to the operands*, it
does not change *this* node's conversion.) This is the only step that is not a
pure R-refinement; it is an **I** (identity) on the tested domain, justified by
the transformer's visitor set. No kind-3 step.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The operation that genuinely changed
— turning a comparison into a non-evaluating symbolic-comparison call under the
fixed operator→constructor bijection — is modelled **deeply** (the spelled-out
`is_relational`/`rel_class_of` mappings and the verified branch in
`rewrite_comparison`), not hidden behind an axiom about the function under change.
There is no consumed axiom; the rewrite's correspondence to the real callee is
the A-reference that G-AX validates.

## E. verify(model) ⇒ resolved

`rewrite_comparison` verifies only if, for each relational operator, it produces a
symbolic-comparison call (`is_call`) with the constructor `rel_class_of(op)` and
`evaluate == False` applied to the two operands in order (A2–A5), and leaves
non-relational comparisons unchanged (A6). By R (the `ast.Compare`/`ast.Call` ↔
`Compare`/`Node` refinement, the dict ↔ `rel_class_of`/`is_relational`, the
class-name string ↔ constructor code) and I (the operand `self.visit` identity,
row C) the verified rewrite equals the gold `visit_Compare` on the tested
inputs; G-AX confirms the operator→constructor bijection and produced-node shape
equal the real callee (A-reference, B1). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement, and the gold
patch makes `parse_expr('1 < 2', evaluate=False) == Lt(1, 2, evaluate=False)`
(and the other five) — the F2P test `test_issue_24288` — pass (G-RESOLVE). The
single trust point is refinement fidelity (this document, G-EQ); there is no
axiom-soundness trust point because no axiom is consumed (the A-reference is
machine-checked by G-AX).
