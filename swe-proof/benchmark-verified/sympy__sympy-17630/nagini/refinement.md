# refinement.md — sympy__sympy-17630

The operation-by-operation correspondence between `model.py`'s implementation
(the `postprocess` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement, refined carrier type), **A** (axiomatized callee —
**A-consumed**, the proof uses the axiom's `Ensures`, or **A-reference**, a deep
model validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The matrix-expression constructor post-processor — `get_postprocessor(cls)._postprocessor` (`sympy/matrices/expressions/matexpr.py:597-631`)

Gold hunk (the only change):
```
                 return cls._from_args(nonmatrices + [mat_class(*matrices).doit(deep=False)])

+        if mat_class == MatAdd:
+            return mat_class(*matrices).doit(deep=False)
         return mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)
```

The model collapses the rich expression machinery to the two **touched facets**
of the rebuilt matrix-domain combination — its matrix-term count
(`matrix_arg_count`) and whether a scalar coefficient sits among its top-level
arguments (`scalar_arg_present`). The control flow of `_postprocessor` (after the
`if not matrices` early return, which is out of scope — `num_matrices >= 1`)
maps op-for-op:

| # | model.py impl op (`postprocess`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `is_sum`, `num_matrices`, `num_scalars`, `has_explicit_matrix` | `cls` (→`mat_class`), `matrices`, `nonmatrices`, the `Mul` explicit-matrix probe | R | the carrier refinements of mapping.md §2: `is_sum` ↔ `cls == Add`; `num_matrices` ↔ `len(matrices)`; `num_scalars` ↔ `len(nonmatrices)`; `has_explicit_matrix` ↔ an absorbable explicit matrix factor. Every tested observation is on the two `Combo` facets. |
| A1t | `Requires(MustTerminate(2))` (and `MustTerminate(1)` on `Combo.__init__`) | `_postprocessor` always returns its rebuilt node to the `Add`/`Mul` constructor pipeline: a bounded, straight-line computation whose only loop is the `Mul` absorb loop over the finite `matrices` list (`matexpr.py:613-621`) | I | total-correctness obligation: the real callee terminates on every input, so the model must too. Without it a diverging impl (audited attack: `while True: pass` inserted into `_postprocessor`) satisfies the value postconditions only vacuously while hanging every matrix `Add`/`Mul` construction — it does NOT resolve (harness timeout, both F2P unresolved). Nagini's obligation system rejects it ("Obligation leak check failed"). |
| A2 | `if num_scalars > 0:` | `if nonmatrices:` (`matexpr.py:612`) | I | identical guard on the presence of a genuine scalar term. |
| A3 | `if not is_sum:` (the `Mul` branch) with `absorbed = has_explicit_matrix`; `if absorbed: return Combo(num_matrices, False)` else `return Combo(num_matrices, True)` | the `cls == Mul` absorb loop (`matexpr.py:613-621`) then fall-through to the final return `mat_class(cls._from_args(nonmatrices), *matrices)` (`matexpr.py:630`) | R + A-reference | when an explicit matrix factor absorbs the scalar, `nonmatrices` is cleared so no scalar argument remains (`scalar_arg_present == False`); otherwise the scalar coefficient `cls._from_args(nonmatrices)` leads the `MatMul` (`scalar_arg_present == True`). The unchanged `MatMul` constructor / absorb effect on the two facets is the **A-reference** validated == the real callee by G-AX. |
| A4 | `else: return Combo(num_matrices, False)` (the `is_sum` + genuine-scalar branch) | `return cls._from_args(nonmatrices + [mat_class(*matrices).doit(deep=False)])` (`matexpr.py:628`) | R + I | for `Add` with a genuine scalar, the scalar is held apart and the matrix-domain sum `MatAdd(*matrices)` is formed from the matrix terms ALONE — so the matrix-domain node carries no scalar argument (`scalar_arg_present == False`). Same control branch (I); the `MatAdd(*matrices)` facet is the matrix count (R). |
| A5 | `if is_sum: return Combo(num_matrices, False)` (no genuine scalar) | `if mat_class == MatAdd: return mat_class(*matrices).doit(deep=False)` (**the inserted fix**, `matexpr.py:628-629` post-patch) | I + R | the inserted fix builds the matrix-domain sum from the matrix terms alone, NOT collapsing the empty scalar collection into the additive identity — exactly `scalar_arg_present == False`. This is the discriminating step (see C). |
| A6 | `return Combo(num_matrices, False)` (`Mul`, no genuine scalar) | `return mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)` reached for `Mul` (`matexpr.py:630`) | A-reference | for `Mul` with no scalar, `cls._from_args([]) == Mul.identity == One()` is the trivial multiplicative coefficient, which `MatMul` drops — observably no scalar argument (`scalar_arg_present == False`). The drop of the multiplicative identity is the unchanged-`MatMul` **A-reference** validated by G-AX. This branch is IDENTICAL pre- and post-patch (the fix only intercepts `MatAdd`), so it is not part of the bug→fix delta. |

## B. The two `Combo` facets are the unchanged constructor behaviour (A-reference)

`Combo(matrix_arg_count, scalar_arg_present)` abstracts the rebuilt
`MatAdd`/`MatMul` node. There is **no consumed `@ContractOnly` axiom**: the
unchanged matrix-domain constructors and the scalar collapse/absorb helpers
contribute nothing to the touched facets beyond what the impl spells out, so
they are an **A-reference**, validated == the real callee by `axiom_check.py`
(G-AX), not consumed in the proof. The `axioms` region is intentionally empty.

| # | model.py construct | repo op | tag | justification |
|---|---|---|---|---|
| B1 | `Combo.matrix_arg_count == num_matrices` (every branch) | `*matrices` splat into `mat_class(...)` (`matexpr.py:628-630`), absorb loop preserves `len(matrices)` | A-reference | the rebuilt matrix-domain node is fed exactly the matrix terms; the count is preserved by the (unchanged) constructor; G-AX checks it against the real `Add`/`Mul` results. |
| B2 | `Combo.scalar_arg_present` per branch | whether `cls._from_args(nonmatrices)` is passed as a top-level argument of `mat_class(...)` | A-reference | the load-bearing facet; G-AX asserts the real callee's matrix-domain node carries a scalar argument exactly when the model says so. |

## C. The discriminating content of the change

The bug: the pre-patch final return `mat_class(cls._from_args(nonmatrices),
*matrices).doit(deep=False)` is reached for **`Add` with no genuine scalar
term** (`nonmatrices == []`), where `cls._from_args([])` evaluates to
`Add.identity == Zero()` — a **scalar** zero. Injecting it as
`MatAdd(Zero, *matrices)` contaminates the matrix-domain sum with a scalar; the
sum no longer presents the `.cols` matrix facet, so a subsequent block
multiplication raises `'Zero' object has no attribute 'cols'`. The fix
intercepts the `MatAdd` case (`if mat_class == MatAdd:`) and rebuilds the sum
from the matrix terms alone.

The discriminating case (modeled, tested): `is_sum == True`,
`num_scalars == 0`, `num_matrices >= 1`.
- **gold / model.py (A5):** `num_scalars > 0`? No → `is_sum`? Yes →
  `Combo(num_matrices, False)`. The matrix-domain sum carries NO scalar argument
  → stays a `MatrixExpr`.
- **pre-patch / model_prepatch.py:** the same case falls through to the
  reproduced pre-patch final return, which collapses the empty scalar collection
  into the additive identity and injects it → `Combo(num_matrices, True)`.

`model_prepatch.py` reproduces the pre-patch final return in exactly this branch
and **fails** the postcondition `Implies(is_sum, scalar_arg_present == False)`
— the single failing clause (G-DIFF). For the `Mul`-no-scalar branch (A6) the
prepatch agrees with the model (the multiplicative identity is dropped, so the
pre-patch and post-patch behaviours are observably identical there — the fix
does not touch `MatMul`), so the prepatch fails ONLY on the genuinely-fixed
behaviour. This is exactly the F2P pair: `Add(ZeroMatrix, ZeroMatrix) ==
ZeroMatrix` (a matrix zero, not scalar `Zero`) and `block_collapse(b*b*b)`
succeeding (the all-zero blocks stay matrices with a `.cols`).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely
*changed* — the choice to rebuild the matrix-domain sum from the matrix terms
alone rather than injecting the collapsed scalar identity — is modeled
**deeply** (the spelled-out branch logic over the two integer/bool facets in the
impl region), not hidden behind an axiom about the function under change. There
is **no consumed `@ContractOnly` axiom**: the only opaque sub-operations (the
unchanged matrix-domain constructors and the scalar collapse/absorb) are
**A-reference**s, validated == the real callee by G-AX. The `axioms` region is
intentionally empty.

## E. verify(model) ⇒ resolved

`postprocess` verifies only if (A5) for a SUM the result carries no scalar
coefficient argument — even with no genuine scalar term, so the additive
identity is not injected (`Implies(is_sum, scalar_arg_present == False)`) — and
only if (A3/A4/A6) the `Mul`/genuine-scalar branches keep their unchanged
behaviour, and only if (A1t) it actually terminates and returns its `Combo`
(the `MustTerminate(2)` obligation — a diverging impl that would satisfy the
value clauses vacuously while hanging the constructor pipeline is rejected by
Nagini's obligation system). By R (`cls`/`mat_class` ↔ `is_sum`; term lists ↔ counts; rebuilt node
↔ `Combo`) the verified function is the gold hunk up to the facet abstraction;
by G-AX the deep facet model equals the real `_postprocessor` behaviour
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited matrix-domain reference
— and the gold patch resolves (G-RESOLVE). The trust points are exactly the two
of PLAN §1.1: matrix-domain-callee soundness (G-AX) and refinement fidelity
(this document, G-EQ).
