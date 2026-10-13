# mapping.md — sphinx-doc__sphinx-7454

## Instance
- repo: sphinx-doc/sphinx
- base_commit: aca3f825f2e4a8817190f3c885a242a285aa0dba
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`_parse_annotation(annotation)` (sphinx/domains/python.py:71) turns a Python type
annotation string into a list of docutils nodes for rendering an API signature.
Each bare name token of the annotation is converted to a `pending_xref`
cross-reference node by the inner helper `make_xref(text)`
(sphinx/domains/python.py:73). At base_commit `make_xref` builds:

```python
return pending_xref('', nodes.Text(text),
                    refdomain='py', reftype='class', reftarget=text)
```

i.e. domain `'py'`, reference type `'class'`, target = label = `text`, for EVERY
token. Because the `None` token is given `reftype='class'`, the intersphinx
resolver looks `None` up as a class and finds nothing, so the `None` in a
signature type hint produces no clickable link — whereas in `'description'` mode
`None` IS linked (to the `None` singleton's docs). The gold patch makes the
reference type branch on the token:

```python
-                    refdomain='py', reftype='class', reftarget=text)
+    if text == 'None':
+        reftype = 'obj'
+    else:
+        reftype = 'class'
+    ...
+                    refdomain='py', reftype=reftype, reftarget=text)
```

so the `None` token gets `reftype='obj'` (an object reference, resolving to the
`None` singleton's documentation) while every other token keeps `reftype='class'`.
domain, target, and label are unchanged for all tokens.

## Modeled behavior
The modeled object is the cross-reference `make_xref(text)` builds for a single
annotation token `text`: its four data fields `(refdomain, reftype, reftarget,
text-label)`. Post-patch:

  * `refdomain = 'py'` always,
  * `reftarget = text`, visible label = `text` always,
  * `reftype = 'obj'` iff `text == 'None'`, else `'class'`.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_annotationRef` | `make_xref(text)` inner helper of `_parse_annotation` (sphinx/domains/python.py:73), i.e. the `pending_xref` node it returns, viewed as its `(refdomain, reftype, reftarget, label)` data |
| `problem_spec_annotationRef` | the post-condition that node's four fields must satisfy |
| `TypeRef` | the relevant data of the `pending_xref` node: `domain`=`refdomain`, `kind`=`reftype`, `target`=`reftarget`, `label`=the `nodes.Text(text)` child's text |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `text : List Char` | the token string `text` passed to `make_xref` | per-code-point sequence; `List Char` is total/sound |
| `TypeRef.domain : String` | `node['refdomain']` | always `"py"` |
| `TypeRef.kind : String` | `node['reftype']` | `"class"` / `"obj"` |
| `TypeRef.target : List Char` | `node['reftarget']` (a `str`) | per code point |
| `TypeRef.label : List Char` | text of the single `nodes.Text` child of the node | per code point |
| `text = "None".toList` | `text == 'None'` | exact string equality |

`List Char` ↔ Python `str` is the per-code-point bijection.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. `pending_xref(...)` is a node
  constructor: it stores the keyword arguments verbatim as node attributes and
  the positional `nodes.Text(text)` as its child. The four observed fields are
  exactly the literals/branch the helper passes, so there is no opaque callee
  behavior the proof must assume; building the node is modeled deeply (the
  `TypeRef` record). `axiom_check.py` is therefore a skip stub.
- No flag dependency: `make_xref`'s output depends only on `text`.

## G-CONF fuzz seed
- pinned seed: `7454`
- ≥10^5 fuzzed tokens, drawn to exercise the discriminating token `None` and its
  near-misses: the empty string, `None` itself, `none`/`NONE`/`Nonee`/`Non`
  (case + prefix/suffix variants), other common annotation tokens (`int`, `str`,
  `List`, `Optional`, `bool`), and random short alphanumeric/dotted tokens. Each
  token is checked against the REAL patched `make_xref` (imported from the live
  patched `sphinx.domains.python`) by comparing all four node fields.
