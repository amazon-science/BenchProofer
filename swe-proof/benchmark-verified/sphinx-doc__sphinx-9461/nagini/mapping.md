# mapping.md — sphinx-doc__sphinx-9461

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 939c7bb7ff7c53a4d27df067cea637540f0e1dad`, states the type
abstraction, and gives the provenance of the three kind-A items (all
A-references: the deep prefix model validated == the real string-join assembly;
the deep option-block model + discovery decision validated == the real autodoc
emission/discovery; and the retention decision validated == the real
`getdoc`-driven class-walk keep).

Repo files under change for the modeled functions:
`sphinx/domains/python.py` (site 1), `sphinx/ext/autodoc/__init__.py`
(sites 2 and 3) and `sphinx/util/inspect.py` (site 3 docstring resolution).

## 1. Symbol ↔ repo binding

### Site 1 — the qualifier prefix

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `property_qualifier_prefix(has_abstract, has_classlevel)` | `PyProperty.get_signature_prefix(self, sig)` — `sphinx/domains/python.py:867` | the modeled changed function (assembles the property qualifier prefix string) |
| `has_abstract` (bool param) | `'abstractmethod' in self.options` (`python.py:869`) | abstractness qualifier flag |
| `has_classlevel` (bool param) | `'classmethod' in self.options` (`python.py:737` post-patch; the new flag added to `option_spec` at `python.py:855` post-patch) | class-level qualifier flag |
| `word_abstract / word_class / word_property` | the literal role words `'abstract'`, `'class'`, `'property'` in the assembled vocabulary list | pure spec: role words as code-point sequences |
| `space` | the `' '` separator in `' '.join(prefix) + ' '` | pure spec: the single-space separator/terminator |
| `expected_prefix(has_abstract, has_classlevel)` *(deep model — A-reference 1)* | `' '.join(prefix) + ' '` over the assembled word list (`python.py:872` pre / the equivalent post-patch return) | pure spec: the assembled prefix; deep model of the real `str.join` assembly, validated by axiom_check.py (G-AX), NOT consumed as an axiom |

### Site 2 — discovery + option-line emission

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `qualifies_for_property_doc(is_property, is_classlevel_property, member_id)` | `PropertyDocumenter.can_document_member` / `import_object` — `sphinx/ext/autodoc/__init__.py:2661-2706` (post-patch) | the modeled discovery decision: does this member get documented as a property, and is it class-level? |
| `property_option_block(is_abstract, is_classlevel_property, member_id)` | `PropertyDocumenter.add_directive_header` — `sphinx/ext/autodoc/__init__.py:2700+` (post-patch) | the modeled option-line emission for a discovered property member |
| `is_property` (bool param) | `inspect.isproperty(member)` (`sphinx/util/inspect.py`) | the member-is-a-plain-property predicate |
| `is_classlevel_property` (bool param) | `isinstance(obj, classmethod) and inspect.isproperty(obj.__func__)` (autodoc post-patch) | the member-is-a-classmethod-wrapping-property predicate (access bound at the class level) |
| `member_id` (int param) | the identity of the member being examined | abstract member identity (carries the per-member capability) |
| `documented_as_property(member_id)` *(`@ContractOnly @Predicate`)* | the control-flow fact "this member is admitted for documentation" established by `can_document_member`/`import_object` returning True | abstract unforgeable capability gating emission; SOLE producer `establish_documented`; NOT a callee axiom |
| `establish_documented(member_id)` *(`@ContractOnly`)* | the documenter proceeding to document the admitted member (the post-`can_document_member`/`import_object`-True step) | the abstract effect that grants the capability on the qualifying branch |
| `line_abstract / line_class` | the literal emitted option lines `'   :abstractmethod:'` / `'   :classmethod:'` in `add_directive_header` | pure spec: emitted option lines as code-point sequences |
| `expected_option_block(is_abstract, is_classlevel)` *(deep model — A-reference 2)* | the concatenation of the emitted option lines in `add_directive_header` | pure spec: the emitted block; deep model of the real emission, validated by axiom_check.py (G-AX), NOT consumed as an axiom |

### Site 3 — enclosing-class member-walk retention (docstring resolution)

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `member_retained_in_class_walk(is_classlevel_property, has_descriptive_text, member_id)` | `Documenter.filter_members`'s keep decision — `sphinx/ext/autodoc/__init__.py:718` (the `getdoc(..., self.object, membername)` call, post-patch) + `keep = has_doc` | the modeled retention decision: does this walked member survive the drop-the-undocumented filter? |
| `class_walk_option_block(is_abstract, is_classlevel_property, member_id)` | `PropertyDocumenter.add_directive_header` reached for a retained walk member — `sphinx/ext/autodoc/__init__.py:2700+` (post-patch) | the modeled option-line emission in the autoclass-walk path (same emission as site 2, gated on retention) |
| `is_classlevel_property` (bool param) | the member is a `@classmethod @property` (the `isclassmethod(obj, cls, name)` `getmro`/`__func__` branch fires) | the class-level-property predicate (same abstraction as site 2) |
| `has_descriptive_text` (bool param) | the member's genuine descriptive text exists (the underlying property's `__func__.__doc__` is non-empty) | whether the member carries a docstring resolvable via the class-level path |
| `retained_in_class_walk(member_id)` *(`@ContractOnly @Predicate`)* | the control-flow fact "this walked member is kept" established by `filter_members` setting `keep = True` (`has_doc` resolved) | abstract unforgeable capability gating the walk emission; SOLE producer `establish_retained`; NOT a callee axiom |
| `establish_retained(member_id)` *(`@ContractOnly`)* | the walk appending the member to `ret` and proceeding to document it (the post-`keep`-True step) | the abstract effect that grants the retention capability on the retain branch |

The pre-patch repo logic the change replaces (for the refinement audit; not
referenced from the consumer spec view):

* Site 1: `prefix = ['property']` seeded with the property word, the abstractness
  qualifier *prepended* via `prefix.insert(0, 'abstract')`, and NO class-level
  qualifier entry (`python.py:868-872` pre-patch).
* Site 2: `can_document_member` returned `inspect.isproperty(member) and
  isinstance(parent, ClassDocumenter)` — a `@classmethod @property` has
  `isproperty(member) == False`, so it was never admitted/documented; and
  `add_directive_header` had no `:classmethod:` line and no `self.isclassmethod`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the returned prefix / emitted lines) | `List[int]` of Unicode code points | `s[k]` ↔ `result[k] == ord(s[k])`; `len(s)` ↔ `len(result)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `'abstractmethod' in self.options` / `'classmethod' in self.options` (membership of a flag in the directive option mapping) | `bool` parameter | each `directives.flag` option is present-or-absent; the membership test is exactly a boolean. |
| `inspect.isproperty(member)` | `is_property: bool` | true iff the member is a plain `property` descriptor (validated by G-AX A-ref 2 over a real `@property`) |
| `isinstance(obj, classmethod) and inspect.isproperty(obj.__func__)` | `is_classlevel_property: bool` | true iff the member is a classmethod wrapping a property (validated by G-AX A-ref 2 over a real `@classmethod @property`) |
| `can_document_member`/`import_object` admitting a member, then `add_directive_header` running | the capability `documented_as_property(member_id)` gating `property_option_block` | the control-flow gate "discovered ⇒ may emit"; an abstract token, not a data value |
| the assembled `list` of role words + `' '.join(...) + ' '` | the per-word concatenation, each word suffixed by one space | `' '.join([w1,…,wn]) + ' '` == `w1 ' ' … wn ' '`; for the fixed vocabulary the join is exactly this per-word suffix-with-space form (validated by G-AX A-ref 1) |
| `add_directive_header`'s `self.add_line('   :abstractmethod:')` / `self.add_line('   :classmethod:')` | concatenation of the emitted option-line code points | each emitted line is appended in order; the `:classmethod:` line iff `self.isclassmethod` (validated by G-AX A-ref 2) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; specifications are phrased over `PSeq[int]` via `ToSeq`.

The new `'classmethod'` flag is registered in `PyProperty.option_spec` (gold
hunk 1, `python.py:855`); without that registration the directive would reject
`:classmethod:`. The registration is data (`option_spec.update`), modeled as the
mere availability of the `has_classlevel` boolean input.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms** in this bundle. Three
**A-references** validate the deep models against the real callees.

### 3.1 A-reference 1 — `expected_prefix` ↔ real `' '.join` assembly
**Callee:** the standard-library `str.join` (`' '.join(prefix)`) used by the
real `get_signature_prefix` return. The assembly is modeled **deeply** by
`expected_prefix` (with the `word_*`/`space` helpers); there is **no `join`
axiom** the proof consumes.

Post-patch real assembly (`sphinx/domains/python.py`, gold hunk 2):
```python
prefix = []
if 'abstractmethod' in self.options: prefix.append('abstract')
if 'classmethod' in self.options:    prefix.append('class')
prefix.append('property')
return ' '.join(prefix) + ' '
```
Because the vocabulary words contain no spaces, `' '.join(words) + ' '` is
exactly the concatenation of each word followed by one space, in order — what
`expected_prefix` encodes. G-AX asserts `expected_prefix(a, c) == ' '.join(
real_words(a, c)) + ' '` over the full boolean cube (4 combinations) plus the
F2P-observed string forms. CPython `str.join` docs:
https://docs.python.org/3/library/stdtypes.html#str.join.

### 3.2 A-reference 2 — `expected_option_block` + discovery ↔ real autodoc emission
**Callees:** `sphinx.util.inspect.isproperty`, the `isinstance(., classmethod)`
builtin, and `PropertyDocumenter.add_directive_header`'s `self.add_line(...)`.
Provenance: `sphinx/ext/autodoc/__init__.py` `PropertyDocumenter.can_document_member`
/ `import_object` / `add_directive_header` (gold hunks 3–5).

Real post-patch discovery (`can_document_member`/`import_object`): a member is
admitted iff `inspect.isproperty(member)` OR (`isinstance(member, classmethod)
and inspect.isproperty(member.__func__)`); `self.isclassmethod` is set True
exactly on the latter branch. Real post-patch emission (`add_directive_header`):
emits `'   :abstractmethod:'` iff abstract, then `'   :classmethod:'` iff
`self.isclassmethod`.

`axiom_check.py` (G-AX), run inside the instance container with the gold patch
applied (Python 3.9.20, Sphinx 4.2.0), validates:
* `expected_option_block(a, c) == real add_directive_header emission` over the
  full boolean cube (4 combinations) + the F2P forms (`prop1` → no class line,
  `prop2` → `'   :classmethod:'`);
* the discovery decision `qualifies == is_property or is_classlevel_property`
  and the `is_classmethod` flag equal the **real** decision, exercised over an
  actual `@property` (`prop1`) and an actual `@classmethod @property` (`prop2`)
  using the real `sphinx.util.inspect.isproperty` callee (live probe;
  `isproperty(prop1)=True`, `isproperty(prop2)=False`,
  `isinstance(prop2,classmethod) and isproperty(prop2.__func__)=True`).

### 3.3 A-reference 3 — `member_retained_in_class_walk` ↔ real `getdoc`-driven retention
**Callees:** `sphinx.util.inspect.getdoc` / `isclassmethod` (post-patch, with the
`cls,name` class-level resolution branch) and the autoclass member walk's keep
rule `keep = has_doc`. Provenance: `sphinx/ext/autodoc/__init__.py`
`Documenter.filter_members` line-718 `getdoc(member, ..., self.object, membername)`
(gold) + `sphinx/util/inspect.py` `getdoc`/`isclassmethod` `cls,name` hunks (gold).

Real post-patch retention: the walk computes
`doc = getdoc(member, ..., self.object, membername)`; for a `@classmethod
@property` the new `isclassmethod(obj, cls, name)` branch fires and `getdoc`
returns the underlying `getdoc(meth.__func__)` (the property's real docstring),
so `has_doc` is True and the member is kept. Pre-patch, the walk passed
`self.parent, self.object_name` and `getdoc(member)` read the `classmethod`
descriptor's own `__doc__` (the generic builtin classmethod docstring), which
the walk then discards as the descriptor type's `__doc__`, so `has_doc` is False
and the member is dropped.

`axiom_check.py` (G-AX), run inside the instance container with the gold patch
applied, validates the model's `member_retained_in_class_walk` decision
`Result() == has_descriptive_text` (a class-level property is kept iff it has
text, independent of class-level-ness) against the **real** `getdoc`-driven keep
over a live `@property` (`prop1`, kept), a live `@classmethod @property` with a
docstring (`prop2`, kept — its real `getdoc(member, cls, name)` resolves to
`'docstring'`) and a live `@classmethod @property` with no docstring
(`prop_nodoc`, dropped).

In-container result: RC 0 — `A-ref1 expected_prefix == real ' '.join assembly on
4 combos + 4 F2P forms; A-ref2 expected_option_block == real add_directive_header
emission on 4 combos + 2 F2P forms; discovery decision validated against real
isproperty on 2 live members; A-ref3 class-walk retention validated against real
getdoc on 3 live members`.
