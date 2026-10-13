# mapping.md — django__django-13343

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ece18207cbb64dd89014e279ac636a6c9829828e`, states the type
abstraction, and gives the provenance of each modeled callee.

Repo file under change: `django/db/models/fields/files.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| class `AttachmentField` | `class FileField(Field)` — `django/db/models/fields/files.py:216` | the field carrying the touched state (`storage`, `_storage_callable`) |
| `AttachmentField.store` | `FileField.storage` instance attribute — set in `FileField.__init__` at `files.py:230,232` | the live concrete storage backend the field uses at runtime |
| `AttachmentField.has_producer` / `AttachmentField.producer_id` | the presence (via `getattr(self, '_storage_callable', ...)`) and value of `FileField._storage_callable` — set in `__init__` (post-patch line) | whether the field recorded the original callable, and its identity |
| `configure(field, given, given_is_producer, evaluated)` | the storage-handling block of `FileField.__init__` — `files.py:230-237` | the modeled changed function (configuration site) |
| `describe_store(field)` | the storage-handling block of `FileField.deconstruct` — `files.py:281-282` | the modeled changed function (description / deconstruction site) |
| `default_store_id()` | `django.core.files.storage.default_storage` (`files.py:8` import; compared at `files.py:281`) | the ambient default storage singleton, reserved identity 0 |

Pre-patch repo state the change introduces / alters (for the refinement audit;
NOT referenced from the consumer spec view):
- `FileField.__init__` (`files.py:230-237`) evaluated a callable storage
  (`self.storage = self.storage()`) but stored **no** reference to the original
  callable. The patch adds `self._storage_callable = self.storage` immediately
  before the call.
- `FileField.deconstruct` (`files.py:281-282`) emitted
  `kwargs['storage'] = self.storage` (the evaluated backend). The patch changes
  this to `kwargs['storage'] = getattr(self, '_storage_callable', self.storage)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a storage backend object (a `Storage` instance, e.g. `temp_storage`) | `int` (its object identity) | distinct objects ⇔ distinct ints; `x is y` ⇔ `x_id == y_id` |
| a storage *callable* (a function like `callable_storage`, or a callable `Storage` subclass) | `int` (its object identity) | a callable supplied as `storage` is a distinct object ⇒ a distinct id; `given_is_producer` carries `callable(self.storage)` |
| evaluating the callable: `self.storage()` | `int evaluated`, with the precondition `evaluated != given` | calling a real producer returns a **separate** storage object (`callable_storage()` returns `temp_storage`, a different object than the function `callable_storage`). The precondition `evaluated != given` is the faithful, sound abstraction of this; `evaluated != default` because the yielded store is a real backend. |
| `default_storage` (the ambient default singleton) | reserved id `0` (`default_store_id()`) | `self.storage is not default_storage` ⇔ `field.store != default_store_id()` |
| `self._storage_callable` present? | `field.has_producer: bool` | `getattr(self, '_storage_callable', self.storage)` ⇔ `field.producer_id if field.has_producer else field.store`; the gold hunk sets `_storage_callable` ONLY inside the `if callable(...)` branch, so on the non-producer branch `configure` leaves `producer_id` untouched (`producer_id == Old(producer_id)`) — writing anything there would model recording a spurious producer for a concrete store |
| `kwargs['storage']` key absent vs. present | `describe_store` returns `Optional[int]`: `None` ⇔ key absent (storage is default), `int` ⇔ key present with that value | the F2P reads `kwargs['storage']`; the key is present iff the storage is not the default |

`self.storage = storage or default_storage` (`files.py:230`): the F2P field is
configured with a concrete callable/store, so `storage` is truthy and the live
store is exactly the supplied value (or its evaluation). Modeled by the
precondition `given != default_store_id()` (a real store/producer is supplied).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py as A-references)

There is **no consumed `@ContractOnly` axiom**: the behaviour is pure
object-identity and field-state logic, modelled deeply. Two facts the model
encodes about real Python are validated out-of-band by `axiom_check.py` (G-AX)
as **A-references** (deep-model ⇔ real semantics), not consumed as axioms:

### 3.1 Producer evaluation yields a distinct object (A-reference)
`self.storage()` returns an object distinct from `self.storage` (the callable).
Source / evidence: in `tests/file_storage/models.py`, `callable_storage` is a
function whose body `return temp_storage` yields the module-level
`FileSystemStorage` instance `temp_storage` — a different object than the
function `callable_storage` itself; and `CallableStorage().__call__` returns a
fresh/`self` storage, again a `Storage`, not the callable type viewed as the
configured value. axiom_check.py asserts, on the real test producers, that
`producer() is not producer` and `isinstance(producer(), Storage)`. This is the
`evaluated != given` precondition of `configure`.

### 3.2 Default-store identity comparison (A-reference)
`self.storage is not default_storage` is a Python identity test against the
`django.core.files.storage.default_storage` singleton. Modeled by the reserved
id `0`; axiom_check.py confirms a non-default supplied storage is `is not`
`default_storage` (so the `storage` key IS emitted for the F2P field) and that
`default_storage is default_storage` (so for an unconfigured field the key is
suppressed). Provenance: `django/db/models/fields/files.py:8,281`.

The round-trip the F2P test observes (`deconstruct()['storage'] is callable_storage`)
is the composition `describe_store(configure(...))`: configuring with a producer
records the producer (3.1's distinct evaluation makes the recorded producer
observably different from the live store), and describing returns that recorded
producer — exactly `assertIs(storage, callable_storage)`.
