# Requirements: store_cv_values support for RidgeClassifierCV

## Introduction

`sklearn.linear_model.RidgeClassifierCV` (`sklearn/linear_model/ridge.py`) is a
ridge classifier with built-in cross-validation. Its documentation advertises a
`cv_values_` attribute that holds the per-alpha cross-validation values when a
`store_cv_values` flag is enabled, exactly like its regression counterpart
`RidgeCV`. However, `RidgeClassifierCV`'s constructor does not accept a
`store_cv_values` argument, so passing it raises
`TypeError: __init__() got an unexpected keyword argument 'store_cv_values'`,
and there is no way to retrieve the promised cross-validation values.

Both `RidgeCV` and `RidgeClassifierCV` delegate to the shared base
`_BaseRidgeCV`, which already knows how to record and honour a `store_cv_values`
flag (it forwards it to the underlying generalized-cross-validation estimator
`_RidgeGCV` and copies the resulting `cv_values_` back after fitting). The goal
is to expose that option on `RidgeClassifierCV` so that constructing the
classifier with the flag enabled succeeds and, after fitting, the
cross-validation values are available — without changing any existing behavior
of `RidgeCV`, the base estimator, or the classifier's fit/predict results.

## Requirement 1: RidgeClassifierCV accepts and records the cross-validation-value retention flag

**User story:** As a user configuring a cross-validated ridge classifier, I want
to enable retention of the per-alpha cross-validation values at construction
time, so that I can inspect them after fitting just as I can with the regression
estimator.

**Acceptance criteria**
1. WHEN a `RidgeClassifierCV` is constructed with the cross-validation-value
   retention flag set (to either `True` or `False`), THEN construction SHALL
   succeed and SHALL NOT raise a `TypeError` about an unexpected keyword
   argument.
2. The retention flag SHALL default to `False` when it is not supplied to the
   constructor.
3. WHEN a `RidgeClassifierCV` is constructed with the retention flag set to a
   given value, THEN the estimator SHALL record that exact value as its stored
   configuration, so that the flag is retrievable after construction and honoured
   at fit time (it SHALL NOT be dropped or forced back to its default).
4. The system SHALL preserve the other constructor options of
   `RidgeClassifierCV` (the regularization strengths `alphas`, `fit_intercept`,
   `normalize`, `scoring`, `cv`, and `class_weight`), recording each as supplied.

## Requirement 2: Cross-validation values are stored after fitting when retention is enabled

**User story:** As a user, I want the cross-validation values kept after I fit a
`RidgeClassifierCV` with retention enabled, so that I can access them through the
documented `cv_values_` attribute.

**Acceptance criteria**
1. WHEN a `RidgeClassifierCV` constructed with the retention flag enabled and the
   default cross-validation strategy (`cv=None`) is fitted, THEN after fitting the
   estimator SHALL expose a `cv_values_` attribute holding the per-alpha
   cross-validation values.
2. WHEN such an estimator is fitted with a target given as a one-dimensional
   sequence of class labels over `n_samples` samples and a grid of `n_alphas`
   regularization strengths, THEN `cv_values_` SHALL have shape
   `(n_samples, 1, n_alphas)`.
3. WHEN such an estimator is fitted with a two-dimensional target of shape
   `(n_samples, n_targets)` and a grid of `n_alphas` regularization strengths,
   THEN `cv_values_` SHALL have shape `(n_samples, n_targets, n_alphas)`.
4. The number of alphas reflected in the last dimension of `cv_values_` SHALL
   equal the number of regularization strengths supplied in `alphas`.

## Requirement 3: Retention flag remains incompatible with an explicit cross-validation splitter

**User story:** As a maintainer, I want retention of cross-validation values to
stay restricted to the generalized-cross-validation path, so that enabling it
together with an explicit splitter fails clearly rather than silently doing
nothing.

**Acceptance criteria**
1. IF the retention flag is enabled while an explicit cross-validation strategy
   is supplied (i.e. `cv` is not `None`), THEN fitting SHALL raise a `ValueError`
   indicating that the two settings are incompatible.
2. WHEN the retention flag is left disabled, THEN fitting SHALL NOT set a
   `cv_values_` attribute.

## Requirement 4: Preserve existing RidgeCV cross-validation-value behavior

**User story:** As a user of the regression estimator, I want `RidgeCV`'s
existing retention behavior to be unchanged, so that this addition to the
classifier does not regress the regressor.

**Acceptance criteria**
1. WHEN a `RidgeCV` constructed with the retention flag enabled and `cv=None` is
   fitted with a one-dimensional target over `n_samples` samples and `n_alphas`
   regularization strengths, THEN `cv_values_` SHALL have shape
   `(n_samples, n_alphas)`.
2. WHEN a `RidgeCV` so constructed is fitted with a two-dimensional target of
   shape `(n_samples, n_targets)`, THEN `cv_values_` SHALL have shape
   `(n_samples, n_targets, n_alphas)`.

## Requirement 5: Preserve model selection and fit results

**User story:** As a user, I want enabling the retention flag to leave the
model's predictions and selected regularization strength unchanged, so that the
option only adds an attribute and does not alter results.

**Acceptance criteria**
1. The system SHALL leave the selected regularization strength (`alpha_`), the
   coefficients (`coef_`), and the intercept (`intercept_`) of a fitted
   estimator unchanged by whether the retention flag is enabled.
2. WHEN a cross-validated ridge estimator is fitted, THEN the selected
   regularization strength SHALL match the alpha that minimizes the
   cross-validation error over the supplied `alphas` grid, consistent with the
   estimator's prior selection behavior.
