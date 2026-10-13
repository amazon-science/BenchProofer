# mapping.md — sympy__sympy-14976

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9cbea134220b0b951587e11b63e2c832c7246cbc`, states the type
abstraction, and gives the provenance of the unchanged callee (validated
against the real SymPy helper by `axiom_check.py` / G-AX).

Repo file under change: `sympy/printing/pycode.py`.

## 1. Symbol ↔ repo binding

The model function name (`render_mpf_ratio`) is deliberately **non-echoing**:
it does not token-overlap the patched repo method (`_print_Rational`) nor the
patched class (`MpmathPrinter`). The true repo binding lives here in
mapping/meta only, never in the consumer spec view.

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_mpf_ratio(p_digits, q_digits)` | `MpmathPrinter._print_Rational(self, e)` — added at `sympy/printing/pycode.py:335` by the patch (the method does not exist pre-patch; the class is at `pycode.py:314`, the immediately-preceding `_print_Float` at `pycode.py:325`) | the modeled changed renderer: produces the source text for a Rational under the mpmath lambda printer |
| `ctor()` *(deep model — A-reference)* | `self._module_format('mpmath.mpf')` — `PythonCodePrinter._module_format`, `sympy/printing/pycode.py:113` | pure spec: the fixed fully-qualified constructor token `mpmath.mpf`. Under the renderer's default `fully_qualified_modules=True` setting, `_module_format('mpmath.mpf')` returns `'mpmath.mpf'` verbatim. Validated `ctor()` == real helper output by axiom_check.py (G-AX); NOT consumed as an axiom. |
| `rendered(p, q)` *(deep model — A-reference)* | the patched method body `'{0}({1})/{0}({2})'.format(self._module_format('mpmath.mpf'), e.p, e.q)` (`pycode.py:335-340` post-patch) | pure spec: the rendered text `ctor '(' p ')' '/' ctor '(' q ')'`. The changed string construction is modeled DEEPLY (fold-free concatenation), validated against the real renderer by axiom_check.py (G-AX). |

The pre-patch repo behaviour the change overrides (referenced by the refinement
audit, not from the consumer spec view): with no `_print_Rational` on
`MpmathPrinter` or its `PythonCodePrinter`/`CodePrinter` bases, a Rational is
dispatched to `StrPrinter._print_Rational`
(`sympy/printing/str.py:594-600`):

```python
def _print_Rational(self, expr):
    if expr.q == 1:
        return str(expr.p)
    else:
        if self._settings.get("sympy_integers", False):
            return "S(%s)/%s" % (expr.p, expr.q)
        return "%s/%s" % (expr.p, expr.q)
```

i.e. a Rational `p/q` (q != 1, `sympy_integers` off — the printer's default)
renders as the bare `"%s/%s" % (p, q)` → e.g. `Rational(1,2)` → `"1/2"`,
`Rational(232,3)` → `"232/3"`. Neither operand is wrapped in `mpmath.mpf(...)`,
so the quotient is computed by ordinary (limited-precision) division in the
lambdified function. This is the bug the issue reports
(`lambdify(modules='mpmath')` reduced-precision `nsolve`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `e.p` (Python `int`, the Rational numerator) rendered by `'{1}'.format(...)` ≡ `str(e.p)` | `p_digits: List[int]` — the decimal digit string of the numerator as code points | `str(e.p)[k]` ↔ `p_digits[k] == ord(str(e.p)[k])`; the format-field `{1}` substitution ↔ the identity inclusion of `p_digits` into the result. The tested change is independent of which digits appear (it is about WHAT WRAPS them), so the digit string is carried opaquely as `List[int]`. |
| `e.q` (Python `int`, the Rational denominator) rendered by `'{2}'.format(...)` ≡ `str(e.q)` | `q_digits: List[int]` — the decimal digit string of the denominator as code points | as above for `{2}` ↔ `q_digits`. |
| the returned `str` | `List[int]` of code points; specification over `PSeq[int]` via `ToSeq` | `str` concatenation ↔ list `+`; `str` content ↔ `PSeq[int]`; an empty `str` ↔ `[]`. |
| `'{0}({1})/{0}({2})'.format(C, p, q)` template (`{0}` = the constructor token, used twice) | the concatenation `ctor() + '(' + p + ')' + '/' + ctor() + '(' + q + ')'` | the format template is a fixed interleaving of the literal tokens `( ) /` with the field substitutions; the model spells out the same interleaving with `+`. `(`=40, `)`=41, `/`=47. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `ctor` / `rendered` deep model ↔ the patched renderer + `_module_format` (A-reference)

**Callee (unchanged):** `PythonCodePrinter._module_format(self, 'mpmath.mpf')`
(`sympy/printing/pycode.py:113-121`). The patch does NOT change this helper; it
only calls it. Under the printer's default settings
(`_default_settings` includes `fully_qualified_modules=True`, `pycode.py:90-97`,
and `MpmathPrinter` does not override it), the body is:

```python
def _module_format(self, fqn, register=True):
    parts = fqn.split('.')
    if register and len(parts) > 1:
        self.module_imports['.'.join(parts[:-1])].add(parts[-1])
    if self._settings['fully_qualified_modules']:
        return fqn                       # <- 'mpmath.mpf' returned verbatim
    else:
        return fqn.split('(')[0].split('[')[0].split('.')[-1]
```

so `_module_format('mpmath.mpf')` returns the constant string `'mpmath.mpf'`
(the `register` branch is a side effect on `module_imports` that does not affect
the return value). **Flag dependency:** this constant return holds under
`fully_qualified_modules=True`, which is the default and is what the F2P test
`test_MpmathPrinter` exercises (it constructs `MpmathPrinter()` with no
settings). Recorded so G-AX fuzzes the default configuration.

`ctor()` encodes that constant as code points
`[109,112,109,97,116,104,46,109,112,102]` = `mpmath.mpf`. The whole rendered
text is then the deep model `rendered(p, q)` = `ctor '(' p ')' '/' ctor '(' q
')'`, which is exactly the patched template
`'{0}({1})/{0}({2})'.format(C, p, q)` with `C = 'mpmath.mpf'`.

**Soundness check (G-AX):** `axiom_check.py` constructs the real
`MpmathPrinter` (default settings) and asserts, for many `(p, q)` boundary +
fuzz pairs (including the F2P `Rational(1,2)`, `q == 1`, large numerators,
negatives), that the real `MpmathPrinter()._print_Rational(Rational(p, q))`
string equals the deep model `rendered(str(p)-codepoints, str(q)-codepoints)`,
and that the real `_module_format('mpmath.mpf')` equals `ctor()`. It imports
only SymPy (the repo under test) — no stdlib axiom needed. Exit 0 iff sound.
