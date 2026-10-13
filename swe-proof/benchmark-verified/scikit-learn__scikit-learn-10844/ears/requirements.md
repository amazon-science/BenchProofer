# Requirements: Overflow-safe Fowlkes–Mallows score

## Introduction

The `fowlkes_mallows_score` function in
`sklearn/metrics/cluster/supervised.py` measures the similarity of two
clusterings of a common set of samples. Internally it builds an integer
co-occurrence (contingency) matrix relating the two clusterings and forms three
integer pair-counting quantities:

- an agreement count (call it `tk`) — the number of sample pairs grouped
  together by both clusterings,
- a first marginal count (`pk`) — derived from the column totals of the matrix,
- a second marginal count (`qk`) — derived from the row totals of the matrix.

The score is the geometric mean of precision and recall, i.e. the agreement
count divided by the square root of the product of the two marginal counts.

On large inputs, the matrix entries and their squared marginal sums grow large.
Because the contingency matrix data is stored in a narrow integer type, forming
the product of the two marginal counts (`pk * qk`) overflows the integer range,
so the square root of a wrapped/negative product yields `nan` and the function
emits a `RuntimeWarning`. The goal is to make the computation numerically robust
so that large but valid clusterings produce a finite, correct score without
warnings or `nan`, while every existing result on ordinary inputs is preserved
exactly.

## Requirement 1: Overflow-safe score on large inputs

**User story:** As a user comparing large clusterings, I want
`fowlkes_mallows_score` to return a finite, valid number rather than `nan`, so
that I can score clusterings of many samples without hitting integer overflow.

**Acceptance criteria**

1. WHEN `fowlkes_mallows_score` is called with two label vectors whose
   co-occurrence counts are large enough that the product of the two marginal
   counts would exceed the range of the matrix's default integer type, THEN the
   function SHALL return a finite floating-point number (never `nan` or `inf`).
2. WHEN the score is computed on such large inputs, THEN the function SHALL NOT
   rely on any arithmetic that overflows the contingency matrix's default
   integer type; the intermediate pair counts SHALL be carried with enough
   integer width that the marginal sums and their combination do not wrap.
3. WHEN the score is computed on such large inputs, THEN the function SHALL NOT
   emit an overflow-related runtime warning.
4. The system SHALL keep the returned score within the closed interval `[0, 1]`
   for all valid label inputs, including large ones.

## Requirement 2: Correct and unchanged score value

**User story:** As a user of clustering metrics, I want the overflow-safe
computation to produce exactly the mathematically defined Fowlkes–Mallows index
that the function returned before, so that existing results and comparisons stay
valid.

**Acceptance criteria**

1. The system SHALL compute the Fowlkes–Mallows index as the agreement count
   normalised by the geometric mean of the two marginal counts — i.e. the
   agreement count divided by the square root of the product of the two marginal
   counts — mathematically equal to precision-times-recall's square root.
2. IF the agreement count is zero, THEN the function SHALL return `0.0`.
3. WHEN two clusterings match perfectly (identical partitions, up to relabeling
   of clusters), THEN the function SHALL return `1.0`.
4. WHEN the two clusterings are effectively independent (each sample assigned to
   its own singleton in one clustering), THEN the function SHALL return `0.0`.
5. The system SHALL produce, on any input small enough not to trigger overflow,
   a score numerically equal (within floating-point tolerance) to the previous
   agreement-over-geometric-mean formulation.

## Requirement 3: Preserve existing behavior and interface

**User story:** As a maintainer, I want the fix confined to the numerical
computation so that the function's signature, validation, and all other
documented behavior are unchanged.

**Acceptance criteria**

1. The system SHALL keep the function signature accepting the two label vectors
   and the optional sparse-contingency-matrix flag, with unchanged defaults.
2. WHEN the two label vectors have different lengths or are otherwise invalid
   inputs, THEN the function SHALL raise the same error as before, with the same
   validation behavior.
3. WHEN the score is computed on non-consecutive or arbitrarily-valued cluster
   labels, THEN the function SHALL return the same value it would for an
   equivalent relabeling into consecutive integers.
4. The system SHALL preserve the documented mathematical properties of the index
   (symmetry between the two clusterings and the score bounds) for the range of
   inputs previously supported.
5. The system SHALL leave the behavior of the other functions in the module
   (mutual information and related supervised clustering metrics) unchanged.
