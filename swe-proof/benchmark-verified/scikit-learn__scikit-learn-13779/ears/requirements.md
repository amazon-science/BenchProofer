# Requirements — Voting ensemble sample-weight validation with removed estimators

## Introduction

The voting ensembles in `sklearn/ensemble/voting.py` (`VotingClassifier` and
`VotingRegressor`, sharing the base class `_BaseVoting`) hold an ordered list of
`(name, estimator)` pairs in their `estimators` attribute. Any individual
estimator slot may be removed by assigning it `None` through `set_params`
(e.g. `set_params(lr=None)`).

When the caller invokes `fit` with a `sample_weight` argument, `_BaseVoting.fit`
first walks the roster and, for each entry, verifies that the underlying
estimator can consume per-sample weights (via `has_fit_parameter(estimator,
'sample_weight')`). The problem is that this pre-fit validation loop treats
every slot as a live estimator: when a slot has been set to `None`, inspecting
it for sample-weight support dereferences a non-estimator and `fit` raises
`AttributeError: 'NoneType' object has no attribute 'fit'` instead of training
successfully on the remaining estimators.

The goal is to make `fit` tolerate removed (`None`) estimator slots when
`sample_weight` is supplied — skipping them during the support check exactly as
the rest of `fit` already skips them when cloning and training — while
preserving every other validation behavior of the ensembles.

## Requirement 1: Fitting with weights tolerates a removed estimator slot

**User story:** As a user of `VotingClassifier` / `VotingRegressor`, I want to
remove an estimator by setting it to `None` and still fit the ensemble with
per-sample weights, so that dropping a member does not break weighted training.

**Acceptance criteria**

1. WHEN `fit` is called with a non-`None` `sample_weight` and the `estimators`
   roster contains one or more slots whose estimator is `None`, THEN
   `_BaseVoting.fit` SHALL skip each `None` slot during the sample-weight
   support check and SHALL NOT attempt to inspect or access any attribute of a
   `None` slot.
2. WHEN a roster contains a `None` slot and at least one present estimator, and
   every present estimator supports per-sample weights, THEN `fit` SHALL
   complete successfully and SHALL return the fitted ensemble instance without
   raising.
3. WHEN an estimator that was previously fit is then removed via
   `set_params(<name>=None)` and the ensemble is re-fit with the same
   per-sample weights, THEN `fit` SHALL succeed on the remaining present
   estimators.
4. The system SHALL train and store only the present (non-`None`) estimators as
   the fitted members, unchanged from the behavior when no weights are supplied.

## Requirement 2: Prediction after weighted fit with a removed slot

**User story:** As a user, I want the ensemble fitted with weights and a removed
member to produce usable predictions, so that removal does not corrupt output.

**Acceptance criteria**

1. WHEN an ensemble has been successfully fit with per-sample weights while one
   slot was `None`, THEN calling `predict` SHALL return an array whose shape
   matches the target `y` used for fitting (one prediction per input sample).

## Requirement 3: Sample-weight support validation for present estimators is preserved

**User story:** As a maintainer, I want the existing sample-weight support check
to keep rejecting present estimators that cannot use weights, so that dropping
`None` handling does not weaken validation.

**Acceptance criteria**

1. WHEN `fit` is called with a non-`None` `sample_weight` and some present
   (non-`None`) estimator's `fit` does not accept a `sample_weight` parameter,
   THEN `_BaseVoting.fit` SHALL raise `ValueError`.
2. WHEN such a `ValueError` is raised, THEN the message SHALL identify the
   offending estimator by its roster name and state that it does not support
   sample weights.
3. IF more than one present estimator fails the support check, THEN the check
   SHALL report the first such estimator in roster order.
4. WHEN `sample_weight` is `None`, THEN `fit` SHALL NOT perform the
   sample-weight support check for any slot.

## Requirement 4: Preserved roster and configuration validation (regression guards)

**User story:** As a maintainer, I want all other pre-fit validation to remain
intact, so that this change is narrowly scoped to `None`-slot handling.

**Acceptance criteria**

1. IF the `estimators` attribute is `None` or empty when `fit` is called, THEN
   `fit` SHALL raise an error indicating that `estimators` must be a non-empty
   list of `(name, estimator)` tuples.
2. IF `weights` is provided and its length differs from the number of
   `estimators`, THEN `fit` SHALL raise `ValueError` reporting the mismatched
   counts.
3. IF every estimator in the roster is `None`, THEN `fit` SHALL raise
   `ValueError` indicating that at least one estimator is required.
4. The system SHALL continue to validate that estimator names are unique and
   otherwise well-formed before fitting.
5. The system SHALL continue to allow setting an individual estimator slot to
   `None` through `set_params` and to reflect that change in the ensemble's
   parameters.
6. The system SHALL preserve existing weighted-fit behavior for rosters that
   contain no `None` slots, including honoring per-member `weights` during
   prediction and transformation.
