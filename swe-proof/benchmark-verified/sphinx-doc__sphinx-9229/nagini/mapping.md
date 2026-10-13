# mapping.md — sphinx-doc__sphinx-9229

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 876fa81e0a038cda466925b85ccf6c5452e0f685`, states the type
abstraction, and gives the provenance of each axiomatized callee.

Repo file under change: `sphinx/ext/autodoc/__init__.py`, class
`ClassDocumenter` (defined at line 1426).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_doc_block(is_attr_alias, comment, prepared)` | `ClassDocumenter.get_doc(self, ignore)` — `sphinx/ext/autodoc/__init__.py:1676` (alias branch, body line 1677-1679) | first modeled changed function: which documentation block the alias path selects |
| `alias_additional_content(is_attr_alias, comment, target, more_content)` | `ClassDocumenter.add_content(self, more_content, no_docstring)` — `sphinx/ext/autodoc/__init__.py:1724` (body line 1726-1730) | second modeled changed function: whether the synthetic placeholder line replaces the additional content |
| `has_authored_comment(comment)` | the truthiness test on `ClassDocumenter.get_variable_comment()`'s return — `if comment:` (new `get_doc`) / `not self.get_variable_comment()` (new `add_content`) | pure spec: the comment is present iff it is non-empty |
| `placeholder_seq(target)` *(axiom — A-consumed)* | `_('alias of %s') % restify(self.object)` — `restify` at `sphinx/util/typing.py:104`, wrapped in `StringList([...])` (`docutils.statemachine`) at `add_content` line 1728 | unchanged callee: the synthetic 'alias of <target>' line content |
| `make_placeholder(target)` *(axiom — A-consumed)* | the impl-callable face of the same `StringList([_('alias of %s') % restify(self.object)])` construction | unchanged callee, list-returning face used by the impl |
| `comment` (the `List[int]` input) | the value returned by the new `ClassDocumenter.get_variable_comment()` — `list(self.analyzer.attr_docs.get(key, []))` (new method, inserted before line 1724) | the authored attribute-comment lines as code points |

### The new helper `get_variable_comment` (modeled deeply, not axiomatized)
The patch adds `ClassDocumenter.get_variable_comment(self)`:
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
Its result is consumed by `get_doc` and `add_content` ONLY through its
truthiness (`if comment:` / `not self.get_variable_comment()`). The empty list
`[]` (key absent, returned by `attr_docs.get(key, [])`) and `None` (a parse
error, `PycodeError`) are BOTH falsy and BOTH drive the no-comment branch
identically. We therefore model its result as the `List[int]` parameter
`comment`, whose single discriminating property is `len(comment) > 0`
(`has_authored_comment`). The unchanged source-analysis machinery it calls —
`ModuleAnalyzer.for_module` (`sphinx/pycode/__init__.py:118`), `.analyze()`
(line 152), and the `attr_docs` mapping (line 161-166) — is upstream of this
parameter and is exercised end-to-end by G-RESOLVE on the real test module; it
does not need a separate axiom because the parameter already abstracts its
result.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `bool self.doc_as_attr` | `bool is_attr_alias` | identical |
| `Optional[List[str]]` returned by `get_variable_comment()` | `List[int]` `comment` (code points; empty ↔ no comment / parse error) | the only consumed property is truthiness: `bool(list-of-str)` ↔ `len(comment) > 0`. `None` and `[]` (both falsy) collapse to the empty-list case. |
| `Optional[List[List[str]]]` returned by `get_doc()` | `Optional[List[int]]` | the alias path produces only the three observable shapes: `None` (absent), `[]` (present-empty), and the unchanged prepared block (non-alias). `List[List[str]]` ↔ `List[int]`: `None` ↔ `None`; `[]` ↔ a present empty `List[int]`; the prepared docstrings ↔ the read-only `prepared` carrier. |
| `Optional[StringList] more_content` | `Optional[List[int]]` | the additional content lines as code points; `None` ↔ `None`. The pass-through is `is`-identity (the real code leaves the local untouched). |
| `'alias of %s' % restify(self.object)` (a `str`, always non-empty) | `placeholder_seq(target): PSeq[int]` / `make_placeholder(target): List[int]` | `str` ↔ code-point sequence; the defining property is `len > 0`. `target` ↔ `restify`'s `self.object` descriptor (read-only). |

`str` indexing/iteration is banned in Nagini, so character content is carried
as `List[int]` / `PSeq[int]` throughout.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `placeholder_seq` / `make_placeholder` ↔ `StringList([_('alias of %s') % restify(self.object)])` (A-consumed)
**Callee:** Sphinx's `restify` (`sphinx/util/typing.py:104`), composed with the
gettext wrapper `_('alias of %s') % …` and `StringList([...])`
(`docutils.statemachine`). This is the UNCHANGED line-formatting the alias path
emits when it does emit a placeholder; the patch does not touch it — it only
re-gates WHEN it runs.

**Axiom (the weakest the proof needs):** `placeholder_seq(target)` is the
content of that line, and its only consumed property is **non-emptiness**
(`len(Result()) > 0`): `'alias of %s' % restify(cls)` always contains the
literal prefix `'alias of '` (9 characters) plus a non-empty cross-reference for
the target, so the rendered line is never empty for any class/alias target.
`make_placeholder` is the list-returning face used by the impl, tied to
`placeholder_seq` by `ToSeq(Result()) == placeholder_seq(target)`. We do NOT pin
the exact placeholder text — the F2P test that exercises the change asserts the
placeholder is ABSENT, and the unchanged-text case is covered by the
PASS_TO_PASS `test_class_alias`; pinning the exact `restify` output would be an
over-claim (directive 7).

**Soundness check (G-AX):** `axiom_check.py` constructs `'alias of %s' % s` for
a boundary+fuzz family of target descriptors `s` (single chars, dotted module
paths, generics with brackets, empty target, long names) and asserts the
rendered line is always non-empty — exactly the axiom's `Ensures`. It imports
only the standard library; the formatting it reproduces is the gold patch's own
`'alias of %s' %` composition.

## 4. The discriminating behaviour

Both changed functions key on the same predicate `has_authored_comment(comment)`
(repo: the truthiness of `get_variable_comment()`):

- `select_doc_block` (get_doc): an alias **with** a comment selects a PRESENT
  EMPTY block (`return []`); an alias **without** a comment selects the ABSENT
  block (`return None`). Pre-patch always returned the ABSENT block.
- `alias_additional_content` (add_content): the placeholder is substituted for
  an alias **only without** a comment; **with** a comment the incoming content
  is left untouched. Pre-patch substituted for every alias.

The F2P test `test_class_alias_having_doccomment` documents `OtherAlias` (an
alias carrying the `#: docstring` comment) and asserts the rendered output is
the attribute directive with the `docstring` line and NO `alias of …` line —
i.e. the comment-present branch of BOTH functions. The PASS_TO_PASS
`test_class_alias` documents `Alias` (no comment) and asserts the `alias of …`
line is present — the comment-absent branch.
