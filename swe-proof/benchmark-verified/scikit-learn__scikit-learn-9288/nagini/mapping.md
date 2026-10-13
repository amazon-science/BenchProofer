# mapping.md — scikit-learn__scikit-learn-9288

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3eacf948e0f95ef957862568d87ce082f378e186`, states the type
abstraction, and gives the provenance of each abstracted callee (source + the
exact behaviour the abstraction relies on, checked by axiom_check.py / G-AX).

Repo file under change: `sklearn/cluster/k_means_.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `restart_seeds(config, n_restarts)` | the per-restart seed handling in `k_means(...)` — `sklearn/cluster/k_means_.py:363-390` (changed hunks: the hoisted `seeds = random_state.randint(...)` and the single-worker loop `for seed in seeds` / `random_state=seed`) | the modeled changed function: the per-restart seeding the single-worker strategy uses. Returns the list of per-restart seeds. |
| `source_state(config)` *(abstract callee — A-reference)* | the internal state of the live `random_state` source at the point of the up-front draw, i.e. `check_random_state(random_state)` (`sklearn/utils/validation.py:765`, the int→`numpy.random.RandomState(seed)` branch invoked at `k_means_.py:294`) | the unchanged configuration→source step; its real state is `RandomState(config)`'s state at line 363 |
| `advance(state)` *(abstract callee — A-reference)* | the per-draw state transition of the live `RandomState` when `random_state.randint(np.iinfo(np.int32).max, size=n_init)` draws each of the `n_init` entries (`k_means_.py:381` post-patch / pre-patch in the `else` branch) | the unchanged per-draw state move; abstract, but validated as a genuine MOVE (position-dependent draws) by G-AX |
| `draw(state)` *(abstract callee — A-reference)* | the integer seed value a single `randint(np.iinfo(np.int32).max)` draw yields at the current source state (the entries of the `seeds` vector at `k_means_.py:381`) | the unchanged read of a draw's value; abstract, validated against real numpy by G-AX |
| `seed_vector(s, n)` *(deep model)* | the up-front seed vector `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` (`k_means_.py:381` post-patch, hoisted before the branch), consumed by BOTH strategies (`for seed in seeds` at `k_means_.py:366` post-patch and `for seed in seeds` at `k_means_.py:390`) | pure spec: the advancing up-front draw vector of per-restart seeds |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): in the single-worker branch the loop
was `for it in range(n_init)` and each `kmeans_single(...)` received
`random_state=random_state` (`k_means_.py:366,372`) — the one live source object
handed to every restart; and `seeds = random_state.randint(...)` was drawn only
inside the multi-worker (`else`) branch (`k_means_.py:381` pre-patch). The
post-patch hoists that draw before the branch and seeds the single-worker
restart i with `seeds[i]` (a fresh `RandomState(seeds[i])` inside
`kmeans_single`), the identical vector the multi-worker branch consumes.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the configured `random_state` (an `int` seed in the tested configuration; the F2P test passes `random_state=0`) | `config: int` | identity on the integer configuration seed |
| the restart count `n_init` (the per-restart loop length) | `n_restarts: int` | identity (a non-negative count) |
| a `numpy.random.RandomState` source | its integer internal state | a source is modelled by its state; `source_state(config)` is the state of `RandomState(config)` at the up-front draw; `advance` is the state after one `randint` draw; `draw` is the int the draw yields |
| the up-front draw vector `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` (`int32` values, consumed in lockstep by both branches) | `List[int]` of per-restart seeds; specification carried by `PSeq[int]` via `ToSeq` | element k ↔ the int seed `seeds[k]` used for restart k; `seed_vector` is the front-recursive advancing draw fold |
| `kmeans_single(X, ..., random_state=seed)` — a single restart of the clustering, deterministic given its seed and the fixed `X`/weights/init/etc. | abstracted away (orthogonal): each restart is a deterministic function of its seed | only the *seed* fed to restart k is modelled; the clustering body and the `argmin`-of-inertia kept-result selection are UNCHANGED |

The data matrix `X`, sample weights, `init`, `max_iter`, `tol`,
`precompute_distances`, `x_squared_norms`, the `effective_n_jobs`/`Parallel`
machinery, the `best_inertia`/`argmin` kept-result selection, and the
mean-centering / warning guards are all UNCHANGED by the patch and
observationally orthogonal to the single changed concern: whether the
single-worker strategy seeds restart i with the i-th entry of the one up-front
draw vector (fix) or hands the one live source to every restart (bug). The model
abstracts exactly the changed data-flow — the per-restart seed vector — and
elides the unchanged machinery, none of which the F2P test's discriminator
depends on. The F2P test
(`test_result_of_kmeans_equal_in_diff_n_jobs`) only observes that the kept
`labels_` agree between `n_jobs=1` and `n_jobs=2` for the same `random_state`,
which holds iff both strategies consume the same per-restart seed vector — the
property the model pins.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `source_state` / `advance` / `draw` ↔ the real pseudo-random source

**`source_state(config)`** abstracts the live `random_state` source obtained from
`check_random_state(config)` on the integer branch (`sklearn/utils/validation.py:765`):

```python
def check_random_state(seed):
    if seed is None or seed is np.random:
        return np.random.mtrand._rand
    if isinstance(seed, numbers.Integral):
        return np.random.RandomState(seed)   # <- the int branch (random_state=0)
    if isinstance(seed, np.random.RandomState):
        return seed
    raise ValueError(...)
```

`k_means` calls this once at the top (`k_means_.py:294`), so at line 363 the name
`random_state` is one `RandomState(config)` object. `source_state(config)` is
that one source's initial internal state at the point the up-front draw is taken.

**`advance(state)`** / **`draw(state)`** abstract the per-draw state transition
and value read of that one source under
`random_state.randint(np.iinfo(np.int32).max, size=n_init)` (`k_means_.py:381`):
the vector's entries are `n_init` successive draws of one advancing source, so
entry k is `draw(advance^k(state))`.

All three are modelled **abstractly** (no claimed `Ensures`): the proof needs
only that they are deterministic functions of their argument. The fact the
model's discriminator relies on — that the up-front draw vector is a genuine
ADVANCING sequence (its entries are position-dependent, so it is NOT one shared
source value repeated across restarts) — is NOT asserted as a contract; it is
validated against the REAL callees by axiom_check.py (G-AX). This keeps the
abstraction the *weakest* possible (it claims nothing the real callee might
violate) while the discriminating behaviour is checked empirically.

**Soundness check (G-AX).** `axiom_check.py` runs the real numpy `RandomState`
(the source `check_random_state` wraps) and the real, patched
`sklearn.cluster.KMeans`:

  - (A-reference 1) the up-front draw vector
    `np.random.RandomState(config).randint(np.iinfo(np.int32).max, size=n_init)`
    has position-dependent entries (the vector ADVANCES — its entries are not
    all identical) over many seeds — confirming `draw`/`advance` give a genuine
    advancing sequence, so the up-front vector is NOT one shared source value;
  - (A-reference 2) the fix runs restart i from a FRESH source seeded by the
    i-th up-front draw (`RandomState(seeds[i])`), whereas the pre-patch
    single-worker path hands the one live source (`RandomState(config)`) to
    every restart; the randomness a fresh `RandomState(seeds[0])` emits differs
    from the live `RandomState(config)`'s — i.e. the bug path the model forbids
    really diverges from the up-front vector the fix uses;
  - (end-to-end) the real, patched `KMeans` yields IDENTICAL `labels_` for
    `n_jobs=1` and `n_jobs=2` at the same `random_state` (the exact F2P
    observation), whereas reusing the live object across restarts would let the
    single-worker result diverge.

It imports only numpy (the real RNG the patch draws from) and the repository's
own sklearn (the very module the gold patch edits); nothing else. Exit 0 iff
every obligation holds.
