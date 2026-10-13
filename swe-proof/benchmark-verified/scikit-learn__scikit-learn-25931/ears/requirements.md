# Requirements: IsolationForest must not warn about feature names when fitting with a DataFrame and non-default contamination

## Introduction

`IsolationForest` (in `sklearn.ensemble._iforest`) computes an anomaly-score
threshold at the end of `fit` whenever the `contamination` parameter is set to
a value other than `"auto"`. To do so it re-scores the training data `X`.

When a user fits the estimator with a pandas `DataFrame` (which carries column
/ feature names), this end-of-`fit` scoring step previously routed the training
data through the public scoring entry point, which performs input validation.
By the time that scoring step runs, `X` has already been converted to a plain
NumPy array with the feature names dropped, so validation compared an
unnamed array against an estimator that recorded feature names during fitting
and emitted the spurious warning:

> X does not have valid feature names, but IsolationForest was fitted with feature names

This is incorrect: the user did supply valid feature names, and the warning is
raised inside `fit`, not by a genuine mismatched later call. The goal is to
eliminate this warning during `fit` while preserving all public scoring
behavior (`score_samples`, `decision_function`, `predict`) and the
contamination-driven threshold computation.

The affected module is `sklearn/ensemble/_iforest.py`, specifically the
`IsolationForest.fit` method and the `IsolationForest.score_samples` method.

## Requirement 1: No spurious feature-name warning when fitting a DataFrame with non-default contamination

**User story:** As a user fitting `IsolationForest` on a pandas `DataFrame`
with a non-default `contamination` value, I want `fit` to complete without
warning me about feature names, so that valid, named input does not produce
misleading diagnostics.

**Acceptance criteria**
1. WHEN `IsolationForest.fit` is called with a pandas `DataFrame` input that
   has valid feature names AND `contamination` is set to a numeric value other
   than `"auto"`, THEN `fit` SHALL complete without emitting any
   `UserWarning` concerning feature names (including the message that the input
   does not have valid feature names although the estimator was fitted with
   feature names).
2. WHEN the end-of-`fit` threshold computation re-scores the training data to
   determine the offset, THEN the estimator SHALL score that data through an
   internal path that does NOT re-validate the input and therefore does NOT
   compare feature names.
3. The system SHALL treat the training data used for the offset computation as
   already validated by the fitting procedure, so no second feature-name
   consistency check is performed on it.

## Requirement 2: Contamination-based offset is still computed correctly

**User story:** As a user relying on `contamination` to calibrate the outlier
threshold, I want the fitted offset to remain exactly as before, so that
scoring and predictions are unchanged by the warning fix.

**Acceptance criteria**
1. WHEN `contamination` equals `"auto"`, THEN after `fit` the estimator's
   fitted offset SHALL be `-0.5`.
2. WHEN `contamination` is a numeric value other than `"auto"`, THEN after
   `fit` the estimator's fitted offset SHALL equal the percentile of the
   training data's anomaly scores at the position `100 * contamination`,
   computed from the same scores the public scoring method would produce for
   that training data.
3. The system SHALL produce identical fitted offset values, anomaly scores, and
   inlier/outlier predictions to those obtained before the fix for the same
   inputs, `random_state`, and parameters.

## Requirement 3: Public scoring still validates its input

**User story:** As a user calling scoring methods after fitting, I want the
public scoring entry points to keep validating their input, so that genuine
mismatches (wrong feature count, or an unnamed array when the model was fitted
with names) are still detected.

**Acceptance criteria**
1. WHEN `score_samples` is called by a user, THEN it SHALL validate the input
   `X` (accepting dense or CSR-sparse data, converting to 32-bit float, without
   resetting stored fit metadata) before computing scores.
2. IF a user calls `score_samples` with data whose feature names or feature
   count are inconsistent with what the estimator was fitted on, THEN the
   estimator SHALL raise the same error or warning it did before this change.
3. The system SHALL leave the observable results of `score_samples`,
   `decision_function`, and `predict` unchanged for validly-shaped inputs,
   where `decision_function` equals `score_samples` minus the fitted offset and
   `predict` returns `-1` where the decision function is negative and `+1`
   otherwise.
4. WHEN `score_samples`, `decision_function`, or `predict` is called before the
   estimator has been fitted, THEN the estimator SHALL raise the not-fitted
   error.

## Requirement 4: Preserve existing IsolationForest behavior

**User story:** As an existing user, I want all previously working
`IsolationForest` behavior to keep functioning, so that this fix is a pure
regression fix.

**Acceptance criteria**
1. The system SHALL continue to fit correctly and produce anomaly scores for
   dense inputs under both the `"auto"` and numeric `contamination` settings.
   For CSR-sparse inputs, the system SHALL continue to accept them in the public
   scoring methods (`score_samples`, `decision_function`, `predict`) and in
   `fit` when `contamination` is `"auto"`; fitting a CSR-sparse input together
   with a numeric `contamination` value is NOT part of the behavior guaranteed
   by this fix, because the end-of-`fit` offset re-scoring now uses the
   validation-free internal path (Requirement 1.2) that does not perform the
   sparse-format conversion the public scoring path applies.
2. The system SHALL continue to honor the `max_samples`, `max_features`,
   `n_jobs`, `warm_start`, and `random_state` parameters exactly as before,
   including chunked score computation over the training or query data.
3. The system SHALL continue to raise the existing validation errors for
   invalid parameter values (for example, out-of-range `contamination` or
   `max_samples`).
4. WHEN fitting on data with no variance (all samples identical), THEN the
   estimator SHALL still fit and score without error.
