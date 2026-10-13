# refinement.md — django__django-13933

Maps every operation in `implementation_coerceChoice` to its `patch.diff`
counterpart in `ModelChoiceField.to_python` (`django/forms/models.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch `to_python`)
```python
def to_python(self, value):
    if value in self.empty_values:
        return None
    try:
        key = self.to_field_name or 'pk'
        if isinstance(value, self.queryset.model):
            value = getattr(value, key)
        value = self.queryset.get(**{key: value})
    except (ValueError, TypeError, self.queryset.model.DoesNotExist):
        raise ValidationError(
            self.error_messages['invalid_choice'],
            code='invalid_choice',
            params={'value': value},
        )
    return value
```
The modeled value is the COERCION OUTCOME: empty result for a sentinel, the
resolved answer when resolution succeeds, or a `ValidationError` carrying the
template, the fixed code, and (post-patch) the offending value under the
`'value'` placeholder.

## Operation correspondence
| # | Lean op (`implementation_coerceChoice`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if value ∈ emptyValues then return Except.ok none` | `if value in self.empty_values: return None` | R | `value in self.empty_values` ↔ `value ∈ emptyValues` (membership over `List Val`); `return None` ↔ `Except.ok none`. Type bijection in mapping.md. |
| 2 | `match lookup with \| some r => return Except.ok (some r)` | `value = self.queryset.get(**{key: value})` … `return value` (the no-raise path) | R | the resolution's success outcome (a stored object, identity its pk) ↔ `lookup = some r`; `return value` ↔ `Except.ok (some r)`. `queryset.get`/`getattr`/`isinstance` enter as the `lookup` datum (mapping.md), not as an axiom. |
| 3 | `\| none => return Except.error { messageTemplate := invalidMessage, code := invalidChoiceCode, params := [(valueParamName, value)] }` | `except (ValueError, TypeError, DoesNotExist): raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice', params={'value': value})` | R | the resolution raising one of the caught exceptions ↔ `lookup = none`; the raised `ValidationError(msg, code='invalid_choice', params={'value': value})` ↔ `Except.error {messageTemplate := invalidMessage, code := "invalid_choice", params := [("value", value)]}`. The `params={'value': value}` dict ↔ singleton assoc-list `[(valueParamName, value)]` (mapping.md dict-bijection). **This is the operation the patch adds.** |

Every op is R; **no A row** (no axiom consumed, no deep-model reference of an
unchanged callee — `queryset.get` / `getattr` / `empty_values` enter as data per
mapping.md). Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R legs ⇒ G-CONF
The whole impl is R, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the `except` arm is `raise ValidationError(self.error_messages
['invalid_choice'], code='invalid_choice')` — no `params`, so a custom
`invalid_choice` template containing `%(value)s` cannot render the submitted
value. The prepatch impl (`implementation_coerceChoice` with `params := []` on
the rejection branch) is exactly this: it raises the same template and code but
with NO parameter binding. It therefore cannot satisfy
`problem_spec_coerceChoice` on the discriminating clause
(`value ∉ emptyValues → lookup = none → result = Except.error {… params :=
[("value", value)]}`): the carried gold proof's final `rfl` fails because
`params := []` is not definitionally `[("value", value)]`. This is precisely the
case the FAIL_TO_PASS test `test_modelchoicefield_value_placeholder` exercises (a
field whose `invalid_choice` message is `'"%(value)s" is not one of the available
choices.'`, cleaned of `'invalid'`, must render `'"invalid" is not one of the
available choices.'`). G-DIFF: the prepatch `Solution_prepatch.lean` fails to
verify.
