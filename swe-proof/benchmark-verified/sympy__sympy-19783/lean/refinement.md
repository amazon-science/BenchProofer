# refinement.md — sympy__sympy-19783

Operation-by-operation correspondence between the two modeled implementations
(Solution.lean impl regions) and `patch.diff`. Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

## `implementation_conjugateProduct` ↔ `Dagger.__mul__` (dagger.py, added by patch)

```python
def __mul__(self, other):
    from sympy.physics.quantum import IdentityOperator
    if isinstance(other, IdentityOperator):
        return self
    return Mul(self, other)
```

| # | Lean impl op | patch.diff Python op | tag |
|---|---|---|---|
| 1 | `if isIdentityKind other then` | `if isinstance(other, IdentityOperator):` | R |
| 2 | `return Result.lhs` | `return self` | R |
| 3 | `return Result.product` | `return Mul(self, other)` | R |

## `implementation_identityProduct` ↔ `IdentityOperator.__mul__` (operator.py:308)

```python
def __mul__(self, other):
    if isinstance(other, (Operator, Dagger)):   # patch widens from (Operator,)
        return other
    return Mul(self, other)
```

| # | Lean impl op | patch.diff Python op | tag |
|---|---|---|---|
| 4 | `if isOperatorKind other \|\| isConjugateKind other then` | `if isinstance(other, (Operator, Dagger)):` | R |
| 5 | `return Result.rhs` | `return other` | R |
| 6 | `return Result.product` | `return Mul(self, other)` | R |

## Notes

- **Every step is R — no A.** The dispatch (the `isinstance` class tests + the
  choice between returning a factor unchanged and forming the unevaluated product)
  IS the modeled change; it is spelled out structurally over the finite
  `Operand`/`Result` carriers. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op. The `axioms` region is empty; **G-AX skips**.
- **R bijections (mapping.md):**
  - `isinstance(other, IdentityOperator)` ↔ `isIdentityKind other`.
  - `isinstance(other, (Operator, Dagger))` ↔ `isOperatorKind other ||
    isConjugateKind other`. KEY: `IdentityOperator` ⊂ `Operator`, so this is true
    for the identity element too; `Dagger ⊄ Operator`, so the `Dagger` disjunct is
    what the patch adds (`isConjugateKind`). The pre-patch `(Operator,)` test ↔
    `isOperatorKind other` alone.
  - `return self` ↔ `Result.lhs`; `return other` ↔ `Result.rhs`;
    `Mul(self, other)` ↔ `Result.product` (the unevaluated product is an opaque
    result shape — its internal construction is irrelevant to the pinned behavior).
- **The fix, per behavior:**
  - **conjugateProduct (`Dagger.__mul__`):** pre-patch the method is ABSENT, so a
    conjugated operator falls back to the generic `Expr.__mul__` and every product
    — even `Dagger(O) * I` — is an unevaluated product. `Solution_prepatch_1.lean`
    returns `Result.product` unconditionally; the spec demands `Result.lhs` when
    `other = identity`, so its `correct_conjugateProduct` is unprovable. (F2P
    `test_dagger_mul`: `Dagger(O)*Dagger(I) == Dagger(O)` — `Dagger(I)` is the
    identity, absorbed.)
  - **identityProduct (`IdentityOperator.__mul__`):** pre-patch the tuple is
    `(Operator,)` only, so a conjugated operator is not absorbed and
    `I * Dagger(O)` is left unevaluated. `Solution_prepatch_2.lean` tests
    `isOperatorKind other` alone; the spec demands `Result.rhs` when
    `other = conjugate`, so its `correct_identityProduct` is unprovable. (F2P
    `test_identity`: `I * Dagger(O) == Dagger(O)`.)
- **G-CONF** mechanically refutes the R legs: a Python shadow of each impl is
  diffed against an in-process replica of the corresponding post-patch `__mul__`
  (driven by the runtime-class tests, with `IdentityOperator ⊂ Operator` honored)
  over ≥1e5 fuzzed operands.
