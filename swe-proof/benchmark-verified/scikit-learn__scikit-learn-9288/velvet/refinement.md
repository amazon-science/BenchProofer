# refinement.md — scikit-learn__scikit-learn-9288

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `selectBest` `do` block, with the pure `consider`/`bestOverKeys` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/opaque callee — **A-consumed** where the proof uses a stated
contract, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE); it equals the gold patch
in `instance.json` byte-for-byte (verified).

## A. The best-of-`n_init` selection loop — `k_means` (`sklearn/cluster/k_means_.py:178`, body 363–386)

Gold patch (a code MOVE + a re-keying of the single-thread loop):

```
+    seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
     if effective_n_jobs(n_jobs) == 1:
-        for it in range(n_init):
+        for seed in seeds:
             labels, inertia, centers, n_iter_ = kmeans_single(
-                X, ..., random_state=random_state)
+                X, ..., random_state=seed)
             if best_inertia is None or inertia < best_inertia:
                 best_labels, best_centers, best_inertia, best_n_iter = ...
     else:
-        seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
         results = Parallel(...)(delayed(kmeans_single)(..., random_state=seed)
                                 for seed in seeds)
         ... best = np.argmin(inertia); best_* = *[best]
```

| # | Solution.lean impl op (`selectBest`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `keys : List Key`; loop bound `i < keys.length` | the precomputed `seeds = random_state.randint(..., size=n_init)`, iterated `for seed in seeds` | R | seed array ↔ `List Key`; `n_init` ↔ `keys.length` (mapping.md §2). This is the canonical per-attempt key sequence — the SAME one the parallel branch already used; the fix lifts it above the branch so the single-thread path uses it too. |
| A2 | param `altKeys : List Key` (read only, never iterated) | the seed sequence implicitly produced by re-passing the live `random_state` object once per iteration (`random_state=random_state`), which the patch REMOVES | R | the leftover/wrong key sequence ↔ `List Key` (mapping.md §2). Present in scope but must not drive the attempts. Read-only free input (directive 5: not `mut`, `ensures` makes no claim on it). |
| A3 | `let r := runFor k` for `k = keys[i]!` | `kmeans_single(X, ..., random_state=seed)` for `seed in seeds` | A-reference-free / I | the UNCHANGED attempt routine as a function of its seed (all other args fixed) ↔ free input `runFor : Key → Run`. Carried abstractly — no contract consumed (mapping.md §3); holds for EVERY `runFor`. The application at each canonical key is the concrete (I) op. |
| A4 | `best := match best with \| none => some r \| some b => if r.score < b.score then some r else some b` | `if best_inertia is None or inertia < best_inertia: best_* = ...` (single-thread), ≡ `np.argmin(inertia)` (parallel) | I | best-so-far argmin selection: replace incumbent iff none yet or strictly lower score; tie keeps the earlier — exactly `consider`. Transliterated directly. UNCHANGED by the patch. |
| A5 | `return best` (`Option Run`) | the selected `best_labels, best_centers, best_inertia, best_n_iter` | R | reported best outcome ↔ `Option Run` (`none` only if `n_init = 0`); `Run.score` ↔ `inertia`, `Run.payload` ↔ the run content (mapping.md §2). |

The discriminating content of the change — the single-thread loop must run over
the CANONICAL seed sequence (`keys`), not the leftover live-generator draw
(`altKeys`) — lives in WHICH list the `while` iterates. In `Solution.lean` the
loop iterates `keys`, so `out = bestOverKeys runFor keys`. In
`Solution_prepatch.lean` it iterates `altKeys`, so the proof obligation reduces
to `bestOverKeys runFor altKeys = bestOverKeys runFor keys`, which is
**unprovable** (G-DIFF: the prepatch fails on exactly the
`ensures out = bestOverKeys runFor keys` clause).

## B. No consumed axioms / no deep-model references

There are no `axiom`s and no A-reference deep models. The attempt routine
`kmeans_single` (`_kmeans_single_lloyd` / `_kmeans_single_elkan`) is UNCHANGED;
the patch only changes which seed sequence keys it. It is carried as the opaque
free input `runFor` with NO behavioural claim, so there is nothing for G-AX to
check (**G-AX = skip**, no `axiom_check.py`). The selection rule and the
seed-sequence identity are modeled directly in the `do` block / `pure` region.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the per-attempt
key sequence the single-thread loop runs over — is modeled **directly** by which
list the `while` iterates (`keys`, A1, vs `altKeys`, A2), not hidden behind an
axiom about the function under change. There is no consumed axiom about the
modeled loop.

## D. G-CONF status

`conf_skip = false`. The R/I ops A3–A5 form a fuzzable, interpreter-free
transliteration: the selection loop is a fold of `consider` over a key sequence,
with each attempt's outcome the free run map `runFor` applied to a key.
`conformance_check.py` differential-tests the SHADOW (`bestOverKeys`/`consider`
over the canonical `keys`, strict-`<` first-wins) against the ORACLE (the
gold-patched single-thread `k_means` selection loop transliterated verbatim,
`for seed in seeds` / `random_state=seed` + `if best_inertia is None or
inertia < best_inertia`), both driven by the SAME fuzzed seed lists and the SAME
deterministic run map, over ≥10⁵ inputs (seed `9288`). 0 disagreements. The fuzz
favours duplicate seeds and tied scores to exercise the tie-break; falsifiability
is confirmed (a `<=` tie-break or an argmax shadow each disagree on thousands of
inputs). `runFor` is a free input applied identically on both sides, so G-CONF
isolates the R/I selection leg; the whole-estimator `n_jobs` equality stays with
the F2P test (G-RESOLVE). (Transliteration precedent: django__django-12262.)

## E. verify(Solution) ⇒ resolved

`selectBest` verifies only if its output equals `bestOverKeys runFor keys` — the
best attempt over the runs keyed by the CANONICAL seed sequence (A1, A3–A5). By R
(`Key`/`Run`/`Option` bijections, mapping.md §2) the verified loop returns the
best k-means run over `random_state.randint(..., size=n_init)` — exactly what the
gold patch computes by lifting `seeds` above the branch and threading `seed` into
the single-thread loop. The bug the issue reports (`KMeans` gives a different
inertia for `n_jobs=1` than `n_jobs>1`) is exactly the case where the
single-thread loop ran over the wrong key sequence (`altKeys ≠ keys`): the
prepatch returns `bestOverKeys runFor altKeys` and fails verification, while the
patched code returns `bestOverKeys runFor keys`, which the parallel path (already
keyed on `seeds`) also returns — so the two `n_jobs` regimes agree (the F2P
`test_result_of_kmeans_equal_in_diff_n_jobs` passes). The gold patch resolves
(G-RESOLVE). Trust points: spec strength (G-VERIFY/G-DIFF) and refinement
fidelity (this doc, G-EQ).
