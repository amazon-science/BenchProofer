# mapping.md — django__django-16493

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e3a4cee081cf60650b8824f0646383b79cb110e7`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled construct.

Repo file under change: `django/db/models/fields/files.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serializedStorageArg (storage : Backend) (storageCallable : Option Backend)` | `FileField.deconstruct` — `django/db/models/fields/files.py:293` (the storage-kwarg decision at lines 298–299 pre-patch / 298–300 post-patch) | the modeled changed function: which storage reference, if any, the deconstructed (serialized) form of the field records under the `storage` key |
| `Backend` (structure with `id : Nat`) | a storage object — a `Storage` instance (e.g. `FileSystemStorage`) OR the storage callable the field was configured with | opaque storage reference; only reference identity is observable (the consumer compares the recorded reference to the one it supplied and to the default) |
| `defaultBackend` (`{ id := 0 }`) | `default_storage` — `django/core/files/storage/__init__.py` (the `DefaultStorage` proxy), imported into `files.py` | the one distinguished reference whose presence in the serialized form is redundant and so is omitted |
| `storage : Backend` | `self.storage` — the evaluated backend the field currently holds (`FileField.__init__` lines 240–253: `self.storage = storage or default_storage`; if it was callable, `self.storage = self.storage()`) | the evaluated storage backend |
| `storageCallable : Option Backend` | `getattr(self, "_storage_callable", <absent>)` — present iff the field was configured by a callable (`__init__` line 243 sets `self._storage_callable = self.storage` before evaluating) | the original storage callable the field was configured with, or absent |
| `out : Option Backend` | `kwargs.get("storage")` after `deconstruct` — present iff a `storage` kwarg is emitted | the storage reference recorded in the serialized form, or absent |

The pre-patch behaviour the change corrects (refinement audit only, not in the
consumer spec view): the omit decision was keyed on the **evaluated** backend
`self.storage` (line 298: `if self.storage is not default_storage`), and the
recorded value `getattr(self, "_storage_callable", self.storage)` was read only
*after* deciding to emit. So a field configured by a callable that evaluates to
the default backend had its callable reference dropped, even though that
reference differs from the default.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a storage object (a `Storage` instance, or the configuring callable) | `Backend` (tagged `id : Nat`) | distinct storage references ↔ distinct `id`s; the consumer only observes *which* reference was recorded (object identity — the F2P test uses `assertIs`), so an opaque tagged id is faithful. G-CONF bridges via Python `id(obj)`. |
| `default_storage` (the `DefaultStorage` proxy) | `defaultBackend` | the single default reference ↔ `defaultBackend`; identity comparison `x is not default_storage` ↔ `x ≠ defaultBackend`. G-CONF uses `id(default_storage)`. |
| `self.storage` (the evaluated backend) | `storage : Backend` | the backend the field holds after `__init__` evaluated any callable ↔ `storage`. How it is produced (the unchanged `__init__` callable-evaluation) is folded into this free input. |
| `getattr(self, "_storage_callable", <absent>)` | `storageCallable : Option Backend` | the configuring callable present ↔ `some c`; no callable (field configured by a backend directly, or left default) ↔ `none`. The `getattr(self, "_storage_callable", self.storage)` lookup ↔ `storageCallable.getD storage` (callable when present, else the evaluated backend). |
| `kwargs.get("storage")` after deconstruct | `out : Option Backend` | a `storage` kwarg emitted ↔ `some r`; `"storage" not in kwargs` ↔ `none`. |

The `max_length`/`upload_to` kwargs the surrounding lines handle (files.py:295–297)
are storage-irrelevant and identical pre/post patch; they are outside the
modeled carrier.

## 3. Callee provenance (kind-A)

**None.** There are no axiomatized callees and no deep-model references in this
bundle (`meta.json axioms = []`, `deep_model_references = []`; G-AX skipped). The
only modeled behaviour is *which storage reference the serialized form records*
— a closed `Option`/identity-precedence function of two free inputs. How the
evaluated backend is produced from a callable (`FileField.__init__`'s
`self.storage = self.storage()`) is UNCHANGED by the patch and is abstracted to
the free inputs `storage` / `storageCallable` (§2), not consumed as a contract.
The identity comparison against `default_storage` (the one thing the patch
re-targets — from the evaluated backend to the recorded reference) is modeled
deeply as `(storageCallable.getD storage) ≠ defaultBackend`, validated against
the patched `FileField.deconstruct` by G-CONF (§4), not axiomatized.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16493`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`serializedStorageArg` to Python; the ORACLE constructs a **real patched
`FileField(storage=arg)`** and reads back `deconstruct()[3].get("storage")` (the
in-repo FileField/storage sibling django__django-13343 ORACLE-choice precedent:
building and deconstructing the real field is cheap and isolates the modeled
change exactly). Boundary cases cover the full argument matrix: no storage
(→ default → omitted), a concrete non-default backend, a callable returning a
non-default backend, and the decisive F2P corner — **a callable returning
`default_storage`**, whose evaluated backend is the default but whose recorded
reference is the callable (so it must be emitted, not omitted).
