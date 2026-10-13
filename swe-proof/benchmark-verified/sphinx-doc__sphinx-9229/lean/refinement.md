# refinement.md — sphinx-doc__sphinx-9229

Every op in each `implementation_<name>` mapped to its `patch.diff` counterpart.
Tags: **R** (type-only refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

There are NO A-consumed axioms and NO A-reference deep models in this bundle:
both impls are pure control flow over abstract inputs. Every row is R or I.
`meta.json conf_skip = false` (the impl region is NOT all-A-tagged).

## implementation_getDoc  ↔  ClassDocumenter.get_doc (post-patch alias branch)

patch.diff hunk 1:
```python
 if self.doc_as_attr:
-    return None
+    comment = self.get_variable_comment()
+    if comment:
+        return []
+    else:
+        return None
 ... (unchanged ordinary docstring path) ...
```

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `if docAsAttr then …` | `if self.doc_as_attr:` | I | same branch guard |
| `comment` parameter | `comment = self.get_variable_comment()` | R | the helper's result is an abstract input modeled as `Option (List String)` (mapping.md). The branch consumes only its truthiness; the lookup itself is environment-supplied, not part of the fix. |
| `if commentPresent comment then return some []` | `if comment: return []` | R | Python list/None truthiness ↔ `commentPresent`; `[]` (empty doc block) ↔ `some []` |
| `else return none` | `else: return None` | R | `None ↔ none` |
| `return normalDoc` (fallthrough) | unchanged ordinary path return | R | the whole non-alias path collapsed to its abstract result `normalDoc : Option (List (List String))`; pinned to input by the `docAsAttr = false → result = normalDoc` frame conjunct |

## implementation_addContent  ↔  ClassDocumenter.add_content

patch.diff hunk 2:
```python
 def add_content(self, more_content, no_docstring=False):
-    if self.doc_as_attr:
+    if self.doc_as_attr and not self.get_variable_comment():
         try:
             more_content = StringList([_('alias of %s') % restify(self.object)], source='')
         ...
     super().add_content(more_content)
```

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `if docAsAttr && (! commentPresent comment)` | `if self.doc_as_attr and not self.get_variable_comment():` | R | `and not <truthiness>` ↔ `&& ! commentPresent`; same abstract `comment` input as get_doc |
| `return some ["alias of " ++ aliasText]` | `more_content = StringList([_('alias of %s') % restify(self.object)])` | R | the StringList carrying one line ↔ `some [..]`; `restify(self.object)` ↔ `aliasText`; `_('alias of %s') % x` ↔ `"alias of " ++ x` (the gettext id is the identity format here) |
| `return incoming` (fallthrough) | `super().add_content(more_content)` with `more_content` unchanged | R | the forwarded content equals the caller-supplied `incoming` when the guard is false; pinned by the frame conjunct |

## Frame discipline (SPEC_GUIDE §0.5)
- `getDoc`: when `docAsAttr = false` the result is pinned to `normalDoc` (the
  unchanged ordinary path), so a wrong impl cannot fill the non-alias result.
- `addContent`: when the alias-without-comment guard is false the result is
  pinned to `incoming` (unchanged caller content), closing the
  "leave-output-unconstrained" hole.

## G-DIFF: one failing prepatch per independently-fixed behavior
- `Solution_prepatch.lean`: pre-patch `get_doc` (`if docAsAttr then return none`
  — the original `return None`), so `commentPresent comment = true` no longer
  yields `some []`. Unprovable on the `docAsAttr ∧ commentPresent → result =
  some []` clause.
- `Solution_prepatch_2.lean`: pre-patch `add_content` (`if docAsAttr then return
  some [..]` — the original guard without `and not get_variable_comment()`), so
  the alias line is emitted even when a comment is present. Unprovable on the
  `(docAsAttr=false ∨ commentPresent=true) → result = incoming` clause (the
  `commentPresent=true` half).
