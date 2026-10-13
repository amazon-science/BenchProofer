# mapping.md — sphinx-doc__sphinx-8548

## Symbol binding (file:line @ base_commit dd1615c59dc6fff633e27dbb3861f2d27e1fb976)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_gatherMemberDocs` / `problem_spec_gatherMemberDocs` | the whole `for cls in getmro(subject)` member-collection loop at the tail of `get_class_members` — BOTH the annotation-only pass and the attribute-docstring pass it now encloses | `sphinx/ext/autodoc/importer.py:300-327` (post-patch) |
| `gatherMemberDocs` (pure helper) | the post-patch loop walking `getmro(subject)`, consulting per class that class's own `__annotations__` and then its own `attr_docs` namespace | `sphinx/ext/autodoc/importer.py:300-327` (post-patch) |
| `addAnnotations` (pure helper) | the `for name in getannotations(cls): name = unmangle(cls, name); if name and name not in members` body — the annotation-only pass, run per MRO class | `sphinx/ext/autodoc/importer.py:302-308` (post-patch) |
| `addEntries` (pure helper) | the inner `for (ns, name), docstring in analyzer.attr_docs.items(): if ns == qualname and name not in members` body | `sphinx/ext/autodoc/importer.py:317-322` (post-patch) |
| `ClassInfo` (pure type) | a class in the MRO together with its own identity, the names it annotates (`getannotations(cls)`) and the comment-style attribute docstrings recorded for the module that defines it (`ModuleAnalyzer.for_module(modname).attr_docs`) keyed by `(namespace, name)` | `sphinx/ext/autodoc/importer.py`, `sphinx/pycode/__init__.py` `ModuleAnalyzer.attr_docs` |
| `MemberEntry` (pure type) | one entry of the `members` dict: `ClassAttribute`'s `name`, `docstring` and `class_` | `sphinx/ext/autodoc/importer.py:244-251` (`class ClassAttribute`) |
| `MemberEntry.owner` | `ClassAttribute.class_` — the class recorded with the entry; written `cls` by BOTH passes post-patch (`subject` by the docstring pass pre-patch) and read back by the consumer's own-members filter | writes `sphinx/ext/autodoc/importer.py:307` and `:319`; read `sphinx/ext/autodoc/__init__.py:1606` |

The modeled fragment is the `for cls in getmro(subject)` loop at the tail of
`get_class_members`, and it comprises BOTH passes that loop contains post-patch:
the annotation-only pass (`attr: int`, contributing a name with NO docstring) and
the attribute-docstring pass (`self.attr = …  #: doc`, contributing a name with the
docstring the `ModuleAnalyzer` recovered).

Modeling BOTH is load-bearing rather than incidental thoroughness. The gold patch's
structural change was to MOVE the attribute-docstring pass INSIDE the MRO loop the
annotation-only pass already had, so post-patch the two run INTERLEAVED, one class
at a time. Under `name not in members` (first-occurrence-wins) that interleaving is
OBSERVABLE: when a base class annotates a name that a more-derived class documents,
the real loop reaches the derived class first and records its docstring, whereas
treating the annotation-only pass as fully applied before the docstring pass lets
the base's bare annotation land first and pre-empt the docstring. A previous
revision of this bundle folded the annotation-only pass into `initial` up-front and
so predicted no docstring where the real callee produces one; see "Interleaving" in
the notes below for the reproduced witness. Hence `initial` is only the passes that
run BEFORE the loop (enum members, `__slots__`, `dir(subject)`), all UNCHANGED by
the patch, and we model the function from that table forward.

The FAIL_TO_PASS test (`test_inherited_instance_variable`) observes the
docstring pass reaching base classes; the interleaving clause is what keeps the
model faithful on the neighbouring inputs where the two sources meet.

### What the modeled fragment does

base_commit (`importer.py`) — the annotation-only pass walks the whole MRO, then
the attribute-docstring pass runs ONCE for a single namespace:
```python
# annotation only member (ex. attr: int)
for cls in getmro(subject):
    try:
        for name in getannotations(cls):
            name = unmangle(cls, name)
            if name and name not in members:
                members[name] = ClassAttribute(cls, name, INSTANCEATTR)
    except AttributeError:
        pass

if analyzer:
    # append instance attributes (cf. self.attr1) if analyzer knows
    namespace = '.'.join(objpath)
    for (ns, name), docstring in analyzer.attr_docs.items():
        if namespace == ns and name not in members:
            members[name] = ClassAttribute(subject, name, INSTANCEATTR,
                                           '\n'.join(docstring))
```

- The attribute-docstring pass runs ONCE, for a single `namespace =
  '.'.join(objpath)` — the qualified name of the TARGET class only. The
  `attr_docs` recorded for any base class (under the base class's own namespace)
  are never consulted, so an instance attribute declared on a base class
  (`self.attr1` in `Foo`, documented `#: docstring foo`) is dropped when
  documenting the derived class `Bar` with `:inherited-members:` — the bug.

post-patch (`patch.diff`):
```python
try:
    for cls in getmro(subject):
        # annotation only member (ex. attr: int)
        try:
            for name in getannotations(cls):
                name = unmangle(cls, name)
                if name and name not in members:
                    members[name] = ClassAttribute(cls, name, INSTANCEATTR)
        except AttributeError:
            pass

        # append instance attributes (cf. self.attr1) if analyzer knows
        try:
            modname = safe_getattr(cls, '__module__')
            qualname = safe_getattr(cls, '__qualname__')
            analyzer = ModuleAnalyzer.for_module(modname)
            analyzer.analyze()
            for (ns, name), docstring in analyzer.attr_docs.items():
                if ns == qualname and name not in members:
                    members[name] = ClassAttribute(cls, name, INSTANCEATTR,
                                                   '\n'.join(docstring))
        except (AttributeError, PycodeError):
            pass
except AttributeError:
    pass
```

- The attribute-docstring pass now runs INSIDE the `for cls in getmro(subject)`
  loop, once per class in the inheritance chain. For each class it analyzes that
  class's own module and consults the `attr_docs` recorded under THAT class's own
  `__qualname__` (`if ns == qualname`). Because the chain is walked most-derived
  first and `name not in members` is checked, a redefined attribute keeps the
  most-derived occurrence while an attribute declared only on a base class is now
  collected. This is exactly the fix: inherited instance attributes appear.
- The recorded `ClassAttribute` also changes its FIRST argument: pre-patch the
  docstring pass built `ClassAttribute(subject, name, …)`, post-patch it builds
  `ClassAttribute(cls, name, …)` (`importer.py:319`) — the class the loop is
  visiting, matching what the annotation pass already recorded (`:307`). That
  argument lands in `ClassAttribute.class_` and is read back by the consumer at
  `sphinx/ext/autodoc/__init__.py:1606`:
  ```python
  return False, [ObjectMember(m.name, m.value, docstring=m.docstring)
                 for m in members.values() if m.class_ == self.object]
  ```
  so it decides, on the default (no `:inherited-members:`) path, which of the
  collected members a class documents as its OWN. It is therefore an observable
  output component of the modeled fragment, not a constant — see "Recorded owner"
  in the notes below for the measurement that settles it.

The `annotation only member` pass keeps the same body and the same
`name not in members` guard, but the patch changes WHEN it runs relative to the
docstring pass: pre-patch it completes over the whole MRO before any docstring is
consulted, post-patch the two alternate per class. That relative order is part of
the modeled behavior (see Interleaving below), so BOTH passes are in the bijection
and only the pre-loop passes are folded into `initial`.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| the MRO `getmro(subject)`, most-derived first | `mro : List ClassInfo` | element `i` ↔ the `i`-th class in the MRO; the empty MRO ↔ `[]`. |
| a class `cls` in the MRO | `ClassInfo` | `classKey` ↔ the class OBJECT's identity, under any injective encoding (G-CONF uses a per-`id(cls)` token, kept alive in its table); `nsKey` ↔ `cls.__qualname__` (post-patch key); `annNames` ↔ `[unmangle(cls, n) for n in getannotations(cls)]` with the falsy results dropped (`if name and …`), in `__annotations__` order; `attrDocs` ↔ the list of `((ns, name), docstring)` entries in `ModuleAnalyzer.for_module(cls.__module__).attr_docs`, flattened to `(ns, name, '\n'.join(docstring))` triples in `attr_docs` iteration order. A class whose module cannot be analyzed (`PycodeError`) or which has no `__annotations__` (`AttributeError`) ↔ the corresponding field `[]`. |
| an `attr_docs` entry `((ns, name), docstring)` | `(String × String × String)` = `(ns, name, joinedDoc)` | `ns` ↔ entry namespace; `name` ↔ attribute name; `joinedDoc` ↔ `'\n'.join(docstring)`. |
| the `members` dict, restricted to `(name, docstring, class_)` and insertion order | `List MemberEntry` (assoc list) | `members[name].docstring` ↔ `doc`; `members[name].class_` ↔ `owner`; the dict key ↔ `name`; key set + first-insertion order preserved. `None` docstring ↔ `none` and a recovered docstring ↔ `some s`. The `Option` is load-bearing, not decoration: `ClassAttribute.docstring` is genuinely `None` for an annotation-declared member and `'\n'.join(docstring)` for a documented one, and an empty comment (`#:` with no text) yields `some ""` — a value distinct from `none`, verified in the container. `owner` is `Option String` for the same reason: the pre-loop `dir(subject)` pass really does record `ClassAttribute(None, unmangled, value)` for an inherited name (`importer.py:293` pre-patch), so `none` is a REACHABLE owner in `initial`, while everything the modeled fragment itself collects is `some`. |
| the dict key vs `ClassAttribute.name` | one `MemberEntry.name` field, not two | the two are equal by construction at every write in this file (`members[name] = ClassAttribute(cls, name, …)`, and `unmangled` for the pre-loop pass), and the consumer reads `m.name` while the collection guard reads the key — so a carrier with two independent fields would admit tables the real code cannot build. MEASURED that they must not be allowed to diverge rather than assumed equal: a gold-derived patch storing a different string in `ClassAttribute.name` than the dict key fails 2 of the 6 tests in `tests/test_ext_autodoc_autoclass.py`. Modeled as ONE datum; the equality is the well-formedness of the bijection, not a spec clause. |
| `ClassAttribute(cls, name, INSTANCEATTR[, doc])` — the `cls` argument | `owner := some cls.classKey` | the class recorded with a collected member is the chain member being visited, for BOTH sources (`importer.py:307`, `:319`). Pre-patch the docstring pass recorded `subject` instead — the head of the chain — which is the divergence the prepatch twin carries. |
| `ClassAttribute.value` (`INSTANCEATTR` / `SLOTSATTR`) | *not modeled* | frame. Inside the modeled fragment both writes pass the SAME constant `INSTANCEATTR`, so the fragment never chooses this field as a function of its inputs — a constant carries no information about the collection behavior the patch changed. Measured rather than asserted: a gold-derived patch substituting `None` for that constant in the docstring branch — the branch the patch rewrites — still resolves the instance (6/6 in `tests/test_ext_autodoc_autoclass.py`), and the annotation branch's write is patch-unchanged byte-for-byte. |
| `name not in members` | `entry.snd.fst ∉ members.map MemberEntry.name` (docstring pass) / `name ∉ members.map MemberEntry.name` (annotation pass) | membership by key; first occurrence wins. Both passes test the SAME growing table, which is what makes their relative order observable. |
| the per-class body: annotation block, then docstring block | `addEntries cls.nsKey cls.classKey cls.attrDocs (addAnnotations cls.classKey cls.annNames members)` | the annotation block runs first for that class, then the docstring block, then the loop advances — `addAnnotations` applied innermost. Both take the visited class's identity, because both record it. |
| `if ns == qualname` (post-patch) — does this entry belong to `cls`? | `entry.fst = cls.nsKey` | a `attr_docs` entry is collected for `cls` iff its recorded namespace equals `cls`'s own qualname. |

Modeling notes:
- The model carries each class's `attr_docs` as an INPUT (`ClassInfo.attrDocs`).
  In Python `ModuleAnalyzer.for_module(modname).attr_docs` is the unchanged callee
  that produces these; the patch does not change *what* `attr_docs` contains, only
  *which* class's `attr_docs`/namespace are consulted and *how many* classes in the
  chain. So `attr_docs` is environmental input, not an axiomatized callee.
- `members.map MemberEntry.name` models the dict key set; appending only when the key
  is absent models `if name not in members`. `initial` is the table built by the passes
  that run BEFORE the MRO loop only — enum members, `__slots__`, and the
  `dir(subject)` pass — all unchanged by the patch. The annotation-only pass is NOT
  part of `initial`: it lives inside the modeled loop.
- **Interleaving (the clause a faithfulness review found missing).** Because both
  passes guard on the same growing table, folding the annotation pass in up-front
  is NOT equivalent to interleaving it. Reproduced against the gold-patched repo
  in the instance container, with `Base` annotating `x: int` and `Derived(Base)`
  documenting `self.x = 1  #: derived x doc`: the real
  `get_class_members(Derived, ['Derived'], safe_getattr)` returns `x` with
  `docstring='derived x doc\n'` (and `class_=Derived`), because the loop reaches
  `Derived` first, whose `__annotations__` hold only `y`, and `Derived`'s
  `attr_docs` entry for `x` is then recorded. A model that applies every class's
  annotations first has `x` already present (from `Base`) and yields `None`. The
  repaired model interleaves, and predicts `[("y", none), ("x", some "derived x
  doc\n")]` — the real value. Base commit yields `None` there too, but for the
  DIFFERENT reason that its docstring pass never runs for a non-target namespace.
- The base-commit single-namespace key `'.'.join(objpath)` and the post-patch
  per-class `cls.__qualname__` coincide for the target (head) class, which is why
  the only observable difference is whether base-class attributes are collected —
  captured by walking the whole `mro` vs only its head.
- **Recorded owner (the clause a spec-too-weak break found missing).** An earlier
  revision of this carrier projected `ClassAttribute.class_` away and defended the
  omission as a frame ("constant for this pass, fixed not chosen"). That claim was
  FALSE, and the falseness was demonstrated, not argued: the gold patch with the
  single token `cls` → `subject` in the docstring branch (`importer.py:319`) shares
  this bundle's spec byte-for-byte, verified in 6.7s, and yet fails the instance —
  `FAIL_TO_PASS test_inherited_instance_variable` still PASSES (the attribute is
  still found, with the right docstring, in the right order) while `PASS_TO_PASS
  test_instance_variable` FAILS, because with `:inherited-members:` off the consumer
  keeps only `m.class_ == self.object` (`__init__.py:1606`) and the base's attribute
  now claims to be the derived class's own. Measured in the instance container: 1
  failed, 1 passed, against 6/6 for the gold patch. The field is thus an observable
  the fragment CHOOSES per entry, and the carrier now records it (`MemberEntry.owner`)
  with `problem_spec_gatherMemberDocs` pinning it. Two data are deliberately kept
  apart: `ClassInfo.classKey` (the class's identity, which is what the consumer's
  `==` compares) and `ClassInfo.nsKey` (its `__qualname__`, which is what the entry's
  namespace is matched against). They are NOT interchangeable — two classes on one
  chain can share a `__qualname__` (name shadowing, or a class factory), and a patch
  that stored the qualname in `class_` would make the consumer's identity test reject
  every collected member. G-CONF drives both lanes on the owner and includes a
  shared-`__qualname__` shape for exactly this reason.

## Callee provenance + flag dependencies

- **`mro`, `ClassInfo.attrDocs` — INPUTS, not consumed callees.** `getmro(subject)`
  and `ModuleAnalyzer.for_module(...).attr_docs` produce the chain and the
  per-class documented attributes; the patch does not change their contents, only
  the control flow that consumes them (one namespace → every class's namespace
  along the chain). They are environmental inputs to the modeled function. Hence
  the `axioms` region declares no `opaque`/`axiom` (no `_prop` consumed).
- **`ClassInfo.annNames` — an INPUT too.** `getannotations(cls)` and `unmangle` are
  unchanged by the patch; only when their results are consumed relative to the
  docstring pass changes. So the annotation names are environmental input as well,
  not an axiomatized callee.
- **`gatherMemberDocs` / `addAnnotations` / `addEntries` — the changed control flow,
  modeled deeply (R/I).** The fix moves the attribute-docstring pass inside the MRO
  loop, keys it on each class's own qualname, and thereby interleaves it with the
  annotation pass. Modeled structurally by recursion over the chain and each entry
  list — NEVER axiomatized (SPEC_GUIDE §3). G-CONF differential-tests it against the
  REAL callee.
- **Flag dependencies.** Whether `:inherited-members:` is set governs upstream
  filtering (whether base-class members are *displayed*), but the collection pass
  modeled here always gathers them post-patch; the display filter is a separate,
  unchanged downstream step. The `PycodeError`/`AttributeError` guards added by the
  patch are defensive (a class whose module cannot be analyzed contributes no
  entries) and correspond to that class's `attrDocs = []` in the model.

## G-CONF corpus + seed

Pinned seed: **8548** (see `conformance_check.py` `SEED`). TWO lanes, because a
replica-only oracle is what let the interleaving drift through: a replica can only
confirm the model's own assumptions, and the previous revision's replica shared the
model's flattening.

- **lane=real (load-bearing).** 600 generated class hierarchies, each written to a
  module, imported, and driven through the REAL post-patch
  `get_class_members`; `initial` is computed by replaying the patch-unchanged
  pre-loop passes, and `mro` is bridged from the live classes. Shapes include the
  interleaving case (a base annotating what a derived class documents), diamonds
  with a non-trivial MRO, `__slots__`, enums, nested qualnames, mangled names,
  empty `#:` docstrings, and two DISTINCT classes on one chain sharing a
  `__qualname__` (so the recorded identity cannot be recovered from the namespace
  key). The comparison includes the recorded owner: the real `ClassAttribute.class_`
  is bridged through an identity-injective token and compared entry by entry. The
  lane FAILS if no generated hierarchy credits a member to a class other than the
  target, so the owner clause cannot go untested; the current corpus has 212 of 600
  such cases (and 577 exercising the interleaving clause). If Sphinx cannot be
  imported the script FAILS rather than falling back, so this lane cannot silently
  vanish.
- **lane=fuzz.** ≥1e5 cases over the bijected carrier directly (1–5 classes, small
  name/namespace/docstring alphabets, an identity independent of the namespace key
  so chain classes may share a key, entries whose `ns` does NOT match the class's
  `nsKey`, duplicate names across classes, annotation names colliding with
  documented ones, and a seeded `initial` whose owners include the `none` the
  `dir()` pass produces), against an in-process replica of the post-patch nested
  loop. It reaches combinations generated source cannot express and asserts the
  corpus still discriminates BOTH the prepatch behavior (35651 of 120000 cases) and
  the target-credited-owner rival that broke the previous revision of this spec
  (24173 of 120000).

Both lanes additionally pin the FAIL_TO_PASS shape, the interleaving witness, and
the shared-`__qualname__` shape as explicit assertions; the FAIL_TO_PASS assertion
records that the target-credited-owner rival agrees on every name and docstring
there and differs ONLY in the class credited with the inherited attribute. G-AX is a skip stub (no consumed axiom; the only deep model is
the pure control flow over the bijected `ClassInfo` chain, exercised by G-CONF).
