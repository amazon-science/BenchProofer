# refinement.md — operation correspondence (sympy__sympy-14976)

Maps every op in `implementation_mpfRational` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patch ADDS `MpmathPrinter._print_Rational(self, e)`:

```python
def _print_Rational(self, e):
    return '{0}({1})/{0}({2})'.format(
        self._module_format('mpmath.mpf'),
        e.p,
        e.q,
        )
```

i.e. it formats the template `"{0}({1})/{0}({2})"` with
`{0} = self._module_format('mpmath.mpf')`, `{1} = e.p`, `{2} = e.q`. The Lean
impl reproduces exactly that string assembly as a concatenation of the same
pieces.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `p q : Int` | `e.p`, `e.q` (the rational's integer numerator/denominator) | R | `int` ↔ `Int` bijection (mapping.md) |
| 2 | `let func := mpfName` | `self._module_format('mpmath.mpf')` (= `'mpmath.mpf'` under default `fully_qualified_modules=True`) | A-reference | UNCHANGED callee modeled deeply as the constant `mpfName`; validated == real `_module_format('mpmath.mpf')` by G-AX. NOT axiomatized. |
| 3 | `func ++ "(".toList ++ intText p ++ ")/".toList` | template prefix `'{0}({1})/'` filled with `{0}`, `{1}=e.p` | I / A-reference | literal concatenation `{0}`,`(`,`str(e.p)`,`)/` ; `intText` validated == Python `str(int)` by G-AX |
| 4 | `++ func ++ "(".toList ++ intText q ++ ")".toList` | template suffix `'{0}({2})'` filled with `{0}`, `{2}=e.q` | I / A-reference | literal concatenation `{0}`,`(`,`str(e.q)`,`)` |

No A-consumed rows: the proof discharges the string concatenation, `mpfName`
and `intText` directly; no UNCHANGED callee property is *assumed* (the two
callee models are A-references, executable-checked by G-AX, not proof axioms).
No changed-inexpressible op.

## The discriminating clause (G-DIFF)
Pre-patch, `MpmathPrinter` had no `_print_Rational`; the call fell through the
MRO to `StrPrinter._print_Rational`, which returns `"%s/%s" % (e.p, e.q)` — the
bare textual quotient `<p>/<q>` with no backend constructor. The prepatch impl
models exactly that fallback: `intText p ++ "/".toList ++ intText q`
(e.g. `Rational(1,2)` → `"1/2"`).

The frozen `problem_spec_mpfRational` pins the result to
`mpmath.mpf(<p>)/mpmath.mpf(<q>)`. For ANY `(p, q)` (e.g. the F2P input `1/2`)
the fallback string `"1/2"` ≠ `"mpmath.mpf(1)/mpmath.mpf(2)"`, so
`correct_mpfRational` cannot close against the frozen spec on the prepatch impl —
the G-DIFF signal. The post-patch impl satisfies the spec on every input.
