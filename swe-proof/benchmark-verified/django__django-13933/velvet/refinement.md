# refinement.md — django__django-13933

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderInvalidChoice` `do` block + the deep `rendered`/`renderFrag` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(a deep model validated `== the real callee` by axiom_check.py / G-AX), or **I**
(identical concrete operation). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviorally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The rejection-message site — `ModelChoiceField.to_python` (`django/forms/models.py:1284`)

Gold hunk:
```
- raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
+ raise ValidationError(
+     self.error_messages['invalid_choice'],
+     code='invalid_choice',
+     params={'value': value},
+ )
```

The observable effect (what F2P `test_modelchoicefield_value_placeholder`
asserts via `cm.exception.messages`): the rejection message now has the offending
value interpolated at its `%(value)s` placeholder, rather than the placeholder
being yielded verbatim. `renderInvalidChoice` models that message.

| # | Solution.lean impl op (`renderInvalidChoice`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `template : List Frag` | `self.error_messages['invalid_choice']` (a `%(value)s`-style template `str`) | R | template `str` ↔ `List Frag` (mapping.md §2): each `%(value)s` ↔ `valueSlot`, each literal char ↔ `lit c`. G-CONF bridges via `template_to_format_string`. |
| A2 | parameter `value : List Char` | the `value` local interpolated by `params={'value': value}` (coerced `str(value)`) | R | `str` ↔ `List Char` (mapping.md §2). The F2P value is already a `str`, so `str(value)` is observationally the identity on the carrier. |
| A3 | result is `rendered value template`: the per-fragment substitution (`valueSlot → value`, `lit c → [c]`), computed by the backward `while` fold | the message rendered by `ValidationError.__iter__` once `params={'value': value}` is supplied (`message %= error.params`) | A-reference + I | the changed behavior is modeled **deeply**: `rendered`/`renderFrag` (pure region) and the verified loop ARE the substitution. No consumed axiom. The fold ops (`renderFrag value f`, `++`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real printf interpolation is the **A-reference** G-AX validates (mapping.md §3.1). |
| A4 | `out` returned (`List Char`) | the `str` the test reads as `exception.messages[0]` | R | `str` ↔ `List Char` (mapping.md §2); `assertEqual(cm.exception.messages, expected)` compares rendered characters. |

Discriminating content of the change — a value placeholder must be FILLED with
the offending value, not left standing — lives in `rendered value [valueSlot] =
value` (model) ⇔ the `message %= error.params` substitution the supplied
`params={'value': value}` enables (real). The pre-patch raised the error with NO
`params`, so `__iter__` skipped the interpolation and yielded the template
verbatim (the `%(value)s` placeholder unfilled); `Solution_prepatch.lean`
reproduces exactly that (the value slot renders to the literal `%(value)s` token)
and **fails** the value-slot clause `rendered value [valueSlot] = value` — the
unsolved goal `['%','(','v','a','l','u','e',')','s'] = renderFrag value valueSlot`
(G-DIFF). On a template with no value slot the prepatch renders the same literal
text, so the divergence is isolated to templates carrying the placeholder — the
real bug, and what the PASS_TO_PASS `test_modelchoicefield` (a literal `'INVALID
CHOICE'` template, no placeholder) leaves untouched.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation whose OBSERVABLE behavior genuinely
changed — the rejection message acquiring the interpolated value — is modeled
**deeply** (the spelled-out fold `rendered`/`renderFrag`, step A3, an A-reference
+ I), not hidden behind an axiom about the operation under change. There are **no
consumed axioms** (`Solution.lean`'s `axioms` region is empty): the renderer
`%` is a Python builtin modeled deeply and validated against the real
interpolation by G-AX, not stood in for by an `axiom`. The unchanged machinery —
the `try/except` choice of branch, the `queryset.get` lookup, the `ValidationError`
construction and storage — is outside the modeled scope (mapping.md §1): the patch
adds only the `params={'value': value}` keyword; it changes no control flow.

## C. verify(Solution.lean) ⇒ resolved

`renderInvalidChoice` verifies only if its output equals the exact per-fragment
substitution with the value FILLED at each `valueSlot` (A3) and the value-slot /
literal anchors hold (`rendered value [valueSlot] = value`, `∀ c, rendered value
[lit c] = [c]`). By R (`template str ↔ List Frag`, `value str ↔ List Char`, the
`messages[0]` ↔ `out` identity) the verified renderer equals the message
`ValidationError(..., params={'value': value}).messages[0]` produces on the tested
inputs; by G-AX the deep model `rendered` equals the real printf interpolation
(A-reference); by G-CONF the R/I transliteration of the fold agrees with the real
`ValidationError(...).messages` rendering on 10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited interpolation reference — and the gold patch resolves
(G-RESOLVE: the F2P `test_modelchoicefield_value_placeholder` now sees the
offending value in the message). The single trust point is refinement fidelity
(this document, G-EQ) plus the G-AX interpolation-equality check; there is no
axiom-soundness trust point because no axiom is consumed.
