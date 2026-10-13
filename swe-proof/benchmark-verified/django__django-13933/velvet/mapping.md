# mapping.md — django__django-13933

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 42e8cf47c7ee2db238bf91197ea398126c546741`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one deep-model reference.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderInvalidChoice (template : List Frag) (value : List Char)` | the observable effect of the changed `raise ValidationError(...)` in `ModelChoiceField.to_python` — `django/forms/models.py:1284` (the `except` clause, body line 1288) — namely the message the raised error renders (`ValidationError.messages`, the F2P observation) | the modeled changed behavior: the rejection message produced when an invalid choice is rejected |
| `Frag` (`lit` / `valueSlot`) | a fragment of a `%(name)s`-style message template: a literal code point, or the `%(value)s` named placeholder | pure spec: the abstract shape of a parametrized message |
| `renderFrag` / `rendered` *(deep model — A-reference)* | the printf-style interpolation `message %= error.params` performed by `ValidationError.__iter__` (`django/core/exceptions.py`) once the gold patch supplies `params={'value': value}` | pure spec: rendering = substitute the offending value at each placeholder, pass literals through; deep model of the (unchanged) string-interpolation builtin, validated `rendered == template % {'value': value}` by axiom_check.py (G-AX), NOT consumed as an axiom |

The patched call site adds the keyword argument `params={'value': value}` to the
`ValidationError(...)` raised in the `except (ValueError, TypeError,
self.queryset.model.DoesNotExist)` branch. The renderer
`ValidationError.__iter__` already existed and is UNCHANGED: it does
`message %= error.params` iff `error.params` is truthy. The gold change is purely
"now pass the value as a substitution parameter"; its sole observable effect is
that a value placeholder in `error_messages['invalid_choice']` gets FILLED with
the offending value instead of being yielded verbatim. That observable effect is
what `renderInvalidChoice` models.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the message template `error_messages['invalid_choice']` (a `%(value)s`-style printf `str`) | `List Frag` | each `%(value)s` named placeholder ↔ `Frag.valueSlot`; each literal code point `ch` ↔ `Frag.lit (Char.ofNat (ord ch))`; a literal `'%'` ↔ `Frag.lit '%'` (written `%%` in the printf string so it is never a conversion specifier). `len` ↔ `.length`; `str` concat ↔ `List` `++`; empty template ↔ `[]` |
| the offending submitted `value` (rendered via `str(value)`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; on the BMP `Char.ofNat (ord ch)` ↔ `ch` is total and exact |
| the rendered message `ValidationError(...).messages[0]` (a `str`) | `List Char` (`out`) | same `str` ↔ `List Char` bijection; this is the F2P observation (`assertEqual(cm.exception.messages, expected)`) |

Lean `String`/`List Char` indexing is total and sound; the carrier is `List Char`
/ `List Frag` because the operation is a per-fragment / per-code-point
concatenation.

`value` (the submitted choice) is in reality the object passed to `to_python`;
`ValidationError.__iter__` interpolates it via `%`, which coerces with
`str(value)`. The F2P test passes a `str` (`'invalid'`), so the `str(value)`
coercion is observationally the identity on the carrier; the model takes `value`
as an already-`str` `List Char` (the tested domain).

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `rendered` deep model ↔ printf-style `%` interpolation (A-reference)
**Callee:** CPython printf-style string interpolation `template % {'value': v}`,
the operation `ValidationError.__iter__` runs (`message %= error.params`) once the
gold patch supplies `params`. The changed behavior is modeled **deeply** by
`rendered`/`renderFrag` (`pure` region); there is **no consumed axiom**. The real
renderer (`django/core/exceptions.py`):

```python
def __iter__(self):
    ...
    for error in self.error_list:
        message = error.message
        if error.params:
            message %= error.params      # post-patch params={'value': value}
        yield str(message)
```

`%(value)s` named interpolation substitutes every `%(value)s` placeholder with
`str(value)` and passes all other text through verbatim — which is exactly what
`rendered`/`renderFrag` encode (`valueSlot → value`, `lit c → [c]`). When NO
`params` is supplied (pre-patch), the branch is skipped and the template is
yielded verbatim — the placeholder stays literal. That is the bug
`Solution_prepatch.lean` reproduces (the value slot renders to the literal
`%(value)s` token), failing the `rendered value [valueSlot] = value` clause.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL printf interpolation
`template_to_format_string(template) % {'value': value}` on boundary inputs
(placeholder alone, leading/trailing/repeated placeholders, no placeholder, empty
template, empty value, value carrying `%`/significant chars) plus 50 000
randomized fuzz inputs, asserting `rendered(value, template) ==` the real
interpolation. Imports only the Python builtin `%`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13933`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`renderFrag`/`rendered` (the I/R fold ops) to Python and bridges templates via
the `List Frag ↔ %(value)s`-template bijection above. The ORACLE is the REAL repo
path: it constructs `django.core.exceptions.ValidationError(fmt,
code='invalid_choice', params={'value': value})` (the gold patch's call) and
reads `.messages[0]` — exactly the F2P observation. The deep model's equality to
that interpolation is the A-reference (G-AX); G-CONF additionally checks the
spelled-out fold transliterates faithfully end-to-end against the real renderer.
