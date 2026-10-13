# Requirements: KBinsDiscretizer kmeans strategy must produce monotonic bin edges

## Introduction

`KBinsDiscretizer` (`sklearn/preprocessing/_discretization.py`) bins continuous
features into discrete intervals. During `fit`, for each feature column it
computes an array of bin edges according to the chosen `strategy`
(`'uniform'`, `'quantile'`, or `'kmeans'`) and stores them in `bin_edges_`.
`transform` then assigns each value to a bin with `np.digitize` against those
edges.

For `strategy='kmeans'`, the interior bin edges are derived as the consecutive
midpoints of the 1-D cluster centers returned by the clustering routine
(`KMeans`), bracketed by the column minimum and maximum. `np.digitize` requires
its bin boundaries to be monotonically increasing. However, the cluster centers
are not guaranteed to come back in ascending order — even when the clustering is
seeded with an ascending initialization — so the derived edges can be
non-monotonic. When that happens (which becomes likely as the requested number
of bins approaches the number of distinct data points), `transform` raises
`ValueError: bins must be monotonically increasing or decreasing` and
`fit_transform` fails.

The goal is to make the `kmeans` branch of `KBinsDiscretizer.fit` produce bin
edges that are always non-decreasing, so discretization succeeds for any valid
number of bins, while leaving the `uniform` and `quantile` strategies and all
other existing behavior of `KBinsDiscretizer` unchanged.

## Requirement 1: kmeans bin edges are always monotonically non-decreasing

**User story:** As a user discretizing data with the kmeans strategy, I want
`fit`/`fit_transform` to succeed for any valid number of bins, so that a larger
bin count relative to the data does not raise an error.

**Acceptance criteria**
1. WHEN `KBinsDiscretizer.fit` is called with `strategy='kmeans'` on a
   non-constant feature column, THEN the stored `bin_edges_` for that column
   SHALL be sorted in non-decreasing order.
2. The system SHALL derive the interior bin edges for a kmeans feature as the
   midpoints of consecutive cluster centers after those centers have been
   ordered ascending, bracketed by the column minimum as the first edge and the
   column maximum as the last edge.
3. WHEN `KBinsDiscretizer` is fit and transformed with `strategy='kmeans'` and
   `encode='ordinal'` on data whose cluster centers would otherwise be returned
   out of order, THEN `fit_transform` SHALL complete without raising
   `ValueError` (and specifically without "bins must be monotonically
   increasing or decreasing").
4. The system SHALL leave the computed cluster centers themselves used only for
   deriving edges; reordering the centers to produce edges SHALL NOT change the
   requirement that each interior edge lies between the column min and max.

## Requirement 2: Correct ordinal assignment under the kmeans strategy

**User story:** As a user, I want values binned into the interval whose center
is nearest, so that the discretized output is a correct, contiguous set of
ordinal codes.

**Acceptance criteria**
1. WHEN a fitted kmeans `KBinsDiscretizer` with `encode='ordinal'` transforms
   data, THEN each value SHALL be assigned an integer bin index in the range
   `[0, n_bins_ - 1]` for that feature.
2. WHEN values that are monotonically increasing across the observed range are
   transformed, THEN their assigned ordinal codes SHALL be monotonically
   non-decreasing (a value SHALL never receive a lower bin index than a strictly
   smaller value).
3. IF a transformed value lies at or beyond the extremes of the fitted range,
   THEN its bin index SHALL be clipped into `[0, n_bins_ - 1]` rather than
   falling outside that range.

## Requirement 3: Preserve uniform and quantile strategy behavior

**User story:** As an existing user of the uniform and quantile strategies, I
want their edges and outputs unchanged, so that this fix does not regress them.

**Acceptance criteria**
1. The system SHALL, for `strategy='uniform'`, place bin edges at equally spaced
   points spanning the column minimum to maximum.
2. The system SHALL, for `strategy='quantile'`, place bin edges at the
   equally-spaced percentiles of the column.
3. WHEN `fit_transform` is applied with `strategy` set to `'uniform'` or
   `'quantile'` and `encode='ordinal'`, THEN the resulting ordinal codes SHALL
   be identical to those produced before this change.

## Requirement 4: Preserve constant-feature and degenerate-column handling

**User story:** As a user, I want constant columns handled gracefully, so that
edge cases do not error.

**Acceptance criteria**
1. WHEN a feature column has an equal minimum and maximum (constant column),
   THEN `KBinsDiscretizer.fit` SHALL treat that feature as a single bin, warn
   that the feature is constant, and assign bin index 0 to all its values on
   transform — regardless of the selected strategy.

## Requirement 5: Preserve encoding, inverse-transform, and validation behavior

**User story:** As a maintainer, I want the surrounding API contract of
`KBinsDiscretizer` intact, so that only the kmeans monotonicity defect changes.

**Acceptance criteria**
1. The system SHALL continue to support `encode` values `'ordinal'`,
   `'onehot'`, and `'onehot-dense'`, producing ordinal codes, sparse one-hot,
   and dense one-hot output respectively, and SHALL raise a `ValueError` for any
   other `encode` value.
2. The system SHALL raise a `ValueError` when `strategy` is not one of
   `'uniform'`, `'quantile'`, or `'kmeans'`.
3. The system SHALL validate `n_bins`, raising a `ValueError` when it is not an
   integer (or integer array of shape `(n_features,)`) of value at least 2, and
   accepting a per-feature array of bin counts otherwise.
4. WHEN `inverse_transform` is applied to discretized output, THEN each code
   SHALL be mapped back to the center of its bin, for every combination of
   `encode` and `strategy`.
5. IF `transform` receives data whose number of features differs from the number
   seen at fit time, THEN it SHALL raise a `ValueError`.
6. The system SHALL preserve its numeric-stability handling so that values lying
   extremely close to a bin edge are binned consistently with their decimal
   truncation.
