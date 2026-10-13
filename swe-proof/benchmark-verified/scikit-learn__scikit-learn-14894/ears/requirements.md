# Requirements: Robust sparse SVM fitting when no support vectors are found

## Introduction

Support Vector Machine estimators in scikit-learn (`sklearn.svm`, e.g. `SVR`,
`SVC`, `NuSVR`, `NuSVC`, `OneClassSVM`) can be trained on sparse input matrices.
When a model is fit on sparse data, the internal sparse training path
(`_sparse_fit` in `sklearn/svm/base.py`) assembles the fitted `dual_coef_`
attribute as a compressed-sparse-row (CSR) matrix from three pieces produced by
the underlying libsvm sparse trainer: the coefficient data buffer, a per-class
repeated block of support-vector column indices, and a vector of evenly spaced
row offsets computed by dividing the total number of index entries by the number
of classes.

For certain datasets the trained model legitimately ends up with an **empty**
set of support vectors (the support-vector array has zero rows). In that
situation the offset computation divides by the number of index entries, which
is zero, and the sparse fit path raises `ZeroDivisionError` — even though the
equivalent dense fit path completes without error and simply produces an empty
coefficient matrix.

The goal is to make sparse fitting complete successfully in this degenerate
case, producing an empty coefficient matrix consistent with the dense path,
while leaving the normal (non-empty support vectors) fitting behavior unchanged.
The affected function is `_sparse_fit`; the observable attributes are
`support_vectors_` and `dual_coef_` on the fitted estimator.

## Requirement 1: Sparse fitting with an empty support set completes without error

**User story:** As a user fitting an SVM on sparse data, I want training to
finish normally even when the model finds no support vectors, so that a valid
dataset does not crash the fit.

**Acceptance criteria**

1. WHEN an SVM estimator is fit on a sparse input matrix and the resulting set
   of support vectors is empty, THEN the fit routine SHALL complete successfully
   and SHALL NOT raise an error.
2. IF the number of support vectors resulting from a sparse fit is zero, THEN
   the sparse fit routine SHALL NOT perform the per-class row-offset division
   that would divide by zero.
3. WHEN a sparse fit yields an empty support set, THEN the fitted estimator's
   `support_vectors_` attribute SHALL contain no stored values (its data buffer
   SHALL be empty).

## Requirement 2: Empty coefficient matrix is produced for an empty support set

**User story:** As a user inspecting a fitted sparse SVM that found no support
vectors, I want its dual coefficients to be an empty matrix, so that downstream
code sees a consistent, well-formed result.

**Acceptance criteria**

1. WHEN a sparse fit yields an empty support set, THEN the fitted estimator's
   `dual_coef_` attribute SHALL be a sparse matrix containing no stored values
   (its data buffer SHALL be empty).
2. WHEN a sparse fit yields an empty support set, THEN the produced `dual_coef_`
   SHALL be a valid sparse matrix object of the same sparse type used for a
   non-empty fit, so that attribute access and further use do not fail.
3. The behavior of a sparse fit with an empty support set SHALL be consistent
   with the corresponding dense fit on the same data, in that both SHALL leave
   the estimator with no support vectors and an empty set of dual coefficients
   rather than raising an error.

## Requirement 3: Normal sparse fitting behavior is preserved

**User story:** As a user fitting SVMs on typical sparse data with a non-empty
support set, I want existing results to be unchanged, so that the empty-case fix
introduces no regression.

**Acceptance criteria**

1. WHEN a sparse fit yields a non-empty support set, THEN the estimator's
   `dual_coef_` SHALL be assembled exactly as before: its stored values SHALL be
   the coefficient buffer returned by the trainer, its column indices SHALL be
   the support-vector index ramp repeated once per class, and its row offsets
   SHALL be evenly spaced by the number of support vectors.
2. WHEN a sparse fit yields a non-empty support set, THEN the resulting
   `dual_coef_` SHALL have a shape of (number of classes minus one for
   classification, or one for regression) rows by (number of support vectors)
   columns.
3. The system SHALL preserve the existing fitting, prediction, decision
   function, probability, and sample-weight behavior of all SVM estimators
   (`SVC`, `NuSVC`, `SVR`, `NuSVR`, `OneClassSVM`, and the linear variants) on
   both dense and sparse inputs for cases with a non-empty support set.
4. The system SHALL keep raising the existing input-validation and parameter
   errors (for invalid data, invalid `gamma`, and other unsupported parameter
   combinations) unchanged.
