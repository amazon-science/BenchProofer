# refinement.md — sphinx-doc__sphinx-8548

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_attribute_doc` impl region and the deep `resolve_from` /
`lookup_owner_doc` spec) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The collection site — `get_class_members` (`sphinx/ext/autodoc/importer.py`)

Gold hunk (the instance-attribute collection, body lines ~300-330): the
pre-patch
```python
# annotation only member (ex. attr: int)
for cls in getmro(subject):
    ... getannotations(cls) ...

if analyzer:
    namespace = '.'.join(objpath)
    for (ns, name), docstring in analyzer.attr_docs.items():
        if namespace == ns and name not in members:
            members[name] = ClassAttribute(subject, name, INSTANCEATTR, ...)
```
becomes the post-patch MRO-walking
```python
for cls in getmro(subject):
    ... getannotations(cls) ...
    try:
        modname = safe_getattr(cls, '__module__')
        qualname = safe_getattr(cls, '__qualname__')
        analyzer = ModuleAnalyzer.for_module(modname); analyzer.analyze()
        for (ns, name), docstring in analyzer.attr_docs.items():
            if ns == qualname and name not in members:
                members[name] = ClassAttribute(cls, name, INSTANCEATTR, ...)
    except (AttributeError, PycodeError):
        pass
```

| # | model.py impl op (`resolve_attribute_doc`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `mro: List[int]`, `ens/enm/edoc: List[int]` | `getmro(subject)` and the `(ns, name) -> docstring` items of `ModuleAnalyzer.for_module(...).attr_docs` | R | a class ↔ an owner code; a class qualname (the `ns` an `attr_docs` key carries) ↔ that owner code; an attribute name ↔ a name code; a documentation comment ↔ a documentation-body code; the MRO ↔ `mro` (subject first); the record items ↔ the parallel `(ens, enm, edoc)` table (mapping.md §2). The values `getmro`/`safe_getattr`/`ModuleAnalyzer` compute are the *inputs* to the abstraction, not modeled operations. |
| A2 | outer `while c < len(mro)` scanning `mro[c]` front-to-back, returning the first owning class's body | `for cls in getmro(subject)` filling `members` front-to-back with the `name not in members` guard | A-reference | the changed membership+precedence rule is modeled **deeply**: `resolve_from` (front-recursive over the MRO start `c`) takes the first MRO class that owns a matching record, exactly as the loop's front-to-back `members` fill + `name not in members` makes the earliest MRO class win. There is **no consumed axiom** — the proof depends on no `@ContractOnly`. G-AX validates the deep model == the real patched loop on boundary + 20 000 fuzz hierarchies and against the real `sphinx.pycode` parser / `get_class_members` (mapping.md §3.1). |
| A3 | inner `lookup_owner_doc(owner, nm, …, 0)`: first record with `ens[j]==owner and enm[j]==nm` | `for (ns, name), docstring in analyzer.attr_docs.items(): if ns == qualname and name not in members` | A-reference | the per-class match: `ns == qualname` (post-patch) ↔ `ens[j] == mro[c]`; `name not in members` (first wins for that owner) ↔ `lookup_owner_doc` returns the *first* matching entry. Validated by the same G-AX equivalence. |
| A4 | `found != ABSENT` decides "the name is documented on this class" | the loop writes `members[name]` only when a record matches and `name not in members` | I | a record either exists for `(owner, name)` or not; `ABSENT = -1` is reserved (documentation codes are ≥ 0), so `!= ABSENT` exactly means "a matching record was found", matching the loop's conditional write. |
| A5 | return the resolved body / `ABSENT` | `members[name].docstring` (or the name being absent from `members`) | R | the documentation-body code ↔ the stored `'\n'.join(docstring)`; "no entry" ↔ `ABSENT`. The F2P observes the documentation rendered for each attribute, i.e. exactly this resolution. |
| A6 | `Requires(MustTerminate(2))` + the loop measure `Invariant(MustTerminate(len(mro) - c))` | the collection loop is a bounded scan of the finite `getmro(subject)` tuple against the finite `attr_docs` dict — it always returns its `members` | I | total-correctness obligation: Nagini is a partial-correctness verifier by default, so without it a diverging same-spec impl (e.g. an endless loop before the return) satisfies every `Ensures` vacuously while never delivering any documentation. The real loop over two finite carriers trivially terminates, so the obligation adds no behaviour beyond what the repo code already has. |

The discriminating content of the change — a record owned by a **base class**
(e.g. `(Foo, attr1)`) now matches because the lookup walks the whole MRO, and an
**overridden** attribute (`attr2`, owned by both `Bar` and `Foo`) keeps the
subject's body because the earliest MRO class wins — lives in `resolve_from`
walking `mro` rather than testing only `mro[0]`. `model_prepatch.py` reproduces
the pre-patch rule (match only the subject owner `mro[0]`) and **fails** the
postcondition `Result() == resolved_doc(nm, …)` on every base-only name, which
is exactly the spec sensing the change (G-DIFF).

## B. The call-site signature follow-through (`sphinx/ext/autodoc/__init__.py`)

Gold hunk:
```
- members = get_class_members(self.object, self.objpath, self.get_attr, self.analyzer)
+ members = get_class_members(self.object, self.objpath, self.get_attr)
```
plus the matching signature change of `get_class_members` (drop the
`analyzer: ModuleAnalyzer = None` parameter) and the new `PycodeError` import.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | none (the model takes the record table directly as `ens/enm/edoc`) | dropping the `analyzer` argument / parameter; `get_class_members` now builds the analyzer per MRO class internally | R | a pure signature adjustment: where the caller used to pass one pre-built analyzer (the subject's), the function now derives one analyzer per MRO class. Under the abstraction both reduce to the same `(owner, name) -> doc` record table the model consumes (mapping.md §3.3); no behavioural content of its own and so no separate failing prepatch. The `PycodeError` import only widens the `except` so a missing-source base class is skipped rather than crashing — orthogonal to the resolution under test. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the rule deciding which documentation record resolves an attribute
name (own-owner-only vs. any-MRO-owner, with earliest-MRO-owner precedence) — is
modeled **deeply** (the spelled-out front-recursive `resolve_from` /
`lookup_owner_doc`, consumed by `resolve_attribute_doc`, steps A2/A3, an
**A-reference**), not hidden behind an axiom about the function under change.
There is **no consumed axiom** in this bundle: the callees the loop invokes
(`getmro`, `safe_getattr`, `ModuleAnalyzer`, `getannotations`, `ClassAttribute`)
are unchanged and supply the *inputs* to the abstraction, never modeled
operations.

## D. verify(model) ⇒ resolved

`resolve_attribute_doc` verifies only if its result equals the
earliest-MRO-owner, first-record resolution (`resolved_doc`) — which for a
base-only name yields that base class's body (A2) and for an overridden name
yields the subject's body (A3). By R (class ↔ owner code, qualname ↔ owner code,
name/doc ↔ codes, the analyzer/MRO callees feeding the record table) the verified
resolution equals the documentation `get_class_members` stores for each
attribute on the tested hierarchy; by G-AX the deep model `resolve_from` equals
the real patched loop (A-reference) and the record-table abstraction matches the
real Sphinx parser. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited deep model — and
the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity + deep-model soundness (this document + G-AX); there is no axiom-
soundness trust point because there is no consumed axiom.
