# refinement.md — sphinx-doc__sphinx-8265

Maps every op of the two `implementation_*` skeletons to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

The R/I legs are mechanically refuted by G-CONF; there are no A legs, so G-AX is
a skip stub.

## implementation_tupleDisplay ↔ patch.diff `visit_Tuple` (ast.py:174-178)

Post-patch Python:
```python
def visit_Tuple(self, node):
    if node.elts:
        return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
    else:
        return "()"
```

| Lean op | Python op | tag | note |
|---|---|---|---|
| `elts : List (List Char)` param | `[self.visit(e) for e in node.elts]` | R | Python `str` per-code-point ↔ Lean `List Char`; the element renderings are the modeled input (recursion not modeled — its results ARE `elts`). |
| `if elts ≠ []` | `if node.elts:` | I | non-empty test (`bool(node.elts)`). |
| `['('] ++ List.intercalate [',', ' '] elts ++ [')']` | `"(" + ", ".join(...) + ")"` | R | `", ".join` ↔ `List.intercalate [',', ' ']`; string concat ↔ `++`; the `'('`/`')'` wrap is the changed grouping. |
| `return ['(', ')']` | `return "()"` | I | empty-tuple literal. |

Every op is R or I. The whole result is a function of `elts` alone — no callee.

## implementation_subscription ↔ patch.diff `visit_Subscript` (ast.py:168-169)

Post-patch Python:
```python
def visit_Subscript(self, node):
    def is_simple_tuple(value): ...
    if is_simple_tuple(node.slice):
        elts = ", ".join(self.visit(e) for e in node.slice.elts)
        return "%s[%s]" % (self.visit(node.value), elts)
    elif isinstance(node.slice, ast.Index) and is_simple_tuple(node.slice.value):
        elts = ", ".join(self.visit(e) for e in node.slice.value.elts)
        return "%s[%s]" % (self.visit(node.value), elts)
    else:
        return "%s[%s]" % (self.visit(node.value), self.visit(node.slice))
```

| Lean op | Python op | tag | note |
|---|---|---|---|
| `valueStr : List Char` param | `self.visit(node.value)` | R | already-rendered value text; recursion not modeled — its result IS `valueStr`. |
| `idx : IndexForm` param | the `is_simple_tuple(node.slice)` / `ast.Index`-wrapped / else dispatch | R | `IndexForm.elementTuple elts` ↔ a simple-tuple slice (carries `[self.visit(e) for e …]`); `IndexForm.plain rendered` ↔ any other slice (carries `self.visit(node.slice)`). The py3.8 / py<3.8 (`ast.Index`) branches collapse to the same `elementTuple` case. |
| `match idx with .elementTuple elts =>` | `if is_simple_tuple(...) [elif ast.Index...]:` | I | the simple-tuple branch selection. |
| `let inner := List.intercalate [',', ' '] elts` | `elts = ", ".join(self.visit(e) for e in node.slice.elts)` | R | `", ".join` ↔ `List.intercalate [',', ' ']`. The CHANGED op: components listed directly, NOT through the parenthesizing tuple display. |
| `valueStr ++ ['['] ++ inner ++ [']']` | `"%s[%s]" % (self.visit(node.value), elts)` | R/I | `"%s[%s]" % (v, s)` ↔ `v ++ '[' ++ s ++ ']'`. |
| `match idx with .plain rendered =>` | `else:` | I | fallback branch. |
| `valueStr ++ ['['] ++ rendered ++ [']']` | `"%s[%s]" % (self.visit(node.value), self.visit(node.slice))` | R/I | same template; `rendered` = `self.visit(node.slice)`. |

Every op is R or I. No callee contract is consumed; `is_simple_tuple` is an
in-function helper whose decision is captured by the `IndexForm` constructor
chosen, not axiomatized.

## Prepatch correspondence (G-DIFF)
- `Solution_prepatch.lean` — pre-patch `visit_Tuple`: non-empty returns
  `", ".join(...)` with NO surrounding parens (`return List.intercalate [',', ' '] elts`).
  On `(1,2,3)` it yields `1, 2, 3` ≠ `(1, 2, 3)`, violating `problem_spec_tupleDisplay`
  on the non-empty branch. This is the FAIL_TO_PASS bug.
- `Solution_prepatch_2.lean` — pre-patch `visit_Subscript`: a tuple index is
  rendered through the (now-parenthesizing) tuple display, so `inner` becomes
  `"(" + join + ")"`. On `Tuple[int, int]` it yields `Tuple[(int, int)]`
  ≠ `Tuple[int, int]`, violating `problem_spec_subscription` on the
  `elementTuple` branch — the companion regression the `visit_Subscript` change
  prevents (PASS_TO_PASS `Tuple[int, int]`).
