# refinement.md — sphinx-doc__sphinx-9229

Operation-by-operation correspondence between `Solution.lean`'s impl regions (the
`aliasDocstrings` / `aliasContentOverride` `do` blocks and the deep
`commentPresent` / `docForAlias` / `contentForAlias` models) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — A-consumed / A-reference), or **I** (identical concrete op). EVERY step
is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1, run in-container with the gold patch applied); the narrative is audited by
**G-EQ**. There are **no A-tagged ops** (no axioms, no deep-model references): the
changed behaviour calls only the added helper `get_variable_comment` (observed by
its optional-list result) and unchanged label/docstring machinery, all modeled
deeply as closed functions of the inputs.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The docstring-container site — `ClassDocumenter.get_doc` (`sphinx/ext/autodoc/__init__.py`, the `doc_as_attr` branch)

Gold hunk:
```
     def get_doc(self, ignore: int = None) -> Optional[List[List[str]]]:
         if self.doc_as_attr:
             # Don't show the docstring of the class when it is an alias.
-            return None
+            comment = self.get_variable_comment()
+            if comment:
+                return []
+            else:
+                return None
```

| # | Solution.lean impl op (`aliasDocstrings`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `isAlias : Bool` | `self.doc_as_attr` | R | alias flag ↔ `Bool` (mapping.md §2). G-CONF sets `fake.doc_as_attr`. |
| A2 | param `varComment : Option (List String)` | `comment = self.get_variable_comment()` | R | `Optional[List[str]]` ↔ `Option (List String)`; `None`↔`none`, `list`↔`some` (mapping.md §2, §3.1). G-CONF overrides the real `get_variable_comment`. |
| A3 | param `normalDoc : Option (List (List String))` | the unchanged non-`doc_as_attr` `get_doc` body (returns `Optional[List[List[str]]]`) | R | the alias change never touches this path; carried as the input value (identity refinement). |
| A4 | `if commentPresent varComment then some [] else none` (= `docForAlias true ...`) | `if comment: return [] else: return None` | I (deep model of the changed branch) | `commentPresent = (varComment is a non-empty list)` models `if comment:` (Python list/None truthiness, mapping.md §2); `some []`↔`[]`, `none`↔`None`. NOT a consumed axiom — G-CONF validates against the real patched `get_doc`. |
| A5 | `else return normalDoc` | the fall-through to the rest of `get_doc` (non-alias path) | I (R-identity) | when not an alias, the result is exactly the ordinary documentation, unchanged by the fix. |

Pinned exactly by the post-conditions: `out = docForAlias ...` AND the two
guarded clauses `(isAlias ∧ commentPresent) → out = some []`,
`(isAlias ∧ ¬commentPresent) → out = none`. No impl that returns `none` for an
alias carrying a comment (the issue's complaint — the docstring ignored), or
`some []` for an alias with no comment, can satisfy it.

## B. The content-override site — `ClassDocumenter.add_content` (the `doc_as_attr` guard)

Gold hunk:
```
     def add_content(self, more_content: Optional[StringList], no_docstring: bool = False
                     ) -> None:
-        if self.doc_as_attr:
+        if self.doc_as_attr and not self.get_variable_comment():
             try:
                 more_content = StringList([_('alias of %s') % restify(self.object)], source='')
             except AttributeError:
                 pass  # Invalid class object is passed.
```

| # | Solution.lean impl op (`aliasContentOverride`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `isAlias : Bool`, `varComment : Option (List String)` | `self.doc_as_attr`, `self.get_variable_comment()` | R | as A1/A2 (mapping.md §2). |
| B2 | param `incoming : List String` | the inbound `more_content` `StringList` | R | content lines ↔ `List String` (mapping.md §2). G-CONF passes a real `StringList(incoming)`. |
| B3 | param `aliasLabel : List String` | `[_('alias of %s') % restify(self.object)]` | R | the one-line rendered label ↔ a singleton `List String`; the label text is unchanged by the fix (mapping.md §2). G-CONF mirrors the exact label. |
| B4 | `if isAlias && !commentPresent varComment then aliasLabel else incoming` (= `contentForAlias ...`) | `if self.doc_as_attr and not self.get_variable_comment(): more_content = StringList([label]) ` ; else forward `more_content` | I (deep model of the changed guard) | the guard `doc_as_attr and not comment` ↔ `isAlias && !commentPresent`; override ↔ choosing `aliasLabel`, no override ↔ forwarding `incoming`. NOT a consumed axiom — G-CONF captures the `super().add_content` forwarded content. The `try/except AttributeError` around label *construction* is orthogonal control flow that does not alter which content is chosen when the label is constructible (the F2P case constructs it); not modeled (mapping.md §3.2). |

Pinned exactly by the post-conditions: `out = contentForAlias ...` AND
`(isAlias ∧ commentPresent) → out = incoming`,
`(isAlias ∧ ¬commentPresent) → out = aliasLabel`. No impl that overrides an
alias-with-comment's content with the label (the issue's complaint — only the
"alias of …" text shown) can satisfy it.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operations that genuinely *changed* — making both the
docstring container and the content override conditional on the presence of a
doc-comment, and the added `get_variable_comment` helper — are modeled **deeply**
(`docForAlias`/`contentForAlias`/`commentPresent`), not behind an axiom about the
functions under change. There is **no axiomatized callee** (G-AX skipped;
`meta.json axioms = []`, `deep_model_references = []`): `get_variable_comment` is
the helper the patch ADDS (observed by its optional-list result, an R
refinement — not a pre-existing callee with a contract to consume), and the
docstring/label/`StringList` machinery is unchanged and carried as inputs (R).

## D. Two independently-fixed behaviours ⇒ two prepatches

The fix changes two separately-observable behaviours, each with its own failing
prepatch (G-DIFF), both keeping the spec byte-identical (`same_spec`):

- `Solution_prepatch_1.lean` — `aliasDocstrings` always returns `none` for an
  alias (the pre-patch `get_doc` `return None`). Fails the clause
  `(isAlias ∧ commentPresent) → out = some []`: when a comment is present,
  `none ≠ some []`. This is the docstring-ignored half of the issue.
- `Solution_prepatch_2.lean` — `aliasContentOverride` always overrides an
  alias's content with the label (the pre-patch `add_content` guard `if
  self.doc_as_attr:`). Fails the clause `(isAlias ∧ commentPresent) → out =
  incoming`: when a comment is present, `aliasLabel ≠ incoming`. This is the
  "only alias-of text shown" half.

## E. verify(Solution) ⇒ resolved

`aliasDocstrings` / `aliasContentOverride` verify only if their outputs are
`docForAlias` / `contentForAlias` (A4/B4): an alias-with-comment exposes the
empty container `some []` and keeps its incoming content; an alias-without-comment
exposes `none` and is overridden with the label; a non-alias is untouched. By R
(`doc_as_attr`/`get_variable_comment` ↔ the inputs; `StringList`/docstring
containers ↔ `List`/`Option` carriers) the verified methods equal the patched
`ClassDocumenter.get_doc`/`add_content` on every configuration. By G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs against the
REAL patched code driving the real `get_variable_comment` truthiness (and the
prepatch skeletons diverge exactly at "comment present", confirming
discrimination). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc + G-CONF);
there is no axiom-soundness trust point (no axioms).
