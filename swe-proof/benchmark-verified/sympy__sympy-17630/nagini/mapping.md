# mapping.md — sympy__sympy-17630

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 58e78209c8577b9890e957b624466e5beed7eb08`, states the type
abstraction, and gives the provenance of each callee the deep model is validated
against (kind A-reference — checked by G-AX / axiom_check.py).

Repo file under change: `sympy/matrices/expressions/matexpr.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `postprocess(is_sum, num_matrices, num_scalars, has_explicit_matrix)` | the closure `_postprocessor(expr)` returned by `get_postprocessor(cls)` — `sympy/matrices/expressions/matexpr.py:597-631` (the modeled function; the patched hunk is its final-return region, lines 628-630) | the modeled changed function: rebuilds a matrix-domain combination from a `Mul`/`Add` of mixed matrix and scalar terms |
| `Combo(matrix_arg_count, scalar_arg_present)` | the rebuilt matrix-domain node `MatAdd(...)` / `MatMul(...)` produced by `_postprocessor` (`matexpr.py:628-630`; for `MatAdd`, the patched line) | the result, described by its two touched facets |
| `Combo.matrix_arg_count` | number of matrix terms fed into `mat_class(...)` (the `*matrices` splat) | touched facet: matrix-term count of the rebuilt combination |
| `Combo.scalar_arg_present` | whether `cls._from_args(nonmatrices)` (a SCALAR) is passed as a top-level argument of `mat_class(...)` | touched facet: scalar-coefficient argument present in the rebuilt combination |

The pre-patch behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the unconditional final return
`mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)`
(`matexpr.py:630`). When `cls == Add` and `nonmatrices == []`,
`cls._from_args([])` is `Add.identity == Zero()` (a SCALAR zero —
`sympy/core/numbers.py:3968 Add.identity = Zero()`, via
`AssocOp._from_args` returning `cls.identity` for empty args,
`sympy/core/operations.py:62-63`); injecting it into `MatAdd(Zero, *matrices)`
contaminates the matrix-domain sum with a scalar, which downstream lacks the
`.cols` matrix facet (the reported crash). The fix
(`matexpr.py:628-629` post-patch) intercepts the `MatAdd` case and rebuilds
`mat_class(*matrices).doit(deep=False)` from the matrix terms alone.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `cls` ∈ `{Mul, Add}` selecting `mat_class` ∈ `{MatMul, MatAdd}` (`matexpr.py:600`) | `is_sum: bool` | `is_sum == True` ↔ `cls == Add` (`mat_class == MatAdd`); `is_sum == False` ↔ `cls == Mul` (`mat_class == MatMul`) |
| `matrices` — the list of terms with `isinstance(term, MatrixExpr)` (`matexpr.py:603-605`) | `num_matrices: int >= 1` | `num_matrices == len(matrices)`; the precondition `num_matrices >= 1` is the `if not matrices: …` early return (`matexpr.py:609-610`) being out of scope |
| `nonmatrices` — the remaining (scalar) terms (`matexpr.py:606-607`) | `num_scalars: int >= 0` | `num_scalars == len(nonmatrices)`; a genuine scalar term is present iff `num_scalars > 0` |
| the `Mul` absorb loop: `if not matrices[i].is_MatrixExpr: matrices[i] = matrices[i].__mul__(...); nonmatrices = []` (`matexpr.py:613-621`) | `has_explicit_matrix: bool` | an explicit (non-`MatrixExpr`, e.g. `ImmutableDenseMatrix`) matrix factor is present to absorb the scalar coefficient; when present the scalar is folded into a matrix factor and `nonmatrices` is cleared |
| the rebuilt `MatAdd`/`MatMul` node | `Combo` (two int/bool facets) | `matrix_arg_count` ↔ count of matrix args; `scalar_arg_present` ↔ a scalar `cls._from_args(nonmatrices)` sits among the node's top-level args |

`MatAdd`/`MatMul` node identity, the `.doit(deep=False)` canonicalisation, and
the concrete term payloads are abstracted away: the F2P-observable property is
exactly whether a scalar coefficient contaminates the matrix-domain sum
(facet `scalar_arg_present`), which is what the spec pins.

**Termination (total correctness).** The real `_postprocessor`
(`matexpr.py:597-631`) is a bounded, straight-line computation (its only loop
is the `Mul` absorb loop over the finite `matrices` list) that always returns
its rebuilt node to the `Add`/`Mul` constructor pipeline. The spec carries
this as `Requires(MustTerminate(2))` on `postprocess` (and `MustTerminate(1)`
on the `Combo` constructor it calls): an implementation that diverges before
returning would satisfy the value postconditions only vacuously — the exact
class exploited by the audited attack that inserted `while True: pass` into
`_postprocessor`, hanging every matrix `Add`/`Mul` construction (the SWE-bench
harness times out with both F2P unresolved). Nagini's obligation system
rejects such an impl ("Obligation leak check failed").

## 3. Callee provenance (kind A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. The matrix-domain combination
rebuilt by the post-processor is modeled **deeply** by the two integer/bool
facets of `Combo`; the unchanged matrix-domain constructors
(`MatAdd.__new__`/`doit`, `MatMul.__new__`/`doit`) and the scalar
collapse/absorb helpers (`AssocOp._from_args`, the `Mul` absorb loop)
contribute nothing to the touched facets beyond what the impl spells out.

### 3.1 `postprocess` deep facet model ↔ real `_postprocessor` (A-reference)
**Callee:** the matrix-expression constructor post-processor, reached through the
public `Add(...)` / `Mul(...)` constructors (the post-processor is registered at
`matexpr.py:634-637`, `Basic._constructor_postprocessor_mapping[MatrixExpr]`).
The deep model `postprocess` is validated equal to the real callee out-of-band
by `axiom_check.py` (G-AX), which builds representative `Add`/`Mul` expressions
over matrix symbols, explicit matrices, zero matrices, and scalar terms and
asserts the two facets match:

- **SUM, no genuine scalar (the fixed case):** the rebuilt matrix-domain sum is
  formed from the matrix terms alone and carries NO scalar argument
  (`scalar_arg_present == False`); the additive identity `Add._from_args([]) ==
  Zero()` is NOT collapsed in. The rebuilt sum therefore stays a `MatrixExpr`,
  and an all-(matrix-)zero sum stays a matrix zero (`Add(ZeroMatrix, ZeroMatrix)
  == ZeroMatrix`), never a bare scalar `Zero`.
- **SUM with a genuine scalar:** the scalar is held apart (`Add(scalar,
  MatAdd(*matrices))`, `matexpr.py:628`); the matrix-domain sum is still formed
  from the matrix terms alone (`scalar_arg_present == False`).
- **PRODUCT:** a scalar coefficient is absorbed into an explicit matrix factor
  when present (`scalar_arg_present == False`), else leads the matrix-domain
  product (`scalar_arg_present == (num_scalars > 0 and not has_explicit_matrix)`);
  the matrix factor count is preserved.

`axiom_check.py` also reproduces the exact FAIL_TO_PASS witnesses:
`block_collapse(b*b*b)` for `b = BlockMatrix([[a, z], [z, z]])` does NOT raise
and equals `BlockMatrix([[a**3, z], [z, z]])` (the all-zero blocks stay matrices
with a `.cols`), and `Add(ZeroMatrix(2, 2), ZeroMatrix(2, 2)) == ZeroMatrix(2,
2)`. It imports only `sympy` (the repo under test with the patch applied); exit
0 iff every observation matches the deep model.

**Soundness evidence (host pre-check, before in-container G-AX):** run against a
patched sympy, `axiom_check.py` passes all observations; run against the
pre-patch `_postprocessor` (the fix reverted), the SUM-of-matrices construction
contaminates `MatAdd` with the scalar additive identity and breaks (the matrix
zero degrades to a scalar `Zero` — the reported `'Zero' object has no attribute
'cols'` failure mode at sympy 1.5; a `TypeError: Mix of Matrix and Scalar
symbols` at later versions). The discriminating facet `scalar_arg_present` is
exactly what separates the two.
