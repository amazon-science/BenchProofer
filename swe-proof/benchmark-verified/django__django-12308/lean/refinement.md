# refinement.md — django__django-12308

Operation correspondence between `implementation_displayForField` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real behavior by
G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The fix is a pure *dispatch* change: it adds
a branch routing a present, non-empty JSON value through its JSON serializer
(with a fall-back to the generic renderer on a serialization failure). Both leaf
operations — JSON serialization (`field.get_prep_value`) and the generic
renderer (`display_for_value`) — are UNCHANGED. They are modeled as `opaque`
callees that appear IDENTICALLY in `problem_spec` and in the impl, so the proof
consumes no property of either (case analysis only). Every row below is **R**,
**A-reference**, or **I**. The R/I/A-reference legs are differential-tested by
G-CONF; G-AX is a skip stub.

## What the gold patch changes (`django/contrib/admin/utils.py`, `display_for_field`)

Inserts a branch after the `FileField` case:

```python
elif isinstance(field, models.JSONField) and value:
    try:
        return field.get_prep_value(value)
    except TypeError:
        return display_for_value(value, empty_value_display)
```

Pre-patch, a JSON-valued field's value fell through to the final
`else: return display_for_value(value, empty_value_display)`, so a present,
non-empty value (e.g. `{"foo": "bar"}`) was rendered by `str(...)` as
`{'foo': 'bar'}` instead of as JSON `{"foo": "bar"}`.

## `implementation_displayForField` ↔ the patched body

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `value : PyVal`, `empty : String` | the `value` argument and `empty_value_display` argument to `display_for_field`, specialized to `isinstance(field, models.JSONField)` | R | the model is the rendering decision for a JSON-valued field; `PyVal` is the value type bijection (mapping.md) |
| `if isNull value then return empty` | the earlier `elif value is None: return empty_value_display` in the cascade | I | an absent value shows the placeholder (reached before the JSONField branch; both pre- and post-patch) |
| `if truthy value then …` | the `and value` truthiness guard on the new `elif isinstance(field, models.JSONField) and value:` branch | A-reference | present-and-non-empty gates the JSON rendering; Python truthiness ↦ `truthy`; validated by G-CONF |
| `match jsonSerialize value with \| .ok s => return s \| .error _ => return genericDisplay value empty` | `try: return field.get_prep_value(value) except TypeError: return display_for_value(value, empty_value_display)` | A-reference | the EDITED dispatch: JSON text on success, generic rendering on a `TypeError`; `get_prep_value`/`display_for_value` are UNCHANGED callees modeled as `opaque`, validated == real by G-CONF |
| `return genericDisplay value empty` (present-but-empty tail) | the cascade's final `else: return display_for_value(value, empty_value_display)`, reached for a present-but-empty JSON value (the `and value` guard is false) | I | empty value uses the generic renderer, matching pre- and post-patch behavior for that class |

`jsonSerialize` ↦ `field.get_prep_value` (`json.dumps(value, cls=encoder)`),
with `.error ()` modeling the `TypeError` path. `genericDisplay` ↦
`display_for_value`. Neither is axiomatized: they are identical on both sides of
the spec↔impl relation, so the proof needs no contract for them; G-CONF runs the
REAL callees on both legs.

## Independently-observable behaviors (G-DIFF)

One prepatch variant:

- **`Solution_prepatch.lean`** — omits the JSON-rendering branch entirely: a
  present value goes straight to the generic renderer
  (`return genericDisplay value empty`). Fails `correct_displayForField` on the
  present-and-non-empty clause whenever `jsonSerialize value = .ok s` with
  `s ≠ genericDisplay value empty` — i.e. exactly the reported behavior: a
  JSON-representable dict/list/scalar (e.g. `{"foo":"bar"}`) is rendered by the
  generic `str(...)` renderer (`{'foo': 'bar'}`) instead of as JSON
  (`{"foo": "bar"}`). This is the FAIL_TO_PASS behavior
  (`test_json_display_for_field`). The variant keeps the spec view
  byte-identical to `Solution.lean`.

The `error`-fallback sub-behavior (a value `get_prep_value` rejects with a
`TypeError`, e.g. `{('a','b'): 'c'}`) is *not* independently observable from the
prepatch: the prepatch renders such a value with `genericDisplay`, which is
exactly what the spec's `.error` arm demands, so it agrees on that input. It is
covered by G-CONF, which fuzzes both serializer outcomes against the real
callees.
