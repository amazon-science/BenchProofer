# mapping.md — django__django-16100

## Symbol binding (base_commit c6350d594c)
- Changed function: `ModelAdmin.changelist_view`
  (`django/contrib/admin/options.py:1989` @ base_commit), specifically the
  bulk list-editable save loop at `options.py:2011-2021`.
- Modeled function name: `changelistView` (de-narrated; the spec view names no
  patched file/symbol).

## What the fix changes
The per-form save loop

```python
for form in formset.forms:
    if form.has_changed():
        obj = self.save_form(...); self.save_model(...)
        self.save_related(...); self.log_change(...)
        changecount += 1
```

is wrapped in `with transaction.atomic(using=router.db_for_write(self.model)):`.
Effect: the loop body's database writes become one atomic unit. If any write or
`log_change` raises, the whole unit rolls back, so the store is observed in its
pre-loop state; otherwise all changes commit together.

## Lean ↔ Python type bijection (used by G-CONF, G-AX)
| Python | Lean | notes |
|---|---|---|
| database store (rows touched by the loop) | `σ` (abstract type var) | only the observable store state matters |
| one changed form's full save sequence (`save_form`→`save_model`→`save_related`→`log_change`) | `f : σ → Except E σ` | success ⇒ `.ok newState`; any raise ⇒ `.error e` |
| `formset.forms` filtered to `has_changed()` | `steps : List (σ → Except E σ)` | front-to-back order preserved |
| `DatabaseError` / any exception propagated out of the loop | `Option E` component of result | `some e` ⇔ an exception propagated |
| committed store state seen by callers / `refresh_from_db()` | `σ` component of result | rollback ⇒ equals original `s0` |

`result : σ × Option E` = (observable store state after the view, propagated
failure if any).

## Callee provenance + flag deps
- `save_form`, `save_model`, `save_related`, `log_change`, `construct_change_message`:
  UNCHANGED callees. They are NOT axiomatized — each form's entire save sequence
  is folded into one input step-function `f`, modeled deeply (A-reference-free:
  the steps are universally quantified inputs, so the theorem holds for every
  possible callee behavior). No `opaque`/`axiom` is needed.
- `transaction.atomic` / `router.db_for_write`: the changed control-flow
  construct itself — modeled deeply as the rollback semantics of `applyAll` +
  the spec's error branch (`result = (s0, some e)`). NOT axiomatized.
- No flag dependencies.

## G-CONF fuzz seed
pinned seed = 16100 (see conformance_check.py).
