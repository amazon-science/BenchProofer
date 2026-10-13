# refinement.md — sympy__sympy-24661

Operation-by-operation correspondence between `implementation_transformRelational`
(Solution.lean impl region) and `patch.diff` (the new `visit_Compare` method of
`EvaluateFalseTransformer`). Tags: **R** type refinement, **A-consumed** proof
uses an axiom, **A-reference** deep model validated == real callee, **I** identical
concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match relClassName op with \| some cls => … \| none => …` | `if node.ops[0].__class__ in self.relational_operators: … else: return node` | R |
| 2 | `let right' := transform right` | `right = self.visit(node.comparators[0])` | R |
| 3 | `let left' := transform left` | `left = self.visit(node.left)` | R |
| 3a | `transform (.app f args ef) = .app f (transformArgs args) (ef \|\| isNonEvaluatingFunc f)` | `visit_Call` @ 1189-1193: `new_node = self.generic_visit(node)` THEN `if node.func.id in self.functions: new_node.keywords.append(evaluate=False)` | R |
| 3b | `transformArgs (a :: rest) = transform a :: transformArgs rest` | `generic_visit`'s per-field list walk (`value = self.visit(value)` for each AST child) | R |
| 4 | `return AstNode.app cls [left', right'] true` | `new_node = ast.Call(func=ast.Name(id=sympy_class), args=[left, right], keywords=[ast.keyword(arg='evaluate', value=NameConstant(False))]); return new_node` | R |
| 5 | `\| none => return AstNode.cmp left op right` | `return node` (operator not in the table) | I |

Notes:

- **Every step is R or I — no A.** The comparison rewrite, including the recursive
  `self.visit` of each operand, is modeled DEEPLY (`transform` / `transformArgs` /
  the `AstNode` inductive); SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op. The `axioms` region is empty; **G-AX skips**.
- **Ops 3a-3b (the call arm of the dispatch)** R, and they are the reason the
  dispatch needs TWO legs rather than one. `self.visit` on an `ast.Call` reaches
  `visit_Call`, which is unchanged by the patch but is nonetheless CONSUMED by the
  postcondition, because the spec pins `transform left` / `transform right` and an
  operand may be a call. `visit_Call` does two things in sequence and both are
  modeled: (a) `generic_visit` recursively visits every child, so the call's
  ARGUMENTS are rewritten — `transformArgs`; then (b) a whole-node overlay
  APPENDS `evaluate=False` when the callee name is in the `functions` table @
  1112-1118 — `evalFalse || isNonEvaluatingFunc func`. Step (b) runs AFTER (a) and
  can only ADD the flag, never clear one, which is why the model disjoins rather
  than assigns. Modeling (a) without (b), or either without the other, predicts a
  node the real transformer does not build.
- **Op 1 (the operator-table lookup)** R: `node.ops[0].__class__ in
  self.relational_operators` / the dict value ↔ `relClassName op` (`some cls` /
  `none`); the `RelOp` ↔ ast-comparison-class bijection is in mapping.md.
- **Ops 2–3 (operand recursion)** R: `self.visit(child)` ↔ `transform child`. The
  Python method evaluates `right` BEFORE `left`; the impl mirrors that order
  (`right'` bound first) while building the args list `[left', right']` —
  matching `args=[left, right]`. The visitor's behaviour on the operands is
  modeled by `transform`, not assumed.
- **Op 4 (build the call)** R: the constructed `ast.Call` to the relational
  constructor with `evaluate=False` ↔ `AstNode.app cls [left', right'] true`
  (`evalFalse = true` ↔ the `evaluate=False` keyword). The constructor name `cls`
  is the table value; `func=ast.Name(id=sympy_class)` ↔ the `func` field.
- **Op 5 (fallthrough)** I: an unrecognised comparison operator returns the node
  unchanged — `return node` ↔ `return AstNode.cmp left op right`.
- The **fix itself** is the *presence* of this handler. The pre-patch impl
  (`Solution_prepatch.lean`) has no comparison handler and returns the comparison
  node unchanged for EVERY operator (`return AstNode.cmp left op right`),
  reproducing the defect: a recognised relational operator is not rebuilt as an
  unevaluated relational call. G-DIFF observes the recognised-operator clause: the
  spec demands `app cls …`, the buggy impl yields `cmp …`, so its `correct_*` is
  unprovable.
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl (plus the modeled `transform`/`transformArgs`) is diffed against the
  REAL imported `EvaluateFalseTransformer.visit_Compare` — driven on genuine
  `ast.Compare` nodes via the mapping.md §2 bijection, NOT against a replica —
  over ≥1e5 fuzzed `AstNode`s whose operands include calls on both sides of the
  `functions` table. Legs 3a/3b are exactly what a replica-based oracle could not
  refute, since a replica sharing the model's `transform` agrees with it by
  construction; see mapping.md's G-CONF section.
