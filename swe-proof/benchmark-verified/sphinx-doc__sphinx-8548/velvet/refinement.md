# refinement.md — sphinx-doc__sphinx-8548

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`collectInstanceAttrDocs` `do` block and the
`levelCandidates`/`candidates`/`collectStep`/`collected` direct model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — none consumed in this bundle), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §E);
the structural-abstraction facts by **G-AX** (`axiom_check.py`, mapping.md §3);
this narrative by **G-EQ**. Claim: any impl verifying against this frozen spec,
refined per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). Line numbers are those of
the patched worktree.

## A. The collection site — `get_class_members()` (`sphinx/ext/autodoc/importer.py:254`)

Gold hunk. Pre-change, the two kinds of declaration were gathered by two separate
passes: an MRO walk that took annotations only, and then a single analyzer pass
keyed on the **fixed** namespace `'.'.join(objpath)` — the subject class — which
attributed everything it found to `subject`. Post-change there is ONE walk, and
each class contributes both kinds:

```
-    # annotation only member (ex. attr: int)
-    for cls in getmro(subject):
-        try:
-            for name in getannotations(cls):
-                name = unmangle(cls, name)
-                if name and name not in members:
-                    members[name] = ClassAttribute(cls, name, INSTANCEATTR)
-        except AttributeError:
-            pass
-
-    if analyzer:
-        # append instance attributes (cf. self.attr1) if analyzer knows
-        namespace = '.'.join(objpath)
-        for (ns, name), docstring in analyzer.attr_docs.items():
-            if namespace == ns and name not in members:
-                members[name] = ClassAttribute(subject, name, INSTANCEATTR,
-                                               '\n'.join(docstring))
+    try:
+        for cls in getmro(subject):
+            # annotation only member (ex. attr: int)
+            try:
+                for name in getannotations(cls):
+                    name = unmangle(cls, name)
+                    if name and name not in members:
+                        members[name] = ClassAttribute(cls, name, INSTANCEATTR)
+            except AttributeError:
+                pass
+
+            # append instance attributes (cf. self.attr1) if analyzer knows
+            try:
+                modname = safe_getattr(cls, '__module__')
+                qualname = safe_getattr(cls, '__qualname__')
+                analyzer = ModuleAnalyzer.for_module(modname)
+                analyzer.analyze()
+                for (ns, name), docstring in analyzer.attr_docs.items():
+                    if ns == qualname and name not in members:
+                        members[name] = ClassAttribute(cls, name, INSTANCEATTR,
+                                                       '\n'.join(docstring))
+            except (AttributeError, PycodeError):
+                pass
+    except AttributeError:
+        pass
```

| # | Solution.lean op | patch.diff op (patched worktree line) | tag | justification |
|---|---|---|---|---|
| A1 | param `existing : List String` | the member names in `members` when the walk is reached, from the untouched prefix `importer.py:259-298` | R | `n ∈ members` ↔ `existing.contains n` (mapping.md §2, §3.3). Read-only — not `mut`. G-AX reads it off the real base callee. |
| A2 | param `hierarchy : List ClassLevel` | `getmro(subject)` (`importer.py:301`) with, per class, `getannotations(cls)` (`304`) and that class's own `attr_docs` selection (`313-317`) | R | positional MRO order + the two per-class declaration groups (mapping.md §2, §3.1-3.2). Read-only — not `mut`. |
| A3 | `ClassLevel.owner`, `Member.owner` | `cls` as bound at `importer.py:301` and passed as `ClassAttribute(cls, …)` at `307` and `319`, read back by consumers as `ClassAttribute.class_` | R | class ↔ `'<module>.<qualname>'`, asserted injective on the MRO by G-AX. The pre-change code passed `subject` at the corresponding attribute site, which is precisely what A3 makes observable. |
| A4 | `(c.annots.filter (fun n => n != "")).map (fun n => ⟨n, c.owner, none⟩)` | the annotation phase `importer.py:302-309` | I | `unmangle` at `305` returns `None` for a private identifier owned by another class of the MRO, and the leading `if name` at `306` passes it over — the `· != ""` filter (mapping.md §2). `ClassAttribute(cls, name, INSTANCEATTR)` at `307` is the **3-argument** form, so `docstring` defaults to `None` — the `none` in the model. |
| A5 | `c.attrs.map (fun a => ⟨a.name, c.owner, some a.doc⟩)` | the attribute phase `importer.py:311-320` | I | `ns == qualname` at `318` selects that class's own namespace; `ClassAttribute(cls, name, INSTANCEATTR, '\n'.join(docstring))` at `319-320` supplies both the attribution (`cls`) and a present docstring — the `some` in the model. |
| A6 | `levelCandidates c = A4 ++ A5` | the ORDER of the two phases inside one iteration of `for cls`: `302-309` precedes `311-320` | I | concrete. With `collectStep`'s first-wins guard this gives an identifier a class both annotates and documents the annotation's (absent) docstring — the real effect of `306` claiming the name before `318` is evaluated. |
| A7 | `candidates hierarchy = (hierarchy.map levelCandidates).flatten` | the walk `importer.py:301-324` read as a candidate stream: class k's annotations, then class k's attributes, then class k+1's | I | concrete. Both phases sit inside the `for cls` body, so the interleaving is per class — NOT two hierarchy-wide passes (which is what the pre-change shape was, and what rival `weak-annotation-prepass` is). |
| A8 | the `while` loop over `candidates hierarchy`, each step `result := collectStep existing result a` | the guards `if name and name not in members` (`306`) and `if ns == qualname and name not in members` (`318`) with the assignments under them | I | concrete, transliterated by G-CONF. `collectStep` skips a candidate whose name is in `existing` (already a member) or already collected (`acc.any … name`), matching `name not in members` against the growing dict; otherwise appends. First occurrence wins, which is what `not in members` enforces as the walk runs most-derived-first. |
| A9 | `out = collected existing (candidates hierarchy)` (return `result`) | the returned `members` (`importer.py:326`) restricted to the entries this walk created (`value is INSTANCEATTR`) | R | `name ↦ (class_, docstring)` map ↔ `List Member` (mapping.md §2). Dict insertion order is not observable; `class_` and `docstring` are (`__init__.py:1602-1606`). |

## B. Independently-observable behaviours, and the prepatch twin for each

G-DIFF requires one failing `Solution_prepatch*.lean` per independently-observable
behaviour the change fixes. This patch has **three**, and each is frozen by its
own twin. All three twins share the frozen spec byte-for-byte (`markers.same_spec`
= True) and each fails with exactly one `error: unsolved goals` on
`ensures_1` — measured.

| twin | pre-change behaviour it reproduces | the patched line that refutes it | observable |
|---|---|---|---|
| `Solution_prepatch.lean` | documented attributes gathered from the **subject's namespace only** (`namespace = '.'.join(objpath)`), annotations still walked MRO-wide | `importer.py:314,318` — the namespace key is `cls.__qualname__` per class | an attribute documented only on a base class is never gathered, so it cannot be rendered even with `inherited-members` |
| `Solution_prepatch_attribution.lean` | the whole hierarchy walked for attributes, but every gathered attribute recorded as belonging to `subject` (`ClassAttribute(subject, …)`) | `importer.py:319` — the first argument is `cls` | `__init__.py:1606`'s `m.class_ == self.object` filter: a base class's attribute would be listed among a subclass's OWN members |
| `Solution_prepatch_annotation_prepass.lean` | the two phases as two hierarchy-wide passes: every class's annotations first, then every class's attributes | `importer.py:302-320` — both phases sit inside one `for cls` body | for an identifier a base class annotates and a subclass documents, which declaration wins is decided by hierarchy position, not by declaration kind |

The second and third are genuinely independent of the first: each walks the whole
hierarchy and gathers exactly the same member NAMES as the patched function. They
diverge only in the attribution component and in the interleaving respectively —
which is why `Member.owner` and the per-class grouping of `candidates` are part of
the spec (mapping.md §2.1) rather than left free. The caller edit at
`__init__.py:1587` (dropping the now-unused `analyzer` argument) is a mechanical
signature follow-through with no independent observable and needs no twin.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operations that genuinely changed — the namespace
the documented attributes are gathered from (widened from the subject to each
class), the class each gathered attribute is attributed to, and the merging of the
two phases into one per-class body — are modeled **directly** (A4-A9, all I), not
hidden behind an axiom about the function under change. There is **no consumed
axiom and no deep-model reference**: `getmro`, `getannotations`, `unmangle`,
`ModuleAnalyzer.attr_docs` and the pre-collected member set are unchanged
read-only structural descriptors captured by the inputs `existing`/`hierarchy`,
validated against the real callees by G-AX (mapping.md §3). Their faithful
abstraction is a refinement (R), not an axiom.

## D. verify(Solution) ⇒ resolved

`collectInstanceAttrDocs` verifies only if its output equals the first-wins
collection over the per-class candidate stream of the WHOLE hierarchy — with each
member's attribution and its present-or-absent docstring (A4-A9). By R
(mapping.md §2) that collection is the patched `get_class_members` output on the
`INSTANCEATTR` entries, read as `name ↦ (class_, docstring)`. So:

* the F2P scenario (`tests/test_ext_autodoc_autoclass.py::test_inherited_instance_variable`,
  `Bar(Foo)` with `:inherited-members:`) renders `attr1` because the base class's
  documented attribute is gathered at all (A7/A9; `Solution_prepatch.lean` fails
  here);
* the P2P scenario `test_instance_variable` (same fixture, members-only) renders
  `Bar.attr2`/`Bar.attr3` and NOT `attr1`, because `attr1` is attributed to `Foo`
  and `__init__.py:1606` filters it out (A3; `Solution_prepatch_attribution.lean`
  fails here). A spec pinning only names and docstrings would admit an impl that
  breaks this test while passing the F2P one.

By G-AX the structural abstraction is sound; by G-CONF the R/I transliteration
agrees with the real patched `get_class_members` — name, attribution and docstring
together — on 20012 generated hierarchies with 0 disagreements. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement, and the gold patch resolves (G-RESOLVE). The only trust points are
refinement fidelity (this doc, G-EQ + G-CONF) and structural-abstraction
soundness (G-AX); there is no axiom-soundness trust point because no axiom is
consumed.

## E. G-CONF discrimination (why the 0 disagreements mean something)

`conformance_check.py` compares the transliterated model to the real patched
function on the full observable (`{name: (owner_key(attr.class_), attr.docstring)}`
over the `INSTANCEATTR` entries), and separately asserts on every input that its
transliteration of the untouched prefix (`importer.py:259-298`) equals the real
callee's non-`INSTANCEATTR` names — so `existing` is measured, not assumed. Its
generator emits the shapes that make the three §B observables fork: bases in a
different module, classes that both annotate and document one identifier,
identifiers documented on two classes, mangled private annotations, `__slots__`,
class attributes, and diamond MROs. Three negative controls, run against the same
oracle, each FAIL:

| control | perturbation | fails on |
|---|---|---|
| A | every member attributed to the subject | the F2P `Bar(Foo)` fixture: `attr1` reported as `Bar`'s, oracle says `Foo`'s |
| B | annotations hoisted into one hierarchy-wide prepass | a base annotation vs. a subclass docstring for one identifier |
| C | only the subject's own class walked | any base-declared documented attribute |

So a 0-disagreement run is a measurement of agreement, not an artefact of a
comparison too coarse to disagree.
