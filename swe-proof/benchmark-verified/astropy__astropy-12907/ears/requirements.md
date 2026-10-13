# Requirements: Correct separability for nested compound models

## Introduction

`astropy.modeling.separable` provides `separability_matrix(transform)` and
`is_separable(transform)`, which report how the outputs of a (compound) model
depend on its inputs. `separability_matrix` returns a boolean correlation
matrix of shape `(n_outputs, n_inputs)`: entry `[i, j]` is `True` when output
`i` depends on input `j`, and `False` when it is independent.

The correlation of a compound model is assembled recursively from its
sub-transforms according to the operator that joins them. For the parallel
("and", `&`) operator the two sub-transforms act on disjoint blocks of inputs
to produce disjoint blocks of outputs, so the combined matrix should be
*block-diagonal*: the left sub-transform's own correlation block in the
top-left, the right sub-transform's own correlation block in the bottom-right,
and zeros elsewhere.

There is a defect in the helper that implements the `&` combination
(`_cstack` in `astropy/modeling/separable.py`). When the right operand of `&`
is itself an already-computed correlation matrix — which happens whenever a
compound model is *nested* inside another with `&` (e.g.
`Pix2Sky_TAN() & (Linear1D(10) & Linear1D(5))`) — the helper discards the
right operand's internal structure and marks the whole right block as fully
correlated (all-ones) instead of copying the right operand's actual matrix
into the bottom-right block. As a result, outputs and inputs that are in fact
independent are reported as coupled. The goal is to make the `&` combination
preserve each operand's own correlation structure regardless of nesting depth,
so that a nested composition yields the same separability matrix as the
equivalent flat composition.

The affected module is `astropy/modeling/separable.py`; the behavior is
observed through `separability_matrix` and `is_separable`.

## Requirement 1: Parallel combination preserves each operand's own structure

**User story:** As a user analyzing a compound model, I want the `&` (parallel)
combination of two sub-transforms to keep each sub-transform's internal
input/output dependency structure, so that separable outputs stay reported as
separable no matter how the model is grouped.

**Acceptance criteria**

1. WHEN `separability_matrix` combines two sub-transforms with the `&`
   operator, THEN the system SHALL produce a matrix whose top-left block equals
   the left sub-transform's own correlation matrix and whose bottom-right block
   equals the right sub-transform's own correlation matrix.
2. WHEN two sub-transforms are combined with `&`, THEN the system SHALL set
   every entry outside those two diagonal blocks to `False` (independent),
   reflecting that the two sub-transforms share neither inputs nor outputs.
3. WHEN the right operand of a `&` combination is an already-computed
   correlation matrix (as arises when a compound model is nested on the right),
   THEN the system SHALL copy that operand's actual matrix entries into the
   bottom-right block rather than marking the block as uniformly correlated.
4. The resulting matrix SHALL have shape `(left_outputs + right_outputs,
   left_inputs + right_inputs)`.

## Requirement 2: Nested compound models match their flat equivalents

**User story:** As a user, I want a nested compound model to report the same
separability as the logically equivalent un-nested model, so that grouping
sub-models with parentheses does not change the reported independence of
outputs.

**Acceptance criteria**

1. WHEN `separability_matrix` is called on a model built as
   `A & (B & C)`, THEN the system SHALL return the same matrix it returns for
   the equivalent flat model `A & B & C`.
2. WHEN a compound model consisting solely of independent one-dimensional
   sub-models is combined under `&` at any nesting depth, THEN the system SHALL
   return a purely diagonal boolean matrix (each output depends only on its own
   single input).
3. WHEN a non-separable multi-input sub-model (whose outputs each depend on all
   of its own inputs) is placed in parallel with other sub-models via `&`,
   THEN the system SHALL report full mutual dependence only within that
   sub-model's own input/output block and independence between that block and
   the other sub-models' blocks, regardless of nesting.
4. IF nesting a compound model on the right of `&` previously introduced
   spurious `True` entries linking otherwise-independent outputs and inputs,
   THEN the system SHALL no longer report those spurious dependencies.

## Requirement 3: Correlation-matrix contract of `separability_matrix`

**User story:** As a downstream consumer, I want `separability_matrix` to keep
its established output contract, so that existing callers continue to work.

**Acceptance criteria**

1. The system SHALL return a boolean array (`dtype` bool) of shape
   `(transform.n_outputs, transform.n_inputs)`.
2. WHEN a transform has a single input but more than one output, THEN
   `separability_matrix` SHALL return an all-`True` matrix of shape
   `(n_outputs, 1)`.
3. The system SHALL map any nonzero internal correlation weight to `True` and
   any zero weight to `False` in the returned matrix.
4. The system SHALL leave the reported separability of non-nested compound
   models (parallel, series, and arithmetic combinations) unchanged from its
   previously correct behavior.

## Requirement 4: `is_separable` remains consistent

**User story:** As a user, I want `is_separable` to reflect the corrected
separability matrix, so that its per-output verdicts are accurate for nested
models too.

**Acceptance criteria**

1. WHEN `is_separable` is called on a transform, THEN the system SHALL return a
   boolean array of length `transform.n_outputs` where an element is `True`
   exactly when the corresponding output depends on a single input in the
   corrected correlation matrix.
2. WHEN a transform has a single input and more than one output, THEN
   `is_separable` SHALL report every output as non-separable (`False`).

## Requirement 5: Regression protection for supporting helpers and cases

**User story:** As a maintainer, I want the operator helpers and the existing
model catalogue of separability cases to keep their behavior, so that the fix
introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep producing, for a simple standalone model, a correlation
   matrix that places each output's dependence on the correct inputs (the
   single-model coordinate mapping used to seed the recursion).
2. The system SHALL keep computing the series ("pipe", `|`) combination as the
   composition of the two operands' correlation matrices, so that a dependence
   chain is propagated through the pipeline.
3. The system SHALL keep computing arithmetic combinations (`+`, `-`, `*`, `/`,
   `**`) as fully non-separable results of the shared shape, and SHALL continue
   to reject operands with mismatched input/output counts for these operators.
4. The system SHALL keep returning the previously correct matrices for
   parallel and series compositions that involve a `Mapping`, so that axis
   reordering and duplication are reflected accurately.
5. The system SHALL keep honoring a model's own custom separability declaration
   when one is provided, so that a user-defined model's stated input/output
   dependence is reflected in the computed matrix.
6. WHEN combining two already-computed correlation matrices with `&`, THEN the
   left block SHALL continue to be copied faithfully into the top-left region
   (the already-correct mirror of the fixed right-block behavior).
