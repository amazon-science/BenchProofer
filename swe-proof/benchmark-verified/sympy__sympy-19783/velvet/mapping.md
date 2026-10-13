# mapping.md — sympy__sympy-19783

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 586a43201d0357e92e8c93548d69a9f42bf548f4`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each callee model.

Repo files under change:
- `sympy/physics/quantum/dagger.py` — `Dagger.__mul__` ADDED.
- `sympy/physics/quantum/operator.py` — `IdentityOperator.__mul__` widened.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `daggerProduct (self other : QExpr)` | `Dagger.__mul__(self, other)` — `sympy/physics/quantum/dagger.py` (ADDED post-patch after `__new__`, line 79-86) | modeled changed function #1: the conjugate object's product dispatch |
| `identityProduct (self other : QExpr)` | `IdentityOperator.__mul__(self, other)` — `sympy/physics/quantum/operator.py:308` | modeled changed function #2: the identity operator's product dispatch |
| `QExpr` | symbolic quantum expression objects (`Operator`, `IdentityOperator`, `Dagger`, `Mul`) | the finite carrier for the fragment the dispatch distinguishes |
| `isOperatorClass` *(A-reference)* | `isinstance(other, Operator)` — the `Operator` membership test in both `__mul__` branches | deep model of the operator-class membership test; validated == real `isinstance` by axiom_check.py (G-AX) |
| `isDaggerClass` *(A-reference)* | `isinstance(other, Dagger)` — added to `IdentityOperator.__mul__`'s tuple; and the dispatch precondition of `daggerProduct` | deep model of the conjugate-object membership test; G-AX validated |
| `isIdentityClass` *(A-reference)* | `isinstance(other, IdentityOperator)` — the test in the new `Dagger.__mul__` | deep model of the identity membership test; G-AX validated |
| `daggerProd` / `identityProd` | the per-branch result of the two `__mul__` bodies | pure spec: the desired product value for each operand pair |

The unchanged sibling `Operator.__mul__` (`operator.py:179`) — which already
collapses `Operator * IdentityOperator` to `self` — is NOT modeled: the patch
does not touch it, and it is not on the fix path the F2P tests observe for these
two methods.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the real sympy objects. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a plain operator `Operator(name)` | `QExpr.op name` | `Operator(s)` ↔ `QExpr.op s` |
| the identity operator `IdentityOperator()` | `QExpr.ident` | `IdentityOperator()` ↔ `QExpr.ident` |
| a conjugate object `Dagger(Operator(name))` | `QExpr.dag (op name)` | `Dagger(Operator(s))` ↔ `QExpr.dag (.op s)`. **`dag` wraps a plain operator only**: `Dagger(IdentityOperator())` evaluates to `IdentityOperator()` in the real library (the `_eval_adjoint` of the identity is itself), so it is NOT a conjugate object and is excluded from the `dag` image to keep the bijection exact. |
| a product node | `QExpr.mul a b` | **direction-sensitive.** INPUT side (concretizing a carrier value to feed the dispatch): an unevaluated product object `Mul(<a>, <b>, evaluate=False)` — a `Mul` instance handed in as data. RESULT side (realizing the dispatch's fall-through output): the real constructor **call** `Mul(<a>, <b>)` exactly as the modeled method invokes it, i.e. with sympy's default evaluation, so whatever normalization the real constructor applies (flattening, collecting a repeated factor into a power, …) is part of the realized value. `QExpr.mul self other` as a *result* denotes "the value the real product constructor returns for these operands", not a frozen unevaluated tree. |
| equality of result objects | Lean `DecidableEq` on `QExpr` | sympy structural `==` on the REALIZED results (result-side realization above); the dispatch returns either an operand (echoed identically) or the value of the real product-constructor call on the two operands |

Membership semantics that the bijection makes precise (and G-AX checks):
`isinstance(IdentityOperator(), Operator)` is **True** (the identity is a
subclass of operator) — so `isOperatorClass QExpr.ident = true`. `Dagger` is NOT
a subclass of `Operator` (`isinstance(Dagger(Operator('A')), Operator)` is
False) — so the identity's widened test needs the explicit `Dagger` arm, which
is precisely the bug fix.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

The three membership tests are **deep-modeled** A-references, not consumed
axioms: the spec spells them out structurally over the carrier
(`isOperatorClass`/`isDaggerClass`/`isIdentityClass`) and the proof discharges
each `ensures` by `simp` on those definitions — no module-level `axiom` is used.
G-AX (`axiom_check.py`) validates the A-reference by running the real library
`isinstance` against `Operator` / `Dagger` / `IdentityOperator` on the carrier
image over 5 boundary + 20 000 fuzz objects, asserting each deep model equals the
real membership test. Imports sympy + stdlib only; exit 0 iff sound.

There are **no consumed axioms** and no flag-dependent callees.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` seed their `random.Random` with
**`19783`** so the verdict is reproducible. The R/I shadow transliterates the two
`do` blocks to Python over the real sympy objects, leaves the membership tests as
the real `isinstance` callee (A-reference → run real callee), builds the
fall-through product with the real `Mul`, and diffs against `patch.diff`'s gold
`__mul__` dispatch over ≥10⁵ fuzzed inputs.
