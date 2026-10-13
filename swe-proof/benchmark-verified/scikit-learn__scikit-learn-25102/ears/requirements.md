# Requirements: preserve per-column dtypes in feature-selection pandas output

## Introduction

When a scikit-learn feature-selection transformer is configured to emit pandas
output (via `set_output(transform="pandas")`) and is given a pandas
`DataFrame`, the columns it keeps currently lose their original per-column
dtypes. The transformer first routes the input through the estimator input
validation in `sklearn.base.BaseEstimator._validate_data`, which unconditionally
coerces the `DataFrame` into a single homogeneous numeric array; every column is
collapsed to one common element type (for example a mix of `float32`,
`float64`, and `category` columns all become `float64`). The pandas container is
only re-attached afterwards, so the dtype information is already gone.

This affects the public `transform` method of `SelectorMixin` in
`sklearn/feature_selection/_base.py` (the base class shared by selectors such as
`SelectKBest` and the other univariate/model-based feature selectors), together
with its helper `_transform`, and the `_validate_data` method in
`sklearn/base.py`. The goal is to preserve each surviving column's original
dtype, ordering, row count, and row index when — and only when — the input is a
native pandas `DataFrame` and pandas output has been requested, while leaving
the array/sparse code paths and all existing selection behavior unchanged.

## Requirement 1: Preserve original per-column dtypes in pandas output

**User story:** As a user who selects features from a pandas `DataFrame` with a
feature selector configured for pandas output, I want each retained column to
keep the dtype it had on input, so that dtype-carried information (such as
categorical or reduced-precision float columns) survives feature selection for
later analysis steps.

**Acceptance criteria**

1. WHEN a feature selector's `transform` is called with a pandas `DataFrame`
   input AND the transformer's output configuration for dense data is `"pandas"`,
   THEN `transform` SHALL return a pandas `DataFrame` in which every retained
   column has exactly the same dtype it had in the corresponding input column
   (for example a `float32` column stays `float32`, a `float64` column stays
   `float64`, and a `category`/categorical column stays categorical).
2. WHEN the input is a pandas `DataFrame` AND pandas output is configured, THEN
   the transformer SHALL NOT coerce the input to a single homogeneous numeric
   array before selecting columns; the retained columns SHALL be taken from the
   original container so their individual element types are preserved.
3. WHEN the retained set spans columns of differing input dtypes, THEN each
   output column SHALL independently match its own source column's dtype rather
   than a common promoted dtype shared across the output.

## Requirement 2: Preserve column identity, order, and selection semantics

**User story:** As a user, I want the pandas output to contain exactly the
selected columns, labeled and ordered as in the input, so that the result is
unambiguous and matches the selector's support mask.

**Acceptance criteria**

1. WHEN a feature selector's `transform` returns pandas output for a `DataFrame`
   input, THEN the output columns SHALL be exactly those input columns whose
   support-mask entry is selected, keeping their original column labels.
2. The system SHALL preserve the input column ordering in the output: retained
   columns appear in the same relative order they had in the input.
3. WHEN pandas output is requested for a `DataFrame`, THEN the set of retained
   columns SHALL be identical to the selection produced by the estimator's
   support mask (`get_support`), so pandas output selects neither more nor fewer
   columns than the array-based path would.

## Requirement 3: Preserve row count and row index

**User story:** As a user, I want the transformed pandas output to have the same
rows (and index) as my input, so that I can align it with other data.

**Acceptance criteria**

1. WHEN `transform` returns pandas output for a `DataFrame` input, THEN the
   number of rows in the output SHALL equal the number of rows in the input.
2. WHEN `transform` returns pandas output for a `DataFrame` input, THEN the
   output SHALL retain the input's row index unchanged.

## Requirement 4: Handle the empty-selection case for pandas output

**User story:** As a user, I want a well-defined result even when a selector
retains no features, so that downstream code does not break on an unexpected
shape.

**Acceptance criteria**

1. WHEN a feature selector selects no features AND the input is a pandas
   `DataFrame` with pandas output configured, THEN `transform` SHALL return a
   pandas `DataFrame` with zero columns and the same number of rows as the
   input.
2. WHEN a feature selector selects no features, THEN `transform` SHALL emit a
   `UserWarning` indicating that no features were selected.
3. WHEN no features are selected AND the input is a pandas `DataFrame` with
   pandas output configured, THEN the returned zero-column result SHALL keep the
   input's row index.

## Requirement 5: Keep feature-count and feature-name validation without casting

**User story:** As a maintainer, I want input validation to still record the
number of input features and check feature names even when the input is not cast
to an array, so that selection and downstream checks continue to work in the
dtype-preserving path.

**Acceptance criteria**

1. WHEN `_validate_data` is invoked in a mode that does not cast the input to an
   array, THEN it SHALL leave the input value unchanged (neither converting it to
   a numeric array nor altering its dtypes) while still performing feature-name
   and feature-count validation.
2. WHEN `_validate_data` runs in this non-casting mode, THEN the estimator's
   recorded number of input features (`n_features_in_`) SHALL be set/checked from
   the input just as it is in the casting mode.
3. The system SHALL default to the pre-existing casting behavior: unless the
   non-casting mode is explicitly requested, `_validate_data` SHALL continue to
   convert `X` (and `y` when applicable) to an array with the existing checks.

## Requirement 6: Preserve existing array and sparse behavior (regression protection)

**User story:** As an existing user who does not use pandas output, I want
feature selection on plain arrays and sparse matrices to behave exactly as
before, so that this change is backward compatible.

**Acceptance criteria**

1. WHEN the input is not a pandas `DataFrame`, OR the output configuration is not
   pandas, THEN `transform` SHALL validate and coerce the input to an array (or
   accepted sparse matrix) as before and SHALL return an array/sparse result
   containing the selected columns.
2. WHEN a plain array or sparse input yields no selected features, THEN
   `transform` SHALL return an empty result with zero columns and the original
   number of rows, and SHALL emit the "no features were selected" `UserWarning`.
3. The system SHALL keep `get_support` returning the boolean support mask (or,
   when indices are requested, the integer indices of the retained features)
   unchanged.
4. The system SHALL keep `inverse_transform` behavior unchanged, reconstructing a
   result whose retained-feature columns come from the input and whose dropped
   features are filled with zeros, for both dense and sparse inputs.
5. WHEN a selector is applied for the standard array path (dense or sparse) with
   any supported score/selection configuration, THEN the selected columns SHALL
   match the support mask exactly, preserving all pre-existing univariate and
   model-based selection results.
