# mapping.md — django__django-13343

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`ece18207cbb64dd89014e279ac636a6c9829828e`). No prior twin/spec consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_initStorage` / `problem_spec_initStorage` / `correct_initStorage` | `FileField.__init__` storage-resolution block | `django/db/models/fields/files.py:227-241` (block 230-237) |
| `implementation_deconstructStorage` / `problem_spec_deconstructStorage` / `correct_deconstructStorage` | `FileField.deconstruct` storage-kwarg decision | `django/db/models/fields/files.py:276-283` (block 281-282) |

Both functions are CHANGED by the gold patch. They form a **producer→consumer
chain**: `__init__` resolves the field's storage state, and `deconstruct` reads
that state. Neither hunk alone fixes the observable round-trip (see G-DIFF),
but each hunk has its own well-defined, separately-specifiable behavior, so we
model two triples. No callee is axiomatized; both behaviors are modeled deeply.

## Behavior A — `FileField.__init__` (storage resolution)

At `base_commit`:

```python
self.storage = storage or default_storage
if callable(self.storage):
    self.storage = self.storage()
    if not isinstance(self.storage, Storage):
        raise TypeError(...)
```

The gold patch inserts one statement inside the `callable` branch, BEFORE the
callable is evaluated, recording the original callable on the instance:

```python
if callable(self.storage):
    self._storage_callable = self.storage   # <-- added
    self.storage = self.storage()
    ...
```

The observable field state produced by `__init__` (the part `deconstruct`
later reads) is the pair:

* `self.storage`            — the resolved `Storage` instance used at runtime
* `self._storage_callable`  — present iff the `storage` argument was a callable;
  holds the original callable object

### Lean ↔ Python type bijection (behavior A)

| Python | Lean | bijection |
|---|---|---|
| the `storage` constructor argument | `arg : StorageArg` | `None`/falsy ↦ `.useDefault`; a `Storage` instance (non-callable) ↦ `.inst s`; a callable ↦ `.callable c` |
| `default_storage` | `defaultStorage : StorageInst` | the project-default storage instance (identity) |
| a `Storage` instance | `StorageInst` (a `Nat` identity token) | object identity ↦ `id` |
| a callable storage `c` and the instance it returns | `Callable` (`id : Nat`, `result : StorageInst`) | `c` identity ↦ `id`; `c()` ↦ `result` |
| `(self.storage, self._storage_callable?)` | `FieldState` (`storage : StorageInst`, `storageCallable : Option Callable`) | `_storage_callable` absent ↦ `none`; present ↦ `some c` |

Notes / unchanged frame:
* The `isinstance(... , Storage)` `TypeError` guard is UNCHANGED by the patch
  and orthogonal to the modeled behavior. We model the success path only
  (a callable yields a valid `Storage`), captured by `Callable.result :
  StorageInst`. The error path is out of frame.
* `storage or default_storage`: a falsy/absent argument ↦ `.useDefault`
  (resolves to `defaultStorage`). A plain instance is never callable, so it
  takes neither the callable branch nor records a callable.

## Behavior B — `FileField.deconstruct` (storage kwarg)

At `base_commit`:

```python
if self.storage is not default_storage:
    kwargs['storage'] = self.storage
```

The gold patch returns the original callable when one was recorded:

```python
if self.storage is not default_storage:
    kwargs['storage'] = getattr(self, '_storage_callable', self.storage)
```

`getattr(self, '_storage_callable', self.storage)` is the recorded callable if
`__init__` saved one, else the resolved instance.

### Lean ↔ Python type bijection (behavior B)

| Python | Lean | bijection |
|---|---|---|
| the field state read by deconstruct | `state : FieldState` | as produced by behavior A |
| `default_storage` | `defaultStorage : StorageInst` | identity |
| value stored under `kwargs['storage']` (callable or `Storage` instance), or key absent | `result : Option DeconstructStorage` | key absent ↦ `none`; a recorded callable ↦ `some (.callable c)`; a `Storage` instance ↦ `some (.inst s)` |

The decision:
* `self.storage is default_storage`  ↦ `state.storage = defaultStorage` ⇒ key
  omitted (`none`).
* otherwise ↦ `getattr(...)`: `state.storageCallable` is `some c` ⇒
  `.callable c`; `none` ⇒ `.inst state.storage`.

The F2P test `test_deconstruction` asserts `kwargs['storage'] is
callable_storage` — i.e. the deconstructed value is **identically** the original
callable. `DeconstructStorage.callable c` carries `c`'s identity (`Callable.id`,
`DecidableEq`), so the spec pins that exact observable.

## Callee provenance / flag deps

* No UNCHANGED callee needs an axiom. Both changed functions are modeled deeply
  with concrete Lean operations (a 3-way case on the storage argument; an
  identity comparison + `Option` case). → `axioms` region is EMPTY;
  `axiom_check.py` is a skip stub.
* `callable(self.storage)` is the discriminator that splits `StorageArg` into
  `.callable` vs `.inst`/`.useDefault`. There is no runtime config flag.

## G-CONF fuzz seed

Pinned seed: **20240613**. `conformance_check.py` constructs the REAL
`FileField` with each storage-argument shape (default/None, a `Storage`
instance, a callable returning a fresh instance, a callable returning
`default_storage`), calls the REAL `.deconstruct()`, and compares the
`kwargs.get('storage')` identity against the composed Python shadow of
`implementation_initStorage` ∘ `implementation_deconstructStorage` over the full
discrete matrix plus ≥1e5 randomized draws.
