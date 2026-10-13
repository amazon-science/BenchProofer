# refinement.md — sphinx-doc__sphinx-9591

Maps every operation in `implementation_propertyTypeAnnotation` to its
`patch.diff` counterpart in `PyProperty.handle_signature`
(`sphinx/domains/python.py`, the `if typ:` type-annotation arm).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch type-annotation arm)
```python
typ = self.options.get('type')
if typ:
    annotations = _parse_annotation(typ, self.env)
    signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)
```
The modeled value is the ORDERED LIST OF CHILD NODES that the type annotation
contributes to the signature. The wrapper `addnodes.desc_annotation(typ, '',
nodes.Text(': '), *annotations)` is built with `rawsource=typ`, `text=''` (the
empty `text` argument adds NO child), and varargs children `(Text(': '),
*annotations)` in order — i.e. the children list is `[Text(": ")] ++ annotations`
where `annotations = _parse_annotation(typ, self.env)`.

## Operation correspondence
| # | Lean op (`implementation_propertyTypeAnnotation`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut children : List Node := []` | no annotation fragment is appended when the type option is absent/empty | I | the accumulator starts empty (the `if typ:` guard is not yet entered). |
| 2 | `if typ ≠ "" then` | `if typ:` (with `typ = self.options.get('type')`) | R | Python truthiness of the option string `typ` ↔ Lean `typ ≠ ""`. A present `:type:` option supplies a non-empty string; an absent/empty option is falsy. Type bijection in mapping.md. |
| 3 | `let annotations := crossRefParser typ` | `annotations = _parse_annotation(typ, self.env)` | A-reference | the UNCHANGED downstream parser, turning the annotation string into a list of inline nodes (type names → cross-reference nodes). Modeled as the universally-quantified parameter `crossRefParser : String → List Node`; validated == the real callee by G-CONF (it drives the real `_parse_annotation`). NOT a consumed axiom (the proof uses no property of it). |
| 4 | `children := mkText ": " :: annotations` | `addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)` children = `[Text(': ')] ++ annotations` | R/I | the `": "` separator becomes its own plain-text node (`mkText ": "` ↔ `nodes.Text(': ')`), prepended in order to the parsed annotation nodes. The `desc_annotation` wrapper's `rawsource=typ` and `text=''` arguments contribute no child, so the children are exactly this ordered list. `::` ↔ list prepend. |
| 5 | `return children` | the children appended to `signode` as the type annotation | I | return the assembled children list. |

Tags present: R, A-reference, I. **No A-consumed row** (the parser is universally
quantified, so the proof consumes no callee property). Therefore
`meta.json axioms = []`, `deep_model_references = ["_parse_annotation"]`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The impl has genuine R/I content (the node-framing: separator text node prepended
to the parsed nodes, present-vs-empty guard), so `conformance_check.py`
mechanically differential-tests the impl shadow (separator text node + the REAL
`_parse_annotation` output) against the patched `handle_signature` children over
≥10^5 fuzzed inputs. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the arm is `signode += addnodes.desc_annotation(typ, ': ' + typ)` — the
declared type is emitted as a SINGLE plain-text run `": " + typ`, so the type text
is inert and never parsed into cross-reference-aware nodes. The prepatch impl
(`implementation_propertyTypeAnnotation := if typ ≠ "" then children := [mkText
(": " ++ typ)]`) is exactly this: it builds one plain-text node and discards the
parser's output. It therefore cannot satisfy
`problem_spec_propertyTypeAnnotation` on the discriminating clause
(`typ ≠ "" → result = mkText ": " :: crossRefParser typ`): a single plain-text
node `[mkText (": " ++ typ)]` is not the `": "` separator node followed by the
parser's nodes for any non-trivial parser output. This is precisely what the
FAIL_TO_PASS test `test_pyproperty` exercises: it asserts the property's type
annotation children are `(": ", [pending_xref, "str"])` (a `": "` text node
followed by a cross-reference node), which the prepatch's single inert text node
cannot produce. The carried gold-style proof fails to typecheck against the buggy
impl (G-DIFF).
