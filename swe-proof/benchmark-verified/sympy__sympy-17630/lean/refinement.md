# refinement.md — sympy__sympy-17630

Operation correspondence between `implementation_matrixSum` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the canonicalization of a matrix sum
(`MatAdd.doit`/`canonicalize`) is modeled DEEPLY as `canonicalizeMatrixSum`.
Every row is **R**, **A-reference**, or **I**. The R/I/A-reference legs are
differential-tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## The fix

```python
@@ def _postprocessor(expr):
                 return cls._from_args(nonmatrices + [mat_class(*matrices).doit(deep=False)])
+        if mat_class == MatAdd:
+            return mat_class(*matrices).doit(deep=False)
         return mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)
```

On the all-matrix-terms branch (`nonmatrices == []`), the pre-patch return is
`MatAdd(cls._from_args([]), *matrices).doit(deep=False)` =
`MatAdd(S.Zero, *matrices).doit(deep=False)` — a scalar `Zero` is seeded ahead of
the matrix terms. The fix returns `MatAdd(*matrices).doit(deep=False)` instead:
no scalar seed.

## `implementation_matrixSum` ↔ the fix

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `terms : List MatSumTerm` | the `matrices` list (all-matrix branch; `nonmatrices == []`) | R | each `MatrixExpr` term ↦ `zeroMatrix` (a `ZeroMatrix`) or `named name` (a `MatrixSymbol`). The scalar seed `S.Zero` is NOT present here — it is the pre-patch's `cls._from_args([])`, modeled as `scalarZero` and excluded by the precondition. |
| `canonicalizeMatrixSum terms` (no `scalarZero` prepended) | `MatAdd(*matrices).doit(deep=False)` | A-reference | the fix builds `MatAdd` over the matrix terms ONLY, then `doit`-canonicalizes. `canonicalizeMatrixSum` models `canonicalize`: `rm_id(ZeroMatrix/0)` ↦ `survivingNames` (drop identity terms), `sort(default_sort_key)` ↦ `mergeSort nameLe`. Validated == real `Add(*terms)` postprocessor output by G-CONF. |
| result `MatSum.matrix names` | the returned `MatAdd`/`MatrixSymbol`/`ZeroMatrix` (a matrix-valued object) | R | `MatSum.matrix []` ↦ `ZeroMatrix` (shape preserved); `MatSum.matrix [n]` ↦ a single `MatrixSymbol`; `MatSum.matrix [n₀,…]` ↦ a `MatAdd` with those args sorted. Crucially the result is always matrix-valued (carries a shape). |
| `return …` | `return …` | I | the postprocessor's return |

The PRE-PATCH op corresponding to the bug is the scalar-seed injection
`cls._from_args(nonmatrices)` = `S.Zero` prepended to the matrix terms, modeled
by `canonicalizeMatrixSum (MatSumTerm.scalarZero :: terms)` in
`Solution_prepatch.lean`. When all `terms` are `zeroMatrix`, `survivingNames` is
`[]` and the leading retained term is `scalarZero` ⇒ `MatSum.scalar` (a shapeless
scalar), exactly the `Zero`-vs-`ZeroMatrix` defect.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the matrix sum is built with the scalar identity
  seeded ahead of the matrix terms (`canonicalizeMatrixSum (scalarZero :: terms)`).
  On an all-identity input this yields `MatSum.scalar` instead of
  `MatSum.matrix []`, so the carried gold proof of `correct_matrixSum` fails to
  close on the `zeroMatrix` leading case (`MatSum.scalar = MatSum.matrix []` is
  false). This is exactly the `Zero`-without-`.cols` crash. (FAIL_TO_PASS:
  `test_issue_17624`, `test_zero_matrix_add`.)
