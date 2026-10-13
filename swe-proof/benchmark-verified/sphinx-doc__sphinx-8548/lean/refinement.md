# refinement.md — sphinx-doc__sphinx-8548

Maps every operation in `implementation_gatherMemberDocs` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `gatherMemberDocs` (the `for cls in getmro(subject)` member-collection loop of `get_class_members`)

Post-patch repo code (`patch.diff`, `sphinx/ext/autodoc/importer.py:300-327`):
```python
try:
    for cls in getmro(subject):
        # annotation only member (ex. attr: int)  -- INSIDE the loop; modeled
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

Lean impl (`implementation_gatherMemberDocs`):
```lean
def implementation_gatherMemberDocs (mro : List ClassInfo)
    (initial : List MemberEntry) : List MemberEntry := Id.run do
  let mut members := initial
  for cls in mro do
    for name in cls.annNames do
      if name ∉ members.map MemberEntry.name then
        members := members ++ [⟨name, none, some cls.classKey⟩]
    for entry in cls.attrDocs do
      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
  return members
```

**Owner note.** The `class_` argument of the recorded `ClassAttribute` is part of
this fragment's output, not part of its frame. An earlier revision of this bundle
omitted it as "constant for this pass"; that was refuted with a real build plus a
real harness run (see mapping.md "Recorded owner"), so `MemberEntry.owner` is now an
observable component and every write of it is a row below.

**Scope note.** An earlier revision modeled only the docstring pass and folded the
annotation-only pass into `initial`. That was UNFAITHFUL: both passes guard on the
same growing `members`, and the patch moved the docstring pass inside the loop the
annotation pass already had, so their per-class alternation is observable. See
mapping.md "Interleaving" for the reproduced witness. Both passes are therefore in
scope, and `initial` is only the pre-loop passes.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `mro : List ClassInfo` | `getmro(subject)` | **R** | the inheritance chain (most-derived first) ↔ a `List ClassInfo`. Produced by the unchanged `getmro`; an input, not a consumed callee (mapping.md bijection). |
| 2 | `cls.nsKey : String` | `safe_getattr(cls, '__qualname__')` (post-patch key) | **R** | each class's own namespace key ↔ its `__qualname__`. The base-commit code used a single `'.'.join(objpath)` for the target; post-patch keys per class — captured by `nsKey` per chain element. |
| 2b | `cls.classKey : String` | the class OBJECT `cls` itself, as recorded in `ClassAttribute.class_` and compared by the consumer with `==` (`sphinx/ext/autodoc/__init__.py:1606`) | **R** | a class's identity ↔ an injective `String` token (G-CONF bridges it per `id(cls)`). Deliberately SEPARATE from `nsKey`: `__qualname__` is not injective on a chain (name shadowing, class factories), and the consumer's test is identity, not name. |
| 3 | `cls.attrDocs : List (String×String×String)` | `ModuleAnalyzer.for_module(cls.__module__).attr_docs.items()`, flattened to `(ns, name, '\n'.join(docstring))` | **R** | the documented attributes recorded for the class's module ↔ the triple list. The patch does not change `attr_docs`'s contents, only which class's are consulted; an input. |
| 3b | `cls.annNames : List String` | `[unmangle(cls, n) for n in getannotations(cls)]`, falsy dropped | **R** | the names the class declares by annotation alone ↔ a `List String`. `getannotations`/`unmangle` are unchanged by the patch; an input, not a consumed callee. A class with no `__annotations__` (`AttributeError`) ↔ `[]`. |
| 4 | `let mut members := initial` | `members` entering the loop (populated by the pre-loop enum / `__slots__` / `dir(subject)` passes) | **I** | initial member table; the modeled function starts from it. Restricted to `(name, docstring, class_)` as `List MemberEntry` — `doc = none` for a member with no docstring, `some s` for one carrying `s`; `owner = none` for a member the pre-loop `dir()` pass recorded with no class (`ClassAttribute(None, unmangled, value)`), `some k` for one recorded with class `k`. `ClassAttribute.value` is the only omitted field (frame — a constant of this fragment, with the measurement in mapping.md). |
| 5 | `for cls in mro do …` | `for cls in getmro(subject):` (the loop the attribute pass was MOVED INSIDE of) | **I** (deep model of the changed control flow) | **the fixed structure.** Base-commit ran the attribute pass once, outside the chain loop; post-patch it runs once per class in the chain. Modeled deeply by iterating the whole `mro`, never axiomatized (SPEC_GUIDE §3). |
| 5b | the per-class body: `for name in cls.annNames` block, THEN `for entry in cls.attrDocs` block | the annotation block followed by the docstring block inside one loop iteration | **I** (deep model of the changed control flow) | **the interleaving.** Base-commit finished the annotation pass over the whole MRO before the single docstring pass; post-patch the two alternate per class. Both guard on the same growing `members`, so the order is observable when one class annotates a name another documents. Modeled as `addEntries … (addAnnotations … members)` per chain element. |
| 5c | `if name ∉ members.map MemberEntry.name then members := members ++ [⟨name, none, some cls.classKey⟩]` | `if name and name not in members: members[name] = ClassAttribute(cls, name, INSTANCEATTR)` (`importer.py:307`) | **I** | an annotation-declared member is added with NO docstring — `ClassAttribute`'s `docstring` parameter defaults to `None` — modeled as `none`, distinct from `some ""`; and it records the class whose annotation declared it, `cls`, as `owner`. |
| 6 | `for entry in cls.attrDocs do` | `for (ns, name), docstring in analyzer.attr_docs.items():` | **I** | iterate the class's recorded attribute docstrings in order. |
| 7 | `if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name` | `if ns == qualname and name not in members:` | **I** (deep model of the changed predicate) | **the fixed predicate.** Base-commit tested `namespace == ns` for the single target namespace; post-patch tests `ns == qualname` against the CURRENT class's qualname, so each class contributes its own attributes. `name not in members` ↔ key-absence (first-occurrence-wins). G-CONF differential-tests it. |
| 8 | `members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]` | `members[name] = ClassAttribute(cls, name, INSTANCEATTR, '\n'.join(docstring))` (`importer.py:319`) | **I** (deep model of the changed argument) | append the `(name, docstring, class_)` to the table when the guard holds; insertion order preserved. `some` marks a recovered docstring, including the empty one an argument-less `#:` produces. **The first argument is `cls`, and that is a second thing this hunk changed:** pre-patch the same write was `ClassAttribute(subject, name, …)`. It is not a frame — it is read back at `__init__.py:1606` to decide which members a class documents as its own — so `owner := some cls.classKey` is modeled and pinned. `ClassAttribute.value` remains the one omitted field (frame, measured). |
| 9 | `return members` | the `members` dict returned by `get_class_members` | **I** | the final member table after the pass. |

The impl region contains **R/I ops only** and NO consumed axiom, so
`conf_skip = false`: `conformance_check.py` differential-tests the R/I leg against
the REAL post-patch `get_class_members`, driven over 600 generated class
hierarchies inside the patched container (plus a ≥1e5-case fuzz lane over the
bijected carrier). Driving the real function, rather than a replica, is what makes
the gate able to refute the interleaving drift described above — the previous
replica shared the model's flattening and so confirmed it.

## Soundness check (verify ⟹ correct)

- `problem_spec_gatherMemberDocs mro initial result` pins the table EXACTLY:
  `result = gatherMemberDocs mro initial`, the deterministic fold over the WHOLE
  chain. Directive 5 (frame): the result is fully determined — no unconstrained
  output component. Each entry's name, docstring AND recorded class are pinned;
  the only omitted `ClassAttribute` field is `value`, a constant of this fragment
  (mapping.md carries the measurement, and the earlier revision's claim that
  `class_` was likewise constant is recorded there as refuted). Directive 8: the postcondition is grounded in the inputs via the
  structural fold (`addEntries` over each `cls.attrDocs` with the
  namespace-match + key-absence guard), not an opaque oracle; every collected
  `(name, docstring)` must be *produced by* matching some chain class's own
  attribute entry.
- The prepatch impl runs the annotation pass over the whole chain first and then
  consults documented attributes for the head only, i.e. the base-commit shape. It
  violates the spec on TWO independent clauses, either of which alone refutes it:
  (a) a chain `[Bar, Foo]` where `Foo` (a base class) records an attribute `attr1`
  documented under `Foo`'s namespace and absent from `Bar` — the spec's fold
  collects `attr1`, the prepatch never consults `Foo`'s records and drops it; and
  (b) the interleaving witness, where `Base` annotates `x` and `Derived` documents
  it — the spec yields `[⟨"y", none, some B⟩, ⟨"x", some "derived x doc\n", some D⟩]`,
  the prepatch yields `[⟨"y", none, some B⟩, ⟨"x", none, some B⟩]` — a divergence in
  BOTH the docstring and the recorded supplying class. Both witnesses were checked
  as real Lean builds:
  `¬ problem_spec_gatherMemberDocs mro [] (implementation_gatherMemberDocs mro [])`
  closes by `decide` against the prepatch impl — both are `example`s inside the twin's
  proof region, so the twin's rejection is semantic rather than a tactic that stopped
  matching. Its carried gold proof (`exact outer_helper mro initial`, byte-identical to
  Solution.lean's) cannot close: the verifier reports a type mismatch between the two
  loop shapes (G-DIFF/G-PANEL).
- The owner clause cannot be refuted by the prepatch twin *alone*: the prepatch's
  docstring pass only ever consults the head class, and for the head the spec's
  owner and the prepatch's `subject` coincide, so every prepatch divergence in
  `owner` is accompanied by one in `doc` (witness (b) above). An owner-ONLY
  divergence needs a rival that keeps the fixed loop shape and changes just the
  recorded class — `ClassAttribute(subject, …)` inside the per-class loop. That
  rival exists, resolves nothing, and is refuted by construction: it is
  `weak-doc-owner-target` in the G-PBT battery and `target_owner_gather` in the
  G-CONF fuzz lane, and mapping.md "Recorded owner" carries its full reproduction
  (verifies against the OLD spec in 6.7s; its patch fails `test_instance_variable`,
  1 failed 1 passed against gold's 6/6).
- This discriminating case is exactly the FAIL_TO_PASS test
  `test_inherited_instance_variable`: `class Bar(Foo)` where `Foo.__init__` sets
  `self.attr1 = None  #: docstring foo`; with `:inherited-members:`, post-patch
  `Bar`'s docs include `attr1` (`docstring foo`); base_commit dropped it.
- The PASS_TO_PASS test `test_instance_variable` (no `:inherited-members:`) and
  `test_classes`/`test_decorators` exercise only own-class attributes — the head of
  the chain — where prepatch and spec agree; preserved identically. That test is also
  the one the recorded owner clause answers to: on the no-`:inherited-members:` path
  the consumer keeps only `m.class_ == self.object` (`__init__.py:1606`), so a rival
  that collects the right names and docstrings but credits them to the target class
  passes the FAIL_TO_PASS and fails THIS test.
  (`:inherited-members:` filtering of *non*-attribute members is an unchanged
  downstream step.)

## Why no axiom

The patch changes a control-flow STRUCTURE (run the attribute pass per chain class
instead of once, interleaved with the annotation pass) and the match PREDICATE
(`ns == qualname` per class), not a callee. The chain, the per-class `attr_docs` and
the per-class annotation names are inputs (`mro`, `ClassInfo.attrDocs`,
`ClassInfo.annNames`); the collection logic is modeled deeply as a total recursion
over the chain. There is no unchanged pure callee whose property the
proof must consume, so the `axioms` region is empty and `axiom_check.py` is a skip
stub (G-AX = skip). G-CONF is the primary and exhaustive differential.
