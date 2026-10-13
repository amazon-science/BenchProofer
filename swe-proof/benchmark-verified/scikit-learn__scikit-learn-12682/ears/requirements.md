# Requirements: Expose the solver iteration budget on the sparse-coding estimators

## Introduction

In `sklearn/decomposition/dict_learning.py`, the sparse-coding estimators
`SparseCoder`, `DictionaryLearning`, and `MiniBatchDictionaryLearning` (all
built on `SparseCodingMixin`) encode data by delegating to the module-level
`sparse_encode` function, which in turn runs a per-algorithm solver:
coordinate descent (`Lasso`) when the transform algorithm is `lasso_cd`, or
`LassoLars` when the transform algorithm is `lasso_lars`. These solvers are
iterative and stop either at convergence or at a maximum-iteration cap.

The defect: the estimators let the user configure the algorithm, the
regularization, the number of nonzero coefficients, positivity, and so on, but
they provide **no way to control the maximum number of iterations of the
underlying iterative solver**. Regardless of what the user wants, the solver
runs at its own hard-coded default cap. When that cap is too small for a hard
problem the solver fails to converge and emits a `ConvergenceWarning` (this is
what surfaced in the sparse-coding example), and the user has no lever to raise
the cap and make it converge.

The goal is to give these estimators a construction-time option for the
solver's maximum-iteration budget (defaulting to the previous value of 1000 so
existing behavior is unchanged), to thread that budget through the encoding
step into the underlying solver for both the coordinate-descent and the
least-angle lasso algorithms, and to expose an equivalent budget on the
module-level dictionary-learning entry points (`sparse_encode`,
`dict_learning`, `dict_learning_online`) so the value actually reaches the
solver. The affected module is `sklearn/decomposition/dict_learning.py`.

## Requirement 1: Configurable solver iteration budget on `SparseCoder`

**User story:** As a user of `SparseCoder`, I want to set the maximum number of
iterations of the underlying sparse-coding solver, so that I can make a hard
problem converge instead of being stuck at a fixed default cap.

**Acceptance criteria**

1. The `SparseCoder` constructor SHALL accept an optional integer option that
   specifies the maximum number of iterations to allow the underlying
   iterative sparse-coding solver, and SHALL default that option to 1000 when
   the caller does not supply it.
2. The system SHALL record the supplied value on the constructed estimator so
   that it governs subsequent transforms, without requiring any change to the
   existing constructor options (algorithm, number of nonzero coefficients,
   alpha, split-sign, parallel jobs, positivity).
3. WHEN `SparseCoder.transform` (or `fit_transform`) encodes input data, THEN
   the system SHALL pass the configured maximum-iteration budget to the
   sparse-encoding step so that it bounds the underlying solver's iterations.
4. WHILE the configured budget is left at its default, the system SHALL produce
   the same encoding results and the same solver iteration behavior as before
   the option existed (i.e. the default of 1000 reproduces prior behavior).

## Requirement 2: The budget actually governs solver convergence

**User story:** As a user, I want the iteration budget I set to genuinely reach
the iterative solver, so that raising it removes non-convergence warnings and
lowering it forces early termination.

**Acceptance criteria**

1. WHEN a `SparseCoder` configured to encode with the coordinate-descent
   algorithm is fit/transformed on data for which that solver needs many
   iterations, AND the configured maximum-iteration budget is set to a value
   far too small for that solver to reach convergence, THEN the system SHALL
   allow the solver to stop at that cap without converging and SHALL emit a
   `ConvergenceWarning`.
2. WHEN the same estimator on the same data is instead configured with a
   maximum-iteration budget large enough for the coordinate-descent solver to
   converge, THEN the system SHALL let the solver converge and SHALL NOT emit
   any warning.
3. The system SHALL treat the configured budget as the effective iteration cap
   of the solver, so that the presence or absence of the non-convergence
   warning is determined by the user-supplied value rather than by a fixed
   internal default.

## Requirement 3: Budget forwarded through the module-level encoding functions

**User story:** As a caller of the module-level sparse-coding and
dictionary-learning functions, I want a maximum-iteration budget I pass in to
be forwarded to the underlying solver, so that the estimators built on these
functions can control it.

**Acceptance criteria**

1. WHEN `sparse_encode` is called with a maximum-iteration budget, THEN the
   system SHALL forward that budget to the solver selected by the `algorithm`
   argument for both the coordinate-descent (`lasso_cd`) and the least-angle
   lasso (`lasso_lars`) algorithms, rather than passing it to only one of them.
2. The `dict_learning` and `dict_learning_online` functions SHALL accept an
   optional integer parameter (default 1000) that specifies the maximum number
   of iterations to use when solving the sparse-coding sub-problem, and SHALL
   forward it to their internal calls to the sparse-encoding step.
3. WHEN no maximum-iteration budget is supplied to these functions, THEN the
   system SHALL use 1000, preserving the previously effective iteration cap.

## Requirement 4: Budget exposed on the dictionary-learning estimators

**User story:** As a user of `DictionaryLearning` and
`MiniBatchDictionaryLearning`, I want the same iteration-budget control, so
that the transform/coding step in these estimators can be tuned too.

**Acceptance criteria**

1. The `DictionaryLearning` and `MiniBatchDictionaryLearning` constructors SHALL
   each accept an optional integer maximum-iteration option (default 1000) with
   the same meaning as on `SparseCoder`, and SHALL record it on the estimator.
2. WHEN `DictionaryLearning.fit` runs its dictionary-learning routine, THEN the
   system SHALL forward the configured maximum-iteration budget into the
   sparse-coding step of that routine.
3. WHEN `MiniBatchDictionaryLearning.fit` or `partial_fit` runs its online
   dictionary-learning routine, THEN the system SHALL forward the configured
   maximum-iteration budget into the sparse-coding step of that routine.

## Requirement 5: Regression protection for existing behavior

**User story:** As a maintainer, I want the existing sparse-coding and
dictionary-learning behavior to be unchanged apart from the new control, so
that adding the iteration-budget option introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep producing correctly shaped codes and dictionaries for
   `sparse_encode`, `dict_learning`, `dict_learning_online`, `SparseCoder`,
   `DictionaryLearning`, and `MiniBatchDictionaryLearning` across the supported
   algorithms (`omp`, `lars`, `lasso_lars`, `lasso_cd`, `threshold`).
2. The system SHALL continue to honor the `positive_code`/`positive` and
   `positive_dict` options, producing non-negative codes and/or dictionaries
   when requested, and SHALL continue to reject positivity for algorithms that
   do not support it.
3. The system SHALL continue to reject an unknown sparse-coding algorithm and
   an unknown fit algorithm with an error, unchanged by the new option.
4. The system SHALL keep the split-sign feature-vector behavior, the parallel
   (multi-job) encoding behavior, and read-only input handling working as
   before.
5. The system SHALL keep the reconstruction quality of the dictionary-learning
   routines within their previously expected tolerance, so that fitted models
   still approximate their input.
6. The system SHALL preserve the existing signatures' behavior for all
   previously accepted arguments, so that callers that do not use the new
   maximum-iteration option observe no change.
