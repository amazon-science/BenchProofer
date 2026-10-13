# refinement.md — sphinx-doc__sphinx-9591

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `propertyTypeNodes` `do` block + the deep `annotationNodes` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/deeply-modeled callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A leg and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The property type-annotation site — `PyProperty.handle_signature` (`sphinx/domains/python.py:859`)

Gold hunk (the `if typ:` branch):
```
-            signode += addnodes.desc_annotation(typ, ': ' + typ)
+            annotations = _parse_annotation(typ, self.env)
+            signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)
```

The modeled quantity `out` is the **child sequence** of the appended
`desc_annotation` node — exactly what the F2P test reads
(`[desc_annotation, (": ", [pending_xref, "str"])]`).

| # | Solution.lean impl op (`propertyTypeNodes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `typ : List Char`, `require isBareName typ` | `typ = self.options.get('type')`, the `if typ:` guard | R | `str` ↔ `List Char` (mapping.md §2). The precondition restricts to a single (possibly dotted) type name — the domain on which the deep model is exact and the F2P case (`str`) lives. |
| A2 | `let annotations := annotationNodes typ` | `annotations = _parse_annotation(typ, self.env)` | A-reference | the UNCHANGED callee `_parse_annotation` is modeled **deeply**: on a bare name it returns one cross-reference node, `annotationNodes typ = [DocNode.xref typ]`. No consumed axiom; the equality of this deep model to the real callee is the A-reference G-AX validates (mapping.md §3.1). |
| A3 | `DocNode.text ": ".toList :: annotations` (cons the literal node, then the parsed nodes), returned as `out` | `addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)` | I + R | **I**: the child list is `Text(': ')` followed by the unpacked `annotations` — identical construction (the `''` auto-text arg contributes no child; mapping.md §2). **R**: the wrapping `desc_annotation` is identity over its children for what the test observes; `out` IS that child list. Transliterated and diff-tested by G-CONF. |

Discriminating content of the change — a documented type renders as a
**cross-reference node** (`DocNode.xref typ`) inside a separate-literal layout,
NOT as one inert text node `": " ++ typ`. The pre-patch built
`desc_annotation(typ, ': ' + typ)` = a single `text` node; `Solution_prepatch.lean`
reproduces exactly that (`[DocNode.text (": ".toList ++ typ)]`) and **fails** the
postcondition `out = DocNode.text ": ".toList :: annotationNodes typ` (G-DIFF) —
the clause forces both the split literal node and the `xref` node.

## B. No second site

The gold patch is a single hunk in one function; there is no second
independently-fixed behavior, hence one `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — routing the
property's type string through the annotation parser so the type name becomes a
cross-reference — is captured by the **I** layout op (A3) plus the **A-reference**
deep model of the unchanged callee `_parse_annotation` (A2). There is no consumed
axiom about the function under change (`PyProperty.handle_signature` is the
function under spec, never axiomatized) and no op Velvet cannot express.

## D. verify(Solution) ⇒ resolved

`propertyTypeNodes` verifies only if `out` is the split layout
`text ": " :: annotationNodes typ` with `annotationNodes typ = [xref typ]` (A2,
A3) — i.e. a separate literal node followed by a cross-reference node. By R
(`str ↔ List Char`; `desc_annotation` identity over children) the verified output
equals the patched `desc_annotation(typ, '', Text(': '), *_parse_annotation(typ,
env))`'s children on the tested bare-name inputs; by G-AX the deep model
`annotationNodes` equals the real `_parse_annotation` on the spec domain
(A-reference); by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited callee — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: callee-model soundness (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).
