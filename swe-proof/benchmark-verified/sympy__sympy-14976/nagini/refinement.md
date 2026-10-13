# refinement.md — sympy__sympy-14976

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_mpf_ratio` impl region and the deep pure models `ctor` /
`rendered`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed**, the proof uses the
axiom's `Ensures`, vs **A-reference**, a deep model validated == the real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The renderer site — `MpmathPrinter._print_Rational` (added at `sympy/printing/pycode.py:335`)

Gold hunk (the method is newly added to `MpmathPrinter`):
```python
+    def _print_Rational(self, e):
+        return '{0}({1})/{0}({2})'.format(
+            self._module_format('mpmath.mpf'),
+            e.p,
+            e.q,
+            )
```

| # | model.py impl op (`render_mpf_ratio`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `p_digits: List[int]` | `e.p` (int), substituted as `'{1}'` ≡ `str(e.p)` | R | `int` rendered by `str(...)` ↔ its decimal digit string as code points `List[int]` (mapping.md §2). The tested behaviour is independent of the digits, so they are carried opaquely. |
| A2 | parameter `q_digits: List[int]` | `e.q` (int), substituted as `'{2}'` ≡ `str(e.q)` | R | as A1 for the denominator. |
| A3 | `out = out + [109,112,109,97,116,104,46,109,112,102]` (the `ctor()` constant), appended twice (before `p_digits` and before `q_digits`) | `self._module_format('mpmath.mpf')` substituted as `'{0}'`, used twice | A-reference | `_module_format` is an UNCHANGED helper the new method calls; under the default `fully_qualified_modules=True` it returns the constant `'mpmath.mpf'` (mapping.md §3.1). Modeled DEEPLY by the pure constant `ctor()`, validated `ctor() == real _module_format('mpmath.mpf')` by axiom_check.py (G-AX). Not a consumed axiom. |
| A4 | the literal tokens `[40]` `(`, `[41]` `)`, `[47]` `/` interleaved exactly as `ctor '(' p ')' '/' ctor '(' q ')'` | the format template `'{0}({1})/{0}({2})'` literal characters `( ) / ( )` | I | identical concrete characters in identical order; `'{0}({1})/{0}({2})'.format(C,p,q)` is the same interleaving of `C`, `p`, `q` with `(`, `)`, `/` that the impl builds with `+` (mapping.md §2). |
| A5 | `return out` (a `List[int]`), whose `ToSeq` equals `rendered(ToSeq(p_digits), ToSeq(q_digits))` | `return '...'.format(...)` (the rendered `str`) | R | `str` ↔ `List[int]` content; list `+` ↔ `str` concatenation (mapping.md §2). The method's caller (`StrPrinter.doprint` → `_print`) returns this string verbatim. |

The discriminating content of the change — BOTH operands wrapped in
`mpmath.mpf(...)` rather than divided bare — lives in the postcondition
`ToSeq(Result()) == rendered(...)`, whose `rendered` prepends `ctor '('` before
each digit string and closes with `')'`. The pre-patch behaviour (inherited
`StrPrinter._print_Rational`, the bare `"%s/%s" % (p, q)`) renders
`p_digits + '/' + q_digits` with no constructor wrapping; `model_prepatch.py`
reproduces exactly that and **fails** the postcondition
`ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits))` — which is
precisely the spec sensing the change (G-DIFF, fails at `model_prepatch.py:83`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the renderer's string construction wrapping each operand in
`mpmath.mpf(...)` — is modeled **deeply** (the spelled-out concatenation
`rendered`, consumed via the postcondition), not hidden behind an axiom about
the function under change: there is **no consumed `_print_Rational` axiom**. The
only callee touched, `_module_format`, is **unchanged** and appears solely as
the **A-reference** `ctor()` that G-AX validates the deep model against. There
are no `@ContractOnly` consumed axioms in this bundle.

## C. verify(model) ⇒ resolved

`render_mpf_ratio` verifies only if its output equals the exact constructor-
wrapped concatenation `rendered(p, q)` = `ctor '(' p ')' '/' ctor '(' q ')'`
(steps A3, A4, A5). By R (`int`→digit-string `List[int]`, `str`↔`List[int]`,
`+`↔concatenation) the verified renderer equals the patched
`'{0}({1})/{0}({2})'.format(self._module_format('mpmath.mpf'), e.p, e.q)` on the
tested Rationals; by G-AX the deep model `ctor()` equals the real
`_module_format('mpmath.mpf')` under the default flag, and the full `rendered`
equals the real `MpmathPrinter()._print_Rational` output (A-reference).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited unchanged callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly those of PLAN §1.1:
axiom/deep-model soundness (G-AX) and refinement fidelity (this document, G-EQ).
The F2P test `test_MpmathPrinter` asserts
`MpmathPrinter().doprint(Rational(1,2)) == 'mpmath.mpf(1)/mpmath.mpf(2)'`,
exactly the `rendered` structure with `p_digits = [49]` (`'1'`),
`q_digits = [50]` (`'2'`).
