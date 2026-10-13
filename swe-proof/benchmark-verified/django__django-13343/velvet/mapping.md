# mapping.md — django__django-13343

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ece18207cbb64dd89014e279ac636a6c9829828e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance / flag dependencies.

Repo file under change: `django/db/models/fields/files.py` (class `FileField`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initField (arg : BackendArg)` | `FileField.__init__(..., storage=None, ...)` — `django/db/models/fields/files.py:226` (storage handling: lines 229–238) | the modeled changed function (constructor's storage resolution) |
| `deconstructStorage (st : FieldState)` | `FileField.deconstruct(self)` — `django/db/models/fields/files.py:267` (storage kwarg: lines 281–283) | the modeled changed function (deconstruction's `storage` kwarg) |
| `roundTripStorage (arg : BackendArg)` | the composite `FileField(storage=arg).deconstruct()['storage']` lifecycle the F2P test exercises (`tests/file_storage/tests.py::test_deconstruction`) | the composite behavior the fix is about: deconstruct ∘ construct |
| `Backend` | a `django.core.files.storage.Storage` **instance** | the resolved storage object |
| `defaultBackend` | `django.core.files.storage.default_storage` | the ambient storage; `self.storage is not default_storage` gates whether `storage` is emitted (`files.py:282`) |
| `Producer` | a **callable** passed as `storage=` (e.g. the module-level `callable_storage` function, `tests/file_storage/models.py:30`) | a callable storage parameter; `yields` = the `Storage` it returns when called |
| `BackendArg` | the value of the `storage` constructor kwarg / the `storage` deconstruct kwarg | sum of the three shapes the `storage` slot can take |
| `FieldState` | the `(self.storage, self._storage_callable)` pair the constructor leaves behind | the field's retained storage configuration |
| `initState` / `emit` | pure deep models of the two storage code-paths (see §3) | deep models, NOT axiomatized callees |

The post-patch repo symbol the fix introduces (refinement audit only): the
`self._storage_callable` attribute (`files.py:232`, read back via
`getattr(self, '_storage_callable', self.storage)` at `files.py:283`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `storage` constructor kwarg | `BackendArg` | `None`/omitted ↔ `BackendArg.omitted`; a `Storage` instance `s` ↔ `BackendArg.concrete ⟨id(s), bool(s)⟩`; a callable `f` ↔ `BackendArg.producer ⟨id(f), yields, bool(f)⟩` (`yields = ⟨id(f())⟩` when `f` is truthy; when `f` is falsy it is **never called**, so `yields` is unconstrained — the shadow assigns the sentinel default) |
| a `Storage` instance | `Backend` | identity of the storage object ↔ `Backend.handle`; Python truthiness `bool(s)` ↔ `Backend.present` (the value's behavior under the pre-existing `storage or default_storage` presence test); two `Storage` objects are equal-as-`Backend` iff they are the same object (Django compares storage by identity in `deconstruct`'s `is not default_storage` and in the F2P `assertIs`) |
| `default_storage` | `defaultBackend` (`⟨0, true⟩`) | the unique ambient storage (truthy, hence `present := true`); modeled by the reserved handle `0`, which no real `id()` collides with in the shadow (the shadow assigns the default a dedicated sentinel) |
| a callable storage `f` | `Producer` | `Producer.handle` ↔ `id(f)` (the callable's identity, what `deconstruct` must return per the F2P `assertIs(storage, callable_storage)`); `Producer.present` ↔ `bool(f)`; `Producer.yields` ↔ `⟨id(f())⟩` (the `Storage` the callable evaluates to, used as `self.storage`) — consulted only when `present`; a falsy callable is short-circuited away by `storage or default_storage` before the `callable(...)` test, so it is never called and `yields` is never observed |
| the deconstructed `storage` kwarg value | `BackendArg` | absent (kwarg omitted) ↔ `BackendArg.omitted`; the original callable returned ↔ `BackendArg.producer`; a concrete `Storage` returned ↔ `BackendArg.concrete` |
| `storage or default_storage` truthiness short-circuit | the `if …​.present` guard in `initState`'s `.concrete`/`.producer` arms | a falsy `storage` value (falsy callable, falsy `Storage`, `0`, `''`) does not count as supplied: `self.storage` becomes `default_storage`, nothing is retained, and `deconstruct` emits no `storage` kwarg — `initState` maps any not-`present` argument to `{ backend := defaultBackend, origProducer := none }` |
| `callable(self.storage)` test | the `arg` constructor `match`'s `.producer` arm (reached only when `present`) | a value is a `Producer` iff Python `callable(.)` holds for it; the presence test precedes the callable test, exactly as `storage or default_storage` runs before `if callable(self.storage)` |

Modeling note — **producer-yields-default corner.** `emit` checks
`st.backend = defaultBackend` *before* consulting `origProducer`, exactly
mirroring the real `self.storage is not default_storage` guard at `files.py:282`:
a callable that returns `default_storage` makes `deconstruct` emit nothing at
all (no `storage` kwarg), so it is reported as `omitted`, not as the producer.
The model reproduces this (a `Producer` whose `yields = defaultBackend` is
`emit`-ed as `omitted`), and G-CONF fuzzes that corner.

Modeling note — **falsy-storage corner.** The constructor's first storage step
is `self.storage = storage or default_storage` (`files.py:231`, pre-existing):
`or` short-circuits on Python truthiness, so ANY falsy `storage` value — a
falsy callable, a falsy `Storage` instance, `0`, `''` — is discarded and
`self.storage` becomes `default_storage`. The subsequent
`callable(self.storage)` test then sees `default_storage` (not callable), so a
falsy callable is **never called and never retained** (`_storage_callable` is
not set), and `deconstruct` emits no `storage` kwarg. The model carries this
as `.present` (↔ `bool(value)`) on `Backend`/`Producer`: `initState` maps any
not-`present` argument to `{ backend := defaultBackend, origProducer := none }`,
which `emit` reports as `omitted`. Verified against the patched repo (base
`ece18207` + patch.diff): falsy callable / falsy `Storage` / `0` / `''` all
construct to `self.storage is default_storage` and deconstruct with no
`storage` kwarg. G-CONF fuzzes this corner (boundary inputs + pool).

## 3. Callee provenance (deep models — NOT axioms)

This fix changes no foreign callee; it rewires the field's own data-flow.
Accordingly there are **no consumed axioms and no deep-model references to a
foreign callee** (`axioms` region is empty; `meta.json axioms = []`,
`deep_model_references = []`). `initState` and `emit` are *deep models of the
two code paths the patch edits*, not of unchanged callees:

- `initState` models `FileField.__init__`'s storage block (`files.py:229–238`
  post-patch): `self.storage = storage or default_storage`; if
  `callable(self.storage)`, retain `self._storage_callable = self.storage` then
  `self.storage = self.storage()`. The `.producer` arm retaining `some p` is the
  gold-added `self._storage_callable = self.storage` line.
- `emit` models `FileField.deconstruct`'s storage block (`files.py:281–283`
  post-patch): `if self.storage is not default_storage: kwargs['storage'] =
  getattr(self, '_storage_callable', self.storage)`. The `some p => producer p`
  arm is the gold-changed `getattr(self, '_storage_callable', self.storage)`.

Because these model the **changed** operations, they are exercised end-to-end by
G-CONF against the patched real `FileField` (§4 below), not by an axiom check.
There is no `axiom_check.py` in this bundle (G-AX skips: no axioms).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13343`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds is the
transliteration of `initState`/`emit`/`roundTripStorage` (all R/I-tagged ops, no
A-tagged callee in the computed output) to Python over the real `FileField`:
it constructs a real `FileField(storage=arg)` and reads
`deconstruct()[3].get('storage')`, comparing against the shadow's `emit ∘
initState`. Inputs span: omitted storage, a concrete `Storage` instance, a
callable returning a non-default `Storage`, a callable returning
`default_storage` (the producer-yields-default corner), falsy storage values
(a falsy callable, a falsy `Storage` instance, `0`, `''` — the falsy-storage
corner), and randomized mixtures.
