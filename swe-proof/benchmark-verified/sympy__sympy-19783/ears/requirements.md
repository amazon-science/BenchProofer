# Requirements: Identity-operator absorption for Hermitian conjugates

## Introduction

In SymPy's quantum module, the `IdentityOperator` (from
`sympy.physics.quantum.operator`, also re-exported as
`sympy.physics.quantum.IdentityOperator`) is meant to act as a two-sided
multiplicative identity in operator expressions: multiplying any operator by the
identity should collapse to that operator rather than leaving an unevaluated
product.

Today this simplification works for a plain `Operator` (`A * Identity` returns
`A`, and `Identity * A` returns `A`), but it fails when one factor is the
Hermitian conjugate of an operator, i.e. a `Dagger` instance (from
`sympy.physics.quantum.dagger`). The reported problem is that
`Dagger(A) * Identity` is left as the unevaluated product `Dagger(A)*I` instead
of simplifying to `Dagger(A)`.

The goal is to make multiplication by the identity operator absorb the identity
on either side when the other factor is a Hermitian conjugate, while preserving
every existing simplification and leaving genuinely non-simplifiable products
unevaluated. The affected modules are `sympy/physics/quantum/dagger.py`
(the `Dagger` class) and `sympy/physics/quantum/operator.py` (the
`IdentityOperator` class).

## Requirement 1: Hermitian conjugate absorbs a right-hand identity operator

**User story:** As a user building quantum operator expressions, I want the
product of a Hermitian conjugate and the identity operator to simplify to the
conjugate, so that identity factors do not clutter my expressions.

**Acceptance criteria**

1. WHEN a `Dagger` instance is multiplied on the left of an `IdentityOperator`
   (the `Dagger` is the left factor, the identity operator is the right factor),
   THEN the system SHALL return that `Dagger` instance unchanged (equal to the
   conjugate itself), not an unevaluated product.
2. WHEN a `Dagger` instance is multiplied by the Hermitian conjugate of an
   identity operator, THEN the system SHALL return that `Dagger` instance
   unchanged, because the conjugate of the identity operator is itself the
   identity operator.

## Requirement 2: Identity operator absorbs a right-hand Hermitian conjugate

**User story:** As a user, I want the identity operator on the left of a
Hermitian conjugate to simplify to that conjugate, so that identity absorption
is symmetric.

**Acceptance criteria**

1. WHEN an `IdentityOperator` is multiplied on the left of a `Dagger` instance
   (the identity operator is the left factor, the `Dagger` is the right factor),
   THEN the system SHALL return that `Dagger` instance unchanged (equal to the
   conjugate itself), not an unevaluated product.

## Requirement 3: Non-identity products of a Hermitian conjugate stay unevaluated

**User story:** As a user, I want products that genuinely cannot be simplified to
be preserved exactly, so that no information is lost and existing algebra keeps
working.

**Acceptance criteria**

1. WHEN a `Dagger` instance is multiplied by a factor that is not an identity
   operator (for example a plain `Operator`), THEN the system SHALL return the
   unevaluated product of the two factors (equal to the ordinary multiplication
   of the left and right factors), and SHALL NOT collapse it to either factor.
2. WHEN a `Dagger` instance is multiplied by another `Dagger` instance of the
   same operator, THEN the system SHALL return the same result as raising that
   conjugate to the second power (the square of the conjugate).
3. WHEN a product of a `Dagger` instance and a plain `Operator` is further
   multiplied by an `IdentityOperator`, THEN the system SHALL preserve the
   already-formed product as the operand of that final multiplication (the
   final product SHALL equal the unevaluated product multiplied by the identity
   operator, with the inner product unchanged).

## Requirement 4: Existing identity-operator simplifications are preserved

**User story:** As a user relying on current behavior, I want the pre-existing
identity simplifications and construction rules to remain intact, so that this
change is strictly additive.

**Acceptance criteria**

1. WHEN an `IdentityOperator` is multiplied on the left of a plain `Operator`,
   THEN the system SHALL return that `Operator` unchanged.
2. WHEN a plain `Operator` is multiplied on the left of an `IdentityOperator`,
   THEN the system SHALL return that `Operator` unchanged.
3. WHEN two `IdentityOperator` instances are multiplied together, THEN the system
   SHALL return an `IdentityOperator`.
4. WHEN an `IdentityOperator` is multiplied by an ordinary scalar or symbol (a
   factor that is neither an operator nor a Hermitian conjugate), THEN the system
   SHALL leave the product unevaluated (an ordinary multiplication expression).
5. The system SHALL continue to construct the Hermitian conjugate of a supported
   argument through its existing dagger/adjoint rules (scalars, matrices, kets,
   bras, inner and outer products, sums, products, and powers), so that
   introducing the multiplication behavior above changes none of those results.
