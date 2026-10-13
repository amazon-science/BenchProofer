# refinement.md — sphinx-doc__sphinx-7454

Maps every operation in `implementation_annotationRef` to its `patch.diff`
counterpart in `make_xref` (sphinx/domains/python.py:73). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference** op
left as the real repo callee in G-CONF (not axiomatized), **I** identical
concrete op.

## Patch (post-patch `make_xref`)
```python
 def make_xref(text: str) -> addnodes.pending_xref:
+    if text == 'None':
+        reftype = 'obj'
+    else:
+        reftype = 'class'
+
     return pending_xref('', nodes.Text(text),
-                        refdomain='py', reftype='class', reftarget=text)
+                        refdomain='py', reftype=reftype, reftarget=text)
```

The changed op is the computation of `reftype`: pre-patch the literal `'class'`
for every token; post-patch `'obj'` when `text == 'None'`, else `'class'`. The
domain (`'py'`), the target (`text`), and the visible label (`nodes.Text(text)`)
are unchanged.

## Modeling decision
`make_xref` returns a `pending_xref` node whose relevant data is its four fields
`(refdomain, reftype, reftarget, label)`. `pending_xref(...)` simply stores the
keyword args as node attributes and the positional `nodes.Text(text)` as the
node's text child; nothing about the result is opaque, so the node is modeled
deeply as the `TypeRef` record — no axiom. The branch on `text == 'None'` is
spelled out structurally (`if text = "None".toList`).

## Operation correspondence
| # | Lean op (`implementation_annotationRef`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut kind := "class"` ; `if text = "None".toList then kind := "obj" else kind := "class"` | `if text == 'None': reftype = 'obj' else: reftype = 'class'` | R | the only changed op; the `None`-token branch selecting the object kind. `List Char` ↔ `str`; `"obj"`/`"class"` ↔ `'obj'`/`'class'`. |
| 2 | `{ domain := "py", … }` | `refdomain='py'` | I | constant domain literal. |
| 3 | `{ …, kind := kind, … }` | `reftype=reftype` | I | kind threaded from op 1. |
| 4 | `{ …, target := text, … }` | `reftarget=text` | I | target = token (unchanged). |
| 5 | `{ …, label := text }` | `nodes.Text(text)` child | I | visible label = token (unchanged). |

The behavior-changing op is #1: pre-patch `kind` is always `"class"` (so the
`None` token resolves as a class and is not linked); post-patch the `None` token
gets `"obj"`. The prepatch impl encodes the pre-patch constant `"class"`, so on
`text = "None"` it yields `kind = "class"` while the spec forces `"obj"` — the
exact discrimination behind the F2P assertion
`assert_node(doctree[0], pending_xref, reftype="obj")` for `_parse_annotation("None")`.

## R/I legs ⇒ G-CONF
All ops are R/I (op 1 R, ops 2–5 I); no op is left as an opaque callee, so there
is no A-reference and no A-consumed row. G-CONF imports the REAL patched
`make_xref` from the live `sphinx.domains.python` and differential-tests the
Python transliteration of `implementation_annotationRef` (the same `kind` branch
+ the four constant/threaded fields) against it over ≥10^5 fuzzed tokens, by
comparing all four node fields. `conf_skip = false`: the impl region is genuine
R/I content.

## No A-consumed / A-reference row
The proof consumes no axiom and references no real callee: `TypeRef` is a
concrete record, the `None` branch is a concrete `if`. `meta.json axioms = []`,
`deep_model_references = []`. There is no `opaque`/`axiom` declaration in
`Solution.lean`; `axiom_check.py` is a skip stub.

## F2P / issue alignment
- The new F2P assertions in `tests/test_domain_py.py::test_parse_annotation`:
  `_parse_annotation("int")` → `reftype="class"`, and `_parse_annotation("None")`
  → `reftype="obj"`. The spec forces exactly these (`kind = "class"` for `int`,
  `kind = "obj"` for `None`); the prepatch impl yields `kind = "class"` for
  `None`, failing the `None` assertion — the discriminating clause.
- `patch.diff` is the gold patch verbatim; it makes the harness resolve.
