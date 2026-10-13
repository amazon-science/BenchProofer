# mapping.md — django__django-13933

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 42e8cf47c7ee2db238bf91197ea398126c546741`, states the type
abstraction, and gives the provenance of the one deep-model reference
(A-reference). This bundle consumes **no** `@ContractOnly` axiom.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_invalid_choice(template, value)` | the invalid-choice error produced by `ModelChoiceField.to_python` — `django/forms/models.py:1278-1288` (the `except (...) : raise ValidationError(...)` arm, body line 1287) — observed through how its message is rendered (`ValidationError.__iter__`, `django/core/exceptions.py:178-183`) | the modeled changed behaviour: the rendered text of the invalid-choice error |
| `interpolated(template, value)` *(deep model — A-reference)* | the named-mapping `%`-interpolation `message %= error.params` in `ValidationError.__iter__` — `django/core/exceptions.py:181-182` — applied to the field's `invalid_choice` template with `params={'value': value}` | pure spec: substitution of the rejected value into the template's `%(value)s` placeholder; the deep model of the real `str.__mod__` named mapping, validated `interpolated == (template % {'value': value})` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `placeholder()` | the literal named-placeholder token `%(value)s` appearing in the configurable `invalid_choice` error templates (e.g. `ModelMultipleChoiceField.default_error_messages['invalid_choice']`, `django/forms/models.py:1307`, and any user-supplied `error_messages={'invalid_choice': '... %(value)s ...'}`) | pure spec: the placeholder token as code points |
| `starts_with_placeholder(s)` | the per-position check inside the named `%`-mapping scanner that recognizes the `%(value)s` conversion | pure spec helper for the fold |
| `_render(ts, value, i)` | internal proof carrier (the verified skeleton of the substitution) | no repo counterpart; realizes `interpolated` constructively |

The pre-patch repo fact the change fixes (for the refinement audit, not
referenced from the consumer spec view): `to_python`'s `raise
ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')`
at `django/forms/models.py:1287` passes **no** `params`, so when the message is
later rendered (`ValidationError.__iter__`, `django/core/exceptions.py:180-182`)
the guard `if error.params:` is false, the `message %= error.params` step is
skipped, and the template — including any `%(value)s` placeholder — survives
verbatim into the user-visible message.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `invalid_choice` message template, the rejected `value`, and the rendered message) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `value` coerced to text by `%s` inside the mapping | identity on the code-point list | the F2P value is already a `str` (`'invalid'`); `%(value)s` formats it with `str(...)`, observationally the identity on its code points |
| `params={'value': value}` dict argument to `ValidationError`, consumed by `message %= error.params` | the second argument `value` of `render_invalid_choice` / `interpolated` | the only key the `invalid_choice` template references is `value`; the mapping substitutes it for the `%(value)s` token |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `interpolated` deep model ↔ real `str` named-mapping (A-reference)
**Operation:** CPython `str.__mod__` with a mapping argument — i.e.
`template % {'value': value}` — restricted to the domain Django's
invalid-choice templates inhabit: templates whose only `%`-conversion is the
named placeholder `%(value)s`. The changed behaviour is modeled **deeply** by
the `@Pure` front-recursive fold `interpolated` (with `placeholder` and
`starts_with_placeholder`) in the `pure` region; there is **no consumed axiom**.
The deep model is validated equal to the real operation out-of-band by
axiom_check.py (G-AX).

For a template whose only `%`-construct is `%(value)s`, the named mapping
replaces **every** occurrence of `%(value)s` with `str(mapping['value'])` and
leaves all other characters unchanged — exactly the substitution
`interpolated` computes:

  `%(value)s → value`, every other code point → itself.

**Domain (kept sound):** the model does NOT cover templates with a bare `%`, an
escaped `%%`, or any other conversion (`%s`, `%(pk)s`, …); on those the real
operator escapes / raises / substitutes differently. The `invalid_choice`
templates this change concerns contain only `%(value)s`, so the model's domain
is exactly the relevant one. axiom_check.py builds its fuzz inputs from this
domain (placeholder tokens interleaved with non-`%` characters) and asserts
`interpolated == (template % {'value': value})` on 143 boundary + 40000 fuzz
inputs (incl. the literal Django templates and the F2P configured template),
0 mismatch. Docs: https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting

**Why this is the right callee, not the function under change.** The gold patch
edits `to_python` to *supply* `params={'value': value}` to the
`ValidationError`. The observable consequence — the only thing the F2P test
checks — is that the rendered message interpolates the value. That rendering is
performed by the unchanged `ValidationError.__iter__` via the unchanged `str`
`%`-mapping. The deep model captures that rendering; the change itself (passing
`params`) is what flips whether interpolation happens at all, which is the
discriminating clause the prepatch fails.
