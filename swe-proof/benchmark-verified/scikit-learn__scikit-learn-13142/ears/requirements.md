# Requirements — Consistent labels from mixture `fit_predict`

## Introduction

The Gaussian mixture estimators in `sklearn.mixture` expose a combined
`fit_predict(X)` method (implemented once on the shared base class
`BaseMixture.fit_predict` in `sklearn/mixture/base.py`, inherited by both
`GaussianMixture` and `BayesianGaussianMixture`). `fit_predict(X)` is documented
and expected to be equivalent to calling `fit(X)` followed by `predict(X)`:
after fitting, it should assign each sample the label of the component that the
*fitted* model considers most probable.

When the estimator runs more than one initialization (`n_init > 1`), it performs
several independent fitting trials, scores each by its final lower bound, and
keeps the parameters of the highest-scoring trial as the model's fitted
parameters. The defect is that `fit_predict` computed its returned labels from
the responsibilities of the *last* trial that happened to run, rather than from
the *selected* best-scoring trial's parameters — the parameters the estimator
actually stores and that `predict` subsequently uses. As a result, with
`n_init > 1` the labels returned by `fit_predict(X)` frequently disagreed with a
following `predict(X)` on the same data. When `n_init == 1` the last trial is
the selected trial, so the two paths already agreed; the disagreement only
surfaces for multiple initializations.

The goal is to guarantee that the labels returned by `fit_predict(X)` are always
computed from the estimator's finally-selected parameters, so they agree exactly
with `predict(X)`, for every value of `n_init`, `max_iter`, `tol`, and
`random_state`, without disturbing the existing model-selection, convergence, or
attribute-setting behavior.

## Requirement 1: `fit_predict` labels agree with `predict` for any number of initializations

**User story:** As a user of `GaussianMixture` / `BayesianGaussianMixture`, I
want `fit_predict(X)` to return the same labels I would get from `predict(X)`
after fitting, so that the two APIs are interchangeable regardless of how many
initializations I request.

**Acceptance criteria**

1. WHEN `fit_predict(X)` is called on a mixture estimator configured with
   `n_init > 1`, THEN the returned label array SHALL be element-for-element
   identical to the array returned by calling `predict(X)` on the same fitted
   estimator immediately afterward, for the same input `X`.
2. WHEN `fit_predict(X)` is called with `n_init == 1`, THEN the returned label
   array SHALL remain element-for-element identical to a following `predict(X)`
   (this equivalence, already holding, SHALL be preserved).
3. The system SHALL derive the labels returned by `fit_predict(X)` from the
   parameter configuration that the estimator retains as its fitted parameters
   (the highest-scoring trial's parameters), not from any trial's parameters
   that are discarded during model selection.
4. The equivalence between `fit_predict(X)` and a subsequent `predict(X)` SHALL
   hold for any combination of `max_iter`, `tol`, and `random_state`, including
   cases where fitting does not converge.

## Requirement 2: Correct selection of the best initialization is preserved

**User story:** As a user relying on multiple initializations, I want
`fit_predict` and `fit` to keep selecting the best trial, so that the change to
label consistency does not alter which model is chosen.

**Acceptance criteria**

1. WHEN more than one initialization is run, THEN the estimator SHALL retain the
   parameters of the trial with the greatest final lower bound as its fitted
   parameters.
2. IF two or more trials attain the same greatest lower bound, THEN the
   estimator SHALL retain the parameters of the earliest such trial, matching
   the pre-existing tie-handling behavior.
3. After `fit_predict(X)` returns, the estimator's stored fitted attributes
   (its component parameters, the recorded number of iterations for the selected
   trial, and the recorded best lower bound) SHALL reflect the selected
   best-scoring trial, exactly as before this change.
4. The final label-computation step used by `fit_predict` SHALL be applied while
   the estimator holds the selected best-scoring trial's parameters.

## Requirement 3: Convergence reporting and fitting workflow are unchanged

**User story:** As a user, I want the existing warnings and fitting behavior to
be unaffected, so that only the label-consistency defect is fixed.

**Acceptance criteria**

1. IF no initialization converges within `max_iter` iterations, THEN the
   estimator SHALL still raise a convergence warning, as it did before.
2. The system SHALL continue to run each initialization's expectation–
   maximization iterations, scoring, and best-parameter bookkeeping unchanged;
   only the point at which the final label-producing expectation step is
   performed relative to storing the selected parameters SHALL change.
3. WHEN `fit_predict(X)` completes, THEN it SHALL return one integer component
   label per input sample, in input order, with values in the range of valid
   component indices — the same output shape and label semantics as before.
4. The behavior of `predict(X)`, `predict_proba(X)`, and score-based methods
   SHALL remain unchanged; this change SHALL affect only which parameter
   configuration `fit_predict` uses to compute its returned labels.
