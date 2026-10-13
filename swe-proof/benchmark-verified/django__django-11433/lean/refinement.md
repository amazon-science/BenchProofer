# refinement.md — django__django-11433

Operation correspondence between `implementation_bindFields` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real behavior by
G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. Every per-field predicate the routine
consults is an UNCHANGED callee whose result is supplied as a boolean field of
the `FieldInput` record; the assignment-selection conjunction (the thing the
patch edits) is modeled DEEPLY in `assignField`. Every row is **R**,
**A-reference**, or **I**. The R/I/A-reference legs are differential-tested by
G-CONF; `axiom_check.py` is a skip stub.

## What the gold patch changes (`django/forms/models.py`, `construct_instance`)

A single edit to the "leave the field at its default" guard inside the
`for f in opts.fields:` loop. Pre-patch:

```python
if (f.has_default() and
        form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))):
    continue
```

Post-patch a third conjunct is added:

```python
if (
    f.has_default() and
    form[f.name].field.widget.value_omitted_from_data(...) and
    cleaned_data.get(f.name) in form[f.name].field.empty_values
):
    continue
```

So a field is left at its model default only when it has a default AND its value
was omitted from the payload AND its resolved value is itself an empty sentinel.
A non-empty resolved value now overrides the default. Everything else in the loop
(the editable / auto-key / membership guards, the `fields`/`exclude` filters, the
file-field deferral, the second pass) is unchanged.

## `implementation_bindFields` ↔ the patched loop

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `nameFilter : Option (List String)`, `skipNames : List String`, `fields : List FieldInput` | `fields=None`/list, `exclude=None`/list, `opts.fields` + the per-field observables | R | type bijection in mapping.md; `iter` over `opts.fields` ↦ `for f in fields` |
| `if !f.editable \|\| f.isAuto \|\| !f.inResolved then continue` | `if not f.editable or isinstance(f, models.AutoField) or f.name not in cleaned_data: continue` | I | unchanged skip guard; the three predicates are inputs |
| `if let some names := nameFilter then if !names.contains f.name then continue` | `if fields is not None and f.name not in fields: continue` | I | unchanged `fields` restriction |
| `if !skipNames.isEmpty && skipNames.contains f.name then continue` | `if exclude and f.name in exclude: continue` | I | unchanged `exclude` skip; `exclude` truthiness ↦ `!skipNames.isEmpty` |
| `if f.hasDefault && f.omitted && f.resolvedEmpty then continue` | `if (f.has_default() and value_omitted_from_data(...) and cleaned_data.get(f.name) in field.empty_values): continue` | A-reference | the EDITED guard, modeled deeply; the three predicates are inputs, validated == the real three-way conjunction by G-CONF. (Pre-patch this row drops `f.resolvedEmpty`.) |
| `if f.isFile then fileFields := fileFields ++ [(f.name, f.resolvedValue)] else assigned := assigned ++ [(f.name, f.resolvedValue)]` | `if isinstance(f, models.FileField): file_field_list.append(f) else: f.save_form_data(instance, cleaned_data[f.name])` | I | non-file fields assigned in pass 1; file fields deferred. Each emitted assignment records `(f.name, cleaned_data[f.name])` |
| `return assigned ++ fileFields` | `for f in file_field_list: f.save_form_data(instance, cleaned_data[f.name]); return instance` | R | pass-2 assignments appended after pass-1; the resulting model instance ↦ the ordered assignment sequence (mapping.md: a field left at default emits no entry) |

`value_omitted_from_data`, `has_default`, `empty_values` membership,
`save_form_data`, the `editable`/`AutoField`/`FileField` tests are all UNCHANGED
callees; their per-field results are the `FieldInput` booleans. The patch only
adds a conjunct, so they are A-reference/I rows, never axiomatized (§0.7).

## Independently-observable behavior (G-DIFF)

One fixed behavior, one prepatch variant:

- **`Solution_prepatch.lean`** — the leave-default guard omits the third conjunct
  (`if f.hasDefault && f.omitted then continue`). Fails `correct_bindFields` for
  any field with `hasDefault = true`, `omitted = true`, `resolvedEmpty = false`,
  and otherwise eligible: the prepatch skips it (no assignment ⇒ field keeps its
  default), but `problem_spec_bindFields` demands its `(name, value)` assignment
  be emitted. This is exactly the FAIL_TO_PASS behavior
  (`test_default_not_populated_on_non_empty_value_in_cleaned_data`: a non-empty
  `cleaned_data` value must overwrite the model default). The PASS_TO_PASS empty
  cases (`test_default_populated_on_optional_field`, the checkbox/selectmultiple
  defaults) all have `resolvedEmpty = true`, so both impls agree there — the spec
  pins those too.

The prepatch keeps the spec view byte-identical to `Solution.lean`.
