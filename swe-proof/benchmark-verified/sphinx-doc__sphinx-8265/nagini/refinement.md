# refinement.md — sphinx-doc__sphinx-8265

The operation-by-operation correspondence between `model.py`'s implementation
(the `tuple_render` and `subscript_render` impl regions and the deep
`join_comma` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (a callee — **A-consumed** where the proof uses
an axiom's `Ensures`, **A-reference** where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). It is multi-site: two sibling methods
of the AST unparser change together.

## A. Site 1 — the standalone group, `visit_Tuple` (`sphinx/pycode/ast.py:174`)

Gold hunk:
```
     def visit_Tuple(self, node: ast.Tuple) -> str:
         if node.elts:
-            return ", ".join(self.visit(e) for e in node.elts)
+            return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
         else:
             return "()"
```

| # | model.py impl op (`tuple_render`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elts: PSeq[PSeq[int]]` | `[self.visit(e) for e in node.elts]` (the rendered members) | R | `str` ↔ `PSeq[int]`; `List[str]` ↔ `PSeq[PSeq[int]]` (mapping.md §2). The per-member `self.visit` recursion is UNCHANGED and produces this list both pre- and post-patch. |
| A2 | branch `if len(elts) > 0` | `if node.elts:` | R | non-empty test on the member list; `len(elts) > 0` ↔ truthiness of `node.elts`. |
| A3 | non-empty result `(PSeq(40) + join_comma(elts)) + PSeq(41)` | `"(" + ", ".join(...) + ")"` | R + A-reference | the wrapping characters `'(' '∙' ')'` are literal concatenation (`'(' == 40`, `')' == 41`, R); the inner `", ".join(...)` is modeled **deeply** by `join_comma` (front-recursive fold, `pure` region), an **A-reference** validated `== ", ".join` by G-AX (mapping.md §3.1). |
| A4 | empty result `PSeq(40, 41)` | `return "()"` | I | the empty group renders as the two characters `'('`,`')'` in both; `PSeq(40, 41)` is that literal. Unchanged by the fix. |

The discriminating content of site 1 — that a non-empty group is **wrapped in
round brackets** — lives in the postcondition
`Result() == (PSeq(40) + join_comma(elts)) + PSeq(41)`. The pre-patch code
returned the bare join; `model_prepatch.py` reproduces that (`result =
join_comma(elts)`) and **fails** this postcondition (verified failure on the
`tuple_render` postcondition), which is exactly the spec sensing the F2P change
`(1, 2, 3)` → `(1, 2, 3)` (formerly `1, 2, 3`). G-DIFF.

## B. Site 2 — the index, `visit_Subscript` (`sphinx/pycode/ast.py:168`)

Gold hunk:
```
     def visit_Subscript(self, node: ast.Subscript) -> str:
-        return "%s[%s]" % (self.visit(node.value), self.visit(node.slice))
+        def is_simple_tuple(value: ast.AST) -> bool:
+            return (isinstance(value, ast.Tuple) and bool(value.elts)
+                    and not any(isinstance(elt, ast.Starred) for elt in value.elts))
+        if is_simple_tuple(node.slice):
+            elts = ", ".join(self.visit(e) for e in node.slice.elts)
+            return "%s[%s]" % (self.visit(node.value), elts)
+        elif isinstance(node.slice, ast.Index) and is_simple_tuple(node.slice.value):
+            elts = ", ".join(self.visit(e) for e in node.slice.value.elts)
+            return "%s[%s]" % (self.visit(node.value), elts)
+        else:
+            return "%s[%s]" % (self.visit(node.value), self.visit(node.slice))
```

| # | model.py impl op (`subscript_render`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `value: PSeq[int]` | `self.visit(node.value)` | R | `str` ↔ `PSeq[int]`; unchanged upstream base rendering taken as input. |
| B2 | parameter `index_is_member_group: bool` | `is_simple_tuple(node.slice)` ∨ (`isinstance(node.slice, ast.Index)` ∧ `is_simple_tuple(node.slice.value)`) | R | the two version-specific branches (`ast.Tuple` directly on py3.9+, `ast.Index`-wrapped on ≤py3.8) both lead to the SAME body `", ".join(... .elts)`, so they collapse to one boolean: the index is a non-empty tuple with no `Starred` member (mapping.md §2). |
| B3 | parameter `elts: PSeq[PSeq[int]]` (rendered slice members) | `[self.visit(e) for e in node.slice.elts]` (or `node.slice.value.elts`) | R | rendered members of the tuple index; the `Requires(Implies(index_is_member_group, len(elts) > 0))` mirrors `bool(value.elts)` in `is_simple_tuple`. |
| B4 | parameter `slice_rendered: PSeq[int]` | `self.visit(node.slice)` (general `else` branch) | R | the index's own rendering for the non-simple-tuple case; unchanged upstream input. |
| B5 | simple-tuple body `join_comma(elts)` (no surrounding `( )`) | `", ".join(self.visit(e) for e in node.slice.elts)` | A-reference | the BARE comma-and-space join, no round brackets; modeled deeply by `join_comma`, validated `== ", ".join` by G-AX. |
| B6 | result `((value + PSeq(91)) + body) + PSeq(93)` | `"%s[%s]" % (self.visit(node.value), <body>)` | R | `'[' == 91`, `']' == 93`; `%`-format is literal concatenation of base, `'['`, body, `']'`. |

The discriminating content of site 2 — that a **simple tuple index keeps NO
inner round brackets** (`base[m0, m1]`, not `base[(m0, m1)]`) — lives in the
postcondition `Implies(index_is_member_group, Result() == ((value + PSeq(91)) +
join_comma(elts)) + PSeq(93))`. Once site 1 parenthesises standalone groups,
the pre-patch `visit_Subscript` (which rendered the slice via the same
`self.visit`) would produce the parenthesised body. `model_prepatch_2.py`
reproduces that (`body = (PSeq(40) + join_comma(elts)) + PSeq(41)`) and **fails**
this postcondition (verified failure on the `subscript_render` postcondition).
This is the coupling: site 2 is the regression guard that keeps the P2P
`Tuple[int, int]` → `Tuple[int, int]` test passing under site 1's change.
G-DIFF (second independently-observable behaviour ⇒ second prepatch variant).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one library operation the two
hunks build on — the `", ".join` — is modeled **deeply** over `PSeq[int]`
(the front-recursive fold `join_comma`), not hidden behind a consumed axiom.
There is **no `@ContractOnly` axiom in this bundle.** The per-member and
non-tuple-index `self.visit` recursions are UNCHANGED upstream computations
taken as already-rendered inputs (mapping.md §3.2), not modeled or axiomatized —
the patch does not touch how a member is rendered, only how the rendered members
are wrapped. The deep model is validated `join_comma == ", ".join` by G-AX
(axiom_check.py).

## D. verify(model) ⇒ resolved

`tuple_render` verifies only if a non-empty group is exactly `'(' + join + ')'`
and the empty group is exactly `'()'` (A3, A4); `subscript_render` verifies only
if a simple-tuple index body is the BARE join inside `[...]` (B5) and any other
index body is its own rendering inside `[...]` (B4). By R (`str` ↔ `PSeq[int]`,
literal-bracket concatenation, the `is_simple_tuple`/`ast.Index` collapse) the
two verified renderers equal the two gold-patched methods on the tested inputs;
by G-AX the deep model `join_comma` equals the real `", ".join` (A-reference).
Therefore a model satisfying this spec, refined by the map above, IS the gold
patch up to type refinement and the audited deep model — and the gold patch
resolves (G-RESOLVE). The F2P test observes a standalone `(1, 2, 3)` rendering
back to `(1, 2, 3)` (gold) where the pre-patch produced `1, 2, 3`; the coupled
P2P test observes `Tuple[int, int]` staying `Tuple[int, int]` where the naive
site-1-only change would have produced `Tuple[(int, int)]`. The single trust
point of PLAN §1.1 active here is deep-model soundness (G-AX); refinement
fidelity is this document (G-EQ). No consumed-axiom trust point exists (there is
no `@ContractOnly`).
