# mapping.md — sphinx-doc__sphinx-9229

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 876fa81e0a038cda466925b85ccf6c5452e0f685`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `sphinx/ext/autodoc/__init__.py` (the `ClassDocumenter`
class, `DocstringSignatureMixin, ModuleLevelDocumenter`, line 1426).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `aliasDocstrings (isAlias, varComment, normalDoc)` *(method)* | `ClassDocumenter.get_doc`, the `if self.doc_as_attr:` block — `sphinx/ext/autodoc/__init__.py:1675` (the `return None` at `:1679`) | modeled changed function #1: which docstring container an alias entry exposes |
| `aliasContentOverride (isAlias, varComment, incoming, aliasLabel)` *(method)* | `ClassDocumenter.add_content`, the `if self.doc_as_attr:` guard — `sphinx/ext/autodoc/__init__.py:1724` (guard at `:1726`) | modeled changed function #2: whether an alias entry's content is overridden with the alias label |
| `commentPresent (varComment)` *(pure, deep model)* | `bool(self.get_variable_comment())` — the truthiness of the helper the patch ADDS at `sphinx/ext/autodoc/__init__.py:1728` (post-patch) | pure spec: whether a doc-comment is attached to the alias name |
| `docForAlias (...)` *(pure, deep model)* | the post-patch `get_doc` alias branch: `comment = self.get_variable_comment(); return [] if comment else None` | pure spec: the docstring container for an alias entry |
| `contentForAlias (...)` *(pure, deep model)* | the post-patch `add_content` guard `if self.doc_as_attr and not self.get_variable_comment():` choosing the `alias of %s` override vs. the unchanged `more_content` | pure spec: the content forwarded for an alias entry |

`varComment : Option (List String)` is the result of the added
`get_variable_comment` helper (its callees — `self.objpath`,
`ModuleAnalyzer.for_module(self.get_real_modname())`, `analyzer.analyze()`,
`self.analyzer.attr_docs.get(key, [])`, and the `PycodeError` guard — are
UNCHANGED repo machinery; they are abstracted to the helper's optional-list
result, an R-refinement, §2/§3). `normalDoc : Option (List (List String))` is the
documentation the ordinary (non-`doc_as_attr`) `get_doc` path produces, also
UNCHANGED (R). `aliasLabel : List String` is the `[_('alias of %s') %
restify(self.object)]` line built by the unchanged label machinery (R).

Pre-patch repo behaviour the change replaces (refinement audit only, not in the
consumer spec view): `get_doc`'s alias branch returned `None` unconditionally
(`:1679`); `add_content`'s guard was `if self.doc_as_attr:` with no doc-comment
exception (`:1726`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.doc_as_attr` — whether the entry is documented as an alias | `isAlias : Bool` | truthy `doc_as_attr` ↔ `true`; falsy ↔ `false`. |
| `self.get_variable_comment()` — `Optional[List[str]]` doc-comment lookup | `varComment : Option (List String)` | `None` (analysis failed / `PycodeError`) ↔ `none`; `list(...)` of comment lines ↔ `some [l₀, l₁, …]`; each line `str` ↔ `String`. The lookup returns `[]` when the source analysed but the name has no attached comment — `some []`. |
| `bool(self.get_variable_comment())` — the truthiness used at both sites | `commentPresent varComment` | `None`/`[]` → falsy ↔ `false`; a non-empty list → truthy ↔ `true`. Models Python list truthiness exactly: empty ⇒ false, non-empty ⇒ true; `None` ⇒ false. |
| `get_doc()` return `Optional[List[List[str]]]` | `out : Option (List (List String))` | `None` ↔ `none`; `[]` (empty docstring container) ↔ `some []`; `[[…lines…], …]` ↔ `some [[…], …]`. The `None` vs `[]` distinction is observable downstream (`add_content` skips event firing on `None`, fires it on `[]`). |
| the documentation the non-alias `get_doc` path returns | `normalDoc : Option (List (List String))` | identity on the carrier; the alias change never touches this path (R). |
| `more_content` `StringList` forwarded by `add_content` (the incoming content) | `incoming : List String` | the sequence of content lines ↔ `List String`; `StringList` order/content preserved. |
| `StringList([_('alias of %s') % restify(self.object)])` — the rendered alias label | `aliasLabel : List String` | the one-line label ↔ a `List String` (single element); content identity, the label text is unchanged by the fix (R). |

The doc-comment is modeled as `Option (List String)` (not just `Bool`) so that
"could not analyse" (`none`) and "analysed, empty" (`some []`) are genuinely
distinct inputs that the spec must nonetheless treat identically for the
decision; `commentPresent` collapses them. The `get_doc` result is
`Option (List (List String))` because the observable distinction the fix
introduces is `some []` vs `none` — an empty container vs no container.

## 3. Callee provenance & flag dependencies

### 3.1 `commentPresent` / the `get_variable_comment` truthiness (deep model, R — NOT an axiom)
**Callee:** the helper the patch adds:
```python
def get_variable_comment(self) -> Optional[List[str]]:
    try:
        key = ('', '.'.join(self.objpath))
        analyzer = ModuleAnalyzer.for_module(self.get_real_modname())
        analyzer.analyze()
        return list(self.analyzer.attr_docs.get(key, []))
    except PycodeError:
        return None
```
Its observable result is an `Optional[List[str]]`; both decision sites consume
only its **truthiness** (`if comment:` in `get_doc`; `not self.get_variable_comment()`
in `add_content`). Modeled DEEPLY as the input `varComment : Option (List String)`
and `commentPresent varComment = (varComment is a non-empty list)`. The helper's
own callees (`objpath`, `ModuleAnalyzer.for_module`, `analyze`, `attr_docs`,
`PycodeError`) are UNCHANGED machinery and are abstracted to the optional-list
result — an R refinement (§2). There is **no consumed axiom**: the truthiness is
spelled out and G-CONF validates the whole decision against the real patched
`get_doc` / `add_content` driving the real `get_variable_comment`.

**No flag dependency** beyond `doc_as_attr` (`isAlias`): both sites gate first on
`doc_as_attr`, then on the doc-comment truthiness. G-CONF fuzzes all four
`(isAlias, comment∈{none,[],non-empty})` configurations.

### 3.2 `docForAlias` / `contentForAlias` deep models ↔ the two changed branches (deep model, R/I)
**Callees:** the changed `get_doc` alias branch and the changed `add_content`
guard (gold hunks in patch.diff). `docForAlias` models `return [] if comment else
None` (only on the `doc_as_attr` branch; otherwise the unchanged `normalDoc`
path); `contentForAlias` models `if self.doc_as_attr and not comment: more_content
= alias_label else: more_content` (the `try/except AttributeError` around the
label *construction* is orthogonal control flow that does not change which
content is chosen when the label is constructible — the F2P case constructs it
fine — so it is not modeled; mapping treats the alias-label branch as producing
`aliasLabel`). Modeled deeply (R/I), not behind an axiom about the functions
under change.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9229`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`commentPresent`/`docForAlias`/`contentForAlias` to Python and exercises both
decisions against the REAL gold-patched `ClassDocumenter.get_doc` and
`ClassDocumenter.add_content`, driven by a duck-typed documenter whose
`get_variable_comment` returns the case's optional comment, over boundary +
fuzzed `(isAlias, comment, normalDoc, incoming, aliasLabel)` configurations.
