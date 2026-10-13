# mapping.md — django__django-13212

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f4e93919e4608cfc50849a1f764fd856e0917401`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one free-input callee.

Repo files under change:
* `django/core/validators.py` — twelve failure sites across nine validators.
* `django/forms/fields.py` — removal of a redundant value-less failure path.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateValue (value …) (isValid : Bool) …` | the common shape of every validator failure site: `if <check fails>: raise ValidationError(msg, code=code, params={…})` — see §1.1 for the twelve concrete sites | the modeled changed behaviour: error **construction** on the failure branch |
| `isValid : Bool` *(free input — not an axiom)* | the per-site validity test (`self.regex.search(...)`, `ipaddress.IPv4Address(...)`, `'@' in value`, `exponent in {'F','n','N'}`, `extension in self.allowed_extensions`, `'\x00' in str(value)`, …) | the **unchanged** check; abstracted as a free Bool (strictly weaker than any concrete test — directive 7) |
| `VErr` (`code`, `params`) | the constructed `django.core.exceptions.ValidationError` — its `code` and `params` fields (`django/core/exceptions.py:99`, fields set at `:139-141`) | the touched fields of the raised error object (§2) |
| `buildError` *(deep model)* | the changed `ValidationError(message, code=…, params={… , 'value': value})` constructor call (the post-patch RHS at every site) | pure spec: the error built on the failure branch, now carrying `'value'` |
| `lookupKey "value"` | `message %= error.params` in `ValidationError.__iter__` (`exceptions.py:174`) projecting the `%(value)s` placeholder | pure spec: the (unchanged) rendering's lookup of the `value` key |

### 1.1 The twelve `validators.py` failure sites (all the same shape)

Each adds `params={'value': value}` (or appends `'value': value` to an existing
`params` dict) to a `ValidationError(...)` raised on a validity-failure branch:

| validator (`django/core/validators.py`) | line(s) @ base | pre-existing params |
|---|---|---|
| `RegexValidator.__call__` | 51 | — |
| `URLValidator.__call__` (not-a-str) | 103 | — |
| `URLValidator.__call__` (bad scheme) | 107 | — |
| `URLValidator.__call__` (urlsplit ValueError) | 118 | — |
| `URLValidator.__call__` (bad IPv6 netloc) | 135 | — |
| `URLValidator.__call__` (netloc > 253) | 142 | — |
| `EmailValidator.__call__` (empty / no `@`) | 211 | — |
| `EmailValidator.__call__` (bad user part) | 216 | — |
| `EmailValidator.__call__` (bad domain part) | 228 | — |
| `validate_ipv4_address` | 275 | — |
| `validate_ipv6_address` | 280 | — |
| `validate_ipv46_address` | 290 | — |
| `DecimalValidator.__call__` (non-finite) | 441 | — (also gains `code='invalid'`) |
| `DecimalValidator.__call__` (max_digits) | 460-463 | `{'max': …}` |
| `DecimalValidator.__call__` (max_decimal_places) | 465-469 | `{'max': …}` |
| `DecimalValidator.__call__` (max_whole_digits) | 471-476 | `{'max': …}` |
| `FileExtensionValidator.__call__` | 507-514 | `{'extension': …, 'allowed_extensions': …}` |
| `ProhibitNullCharactersValidator.__call__` | 553 | — |

`BaseValidator.__call__` (line 341) already carries `'value'` at base_commit and
is **not** modeled (not part of this fix). The non-finite `DecimalValidator`
site additionally gains `code='invalid'` — captured by the modeled `code` field.

### 1.2 The `forms/fields.py` removal

`DecimalField.validate` (deleted, `django/forms/fields.py:353-358` @ base) was a
redundant value-less `ValidationError(..., code='invalid')` for non-finite
decimals. Its removal lets `DecimalValidator.__call__`'s value-carrying
`invalid` error surface instead. Under the model this is the removal of a
value-less duplicate of the same failure branch — it carries no new modeled op;
it only ensures the modeled value-carrying path (`buildError`) is the one
observed (refinement.md §B).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the validator argument `value` (whatever its Python type) as the placeholder renders it, `str(value)` | `List Char` | `str(value)` ↔ `value.toList`-shaped `List Char`. The `%(value)s` placeholder stringifies via `str(...)`; the F2P tests assert `form.errors == {'field': [str(value)]}`. |
| the validity test result (`not regex_matches`, `IPv4Address` raised, etc.) | `isValid : Bool` (`true` = passes, `false` = the branch that raises) | per-site Boolean; unchanged by the patch, so a free input. |
| `ValidationError.code` (a short ASCII slug) | `code : List Char` | identity on characters. |
| `ValidationError.params` dict `{k: v}` of placeholder bindings | `params : List (String × List Char)` (key ↦ its `str`-rendered binding) | Python dict ↔ assoc list; insertion order preserved (Python 3.7 dicts are ordered); `'value'` appended last. The test only renders the `value` key. |
| `message %= params` rendering of a `%(value)s` template | `lookupKey "value" params` | extracting the `value` binding from the params dict — the unchanged `ValidationError.__iter__` rendering. |

The pre-existing params at the `DecimalValidator`/`FileExtensionValidator` sites
(`'max'`, `'extension'`, `'allowed_extensions'`) are modeled as the free
`oldParams` list, none of whose keys is `"value"` (the `require`); the patch
**appends** `('value', value)`, preserving them.

## 3. Callee provenance — the free input (no consumed axiom)

There is **no module-level `axiom`** in this bundle and **no deep-model
reference** to a stdlib callee. The only unchanged callee — the per-site
validity test — is modeled as the free Boolean `isValid`: the postconditions
hold for **every** value of it, so it is owed no contract (directive 7; the
django-16667 `ConstructOutcome`/`f` precedent). The CHANGED behaviour (the error
constructed on the failure branch) is modeled **deeply** by `buildError` in the
`pure` region.

Because the impl region contains no A-tagged op (only R/I ops over a free Bool),
there are no axioms or deep-model references for G-AX to check, so the bundle
ships **no `axiom_check.py`** and G-AX is `skip` by design (the django-16667
no-axiom precedent). G-CONF fuzzes the R/I error-construction shadow against the
real patched validators (`conformance_check.py`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13212`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`buildError`/`validateOutcome` (the failure-branch error construction) to Python
and drives the **real** patched validators (`RegexValidator`, `validate_email`,
`validate_ipv4_address`, `DecimalValidator`, `FileExtensionValidator`,
`ProhibitNullCharactersValidator`, …) at base_commit+gold, asserting that on
every failing input the real `ValidationError.params['value']` equals the
modeled `value` (and on passing input no error is raised).
