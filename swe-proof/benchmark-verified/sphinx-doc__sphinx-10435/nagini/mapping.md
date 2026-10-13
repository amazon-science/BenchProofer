# mapping.md — sphinx-doc__sphinx-10435

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f1061c012e214f16fd8790dec3c283d787e3daa8`, states the type
abstraction, and gives the provenance of the upstream producer the deep model
is validated against.

Repo file under change: `sphinx/writers/latex.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_inline_code(content)` | the highlighted-inline-code branch of `LaTeXTranslator.visit_literal` — `sphinx/writers/latex.py:1707-1718` (the three changed statements at lines 1712-1717) | the modeled changed behavior: build the inline-code wrapper string appended to `self.body` |
| `open_wrap()` | the `replace` target literal `r'\sphinxcode{\sphinxupquote{'` (`latex.py:1713`, the part before the patch's trailing `%`) | the opening inline-code wrapper |
| `close_wrap()` | the `'}}'` literal appended last (`latex.py:1717`) | the closing inline-code wrapper |
| `cp_suppress()` | the `'%'` character the patch inserts (`latex.py:1713` target `…{%`, and `latex.py:1717` `'%' + CR + '}}'`) | the LaTeX end-of-line comment marker that neutralises a line-break |
| `cp_break()` | `CR = '\n'` (`latex.py:53`) | the line-break code point |

The upstream markers that flank `content` in the carrier are NOT modeled as
spec-view symbols (their concrete shape is the unchanged producer's, irrelevant
to the desired behaviour, and would otherwise reproduce a repo literal in the
consumer view). They appear in the model only as the opaque `OPEN`/`CLOSE`
boundaries of the precondition carrier shape. For the refinement audit only
(not the consumer spec view), their concrete repo values are:
the opening marker is the `replace` source literal
`r'\begin{Verbatim}[commandchars=\\\{\}]'` (`latex.py:1712`) and the closing
marker is `r'\end{Verbatim}'` (the trailer stripped by `rstrip()[:-14]`/`[:-15]`,
`latex.py:1715`). `axiom_check.py` validates the deep model against the real
surgery using these concrete literals (A-reference, §3).

The pre-patch repo state the change edits (for the refinement audit, not the
consumer spec view): the three statements

```python
hlcode = hlcode.replace(r'\begin{Verbatim}[commandchars=\\\{\}]',
                        r'\sphinxcode{\sphinxupquote{')   # no trailing '%'
hlcode = hlcode.rstrip()[:-14]   # strips '\end{Verbatim}' only
self.body.append('}}')           # no '%' + CR
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`hlcode`, the appended fragments) | `List[int]` of code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` `+` ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `self.body.append(hlcode); self.body.append(suffix)` (two appends to a list of strings) | a single returned `List[int]` equal to the concatenation `hlcode ++ suffix` | the rendered LaTeX is the concatenation of the appended fragments; the F2P test (`test_latex_code_role`) matches that concatenation as a substring of `python.tex`. Modeled as the produced concatenation. |
| `CR` (`'\n'`, `latex.py:53`) | `cp_break() == 10` | the single line-break code point |
| `'%'` | `cp_suppress() == 37` | the LaTeX comment char |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Producer provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 The upstream carrier shape — `highlighter.highlight_block` → Pygments `LatexFormatter`
**Producer (unchanged):** `self.highlighter.highlight_block(...)`
(`sphinx/highlighting.py:136`, returns `texescape.hlescape(hlsource, …)` for
the LaTeX destination) wraps the highlighted source with Pygments'
`LatexFormatter`, whose output for a code block is

```
\begin{Verbatim}[commandchars=\\\{\}]<CR><highlighted-content><CR>\end{Verbatim}<CR>
```

— a single opening `Verbatim` environment line, the highlighted content, the
closing `\end{Verbatim}` line, and one trailing newline. This shape is the
**precondition** of `assemble_inline_code` (the carrier =
`open_marker ++ BREAK ++ content ++ BREAK ++ close_marker ++ BREAK`), NOT a
consumed `@ContractOnly` axiom: the producer is unchanged and its shape is
exactly what the writer's existing `rstrip()[:-14]` (pre) / `[:-15]` (post)
slice-constants assume — `[:-14]` strips precisely `\end{Verbatim}` (14 chars)
and `[:-15]` strips `\n\end{Verbatim}` (15 chars). `close_marker` ends in `}`,
so the only trailing whitespace is the single closing `CR`, which `rstrip()`
removes.

### 3.2 The string surgery — modeled DEEPLY (A-reference, not an axiom)
The changed operation is the writer's own string surgery

```python
hlcode = hlcode.replace(OPEN, r'\sphinxcode{\sphinxupquote{%')
hlcode = hlcode.rstrip()[:-15]
self.body.append(hlcode); self.body.append('%' + CR + '}}')
```

This is modeled **deeply** in `model.py`'s impl (spelled-out `take`/`drop`/`+`
over `PSeq[int]`), with no `@ContractOnly` axiom about it. `axiom_check.py`
(G-AX) validates the deep model **==** this real surgery by running the exact
`.replace().rstrip()[:-15] + '%'+CR+'}}'` Python on boundary + 20 000 fuzz
carriers of the §3.1 shape and asserting equality with the model's assembled
output `open_wrap ++ '%' ++ CR ++ content ++ '%' ++ CR ++ '}}'`. It also runs
the **pre-patch** surgery (`[:-14]`, no `'%'`) and asserts it equals
`model_prepatch`'s assembled output (no suppressors) — the real bug→fix delta.
Imports only the standard library; exit 0 iff faithful.

There is **no consumed axiom** in this bundle: `meta.json axioms == []`.
