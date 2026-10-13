# refinement.md — sympy__sympy-13798

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveMulSeparators` `do` block, with the pure models
`mulTable`/`numKey`/`spacingSyms` and the `resolveSpec` pair) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection) or **I** (identical concrete op). EVERY step is R or I — there is **no
axiom** in this bundle (no A-consumed, no A-reference): the change is entirely
self-contained in `__init__`, so its data (the named-symbol table, the spacing
list) is the changed function's own inline data, not an unchanged external
callee. Hence the bundle ships **no `axiom_check.py`** and **G-AX skips**.

All R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); this narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The separator resolution — `LatexPrinter.__init__` (`sympy/printing/latex.py`)

Gold hunk (latex.py:158–177 post-patch):
```
-        self._settings['mul_symbol_latex'] = \
-            mul_symbol_table[self._settings['mul_symbol']]
-        self._settings['mul_symbol_latex_numbers'] = \
-            mul_symbol_table[self._settings['mul_symbol'] or 'dot']
+        try:
+            self._settings['mul_symbol_latex'] = \
+                mul_symbol_table[self._settings['mul_symbol']]
+        except KeyError:
+            self._settings['mul_symbol_latex'] = \
+                self._settings['mul_symbol']
+        try:
+            self._settings['mul_symbol_latex_numbers'] = \
+                mul_symbol_table[self._settings['mul_symbol'] or 'dot']
+        except KeyError:
+            if (self._settings['mul_symbol'].strip() in
+                    ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']):
+                self._settings['mul_symbol_latex_numbers'] = \
+                    mul_symbol_table['dot']
+            else:
+                self._settings['mul_symbol_latex_numbers'] = \
+                    self._settings['mul_symbol']
```

| # | Solution.lean impl op (`resolveMulSeparators`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `sym : Option String` | `self._settings['mul_symbol']` (`None` or `str`) | R | `None ↔ none`, `str s ↔ some s` (mapping.md §2). G-CONF bridges via the real `mul_symbol` kwarg. |
| A2 | `mulTable : Option String → Option String` | the literal `mul_symbol_table` built inline in `__init__` (`latex.py:152–157`) | I | `mulTable` transliterates, value-for-value, the four-entry dict + default the changed function carries inline; `none` result ↔ the `KeyError` a bare index raises. NOT an external callee — it is the changed function's own data, so it is modeled directly (no axiom). G-CONF copies the identical literal into the shadow and diffs the result. |
| A3 | `first` = `match mulTable sym with \| some v => v \| none => sym.getD ""` | `try: …=mul_symbol_table[mul_symbol] except KeyError: …=mul_symbol` | I | concrete control flow: the `match`/`try-except` are the same dispatch (table value on a hit, the symbol verbatim on a miss). Both the hit/miss split and the table data of A2 are **I**. G-CONF transliterates it. |
| A4 | `numbers` = `match mulTable (some (numKey sym)) with \| some v => v \| none => if spacingSyms.contains (pyStrip (sym.getD "")) then " \cdot " else sym.getD ""` | `try: …=mul_symbol_table[mul_symbol or 'dot'] except KeyError: if mul_symbol.strip() in [..7 forms..]: …=mul_symbol_table['dot'] else: …=mul_symbol` | I | `numKey sym` = `mul_symbol or 'dot'` (falsy → `'dot'`). On a miss: `spacingSyms` is the verbatim seven-form list (inline data, **I**) and `pyStrip` ↔ `.strip()` — `pyStrip` drops the FULL Unicode `str.isspace()` whitespace set (`pyWhitespace`: U+0009–U+000D, U+001C–U+001F, U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028/29, U+202F, U+205F, U+3000) from both ends, exactly matching Python `str.strip()` (Lean's builtin `String.trim` strips only the four ASCII forms and would diverge on e.g. `'\x0c'`); the dot value ` \cdot ` is `mulTable (some "dot")` inlined. Every sub-op — the lookup, the membership test, the branch structure — is concrete and identical; G-CONF transliterates it whole (boundary inputs include the control/Unicode whitespace symbols and the ZWSP/U+180E non-whitespace look-alikes). |
| A5 | `return Except.ok (first, numbers)` | the constructor completes with the two `self._settings[...]` assignments | R | `Except.ok (a, b)` ↔ a completed constructor whose two settings are `a`, `b` (mapping.md §2). The post-patch constructor is TOTAL: both `try/except` legs assign, so no `KeyError` escapes ⇒ the result is always `ok`. |

Discriminating content of the change — a symbol NOT among the four named keys
(e.g. the thin space `\,`, the F2P case) — lives in the totality of the
resolution: the spec resolves such a symbol to `Except.ok (sym, dot-or-sym)`,
whereas the pre-patch bare index `mul_symbol_table[mul_symbol]` raises `KeyError`
(modeled `Except.error MulErr.unresolved`). `Solution_prepatch.lean` reproduces
the bare-index skeleton and **fails** `out = resolveSpec sym` exactly on the
`mulTable sym = none` goal (it yields `error` where the spec requires `ok`),
which is the F2P input `latex(3*x**2*y, mul_symbol='\\,')` (G-DIFF).

## B. No axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — making the two
separator assignments total instead of a bare table index — is modeled
**directly** by the `match` ladder of A3/A4/A5 (concrete control flow, **I**)
over the inline table `mulTable` and list `spacingSyms` (also **I**: the changed
function's own literal data, copied value-for-value). There is **no axiom**
(neither A-consumed nor A-reference): nothing is assumed about the function under
change, and the data lifted (the table, the list) is part of that very function,
not an unchanged external callee — so per SPEC_GUIDE directive 7 it must be
modeled directly, not axiomatized. The stdlib string ops (`or`, `.strip()`,
membership) are concrete (**I**). Consequently there is no `axiom_check.py` and
**G-AX skips**; all fidelity rests on G-CONF.

## C. verify(Solution) ⇒ resolved

`resolveMulSeparators` verifies only if its output equals `resolveSpec sym` =
`Except.ok (firstSep sym, numSep sym)`: a named symbol resolves to its standard
separators (A2/A3/A4), and any other symbol is accepted — used verbatim for the
general separator and dot-or-verbatim for the numeric one (A3/A4) — so the
resolution is total (A5). By R (`Option String ↔ None\|str`, the pair ↔ the two
settings) the verified resolution equals the gold-patched `__init__` separator
derivation on the tested symbols; by G-CONF the R/I transliteration of the
resolution (including the inline table/list copied verbatim) agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point of plan §1.1 in play here is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness leg.
