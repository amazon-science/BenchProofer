# mapping.md — sympy__sympy-13798

## Symbol binding (file:line @ base_commit `7121bdf1facdd90d05b6994b4c2e5b2865a4638a`)

Modeled function: the multiplication-symbol settings derivation inside
`LatexPrinter.__init__` — `sympy/printing/latex.py:138-163` (the
`mul_symbol_table` dict at L152-157 and the two derived assignments at
L159-163). The patch (gold) rewrites exactly L159-163.

| Lean | Python |
|---|---|
| `implementation_initMulSymbol` / `problem_spec_initMulSymbol` / `correct_initMulSymbol` | the `mul_symbol_latex` / `mul_symbol_latex_numbers` derivation in `LatexPrinter.__init__(self, settings)` |
| `mulSymbolTable` | the local `mul_symbol_table` dict (L152-157) |
| `numKey` | the key expression `self._settings['mul_symbol'] or 'dot'` (L163) |
| `isSpaceLike` (via `pyStrip`/`pyWhitespace`) | the membership test `self._settings['mul_symbol'].strip() in ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']` |
| `dotLatex` | `mul_symbol_table['dot']` = `r" \cdot "` |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | notes |
|---|---|---|
| `mul_symbol` setting: `None \| str` | `Option String` | `None ↔ none`, `s ↔ some s` |
| `(mul_symbol_latex, mul_symbol_latex_numbers)` : `(str, str)` | `String × String` | the two derived settings |
| the constructor RAISING `KeyError` (printer construction fails) | `Except.error ()` | a raised lookup is modeled as the error branch of `Except Unit (String × String)`; a successful construction is `Except.ok (latex, latexNum)` |
| `mul_symbol_table[k]` (dict access, may raise) | `mulSymbolTable : Option String → Option String` | `none` return = the `KeyError` case |
| `mul_symbol or 'dot'` (Python truthiness) | `numKey` | `None`/`''` are falsy → `'dot'`; any other string is itself |
| `s.strip()` | `pyStrip` (dropWhile `pyWhitespace` from both ends) | `pyWhitespace` enumerates exactly the code points Python's `str.isspace()`/`str.strip()` treats as whitespace: U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000. (Lean's built-in `String.trim` only strips space/tab/CR/LF, so it is NOT used: it would diverge on e.g. `\x0c` or NBSP — the G-PANEL-2 counterexample class.) |
| `x in [..]` | `x ∈ ([..] : List String)` | membership in the space-like separator set |
| Python `str` literal `r" \cdot "` | Lean `" \\cdot "` | backslash escaped in Lean source; same bytes |

## Callee provenance + flag deps

No UNCHANGED outside callee is consumed. The modeled derivation is a pure
function of the `mul_symbol` setting and the constant `mul_symbol_table` (a
literal, carried into the model deeply as `mulSymbolTable`). There is no
`opaque`/`axiom` callee contract: every operation is R or I (see
refinement.md). G-AX is therefore a skip; G-CONF differential-tests the R/I legs.

The derived settings feed the later `_print_Mul` / `_print_Float` rendering
(which inserts `mul_symbol_latex` between factors and `mul_symbol_latex_numbers`
between numeric coefficients). That rendering is UNCHANGED by the patch and is
out of model scope: the patch fixes only how the two separator strings are
derived from `mul_symbol`. There is no flag dependency.

## G-CONF fuzz seed

Pinned seed: **13798** (also recorded in conformance_check.py and meta.json).
