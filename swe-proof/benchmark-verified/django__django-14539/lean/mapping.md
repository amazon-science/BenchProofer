# mapping.md — django__django-14539

## Symbol binding (file:line @ base_commit `6a5ef557f8`)

| Lean | Python | location |
|---|---|---|
| `implementation_peelTrailingPunct` / `problem_spec_peelTrailingPunct` / `correct_peelTrailingPunct` | the trailing-punctuation peel block of the `trim_punctuation` closure inside `urlize` | `django/utils/html.py:281-287` (edited hunk `@@ -283,8 +283,9 @@`) |
| `decode` (opaque) | `html.unescape` (stdlib `html` module) | `django/utils/html.py:284` (`import html` at line 3) |
| `rstripPunct` | `str.rstrip(TRAILING_PUNCTUATION_CHARS)` | `django/utils/html.py:285` |
| `TRAILING_PUNCT` | `TRAILING_PUNCTUATION_CHARS = '.,:;!'` | `django/utils/html.py:19` |
| `token` | `middle` (local var of `trim_punctuation`) | — |
| `tailPunct` | `trail` (local var of `trim_punctuation`) | — |
| 3rd result `Bool` | `trimmed_something` | `django/utils/html.py:286` |

The modeled operation is one application of the trailing-punctuation block (the
patched hunk). The surrounding `while trimmed_something` loop, the
wrapping-punctuation block, and `lead` handling are unchanged by the patch and
are outside the modeled function (frame: the hunk rewrites only the `trail` and
`middle` assignments).

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

| Lean | Python | notes |
|---|---|---|
| `List Char` | `str` | per-code-point; Lean indexing total |
| `xs.length` | `len(s)` | |
| `rstripPunct cs` | `s.rstrip('.,:;!')` | drop maximal trailing-punct suffix |
| `takeRightN cs n` = `cs.drop (cs.length - n)` | `s[-n:]` | for `1 ≤ n ≤ len` |
| `dropRightN cs n` = `cs.take (cs.length - n)` | `s[:-n]` | for `1 ≤ n ≤ len` |
| `decode token` | `html.unescape(middle)` | A-reference |
| `decide (decoded ≠ stripped)` | `middle_unescaped != stripped` | |

Edge of the slice analogy: `s[-0:]` is the WHOLE string and `s[:-0]` is `""` in
Python, but inside the guarded `if` the count is always `≥ 1`, where
`takeRightN/dropRightN` match Python exactly. G-CONF tests both branches.

## Callee provenance + flag deps

- `html.unescape` (CPython stdlib `html.__init__.unescape`): pure, total, never
  raises on `str` input; **decoding never lengthens the string** (entities are
  replaced by ≤ their literal length; non-entities pass through). No flag
  dependency. The proof consumes no property of it (A-reference, not consumed);
  G-CONF exercises its real behaviour.
- `TRAILING_PUNCTUATION_CHARS = '.,:;!'` — module constant, unchanged by patch.

## G-CONF fuzz seed

`SEED = 20210619` (instance `created_at` date). `N_RANDOM = 120_000` (≥ 1e5),
plus a 12-entry discrete catalogue including the issue's exact trigger token
`google.com/?q=1&lt!` and several entity variants.
