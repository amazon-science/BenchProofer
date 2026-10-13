# mapping.md — django__django-11276

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 28d5262fa3315690395f04e3619ed554dbaf725b`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/utils/html.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `escape_codepoints(text)` | `escape(text)` — `django/utils/html.py:37` (body line 46) | the modeled changed function (HTML escaper) |
| `entity_decode(tok)` *(axiom — A-consumed)* | `html.unescape` — CPython stdlib `Lib/html/__init__.py` (called in `urlize` at `django/utils/html.py:295,332,334` post-patch) | unchanged community callee the patch switches `urlize`'s local decoder to |
| `entity(c)` | the per-character mapping in `str.translate(_html_escapes)` / `html.escape`'s `.replace` chain (`django/utils/html.py:27-33,46`) | pure spec: entity sequence for one code point |
| `escaped_seq(s)` *(deep model — A-reference)* | `html.escape` — CPython stdlib `Lib/html/__init__.py` (the whole-string escape `str(text).translate(...)` → `html.escape(str(text))`, called at `django/utils/html.py:46` post-patch) | pure spec: escape of a sequence; the deep model of the unchanged callee `html.escape`, validated `escaped_seq == html.escape` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `seq_amp/seq_lt/seq_gt/seq_quot/seq_apos_hex/seq_apos_dec` | the literal entity strings `&amp; &lt; &gt; &quot; &#x27; &#39;` | pure spec: entity tokens as code-point sequences |

The pre-patch repo symbols the change removes (for the refinement audit, not
referenced from the consumer spec view): the module-level dict `_html_escapes`
(`html.py:27-33`, with `ord("'"): '&#39;'`) and the nested `urlize.unescape`
helper (`html.py:262-269`, the `.replace('&amp;','&')…replace('&#39;',"'")`
chain).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `text`/`value` argument, and `escape`'s return) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `mark_safe(x)` wrapper (`html.py:46`) | identity (omitted) | `mark_safe` only sets the `SafeString` flag; it does not alter the character content the F2P tests observe (`test_escape` compares the rendered text). Modeled as the identity on code points. |
| `str(text)` coercion (`html.py:46`) | identity on the code-point list | the F2P inputs are already `str`; coercion is observationally the identity for them. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `escaped_seq` deep model ↔ `html.escape` (A-reference)
**Callee:** CPython `html.escape(s, quote=True)`. The changed escape operation
is modeled **deeply** by the `@Pure` fold `escaped_seq` (with `entity`) in the
`pure` region; there is **no `escape_html` axiom** the proof consumes. The deep
model is instead validated equal to the real callee out-of-band by
axiom_check.py (G-AX). Source (every supported 3.x, including the 3.6
interpreter in this instance's image):

```python
def escape(s, quote=True):
    s = s.replace("&", "&amp;")  # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
        s = s.replace('\'', "&#x27;")
    return s
```

Django calls it with the default `quote=True` (`mark_safe(html.escape(str(text)))`).
Because `&` is replaced **first**, the `&` that begins every emitted entity
(`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&#x27;`) is already past the `&`-pass and
is never re-escaped; the four later targets `< > " '` never occur inside an
already-emitted entity. Hence the chained `.replace` is exactly the
**per-code-point substitution**

  `& → &amp;`, `< → &lt;`, `> → &gt;`, `" → &quot;`, `' → &#x27;`, else identity,

which is what `escaped_seq` / `entity` encode; G-AX asserts
`escaped_seq(s) == html.escape(s)` (the deep model == the real callee) on
boundary + fuzz inputs. The apostrophe maps to the
**numeric character reference `&#x27;`** (`PSeq(38,35,120,50,55,59)`), not the
legacy `&#39;` — this is the single behavioural change the F2P `test_escape`
observes. Docs: https://docs.python.org/3/library/html.html#html.escape.

### 3.2 `entity_decode` ↔ `html.unescape` (A-consumed)
**Callee:** CPython `html.unescape(s)` — converts all named and numeric
character references to the corresponding Unicode characters per the HTML5
rules (`Lib/html/__init__.py`, `_charref.sub(_replace_charref, s)`). Docs:
https://docs.python.org/3/library/html.html#html.unescape.

The axiom encodes only the obligations the urlize site relies on: the six
entity tokens this benchmark emits/encounters decode to their single code
point —

  `&amp; → &`, `&lt; → <`, `&gt; → >`, `&quot; → "`, `&#x27; → '`, `&#39; → '`.

`html.unescape` decodes both the hexadecimal `&#x27;` and the decimal `&#39;`
numeric references to U+0027, and the four named references to their
characters — a superset of the old hand-rolled `urlize.unescape` (which knew
only `&amp; &lt; &gt; &quot; &#39;` and would leave the new `&#x27;` intact).
The axiom is the **weakest** contract the round-trip clause in
`escape_codepoints` needs (six single-token implications), not the full HTML5
decoder.

**Soundness check (G-AX):** `axiom_check.py` runs the real `html.escape` /
`html.unescape` on boundary inputs over `& < > " '` (alone, doubled, combined,
mixed with text and with already-escaped input) plus 20 000 randomized fuzz
strings. It asserts the deep model `escaped_seq` equals the real `html.escape`
(the A-reference, §3.1) and that every `html.unescape` observation equals the
`entity_decode` axiom's Ensures (the A-consumed callee, §3.2). Exit 0 iff sound.
It imports only the standard-library `html` module (the very module the patch
calls); nothing repo-specific.
