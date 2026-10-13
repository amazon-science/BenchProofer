# mapping.md — django__django-16877

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 98f6ada0e2058d67d91fb6c16482411ec2ca0967`, states the type
abstraction, and gives the provenance of the one kind-A reference (the deep
escape model, checked by G-AX).

Repo file under change: `django/template/defaultfilters.py` (the gold patch adds
one new filter function; it changes nothing else).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `escape_each(value)` | the new filter `escapeseq(value)` — `django/template/defaultfilters.py` (added after `escape_filter`, line 444) | the modeled new function: maps each item of the sequence through per-item escape-when-needed and returns a list |
| `escape_when_unsafe_item(item)` | `conditional_escape(obj)` — `django/utils/html.py:82` (called once per item by the list comprehension `[conditional_escape(obj) for obj in value]`) | the per-item transform: escape an item unless it is already marked safe; under specification (its contract is used by `escape_each`), NOT an axiom |
| `escape_codepoints(text)` / `escaped_seq(s)` *(deep model — A-reference)* | `html.escape` — CPython stdlib `Lib/html/__init__.py`, reached via `conditional_escape` → `escape` (`django/utils/html.py:18`, `SafeString(html.escape(str(text)))`) | pure spec: the per-code-point HTML escape of an unsafe item's content; deep model of the unchanged stdlib escaper, validated `escaped_seq == html.escape` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `Elem(chars, is_safe)` | one item of the input sequence (any `str`/`SafeString`/lazy/`__html__`-bearing object) | minimal carrier of the two touched aspects: character content and the "already marked safe" flag |
| `entity(c)` | the per-character mapping inside `html.escape`'s `.replace` chain | pure spec: entity sequence for one code point |
| `seq_amp/seq_lt/seq_gt/seq_quot/seq_apos_hex` | the literal entity strings `&amp; &lt; &gt; &quot; &#x27;` | pure spec: entity tokens as code-point sequences |

The gold patch (`escapeseq`) is **purely additive** — it removes nothing. The
analogous existing filter for comparison (not changed) is `safeseq`
(`defaultfilters.py:492`, `[mark_safe(obj) for obj in value]`); `escapeseq` is
its escape-counterpart, using `conditional_escape` instead of `mark_safe`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an item `str` (and the escaped result `SafeString`) | `Elem.chars : PSeq[int]` of Unicode code points | `s[k]` ↔ `chars[k] == ord(s[k])`; `len(s)` ↔ `len(chars)`; `str` concatenation ↔ `PSeq` `+`; empty `str` ↔ empty `PSeq` |
| "the item exposes `__html__` / is a `SafeData`" (the predicate `conditional_escape` branches on: `isinstance(text, Promise)` then `hasattr(text, "__html__")`) | `Elem.is_safe : bool` | `True` ⟺ the item is already a safe string (has `__html__`) and `conditional_escape` returns it unchanged; `False` ⟺ a plain string `conditional_escape` escapes |
| the input list `value` | `List[Elem]` | `value[k]` ↔ the k-th item; `len(value)` preserved; order preserved |
| the comprehension result `[...]` (a plain Python `list`) | `List[Elem]` (a fresh, fully-owned list) | one output item per input item, in order |
| `SafeString(html.escape(str(text)))` wrapper (`escape`, the unsafe branch) | identity on code points + `is_safe := True` | `SafeString`/`mark_safe` only set the safety flag; they do not alter character content the F2P tests observe (the tests compare the rendered text after `join`). Modeled as: result `chars` = escaped content, result `is_safe` = `True`. |
| `str(text)` coercion inside `escape` | identity on the code-point list | the F2P item inputs are already `str`; coercion is observationally the identity for them. |

`str` indexing/iteration is banned in Nagini, so item content is `PSeq[int]`;
the per-element specification is carried by `Forall` over the list with explicit
in-bounds guards.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `escaped_seq` deep model ↔ `html.escape` (A-reference)
**Callee:** CPython `html.escape(s, quote=True)`, reached through
`conditional_escape(obj)` → (obj not safe) → `escape(obj)` →
`SafeString(html.escape(str(obj)))` (`django/utils/html.py:18,82`). The escape
operation of an *unsafe* item is modeled **deeply** by the `@Pure` fold
`escaped_seq` (with `entity`) in the `pure` region and the verified loop
`escape_codepoints`; there is **no `escape_html` axiom** the proof consumes. The
deep model is validated equal to the real callee out-of-band by axiom_check.py
(G-AX). Source (every supported 3.x, incl. the 3.x interpreter in this image):

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

Because `&` is replaced **first**, the `&` that begins every emitted entity is
already past the `&`-pass and is never re-escaped, and the four later targets
`< > " '` never occur inside an already-emitted entity. Hence the chained
`.replace` is exactly the **per-code-point substitution**

  `& → &amp;`, `< → &lt;`, `> → &gt;`, `" → &quot;`, `' → &#x27;`, else identity,

which is what `escaped_seq` / `entity` encode. The apostrophe maps to the
numeric character reference `&#x27;` (`PSeq(38,35,120,50,55,59)`). Django relies
on the CPython default `quote=True` (it calls `html.escape(str(text))` with no
flag). Docs: https://docs.python.org/3/library/html.html#html.escape.

### 3.2 The conditional (`is_safe`) branch ↔ `conditional_escape` (R + A-reference cross-check)
`conditional_escape` (`django/utils/html.py:82`) is:

```python
def conditional_escape(text):
    if isinstance(text, Promise):
        text = str(text)
    if hasattr(text, "__html__"):
        return text.__html__()
    else:
        return escape(text)
```

The `__html__` branch returns the item **unchanged** (a `SafeData`/`SafeString`
returns itself); the `else` branch escapes via §3.1. This two-branch contract is
modeled by `escape_when_unsafe_item` (`is_safe` ⇒ passthrough; not `is_safe` ⇒
`escaped_seq`). It is NOT a consumed axiom — it is spelled out and used directly
by `escape_each`. axiom_check.py cross-checks both branches against
`conditional_escape`'s observable contract (and the real
`django.utils.html.conditional_escape` when importable in-container).

**Soundness check (G-AX):** `axiom_check.py` runs the real `html.escape` and a
faithful re-implementation of `conditional_escape`'s `__html__` convention on 23
boundary inputs over `& < > " '` (alone, doubled, combined, mixed with text and
with already-escaped input) plus 20 000 randomized fuzz strings; it asserts the
deep model `escaped_seq` equals the real `html.escape` (unsafe branch) and that
an already-safe item is returned unchanged (safe branch). When the real Django
callee is importable it is exercised too. Exit 0 iff every obligation holds.
It imports only the standard-library `html` module; nothing repo-specific.
