# mapping.md — sphinx-doc__sphinx-9367

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 6918e69600810a4664e53653d6ff0290c3c4a788
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The AST-to-source unparser renders a tuple expression by wrapping the rendered
text of its component expressions in parentheses, separated by `", "`. At
base_commit the renderer used a single two-way branch:

```python
if node.elts:
    return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
else:
    return "()"
```

For a tuple with exactly ONE component this produced `"(1)"` — which is NOT a
tuple but a parenthesized expression. A one-component tuple must keep its trailing
comma, i.e. render as `"(1,)"`. The gold patch adds the single-component special
case:

```python
if len(node.elts) == 0:
    return "()"
elif len(node.elts) == 1:
    return "(%s,)" % self.visit(node.elts[0])
else:
    return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
```

Each component is rendered by the recursive per-component visit `self.visit(e)`,
which is UNCHANGED by the patch; the only thing the patch changes is how the
rendered components are wrapped/joined for the one-component case.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_renderTuple` | `_UnparseVisitor.visit_Tuple` (sphinx/pycode/ast.py:215-219 @ base_commit) |
| `problem_spec_renderTuple`   | the post-condition this method must satisfy |
| `elts : List String` (input) | `[self.visit(e) for e in node.elts]` — the per-component rendered text, in order; `self.visit` is the unchanged recursive component renderer |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `elts : List String` | `[self.visit(e) for e in node.elts]` | the ordered rendered text of the tuple's component expressions; per-component `self.visit` is the unchanged downstream callee (A-reference), bound to the REAL visitor in G-CONF |
| `elts.length` | `len(node.elts)` | number of tuple components |
| `String.intercalate ", " elts` | `", ".join(self.visit(e) for e in node.elts)` | components joined by comma-space |
| result `: String` | the rendered source text returned by `visit_Tuple` | byte-for-byte `str` |

`String` ↔ Python `str` is the identity bijection (byte-for-byte).

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The per-component renderer
  `self.visit` (the recursive AST→text dispatch) is left implicit: the input
  `elts : List String` IS the list of already-rendered component strings, so the
  spec holds for EVERY component renderer and pins only how those rendered pieces
  are wrapped/joined — which is exactly the modeled change. The proof consumes no
  property of the component renderer, so there is no `axiom <callee>_prop`.
  `axiom_check.py` is a skip stub.
- No flag dependency: the branch is selected solely by `len(node.elts)`
  (0 / 1 / ≥2).

## G-CONF fuzz seed
- pinned seed: `9367`
- ≥10^5 fuzzed tuple expressions of varying arity (0, 1, 2, …) with random simple
  and nested component expressions, parsed at base_commit-equivalent grammar.
  Oracle = the REAL patched `sphinx.pycode.ast.unparse` of the whole tuple node;
  shadow = `[unparse(e) for e in node.elts]` (the real per-component visit) fed
  through the Lean impl's wrap/join logic. The real per-component visit is used so
  nested tuples are rendered by the patched renderer in both legs.
