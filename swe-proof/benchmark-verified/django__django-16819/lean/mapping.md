# mapping.md — django__django-16819

## Symbol binding (file:line @ base_commit 0b0998dc151feb77068e2387c34cc50ef6b356ae)

Modeled function: the `reduce` method ADDED to `AddIndex` by the gold patch,
`django/db/migrations/operations/models.py` (the new method inserted at
post-patch line 864, immediately after `AddIndex.migration_name_fragment` at
`models.py:860-862`):

```python
def reduce(self, operation, app_label):
    if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
        return []
    return super().reduce(operation, app_label)
```

`super()` here resolves to `IndexOperation` → `Operation`, whose unchanged
`reduce` is `django/db/migrations/operations/base.py:128-138`:

```python
def reduce(self, operation, app_label):
    if self.elidable:
        return [operation]
    elif operation.elidable:
        return [self]
    return False
```

Lean modeled function name: `reduceAddIndex` (names the *behavior* — reducing an
add-index operation against the following operation — not a patched repo symbol;
`reduce`/`AddIndex`/`RemoveIndex` are not echoed; see G-LEAK note below).

| Lean symbol | Python binding (file:line @ base_commit) |
|---|---|
| `reduceAddIndex` (modeled decision) | `AddIndex.reduce(self, operation, app_label)`, the method ADDED at `models.py:864-867` (post-patch) |
| `selfName : String` | `self.index.name` — the name of the index the add-index operation creates (`AddIndex.__init__` stores `self.index`, `models.py:811-819`; `Index.name`) |
| `op : OpArg` | `operation` — the following migration operation the reduction is asked about |
| `op.isRemoveIndex : Bool` | `isinstance(operation, RemoveIndex)` (`RemoveIndex` class, `models.py:864`) |
| `op.name : String` | `operation.name` — the index name a `RemoveIndex` targets (`RemoveIndex.__init__`, `models.py:866-869`; `self.name`) |
| `op.elidable : Bool` | `operation.elidable` — the only attribute of `operation` the generic fallback `Operation.reduce` inspects (`base.py:136`) |
| `appLabel : String` | `app_label` — the application label, threaded unchanged to `super().reduce(operation, app_label)` |
| `baseReduce selfName op appLabel : ReduceResult` (opaque, A-reference) | `super().reduce(operation, app_label)` == `Operation.reduce`, `base.py:128-138` (UNCHANGED by the patch) |
| `ReduceResult.replace ops` | a `list` of operations returned by `reduce` (the `[]` annihilation, or `[operation]`/`[self]` from the base) |
| `ReduceResult.cannot` | the `False` sentinel returned by `Operation.reduce` meaning "cannot optimize across" |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean |
|---|---|
| the following operation `operation`, observed only via `isinstance(_, RemoveIndex)`, `.name`, and `.elidable` | `OpArg { isRemoveIndex : Bool, name : String, elidable : Bool }` |
| `self.index.name` (a `str`) | `selfName : String` |
| `operation.name` (a `str`, meaningful when `isinstance(operation, RemoveIndex)`) | `op.name : String` |
| `app_label` (a `str`) | `appLabel : String` |
| `reduce(...)` result: `list[Operation]` | `ReduceResult.replace (ops : List OpArg)` |
| `reduce(...)` result: `False` | `ReduceResult.cannot` |
| `[]` (empty replacement list — the add/remove annihilation) | `ReduceResult.replace []` |
| `super().reduce(operation, app_label)` (`Operation.reduce`) | `baseReduce selfName op appLabel` (opaque A-reference) |

### Modeling notes
- **`OpArg` is the observation interface, not the full operation.** The add-index
  reduction inspects `operation` through exactly three observables:
  `isinstance(operation, RemoveIndex)`, `operation.name`, and (inside the base
  fallback) `operation.elidable`. `OpArg` carries precisely those three fields.
  This is the minimal faithful model (SPEC_GUIDE §2 "rich object → structure with
  only the touched fields").
- **`baseReduce` is an A-reference, not a consumed axiom.** `super().reduce` is an
  UNCHANGED callee the new method delegates to. The spec does not pin its value;
  it only states that, outside the same-name remove-index branch, the result IS
  whatever the base reducer yields for the same two operations. The proof closes
  by case split + `rfl` against the opaque `baseReduce` and consumes NO property
  of it, so it is referenced (G-AX validates the model == real `Operation.reduce`)
  rather than axiomatized. No `baseReduce_prop` axiom is needed.
- **The discriminator is the guard `isinstance(operation, RemoveIndex) and
  self.index.name == operation.name`.** This is the only behavior the patch adds;
  everything else defers to the unchanged base. The spec pins the guard exactly
  and frames the else-branch to the base reducer (SPEC_GUIDE §0.5 frame
  discipline: the fallback result is pinned to `baseReduce`, not left free).

### G-LEAK note
The `problem_statement` is "Reduce Add/RemoveIndex migration operations… We
should reduce AddIndex/RemoveIndex operations when optimizing migration
operations." The terms *reduce*, *AddIndex*, *RemoveIndex*, *optimize*,
*migration operations*, and *index name* are all public in the solver-visible
problem statement, so describing the behavior in those terms is not leakage. The
Lean identifiers nonetheless avoid echoing the patched repo symbols (`reduce`,
`AddIndex`, `RemoveIndex`, `super`); the spec view names no file/line and does
not narrate the edit (it states the desired behavior, not "a method was added").

## G-CONF fuzz seed
Pinned seed: **16819** (also in `conformance_check.py`).
