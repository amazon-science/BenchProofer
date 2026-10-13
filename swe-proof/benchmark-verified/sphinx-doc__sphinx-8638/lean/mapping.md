# mapping.md — sphinx-doc__sphinx-8638

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 4b452338f914d4f6b54704222d70ae8a746e3db5
- modeled behavior: rendering of one documented-variable info-field item
  (name [+ optional type] + description) into inline doctree nodes.

## Symbol binding (file:line @ base_commit)
- Changed config site: `sphinx/domains/python.py:354` — the
  `PyTypedField('variable', label=_('Variables'), rolename='obj', …)` entry in
  `PyObject.doc_field_types`. The fix drops `rolename='obj'` (→ `rolename=None`).
- Behavior site exercised by the fix: `sphinx/util/docfields.py`
  - `TypedField.make_field.handle_item` (lines ~170-196): renders one item —
    `par.extend(make_xrefs(self.rolename, …, literal_strong))` for the NAME,
    then if a type is present `par += " ("`, the type xref via
    `make_xrefs(self.typerolename, …, literal_emphasis)`, `")"`, then `" -- "`,
    then the description content.
  - `Field.make_xref` (lines ~63-72): `if not rolename: return innernode(target,target)`
    (a plain node); else wrap in `pending_xref(reftype=rolename)`.
  - `Field.make_xrefs` (lines ~74-77): `[make_xref(...)]` (single token here).

## Data flow of the fix
The variable field's configured name-`rolename` flips from `"obj"` to `""`/None.
At runtime `make_xref` then takes the `not rolename` branch, so the variable's
NAME renders as a plain `literal_strong` text node instead of being wrapped in a
`pending_xref`. The TYPE rendering is untouched: `typerolename` stays `"class"`,
so the type token remains a `pending_xref(reftype="class")[literal_emphasis]`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| inline doctree node | `RenderNode` inductive |
| `nodes.Text s` | `RenderNode.text s` |
| `addnodes.literal_strong(t,t)` | `RenderNode.strong t` |
| `addnodes.literal_emphasis(t,t)` | `RenderNode.emph t` |
| `addnodes.pending_xref(reftype=r)[inner]` | `RenderNode.xref r inner` |
| `self.rolename` (variable field) | `rolename : String` ("" post-fix) |
| `self.typerolename` | `"class"` (constant, unchanged) |
| `fieldarg` (variable name str) | `fieldarg : String` |
| type token (single Text) or absent | `type : Option String` |
| description `content` (node list) | `content : List RenderNode` |
| paragraph children produced by `handle_item` | `List RenderNode` (result) |

Note: `make_xrefs` returns a singleton list here because the variable name /
type token is a single text token (the F2P scenario). Modeled as one node.

## Callee provenance
- `make_xref` / `make_xrefs`: UNCHANGED callees. Modeled DEEPLY as the pure
  helper `makeXref` (the `not rolename` branch + `pending_xref` branch). Tagged
  **A-reference** (validated == real callee by G-AX over fuzzed rolename/target),
  NOT a consumed axiom. No `opaque`/`axiom` needed.
- `env`/`process_field_xref`: irrelevant to node STRUCTURE (with `env=None` the
  xref is created but not resolved); not modeled.

## Flag deps
None. The rolename change is unconditional config.

## G-CONF fuzz seed
seed = 8638 (pinned in conformance_check.py).
