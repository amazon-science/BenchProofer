# mapping.md — django__django-12754

## Instance
- repo: django/django
- base_commit: `18759b2209ff556aed7f20d83cbf23e3d234e41c`
- modeled file: `django/db/migrations/autodetector.py`

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_createModelDeps` | the per-created-model `dependencies` list built inside `MigrationAutodetector.generate_created_models` | `django/db/migrations/autodetector.py:558–573` |
| self proxy-removal dep `⟨appLabel, modelName, none, false⟩` | `(app_label, model_name, None, False)` | line 558–560 |
| `baseDeps` dotted-base creation dep `⟨ba, bn, none, true⟩` | `dependencies.append((base_app_label, base_name, None, True))` | line 565 |
| `removedFieldDeps` field-removal deps `⟨ba, bn, some f, false⟩` | the `removed_base_fields` loop appending `(base_app_label, base_name, removed_base_field, False)` | lines 566–572 (**the gold fix**, added by patch.diff) |
| primary-key-relation dep `⟨pa, pn, none, true⟩` | `dependencies.append((primary_key_rel._meta.app_label, primary_key_rel._meta.object_name, None, True))` | lines 567–573 |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX

| Lean type | Python reality |
|---|---|
| `Dep := ⟨appLabel, name, field, onCreate⟩` | a dependency 4-tuple `(app_label, model_name, field_name_or_None, on_create_bool)` consumed later by `check_dependency`. `field : Option String` ↔ `field_name` (`none ↔ None`). `onCreate : Bool` ↔ the trailing bool (`true ↔ create`, `false ↔ removal/deletion`). |
| `Base.dotted ba bn` | a base entry of `model_state.bases` that is a `str` containing `"."`, split once on `"."` into `(base_app_label, base_name)` via `base.split(".", 1)`. |
| `Base.other` | any base entry that is not a `str`, or a `str` with no `"."` (a class object base, or `models.Model`); contributes no dependency. |
| `bases : List Base` | `model_state.bases` (a tuple), in iteration order. |
| `modelFields : List String` | the keys of `model_state.fields` (the new model's own field names). `f ∈ modelFields` ↔ `f in model_state.fields` (dict membership = key membership), matching `.intersection(model_state.fields)`. |
| `fromLookup ba bn : Option (List String)` | `self.from_state.models.get((base_app_label, base_name))` projected to its `.fields` keys; `none` ↔ `.get(...) is None` (truthiness: a missing/empty state ↦ `none`). `some fs` ↔ the previous-state base's field-name list. |
| `toLookup ba bn : Option (List String)` | `self.to_state.models.get((base_app_label, base_name))` projected to its `.fields` keys; `none` ↔ absent. |
| `primaryKeyRel : Option (String × String)` | `primary_key_rel` truthiness; `some (pa, pn)` ↔ `(primary_key_rel._meta.app_label, primary_key_rel._meta.object_name)`; `none` ↔ falsy `primary_key_rel`. |

### Set vs list (the R leg G-CONF refutes)
`removed_base_fields = set(old.fields).difference(new.fields).intersection(model_state.fields)`
is an **unordered set**; the subsequent `for removed_base_field in removed_base_fields`
appends in unspecified order. The Lean `removedFieldDeps` produces these via a
`List.filter`/`List.map` over `oldFields`, i.e. a concrete order. Because the
specification `problem_spec_createModelDeps` characterises the result by
**membership** (`d ∈ result ↔ …`), order and multiplicity are irrelevant; G-CONF
therefore compares the two legs as **sets of dependency tuples**.

## Callee provenance / flag deps
None. No unchanged repo callee is consumed as an axiom: every operation
(string split, set difference, set intersection, membership) is modeled directly
over Lean `List`/`Option`/`String`. `axiom_check.py` is a skip stub.

## G-CONF fuzz seed
`12754` (pinned; also set in `conformance_check.py` as `SEED = 12754`).
