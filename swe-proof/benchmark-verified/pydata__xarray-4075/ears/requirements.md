# Requirements: Correct weighted reductions when weights are boolean

## Introduction

`xarray` lets a user attach per-element weights to a `DataArray` (or `Dataset`)
via the `.weighted(weights)` accessor and then compute weighted reductions:
`sum_of_weights()`, `sum()`, and `mean()`. These operations live in
`xarray/core/weighted.py` (the `Weighted`, `DataArrayWeighted`, and
`DatasetWeighted` classes) and are built on top of the internal reduction helper
`_reduce`, which contracts (dot-products) two arrays over one or more
dimensions.

The sum of weights is computed by contracting the data's "not-null" mask against
the weights. When the supplied `weights` array has a boolean dtype, that
contraction is performed in boolean arithmetic, so a dot product of two boolean
arrays collapses to a single boolean (`True`/`False`) instead of counting the
matching entries as a number. As a consequence:

- `sum_of_weights()` on boolean weights returns a boolean-like value (e.g. `True`
  where a genuine count such as `2` is expected), and
- `mean()`, which normalizes by the sum of weights, divides by that wrong value
  and returns an incorrect (often numerically larger) result.

The goal is to make weighted reductions treat boolean weights as ordinary
0/1 numeric weights so that the sum of weights is a true count and the weighted
mean is correctly normalized, while leaving the behavior for numeric (int/float)
weights and all existing validation and missing-value handling unchanged.

## Requirement 1: Sum of weights counts boolean weights numerically

**User story:** As a user computing a weighted reduction with a boolean mask as
weights, I want `sum_of_weights()` to report how many weighted, non-missing
entries contributed, so that I get a numeric count rather than a boolean.

**Acceptance criteria**

1. WHEN a user calls `sum_of_weights()` on a `Weighted` object whose `weights`
   array has a boolean dtype, THEN the operation SHALL return the numeric total
   of the weights over the reduced dimension(s), equal to the number of entries
   that are simultaneously non-missing in the data and `True` in the weights.
2. WHEN the weights are boolean and both the data and the weights contain no
   missing values, THEN `sum_of_weights()` SHALL return a value numerically
   equal to the count of `True` weights, not a boolean truth value (for example,
   two `True` weights SHALL yield `2`, not `True`).
3. WHEN at least one entry contributes along the reduced dimension(s), THEN the
   system SHALL return the sum of weights as a numeric (integer- or float-valued)
   result whose value equals the count of contributing entries, whether that
   count is `1` or greater than `1`. (The case where no entry contributes, i.e.
   a total weight of `0`, is governed by Requirement 4.2, which specifies a
   missing value (NaN) rather than `0` for that position.)
4. WHEN reducing over a proper subset of dimensions with boolean weights, THEN
   `sum_of_weights()` SHALL produce, for each remaining coordinate position, the
   numeric count of contributing entries along the reduced dimension(s).

## Requirement 2: Weighted mean is correctly normalized for boolean weights

**User story:** As a user computing a weighted mean with a boolean mask as
weights, I want the result to be the average over the selected entries, so that
selecting entries with a boolean mask behaves like an ordinary (unweighted)
mean over those entries.

**Acceptance criteria**

1. WHEN a user calls `mean()` on a `Weighted` object whose `weights` array has a
   boolean dtype, THEN the operation SHALL normalize the weighted sum by the
   numeric count of contributing (non-missing, `True`-weighted) entries.
2. WHEN the weights are boolean and every selected data value is equal, THEN
   `mean()` SHALL return that common value (for example, selecting entries that
   all equal `1` SHALL yield `1`, not a larger value produced by dividing by a
   boolean).
3. IF the boolean weights select no entries along the reduced dimension(s) (the
   count of contributing entries is `0`), THEN `mean()` SHALL return a missing
   value (NaN) for that position, consistent with the documented behavior when
   weights sum to zero.

## Requirement 3: Numeric-weight behavior is preserved

**User story:** As a user who already relies on integer or float weights, I want
the weighted reductions to keep returning the same results as before, so that
the boolean fix does not change any existing numeric behavior.

**Acceptance criteria**

1. WHEN the `weights` array has a non-boolean (integer or float) dtype, THEN
   `sum_of_weights()` SHALL return the sum of the weights over the non-missing
   data entries, exactly as it did before this change.
2. WHEN the `weights` array has a non-boolean dtype, THEN `sum()` SHALL return
   the sum of `data * weights` over the reduced dimension(s), and `mean()` SHALL
   return that weighted sum divided by the sum of weights.
3. The system SHALL compute `sum()` (the weighted sum) directly from the data
   and the supplied weights without altering the weights' dtype, so that boolean
   weights continue to contribute as 0/1 in a weighted `sum()`.
4. WHEN weights are all equal to a constant factor, THEN `mean()` SHALL return
   the same value as the corresponding unweighted mean of the data, for any
   non-zero constant factor.

## Requirement 4: Missing-value handling and zero-weight semantics are preserved

**User story:** As a user with missing values in my data, I want weighted
reductions to keep ignoring NaN data entries and to keep flagging positions with
zero total weight, so that the boolean fix does not regress missing-value
handling.

**Acceptance criteria**

1. WHEN the data contains missing values (NaN), THEN `sum_of_weights()` SHALL
   exclude the weights at those positions from the total, counting only entries
   where the data is non-missing.
2. IF the total weight over the reduced dimension(s) is zero, THEN
   `sum_of_weights()` SHALL report a missing value (NaN) for that position rather
   than zero.
3. WHEN `skipna` selection applies for float data, THEN `sum()` and `mean()`
   SHALL continue to treat missing data entries as not contributing, preserving
   the previously documented `skipna` behavior for each dtype.
4. IF the weighted reduction has no contributing weight for a position, THEN
   `mean()` SHALL yield NaN for that position.

## Requirement 5: Input validation is preserved

**User story:** As a user constructing a `Weighted` object, I want invalid
weights to be rejected clearly, so that the boolean fix does not weaken existing
input checks.

**Acceptance criteria**

1. IF the object passed as `weights` is not a `DataArray`, THEN constructing the
   `Weighted` object SHALL raise a `ValueError`.
2. IF the `weights` array contains any missing value (NaN), THEN constructing the
   `Weighted` object SHALL raise a `ValueError` indicating that weights cannot
   contain missing values.

## Requirement 6: Multi-dimensional and mismatched-shape behavior is preserved

**User story:** As a user applying weighted reductions to multi-dimensional data
or to weights that span a subset of the data's dimensions, I want the results to
match the direct definition of the weighted operations, so that behavior across
shapes and coordinates is unchanged.

**Acceptance criteria**

1. WHEN the weights and the data span different (possibly overlapping) sets of
   dimensions, THEN `sum_of_weights()`, `sum()`, and `mean()` SHALL each produce
   results consistent with contracting over the requested dimension(s) after the
   two arrays are aligned/broadcast, for both boolean and numeric weights.
2. WHEN the data and the weights have non-identical coordinates on a shared
   dimension, THEN the weighted operations SHALL align them on their common
   coordinates before reducing, matching the pre-existing alignment behavior.
3. The system SHALL support reducing over a single dimension, over multiple
   dimensions, or over all dimensions (no dimension argument), returning in each
   case the value defined by the corresponding weighted reduction.
