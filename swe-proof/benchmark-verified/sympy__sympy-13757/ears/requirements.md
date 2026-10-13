# Requirements: symmetric evaluation of products mixing a polynomial and a plain expression

## Introduction

In the polynomial-manipulation subsystem (`sympy.polys.polytools`, class
`Poly`), multiplying a polynomial object by a plain (non-`Poly`) SymPy
expression behaves asymmetrically. When the polynomial is on the **left**
(`Poly(x) * x`), the product is carried out and a polynomial value is returned
(e.g. `Poly(x**2, x, domain='ZZ')`). When the polynomial is on the **right**
(`x * Poly(x)`), the product is left as an unevaluated symbolic product
(`x*Poly(x, x, domain='ZZ')`) instead of being carried out. The same asymmetry
appears with numeric factors coming from SymPy's numeric layer
(e.g. `S(-2) * Poly(x)` stays unevaluated while `Poly(x) * S(-2)` evaluates).

The goal is to make the two operand orders behave the same: whenever a plain
expression multiplied on either side of a `Poly` *could* be carried out (the
plain factor is convertible into a polynomial over the polynomial's
generators), the product SHALL be carried out and yield a polynomial value,
regardless of operand order. This is a dispatch/precedence concern: the `Poly`
class must advertise a high enough arithmetic-dispatch precedence that SymPy's
binary-operator machinery routes a mixed product to `Poly`'s reflected
multiplication path (its `__rmul__`), so the polynomial performs the product
even when it is the right operand.

The behavior of `Poly.__mul__` / `Poly.__rmul__` themselves (coerce the plain
factor when convertible, else fall back to a plain symbolic product) is already
correct and must be preserved; the fix concerns only which object is chosen to
handle the operation.

## Requirement 1: A polynomial on the right of a mixed product evaluates

**User story:** As a user multiplying a plain expression by a `Poly`, I want
`expr * Poly(...)` to be carried out and return a polynomial, so that the
result does not depend on which side the polynomial appears on.

**Acceptance criteria**

1. WHEN a plain SymPy expression that is convertible into a polynomial over the
   polynomial's generators is multiplied with a `Poly` and the `Poly` is the
   **right** operand, THEN the system SHALL carry out the product and return a
   `Poly` value equal to the polynomial obtained by performing that
   multiplication. A factor counts as convertible when it can be expressed as a
   polynomial in the generators whose coefficients lie in a ground domain; this
   includes a bare generator symbol, any number, and — importantly — any factor
   that does **not** involve the generators at all (for example another symbol,
   or a transcendental function of some other symbol), since such a factor is
   absorbed as a ground-domain coefficient (its ground domain is extended to
   include it).
2. WHEN a generator symbol `x` is multiplied on the left of `Poly(x)`
   (`x * Poly(x)`), THEN the system SHALL return the polynomial equal to
   `Poly(x**2, x)` over the integer ground domain, identical to the value of the
   reversed product `Poly(x) * x`.
3. IF the plain factor is a plain SymPy integer/number (whether written as a
   Python literal or produced through SymPy's numeric layer, e.g. `S(-2)`),
   THEN the system SHALL carry out `number * Poly(x)` and return the scaled
   polynomial (e.g. `Poly(-2*x, x)` over the integer ground domain), never an
   unevaluated symbolic product.
4. The system SHALL produce, for a mixed product whose plain factor is
   convertible, a genuine `Poly` instance (a polynomial value), not a symbolic
   `Mul` that still displays the `Poly(...)` operand unevaluated.

## Requirement 2: Operand-order symmetry of mixed products

**User story:** As a user, I want `Poly * expr` and `expr * Poly` to give the
same result, so that multiplication is commutative for these operands as it is
mathematically.

**Acceptance criteria**

1. WHEN the same convertible plain expression and the same `Poly` are
   multiplied in the two possible orders, THEN the system SHALL return equal
   results for both orders.
2. The system SHALL preserve the already-correct left-operand behavior: WHEN a
   `Poly` is the left operand and the right factor is convertible, THEN the
   product SHALL be carried out and return the corresponding polynomial value
   (this behavior must not regress).
3. WHEN a `Poly` is multiplied by another `Poly`, THEN the system SHALL carry
   out the polynomial product and return the product polynomial, for either
   operand grouping.

## Requirement 3: Non-convertible factors still fall back to a symbolic product

**User story:** As a user, I want a product that cannot be represented as a
polynomial over the given generators to fall back to a plain symbolic
expression, so that no information is lost or wrongly forced into a polynomial.

**Acceptance criteria**

1. IF the plain factor cannot be converted into a polynomial over the
   polynomial's generators — that is, it involves a generator in a
   non-polynomial way, such as a non-polynomial function of a generator, a
   negative or fractional power of a generator, or a rational expression in a
   generator — THEN the system SHALL return a plain symbolic expression (the
   ordinary product of the polynomial's expression form with the plain factor),
   which is NOT a `Poly` instance, rather than raising an error, for either
   operand order.
2. WHEN the non-convertible fallback occurs, THEN the system SHALL return the
   same symbolic (non-`Poly`) result regardless of which side the polynomial
   appeared on.
3. WHEN the plain factor involves only symbols other than the polynomial's
   generators (e.g. `sin(y)` for a `Poly` in `x`), THEN the system SHALL NOT
   take this fallback but SHALL instead treat the factor as convertible per
   Requirement 1 and return a `Poly` value, because such a factor is absorbed
   into the ground domain rather than treated as non-representable.

## Requirement 4: Dispatch precedence for polynomial arithmetic

**User story:** As a maintainer, I want the `Poly` class to take priority over
plain expressions when resolving mixed arithmetic, so that the polynomial's own
multiplication logic runs even when the polynomial is the right operand.

**Acceptance criteria**

1. The `Poly` class SHALL advertise an arithmetic-dispatch precedence strictly
   greater than that of a generic SymPy expression, so that SymPy's
   binary-operator dispatch selects the `Poly` operand to handle a mixed
   product.
2. WHEN a mixed product is evaluated with the `Poly` as the right operand, THEN
   the dispatch SHALL invoke the polynomial's reflected multiplication path
   (rather than leaving the operation to the plain expression's multiplication),
   so that the coercion-or-fallback logic of Requirements 1 and 3 is applied.
3. The change to dispatch precedence SHALL NOT alter the results of any other
   `Poly` operation (addition, subtraction, negation, absolute value, powers,
   division/quotient/remainder, ground-element arithmetic, equality, and the
   full set of polynomial query/transform methods) beyond making right-operand
   mixed products evaluate as specified.

## Requirement 5: Regression protection for existing polynomial arithmetic

**User story:** As a user, I want all previously working polynomial arithmetic
and construction to keep working unchanged, so that fixing right-operand
multiplication introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep the existing results of `Poly` multiplication in the
   already-working cases: `Poly(x, x) * 2`, `2 * Poly(x, x)`, and
   `Poly(x, x) * Poly(...)` SHALL continue to return their established
   polynomial values.
2. The system SHALL keep the established behavior of `Poly` construction and
   all `Poly` inspection, transformation, arithmetic, and root/factorization
   methods unchanged.
3. The system SHALL keep noncommutative and symbolic multiplication semantics
   for non-`Poly` operands unchanged.
