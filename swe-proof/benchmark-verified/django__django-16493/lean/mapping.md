# mapping.md — symbol binding & type bijection (django__django-16493)

## Modeled function
- **Lean** `implementation_recordedStorage : Option Nat → Nat → Nat → Option Nat`
- **Python** `FileField.deconstruct(self)` —
  `django/db/models/fields/files.py:293-300 @ base_commit`.

The modeled behavior is the storage-kwarg decision inside `deconstruct`. The
field stores two storage-related attributes, set in `__init__`
(`files.py:235-253 @ base_commit`):

```python
self.storage = storage or default_storage      # the EVALUATED storage instance
if callable(self.storage):
    self._storage_callable = self.storage       # the ORIGINAL callable, kept for deconstruct
    self.storage = self.storage()                # ... and self.storage is replaced by its result
```

So `self.storage` is always an evaluated `Storage` instance, while
`_storage_callable` (present only when the caller passed a callable) holds the
original, unevaluated reference. `deconstruct` decides which storage reference,
if any, to record in `kwargs`:

```python
# base (buggy): compares the EVALUATED storage to default
if self.storage is not default_storage:
    kwargs["storage"] = getattr(self, "_storage_callable", self.storage)

# patched: compute the ORIGINAL reference first, compare THAT to default
storage = getattr(self, "_storage_callable", self.storage)
if storage is not default_storage:
    kwargs["storage"] = storage
```

The observable behavior demanded by the F2P test
(`test_deconstruction_storage_callable_default`): a callable that returns
`default_storage` must still be recorded in `kwargs["storage"]` (it is a
non-default *reference* even though it evaluates to the default instance). The
buggy code compares the evaluated value (`default_storage`), so it wrongly drops
the kwarg.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `getattr(self, "_storage_callable", <sentinel>)` — the original callable, or absent | `originalCallable : Option Nat` | `some c` = a callable reference was supplied (identity `c`); `none` = no callable was supplied |
| `self.storage` — the evaluated `Storage` instance | `evaluatedStorage : Nat` | object identity modeled as a `Nat` |
| `default_storage` — the module-global default | `defaultStorage : Nat` | object identity modeled as a `Nat` |
| the recorded `kwargs.get("storage")` after deconstruct | `result : Option Nat` | `some r` = `kwargs["storage"] = <object identity r>`; `none` = key absent |

Identity bijection note: Python `is` comparisons map to `Nat` equality on the
modeled identities. The original reference that `deconstruct` records is
`getattr(self, "_storage_callable", self.storage)` = `originalCallable.getD
evaluatedStorage` (the callable when present, else the evaluated instance — which
is what the absent-attribute fallback yields). Two distinct Python objects have
distinct identities (distinct `Nat`s); the same object has the same `Nat`.

The key subtlety the F2P test exercises: a callable that returns
`default_storage` has its OWN identity (`originalCallable = some c` with
`c ≠ defaultStorage`) while evaluating to `evaluatedStorage = defaultStorage`.
The patched code records `some c`; the buggy code records `none`.

## Callee provenance
- `getattr(self, "_storage_callable", self.storage)` is a plain attribute lookup
  with a default — reproduced concretely as `originalCallable.getD
  evaluatedStorage` (I/R), not axiomatized.
- The `is not default_storage` identity test is the **changed op** (it now runs
  against the original reference rather than the evaluated instance); modeled
  deeply as `Nat` inequality, NOT axiomatized.
- `super().deconstruct()` (`Field.deconstruct`) produces `name, path, args,
  kwargs`; the `max_length`/`upload_to` handling is unchanged by the patch and is
  orthogonal to the storage decision — out of model scope. No `opaque`/axiom is
  needed: the axioms region is empty and G-AX is a skip stub.

## Flag dependency
`_storage_callable` exists iff the caller passed a callable `storage`
(`__init__` line 242: `if callable(self.storage)`). This is exactly the
`originalCallable = some _` vs `none` distinction. G-CONF fuzzes both.

## Scope note
The fix is confined to the storage-kwarg lines; `name`, `path`, `args`, and the
remaining `kwargs` entries (`max_length`, `upload_to`) are unaffected and are not
modeled — directive 5 frame is satisfied because the modeled output (the recorded
storage reference) is fully pinned to the inputs.

## G-CONF fuzz seed
Pinned seed: **16493**. ≥10^5 fuzzed inputs over original-callable presence,
distinct/coinciding identities for the original reference, evaluated instance,
and default — oversampling the discriminating case (a non-default callable that
evaluates to the default).
