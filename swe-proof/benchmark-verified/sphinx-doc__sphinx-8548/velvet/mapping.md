# mapping.md — sphinx-doc__sphinx-8548

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = dd1615c59dc6fff633e27dbb3861f2d27e1fb976`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the read-only callees the direct model depends on.

Repo files under change: `sphinx/ext/autodoc/importer.py` (the modeled function)
and `sphinx/ext/autodoc/__init__.py` (the caller, §3.4). Line numbers below are
those of the **patched** worktree (`patch.diff` applied at `base_commit`); where a
pre-change line is quoted it is marked as such.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line, patched worktree) | role |
|---|---|---|
| `collectInstanceAttrDocs (existing : List String) (hierarchy : List ClassLevel) return (out : List Member)` | `get_class_members(subject, objpath, attrgetter)` — `sphinx/ext/autodoc/importer.py:254`, body of the hierarchy walk at 300-324 | the modeled changed function |
| `ClassLevel` | one class of `getmro(subject)` together with the two groups of declarations the walk reads from it: `getannotations(cls)` (`importer.py:304`) and that class's own analyzer entries (`importer.py:313-317`) | one class of the hierarchy |
| `ClassLevel.owner` | the `cls` bound by `for cls in getmro(subject)` (`importer.py:301`), i.e. the first argument of every `ClassAttribute(cls, …)` the walk constructs (`importer.py:307`, `319`) | which class a declaration belongs to |
| `ClassLevel.annots` | `[unmangle(cls, name) for name in getannotations(cls)]` (`importer.py:304-305`) | that class's annotation-only member names |
| `ClassLevel.attrs` / `AttrDoc` | `{(ns, name) ↦ '\n'.join(docstring) : ns == qualname}` over `ModuleAnalyzer.for_module(safe_getattr(cls,'__module__')).attr_docs` (`importer.py:313-320`) | that class's own-namespace documented instance attributes |
| `Member` | one value of the `members` dict the function returns (`importer.py:326`), restricted to the entries the walk creates | one surfaced member |
| `Member.owner` | `ClassAttribute.class_` (`importer.py:246-252`, assigned `cls` at 307 and 319) | the class the surfaced member is attributed to |
| `Member.doc` | `ClassAttribute.docstring`: absent at `importer.py:307` (the 3-argument `ClassAttribute(cls, name, INSTANCEATTR)`, so `docstring is None`), `'\n'.join(docstring)` at `importer.py:319-320` | the surfaced member's docstring, or its absence |
| `levelCandidates` | the body of one iteration of `for cls in getmro(subject)`: the annotation phase (`importer.py:302-309`) **followed by** the attribute phase (`importer.py:311-320`) | one class's candidates, in the order the walk meets them |
| `candidates` | the whole `for cls in getmro(subject)` walk (`importer.py:301-324`) read as the stream of candidates it considers | the candidate stream |
| `collectStep` | the two admission guards `if name and name not in members` (`importer.py:306`) and `if ns == qualname and name not in members` (`importer.py:318`), against the growing `members` dict | first-occurrence admission |
| `collected` | the assignment `members[name] = ClassAttribute(…)` performed under those guards as the walk runs | the hierarchy-wide first-wins collection |

`existing`/`hierarchy` are read-only structural descriptors (not `mut`): the
function reads `getmro(subject)`, each class's `__module__`/`__qualname__`, each
class's annotations, and each module's `ModuleAnalyzer.attr_docs`; it never
mutates them. The `members` dict it builds is the *output*, modeled by `out`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the k-th class of `getmro(subject)` (most-derived-first; `sphinx/util/inspect.py:173`) | the k-th element of `hierarchy : List ClassLevel` | positional: the **order** of `hierarchy` IS the MRO order. G-AX asserts `getmro` leads with the subject and has pairwise-distinct entries |
| a class's identity | `ClassLevel.owner : String` and `Member.owner : String` | `'%s.%s' % (cls.__module__, cls.__qualname__)`. G-AX asserts this key is **injective** on `getmro(subject)`, so owner equality in Lean is class identity in Python — which is what `m.class_ == self.object` (`sphinx/ext/autodoc/__init__.py:1606`) tests |
| `unmangle(cls, name)` for `name in getannotations(cls)` (`importer.py:304-305`) | one entry of `ClassLevel.annots : List String`, in `__annotations__` iteration order | `str` ↔ itself; **`None` ↔ `""`**. `unmangle` returns `None` for a private identifier owned by a different class of the MRO, and `importer.py:306`'s leading `if name` then passes it over — modeled by `annots.filter (· != "")` |
| a documented instance attribute `((ns, name), docstring)` with `ns == cls.__qualname__` | one entry of `ClassLevel.attrs : List AttrDoc`, in `attr_docs` iteration order | `name` ↔ `AttrDoc.name`; `'\n'.join(docstring)` ↔ `AttrDoc.doc` (the analyzer appends a trailing `''` line, so both sides of every comparison join identically and the trailing blank cancels) |
| the member names already in `members` when the hierarchy walk is reached — the enum (`importer.py:264-275`), `__slots__` (`importer.py:277-286`) and `dir(subject)` (`importer.py:288-298`) phases | `existing : List String` | `n ∈ members.keys()` ↔ `existing.contains n`. That prefix is **unchanged** by the patch; G-AX asserts the transliteration of it (§3.3) equals the non-`INSTANCEATTR` names the REAL base `get_class_members` reports |
| one `ClassAttribute` the walk creates, i.e. a `members` value with `value is INSTANCEATTR` | `Member {name, owner, doc}` | `name` ↔ `.name`; `class_` ↔ `.owner` via the identity key above; `docstring` ↔ `.doc` with **`None` ↔ `none`** and `str` ↔ `some` |
| the returned `members` dict restricted to `value is INSTANCEATTR` | `out : List Member` | as a `name ↦ (owner, doc)` map. A consumer renders `docstring` and selects members by comparing `class_` (`__init__.py:1602-1606`), so both components are observable; dict insertion order is not, so the map comparison is order-insensitive |

`List Char`/indexing subtleties do not arise — the carrier is structural records,
not strings-as-code-points.

### 2.1 Why `owner` and `doc` are modeled and not elided

`sphinx/ext/autodoc/__init__.py:1601-1606` reads the collection twice with two
different projections:

```
elif self.options.inherited_members:
    return False, [ObjectMember(m.name, m.value, docstring=m.docstring)
                   for m in members.values()]
else:
    return False, [ObjectMember(m.name, m.value, docstring=m.docstring)
                   for m in members.values() if m.class_ == self.object]
```

The `else` branch — the default, taken whenever `inherited-members` is not
requested — filters on `m.class_`, so the class each surfaced member is
attributed to decides whether it is listed at all. A spec that pinned only the
member names and docstrings would leave that filter's input free, and an impl
attributing every gathered member to the documented class would satisfy it while
changing the default rendering of every subclass. `Member.owner` is therefore a
required observable, not decoration; `weak-subject-attribution` in
`properties.py` is that impl, and it is rejected. Likewise `docstring` is passed
straight to `ObjectMember`, and `None` (`importer.py:307`) is not `''`
(`importer.py:319`) to a consumer that falls back when documentation is absent,
so `Member.doc` is `Option String` rather than `String`.

## 3. Callee provenance — the read-only structural helpers (checked by G-AX)

This bundle has **no consumed axiom and no deep-model reference to a foreign
callee**: the changed collection is modeled DIRECTLY by
`levelCandidates`/`candidates`/`collectStep`/`collected` (refinement.md §C). The
helpers the direct model abstracts are all **unchanged** and **read-only**; G-AX
validates that the abstraction into `existing`/`hierarchy` is faithful, by
executing those helpers at the base commit and comparing them against ground
truth known from the generated source.

### 3.1 `getmro` → the order of `hierarchy`
**Callee (unchanged):** `sphinx.util.inspect.getmro` (`sphinx/util/inspect.py:173`)
returns `subject.__mro__`, most-derived-first. `importer.py:301` walks it in that
order, and `importer.py:306`/`318`'s `name not in members` gives the first
contributor of an identifier precedence — so hierarchy position decides which
class's declaration survives. G-AX asserts the order, distinctness, and injectivity
of the identity key on it.

### 3.2 per-class `getannotations` and `ModuleAnalyzer.attr_docs` → `ClassLevel`
**Callees (unchanged):** `sphinx.util.inspect.getannotations`;
`ModuleAnalyzer.for_module(modname)` + `analyze()`
(`sphinx/pycode/__init__.py:111,161`) yielding `attr_docs` keyed
`((ns, name), docstring)` where `ns` is the **defining class's** `__qualname__`.
Two facts the model depends on, both asserted by G-AX against generated ground
truth:

* the analyzer is built from **that class's own** `__module__`
  (`importer.py:313,315`), so a base class living in a different module
  contributes its documented attributes — a per-class lookup, not one lookup for
  the subject's module;
* `cls.__annotations__` is reached through `getattr`, so a class declaring none
  inherits its nearest ancestor's. G-AX therefore does not assert that `annots`
  contains *only* that class's own annotations; it asserts that every identifier
  the class itself annotates is present, and that a private identifier annotated
  by a *different* class of the MRO is present as `""` (because `unmangle`
  returns `None` there). The count of such `""` slots is asserted non-zero, so
  the clause cannot pass vacuously.

Both phases are read in one class's iteration before the next class is reached
(`importer.py:302-309` then `311-320`, both inside the `for cls` body), which is
exactly `levelCandidates`' concatenation and is why `candidates` maps
`levelCandidates` over the hierarchy rather than concatenating two
hierarchy-wide passes.

### 3.3 the pre-collected member names → `existing`
**Callee (unchanged):** the prefix of `get_class_members` at
`importer.py:259-298` (enum members, `__slots__`, `dir(subject)`) populates
`members` before the hierarchy walk; `importer.py:306`/`318`'s `name not in
members` consults it. The patch does not touch those lines. G-AX transliterates
that prefix and asserts, on every input, that it equals the non-`INSTANCEATTR`
member names the REAL base-commit `get_class_members(subject, objpath,
attrgetter)` reports when called with the `analyzer` argument omitted (its
attr-doc phase is then inert), so `existing` is read off the real callee rather
than restated. `existing` is a general input with no precondition: nothing
restricts it to the empty list, and `weak-ignore-existing` in `properties.py`
pins that the spec depends on it.

### 3.4 the caller — `ClassDocumenter.get_object_members`
**Site:** `sphinx/ext/autodoc/__init__.py:1587` calls
`get_class_members(self.object, self.objpath, self.get_attr)`; the patch drops
the `self.analyzer` argument it used to pass, because the patched function builds
an analyzer per class internally (`importer.py:315`). The call is a mechanical
consequence of the signature change and carries no independent observable
behaviour of its own. Its **surrounding** lines are not neutral, though, and are
the reason for §2.1: `1602-1603` list every member, `1605-1606` list only those
with `m.class_ == self.object`. G-RESOLVE covers the whole patch.

**Soundness check (G-AX):** `axiom_check.py` builds real Python modules and class
hierarchies (documented instance attributes via real `#:` comments, real
annotations including mangled ones, `__slots__`, class attributes, cross-module
bases, diamond MROs) and asserts, against the REAL callees at the base commit:
(1) the MRO shape and identity-key injectivity of §3.1; (2) `annots` per §3.2,
including the non-vacuity of the `""` slot; (3) `attrs` equal to the documented
attributes written in that class's body, in source order, including for a base
class in another module; (4) `existing` equal to the real base callee's
non-`INSTANCEATTR` names per §3.3; and (5) that the model is **discriminating** —
the REAL base `get_class_members` driven with the subject's analyzer omits the
inherited `attr1` of the F2P fixture entirely, while the model surfaces it
attributed to the class whose body declares it. It restates nothing about the
changed collection: that is G-CONF's job, against the real patched function.
Imports only `sphinx` + stdlib. Exit 0 iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8548`** so the
consumer-side verdict is reproducible. It builds real modules, abstracts each
subject with the §2 bijection, and compares a Python transliteration of
`collected existing (candidates hierarchy)` against the REAL patched
`get_class_members` observed as `{name: (class_ identity, docstring)}` over the
`INSTANCEATTR` entries — name, attribution and docstring together, on 20012
generated hierarchies (0 disagreements). Three negative controls (attribute every
member to the subject; hoist the annotations into one hierarchy-wide prepass;
walk only the subject's class) each FAIL that comparison, so the check is
discriminating and not a tautology. There is no A-tagged callee in the impl
region, so the shadow is pure R/I and `conf_skip` is **false**.
