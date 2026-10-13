# refinement.md — sphinx-doc__sphinx-8638

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderFieldEntry` `do` block, routed through the deep `crossRefOrText` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete op). EVERY
step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg + this narrative are audited by **G-AX**/**G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The variable-field rendering site — `PyTypedField('variable', …)`

Gold hunk (`sphinx/domains/python.py:357`):
```
-        PyTypedField('variable', label=_('Variables'), rolename='obj',
+        PyTypedField('variable', label=_('Variables'),
                      names=('var', 'ivar', 'cvar'),
                      typerolename='class', typenames=('vartype',),
                      can_collapse=True),
```

Effect: the `'variable'` field's `rolename` goes from `'obj'` to `None` (the
default). When the field's one entry is rendered (`TypedField.make_field` →
`handle_item`, `sphinx/util/docfields.py:166-186`), the argument NAME is built by
`make_xrefs(self.rolename, …)`. With `rolename=None`, `Field.make_xref`'s
`if not rolename:` branch fires and the NAME becomes a plain inline node
(`literal_strong` text) instead of a `pending_xref`. The TYPE is built by
`make_xrefs(self.typerolename='class', …)` and is UNCHANGED — still a
`pending_xref` of `reftype='class'`.

| # | Solution.lean impl op (`renderFieldEntry`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name : List Char` (with `require`: non-empty, `isIdentChar`-only) | the variable field argument NAME string (e.g. `"attr"`) | R | `str` ↔ `List Char` (mapping.md §2); the `require` clauses pin the modeled domain to one-word identifiers (mapping.md §2, "Modeled input domain"). |
| A2 | parameter `typ : List Char` (with `require`: non-empty, `isIdentChar`-only, `≠ "None"`) | the variable field TYPE string (e.g. `"int"`) | R | `str` ↔ `List Char` (mapping.md §2); the domain excludes the UNCHANGED `'None'`→`obj`-role special case, `'.'`/`'~'` prefix stripping, and multi-node delimiter splitting — all orthogonal to the gold hunk (mapping.md §2, "Modeled input domain"). |
| A3 | `nameRole : Option (List Char) := none` | the field's `rolename`, now `None` after the hunk removes `rolename='obj'` | R + I | post-patch `rolename` is `None` ↔ `none` (mapping.md §2). This is the **single changed value** the patch produces. |
| A4 | `typeRole : Option (List Char) := some "class".toList` | the field's UNCHANGED `typerolename='class'` | R + I | `'class'` ↔ `some "class".toList` (mapping.md §2). |
| A5 | `nameNode := crossRefOrText nameRole name` ⇒ `RefNode.text name` | `make_xrefs(rolename=None, …)` ⇒ plain `literal_strong` text node (no `pending_xref`) | A-reference + I | the unchanged rendering rule `Field.make_xref` is modeled **deeply** by `crossRefOrText`; the decision op (`match`/`if r = []`) is **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `make_xref` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A6 | `typeNode := crossRefOrText typeRole typ` ⇒ `RefNode.xref "class" typ` | `make_xrefs(typerolename='class', …)` ⇒ `pending_xref` of `reftype='class'` to the type | A-reference + I | same deep model; TYPE keeps its class cross-reference (unchanged). Pins that the patch does NOT also strip the type link — the F2P test asserts the type IS a `pending_xref`. |

Discriminating content of the change — the NAME node is plain text, NOT a
cross-reference — lives in `out.nameNode = RefNode.text name` (post-patch
`rolename=None`) ⇔ the removed `rolename='obj'`. `Solution_prepatch.lean`
reproduces the pre-patch `rolename='obj'` and **fails** `out.nameNode =
RefNode.text name` (the goal reduces to `False`; G-DIFF). The TYPE clause
`out.typeNode = RefNode.xref "class".toList typ` holds in both, so the prepatch
fails ONLY on the name clause — the exact observable the F2P test
`test_info_field_list_var` checks (`literal_strong "attr"` plain, `int` a
`pending_xref` of `reftype="class"`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one thing that genuinely *changed* — the role
passed for the variable NAME, hence whether the NAME becomes a cross-reference —
is modeled **deeply** (the spelled-out `crossRefOrText` decision, steps A3/A5, an
A-reference + I), not hidden behind an axiom about the function under change.
There are no consumed axioms; the only deep-model reference, `crossRefOrText`,
models the **unchanged** helper `Field.make_xref` and is G-AX-validated.

## C. verify(Solution) ⇒ resolved

`renderFieldEntry` verifies only if the NAME node is plain `text` (A5, the change)
and the TYPE node is a `class` `xref` (A6, the preserved behaviour). By R
(`str ↔ List Char`, role ↔ `Option`) the verified rendering equals what the
patched Sphrender of a `:var TYPE NAME:` field produces; by G-AX the deep model
`crossRefOrText` equals the real `Field.make_xref` node-shape (A-reference); by
G-CONF the R/I transliteration agrees with `patch.diff`'s rendering on the fuzzed
input space. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited callee — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
