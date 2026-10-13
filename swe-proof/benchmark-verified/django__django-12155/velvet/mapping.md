# mapping.md — django__django-12155

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e8fcdaad5c428878d0a5d6ba820d957013f75595`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo files under change: `django/contrib/admindocs/utils.py` and
`django/contrib/admindocs/views.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalizeIndentation (text : List Char)` | the docstring-indentation normalization applied inside `parse_docstring(docstring)` — `django/contrib/admindocs/utils.py:42` (the `docstring = …` step at line 46) | the modeled changed behavior (docstring indent normalization) |
| `cleanDocModel (text : List Char)` *(deep model — A-reference)* | `inspect.cleandoc` — CPython stdlib `Lib/inspect.py` (called post-patch at `django/contrib/admindocs/utils.py:46` and `django/contrib/admindocs/views.py:260`) | pure spec: the post-patch normalization; deep model of the unchanged stdlib callee `inspect.cleandoc`, validated `cleanDocModel == inspect.cleandoc` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `splitLines`, `commonIndent`, `dedentLines`, `dropLeadingBlank`, `dropTrailingBlank`, `joinNL`, `leadingSpaces`, `stripLeadingSpaces`, `hasContent` | the constituent steps of `inspect.cleandoc` (`Lib/inspect.py`: `split('\n')`, the margin loop over `lines[1:]`, `lstrip` / `[margin:]`, the trailing/leading blank `pop`, `'\n'.join`) | pure spec building blocks of the deep model |

The pre-patch repo symbol the change removes (refinement audit only, not in the
consumer spec view): the helper `trim_docstring` (`utils.py:28-39`), whose
`indent = min(len(line) - len(line.lstrip()) for line in lines if line.lstrip())`
took the common indentation over **all** lines including the first.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the `docstring` argument and the normalized return) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`; `'\n'` ↔ `'\n'` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `str.split('\n')` | `splitLines` | Python `s.split('\n')` ↔ `splitLines s.toList`; both always yield ≥1 segment (empty str ↔ `[[]]`) |
| `line.lstrip()` (with leading whitespace == spaces, see §2.1) | `stripLeadingSpaces` | leading-space removal; `len(line) - len(line.lstrip())` ↔ `leadingSpaces line` |
| `'\n'.join(lines)` | `joinNL` | segment rejoin with the newline separator |

### 2.1 Domain restriction (recorded for G-AX / G-CONF fuzzing)
`inspect.cleandoc` first calls `doc.expandtabs()`, which converts tabs to spaces,
then operates on `'\n'`-separated lines and treats a line as blank/indented using
`str.lstrip()` (all Unicode whitespace). The F2P-relevant inputs (Python
docstrings after tab expansion) contain **no tab/`\r`/`\v`/`\f`** and use the
**space** character for indentation. The deep model `cleanDocModel` therefore
models the post-`expandtabs` domain where the only whitespace used for
indentation is the ASCII space `' '` and the only line separator is `'\n'`.
axiom_check.py fuzzes over this domain (space + newline + ordinary printables);
G-CONF uses the same domain. Inputs outside it (raw tabs, `\r`, other Unicode
spaces) are out of the modeled domain and are not claimed.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `cleanDocModel` deep model ↔ `inspect.cleandoc` (A-reference)
**Callee:** CPython `inspect.cleandoc(doc)`. The changed normalization operation
is modeled **deeply** by `cleanDocModel` (with `splitLines` / `commonIndent` /
`dedentLines` / `dropLeadingBlank` / `dropTrailingBlank` / `joinNL`) in the
`pure` region; there is **no `cleandoc` axiom** the proof consumes. Source (every
supported 3.x incl. the interpreter in this image):

```python
def cleandoc(doc):
    lines = doc.expandtabs().split('\n')
    margin = sys.maxsize
    for line in lines[1:]:
        content = len(line.lstrip())
        if content:
            indent = len(line) - content
            margin = min(margin, indent)
    if lines:
        lines[0] = lines[0].lstrip()
    if margin < sys.maxsize:
        for i in range(1, len(lines)): lines[i] = lines[i][margin:]
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return '\n'.join(lines)
```

The margin is computed over `lines[1:]` (lines AFTER the first) — this is the
behavioral fix: the pre-patch `trim_docstring` took the min over **all** lines,
so a first line at column 0 forced the margin to 0 and the body was never
dedented (the issue). `commonIndent (lines.drop 1)` encodes the `lines[1:]`
restriction; `dedentLines` always `lstrip`s the first line and removes `margin`
chars from the rest (or leaves them when no content line exists, the
`margin == sys.maxsize` / `none` branch); `dropTrailingBlank`/`dropLeadingBlank`
encode the two `pop` loops. Docs: https://docs.python.org/3/library/inspect.html#inspect.cleandoc.

**Soundness check (G-AX):** `axiom_check.py` runs the real `inspect.cleandoc` on
boundary inputs (empty, first-line-at-col-0 vs indented-first-line, all-blank,
trailing/leading blank runs, mixed indentation) plus 200 000 randomized fuzz
strings over the modeled domain (space + newline + ordinary chars), asserting
`cleanDocModel == real inspect.cleandoc`. Imports only stdlib `inspect`. Exit 0
iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12155`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `splitLines`/`commonIndent`/`dedentLines`/`dropLeadingBlank`/
`dropTrailingBlank`/`joinNL` (all R/I-tagged ops) to Python and diffs against
`patch.diff` behaviour (the patched `parse_docstring`, observed via its returned
`(title, body, metadata)`) over the modeled domain. There are no A-tagged
callees in the impl region (the deep model is all R/I), so the shadow is pure
R/I.
