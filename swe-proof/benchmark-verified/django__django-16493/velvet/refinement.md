# refinement.md — django__django-16493

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`serializedStorageArg` `do` block) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — A-consumed /
A-reference), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no A-tagged ops** (no
consumed axioms, no deep-model references): the changed behaviour is *which
storage reference the serialized form records*, modeled as a closed
`Option`/identity-precedence function of two free inputs; the unchanged
`__init__` callable-evaluation that produces the evaluated backend is abstracted
to the free inputs `storage` / `storageCallable` (R), not a callee with a
contract to consume.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The storage-deconstruction site — `FileField.deconstruct` (`django/db/models/fields/files.py:293`)

Gold hunk (the behavioural core):
```
         kwargs["upload_to"] = self.upload_to
-        if self.storage is not default_storage:
-            kwargs["storage"] = getattr(self, "_storage_callable", self.storage)
+        storage = getattr(self, "_storage_callable", self.storage)
+        if storage is not default_storage:
+            kwargs["storage"] = storage
         return name, path, args, kwargs
```

| # | Solution.lean impl op (`serializedStorageArg`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `storage : Backend` | `self.storage` — the evaluated backend the field holds (`__init__` evaluated any callable) | R | a storage object ↔ `Backend` (mapping.md §2). How the backend is produced from a callable is unchanged and folded into this free input. |
| A2 | param `storageCallable : Option Backend` | `getattr(self, "_storage_callable", …)` — present iff the field was configured by a callable | R | configuring-callable-or-absent ↔ `Option Backend` (mapping.md §2). The `__init__` line that records `self._storage_callable` is unchanged; whether it is present is the free input. |
| A3 | `let value := storageCallable.getD storage` | `storage = getattr(self, "_storage_callable", self.storage)` (the **moved-up** value computation) | I | the recorded reference is the configuring callable when one was supplied, else the evaluated backend — exactly `getattr(self, "_storage_callable", self.storage)`. The patch's behavioural change is computing this value **before** the identity test (it was read only inside the emit branch pre-patch). G-CONF transliterates `getD`. |
| A4 | `let mut out := none; if value ≠ defaultBackend then out := some value` (= `if value ≠ defaultBackend then some value else none`) | `if storage is not default_storage: kwargs["storage"] = storage` | I (deep model of the re-targeted identity test) | the identity comparison against the default is keyed on the **recorded reference** `value` (post-patch), not on the evaluated backend. Spelled out, not a consumed axiom — G-CONF validates against the patched control flow. The recorded reference is emitted (`some`) unless it is the default backend. |

The post-condition pins this exactly:
`out = (if (storageCallable.getD storage) ≠ defaultBackend then some (storageCallable.getD storage) else none)`.
No implementation that keys the omit decision on the evaluated backend `storage`
instead of the recorded reference `storageCallable.getD storage` can satisfy it.
The discriminating case — `storageCallable = some c`, `storage = defaultBackend`,
`c ≠ defaultBackend` — is exactly the F2P scenario (a callable returning
`default_storage`): the evaluated backend is the default, but the spec requires
`out = some c` (the callable reference is recorded, not omitted).
`Solution_prepatch.lean` reproduces the pre-patch decision (keyed on `storage`:
`if storage ≠ defaultBackend then out := some value`) and **fails**
`out = (if (storageCallable.getD storage) ≠ defaultBackend then …)` precisely
there — and symmetrically in the dual corner where the callable evaluates to a
non-default backend the field no longer holds (G-DIFF).

## B. No second behavioural site

The change is a single re-targeted identity test in one function. The
`max_length` deletion (files.py:295–296) and the `upload_to` assignment (:297)
are storage-irrelevant and identical pre- and post-patch, so they are neither
modeled nor a separate prepatch. The `FileField.__init__` lines that record
`self._storage_callable` and evaluate the callable (:241–244) are unchanged by
this patch and are the source of the free inputs, not a modeled site.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operation that genuinely *changed* — keying the
identity test against `default_storage` on the recorded reference rather than on
the evaluated backend — is modeled **deeply** (the `Option`/identity precedence
`if (storageCallable.getD storage) ≠ defaultBackend then …`), not behind an
axiom about the function under change. There is **no axiomatized callee** and
**no deep-model reference** (`meta.json axioms = []`,
`deep_model_references = []`; G-AX skipped): the unchanged callable-evaluation in
`__init__` and the identity of `default_storage` are abstracted to the free
inputs `storage` / `storageCallable` / `defaultBackend` (an R refinement, A1/A2),
not pre-existing callees with contracts to consume.

## D. verify(Solution) ⇒ resolved

`serializedStorageArg` verifies only if its output is
`if (storageCallable.getD storage) ≠ defaultBackend then some (storageCallable.getD storage) else none`
(A3, A4): it records the configuring callable when one was supplied (else the
evaluated backend), omitting it exactly when that recorded reference is the
default backend. By R (`self.storage` ↔ `storage`; `getattr(self,
"_storage_callable", …)` ↔ `storageCallable`; `default_storage` ↔
`defaultBackend`; `getattr(self, "_storage_callable", self.storage)` ↔
`storageCallable.getD storage`) the verified method equals the patched
`FileField.deconstruct`'s storage choice on every configuration. By G-CONF the
R/I transliteration agrees with the **real patched `FileField` construct +
deconstruct** on ≥10⁵ inputs (and diverges from the pre-patch evaluated-backend
test on the F2P corner, confirming discrimination). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The sole trust point is refinement
fidelity (this doc + G-CONF); there is no axiom-soundness trust point (no axioms).
