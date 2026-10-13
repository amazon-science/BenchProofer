# mapping.md — django__django-13212

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f4e93919e4608cfc50849a1f764fd856e0917401`, states the type
abstraction, and records callee provenance. There are no consumed axioms (the
behaviour is modelled deeply); §3 records the one stdlib mechanism the model
relies on and how `axiom_check.py` (G-AX) validates the deep model against it.

Repo files under change:
  * `django/core/validators.py` — the validator raise sites (the param map each
    rejection produces).
  * `django/forms/fields.py` — `DecimalField.validate` (a duplicate, paramless
    not-finite check removed so the param-carrying validator handles it).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_invalid_params(value)` | the `params=...` argument constructed at every bare-rejection `raise ValidationError(self.message, code=self.code)` site in `django/core/validators.py` (lines 51, 103, 107, 118, 135, 142, 211, 216, 228, 553) plus the `code='invalid'` raises in `validate_ipv4_address`/`validate_ipv6_address`/`validate_ipv46_address` (lines 275, 280, 290) and the `DecimalValidator` not-finite raise (line 441) | the modeled changed behaviour: the parameter mapping a bare rejection produces (the fix adds `params={'value': value}`) |
| `build_limit_params(value, limit)` | the `params=...` argument constructed at the three `DecimalValidator.__call__` magnitude raises in `django/core/validators.py:460-477` (`max_digits` / `max_decimal_places` / `max_whole_digits`), and structurally the `FileExtensionValidator` raise (line 507, which likewise adds `'value': value` to a params dict that already carries other bindings) | the modeled changed behaviour: the parameter mapping a bound-limit rejection produces (the fix adds `'value': value` to a params dict that already binds another placeholder, e.g. `{'max': ...}`) |
| `decimal_reject_params(finite, value)` | `DecimalField.validate` (`django/forms/fields.py:350-358`, **removed** by the patch) together with `DecimalValidator.__call__`'s `exponent in {'F','n','N'}` bare rejection (`django/core/validators.py:440-441`) | the modeled changed behaviour: removing the duplicate not-finite screen so a not-finite decimal candidate is no longer short-circuited with a paramless error but flows to the value-binding bare rejection (the produced map binds `'value'` regardless of finiteness) |
| `placeholder_value()` | the `'value'` key of the params dict / the `%(value)s` named placeholder in a template | pure spec: the name token of the value placeholder |
| `placeholder_limit()` | the `'max'` key of the params dict (DecimalValidator's `max_*` messages, e.g. `'Ensure that there are no more than %(max)s digit(s)…'`) | pure spec: the name token of the numeric-limit placeholder |
| `finite` (parameter of `decimal_reject_params`) | the `value.is_finite()` predicate the deleted screen tested (`fields.py:357`) | carrier: whether the rejected decimal candidate is representable (`True`) or a not-a-number/unbounded magnitude (`False`) |

The rendering mechanism the model abstracts (unchanged by the patch, §3):
`ValidationError.__iter__` does `message %= error.params` for each error
(`django/core/exceptions.py:166-175`), and `Field.run_validators` overrides
`e.message` with the user template keyed by `e.code` while **preserving
`e.params`** (`django/forms/fields.py:130-142`). So a custom `'%(value)s'`
template renders to `str(params['value'])` exactly when `'value'` is in
`params`.

The removed control-flow site (now modelled by `decimal_reject_params`):
`DecimalField.validate` (`django/forms/fields.py:350-358`) — a not-finite check
that raised `ValidationError(self.error_messages['invalid'], code='invalid')`
with **no params**. Removing it lets the not-finite/NaN `Decimal` flow through to
`DecimalValidator.__call__`'s `if exponent in {'F','n','N'}` branch
(`validators.py:440-441`), which the patch updates to a bare rejection carrying
`params={'value': value}`. `decimal_reject_params` carries the routing decision
on the `finite` flag and delegates the produced map to `build_invalid_params`
(site A) — the control-flow change is modelled deeply, not behind an axiom.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the offending input `value` (a `str` for the char-field cases; `str(value)` for the rendered form generally) | `List[int]` of Unicode code points | `value[k]` ↔ `ord(real_value[k])`; `len` ↔ `len`; the *rendered* string of the value is `str(value)`, which for a `str` input is the input itself, modelled as the identity on code points |
| the numeric limit `self.max_digits` / `self.decimal_places` / `self.max_digits - self.decimal_places` (the `'max'` param) | `List[int]` of code points of its string form | the param value renders via `%(max)s` to `str(limit)`; modelled as the code-point list of that string form (identity) |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq` |
| the params `dict` passed to `ValidationError` | `Dict[int, PSeq[int]]` from a placeholder-name token to the string that placeholder renders to | a key `'value'`/`'max'` ↔ token `placeholder_value()`/`placeholder_limit()`; `k in params` ↔ token in dict; `params[k]` (the rendered string) ↔ dict value |
| `value.is_finite()` (the predicate the deleted `DecimalField.validate` screen tested) | the `finite: bool` parameter of `decimal_reject_params` | `True` ↔ a representable candidate; `False` ↔ a not-a-number / unbounded magnitude (the case the duplicate screen intercepted) — a `Decimal` is otherwise inexpressible in Nagini, so only the finiteness bit the branch reads is carried |

The `%`-interpolation `message %= params` for a template that is exactly one
named placeholder is, semantically, the dict lookup of that placeholder's name
(raising `KeyError` if absent). The model carries `params[name_token]` as the
rendered string of that placeholder, so membership models renderability and the
dict value models the rendered text. `str` indexing/iteration is banned in
Nagini, so the carrier is `List[int]`; the spec is phrased over `PSeq[int]` via
`ToSeq`.

## 3. The rendering mechanism (deep-modelled; G-AX A-reference)

There is **no consumed `@ContractOnly` axiom** — the changed behaviour (which
keys the rejection's param map binds) is spelled out in the impl region. The
one *unchanged* mechanism the model leans on is Python's `%`-style named
interpolation of `ValidationError.__iter__` (`message %= error.params`): for a
template that is exactly `'%(NAME)s'`, the rendered output is
`str(params['NAME'])` when `'NAME' in params`, and a `KeyError` otherwise.

`axiom_check.py` (G-AX) validates this deep model against the real mechanism by
running the actual Django stack in-container:
  * It constructs the real `ValidationError(msg, code=code, params=p)` and the
    real form/field path (`MyForm({'field': value}); form.is_valid();
    form.errors`), with a custom `error_messages={code: '%(value)s'}` template,
    and asserts the rendered error text equals `str(value)` for every bare
    rejection (`build_invalid_params` reference) and that the `%(max)s`
    placeholder still renders for the bound-limit rejections
    (`build_limit_params` reference).
  * It asserts the converse: with the pre-patch param maps (no `'value'`), the
    `'%(value)s'` template does NOT render to `str(value)` (it raises / leaves
    the placeholder), confirming the binding is load-bearing.

This uses only Django + the standard library (the very stack the patch lives
in); nothing is faked. Provenance:
`django/core/exceptions.py:166-175` (`__iter__`, `message %= error.params`),
`django/forms/fields.py:130-142` (`run_validators` preserves `e.params`),
Django docs "Writing validators"
(https://docs.djangoproject.com/en/3.0/ref/validators/#writing-validators) —
the `%(value)s` placeholder shown there is the public behaviour this fix
enables.
