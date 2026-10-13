# Requirements: Make KMeans results independent of `n_jobs`

## Introduction

`sklearn.cluster.KMeans` (and the module-level `k_means` function in
`sklearn/cluster/k_means_.py`) fits a clustering by running the underlying
single-start k-means routine `n_init` times from different random
initializations and keeping the run with the lowest inertia. The number of these
restarts is controlled by `n_init`, the pseudo-random behavior by
`random_state`, and the degree of parallelism by `n_jobs`.

There is a defect: for the same `random_state`, `KMeans` produces a *different*
clustering depending on whether it runs single-threaded (`n_jobs == 1`) or in
parallel (`n_jobs > 1`). The cause is that the two code paths seed their
`n_init` restarts differently. The single-threaded branch feeds the shared
`random_state` object into every restart (so each restart advances and consumes
the same evolving generator), while the parallel branch first draws a fixed
array of integer seeds from `random_state` and gives one seed to each restart.
Because these two seeding schemes yield different initializations, the selected
best run — and hence `inertia_`, `labels_`, and `cluster_centers_` — can differ
between the serial and parallel cases.

The affected function is `k_means` in `sklearn/cluster/k_means_.py`, which is the
core used by `KMeans.fit`. The goal is to make the fitted result a pure function
of the inputs (data, `n_clusters`, `init`, `n_init`, `random_state`, `max_iter`,
`tol`, `algorithm`, `sample_weight`) and independent of `n_jobs`, while keeping
every other aspect of k-means behavior unchanged.

## Requirement 1: Identical clustering regardless of `n_jobs`

**User story:** As a data scientist, I want `KMeans` fit with a fixed
`random_state` to return the same model whether I run it on one job or many, so
that parallelism is a performance choice with no effect on results.

**Acceptance criteria**

1. WHEN `KMeans` (or `k_means`) is fit twice on the same input data with the same
   `n_clusters`, `init`, `n_init`, `max_iter`, `tol`, `algorithm`,
   `sample_weight`, and the same `random_state` seed, differing only in the value
   of `n_jobs`, THEN the two fits SHALL produce the same `labels_` for every
   sample.
2. WHEN two such fits differ only in `n_jobs`, THEN they SHALL produce the same
   `inertia_` and the same `cluster_centers_` (up to the routine's ordinary
   numerical determinism, i.e. bit-for-bit equal cluster assignments).
3. The fitted result of `KMeans`/`k_means` SHALL NOT depend on `n_jobs` in any
   observable way; `n_jobs` SHALL affect only how the work is distributed, not
   which candidate initializations are evaluated nor which one is selected.

## Requirement 2: Deterministic per-restart seeding derived from `random_state`

**User story:** As a maintainer, I want the `n_init` restarts to be seeded from
`random_state` in one canonical way that does not depend on the execution path,
so that the serial and parallel branches evaluate exactly the same set of
initializations.

**Acceptance criteria**

1. WHEN `k_means` prepares to perform its `n_init` restarts, THEN it SHALL derive
   a sequence of `n_init` per-restart random seeds from `random_state` a single
   time, before any branch on `n_jobs`, so that the same seed sequence is used
   whether the restarts run single-threaded or in parallel.
2. WHEN the restarts run single-threaded, THEN the i-th restart SHALL be
   initialized from the i-th seed of that sequence, exactly as the i-th restart
   in the parallel case is; the serial path SHALL NOT instead thread the shared
   `random_state` generator through successive restarts.
3. WHEN `random_state` is given as the same fixed integer seed, THEN the derived
   per-restart seed sequence SHALL be reproducible across runs, so repeated fits
   with the same inputs yield the same model.
4. The number of candidate runs evaluated SHALL equal the effective `n_init`
   regardless of `n_jobs`, and each candidate run SHALL correspond to one derived
   seed.

## Requirement 3: Preserve existing k-means behavior (regression protection)

**User story:** As a maintainer, I want clustering correctness and every other
option to behave exactly as before, so that fixing the `n_jobs` discrepancy does
not change any other result.

**Acceptance criteria**

1. WHEN multiple restarts are performed, THEN `k_means` SHALL select and return
   the restart with the lowest inertia as the fitted model (its `labels_`,
   `cluster_centers_`, `inertia_`, and iteration count), exactly as before.
2. The fitted clustering SHALL remain correct for both the `"full"` (Lloyd) and
   `"elkan"` algorithms, for dense and sparse (CSR) inputs, and for `float32` and
   `float64` data, producing the same partitions those configurations produced
   previously.
3. WHEN an explicit array of initial centers is passed as `init`, THEN `k_means`
   SHALL perform only a single initialization run (treat `n_init` as 1) as
   before, and the `n_jobs`-independence of the result SHALL still hold.
4. WHEN `n_jobs > 1` is requested, THEN the parallel execution path SHALL still
   run the `n_init` restarts and combine them by choosing the minimum-inertia
   result, producing the same fitted model it did before this change.
5. The behavior governed by `n_clusters`, `max_iter`, `tol`, `sample_weight`,
   `precompute_distances`, and input validation (including the error when
   `n_samples < n_clusters` and the warning when fewer distinct clusters than
   `n_clusters` are found) SHALL be unchanged.
6. WHEN two fits share the same fixed `random_state` seed and differ only in
   `n_jobs`, THEN the `n_jobs`-independence guarantee of Requirement 1 SHALL
   hold; the system SHALL otherwise leave unseeded (default `random_state`)
   behavior unchanged, so fits that do not fix `random_state` remain free to
   differ as before.
