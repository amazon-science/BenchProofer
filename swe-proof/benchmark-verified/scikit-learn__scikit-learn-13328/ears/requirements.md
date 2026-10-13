# Requirements: Robust input dtype handling in HuberRegressor.fit

## Introduction

`HuberRegressor` (in `sklearn/linear_model/huber.py`) fits a robust linear
regression model by minimizing the Huber loss through an L-BFGS-B optimization
of `_huber_loss_and_gradient`. When a caller passes a feature matrix `X` whose
element type is boolean, `HuberRegressor.fit` raises a `TypeError` deep inside
the loss/gradient computation, because the internal arithmetic (notably the
unary negation applied to a slice of `X`) is not defined for boolean arrays.
Other linear estimators in scikit-learn (e.g. `LinearRegression`) accept
boolean `X` by silently converting it to a floating-point representation before
computing.

The goal is to make `HuberRegressor.fit` accept a boolean `X` (and, more
generally, any integer-like `X`) by coercing the feature matrix to a
floating-point representation during input validation, so that fitting
succeeds and produces the same result as if the caller had passed the
equivalent float matrix — while preserving all existing fitting behavior for
inputs that already worked.

## Requirement 1: Accept boolean feature matrices without error

**User story:** As a user fitting a `HuberRegressor` on features that happen to
be stored as booleans, I want `fit` to work the same way it does for numeric
predictors, so that I do not have to manually cast my data to floats before
calling the estimator.

**Acceptance criteria**
1. WHEN `HuberRegressor.fit` is called with a dense feature matrix `X` whose
   element type is boolean and a valid numeric target `y`, THEN `fit` SHALL
   complete without raising an exception.
2. WHEN `HuberRegressor.fit` is called with a boolean `X`, THEN it SHALL
   return the fitted estimator instance (`self`) with the fitted attributes
   (`coef_`, `intercept_`, `scale_`, `n_iter_`) populated.
3. The system SHALL, during input validation in `HuberRegressor.fit`, convert
   a non-floating-point `X` (such as a boolean or integer array) into a
   floating-point representation before it is used in the loss and gradient
   computation.
4. WHEN `HuberRegressor.fit` receives a boolean `X`, THEN the fitted result
   SHALL be equivalent (within numerical tolerance) to the result obtained by
   fitting on the same data cast to floating point beforehand.

## Requirement 2: Preserve existing dtype behavior for floating-point input

**User story:** As an existing user who already passes floating-point features,
I want the dtype-coercion change to leave my current results untouched, so that
the fix does not silently alter model behavior.

**Acceptance criteria**
1. WHEN `HuberRegressor.fit` is called with an `X` already stored in a
   floating-point type (single- or double-precision), THEN the validated
   feature matrix SHALL retain a floating-point representation and the fit
   SHALL proceed without unnecessary dtype conversion of already-float data.
2. WHEN `HuberRegressor.fit` is called with a sparse CSR feature matrix, THEN
   it SHALL continue to accept that sparse input and complete the fit without
   densifying it away, preserving the previously supported sparse code path.
3. The system SHALL continue to validate that `X` and `y` have consistent
   numbers of samples and that `y` is numeric, rejecting inconsistent inputs
   as before.

## Requirement 3: Preserve numerical fitting behavior and public results

**User story:** As a user relying on the numerical output of `HuberRegressor`,
I want the estimator to keep producing the same coefficients, scale, and
predictions as before for previously valid inputs, so that the dtype fix is
behavior-preserving.

**Acceptance criteria**
1. The system SHALL keep the loss-and-gradient computation numerically
   correct: the analytically computed gradient returned by
   `_huber_loss_and_gradient` SHALL match a finite-difference approximation of
   its loss to within numerical tolerance, including when per-sample weights
   are supplied.
2. WHEN a `HuberRegressor` is fit with per-sample weights, THEN scaling all
   sample weights and repeating samples according to those weights SHALL yield
   equivalent fitted coefficients and intercept (within numerical tolerance),
   preserving the sample-weight semantics.
3. WHEN the same data and target are scaled by a common positive factor, THEN
   the fitted `HuberRegressor` coefficients SHALL remain invariant under that
   rescaling (within numerical tolerance).
4. WHILE `epsilon` is set to a very large value, the `HuberRegressor` fit
   SHALL approach the ordinary least-squares (unregularized linear regression)
   solution, matching its coefficients and intercept within numerical
   tolerance.
5. The system SHALL produce, for data containing outliers, a fit whose score
   on the non-outlier subset is better than that of a comparable squared-loss
   (Ridge) estimator, and whose score on the outlier subset is correspondingly
   poor — preserving the robustness property of the estimator.
6. WHEN `warm_start` is enabled and `fit` is called a second time on the same
   data, THEN the estimator SHALL resume from the previously fitted parameters
   and converge, preserving warm-start behavior.

## Requirement 4: Preserve convergence, iteration, and error reporting

**User story:** As a user, I want the estimator's convergence controls and
error signalling to behave exactly as before, so that the dtype fix does not
change how many iterations run or how failures are reported.

**Acceptance criteria**
1. WHEN a `max_iter` limit is supplied, THEN the recorded number of iterations
   (`n_iter_`) SHALL not exceed that limit.
2. IF `epsilon` is configured below its minimum permitted value (less than
   1.0), THEN `fit` SHALL raise a `ValueError` describing the invalid
   `epsilon`.
3. IF the underlying optimizer fails to converge, THEN `fit` SHALL raise a
   `ValueError` reporting the convergence failure, as it did previously.
