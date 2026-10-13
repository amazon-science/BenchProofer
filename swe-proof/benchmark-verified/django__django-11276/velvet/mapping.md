# mapping.md — django__django-11276

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 28d5262fa3315690395f04e3619ed554dbaf725b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `django/utils/html.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `escapeCodepoints (text : List Char)` | `escape(text)` — `django/utils/html.py:37` (body line 46) | the modeled changed function (HTML escaper) |
| `entityDecode` *(axiom — A-consumed)* | `html.unescape` — CPython stdlib `Lib/html/__init__.py` (called in `urlize` post-patch at `django/utils/html.py:295,332,334`) | unchanged community callee `urlize`'s local decoder is switched to |
| `entity (c : Char)` | the per-character mapping `html.escape`'s `.replace` chain implements (`django/utils/html.py:46` post-patch) | pure spec: entity sequence for one code point |
| `escapedSeq (s : List Char)` *(deep model — A-reference)* | `html.escape` — CPython stdlib `Lib/html/__init__.py` (`html.escape(str(text))`, `django/utils/html.py:46` post-patch) | pure spec: escape of a sequence; deep model of the unchanged callee `html.escape`, validated `escapedSeq == html.escape` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo symbols the change removes (refinement audit only, not in the
consumer spec view): module dict `_html_escapes` (`html.py:27-33`, with
`ord("'"): '&#39;'`) and the nested `urlize.unescape` helper (`html.py:262-269`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the `text`/`value` argument, and `escape`'s return) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `mark_safe(x)` wrapper (`html.py:46`) | identity (omitted) | `mark_safe` only sets the `SafeString` flag; it does not alter character content the F2P `test_escape` observes. Identity on `List Char`. |
| `str(text)` coercion (`html.py:46`) | identity on the `List Char` | F2P inputs are already `str`; coercion is observationally the identity. |

Lean `String`/`List Char` indexing is total and sound (no Nagini `List[int]`
workaround needed); the carrier is `List Char` because the operation is
per-code-point.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `escapedSeq` deep model ↔ `html.escape` (A-reference)
**Callee:** CPython `html.escape(s, quote=True)`. The changed escape operation
is modeled **deeply** by `escapedSeq` (with `entity`) in the `pure` region;
there is **no `escapeHtml` axiom** the proof consumes. Source (every supported
3.x incl. the 3.6 interpreter in this image):

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
Because `&` is replaced **first**, the `&` beginning every emitted entity is
never re-escaped, and the four later targets `< > " '` never occur inside an
already-emitted entity. Hence the chained `.replace` is exactly the
per-code-point substitution `& → &amp;`, `< → &lt;`, `> → &gt;`, `" → &quot;`,
`' → &#x27;`, else identity — which is what `escapedSeq`/`entity` encode. The
apostrophe maps to the **numeric character reference `&#x27;`** (`entity '\''
= "&#x27;".toList`), not the legacy `&#39;` — the single behavioural change the
F2P `test_escape` observes. Docs: https://docs.python.org/3/library/html.html#html.escape.

### 3.2 `entityDecode` ↔ `html.unescape` (A-consumed)
**Callee:** CPython `html.unescape(s)`. The axioms encode only the obligations
the urlize site relies on: the five emitted entity tokens decode to their single
code point — `&amp; → &`, `&lt; → <`, `&gt; → >`, `&quot; → "`, `&#x27; → '`.
The Lean axioms (`entityDecode_amp` … `entityDecode_apos`) are the **weakest**
contract the round-trip postconditions need, not the full HTML5 decoder.

**Soundness check (G-AX):** `axiom_check.py` runs the real `html.escape` /
`html.unescape` on boundary inputs over `& < > " '` (alone, doubled, combined,
mixed) plus 20 000 randomized fuzz strings, asserting (a) `escapedSeq == real
html.escape` (A-reference) and (b) every `html.unescape` observation matches the
`entityDecode_*` axioms (A-consumed). Imports only stdlib `html`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` and `hypothesis` derandomize
with **`11276`** so the consumer-side verdict (§11.3) is reproducible. The R/I
shadow it builds transliterates `entity`/`escapedSeq` (R/I-tagged ops) to Python
and leaves `entityDecode`'s callee as the real `html.unescape` (A-tagged → run
real callee, not the axiom model).
