# mapping.md — sympy__sympy-24661

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a36caf5c74fe654cedc488e8a8a05fad388f8406`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/parsing/sympy_parser.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rewrite_comparison(node)` | `EvaluateFalseTransformer.visit_Compare(self, node)` — added by the patch at `sympy/parsing/sympy_parser.py:1120` (within the class at line 1102) | the modeled changed function (rewrite of a comparison syntax node) |
| `Compare` (class) | an `ast.Compare` node: `node.ops[0]` (the single comparison operator), `node.left`, `node.comparators[0]` (right operand) | the comparison syntax node the rewrite receives |
| `Compare.op` (int code) | `node.ops[0].__class__` — one of `ast.Lt / ast.LtE / ast.Gt / ast.GtE / ast.NotEq / ast.Eq` (relational), or another comparison op class (`ast.In`, `ast.Is`, …) | the comparison operator |
| `Compare.left` / `Compare.right` | `node.left` / `node.comparators[0]` | the two operand sub-expressions |
| `Node` (class) | the value `visit_Compare` returns: either the new `ast.Call(func=ast.Name(id=sympy_class), args=[left, right], keywords=[evaluate=False])` (converted) or the original `node` (unchanged) | the rewritten node |
| `Node.is_call` | "the returned value is the new `ast.Call`" vs "the returned value is the original `ast.Compare`" | whether a symbolic-comparison call was produced |
| `Node.rel_class` (int code) | `sympy_class` — the value looked up in `relational_operators[node.ops[0].__class__]` (a SymPy relational class name string `'Lt'/'Le'/'Gt'/'Ge'/'Ne'/'Eq'`) | the symbolic-comparison constructor |
| `Node.evaluate` | the `evaluate` keyword value on the produced `ast.Call` | the non-evaluating flag |
| `Node.op` | for the unchanged case: the returned node's own operator (`node.ops[0].__class__` — the real code returns `node` itself, operator included). For the converted case: the operator the call was built from (bookkeeping — the produced `ast.Call` carries the operator only implicitly, via the constructor name; the model records it explicitly and pins it to the input so the field is not an unconstrained channel) | the operator code carried by the rewritten node |
| `is_relational(op)` | `node.ops[0].__class__ in self.relational_operators` | the conversion guard |
| `rel_class_of(op)` | `self.relational_operators[node.ops[0].__class__]` (the lookup), with `REL_NONE` for the not-in-table case | the operator→constructor correspondence |

The patch adds the class attribute `relational_operators` (a dict mapping six
`ast` comparison-operator classes to SymPy relational class-name strings) and
the method `visit_Compare`. There is no pre-existing `visit_Compare`; before the
patch a comparison node has no dedicated visitor, so `ast.NodeTransformer`'s
default leaves it a bare `ast.Compare` (which compiles to a concrete Python
comparison and collapses to a `bool`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `ast.Compare` node | `Compare` class (`op`, `left`, `right`) | `node.ops[0].__class__` ↔ `op` (int code: `ast.Lt`↔`OP_LT=0`, `ast.LtE`↔`OP_LE=1`, `ast.Gt`↔`OP_GT=2`, `ast.GtE`↔`OP_GE=3`, `ast.NotEq`↔`OP_NE=4`, `ast.Eq`↔`OP_EQ=5`, any other comparison-op class ↔ code ≥ 6); `node.left` ↔ `left`; `node.comparators[0]` ↔ `right` |
| operand sub-expression (`node.left` / `node.comparators[0]`) | `Expr` opaque carrier | the rewrite recurses into each operand (`self.visit(...)`) but the property under specification depends only on operand *identity/order*, not internal structure, so the operand is modelled as an opaque node with a single dummy field. `self.visit(left)`/`self.visit(right)` ↔ identity on the `Expr` (see refinement.md row C). |
| the produced `ast.Call` / the unchanged `ast.Compare` | `Node` class | `isinstance(result, ast.Call)` ↔ `is_call == True`; `result.func.id` (SymPy class name string) ↔ `rel_class` (int code `'Lt'`↔`REL_LT=100`, `'Le'`↔`REL_LE=101`, `'Gt'`↔`REL_GT=102`, `'Ge'`↔`REL_GE=103`, `'Ne'`↔`REL_NE=104`, `'Eq'`↔`REL_EQ=105`); `result.args == [left, right]` ↔ `Node.left is left and Node.right is right`; the `evaluate=False` keyword ↔ `Node.evaluate == False`; the unchanged-comparison case ↔ `is_call == False`, `REL_NONE = -1` |
| dict membership / lookup `relational_operators[cls]` | `is_relational(op)` guard + `rel_class_of(op)` pure function | the dict's six (key, value) pairs are spelled out as the bijection in `rel_class_of`; membership is `is_relational`. The dict is a fixed module-level constant; modelling it as the two pure functions is a faithful R-refinement (the dict is never mutated). |

`str` (the SymPy class-name string) and the rich `ast` node objects are
banned/unsupported carriers in Nagini; the constructor identity is carried by
an `int` code and the node shape by the small `Node`/`Compare`/`Expr` classes.

## 3. Callee provenance

**No `@ContractOnly` axiom is consumed.** The comparison rewrite is a pure,
fully-expressible AST transformation: it reads `node.ops[0].__class__`, looks up
a fixed dict, recurses into the two operands, and constructs a new `ast.Call`.
It calls no unchanged external library function whose behaviour the proof must
assume. (`self.visit(...)` is recursion within the same transformer; on the
F2P inputs the operands are integer literals that `visit` leaves unchanged —
see refinement.md row C.)

**A-reference (deep model validated by G-AX, not consumed):** the model's
operator→constructor correspondence (`rel_class_of` / `is_relational`) and the
shape of the produced node ARE the deep model of `visit_Compare`. `axiom_check.py`
validates this deep model against the REAL post-patch
`EvaluateFalseTransformer.visit_Compare`:

  * `EvaluateFalseTransformer.relational_operators` (the real dict) has exactly
    the six keys `ast.NotEq/Lt/LtE/Gt/GtE/Eq` mapping to `'Ne'/'Lt'/'Le'/'Gt'/
    'Ge'/'Eq'`, matching `rel_class_of`;
  * running the real `visit_Compare` on `1 < 2`, `1 <= 2`, `1 > 2`, `1 >= 2`,
    `1 != 2`, `1 == 2` yields an `ast.Call` to the matching SymPy constructor
    with `evaluate=False` and operands in left/right order;
  * running it on non-relational comparisons (`in`, `not in`, `is`, `is not`)
    returns the node unchanged.

Provenance: the patch hunk itself (`sympy/parsing/sympy_parser.py`, the added
`relational_operators` table + `visit_Compare`), and the SymPy relational
constructors `Lt, Le, Gt, Ge, Ne, Eq` (`sympy/core/relational.py`), which the
generated `ast.Call(func=Name('Lt'), …, evaluate=False)` invokes when the
rewritten tree is compiled and evaluated in the parser's namespace. The
end-to-end behaviour (`parse_expr('1 < 2', evaluate=False) == Lt(1, 2,
evaluate=False)`) is exactly the F2P test `test_issue_24288`.
