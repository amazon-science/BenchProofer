# mapping.md — django__django-13964

## Symbol binding (file:line @ base_commit f39634ff22)
Modeled behavior: the adoption decision inside
`Model._prepare_related_fields_for_save(self, operation_name)`,
`django/db/models/base.py:911-952`. The relevant branch (post-patch) is:

```python
# django/db/models/base.py, _prepare_related_fields_for_save
for field in self._meta.concrete_fields:
    if field.is_relation and field.is_cached(self):
        obj = getattr(self, field.name, None)
        if not obj:
            continue
        if obj.pk is None:                       # related object unsaved -> error path
            ...
            raise ValueError(...)
        elif getattr(self, field.attname) in field.empty_values:   # <-- the fix (line 936)
            # Use pk from related object if it has been saved after
            # an assignment.
            setattr(self, field.attname, obj.pk)
        ...
```

The gold patch changes the guard on line 936 from
`getattr(self, field.attname) is None` to
`getattr(self, field.attname) in field.empty_values`.

- `getattr(self, field.attname)` is the foreign-key field's stored *key value*
  (the scalar column, e.g. `order.product_id`). For a relation to a model with a
  `CharField` primary key, this scalar starts as the empty string `''` (the field
  default), not `None`.
- `obj = getattr(self, field.name)` is the related object (e.g. `order.product`);
  `obj.pk` is its primary key.
- `field.empty_values` (`django/db/models/fields/__init__.py:91`,
  `list(validators.EMPTY_VALUES)`) is `[None, '', [], (), {}]`
  (`django/core/validators.py:16`). For a scalar foreign-key key value the
  reachable members are `None` and `''`.

We model only the single adoption decision the patch changes: given the stored
key value and the related object's (present) primary key, what does the stored
key value become?

Lean modeled function name: `foreignKeyValueOnSave` (names the *behavior* — the
foreign-key key value after the save-preparation adoption decision — abstractly).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `fkValue : Option String` | the stored foreign-key key value `getattr(self, field.attname)` (line 936); `none` ↔ `None`, `some s` ↔ the string scalar `s` |
| `objPk : String` | the related object's primary key `obj.pk` (present, since the `obj.pk is None` branch on line 924 already returned/raised) |
| `fkValueIsEmpty v` | the membership test `getattr(self, field.attname) in field.empty_values`, restricted to the scalar key value's reachable values (`None` and the empty string) |
| `result : Option String` | the stored key value after the branch (`setattr(self, field.attname, obj.pk)` adopts `obj.pk`; otherwise it is unchanged) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| stored FK key value `getattr(self, field.attname)` (a string column, possibly `None`) | `fkValue : Option String` |
| `obj.pk` (the related object's primary key, a non-empty string for the CharField-PK case) | `objPk : String` |
| `x in field.empty_values` where `field.empty_values == [None, '', [], (), {}]`, `x` a scalar FK value | `fkValueIsEmpty x` = `x is None or x == ''` |
| `setattr(self, field.attname, obj.pk)` | `result := some objPk` |
| key value left unchanged | `result := fkValue` |

### empty_values bijection
`field.empty_values` is `[None, '', [], (), {}]`. A foreign-key *scalar* key value
(`order.product_id`) can only ever be `None` or a string; among the empty values
the only reachable members for a string scalar are `None` and `''`. Hence
`getattr(self, field.attname) in field.empty_values` is, on the modeled domain,
exactly `value is None or value == ''`, which is `fkValueIsEmpty`
(`none => true`, `some s => s.isEmpty`). The list/tuple/dict members of
`empty_values` are unreachable for a scalar FK key value and are not part of the
modeled domain.

### Result-type modeling note
The real method mutates `self` via `setattr` and returns `None`; the single
observable component the fix changes is the stored key value
`getattr(self, field.attname)` after the branch. We model that scalar as the
result. The F2P test
(`test_save_fk_after_parent_with_non_numeric_pk_set_on_child`) observes exactly
this: after `child.save()` it asserts `child.parent_id == parent.name` (the
adopted pk) rather than the empty string `''`.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The emptiness membership test
  (`in field.empty_values`) is modeled deeply as `fkValueIsEmpty` over the
  scalar's reachable values, and the adoption (`setattr ... obj.pk`) is a direct
  assignment. Both are spelled out in the Lean `pure`/`impl` regions, so no
  `opaque`/`axiom` callee contract is required ⇒ `axioms = []`,
  `deep_model_references = []`, `axiom_check.py` is a skip stub (G-AX skips).
- Preconditions (encoded as the modeled domain, not spec conjuncts): the
  adoption branch is only reached when `obj` is truthy (`if not obj: continue`)
  and `obj.pk is not None` (the `obj.pk is None` branch returns first). So
  `objPk` is modeled as a present `String`. The branch where `obj.pk is None`
  (raises `ValueError`) is a separate, unchanged behavior and is out of scope for
  this modeled decision.
- No flag dependency.

## G-LEAK
The solver-visible `problem_statement` publicly names the data-loss scenario:
a `ForeignKey` to a model with a non-auto `CharField` primary key, an empty
related instance whose primary key is set later, `product_id` ending up as the
empty string instead of the related object's `sku`. The spec view names only
abstract behavior ("stored key value", "related object's primary key", "empty",
"empty scalar / empty string", "adopted"). It does NOT name the patched
file/function (`_prepare_related_fields_for_save`), the changed symbols
(`field.empty_values`, `field.attname`, `getattr`/`setattr`), reproduce any
gold-diff line or marker, or narrate the `is None` → `in empty_values` edit
mechanism.

## Pinned G-CONF fuzz seed
`13964`.
