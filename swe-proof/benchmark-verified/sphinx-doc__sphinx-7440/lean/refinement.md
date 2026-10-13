# refinement.md — sphinx-doc__sphinx-7440

Every op in each `implementation_<name>` mapped to its `patch.diff` counterpart.
Tags: **R** (type-only refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

There are NO A-consumed axioms and NO A-reference deep models in this bundle:
both impls pass the term/reference text through unchanged (the changed behavior
is exactly the removal of a case fold). Every row is R or I. `meta.json
conf_skip = false` (the impl region is NOT all-A-tagged).

## implementation_glossaryTermEntry  ↔  `sphinx/domains/std.py` make_glossary_term

patch.diff hunk 1:
```python
     std = cast(StandardDomain, env.get_domain('std'))
-    std.note_object('term', termtext.lower(), node_id, location=term)
+    std.note_object('term', termtext, node_id, location=term)
```
(The index entry built a few lines below already uses the un-folded `termtext`:
`indexnode['entries'] = [('single', termtext, node_id, 'main', index_key)]` —
unchanged by the patch.)

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `termtext` parameter | `termtext = term.astext()` | R | the term's text; Python `str` per code point ↔ `List Char` |
| `let key := termtext` | `note_object('term', termtext, …)` key arg | R | identity pass-through; was `termtext.lower()` pre-patch (the bug) |
| `let indexTerm := termtext` | `('single', termtext, …)` index entry term | I | unchanged frame component; the index entry already used the un-folded text |
| `return (key, indexTerm)` | the two term-derived values produced for this term | R | the pair models the two observable term-derived strings (mapping.md) |

## implementation_termXrefTarget  ↔  the `'term'` cross-reference role

patch.diff hunk 2:
```python
-        'term':    XRefRole(lowercase=True, innernodeclass=nodes.inline,
+        'term':    XRefRole(innernodeclass=nodes.inline,
                             warn_dangling=True),
```
The role's case-folding flag governs `XRefRole.create_xref_node`
(`sphinx/roles.py:146-147`):
```python
        if self.lowercase:
            target = target.lower()
```
Dropping `lowercase=True` leaves the flag falsey for the `'term'` role, so the
target is used as written.

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `target` parameter | `target = self.target` | R | the reference text; `str` per code point ↔ `List Char` |
| `return target` | `target` with the `if self.lowercase` fold disabled | R | identity pass-through; was `target.lower()` when the flag was set (the bug) |

## Frame discipline (SPEC_GUIDE §0.5)
- `glossaryTermEntry`: BOTH output components are pinned to `termtext` —
  `result.1 = termtext` (the changed registration key) AND `result.2 = termtext`
  (the unchanged index entry term). Pinning the index component too is what makes
  the spec require the key to MATCH it; a wrong impl cannot lowercase the key and
  still satisfy `result.1 = termtext`.
- `termXrefTarget`: the single output is pinned to `target`; no component is left
  unconstrained.

## G-DIFF: one failing prepatch per independently-fixed behavior
- `Solution_prepatch.lean`: pre-patch `glossaryTermEntry` sets
  `key := termtext.map Char.toLower`, so on a mixed-case term (e.g. `TERM2`) the
  key is `term2 ≠ TERM2`, contradicting `result.1 = termtext`. Unprovable.
- `Solution_prepatch_2.lean`: pre-patch `termXrefTarget` returns
  `target.map Char.toLower`, so on `TERM2` the lookup target is `term2 ≠ TERM2`,
  contradicting `result = target`. Unprovable.
