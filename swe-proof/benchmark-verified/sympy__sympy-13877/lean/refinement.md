# refinement.md — sympy__sympy-13877

Operation correspondence between `implementation_firstNonzero` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The mathematical zero test the changed pivot
search consumes (`_is_zero_after_expand_mul` = `expand_mul(x)==0`) is modeled
DEEPLY as the `eval` / `isMathZero` helpers (an A-reference, validated by G-CONF
against the real `_find_reasonable_pivot(..., iszerofunc=_is_zero_after_expand_mul)`).
The operation the patch changes — replacing literal-zero truthiness with the real
zero test in pivot selection — is captured by the difference between the
pre-patch impl (`x ≠ const 0`) and the post-patch impl (`isMathZero x = false`).
Every row is **R**, **A-reference**, or **I**.

## The gold patch (modeled hunk)

```python
-        # XXX included as a workaround for issue #12362 ...
-        def _find_pivot(l):
-            for pos,val in enumerate(l):
-                if val:
-                    return (pos, val, None, None)
-            return (None, None, None, None)
 ...
-            pivot_pos, pivot_val, _, _ = _find_pivot(mat[:, 0])
+            pivot_pos, pivot_val, _, _ = _find_reasonable_pivot(mat[:, 0],
+                                         iszerofunc=_is_zero_after_expand_mul)
```
plus the added helper `_is_zero_after_expand_mul(x): return expand_mul(x) == 0`.

The surrounding recursion, the `if pivot_pos == None: return S.Zero` guard, and
the elimination step are unchanged; only the pivot-selection zero test changes.
(The `random_complex_number` `tolerance` hunk in `randtest.py` is auxiliary
test-support, not exercised by the F2P test — out of modeled scope; see
mapping.md.)

## `implementation_firstNonzero` ↔ the post-patch pivot search

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| input `col : List PExpr` | `mat[:, 0]` — the first column passed to `_find_reasonable_pivot` | R | column of symbolic entries ↦ `List PExpr` (univariate integer-polynomial AST) |
| `for x in col do … i := i + 1` (scan top to bottom) | `_find_reasonable_pivot` PASS 1: `for i, x in enumerate(col): is_zero = iszerofunc(x)` | I | first-to-last scan, same order |
| `if isMathZero x = false then return some (i, x)` | `if is_zero == False: return (i, x, False, …)` with `iszerofunc=_is_zero_after_expand_mul` | **A-reference** | the EDITED op: the real zero test is `expand_mul(x)==0`; modeled deeply as `isMathZero` (= all polynomial coefficients zero), validated by G-CONF |
| `isMathZero x` via `eval x` (coefficient list, all `== 0`) | `_is_zero_after_expand_mul(x)` = `expand_mul(x) == 0` | A-reference | `eval` reproduces `expand_mul`'s canonical (coefficient) normal form for univariate integer polynomials |
| `return none` (after the loop) | `return (None, None, …)` — no genuinely nonzero entry found | R | "no pivot" ↦ `none`; downstream maps to `S.Zero` determinant |

The pre-patch leg (`Solution_prepatch.lean`) replaces the zero test with
`x ≠ PExpr.const 0` — the literal-zero truthiness of the old `_find_pivot`'s
`if val:`. That is the discriminating clause G-DIFF observes: on a column whose
first entry is a non-trivial-but-mathematically-zero expression (e.g.
`add sym (neg sym)` = `a + (-a)`), the pre-patch impl returns `some (0, x)` —
violating `isMathZero val = false` — whereas the post-patch impl skips it and
either selects a later genuine pivot or returns `none`. This mirrors the real bug
exactly: the old test selected a mathematically-zero pivot, producing the `0/0 →
nan` crash.

The R / I / A-reference legs are differential-tested by `conformance_check.py`
(G-CONF) against the real `_find_reasonable_pivot` with the patched zero test;
G-AX is a skip stub (no consumed callee axiom).
