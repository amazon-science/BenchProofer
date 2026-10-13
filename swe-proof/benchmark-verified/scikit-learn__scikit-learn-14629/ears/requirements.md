# Requirements: per-target class labels on the multi-output classifier

## Introduction

`sklearn.multioutput.MultiOutputClassifier` extends a base classifier to
multi-target problems by fitting one independent sub-estimator per target
column of `Y`. After fitting, each sub-estimator records the distinct class
labels it observed for its own target.

Consumers of a fitted classifier — including cross-validation utilities such as
`sklearn.model_selection.cross_val_predict` when called with
`method='predict_proba'` — read the fitted estimator's `classes_` attribute to
align the columns of predicted probabilities with class labels. Today
`MultiOutputClassifier` inherits its `fit` from `MultiOutputEstimator` and never
exposes a `classes_` attribute, so reading `estimator.classes_` on a fitted
`MultiOutputClassifier` raises `AttributeError`, and
`cross_val_predict(..., method='predict_proba')` fails on such an estimator.

The goal is for a fitted `MultiOutputClassifier` to expose a `classes_`
attribute holding the per-target class labels, mirroring the shape already
provided by `sklearn.multioutput.ClassifierChain`, without changing any other
fitting, prediction, or validation behavior of the affected classes.

## Requirement 1: Expose per-target class labels after fitting the multi-output classifier

**User story:** As a user of `MultiOutputClassifier`, I want the fitted
estimator to expose the class labels for each target, so that downstream tools
that read `classes_` (such as probability-based cross-validation) work without
raising an attribute error.

**Acceptance criteria**

1. WHEN `fit` is called on a `MultiOutputClassifier` with input data `X` and a
   multi-target label matrix `Y`, THEN the fitted estimator SHALL expose a
   `classes_` attribute.
2. The `classes_` attribute of a fitted `MultiOutputClassifier` SHALL be a
   Python `list`.
3. The `classes_` list SHALL contain exactly one entry per target column of
   `Y`, so that its length equals the number of targets (equivalently, the
   number of fitted sub-estimators).
4. WHEN the fitted estimator's `classes_` is read, THEN entry `i` of the list
   SHALL be exactly the class labels recorded by the sub-estimator fitted for
   target column `i`, preserving the order of the targets.
5. The class labels reported in each entry SHALL equal, elementwise and in
   order, the class labels the corresponding sub-estimator would report for its
   target.
6. WHILE a `MultiOutputClassifier` has not yet been fitted, reading `classes_`
   MAY be undefined; the attribute SHALL become defined only as a result of
   fitting.

## Requirement 2: Preserve existing multi-output fitting and prediction behavior

**User story:** As a maintainer, I want the class-label exposure to be purely
additive, so that all previously working multi-output classification,
regression, probability, and sample-weight behaviors keep working unchanged.

**Acceptance criteria**

1. WHEN `fit` is called on a `MultiOutputClassifier`, THEN the estimator SHALL
   still fit one independent sub-estimator per target column of `Y` and expose
   them as the `estimators_` attribute, and SHALL return `self`.
2. WHEN `predict` is called on a fitted `MultiOutputClassifier`, THEN it SHALL
   return the per-target predictions with one column per target, unchanged from
   prior behavior.
3. WHEN `predict_proba` is called on a fitted `MultiOutputClassifier` whose
   sub-estimators support probability estimates, THEN it SHALL return the list
   of per-target probability arrays, unchanged from prior behavior.
4. IF a `sample_weight` argument is supplied to `fit` while the underlying base
   estimator does not support sample weights, THEN `fit` SHALL raise a
   `ValueError`; and IF the base estimator does support sample weights, THEN the
   weights SHALL be forwarded to each sub-estimator as before.
5. The system SHALL continue to raise the existing validation errors for
   invalid inputs (for example, a target array with fewer than two dimensions
   for multi-output estimation, or a base estimator lacking a required method),
   with behavior unchanged by this change.
6. The system SHALL leave the multi-output *regressor* fitting and prediction
   behavior unaffected; only the classifier acquires the per-target class-label
   attribute.

## Requirement 3: Consistent per-target class-label shape across multi-output classifiers

**User story:** As a user who may switch between multi-output classification
strategies, I want the per-target class-label attribute to have the same shape
across them, so that code reading `classes_` behaves uniformly.

**Acceptance criteria**

1. The `classes_` attribute exposed by a fitted `MultiOutputClassifier` SHALL
   have the same structure — a list with one class-label array per target — as
   the `classes_` attribute already exposed by a fitted `ClassifierChain`.
2. WHEN a base classifier that natively supports multi-target labels is fitted
   directly (without a multi-output wrapper), THEN its own `classes_`
   representation SHALL remain unchanged by this change.
3. The system SHALL keep the existing `ClassifierChain` behavior of exposing a
   per-target `classes_` list intact.
