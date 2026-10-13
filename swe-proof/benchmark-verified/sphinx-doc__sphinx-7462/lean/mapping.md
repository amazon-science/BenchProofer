# mapping.md — sphinx-doc__sphinx-7462

## Instance summary
Empty tuple type annotation (`Tuple[()]`) crashes / renders wrong. Two
independent renderers each assemble a tuple from its already-rendered elements
and forget to special-case the empty case:

* `sphinx/domains/python.py :: unparse` builds a list of inline display nodes;
  on an empty tuple it executed `result.pop()` on an empty list → `IndexError`.
* `sphinx/pycode/ast.py :: unparse` builds a source-text string; on an empty
  tuple `", ".join([])` produced `""` instead of `"()"`.

Both fixes add an explicit empty-case branch yielding the literal parentheses.

## Symbol binding (@ base_commit b3e26a6c851133b82b50f4b68b53692076574d13)

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `problem_spec_renderTupleSig` / `implementation_renderTupleSig` / `correct_renderTupleSig` | `unparse(node)` — `ast.Tuple` branch (returns `List[Node]`) | `sphinx/domains/python.py:115-120` (Tuple branch); fixed at gold `@@ -105,11 +105,16` |
| `problem_spec_renderTupleText` / `implementation_renderTupleText` / `correct_renderTupleText` | `unparse(node)` — `ast.Tuple` branch (returns `str`) | `sphinx/pycode/ast.py:116-117` (Tuple branch); fixed at gold `@@ -114,7 +114,10` |

## Type bijection (used by G-CONF + G-AX)

| Python value | Lean model |
|---|---|
| a docutils inline node (`addnodes.desc_sig_punctuation('', s)`, `nodes.Text`, xref) | `SigToken` with `punct : String → SigToken` (a `desc_sig_punctuation` carrying its text) and `text : String → SigToken` (a Text/xref-style node carrying its text). The differential test models each node by `(kind, text)`. |
| `unparse(elem)` result for one tuple element (a `List[Node]`) | one `elem : List SigToken` — the **already-rendered** element. The per-element recursion is the UNCHANGED collaborator and is left universally quantified (arbitrary `elems`), see axioms region. |
| `node.elts` (the tuple's elements) | `elems : List (List SigToken)` — list of per-element rendered token lists |
| `result.pop()` (drop trailing `', '` separator) | `List.dropLast` |
| `", ".join(parts)` of element source strings | `String.intercalate ", " elems` (`elems : List String`) |
| empty-tuple node-list `['(' , ')']` | `[SigToken.punct "(", SigToken.punct ")"]` |
| empty-tuple text `"()"` | the string literal `"()"` |

### Why elements are universally quantified, not axiomatized
The recursive `unparse(elem)` that renders each element is UNCHANGED by the fix.
Both modeled functions only re-assemble those rendered pieces. Following
SPEC_GUIDE §0.7/§3, the changed assembly op is modeled DEEPLY; the unchanged
per-element renderer is represented by arbitrary input `elems` (∀-quantified in
both `correct_*`), so no callee `opaque`/`axiom` contract is consumed. → G-AX is
a skip stub; the R/I assembly legs are validated by G-CONF.

## Callee provenance / flag deps
None. No flag-dependent collaborator. The `addnodes.desc_sig_punctuation`
constructor is data (a node tag + text), modeled by `SigToken.punct`.

## G-CONF fuzz seed
`7462` (pinned; also in `conformance_check.py` and `meta.json`).
