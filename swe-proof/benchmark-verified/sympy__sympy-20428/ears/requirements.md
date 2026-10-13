# Requirements: Consistent zero-detection for symbolic (EX) polynomial coefficients

## Introduction

SymPy represents polynomials with symbolic coefficients over the "expression
domain" (`EX`), implemented by `ExpressionDomain.Expression` in
`sympy/polys/domains/expressiondomain.py`. Each element wraps a single SymPy
expression (its `ex` attribute). Many polynomial internals decide whether a
coefficient is present or absent by taking the truth value of that element —
for example the dense-list stripping routines (`sympy/polys/densebasic.py`)
drop trailing/leading coefficients that test as false, canonicalizing the zero
polynomial to an empty coefficient list.

The truth test of an `EX` element used a *structural* comparison of the wrapped
expression against the integer `0`. A complicated symbolic expression can be
mathematically equal to zero without being the syntactic literal `0`
(e.g. a nested-radical combination that cancels). Such a coefficient tested as
non-zero, so a constant polynomial that is really the zero polynomial retained
an un-stripped coefficient. The resulting `Poly` printed like `Poly(0, x,
domain='EX')` yet reported `is_zero` as `False`, and downstream operations such
as `terms_gcd()` and `primitive()` behaved inconsistently or raised (this was
the root cause of a reported `ZeroDivisionError`).

The goal is to make the truth value of an `EX` element reflect whether its
wrapped expression is *mathematically* zero, so that a constant `Poly` whose
coefficient evaluates to zero canonicalizes to the true zero polynomial and
behaves consistently everywhere, while preserving all existing behavior for
genuinely non-zero and undetermined coefficients.

## Requirement 1: Truth value of a symbolic-domain element reflects mathematical zero

**User story:** As a user working with polynomials that have symbolic (`EX`)
coefficients, I want the truthiness of a coefficient to reflect whether it is
actually zero, so that a coefficient that cancels to zero is recognized as zero
even when it is written as a complicated non-literal expression.

**Acceptance criteria**

1. WHEN the truth value of an `ExpressionDomain.Expression` element is
   evaluated and the assumptions system determines the wrapped expression to be
   mathematically zero, THEN the element SHALL evaluate as false (zero).
2. WHEN the truth value of an `ExpressionDomain.Expression` element is
   evaluated and the wrapped expression is a complicated symbolic expression
   that is not the syntactic literal `0` but that mathematically cancels to
   zero, THEN the element SHALL evaluate as false (zero).
3. IF the wrapped expression is determined to be non-zero, THEN the element
   SHALL evaluate as true (non-zero).
4. IF the wrapped expression's value cannot be determined to be zero (its
   mathematical zero-status is undetermined), THEN the element SHALL evaluate
   as true (non-zero), so that a coefficient that is not provably zero is never
   discarded.
5. The system SHALL continue to evaluate an element wrapping the literal `0` as
   false (zero) and an element wrapping a non-zero constant such as `1` as true.

## Requirement 2: A symbolic constant polynomial that is zero canonicalizes to the zero polynomial

**User story:** As a user, I want a constant polynomial over the `EX` domain
whose coefficient evaluates to zero to become the canonical zero polynomial, so
that it compares equal to the zero polynomial and reports its status
consistently.

**Acceptance criteria**

1. WHEN a `Poly` over the `EX` domain is built from a single constant
   coefficient whose expression mathematically evaluates to zero, THEN its
   internal dense representation SHALL be stripped to the canonical zero-poly
   form (an empty coefficient list), identical to the representation of
   `Poly(0, x, domain='EX')`.
2. WHEN such a constant polynomial is compared for equality with `Poly(0, x,
   domain='EX')`, THEN the comparison SHALL return true.
3. WHEN `is_zero` is queried on such a polynomial, THEN it SHALL return `True`,
   consistently with the fact that its expression form evaluates to `0`.
4. WHEN a constant polynomial over the `EX` domain is obtained via
   `clear_denoms()` and its cleared coefficient evaluates to zero, THEN the
   returned polynomial SHALL be the canonical zero polynomial as described in
   criteria 1–3.

## Requirement 3: Consistent downstream operations on the canonical zero polynomial

**User story:** As a user, I want polynomial methods to treat a symbolic
constant polynomial that is really zero exactly like the ordinary zero
polynomial, so that no method raises or returns inconsistent results on it.

**Acceptance criteria**

1. WHEN `terms_gcd()` is called on a symbolic constant polynomial whose
   coefficient evaluates to zero, THEN it SHALL behave as it does for the zero
   polynomial and SHALL NOT raise an error.
2. WHEN `primitive()` is called on such a polynomial, THEN it SHALL behave as it
   does for the zero polynomial and SHALL NOT raise a division-by-zero error.
3. The system SHALL ensure that, for such a polynomial, the value returned by
   `is_zero` and the zero-ness of its expression form agree with each other.

## Requirement 4: Preserve existing polynomial behavior

**User story:** As a maintainer, I want the change to zero-detection to leave
all existing polynomial behavior intact, so that non-zero polynomials and
existing coefficient handling are unaffected.

**Acceptance criteria**

1. IF a polynomial has a genuinely non-zero coefficient, THEN its coefficient
   SHALL continue to be retained and the polynomial SHALL continue to report
   `is_zero` as `False`.
2. The system SHALL preserve the existing results of polynomial construction,
   equality and inequality comparison, arithmetic, degree, coefficient
   extraction, `content`, `primitive`, `terms_gcd`, and `clear_denoms` for
   polynomials whose coefficients do not mathematically cancel to zero.
3. WHEN `clear_denoms()` is called, THEN it SHALL continue to return the
   clearing multiplier together with the cleared polynomial, changing only the
   canonicalization of a cleared polynomial that turns out to be zero.
4. The system SHALL keep the truth value of a symbolic-domain element consistent
   with equality against zero for all elements whose zero-status is determinable,
   so that the previously observed disagreement between the element's truthiness
   and its expression evaluating to `0` no longer occurs.
