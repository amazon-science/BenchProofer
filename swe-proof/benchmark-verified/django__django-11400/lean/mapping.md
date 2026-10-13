# mapping.md — django__django-11400

## Symbol binding (file:line @ base_commit 1f8382d34d)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_orderedChoices` / `problem_spec_orderedChoices` / `correct_orderedChoices` | producing the `[(pk, str(obj)), …]` choice list of a related collection, applying an explicit ordering directive only when it is non-empty (else preserving the default `Meta.ordering`) | `django/db/models/fields/__init__.py:809-831` (`Field.get_choices`) AND `django/db/models/fields/reverse_related.py:117-127` (`ForeignObjectRel.get_choices`) @ base_commit |
| `implementation_restrictedChoices` / `problem_spec_restrictedChoices` / `correct_restrictedChoices` | the restricted listing forwarding the configured admin/Meta ordering into `get_choices` (rather than discarding it) | `django/contrib/admin/filters.py:419-422` (`RelatedOnlyFieldListFilter.field_choices`), using the gold helper `field_admin_ordering` (`filters.py:196-201` post-patch) |
| `applyOrdering : List String → List Obj → List Obj` | `QuerySet.order_by(*ordering)` — the record re-sequencing primitive | `django/db/models/query.py` (`order_by`); UNCHANGED callee |
| `Obj` | a related-model instance (only `.pk` and `str(obj)` are read on this path) | `InputArgument`/model instance; the choice carrier `(x.pk, str(x))` |
| `configuredOrdering` | `field_admin_ordering(...)` = `related_admin.get_ordering(request)` if a related admin is registered, else `()` | `filters.py:196-201` (post-patch) |

## The modeled behaviors

### Behavior 1 — `get_choices` conditional ordering (forward + reverse)

Pre-patch (forward, `fields/__init__.py:828-831`):

```python
return (blank_choice if include_blank else []) + [
    (choice_func(x), str(x))
    for x in rel_model._default_manager.complex_filter(limit_choices_to).order_by(*ordering)
]
```

Post-patch:

```python
qs = rel_model._default_manager.complex_filter(limit_choices_to)
if ordering:
    qs = qs.order_by(*ordering)
return (blank_choice if include_blank else []) + [(choice_func(x), str(x)) for x in qs]
```

The reverse analog (`reverse_related.py:117-127`) makes the IDENTICAL change on
`self.related_model._default_manager`. The defect: `order_by()` with NO arguments
*clears* any default ordering, so a model with `Meta.ordering` lost it whenever
the filter supplied an empty directive. The fix guards the `order_by` call on a
non-empty `ordering`. Both sites are the SAME behavior, so they share one triple
(`orderedChoices`); the `choice_func(x)` (forward) vs `x.pk` (reverse) difference
is the unchanged key-extraction and is abstracted to `Obj.pk` (`toChoice`).

### Behavior 2 — `RelatedOnlyFieldListFilter` forwards the ordering

Pre-patch (`filters.py:420-422`): `field.get_choices(include_blank=False,
limit_choices_to={'pk__in': pk_qs})` — the `ordering` kwarg is OMITTED, so the
restricted listing was unordered. The fix introduces `field_admin_ordering` (a
behavior-neutral extraction of the ordering-selection logic already present in
`RelatedFieldListFilter.field_choices`) and forwards its result:
`get_choices(..., ordering=self.field_admin_ordering(...))`. This is layered on
Behavior 1 (it calls the same `get_choices`), so `implementation_restrictedChoices`
calls `implementation_orderedChoices` directly (callee-under-spec) and
`correct_restrictedChoices` is proved via `correct_orderedChoices` — proved, not
assumed.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `ordering` (tuple of field-name strings, possibly empty) | `ordering : List String` | `tuple(...)` ↦ `List String`; `()` ↦ `[]` |
| the related queryset in default `Meta.ordering` order (`ordering=()` ⇒ no `order_by`) | `objs : List Obj` (the carrier in default presentation order) | the materialized default-order list ↦ `objs` |
| `qs.order_by(*ordering)` for non-empty `ordering` | `applyOrdering ordering objs` | the real `order_by` result ↦ `applyOrdering`'s value (opaque/I-tagged: only consulted) |
| `(choice_func(x), str(x))` / `(x.pk, str(x))` | `toChoice o = (o.pk, o.label)` | key-extraction ↦ `o.pk`; `str(x)` ↦ `o.label` |
| `blank_choice if include_blank else []` | `if includeBlank then blank else []` | Boolean bijection on `include_blank`; `BLANK_CHOICE_DASH` ↦ `blank` |
| `field_admin_ordering(...)` (admin/Meta ordering or `()`) | `configuredOrdering (adminOrdering : Option (List String))` | a registered admin's ordering ↦ `some xs`; no related admin ↦ `none` (⇒ `[]`) |

## Callee provenance + flag dependencies

- **No callee axiom is consumed.** `applyOrdering` (`QuerySet.order_by`) is an
  UNCHANGED callee declared `opaque` so it can appear in the executable impl. The
  proofs only ECHO its result in the non-empty-directive branch; they assert NO
  property of it (§0.7 — it is an I-tagged op, not an A-consumed axiom). The
  empty-directive branch never calls it. G-AX is therefore a skip stub; the real
  `order_by` is exercised end-to-end by G-CONF.
- **`order_by()` (empty args) clears default ordering** is the bug's mechanism;
  the spec captures it structurally by making the empty-directive result equal to
  the default-order carrier `objs` (NOT `applyOrdering [] objs`). The spec NEVER
  constrains `applyOrdering []`, so a wrong impl cannot discharge the
  empty-directive case by routing through the primitive.
- Flag dependency: Behavior 2's `field_admin_ordering` returns a non-empty
  directive only when a related `ModelAdmin` is registered with an `ordering`, or
  the related model has `Meta.ordering`. G-CONF fuzzes both `adminOrdering = None`
  (⇒ `[]`) and several concrete directives, against a related model that DOES
  carry `Meta.ordering` (so default order ≠ insertion order ≠ key order — every
  dropped/garbled ordering is observable).

## G-CONF fuzz seed

`SEED = 20240629` (pinned in `conformance_check.py`).
