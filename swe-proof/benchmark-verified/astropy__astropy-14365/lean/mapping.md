# mapping.md — astropy__astropy-14365

## Symbol binding (file:line @ base_commit 7269fa3e)

Two independently-fixed behaviors, both in `astropy/io/ascii/qdp.py`.

### Behavior 1 — line classification is case-insensitive
Modeled function: `_line_type(line, delimiter=None)`
- File: `astropy/io/ascii/qdp.py`, `def _line_type` at line 19 @ base_commit.
- Gold-patch edit (line 71 of file): `_line_type_re = re.compile(_type_re)`
  → `re.compile(_type_re, re.IGNORECASE)`.
- The function builds a regex (`_type_re`) recognizing the textual line
  categories of the format (a command line `READ [TS]ERR ...`, a "new-table"
  marker line, a numeric data line possibly with a trailing comment, or a pure
  comment), matches the stripped line against it, and returns the category name
  (`"command" | "new" | "data,<ncol>" | "comment"`) or raises `ValueError`
  ("Unrecognized QDP line") when nothing matches.
- The edit makes the match **case-insensitive**. Empirically the patched matcher
  is *case-invariant*: classification of a line equals classification of every
  case-variant of that line (verified, 200k fuzz, 0 mismatches). NB this is NOT
  the same as case-sensitive matching on the upper-cased line — the pattern mixes
  upper-case literals (`READ`, `SERR`, `NO`) with a lower-case literal (`nan`), so
  an upper-fold breaks `nan` recognition (14k mismatches). It IS modeled by the
  matcher's own case-insensitive mode.

### Behavior 2 — masked-value sentinel detection is case-insensitive
Modeled function: the per-token value loop in
`_get_tables_from_qdp_file(qdp_file, input_colnames=None, delimiter=None)`
- File: `astropy/io/ascii/qdp.py`, `def _get_tables_from_qdp_file` at line ~218;
  the edited loop is at lines 306–314 @ base_commit.
- Gold-patch edit (line 308): `if v == "NO":` → `if v.upper() == "NO":`.
- The loop splits a data line into whitespace/`delimiter`-separated tokens and,
  per token `v`, appends `np.ma.masked` if `v` is the masked sentinel, otherwise
  the parsed number (`int(v)`, falling back to `float(v)`).
- The edit makes the sentinel test **case-insensitive**: a lower-case `no` token
  is the masked sentinel too (previously it fell through to number parsing and
  crashed).

## Lean ↔ Python type bijection (G-CONF / G-AX use this)

| Lean | Python |
|---|---|
| `line : List Char` | a single file line `line : str` (per-character; ASCII) |
| `LineCategory` (`comment`/`command`/`newBlock`/`data n`/`unrecognized`) | the classification result of `_line_type`: the returned category string, with `unrecognized` ↔ the `ValueError("Unrecognized QDP line")` branch; `newBlock` ↔ `"new"`; `data n` ↔ `"data,<n>"` |
| `matchCategory : Bool → List Char → LineCategory` (opaque) | the regex matcher of `_line_type`; the `Bool` selects case-insensitive matching (`re.IGNORECASE` set vs not). Post-fix = `matchCategory true`; pre-fix = `matchCategory false`. |
| `l.map Char.toUpper = v.map Char.toUpper` | `l` and `v` are equal up to ASCII letter-case |
| `tok : List Char` | one split token `v : str` of a data line |
| `NumVal` (opaque) + `parseNumber : List Char → NumVal` (opaque) | the unchanged number parser `int(v)`-then-`float(v)`; `NumVal` ↔ the resulting Python number object |
| `Cell` (`missing`/`number NumVal`) | one parsed cell: `np.ma.masked` vs a number |
| `isSentinel tok := tok.map Char.toUpper = ['N','O']` | `v.upper() == "NO"` (the fixed sentinel test) |
| `tokens.map cellOfToken` | the `values` list built by the loop |

## Callee provenance + flag deps

- `matchCategory` — **A-reference** (Behavior 1).
  Models the UNCHANGED regex matcher of `_line_type`; the patch only SELECTS its
  case-insensitive mode (the `Bool` argument `true`), it does not change the
  matcher/pattern. The spec pins `result = matchCategory true line` (and the
  prepatch's `matchCategory false line` fails it — the G-DIFF discriminator), so
  `correct_classify` closes by `rfl` and consumes **no** property axiom. The
  soundness-critical SEMANTIC property of the A-reference — **case-invariance of
  the case-insensitive mode** (`∀ l v, l.map toUpper = v.map toUpper →
  matchCategory true l = matchCategory true v`, and acceptance of the lower-case
  `read serr` / `no no` / `1 nan` lines the issue reports) — is validated by G-AX
  (`axiom_check.py`) against the real `re.IGNORECASE` matcher, NOT asserted as a
  Lean axiom. The pre-fix mode is not case-invariant; that is exactly the bug.
- `parseNumber` — **A-reference** (Behavior 2). Models the UNCHANGED number
  parser (`int(v)` else `float(v)`). The fix does not touch it; the spec only
  states a non-sentinel token maps to `number (parseNumber tok)`. No property
  axiom is consumed about its value. Flag dep: none.

## Pinned G-CONF fuzz seed
`conf_seed = 20240629`. Behavior 2 carries the R/I content (the `isSentinel`
decision + list structure); `parseNumber` is left as the real repo parser in the
Python R/I shadow. Behavior 1's impl op (`matchCategory true`) is all-A, validated
by G-AX, so it contributes no R/I leg.
