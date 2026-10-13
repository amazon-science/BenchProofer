# refinement.md — django__django-12155

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `normalizeIndentation` `do` block and the deep `cleanDocModel` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The normalization site — `parse_docstring()` (`utils.py:42`)

Gold hunk (the behavioral change):
```
- docstring = trim_docstring(docstring)        # min indent over ALL lines
+ if not docstring:
+     return '', '', {}
+ docstring = cleandoc(docstring)               # margin over lines[1:]
```
(`trim_docstring` itself is deleted; `views.py` likewise swaps
`utils.trim_docstring(verbose)` for `cleandoc(verbose)` — the SAME normalization
change, no independent behavior.)

| # | Solution.lean impl op (`normalizeIndentation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text : List Char` | `docstring: str` arg of `parse_docstring` (and `verbose` in views.py) | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `splitLines text` | `doc.expandtabs().split('\n')` inside `cleandoc` | R + I | `splitLines` ↔ `str.split('\n')` (mapping.md §2); `expandtabs` is the identity on the modeled tab-free domain (mapping.md §2.1). Concrete op, transliterated by G-CONF. |
| A3 | `commonIndent (lines.drop 1)` | the `margin` loop over `lines[1:]` in `cleandoc` | A-reference + I | the changed normalization is modeled **deeply**: `commonIndent`/`leadingSpaces`/`hasContent` (pure region) ARE the `margin = min(len(line)-len(line.lstrip()) …)` loop, **restricted to `lines[1:]`** — the behavioral fix. The op (`commonIndent`, `drop 1`) is **I** (concrete, transliterated by G-CONF); the equality of the whole deep model to the real `inspect.cleandoc` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A4 | `dedentLines margin lines` | `lines[0]=lines[0].lstrip()` + `lines[i]=lines[i][margin:]` (guarded by `margin < maxsize`) | I | always `lstrip` the first line; strip `margin` chars from the rest, or leave them when no content line exists (`none` ↔ `margin == sys.maxsize`). Concrete. |
| A5 | `dropLeadingBlank (dropTrailingBlank dedented)` | the two `while … pop()` loops | I | drop trailing then leading blank (empty) lines. Concrete. |
| A6 | `joinNL trimmed` returned (`List Char`) | `'\n'.join(lines)` returned to `parse_docstring` | R + I | `joinNL` ↔ `'\n'.join` (mapping.md §2). The normalized string then flows into the unchanged `re.split`/title/body parsing. |

Discriminating content of the change — the margin is measured over the lines
**after the first** (`commonIndent (lines.drop 1)`), not all lines — lives in step
A3. The pre-patch `trim_docstring` took the min over **all** lines, so a first
line beginning at column 0 forced the margin to 0 and the body was never
dedented; `Solution_prepatch.lean` reproduces that (`commonIndent lines`, no
`drop 1`) and **fails** `out = cleanDocModel text` (G-DIFF).

## B. The `views.py` site — same callee swap

Gold hunk: `utils.parse_rst(utils.trim_docstring(verbose), …)` becomes
`utils.parse_rst(cleandoc(verbose), …)` (`views.py:260`). This is the **same**
normalization change applied to a different caller; it introduces no
independently-observable behavior beyond the `cleandoc` normalization already
modeled by `normalizeIndentation`. Hence no separate `Solution_prepatch_<k>.lean`
(a prepatch must keep the spec byte-identical, G-DIFF; the shared change is
already exercised by site A's prepatch). Its soundness rides on the same
A-reference (`cleanDocModel == inspect.cleandoc`, G-AX).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
indentation-margin computation (all lines → lines after the first, i.e. the swap
from `trim_docstring` to `inspect.cleandoc`) — is modeled **deeply** (the
spelled-out `cleanDocModel`, step A3, an A-reference + I), not hidden behind an
axiom about the function under change. There are **no consumed axioms**: the only
kind-A element is the A-reference deep model validated == the real
`inspect.cleandoc` by G-AX.

## D. verify(Solution) ⇒ resolved

`normalizeIndentation` verifies only if its output equals the exact deep model
`cleanDocModel` (margin over `lines.drop 1`, A3). By R (`str ↔ List Char`,
`split('\n') ↔ splitLines`, `'\n'.join ↔ joinNL`, `expandtabs`-identity on the
modeled domain) the verified normalizer equals `inspect.cleandoc(docstring)` on
the tested inputs; by G-AX the deep model `cleanDocModel` equals the real
`inspect.cleandoc` (A-reference); by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. The patched `parse_docstring` also adds
an early `if not docstring: return '', '', {}` guard — observationally identical
to the old `trim_docstring`'s `if not docstring or not docstring.strip(): return
''` for the F2P/PASS_TO_PASS inputs (a non-empty docstring proceeds to `cleandoc`
either way; an empty/falsy docstring yields empty title/body/metadata both ways),
so it adds no behavior the spec must pin. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
callee — and the gold patch resolves (G-RESOLVE). Trust points are exactly the
two of plan §1.1: deep-model fidelity (G-AX) and refinement fidelity (this doc,
G-EQ + G-CONF).
