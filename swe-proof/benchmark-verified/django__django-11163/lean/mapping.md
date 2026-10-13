# mapping.md — django__django-11163

## Instance
- repo: django/django
- base_commit: e6588aa4e793b7f56f4cadbfa155b581e0efc59a
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`model_to_dict(instance, fields=None, exclude=None)` (django/forms/models.py:78-91)
builds a `{name: value}` dict by walking the model's fields in order. For each
field `f` it skips the field when any of these hold:

1. `f` is not editable (`not getattr(f, 'editable', False)`);
2. a field-name selection is in force and `f` is not in it;
3. an exclusion list is in force and `f` is in it.

Otherwise it records `data[f.name] = f.value_from_object(instance)`.

At base_commit the selection test (item 2) is written `if fields and f.name not in
fields:`. In Python an empty list is falsy, so when the caller passes the empty
selection `fields=[]`, the guard `fields` is false and the field is NOT skipped —
the function returns ALL editable fields instead of none. The gold patch rewrites
the guard to `if fields is not None and f.name not in fields:`, distinguishing
"no selection supplied" (`fields is None` → include all) from "an empty selection
supplied" (`fields == []` → include none).

```python
-        if fields and f.name not in fields:
+        if fields is not None and f.name not in fields:
             continue
```

The exclusion test (item 3, `if exclude and f.name in exclude:`) is NOT changed.
Its truthy guard is behavior-irrelevant: `f.name in exclude` is already false for
an empty/absent exclusion, so `exclude is None`, `exclude == []`, and any
exclusion not containing `f.name` all leave the field in. The model preserves this
exact (unchanged) semantics.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_modelToDict` | `model_to_dict` (django/forms/models.py:78) — the dict it returns |
| `problem_spec_modelToDict`   | the post-condition that dict must satisfy |
| `Field` (structure)          | one element of `chain(opts.concrete_fields, opts.private_fields, opts.many_to_many)` (a model field object), restricted to the three attributes the function reads |
| `Field.name`                 | `f.name` |
| `Field.editable`             | `getattr(f, 'editable', False)` |
| `Field.val`                  | `f.value_from_object(instance)` — the field's extracted value for this instance, carried as a given attribute (unchanged by the patch) |
| `fields` parameter           | the `fields` argument: `none` ↔ `None`, `some xs` ↔ the Python list `xs` |
| `exclude` parameter          | the `exclude` argument: `none` ↔ `None`, `some xs` ↔ the Python list `xs` |
| result `: List (String × α)` | the returned `dict` as an insertion-ordered list of `(name, value)` pairs |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `fs : List (Field α)` | `list(chain(opts.concrete_fields, opts.private_fields, opts.many_to_many))` | iteration order preserved; each element duck-typed with `.name`, `.editable`, `.value_from_object` |
| `Field.val : α` | `f.value_from_object(instance)` | modeled as a generic value `α`; in G-CONF bound to a concrete deterministic value per field |
| `fields : Option (List String)` | `fields: Optional[list[str]]` | `none↔None`, `some xs↔xs` |
| `exclude : Option (List String)` | `exclude: Optional[list[str]]` | `none↔None`, `some xs↔xs` |
| result `List (String × α)` | the returned `dict` | Python dict iteration order == insertion order == field walk order; bijection is `list(d.items())` |

`String` ↔ Python `str` field-name; `List` order ↔ dict insertion order.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The only callee `model_to_dict`
  invokes per field is `f.value_from_object(instance)`, whose result is unchanged by
  the patch and is not constrained by the spec beyond "it is this field's value".
  It is therefore modeled as a carried attribute `Field.val` (a type refinement, R),
  NOT axiomatized. `axiom_check.py` is a skip stub.
- No flag dependency.

## G-CONF fuzz seed
- pinned seed: `11163`
- ≥10^5 fuzzed inputs, each a random list of duck-typed field objects (random
  names, random `editable` flags, deterministic per-field values) together with
  `fields` and `exclude` each drawn from {`None`, `[]`, a random subset of present
  names, names absent from the list}. The empty-selection case (`fields=[]`) and
  the empty-exclusion case (`exclude=[]`) are oversampled (the discriminating
  behaviors). Each input is run through the REAL patched `model_to_dict` (oracle)
  and the R/I Python shadow of `implementation_modelToDict`; results compared as
  ordered `(name, value)` lists.
