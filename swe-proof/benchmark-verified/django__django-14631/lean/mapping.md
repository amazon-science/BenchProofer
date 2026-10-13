# mapping.md — django__django-14631

## Instance
- repo: django/django
- base_commit: `84400d2e9db7c51fee4e9bb04c028f665b8e7624`
- spec_provenance: **cold** (derived only from problem_statement + gold patch + repo @ base_commit)

## Modeled function
The patch refactors several form methods so that field values are accessed
through `BoundField` objects. Only ONE of those edits changes observable
behavior; the rest are behavior-preserving code movement (see "Unmodeled,
behavior-preserving" below). The modeled function is the per-field value
selection inside form field cleaning:

- `BaseForm._clean_fields` — `django/forms/forms.py:389-406` @ base_commit.
  Symbol bound to Lean `implementation_cleanFields` / `problem_spec_cleanFields`.

### The behavioral change (what F2P pins)
Pre-patch (`forms.py:389-394` @ base):
```python
for name, field in self.fields.items():
    if field.disabled:
        value = self.get_initial_for_field(field, name)   # raw, re-evaluated
    else:
        value = self._field_data_value(field, self.add_prefix(name))
```
Post-patch:
```python
for name, bf in self._bound_items():
    field = bf.field
    value = bf.initial if field.disabled else bf.data       # cached, stripped
```
For a **disabled** field the clean value now is `bf.initial`. `bf.initial`
(`boundfield.py:212-220` @ base) differs from the raw `get_initial_for_field`
result in two ways:
1. sub-second (microsecond) component is **discarded** when the value is a
   date/time and the field's widget reports `supports_microseconds == False`;
2. it is computed exactly **once** (`cached_property`), so a callable initial is
   not re-evaluated.

The robust, expressible discriminator is (1): on a disabled date/time field with
a non-zero sub-second component whose widget lacks sub-second support, the
patched code yields a sub-second-zeroed value while the pre-patch code yields the
raw value. (Aspect (2), re-evaluation of a non-deterministic callable, is a
temporal/side-effect property; it is not separately modeled — the microsecond
discriminator already separates patched from pre-patch.)

## Callees referenced
- `BaseForm.get_initial_for_field` (`forms.py:490-498` @ base) — returns the
  already-evaluated preset initial. Modeled as the input `FieldModel.rawInitial`
  (the value AFTER any callable evaluation). Not axiomatized.
- `BoundField.initial` micro-strip (`boundfield.py:216-219`) — modeled DEEPLY as
  `boundInitial` (A-reference; no consumed axiom).
- `Field.clean` / `to_python` — unchanged by the patch; on an already-typed
  date/time value `to_python` is the identity, so `field.clean(value)` is modeled
  as the identity on the selected value (the success path the F2P tests exercise:
  `form.errors == {}`). Not axiomatized.
- `_bound_items` / `self.fields.items()` — both enumerate the form's fields in
  declared order; modeled as the input `List FieldModel`.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
| Python | Lean |
|---|---|
| a `datetime`/`time` value | `FieldValue.ts ⟨whole, sub⟩` — `whole` = whole-second-and-coarser component (Int), `sub` = microsecond component (Nat 0..999999) |
| any non-temporal field value (str/int/…) | `FieldValue.other n` (Int payload stands in for an opaque value) |
| one form field + its bound state | `FieldModel ⟨disabled, supportsMicro, rawInitial, data⟩` |
| `field.disabled` | `FieldModel.disabled : Bool` |
| `field.widget.supports_microseconds` | `FieldModel.supportsMicro : Bool` |
| `get_initial_for_field(field, name)` (evaluated) | `FieldModel.rawInitial : FieldValue` |
| `bf.data` (`_widget_data_value(widget, html_name)`) | `FieldModel.data : FieldValue` |
| `self.fields` (ordered) | `List FieldModel` |
| `cleaned_data` (dict, in field order) | `List FieldValue` (i-th entry = i-th field's cleaned value) |

`cleaned_data` is a dict keyed by field name; we model it as a list in field
order. The name↔index bijection is total (field names are distinct and ordered),
so the list carries the same information.

## Unmodeled, behavior-preserving (NOT separate discriminators)
- `changed_data` / `BoundField._has_changed` (`forms.py:437-459`,
  `boundfield.py` new method): pure code movement. `data_value` old
  `_field_data_value(field, add_prefix(name))` == new `bf.data`
  (`html_name == add_prefix(name)`); `initial_value` old `self[name].initial` ==
  new `self.initial`; the hidden-initial branch is copied verbatim. No observable
  change ⇒ no prepatch discriminator ⇒ not modeled.
- `_html_output` loop rewrite, `_bound_items`, `__iter__` docstring: code
  movement, no behavior change.

## G-CONF fuzz seed
Pinned seed: **20140631** (see conformance_check.py).
