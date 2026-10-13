# mapping.md — sympy__sympy-13877

## Symbol binding (file:line @ base_commit 1659712001)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_firstNonzero` / `problem_spec_firstNonzero` / `correct_firstNonzero` | pivot selection inside the recursive `bareiss(...)` helper of `_eval_det_bareiss`: choosing the first entry of the first column that is not zero | `sympy/matrices/matrices.py:165-216` @ base_commit (edited hunk: lines `177-181`, `192-197`) |
| pre-patch pivot test (literal-zero truthiness) | `def _find_pivot(l): for pos,val in enumerate(l): if val: return (pos,val,None,None); return (None,)*4` then `pivot_pos,pivot_val,_,_ = _find_pivot(mat[:, 0])` | `matrices.py:177-181, 194-195` (pre-patch) |
| post-patch pivot test (real zero test) | `pivot_pos,pivot_val,_,_ = _find_reasonable_pivot(mat[:, 0], iszerofunc=_is_zero_after_expand_mul)` | `matrices.py:192-194` (post-patch) |
| the new zero test `_is_zero_after_expand_mul` | `def _is_zero_after_expand_mul(x): return expand_mul(x) == 0` | `matrices.py:42-45` (added by patch) |
| `isMathZero e` (mathematically-zero predicate) | `_is_zero_after_expand_mul(x)` i.e. `expand_mul(x) == 0` | the zero test the post-patch pivot search consumes |
| `eval e` (expression → coefficient list) | `expand_mul(x)` normalizing a polynomial expression to its canonical (coefficient) form | for integer polynomials in one symbol, `expand_mul(x)==0` ⟺ all coefficients vanish |

## What the function does (Bareiss pivot selection)

`_eval_det_bareiss` runs a recursive fraction-free Gaussian elimination. At each
recursion level it takes the first column `mat[:, 0]` and must choose a *pivot*:
the first entry that is not zero. The chosen pivot value then divides later
entries (`(pivot_val*… - …)/cumm`), so the pivot MUST be genuinely nonzero.

### The bug and the fix

Pre-patch, pivot selection used a local `_find_pivot` whose test was Python
truthiness (`if val:`). A sympy expression is truthy unless it is *literally* the
zero object `S.Zero`; a structurally non-trivial expression that is nonetheless
mathematically zero (e.g. a difference of products that cancels completely) is
truthy and was wrongly chosen as a pivot. Dividing by such a "pivot" produced a
`0/0` form that simplified to `nan`, and a downstream `nan` comparison raised
`TypeError: Invalid NaN comparison` (the reported crash on `det(Matrix([[i + a*j
…]]))` for `n ≥ 5`).

The patch routes pivot selection through the existing `_find_reasonable_pivot`
with `iszerofunc=_is_zero_after_expand_mul`, where
`_is_zero_after_expand_mul(x) = (expand_mul(x) == 0)`. This is a *real*
mathematical zero test: an entry that expands to `0` is now recognized as zero
and skipped, so the first GENUINELY nonzero entry is selected as the pivot. The
F2P determinants (`M(5).det() == 0`, `M(6)`, `M(7)`) now return `0` instead of
`nan`/raising.

The second gold hunk (`random_complex_number` gains an optional `tolerance`
keyword in `sympy/utilities/randtest.py`) is an auxiliary test-support change; it
is NOT exercised by the F2P test `test_determinant` and is out of the modeled
scope. The modeled, F2P-discriminating behavior is the pivot-selection fix.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| a column entry: a sympy expression in one symbol `a`, built from integer constants, `a`, `+`, `*`, unary `-` | `PExpr` (`const`/`sym`/`add`/`mul`/`neg`) | node-for-node AST bijection; `sym ↔ a` |
| the first column `mat[:, 0]` passed to the pivot search | `col : List PExpr` | element-wise, top-to-bottom order |
| `expand_mul(x)` canonical form / coefficients | `eval e : List Int` (little-endian coefficients) | for integer polynomials in one symbol the coefficient list is the canonical normal form |
| `_is_zero_after_expand_mul(x)` = `expand_mul(x)==0` | `isMathZero e : Bool` | `True ⟺ isMathZero e = true ⟺ all coefficients 0` |
| `_find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul)` → `(pos, val, _, _)` with `pos is not None` | `result = some (pos, val)` | the selected pivot offset + value |
| `… → (None, None, _, _)` (no nonzero entry) | `result = none` | column is entirely (mathematically) zero |

`PExpr` restricted to integer-coefficient univariate polynomials is sound for the
modeled path: it is the exact shape of the issue's entries (`i + a*j`), and on
that class `expand_mul(x)==0` agrees with "all coefficients zero" (which Lean
`isMathZero` decides). G-CONF fuzzes the broader expression tree (nested
`add`/`mul`/`neg`, including non-trivial cancellations) to validate the agreement.

## Callee provenance + flag dependencies

- No callee axiom is consumed. The zero test that the changed pivot search
  consumes (`_is_zero_after_expand_mul` / `expand_mul`) is modeled DEEPLY as
  `eval` / `isMathZero` (an A-reference validated by G-CONF against the real
  `_find_reasonable_pivot(..., iszerofunc=_is_zero_after_expand_mul)`), never
  axiomatized (§0.7). The operation the patch actually changes — replacing
  literal-zero truthiness with the real zero test — is captured by the difference
  between the pre-patch impl (literal-zero test, `x ≠ const 0`) and the
  post-patch impl (`isMathZero x = false`).
- `_find_reasonable_pivot`'s float/partial-pivoting branch (all-`Float`/`Integer`
  columns) is NOT on the modeled path: the issue's entries are symbolic
  (polynomials in `a`), which take the symbolic PASS-1 branch where the first
  `iszerofunc(x) == False` entry is returned. G-CONF constructs only symbolic
  (non-pure-numeric) columns, the configuration the bug manifests in.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
