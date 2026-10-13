# mapping.md — sphinx-doc__sphinx-8551

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 57ed10c68057c96491acbd3e62254ccfaf9e3861`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo files under change: `sphinx/domains/python.py`, `sphinx/util/docfields.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildCrossRef` | the concrete inline-type reference builders' `make_xref` chain: `PyField.make_xref` (`sphinx/domains/python.py:310`) / `PyTypedField.make_xref` (`python.py:325`) → `PyXrefMixin.make_xref` (`python.py:269`, changed body line 274). These concrete overrides are the entry points the info-field transform actually calls (and the class G-CONF instantiates); each first normalizes the rolename (`'class'`+target `'None'` → `'obj'`, unchanged behaviour) and then delegates to the changed `PyXrefMixin.make_xref`. | the modeled changed function: builds the cross-reference descriptor for an inline type specifier |
| `CrossRef` (structure) | the `addnodes.pending_xref` node `result` that `make_xref` returns (its resolution-relevant attributes) | the descriptor whose attributes resolution reads |
| `scopedRef` (deep model — R/I) | the post-patch body of the `make_xref` chain (`'class'`/`'None'` kind rewrite, `refspecific=True`, `py:module`/`py:class` stamped from `env.ref_context`, `'.'`/`'~'` prefix handling) | pure spec: the descriptor produced for a target under a scope; validated == real patched `make_xref` by G-CONF |
| `normalizeKind` (R/I) | the `if rolename == 'class' and target == 'None': rolename = 'obj'` guard in `PyField.make_xref` / `PyTypedField.make_xref` (`python.py:313-315` / `:328-330`) | pure spec: `None` is not a type — a class-kind reference to the literal target `None` is built object-kind (unchanged behaviour) |
| `normalizeTarget` (R/I) | the `if target.startswith(('.', '~')): prefix, result['reftarget'] = target[0], target[1:]` block (`python.py:275-277` post-patch) | pure spec: strip a leading `.`/`~` from the stored target |
| `ScopeName` (`Option (List Char)`) | `env.ref_context.get('py:module')` / `env.ref_context.get('py:class')` — each `Optional[str]` | the documentation scope inputs |

The modeled boundary is deliberately the **concrete builders'** `make_xref`
(not the bare mixin method): the info-field path always enters through
`PyField`/`PyTypedField`, so the pre-existing `'class'`+`'None'` → `'obj'` kind
rewrite is inside the observable behaviour of the changed call chain and must
be pinned (a spec that stores the kind verbatim diverges from the repo on
`(kind='class', target='None')`). `PyGroupedField` (`python.py:320`) has no
override, but it is registered only with `rolename='exc'` (`python.py:359`),
for which the rewrite is vacuously the identity — `normalizeKind` is exactly
the identity there too, so the single model covers all three builders.

**Domain restriction (`require kind ≠ []`).** The method carries the
precondition that the reference kind is non-empty. This matches the repo: an
empty/falsy `rolename` short-circuits in the base `Field.make_xref`
(`sphinx/util/docfields.py:71`, `if not rolename: return contnode or
innernode(...)`) and returns a plain display node — **no** `pending_xref` is
constructed, so there is no descriptor and none of the modeled observables
exist on that path. Every call site inside the modeled slice supplies a
non-empty rolename: the py-domain field registrations use
`typerolename='class'` / `bodyrolename='class'` / `rolename='exc'`
(`python.py:352-367`), and the F2P path (`test_info_field_list`) enters with
`'class'`. `buildCrossRef` therefore models only the descriptor-building
branch; the kindless display-only branch is outside the modeled boundary, and
the precondition records that boundary explicitly (it is identical in the
prepatch twin, so it excludes no discriminating behaviour). G-CONF likewise
fuzzes only non-empty kinds, matching the precondition's domain.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The modeled behaviour is a straight-line record
construction that always terminates and returns, and the graded tests observe
the returned descriptor, so total correctness is the faithful semantics.
Partial correctness would admit a same-spec implementation that diverges (an
infinite loop vacuously satisfies every `ensures`) — a wrong impl the tests
would fail — leaving the spec too weak.

The companion edit in `sphinx/util/docfields.py` (`DocFieldTransformer.transform`,
`:250`; the `make_xrefs(... )` call at `:289`) is a **threading change only**: it
forwards `env=self.directive.state.document.settings.env` into the same
`make_xref` path on the unknown/inline-type-field branch, so that the `env`
argument `make_xref` now reads is non-`None`. It introduces no new behaviour of
its own; its entire observable effect is "`make_xref` receives the real `env`",
which is exactly the precondition under which `buildCrossRef`'s scope-stamping is
exercised. Modeled by `buildCrossRef` taking the scope (`curModule`/`curClass`)
directly as inputs (refinement.md row R4).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `target: str`, `domain: str`, `rolename: str` | `List Char` | Python `str` ↔ `s.toList`-shaped `List Char`; G-CONF bridges by passing/reading the `str` directly (the per-character structure that matters is the leading-char test `target[0] in {'.','~'}` ↔ `match target with c :: _`). empty `str` ↔ `[]` |
| `env.ref_context.get('py:module')` (`Optional[str]`) | `curModule : ScopeName = Option (List Char)` | `None` ↔ `none`; `"mod.submod"` ↔ `some "mod.submod".toList` |
| `env.ref_context.get('py:class')` (`Optional[str]`) | `curClass : ScopeName` | as above |
| the returned `pending_xref` node | `CrossRef` record | observable attrs read by `resolve_xref` (`python.py:1292`): `refdomain`↔`refdomain`, `reftype`↔`reftype`, `reftarget`↔`reftarget`, `refspecific`(bool)↔`refspecific`, `node.get('py:module')`↔`scopeModule`, `node.get('py:class')`↔`scopeClass` |

`refspecific` is stored on the node as the Python literal `True`; G-CONF reads it
through `bool(node.get('refspecific'))`. The descriptor models only the
resolution-relevant attributes; `innernode`/`contnode` text content is orthogonal
to the scope-resolution behaviour at issue (it carries display text, which the
F2P test checks separately and the patch does not change).

### 2.1 Why these attributes pin the fixed behaviour

`resolve_xref` (`python.py:1292`) reads `node.get('py:module')` and
`node.get('py:class')`, then calls `find_obj(env, modname, clsname, target, …,
searchmode=1)` (because `refspecific` is set). With `modname`/`clsname` present,
`find_obj` first tries `modname + '.' + name` (and `modname.clsname.name`) before
falling back to the fuzzy "ends-with `.name`" search that returns *every*
same-named target in *every* submodule — the multiple-matches branch that emits
the "more than one target found" warning. So recording the scope onto the node
is exactly what lets an unqualified `A` under `currentmodule:: mod.submod`
resolve to `mod.submod.A` instead of matching both `mod.A` and `mod.submod.A`.
The pre-patch node carried neither attribute (both default to `None`), so
`find_obj` always took the fuzzy branch for unqualified names.

## 3. Callee provenance (kind-A)

**None.** The modeled function builds a descriptor purely from its own inputs:
the scope values it stamps come from `env.ref_context` (passed in as
`curModule`/`curClass`), the target/domain/type are passed through, and the
prefix normalization is a concrete string operation. There is **no unchanged
callee whose behaviour the proof relies on** — `super().make_xref`
(`Field.make_xref`, `sphinx/util/docfields.py:68`) only constructs the node and
sets `refdomain`/`reftype`/`reftarget` and calls the py-domain
`process_field_xref`, which is a **no-op** (`sphinx/domains/__init__.py:312`,
`pass`). Those constructed attributes are modeled concretely in `scopedRef`'s
base record, and G-CONF runs the *real* `super().make_xref` chain in the oracle,
so no axiom is needed or claimed. There is no module-level `axiom` and no `:|`
stub; `axiom_check.py` is therefore absent and G-AX skips (meta.json `axioms:
[]`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8551`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`buildCrossRef`/`scopedRef`/`normalizeKind`/`normalizeTarget` (all R/I-tagged
ops) to Python and drives the real patched `make_xref` chain as the oracle
through a concrete `PyField` (whose own `make_xref` performs the
`'class'`+`'None'` → `'obj'` kind rewrite before delegating to the changed
`PyXrefMixin.make_xref`) and a minimal `BuildEnvironment` stub supplying
`ref_context` and a no-op `process_field_xref` domain (the only `env` surface
the patched code touches). It checks the exhaustive cross product of small
scope/target carrier sets first (the carriers include the literal target
`"None"` so the kind-rewrite branch is exercised), then re-samples to exceed
the 10⁵ fuzz floor.
