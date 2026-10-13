# mapping.md — sphinx-doc__sphinx-10435

## Symbol binding (file:line @ base_commit f1061c012e)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_visit_literal` / `problem_spec_visit_literal` / `correct_visit_literal` | the highlighted-`code`-role tail of `LaTeXTranslator.visit_literal` (the block after `highlight_block`, ending in `raise nodes.SkipNode`) | `sphinx/writers/latex.py:1702-1717` @ base_commit (edited lines `1712-1717` of file, hunk `@@ -1710,11`) |
| `verbOpen` | the literal `r'\begin{Verbatim}[commandchars=\\\{\}]'` (1st arg of `hlcode.replace`) | `latex.py:1712` |
| `upquoteOpen` | the literal `r'\sphinxcode{\sphinxupquote{%'` (2nd arg of `hlcode.replace`, POST-patch; pre-patch had no trailing `%`) | `latex.py:1713` (gold) |
| `replaceAll verbOpen upquoteOpen hl` | `hlcode = hlcode.replace(r'\begin{Verbatim}…', r'\sphinxcode{\sphinxupquote{%')` | `latex.py:1712-1713` |
| `dropLastN 15 (rstripWs hl)` | `hlcode = hlcode.rstrip()[:-15]` (POST-patch; pre-patch `[:-14]`) | `latex.py:1715` |
| `rstripWs` | `str.rstrip()` (default whitespace set) | `latex.py:1715` |
| `dropLastN n` | value-level Python slice `s[:-n]`, `n>0` | `latex.py:1715` |
| `closingTail` = `'%' :: CR :: "}}"` | `self.body.append(hlcode); self.body.append('%' + CR + '}}')` (POST-patch; pre-patch `self.body.append('}}')`) | `latex.py:1716-1717` |
| `CR` | module-level `CR = '\n'` | `latex.py:53` |

## The modeled function and the fix

`visit_literal`, for an inline node whose `classes` contain `'code'` and that has
a `language`, runs the syntax highlighter and post-processes its output before
appending it to `self.body`. The highlighter wraps the code in a
`\begin{Verbatim}…\end{Verbatim}` environment, with a newline immediately after
the opening and immediately before the closing delimiter.

The post-processing does three things; the gold patch edits all three so that the
two framing newlines are *comment-suppressed* (a trailing `%` in LaTeX comments
out the rest of its line, including the newline), instead of surviving as
spurious inter-token spaces in the rendered PDF:

```python
# POST-PATCH (gold)
hlcode = hlcode.replace(r'\begin{Verbatim}[commandchars=\\\{\}]',
                        r'\sphinxcode{\sphinxupquote{%')   # +%
hlcode = hlcode.rstrip()[:-15]   # strip "\n\end{Verbatim}" (was [:-14], "\end{Verbatim}")
self.body.append(hlcode)
self.body.append('%' + CR + '}}')   # was '}}'
```

- `\end{Verbatim}` is exactly 14 characters; `[:-15]` therefore removes it AND the
  one newline that precedes it (after `rstrip()` removes any further trailing
  whitespace). `[:-14]` removed only the delimiter, leaving that newline in place.
- The two appended strings are concatenated in `body`; the model returns their
  concatenation `trimmed ++ closingTail`.

## Modeled input / output (Lean ↔ Python type bijection)

| Python | Lean | note |
|---|---|---|
| `hlcode : str` (highlighter output) | `hlcode : List Char` | per-code-point textual op; `List Char` is total/sound for indexing & slicing (SPEC_GUIDE §2) |
| concatenation appended to `self.body` for this node | `result : List Char` | the two `self.body.append(...)` strings, concatenated |
| `str.replace(a, b)` | `replaceAll a b` | all non-overlapping, left-to-right (Python `str.replace` semantics) |
| `str.rstrip()` | `rstripWs` | default whitespace set: space, `\t`, `\n`, `\r`, `\v`(0x0b), `\f`(0x0c). Faithful on the modeled domain: Pygments `LatexFormatter` output ends in `…\n\end{Verbatim}` optionally followed by ASCII whitespace/newlines — never the exotic Unicode whitespace (e.g. U+00A0, U+2028) where `str.rstrip()` and `rstripWs` could diverge. G-CONF fuzzes only this highlighter shape, matching the A-reference domain. |
| `s[:-n]`, `n>0` | `dropLastN n` | empty if `n ≥ len` |
| `'\n'` (`CR`) | `CR : Char` | |

`self.body` is a list of strings later `''.join`-ed; modeling the per-node
contribution as one `List Char` (the concatenation of the two appends) is exact
for the rendered output, since `''.join` is plain concatenation.

## Callee provenance + flag deps

- `highlight_block` (the highlighter) is UPSTREAM of the modeled fragment: its
  output `hlcode` is the *input* to the modeled function, so it is neither
  axiomatized nor modeled — it is a free input quantified over in the theorem.
  The fix does not touch it.
- No unchanged callee is consumed as an axiom. `str.replace` / `str.rstrip` /
  slicing are modeled deeply (`replaceAll` / `rstripWs` / `dropLastN`) and are
  **A-reference** rows validated by G-CONF against the real Python operations.
- Flag dependency: the modeled branch is reached only when `'code' in
  node['classes'] and node.get('language')` and the node is not in a title and
  not a `kbd`. The fragment shape (a single `\begin{Verbatim}[commandchars=…]`
  followed by code and a single `\end{Verbatim}`) is the invariant Pygments
  `LatexFormatter` output; G-CONF fuzzes over that shape.

## G-CONF fuzz seed

Pinned seed: `20240630` (see `meta.json.verifier_pins.conf_seed`).
