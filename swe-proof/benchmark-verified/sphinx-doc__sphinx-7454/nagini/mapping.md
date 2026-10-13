# mapping.md — sphinx-doc__sphinx-7454

Binds every `model.py` symbol to its repository counterpart at
`base_commit = aca3f825f2e4a8817190f3c885a242a285aa0dba`, states the type
abstraction, and records the (single) change site.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `make_cross_reference(text)` | `make_xref(text)` — the nested helper inside `_parse_annotation`, `sphinx/domains/python.py:73` (return at line 74-75) | the modeled changed function: turns one annotation name into a cross-reference node |
| `CrossReference` (class, fields `kind`, `target`) | `addnodes.pending_xref('', nodes.Text(text), refdomain='py', reftype=…, reftarget=text)` — `sphinx/domains/python.py:74-75` | minimal model of the cross-reference node, exposing only the two touched fields: `kind` ↔ `reftype`, `target` ↔ `reftarget` |
| `name_value()` | the string literal `'None'` in the test `text == 'None'` (`sphinx/domains/python.py:74` post-patch) | pure spec: the singleton value name as code points `PSeq(78,111,110,101)` |
| `tag_value()` | the string literal `'obj'` (`reftype = 'obj'`, post-patch) | pure spec: the value-reference tag as code points `PSeq(111,98,106)` |
| `tag_type()` | the string literal `'class'` (`reftype = 'class'` / the pre-patch unconditional `reftype='class'`) | pure spec: the type-reference tag as code points `PSeq(99,108,97,115,115)` |
| `kind_for(text)` | the `if text == 'None': reftype = 'obj' else: reftype = 'class'` classification (`sphinx/domains/python.py:74-77` post-patch) | pure spec: the reference-kind classifier; the deep model of the changed operation |

The pre-patch repo symbol the change replaces (for the refinement audit, not
referenced from the consumer spec view): the unconditional `reftype='class'`
argument in `make_xref`'s single `return pending_xref(...)` statement
(`sphinx/domains/python.py:74-75`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `text` argument of `make_xref`; the `reftarget` value; the tag string literals `'None'`/`'obj'`/`'class'`) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` equality `text == 'None'` ↔ `ToSeq(text) == name_value()`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` equality mirrors `str` equality |
| `addnodes.pending_xref('', nodes.Text(text), refdomain='py', reftype=R, reftarget=T)` | `CrossReference` with `kind == R` (code points), `target == T` (code points) | the constructor, the empty rawsource `''`, the `nodes.Text(text)` child, and the fixed `refdomain='py'` are UNCHANGED context; only the two fields the patch touches (`reftype`→`kind`, `reftarget`→`target`) are modeled. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance

None. No library callee mediates the changed behaviour, so there is **no**
`@ContractOnly` axiom and **no** A-reference deep-model check. The whole change
is a pure in-function conditional over the input string (`text == 'None'`
selecting between two constant tags), modeled deeply by `kind_for` and the
verbatim code-point tag constants. `axiom_check.py` therefore performs no
in-container callee fuzzing; it instead independently checks the deep
classification model against the gold rule and against the F2P-observed values
(`'int' → 'class'`, `'None' → 'obj'`, `reftarget == text`), using only the
Python standard library — see `axiom_check.py`. (G-AX has no axiom to discharge
here; the check documents the deep-model fidelity that G-EQ audits.)
