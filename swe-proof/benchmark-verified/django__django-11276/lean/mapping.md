# mapping.md — django__django-11276

Base commit: `28d5262fa3315690395f04e3619ed554dbaf725b`
Spec provenance: **cold** (derived only from problem_statement + gold patch +
repo source at base_commit).

## Symbol binding

| Lean symbol | Python | file:line @ base_commit |
|---|---|---|
| `implementation_escape` / `problem_spec_escape` / `correct_escape` | `escape(text)` | `django/utils/html.py:37` (body at `:46`), the module-level `_html_escapes` table at `:27-33` |

The modeled function is `escape(text)`. At base_commit its body is
`mark_safe(str(text).translate(_html_escapes))`, where `_html_escapes` is the
per-code-point translation table

```python
_html_escapes = {
    ord('&'): '&amp;', ord('<'): '&lt;', ord('>'): '&gt;',
    ord('"'): '&quot;', ord("'"): '&#39;',
}
```

The gold patch deletes this table and rewrites the body to
`mark_safe(html.escape(str(text)))`, i.e. it delegates to the Python standard
library escaper (called with its default `quote=True`).

## Lean ↔ Python type bijection

| Python | Lean | notes |
|---|---|---|
| `str` argument `str(text)` | `List Char` | per-code-point op; Lean `Char` = Unicode scalar value, matching Python `str` iteration which yields one code point per element. `str.translate` maps code point → replacement, exactly a per-`Char` map. |
| result `str` (wrapped in `mark_safe`) | `List Char` | `mark_safe` only tags the string `SafeString`; it does not alter the character sequence, so it is outside the modeled boundary (identity on the char list). |
| `str.translate(table)` / `html.escape(·)` | `escapeSeq : List Char → List Char` (in-order concatenation of `escapeChar`) | deep model; see below. |

`str(text)` (the coercion of an arbitrary object to its string form) is upstream
of the modeled boundary: the spec's domain is the already-stringified text, as
a `List Char`. `mark_safe` is downstream and character-preserving. Both are
identity on the char sequence and are not modeled as callees.

## Callee provenance

`html.escape` (stdlib, Python ≥ 3.2, default `quote=True`) is the only callee the
post-patch body introduces. It is **not** declared as an `opaque`/`axiom` callee:
it is modeled DEEPLY as `escapeChar`/`escapeSeq` (an A-reference — see
refinement.md), because it IS the operation the patch changes and §0.7 forbids
axiomatizing the changed op.

### `html.escape` semantics (default `quote=True`), validated
`html.escape(s, quote=True)` performs exactly these ordered replacements over the
whole string:

```
&  -> &amp;    (done first, so later insertions of '&' are not re-touched)
<  -> &lt;
>  -> &gt;
"  -> &quot;
'  -> &#x27;
```

Because `&` is replaced first and the replacement texts introduce no `<`, `>`,
`"`, or `'`, the whole-string `.replace()` chain is observationally identical to
a single left-to-right per-code-point map. This equivalence is checked
mechanically in `conformance_check.py` over the real `html.escape` and in
`axiom_check.py` (>10^5 fuzzed inputs + boundary set). `escapeChar` encodes that
per-code-point map; `escapeSeq` is its in-order concatenation.

### Flag dependency
`html.escape` only performs the `"`→`&quot;` and `'`→`&#x27;` substitutions under
`quote=True`. Django calls it with the default (`quote=True`), so all five
substitutions apply. `axiom_check.py` and `conformance_check.py` drive
`html.escape(s)` (default), matching the call site.

## The observable change (pre-patch vs post-patch)
Only ONE code point's encoding changes: the apostrophe `'` maps to `&#x27;`
post-patch, where it mapped to `&#39;` pre-patch. The other four substitutions
(`&`, `<`, `>`, `"`) are byte-identical across the patch. This is the single
discriminating clause the prepatch violates (G-DIFF), and it is exactly the
behavioral change the FAIL_TO_PASS tests assert (`&#39;` → `&#x27;`).

## G-CONF fuzz seed
Pinned seed: **11276** (also in `conformance_check.py`).
