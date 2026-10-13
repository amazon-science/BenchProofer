# refinement.md — django__django-13741

Operation correspondence between `implementation_passwordHashField` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The two pieces of base-`Field` behavior the
fix relies on — recording the (defaulted) disabled setting in the constructor,
and the inherited change decision — are modeled DEEPLY in the impl, so every row
is **R**, **A-reference**, or **I**. The R/I/A-reference legs are
differential-tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## What the gold patch changes

```python
 def __init__(self, *args, **kwargs):
     kwargs.setdefault("required", False)
+    kwargs.setdefault('disabled', True)        # POST-PATCH: default the field disabled
     super().__init__(*args, **kwargs)
-
-def bound_data(self, data, initial):           # PRE-PATCH overrides removed
-    return initial
-def has_changed(self, initial, data):
-    return False
```

Pre-patch the field forced non-editability via the two overrides while
`self.disabled` stayed `False`. Post-patch the field carries `disabled = True`
by default and inherits the base `Field` methods, which already special-case a
disabled field (`bound_data` returns `initial`; `has_changed` returns `False`).
The patch also drops `UserChangeForm.clean_password`, which becomes redundant
once the field ignores submitted data — the SAME observable, not an independent
behavior.

## `implementation_passwordHashField` ↔ the patched field

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `let disabled := disabledArg.getD true` | `kwargs.setdefault('disabled', True)` then `self.disabled = disabled` (Field.__init__, fields.py:87) | A-reference | the EDITED op: the effective disabled setting is the caller's value, or `True` when unsupplied. Validated == real `field.disabled` by G-CONF |
| `if disabled then return { …, changed := false }` | base `Field.has_changed`: `if self.disabled: return False` (fields.py:179) | A-reference | inherited disabled branch the fix now relies on (replaces the removed override). Validated by G-CONF |
| `if !(valEq initial data) then changed := true` | base `Field.has_changed` non-disabled path: `initial_value = initial if initial is not None else ''; data_value = data if data is not None else ''; return initial_value != data_value` (fields.py:190-192) | A-reference | value compare with `None`→`''`; this field has no `to_python`/`_coerce` override so the path reduces to equality. Validated by G-CONF |
| `valEq a b := (a.getD "") == (b.getD "")` (pure helper) | `None`→`''` normalisation + `!=` | R | `Option String` (`none`↔`None`) ↦ value equality |
| `return { disabled := disabled, changed := changed }` | `(field.disabled, field.has_changed(initial, data))` | R | observable carrier `FieldOutcome` ↦ the (disabled, changed) pair |

`disabledArg : Option Bool` ↦ presence/value of the `disabled` kwarg
(`none`↔absent, `some b`↔`disabled=b`). `initial`/`data : Option String` ↦
`None | str`.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the constructor applies NO default (defaults to
  `false` when no setting is supplied) and the change decision is hard-wired to
  `false`. So a default-constructed field reports `disabled = false`, whereas the
  spec pins `result.disabled = disabledArg.getD true` (i.e. `true` when
  unsupplied). The carried gold proof of `correct_passwordHashField` fails to
  close on the `result.disabled = disabledArg.getD true` clause (and on the
  change clause for an enabled field whose values differ). This is the single
  fixed behavior. (FAIL_TO_PASS: `test_readonly_field_has_changed`, which asserts
  `field.disabled is True`.)
