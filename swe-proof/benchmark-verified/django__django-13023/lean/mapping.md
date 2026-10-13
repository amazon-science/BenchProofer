# mapping.md — django__django-13023

## Symbol binding (file:line @ base_commit f83b44075d)
Modeled function: `DecimalField.to_python(self, value)`,
`django/db/models/fields/__init__.py:1497-1509`. The method interprets an
arbitrary input `value` as a fixed-point decimal number:

```python
def to_python(self, value):
    if value is None:
        return value
    if isinstance(value, float):
        return self.context.create_decimal_from_float(value)
    try:
        return decimal.Decimal(value)
    except decimal.InvalidOperation:        # gold widens to (InvalidOperation, TypeError, ValueError)
        raise exceptions.ValidationError(
            self.error_messages['invalid'], code='invalid', params={'value': value})
```

The gold patch widens the set of low-level failures the conversion's handler
recognizes: previously only one failure mode of `decimal.Decimal(value)` was
turned into a `ValidationError`; the other low-level failure modes escaped the
method uncaught. After the patch every low-level failure of the conversion is
turned into the same single `ValidationError`.

Lean modeled function name: `toPython` (names the *behavior* — interpret a value
as a decimal number; the public `problem_statement` already names
`DecimalField.to_python`, `ValidationError`, and the conversion).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `v : Value` | the `value` argument to `to_python` (`__init__.py:1497`) |
| `v.isNone` | `value is None` (`__init__.py:1498`) |
| `v.isFloat` | `isinstance(value, float)` (`__init__.py:1500`) |
| `v.conv` | the behavior of `decimal.Decimal(value)` (`__init__.py:1503`): `none` ↔ it returns a `Decimal`; `some e` ↔ it raises a low-level exception classified by `e` |
| result | the observable outcome of `to_python`: a normal return (`Outcome.returned`), a raised `ValidationError` (`Outcome.validationError`), or a low-level exception escaping uncaught (`Outcome.propagated`) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `value is None` | `v.isNone = true` |
| `isinstance(value, float)` (and not None) | `v.isFloat = true` |
| `decimal.Decimal(value)` returns a `Decimal` | `v.conv = none` |
| `decimal.Decimal(value)` raises `decimal.InvalidOperation` | `v.conv = some ConvError.notANumber` |
| `decimal.Decimal(value)` raises `TypeError` | `v.conv = some ConvError.unsupportedType` |
| `decimal.Decimal(value)` raises `ValueError` | `v.conv = some ConvError.malformedValue` |
| `to_python` returns (a `Decimal` or `None`) | `Outcome.returned` |
| `to_python` raises `exceptions.ValidationError` | `Outcome.validationError` |
| a low-level exception escapes `to_python` uncaught | `Outcome.propagated` |

### Classification note (the `conv` abstraction)
`decimal.Decimal(value)`, applied to a non-`float` non-`None` value, either
returns a `Decimal` or raises exactly one of three low-level exception types:
`decimal.InvalidOperation` (a number-like value that is not a well-formed decimal
literal — e.g. `'abc'`), `TypeError` (a value whose type cannot be interpreted as
a decimal at all — e.g. `{}`, `set()`, `object()`, `complex()`, `b'...'`), or
`ValueError` (a structured/empty value malformed as a literal — e.g. `()`, `[]`).
G-CONF derives `v.conv` for a real Python value by actually running
`decimal.Decimal(value)` and catching, so the bijection is validated, not
assumed.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** `to_python` calls
  `decimal.Decimal(value)` (the conversion) and `self.context.create_decimal_from_float`
  (the float branch). Neither is changed by the patch and neither has a property
  the proof consumes: the conversion's behavior is modeled *deeply* as the input
  classification `v.conv` (validated against the real `decimal.Decimal` by
  G-CONF), and the float branch is modeled as a normal return (`Outcome.returned`).
  Hence `axioms = []`, `deep_model_references = []` of the consumed kind, and
  `axiom_check.py` is a skip stub (G-AX skips).
- No flag dependency: each branch fires purely on the value's classification
  (`is None`, `isinstance float`, and how the decimal conversion behaves).

## G-LEAK
The solver-visible `problem_statement` publicly names `DecimalField.to_python`,
`ValidationError`, `TypeError`, `dict`, and "a decimal number". The spec view
(`Solution.lean` minus impl+proof) states only the abstract contract: `None`
passes through, a float is converted, otherwise the value is interpreted as a
decimal number, and any low-level failure of that interpretation is reported as a
single uniform validation error. No gold-diff line is reproduced, no diff marker,
no patched file path. The `except` clause's exact exception-type tuple — the
thing the patch edits — appears ONLY in the elided impl region (as the
recognized-failure set), never in the spec view; the `ConvError` constructor
names (`notANumber`/`unsupportedType`/`malformedValue`) describe the *nature* of
each low-level conversion failure, not the edit, and the spec treats all three
identically, so the spec view never reveals which failure modes the fix added.

## Pinned G-CONF fuzz seed
`13023`.
