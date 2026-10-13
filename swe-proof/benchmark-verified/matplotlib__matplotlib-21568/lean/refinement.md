# refinement.md — matplotlib__matplotlib-21568

Maps every operation in `implementation_texLabel` to its `patch.diff`
counterpart in the math-label helper `_wrap_in_tex`
(`lib/matplotlib/dates.py:594-601`, post-patch).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed/used op validated == real callee, **I**
identical concrete op.

## Patch (post-patch body)
```python
def _wrap_in_tex(text):
    p = r'([a-zA-Z]+)'
    ret_text = re.sub(p, r'}$\1$\\mathdefault{', text)

    # Braces ensure symbols are not spaced like binary operators.
    ret_text = ret_text.replace('-', '{-}').replace(':', '{:}')
    # To not concatenate space between numbers.
    ret_text = ret_text.replace(' ', r'\;')
    ret_text = '$\\mathdefault{' + ret_text + '}$'
    ret_text = ret_text.replace('$\\mathdefault{}$', '')
    return ret_text
```
The modeled value is the returned string: the math-mode rendering of `text`.

## Operation correspondence
| # | Lean op (`implementation_texLabel`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let lifted := bracketLetterRuns text` | `ret_text = re.sub(r'([a-zA-Z]+)', r'}$\1$\\mathdefault{', text)` | A-reference | The regex substitution is an UNCHANGED callee (`re.sub`), modeled DEEPLY as the front-recursive run scanner `bracketLetterRuns` (close group `}$`, emit the maximal letter run, reopen `$\mathdefault{`). Validated `== re.sub` by `axiom_check.py` (G-AX). `Char.isAlpha` = ASCII `[a-zA-Z]` (verified), matching the regex class exactly. |
| 2 | `for c in lifted do escaped := escaped ++ escapeMathSym c` | `ret_text.replace('-', '{-}').replace(':', '{:}')` then `.replace(' ', r'\;')` | R | Three independent single-character `str.replace`s over a string with NO multi-character source token compose into one per-character map (`-`↦`{-}`, `:`↦`{:}`, ` `↦`\;`, else identity). Because the three sources `-`,`:`,` ` are distinct single chars and none appears in any replacement's *source*, the chained replaces equal a single left-to-right per-char rewrite — modeled as the accumulator loop applying `escapeMathSym`. **This is the heart of the fix**: pre-patch only `-`↦`{-}` ran (colon/space passed through bare). |
| 3 | `let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList` | `ret_text = '$\\mathdefault{' + ret_text + '}$'` | I | wrap the escaped body in one outer math-default group (literal concatenation). |
| 4 | `return dropToken '$' "\\mathdefault{}$".toList wrapped` | `ret_text = ret_text.replace('$\\mathdefault{}$', '')` | R | delete every occurrence of the empty math-default group token. `str.replace(old,'')` is left-to-right non-overlapping deletion; modeled as `dropToken` (same scan). `old` = `$\mathdefault{}$` contains no `$\mathdefault{}$` proper sub-occurrence overlap issue (the deletions cannot create a new match left of the cursor), so the single-pass `dropToken` equals Python's `replace`. |

Tags present: **A-reference** (op 1), **R** (ops 2, 4), **I** (op 3). No
**A-consumed** row — no axiom contract is consumed (the regex callee is
deep-modeled, not assumed). Therefore `meta.json axioms = []`,
`deep_model_references = ["re.sub run-lifting (bracketLetterRuns)"]`.

## R/I/A-reference legs ⇒ G-CONF + G-AX
- Ops 1-4 form the full impl; `conformance_check.py` (G-CONF) differential-tests
  the whole impl shadow against the EXACT post-patch `_wrap_in_tex` body over
  >2·10^5 fuzzed inputs (incl. the deep-modeled op 1). `conf_skip = false`.
- `axiom_check.py` (G-AX) separately validates the op-1 deep model against the
  real `re.sub` callee.

## Prepatch = the real bug
Pre-patch, `_wrap_in_tex` did:
```python
ret_text = re.sub(p, r'}$\1$\\mathdefault{', text)
ret_text = '$\\mathdefault{'+ret_text.replace('-', '{-}')+'}$'
ret_text = ret_text.replace('$\\mathdefault{}$', '')
```
i.e. it braced ONLY hyphens; colons and spaces were left as bare characters
inside the math group (rendered with binary-operator spacing — the unclear
spacing reported in the issue). The prepatch impl
(`implementation_texLabel` with the loop body `if c = '-' then …{-}… else …[c]…`,
no colon/space handling) is exactly this. It therefore cannot satisfy
`problem_spec_texLabel` (`result = texLabel text`) on any input containing a
colon or a space — precisely the FAIL_TO_PASS vectors
`$\mathdefault{1990{-}01{-}%02d}$`, `$\mathdefault{01\;…}$`,
`$\mathdefault{01\;00{:}%02d}$`, and `…{04{:}00}…`. The carried gold proof
(`unfold …; rfl`) fails to typecheck against the buggy impl (G-DIFF; confirmed:
prepatch verify exits 1).
