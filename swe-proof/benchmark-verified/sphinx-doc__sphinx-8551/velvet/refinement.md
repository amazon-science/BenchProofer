# refinement.md — sphinx-doc__sphinx-8551

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildCrossRef` `do` block, with the deep models `scopedRef`/`normalizeTarget`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (a deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I; no kind-3 (changed
inexpressible op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no A legs** (no
axioms / no callee stubs — mapping.md §3), so G-AX skips.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The scope-stamping site — the inline-type `make_xref` chain
(`PyField.make_xref`/`PyTypedField.make_xref` → `PyXrefMixin.make_xref`,
`sphinx/domains/python.py:310`/`:325` → `:269`; the modeled boundary is the
concrete builders' entry point, mapping.md §1)

Gold hunk (inside `PyXrefMixin.make_xref`):
```
  result = super().make_xref(rolename, domain, target, innernode, contnode, env)
  result['refspecific'] = True
+ result['py:module'] = env.ref_context.get('py:module')
+ result['py:class'] = env.ref_context.get('py:class')
  if target.startswith(('.', '~')):
      prefix, result['reftarget'] = target[0], target[1:]
      ...
```

| # | Solution.lean impl op (`buildCrossRef`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | `kindAdj := if kind = "class" ∧ target = "None" then "obj" else kind` (= `normalizeKind`) | (context, unchanged) `PyField.make_xref`/`PyTypedField.make_xref`: `if rolename == 'class' and target == 'None': rolename = 'obj'` before delegating to the changed `PyXrefMixin.make_xref` | R + I | pre-existing behaviour of the concrete builders the info-field path enters through: `None` is not a type, so a class-kind reference to the literal `None` is built object-kind. Inside the modeled boundary (mapping.md §1) so the descriptor's stored kind matches the real node's `reftype` on every input; G-CONF exercises it via the real `PyField`. |
| A1 | `base : CrossRef` with `refdomain := domain, reftype := kindAdj, reftarget := target, refspecific := false, scope* := none` | `result = super().make_xref(rolename, domain, target, …, env)` | R + I | the node the base reference builder returns, carrying domain/type/raw-target. `super().make_xref` (`docfields.py:68`) only sets these three attrs + calls the no-op py `process_field_xref`; modeled concretely. `str ↔ List Char` (mapping.md §2). G-CONF runs the **real** `super().make_xref`. |
| A2 | `withSpec := { base with refspecific := true }` | `result['refspecific'] = True` | I | identical concrete attribute set; `Bool true ↔ Python True`. |
| A3 | `withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }` | `result['py:module'] = env.ref_context.get('py:module')`; `result['py:class'] = env.ref_context.get('py:class')` | R + I | **the fix.** Stamp the current documentation scope onto the descriptor. `curModule`/`curClass` ↔ `env.ref_context.get('py:module'/'py:class')` (`Option (List Char) ↔ Optional[str]`, mapping.md §2). The discriminating step: the pre-patch left both unset. |
| A4 | `match target with c :: rest => if c = '.' ∨ c = '~' then { withScope with reftarget := rest } else withScope \| [] => withScope` (= `normalizeTarget`) | `if target.startswith(('.', '~')): prefix, result['reftarget'] = target[0], target[1:]` | R + I | strip a leading `.`/`~` from the stored target. Unchanged behaviour, modeled concretely. The Python `prefix`/text-relabel side effect is display-only and orthogonal to resolution (mapping.md §2); only `reftarget` is observable to `find_obj`. `str.startswith(('.','~'))` ↔ `match` on the head char. |

Companion threading edit (`sphinx/util/docfields.py:289`):

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| R4 | `curModule`/`curClass` are **method inputs** (the scope in effect, supplied to `buildCrossRef`) | `+ env=self.directive.state.document.settings.env` added to the `make_xrefs(...)` call in `DocFieldTransformer.transform` | R | a pure data-threading change: it makes `make_xref` receive the real `env` (non-`None`) on the inline-type-field branch, which is the precondition under which A3 reads `env.ref_context`. Modeled by `buildCrossRef` taking the scope directly as inputs; introduces no behaviour of its own (mapping.md §1). |

## A.1 Domain restriction and termination semantics

**`require kind ≠ []`.** The method's precondition restricts the modeled
domain to non-empty reference kinds. This mirrors the repo boundary: an
empty/falsy rolename short-circuits in the base builder
(`sphinx/util/docfields.py:71`) and returns a plain display node — no
cross-reference descriptor exists on that path, so none of the modeled
observables are defined there. All call sites inside the modeled slice pass a
non-empty rolename (mapping.md §1, "Domain restriction"). The precondition is
byte-identical in `Solution_prepatch.lean`, so it excludes no discriminating
behaviour; the prepatch still fails on the scope-recording goals within the
restricted domain.

**Total correctness.** The file uses `loom.semantics.termination "total"`.
The modeled behaviour is a straight-line record construction that always
terminates and returns, and the graded tests observe the returned descriptor,
so total correctness is the faithful semantics. Partial correctness would
admit a same-spec implementation that diverges (an infinite loop vacuously
satisfies every `ensures`) — a wrong impl the tests would fail — leaving the
spec too weak.

## B. Discriminating content of the change

The change is: the descriptor records the current scope (A3). Its observable
consequence — verified deep in resolution (`find_obj`, `python.py:1236`) — is
that an unqualified target resolves against the current module/class first,
instead of fuzzy-matching the same short name in every submodule. The
`Solution_prepatch.lean` skeleton reproduces the bug exactly: it sets
`withScope := withSpec` (scope left `none`) and so **fails** the `ensures`
clauses `out.scopeModule = curModule` and `out.scopeClass = curClass` — the
unsolved goal is literally `none = curModule ∧ none = curClass` (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely changed — stamping the
documentation scope onto the cross-reference descriptor (A3) — is modeled
**directly** as a record-field assignment over the read-only scope inputs, not
hidden behind an axiom. There is **no consumed axiom and no deep-model
reference to a foreign callee**: `super().make_xref`'s constructed attributes are
modeled concretely and exercised for real by G-CONF, and the py-domain
`process_field_xref` it calls is a no-op.

## D. verify(Solution) ⇒ resolved

`buildCrossRef` verifies only if its output equals `scopedRef curModule curClass
domain reftype target` — i.e. the descriptor records `refspecific = true`, the
normalized kind (A0), the normalized target, AND the current scope `scopeModule
= curModule`, `scopeClass = curClass` (A0, A2–A4). By R (`str ↔ List Char`,
`Optional[str] ↔ ScopeName`, the node-attribute bijection of mapping.md §2) the
verified descriptor equals the real patched `make_xref` chain's `result` on
every input — G-CONF confirms this mechanically over 10⁵ inputs (the exhaustive
scope×target boundary grid, including the literal target `None`, + fuzz, 0
disagreements). The companion `env`-threading edit (R4) supplies
the non-`None` `env` the stamping reads, with no behaviour of its own. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust point
is refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust.
