# mapping.md — django__django-13933

## Symbol binding (file:line @ base_commit 42e8cf47c7)
Modeled function: the value-coercion routine of the single-choice field backed by
a record set, `ModelChoiceField.to_python`, `django/forms/models.py:1278-1288`
(@ base). The gold patch rewrites the `except` arm (line 1287 pre-patch): the
`ValidationError` raised on a failed resolution gains `params={'value': value}`
so the configured `invalid_choice` message template can interpolate the offending
submission.

Lean modeled function name: `coerceChoice` (deliberately neutral — it names the
*behavior* "coerce a submitted value into one of the available choices", not the
patched symbol; see G-LEAK note below).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `coerceChoice` (modeled coercion) | `ModelChoiceField.to_python`, `models.py:1278-1288` |
| `emptyValues` | `self.empty_values` — the recognised "no answer" sentinels, `models.py:1279` (`if value in self.empty_values: return None`) |
| `value` | the submitted value argument `value`, `models.py:1278` |
| `lookup` | the observable outcome of the resolution `self.queryset.get(**{key: value})` (after the optional `getattr(value, key)` model-instance unwrap): `some r` when it returns a stored object (identity `r`), `none` when it raises `ValueError`/`TypeError`/`DoesNotExist`, `models.py:1281-1286` |
| `invalidMessage` | `self.error_messages['invalid_choice']` — the rejection message template, `models.py:1287` |
| `invalidChoiceCode` | the literal `code='invalid_choice'`, `models.py:1287` |
| `valueParamName` | the placeholder name `'value'` in `params={'value': value}` (post-patch `models.py:1287-1291`) |
| result | the return / raise outcome: `Except.ok none` (sentinel), `Except.ok (some r)` (resolved), or `Except.error {…}` (the raised `ValidationError`) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| submitted `value` (raw text) | `value : Val := String` |
| `self.empty_values` (list of sentinels) | `emptyValues : List Val` |
| resolution outcome of `queryset.get(...)`: object vs raised | `lookup : Option Resolved` (`some pk` / `none`) |
| `self.error_messages['invalid_choice']` (str template) | `invalidMessage : String` |
| `return None` | `Except.ok none` |
| `return value` (the resolved object, identity its pk) | `Except.ok (some r)` |
| `raise ValidationError(msg, code='invalid_choice', params={'value': value})` | `Except.error { messageTemplate := msg, code := "invalid_choice", params := [("value", value)] }` |
| `ValidationError.params` (dict `{name: bound_value}`) | `ChoiceError.params : List (String × Val)` (association list) |

### Resolution-outcome modeling note
`queryset.get(**{key: value})` is an UNCHANGED dependency: the patch does not
touch it. Its only observable used by the modeled behavior is the two-way
outcome — it returns the matching stored object, or it raises one of
`(ValueError, TypeError, DoesNotExist)`. We expose that outcome as the plain
`lookup : Option Resolved` datum (`some` / `none`); the identity of a resolved
object is its pk (`Resolved := Nat`). The optional `getattr(value, key)`
model-instance unwrap (`models.py:1283-1284`) is part of producing that outcome
and is folded into `lookup` as well. The modeled operation is purely the
assembly of the three-way result and, on the rejection branch, the parameter
binding — modeled deeply over the data, not axiomatized.

### params association-list note
`ValidationError.params` is a Python `dict`. The patch sets it to the singleton
`{'value': value}`. Message interpolation is membership-keyed (`%(value)s` looks
up key `'value'`), so the dict is modeled as a single-entry association list
`[("value", value)]`. G-CONF compares the parameter binding as a `dict`, so the
list↔dict bijection is exact for this singleton.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `queryset.get`, `getattr`, and
  `self.empty_values` enter as DATA: their observable outcomes are supplied as
  the `lookup` and `emptyValues` inputs. The result assembly (the three branches
  and the `params={'value': value}` binding) is modeled deeply as an
  `Except`-valued `Id.run do`, an R/I op, not an axiom.
- No flag dependency: the rejection branch is unconditional once the resolution
  has failed and the submission is not a sentinel.

## G-LEAK
The problem_statement names `ModelChoiceField`, `ChoiceField`,
`ModelMultipleChoiceField`, `ValidationError`, `invalid_choice`, `value`, and
`%(value)s` (it quotes the source). The spec view nonetheless avoids the patched
symbol: the modeled-function identifier `coerceChoice` shares no patched
def/class name (the patch touches only `to_python`; `coerceChoice` does not embed
`to_python`). The spec view describes behavior ("coerce a submitted value", "the
rejection report carries the offending value") and never narrates the edit.
`invalidChoiceCode = "invalid_choice"` and `valueParamName = "value"` are literal
behavioral constants that the problem_statement itself exhibits, not edit
narration.

## Pinned G-CONF fuzz seed
`13933`.
