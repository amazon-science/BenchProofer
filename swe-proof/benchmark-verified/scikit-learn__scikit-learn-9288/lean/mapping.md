# mapping.md — scikit-learn__scikit-learn-9288

## Symbol binding (file:line @ base_commit 3eacf948e0)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_bestTrial` / `problem_spec_bestTrial` / `correct_bestTrial` | the single-thread best-of-`n_init`-runs loop inside `k_means` (the `effective_n_jobs(n_jobs) == 1` branch) | `sklearn/cluster/k_means_.py:362-379` @ base_commit |
| `runTrial : Int → Outcome` | `kmeans_single(X, sample_weight, n_clusters, …, random_state=<seed>)` — one clustering run, deterministic given its integer seed | `sklearn/cluster/k_means_.py:367-372` (`kmeans_single` is `_kmeans_single_lloyd` / `_kmeans_single_elkan`, UNCHANGED) |
| `trials : List Int` | `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` — the precomputed per-run seed array | gold patch, `k_means_.py:363` (post-patch, hoisted above the `n_jobs` branch) |
| `Outcome.cost` | `inertia` (a `float`) returned by `kmeans_single` | `k_means_.py:367` |
| `Outcome.assignment` | `labels` (the cluster assignment `labels_`) returned by `kmeans_single` | `k_means_.py:367` |

## What the modeled function computes

The single-thread branch of `k_means` runs `kmeans_single` once per init and keeps
the best (lowest-inertia) run:

```python
seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)   # POST-PATCH: hoisted up
if effective_n_jobs(n_jobs) == 1:
    for seed in seeds:                                              # POST-PATCH (was: for it in range(n_init))
        labels, inertia, centers, n_iter_ = kmeans_single(
            X, sample_weight, n_clusters, …, random_state=seed)     # POST-PATCH (was: random_state=random_state)
        if best_inertia is None or inertia < best_inertia:          # keep first strict-minimum
            best_labels, best_centers, best_inertia, best_n_iter = labels, centers, inertia, n_iter_
```

The PRE-PATCH serial loop iterated `for it in range(n_init)` and passed the shared
mutable `random_state` object to every `kmeans_single` call. The randomness each
run consumed there is therefore NOT the `seeds` array that the parallel
(`n_jobs>1`) branch uses — so the two branches selected over different seed sets
and returned slightly different models (the reported bug). The fix makes the
serial branch run over exactly `seeds`, identical to the parallel branch, so the
result is independent of `n_jobs`.

`random_state.randint(...)` itself is unchanged in value (same RNG, same call);
the patch only MOVES it above the branch. So `seeds` is an INPUT (`trials`) to the
modeled function — we do not model the RNG.

## Selection semantics

`best_inertia is None or inertia < best_inertia` uses a STRICT `<`, so among equal
minima the FIRST run is kept. `np.argmin` (parallel branch) also returns the first
occurrence of the minimum. Both tie-breaks agree → the modeled `problem_spec`
pins "first index achieving the global minimum cost".

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `seeds` (1-D int32 ndarray, length `n_init`) | `trials : List Int` | element-wise; `trials.length = n_init` |
| one `kmeans_single(..., random_state=seed)` output tuple | `runTrial seed : Outcome` | deterministic function of the seed; `inertia ↦ Outcome.cost`, `labels ↦ Outcome.assignment` |
| `inertia : float` | `Outcome.cost : Int` | ORDER-ONLY (only `<` / `argmin` observed); float order ↦ Int order (DECISIONS.md: kernel `Float` order opaque). G-CONF fuzzes the order relation |
| `labels : int ndarray` | `Outcome.assignment : List Int` | element-wise cluster ids |
| returned `(best_labels, best_inertia, …)` | `result : Outcome` | result is exactly the chosen run's full output tuple (frame: all components come from one `runTrial`) |

## Callee provenance + flag dependencies

- `runTrial` (`kmeans_single`) is an UNCHANGED callee, invoked identically
  (only its `random_state=` argument source changed from the shared object to
  `seed`). It is declared `opaque runTrial : Int → Outcome` so the executable impl
  can call it. The proof consumes NO property of it (the argmin selection holds for
  any function), so there is NO `runTrial_prop` axiom — G-AX is a skip stub.
- The selection loop (track best, strict-`<` update) is modeled DEEPLY and is the
  R/I leg differential-tested by G-CONF.
- Branch dependency: this models the `effective_n_jobs(n_jobs) == 1` branch
  (the one the patch edits). The parallel branch already used `seeds`; the fix
  makes the serial branch match it.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
