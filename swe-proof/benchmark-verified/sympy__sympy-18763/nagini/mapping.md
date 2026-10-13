# mapping.md — sympy__sympy-18763

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 70381f282f2d9d039da860e391fe51649df2779d`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/printing/latex.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `format_restriction(body, cond)` | `LatexPrinter._print_Subs(self, subs)` — `sympy/printing/latex.py:699` (assembled in the `return`, lines 706-707) | the modeled changed function (the LaTeX renderer for a substitution/restriction object) |
| parameter `body: List[int]` | `latex_expr` local — `latex.py:701` (`latex_expr = self._print(expr)`) | the already-rendered inner-expression fragment that the layout encloses |
| parameter `cond: List[int]` | `latex_subs` local — `latex.py:704-705` (`latex_subs = r'\\ '.join(...)`) | the already-rendered condition fragment placed after the body group |
| `open_layout()` | the literal `r'\left. '` in the return template (`latex.py:706`) | fixed opening layout |
| `open_delim()` | the literal `r'\left('` ADDED by the change directly before the expression | the scaling open delimiter enclosing the body |
| `close_delim()` | the literal `r'\right)'` ADDED by the change directly after the expression | the scaling close delimiter enclosing the body |
| `mid_layout()` | the literal `r' \right|_{\substack{ '` in the return template | layout between the body group and the condition |
| `tail()` | the literal `r' }}'` in the return template | fixed closing layout |
| `assembled(body, cond)` | the whole `r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs)` string (post-change, `latex.py:706-707`) | pure spec: the fully assembled layout |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`latex_expr`, `latex_subs`, and the returned LaTeX string) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` `%`-template substitution and concatenation ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `%s ... %s` printf-style template (`latex.py:706-707`) | concatenation of the fixed code-point segments around the two substituted fragments | `'A%sB%sC' % (x, y)` ↔ `A + x + B + y + C`; the two `%s` are the two `List[int]` inputs, the literals are the constant `PSeq` segments |

The literal LaTeX fragments expand to ASCII code points (verified against the
exact bytes of the gold return string):

| fragment | raw text | code points |
|---|---|---|
| `open_layout()` | `\left. ` (note trailing space) | `92,108,101,102,116,46,32` |
| `open_delim()` | `\left(` | `92,108,101,102,116,40` |
| `close_delim()` | `\right)` | `92,114,105,103,104,116,41` |
| `mid_layout()` | ` \right|_{\substack{ ` (leading + trailing space) | `32,92,114,105,103,104,116,124,95,123,92,115,117,98,115,116,97,99,107,123,32` |
| `tail()` | ` }}` (leading space) | `32,125,125` |

Composition check: `open_layout + open_delim + body + close_delim + mid_layout
+ cond + tail` reproduces, byte-for-byte, the gold template
`r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (body, cond)` (confirmed
by executing the template with marker substituents). The pre-change template
`r'\left. %s \right|_{\substack{ %s }}'` is exactly the same composition with
`open_delim` and `close_delim` removed.

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A) — NONE

There are **no consumed axioms and no A-reference deep models** in this bundle,
so there is no `axiom_check.py`.

`_print_Subs` calls `self._print(...)` to render `expr`/`old`/`new` and
`str.join` to build `latex_subs`. None of these callees is changed by the patch,
and none needs to be axiomatized: their *outputs* are the already-rendered
fragments `latex_expr` and `latex_subs`, which the model takes as the opaque
read-only inputs `body` and `cond` (full code-point generality, `Acc(..., 1/2)`).
The only operation the patch changes is the fixed surrounding template, which is
modeled deeply as literal code-point segments in the `pure` region. There is
nothing left to execute against a real callee.
