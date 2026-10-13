# refinement.md — sphinx-doc__sphinx-10435

The operation-by-operation correspondence between `model.py`'s implementation
(`assemble_inline_code`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (proof uses a `@ContractOnly` axiom's
Ensures), **A-reference** (a deep model validated == the real callee/operation
by axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The inline-code assembly — `visit_literal` highlighted branch (`sphinx/writers/latex.py:1712-1717`)

Gold hunk (three coordinated edits):
```
- hlcode = hlcode.replace(OPEN, r'\sphinxcode{\sphinxupquote{')
+ hlcode = hlcode.replace(OPEN, r'\sphinxcode{\sphinxupquote{%')
- hlcode = hlcode.rstrip()[:-14]   # strip \end{Verbatim}
+ hlcode = hlcode.rstrip()[:-15]   # strip \n\end{Verbatim}
  self.body.append(hlcode)
- self.body.append('}}')
+ self.body.append('%' + CR + '}}')
```
where `OPEN = r'\begin{Verbatim}[commandchars=\\\{\}]'`.

The carrier `hlcode` is the upstream Pygments-formatted block of the documented
shape `OPEN ++ CR ++ content ++ CR ++ CLOSE ++ CR` (mapping.md §3.1).

| # | model.py impl op (`assemble_inline_code`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `content: List[int]` | the highlighted body inside `hlcode` | R | `str` ↔ `List[int]` code points (mapping.md §2); the carrier shape (`content` flanked by markers/breaks) is the precondition. |
| A2 | `result = [ open_wrap literal ] ++ [SUPPRESS] ++ [BREAK]` (the 27-code-point `\sphinxcode{\sphinxupquote{` literal, then `%`, then `\n`) | `hlcode.replace(OPEN, r'\sphinxcode{\sphinxupquote{%')` on a carrier that begins with `OPEN` | R + I | the carrier begins with the single occurrence of `OPEN`, so `replace` yields `open_wrap ++ '%' ++ tail`; the impl materialises `open_wrap ++ '%'` then carries the first `BREAK` of `tail`. The `%` after the wrapper is the **identical** new literal char (I); the wrapper/break are R (str↔List[int]). |
| A3 | copy-loop appending `content[k]` so `ToSeq(result) == open_wrap ++ '%' ++ BREAK ++ content` | the `tail` after `OPEN` is `BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK`; `rstrip()` drops the trailing `BREAK`, `[:-15]` drops `BREAK ++ CLOSE`, leaving `open_wrap ++ '%' ++ BREAK ++ content` | R + I | `rstrip()[:-15]` over the documented shape strips exactly `\n\end{Verbatim}` (15 chars; mapping.md §3.1), so the retained prefix is `open_wrap ++ '%' ++ BREAK ++ content`. The deep model reproduces this prefix; equality with the real surgery is checked by G-AX (A-reference, §C). |
| A4 | `result = result + [SUPPRESS, BREAK, 125, 125]` (append `'%'`, `'\n'`, `'}}'`) | `self.body.append('%' + CR + '}}')` | I | the appended suffix `'%' + '\n' + '}}'` is the **identical** literal; the two `self.body.append` calls (the stripped `hlcode` then this suffix) concatenate in the rendered output (mapping.md §2), which the impl models as one returned concatenation. |

The discriminating content of the change — the two LaTeX comment markers `%`
that neutralise the line-break after the opening wrapper and the line-break
before the closing wrapper — lives in `cp_suppress()` placed at offsets
`len(open_wrap)` and `len(Result) - len(close_wrap) - 2` (model) ⇔ the `…{%`
replace target and the `'%' + CR + '}}'` append (real). The pre-patch omits
both markers; `model_prepatch.py` reproduces that (no `'%'`, `[:-14]` instead of
`[:-15]`) and **fails** the postcondition `ToSeq(Result()) == open_wrap ++ '%'
++ BREAK ++ content ++ '%' ++ BREAK ++ close_wrap`, which is exactly the spec
sensing the change (G-DIFF).

## B. No consumed axioms

This bundle consumes **no** `@ContractOnly` axiom (`meta.json axioms == []`).
The only external dependency is the upstream Pygments carrier shape, which is
encoded as the **precondition** (mapping.md §3.1) and is a property of an
**unchanged** producer — not an axiom the proof's Ensures rests on. It is
validated executably by axiom_check.py (G-AX) as part of the A-reference check.

## C. The one A-reference (deep model == real surgery)

The changed operation — the `.replace().rstrip()[:-15]` + `'%'+CR+'}}'` string
surgery — is modeled **deeply** (spelled-out sequence ops in the impl, pinned by
the postcondition), NOT behind a consumed axiom. It is an **A-reference**:
`axiom_check.py` runs the REAL post-patch surgery on boundary + 20 000 fuzz
carriers of the documented shape and asserts it equals the model's assembled
output `open_wrap ++ '%' ++ BREAK ++ content ++ '%' ++ BREAK ++ close_wrap`; it
also asserts the REAL pre-patch surgery equals `model_prepatch`'s output (no
suppressors). Both held with 0 mismatches (§meta G-AX).

## D. No kind-3 (unexpressible-changed-op) steps

Every step in §A is R, I, or covered by the §C A-reference. The operation that
genuinely *changed* — the string surgery adding the two `%` line-suppressors —
is modeled **deeply** (steps A2–A4, validated as the A-reference of §C), not
hidden behind an axiom about the function under change. There is no kind-3 step.

## E. verify(model) ⇒ resolved

`assemble_inline_code` verifies only if its output equals
`open_wrap ++ '%' ++ BREAK ++ content ++ '%' ++ BREAK ++ close_wrap` (the
postcondition, with the two `%` suppressors at the pinned offsets). By R
(str ↔ List[int]; two appends ↔ one concatenation) and the A-reference of §C
(the deep model == the real post-patch surgery on the documented carrier), the
verified assembly equals the gold patch's
`hlcode.replace(OPEN,'…{%').rstrip()[:-15]` + `'%'+CR+'}}'` on the highlighted
inline-code path. The F2P test `test_latex_code_role` matches exactly this
concatenation (`\sphinxcode{\sphinxupquote{%\n … %\n}}`) as a substring of
`python.tex`. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited A-reference — and the
gold patch resolves (G-RESOLVE). The single trust point is refinement fidelity
(this document, G-EQ) plus the executable A-reference (G-AX); there is no
consumed-axiom trust point.
