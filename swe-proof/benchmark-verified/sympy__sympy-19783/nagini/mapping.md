# mapping.md — sympy__sympy-19783

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 586a43201d0357e92e8c93548d69a9f42bf548f4`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
methods the deep models are validated against by axiom_check.py / G-AX).

Repo files under change:
`sympy/physics/quantum/operator.py`, `sympy/physics/quantum/dagger.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `identity_mul(other_kind)` | `IdentityOperator.__mul__(self, other)` — `sympy/physics/quantum/operator.py:308` (body 310-313) | modeled changed function (site 1): left-multiplication by the identity element |
| `dagger_mul(other_kind)` | `Dagger.__mul__(self, other)` — `sympy/physics/quantum/dagger.py` (NEW method added by the patch after `__new__`, post-patch lines 86-91) | modeled changed function (site 2): left-multiplication by a Hermitian-conjugate factor |
| `is_operator_like(k)` *(deep model — A-reference)* | `isinstance(other, (Operator, Dagger))` test in `IdentityOperator.__mul__` (post-patch `operator.py:310`) restricted to the operator branch; pre-patch `isinstance(other, Operator)` | the membership test site 1 dispatches on |
| `is_identity(k)` *(deep model — A-reference)* | `isinstance(other, IdentityOperator)` test in `Dagger.__mul__` (post-patch `dagger.py`) | the membership test site 2 dispatches on |
| `is_conjugate(k)` *(deep model — A-reference)* | `isinstance(x, Dagger)` (`Dagger` defined `sympy/physics/quantum/dagger.py:13`, subclasses `adjoint`, NOT `Operator`) | the family the patch newly absorbs in site 1 and the LHS family of site 2 |
| `Product` (`is_mul`, `result_kind`, `left_kind`, `right_kind`) | the value returned by each `__mul__`: either one operand (a collapse) or `Mul(self, other)` (`sympy.core.mul.Mul`) | abstract record of the product step's return |

Pre-patch repo facts that make the bug observable (for the refinement audit,
not referenced from the consumer spec view):
- `Operator.__mul__` (`operator.py:179-184`) already returns `self` for an
  `IdentityOperator` right operand — so `O * I == O` works pre-patch.
- `IdentityOperator.__mul__` pre-patch (`operator.py:310`) tests only
  `isinstance(other, Operator)`. `Dagger(O)` is NOT an `Operator` (it subclasses
  `adjoint`), so `I * Dagger(O)` falls to `Mul(self, other)` → unsimplified.
- `Dagger` has NO `__mul__` pre-patch, so `Dagger(O) * I` uses the inherited
  `Expr.__mul__` (`sympy/core/expr.py:202`) → `Mul(Dagger(O), I)` → unsimplified.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a SymPy quantum expression operand (`Operator`, `IdentityOperator`, `Dagger`, scalar `Symbol`/`Integer`/…) | an integer "kind" tag `other_kind ∈ {0,1,2,3}` | `0` ↔ a plain `Operator` that is not a `Dagger`; `1` ↔ an `IdentityOperator`; `2` ↔ a `Dagger`; `3` ↔ any other factor. The classification mirrors the `isinstance` tests the real `__mul__` methods perform; `IdentityOperator` is a subclass of `Operator` (so kind 1 is operator-like), and `Dagger` is NOT (kind 2 is excluded from `is_operator_like`). |
| the return of `__mul__`: one operand, or `Mul(self, other)` | `Product` record | `is_mul == False` ↔ the method returned one operand (a collapse); `result_kind` ↔ the kind of that surviving operand. `is_mul == True` ↔ the method returned `Mul(self, other)`; `left_kind`/`right_kind` ↔ the two operands' kinds. SymPy may canonicalize `Mul(self, other)` (e.g. `Dagger(O)*Dagger(O)` → `Dagger(O)**2`); that canonicalization is downstream of `__mul__` and is still the "generic product" case (`is_mul == True`). |
| keyword/positional `self`, `other` | the LHS is fixed by which function (identity vs conjugate); the RHS is `other_kind` | site 1 LHS is the identity (kind 1); site 2 LHS is the conjugate (kind 2). |

`self` is read-only in both methods (each constructs a fresh return value and
never mutates an operand); the modeled functions take only the right operand's
kind and the `Product` fields are stated exactly.

## 3. Deep-model references (A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom** in this bundle. The changed
operations are the two `__mul__` methods themselves, so they are modeled
**deeply** (spelled-out integer-kind dispatch) and validated equal to the real
methods out-of-band, never axiomatized.

### 3.1 `is_operator_like` / `is_identity` / `is_conjugate` ↔ the real type tests
`Dagger` (`dagger.py:13`) is `class Dagger(adjoint)` where `adjoint`
(`sympy/functions/elementary/complexes.py:775`) subclasses `Function`; it is
therefore NOT a subclass of `Operator`. `IdentityOperator` (`operator.py:249`)
is `class IdentityOperator(Operator)`. Hence:
`isinstance(x, (Operator, Dagger))` is True for kinds {0,1,2}; `isinstance(x,
IdentityOperator)` is True only for kind 1; `isinstance(x, Dagger)` only for
kind 2. `axiom_check.py::check_classification` asserts the model predicates
equal these exact `isinstance` results on one representative per kind.

### 3.2 `identity_mul` ↔ `IdentityOperator.__mul__` (post-patch)
Post-patch source (`operator.py:308-313`):
```python
def __mul__(self, other):
    if isinstance(other, (Operator, Dagger)):
        return other
    return Mul(self, other)
```
So `I * other` collapses to `other` for kinds {0,1,2} and is the generic
product for kind 3. `axiom_check.py::check_identity_mul` runs the REAL `I*rep`
for a representative of every kind and asserts it equals the model's predicted
expression (the surviving operand, or `Mul(I, rep)`).

### 3.3 `dagger_mul` ↔ `Dagger.__mul__` (post-patch, new method)
Post-patch source (`dagger.py`):
```python
def __mul__(self, other):
    from sympy.physics.quantum import IdentityOperator
    if isinstance(other, IdentityOperator):
        return self
    return Mul(self, other)
```
So `Dagger(O) * other` collapses to `self` (the conjugate, kind 2) for kind 1
and is the generic product otherwise. `axiom_check.py::check_dagger_mul` runs
the REAL `Dag*rep` for every kind and asserts equality with the model's
predicted expression.

**Soundness check (G-AX).** `axiom_check.py` is run against the **gold-patched**
tree (the twin's `patch.diff` applied — the standard in-container setup, since
the patch is the real correctness oracle). It (a) checks the kind predicates
against the real `isinstance` tests, (b) checks `identity_mul`/`dagger_mul`
against the real `IdentityOperator.__mul__`/`Dagger.__mul__` on every operand
kind, and (c) asserts the exact F2P discriminating equalities
(`I*Dagger(O)==Dagger(O)`, `Dagger(O)*I==Dagger(O)`, `Dagger(O)*Dagger(O)==
Dagger(O)**2`, `Dagger(I)==I`, plus the unchanged `I*O==O`, `O*I==O`,
`isinstance(I*I, IdentityOperator)`, `isinstance(3*I, Mul)`,
`isinstance(I*x, Mul)`), failing loud on any mismatch — no skip-guard. On the
**pre-patch** tree the same check fails on `identity_mul(kind=2)` (real
`I*Dagger(O)` stays `I*Dagger(O)` instead of `Dagger(O)`), confirming the deep
models encode the FIXED behavior, not the bug. Imports only `sympy` (the very
package the patch edits) + stdlib.
