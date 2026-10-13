# refinement.md — sphinx-doc__sphinx-8265

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `renderGroup` and `renderIndex` `do` blocks, plus the deep `render` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == the real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

This bundle has **no A-tagged steps**: there are no axioms and no A-references
(mapping.md §3). Every step is R or I. The R/I legs are mechanically refuted by
**G-CONF** (`conformance_check.py`); the narrative is audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The tuple/group site — `visit_Tuple` (`sphinx/pycode/ast.py:171`)

Gold hunk:
```
  def visit_Tuple(self, node: ast.Tuple) -> str:
      if node.elts:
-         return ", ".join(self.visit(e) for e in node.elts)
+         return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
      else:
          return "()"
```

| # | Solution.lean impl op (`renderGroup`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elts : List Expr` | `node.elts` of an `ast.Tuple` | R | `ast.Tuple` element list ↔ `List Expr` (mapping.md §2). |
| A2 | `if elts.isEmpty then "()".toList` | `if node.elts: … else: return "()"` | I | empty-list test ↔ Python list falsiness; empty case emits the literal `()` unchanged (the `else` arm is untouched by the patch). |
| A3 | `else "(".toList ++ joinComma (elts.map render) ++ ")".toList` | `return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"` | R + I | the new wrapping in surrounding parentheses. `", ".join(self.visit(e) …)` ↔ `joinComma (elts.map render)` (R: str↔List Char, the join); the `"(" + … + ")"` wrapping is the I-op transliterated by G-CONF. The discriminating change. |

The single behavioural change here — a non-empty group gains its surrounding
parentheses — lives in A3. `Solution_prepatch.lean` reproduces the pre-patch
bare-join (no parentheses) and **fails** `out = render (.group elts)` (G-DIFF).

## B. The subscript/index site — `visit_Subscript` (`sphinx/pycode/ast.py:168`)

Gold hunk (the reachable branches under Python 3.11; the `ast.Index` `elif` is
dead code there — mapping.md §2):
```
  def visit_Subscript(self, node: ast.Subscript) -> str:
-     return "%s[%s]" % (self.visit(node.value), self.visit(node.slice))
+     def is_simple_tuple(value): return (isinstance(value, ast.Tuple)
+         and bool(value.elts) and not any(isinstance(elt, ast.Starred) ...))
+     if is_simple_tuple(node.slice):
+         elts = ", ".join(self.visit(e) for e in node.slice.elts)
+         return "%s[%s]" % (self.visit(node.value), elts)
+     elif isinstance(node.slice, ast.Index) and is_simple_tuple(node.slice.value):
+         ...                                  # DEAD under py3.11 (no ast.Index)
+     else:
+         return "%s[%s]" % (self.visit(node.value), self.visit(node.slice))
```

| # | Solution.lean impl op (`renderIndex`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameters `value idx : Expr` | `node.value`, `node.slice` of `ast.Subscript` | R | node fields ↔ `Expr` (mapping.md §2). |
| B2 | `match idx with \| .group elts => …` | `is_simple_tuple(node.slice)` (slice IS a tuple) | R | dispatch on whether the slice is a group ↔ `isinstance(node.slice, ast.Tuple)`. |
| B3 | `if (!elts.isEmpty) && (!elts.any isUnpack) then render value ++ "[" ++ joinComma (elts.map render) ++ "]"` | the `is_simple_tuple` true arm: `"%s[%s]" % (self.visit(node.value), ", ".join(self.visit(e) for e in node.slice.elts))` | R + I | `bool(value.elts)` ↔ `!elts.isEmpty`; `not any(isinstance(elt, ast.Starred) …)` ↔ `!elts.any isUnpack`; the members are rendered directly inside the brackets (no extra parentheses around the slice). The change that keeps `Tuple[int, int]` from becoming `Tuple[(int, int)]`. |
| B4 | `else render value ++ "[" ++ render (.group elts) ++ "]"` | the `is_simple_tuple` false sub-case (empty/starred tuple slice) routed to the `else`: `"%s[%s]" % (self.visit(node.value), self.visit(node.slice))` | I | a non-simple group slice is rendered as a whole expression (which re-enters `render (.group …)` ⇒ `visit_Tuple`). Same observable result as the gold `else`. |
| B5 | `\| s => render value ++ "[" ++ render s ++ "]"` | the gold `else` arm for a non-tuple slice | I | a non-group slice is rendered as a whole expression inside the brackets — identical to the unchanged `"%s[%s]"` form. |

The behavioural change here — a simple (non-empty, no-starred) tuple slice has
its members placed directly inside the brackets rather than re-parenthesised —
lives in B3. `Solution_prepatch_2.lean` reproduces the pre-patch
"always render the whole slice expression" and **fails**
`out = render (.index value idx)` (G-DIFF), diverging exactly on a group slice.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. Both changed operations — the tuple parenthesisation and
the simple-tuple-slice flattening — are modeled **deeply** by `render` (spelled
out, recursive), not hidden behind any axiom. There are no A-tagged steps: no
consumed axiom, no A-reference, no `:|`-stub. The unchanged child renderers are
represented as `Expr.atom` leaves (I-ops: their text reproduces unchanged).

## D. verify(Solution) ⇒ resolved

`renderGroup` verifies only if its output equals the parenthesised group form
(A3); `renderIndex` verifies only if a simple-tuple slice flattens (B3). By R
(`ast` node ↔ `Expr`, str ↔ `List Char`, the join) the verified renderers equal
the patched `visit_Tuple` / `visit_Subscript` on every renderable tree; by
G-CONF the R/I transliteration of `render` agrees with `patch.diff`'s behaviour
on ≥10⁵ trees plus the boundary set, zero disagreements. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axioms, so
the only trust point is refinement fidelity (this doc, G-EQ + G-CONF); there is
no axiom-soundness trust point (G-AX is vacuous here).
