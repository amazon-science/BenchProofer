# mapping.md — django__django-11740

## Symbol binding (file:line @ base_commit 003bb34b218adb23d1a7e67932a6ba9b3c4dcc81)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_generateAlteredFields` / `problem_spec_generateAlteredFields` | `MigrationAutodetector.generate_altered_fields` — the per-field loop body's dependency assembly + `add_operation(..., dependencies=...)` | `django/db/migrations/autodetector.py:904-978` |
| `getDependenciesForForeignKey` (pure helper, A-reference) | `MigrationAutodetector._get_dependencies_for_foreign_key` | `django/db/migrations/autodetector.py:1060-1077` |
| `Dep` (pure helper) | one dependency tuple `(app_label, model_name_or_object_name, field_name, create)` consumed by `add_operation` (`_auto_deps`) | `autodetector.py:437-439`, format documented at `:438` |
| `FKInfo` (pure helper) | the reference-target data read by `_get_dependencies_for_foreign_key` off `new_field`: `swappable_setting`, `remote_field.model._meta.{app_label,object_name}`, `remote_field.through._meta.{app_label,object_name,auto_created}` | `autodetector.py:1062-1076` |
| `AlteredField.isRelation` | `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` — whether the new field is a relation | `autodetector.py:917`, `:940` (the guard around the `dependencies.extend(...)` line) |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean type | Python value |
|---|---|
| `Dep { appLabel, objectName, fieldName, create }` | tuple `(app_label:str, object_name:str, field_name:str|None, create:bool)` — Django's `(app_label, model_name, field_name, create/delete)` dependency 4-tuple (`autodetector.py:438`) |
| `FKInfo.swappableSetting : Option String` | `getattr(field, 'swappable_setting', None)` (a settings name like `"AUTH_USER_MODEL"`, else `None`) |
| `FKInfo.remoteAppLabel / remoteObjectName : String` | `field.remote_field.model._meta.app_label` / `field.remote_field.model._meta.object_name` |
| `FKInfo.through : Option (String × String × Bool)` | `field.remote_field.through` → `(through._meta.app_label, through._meta.object_name, through._meta.auto_created)` when truthy, else `None`. The Lean `autoCreated` flag mirrors `_meta.auto_created`; the Python guard is `through and not through._meta.auto_created`. |
| `AlteredField.isRelation : Bool` | truthiness of `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` |
| `List AlteredField` | the sequence of `new_field`s for the keys in `sorted(self.old_field_keys & self.new_field_keys)` whose deconstruction differs and which take the `both_m2m or neither_m2m` branch (the `AlterField` branch) |
| `AlterFieldOp { field, dependencies }` | one emitted `AlterField` operation, restricted to its altered field (identity) and the `dependencies` list passed to `add_operation` for it |
| `List AlterFieldOp` (result) | the sequence of emitted `AlterField` operations, in emission order; each pairs the field it alters with the dependency list it carries (`operation._auto_deps`) |

## What the function does (base_commit) and what changes

`generate_altered_fields` iterates the kept field keys; for each field whose
deconstruction changed and that stays a concrete-or-m2m field (the `AlterField`
branch, `autodetector.py:954-974`), it builds an `AlterField` operation and calls
`self.add_operation(app_label, operations.AlterField(...))`.

At base_commit, that `add_operation` call passes **no** `dependencies`, so
`operation._auto_deps = []` (`add_operation`, `:439`) for every altered field —
including a field that has just become a relation. The gold patch:

1. introduces a per-iteration `dependencies = []` (`autodetector.py:912`+);
2. inside the relation guard (`hasattr(new_field,"remote_field") and
   getattr(new_field.remote_field,"model",None)`), after the rename handling,
   appends `self._get_dependencies_for_foreign_key(new_field)`
   (`autodetector.py:940`+);
3. passes `dependencies=dependencies` into the `add_operation` /`AlterField` call
   (`autodetector.py:972`+).

So the OBSERVABLE behavior change is exactly: an altered field that is a relation
now contributes the FK-induced ordering dependencies to its `AlterField`
operation; a non-relation altered field still contributes none.

`_get_dependencies_for_foreign_key(field)` (`autodetector.py:1060-1077`):
* base dep: `("__setting__", field.swappable_setting, None, True)` when
  `field.swappable_setting is not None`; else
  `(field.remote_field.model._meta.app_label,
    field.remote_field.model._meta.object_name, None, True)`;
* if `field.remote_field.through` is truthy AND
  `not field.remote_field.through._meta.auto_created`, append
  `(through._meta.app_label, through._meta.object_name, None, True)`.

This is modeled DEEPLY as `getDependenciesForForeignKey` (refinement.md tag
**A-reference**), validated == the real callee by G-AX.

## Callee provenance + flag deps

- `_get_dependencies_for_foreign_key` — UNCHANGED by the patch; modeled deeply
  (A-reference), G-AX-validated. Its flag dependency: the through-dep is appended
  only when the relation has an explicit, non-auto-created intermediary model
  (`through and not through._meta.auto_created`) — `FKInfo.through =
  some (_,_,autoCreated)` with `autoCreated = false`. The swappable branch fires
  only when `swappable_setting is not None`.
- The rename-handling block (`autodetector.py:917-948`) mutates `new_field`'s
  remote/from/to fields for renamed models; it is UNCHANGED by the patch and
  orthogonal to the dependency-list computation (it adjusts which model/field the
  relation points at; `_get_dependencies_for_foreign_key` then reads the adjusted
  target). The modeled `FKInfo` carries the post-adjustment reference target, so
  the rename block is folded into the input value (not separately modeled).
- The not-null-alteration questioner branch (`:957-963`) and the
  m2m↔concrete `else` branch (`:975-978`) do not change the `dependencies` list
  and are not modeled; the modeled loop assembles the dependency list that the
  patch newly threads through.

## G-CONF fuzz seed

Pinned seed: **11740** (also set in `conformance_check.py`).
