# refinement.md — sphinx-doc__sphinx-9461

The operation-by-operation correspondence between `model.py`'s implementations
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the maps below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

The gold patch fixes **three independently F2P-observable behaviours**, each
modeled as its own contracted function (or pair) with its own failing pre-patch
witness (SPEC_GUIDE §3):

1. **§A — the qualifier prefix** (`PyProperty.get_signature_prefix`,
   `sphinx/domains/python.py`): observed by `test_pyproperty`.
2. **§B — direct discovery + option-line emission** (autodoc
   `PropertyDocumenter.can_document_member`/`import_object`/`add_directive_header`,
   `sphinx/ext/autodoc/__init__.py`): the autoproperty-direct path, observed by
   `test_class_properties` (`test_ext_autodoc_autoproperty.py`) and (for the
   prefix/emission) `test_pyproperty`.
3. **§C — enclosing-class member-walk retention** (the docstring-resolution that
   decides whether a class-level property survives the autoclass member walk:
   autodoc `filter_members`' `getdoc(..., self.object, membername)` call +
   `sphinx/util/inspect.py`'s `getdoc`/`isclassmethod` `cls,name` resolution):
   observed by `test_properties` (`test_ext_autodoc_autoclass.py`).

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. Modeled site 1 — the qualifier prefix (`get_signature_prefix`, `python.py:867`)

Gold hunk 2:
```
-        prefix = ['property']
+        prefix = []
         if 'abstractmethod' in self.options:
-            prefix.insert(0, 'abstract')
+            prefix.append('abstract')
+        if 'classmethod' in self.options:
+            prefix.append('class')

+        prefix.append('property')
         return ' '.join(prefix) + ' '
```

Model function: `property_qualifier_prefix(has_abstract, has_classlevel)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `has_abstract: bool` | `'abstractmethod' in self.options` | R | a `directives.flag` option's presence is exactly a boolean (mapping.md §2). |
| A2 | parameter `has_classlevel: bool` | `'classmethod' in self.options` | R | likewise; the new flag is registered in `option_spec` (gold hunk 1) so the membership test is well-defined. The model input is the availability of the boolean. |
| A3 | `if has_abstract: result += abstract-codepoints + space-codepoints` | `if 'abstractmethod' in self.options: prefix.append('abstract')` | R + I | the `'abstract'` word, appended in order, contributing `abstract` + one separator space (mapping.md §2 join refinement). |
| A4 | `if has_classlevel: result += class-codepoints + space-codepoints` | `if 'classmethod' in self.options: prefix.append('class')` | R + I | the `'class'` word, appended in order after `'abstract'`; contributes `class` + one space. This is the new word the change introduces. |
| A5 | `result += property-codepoints + space-codepoints` (always, last) | `prefix.append('property')` (always, last) | R + I | the `'property'` word is unconditionally appended last. |
| A6 | the result `ToSeq` equals `expected_prefix(has_abstract, has_classlevel)` | `' '.join(prefix) + ' '` | A-reference | the changed string-assembly operation is modeled **deeply**: `expected_prefix` (the spelled-out per-word concatenation in the `pure` region) and the verified loop-free build ARE the assembly. No consumed `join` axiom; validated **== the real callee** by axiom_check.py (G-AX, A-ref 1) over all four qualifier combinations + F2P forms. |

The discriminating content — a class-level property contributes the `'class'`
word so its prefix is `class property ` (rather than the pre-patch `property `)
— lives in step A4 and is pinned by the `expected_prefix` clause.
`model_prepatch.py` reverts exactly this impl (seeds the vocabulary from the
property word, conditionally prepends `abstract`, never adds `class`) and
**fails** `ToSeq(Result()) == expected_prefix(has_abstract, has_classlevel)` on
any input with `has_classlevel = True` (G-DIFF). This is the string
`test_pyproperty` observes for `prop2` (`:classmethod:` → `class property `).

## B. Modeled site 2 — direct discovery + option-line emission (autodoc `PropertyDocumenter`)

This is the load-bearing site that `test_class_properties` (the
autoproperty-direct path) observes and that is **NOT** pinned by §A: §A only
assembles the prefix string *given* `has_classlevel = True`; it does not make a
`@classmethod @property` member be **discovered/documented at all** via the
direct documenter path nor emit its `:classmethod:` option line. The witness
`refined_python_only.diff` (the two `python.py` hunks alone) leaves
`test_pyproperty` PASS but `test_properties`/`test_class_properties` FAIL
(the `:classmethod:` line at index 3 is `''` instead of `'   :classmethod:'`),
proving this site carries independently-observable behaviour. It is therefore
modeled as its own contracted pair of functions, not hand-waved as A-opaque.
(The autoclass-walk path that `test_properties` observes additionally requires
the docstring-resolution retention modeled separately in §C below.)

Gold hunks 3–4 (`sphinx/ext/autodoc/__init__.py`):
```
-        return inspect.isproperty(member) and isinstance(parent, ClassDocumenter)
+        if isinstance(parent, ClassDocumenter):
+            if inspect.isproperty(member):
+                return True
+            else:
+                __dict__ = safe_getattr(parent.object, '__dict__', {})
+                obj = __dict__.get(membername)
+                return isinstance(obj, classmethod) and inspect.isproperty(obj.__func__)
+        else:
+            return False
   ...
+    def import_object(self, raiseerror=False) -> bool:
+        ret = super().import_object(raiseerror)
+        if ret and not inspect.isproperty(self.object):
+            ... obj = parent.__dict__.get(self.objpath[-1])
+            if isinstance(obj, classmethod) and inspect.isproperty(obj.__func__):
+                self.object = obj.__func__; self.isclassmethod = True; return True
+            else: return False
+        self.isclassmethod = False; return ret
   ...
   # add_directive_header:
+        if self.isclassmethod:
+            self.add_line('   :classmethod:', sourcename)
```

Model functions: the discovery decision `qualifies_for_property_doc(is_property,
is_classlevel_property, member_id)` and the emission
`property_option_block(is_abstract, is_classlevel_property, member_id)`. The
control-flow gate "the member is documented at all" is carried by the abstract
unforgeable capability `documented_as_property(member_id)` (a `@ContractOnly
@Predicate`, no body): its sole producer is `establish_documented`, performed by
the discovery decision exactly on its qualifying branch; the emission *requires*
it, so an option block can be emitted only for a member the discovery step
established as documentable. This faithfully mirrors the gold control flow
(`add_directive_header` runs only after `can_document_member`/`import_object`
admit the member).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `is_property: bool` | `inspect.isproperty(member)` | R + A-reference | the member-is-a-plain-property predicate; validated == real `sphinx.util.inspect.isproperty(member)` over actual members by axiom_check.py (A-ref 2 live probe). |
| B2 | parameter `is_classlevel_property: bool` | `isinstance(obj, classmethod) and inspect.isproperty(obj.__func__)` | R + A-reference | the member-is-a-classmethod-wrapping-property predicate (the property whose access is bound at the class level); validated == the real `isinstance(.,classmethod) and isproperty(.__func__)` over an actual `@classmethod @property` by axiom_check.py (A-ref 2 live probe). |
| B3 | `qualifies = is_property or is_classlevel_property`; on each qualifying branch `establish_documented(member_id)`; return the decision | `can_document_member` returns `isproperty(member) or (classmethod-wrapping-property)` (and `import_object` sets `self.isclassmethod`, returns True) | R + A-reference | the discovery decision. `Ensures(Result() == is_property or is_classlevel_property)` pins it; the qualifying branch grants the capability. Validated == the real `can_document_member` decision over `prop1`/`prop2` by axiom_check.py (A-ref 2). |
| B4 | `Requires(documented_as_property(member_id))` on `property_option_block` | `add_directive_header` runs only for a discovered/imported member | I (control-flow) | emission is gated on discovery; mirrored by requiring the capability the discovery step grants. |
| B5 | `if is_abstract: result += abstractmethod-line-codepoints` | `if inspect.isabstractmethod(self.object): self.add_line('   :abstractmethod:', …)` | R + I | the abstractness option line (unchanged behaviour, retained for faithful emission ordering). |
| B6 | `if is_classlevel_property: result += classmethod-line-codepoints` | `if self.isclassmethod: self.add_line('   :classmethod:', …)` | R + I | the class-level option line — the NEW emission the change introduces; `self.isclassmethod` is True exactly on the B2/B3 classmethod-property branch. |
| B7 | the result `ToSeq` equals `expected_option_block(is_abstract, is_classlevel_property)` | the concatenated emitted option lines | A-reference | the emission is modeled **deeply** (`expected_option_block`, pure region); validated == the real `add_directive_header` line emission by axiom_check.py (A-ref 2) over the boolean cube + F2P forms. No consumed emission axiom. |

The discriminating content — a `@classmethod @property` member IS discovered
(`qualifies = True`, where the pre-patch returns `is_property = False`) and its
`:classmethod:` option line IS emitted — lives in B3/B6.
`model_prepatch_2.py` reverts exactly this: discovery qualifies **only** when
`is_property` (so a class-level property is never established as documentable),
and the emission has no class-level line branch. It **fails** both
`Result() == (is_property or is_classlevel_property)` (the `prop2` case:
`is_property=False, is_classlevel_property=True` → real True, pre-patch False)
and `ToSeq(Result()) == expected_option_block(...)` (no `:classmethod:` line) —
exactly the spec sensing the discovery/emission change (G-DIFF). This is the
`:classmethod:` option line and class-level discovery that `test_class_properties`
(and, through the §C-retained walk, `test_properties`) observe for `prop2`.

## C. Modeled site 3 — enclosing-class member-walk retention (docstring resolution)

This is the third independently-F2P-observable site, observed by `test_properties`
(the autoclass member-walk path), and it is **NOT** pinned by §A or §B. The
autoclass member walk (autodoc `filter_members`) keeps a member only if its
descriptive text resolves (`keep = has_doc` in the default no-undoc-members
walk). For a `@classmethod @property`, the pre-patch resolution reads the
`classmethod` descriptor's own `__doc__` — the generic builtin classmethod
docstring — which the walk then discards (it matches the descriptor type's
`__doc__`), so `has_doc = False` and the member is **dropped from the walk and
never documented at all**. The gold makes the walk pass the enclosing class +
member name into the docstring resolver (`getdoc(..., self.object, membername)`)
and adds a class-level resolution branch (`isclassmethod`/`getdoc` `cls,name` →
`getmro(cls)` → underlying `__func__.__doc__`), so the class-level property's
real text (`'docstring'`) resolves, `has_doc = True`, and the member is retained.

Witness (re-audit): the previous "refinement-justified subset"
(`$SCRATCH/refinement_justified_subset.diff`, §A + §B hunks only, omitting
this retention) returns `resolved: false` with `test_properties` FAILING — the
entire `prop2` block is absent because the member is filtered out of the walk.
This proves the site carries independently-observable behaviour, so it is modeled
as its own contracted pair, **not** hand-waved as F2P-constant plumbing.

Gold hunks (`filter_members` line 718 + `sphinx/util/inspect.py` `isclassmethod`/`getdoc`):
```
   # filter_members (sphinx/ext/autodoc/__init__.py):
-  doc = getdoc(member, self.get_attr, ..., self.parent, self.object_name)
+  doc = getdoc(member, self.get_attr, ..., self.object, membername)
   ...
   # sphinx/util/inspect.py:
+  def isclassmethod(obj, cls=None, name=None):
+      ... elif cls and name: for basecls in getmro(cls): meth = basecls.__dict__.get(name); if meth: return isclassmethod(meth)
+  def getdoc(obj, ..., cls=None, name=None):
+      if cls and name and isclassmethod(obj, cls, name):
+          for basecls in getmro(cls): meth = basecls.__dict__.get(name); if meth: return getdoc(meth.__func__)
```

Model functions: the retention decision
`member_retained_in_class_walk(is_classlevel_property, has_descriptive_text, member_id)`
and the walk emission `class_walk_option_block(is_abstract, is_classlevel_property,
member_id)`. The control-flow gate "the member survives the walk" is carried by a
second abstract unforgeable capability `retained_in_class_walk(member_id)` (a
`@ContractOnly @Predicate`, no body): its sole producer is `establish_retained`,
performed by the retention decision exactly on its retain branch; the walk
emission *requires* it, so a walk option block can be produced only for a member
the walk actually retained.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | parameter `is_classlevel_property: bool` | the member is a `@classmethod @property` (the `isclassmethod(obj, cls, name)` branch fires) | R + A-reference | the class-level-property predicate; same abstraction as B2. |
| C2 | parameter `has_descriptive_text: bool` | the underlying member carries a docstring (`getmro(cls)`/`__func__.__doc__` is non-empty) | R + A-reference | whether the member's genuine descriptive text exists; validated == the real `getdoc(member, cls, name)` resolving non-empty by axiom_check.py (A-ref 3 live probe). |
| C3 | `text_resolves = has_descriptive_text`; if it resolves `establish_retained(member_id)`; return the decision | `keep = has_doc` after `doc = getdoc(member, …, self.object, membername)`; the new `getdoc` `cls,name` branch makes a class-level property's `has_doc` True iff its text exists | R + A-reference | the retention decision. `Ensures(Result() == has_descriptive_text)` pins it — a class-level property is kept on the same footing as an ordinary property (NOT dropped for being class-level); the retain branch grants the capability. Validated == the real `getdoc`-driven keep over `prop1`/`prop2`/`prop_nodoc` by axiom_check.py (A-ref 3). |
| C4 | `Requires(retained_in_class_walk(member_id))` on `class_walk_option_block` | the walk calls `add_directive_header` (emits the block) only for a kept member | I (control-flow) | walk emission is gated on retention; mirrored by requiring the capability the retention step grants. |
| C5 | `class_walk_option_block` body == `expected_option_block(is_abstract, is_classlevel_property)` | the emitted option lines for the retained member | A-reference | the same deep emission model as §B (B5–B7), here gated on retention; validated == the real `add_directive_header` emission by axiom_check.py (A-ref 2). |

The discriminating content — a `@classmethod @property` member's descriptive
text resolves, so it is **retained** in the walk (where the pre-patch resolution
drops it) — lives in C2/C3. `model_prepatch_3.py` reverts exactly this: for a
class-level property the text does NOT resolve in the walk
(`text_resolves = has_descriptive_text and not is_classlevel_property`), so a
class-level property with descriptive text is dropped and gets no walk block. It
**fails** `Result() == has_descriptive_text` for `member_retained_in_class_walk`
(the `prop2` case: `is_classlevel_property=True, has_descriptive_text=True` →
real True, pre-patch False) — exactly the spec sensing the docstring-resolution
change (G-DIFF). This is what makes the `prop2` block present in `test_properties`.

## C′. The remaining supporting hunk (not separately modeled — why)

| site | gold hunk | tag | why not a separate modeled function |
|---|---|---|---|
| `PyProperty.option_spec.update({'classmethod': directives.flag})` (`python.py:855`) | hunk 1 | R (data) | registers the `:classmethod:` flag so the directive accepts it; modeled as the mere *availability* of the `has_classlevel` boolean input to §A (mapping.md §2). No behaviour beyond enabling A2/A4. It is **not** F2P-load-bearing on its own (it is the precondition for §A's `has_classlevel` to be settable), and carries no F2P-observable delta independent of §A. |

## D. No kind-3 (unexpressible-changed-op) steps

Every step in §A, §B and §C is R, A-reference, A-consumed-free, or I. The three
operations that genuinely *changed* — the prefix string assembly (now
contributing the `'class'` word), the discover→emit pipeline (now admitting a
class-level property and emitting its `:classmethod:` line), and the class-walk
docstring resolution (now resolving a class-level property's text so it is
retained) — are all modeled **deeply** (`expected_prefix` / `expected_option_block`
+ the discovery decision + the retention decision + the two capability gates),
not hidden behind an axiom about a function under change. There are **no
A-consumed axioms**. The kind-A items are three **A-references** that G-AX
validates the deep models against (the real `' '.join` assembly; the real
`add_directive_header` emission + the real `isproperty`-based discovery decision;
the real `getdoc`-driven class-walk retention). `establish_documented` /
`documented_as_property` and `establish_retained` / `retained_in_class_walk` are
abstract capabilities modeling the discovery→emit and retention→emit control-flow
gates, not callee axioms (no `Ensures` over a value the proof reads as data —
only the opaque capability tokens).

## E. verify(model) ⇒ resolved

* §A: `property_qualifier_prefix` verifies only if its output equals the exact
  per-word concatenation in which the class-level qualifier contributes the
  `'class'` word (A4, A6). By R and G-AX A-ref 1, the verified assembly equals
  the gold `' '.join(prefix) + ' '` for every qualifier combination. Pins
  `test_pyproperty`.
* §B: `qualifies_for_property_doc` verifies only if it admits a class-level
  property (B3) and `property_option_block` verifies only if it emits the
  `:classmethod:` line for one (B6/B7). By R and G-AX A-ref 2, this equals the
  gold `can_document_member`/`import_object` discovery and `add_directive_header`
  emission over the tested members. Pins `test_class_properties` (the
  autoproperty-direct path).
* §C: `member_retained_in_class_walk` verifies only if it retains a class-level
  property whose descriptive text exists (C3, `Result() == has_descriptive_text`)
  and `class_walk_option_block` verifies only if it emits the block for a
  retained member (C4/C5). By R and G-AX A-ref 3, this equals the gold
  `getdoc(..., self.object, membername)` + class-level `getdoc`/`isclassmethod`
  resolution that keeps `prop2` in the autoclass walk. Pins `test_properties`
  (the autoclass member-walk path).
* The remaining hunk (§C′) supplies the `has_classlevel` flag registration and
  carries no F2P-observable delta independent of §A.

Therefore a model satisfying this spec, refined by the maps above, is the gold
patch up to type refinement and the audited reference callees; and the gold
patch resolves all three F2P tests (G-RESOLVE). The refinement-justified
subset is now the **full gold patch**: §A needs the `python.py` hunks, §B needs
the autodoc `can_document_member`/`import_object`/`add_directive_header` hunks,
and §C needs the `filter_members` line-718 call + the `sphinx/util/inspect.py`
`getdoc`/`isclassmethod` hunks. Both previously-failing subset witnesses are now
CLOSED: `refined_python_only.diff` (§A hunks only) and
`refinement_justified_subset.diff` (§A+§B only, omitting §C) are each no longer
the refinement-justified subset — §C now requires the inspect/line-718 hunks, so
the refinement-justified patch is the full gold patch, which resolves all three
F2P. The trust points are exactly the two of PLAN §1.1: reference-callee
soundness (G-AX, three A-references) and refinement fidelity (this document,
G-EQ).
