# mapping.md — scikit-learn__scikit-learn-9288

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3eacf948e0f95ef957862568d87ce082f378e186`, states the type
abstraction (the bijection G-CONF and G-AX would use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo file under change: `sklearn/cluster/k_means_.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectBest (keys altKeys : List Key) (runFor : Key → Run)` | the single-thread best-of-`n_init` selection loop of `k_means(...)` — `sklearn/cluster/k_means_.py:178` (changed body lines 363–386) | the modeled changed function: run one attempt per key and report the best-scoring outcome |
| `keys : List Key` | `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` — the precomputed per-attempt seed array (post-patch, lifted to `k_means_.py:363`; pre-patch it lives only in the `else`/parallel branch at line 381) | the canonical per-attempt key sequence the loop must iterate |
| `altKeys : List Key` | the per-attempt seed sequence implicitly drawn by re-passing the live `random_state` object into `kmeans_single` once per iteration (pre-patch single-thread path, `random_state=random_state` at line 373) | a different key sequence in scope that must NOT drive the attempts |
| `runFor : Key → Run` *(free input — no axiom)* | `kmeans_single` ∈ {`_kmeans_single_lloyd` (`k_means_.py:420`), `_kmeans_single_elkan` (`k_means_.py:282`)} — one k-means run for a given seed, returning `(labels, inertia, centers, n_iter_)` | UNCHANGED attempt routine, carried abstractly (no behavioural claim) |
| `consider` / `bestOverKeys` | the `if best_inertia is None or inertia < best_inertia:` best-so-far block (`k_means_.py:374–378`), equivalently the `np.argmin(inertia)` selection in the parallel branch | pure spec: best-so-far argmin over attempt scores, earliest-wins on ties |
| `Run.score` | `inertia` (a float, the k-means objective; lower is better) | the minimised quantity |
| `Run.payload` | the reportable run content `(labels, centers, n_iter_)` | abstract attempt content |

The operation the patch changes is purely WHICH key sequence drives the
single-thread loop (`for it in range(n_init)` re-passing the live `random_state`
→ `for seed in seeds`); the attempt routine and the selection rule are unchanged.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| an `int32` seed value | `Key = Int` | seed `s` ↔ `(s : Int)`; the seed array `seeds` ↔ the `List Key` in attempt order; `n_init` ↔ `keys.length` |
| `inertia` (float objective, order is the behaviour) | `Run.score : Rat` | order-only comparison `inertia < best_inertia` ↔ `r.score < b.score` modeled with `Rat` (exact order), per CLAUDE.md "model order-only floats with `Rat`" |
| a single run result `(labels, inertia, centers, n_iter_)` | `Run` (`score`, `payload`) | only the score (for selection) and the fact that distinct runs are distinct outcomes are observed; `payload : Nat` is an opaque content identifier |
| `best_*` running incumbent (`None` until first run) | `Option Run` | `best_inertia is None` ↔ `none`; an established incumbent ↔ `some b` |
| `kmeans_single(X, ..., random_state=k)` | `runFor : Key → Run` | the unchanged attempt routine as a pure function of its seed (all other arguments fixed across the loop); carried as a free input — the spec holds for EVERY `runFor` |

`X`, `sample_weight`, `n_clusters`, `max_iter`, `init`, `tol`, etc. are loop
invariants (identical on every iteration), so they are absorbed into the fixed
`runFor` and play no role in the modeled distinction.

## 3. Callee provenance — no axioms, no deep-model references

There are **no `axiom`s** and **no A-reference deep models**, so **G-AX is
skipped** (no `axiom_check.py`).

- The attempt routine `kmeans_single` (`_kmeans_single_lloyd` /
  `_kmeans_single_elkan`) is UNCHANGED by the patch. It is carried as the free
  input `runFor : Key → Run` with NO behavioural claim — the spec `out =
  bestOverKeys runFor keys` holds for every function `runFor` could be — so there
  is nothing to validate against the real callee. (Contrast: a deep model would
  pin its values and require G-AX. We pin only that the report is the best over
  the runs keyed by the canonical sequence.)
- The selection rule (`consider` / `bestOverKeys`) and the seed-sequence identity
  are modeled DEEPLY in the `pure`/`impl` regions, not behind any contract.
- `random_state.randint(...)` (which produces the canonical `seeds`) is the data
  source for `keys`; its concrete values are irrelevant to the modeled
  distinction (the spec quantifies over `keys`), so it too is left abstract.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conf_skip = false`. The impl region is pure R/I (the selection loop: a fold of
`consider` over `keys`), so it IS differential-testable. `conformance_check.py`
seeds its `random.Random` with **`9288`** so the verdict is reproducible.

The R/I shadow transliterates `consider`/`bestOverKeys` to Python (none ↦ take;
some b ↦ take iff `r.score < b.score`, strict — first-wins on tie) and iterates
the CANONICAL key sequence `keys`. The oracle is the gold-patched single-thread
selection loop of `k_means`, transliterated VERBATIM with the fixed
`for seed in seeds` / `random_state=seed` and the real
`if best_inertia is None or inertia < best_inertia` control flow. Both sides are
driven by the SAME fuzzed seed list and the SAME deterministic run map `run_for`
(the unchanged `kmeans_single` as a free function of its seed — applied
identically on both sides, since it is a free input, not the changed op). The
fuzz draws seeds and inertias from small ranges so duplicate seeds and tied
inertias are common, heavily exercising the strict-`<` first-wins tie-break; the
score is an exact integer (the order-only `Rat`, §2) so the comparison is
unambiguous. They must agree on the selected run over ≥10⁵ inputs; exit 0 iff
zero disagreements. (Pattern precedent: django__django-12262, which
transliterates the gold-patched `parse_bits` loop as oracle rather than importing
it.) Falsifiability is confirmed: a `<=` tie-break or an argmax shadow each
disagree on thousands of the fuzzed inputs.

The free input `runFor` (the unchanged `kmeans_single`) is NOT substituted by any
axiom model here — it is applied as the identical run map on both shadow and
oracle, so G-CONF isolates the R/I selection-loop leg exactly. The whole-estimator
`n_jobs=1` vs `n_jobs>1` equality is the F2P test
`test_result_of_kmeans_equal_in_diff_n_jobs`'s job (G-RESOLVE), not this gate's.
