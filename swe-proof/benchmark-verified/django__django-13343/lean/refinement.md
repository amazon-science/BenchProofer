# refinement.md — django__django-13343

Operation correspondence between the Lean `implementation_*` skeletons and the
gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: both changed functions are modeled deeply
with concrete Lean operations. Every row is **R** or **I**. (G-AX is therefore a
skip stub; the R/I legs are differential-tested by G-CONF.)

## Behavior A — `implementation_initStorage` ↔ `FileField.__init__`

patch.diff (db/models/fields/files.py) inserts one statement inside the
`callable` branch, retaining the original callable before it is evaluated:

```python
 self.storage = storage or default_storage
 if callable(self.storage):
+    # Hold a reference to the callable for deconstruct().
+    self._storage_callable = self.storage
     self.storage = self.storage()
     ...
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut storage := defaultStorage` | `self.storage = storage or default_storage` (the falsy/default arm) | R | `default_storage` ↦ `defaultStorage : StorageInst`; accumulator init |
| `let mut storageCallable := none` | `_storage_callable` initially unset | I | absence of the attribute ↦ `none` |
| `.useDefault => pure ()` | `storage or default_storage` falls back; not callable | R | falsy arg ↦ `.useDefault`; keeps `storage = defaultStorage` |
| `.inst s => storage := s` | non-callable instance: `self.storage = storage`, branch skipped | R | `Storage` instance ↦ `.inst s`; `callable(...)` is False so no callable retained |
| `.callable c => storageCallable := some c` | `self._storage_callable = self.storage` (the original callable) | R | callable object identity ↦ `c : Callable`; attribute set ↦ `some c`. **This is the added line.** |
| `.callable c => storage := c.result` | `self.storage = self.storage()` | R | evaluating the callable ↦ `c.result : StorageInst` (the produced instance) |
| `return { storage, storageCallable }` | `(self.storage, self._storage_callable?)` field state | R | observable pair read by `deconstruct` |

The `isinstance(self.storage, Storage)` `TypeError` guard is UNCHANGED by the
patch and orthogonal to the modeled behavior; the success path is modeled via
`Callable.result : StorageInst` (a valid instance), the error path is out of
frame (mapping.md).

## Behavior B — `implementation_deconstructStorage` ↔ `FileField.deconstruct`

patch.diff replaces the stored storage value with the retained callable when one
exists:

```python
 if self.storage is not default_storage:
-    kwargs['storage'] = self.storage
+    kwargs['storage'] = getattr(self, '_storage_callable', self.storage)
 return name, path, args, kwargs
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut result := none` | `kwargs` without a `storage` key | I | key-absent state ↦ `none` |
| `if state.storage ≠ defaultStorage` | `if self.storage is not default_storage` | R | identity comparison ↦ `Nat` `≠`; `default_storage` ↦ `defaultStorage` |
| `result := some (match … some c => .callable c …)` | `kwargs['storage'] = getattr(self, '_storage_callable', self.storage)` — present case | R | retained callable ↦ `state.storageCallable = some c` ↦ `.callable c`. **This is the changed line.** |
| `result := some (… none => .inst state.storage)` | `getattr(...)` default arm: no `_storage_callable`, falls back to `self.storage` | R | absent attribute ↦ `none` ↦ `.inst state.storage` |
| `return result` | the `storage` entry of the returned `kwargs` | R | `Option DeconstructStorage` ↦ `kwargs.get('storage')` |

The spec frames the omission case (`state.storage = defaultStorage ⇒ result =
none`, directive 5) and pins the present case to exactly the retained-callable /
resolved-instance disjunction.

## Independently-observable behaviors (G-DIFF)

The fix is a producer→consumer chain across two functions, each with its own
well-defined behavior; the gold patch edits both. One prepatch per hunk:

- `Solution_prepatch_1.lean`: behavior A buggy — the `callable` branch evaluates
  the callable but does NOT retain it (`storageCallable` stays `none`). The
  carried gold proof of `correct_initStorage` fails to close on the `.callable c`
  case (`some c` vs `none`). Observable: with no retained callable, `deconstruct`
  inlines the evaluated instance, breaking the round-trip (FAIL_TO_PASS
  `test_deconstruction`).
- `Solution_prepatch_2.lean`: behavior B buggy — the serialized value always
  echoes the resolved instance (`.inst state.storage`), ignoring any retained
  callable. The carried gold proof of `correct_deconstructStorage` fails to close
  when `state.storageCallable = some c`. Observable: even with the callable
  retained by `__init__`, deconstruction inlines the instance (FAIL_TO_PASS
  `test_deconstruction`).

Each hunk is independently necessary: dropping either reproduces the original
bug, so each must verify against the spec for the bundle to be green.
