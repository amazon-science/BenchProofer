# mapping.md — django__django-11820

## Symbol binding (file:line @ base_commit c2678e49759e5c4c329bff0eeca2886267005d21)

Modeled function: `Model._check_ordering` (classmethod), the
"check related fields" inner loop — `django/db/models/base.py:1705-1718` at
base_commit. Specifically the per-lookup-path traversal:

```python
for field in related_fields:          # base.py:1705
    _cls = cls
    fld = None
    for part in field.split(LOOKUP_SEP):   # split a "a__b__c" path into parts
        try:
            fld = _cls._meta.get_field(part)         # base.py:1711 (gold adds pk-alias branch)
            if fld.is_relation:
                _cls = fld.get_path_info()[-1].to_opts.model   # advance to related model
            # gold adds:  else: _cls = None
        except (FieldDoesNotExist, AttributeError):
            if fld is None or fld.get_transform(part) is None:
                errors.append(checks.Error(... id='models.E015'))
```

The modeled unit is the **traversal of ONE lookup path** (`field.split('__')`)
through the model graph, producing accept (no E015 for this path) / reject (an
E015 is appended).

## Lean ↔ Python type bijection (G-CONF / G-AX use this)

| Python | Lean |
|---|---|
| a model class (its `_meta`) | a `Nat` index into `models : Nat → ModelInfo` |
| `_cls` (current model, or invalid) | `Option Nat` (`none` = traversal terminated / `None._meta`) |
| `fld` (last resolved field, or `None`) | `Option FieldInfo` |
| `field.split(LOOKUP_SEP)` (list of parts) | `parts : List String` |
| `opts.get_field(part)` → field / raises `FieldDoesNotExist` | `(models c).getField part : Option FieldInfo` (`none` = not found / alias) |
| `opts.pk` (the primary-key field) | `(models c).primaryKey : FieldInfo` |
| `fld.is_relation` | `FieldInfo.isRelation : Bool` |
| `fld.get_path_info()[-1].to_opts.model` (related model) | `FieldInfo.target : Nat` |
| `fld.get_transform(part) is not None` | `FieldInfo.acceptsTransform part : Bool` |
| `'pk'` alias literal | the `String` `"pk"` |
| accept (no E015 appended for this path) / reject | `result : Bool` (`true` = accept) |

Note: in Python `opts.get_field('pk')` raises `FieldDoesNotExist` (pk is an
alias, not a real field) — so the bijection sends `getField "pk" = none`; the
primary-key field is reachable ONLY through `primaryKey`.

## Callee provenance + flag deps

All graph operations are modeled as **data passed in** (`models : Nat → ModelInfo`,
`FieldInfo`), not as opaque callees: the traversal walks a finite model graph
whose per-name field lookups, relation targets, primary-key field, and transform
admissibility are the carrier. Hence there is **no consumed axiom** — the changed
behavior (the per-part resolution control flow) is expressed concretely (R/I);
the graph operations are A-reference data bridged to the real
`opts.get_field` / `opts.pk` / `field.is_relation` / `field.get_path_info` /
`field.get_transform` in G-CONF.

`get_transform` is field-dependent and lookup-registration-dependent
(`register_lookup`); G-CONF fuzzes both registered and unregistered lookups via
`acceptsTransform`.

## G-CONF fuzz seed (pinned): 11820
