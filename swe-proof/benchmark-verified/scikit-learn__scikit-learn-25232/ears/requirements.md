# IterativeImputer constant-strategy fill value

## Introduction

`sklearn.impute.IterativeImputer` seeds the first imputation round by delegating
to an internal `SimpleImputer` whose strategy is taken from the estimator's
`initial_strategy` parameter. When `initial_strategy="constant"`, that internal
imputer replaces every missing entry with a constant. `SimpleImputer` lets the
caller choose this constant through its `fill_value` parameter, but
`IterativeImputer` exposed no equivalent parameter, so users could not control
the constant used for the initial imputation.

This bundle specifies the behavior of adding a caller-controllable constant to
`IterativeImputer` (class `IterativeImputer` in `sklearn/impute/_iterative.py`),
wired through to the internal initial imputer built in the estimator's initial
imputation step (`_initial_imputation`). The goal: when the initial strategy is
constant, the initial imputation must use the user-supplied constant, matching
the semantics already provided by `SimpleImputer`, while leaving all other
strategies and existing behavior unchanged.

## Requirement 1: Expose a caller-controllable constant on IterativeImputer

**User story:** As a user of `IterativeImputer`, I want to specify the constant
used to seed missing values when the initial strategy is constant, so that I
control the starting point of the iterative imputation.

**Acceptance criteria**
1. The system SHALL accept a new keyword parameter on the `IterativeImputer`
   constructor that names the constant to use for constant initial imputation,
   with a default value of `None`.
2. WHEN an `IterativeImputer` is constructed with a value for this parameter,
   THEN the estimator SHALL store that value unchanged as a public attribute of
   the same name, so that `get_params` returns it verbatim.
3. The system SHALL treat this parameter as accepting any value, imposing no
   parameter-validation constraint of its own on the constructor argument
   (validation of the constant against the data is deferred to the initial
   imputation step).
4. WHEN this parameter is not supplied, THEN the estimator SHALL behave exactly
   as before its introduction, preserving the previous constant-initialization
   default (0 for numeric data and the string `"missing_value"` for
   string/object data).

## Requirement 2: Propagate the constant to the initial imputation

**User story:** As a user who set `initial_strategy="constant"`, I want my chosen
constant to actually be used for the first-round imputation, so that missing
values are seeded with the value I asked for.

**Acceptance criteria**
1. WHEN the estimator builds its internal initial imputer during fitting, THEN
   it SHALL forward the caller-supplied constant to that internal `SimpleImputer`
   as the latter's fill value, alongside the already-forwarded missing-values,
   strategy, and empty-feature settings.
2. WHEN `initial_strategy="constant"` and a numerical constant is supplied,
   THEN after fitting the fitted internal initial imputer SHALL expose a
   per-feature statistics array in which every feature's statistic equals the
   supplied constant.
3. WHEN `initial_strategy="constant"` and a constant is supplied, THEN each
   missing entry of the input SHALL be replaced in the initial imputation by the
   supplied constant, and non-missing entries SHALL be left unchanged.
4. WHEN `initial_strategy="constant"` and no constant is supplied, THEN the
   initial imputation SHALL use the default constant (0 for numeric data,
   `"missing_value"` for string/object data), matching the prior behavior.
5. IF the number of iterative refinement rounds is configured to zero, THEN
   `fit_transform` SHALL still complete the initial imputation, fit the internal
   initial imputer, and make that fitted internal imputer available on the
   estimator for inspection.

## Requirement 3: Preserve existing imputation behavior

**User story:** As an existing user of `IterativeImputer` and `SimpleImputer`, I
want all prior behavior to remain intact, so that adding the new parameter does
not regress any existing functionality.

**Acceptance criteria**
1. WHEN `initial_strategy` is `"mean"`, `"median"`, or `"most_frequent"`, THEN
   the initial imputation SHALL be computed exactly as before and SHALL be
   unaffected by the value of the new constant parameter.
2. The system SHALL continue to accept only `"mean"`, `"median"`,
   `"most_frequent"`, and `"constant"` as valid values of `initial_strategy`,
   rejecting any other value.
3. The system SHALL preserve the shape and semantics of `IterativeImputer`
   output: transformed arrays keep the input's row and column counts, and
   features that were entirely missing are handled according to the
   empty-feature setting as before.
4. The system SHALL preserve `SimpleImputer`'s constant-strategy behavior across
   numeric, string, object, and pandas-categorical data, including its handling
   of empty features under the empty-feature setting.
5. WHEN clipping bounds (`min_value`/`max_value`) are configured, THEN
   `IterativeImputer` SHALL continue to honor them as before, independent of the
   new constant parameter.
