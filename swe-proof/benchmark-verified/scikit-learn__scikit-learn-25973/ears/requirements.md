# Requirements: SequentialFeatureSelector accepts one-pass iterables of CV splits

## Introduction

`SequentialFeatureSelector` (`sklearn/feature_selection/_sequential.py`) selects
features greedily. At each step its `fit(X, y)` method repeatedly evaluates
candidate feature subsets by calling `cross_val_score` with the selector's `cv`
argument. Because feature selection is iterative, `fit` performs *many*
cross-validation evaluations: once per candidate feature, across several
selection rounds.

The `cv` parameter is documented (like the `*SearchCV` estimators) to accept an
integer, `None`, a cross-validation splitter object, **or an iterable that
yields `(train, test)` index arrays**. However, when `cv` is a single-pass
iterable such as a generator produced by a splitter's `split(...)` method, the
selector consumes it during the first evaluation and every later evaluation sees
an exhausted iterable. This yields empty cross-validation scores and the fit
aborts with an `IndexError` raised deep inside the scoring machinery, instead of
completing.

The goal is to make `SequentialFeatureSelector.fit` treat the `cv` argument the
same way the rest of scikit-learn's cross-validation consumers do: normalize it
once at the start of `fit` (via `sklearn.model_selection.check_cv`, taking into
account whether the wrapped estimator is a classifier so that the default
stratification choice matches the `cv` documentation), materializing a
one-pass iterable into a reusable form so that every subsequent evaluation
reuses the identical set of splits. All existing behavior for the other accepted
`cv` values, and for every other selector option, must be preserved.

The change is localized to `SequentialFeatureSelector.fit` and its helper
`_get_best_new_feature_score`.

## Requirement 1: Support single-pass iterables of splits as `cv`

**User story:** As a user of `SequentialFeatureSelector`, I want to pass the
splits produced by a cross-validation splitter (for example a generator returned
by a splitter's `split` method) as the `cv` argument, so that I can drive
feature selection with a custom set of train/test folds.

**Acceptance criteria**
1. WHEN `fit(X, y)` is called on a `SequentialFeatureSelector` whose `cv` is a
   single-pass iterable yielding `(train, test)` index-array pairs, THEN `fit`
   SHALL complete successfully and set the fitted attributes (`support_`,
   `n_features_to_select_`) without raising an exception.
2. WHEN `cv` is such a one-pass iterable, THEN the same set of splits SHALL be
   used for every candidate-feature evaluation across every selection round,
   rather than being exhausted after the first evaluation.
3. The system SHALL normalize the `cv` argument once, at the beginning of `fit`,
   into a reusable cross-validation representation, and SHALL use that
   representation for all cross-validation scoring performed during the fit.
4. WHEN normalizing `cv` for `fit`, THEN the selector SHALL take into account
   whether the wrapped estimator is a classifier, so that integer/`None` `cv`
   values continue to select the stratified-or-plain default fold strategy
   described for the `cv` parameter.

## Requirement 2: Preserve existing `cv` behaviors

**User story:** As an existing user, I want the previously supported `cv` values
to behave exactly as before, so that this fix does not change my results.

**Acceptance criteria**
1. WHEN `cv` is an integer, `None`, or a reusable cross-validation splitter
   object, THEN `fit` SHALL produce the same selected-feature mask it produced
   before this change for the same inputs.
2. The system SHALL continue to compute each candidate subset's score as the
   mean cross-validation score of the wrapped estimator on the candidate
   features, honoring the configured `scoring`, `n_jobs`, and `direction`.
3. WHEN feature selection completes, THEN `support_` SHALL be a boolean mask with
   exactly the number of selected features implied by `n_features_to_select`
   (and, for auto selection with `tol`, by the stopping criterion), and
   `n_features_to_select_` SHALL equal the number of selected features.

## Requirement 3: Preserve validation and other selector behavior

**User story:** As a maintainer, I want all of the selector's existing input
validation, deprecation, and support behaviors to remain intact, so that the
`cv` fix is additive only.

**Acceptance criteria**
1. IF `n_features_to_select` is an integer outside the range 1 to
   `n_features - 1`, THEN `fit` SHALL raise a `ValueError`.
2. IF `tol` is set while `n_features_to_select` is left at its deprecated
   default, THEN `fit` SHALL raise a `ValueError`.
3. IF `tol` is negative while `direction` is `"forward"`, THEN `fit` SHALL raise
   a `ValueError`.
4. WHEN `n_features_to_select` is left at its deprecated default, THEN `fit`
   SHALL emit a `FutureWarning` about that deprecation.
5. The system SHALL continue to support sparse input, inputs containing NaN when
   the wrapped estimator allows it, use inside a pipeline, and unsupervised
   fitting where `y` is `None` or ignored, exactly as before this change.
6. WHEN `direction` is `"backward"`, THEN the selector SHALL continue to remove
   features and produce the complementary support mask as before.
