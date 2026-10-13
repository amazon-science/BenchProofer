# mapping.md — sphinx-doc__sphinx-8593

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 07983a5a8704ad91ae855218ecbda1c8598200ca`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo files under change:
`sphinx/ext/autodoc/__init__.py` and `sphinx/ext/autodoc/importer.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `member_effective_doc(attr_doc, value_doc)` | the documentation a module member carries for the visibility decision: post-patch the new `ModuleDocumenter.get_module_members()` attaches `docstring="\n".join(attr_docs.get(('', name), []))` to each `ObjectMember` (gold hunk on `sphinx/ext/autodoc/__init__.py`, new method around line 1046); `filter_members` then prefers that attached docstring (`if isinstance(obj, ObjectMember) and obj.docstring: doc = obj.docstring`, `sphinx/ext/autodoc/__init__.py:725-727`) over the value's intrinsic `getdoc(member)` (`__init__.py:711`) | modeled changed behaviour (1): the effective documentation of a module member |
| `keep_module_member(name_underscored, attr_doc, value_doc, want_all, private_mode, name_selected)` | the retention decision for a documented module member in `Documenter.filter_members` (`sphinx/ext/autodoc/__init__.py:662`): the `metadata = extract_metadata(doc)` / `isprivate` classification (`__init__.py:731-739`) and the documented-attribute keep branch (`(namespace, membername) in attr_docs`, `__init__.py:759-768`) | modeled changed behaviour (2): whether a documented module member is kept, given its effective documentation |
| `meta_class(doc)` *(axiom — A-consumed)* | `sphinx.util.docstrings.extract_metadata` (`sphinx/util/docstrings.py:23`) + the public/private branch reading it (`sphinx/ext/autodoc/__init__.py:731-737`) | unchanged community callee classifying a documentation block's explicit visibility marker |
| `effective_doc(attr_doc, value_doc)` | the attribute-doc-preferred-over-intrinsic-doc choice (`__init__.py:711` vs `725-727`) | pure spec: the effective documentation function |
| `is_private(name_underscored, doc)` | the `isprivate` computation (`__init__.py:732-739`) | pure spec: visibility classification of a member |
| `in_private_selection(mode, selected)` | the private-members selection (`__init__.py:761-764`): `private_members is None` (mode 0), `ALL` / `membername in ALL` (mode 1), explicit list / `membername in private_members` (mode 2) | pure spec: whether a private member is selected for retention |

The pre-patch repo symbols the change supersedes (for the refinement audit, not
referenced from the consumer spec view): the module-level
`sphinx.ext.autodoc.importer.get_module_members(module)` (`importer.py:140`,
returning bare `(name, value)` tuples with NO docstring) — the source the
pre-patch `ModuleDocumenter.get_object_members` called (`__init__.py:1048`,
`members = get_module_members(self.object)`). Because those tuples carried no
docstring, `filter_members` fell back to the value's intrinsic documentation
(empty for a plain data constant), never seeing the inline `:meta public:` /
`:meta private:` attribute documentation.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` documentation block (`doc`, `obj.docstring`, the joined `attr_docs` lines) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; empty `str`/`None`-as-empty ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list; `PSeq` `len`/`[i]` mirror `str` `len`/index |
| `attr_docs.get(('', name), [])` joined by `"\n"` (the inline attribute documentation), `__init__.py:1046` new method | `attr_doc: List[int]` | a non-empty `attr_doc` ↔ an inline attribute-doc comment exists for the member |
| `getdoc(member, ...)` — the value's intrinsic `__doc__` (`__init__.py:711`) | `value_doc: List[int]` | empty for a plain data constant whose value is `None` |
| `membername.startswith('_')` (`__init__.py:739`) | `name_underscored: bool` | True iff the member name begins with `_` |
| `special_member_re.match(membername)` (`__init__.py:750`) | `name_special: bool` | True iff the member name has the reserved `__name__` form; the precondition `not name_special` keeps such members outside the modeled slice (their retention is the unchanged special-members branch, `__init__.py:750-758`, which runs before the modeled branch) |
| `want_all` (`filter_members` param, `__init__.py:662`) | `want_all: bool` | identical |
| `self.options.private_members` (`__init__.py:761`): `None` / `ALL` / list | `private_mode: int` ∈ {0,1,2} | 0 = not requested (`None`); 1 = all requested (`ALL`, whose `__contains__` is always True, `__init__.py:71-75`); 2 = explicit list |
| `membername in self.options.private_members` for an explicit list (`__init__.py:764`) | `name_selected: bool` | True iff the member name is in the explicit list (immaterial when mode≠2) |
| the keep result fed to `ret.append((membername, member, isattr))` (`__init__.py:807-808`) | `bool` returned by `keep_module_member` | True ↔ the member is documented |

`str` indexing/iteration is banned in Nagini, so documentation blocks are
`List[int]`; specifications are phrased over `PSeq[int]` via `ToSeq`.

Why the documented-attribute branch (`__init__.py:759-768`) is the only keep
branch modeled: a module member with an inline `#:` attribute-doc comment is
recorded in the analyzer's `attr_docs`, so `(namespace='', membername) in
attr_docs` holds and `filter_members` enters that branch. The retention rule
there is exactly "keep unless (want_all and isprivate and not selected)", which
`keep_module_member` encodes. The other branches (special methods, mocked
objects, exclude-members, the non-attr fallback) are unchanged by the fix and
not on the path the failing tests exercise.

**Domain boundary (enforced by `Requires(len(attr_doc) > 0 or len(value_doc) >
0)`):** `keep_module_member` models the retention of a DOCUMENTED module
member only — one carrying inline attribute documentation (the `attr_docs`
branch above) or, when that is absent, a non-empty intrinsic documentation
(then `has_doc` is True and the private/else branches reduce to the same
formula). A member with NO documentation of either kind is decided by the
undocumented-member logic (`keep = has_doc or self.options.undoc_members`,
i.e. dropped under default options), an unchanged branch outside this model's
slice; the precondition excludes it rather than mis-asserting a keep value
for it. Verified by exhaustive enumeration of the emulated `filter_members`
against the model formula over the restricted domain: no diverging input.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `meta_class` ↔ `extract_metadata` + visibility branch (A-consumed)
**Callee:** `sphinx.util.docstrings.extract_metadata(s)` (`sphinx/util/docstrings.py:23`),
followed by the unchanged visibility branch in `filter_members`
(`sphinx/ext/autodoc/__init__.py:731-737`):

```python
metadata = extract_metadata(doc)
if 'private' in metadata:
    isprivate = True
elif 'public' in metadata:
    isprivate = False
else:
    isprivate = membername.startswith('_')
```

`extract_metadata` parses reST field markers and records any `:meta <name>:`
field into a dict; `'public'` / `'private'` keys arise from `:meta public:` /
`:meta private:` markers. The model abstracts the whole classifier into
`meta_class(doc) ∈ {NONE=0, PUBLIC=1, PRIVATE=2}`.

The axiom is the **weakest** the proof needs:
  (1) `Result() ∈ {0,1,2}` — the classification is a total function of the
      documentation block; and
  (2) an empty documentation block (`len(doc)==0`) classifies as `NONE` — so a
      member with NO documentation falls back to the underscore convention.

The proof does NOT pin `meta_class` to return PUBLIC/PRIVATE on any specific
input: the discriminating postcondition
`Implies(meta_class(effective_doc(...)) == PUBLIC, Result())` is parametric in
`meta_class` and holds for any classifier. This keeps the axiom sound (it never
claims more than the real callee guarantees) while the *load-bearing* change —
that the public-marked attribute documentation actually REACHES the classifier
(`effective_doc` prefers `attr_doc`) — is modeled deeply, not axiomatized.

**Soundness check (G-AX):** `axiom_check.py` runs the real `extract_metadata`
(+ the visibility branch) on boundary documentation blocks (empty, `None`,
`:meta public:`, `:meta private:`, prose, other field markers, multi-line,
whitespace-padded, both-markers) plus 20 000 randomized fuzz blocks, and
asserts every observation satisfies (1) and (2). It additionally records (not
pinned in the axiom) that the real classifier maps `:meta public:` → PUBLIC and
`:meta private:` → PRIVATE — the behaviour the deep keep-decision model relies
on the classifier being a function of the documentation. It imports only the
real `sphinx.util.docstrings` module (the module the unchanged code calls);
nothing repo-private is re-implemented. Exit 0 iff sound.

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned fuzz seed: `SEED = 8593`.** Inputs: 31 boundary cases + 100 000 seeded
fuzz cases = 100 031, every one satisfying `keep_module_member`'s `Requires`
(`private_mode ∈ {0,1,2}`, `len(attr_doc) > 0 or len(value_doc) > 0`,
`not name_special`; asserted per case rather than assumed).

**Shadow (provenance "direct").** Both `# impl-start` / `# impl-end` regions of
`model.py` — `member_effective_doc` and `keep_module_member` — copied verbatim
with only the contract calls removed, plus the `@Pure` helpers they call
(`is_private`, `in_private_selection`). `PSeq` is an immutable-tuple shim and
`ToSeq` materializes one. The `@ContractOnly` axiom `meta_class` has no body to
copy, so the shadow calls the REAL callee it axiomatizes
(`sphinx.util.docstrings.extract_metadata` + the unchanged visibility branch at
`sphinx/ext/autodoc/__init__.py:731-739`) — the axiom is exercised, not assumed.

**Oracle (called, not transliterated).** The real gold-patched pipeline,
composed as `Documenter.document_members` composes it:
`ModuleDocumenter.get_module_members` (the method the gold patch ADDS, which
attaches `docstring="\n".join(attr_docs.get(('', name), []))`) feeding
`Documenter.filter_members` (`__init__.py:662`, the unchanged consumer at
`:711` / `:725-727` / `:731-739` / `:759-768`). Driven on a duck-typed
documenter exposing only the attributes those two methods read, with a genuine
`types.ModuleType` as `self.object` so `dir` / `safe_getattr` /
`inspect.getannotations` behave as in production. Behaviour (1) is observed by
temporarily rebinding `sphinx.ext.autodoc.extract_metadata` to a recorder that
forwards to the real callee and records its argument — the effective `doc` the
real code actually arrived at; behaviour (2) is observed as the case's name
appearing in `filter_members`' returned list (`:807-808`).

**Type bridge (§2 inverted).** Generation happens on the `str` side;
`str_to_cps` / `cps_to_str` map documentation blocks to and from the model's
`List[int]` code-point carrier, with a real `doc` of `None` (absent or non-`str`
`__doc__`) bridging to `[]`. The inline attribute documentation is fed as
`attr_doc_text.split("\n")` so the repo's `"\n".join` reproduces the model's
`attr_doc` exactly (including the trailing `''` line the real `ModuleAnalyzer`
appends, `sphinx/pycode/__init__.py:173`). `private_mode` inverts to
`self.options.private_members`: 0 → `None`, 1 → the repo's `ALL` sentinel,
2 → an explicit list. `name_special` is held False by never generating a
reserved `__name__` form, honouring `Requires(not name_special)`.

**Branch coverage.** Boundary set takes both arms of `member_effective_doc`
(attribute doc present / absent — including the key-present-but-empty vs
key-absent distinction, which are two different real keep branches, `:759`
vs `:769`), all three arms of `is_private` (PUBLIC / PRIVATE / underscore
fallback), all three of `in_private_selection`, and all three of
`keep_module_member`. It includes the issue verbatim
(`_foo = None  #: :meta public:` under `:members:` with no `:private-members:`
— must be retained), its `:meta private:` mirror, the F2P `target.private`
shapes, both-markers blocks (the real branch tests `'private'` first → PRIVATE),
multi-line / indented / whitespace-only / non-ASCII blocks, and attribute
documentation overriding a conflicting intrinsic docstring.

**Refutation capability (checked, not asserted).** Four deliberate mutants were
run in-container and all four were caught, so a green G-CONF here is load-bearing:
(A) shadow with `member_effective_doc`'s precedence inverted → 2 disagreements;
(B) shadow with `is_private` ignoring the metadata marker → 5 disagreements;
(C) oracle without the gold patch applied → the patched method is absent;
(D) oracle swapped for the PRE-PATCH `importer.get_module_members` (bare
`(name, value)` tuples, no attached docstring — the actual bug) → 5
disagreements, the first on the issue's own `_foo`/`:meta public:` case.
