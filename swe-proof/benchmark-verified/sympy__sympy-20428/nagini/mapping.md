# mapping.md — sympy__sympy-20428

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c0e85160406f9bf2bcaa2992138587668a1cd0bc`, states the type
abstraction, and gives the provenance of the deep-model reference (the symbolic
zero-test) the bundle validates against.

Repo file under change: `sympy/polys/domains/expressiondomain.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `coeff_truthy(c)` | `ExpressionDomain.Expression.__bool__(f)` — `sympy/polys/domains/expressiondomain.py:122` (body line 123) | the modeled changed function: truthiness of a symbolic ground-domain coefficient |
| `strip_constant_len(c)` | the leading-zero stripping of a constant univariate poly that *consumes* `__bool__`: `dup_strip(f)` — `sympy/polys/densebasic.py:252` (the `if not f or f[0]` guard, line 265), as reached from `Poly`/`DMP` construction and `clear_denoms` | the observable consequence: a length-1 coefficient list collapses to the canonical empty list (the zero polynomial) iff the single coefficient denotes zero |
| `Coeff.mzero` *(deep-model facet — A-reference)* | `Expr.is_zero` — `sympy/core/expr.py` / `assumptions` machinery (the property the fix re-routes the test through, `not f.ex.is_zero`) | the MATHEMATICAL-value facet: 1 iff the expression denotes zero |
| `Coeff.lit0` | "the structural form IS the bare literal `Integer(0)`", i.e. the predicate `f.ex == Integer(0)` that `f.ex != 0` decides structurally | the STRUCTURAL facet the buggy test keyed on |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): the body `return f.ex != 0`
(`expressiondomain.py:123`), which compares the stored expression structurally
against the literal `0`. `Expr.__ne__`/`Expr.__eq__` on a non-evaluated symbolic
expression decide *structural* (syntactic-canonical) (in)equality, NOT
mathematical value — so `f.ex != 0` is `True` for any `f.ex` whose canonical
form is not the bare `Integer(0)`, even when `f.ex` denotes zero.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `ExpressionDomain.Expression` instance (an `EX` coefficient wrapping `f.ex`, a SymPy `Expr`) | `Coeff` class with two int flags | `Coeff.lit0 == 1` ↔ `f.ex == Integer(0)` (structural / canonical-form equality with the bare zero literal); `Coeff.mzero == 1` ↔ `f.ex.is_zero is True` (mathematical zeroness) |
| `bool(coeff)` / `coeff.__bool__()` returning a Python `bool` | `coeff_truthy(c) -> bool` | `True` ↔ truthy (non-zero coefficient) |
| the stored dense univariate representation of a CONSTANT polynomial, a list `[coeff]` or `[]` (`DMP.rep`) | the rep *length* (int, 0 or 1) returned by `strip_constant_len` | `len == 0` ↔ `DMP([], EX, None)` (the canonical zero poly, the desired `Poly(0, x, domain='EX').rep`); `len == 1` ↔ `DMP([coeff], EX, None)` (a retained constant; the buggy `DMP([EX(0)], EX, None)` of the issue) |

`dup_strip([c])` (`densebasic.py:265`) returns `f` unchanged when `f[0]` is
truthy and `[]` (via the empty fall-through) when it is falsy; the constant case
is exactly "keep `[c]` iff `bool(c)`", which is what `strip_constant_len`
encodes by its returned length. The structural facet `lit0` cannot be the
truthiness test because a coefficient can denote zero (`mzero == 1`) while not
being the bare literal (`lit0 == 0`) — the discriminating state the issue's
`EX(...)` coefficient occupies.

### Total-correctness obligation (`MustTerminate`)

Both modeled functions require `MustTerminate` (`coeff_truthy` measure 2,
`strip_constant_len` measure 3; the `Coeff` constructor measure 1). Repo
counterpart: the real `__bool__` is a straight-line read (`not f.ex.is_zero`)
and `dup_strip` on a constant list is a bounded scan — both *return*; their
callers (`dup_strip`'s `if not f or f[0]` guard, `Poly`/`DMP` construction)
consume the returned value. A diverging implementation satisfies the value
postconditions only vacuously and its faithful real patch hangs the F2P test
(recorded: atk_8 timed out after 240s), so termination is part of the
behaviour under spec, not an artifact of the encoding.

### Class invariant (constructor `Coeff.__init__`)

`Implies(lit0 == 1, mzero == 1)`: a coefficient whose structural form is the
bare zero literal necessarily denotes zero. The converse is deliberately NOT
imposed — `lit0 == 0, mzero == 1` is the bug-triggering coefficient (a
non-trivial structural shape that nonetheless denotes zero). This invariant is
the SymPy fact that `Integer(0).is_zero is True`.

## 3. Deep-model reference provenance (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `Coeff.mzero` deep facet ↔ `Expr.is_zero` (A-reference)

**Reference:** the SymPy assumption property `Expr.is_zero` (the property the
fix routes the truthiness test through: `not f.ex.is_zero`). The changed
operation — "decide truthiness by mathematical zeroness, not structural shape"
— is modelled **deeply** by giving the coefficient an explicit `mzero` facet
and defining `coeff_truthy(c) == (c.mzero == 0)`. There is **no `@ContractOnly`
axiom** the proof consumes; `mzero` is a modeled field, and the deep model is
validated equal to the real callee out-of-band by `axiom_check.py` (G-AX).

The behavioural facts the model relies on, all standard SymPy semantics:

- `Expr.is_zero` is the *mathematical* zero predicate: it is `True` iff the
  expression denotes 0, independent of its structural shape. SymPy's polynomial
  machinery is the canonical source of "non-obvious" zeros: an `EX` coefficient
  produced by symbolic cancellation can have an elaborate radical form whose
  `is_zero` is `True` (the issue's `clear_denoms()` coefficient). Docs:
  https://docs.sympy.org/latest/guides/assumptions.html (the `is_zero`
  assumption).
- `f.ex != 0` (the pre-patch test) uses `Expr.__ne__`, which on an unevaluated
  symbolic expression returns *structural* inequality with the literal
  `Integer(0)`. It is `True` whenever `f.ex` is not canonically the bare
  `Integer(0)`, even if `f.ex.is_zero is True`. Source: `expressiondomain.py:123`
  (pre-patch), `sympy/core/expr.py` relational/`__eq__` handling.
- `Integer(0).is_zero is True` and `Integer(0) != 0` is `False` — so on the
  bare literal the two tests AGREE (`lit0 == 1 ==> mzero == 1`, both report
  "zero"); they DISAGREE exactly on `lit0 == 0, mzero == 1`.

**Soundness check (G-AX):** `axiom_check.py` constructs real `EX` coefficients
(`ExpressionDomain.Expression`) over a battery of SymPy expressions — bare
zero, ordinary non-zero literals/symbols, and crucially *structurally
non-trivial expressions that denote zero* (cancelling radical/rational
combinations, including the exact `clear_denoms()` coefficient from the issue)
— and asserts for each that
  `bool(coeff) == (not coeff.ex.is_zero)`  (the FIX = the model `coeff_truthy`)
and that on the bare zero literal the structural test agrees, while on the
denoting-zero-but-non-trivial expressions the OLD structural test `coeff.ex != 0`
disagrees (witnessing the modeled discrimination). It further reconstructs the
issue's `clear_denoms()` / `dup_strip` consequence: the constant poly built from
a denoting-zero coefficient strips to `DMP([], EX, None)` under the fix and to
`DMP([EX(0)], EX, None)` under the old test. Imports only `sympy` (the repo
under test); exit 0 iff every observation matches the model.
