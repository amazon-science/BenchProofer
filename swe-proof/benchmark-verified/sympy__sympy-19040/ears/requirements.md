# Requirements: multivariate factorization over an algebraic extension must not drop factors

## Introduction

SymPy's polynomial `factor` supports factoring over an algebraic number field
when the caller supplies an `extension` (for example `extension=[I]`). For
multivariate inputs this is handled by `dmp_ext_factor` in
`sympy/polys/factortools.py`, which is reached from the public `factor` /
`Poly.factor_list` machinery. The routine makes the input monic, disposes of
the trivial (all per-variable degrees non-positive) case, then:

1. computes a square-free part of the polynomial with respect to the principal
   (first) variable,
2. builds a *square-free norm* over the ground domain (via `dmp_sqf_norm`),
3. factors that ground norm into ground factors
   (`dmp_factor_list_include`),
4. lifts each ground factor back over the extension and composes it with the
   norm's shift, and
5. recovers multiplicities against the original monic polynomial by trial
   division (`dmp_trial_division`).

A defect appears in step 2: the square-free norm was being taken of the
square-free *part* of the polynomial rather than of the full monic polynomial.
Because the square-free part is computed with respect to only the principal
variable, factors that are square-free in that variable but carry the full
multivariate structure — in particular irreducible components that do not
involve the principal variable — were not represented in the ground norm, and
so were silently dropped from the returned factorization. The reported symptom:
factoring an expanded product such as `(x - 1)*(y - 1)` with an algebraic
`extension` returned only `x - 1`, losing the `y - 1` factor.

The goal is that multivariate factorization over an algebraic extension is
**complete**: the returned factors reconstruct the input polynomial, and no
irreducible component is dropped, while univariate factoring, factoring without
an extension, and the underlying square-free / norm utilities are unchanged.

## Requirement 1: Factorization over an algebraic extension is complete

**User story:** As a user factoring a multivariate polynomial over an algebraic
number field, I want every irreducible factor returned, so that the
factorization equals the original polynomial.

**Acceptance criteria**

1. WHEN `factor` is applied to a multivariate polynomial with an algebraic
   `extension` supplied, THEN the product of the returned factors, taken
   together with any returned constant/leading coefficient, SHALL be
   mathematically equal to the input polynomial (i.e. expanding the returned
   factored form SHALL reproduce the expanded input).
2. WHEN such a polynomial factors into irreducible components of which one or
   more do not involve the principal (first) variable, THEN every such component
   SHALL appear in the returned factorization and SHALL NOT be dropped.
3. WHEN the input is (up to expansion) a product of two or more distinct
   irreducible multivariate factors and is factored over an algebraic
   extension, THEN the number of distinct irreducible factors returned SHALL
   match the number present in the input rather than being reduced.
4. IF an irreducible component occurs to a multiplicity greater than one in the
   input, THEN that component SHALL be reported with its correct multiplicity.

## Requirement 2: The ground square-free norm is derived from the full monic polynomial

**User story:** As a maintainer of the algebraic-extension factoring routine, I
want the ground factor list to be built from the complete polynomial, so that
all of its structure is preserved through the norm step.

**Acceptance criteria**

1. WHEN `dmp_ext_factor` builds the square-free norm over the ground domain,
   THEN the norm SHALL be computed from the full monic polynomial (the
   polynomial after being made monic and before the square-free-part reduction),
   NOT from its principal-variable square-free part.
2. WHEN the ground factor list is obtained by factoring that norm, THEN it SHALL
   represent every irreducible component of the input polynomial, so that the
   subsequent lift-and-trial-division step can recover each factor.
3. The system SHALL continue to recover factor multiplicities by trial division
   of the recovered factors against the original monic polynomial.

## Requirement 3: Boundary and coefficient behavior is preserved

**User story:** As a user, I want the leading coefficient and degenerate cases
to be handled exactly as before, so that only the factor-dropping defect is
corrected.

**Acceptance criteria**

1. WHEN `dmp_ext_factor` is called, THEN the returned leading/ground coefficient
   SHALL equal the leading coefficient of the input polynomial, unchanged by the
   fix.
2. IF every per-variable degree of the monic polynomial is non-positive, THEN
   the routine SHALL return that leading coefficient together with an empty
   factor list.
3. WHEN the ground norm factors into a single ground factor, THEN the recovered
   factor list SHALL be the principal-variable square-free part, as before.

## Requirement 4: Existing factoring and helper behavior is unchanged (regression protection)

**User story:** As a maintainer, I want all previously-correct factoring to keep
working, so that the fix introduces no regressions.

**Acceptance criteria**

1. WHEN a univariate polynomial is factored over an algebraic extension, THEN it
   SHALL be factored exactly as before (the univariate path is unaffected).
2. WHEN a polynomial is factored without any `extension` supplied, THEN its
   factorization SHALL be unchanged.
3. The system SHALL keep the behavior of the square-free norm, square-free part,
   square-free list, and norm utilities unchanged for all inputs.
4. WHEN factoring a polynomial that already factored correctly over an
   extension before the fix, THEN it SHALL continue to produce the same
   factorization.
5. The system SHALL preserve all other polynomial-manipulation behavior
   (construction, arithmetic, GCD, resultants, root finding, and the rest of the
   `Poly` API) unchanged.
