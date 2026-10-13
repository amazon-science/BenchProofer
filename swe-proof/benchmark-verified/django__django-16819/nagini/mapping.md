# mapping.md — django__django-16819

Binds every model symbol to its repo counterpart at `base_commit`
`0b0998dc151feb77068e2387c34cc50ef6b356ae`, states the type abstraction, and
documents callee provenance.

## 1. Modeled function

| model symbol | repo symbol | repo location (base_commit) | role |
|---|---|---|---|
| `reduce_add_index(index_name, self_elidable, operation)` | `AddIndex.reduce(self, operation, app_label)` | `django/db/migrations/operations/models.py` — added by the gold patch immediately after `AddIndex.migration_name_fragment` at line 862 (the method does not exist at base_commit) | the changed function under specification (the new combination rule for the add-index operation) |

The gold patch adds:

```python
def reduce(self, operation, app_label):
    if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
        return []
    return super().reduce(operation, app_label)
```

`AddIndex` is defined at `django/db/migrations/operations/models.py:811`; its
managed index name is `self.index.name` (the `index` attribute is set in
`AddIndex.__init__`, line 821, and required to be non-empty, lines 816-820).

## 2. Type abstraction

| repo reality | model |
|---|---|
| `self.index.name` (a `str`) | `index_name: List[int]` — the index name as a sequence of Unicode code points (Nagini bans `str` indexing). Read-only ⇒ `Acc(list_pred(index_name), 1/2)` required and ensured (directive 5). |
| `operation` (an arbitrary `Operation` instance) | `operation: Operand`, a minimal class carrying only the touched facets. |
| `isinstance(operation, RemoveIndex)` | `operation.is_remove_index: bool` — the runtime type test, abstracted to a boolean tag. |
| `operation.name` (the removed index's name `str`; exists on `RemoveIndex`, set in `RemoveIndex.__init__`, line 870) | `operation.name: List[int]` — code points; read-only ⇒ `Acc(list_pred(...), 1/2)`. Consulted only under the `is_remove_index` guard, mirroring Python's short-circuit `and`. |
| `self.index.name == operation.name` (Python `str.__eq__`) | `names_equal(index_name, operation.name) == (ToSeq(index_name) == ToSeq(operation.name))` — sequence equality of code points, the faithful refinement of `str ==`. |
| `self.elidable` / `operation.elidable` (the `Operation.elidable` class flag, base.py:32, default `False`) | `self_elidable: bool` / `operation.elidable: bool`. |
| return `[]` | tag `1` (the empty operation list — the pair cancels). |
| return `[operation]` (the `self.elidable` branch of base reduce) | tag `2`. |
| return `[self]` (the `operation.elidable` branch of base reduce) | tag `3`. |
| return `False` (cannot reduce) | tag `0`. |

The mixed list/bool return of the real `reduce` (`list` vs `False`) is modelled
by a single integer-tagged outcome; the optimizer (`optimizer.py:48`) only
distinguishes `isinstance(result, list)` (here tags 1/2/3) from a falsey `False`
(tag 0), and among lists it consumes their contents — captured exactly by the
four tags.

## 3. Callee provenance

The function calls only `super().reduce(operation, app_label)`. The MRO of
`AddIndex` is `AddIndex -> IndexOperation -> Operation`; `IndexOperation`
(models.py:803) does NOT override `reduce`, so `super().reduce` is
`Operation.reduce` (`django/db/migrations/operations/base.py:129-139`):

```python
def reduce(self, operation, app_label):
    if self.elidable:
        return [operation]
    elif operation.elidable:
        return [self]
    return False
```

This is the function-under-specification's own base-class logic (the generic
combination rule), **fully expressible** in Nagini — three branches over two
boolean flags. It is therefore modelled **deeply** as the pure helper
`base_combine(self_elidable, op_elidable)` (1:1 with the three branches above),
**NOT** axiomatized: there is no opaque external callee, hence no `@ContractOnly`
axiom and no `axiom_check.py` axiom-soundness obligation. `Operation.elidable`
defaults to `False` (base.py:32); the model leaves both elidable flags free so
the spec covers the general combination rule, not only the `False/False` case
the F2P test exercises.

The `app_label` parameter is threaded through to `super().reduce` but is never
read by `Operation.reduce` (it is used only by other operations' `reduce`
overrides via `references_model`); it has no effect on the add-index outcome and
is dropped from the model.

## 4. Flag dependencies

None. No stdlib/library callee whose default flags matter (contrast
`html.escape`'s `quote=True`); the change is pure control-flow over the
operation's own attributes.
