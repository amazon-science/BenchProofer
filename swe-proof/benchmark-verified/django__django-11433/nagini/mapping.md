# mapping.md — django__django-11433

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 21b1d239125f1228e579b1ce8d94d4d5feadd2a6`, states the type
abstraction, and records the provenance of each per-field input predicate.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `construct_writes(selected, has_default, omitted, value_empty)` | `construct_instance(form, instance, fields, exclude)` — `django/forms/models.py:31` (body loop lines 41–62) | the modeled changed function: the per-field decision loop deciding which cleaned values are written onto the instance |
| `write_value(selected, has_default, omitted, value_empty)` | the negated "leave defaults" guard of the loop body — `django/forms/models.py:49–53` (post-patch) | pure spec: whether one candidate field's cleaned value is written |
| `result[i]` (a `bool`) | `f.save_form_data(instance, cleaned_data[f.name])` having been executed for field `i` (lines 56–62) | the observable effect: field `i`'s cleaned value written onto the instance |

The repo loop performs the candidacy filtering (lines 42–48) inline; the model
folds the outcome of those four filters into the single boolean `selected[i]`
(see §2). The post-patch "leave defaults" condition (lines 51–53) is

```python
if (
    f.has_default() and
    form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name)) and
    cleaned_data.get(f.name) in form[f.name].field.empty_values
):
    continue
```

so a field is written iff it is `selected` and the above guard is false:
`selected and not (has_default and omitted and value_empty)` — exactly
`write_value`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the ordered fields `opts.fields` iterated by `construct_instance` | positions `i ∈ [0, n)` of four index-aligned `List[bool]` | field in iteration order ↔ index `i`; `n` ↔ `len(opts.fields)` filtered identically |
| the candidacy filters `f.editable ∧ ¬AutoField ∧ f.name ∈ cleaned_data ∧ (fields is None ∨ f.name ∈ fields) ∧ ¬(exclude ∧ f.name ∈ exclude)` (lines 42–48, each `continue`) | `selected[i]: bool` | `selected[i]` ↔ field `i` reaches the "leave defaults" guard (was not `continue`-skipped earlier). A skipped field writes nothing, modeled `write_value(False, …) == False`. |
| `f.has_default()` (`django/db/models/fields/__init__.py:788`) | `has_default[i]: bool` | the boolean returned by `has_default()` |
| `form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))` (`django/forms/widgets.py:260` and overrides) | `omitted[i]: bool` | the boolean returned by `value_omitted_from_data(...)` |
| `cleaned_data.get(f.name) in form[f.name].field.empty_values` — membership of the cleaned value in `empty_values = list(EMPTY_VALUES)`, `EMPTY_VALUES = (None, '', [], (), {})` (`django/forms/fields.py:55`; `django/core/validators.py:13`) | `value_empty[i]: bool` | the boolean value of the `in` test; True iff the cleaned value is one of the recognised empty sentinels |
| `f.save_form_data(instance, cleaned_data[f.name])` executed (lines 56/59/62) | `result[i] == True` | whether the field's cleaned value is written onto the instance. (The FileField deferral, lines 54–62, only re-orders WHEN the same `save_form_data` runs; it does not change WHETHER it runs, so it is the identity for the modeled `whether-written` observation — §3.) |

The four per-field predicates are **boolean-valued inputs**: each repo
expression evaluates to a `bool`, carried by a `List[bool]` entry. No callee is
axiomatized — the changed operation is purely the boolean decision (the added
`and value_empty` conjunct), modeled deeply by `write_value`. `has_default`,
`value_omitted_from_data`, and the `empty_values` membership test are all
unchanged primitives whose outcomes are the boolean inputs; modeling each as a
`bool` carrier is a type refinement (R), not an axiom.

## 3. Why no axiom / no callee provenance section

The patch changes only the `if` guard at lines 51–53 by appending the conjunct
`cleaned_data.get(f.name) in form[f.name].field.empty_values`. It does not call
any new opaque callee whose contract the proof must assume: the three operands
of the guard are already-computed booleans, and the new conjunct is a `bool`
from a stdlib `in` test over a fixed 5-element tuple. The decision is therefore
modeled deeply (`write_value`); there is no `@ContractOnly` axiom, hence no
G-AX-consumed axiom and no callee-soundness obligation. `axiom_check.py`
records this (it asserts the empty-sentinel membership semantics of
`EMPTY_VALUES` and the truth table of the decision against the model, exit 0),
so the bundle has a uniform G-AX entry point even though no axiom is consumed.

The FileField branch (lines 54–62) is unchanged by the patch: both pre- and
post-patch, a written field runs `save_form_data` either immediately or
deferred. The modeled observation is *whether* the cleaned value is written, on
which the deferral is the identity; the F2P test observes the final attribute
value, set by exactly one `save_form_data` call regardless of ordering.
