# mapping.md — sympy__sympy-24661

## Symbol binding (file:line @ base_commit a36caf5c74fe654cedc488e8a8a05fad388f8406)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_transformRelational` / `problem_spec_transformRelational` / `correct_transformRelational` | the `EvaluateFalseTransformer` method that rewrites a comparison node (added by the patch) | `sympy/parsing/sympy_parser.py` — `class EvaluateFalseTransformer` @ 1102; the new method body @ 1122-1144 (post-patch) |
| `transform` / `transformArgs` (pure helpers) | the transformer's recursive `self.visit(...)` dispatch applied to a sub-node, and the argument walk `generic_visit` performs | `sympy/parsing/sympy_parser.py:1095` (`EvaluateFalseTransformer().visit(node)`); the per-node `visit_*` dispatch; `visit_Call` @ 1189-1193 (UNCHANGED by the patch) and `ast.NodeTransformer.generic_visit` (stdlib) |
| `nonEvaluatingFuncs` / `isNonEvaluatingFunc` (pure helpers) | the `functions` tuple and the `node.func.id in self.functions` test in `visit_Call` | `sympy/parsing/sympy_parser.py` — `functions` @ 1112-1118, membership test @ 1191 (both UNCHANGED by the patch) |
| `relClassName` (pure helper) | the `relational_operators` dict (`{ast.NotEq:'Ne', ast.Lt:'Lt', ast.LtE:'Le', ast.Gt:'Gt', ast.GtE:'Ge', ast.Eq:'Eq'}`) | added @ 1122-1129 (post-patch) |
| `AstNode` / `RelOp` (pure helpers) | the `ast` node tree the transformer walks (`ast.Compare`, `ast.Call`, `ast.Name`, constant) and the comparison-operator class | the `ast` module nodes consumed by the transformer |

## What the function does (base_commit vs patch)

`evaluateFalse(s)` parses a string with `ast.parse`, then runs
`EvaluateFalseTransformer().visit(node)` to rewrite operators into their SymPy
equivalents carrying `evaluate=False`, so that `parse_expr(..., evaluate=False)`
builds an UNEVALUATED expression.

At `base_commit` the transformer has `visit_BinOp` (arithmetic) and `visit_Call`
(named functions) but **no handler for comparison nodes**. A comparison such as
`1 < 2` is therefore left as an `ast.Compare` node, which Python/SymPy then
evaluates to a truth value — so `parse_expr('1 < 2', evaluate=False)` returns
`True` instead of the unevaluated relational `Lt(1, 2, evaluate=False)`.

The patch adds a `relational_operators` table and a `visit_Compare` method:

```python
relational_operators = {ast.NotEq:'Ne', ast.Lt:'Lt', ast.LtE:'Le',
                        ast.Gt:'Gt', ast.GtE:'Ge', ast.Eq:'Eq'}
def visit_Compare(self, node):
    if node.ops[0].__class__ in self.relational_operators:
        sympy_class = self.relational_operators[node.ops[0].__class__]
        right = self.visit(node.comparators[0])
        left  = self.visit(node.left)
        new_node = ast.Call(func=ast.Name(id=sympy_class, ctx=ast.Load()),
                            args=[left, right],
                            keywords=[ast.keyword(arg='evaluate',
                                      value=ast.NameConstant(value=False, ctx=ast.Load()))],
                            starargs=None, kwargs=None)
        return new_node
    return node
```

So for the first comparison operator `node.ops[0]`:

- if it is one of the six relational operators, the node becomes a `Call` to the
  corresponding SymPy relational constructor on the (recursively transformed)
  left and right operands, with `evaluate=False`;
- otherwise the node is returned unchanged.

The FAIL_TO_PASS test `test_issue_24288` asserts, for each of the six operators on
two integer literals, that `parse_expr(text, evaluate=False)` equals
`Lt/Le/Gt/Ge/Ne/Eq(1, 2, evaluate=False)`.

## Lean modeling

- `RelOp` enumerates the comparison operator class: `lt le gt ge eq ne` (the six
  in the table) plus `other` for any operator NOT in the table (`is`, `in`, …),
  which is left unchanged.
- `relClassName : RelOp → Option String` is the table: `some "Lt"/"Le"/"Gt"/
  "Ge"/"Eq"/"Ne"` for the six, `none` for `other`.
- `AstNode` is the fragment of the parsed tree the transformer touches:
  `const` (a numeric literal), `name` (an identifier), `app func args evalFalse`
  (a function-call node; `evalFalse` records whether the `evaluate=False` keyword
  is present), `cmp left op right` (a single comparison, i.e. `node.left`,
  `node.ops[0]`, `node.comparators[0]`).
- `transform : AstNode → AstNode` is the recursive transformer dispatch
  (`self.visit`), and `transformArgs` is the elementwise walk over a call's
  arguments. `self.visit` dispatches by node class (`ast.NodeVisitor.visit`:
  `getattr(self, 'visit_' + type(node).__name__, self.generic_visit)`), so the
  model has ONE LEG PER REACHABLE ARM, enumerated as STEPS:
    1. `ast.Compare` → `visit_Compare` (the patched method): the relational rule
       (`.cmp` arm).
    2. `ast.Call` → `visit_Call` @ 1189-1193, which is TWO steps of its own and
       BOTH are modeled in the `.app` arm:
       (a) `new_node = self.generic_visit(node)` — the stdlib walk
           (`ast.NodeTransformer.generic_visit`) recursively `self.visit`s every
           child in every field, so a call's ARGUMENTS are themselves rewritten;
           this is `transformArgs args`.
       (b) `if isinstance(node.func, ast.Name) and node.func.id in
           self.functions: new_node.keywords.append(evaluate=False)` — a
           whole-node overlay applied AFTER (a) that consults the `functions`
           table @ 1112-1118; this is `evalFalse || isNonEvaluatingFunc func`.
           Note it APPENDS, never removes, so a flag already present survives —
           hence the disjunction rather than an assignment.
    3. `ast.Constant` / `ast.Name` → no `visit_*` method, so `generic_visit`
       runs and finds no AST-valued child to rewrite: the node is returned
       unchanged (`.const` / `.name` arms are the identity).
  `visit_BinOp`'s arithmetic denesting is not modeled because `AstNode` has no
  binary-operator constructor: an arithmetic operand is outside the modeled node
  fragment. Comparison operands in the modeled scope are atoms, calls, or nested
  comparisons, and each of those three has a leg above.
- `implementation_transformRelational` is the `Id.run do` skeleton of the new
  method: match the comparison, look the operator up in the table, and on a hit
  build the relational call from the transformed operands (right then left, the
  method's order), else return the node.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| comparison-operator class `node.ops[0].__class__` | `RelOp` | `ast.Lt↔.lt`, `ast.LtE↔.le`, `ast.Gt↔.gt`, `ast.GtE↔.ge`, `ast.Eq↔.eq`, `ast.NotEq↔.ne`, anything else ↔ `.other` |
| `relational_operators` dict lookup | `relClassName` | `.lt→"Lt"`, `.le→"Le"`, `.gt→"Gt"`, `.ge→"Ge"`, `.eq→"Eq"`, `.ne→"Ne"`, `.other→none` |
| numeric literal node | `AstNode.const n` | value-as-`Int` |
| `ast.Name(id=s)` | `AstNode.name s` | identifier string |
| `ast.Call(func=Name(id=f), args, keywords=[evaluate=False?])` | `AstNode.app f args evalFalse` | `evalFalse = True` iff an `evaluate=False` keyword is present |
| `ast.Compare(left, ops=[op], comparators=[right])` | `AstNode.cmp left op right` | first operator / first comparator |
| `self.visit(child)` | `transform child` | recursive dispatch |
| `generic_visit(node)` over a call's `args` | `transformArgs args` | elementwise `transform` |
| `functions` tuple membership (`node.func.id in self.functions`) | `isNonEvaluatingFunc func` / `nonEvaluatingFuncs` | the 35 names, in file order |
| `new_node.keywords.append(evaluate=False)` (an APPEND, so an existing flag persists) | `evalFalse \|\| isNonEvaluatingFunc func` | boolean disjunction |

## Callee provenance + flag dependencies

- **No consumed callee axiom and no A-reference axiom.** The behavior the patch
  introduces — rewriting a comparison into an unevaluated relational call — is
  modeled DEEPLY and structurally over the comparison's components; SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled changed op. The recursive `self.visit`
  dispatch is modeled deeply as `transform`/`transformArgs`, not axiomatized, and
  that INCLUDES the unchanged `visit_Call` (+ stdlib `generic_visit`) the dispatch
  reaches on a call-shaped operand: it is modeled deeply rather than
  axiomatized, so it is not a consumed-callee axiom either. G-CONF validates the
  whole dispatch by driving the REAL imported `EvaluateFalseTransformer` (see
  below). The `axioms` region is therefore empty and **G-AX skips**.
- `ast.parse`, `ast.fix_missing_locations`, and the eventual `eval`/`sympify` of
  the rewritten tree are upstream/downstream of the modeled rewrite and unchanged
  by the patch; they are not modeled. The observable the patch changes is the
  shape of the rewritten node, which `transform`/`implementation_transformRelational`
  produce structurally.

## G-CONF fuzz seed

Pinned LCG seed: **24661** (see `conformance_check.py` `SEED`). Corpus: randomized
`AstNode`s with emphasis on the discriminating category — `cmp` nodes over every
`RelOp` (the six recognized operators and `other`), operands drawn from constants,
names, calls (callee drawn from BOTH sides of the `functions` table, arity 0-2,
flag possibly already set) and nested comparisons — plus hand-picked edge cases
mirroring the F2P literals (`1 < 2`, `1 <= 2`, `1 > 2`, `1 >= 2`, `1 != 2`,
`1 == 2`) and twelve cases that pin the call arm specifically.

**The oracle is the REAL callee, not a replica.** `conformance_check.py` imports
`EvaluateFalseTransformer` from the patched repo and calls its bound
`visit_Compare` on a genuine `ast.Compare` built from each fuzzed input, crossing
the boundary with the §2 bijection (`to_ast` / `from_ast`) in both directions. The
R/I shadow of `implementation_transformRelational` (plus the modeled
`transform`/`transformArgs`) is diffed against that over ≥1e5 inputs.

This replaced an earlier revision whose `oracle()` and `shadow()` both called the
SAME local `transform()` helper — a transliteration of the Lean model rather than
the repo. A shadow that shares the helper under suspicion cannot refute it, and
that revision reported `disagreements=0` on 120k inputs while the model's
`transform` was the identity on call nodes and the real dispatch was not. The
current script, run against a model with that identity arm restored, fails on the
first hand case, so the check is now load-bearing on this branch.
