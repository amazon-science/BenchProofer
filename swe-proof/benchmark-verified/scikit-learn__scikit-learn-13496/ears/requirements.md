# Requirements: Expose `warm_start` in IsolationForest

## Introduction

`sklearn.ensemble.IsolationForest` is an outlier-detection estimator that
inherits its ensemble-fitting machinery from `sklearn.ensemble.BaseBagging`.
The bagging base class already supports incremental growth of an ensemble
through a `warm_start` configuration flag: when enabled, a subsequent call to
`fit` reuses the estimators built by a previous call and appends only the
additional estimators required to reach the current requested ensemble size,
instead of discarding the ensemble and building it from scratch.

However, `IsolationForest.__init__` did not accept `warm_start` as a
constructor argument. Because the flag was never passed up to the parent
constructor, an `IsolationForest` instance always used the base-class default
(the disabled state), and the incremental-growth capability was effectively
unreachable through the public constructor API.

The goal is to expose `warm_start` as a public constructor parameter of
`IsolationForest` (module `sklearn/ensemble/iforest.py`), defaulting to the
disabled state, and to forward it to the parent bagging constructor so that the
incremental ensemble-growth behavior becomes usable — while leaving all other
existing `IsolationForest` behavior unchanged.

## Requirement 1: Expose the warm-start configuration flag on the constructor

**User story:** As a user of `IsolationForest`, I want to configure warm-start
behavior directly through the constructor, so that I can grow an isolation
forest incrementally without inspecting or monkey-patching library internals.

**Acceptance criteria**

1. The system SHALL accept a `warm_start` keyword argument on
   `sklearn.ensemble.IsolationForest.__init__`.
2. WHEN `IsolationForest` is constructed without specifying `warm_start`, THEN
   the constructor SHALL default the warm-start configuration to the disabled
   state (a boolean false value).
3. WHEN `IsolationForest` is constructed with an explicit `warm_start` value,
   THEN the constructed instance SHALL retain that exact value as the
   `warm_start` attribute readable on the instance.
4. The system SHALL forward the supplied `warm_start` value to the parent
   ensemble constructor so that the parent's fitting logic observes the same
   value that was supplied to `IsolationForest`.
5. The system SHALL allow the `warm_start` attribute to be changed after
   construction through the standard estimator parameter-setting interface, and
   a subsequent fit SHALL honor the updated value.

## Requirement 2: Incremental addition of trees when warm-start is enabled

**User story:** As a user growing an isolation forest over several fits, I want
enabling warm-start and increasing the requested number of estimators to append
new trees rather than rebuild the whole forest, so that previously fitted trees
are preserved.

**Acceptance criteria**

1. WHEN an `IsolationForest` is constructed with the warm-start configuration
   enabled and fitted, and then the requested number of estimators is increased
   and the estimator is fitted again on the same data, THEN the fitted ensemble
   SHALL contain exactly the newly requested number of trees.
2. WHILE warm-start is enabled across successive fits with a growing requested
   ensemble size, the estimator SHALL preserve the trees produced by earlier
   fits: each tree object present after an earlier fit SHALL remain the same
   object at its original position in the ensemble after the later fit.
3. WHEN the ensemble is grown under warm-start, THEN only the additional trees
   needed to reach the requested count SHALL be built, and the previously built
   trees SHALL NOT be refitted or replaced.

## Requirement 3: Preserve existing IsolationForest behavior

**User story:** As an existing user of `IsolationForest`, I want all prior
functionality to keep working unchanged after warm-start is exposed, so that
adding the new parameter does not regress current usage.

**Acceptance criteria**

1. WHEN `IsolationForest` is constructed and fitted with default parameters
   (warm-start left at its disabled default), THEN each fit SHALL build a fresh
   ensemble containing exactly the requested number of estimators, independent
   of any previous fit.
2. The system SHALL continue to accept and store all previously supported
   constructor parameters (including the number of estimators, the sample-count
   setting, the feature-fraction setting, bootstrap selection, contamination,
   behaviour selection, parallelism, random-state, and verbosity) with their
   established defaults and meanings.
3. The system SHALL continue to support fitting on both dense and sparse input
   data, and SHALL continue to raise the established errors for invalid
   configurations (for example an out-of-range sample-count setting or an
   unsupported contamination value).
4. The system SHALL continue to expose the established fitted attributes and
   the anomaly-scoring, decision-function, and prediction interfaces with
   their existing semantics after fitting.
5. IF warm-start is enabled but the requested number of estimators is not
   increased before a subsequent fit, THEN the estimator SHALL NOT silently
   corrupt the ensemble and SHALL leave the previously fitted trees intact.
