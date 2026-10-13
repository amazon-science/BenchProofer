# Requirements: Bounded leading threshold in `roc_curve`

## Introduction

The receiver-operating-characteristic routine `roc_curve` in
`sklearn/metrics/_ranking.py` computes, from the target scores, a vector of
decreasing false-positive rates (`fpr`), true-positive rates (`tpr`), and the
`thresholds` at which they are measured. To guarantee that the plotted curve
starts at the origin `(0, 0)`, the routine prepends one extra operating point —
the point at which *no* instance is predicted positive — to each of the three
returned vectors.

Historically the extra leading threshold was computed as `max(y_score) + 1`.
When the scores are probability estimates (values in `[0, 1]`), this produced a
leading threshold greater than `1`, which is not a meaningful probability and is
surprising to callers who interpret thresholds as probabilities. The goal is to
make the leading threshold a value that is unambiguously "above every possible
score" regardless of the scale of `y_score`, while leaving every other returned
value unchanged.

The affected function is `roc_curve` (module `sklearn.metrics._ranking`); the
downstream `fpr`/`tpr` computation and the `drop_intermediate` thinning logic
in the same function are the surrounding behavior that must be preserved.

## Requirement 1: Leading threshold is the positive-infinity sentinel

**User story:** As a user of `roc_curve` who feeds in probability estimates, I
want the arbitrary leading threshold to be a value that always sits above any
score rather than a value that can exceed 1, so that a returned threshold never
looks like an out-of-range probability.

**Acceptance criteria**
1. WHEN `roc_curve` returns its `thresholds` array, THEN `roc_curve` SHALL set
   the first element of `thresholds` to positive infinity (`np.inf`).
2. WHEN `roc_curve` is called with target scores that are probability estimates
   (all values in the interval `[0, 1]`), THEN the first element of the returned
   `thresholds` SHALL be infinite rather than a finite value greater than `1`.
3. The system SHALL NOT compute the leading threshold as `max(y_score) + 1` or
   as any other value derived by offsetting the largest score.
4. WHEN the first element of `thresholds` is the positive-infinity sentinel,
   THEN this leading value SHALL still be strictly greater than every other
   (finite) threshold, so the returned `thresholds` array remains sorted in
   strictly decreasing order.

## Requirement 2: Remaining thresholds, `fpr`, and `tpr` are unchanged

**User story:** As a maintainer, I want the fix to change only the arbitrary
leading operating point, so that all other outputs of `roc_curve` are exactly
what they were before.

**Acceptance criteria**
1. The system SHALL leave every element of `thresholds` other than the first
   (i.e. `thresholds[1:]`) equal to the decreasing finite score thresholds
   computed from `y_score`, in the same order and with the same values as before.
2. The system SHALL keep the returned `fpr` and `tpr` arrays identical to their
   previous values, including the leading `fpr = 0` and `tpr = 0` entry that
   makes the curve start at `(0, 0)`.
3. WHEN `drop_intermediate=True` (the default), THEN `roc_curve` SHALL still drop
   the same suboptimal/collinear intermediate thresholds as before, and the
   surviving finite thresholds SHALL appear after the leading infinite value.
4. WHEN `drop_intermediate=False`, THEN `roc_curve` SHALL retain all finite
   thresholds after the leading infinite value.
5. The system SHALL keep the returned `fpr`, `tpr`, and `thresholds` arrays the
   same length as one another, each one longer than the number of distinct
   finite thresholds by exactly the single prepended leading position.

## Requirement 3: Preserved edge-case and warning behavior

**User story:** As a user relying on `roc_curve` for degenerate inputs, I want
the existing warnings and NaN handling to be unaffected by this change.

**Acceptance criteria**
1. IF `y_true` contains no negative samples, THEN `roc_curve` SHALL still emit
   the existing "No negative samples" undefined-metric warning and return `fpr`
   filled with NaN, exactly as before.
2. IF `y_true` contains no positive samples, THEN `roc_curve` SHALL still emit
   the existing "No positive samples" undefined-metric warning and return `tpr`
   filled with NaN, exactly as before.
3. The system SHALL continue to accept the same `pos_label`, `sample_weight`,
   and `drop_intermediate` arguments and raise the same errors for multiclass or
   otherwise invalid input as before.

## Requirement 4: Documentation reflects the leading value

**User story:** As a reader of the API documentation, I want the description and
worked example for `thresholds` to match the actual returned value.

**Acceptance criteria**
1. The system SHALL describe the leading `thresholds[0]` entry in the `roc_curve`
   documentation as the "no instances predicted" operating point set to positive
   infinity, rather than to `max(y_score) + 1`.
2. WHEN the documented worked example is evaluated, THEN the first element of the
   example's `thresholds` output SHALL be shown as infinite rather than as a
   finite value above the maximum score.
