# refinement.md — django__django-11400

Operation correspondence between the `implementation_*` skeletons and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by G-AX),
**I** (identical concrete op).

No axioms are declared or consumed. The single `opaque applyOrdering` is an
**I-tagged** op (`QuerySet.order_by`): the impl/proof only ECHO its result and
never assert a property of it. Every row below is **R** or **I**. The R/I legs
are differential-tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## Behavior 1 — `implementation_orderedChoices` ↔ patched `get_choices`

Gold (forward, `fields/__init__.py`; the reverse `reverse_related.py` hunk is
identical in structure on `self.related_model._default_manager`):

```python
qs = rel_model._default_manager.complex_filter(limit_choices_to)   # default order
if ordering:
    qs = qs.order_by(*ordering)                                    # re-sequence
return (blank_choice if include_blank else []) + [(choice_func(x), str(x)) for x in qs]
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut qs := objs` | `qs = rel_model._default_manager.complex_filter(limit_choices_to)` (the collection in default `Meta.ordering` order) | R | the related queryset materialized in default presentation order ↦ `objs : List Obj`. (`complex_filter`/`limit_choices_to` is the unchanged restriction; on the unrestricted path it is `.all()`. The restriction is modeled at the Behavior-2 layer / G-CONF, not re-sorted here.) |
| `if ordering ≠ []` | `if ordering:` | R | Python truthiness of an ordering tuple ↦ `ordering ≠ []` (`List String`). Empty tuple ↦ `[]`. This guard IS the fix. |
| `qs := applyOrdering ordering objs` | `qs = qs.order_by(*ordering)` | I | `order_by(*ordering)` on the default-order queryset ↦ `applyOrdering ordering objs`. Opaque/echoed; the real `order_by` is run by G-CONF. |
| `(if includeBlank then blank else [])` | `(blank_choice if include_blank else [])` | R | `BLANK_CHOICE_DASH` ↦ `blank : List (Int × String)`; Boolean bijection on `include_blank`. |
| `++ qs.map toChoice` | `+ [(choice_func(x), str(x)) for x in qs]` | R | the comprehension ↦ `List.map toChoice`; `choice_func(x)`/`x.pk` ↦ `o.pk`, `str(x)` ↦ `o.label`. |
| `return …` | the `return` of the concatenated list | I | result assembly. |

The key soundness point: the spec's empty-directive result is `objs.map toChoice`
(the DEFAULT-order carrier), **not** `(applyOrdering [] objs).map toChoice`. This
is exactly the corrected behavior (`order_by()` with empty args must NOT run,
because it would clear the default order). A wrong impl that calls
`applyOrdering` unconditionally cannot satisfy the spec (see prepatch_1).

## Behavior 2 — `implementation_restrictedChoices` ↔ patched `RelatedOnlyFieldListFilter`

Gold (`filters.py`): `ordering = self.field_admin_ordering(field, request,
model_admin)` then `field.get_choices(include_blank=False,
limit_choices_to={'pk__in': pk_qs}, ordering=ordering)`.

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let ordering := configuredOrdering adminOrdering` | `ordering = self.field_admin_ordering(...)` (admin/Meta ordering, else `()`) | R | `field_admin_ordering`'s result ↦ `configuredOrdering (adminOrdering : Option (List String))` = `adminOrdering.getD []`. Pre-patch this was implicitly `()` (kwarg omitted). |
| `return implementation_orderedChoices false [] ordering objs` | `field.get_choices(include_blank=False, limit_choices_to=…, ordering=ordering)` | I (callee-under-spec) | the SAME `get_choices` of Behavior 1, called with `include_blank=False` and the forwarded directive. Proved via `correct_orderedChoices`, not assumed. The `objs` here are the restricted (`pk__in`) collection in default order; the `limit_choices_to` restriction is the unchanged input carrier (G-CONF supplies the real restricted queryset). |

## Independently-observable behaviors (G-DIFF)

- **`Solution_prepatch_1.lean`** (Behavior 1 bug): the re-sequencing primitive is
  applied UNCONDITIONALLY (`qs := applyOrdering ordering objs`, no guard). The
  carried gold proof of `correct_orderedChoices` fails to close on the
  `ordering = []` case (residual goal `applyOrdering [] objs = objs` is
  unprovable — `applyOrdering` is opaque). This is the real bug: an empty
  directive clears the default order.
  (FAIL_TO_PASS: `test_get_choices_default_ordering`,
  `test_get_choices_reverse_related_field_default_ordering`,
  `test_relatedfieldlistfilter_*_default_ordering`.)
- **`Solution_prepatch_2.lean`** (Behavior 2 bug): the restricted listing discards
  the configured directive (`implementation_orderedChoices false [] [] objs` —
  always the empty directive), mirroring the pre-patch omitted `ordering` kwarg.
  The carried gold proof of `correct_restrictedChoices` fails (the implementation
  uses `[]` where the spec demands `configuredOrdering adminOrdering`).
  (FAIL_TO_PASS: `test_relatedonlyfieldlistfilter_foreignkey_ordering`,
  `test_relatedonlyfieldlistfilter_foreignkey_default_ordering`.)
