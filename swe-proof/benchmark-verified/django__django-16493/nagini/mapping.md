# mapping.md — django__django-16493

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e3a4cee081cf60650b8824f0646383b79cb110e7`, states the type
abstraction, and records the (sole) real-world reachability fact relevant to
the totalized spec (§3).

Repo file under change: `django/db/models/fields/files.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deconstruct_storage(self)` | `FileField.deconstruct(self)` — `django/db/models/fields/files.py:293` (storage branch, lines 298-299) | the modeled changed function (its storage-kwarg decision) |
| `FileBackedField` | `FileField` — `django/db/models/fields/files.py:224` | minimal stand-in carrying only the three attributes the storage decision reads |
| `self.store_id` | `self.storage` — set in `FileField.__init__` (`files.py:240,244`), the EVALUATED concrete store | object-identity tag of the evaluated store |
| `self.has_producer` | presence of attribute `self._storage_callable` — set iff `callable(storage)` in `__init__` (`files.py:241-243`) | boolean: was a callable supplied |
| `self.producer_id` | `self._storage_callable` — `files.py:243`, the held original callable | object-identity tag of the held callable |
| `default_store_id()` | `default_storage` — `django.core.files.storage.default_storage` (imported in `files.py`) | identity tag of the canonical default store sentinel |
| `reported_value(...)` | `getattr(self, "_storage_callable", self.storage)` — `files.py:299` (post-patch) / inner of `files.py:299` (pre-patch) | pure spec: the producer if held, else the concrete store |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| Python object identity (`is` / `is not`) | integer identity tags compared with `==` / `!=` | distinct objects ↔ distinct tags; same object ↔ equal tags |
| `self.storage` (a `Storage` instance) | `self.store_id: int` | identity tag |
| `default_storage` (the singleton default `Storage`) | `default_store_id() == 0` | the distinguished tag `0` |
| `_storage_callable` attribute present/absent | `self.has_producer: bool` | `hasattr(self, "_storage_callable")` |
| `self._storage_callable` (a callable object) | `self.producer_id: int` | identity tag |
| `getattr(self, "_storage_callable", self.storage)` | `reported_value(has_producer, producer_id, store_id)` | `getattr`-with-default ↔ the conditional read |
| `kwargs["storage"]` present vs. absent + its value | `Tuple[bool, int]` = `(included, value)` | inclusion flag ↔ key present; value tag ↔ stored object |

`deconstruct()` does not mutate the field; the field's three attributes are
required AND ensured at fractional permission `1/2`, and the postcondition pins
each attribute to its `Old(...)` value (read-only, directive 5).

## 3. Totality; the one real-world reachability fact (no axiom, no precondition)

There is **no `@ContractOnly` axiom** in this bundle — the behaviour is pure
object-identity decision logic, modelled deeply. The specification is also
**total**: the only precondition is the read-only fractional permissions, so
the two equality postconditions pin `Result()` as total functions of the three
fields on **every** field configuration. No input is excluded, so no verifying
implementation can differ from the modelled decision anywhere (there is no
vacuous corner for a wrong implementation to hide on).

One configuration — `has_producer` with `producer_id == default_store_id()`
(i.e. `_storage_callable is default_storage`) — is unreachable in the real
code: `_storage_callable` is set (`files.py:243`) only inside
`if callable(self.storage)` (`files.py:241`) and holds the *callable* (e.g. a
function or a `Storage` subclass with `__call__`); `default_storage` is a
concrete `Storage` *instance* obtained by evaluating that callable
(`self.storage = self.storage()`, `files.py:244`), and `default_storage` is
not itself callable. The callable and its return value are necessarily
different objects, so the held callable can never be the `default_storage`
singleton. The spec nonetheless pins the behaviour there too, by the same
general include-iff-reported-value-non-default rule — which coincides with
what the gold code computes on that hypothetical state (`storage =
getattr(...)` would be `default_storage`, the `is not default_storage` guard
would be false, the kwarg omitted). So totalization adds no divergence from
the gold on any input, reachable or not. The F2P test
`test_deconstruction_storage_callable_default` constructs the *reachable*
neighbour of this corner (`callable_default_storage` is a function returning
`default_storage`), for which the distinct-object fact holds
(`callable_default_storage is not default_storage`) and the spec's general
rule demands inclusion of the producer.

`axiom_check.py` is an executable sanity check (stdlib-only) that exercises this
identity disjointness and the full decision table on the four reachable field
configurations (no-producer/default, no-producer/custom, producer/custom,
producer-returns-default) plus the unreachable totalized corner, confirming the
modelled decision matches the intended behaviour. It consumes no repo code and
no axiom; G-AX is vacuous (no `@ContractOnly`).
