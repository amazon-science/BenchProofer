# mapping.md — django__django-13212

## Symbol binding (file:line @ base_commit f4e93919e4)
The gold patch makes the built-in validators include the rejected input in the
`ValidationError` they raise, so a custom message can use a `%(value)s`
placeholder. The edit is the SAME at every rejection site across
`django/core/validators.py`: the `raise ValidationError(message, code=…)` gains
`params={'value': value}` (or, where `params` already exists, a `'value': value`
entry is added). Representative sites:

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| modeled function `checkOutcome` (the rejection-context builder) | the common `raise ValidationError(self.message, code=self.code, params={'value': value})` rejection step shared by every validator's `__call__` |
| `RegexValidator.__call__` rejection | `django/core/validators.py:50` |
| `URLValidator.__call__` rejections | `validators.py:103,105,118,135,142` |
| `EmailValidator.__call__` rejections | `validators.py:210,215,228` |
| `validate_ipv4_address` / `validate_ipv6_address` / `validate_ipv46_address` | `validators.py:275,281,290` |
| `DecimalValidator.__call__` rejections (with pre-existing `params={'max': …}`) | `validators.py:441,463,469,475` |
| `FileExtensionValidator.__call__` rejection (with pre-existing `params={'extension':…,'allowed_extensions':…}`) | `validators.py:512` |
| `ProhibitNullCharactersValidator.__call__` rejection | `validators.py:553` |
| `value` (the rejected input) | the `value` argument of each `__call__` / validator function |
| `'value'` substitution key | the literal dict key `'value'` added to `params` |
| pre-existing intrinsic params (`max`, `extension`, `allowed_extensions`) | the `params={…}` already passed at the DecimalValidator / FileExtensionValidator sites |

Lean modeled function name: `checkOutcome` (neutral — names the *behavior* "produce
the validation outcome / error context for one input", not any patched symbol).

### The patched step (uniform across sites)
```python
# pre-patch (e.g. validators.py:50)
raise ValidationError(self.message, code=self.code)
# post-patch
raise ValidationError(self.message, code=self.code, params={'value': value})

# where intrinsic params already exist (e.g. DecimalValidator max_digits, :463)
params={'max': self.max_digits}                       # pre
params={'max': self.max_digits, 'value': value}       # post
```
The acceptance/rejection verdict (`if invalid_input`, `if scheme not in
self.schemes`, `ipaddress.IPv4Address(value)` raising, `digits > max_digits`,
`'\x00' in str(value)`, …) is UNCHANGED by the patch. The only behavioral change
is that a rejection's `ValidationError.params` dict now binds `'value'` to the
rejected input, in addition to whatever intrinsic params that site already
supplied. A `ValidationError(msg, code, params={...})` renders its message by
`msg % params`, so binding `'value'` makes a `%(value)s` placeholder resolve to
the rejected input (the F2P tests set `error_messages={code: '%(value)s'}` and
assert the rendered error equals the submitted value).

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)
| Python | Lean |
|---|---|
| the rejected input `value` (rendered as `str(value)`) | `value : String` |
| the validator's acceptance verdict (`True` = accepted / no raise, `False` = rejected / raises) | `accepted : Bool` |
| the intrinsic `params={...}` dict already supplied at the site (minus any `'value'`) — its ordered entries `list(dict.items())` | `baseParams : List (String × String)` (key→rendered-value pairs in insertion order; `[]` when the site passed no `params`) |
| the validation outcome: no error vs. a raised error carrying a substitution dict | `result : Option (List (String × String))` — `none` = accepted, `some params` = rejected with the substitution map's ordered entries |
| `list(ValidationError.params.items())` (Python dicts are insertion-ordered) | the association list `params` itself, entry for entry, in order |
| `ValidationError.params['value']` | `params.lookup "value"` (a corollary of the pinned sequence) |
| `ValidationError.params[k]` for an intrinsic key `k` | `params.lookup k` (a corollary of the pinned sequence) |

### Modeling notes
- `value` is modeled as a `String`: the message interpolation observes only the
  rendered form `%(value)s == str(value)` (the F2P tests assert
  `form.errors == {'field': [str(value)]}`). The IntegerField/DecimalField cases
  feed `str(value)`, the CharField cases feed the string itself; all reduce to a
  string content the placeholder must reproduce.
- The verdict is an INPUT (`accepted`), not a callee axiom: the patch does not
  touch how validity is decided, so modeling the decision is out of scope and
  would be a dead axiom. The spec ranges over BOTH verdicts (accept ⇒ no error;
  reject ⇒ error context with the `value` binding).
- `baseParams` carries the site-intrinsic params (DecimalValidator's `max`,
  FileExtensionValidator's `extension`/`allowed_extensions`). The theorem
  precondition `baseParams.lookup "value" = none` reflects that no built-in
  site already binds `'value'` itself — the patch is the sole source of that
  key.
- The association list is the ORDERED ENTRY SEQUENCE of the params dict, not
  merely a lookup table: Python dicts preserve insertion order, and every
  patched site constructs the dict with its intrinsic entries first and
  `'value': value` last (`params={'max': ..., 'value': value}`,
  `params={'extension': ..., 'allowed_extensions': ..., 'value': value}`, or
  just `params={'value': value}`). The spec therefore pins the rejection result
  to EXACTLY `baseParams ++ [("value", value)]` — the unique list corresponding
  to the patched dict under `list(dict.items())`. This leaves no
  lookup-unreachable freedom (no duplicate/shadowed entries, no reordering),
  closing the list-vs-dict artifact a lookup-only spec admits.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom, and there is no A-reference
  callee: the changed operation (attaching `'value'` to the error params) is a
  pure data construction over the inputs, modeled DEEPLY as `baseParams ++
  [(valueKey, value)]`. The validity decision is carried as the `accepted` input.
- No flag dependency: every rejection site gains the `'value'` binding
  unconditionally; the only variation is which intrinsic params pre-exist
  (modeled by `baseParams`).
- `axiom_check.py` is a skip stub (`status=skip`): the bundle consumes no callee
  axiom (`meta.json axioms = []`, `deep_model_references = []`).

## Pinned G-CONF fuzz seed
`13212`.
