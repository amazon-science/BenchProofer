# refinement.md — sphinx-doc__sphinx-8593

The operation-by-operation correspondence between `model.py`'s implementation
(the `member_effective_doc` and `keep_module_member` impl regions, the pure
`effective_doc` / `is_private` / `in_private_selection` models, and the
`meta_class` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The effective-documentation site — `member_effective_doc`

Gold change (`sphinx/ext/autodoc/__init__.py`): a new
`ModuleDocumenter.get_module_members()` builds, for each module member,
`ObjectMember(name, value, docstring="\n".join(attr_docs.get(('', name), [])))`,
and `get_object_members` now feeds those `ObjectMember`s (with the attached
docstring) to `filter_members`, which already prefers an attached docstring
(`if isinstance(obj, ObjectMember) and obj.docstring: doc = obj.docstring`,
`__init__.py:725-727`) over the value's intrinsic `getdoc(member)`
(`__init__.py:711`).

| # | model.py impl op (`member_effective_doc`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `attr_doc, value_doc: List[int]` | the joined `attr_docs.get(('', name), [])` string and the value's `getdoc(member)` string | R | `str` ↔ `List[int]` code points (mapping.md §2); `attr_docs.get(...)` joined by `"\n"` ↔ `attr_doc`; `getdoc(member)` ↔ `value_doc`. |
| A2 | `if len(attr_doc) > 0: result = list(attr_doc) else: result = list(value_doc)` | the new `ObjectMember(..., docstring="\n".join(attr_docs.get(...)))` attaching the attribute documentation, consumed by `filter_members`'s `if obj.docstring: doc = obj.docstring` precedence over `getdoc(member)` | I | the precedence "use the attached attribute documentation when present, else the intrinsic documentation" is the same concrete branch; `"\n".join([])` is the empty string ⇔ `len(attr_doc)==0`. |
| A3 | `return result` (a `List[int]`) | the `doc` variable used downstream in `filter_members` | R | `str` ↔ `List[int]`; the returned effective documentation is what the visibility classifier reads. |

The discriminating content: pre-patch the member was a bare `(name, value)`
tuple from `importer.get_module_members` carrying NO docstring, so
`filter_members` used the value's empty intrinsic documentation and the inline
attribute documentation never reached the classifier. `model_prepatch.py`
reproduces that (the impl returns `value_doc`, ignoring `attr_doc`) and **fails**
the postcondition `ToSeq(Result()) == effective_doc(ToSeq(attr_doc),
ToSeq(value_doc))` — exactly the spec sensing the change (G-DIFF).

## B. The retention site — `keep_module_member`

Gold-relevant code (`filter_members`, `__init__.py:731-768`, unchanged by the
fix but consuming the now-attached documentation):

```python
metadata = extract_metadata(doc)
if 'private' in metadata:   isprivate = True
elif 'public' in metadata:  isprivate = False
else:                       isprivate = membername.startswith('_')
...
elif (namespace, membername) in attr_docs:        # module attrs are here
    if want_all and isprivate:
        if self.options.private_members is None:   keep = False
        else:                                      keep = membername in self.options.private_members
    else:                                          keep = True
```

| # | model.py impl op (`keep_module_member`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | `doc = member_effective_doc(attr_doc, value_doc)` | the `doc` chosen in `filter_members` (attached attribute documentation preferred) | I | uses behaviour A (under spec, not an axiom): the caller's spec uses the callee's spec. |
| B2 | `private = is_private(name_underscored, ToSeq(doc))` → `meta_class(doc)` PUBLIC⇒False / PRIVATE⇒True / else `name_underscored` | `metadata = extract_metadata(doc)`; `'public'`⇒`isprivate=False`, `'private'`⇒`isprivate=True`, else `membername.startswith('_')` | A-consumed | `meta_class` axiomatizes the unchanged classifier `extract_metadata` + the public/private branch; the proof consumes its `Ensures` (result ∈ {0,1,2}; empty⇒NONE). G-AX confirms it against the real callee (mapping.md §3.1). |
| B3 | `if not want_all: keep=True; elif not private: keep=True; else: keep = in_private_selection(private_mode, name_selected)` | the documented-attribute keep branch `__init__.py:759-768` (`want_all and isprivate` ⇒ private-members selection, else keep) | I + R | the control flow is identical; `private_mode`/`name_selected` are the R-refinement of `self.options.private_members` ∈ {None, ALL, list} and `membername in private_members` (mapping.md §2). `ALL.__contains__` always True ⇒ mode 1 keeps. |
| B4 | `return keep` | `keep` decides `ret.append((membername, member, isattr))` | R | the boolean retention decision ↔ whether the member is documented. |

Domain boundary: the precondition `len(attr_doc) > 0 or len(value_doc) > 0`
restricts behaviour B to DOCUMENTED module members (inline attribute
documentation present, or a non-empty intrinsic documentation). On that slice
the branch structure above is exactly the retention formula. A member with no
documentation of either kind falls to the unchanged undocumented-member
branch of the real retention code (kept only when undoc-members is requested),
which is outside the modeled slice; the precondition excludes it instead of
asserting a keep value there (mapping.md §2 end).

Second boundary: the precondition `not name_special` restricts behaviour B to
ordinarily named members. A member whose name has the reserved
double-underscore form is handled by the unchanged special-members branch of
the real retention code, which runs BEFORE the modeled branch and applies its
own selection option; that branch is outside the modeled slice, so the
precondition excludes those names rather than asserting a keep value for them
(mapping.md §2).

The discriminating content: when an underscore-named member carries a public
attribute-doc marker, post-patch `effective_doc` delivers that marker to the
classifier, so `is_private` is False and the member is kept regardless of the
private-members selection (and its `:meta public:` documentation is rendered).
`model_prepatch_2.py` isolates behaviour (2): it classifies on `value_doc`
(the empty intrinsic documentation) instead of the effective documentation,
mirroring the pre-patch flow, and **fails** the keep postcondition
`Result() == ((not want_all) or (not is_private(name_underscored,
effective_doc(...))) or in_private_selection(...))`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — that
the inline attribute documentation of a module member is attached to the member
and thereby reaches the visibility classifier — is modeled **deeply**
(`member_effective_doc` with the spelled-out `effective_doc` precedence,
behaviour A, step A2 = **I**), not hidden behind an axiom about the function
under change. The only **A-consumed** axiom, `meta_class` (behaviour B, step
B2), covers the **unchanged** classifier `extract_metadata` the new flow feeds;
there is no **A-reference** deep model here (the changed op is plain
control/data flow, expressed directly).

## D. verify(model) ⇒ resolved

`member_effective_doc` verifies only if its output equals the
attribute-doc-preferred effective documentation (A2) and `keep_module_member`
verifies only if its retention equals the visibility-derived rule computed on
THAT effective documentation (B1-B3), including the discriminating clause that a
public-marked member is always kept. By R (str ↔ List[int]; the option-mode
bijection; the underscore predicate) the verified models equal the gold patch's
new `get_module_members` + the unchanged `filter_members` flow on the tested
inputs; by G-AX the `meta_class` axiom is sound against the real
`extract_metadata`. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the one audited callee — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
