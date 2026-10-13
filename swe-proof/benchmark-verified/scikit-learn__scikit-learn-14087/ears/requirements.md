# Requirements — LogisticRegressionCV with `refit=False`

## Introduction

`LogisticRegressionCV.fit` in `sklearn/linear_model/logistic.py` estimates an
inverse-regularization strength (and, for elastic-net, a mixing ratio) by
cross-validation. When `refit=True` it refits a final model; when
`refit=False` it instead summarizes the cross-validation results directly by
averaging, per class, the best-scoring per-fold coefficient estimates and
recording the corresponding chosen hyper-parameters into the fitted
attributes `coef_`, `intercept_`, `C_`, and `l1_ratio_`.

Two defects exist in the `refit=False` summary loop:

1. The branch that selects how the per-fold coefficient array (`coefs_paths`)
   is averaged is chosen from the **raw configured** `self.multi_class`
   attribute rather than the **effective** multiclass strategy that the rest
   of `fit` actually used. `self.multi_class` defaults to `'auto'`, and
   `fit` resolves `'auto'` (via `_check_multi_class`) to a concrete
   `'ovr'` or `'multinomial'` strategy that determines the shape of
   `coefs_paths`. When the configured value is `'auto'` (or otherwise differs
   from the resolved value) the summary loop selects the wrong averaging
   branch and indexes `coefs_paths` with the wrong number of axes, raising
   `IndexError: too many indices for array`.

2. The loop unconditionally computes and records a mixing-ratio value into
   `l1_ratio_` even when `penalty` is not `'elasticnet'`. Outside elastic-net,
   the internal mixing-ratio list is a singleton placeholder rather than a
   list of requested ratios, so the recorded value is meaningless.

The goal is that fitting a `LogisticRegressionCV` with `refit=False` completes
without error for every combination of multiclass strategy and (non-)elastic-net
penalty, and that the fitted summary attributes are correct.

## Requirement 1: Fit succeeds with `refit=False` regardless of multiclass strategy

**User story:** As a user tuning regularization by cross-validation without a
final refit, I want `LogisticRegressionCV(refit=False).fit(X, y)` to complete
successfully, so that I can obtain cross-validated hyper-parameter estimates
without hitting an internal error.

**Acceptance criteria**
1. WHEN `LogisticRegressionCV` is fit with `refit=False` and `multi_class`
   left at its default (`'auto'`), THEN the estimator SHALL complete `fit`
   without raising an exception.
2. WHEN `LogisticRegressionCV` is fit with `refit=False` and `multi_class`
   set to `'ovr'`, `'multinomial'`, or `'auto'`, THEN the estimator SHALL
   complete `fit` without raising an exception.
3. WHEN `LogisticRegressionCV` is fit with `refit=False` on a problem with
   more than two classes, THEN the estimator SHALL complete `fit` without
   raising `IndexError` (or any other exception) in the per-class coefficient
   summary loop.
4. The coefficient-averaging branch used in the `refit=False` summary loop
   SHALL be selected according to the effective multiclass strategy actually
   used to compute `coefs_paths` (the value produced by resolving
   `self.multi_class` through `_check_multi_class` for the given solver and
   number of classes), NOT according to the unresolved configured
   `self.multi_class` value.
5. WHEN the effective multiclass strategy is one-vs-rest, THEN the per-fold
   coefficient array SHALL be indexed and averaged using the per-class
   (fewer-leading-axes) layout; WHEN the effective strategy is multinomial,
   THEN it SHALL be indexed and averaged using the joint (additional-leading-axis)
   layout.

## Requirement 2: Correct `l1_ratio_` recording outside elastic-net

**User story:** As a user inspecting the fitted attributes after a
`refit=False` cross-validation, I want the recorded mixing ratio to reflect
whether an elastic-net penalty was actually used, so that the reported value
is meaningful.

**Acceptance criteria**
1. IF `penalty` is not `'elasticnet'`, THEN for each class the `refit=False`
   summary loop SHALL append `None` as that class's entry in `l1_ratio_`.
2. IF `penalty` is `'elasticnet'`, THEN for each class the `refit=False`
   summary loop SHALL append the mean of the requested mixing ratios selected
   by the best-scoring per-fold indices, exactly as before.
3. WHEN `refit=False` is used with a non-elastic-net penalty, THEN the summary
   loop SHALL NOT index the internal mixing-ratio placeholder list to derive a
   numeric mixing ratio.

## Requirement 3: Preserve chosen-`C_` and coefficient summary behavior

**User story:** As a user relying on the cross-validated summary attributes, I
want the chosen regularization strength and averaged coefficients to keep their
established semantics, so that fixing the error does not change correct results.

**Acceptance criteria**
1. WHEN `refit=False`, THEN for each class `C_` SHALL record the mean of the
   inverse-regularization strengths selected by the best-scoring per-fold
   indices, unchanged from the prior behavior.
2. WHEN `refit=False`, THEN `coef_` and `intercept_` SHALL be populated from
   the average, across folds, of the best-scoring per-fold coefficient
   estimates, consistent with the effective multiclass strategy.
3. The fitted `l1_ratio_` attribute SHALL have one entry per modeled class
   (tiled across classes for the multinomial strategy, as before).

## Requirement 4: Preserve elastic-net and `refit=True` behavior (regression protection)

**User story:** As an existing user of elastic-net cross-validation and of the
default refitting path, I want their behavior unchanged, so that the fix is
strictly additive.

**Acceptance criteria**
1. WHEN `refit=False` is used with `penalty='elasticnet'` (with any of the
   `'ovr'`, `'multinomial'`, or `'auto'` multiclass strategies), THEN `fit`
   SHALL complete successfully and produce the same fitted attribute shapes
   and values as before this fix.
2. WHEN `refit=True`, THEN the final-model refitting path and all of its
   fitted attributes SHALL remain unchanged.
3. The estimator SHALL continue to produce correctly shaped `coefs_paths_`,
   `scores_`, `n_iter_`, `Cs_`, and `l1_ratios_` attributes, including the
   additional mixing-ratio dimension added when an elastic-net penalty with a
   requested `l1_ratios` array is used.
4. The system SHALL continue to raise the existing validation errors for
   invalid configurations (for example, an unsupported penalty or an invalid
   `l1_ratio`/`l1_ratios` value) with no change to their behavior.
