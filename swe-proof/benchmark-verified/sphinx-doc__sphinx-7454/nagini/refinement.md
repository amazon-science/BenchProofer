# refinement.md — sphinx-doc__sphinx-7454

The operation-by-operation correspondence between `model.py`'s implementation
(the `make_cross_reference` impl region, with the deep `kind_for` classifier and
the `name_value` / `tag_value` / `tag_type` code-point constants) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`Ensures`, **A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — the `make_xref` helper inside `_parse_annotation` (`sphinx/domains/python.py:73-77`)

Gold hunk:
```
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

| # | model.py impl op (`make_cross_reference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text: List[int]` | `text: str` argument of `make_xref` | R | `str` ↔ `List[int]` of Unicode code points (mapping.md §2). |
| A2 | `ref = CrossReference()`; building `ref.target` by copying `text` element-by-element, `ref.target == text` | `pending_xref('', nodes.Text(text), refdomain='py', …, reftarget=text)` constructs the cross-reference node carrying `text` as both its display text and its `reftarget` | R | the `pending_xref` constructor and the fixed `refdomain='py'` are UNCHANGED by the patch; only the two touched fields (`reftype`, `reftarget`) are modeled. `reftarget=text` ↔ `ToSeq(ref.target) == ToSeq(text)`; the carry-through copy is the identity on code points (mapping.md §2). |
| A3 | `if ToSeq(text) == name_value(): ref.kind = [111,98,106]  # 'obj'` `else: ref.kind = [99,108,97,115,115]  # 'class'` | `if text == 'None': reftype = 'obj'  else: reftype = 'class'`; then `reftype=reftype` | I + R | the conditional and the two constant tags are the **changed operation, modeled deeply**: the `kind_for` classifier (pure region) IS the `text == 'None'` test under the string↔`List[int]` refinement (R), and the assigned tags `'obj'`/`'class'` are the verbatim code-point constants `tag_value()` / `tag_type()` (I on the literal values, R on the carrier). The string comparison `text == 'None'` ↔ `ToSeq(text) == name_value()` is the code-point-sequence equality (R). |

No callee is axiomatized: the cross-reference constructor and `refdomain='py'`
are unchanged context, not part of the classified behaviour; the classification
itself (the only thing that changed) is spelled out deeply in `kind_for`.

## B. The discriminating clause (G-DIFF)

The behavioural change is `reftype` for the name `'None'`: it must be the VALUE
tag `'obj'` (`tag_value() == PSeq(111,98,106)`) instead of the TYPE tag
`'class'` (`tag_type() == PSeq(99,108,97,115,115)`). The model pins this in two
redundant forms:

```
Ensures(ToSeq(Result().kind) == kind_for(ToSeq(text)))
Ensures(Implies(ToSeq(text) == name_value(), ToSeq(Result().kind) == tag_value()))
Ensures(Implies(ToSeq(text) != name_value(), ToSeq(Result().kind) == tag_type()))
```

`model_prepatch.py` reproduces the pre-patch skeleton — every name classified as
`'class'` (`ref.kind = [99,108,97,115,115]`, the old unconditional
`reftype='class'`) — and **fails** the postcondition
`ToSeq(Result().kind) == kind_for(ToSeq(text))` (which equals `tag_value()` when
`text == 'None'`). That is exactly the spec sensing the change (G-DIFF), and it
matches the F2P assertion `assert_node(doctree[0], pending_xref, …,
reftype="obj", reftarget="None")` that the pre-patch fails.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or R+I. The one operation that genuinely *changed* —
the `reftype` classification of a single name — is modeled **deeply** (the
spelled-out `kind_for` classifier and the verbatim code-point tags), not hidden
behind an axiom. There are **no** consumed axioms and **no** A-reference deep
models against an external callee: the change is pure in-function structure
logic over the input text, with no library callee mediating the classified
behaviour. (The `pending_xref` / `nodes.Text` constructors are unchanged context
referenced only as the carrier of the two touched fields — refinement R, step
A2 — not callees whose behaviour the patch alters.)

## D. verify(model) ⇒ resolved

`make_cross_reference` verifies only if (i) its target equals the input text
(A2) and (ii) its kind is `tag_value()` exactly when the text is `name_value()`
and `tag_type()` otherwise (A3, clause B). By R (`str` ↔ `List[int]`; the
unchanged `pending_xref` constructor and `refdomain='py'`), the verified
classifier equals the gold `make_xref` on every annotation-name string: for
`text == 'None'` it yields `reftype='obj'`, for every other name `reftype='class'`,
with `reftarget=text` throughout. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). There are no trust points beyond refinement fidelity
(this document, G-EQ): no axiom soundness obligation arises because no callee is
axiomatized.
