# mapping.md — django__django-13741

## Instance
- repo: django/django
- base_commit: d746f28949c009251a8741ba03d156964050717f
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`ReadOnlyPasswordHashField` (django/contrib/auth/forms.py:54) is a
`forms.Field` subclass used to display (not edit) a stored password hash. At
base_commit it forces non-editability *imperatively* by overriding two `Field`
methods:

```python
def bound_data(self, data, initial):
    return initial            # ignore submitted data, keep initial
def has_changed(self, initial, data):
    return False              # never report a change
```

and its `__init__` only sets `kwargs.setdefault("required", False)`, leaving the
field's `disabled` attribute at the base default `False`.

The gold patch removes both overrides and instead sets the field's `disabled`
attribute to `True` by default in `__init__`:

```python
 def __init__(self, *args, **kwargs):
     kwargs.setdefault("required", False)
+    kwargs.setdefault('disabled', True)
     super().__init__(*args, **kwargs)
-
-def bound_data(self, data, initial):
-    return initial
-
-def has_changed(self, initial, data):
-    return False
```

`Field.__init__` stores `self.disabled = disabled` (django/forms/fields.py:87),
and the base `Field` methods already special-case a disabled field
(django/forms/fields.py:154-192):

```python
def bound_data(self, data, initial):
    if self.disabled:
        return initial
    return data
def has_changed(self, initial, data):
    if self.disabled:
        return False
    ...
    initial_value = initial if initial is not None else ''
    data_value = data if data is not None else ''
    return initial_value != data_value
```

So the *observable* config of the constructed field is what changes: its
`disabled` attribute is now `True` by default (it was `False`), and as a
consequence the base change-detection decision returns `False` for a
default-constructed field instead of relying on the removed override. The gold
patch also removes `UserChangeForm.clean_password` (forms.py:159), which is no
longer needed once the field ignores submitted data — that is the SAME observable
(the disabled field never accepts a change), not an independent behavior.

`kwargs.setdefault('disabled', True)` means: the effective `disabled` value is
whatever the caller passed, or `True` if the caller passed nothing. This is the
behavior modeled.

The single discriminating observable pinned by the FAIL_TO_PASS test
`test_readonly_field_has_changed` is `field.disabled is True` for a
default-constructed field (pre-patch: `False`).

For this field there is no `to_python` override and no `_coerce`, so the base
`has_changed` reduces, when not disabled, to comparing the initial and submitted
values with `None` normalised to the empty string.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_passwordHashField` | the construction of a `ReadOnlyPasswordHashField` (`__init__`, forms.py:57) followed by its inherited `Field.has_changed(initial, data)` decision (fields.py:175) |
| `problem_spec_passwordHashField`   | the post-condition this construction + decision must satisfy |
| `FieldOutcome.disabled`            | the constructed field's `self.disabled` attribute (fields.py:87) |
| `FieldOutcome.changed`             | the boolean returned by the field's `has_changed(initial, data)` |
| `disabledArg : Option Bool`        | the `disabled` keyword the caller passed to the constructor: `some b` = `disabled=b` supplied, `none` = not supplied (so `setdefault` applies the default `True`) |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `disabledArg : Option Bool` | presence/value of the `disabled` kwarg | `none` ↔ kwarg absent; `some true/false` ↔ `disabled=True/False` |
| `initial : Option String` | the `initial` argument to the change decision | `none` ↔ `None`; `some s` ↔ the string `s` |
| `data : Option String` | the submitted `data` argument | `none` ↔ `None`; `some s` ↔ the string `s` |
| `FieldOutcome.disabled : Bool` | `field.disabled` after construction | direct bool |
| `FieldOutcome.changed : Bool` | `field.has_changed(initial, data)` | direct bool |

`String` ↔ Python `str` value-level equality (the decision only compares the two
values for equality; no per-code-point indexing is involved).

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an `axiom`. The two pieces of base
  `Field` behavior the fix relies on — (a) `__init__` recording the (defaulted)
  `disabled` attribute, and (b) the inherited change decision returning `False`
  when disabled and otherwise comparing initial vs submitted with `None`→`''`
  — are modeled DEEPLY (spelled out in the impl). They are therefore
  **A-reference** legs validated by G-CONF against the real patched field, not
  consumed axioms. `axiom_check.py` is a skip stub.
- No flag dependency beyond the `disabled` kwarg itself, which is modeled
  explicitly as `disabledArg`.

## G-CONF fuzz seed
- pinned seed: `13741`
- ≥10^5 fuzzed cases drawn over: the `disabled` kwarg ∈ {absent, True, False};
  `initial`, `data` ∈ {None, equal strings, differing strings, empty string,
  unicode}. Each case constructs the REAL patched `ReadOnlyPasswordHashField`
  and reads `field.disabled` and `field.has_changed(initial, data)`, comparing
  against the R/I shadow of `implementation_passwordHashField`.
