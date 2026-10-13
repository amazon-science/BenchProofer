# Requirements: Honor the configured input-duplication choice when fitting `LassoLarsIC`

## Introduction

The `LassoLarsIC` estimator in `sklearn/linear_model/least_angle.py` exposes a
boolean `copy_X` at construction time that controls whether the input feature
matrix is duplicated before the data-preparation step (`_preprocess_data`) runs,
or may instead be overwritten in place. Its `fit(X, y, ...)` method also accepts
a `copy_X` argument of the same meaning.

Because the two settings existed independently, the value supplied at
construction time was ignored: `fit` always forwarded the estimator's stored
attribute to the data-preparation step while its own `copy_X` argument (with a
non-`None` default) was silently dropped. A user who constructed
`LassoLarsIC(copy_X=False)` and then called `fit(X, y)` had their choice
overridden, and there was no way to state the choice per call.

The goal is a single, well-defined resolution: the value the caller supplies at
fit time takes precedence when one is explicitly given; otherwise the value
configured at construction time is used; and exactly that resolved boolean is the
one delivered to the data-preparation step (and therefore governs whether the
feature matrix is copied). All existing least-angle regression behavior must be
preserved.

## Requirement 1: `fit` honors an explicit per-call duplication choice

**User story:** As a user of `LassoLarsIC`, I want the `copy_X` value I pass to
`fit` to take effect, so that I can decide per call whether my feature matrix may
be overwritten in place.

**Acceptance criteria**

1. WHEN `fit` is called on a `LassoLarsIC` estimator with an explicit `copy_X`
   value, THEN the estimator SHALL use that explicit value as the
   input-duplication choice delivered to the data-preparation step, regardless of
   the value configured at construction time.
2. WHEN `fit` is called with an explicit input-duplication value of true, THEN
   the estimator SHALL leave the caller's feature matrix unchanged (its contents
   equal to before the call) after fitting completes.
3. WHEN `fit` is called with an explicit input-duplication value of false, THEN
   the estimator SHALL be permitted to overwrite the caller's feature matrix in
   place during data preparation.
4. IF the explicit per-call value differs from the value configured at
   construction time, THEN the estimator SHALL use the explicit per-call value
   and SHALL NOT substitute the configured value.

## Requirement 2: `fit` falls back to the configured choice when none is given

**User story:** As a user of `LassoLarsIC`, I want the `copy_X` value I set at
construction to be respected when I call `fit` without restating it, so that my
configured choice is not silently overridden.

**Acceptance criteria**

1. WHEN `fit` is called without an explicit `copy_X` argument, THEN the estimator
   SHALL use the input-duplication value configured at construction time as the
   choice delivered to the data-preparation step.
2. WHEN a `LassoLarsIC` estimator is constructed with the input-duplication
   choice set to false and `fit(X, y)` is then called without an explicit
   per-call value, THEN the estimator SHALL be permitted to overwrite the
   caller's feature matrix in place (it SHALL NOT force a copy).
3. WHEN a `LassoLarsIC` estimator is constructed with the input-duplication
   choice set to true and `fit(X, y)` is then called without an explicit per-call
   value, THEN the estimator SHALL leave the caller's feature matrix unchanged
   after fitting completes.
4. The system SHALL treat the per-call argument as optional, providing a default
   that is distinguishable from any explicit boolean the caller may pass, so that
   "no value supplied" is reliably separated from an explicitly supplied `false`.

## Requirement 3: A single, definite duplication flag is delivered

**User story:** As a maintainer, I want exactly one well-defined duplication flag
to reach the data-preparation step, so that fitting has no mixed or contradictory
behavior between the two `copy_X` settings.

**Acceptance criteria**

1. The system SHALL resolve the two input-duplication settings into exactly one
   definite boolean before invoking the data-preparation step.
2. WHEN the data-preparation step is invoked during `fit`, THEN the estimator
   SHALL pass it the resolved duplication boolean (the explicit per-call value if
   one was supplied, otherwise the configured value) rather than unconditionally
   passing the configured attribute.
3. The system SHALL leave the estimator's configuration attribute unchanged by a
   `fit` call; supplying a per-call value SHALL affect only that call.

## Requirement 4: Existing least-angle regression behavior is preserved

**User story:** As an existing user, I want all other `LassoLarsIC`, `Lars`, and
`lars_path` behavior to remain unchanged, so that this fix introduces no
regression.

**Acceptance criteria**

1. WHEN `fit` is called in the ordinary way (no explicit per-call duplication
   value), THEN the estimator SHALL continue to compute the same fitted
   coefficients, information-criterion selection, and path results it produced
   before, for both the AIC and BIC criteria.
2. The system SHALL keep the existing behavior of the Lars, LarsCV, LassoLars,
   LassoLarsCV, and `lars_path` code paths in `sklearn/linear_model/least_angle.py`
   unchanged, including their support for precomputed Gram matrices, the
   positivity constraint, multi-target inputs, and the no-path
   (`fit_path=False`) option.
3. The system SHALL continue to validate `X` and `y` and apply centering/scaling
   during data preparation exactly as before, differing only in which
   duplication boolean governs whether the feature matrix is copied.
