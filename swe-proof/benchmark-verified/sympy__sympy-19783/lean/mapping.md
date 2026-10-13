# mapping.md — sympy__sympy-19783

## Symbol binding (file:line @ base_commit 586a4320)

Two independently-changed multiplication-dispatch methods, each deciding the
result of a product `self * other` from the runtime class of `other`.

| Lean symbol | Python symbol | file @ base_commit | lines |
|---|---|---|---|
| `implementation_conjugateProduct` / `problem_spec_conjugateProduct` / `correct_conjugateProduct` | `Dagger.__mul__` (added by patch) | `sympy/physics/quantum/dagger.py` | new method after `__new__` (post-patch lines 86-91); class `Dagger` at line 12 |
| `implementation_identityProduct` / `problem_spec_identityProduct` / `correct_identityProduct` | `IdentityOperator.__mul__` | `sympy/physics/quantum/operator.py` | 308-313 (class `IdentityOperator` at 249) |

## Type bijection (used by G-CONF + G-AX)

The result of either product is one of three abstract shapes; the only behavior
the issue + F2P tests pin is WHICH shape is produced as a function of the
right-operand's class. So the Python objects are abstracted to a finite operand
class and a finite result shape.

| Python runtime object (the `other` argument) | Lean `Operand` |
|---|---|
| `IdentityOperator()` instance | `Operand.identity` |
| an `Operator` instance that is NOT an `IdentityOperator` (e.g. `Operator('O')`) | `Operand.operator` |
| a `Dagger(...)` instance (a Hermitian-conjugate expression) | `Operand.conjugate` |
| any other expression (symbol, number, `Mul`, …) | `Operand.other` |

| Python returned object | Lean `Result` |
|---|---|
| `self` (the left factor returned unchanged) | `Result.lhs` |
| `other` (the right factor returned unchanged) | `Result.rhs` |
| `Mul(self, other)` (an unevaluated product of the two factors) | `Result.product` |

### Subclass fact that drives `identityProduct` (READ CAREFULLY)

`IdentityOperator` is a SUBCLASS of `Operator`
(`class IdentityOperator(Operator)`, operator.py:249). Therefore
`isinstance(other, (Operator, Dagger))` is **True** when `other` is an
`IdentityOperator`, a plain `Operator`, OR a `Dagger`. Hence in
`IdentityOperator.__mul__` the simplified (`return other`) branch fires for
`Operand.identity`, `Operand.operator`, AND `Operand.conjugate`; only
`Operand.other` falls through to `Mul(self, other)`. (Confirmed: the existing
test `assert isinstance(I * I, IdentityOperator)` — `I * I` returns the right
`I`, i.e. `Result.rhs`.)

`Dagger` is NOT a subclass of `Operator` (`class Dagger(adjoint)`,
`adjoint`⊂`Expr`); that is exactly why the pre-patch `IdentityOperator.__mul__`,
which tested only `isinstance(other, Operator)`, left `I * Dagger(O)`
unsimplified — the defect the patch fixes by adding `Dagger` to the tuple.

For `Dagger.__mul__` the test is `isinstance(other, IdentityOperator)`, true ONLY
for `Operand.identity`; every other operand class falls through to
`Mul(self, other)`.

## Callee provenance / flag deps

- No unchanged callee is consumed as an axiom. The dispatch (the `isinstance`
  class tests and the choice between returning a factor unchanged vs. an
  unevaluated product) is the MODELED change; it is spelled out structurally over
  the finite `Operand`/`Result` carriers. `Mul(self, other)` is abstracted to the
  opaque shape `Result.product` — its internal evaluation is irrelevant to the
  pinned behavior, so it is neither modeled deeply nor axiomatized.
- No configuration flags.

## G-CONF fuzz seed

`SEED = 19783` (also pinned in conformance_check.py).
