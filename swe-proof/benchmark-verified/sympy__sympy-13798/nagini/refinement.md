# refinement.md — sympy__sympy-13798

The operation-by-operation correspondence between `model.py`'s implementation
(the `general_separator` and `numeric_separator` impl regions, the pure
derivations `general_sep_of` / `numeric_sep_of`, and the `trimmed` axiom)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses this axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The gold hunk (`sympy/printing/latex.py`, `LatexPrinter.__init__`)

```
- self._settings['mul_symbol_latex'] = mul_symbol_table[self._settings['mul_symbol']]
- self._settings['mul_symbol_latex_numbers'] = mul_symbol_table[self._settings['mul_symbol'] or 'dot']
+ try:
+     self._settings['mul_symbol_latex'] = mul_symbol_table[self._settings['mul_symbol']]
+ except KeyError:
+     self._settings['mul_symbol_latex'] = self._settings['mul_symbol']
+ try:
+     self._settings['mul_symbol_latex_numbers'] = mul_symbol_table[self._settings['mul_symbol'] or 'dot']
+ except KeyError:
+     if (self._settings['mul_symbol'].strip() in ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']):
+         self._settings['mul_symbol_latex_numbers'] = mul_symbol_table['dot']
+     else:
+         self._settings['mul_symbol_latex_numbers'] = self._settings['mul_symbol']
```

`mul_symbol_table = {None: r" ", "ldot": r" \,.\, ", "dot": r" \cdot ", "times": r" \times "}`.

## A. The general separator — `general_separator` ↔ `mul_symbol_latex`

| # | model.py impl op (`general_separator`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `sym: Optional[List[int]]` | `self._settings['mul_symbol']` (`None` or `str`) | R | `None`↔unset; `str`↔`List[int]` code points (mapping.md §2). |
| A2 | `sym is None -> [32]` | the table lookup `mul_symbol_table[None] == r" "` (the `try` succeeds for the `None` key) | R | `mul_symbol_table[None] == " "` ↔ `sep_blank() == PSeq(32)`. |
| A3 | `s == tok_dot()/tok_times()/tok_ldot() -> the matching separator literal` | `mul_symbol_table[mul_symbol]` for a recognised key (the `try` succeeds) | R + I | finite dict lookup ↔ key-equality selection; the literal code-point lists equal the dict values (mapping.md §1). |
| A4 | fall-through: copy `sym` into `res` element-wise and return it (`ToSeq(res) == ToSeq(sym)`) | `except KeyError: self._settings['mul_symbol_latex'] = self._settings['mul_symbol']` | R + I | the `KeyError` path returns the selector **verbatim**; the model's element-wise copy is the identity on the code-point list, i.e. `general_sep_of(sym) == ToSeq(sym)` for an unrecognised token. |

The whole derivation is captured by the pure `general_sep_of`; the impl mirrors
it branch-for-branch and the postcondition is `ToSeq(Result()) == general_sep_of(sym)`.

## B. The numeric separator — `numeric_separator` ↔ `mul_symbol_latex_numbers`

| # | model.py impl op (`numeric_separator`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `sym is None -> sep_dot()` | `mul_symbol_table[None or 'dot'] == mul_symbol_table['dot'] == r" \cdot "` (the `try` succeeds) | R + I | `None or 'dot' == 'dot'`; `mul_symbol_table['dot']` ↔ `sep_dot()`. |
| B2 | `s == tok_dot()/tok_times()/tok_ldot() -> the matching separator literal` | `mul_symbol_table[mul_symbol or 'dot']` for a recognised key (the `try` succeeds) | R + I | same as A3; for a non-`None` recognised key, `mul_symbol or 'dot' == mul_symbol`. |
| B3 | `t = trimmed(s)` | `self._settings['mul_symbol'].strip()` (inside `except KeyError`) | A-reference | `trimmed` models the unchanged builtin `str.strip` and is validated == the real callee by G-AX (mapping.md §3.1). It is **not consumed** by the proof: the numeric postcondition `ToSeq(Result()) == numeric_sep_of(sym)` discharges by functional congruence — impl and oracle both call the *same* `trimmed(s)` and take the same `is_spacing_only` branch, so they agree for *any* value of `trimmed`. (Verified empirically: replacing the axiom's `Ensures` with `Ensures(True)`, or a contradictory always-empty Ensures, still verifies.) `trimmed` is load-bearing only via refinement fidelity: the oracle's spacing-only test is the real `str.strip` behaviour exactly because G-AX checks `trimmed` ≈ `str.strip`. |
| B4 | `is_spacing_only(t) -> sep_dot()` | `if mul_symbol.strip() in ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']: mul_symbol_table['dot']` | R + I | finite-set membership ↔ the seven-way `==` disjunction over code-point sequences; the result `mul_symbol_table['dot']` ↔ `sep_dot()`. |
| B5 | fall-through: copy `sym` element-wise and return it | `else: self._settings['mul_symbol_latex_numbers'] = self._settings['mul_symbol']` | R + I | an unrecognised, non-spacing selector yields the selector verbatim. |

The whole derivation is captured by the pure `numeric_sep_of`; the impl mirrors
it branch-for-branch and the postcondition is `ToSeq(Result()) == numeric_sep_of(sym)`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The only library callee the *new* code
invokes and does not change — `str.strip()` — is modeled by the **A-reference**
`trimmed` axiom (an unchanged builtin), validated == the real callee by G-AX.
The proof does **not** consume this axiom's `Ensures` (replacing it with
`Ensures(True)`, or even a contradictory always-empty `Ensures`, still verifies
— the numeric postcondition discharges by functional congruence because impl and
oracle call the same `trimmed(s)` and branch identically); its guarantee comes
entirely from refinement fidelity (the oracle's spacing-only test is faithful to
the real callee only because `trimmed` ≈ `str.strip`, which is exactly what G-AX
validates). There is no axiom about the function under change: the changed logic
(the two `try/except` derivations, the spacing-only fall-back) is modeled
**deeply** as the spelled-out `general_sep_of` / `numeric_sep_of` and the
matching impl loops.

## D. The discriminating behaviour and the two prepatches

The change the F2P test observes (`sympy/printing/tests/test_latex.py`):

  * `latex(3*x**2*y, mul_symbol='\\,') == r"3\,x^{2}\,y"` — between symbols the
    selector `\,` is used **verbatim**. This exercises `general_separator`: for
    an unrecognised token the general separator is `ToSeq(sym)` (step A4). Pre-
    patch the unguarded `mul_symbol_table['\\,']` raises `KeyError` (the printer
    cannot even be built). `model_prepatch.py` reproduces the pre-patch
    "unrecognised selector not honoured" skeleton (the fall-through returns the
    blank `[32]`) and **fails** the postcondition
    `ToSeq(Result()) == general_sep_of(sym)` (which requires `[92,44]`).

  * `latex(1.5*3**x, mul_symbol='\\,') == r"1.5 \cdot 3^{x}"` — between numbers
    the selector `\,`, being spacing-only after trimming, is replaced by the
    centred dot. This exercises `numeric_separator`: steps B3+B4 force
    `sep_dot()`. `model_prepatch_2.py` reproduces the pre-patch skeleton (no
    spacing-only fall-back; the fall-through returns the blank `[32]`) and
    **fails** the postcondition `ToSeq(Result()) == numeric_sep_of(sym)` (which
    requires `sep_dot()`).

Two independently-fixed behaviours ⇒ two failing prepatches (G-DIFF), one per
derived setting.

## E. verify(model) ⇒ resolved

`general_separator`/`numeric_separator` verify only if their outputs equal the
exact derivations `general_sep_of`/`numeric_sep_of` of the selector — including
the verbatim-on-unrecognised behaviour (A4/B5) and the spacing-only→dot
behaviour (B3+B4) the F2P assertions demand. By R (`None`↔unset, `str`↔
`List[int]`, the finite-dict ↔ key-equality refinement) the verified
derivations equal the gold's two `try/except` assignments on the tested
selectors; by G-AX the `trimmed` axiom over-approximates the real `str.strip`.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited builtin — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX, the `trimmed` axiom) and refinement fidelity (this document,
G-EQ).
