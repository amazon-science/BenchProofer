# mapping.md — django__django-12308

## Symbol binding (file:line @ base_commit 2e0f04507b17362239ba49830d26fec504d46978)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_displayForField` / `problem_spec_displayForField` / `correct_displayForField` | the value-rendering decision in `display_for_field` for a JSON-valued field: which textual rendering is selected for the field's value | `django/contrib/admin/utils.py:380-405` @ base_commit (the chain of `isinstance`/value tests; the gold patch adds the `models.JSONField` branch at 399-403 post-patch) |
| `jsonSerialize value` | `field.get_prep_value(value)` — `json.dumps(value, cls=self.encoder)`; raises `TypeError` for a value not representable as JSON | `django/db/models/fields/json.py:83-85` (UNCHANGED callee; reached only on the JSONField + truthy branch) |
| `genericDisplay value empty` | `display_for_value(value, empty_value_display)` | `django/contrib/admin/utils.py:407-423` (UNCHANGED callee; the generic fall-through renderer) |

## What the gold patch changes

`display_for_field(value, field, empty_value_display)` is a cascade of
`isinstance(field, …)`/value tests selecting how to render `value`. Pre-patch,
a `JSONField` value fell through to the final `else: return
display_for_value(value, empty_value_display)`, which renders a dict/list via
`str(...)` — e.g. `{"foo": "bar"}` displayed as `{'foo': 'bar'}` (not valid
JSON). The gold patch inserts, immediately after the `FileField` branch:

```python
elif isinstance(field, models.JSONField) and value:
    try:
        return field.get_prep_value(value)
    except TypeError:
        return display_for_value(value, empty_value_display)
```

The modeled function is the rendering decision *as specialized to a JSON-valued
field* (the `isinstance(field, models.JSONField)` test is the precondition that
selects this model; it is not itself an input). The earlier `value is None`
test in the cascade is modeled by `isNull`; the `and value` truthiness guard on
the new branch is modeled by `truthy`.

## Modeled inputs

| Lean | Python reality | meaning |
|---|---|---|
| `value : PyVal` | the field's stored value passed to `display_for_field` | the JSON value to render; `PyVal` carries the presence/emptiness structure and can represent values `json.dumps` rejects (e.g. a dict keyed by a tuple) |
| `empty : String` | `empty_value_display` | placeholder text shown for an absent value |

## Output

| Lean | Python |
|---|---|
| `result : String` | the string `display_for_field` returns for a JSON-valued field |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `None` | `PyVal.null` | identity |
| `bool` | `PyVal.bool` | identity |
| `int` | `PyVal.int` | identity |
| `str` | `PyVal.str` | identity |
| `list` | `PyVal.list` | element-wise |
| `tuple` | `PyVal.tuple` | element-wise |
| `dict` | `PyVal.dict` | key/value pairs, order-preserving |
| `value is None` | `isNull value = true` | identity |
| Python truthiness `bool(value)` | `truthy value = true` | `None`/`False`/`0`/`""`/empty container ↦ false; else true |
| `field.get_prep_value(value)` (= `json.dumps(value)`), `TypeError` ↦ failure | `jsonSerialize value : Except Unit String` | `.ok s` ↦ the JSON text; `.error ()` ↦ `TypeError` raised |
| `display_for_value(value, empty_value_display)` | `genericDisplay value empty : String` | identity (same string) |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The two operations the modeled branch invokes —
  `field.get_prep_value` (JSON serialization) and `display_for_value` (generic
  rendering) — are UNCHANGED by the patch. The proof consumes NO property of
  them: they appear identically in `problem_spec` and in the impl, so the proof
  is pure case analysis on `isNull`/`truthy`/the serialization result. They are
  declared `opaque` only so they can appear in the executable impl. Their real
  behavior is exercised on both sides of the differential by G-CONF
  (A-reference). `axiom_check.py` is a skip stub.
- **No flag dependency.** The selection depends only on `isNull value` and
  `truthy value`. (`isinstance(field, models.JSONField)` is the model's
  precondition, fixed, not a runtime input.)
- **Emptiness convention.** `truthy` reproduces Python truthiness for the value
  classes a JSON field can hold; the `and value` guard on the new branch routes
  a present-but-empty value (`{}`, `[]`, `""`, `0`, `False`) through the generic
  renderer, exactly as the cascade's final `else` does.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py`).
