# mapping.md — sympy__sympy-13798

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7121bdf1facdd90d05b6994b4c2e5b2865a4638a`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep-modeled construct.

Repo file under change: `sympy/printing/latex.py` — the constructor of the
LaTeX printer (`LatexPrinter.__init__`, the block that derives the two
multiplication-separator settings, lines 152–163 @ base_commit).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveMulSeparators (sym)` | the `__init__` block that computes `self._settings['mul_symbol_latex']` and `self._settings['mul_symbol_latex_numbers']` (`sympy/printing/latex.py:159–163`) | the modeled changed function: from the user-supplied multiplication-symbol setting, derive the two LaTeX separator strings |
| `mulTable (k)` *(R/I — inline data)* | the literal lookup table `mul_symbol_table = {None: " ", "ldot": " \,.\, ", "dot": " \cdot ", "times": " \times "}` defined inside `__init__` (`latex.py:152–157`) | pure spec: the named-symbol → separator map carried inline by the changed function itself; `none` result models the `KeyError` a missing key raises |
| `numKey (sym)` | the key expression `self._settings['mul_symbol'] or 'dot'` (`latex.py:163`) | pure spec: the falling-back key for the numeric separator (a falsy symbol — `None` or `""` — uses `'dot'`) |
| `spacingSyms` *(R/I — inline data)* | the literal whitelist `['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']` written inline in the post-patch branch (`latex.py:172–173`) | pure spec: the stripped-symbol forms for which the numeric separator falls back to the dot |
| `MulErr.unresolved` *(prepatch outcome model)* | the `KeyError` `mul_symbol_table[...]` raises on a symbol absent from the table | the failure the pre-patch constructor escapes with on a non-named symbol (e.g. a thin space); never reached by the total post-patch spec |

There is **no consumed `axiom` and no A-reference** in this bundle. The lookup
table and the spacing-form list are not unchanged *external callees* — they are
fixed literal data the changed function `__init__` carries inline. Every impl op
is therefore R/I (a value-level transliteration of repo data + stdlib string
primitives), validated wholesale by **G-CONF** against the gold-patched printer.
Consequently this bundle ships **no `axiom_check.py`** and **G-AX skips**
(gates.py: "no axiom_check.py (no axioms in bundle)"). Axiomatizing
`mul_symbol_table` would violate SPEC_GUIDE directive 7 (an axiom must be about a
real callee the changed function *calls but does not change*); here it is part of
the function under change, so it is modeled directly, not assumed.

The pre-patch repo behavior the change fixes (refinement audit only, not in the
consumer spec view): both separators were obtained by a bare table index
(`mul_symbol_table[self._settings['mul_symbol']]` and
`mul_symbol_table[self._settings['mul_symbol'] or 'dot']`), so any symbol not
among the four named keys raised `KeyError` and the constructor failed.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self._settings['mul_symbol']` — `None` or a `str` | `sym : Option String` | `None` ↔ `none`; a `str s` ↔ `some s` (Python `str` ↔ Lean `String`, value-level — only whole-string equality, `or`-falsiness, `.strip()` and set membership are observed, never per-codepoint indexing) |
| `mul_symbol_table[k]` (raises `KeyError` if `k` absent) | `mulTable k : Option String` | a present key ↔ `some v` with `v` the mapped separator; an absent key ↔ `none` (the `KeyError`) |
| `mul_symbol or 'dot'` | `numKey sym` | `None`/`""` (falsy) ↔ `none`/`some ""` → `some "dot"`; any other `str` ↔ itself |
| `mul_symbol.strip()` | `pyStrip (sym.getD "")` | Python `str.strip()` strips the FULL Unicode `str.isspace()` set (U+0009–U+000D, U+001C–U+001F, U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000). `pyStrip` drops exactly that set (`pyWhitespace`) from both ends. NOTE: Lean's builtin `String.trim` strips only `' '`, `'\t'`, `'\n'`, `'\r'` and is NOT a faithful model — e.g. it leaves a form feed `'\x0c'` in place where `str.strip()` removes it (the G-PANEL-2 counterexample); hence the explicit `pyWhitespace`/`pyStrip` transliteration. |
| `mul_symbol.strip() in ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']` | `spacingSyms.contains (pyStrip (sym.getD ""))` | substring-set membership ↔ `List.contains` over the same seven string literals |
| the pair `(self._settings['mul_symbol_latex'], self._settings['mul_symbol_latex_numbers'])`, OR the `KeyError` the constructor raises | `Except MulErr (String × String)` | `Except.ok (a, b)` ↔ a constructor that completes with those two separator settings; `Except.error MulErr.unresolved` ↔ the constructor raising `KeyError` |

Notes that fix the abstraction boundary (so the model is neither too strong nor
too weak):

* **Both separators are observed, never assumed.** The post-patch constructor is
  total (never raises): the first separator is the table value when the symbol is
  named, otherwise the symbol itself; the second is the table value for the
  fallback key when present, otherwise the dot when the stripped symbol is one of
  the seven spacing-only forms, otherwise the symbol itself. Both legs are
  G-CONF-checked against the real gold-patched printer (the table/whitelist are
  the changed function's own inline data — repo code copied into the shadow, not
  an axiom).
* **`KeyError` is reachable only pre-patch.** On the gold-patched printer every
  symbol completes, so `Except.error MulErr.unresolved` is UNREACHABLE through
  the patched oracle. It is the modeling vehicle the prepatch uses to reject an
  unrecognized symbol; its divergence from the total spec is what G-DIFF
  observes. It is never tied to a live callee, so there is no axiom to check.
* **`'\\'`-prefixed literals.** In the Python source `'\\'` denotes a single
  backslash character; the seven whitelist entries are therefore `""`, `" "`,
  `"\"`, `"\,"`, `"\:"`, `"\;"`, `"\quad"`. In Lean each backslash is written
  `\\`, so e.g. `"\\,"` is the thin-space symbol `\,`.

## 3. Provenance (no axioms, no A-references — all R/I)

There is **no consumed `axiom` and no A-reference** in this bundle (directive 7).
The changed computation is modeled **directly**; the only constructs lifted from
the repo are *the changed function's own inline data* (the four-entry named table
and the seven-form spacing list) and stdlib string primitives (`or`-falsiness,
`str.strip()`, list membership). None is an unchanged external callee, so nothing
is axiomatized and there is no `axiom_check.py`; **G-AX skips**. Every impl op is
R/I and is refuted (if wrong) wholesale by **G-CONF**:

* **§3.1 `mulTable`** — the four-entry named-symbol table, transliterated from the
  `mul_symbol_table` literal `__init__` builds inline. G-CONF copies the same
  literal into the shadow and diffs the resulting `(mul_symbol_latex,
  mul_symbol_latex_numbers)` pair against the real gold-patched printer over the
  full fuzz domain; any wrong value surfaces as a disagreement.
* **§3.2 `spacingSyms` + `numKey` + strip** — the dot-fallback decision for the
  numeric separator. G-CONF asserts, over boundary + fuzzed symbols, that the
  real gold-patched printer's `mul_symbol_latex_numbers` equals the shadow
  computation (`numKey` fallback, spacing-set membership of the stripped symbol,
  dot vs passthrough) and its `mul_symbol_latex` equals the table-or-passthrough
  computation. The strip is modeled by `pyStrip`/`pyWhitespace` — the full
  Unicode whitespace set of Python `str.strip()` — and the G-CONF boundary
  inputs include the control/Unicode whitespace symbols (`\x0b`, `\x0c`,
  `\x1c`–`\x1f`, NEL, NBSP, U+1680, U+2000–U+200A, U+2028/29, U+202F, U+205F,
  U+3000) plus the non-whitespace look-alikes ZWSP and U+180E, so a wrong
  whitespace predicate surfaces as a disagreement.

## 4. G-CONF fuzz seed

`conformance_check.py` is seeded `SEED = 13798`, `N_FUZZ = 100_000`. Inputs:
`None`, `""`, the four named keys, the F2P thin-space symbol `\,`, the other six
spacing-only forms, the full control/Unicode whitespace boundary set for the
strip model (§3.2), and randomized arbitrary symbols (latex commands, plain
strings, whitespace-wrapped spacing forms). The oracle is the real gold-patched
`LatexPrinter`; the shadow is the R/I transliteration of the impl region.
