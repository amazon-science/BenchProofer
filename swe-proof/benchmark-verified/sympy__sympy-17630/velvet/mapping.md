# mapping.md — sympy__sympy-17630

Model ↔ repo symbol binding, type abstraction, and callee provenance.
All file:line references are at `base_commit`
`58e78209c8577b9890e957b624466e5beed7eb08`.

Repo file under change: `sympy/matrices/expressions/matexpr.py`.

## 1. Changed function under specification

| model symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `recombineMatrixNode (op leadingScalar matrixTerms : Int)` | the final recombination tail of the closure `_postprocessor` returned by `get_postprocessor(cls)` | `sympy/matrices/expressions/matexpr.py:597-631` (closure `_postprocessor`, the path taken when `matrices` is non-empty and `nonmatrices` is empty) |

The repo code at the modeled tail (`matexpr.py`, post-patch):

```python
def get_postprocessor(cls):
    def _postprocessor(expr):
        mat_class = {Mul: MatMul, Add: MatAdd}[cls]
        nonmatrices = []
        matrices = []
        for term in expr.args:
            if isinstance(term, MatrixExpr):
                matrices.append(term)
            else:
                nonmatrices.append(term)

        if not matrices:
            return cls._from_args(nonmatrices)

        if nonmatrices:
            ...            # the `nonmatrices` non-empty path — NOT modeled here
                           #   (Mul: absorb scalar into a matrix; Add: early return)

        if mat_class == MatAdd:                            # <-- the fix
            return mat_class(*matrices).doit(deep=False)
        return mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)
    return _postprocessor
```

`recombineMatrixNode` models the **tail reached when `matrices` is non-empty and
`nonmatrices` is empty** — the last two statements of `_postprocessor`. At that
point `cls._from_args(nonmatrices) == cls._from_args([])` is the operator's
scalar identity element (the `leadingScalar` parameter). The fix inserts the
`if mat_class == MatAdd: return mat_class(*matrices).doit(deep=False)` branch so
the additive case composes the matrix terms alone, instead of falling through to
the final line which prepends that scalar identity.

The control context that selects this tail — the term partition loop
(`matexpr.py:601-607`), the `if not matrices` guard (`:609-610`), and the `if
nonmatrices:` block (`:612-628`) — is NOT part of the modeled data flow; it
chooses the branch and is not modeled. (For the inputs the F2P tests exercise,
`nonmatrices` is empty, so the modeled tail is exactly the path taken.)

## 2. Type abstraction (opaque-handle model)

Symbolic expressions and class objects are modeled as opaque `Int` handles — the
Lean port of the "opaque integer handle" model (cf. sympy__sympy-13480). The
only property the proof relies on is that each composer / constructor /
class-object is a deterministic map or constant (a fixed argument denotes a
fixed result handle), so "compose the matrix terms" and "the operator in effect"
each denote a single well-defined value. This is exactly what `opaque : Int → Int`
and `opaque : Int` provide in Lean and what sympy guarantees (deterministic
construction; `Add`/`MatAdd` are module-level singletons, so the `==` class test
is deterministic). No richer property of the composers is used.

| repo reality | model |
|---|---|
| a sympy expression / args bundle (`Basic`/`Expr` or `*args` tuple) | opaque integer handle (`Int`) |
| the class object `Add` (the `cls` for the additive postprocessor) | the opaque distinguished handle `additiveOp : Int` |
| `mat_class(*matrices).doit(deep=False)` with `mat_class == MatAdd` | the opaque composer `additiveCombine : Int → Int` applied to `matrices` |
| `mat_class(...).doit(deep=False)` with `mat_class == MatMul` | the opaque composer `multiplicativeCombine : Int → Int` |
| `(cls._from_args(nonmatrices), *matrices)` — the args bundle that puts the leading scalar first | `withLeadingScalar : Int → Int → Int` applied to `(leadingScalar, matrices)` |
| `cls._from_args(nonmatrices)` when `nonmatrices == []` (the operator's scalar identity) | the `leadingScalar : Int` parameter |
| `mat_class == MatAdd` (class-object identity test) | `op = additiveOp` (decidable `Int` equality) |

`mat_class` is a bijective function of `cls` (`{Mul: MatMul, Add: MatAdd}`), so
the post-patch test `mat_class == MatAdd` is equivalent to `cls == Add`; the
model tests `op = additiveOp` (i.e. `cls is Add`), the same two-way split.
`opaque` (not `axiom`) is required: these symbols are referenced inside the
executable Velvet `do` block, and a bare `axiom` referenced in a `do` block
triggers Lean's code-generator error (`dependsOnNoncomputable`). `opaque` keeps
the value abstract for the proof (same weakest-contract semantics) while being
computable so the block elaborates.

## 3. Callee provenance (axioms region — all opaque, no asserted contract)

| model symbol | repo callee / constant | role |
|---|---|---|
| `additiveOp` | the class object `Add` (`sympy.core.add.Add`) used as `cls`; equivalently `MatAdd` after the `{Mul:MatMul, Add:MatAdd}` map | the distinguished additive operator the branch tests against |
| `additiveCombine` | `MatAdd(*matrices).doit(deep=False)` — `sympy.matrices.expressions.matadd.MatAdd` + `Basic.doit` | additive composition of the matrix terms alone |
| `multiplicativeCombine` | `MatMul(...).doit(deep=False)` — `sympy.matrices.expressions.matmul.MatMul` + `Basic.doit` | multiplicative composition (the unchanged else branch) |
| `withLeadingScalar` | the args tuple `(cls._from_args(nonmatrices), *matrices)` consumed by the composer constructor (`Basic.__new__`) | bundle constructor placing the leading scalar first |

Every symbol is an `opaque` free function or constant carrying **no asserted
`ensures`**; the proof relies only on opaque-determinism (a fixed argument → a
fixed result handle). This is the weakest sufficient contract (SPEC_GUIDE
directive 7) and cannot over-claim a value, identity, or raise behavior. They
are FREE — nothing to validate against the real callee, so **G-AX is skipped (no
`axiom_check.py`)**.

There is **no A-reference / deep model**: the operation the patch changes (the
choice of recombination args for the additive operator) is modeled directly with
the same control/data flow; the things made opaque (`Add`/`MatAdd`/`MatMul`, the
args constructor) are the UNCHANGED callees/constants the tail consults. No
changed operation is hidden behind an opaque symbol.

## 4. G-CONF fuzz seed

`conf_skip = true` (see meta.json / conformance_check.py). The modeled tail is a
SYMBOLIC operation over sympy `Basic`/`Expr` trees and class objects: the oracle
is sympy's symbolic engine itself (constructing `MatAdd(*matrices).doit()` vs
`MatAdd(S.Zero, *matrices).doit()` and observing whether the result is a
`ZeroMatrix` or collapses to the scalar `Zero`), which cannot be reproduced from
the opaque integer-handle abstraction. The impl region is entirely opaque /
A-tagged, so there is no DB-free numeric R/I shadow to differential-test. No fuzz
seed is pinned; G-CONF ships a `status=skip` stub. Soundness rests on G-VERIFY +
G-DIFF + G-RESOLVE + G-EQ.
