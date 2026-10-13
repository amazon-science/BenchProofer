# mapping.md — sympy__sympy-18763

## Instance
- repo: sympy/sympy
- base_commit: 70381f282f2d9d039da860e391fe51649df2779d
- modeled function: the markup renderer for a bound-evaluation expression
  (`_print_Subs`), `sympy/printing/latex.py`
- spec_provenance: cold

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python | location @ base_commit |
|---|---|---|
| `implementation_renderRestriction` | `_print_Subs(self, subs)` | `sympy/printing/latex.py:699`–`:707` |
| `inner` (input) | `latex_expr = self._print(expr)` | `sympy/printing/latex.py:701` |
| `lhs` (input) | `latex_old = (self._print(e) for e in old)` | `sympy/printing/latex.py:702` |
| `rhs` (input) | `latex_new = (self._print(e) for e in new)` | `sympy/printing/latex.py:703` |
| pair build + join | `latex_subs = r'\\ '.join(e[0] + '=' + e[1] for e in zip(latex_old, latex_new))` | `sympy/printing/latex.py:704`–`:705` |
| final assembly | `return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs)` (post-patch) | `sympy/printing/latex.py:706`–`:707` |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

`_print_Subs` consumes `subs.args = (expr, old, new)` and the printer's recursive
`self._print` rendering of each, then emits one markup string.

| Python value | Lean carrier |
|---|---|
| `latex_expr : str` (rendered body) | `inner : String` |
| `latex_old : Iterable[str]` (rendered LHS tokens) | `lhs : List String` |
| `latex_new : Iterable[str]` (rendered RHS tokens) | `rhs : List String` |
| returned markup `str` | `result : String` |
| `zip(latex_old, latex_new)` | `lhs.zip rhs` (both truncate to the shorter list) |
| `e[0] + '=' + e[1]` | `fun p => p.1 ++ "=" ++ p.2` |
| `r'\\ '.join(...)` | `String.intercalate "\\\\ " ...` (separator = backslash,backslash,space) |
| `%`-format assembly | `String` append of the fixed literal fragments |

String-literal correspondence (actual characters):
- prefix `\left. \left(` ↔ Lean `"\\left. \\left("`
- mid `\right) \right|_{\substack{ ` ↔ Lean `"\\right) \\right|_{\\substack{ "`
- suffix ` }}` ↔ Lean `" }}"`
- join separator (LaTeX line break) `\\ ` (2 backslashes + space) ↔ Lean `"\\\\ "`

## Callee provenance + flag deps
- `self._print(expr)` / `self._print(e)` — UNCHANGED recursive renderer. The fix
  does NOT touch how sub-expressions are rendered; it only changes how the
  already-rendered `inner` body is wrapped in the surrounding markup. The rendered
  strings are therefore taken as INPUTS to the model (R-abstraction), exactly as a
  caller-supplied value — NOT axiomatized (no `opaque`/`axiom` callee, no `_prop`
  consumed). G-AX has nothing to check → axiom_check.py is a skip stub.
- No flag-dependent callees.

## G-CONF fuzz seed
- pinned seed: `18763`
- fuzz domain: random `inner` token strings (incl. empty, special chars,
  pre-existing backslashes/braces) and random equal/unequal-length `lhs`/`rhs`
  token lists (incl. empty), ≥10^5 samples. The R/I shadow of the impl is diffed
  against an in-process replica of the post-patch `%`-format assembly.
