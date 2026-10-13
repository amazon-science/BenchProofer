# refinement.md — django__django-13212

Maps every operation in `implementation_checkOutcome` to its `patch.diff`
counterpart (the uniform rejection step shared by every validator's `__call__` in
`django/core/validators.py`). Tags: **R** type-refinement, **A-consumed** proof
uses a callee axiom, **A-reference** deep-modeled changed op validated == real
callee, **I** identical concrete op.

## Patch (post-patch, the uniform rejection step)
```python
def __call__(self, value):
    ...                                  # decide acceptance/rejection (UNCHANGED)
    if <input is acceptable>:
        return                           # success, no error context
    # rejection:
    raise ValidationError(self.message, code=self.code, params={'value': value})
    #   or, where a site already supplies intrinsic params:
    #   params={'max': self.max_digits, 'value': value}
```
The modeled value is the validation OUTCOME for one input: `none` when the input
is accepted (no error raised), `some params` when rejected (the ordered entries
of the `ValidationError`'s substitution `params` dict — Python dicts are
insertion-ordered, and each patched site writes its intrinsic entries first and
`'value'` last). The patch's behavioral change is that a rejection's `params`
now binds `'value'` to the rejected input, appended after the intrinsic entries.
The spec pins the rejection result to exactly `baseParams ++ [("value", value)]`
(the whole sequence, not just its lookup view), matching
`list(dict.items())` of the patched dict.

## Operation correspondence
| # | Lean op (`implementation_checkOutcome`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if accepted then return none` | the acceptance path: validator returns without raising (`if invalid_input:` is false, scheme valid, address parses, …) | I | acceptance ⇒ no error context. The verdict itself is the UNCHANGED logic, carried as the input `accepted` (mapping.md); the patch does not touch it. |
| 2 | `return some (baseParams ++ [(valueKey, value)])` | `raise ValidationError(self.message, code=self.code, params={**intrinsic, 'value': value})` | R + I | a raised `ValidationError` carrying a `params` dict ↔ `some params`; the dict ↔ its ordered entry list `list(dict.items())` (key→rendered-value, insertion order). The **changed** part — appending the `('value', value)` binding after whatever intrinsic params pre-exist (every patched site writes `'value'` last) — is modeled DEEPLY as a list append, not axiomatized. `baseParams` ↔ the pre-existing `params={...}` (empty at most sites; `{'max':…}` for DecimalValidator, `{'extension':…,'allowed_extensions':…}` for FileExtensionValidator). |
| 3 | `valueKey := "value"` | the literal dict key `'value'` | I | the substitution name a `%(value)s` placeholder resolves against. |

No op is **A-consumed** or **A-reference**: the changed operation is a pure data
construction over the inputs (`baseParams ++ [("value", value)]`), and the
validity verdict is an input rather than a modeled callee. Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I (a pure function of `value`, `accepted`, `baseParams`): on
acceptance it yields `none`; on rejection it yields the intrinsic params with the
`'value'` binding appended. `conformance_check.py` differential-tests this shadow
against the patched behavior (a faithful in-process replica of the patched
construction: an insertion-ordered dict built intrinsic-entries-first with
`'value'` added last), comparing the FULL ordered entry sequence
(`list(dict.items())` vs. the shadow's association list) over ≥10^5 fuzzed
inputs. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the rejection step is `raise ValidationError(self.message,
code=self.code)` (no `params`, or `params` WITHOUT a `'value'` entry). The
prepatch impl (`implementation_checkOutcome` returning `some baseParams` on
rejection, omitting the `('value', value)` binding) is exactly this bug: the
error context carries no `'value'` key. It therefore cannot satisfy
`problem_spec_checkOutcome` on the discriminating rejection conjunct `result =
some (baseParams ++ [(valueKey, value)])` (in particular the sequence it returns
lacks the trailing `("value", value)` entry) whenever the input is rejected —
precisely the F2P cases
(`test_value_placeholder_with_char_field`, `…_integer_field`, `…_decimal_field`,
`…_file_field`, `…_null_character`), which set `error_messages={code:
'%(value)s'}` and assert the rendered error equals the submitted value. With no
`'value'` param the `%(value)s` interpolation would raise/blank instead of
yielding the value, so the test fails. The acceptance leg (`accepted = true →
result = none`) is unchanged between pre/post, so it never discriminates — only
the rejection params do, which is exactly what the patch fixes. The carried gold
proof fails to typecheck against the buggy impl (G-DIFF; confirmed: the rejection
clause reduces to `False`).

## Note on the `forms/fields.py` hunk
The gold patch also deletes `FloatField.validate` (an over-strict finiteness
re-check) in `django/forms/fields.py`. No FAIL_TO_PASS test exercises that
deletion (the F2P suite is entirely the new `ValidatorCustomMessageTests`, which
covers the `params={'value': value}` behavior); it is carried verbatim in
`patch.diff` (gold) for G-RESOLVE but is not an independently-modeled behavior
and needs no separate prepatch.
