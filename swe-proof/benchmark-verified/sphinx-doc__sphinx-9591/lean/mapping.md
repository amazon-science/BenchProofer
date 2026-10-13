# mapping.md — sphinx-doc__sphinx-9591

## Symbol binding (file:line @ base_commit 9ed054279a)
Modeled function: the type-annotation rendering arm of
`PyProperty.handle_signature` in `sphinx/domains/python.py:858-865`. When the
documented property carries a `:type:` option `typ`, the directive appends a
type-annotation node to the signature node. The gold patch changes HOW that
node's children are built: instead of a single plain-text node carrying the
literal `": " + typ`, it now prepends a `": "` text node and then splices in the
nodes produced by parsing the annotation string (which turns type names into
cross-reference nodes).

Lean modeled function name: `propertyTypeAnnotation` (neutral — it names the
behavior "build the type-annotation nodes for a documented property", which is
exactly the public vocabulary of the problem statement: "property's type
annotations" / "cross-referenced"; it shares no patched def/class name as a
substring).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `propertyTypeAnnotation` (modeled action) | `PyProperty.handle_signature` type arm, `python.py:861-864` (post-patch `:861-865`) |
| `typ` | `typ = self.options.get('type')` — the annotation string, present (truthy) iff the `if typ:` guard fires, `python.py:861-862` |
| `mkText` | `nodes.Text` constructor (`docutils.nodes.Text`) — builds a plain-text node from a string |
| `crossRefParser` | `_parse_annotation(typ, self.env)` — the UNCHANGED downstream callee that parses an annotation string into a list of inline nodes (type names become `pending_xref` cross-reference nodes), `python.py:110-186` (called at `:863` post-patch) |
| result | the ordered list of child nodes appended to the signature as the type annotation: post-patch `[Text(": ")] ++ _parse_annotation(typ, env)` |

The full post-patch statement is
`signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)`
where `annotations = _parse_annotation(typ, self.env)`. The `desc_annotation`
wrapper is constructed with `rawsource=typ`, `text=''` (so the `text` argument
contributes NO child), and the varargs `(Text(': '), *annotations)` become its
children in order. The modeled value is precisely that ordered children list —
the only thing the change and the FAIL_TO_PASS test observe.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| an inline docutils node | `Node : Type` (an opaque/universally-quantified node carrier) |
| `nodes.Text` (string → text node) | `mkText : String → Node` |
| `_parse_annotation(s, env)` → `List[Node]` | `crossRefParser : String → List Node` |
| annotation string `typ : str` (non-empty under the `if typ:` guard) | `typ : String` (precondition `typ ≠ ""`) |
| ordered children appended to the signature: `[Text(': '), *_parse_annotation(typ, env)]` | `result : List Node = mkText ": " :: crossRefParser typ` |

### Node-framing modeling note
The change is purely about the SHAPE of the children list (one plain-text node
vs. a `": "` text node followed by the parsed annotation nodes). The node objects
themselves are modeled as an arbitrary carrier type `Node` with one known
constructor `mkText` (the `nodes.Text` factory); the annotation parser
`crossRefParser` is left universally quantified (the change is WHICH children are
assembled, not what the parser produces). This is the django-11119-style pattern:
the spec holds for EVERY parser, pinning only that the result is the `": "` text
node followed by the parser's output, in that order.

## Callee provenance + flag deps
- `_parse_annotation` is the UNCHANGED downstream callee. It is NOT consumed as
  an axiom: it is left universally quantified (`crossRefParser : String → List
  Node`), so the proof of `correct_propertyTypeAnnotation` uses no property of
  it. It is recorded as an **A-reference** solely to document the G-CONF binding
  to the real callee (G-CONF drives the real `_parse_annotation`).
- Flag dependency: `_parse_annotation` → `type_to_xref` branches on
  `env.config.python_use_unqualified_type_names`. This only affects the INTERNAL
  shape of each parsed node (a single `Text` vs. `pending_xref_condition`
  children), never the FRAMING the patch changes. G-CONF exercises the default
  configuration (`python_use_unqualified_type_names = False`), matching the
  FAIL_TO_PASS test `test_pyproperty` (which expects a `pending_xref` child).
- `nodes.Text` (`mkText`) is the docutils plain-text node factory — also
  unchanged, modeled as the known constructor of `Node`.

## G-LEAK
The solver-visible problem_statement contains "property", "type annotation(s)",
and "cross-referenced". The spec view uses only that public behavioral
vocabulary ("a documented property's type annotation", "parsed into
cross-reference-aware nodes"). It does NOT reproduce any gold-diff line, name the
patched file path (`sphinx/domains/python.py`), or name the patched def/class
symbol `handle_signature`. The callee `_parse_annotation` / `desc_annotation` /
`nodes.Text` are described by behavior, never by name (M1 lesson).

## Pinned G-CONF fuzz seed
`9591`.
