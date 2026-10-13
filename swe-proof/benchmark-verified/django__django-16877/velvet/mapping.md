# mapping.md — django__django-16877

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 98f6ada0e2058d67d91fb6c16482411ec2ca0967`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep-model reference.

Repo file under change: `django/template/defaultfilters.py` (the patch ADDS a new
filter function; no existing function is edited).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `escapeEach (items : List Elem)` | the added filter `escapeseq(value)` — `django/template/defaultfilters.py:447` (body `[conditional_escape(obj) for obj in value]`, line 454 post-patch) | the modeled added function: per-element conditional escape over a sequence |
| `condEscape (e : Elem)` *(deep model — A-reference)* | `conditional_escape` — `django/utils/html.py:82` | pure spec: the per-element transformation the comprehension applies; deep model of the UNCHANGED callee `conditional_escape`, validated `condEscape == conditional_escape` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `escapedSeq (s : List Char)` *(deep model, sub-model of `condEscape`)* | `html.escape(str(text))` inside `django.utils.html.escape` — `django/utils/html.py:18,27` | pure spec: the per-code-point HTML escape applied to a non-safe element |
| `entity (c : Char)` | the per-character expansion `html.escape` performs (`&<>"'`) | pure spec: entity sequence for one code point |
| `escSeq (xs : List Elem)` | the list comprehension `[conditional_escape(obj) for obj in value]` (`defaultfilters.py:454` post-patch) | pure spec: escape of a whole sequence, element-wise, order-preserving |
| `Elem` (`chars : List Char`, `safe : Bool`) | one element `obj` of the input `value` | structure carrying only the two observable facts (§2) |

No symbol is removed by this patch; it is additions-only (a new `@register.filter`
function `escapeseq`). There is no urlize/decode site here, so there are NO
consumed axioms and the `axioms` region is empty.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the input sequence `value` (an iterable of elements) | `List Elem` | `value` ↔ list of `Elem`, order-preserving; `len(value)` ↔ `items.length`; empty iterable ↔ `[]` |
| one element `obj` of `value` | `Elem` | `obj` ↔ `⟨chars, safe⟩` where `chars = list(str(obj))` code points and `safe = hasattr(obj, "__html__")` (i.e. `obj` is `SafeData`/`mark_safe`-wrapped). These are the only facts `conditional_escape` observes about `obj` (it returns `obj.__html__()` if safe, else `escape(str(obj))`). |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `str` (an element's text, and an escaped result) | `List Char` | `s` ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| `conditional_escape(obj)` return | `List Char` (one entry of the output list) | the escaped/passthrough text's code points |
| the comprehension's result list | `List (List Char)` | the list of per-element results, in order |
| `SafeString`/`mark_safe` wrapper on a result | identity (omitted) | `mark_safe`/`SafeString` only set the safe flag; they do not alter the character content the F2P tests observe (the tests compare the rendered string after `join`). Identity on `List Char`. |
| `str(obj)` coercion inside `escape` | identity on the `List Char` | the F2P inputs are already `str` (or `SafeString`, a `str` subclass); coercion is observationally the identity on content. |

Lean `String`/`List Char` indexing is total and sound; the carrier for an
element's content is `List Char` because escaping is per-code-point. The element's
*safety* is the single extra observable bit, carried by `Elem.safe`.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `condEscape` deep model ↔ `conditional_escape` (A-reference)
**Callee:** `django.utils.html.conditional_escape(text)` (`django/utils/html.py:82`),
UNCHANGED by this patch. Source at base_commit:

```python
def conditional_escape(text):
    if isinstance(text, Promise):
        text = str(text)
    if hasattr(text, "__html__"):
        return text.__html__()
    else:
        return escape(text)
```

where `escape(text)` is `SafeString(html.escape(str(text)))` (`html.py:18`). For a
`SafeData`/`mark_safe`-wrapped element, `__html__()` returns the element unchanged
(content-wise); for any other element, `html.escape(str(text))` is applied. This is
exactly `condEscape ⟨chars, safe⟩ = if safe then chars else escapedSeq chars`. The
`Promise` branch only forces lazy strings to `str` and does not change content, so
it is the identity on the `List Char` carrier (mapping.md §2).

### 3.2 `escapedSeq` sub-model ↔ `html.escape` (A-reference, inside §3.1)
**Callee:** CPython `html.escape(s, quote=True)`. Source (every supported 3.x):

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

Django's `escape` calls it with the default `quote=True`. Because `&` is replaced
**first**, the `&` beginning every emitted entity is never re-escaped, and the
four later targets `< > " '` never occur inside an already-emitted entity. Hence
the chained `.replace` is exactly the per-code-point substitution
`& → &amp;`, `< → &lt;`, `> → &gt;`, `" → &quot;`, `' → &#x27;`, else identity —
which is what `escapedSeq`/`entity` encode. The apostrophe maps to the numeric
character reference `&#x27;`. Docs: https://docs.python.org/3/library/html.html#html.escape.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`django.utils.html.conditional_escape` (and, beneath it, `html.escape`) on boundary
inputs (safe and non-safe elements over `& < > " '`, alone/doubled/combined/mixed)
plus 20 000 randomized fuzz strings in both safe and non-safe flavours, asserting
`condEscape == conditional_escape` (and `escapedSeq == html.escape`). Exit 0 iff
sound. There are NO consumed axioms to check.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16877`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `escSeq`/`condEscape`/`escapedSeq` (the R/I-tagged list-building
ops) to Python and compares against `patch.diff`'s behaviour — the real added
`escapeseq` filter applied at base_commit+patch — over both safe and non-safe
elements. There are no A-tagged callees left un-transliterated in the impl region
(no consumed axioms), so the whole impl is R/I and `conf_skip = false`.
