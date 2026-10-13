# mapping.md — django__django-11119

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d4df5e1b0b1c643fe0fc521add0236764ec8e92a`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `django/template/engine.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `valueToDisplay (encodeMarkup : Bool) (value : List Char)` | `Engine.render_to_string(self, template_name, context=None)` — `django/template/engine.py:150` (body lines 167-171) | the modeled changed function: how a context value is rendered to display text under the engine's escaping policy |
| `encodeMarkup : Bool` | `self.autoescape` (`engine.py:44`, set in `Engine.__init__`, default `True`) threaded into the rendering context | the escaping policy flag the fix propagates |
| `escapedSeq (s : List Char)` *(deep model — A-reference)* | the escaping branch of `render_value_in_context` — `conditional_escape(str(value))` ≡ `escape(value)` for a plain `str`, `django/template/base.py:970` / `django/utils/html.py:36,95` | pure spec: markup-escape of a value; deep model of the unchanged escaping callee, validated `escapedSeq == real escape` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `entity (c : Char)` | the per-code-point substitution `str.translate(_html_escapes)` realizes (`django/utils/html.py:27-33,36`) | pure spec: entity sequence for one code point |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the escaping policy flag (`self.autoescape`, threaded into `Context(..., autoescape=self.autoescape)`) | `Bool` (`encodeMarkup`) | Python `True` ↔ `true`, `False` ↔ `false`; `context.autoescape` truthiness ↔ the `Bool` |
| a context value rendered into the template (`str`, e.g. `{'obj': '<script>'}`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `str(value)` coercion / `template_localtime` / `localize` (`base.py:968-969`) | identity on the `List Char` | for the plain-`str` values the F2P test renders, these are observationally the identity (no datetime / number / lazy involved). |
| `mark_safe(...)` wrapper inside `escape` | identity (omitted) | `mark_safe` only sets the `SafeString` flag; it does not alter the character content the rendered output / F2P test observes. Identity on `List Char`. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the escape is per-code-point.

The fixed template text surrounding the variable in the F2P template
`test_context.html` (`obj:{{ obj }}\n`) is rendered by literal `TextNode`s,
unchanged by the fix; G-CONF treats it as an identity (I) passthrough of the
template literal (the constant prefix `obj:` and suffix `\n`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `escapedSeq` deep model ↔ the escaping callee (A-reference)
**Callee:** the escaping branch of `django.template.base.render_value_in_context`
(`base.py:970`): `conditional_escape(value)` after coercion to `str`. For a
**plain `str`** value (the F2P input is `'<script>'`, an ordinary str — not a
`Promise`, not `SafeData`/`__html__`-bearing) `conditional_escape` reduces to
`django.utils.html.escape` (`html.py:95-107`), which at this `base_commit` is:

```python
_html_escapes = {
    ord('&'): '&amp;',
    ord('<'): '&lt;',
    ord('>'): '&gt;',
    ord('"'): '&quot;',
    ord("'"): '&#39;',
}

def escape(text):
    return mark_safe(str(text).translate(_html_escapes))
```

`str.translate` substitutes each code point **independently** in a single pass:
`& → &amp;`, `< → &lt;`, `> → &gt;`, `" → &quot;`, `' → &#39;`, every other code
point passes through unchanged. There is no re-escaping concern (translate maps
each input code point once; the emitted entity bytes are never re-scanned).
This is exactly what `escapedSeq`/`entity` encode. **NB:** at this commit the
apostrophe maps to the legacy decimal reference **`&#39;`** (NOT `&#x27;` — the
`html.escape` switch to `&#x27;` is a *later* Django change, instance 11276; do
not import that here).

**Flag dependency (§3 SPEC_GUIDE):** the escape model is faithful only for plain
non-safe `str` values, where `conditional_escape == escape`; G-AX fuzzes plain
`str` inputs accordingly (it does not feed `SafeString`/`__html__` objects,
which `conditional_escape` would short-circuit — those are out of the F2P
input domain).

### 3.2 No consumed axioms
The escaping callee is modeled **deeply** (`escapedSeq`/`entity`), not consumed
as an axiom; its equality to the real callee is the A-reference G-AX validates.
The operation the patch actually changed — *which rendering branch the value
takes* (escaped vs. verbatim), governed by the threaded flag — is modeled
concretely by the `if encodeMarkup then escapedSeq value else value` selection.
Nothing is delegated to a consumed `axiom`.

**Soundness check (G-AX):** `axiom_check.py` runs the real `escape` /
`conditional_escape` on boundary inputs over `& < > " '` (alone, doubled,
combined, mixed with ordinary text) plus 20 000 randomized fuzz strings,
asserting `escapedSeq == real escape` (A-reference). Imports only the repo's
`django.utils.html`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11119`** so the
consumer-side verdict (§11.3) is reproducible. Its ORACLE is the **patched**
`Engine.render_to_string` exercised through an in-memory (`locmem`) loader on a
`obj:{{ obj }}\n` template, over both engine `autoescape` settings; its SHADOW
transliterates the R/I ops of `valueToDisplay`
(`'obj:' + (escapedSeq(s) if encodeMarkup else s) + '\n'`). The A-reference
`escapedSeq` is transliterated in the shadow (it is an R/I leg for G-CONF;
its equality to the real callee is G-AX's job).
