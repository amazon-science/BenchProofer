# Requirements: Symbolic indexing of the identity matrix

## Introduction

In the symbolic matrix expression system (`sympy/matrices/expressions/matexpr.py`),
the `Identity` matrix expression exposes an element-access routine
(`Identity._entry(i, j)`) that returns the value of the identity matrix at row
position `i` and column position `j`. Because these expressions are symbolic,
`i` and `j` are frequently symbolic expressions (e.g. free integer symbols or
summation dummy indices) rather than concrete integers.

The current routine reports `1` only when `i` and `j` are *structurally
identical* and reports `0` in every other case. For symbolic positions whose
equality is not yet decided, this collapses the off-diagonal answer prematurely:
the element is reported as a plain `0` even though the two positions may later
turn out to be equal. As a consequence, aggregating identity-matrix elements
over a range that spans the diagonal (for instance, a double `Sum` over all
row/column index pairs) loses the diagonal contribution and evaluates to `0`
instead of the matrix order `n`.

The goal is to make the identity element access three-valued with respect to the
comparison of the two positions, so that an undetermined comparison yields a
symbolic indicator (equal to `1` exactly when the positions coincide and `0`
otherwise) rather than a definite `0`. This restores correct results for
summations and any other computation that later substitutes concrete values for
the positions, while preserving all existing identity-matrix behavior.

## Requirement 1: Correct element value for the identity matrix

**User story:** As a user working with symbolic identity matrices, I want
`Identity(n)[i, j]` to give the mathematically correct value for concrete and
symbolic positions alike, so that indexing and downstream computations are
sound.

**Acceptance criteria**

1. WHEN the identity element access is invoked with positions whose equality is
   known to hold (the comparison of the two positions reduces to a definite
   true), THEN the routine SHALL return the value one.
2. WHEN the identity element access is invoked with positions whose equality is
   known to fail (the comparison of the two positions reduces to a definite
   false), THEN the routine SHALL return the value zero.
3. IF the equality of the two positions is not decided (the comparison neither
   reduces to a definite true nor to a definite false, as for two distinct free
   symbolic index expressions), THEN the routine SHALL return a symbolic
   indicator of the equality of the two positions rather than a definite zero.
4. WHILE the two positions remain symbolically undetermined, the returned
   symbolic indicator SHALL evaluate to one when the positions are subsequently
   made equal and to zero when they are made unequal.
5. The returned symbolic indicator for undetermined positions SHALL NOT be
   equal to the number zero (i.e. an inequality comparison of the element
   against zero SHALL NOT reduce to a definite false / SHALL hold as a
   non-trivial relation).

## Requirement 2: Aggregation over identity-matrix elements

**User story:** As a user, I want summations over the elements of an identity
matrix to produce the correct totals, so that the diagonal contribution is never
silently dropped and the total resolves to the matrix order once a concrete order
is supplied.

**Acceptance criteria**

1. WHEN the elements of `Identity(n)` are summed over every row/column index
   pair with both indices ranging over the full index set `0 .. n-1`, THEN the
   summation SHALL retain the diagonal contribution rather than collapsing to a
   definite zero, so that the aggregation does not silently discard the
   diagonal (the incorrect prior behavior in which the total reduced to zero).
2. WHEN such a double summation is evaluated after the symbolic order is
   replaced by a concrete positive integer, THEN the evaluated total SHALL
   equal that concrete order.
3. The evaluated total SHALL be invariant under the way the double summation is
   grouped or ordered: regrouping the two index ranges (rather than keeping them
   together) SHALL NOT cause the diagonal contribution to be lost or the total
   to differ.

## Requirement 3: Preservation of existing identity-matrix behavior

**User story:** As a maintainer, I want the existing algebraic behavior of the
identity matrix to remain intact, so that the fix to element access introduces
no regressions.

**Acceptance criteria**

1. WHEN a matrix symbol is multiplied on either side by an identity matrix of
   compatible dimension, THEN the result SHALL equal the original matrix symbol
   unchanged.
2. WHEN the transpose of an identity matrix is taken, THEN the result SHALL
   equal the same identity matrix.
3. WHEN the inverse of an identity matrix is taken, THEN the result SHALL equal
   the same identity matrix.
4. WHEN the conjugate of an identity matrix is taken, THEN the result SHALL
   equal the same identity matrix.
5. WHEN the determinant of an identity matrix is evaluated, THEN the result
   SHALL equal one.
6. WHEN the trace of an identity matrix is evaluated, THEN the result SHALL
   equal the matrix order.
7. WHEN an identity matrix element is accessed with two identical concrete
   positions, THEN the routine SHALL still return one; and WHEN accessed with
   two distinct concrete positions, THEN it SHALL still return zero.
8. The identity matrix's shape, order, and construction behavior (including a
   deferred, unevaluated order that only resolves on explicit evaluation) SHALL
   remain unchanged.
