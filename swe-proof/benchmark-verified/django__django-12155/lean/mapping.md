# mapping.md — django__django-12155

## Symbol binding (file:line @ base_commit e8fcdaad5c)

- Patched site A: `django/contrib/admindocs/utils.py`
  - `trim_docstring(docstring)` — lines 27–39 @ base_commit (REMOVED by the
    patch); the hand-rolled PEP 257 de-indent routine. Its margin line (37):
    `indent = min(len(line) - len(line.lstrip()) for line in lines if line.lstrip())`
    measures the common indent over ALL non-blank lines (the bug).
  - `parse_docstring(docstring)` — lines 42–65 @ base_commit; call site changed
    from `docstring = trim_docstring(docstring)` (line 46) to an early
    `if not docstring: return '', '', {}` guard plus `docstring = cleandoc(docstring)`.
- Patched site B: `django/contrib/admindocs/views.py` — `get_context_data`,
  line ~259 @ base_commit: `utils.parse_rst(utils.trim_docstring(verbose), …)`
  → `utils.parse_rst(cleandoc(verbose), …)`. Same callee substitution; no new
  behavior beyond site A's, so a single modeled function covers both.

The patch's net behavior change is: the docstring de-indentation now follows the
standard PEP 257 algorithm (`inspect.cleandoc`) instead of the buggy custom one.
That normalization is the MODELED function `normalizeIndent`.

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

| Python | Lean |
|---|---|
| docstring `str` `s` | `lines : List (List Char)` via `s.expandtabs().split('\n')`, each line `List Char` |
| `inspect.cleandoc(s)` (return `str`) | `'\n'.join` of `implementation_normalizeIndent lines` |
| `c.isspace()` (whitespace code point) | `isSpaceChar c` = `whitespaceCodes.contains c.toNat` |
| `len(line) - len(line.lstrip())` | `leadingWs line` |
| `line.lstrip()` | `lstripWs line` |
| all-whitespace (`not line.lstrip()`) line | `isBlank line` |
| `line[margin:]` | `line.drop margin` |
| `min(...)` over lines / `None` sentinel | `marginSpec` returning `Option Nat` |
| trailing/leading `''` line removal | `dropTrailingEmpty` / `dropLeadingEmpty` (empty == `[]`) |

Note: `inspect.cleandoc` itself does `expandtabs()` and splits on `'\n'`; the
bridge therefore expands tabs and splits BEFORE handing the line-list to the
model, and rejoins after. **`str.lstrip()` (and the `not line` blank test) act on
the FULL whitespace set** — everything `str.isspace()` recognizes: space, the
ASCII controls `\t \n \r \v \f`, the ASCII separators U+001C–U+001F, U+0085,
NBSP, and the Unicode space separators (U+1680, U+2000–U+200A, U+2028/U+2029,
U+202F, U+205F, U+3000). `expandtabs()` expands ONLY `\t`; every other whitespace
character survives into the line list and must still be treated as whitespace.
The Lean model captures exactly this set in `whitespaceCodes` (29 code points)
and uses it for `leadingWs`/`lstripWs`/`isBlank`. `conformance_check.py`'s fuzz
alphabet therefore includes non-space whitespace (`\r \f \v \xa0`, a separator)
so real reachable inputs (CRLF docstrings, form-feed page breaks, NBSP-led lines)
are exercised and shown to agree with real `cleandoc`. This corrects a prior
audit's Role-3 faithfulness defect (the earlier model stripped ASCII space only).

## Callee provenance + flag deps

- Consumed callee axioms: NONE. The normalization is modeled deeply
  (A-reference), validated == real `inspect.cleandoc` by G-CONF.
- `inspect.cleandoc` is the real post-patch callee (stdlib, unchanged); it is the
  ORACLE in `conformance_check.py`, not an axiom.
- No flag-dependent callees.

## G-CONF fuzz seed

Pinned seed: **20240629** (matches `conformance_check.py` `SEED`). N = 120_000
random inputs (wide alphabet incl. non-space whitespace) + 20 enumerated edge
cases (incl. CRLF / form-feed / NBSP / vertical-tab / ASCII-separator inputs).
