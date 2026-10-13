# refinement.md — sympy__sympy-13798

Operation-by-operation correspondence between `implementation_initMulSymbol`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH derivation of
`mul_symbol_latex` / `mul_symbol_latex_numbers` in `LatexPrinter.__init__`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut latex : String := ""` | (init of `self._settings['mul_symbol_latex']`) | I |
| 2 | `match mulSymbolTable ms with \| some v => latex := v` | `try: ... = mul_symbol_table[self._settings['mul_symbol']]` (key present) | R |
| 3 | `\| none => latex := ms.getD ""` | `except KeyError: ... = self._settings['mul_symbol']` (key absent) | R |
| 4 | `let mut latexNum : String := ""` | (init of `self._settings['mul_symbol_latex_numbers']`) | I |
| 5 | `match mulSymbolTable (numKey ms) with \| some v => latexNum := v` | `try: ... = mul_symbol_table[self._settings['mul_symbol'] or 'dot']` (key present) | R |
| 6 | `\| none => if isSpaceLike (ms.getD "") then latexNum := dotLatex` | `except KeyError: if mul_symbol.strip() in ['','  ','\\','\\,','\\:','\\;','\\quad']: ... = mul_symbol_table['dot']` | R |
| 7 | `else latexNum := ms.getD ""` | `else: ... = self._settings['mul_symbol']` | R |
| 8 | `return Except.ok (latex, latexNum)` | (constructor returns normally; both settings set) | R |

Notes:

- **The fix is ops 2/3 and 5/6/7 read together.** Pre-patch (`Solution_prepatch.lean`)
  derives each separator by a bare dict subscript `mul_symbol_table[k]`; a key
  outside `{None, 'ldot', 'dot', 'times'}` raises `KeyError` and the constructor
  fails. That is modeled as the `none` branch of `mulSymbolTable` returning
  `Except.error ()`. The patch wraps each subscript in `try/except KeyError`, so
  an unrecognized selector is honored: for the general separator it is used
  verbatim (`= self._settings['mul_symbol']`, op 3); for the numeric separator a
  space-like selector falls back to the dotted form (op 6) while any other
  unrecognized selector is used verbatim (op 7). The discriminating clause is the
  `none` (KeyError) case: gold ⇒ `Except.ok (...)`, prepatch ⇒ `Except.error ()`.

- **`mulSymbolTable` (deep model, A-reference-free).** The Python local
  `mul_symbol_table` dict is a CONSTANT literal, carried into the model deeply as
  the total function `mulSymbolTable : Option String → Option String` returning
  `none` for absent keys (= the `KeyError`). It is not an external callee, so it
  is NOT an axiom — it is spelled out and validated end-to-end by G-CONF. Tagged
  R because the partial Python dict-subscript-that-may-raise is refined to a
  total `Option`-returning lookup; the `KeyError ↔ none` bijection is in
  mapping.md.

- **`numKey` (R).** `self._settings['mul_symbol'] or 'dot'` is Python truthiness:
  `None` and `''` are falsy → `'dot'`; any non-empty string is itself. Modeled as
  `numKey : Option String → Option String`. R: Python `or` on `Optional[str]`
  refined to an explicit `none`/empty test.

- **`isSpaceLike` (R).** `mul_symbol.strip() in [...]` modeled as
  `pyStrip _ ∈` the literal list, where `pyStrip` drops leading/trailing
  characters satisfying `pyWhitespace` — an explicit enumeration of exactly the
  code points Python's `str.strip()` removes (U+0009–U+000D, U+001C–U+0020,
  U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F,
  U+3000). Lean's built-in `String.trim` is deliberately NOT used: it strips
  only space/tab/CR/LF, so it diverges from `str.strip()` on e.g. `"\x0c"` or
  NBSP (a selector that strips to `''` is space-like ⇒ the numeric separator
  falls back to the dotted form; the trim mismatch was the G-PANEL-2
  counterexample). The `pyWhitespace ↔ str.isspace` bijection is validated
  exhaustively by G-CONF (`py_whitespace` in conformance_check.py, with the
  fuzz alphabet including the exotic whitespace code points).

- **Result type (R).** A raised `KeyError` ⇒ the printer construction does not
  complete; modeled as `Except Unit (String × String)` with `error` = raised,
  `ok (latex, latexNum)` = the two derived separators. Frame discipline
  (directive 5): both output components are pinned to the selector via
  `specMulSymbol`; nothing is left unconstrained.

No A-consumed axioms and no A-reference callees: the impl region is entirely
R/I, so G-AX is a skip and G-CONF differential-tests every op.
