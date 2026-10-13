# mapping.md — sphinx-doc__sphinx-8548

Binds every `model.py` symbol to its repository counterpart at
`base_commit = dd1615c59dc6fff633e27dbb3861f2d27e1fb976`, states the type
abstraction, and gives the provenance of the deep-model reference (the changed
collection logic) checked by axiom_check.py / G-AX.

Repo files under change:
- `sphinx/ext/autodoc/importer.py` — `get_class_members` (the instance-attribute
  collection logic; the substantive fix).
- `sphinx/ext/autodoc/__init__.py` — the single call site
  `ClassDocumenter.get_object_members` drops the now-unused `analyzer` argument
  (signature follow-through, no behavioural content of its own).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_attribute_doc(nm, mro, ens, enm, edoc)` | the instance-attribute collection in `get_class_members` — `sphinx/ext/autodoc/importer.py:254` (the loop at body lines 310-316 pre-patch; the MRO-walking loop at lines 300-330 post-patch) | the modeled changed function: resolve one attribute name's documentation under the MRO-aware lookup |
| `resolve_from` / `lookup_owner_doc` *(deep model — A-reference)* | the membership + precedence rule the patch installs: `for cls in getmro(subject): ... for (ns, name), docstring in analyzer.attr_docs.items(): if ns == qualname and name not in members` (`importer.py:300-330` post-patch) | pure spec: the earliest-MRO-owner / first-record resolution; validated == the real patched loop by axiom_check.py (G-AX), NOT consumed as an axiom |
| `mro` (param) | `getmro(subject)` — `sphinx.util.inspect.getmro` returns `subject.__mro__` | the method-resolution order, subject first, modeled as a list of owner codes |
| `ens` / `enm` / `edoc` (params) | the `(ns, name) -> docstring` entries of `ModuleAnalyzer.for_module(modname).attr_docs` (`sphinx/pycode/__init__.py:170-175`), keyed by `(owner-qualname, attr-name)` | the record table, modeled as three parallel `List[int]` of owner codes / name codes / documentation-body codes |
| `ABSENT` (= -1) | "no documented record for this name" (the `name not in members` / never-assigned case) | sentinel distinct from every documentation-body code (codes are non-negative) |
| `Requires(MustTerminate(2))` (+ the impl loop's `Invariant(MustTerminate(len(mro) - c))` measure) | the collection loop always RETURNS its `members`: a bounded scan of the finite `getmro(subject)` tuple against the finite `attr_docs` dict | total-correctness obligation. Nagini verifies partial correctness by default, so without it a same-spec implementation that diverges before returning satisfies every `Ensures` vacuously while never producing any documentation — behaviour the real repo function cannot exhibit. The obligation pins "must answer" and adds nothing else. |

The pre-patch repo logic the change replaces (for the refinement audit, not
referenced from the consumer spec view): `importer.py:310-316` —
`namespace = '.'.join(objpath); for (ns, name), docstring in analyzer.attr_docs.items(): if namespace == ns and name not in members`, where `analyzer` is the
single analyzer of the *subject's* module and `namespace` is the *subject's* own
qualified name. This matches records only against the subject's own owner, so an
attribute documented only on a base class is never collected.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a class object on the MRO (`getmro(subject)` element) | an `int` owner code | distinct classes ↔ distinct codes; the subject is `mro[0]` |
| a class's qualified name `cls.__qualname__` (the `ns` an `attr_docs` key carries, == the owner of the record) | the same `int` owner code | `ns == cls.__qualname__` ↔ `ens[j] == owner-code`; matching `ns == qualname` per MRO class ↔ `ens[j] == mro[c]` |
| an attribute name `name` (the second component of an `attr_docs` key) | an `int` name code | distinct names ↔ distinct codes |
| the documentation comment `'\n'.join(docstring)` stored for `(ns, name)` | an `int` documentation-body code (≥ 0) | distinct documentation bodies ↔ distinct non-negative codes; `ABSENT = -1` is reserved for "no record" |
| the `members` dict built by the loop (`name -> ClassAttribute(..., docstring)`) | resolved per queried name | the loop computes, for each `name`, the documentation of the first record (earliest MRO class, first entry) that names it; `resolve_attribute_doc` returns that per `nm` |
| `getannotations` / `safe_getattr` / `ClassAttribute` construction / the enum / `__slots__` / `dir()` branches of `get_class_members` | omitted | unchanged by the patch and orthogonal to the instance-attribute documentation lookup the issue is about (the F2P observes only the instance-attribute documentation); they do not touch the `(owner, name) -> doc` resolution under test |

**Abstraction assumption (annotation/comment name-collision across MRO).** The
`(owner, name) -> doc` record-table abstraction models only the comment-documented
instance-attribute branch. In gold, the annotation-only branch shares the same
`members` dict and the same `name not in members` guard, so if a name were
annotation-declared on one MRO class AND comment-documented on a different MRO
class, the earlier-MRO branch (whichever ran first) would claim the name and the
later one would be skipped — gold's result would then depend on the interleaving
of the annotation and comment branches per MRO class, which the abstraction does
not represent. The model therefore assumes **no annotation/comment name collision
across MRO classes** (each documented name is owned by at most one branch). This
holds for the F2P/P2P fixtures (instance-attribute comments only, no colliding
annotations) and so does not affect `verify ⟹ correct` for the tested inputs.

`str` indexing/iteration is banned in Nagini, so every identifier (owners, names,
documentation bodies) is an integer code; the specification is carried by
`PSeq[int]` via `ToSeq`.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `resolve_from` / `lookup_owner_doc` ↔ the patched `get_class_members` loop
**Reference:** the post-patch instance-attribute loop of
`get_class_members` (`sphinx/ext/autodoc/importer.py`, post-patch):

```python
for cls in getmro(subject):                 # MRO front-to-back; subject first
    ...
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
```

The changed decision is twofold and is exactly what `resolve_from` /
`lookup_owner_doc` encode:

1. **Membership over the whole MRO.** Pre-patch matched `ns == namespace` for the
   single subject namespace; post-patch matches `ns == qualname` for EACH class
   `cls` on `getmro(subject)`. So a record whose owner is a base class now
   matches. `lookup_owner_doc(owner, nm, …)` is "the first record with that owner
   and name"; `resolve_from(nm, mro, …, c)` walks the MRO from `c` and takes the
   first MRO class that owns such a record.

2. **Earliest-MRO-class precedence.** `members` is filled front-to-back over the
   MRO and an entry is written only if `name not in members`, so the class
   nearest the subject wins. Front-recursion of `resolve_from` over the MRO start
   `c` reproduces this: the first owning class in MRO order supplies the body.

   Among records of the same owner, the loop iterates `attr_docs` in insertion
   order and the first wins (`name not in members`); `lookup_owner_doc` scans
   entries `0,1,…` and returns the first match.

**Record-table keying.** `attr_docs` keys are `(basename, name)` where `basename`
is `".".join(qualname[:-1])`, i.e. the qualified name of the class whose
`__init__` defined the instance attribute (`sphinx/pycode/parser.py:272-275`,
`VariableCommentPicker.add_variable_comment`). For the F2P fixture this is
literally `Foo` / `Bar`. `axiom_check.py` (`check_real_parser`) runs the REAL
`sphinx.pycode.parser.Parser` on the fixture and asserts the keys are exactly
`{(Foo,attr1),(Foo,attr2),(Bar,attr2),(Bar,attr3)}`, grounding the `(owner,name)`
abstraction in real Sphinx output.

**Soundness check (G-AX):** `axiom_check.py`
- transcribes the patched nested loop (`real_loop_collect`) over the SAME abstract
  record table and asserts `resolve_from` agrees with it, per queried name, on 8
  boundary hierarchies (incl. the F2P scenario, overrides, base-only, unrelated
  owners, duplicate records, deep MRO) + 20 000 randomized fuzz hierarchies;
- validates the record-table abstraction against the real `sphinx.pycode` parser
  and re-derives the F2P documentation (`check_real_parser`);
- when Sphinx is fully importable in the container, runs the REAL
  `sphinx.ext.autodoc.importer.get_class_members` on a synthesised `Bar(Foo)`
  module and asserts the attribute→documentation map equals the model
  (`check_real_sphinx`).

It imports only the standard library plus (optionally, guarded) the Sphinx
package the patch lives in; exit 0 iff every observation matches the model.

### 3.2 No consumed axioms
The patch's other callees inside this loop — `getmro`, `safe_getattr`,
`getannotations`, `ModuleAnalyzer.for_module`/`analyze`, `ClassAttribute` —
are NOT modeled or consumed: their results are the *inputs* to the abstraction
(`mro`, the `(owner, name) -> doc` table). The benchmark's changed behaviour
lives entirely in how those inputs are *matched and deduplicated*, which is
modeled deeply. There is therefore no `@ContractOnly` axiom in this bundle.

### 3.3 The `__init__.py` signature follow-through
The companion hunk in `sphinx/ext/autodoc/__init__.py:1587` changes
`get_class_members(self.object, self.objpath, self.get_attr, self.analyzer)` to
`get_class_members(self.object, self.objpath, self.get_attr)` — dropping the
`analyzer` argument that `get_class_members` no longer accepts (it now builds the
analyzer per MRO class internally). This is a pure caller/callee signature
adjustment with no behavioural content beyond enabling the importer change; it
carries no separate modeled function and no failing prepatch of its own.

## G-CONF (differential conformance — `conformance_check.py`)

**Shadow.** The `# impl-start` .. `# impl-end` region of `model.py`, copied
verbatim with only the contract calls deleted (`Invariant`, `Assert`, and the
`# invariants-start`/`-end` markers), plus the `@Pure` helpers it depends on
(`lookup_owner_doc`, `resolve_from`, `resolved_doc`) minus their `Requires`.
Nagini's `PSeq`/`ToSeq` carriers are realized by an immutable-tuple shim, so the
region's `lookup_owner_doc(owner, nm, ToSeq(ens), …)` calls are unaltered. There
is no `@ContractOnly` callee in this bundle (§3.2), so nothing is assumed.
The check compares THREE values per input and demands all three agree: the impl
region, the pure `resolved_doc` the `Ensures` names, and the oracle — so a
model-internal impl/spec divergence is refuted too.

**Oracle.** The real patched repo function is **called**, not transliterated:
`sphinx.ext.autodoc.importer.get_class_members` (§1). Each input is a real
Python module written to a private temp dir, imported, and its leaf class passed
to `get_class_members(subject, objpath, safe_getattr)`; the oracle's answer for a
queried name is `members[name].docstring` when that member is a documented
`INSTANCEATTR`, else absent. The gate applies `patch.diff` to /testbed and sets
`PYTHONPATH` before the script runs.

**Type bridge (§2, inverted).** `mro` comes from the real
`sphinx.util.inspect.getmro(subject)`, each class mapped to an owner code by
`__qualname__`; `ens`/`enm`/`edoc` come from the real
`ModuleAnalyzer.for_module(cls.__module__).attr_docs` table of every MRO class in
MRO order (`PycodeError`/`AttributeError` ⇒ no records, mirroring the real
`except`), keys `(ns, name)` mapped to `(owner code, name code)` and values to a
documentation-body code for `'\n'.join(docstring)`. The `ns == qualname` filter is
deliberately **not** applied in the bridge — leaving it to the model's own
`ens[j] == mro[c]` test is what puts the changed membership decision under test.
Because MRO classes sharing a module contribute that module's table more than
once, the tables also contain duplicate records, exercising
`lookup_owner_doc`'s first-match-wins scan. The result code is inverted back to
a string for comparison; `ABSENT = -1` ↔ "not a documented instance attribute".

**Input domain.** Every input satisfies the `Requires`
(`len(ens) == len(enm) == len(edoc)` holds by construction; permissions and
`MustTerminate` are vacuous at runtime). The oracle-reachable domain has
`len(mro) >= 2` (a real MRO ends in `object`), so the model's `len(mro) == 0`
case has no real counterpart and is not driven. Generated attribute names are
asserted disjoint from `dir(subject)` and every MRO class's annotations, keeping
each input inside the abstraction §2 declares and respecting its
no-annotation/comment-collision assumption.

**Inputs and seed.** 12 boundary hierarchies (the exact F2P `Bar(Foo)` fixture;
empty record table; singleton; base-only documentation; own-only; same name on
class and base; depth-4 chain documented only on the deepest base; a diamond
where both branches document the same name; a cross-module hierarchy; a `dict`
subclass whose bases raise `PycodeError`; a class with a record per name) then
seeded fuzz over random depth-1..4 chains, occasional multiple inheritance and
random two-module splits. Recorded run: **100002 attribute-resolution inputs over
14286 real class hierarchies**, `SEED = 8548` (pinned as a module constant), 0
disagreements. Together the boundary cases take every branch of the impl region:
the `while` falling through to `return ABSENT`, a hit at `c == 0`, a hit at
`c > 0`, and `lookup_owner_doc` returning `ABSENT`, matching on its first entry,
and scanning past non-matching entries and duplicates.

**Teeth (mutation-checked).** Restricting the shadow's loop to `mro[0]` (the
pre-patch decision logic) and, separately, swapping the oracle for a replica of
the pre-patch subject-namespace-only single pass each make the check FAIL on its
first boundary input (the F2P fixture, `attr1`), exit 1.
