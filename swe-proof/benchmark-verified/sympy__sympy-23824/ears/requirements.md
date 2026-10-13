# Requirements: Correct ordering of leading uncontracted gamma matrices in `kahane_simplify`

## Introduction

The function `kahane_simplify` in `sympy/physics/hep/gamma_matrices.py`
simplifies products of Dirac gamma matrices by applying the Kahane algorithm,
which contracts repeated Lorentz indices (for example collapsing
`GammaMatrix(mu) * GammaMatrix(-mu)` to a factor of `4`). Gamma matrices that
appear at the front of the product and carry only free (uncontracted) indices,
occurring before the first contracted index, are not affected by any identity
and must survive the simplification unchanged, keeping both their presence and
their original left-to-right order.

A defect causes these *leading* free gamma matrices to be re-attached to the
simplified result in reverse order. As a result, an expression whose only
contraction sits at the end (with free matrices in front) simplifies to the
correct scalar factor but with the leading matrices transposed. For example,
`GammaMatrix(rho) * GammaMatrix(sigma) * GammaMatrix(mu) * GammaMatrix(-mu)`
wrongly simplified to `4 * GammaMatrix(sigma) * GammaMatrix(rho)` instead of
`4 * GammaMatrix(rho) * GammaMatrix(sigma)`.

The goal is to make `kahane_simplify` preserve the order of leading
uncontracted gamma matrices, while keeping all previously correct
simplifications (scalar factors, index contractions, sign conventions, and the
ordering produced when contractions are interleaved with free matrices)
unchanged.

## Requirement 1: Preserve order of leading uncontracted gamma matrices

**User story:** As a physicist using SymPy's gamma-matrix machinery, I want
`kahane_simplify` to keep the order of the uncontracted gamma matrices that
precede the first contraction, so that simplified expressions remain
mathematically equal to their inputs.

**Acceptance criteria**

1. WHEN `kahane_simplify` is applied to a product of gamma matrices in which one
   or more gamma matrices carrying only free indices appear before the first
   contracted index, THEN `kahane_simplify` SHALL emit those leading gamma
   matrices in the resulting expression in the same left-to-right order in
   which they appear in the input.
2. WHEN `kahane_simplify` is applied to
   `GammaMatrix(rho) * GammaMatrix(sigma) * GammaMatrix(mu) * GammaMatrix(-mu)`
   (two leading free matrices followed by one contracted pair), THEN the result
   SHALL be equal to `4 * GammaMatrix(rho) * GammaMatrix(sigma)`.
3. WHEN there is more than one leading uncontracted gamma matrix before the
   first contraction, THEN `kahane_simplify` SHALL NOT transpose, reverse, or
   otherwise reorder them relative to one another.
4. The system SHALL prepend the leading uncontracted gamma matrices to every
   term of the simplified result, so that each additive term of the output
   carries the full sequence of leading free matrices in original order.

## Requirement 2: Preserve correct contraction, factor, and sign behavior

**User story:** As a maintainer, I want the ordering fix to leave every
previously correct simplification intact, so that no existing behavior
regresses.

**Acceptance criteria**

1. WHEN `kahane_simplify` is applied to
   `GammaMatrix(mu) * GammaMatrix(-mu) * GammaMatrix(rho) * GammaMatrix(sigma)`
   (a contracted pair first, followed by two free matrices), THEN the result
   SHALL be equal to `4 * GammaMatrix(rho) * GammaMatrix(sigma)`.
2. WHEN a contracted index pair encloses (rather than precedes) one or more free
   gamma matrices, so that the free matrices affected by the contraction are not
   the leading ones, THEN the ordering fix SHALL leave the result identical to
   what the pre-existing algorithm already produced for that product — the sign,
   the scalar factor, and the relative ordering of those non-leading matrices
   SHALL be unchanged, because only the placement of the *leading* free matrices
   (those appearing before the first contraction) is corrected by the fix.
3. The system SHALL continue to apply the correct scalar coefficient (including
   the power-of-two factor from contractions and the Kahane sign correction) to
   the simplified expression, unchanged by the ordering fix.
4. IF the entire input product simplifies away to a pure scalar with no
   remaining gamma matrices, THEN `kahane_simplify` SHALL return that scalar
   multiplied by the 4×4 identity so that the result retains matrix form.
5. The system SHALL return a result that is mathematically equal to the input
   product for every supported product of gamma matrices, whether the
   contractions occur at the front, the interior, or the end of the product.
