# Requirements: Report the time spent refitting the best model in BaseSearchCV

## Introduction

The hyper-parameter search estimators in `sklearn/model_selection/_search.py`
(`GridSearchCV` and `RandomizedSearchCV`, both built on `BaseSearchCV`) run a
cross-validated search and then, when refitting is enabled, refit a single best
model on the whole dataset. Users can already read how long each candidate took
to fit and score during the search (through the `cv_results_` timing entries),
but there is no way to know how long the *final* refit of the best model took.
When the search runs with multiple jobs this cannot be recovered by external
timing.

The goal is to have `BaseSearchCV.fit` measure the wall-clock duration of that
final refit and expose it as a new fitted attribute, `refit_time_`, on the
search estimator. The attribute holds the elapsed refit time in seconds and is
present only when a refit is actually performed. All existing search behavior —
candidate timing, the fitted best estimator, and the no-refit case — must be
preserved.

The affected code is the refit block of `BaseSearchCV.fit` in
`sklearn/model_selection/_search.py`, and the observable is the search
estimator's `refit_time_` attribute after `fit` returns.

## Requirement 1: Record the duration of the final refit

**User story:** As a user tuning hyper-parameters, I want the search estimator
to tell me how long it took to refit the best model on the full dataset, so
that I can report the cost of refitting separately from the cost of the search.

**Acceptance criteria**

1. WHEN `BaseSearchCV.fit` is called on a search estimator configured to refit
   the best model, THEN the fitted estimator SHALL expose a `refit_time_`
   attribute after `fit` returns.
2. WHEN the final refit is performed, THEN the system SHALL read a wall-clock
   value immediately before the refit begins and another immediately after it
   completes, and SHALL set `refit_time_` to the elapsed duration between those
   two readings, measured in seconds.
3. The value of `refit_time_` SHALL be a Python `float`.
4. WHEN the final refit is performed, THEN `refit_time_` SHALL be greater than
   or equal to `0`.
5. The `refit_time_` value SHALL measure only the final refit of the best model
   on the whole dataset, not the fitting or scoring of the individual
   cross-validation candidates during the search.

## Requirement 2: Omit the attribute when no refit is performed

**User story:** As a user who disables refitting, I want the estimator not to
claim a refit time it never measured, so that the attribute's presence
reliably signals that a refit happened.

**Acceptance criteria**

1. IF the search estimator is configured not to refit the best model, THEN the
   system SHALL NOT set a `refit_time_` attribute on the fitted estimator.
2. WHEN a search estimator is fitted with refitting disabled, THEN `fit` SHALL
   complete successfully without error and SHALL still populate the other
   search results (such as `cv_results_`), just as before.

## Requirement 3: Preserve existing search and timing behavior

**User story:** As an existing user of the search estimators, I want the new
attribute to be purely additive, so that none of the behavior I already rely on
changes.

**Acceptance criteria**

1. WHEN a search estimator is fitted with refitting enabled, THEN the system
   SHALL still fit `best_estimator_` on the whole dataset using the selected
   best parameters, and that estimator SHALL remain usable for prediction and
   scoring exactly as before.
2. WHEN a search completes, THEN the system SHALL still populate the
   `cv_results_` timing entries for candidate fit and score times, and those
   entries SHALL retain their existing meaning and values.
3. The addition of refit-time recording SHALL NOT alter `best_index_`,
   `best_params_`, `best_score_`, `n_splits_`, or any other previously
   produced result of the search.
4. The system SHALL continue to support both fitting with a target `y` and
   fitting without one, refitting the best model correctly in each case.
