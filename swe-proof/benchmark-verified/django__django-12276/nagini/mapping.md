# mapping.md — django__django-12276

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 53d8646f799de7f92ab9defe9dc56c6125448102`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/forms/widgets.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `requires_value(control, value_present)` | `FileInput.use_required_attribute(self, initial)` — `django/forms/widgets.py`, the method **added** to `class FileInput(Input)` (`widgets.py:374`) by the patch, right after `value_omitted_from_data` (`widgets.py:387-388`) | the modeled changed function |
| `generic_requires_value(hidden)` *(axiom — A-consumed)* | `Widget.use_required_attribute(self, initial)` — `django/forms/widgets.py:275-276` (`return not self.is_hidden`), reached via `super().use_required_attribute(initial)` | the unchanged inherited base callee the new method delegates to |
| `UploadControl.hidden` | `Widget.is_hidden` property — `django/forms/widgets.py:209-211` (`return self.input_type == 'hidden' if hasattr(self, 'input_type') else False`) | the only widget field the base decision reads |
| `value_present` (bool) | the truth value of `initial` (Python truthiness `not initial`) | whether a usable value is already carried |

The pre-patch repo arrangement the change rearranges (for the refinement
audit, not referenced from the consumer spec view): `FileInput` had **no**
`use_required_attribute` and so inherited `Widget.use_required_attribute`
(`widgets.py:275-276`); the conjunction `super().use_required_attribute(initial)
and not initial` existed only on the subclass `ClearableFileInput`
(`widgets.py:454-455`). The patch moves that exact method up from
`ClearableFileInput` to `FileInput`; `ClearableFileInput` then inherits the
identical method, so its observable behaviour is unchanged.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `FileInput` widget instance `self` | `UploadControl` object carrying only `hidden: bool` | the base decision `not self.is_hidden` reads exactly the hidden state; `self.is_hidden` ↔ `control.hidden`. For a `FileInput`, `input_type == 'file'`, so `is_hidden` is `False` — but the model keeps it as a free field so the axiom/decision are faithful for any control of this family. |
| `initial` (any object: `None`, a `str`, a `ContentFile`, a stored file value, …) | `value_present: bool` = the truth value of `initial` | the method's only observation of `initial` is the boolean test `not initial`; `initial` truthy ↔ `value_present == True`, `initial` falsy (`None`, `''`, …) ↔ `value_present == False`. `not initial` ↔ `not value_present`. |
| `super().use_required_attribute(initial)` (the inherited `Widget` method) | `generic_requires_value(control.hidden)` (axiom) | the base ignores `initial` and returns `not self.is_hidden`; the boolean result ↔ the axiom's `Result()`. |
| `and` (Python boolean `and` of two `bool`s) | `and` (Nagini boolean conjunction) | both operands are booleans here (`super()`'s result and `not initial`), so Python `and` returns the second operand iff the first is truthy, which for booleans is exactly boolean conjunction. |

`str`/object indexing is irrelevant: `initial` is never indexed or iterated by
the method, only truth-tested, so the boolean carrier is exact for the modeled
operation.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `generic_requires_value` ↔ `Widget.use_required_attribute` (A-consumed)
**Callee:** `django.forms.widgets.Widget.use_required_attribute(self, initial)`
(`django/forms/widgets.py:275-276`):

```python
def use_required_attribute(self, initial):
    return not self.is_hidden
```

The new `FileInput.use_required_attribute` calls this unchanged base method via
`super().use_required_attribute(initial)`. The base method ignores its
`initial` argument and returns `not self.is_hidden`. The axiom encodes exactly
the weakest contract the proof needs:

  `generic_requires_value(hidden) == (not hidden)`,

i.e. the base decision is `True` for a non-hidden control and `False` for a
hidden one, independent of `initial`. The proof consumes this `Ensures` to
discharge the postcondition that decomposes `requires_value` over the two
observed facts.

**Soundness check (G-AX):** `axiom_check.py` constructs the real `FileInput`
widget (and, as a generalization, hidden/visible widgets) and calls the real
inherited `Widget.use_required_attribute` with a battery of `initial` values
(`None`, empty string, non-empty string, a file-like object, integers, lists,
booleans). It asserts the real base result equals `not self.is_hidden`
regardless of `initial` (the axiom), and additionally validates the FULL moved
method `FileInput.use_required_attribute` post-patch equals
`(not self.is_hidden) and (not initial)` over the same battery — i.e. the
modeled conjunction matches the real conjunction on the truthiness of `initial`.
It imports only Django (the package under change). Exit 0 iff sound.
