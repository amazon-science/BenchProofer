# mapping.md — django__django-11433

## Symbol binding (file:line @ base_commit 21b1d239125f1228e579b1ce8d94d4d5feadd2a6)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_bindFields` / `problem_spec_bindFields` / `correct_bindFields` | the routine that builds a model instance's field assignments from a bound form's resolved data: for each model field it decides whether to assign the form's resolved value or leave the field at the value already on the instance, deferring file-type fields to a second pass | `django/forms/models.py:31-64` @ base_commit (`construct_instance`) |
| `keepField` (the per-field assign decision) | the chain of `continue` guards inside the `for f in opts.fields:` loop that decides whether `f.save_form_data(instance, cleaned_data[f.name])` runs for `f` | `django/forms/models.py:41-59` |
| the third conjunct of `keepField` (`f.cleanedEmpty`) | `cleaned_data.get(f.name) in form[f.name].field.empty_values` | gold patch, `models.py:53` (added); pre-patch the leave-default guard was only `f.has_default() and value_omitted_from_data(...)` at `models.py:51-52` |
| the file-deferral second pass | `for f in file_field_list: f.save_form_data(instance, cleaned_data[f.name])` | `models.py:61-62` (unchanged) |

## Modeled inputs (abstraction of one `construct_instance` call)

The function under spec is the assignment-building loop. The model takes the
already-resolved per-field observables the routine reads at each iteration; the
unchanged callees (`f.editable`, `isinstance(f, AutoField)`, `f.name in
cleaned_data`, `f.has_default()`, `widget.value_omitted_from_data(...)`,
`cleaned_data.get(f.name) in field.empty_values`, `isinstance(f, FileField)`) are
booleans supplied as inputs — the patch changes none of them, only how they are
combined.

| Lean | Python reality | meaning |
|---|---|---|
| `fieldsFilter : Option (List String)` | the `fields` parameter | `none` ⇔ `fields is None` (no restriction); `some fs` ⇔ only names in `fs` are eligible |
| `excludeList : List String` | the `exclude` parameter (None ↦ `[]`) | names to skip; truthiness ⇔ non-empty |
| `fields : List FieldInput` | `opts.fields` in iteration order | one record per model field |
| `FieldInput.name` | `f.name` | field name |
| `FieldInput.editable` | `f.editable` | |
| `FieldInput.isAuto` | `isinstance(f, models.AutoField)` | |
| `FieldInput.inCleaned` | `f.name in cleaned_data` | |
| `FieldInput.hasDefault` | `f.has_default()` | |
| `FieldInput.omitted` | `form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))` | the widget reports the value absent from the submitted payload |
| `FieldInput.cleanedEmpty` | `cleaned_data.get(f.name) in form[f.name].field.empty_values` | the resolved value is one of the field's empty sentinels |
| `FieldInput.isFile` | `isinstance(f, models.FileField)` | |
| `FieldInput.cleanedValue : String` | `cleaned_data[f.name]` rendered as a value | the resolved value assigned via `save_form_data` |

## Output

| Lean | Python |
|---|---|
| `result : List (String × String)` | the sequence of `f.save_form_data(instance, cleaned_data[f.name])` assignments actually performed, as `(f.name, cleaned_data[f.name])`, in execution order (non-file fields first in `opts.fields` order, then the deferred file fields in `opts.fields` order). A field that hits a `continue` produces NO entry — it keeps the value already on the instance (its model default). |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `fields` param (`None` / list) | `Option (List String)` | `None ↦ none`, `list ↦ some` |
| `exclude` param (`None` / list) | `List String` | `None ↦ []` |
| `opts.fields` | `List FieldInput` | per-field observable record (booleans + name + resolved value as `str`) |
| each `save_form_data(instance, cleaned_data[name])` actually executed | element `(name, value)` of `result` | a field left at default ⇒ no element |
| execution order (two passes) | list order: kept non-file fields, then kept file fields | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** Every operation the loop reads
  (`editable`, `AutoField` test, `cleaned_data` membership, `has_default`,
  `value_omitted_from_data`, `empty_values` membership, `FileField` test) is an
  UNCHANGED callee whose result is supplied as a `FieldInput` boolean. The patch
  changes only the conjunction in the leave-default guard (modeled DEEPLY in
  `keepField`). All rows are R, I, or A-reference, validated by G-CONF.
  `axiom_check.py` is a skip stub.
- **The edit:** the leave-default guard gains a third conjunct — the resolved
  value must itself be empty for the model default to be kept. So a field with a
  default whose value was omitted from the payload BUT whose resolved value is
  non-empty is now assigned that resolved value instead of being left at default.
- **File deferral** does not change which value a field receives (each kept field
  is assigned `cleaned_data[f.name]` exactly once); it only reorders the
  assignment sequence. The model preserves the two-pass order.

## G-CONF fuzz seed

`SEED = 20240629` (pinned in `conformance_check.py`).
