# mapping.md — sphinx-doc__sphinx-8265

## Instance
- repo: sphinx-doc/sphinx
- base_commit: b428cd2404675475a5c3dc2a2b0790ba57676202
- modeled file: `sphinx/pycode/ast.py` (class `_UnparseVisitor`, the cut-down
  AST → source-text unparser used to render default-argument / annotation
  expressions in autodoc signatures).

## Modeled functions (symbol binding @ base_commit)

| Lean triple | Python site | file:line @ base_commit |
|---|---|---|
| `*_tupleDisplay` | `_UnparseVisitor.visit_Tuple` | `sphinx/pycode/ast.py:174-178` |
| `*_subscription` | `_UnparseVisitor.visit_Subscript` | `sphinx/pycode/ast.py:168-169` |

Post-patch the two sites become (gold patch):
- `visit_Tuple`: non-empty → `"(" + ", ".join(self.visit(e) for e in node.elts) + ")"`;
  empty → `"()"`.
- `visit_Subscript`: when the index (`node.slice`, or `node.slice.value` behind a
  py<3.8 `ast.Index` wrapper) is a *simple tuple* — an `ast.Tuple` with at least
  one element and no `ast.Starred` element — the element renderings are listed
  directly between the brackets: `"%s[%s]" % (visit(value), ", ".join(visit(e) …))`;
  otherwise the index's own rendering is placed between the brackets:
  `"%s[%s]" % (visit(value), visit(slice))`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| a rendered expression / source fragment (`str`, per-code-point) | `List Char` |
| the list of already-rendered element strings `[self.visit(e) …]` | `elts : List (List Char)` |
| `", ".join(parts)` | `List.intercalate [',', ' '] parts` |
| `"(" + s + ")"` | `['('] ++ s ++ [')']` |
| `"%s[%s]" % (v, s)` | `v ++ ['['] ++ s ++ [']']` |
| the unparser's `node.slice` shape | `IndexForm` (see below) |

### `IndexForm` — the modeled shape of a subscription index
- `IndexForm.elementTuple (elts : List (List Char))` ↔ `node.slice` is an
  `ast.Tuple` with `bool(value.elts)` true and no `ast.Starred` element (the
  `is_simple_tuple` predicate true; equivalently the py<3.8 `ast.Index`-wrapped
  form `is_simple_tuple(node.slice.value)`). `elts` carries the element
  renderings `[self.visit(e) for e in node.slice.elts]`. Invariant `elts ≠ []`
  (empty tuples never satisfy `is_simple_tuple`).
- `IndexForm.plain (rendered : List Char)` ↔ any other index, carrying its own
  rendering `self.visit(node.slice)`. This subsumes: non-tuple indices
  (`a[b]`, `a[1:2]`), the empty tuple `a[()]` (renders `"()"`), and starred
  tuples (`a[*b,]`).

## Refinement boundary (what is modeled vs abstracted)
The two modeled functions transcribe ONLY the joining / wrapping logic of the
two visitor methods. The per-element recursion `self.visit(e)` and
`self.visit(node.value)` are NOT modeled: their results are the inputs
(`elts` element renderings, `valueStr`). There is therefore no UNCHANGED callee
whose contract a proof must consume and no deep-model reference to validate —
G-AX is a skip stub. The recursion boundary is exercised by G-CONF, which feeds
real `_UnparseVisitor` output back in as the modeled inputs.

## Flag / version dependency
- py3.8+ : `node.slice` of a `Tuple[...]` subscription is the `ast.Tuple`
  directly (the `is_simple_tuple(node.slice)` branch).
- py<3.8 : `node.slice` is an `ast.Index` wrapping the tuple; the patch handles
  it with the `isinstance(node.slice, ast.Index) and is_simple_tuple(node.slice.value)`
  branch. Both branches reduce to the same `IndexForm.elementTuple` case; the
  model collapses them. G-CONF runs under the testbed interpreter (py3.x).

## G-CONF fuzz seed
- pinned seed: **8265**, N = 120000 fuzzed inputs.
- atoms restricted to identity-rendering tokens (bare names like `ab`, integer
  literals like `12`) so that an element's rendering equals its source token;
  this makes the modeled boundary (`elts` = element renderings) exact against
  the real `sphinx.pycode.ast.unparse` oracle.
