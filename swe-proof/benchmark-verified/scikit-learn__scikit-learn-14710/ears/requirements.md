# Requirements: histogram gradient boosting early stopping with categorical (string) targets

## Introduction

The histogram-based gradient boosting estimators in
`sklearn.ensemble._hist_gradient_boosting.gradient_boosting`
(`HistGradientBoostingClassifier` and `HistGradientBoostingRegressor`, sharing a
common `BaseHistGradientBoosting.fit`) support early stopping. When early
stopping is driven by a scorer (rather than by the training loss), `fit`
periodically computes a score by invoking the estimator's fitted scorer callable
on a subsample of the training data and, when validation data is held out, on the
validation data as well. This happens in the helper
`_check_early_stopping_scorer`.

For a classifier, the class labels are first passed through a `LabelEncoder`
during target preparation, so the target arrays that flow through `fit` and reach
the scoring step hold **integer class codes** (`0 .. n_classes - 1`), not the
original labels. The scorer, however, calls the estimator's `predict`/`score`,
which produce and compare against the **original class labels**. When the
original labels are non-numeric (e.g. Python strings), comparing integer-coded
targets against string predictions raises a `TypeError` (an ordering comparison
between `str` and `float`), and `fit` crashes before it can complete.

The goal is that fitting a classifier on a categorical (including string-valued)
target with scorer-based early stopping enabled completes without error, by
decoding the integer-coded targets back to their original class labels before
they are handed to the scorer, while leaving all other early-stopping behavior
(regression, loss-based early stopping, numeric-label classification, and the
stop decision itself) unchanged.

## Requirement 1: Decode classifier targets to original labels before scoring

**User story:** As a user training `HistGradientBoostingClassifier` with
non-numeric (e.g. string) class labels and scorer-based early stopping enabled, I
want fitting to succeed, so that early stopping works regardless of my label
dtype.

**Acceptance criteria**

1. WHEN the early-stopping scoring step runs for an estimator that is a
   classifier, THEN the system SHALL convert the integer-coded training target
   array into original class labels before passing it to the scorer, by using
   each integer code as an index into the fitted class-label table
   (`classes_`), so that element `i` of the array handed to the scorer is
   `classes_[code_i]`.
2. WHILE validation data is in use during a classifier's early-stopping scoring
   step, the system SHALL apply the same integer-code-to-label conversion to the
   validation target array before passing it to the scorer.
3. WHEN a classifier is fitted on string (object-dtype) class labels with
   scorer-based early stopping enabled, THEN `fit` SHALL complete without raising
   an error.
4. WHEN a classifier is fitted on string class labels with scorer-based early
   stopping enabled, THEN the scorer SHALL receive a target array whose values
   are drawn from the original class labels and whose dtype matches those labels
   (not the internal integer/float codes), so that scoring against label-valued
   predictions does not raise a type/ordering error.
5. The system SHALL determine whether the estimator is a classifier using the
   standard estimator-type check (the same predicate already used elsewhere in
   `fit`, e.g. for stratified subsampling), rather than by inspecting label
   values.

## Requirement 2: Preserve early-stopping behavior for non-classifiers and unchanged score computation

**User story:** As a maintainer, I want the target-decoding fix to be scoped to
classifiers only, so that regressors and all existing scoring semantics are
unaffected.

**Acceptance criteria**

1. IF the estimator is not a classifier (e.g. a regressor), THEN the system SHALL
   pass the training and validation target arrays to the scorer unchanged, with
   no code-to-label conversion applied.
2. The system SHALL always append exactly one training score, computed by the
   fitted scorer on the training subsample, to the running training-score
   history each time the scoring step runs.
3. WHILE validation data is in use, the system SHALL append exactly one
   validation score, computed by the fitted scorer on the validation data, to
   the running validation-score history each time the scoring step runs.
4. WHEN validation data is in use, THEN the early-stopping stop decision SHALL be
   determined by applying the stopping rule to the validation-score history
   (after it has been extended with the new validation score).
5. WHEN validation data is not in use, THEN the early-stopping stop decision
   SHALL be determined by applying the stopping rule to the training-score
   history (after it has been extended with the new training score), and the
   validation-score history SHALL remain unchanged.

## Requirement 3: Preserve existing early-stopping paths and regression protection

**User story:** As a user relying on the existing behavior of histogram gradient
boosting, I want all previously-working early-stopping configurations to keep
working exactly as before.

**Acceptance criteria**

1. WHEN early stopping is configured to use the loss (`scoring='loss'`) rather
   than a scorer, THEN the system SHALL compute scores from the loss without
   applying any label decoding, preserving the existing loss-based early-stopping
   behavior for both classifiers and regressors.
2. WHEN a classifier is fitted on numeric class labels with scorer-based early
   stopping enabled, THEN `fit` SHALL continue to complete successfully and
   produce the same fitted result as before this change.
3. WHEN a regressor is fitted with scorer-based or loss-based early stopping,
   THEN `fit` SHALL complete successfully and its scoring behavior SHALL be
   unchanged.
4. The system SHALL keep the fitted `classes_` attribute of a classifier as the
   sorted array of the distinct original class labels, so that decoding an
   integer code `c` yields the same label the encoder assigned to `c`.
5. The system SHALL leave the estimators' existing fit-time input validation
   unchanged by this fix, so that any configuration that was accepted (or
   rejected) before the change is accepted (or rejected) identically after it,
   with the same error behavior.
6. The system SHALL keep the existing stop-decision rule so that fitting stops
   only when the recent score history fails to improve by more than the
   configured tolerance over the configured number of iterations, and otherwise
   continues.
