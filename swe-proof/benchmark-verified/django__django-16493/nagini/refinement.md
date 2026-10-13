# refinement.md — django__django-16493

The operation-by-operation correspondence between `model.py`'s implementation
(the `deconstruct_storage` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed** / **A-reference**), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The decision site — `FileField.deconstruct()` (`django/db/models/fields/files.py:298-299`)

Gold hunk:
```
-        if self.storage is not default_storage:
-            kwargs["storage"] = getattr(self, "_storage_callable", self.storage)
+        storage = getattr(self, "_storage_callable", self.storage)
+        if storage is not default_storage:
+            kwargs["storage"] = storage
```

The patch reorders so the include/omit guard tests the SAME quantity that is
reported: `storage = getattr(self, "_storage_callable", self.storage)`. The
pre-fix code tested `self.storage` (the already-evaluated concrete store)
instead.

### Type / state abstraction (the R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.storage` (the evaluated concrete store object) | `self.store_id: int` (identity tag) | object identity `x is y` ↔ `store_id_x == store_id_y`; `is not` ↔ `!=` |
| `default_storage` (the module-level default store sentinel) | `default_store_id() == 0` | `x is default_storage` ↔ `id_x == default_store_id()` |
| presence of attribute `_storage_callable` (set iff a callable was supplied) | `self.has_producer: bool` | `hasattr(self, "_storage_callable")` ↔ `has_producer` |
| `self._storage_callable` (the held callable) when present | `self.producer_id: int` (identity tag) | object identity as above |
| `getattr(self, "_storage_callable", self.storage)` | `reported_value(has_producer, producer_id, store_id)` = `producer_id if has_producer else store_id` | `getattr`-with-default ↔ the conditional read |
| `kwargs["storage"] = v` present vs. absent | `Result()[0]: bool` (included) with `Result()[1]: int` the value | inclusion flag ↔ key-present; value tag ↔ the stored object |

A held `_storage_callable` is a callable object; `default_storage` is a concrete
store instance. They are never the same object in the real repo. The model does
NOT assume this as a precondition: the spec is **total** (only read-only
fractional permissions are required), and on the real-world-unreachable corner
`has_producer && producer_id == default_store_id()` the general
include-iff-reported-value-non-default postcondition pins the result to
`(False, default)` — exactly what the gold `storage = getattr(...); if storage
is not default_storage` computes on that hypothetical state (mapping.md §3).
Totalization therefore adds no divergence from the gold anywhere while leaving
no excluded input on which a wrong implementation could verify vacuously.

### Operation correspondence

| # | model.py impl op (`deconstruct_storage`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `self: FileBackedField` with fields `store_id`, `has_producer`, `producer_id` | the `FileField` instance and its `self.storage` / `_storage_callable` attributes | R | object-identity ↔ integer-tag refinement (table above). Only the three attributes `deconstruct()` reads on the storage path are modelled. |
| 2 | `value = self.producer_id if self.has_producer else self.store_id` | `storage = getattr(self, "_storage_callable", self.storage)` | R | `getattr`-with-default ↔ the conditional read of the held producer, falling back to the concrete store. Carrier: identity tags. |
| 3 | `included = value != default_store_id()` | `if storage is not default_storage:` | R + I | identical comparison (`is not` ↔ `!=`), refined to identity tags. The guard is taken from the SAME `value`/`storage` computed in step 2 — this reordering IS the fix. |
| 4 | `return (included, value)` | `kwargs["storage"] = storage` under the guard (else key absent) | R | the boolean `included` ↔ whether the key is set; `value` ↔ the stored object. The surrounding `name, path, args, kwargs` plumbing is unchanged by the gold and is identity (only the storage-kwarg decision changes). |

The other lines of `deconstruct()` (the `super().deconstruct()` call, the
`max_length` deletion, `kwargs["upload_to"]` assignment, the final `return`) are
untouched by the gold hunk and are therefore identity; they do not bear on the
specified behaviour and are not modelled.

## Pre-patch differential (G-DIFF)

`model_prepatch.py` reproduces the buggy guard: it still reports
`value = producer_id if has_producer else store_id` (step 2 unchanged) but takes
the include/omit decision from `self.store_id` (the evaluated concrete store)
rather than from `value`:
```
included = self.store_id != default_store_id()
```
This is byte-for-byte the pre-fix `if self.storage is not default_storage:`. It
**fails** the postcondition
`Result()[0] == (reported_value(...) != default_store_id())` — exactly the spec
sensing the change. The discriminating witness is the F2P case: a producer
(`has_producer == True`, `producer_id != default_store_id()`) that evaluates to
the default store (`store_id == default_store_id()`). Post-fix the field is
included (`reported_value == producer_id != default`); pre-fix it is wrongly
omitted (`store_id == default`). This is precisely
`test_deconstruction_storage_callable_default`.

## No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The changed operation is a pure object-identity
decision (`getattr`-with-default plus an `is not` comparison), modelled
**deeply** as integer-tag identity logic — there is no opaque library callee
under specification, hence no consumed axiom and no A-reference. (`axiom_check.py`
records the real `default_storage`/callable identity disjointness that the model
precondition encodes, as an executable sanity check, but the proof consumes no
`@ContractOnly`.)

## verify(model) ⇒ resolved

`deconstruct_storage` verifies only if (a) the reported value is the producer
when one exists and the concrete store otherwise (step 2), and (b) the
include/omit flag is taken from THAT reported value (step 3). The spec is total,
so the two equality postconditions pin `Result()` as total functions of the
three fields on EVERY input — a verifying implementation agrees with the gold
decision everywhere, with no excluded corner to hide on. By the R-refinement
(object identity ↔ integer tags, `getattr`-with-default ↔ the conditional read)
the verified decision equals the gold `deconstruct()` storage path on every
field configuration, including the discriminating producer-returns-default case.
The gold patch resolves (G-RESOLVE). The only trust point is refinement fidelity
(this document, G-EQ); there are no axioms, so G-AX is vacuous here.
