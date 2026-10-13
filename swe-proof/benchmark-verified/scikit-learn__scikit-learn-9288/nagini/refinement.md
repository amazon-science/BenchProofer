# refinement.md — scikit-learn__scikit-learn-9288

The operation-by-operation correspondence between `model.py`'s implementation
(the `restart_seeds` impl region and the deep `seed_vector` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (abstracted callee — **A-consumed** where the proof uses the callee's
`Ensures`, **A-reference** where a deep model / abstract symbol is validated
against the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `k_means` (`sklearn/cluster/k_means_.py:360-390`)

Gold hunks:
```
+
+    seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
     if effective_n_jobs(n_jobs) == 1:
         ...
-        for it in range(n_init):
+        for seed in seeds:
             labels, inertia, centers, n_iter_ = kmeans_single(
                 ... tol=tol, x_squared_norms=x_squared_norms,
-                random_state=random_state)
+                random_state=seed)
             ...
     else:
         # parallelisation of k-means runs
-        seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
         results = Parallel(...)(
             delayed(kmeans_single)(..., random_state=seed)
             for seed in seeds)
```

The fix hoists the up-front draw of the per-restart seed vector
`seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` OUT of the
multi-worker (`else`) branch to BEFORE the strategy split, and makes the
single-worker (`n_jobs==1`) branch consume that same vector
(`for seed in seeds: kmeans_single(..., random_state=seed)`) instead of passing
the live `random_state` object to every restart. Both branches now seed restart
i with `seeds[i]` — the i-th up-front draw — so the kept (`argmin`-of-inertia)
restart is strategy-independent. model.py captures exactly that data-flow in
`restart_seeds`: the single-worker per-restart seed list it returns is the same
up-front draw vector `seed_vector(source_state(config), n_restarts)` the
multi-worker strategy consumes.

| # | model.py impl op (`restart_seeds`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `config: int` | `random_state` (an `int`/seed configuration in the tested call) | R | identity on the integer configuration seed (mapping.md §2); the F2P test passes `random_state=0`. |
| A2 | parameter `n_restarts: int` | `n_init` (the restart count, loop length) | R | identity on a non-negative count (mapping.md §2). |
| A3 | `start = source_state(config)` (the source's initial state, obtained **once**) | the live `random_state` source from which `seeds = random_state.randint(...)` draws | A-reference | the configured seed yields one source; `source_state(config)` is its initial state. Abstract symbol validated against the real callee by G-AX (mapping.md §3.1). |
| A4 | the loop threads one `cur`, emitting `draw(cur)` per restart then `cur = advance(cur)` — `Result()[k]` is the draw at the k-fold advance of `start` | `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` drawn **once** up front, then `for seed in seeds: kmeans_single(..., random_state=seed)` in BOTH branches | A-reference | `randint(max, size=n_init)` is exactly the vector of `n_init` independent draws of one advancing source; `draw`/`advance` abstract a draw's value and the per-draw state move. The deep model `seed_vector` IS that up-front draw vector; G-AX validates that the real `randint(max, size=n_init)` advances (its entries are position-dependent draws, A-reference 1, §3.1) and that hoisting it makes the single-worker branch consume the same vector as the multi-worker branch. |
| A5 | `Result()` returned (a `List[int]` of per-restart seeds) | the per-restart `random_state=seed` argument fed to each `kmeans_single`, whose `argmin`-of-inertia is kept | R | element k ↔ restart k's seed; `kmeans_single` is a deterministic function of its seed (fixed X, weights, init, etc.) and the `best_inertia`/`argmin` selection is unchanged and orthogonal (mapping.md §2). Both strategies feeding the SAME seed vector to the same deterministic restart ⇒ identical kept result. |

The discriminating content of the change — the single-worker strategy consumes
the SAME up-front draw vector as the multi-worker strategy, rather than passing
one shared live source to every restart — lives in
`Ensures(ToSeq(Result()) == seed_vector(source_state(config), n_restarts))`
(model) ⇔ hoisting `seeds = random_state.randint(...)` before the branch and
looping `for seed in seeds` in the single-worker branch (real). The pre-patch
single-worker branch passes `random_state=random_state` (the one live object)
to every restart; `model_prepatch.py` reproduces that (every restart emits the
one shared `draw(start)`) and **fails** the postcondition above — exactly the
spec sensing the change (G-DIFF), because a constant list `[shared, shared, …]`
cannot be proven equal to the advancing up-front vector
`[draw(start), draw(advance(start)), …]` for the abstract `draw`/`advance`.

## B. No consumed axioms; no kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. There is **no A-consumed axiom**: the
proof consumes no callee `Ensures`. `source_state`, `advance`, and `draw` are
abstract pure symbols with no claimed contract; the postcondition and the
front-recursive `seed_vector` are phrased purely structurally over them, and the
proof goes through by definitional unfolding of `seed_vector` (no value claim
about `source_state`/`advance`/`draw` is needed). The single changed operation —
whether the single-worker branch consumes the up-front draw vector (fix) or
reuses one shared live source (bug) — is modelled **deeply** (`seed_vector`
spelled out as the advancing draw fold, threaded by the impl loop), not hidden
behind an axiom about the function under change. The abstract symbols are the
**A-reference**: their real counterparts (numpy `RandomState` seeded by the
configuration, drawn via `randint(max, size=n_init)`) are validated by G-AX,
including the discriminating fact that the up-front draw vector is a genuine
advancing sequence (its entries depend on position) and equals what both
branches consume.

## C. verify(model) ⇒ resolved

`restart_seeds` verifies only if its output is the up-front draw vector
`seed_vector(source_state(config), n_restarts)` (A3+A4): restart k is seeded from
the k-th up-front draw, the identical vector the multi-worker strategy consumes —
never one shared source repeated across restarts. By R (int config identity;
restart-count identity; per-restart-seed ↔ element correspondence; deterministic
`kmeans_single` + unchanged `argmin` selection) the verified function equals the
patched `k_means`'s per-restart seeding on the tested inputs, so the two
execution strategies keep the same restart; by G-AX the abstract
`draw`/`advance`/`source_state` correspond to a real `randint(max, size=n_init)`
draw vector that is position-dependent and shared verbatim by both branches.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
