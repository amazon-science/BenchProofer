# refinement.md — sympy__sympy-17630

Operation-by-operation correspondence between `Solution.lean`'s impl region
(`recombineMatrixNode`) and `patch.diff` (the gold patch, applied at
`base_commit`). Every row is tagged **R** (type refinement), **A-consumed**
(proof uses this opaque symbol's contract), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete operation). No
kind-3 (changed-but-inexpressible) step.

The patch adds a two-line branch to the tail of the closure `_postprocessor`
(`matexpr.py:597-631`), reached when the partitioned children are a non-empty
collection of matrix-valued terms with no scalar-valued terms left:

```python
+        if mat_class == MatAdd:
+            return mat_class(*matrices).doit(deep=False)
         return mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)
```

`recombineMatrixNode` models that tail. `cls._from_args(nonmatrices)` is, on this
path, the operator's scalar identity (`nonmatrices == []`); it is the
`leadingScalar` parameter.

| # | Solution.lean impl op | patch.diff / repo op (post-patch) | tag | justification |
|---|---|---|---|---|
| 1 | `if op = additiveOp then` | `if mat_class == MatAdd:` | A-consumed + R + I | `additiveOp` is the opaque model of the unchanged additive class object (`Add`/`MatAdd`); `=` on the `Int` handle refines the class-object identity test (R: handle equality ↔ class identity). `mat_class == MatAdd` ⇔ `cls == Add` since `mat_class = {Mul:MatMul, Add:MatAdd}[cls]` is a bijection (mapping.md §2). Identical two-way control split (I). |
| 2 | `return additiveCombine matrixTerms` (true branch) | `return mat_class(*matrices).doit(deep=False)` (the added line, `mat_class == MatAdd`) | A-consumed + R | `additiveCombine` is the opaque model of `MatAdd(*matrices).doit(deep=False)` — composing the matrix terms ALONE. `matrixTerms` (the collection of matrix-valued terms) is an `Int` handle refining the `*matrices` args (R). Identical control: the additive branch composes only the matrix terms. The proof consumes only its determinism. |
| 3 | `return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)` (else branch) | `return mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)` (the unchanged final line, reached when `mat_class == MatMul`) | A-consumed + R | `multiplicativeCombine` models `MatMul(...).doit(deep=False)`; `withLeadingScalar leadingScalar matrixTerms` models the args bundle `(cls._from_args(nonmatrices), *matrices)` that places the leading scalar-valued term first (R). `leadingScalar` is `cls._from_args(nonmatrices)` (= the multiplicative scalar identity on this path). Identical control: the non-additive branch keeps the leading scalar. |
| 4 | `if/else` two-way branch | `if mat_class == MatAdd: … ; return …` (guarded-branch + fallthrough) | I | identical concrete two-way control flow: the additive case is the guarded branch, every other case is the fallthrough. |

## Notes

- **No A-reference, no deep model.** The changed operation (which args the
  additive composer receives) is modeled directly with the same control/data
  flow; the things made opaque (`Add`/`MatAdd`/`MatMul`, the args constructor)
  are the UNCHANGED callees/constants the tail consults. There is no changed
  operation hidden behind an opaque symbol, so no A-reference and no
  axiom_check.py.
- **A-consumed contract is just determinism.** The opaque symbols carry no
  asserted `ensures`; the proof relies only on opaque-determinism (a fixed
  argument → a fixed result handle). This is the weakest sufficient contract
  (SPEC_GUIDE directive 7) and cannot over-claim a value, identity, or raise. As
  FREE symbols there is nothing to validate against a real callee, so G-AX is
  skipped.
- **The discriminating I is "additive case composes the matrix terms ALONE."**
  The observable, behavior-fixing operation the patch changes is the ARGS the
  additive composer receives. `Solution.lean` composes `additiveCombine
  matrixTerms` (no leading scalar). `Solution_prepatch.lean` composes
  `additiveCombine (withLeadingScalar leadingScalar matrixTerms)` — the leading
  scalar is carried into the additive case too, exactly mirroring the pre-patch
  fall-through `MatAdd(cls._from_args([]), *matrices).doit()`, where the injected
  scalar identity `S.Zero` collapses the all-`ZeroMatrix` sum to the scalar
  `Zero` (which has no `.cols` — the AttributeError in the issue when the result
  is re-used in a later block-multiply). The discriminating postcondition
  `out = if op = additiveOp then additiveCombine matrixTerms else …` is
  unprovable for any impl whose additive branch is not exactly `additiveCombine
  matrixTerms` — which is why the prepatch fails (`additiveCombine x` and
  `additiveCombine (withLeadingScalar leadingScalar x)` are distinct opaque
  applications loom cannot equate), and any wrong additive args are rejected.

## verify(Solution) ⇒ resolved

`recombineMatrixNode` verifies only if, under the additive operator, the result
is the additive composition of the matrix terms ALONE (row 2) and the
multiplicative case keeps the leading scalar (row 3). By R (handle ↔
expression/class) the verified branch equals the gold patch's recombination tail
on the path the F2P tests exercise (matrices non-empty, nonmatrices empty);
G-CONF is skipped (conf_skip; symbolic op, no DB-free numeric R/I shadow); the
opaque symbols are FREE (no G-AX obligation). The gold patch resolves
(G-RESOLVE). Residual trust: the opaque-determinism assumption on the unchanged
callees and the type bijection in mapping.md, both audited by G-EQ.
