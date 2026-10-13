# refinement.md — django__django-13933

The operation-by-operation correspondence between `model.py`'s implementation
(`render_invalid_choice` + its proof carrier `_render`, and the deep model
`interpolated`) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized/deep-modeled callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated `==` the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`,
confirmed with `git apply --check`, and is the real correctness oracle,
G-RESOLVE).

## A. The change site — `ModelChoiceField.to_python` (`django/forms/models.py:1287`)

Gold hunk:
```
- raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
+ raise ValidationError(
+     self.error_messages['invalid_choice'],
+     code='invalid_choice',
+     params={'value': value},
+ )
```

What the model captures is the **observable** effect of this hunk: the rendered
text of the invalid-choice error. By passing `params={'value': value}`, the
patch causes the unchanged rendering path
(`ValidationError.__iter__`, `django/core/exceptions.py:180-182`:
`if error.params: message %= error.params`) to interpolate the value into the
configurable `invalid_choice` template. The model's
`render_invalid_choice(template, value)` returns exactly that rendered message.

| # | model.py impl op (`render_invalid_choice`) | patch.diff op / framework effect | tag | justification |
|---|---|---|---|---|
| A1 | param `template: List[int]` | `self.error_messages['invalid_choice']` (a `str` template) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | param `value: List[int]` | the local `value` packed into `params={'value': value}` and coerced by `%s` | R | `str` ↔ `List[int]`; `str(value)` is the identity on the F2P `str` input (mapping.md §2). |
| A3 | result is `interpolated(ToSeq(template), ToSeq(value))`, i.e. every `%(value)s` token replaced by `value`, computed by the verified `_render` recursion/fold | the message the framework renders for the raised error: `template % {'value': value}` (because `params` is now non-empty, `ValidationError.__iter__` runs `message %= error.params`) | A-reference | the changed observable (the rendered message) is modeled **deeply**: `interpolated` (the spelled-out front-recursive substitution in the `pure` region) and the verified `_render` ARE the named-mapping interpolation. There is no consumed axiom. The deep model is validated **== the real operation** out-of-band by G-AX (axiom_check.py runs `template % {'value': value}` on boundary+fuzz and asserts `== interpolated`). The real callee `str.__mod__` with `{'value': ...}` IS that substitution on the relevant domain (mapping.md §3.1). |

The discriminating content of the change — that the value is actually
interpolated rather than the literal `%(value)s` placeholder surviving — lives
in `A3`'s postcondition `ToSeq(Result()) == interpolated(...)`. The pre-patch
code supplies **no** `params`, so the `message %= error.params` step is skipped
and the template is emitted verbatim. `model_prepatch.py` reproduces that
(its `render_invalid_choice` returns a verbatim copy of `template`) and **fails**
the postcondition `ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value))`
whenever the template contains the placeholder — exactly the spec sensing the
change (G-DIFF). This matches the F2P test, whose template
`'"%(value)s" is not one of the available choices.'` must render as
`'"invalid" is not one of the available choices.'`.

## B. The proof carrier — `_render`

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `_render(ts, value, i)` recursion building the result by token/character with the front-recursive `interpolated` postcondition | none (internal) | I | `_render` is a verified constructive realization of `interpolated`; it introduces no behaviour beyond computing the deep model. It is not a repo symbol; it carries the proof that a `List[int]` equal to `interpolated(...)` is producible. No refinement obligation beyond `interpolated` itself (A3). |

## C. No consumed axiom; no kind-3 step

Every step above is R, A-reference, or I. The one operation that genuinely
*changed observably* — interpolating the rejected value into the message — is
modeled **deeply** (`interpolated` consumed by `render_invalid_choice`, an
**A-reference**), not hidden behind an axiom about the function under change.
There is **no `@ContractOnly` axiom** in this bundle (the `axioms` region is
empty), so there is nothing to mislabel as A-consumed, and no dead axiom. The
real `str` `%`-mapping appears only as the **A-reference** that G-AX validates
the deep model against. No step is a *changed operation Nagini cannot express*
(kind-3): the substitution is fully expressible as the `List[int]`/`PSeq` fold.

## D. verify(model) ⇒ resolved

`render_invalid_choice` verifies only if its output equals the exact
per-token/per-character interpolation of `value` into `template` (A3). By R
(`str` ↔ `List[int]`, `str(value)` identity) the verified result equals
`template % {'value': value}` on the tested `str` inputs; by G-AX the deep model
`interpolated` equals that real `%`-mapping (A-reference) over its declared
domain (the only `%`-construct being `%(value)s`, which is exactly the form of
Django's `invalid_choice` templates). Therefore a model satisfying this spec,
refined by the map above, produces the same rendered invalid-choice message the
gold patch causes — and the gold patch resolves (G-RESOLVE). The single trust
point is the A-reference soundness audited by G-AX (PLAN §1.1); there is no
consumed-axiom trust point because the bundle consumes no axiom.
