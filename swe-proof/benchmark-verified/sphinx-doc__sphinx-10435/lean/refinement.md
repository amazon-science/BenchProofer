# refinement.md — sphinx-doc__sphinx-10435

Operation-by-operation correspondence between `implementation_visit_literal`
(Lean) and the gold `patch.diff` post-processing in
`LaTeXTranslator.visit_literal`. Every row is tagged **R** (type refinement),
**A-consumed** (proof consumes a callee axiom), **A-reference** (deep model
validated `==` real callee by G-CONF), or **I** (identical concrete op).

| # | Lean op (`implementation_visit_literal`) | `patch.diff` counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut hl := hlcode` | implicit: `hlcode` is the local being rewritten | I | bind the input |
| 2 | `hl := replaceAll verbOpen upquoteOpen hl` | `hlcode = hlcode.replace(r'\begin{Verbatim}…', r'\sphinxcode{\sphinxupquote{%')` | A-reference + R | `replaceAll` deeply models `str.replace` (all non-overlapping, left-to-right); `List Char ↔ str`. Validated by G-CONF. |
| 3 | `hl := dropLastN 15 (rstripWs hl)` | `hlcode = hlcode.rstrip()[:-15]` | A-reference + R | `rstripWs` models `str.rstrip()`; `dropLastN 15` models `s[:-15]`. Validated by G-CONF. |
| 4 | `body := body ++ hl` | `self.body.append(hlcode)` | I | append the trimmed fragment |
| 5 | `body := body ++ closingTail` where `closingTail = '%'::CR::"}}"` | `self.body.append('%' + CR + '}}')` | I | the post-patch closing string |
| 6 | `return body` | (the appended fragments, joined into the body) | R | `''.join` of the two appends = `List Char` concatenation |

There is **no A-consumed** row: the proof requires no callee-property axiom. The
highlighter (`highlight_block`) is upstream — its output `hlcode` is the modeled
function's *free input*, quantified universally in `correct_visit_literal`, not a
consumed callee.

## Changed ops, expressed (no changed-inexpressible op)

The three edited behaviors are all expressed concretely in the impl:

- **`{` → `{%` in the opening replacement** (op 2): `upquoteOpen` ends in `'%'`.
  Pre-patch model: `replaceAll verbOpen (…upquote{) hl` (no `%`).
- **`[:-14]` → `[:-15]`** (op 3): `dropLastN 15`. Pre-patch model: `dropLastN 14`.
- **`'}}'` → `'%' + CR + '}}'`** (op 5): `closingTail = '%'::CR::"}}"`. Pre-patch
  model: `body ++ "}}"`.

Each of the three is independently observable in the emitted character sequence;
the single F2P test (`test_latex_code_role`) asserts the exact post-patch string
(`\sphinxupquote{%` … `%\n}}`), and the prepatch impl reproduces exactly the
buggy (space-producing) string, so the `problem_spec` discriminates it (G-DIFF).

## Why no op is left inexpressible (SPEC_GUIDE §3)

`str.replace`, `str.rstrip`, fixed-count slicing, and string concatenation are
all total textual operations with exact `List Char` models; none requires
floating-point, an opaque object, or an external oracle. The highlighter output
is treated as an arbitrary input, so the spec pins the transformation for ALL
`hlcode`, not just the F2P sample.
