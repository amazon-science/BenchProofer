# mapping.md — sphinx-doc__sphinx-9230

## Modeled function

| Lean | Python | file:line @ base_commit `567ff22716` |
|---|---|---|
| `implementation_paramField` / `problem_spec_paramField` / `correct_paramField` | the `:param type name:` decomposition inside `DocFieldTransformer.transform` — split a field-argument string into its type part and its name part | `sphinx/util/docfields.py:298-307` (the `try: argtype, argname = fieldarg.<split>(None, 1)` block; post-patch uses the last-whitespace split) |

The modeled behavior is the single statement that decomposes the field-argument
string `fieldarg` into a `(type, name)` pair (guarded by `try/except
ValueError`). The surrounding doctree bookkeeping (`types.setdefault(...)`,
`fieldarg = argname`, node construction) is identity on this decomposition: it
consumes the pair verbatim, so pinning the pair pins the observable rendering.
On `ValueError` the original `fieldarg` is left untouched and no type is
recorded — modeled as the `none` result.

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| `fieldarg : str` (the field argument text), per code point | `arg : List Char` | Lean `List` indexing is total/sound; the decomposition is a per-character scan |
| `(argtype, argname) : tuple[str, str]` | `(List Char × List Char)` | the two pieces, each a character string |
| success vs `except ValueError` | `Option (List Char × List Char)` | `some (ty, nm)` ↔ the assignment succeeds; `none` ↔ `ValueError` is raised and the branch is skipped |
| `str.rsplit(None, 1)` (whitespace mode, maxsplit 1) | `extractTypeName` (deep model) | last-whitespace split: name = final token, type = remaining prefix |
| whitespace separators of `str.split()`/`rsplit()` | `isSpace` | the FULL `str.isspace` singleton set: U+0009–U+000D, U+001C–U+001F, space, U+0085 (NEL), U+00A0 (NBSP), U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000 |

### `str.rsplit(None, 1)` semantics (the post-patch callee), pinned

For a string `s`, `s.rsplit(None, 1)` (separator `None` = runs of whitespace,
`maxsplit = 1`):
- ignores trailing whitespace;
- the **name** is the maximal trailing run of non-whitespace characters;
- the **type** is the prefix before the whitespace run separating the name,
  with its own trailing whitespace removed (interior/leading whitespace of the
  type is preserved);
- returns a 2-element list (modeled `some (ty, nm)`) iff there are ≥ 2
  whitespace-delimited tokens; otherwise a 0/1-element list, which fails the
  tuple unpack and raises `ValueError` (modeled `none`).

This is exactly `extractTypeName` (validated == real `str.rsplit` by G-AX over
≥ 2·10⁵ fuzzed inputs).

## Callee provenance / flag deps

- The decomposition delegates to `str.rsplit(None, 1)` post-patch (pre-patch:
  `str.split(None, 1)`). Both are **fully modeled deeply** (`extractTypeName`
  for the post-patch last-split; `dropLeadingSpaces`/`takeWhile` for the
  pre-patch first-split). No opaque callee, no consumed `_prop` axiom.
- The whitespace mode (`sep=None`) collapses runs and strips ends; `maxsplit=1`
  caps at one split. Both flags are pinned directly in the deep model and the
  G-AX fuzzer exercises the real `str.rsplit`/`str.split` in this configuration.
- Whitespace fidelity: Python `str.split(None)` treats every code point with
  `str.isspace() == True` as a separator (U+0009–U+000D, U+001C–U+001F, space,
  U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F,
  U+3000). `isSpace` models exactly this set, so the bijection is exact on ALL
  of Unicode; the G-CONF / G-AX fuzz pools draw separators from the full set
  (this replaced an earlier ASCII-only `isSpace`, which was unfaithful on e.g.
  `"int\x1cx"` — real repo splits, old model returned `none`).

## G-CONF fuzz seed

`conf_seed = 9230` (pinned; see conformance_check.py, axiom_check.py, meta.json).
