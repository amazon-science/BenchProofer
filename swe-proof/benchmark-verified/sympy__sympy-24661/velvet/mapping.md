# mapping.md — sympy__sympy-24661

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a36caf5c74fe654cedc488e8a8a05fad388f8406`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each callee.

Repo file under change: `sympy/parsing/sympy_parser.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rewriteComparison (visit) (k) (l) (r)` | `EvaluateFalseTransformer.visit_Compare(self, node)` — `sympy/parsing/sympy_parser.py` (added by gold patch inside `class EvaluateFalseTransformer`, body line 1102) | the modeled changed function: the node-transformer clause for a comparison expression |
| `visit : Node → Node` *(free input)* | `EvaluateFalseTransformer.visit` — the inherited `ast.NodeTransformer` dispatcher (`sympy/parsing/sympy_parser.py:1137`/`1189` for its sibling clauses) applied to an operand sub-expression | unchanged recursive operand rewrite; abstracted as a free input (mapping.md §3) |
| `CompareKind` | the class of `node.ops[0]` — `ast.Lt`/`ast.LtE`/`ast.Gt`/`ast.GtE`/`ast.Eq`/`ast.NotEq` and any other comparison operator | the comparison operator that selects the relation |
| `RelKind` | the SymPy relational class name the patch's `relational_operators` dict maps to — `'Lt'`,`'Le'`,`'Gt'`,`'Ge'`,`'Eq'`,`'Ne'` | the symbolic-relation constructor produced |
| `relOf : CompareKind → Option RelKind` | the `relational_operators` dict lookup `node.ops[0].__class__ in self.relational_operators` + its value | maps a supported comparison operator to its relation class; `none` ⇔ operator absent from the dict |
| `Node.relation rk false l r` | the produced `ast.Call(func=Name(id=sympy_class), args=[left,right], keywords=[keyword('evaluate', NameConstant(False))])` | a relation constructor applied to the two operands, with `evaluate=False` ⇒ held unevaluated (`built = false`) |
| `Node.comparison k l r` | the original `ast.Compare` node, returned unchanged (the trailing `return node`) | a comparison expression preserved as-is |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the class of `node.ops[0]` (the comparison operator) | `CompareKind` | `ast.Lt ↔ .lt`, `ast.LtE ↔ .le`, `ast.Gt ↔ .gt`, `ast.GtE ↔ .ge`, `ast.Eq ↔ .eq`, `ast.NotEq ↔ .ne`; any other comparison operator class (`ast.Is`, `ast.In`, …) ↔ `.other` |
| the SymPy relational class name string (`'Lt'`…`'Ne'`) | `RelKind` | `'Lt' ↔ .Lt`, `'Le' ↔ .Le`, `'Gt' ↔ .Gt`, `'Ge' ↔ .Ge`, `'Eq' ↔ .Eq`, `'Ne' ↔ .Ne` |
| an AST expression node | `Node` | an operand sub-expression ↔ `.leaf tag` (opaque, tagged so distinct operands stay distinct); the input `ast.Compare(left, [op], [right])` ↔ `.comparison k l r`; the produced `ast.Call(Name(rel), [l,r], keywords=[evaluate=False])` ↔ `.relation rk false l r` |
| `evaluate=False` keyword on the produced `Call` | the `built : Bool` flag fixed to `false` | the relation is constructed with `evaluate=False`, so SymPy holds it as a symbolic `Rel` object instead of evaluating it to a `BooleanAtom`/truth value. `built = false` ⇔ `evaluate=False` present |
| `self.visit(node.comparators[0])` / `self.visit(node.left)` | application of the free input `visit : Node → Node` | the recursive rewrite of an operand; unchanged behaviour, abstracted (mapping.md §3) |

Only the **first** comparison operator (`node.ops[0]`) is consulted — both the
gold patch and this model dispatch on the single leading operator (chained
comparisons such as `a < b < c` use `ops[0]` exactly as the patch does).

## 3. Callee provenance — `visit` (UNCHANGED, free input; no axiom, no G-AX)

`visit` models `EvaluateFalseTransformer.visit`, the recursive node dispatcher
inherited from `ast.NodeTransformer`. It is **not changed** by the gold patch:
the patch's new clause calls `self.visit(node.comparators[0])` and
`self.visit(node.left)` exactly as the pre-existing `visit_BinOp` clause does.
The spec asserts **nothing** about `visit` — `rewriteCompare`/the postconditions
hold for **every** `visit : Node → Node`, so the relation `out = .relation rk
false (visit l) (visit r)` is universally quantified over the operand rewrite.
There is therefore no relied-on property to check against the real callee, and
**no axiom** in the bundle (G-AX skips, like django__django-11149 /
astropy__astropy-13236).

The operand rewrite is held abstract for soundness: pinning it to a concrete
function would over-claim about an unchanged callee (directive 7). What the
patch *changes* — that a supported comparison becomes the matching **unevaluated
relation** instead of being left to evaluate to a truth value — is modeled
**deeply** by `rewriteCompare`/`relOf` (the `pure` region), not behind an axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24661`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `relOf`/`rewriteCompare` to Python and leaves the operand rewrite
as the free input (an opaque tagged operand — A-tagged-style free callee, not
exercised numerically). The oracle is the gold-patched `visit_Compare`'s
node-shape decision (which relation class + the `evaluate=False` keyword vs the
preserved `Compare`), transliterated verbatim; both are differential-tested over
the full finite comparison-operator space plus seeded fuzz.
