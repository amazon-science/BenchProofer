# Requirements: OPTICS float `min_samples` / `min_cluster_size` must yield integer neighborhood sizes

## Introduction

`OPTICS` clustering in `sklearn/cluster/optics_.py` accepts its neighborhood
sizing parameters either as an absolute count (an integer greater than one) or
as a fraction of the dataset size (a float in the interval between 0 and 1). The
two module-level routines that consume these parameters —
`compute_optics_graph(X, min_samples, ...)` and
`cluster_optics_xi(reachability, predecessor, ordering, min_samples,
min_cluster_size, ...)` — first validate the parameter and then, when it was
supplied as a fraction, rescale it into an absolute count by multiplying it by
the number of samples and clamping it to be at least 2.

The defect: the rescaling produced a fractional (floating-point) value rather
than a whole number. `compute_optics_graph` passes the resulting `min_samples`
straight into `NearestNeighbors(n_neighbors=...)`, whose neighbor count must be
an integer; a fractional value raises a `TypeError` ("`n_neighbors` does not
take ... value, enter integer value"). Consequently, calling `OPTICS.fit` with a
float `min_samples` (e.g. `0.1`) crashed instead of clustering, and passing a
float `min_cluster_size` to the `'xi'` cluster method was likewise unsupported.

The goal is that a fractional sizing parameter is converted to a whole-number
absolute count, so that fitting `OPTICS` (and running the `'xi'` extraction) with
fractional sizing parameters succeeds and yields the same clustering as the
equivalent integer sizing parameters. This behavior is localized to the
fraction-to-count conversion in `compute_optics_graph` and `cluster_optics_xi`;
the existing validation in `_validate_size` and the default value of
`OPTICS.min_samples` (`5`) are also relevant.

## Requirement 1: Fractional `min_samples` becomes an integer neighbor count in `compute_optics_graph`

**User story:** As a user clustering data with `OPTICS`, I want to specify
`min_samples` as a fraction of the dataset size, so that the neighborhood size
scales with my data without my having to compute an integer myself.

**Acceptance criteria**
1. WHEN `compute_optics_graph` is called with a `min_samples` value less than or
   equal to 1 (a fraction), THEN it SHALL convert `min_samples` to a whole
   number equal to the larger of 2 and the integer part (truncated toward zero)
   of `min_samples` multiplied by the number of samples, before it is used as a
   neighbor count.
2. WHEN `compute_optics_graph` is called with a fractional `min_samples`, THEN
   the value passed to the nearest-neighbors search as the number of neighbors
   SHALL be an integer, so that no `TypeError` about a non-integer neighbor
   count is raised.
3. WHEN `OPTICS` is fitted (`fit`) on a dataset with `min_samples` given as a
   float between 0 and 1, THEN the fit SHALL complete without raising, producing
   the clustering attributes rather than an error.
4. The system SHALL keep accepting an integer `min_samples` greater than 1 and
   use it directly as the neighbor count without rescaling.

## Requirement 2: Fractional `min_samples` and `min_cluster_size` become integers in `cluster_optics_xi`

**User story:** As a user of the `'xi'` cluster extraction, I want both
`min_samples` and `min_cluster_size` to accept fractions of the dataset size, so
that the steep-region and cluster-size thresholds scale with my data.

**Acceptance criteria**
1. WHEN `cluster_optics_xi` is called with a `min_samples` value less than or
   equal to 1, THEN it SHALL convert `min_samples` to the larger of 2 and the
   integer part (truncated toward zero) of `min_samples` multiplied by the
   number of samples.
2. WHEN `cluster_optics_xi` is called with a `min_cluster_size` value less than
   or equal to 1, THEN it SHALL convert `min_cluster_size` to the larger of 2
   and the integer part (truncated toward zero) of `min_cluster_size` multiplied
   by the number of samples.
3. IF `min_cluster_size` is not supplied (is `None`), THEN it SHALL default to
   the already-conditioned `min_samples` value before any fraction conversion is
   applied to it.
4. The resulting `min_samples` and `min_cluster_size` values used by the
   downstream `'xi'` extraction SHALL be whole numbers, never fractional values.

## Requirement 3: Fractional sizing produces the same clustering as the equivalent integer sizing

**User story:** As a user, I want fractional sizing parameters to be exactly
equivalent to the integer counts they resolve to, so that my results are
predictable and match the absolute-count form.

**Acceptance criteria**
1. WHEN `OPTICS` is fitted with `cluster_method='xi'` using fractional
   `min_samples` and `min_cluster_size` that resolve (per Requirements 1 and 2)
   to particular whole numbers, THEN the resulting cluster labels SHALL be
   identical to those obtained by fitting with those whole-number values
   directly.
2. The system SHALL clamp each converted count to be at least 2, so that a
   fraction small enough to scale below 2 still yields a neighborhood/cluster
   size of 2.

## Requirement 4: Preserve existing validation and default behavior

**User story:** As a maintainer, I want the input validation and default
parameter behavior to remain unchanged, so that the float-conversion fix does
not weaken the guardrails or alter the default clustering.

**Acceptance criteria**
1. The system SHALL continue to reject a sizing parameter that is not a positive
   value, and reject a value greater than 1 that is not a whole number, raising a
   `ValueError` describing the parameter as needing to be a positive integer or a
   float between 0 and 1.
2. IF a sizing parameter exceeds the number of samples, THEN the system SHALL
   raise a `ValueError` reporting that it must be no greater than the number of
   samples.
3. The system SHALL keep the default value of `OPTICS`'s `min_samples` parameter
   at 5.
4. WHEN `OPTICS` is fitted with integer sizing parameters, THEN the resulting
   cluster labels SHALL be unchanged from the previous behavior (the float
   conversion SHALL affect only the fractional-input path).
