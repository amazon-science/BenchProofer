# refinement.md — django__django-13343

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `initField`, `deconstructStorage`, and `roundTripStorage` `do` blocks, plus
the deep models `initState`/`emit`) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement; state the bijection), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (deep model validated == real callee
by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs** (no foreign callee is axiomatized — §C), so G-CONF carries the
full mechanical burden and G-EQ audits only the narrative.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The construction site — `FileField.__init__` (`files.py:229–238`)

Gold hunk:
```
         self.storage = storage or default_storage
         if callable(self.storage):
+            # Hold a reference to the callable for deconstruct().
+            self._storage_callable = self.storage
             self.storage = self.storage()
```

Modeled method: `initField`, deep model `initState`.

| # | Solution.lean impl op (`initField`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `arg : BackendArg` | the `storage` kwarg of `__init__` | R | `storage` value ↔ `BackendArg` (mapping.md §2): `None`↔`omitted`, `Storage`↔`concrete ⟨id, bool⟩`, callable↔`producer ⟨id, yields, bool⟩`; Python truthiness ↔ `.present`. `callable(self.storage)` ↔ the `.producer` match arm (reached only when present). |
| A2 | `.omitted => { backend := defaultBackend, .. }` | `self.storage = storage or default_storage` with `storage=None` (omitted) | I | omitted storage resolves to the ambient backend (mapping.md §2). |
| A2′ | the `if ¬b.present` / `if ¬p.present` legs `=> { backend := defaultBackend, origProducer := none }` | `self.storage = storage or default_storage` short-circuiting on ANY falsy `storage` (falsy callable, falsy `Storage`, `0`, `''`) — pre-existing, unchanged by the patch | I + R | the `or` presence test precedes `callable(self.storage)`; a falsy value is discarded, `self.storage` becomes `default_storage`, the callable branch is skipped, so nothing is consulted or retained and `deconstruct` emits no `storage` kwarg. R: `bool(value)` ↔ `.present` (mapping.md §2, falsy-storage corner). |
| A3 | `.concrete b` (present) `=> { backend := b, origProducer := none }` | non-callable truthy `Storage` passed: `self.storage = storage`, `callable` false so no `_storage_callable` | I | a concrete `Storage` is kept; no callable retained. |
| A4 | `.producer p` (present) `=> { backend := p.yields, origProducer := some p }` | callable branch: `self._storage_callable = self.storage` **then** `self.storage = self.storage()` | I + R | `backend := p.yields` ↔ evaluating the callable (`self.storage()`), `origProducer := some p` ↔ retaining the callable (`self._storage_callable = self.storage`). The retained `some p` is exactly the gold-added line. R: object identity ↔ `Producer.handle` (mapping.md §2). |

## B. The deconstruction site — `FileField.deconstruct` (`files.py:281–283`)

Gold hunk:
```
         if self.storage is not default_storage:
-            kwargs['storage'] = self.storage
+            kwargs['storage'] = getattr(self, '_storage_callable', self.storage)
```

Modeled method: `deconstructStorage`, deep model `emit`.

| # | Solution.lean impl op (`deconstructStorage`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if st.backend = defaultBackend then BackendArg.omitted` | `if self.storage is not default_storage:` guard (false ⇒ no `storage` kwarg) | I + R | identity comparison `is not default_storage` ↔ `st.backend = defaultBackend`; the ambient case emits no kwarg ↔ `omitted` (mapping.md §2). |
| B2 | `some p => BackendArg.producer p` | `getattr(self, '_storage_callable', self.storage)` when `_storage_callable` is set | I | the gold change: a field that retained a callable reports the **callable** (`_storage_callable`), not the evaluated storage. `some p ⇒ producer p` is that `getattr` hitting the retained attribute. |
| B3 | `none => BackendArg.concrete st.backend` | `getattr(self, '_storage_callable', self.storage)` when `_storage_callable` is absent (falls back to `self.storage`) | I | a field with no retained callable reports its concrete storage — the `getattr` default leg, identical to pre-patch behavior for that case. |

## B′. The lifecycle — `roundTripStorage`

| # | Solution.lean op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| C1 | `let st ← initField arg` | `f = FileField(storage=arg)` | I | callee-under-spec: `prove_correct` supplies `initField_correct` (`st = initState arg`). |
| C2 | `let e ← deconstructStorage st` | `f.deconstruct()[3].get('storage')` | I | callee-under-spec: `deconstructStorage_correct` (`e = emit st`). Composition gives `e = emit (initState arg)`. |

`roundTripStorage`'s postcondition `e = emit (initState arg)` is the exact
property the F2P test asserts: deconstructing a field built from a callable
storage returns that same callable (`assertIs(storage, callable_storage)`). With
`arg = producer p`, `p.present`, and `p.yields ≠ defaultBackend`,
`emit (initState (producer p)) = producer p` — the original callable, not the
evaluated backend.

**Semantics: total correctness.** The file sets
`loom.semantics.termination "total"`. The real construction and deconstruction
paths are straight-line dispatches over the field's configuration and always
terminate, so a diverging implementation must not satisfy the spec. Partial
correctness would let a non-terminating branch discharge its postcondition
vacuously (this exact spec-admits-divergence attack was demonstrated by the
audit and is now rejected: a `while true` body fails verification under total
semantics).

## Discriminating clause / prepatch

The behavioral change lives in two places, both reproduced by
`Solution_prepatch.lean` (byte-identical spec, G-DIFF):

1. `initField` producer arm pre-image sets `origProducer := none` (does not
   retain the callable) ⇒ fails `st = initState arg` on `.producer`.
2. `deconstructStorage` pre-image returns `BackendArg.concrete st.backend`
   unconditionally (reports the evaluated backend) ⇒ fails `e = emit st` when a
   producer is retained.

Either reversion makes `roundTripStorage` report `concrete p.yields` (the
evaluated storage) instead of `producer p` (the callable) — exactly the bug the
F2P test catches. A single prepatch suffices: both reversions sit on the one
F2P-observable behavior (deconstruct-after-construct of a callable storage), and
the spec must stay byte-identical across the prepatch, so they are reverted
together in `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps; no A legs

Every step is R or I. The operations that genuinely changed — retaining the
callable at construction (A4) and returning it at deconstruction (B2) — are
modeled **directly** in the impl/deep-models, not behind an axiom. There is no
unchanged foreign callee the proof depends on, so there is **no consumed axiom
and no deep-model reference** (`axioms` region empty; `meta.json axioms=[]`,
`deep_model_references=[]`; G-AX skips). `Backend`/`Producer` identity is an R
refinement of Python object identity (mapping.md §2), checked by G-CONF.

## D. verify(Solution) ⇒ resolved

`roundTripStorage` verifies only if `initField` retains the producer (A4) and
`deconstructStorage` reports it (B2) — i.e. only the gold data-flow satisfies the
frozen spec. By R (`storage`-value ↔ `BackendArg`, object-identity ↔ handle) the
verified lifecycle equals `FileField(storage=arg).deconstruct()['storage']` on
the tested inputs; G-CONF refutes any R/I infidelity over fuzzed `storage`
arguments (including the producer-yields-default corner) by differential
execution against the patched real `FileField`. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The only trust point is refinement
fidelity (this doc + G-CONF); there is no axiom trust point for this bundle.
