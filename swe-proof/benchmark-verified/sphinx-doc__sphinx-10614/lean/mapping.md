# mapping.md — sphinx-doc__sphinx-10614

## Modeled symbol
- **Function under spec:** `html_visit_inheritance_diagram`
  (`sphinx/ext/inheritance_diagram.py:398-428` @ base_commit
  `ac2b7599d212af7d04649959ce6926c63c3133fa`). The modeled behavior is the
  `urls` dict-construction loop at lines **411-423** (the only lines the gold
  patch touches: `@@ -412,13 +412,16 @@`).
- **Lean triple:** `problem_spec_buildUrls` / `implementation_buildUrls` /
  `correct_buildUrls` in `Solution.lean`.

## Source under spec (post-patch loop body, lines 411-423)
```python
urls = {}
pending_xrefs = cast(Iterable[addnodes.pending_xref], node)
for child in pending_xrefs:
    if child.get('refuri') is not None:
        # Construct the name from the URI if the reference is external via intersphinx
        if not child.get('internal', True):
            refname = child['refuri'].rsplit('#', 1)[-1]
        else:
            refname = child['reftitle']
        urls[refname] = child.get('refuri')
    elif child.get('refid') is not None:
        if graphviz_output_format == 'SVG':
            urls[child['reftitle']] = current_filename + '#' + child.get('refid')
        else:
            urls[child['reftitle']] = '#' + child.get('refid')
```
`graphviz_output_format` is `self.builder.env.config.graphviz_output_format.upper()`
(line 409) — modeled by the boolean `isSVG` (`== 'SVG'`). `current_filename` is
`self.builder.current_docname + self.builder.out_suffix` (line 410) — an opaque
string input `currentFilename`.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python (per child / context) | Lean | bijection |
|---|---|---|
| `graphviz_output_format == 'SVG'` | `isSVG : Bool` | `'SVG' ↔ true`, any other format ↔ `false` |
| `current_filename` (str) | `currentFilename : String` | identity |
| `pending_xrefs` (ordered iterable of children) | `children : List Xref` | element-wise, order-preserving |
| `child.get('refuri')` (`str` or `None`) | `Xref.refuri : Option String` | `str ↔ some`, `None ↔ none` |
| `child.get('refid')` (`str` or `None`) | `Xref.refid : Option String` | `str ↔ some`, `None ↔ none` |
| `child['reftitle']` (str) | `Xref.reftitle : String` | identity |
| `child.get('internal', True)` (bool, default True) | `Xref.internal : Bool` | `True ↔ true`, `False ↔ false`; the default is folded into the carrier (a child with no `internal` key ↔ `internal := true`) |
| `urls` (dict str→str, insertion-ordered) | `List (String × String)` | insertion order ↔ list order; the test observes the rendered per-node links, so order/multiplicity is faithful |
| `refuri.rsplit('#', 1)[-1]` | `uriTail refuri` | trailing component after the final `#`; no `#` ⇒ whole string (matches `rsplit('#',1)[-1]`) |

### `internal` default note
The real code reads `child.get('internal', True)`: a pending_xref that never set
`internal` is treated as **internal**. The model folds this default into the
carrier — `internal := true` represents both "internal key present and True" and
"key absent". Only `internal == False` (an external/intersphinx reference) takes
the `rsplit` branch. G-CONF fuzzes both `True` and `False` directly.

### `elif` / branch precedence
`refuri` is checked before `refid` (`elif`); a child with BOTH present takes the
`refuri` branch. The Lean `match c.refuri with | some _ ... | none => match
c.refid ...` reproduces this precedence exactly. A child with neither attribute
contributes nothing (`none`/dropped by `filterMap`).

## Callee provenance / flag deps
- No unchanged pure callee is consumed as an axiom. `rsplit('#', 1)[-1]`,
  string concatenation (`+`), and the dict insert are all modeled deeply as
  `List Char`/`String` operations over the inputs ⇒ `axioms = []`,
  `deep_model_references = []`, `axiom_check.py` is a skip stub (G-AX = skip).
- Flag dependency: the SVG-vs-raster behavior pivots on
  `graphviz_output_format.upper() == 'SVG'`; G-CONF fuzzes both `isSVG` values.
  The `internal` flag is fuzzed both ways.

## G-CONF fuzz seed
Pinned seed: **10614** (matches `conformance_check.py`). ≥1.2e5 inputs (structured
edge enumeration over single-child cases × SVG × filename, plus 1.2e5 random
multi-child diagrams).
