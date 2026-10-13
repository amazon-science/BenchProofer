# mapping.md — sphinx-doc__sphinx-8265

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b428cd2404675475a5c3dc2a2b0790ba57676202`, states the type
abstraction, and gives the provenance of the one deep-model reference (the
comma-and-space join). The patch is multi-site: it edits two sibling methods of
the same AST-unparser class.

Repo file under change: `sphinx/pycode/ast.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `tuple_render(elts)` | `_UnparseVisitor.visit_Tuple(self, node)` — `sphinx/pycode/ast.py:174` | modeled changed function (site 1): textual rendering of a tuple node |
| `subscript_render(value, elts, index_is_member_group, slice_rendered)` | `_UnparseVisitor.visit_Subscript(self, node)` — `sphinx/pycode/ast.py:168` | modeled changed function (site 2): textual rendering of a subscript node |
| `join_comma(parts)` *(deep model — A-reference)* | `", ".join(...)` (CPython `str.join`), used inside both methods (`ast.py:169,176` post-patch) | pure spec: the comma-and-space join of the rendered members; deep model of the unchanged join callee, validated `join_comma == ", ".join` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `elts` member sequences (`PSeq[PSeq[int]]`) | `self.visit(e) for e in node.elts` (`ast.py:160-likewise`) | the already-rendered members; the per-member `self.visit` recursion is UNCHANGED upstream and is taken as an input, not modeled or axiomatized |
| `value` (`PSeq[int]`) | `self.visit(node.value)` of a subscript | already-rendered base; unchanged upstream input |
| `slice_rendered` (`PSeq[int]`) | `self.visit(node.slice)` for a non-simple-tuple index | the index's own rendering for the general branch; unchanged upstream input |
| `index_is_member_group` (`bool`) | the `is_simple_tuple(node.slice)` predicate (plus the `ast.Index`-wrapped variant), introduced by the patch (`ast.py:169-180` post-patch) | abstract flag: the index is a non-empty tuple with no `Starred` member |

The pre-patch repo behaviour the change removes/alters (for the refinement
audit, not referenced from the consumer spec view):
- `visit_Tuple` previously returned `", ".join(...)` for a non-empty tuple with
  **no** surrounding parentheses (`ast.py:176-178`).
- `visit_Subscript` previously returned `"%s[%s]" % (self.visit(node.value),
  self.visit(node.slice))` with **no** special-case for a tuple slice
  (`ast.py:169`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (every rendered fragment / method return) | `List[int]` / `PSeq[int]` of Unicode code points | `s[k]` ↔ code point `ord(s[k])`; `len(s)` ↔ `len`; `str` `+`/`%`-concatenation ↔ `PSeq` `+`; empty `str` ↔ empty sequence |
| `List[str]` of rendered members (the generator `self.visit(e) for e in node.elts`) | `PSeq[PSeq[int]]` | member-wise code-point lift |
| `"%s[%s]" % (a, b)` (`ast.py:169`) | `a + PSeq(91) + b + PSeq(93)` | `'[' == 91`, `']' == 93`; `%`-format is plain concatenation here |
| `"(" + j + ")"` / the bare `j` (`ast.py:176-178`) | `PSeq(40) + j + PSeq(41)` / `j` | `'(' == 40`, `')' == 41` |
| `"()"` literal (empty tuple, `ast.py:178`) | `PSeq(40, 41)` | the two characters `'('`, `')'` |
| `", ".join(...)` (`ast.py:169,176` post-patch) | `join_comma(...)` deep model | separator `', ' == PSeq(44, 32)` (`',' == 44`, `' ' == 32`); see §3.1 |
| `is_simple_tuple(node.slice)` predicate (incl. the `ast.Index`-wrapped form) | the boolean parameter `index_is_member_group` | true iff the index is a non-empty tuple node whose members contain no `Starred` (`*x`) node; the two version-specific branches (`ast.Tuple` directly on py3.9+, `ast.Index` wrapping on ≤py3.8) collapse to one flag because both feed the same `", ".join(... .elts)` body |

`str` indexing/iteration is banned in Nagini, so every fragment is a
code-point sequence; the specification is phrased over `PSeq[int]`.

## 3. Deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `join_comma` deep model ↔ `", ".join` (A-reference)
**Callee:** CPython `str.join` with the separator literal `", "`. The patch uses
it in both edited methods:

```python
# visit_Subscript (post-patch), when the index is a simple tuple:
elts = ", ".join(self.visit(e) for e in node.slice.elts)
return "%s[%s]" % (self.visit(node.value), elts)
# visit_Tuple (post-patch), non-empty:
return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
```

`", ".join([p0, p1, ..., pk])` inserts the two-character separator `', '`
(`[44, 32]`) between consecutive members and concatenates: `p0 + ', ' + p1 +
... + ', ' + pk`. The empty list joins to `''`; a one-element list joins to that
element. This is exactly the front-recursive fold `join_comma` encodes (model.py
`pure` region). There is **no consumed `join` axiom**: the proof spells the join
out and G-AX validates it against the real callee. Docs:
https://docs.python.org/3/library/stdtypes.html#str.join

### 3.2 Why no callee axiom is consumed
The per-member rendering `self.visit(e)` and the non-tuple index rendering
`self.visit(node.slice)` are the **unchanged** recursive dispatch of the
unparser. They are upstream of the edited assembly (the patch does not touch how
a member is rendered, only how the rendered members are wrapped), so the model
takes them as already-rendered `PSeq[int]` inputs rather than axiomatizing them.
The only repository operation that needs out-of-band validation is the
comma-and-space join (§3.1), modeled deeply and checked by G-AX.

**Soundness check (G-AX):** `axiom_check.py` runs the real `", ".join` on
boundary member-lists (including the F2P tuple members `1, 2, 3` and the P2P
subscript members `int, int`) plus 30 000 randomized fuzz lists over a
bracket/comma-rich alphabet, asserting `join_comma == ", ".join` on every
input. It also asserts the two bug-witness discriminations the twin relies on:
the standalone group gains round brackets (`(1, 2, 3)` vs the pre-patch
`1, 2, 3`) and the simple-group index drops them (`Tuple[int, int]` vs the
pre-patch coupling artefact `Tuple[(int, int)]`). It imports only `random`/`sys`;
nothing repo-specific. Exit 0 iff sound.
