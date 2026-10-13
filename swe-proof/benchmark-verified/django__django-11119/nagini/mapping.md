# mapping.md — django__django-11119

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d4df5e1b0b1c643fe0fc521add0236764ec8e92a`, states the type
abstraction, and gives the provenance of each axiom / deep-model reference
(callee source + the exact behaviour encoded).

Repo file under change: `django/template/engine.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_value(value, engine_autoescape)` | `Engine.render_to_string(self, template_name, context)` — `django/template/engine.py:149` (changed line 163) | the modeled changed function: building the rendering context from the engine and producing the rendered interpolation of a single context value |
| `engine_autoescape` (bool param) | `self.autoescape` — `Engine.__init__` attribute set at `django/template/engine.py:44` (constructor kw `autoescape=True`, line 22) | the engine-level auto-escaping flag the fix propagates into the `Context` |
| `escaped_seq(s)` / `entity(c)` *(deep model — A-reference)* | `django.utils.html.escape` (`django/utils/html.py:37`, body line 46 `mark_safe(str(text).translate(_html_escapes))`), reached via `conditional_escape` (`html.py:95`) from `render_value_in_context` (`django/template/base.py:962`, escape branch line 970-973) | pure spec: HTML-escape of a sequence; the deep model of the UNCHANGED escaping callee applied to an interpolated value, validated `escaped_seq == django.utils.html.escape` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `seq_amp/seq_lt/seq_gt/seq_quot/seq_apos_dec` | the literal entity strings `&amp; &lt; &gt; &quot; &#39;` produced by `_html_escapes` (`html.py:27-33`) | pure spec: entity tokens as code-point sequences |

The repo symbol the change touches (for the refinement audit, not referenced
from the consumer spec view): the `Context(context)` construction in
`render_to_string` (`engine.py:163`), whose `autoescape` keyword defaults to
`True` in `Context.__init__` (`django/template/context.py:137`). The
`Context.autoescape` attribute is the flag `render_value_in_context`
(`django/template/base.py:970`) reads to decide whether to call
`conditional_escape(value)` (escape branch) or `str(value)` (verbatim branch).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the interpolated context value, and the rendered fragment) | `List[int]` of Unicode code points | `s[k]` ↔ `value[k] == ord(s[k])`; `len(s)` ↔ `len(value)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `self.autoescape` (Python `bool`) | `bool` param `engine_autoescape` | identity |
| `Context(context, autoescape=self.autoescape)` constructing a context whose `autoescape` attribute is then read by the renderer | the local boolean `ctx_autoescape` assigned from `engine_autoescape` and branched on | identity on the boolean; `Context.__init__` only stores the flag, `render_value_in_context` only reads it |
| `conditional_escape(value)` on a plain (non-`SafeData`, non-`Promise`) `str` (`html.py:95`) | `escaped_seq` deep model (== `escape`) | for the F2P inputs (plain strings with no `__html__` / `Promise`) `conditional_escape` reduces to `escape`; identity on the escape content |
| `mark_safe(x)` wrapper (`html.py:46`) | identity (omitted) | `mark_safe` only sets the `SafeString` flag; it does not alter the character content the F2P test observes |
| literal template text around the interpolation (`obj:` / trailing newline) | omitted (constant prefix/suffix common to both branches) | the F2P test differs only in the interpolated value's escaping; the constant literal text is identical pre/post-patch and not the modeled behaviour |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (checked by G-AX / axiom_check.py)

### 3.1 `escaped_seq` deep model ↔ `django.utils.html.escape` (A-reference)
**Callee:** `django.utils.html.escape` at this base_commit (`html.py:46`):

```python
_html_escapes = {
    ord('&'): '&amp;', ord('<'): '&lt;', ord('>'): '&gt;',
    ord('"'): '&quot;', ord("'"): '&#39;',
}
def escape(text):
    return mark_safe(str(text).translate(_html_escapes))
```

`str.translate(_html_escapes)` replaces each of the five HTML-significant code
points by its entity and leaves every other code point unchanged — a pure
per-code-point substitution with NO re-scan of emitted entities (`translate`
maps each input character independently). Hence it equals the
`@Pure` fold `escaped_seq` (with `entity`) in the `pure` region:

  `& → &amp;`, `< → &lt;`, `> → &gt;`, `" → &quot;`, `' → &#39;`, else identity.

At THIS base_commit the apostrophe maps to the legacy decimal `&#39;`
(`PSeq(38,35,51,57,59)`) — the `html.escape`/`&#x27;` switch (django-11276) is a
LATER commit and is irrelevant here. There is no `escape` axiom the proof
consumes; the deep model is validated equal to the real callee out-of-band by
axiom_check.py (G-AX). The escape operation is UNCHANGED by this patch — it is
the *flag controlling whether escape is applied* that the patch fixes — so the
escaper appears only as the A-reference G-AX validates the deep model against.
Reached at runtime via `render_value_in_context` (`base.py:970-973`):
`conditional_escape(value)` when `context.autoescape` is true, which for a plain
`str` value reduces to `escape(value)`.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`django.utils.html.escape` on boundary inputs over `& < > " '` (alone, doubled,
combined, mixed with text, the F2P `<script>` witness) plus randomized fuzz
strings, asserting `escaped_seq(s) == escape(s)` (deep model == real callee),
and confirms the verbatim branch is the identity (`str(value) == value`). It
imports only `django.utils.html`; exit 0 iff sound.
