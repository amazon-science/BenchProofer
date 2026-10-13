# refinement.md — django__django-13212

The operation-by-operation correspondence between `model.py`'s implementation
(the three contracted functions `build_invalid_params`, `build_limit_params`,
and `decimal_reject_params`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`Ensures`, **A-reference** where a deep model is validated == a real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. Bare-rejection param map — `build_invalid_params(value)`

Representative gold hunk (`django/core/validators.py:51`, identical shape at the
other bare-rejection sites 103/107/118/135/142/211/216/228/275/280/290/441/553):
```
- raise ValidationError(self.message, code=self.code)
+ raise ValidationError(self.message, code=self.code, params={'value': value})
```

| # | model.py impl op (`build_invalid_params`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: List[int]` | the `value` argument of the validator `__call__` (or the module-level `validate_ipv*` function) | R | `str` ↔ `List[int]` code points; the value's rendered form is `str(value)`, the identity on code points for the `str` inputs the F2P tests pass (mapping.md §2). |
| A2 | `params = {}` then `params[placeholder_value()] = ToSeq(value)` | the dict literal `params={'value': value}` | R + I | building a one-entry mapping; the key `'value'` ↔ token `placeholder_value()` (R, mapping.md §1), the entry value `value` ↔ `ToSeq(value)` (R), the construction itself identical (I). |
| A3 | `return params` (a fresh `Dict[int, PSeq[int]]`) | the `params=` keyword reaching `ValidationError.__init__` → `self.params` | R | the produced mapping becomes `error.params`; rendering `'%(value)s' %= params` is the dict lookup of `'value'` (mapping.md §2,§3). |

The discriminating content — the rejection's param map must BIND the value
placeholder — lives in `placeholder_value() in Result()` and
`Result()[placeholder_value()] == ToSeq(value)`. Pre-patch, the bare raises
passed no params, so `error.params` is `None`/empty and `'%(value)s' %= params`
cannot render the input; `model_prepatch.py` reproduces that (empty mapping) and
**fails** the postcondition `placeholder_value() in Result()` — exactly the spec
sensing the change (G-DIFF).

## B. Bound-limit param map — `build_limit_params(value, limit)`

Representative gold hunk (`django/core/validators.py:460-463`, identical shape
at the `max_decimal_places` and `max_whole_digits` raises 466-469 / 473-476, and
structurally at the `FileExtensionValidator` raise 507-512):
```
  raise ValidationError(
      self.messages['max_digits'],
      code='max_digits',
-     params={'max': self.max_digits},
+     params={'max': self.max_digits, 'value': value},
  )
```

| # | model.py impl op (`build_limit_params`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameters `value: List[int]`, `limit: List[int]` | the `value` argument and the limit expression (`self.max_digits` etc.) | R | both rendered via `str(...)`; `str` ↔ `List[int]` (mapping.md §2). |
| B2 | `params[placeholder_limit()] = ToSeq(limit)` | the pre-existing `'max': self.max_digits` entry the patch KEEPS | R + I | the limit binding is preserved, not dropped; key `'max'` ↔ `placeholder_limit()` (R), value ↔ `ToSeq(limit)` (R). |
| B3 | `params[placeholder_value()] = ToSeq(value)` | the added `'value': value` entry | R + I | key `'value'` ↔ `placeholder_value()` (R); the addition itself identical (I). |
| B4 | `return params` (a fresh two-entry `Dict`) | the `params=` keyword reaching `ValidationError.__init__` | R | as A3. |

The discriminating content — a bound-limit rejection must bind BOTH the limit
(preserved) AND the value (added) — lives in the four membership/value
postconditions. Pre-patch the map carried only `{'max': ...}`;
`model_prepatch_2.py` reproduces that and **fails** the postcondition
`placeholder_value() in Result()` (G-DIFF). The "exactly these two keys" closure
clause also fails any impl that drops `'max'`, pinning that the limit binding is
preserved.

## C. The `DecimalField.validate` removal — `decimal_reject_params(finite, value)`

Gold hunk (`django/forms/fields.py:350-358`):
```
-     def validate(self, value):
-         super().validate(value)
-         if value in self.empty_values:
-             return
-         if not value.is_finite():
-             raise ValidationError(self.error_messages['invalid'], code='invalid')
```

This hunk *removes* a duplicate not-finite (NaN/inf) screen that raised a
**paramless** `ValidationError(..., code='invalid')` in the form-field layer.
Removing it lets a not-finite `Decimal` flow through to `DecimalValidator.__call__`'s
`if exponent in {'F','n','N'}` branch (`validators.py:440-441`), which the patch
updates to the bare rejection carrying `params={'value': value}`. The
control-flow change is modelled by `decimal_reject_params`, whose carrier is a
`finite` flag (whether the candidate is representable) plus the offending
`value`; it returns the parameter mapping the rejection produces.

| # | model.py impl op (`decimal_reject_params`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | parameter `finite: bool` | the `value.is_finite()` predicate that drove the deleted screen (`fields.py:357`) | R | a `Decimal` cannot be expressed in Nagini; the only property the deleted branch reads is its finiteness, carried as a `bool` (mapping.md §2). |
| C2 | parameter `value: List[int]` | the `value` argument flowing into `DecimalValidator.__call__` | R | as A1: `str(value)` ↔ `List[int]` code points. |
| C3 | NO `if not finite: return <paramless>` short-circuit — control flows on to the bare rejection | the **deletion** of `if not value.is_finite(): raise ValidationError(self.error_messages['invalid'], code='invalid')` | R/I | the removed branch is exactly the suppressed `not finite` short-circuit; absence of that early return is the deletion. The deleted raise carried no `params`, modelled as the empty mapping the prepatch returns. |
| C4 | `return build_invalid_params(value)` | the not-finite candidate reaching `DecimalValidator.__call__`'s `exponent in {'F','n','N'}` bare rejection, which the patch makes `params={'value': value}` | R + I | after the deletion the NaN error is produced by the param-carrying validator (site A); the produced map is exactly `build_invalid_params(value)` (deep call into site A's modelled behaviour, not an axiom). |

The discriminating content — a rejected decimal candidate must bind the value
placeholder **regardless of finiteness**, producing EXACTLY the bare-rejection
mapping (the value binding and nothing else) whichever way the finiteness bit
falls — lives in `placeholder_value() in Result()`,
`Result()[placeholder_value()] == ToSeq(value)`, and the unconditional
`<binds nothing else>` closure. The closure is unconditional (not guarded on
`not finite`) because the modeled raise site — `DecimalValidator.__call__`'s
bare `invalid` rejection (`validators.py:441`) — produces exactly
`params={'value': value}` for ANY candidate that reaches it; a
finiteness-guarded closure would admit an impl that smuggles a spurious extra
binding (e.g. a bogus `'max'`) onto the finite branch, which no real rejection
shape produces. Pre-patch the
duplicate screen intercepted a not-finite candidate with a paramless error;
`model_prepatch_3.py` reproduces that (the `if not finite: return {}`
short-circuit) and **fails** the postcondition `placeholder_value() in Result()`
of `decimal_reject_params` — exactly the spec sensing the control-flow deletion
(G-DIFF). The change is modelled **deeply**: the routing decision is a concrete
branch on the `finite` carrier and the param map is built by the existing deep
`build_invalid_params`; there is no axiom about the function under change (no
kind-3).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I; there is **no consumed axiom** at all. The one
*unchanged* mechanism the model leans on — Python's `%`-style named
interpolation of `ValidationError.__iter__` (`message %= error.params`) and the
`run_validators` message-override that preserves `error.params` — is modelled
**deeply** (membership of a placeholder token models renderability; the dict
value models the rendered string) and validated against the real Django stack by
G-AX (axiom_check.py, mapping.md §3), as an **A-reference**, not consumed as an
axiom. The changed behaviour (which keys each rejection's param map binds, and
the routing of a not-finite decimal candidate to the value-binding rejection) is
spelled out in the impl region: `decimal_reject_params` decides on the concrete
`finite` carrier and delegates to the deep `build_invalid_params`, so the
function under change (`DecimalField.validate`'s control flow) is modelled
DEEPLY — there is no axiom about it.

## E. verify(model) ⇒ resolved

`build_invalid_params` verifies only if its produced map binds the value
placeholder to the offending input (site A); `build_limit_params` verifies only
if its produced map binds BOTH the preserved limit AND the added value (site B);
`decimal_reject_params` verifies only if a rejected decimal candidate binds the
value placeholder *regardless of finiteness* — i.e. only if no paramless
not-finite short-circuit remains (site C). By R (str ↔ List[int];
`'value'`/`'max'` keys ↔ tokens; dict membership/lookup ↔ `%(name)s`
renderability; `value.is_finite()` ↔ the `finite` flag) the verified maps equal
the gold patch's `params={'value': value}` / `params={'max': ..., 'value': value}`
on the tested inputs, and the not-finite candidate is routed (via the removal of
the duplicate screen) to the site-A bare rejection. By G-AX the deep rendering
model equals the real Django `%`-interpolation: a custom `'%(value)s'` template
renders to `str(value)` exactly when `'value'` is bound, and the F2P tests
observe exactly that (`form.errors == {'field': [value]}`), including the `'NaN'`
decimal case that the removal routes through. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement, and the
gold patch resolves (G-RESOLVE). The single trust point is the rendering
A-reference (G-AX); there is no refinement gap and no consumed axiom.
