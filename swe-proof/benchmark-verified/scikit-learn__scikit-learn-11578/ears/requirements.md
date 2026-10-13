# Requirements: Cross-validation scoring path must honor the requested multiclass regime

## Introduction

`sklearn.linear_model.logistic._log_reg_scoring_path` is the helper that
`LogisticRegressionCV` uses to compute the cross-validation score for each
regularization strength `C`. It first fits a coefficient path via
`logistic_regression_path`, then builds a throwaway `LogisticRegression`
estimator, assigns the fitted coefficients/intercept onto it, and calls the
requested scorer with that estimator on the held-out fold
(`scoring(log_reg, X_test, y_test)`).

The problem: the internal estimator is constructed without propagating the
`multi_class` argument that was requested for the path. As a result it takes the
default one-vs-rest regime even when the caller requested the multinomial
regime. Estimators expose their probability estimates through
`predict_proba` (`sklearn/linear_model/logistic.py`), which for the one-vs-rest
regime maps each class score through the logistic function and normalizes across
classes (`LinearClassifierMixin._predict_proba_lr` in
`sklearn/linear_model/base.py`), and for the multinomial regime maps the whole
row of class scores through the softmax function
(`sklearn.utils.extmath.softmax`). Because these two transforms disagree on
essentially every score row, a probabilistic scorer (for example one based on
the log loss) computed inside the scoring path returns the one-vs-rest score
even when the multinomial regime was requested — a value that does not match the
score the caller's configured multinomial estimator would produce.

The goal is to make the estimator that `_log_reg_scoring_path` hands to the
scorer use the same multiclass regime that was requested for the path, so that
the cross-validation score is computed from probability estimates consistent
with that regime. Behavior for the one-vs-rest regime, for label-based scorers
(accuracy, precision, recall, f1), and the function's return contract must be
preserved.

## Requirement 1: Score with the requested multiclass regime

**User story:** As a user of `LogisticRegressionCV` with a probabilistic scorer,
I want the cross-validation score to be computed using the multiclass regime I
requested, so that the reported scores reflect the model I am actually selecting.

**Acceptance criteria**
1. WHEN `_log_reg_scoring_path` is invoked with a requested multiclass regime,
   THEN the estimator it passes to the scorer SHALL be configured to use that
   same requested regime when producing predictions and probability estimates.
2. WHEN the multinomial regime is requested and a probabilistic scorer (one that
   relies on `predict_proba`, such as a log-loss based scorer) is used, THEN the
   probability estimates driving the score SHALL be the softmax of the per-sample
   score rows (exponentiate each class score, then normalize so each row sums to
   one), not the one-vs-rest logistic-then-normalize values.
3. WHEN the multinomial regime is requested, THEN the score returned by
   `_log_reg_scoring_path` for a given `C` SHALL equal (up to floating-point
   tolerance) the score obtained by applying that same scorer to a
   `LogisticRegression` configured with the multinomial regime and carrying the
   same fitted coefficients and intercept, evaluated on the same held-out data.
4. IF the one-vs-rest regime is requested, THEN the estimator handed to the
   scorer SHALL continue to produce one-vs-rest probability estimates (each class
   score through the logistic function, then normalized across classes).

## Requirement 2: Preserve label-based scorers and the fold/return contract

**User story:** As a maintainer, I want scorers that only depend on class labels
to keep returning the same values, and the scoring path's outputs to remain
structurally unchanged, so that fixing the probabilistic case introduces no
regression.

**Acceptance criteria**
1. WHEN a label-based scorer (for example accuracy, precision, recall, or f1,
   including their macro- and weighted-averaged variants) is used with either the
   one-vs-rest or the multinomial regime, THEN `_log_reg_scoring_path` SHALL
   return, for each `C`, the score that same scorer produces for a
   `LogisticRegression` configured with the requested regime and carrying the
   same fitted coefficients and intercept, evaluated on the same held-out data.
2. The system SHALL set the internal estimator's known class labels so that they
   correspond to the requested regime: the two-class positive/negative labels
   for the one-vs-rest regime and the distinct training-set labels for the
   multinomial regime.
3. WHEN the requested regime string is neither the one-vs-rest nor the
   multinomial identifier, THEN `_log_reg_scoring_path` SHALL raise a
   `ValueError`.
4. The system SHALL return, in order, the array of fitted coefficients, the grid
   of `C` values, the array of per-`C` scores, and the per-`C` iteration counts,
   preserving the existing shapes and ordering of these outputs.
5. WHEN the coefficients and intercept are assigned to the internal estimator,
   THEN the scores SHALL be computed from those exact path coefficients for each
   `C` (the estimator SHALL NOT be refit on the held-out data before scoring).
