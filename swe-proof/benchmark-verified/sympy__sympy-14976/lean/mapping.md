# mapping.md — symbol binding & type bijection (sympy__sympy-14976)

## Modeled function
- **Lean** `implementation_mpfRational : Int → Int → List Char`
  (arguments `p` = numerator, `q` = denominator)
- **Python** `MpmathPrinter._print_Rational(self, e)` —
  `sympy/printing/pycode.py:335-341 @ 9cbea13` (the method the patch ADDS).
  It is the per-`Rational` rendering hook of the arbitrary-precision
  floating-point lambda printer. Before the patch the class had no
  `_print_Rational`, so the call resolved up the MRO
  (`MpmathPrinter → PythonCodePrinter → CodePrinter → StrPrinter`) to
  `StrPrinter._print_Rational` (`sympy/printing/str.py:594-600`), which renders
  `"%s/%s" % (e.p, e.q)` — the plain textual quotient `<p>/<q>`.

The observable behavior the F2P test (`test_MpmathPrinter`) demands:
`p.doprint(Rational(1, 2)) == 'mpmath.mpf(1)/mpmath.mpf(2)'`. The result must now
wrap each integer operand in the backend floating-point constructor instead of
emitting a bare integer quotient, so downstream `nsolve`/`lambdify` evaluate the
rational at full precision rather than as a reduced-precision Python division.

## Inputs / domain
A `Rational` instance `e` carries integer fields `e.p` (numerator) and `e.q`
(denominator, `q > 0`); for any value reaching `_print_Rational`, `q ≠ 1` (SymPy
canonicalizes `q == 1` rationals to `Integer`, dispatched by `_print_Integer`,
never `_print_Rational`). The Lean model takes `p q : Int` directly; the spec is
stated for all integer `p, q` (the discriminating behavior — wrapping each
operand in the constructor — is uniform in `p, q`, so no `q ≠ 1` precondition is
needed to pin it).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `Rational` field `e.p` (`int`) | `p : Int` | numerator, may be negative |
| `Rational` field `e.q` (`int`) | `q : Int` | denominator, `> 0` in practice |
| `str(int)` substituted via `'{1}'.format(...)` | `intText n = (toString n).toList` | decimal text, `-` prefix iff negative; matches Python `str(int)` for the integer domain |
| `self._module_format('mpmath.mpf')` | `mpfName = "mpmath.mpf".toList` | under default `fully_qualified_modules=True`, returns the dotted name verbatim |
| output `str` | `List Char` | the rendered expression `mpmath.mpf(<p>)/mpmath.mpf(<q>)` |
| `'{0}({1})/{0}({2})'.format(mpfName, e.p, e.q)` | `mpfName ++ "(" ++ intText p ++ ")/" ++ mpfName ++ "(" ++ intText q ++ ")"` | concatenation of the same literal pieces |

## Callee provenance
- `self._module_format('mpmath.mpf')` is an UNCHANGED callee the new method
  calls. Under the printer's default settings (`fully_qualified_modules=True`)
  it returns its argument `'mpmath.mpf'` unchanged (it only registers an import
  side-effect and, when `fully_qualified_modules=False`, would shorten the name —
  not the modeled configuration). We model its result DEEPLY as the constant
  `mpfName = "mpmath.mpf".toList`, an **A-reference** validated by G-AX against
  the real `MpmathPrinter()._module_format('mpmath.mpf')`. NOT axiomatized.
- `str(int)` (Python's int → decimal text) ↔ `intText` (`toString` on `Int`).
  This is an A-reference too: G-AX checks `str(n) == intText(n)` agreement over
  fuzzed integers (the only divergence risk is sign/formatting, validated to
  agree on the integer domain).
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.

## Flag dependency
The modeled configuration is the printer's default: `fully_qualified_modules=True`.
Under this flag `_module_format('mpmath.mpf')` returns `'mpmath.mpf'`. G-AX
constructs `MpmathPrinter()` with defaults, matching this flag.

## G-CONF fuzz seed
Pinned seed: **14976**. ≥10^5 fuzzed `(p, q)` integer pairs (q drawn from
positive integers, p from signed integers, including 0, ±1, large magnitudes and
the issue value 232/3), bridged str↔List Char, diffed against the post-patch
`MpmathPrinter._print_Rational`.
