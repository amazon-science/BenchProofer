# RELAXED_LEAKAGE — scikit-learn__scikit-learn-9288 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). This bundle's own P2 audit
(`verdict.md`, carried from the source pipeline) reached exactly this
disposition — "the leak … is a genuine semantic leak of the gold *diagnosis*
— but it is provably unavoidable for any faithful spec … This matches the
RELAXED_LEAKAGE pattern. Fix: set `gates.G-LEAK.status="relaxed"`, add an
in-bundle `RELAXED_LEAKAGE.md`" — this file plus the meta flag IS that
prescribed correction.

## The mismatch

The gold fix to `k_means` (`sklearn/cluster/k_means_.py:178`, changed body
363–386 @ base 3eacf948) re-keys the single-thread best-of-`n_init` loop onto
the precomputed per-attempt seed array, lifting it above the `n_jobs` branch:

```python
+    seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
     if effective_n_jobs(n_jobs) == 1:
-        for it in range(n_init):
+        for seed in seeds:
             ... = kmeans_single(
-                X, ..., random_state=random_state)
+                X, ..., random_state=seed)
     else:
-        seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
         results = Parallel(...)(delayed(kmeans_single)(..., random_state=seed)
                                 for seed in seeds)
```

The F2P test (`test_result_of_kmeans_equal_in_diff_n_jobs`) asserts the
`n_jobs=1` and `n_jobs=2` fits give the same labels/inertia. The
discriminator is therefore: there are TWO per-attempt seed sequences in scope
(the precomputed array vs the sequence implicitly drawn by re-passing the
live `random_state` object each iteration), and the single-thread loop must
run over the precomputed/canonical one.

The leaking facet in this bundle's spec view (frozen contract of
`selectBest` in `Solution.lean`): the second parameter `altKeys` with the
docstring prose "`altKeys` is some other key sequence that happens to be in
scope; it must NOT drive the attempts" and "the best … attempt over the runs
determined by the CANONICAL key sequence — never over runs determined by
`altKeys`". A reader of the spec view alone is guided to the gold diagnosis
(the loop iterates the wrong of two seed sources) — this is the
dispositioned facet.

## Why the leak is unavoidable

The discriminating fact — that a second per-attempt seed sequence exists and
the buggy loop is keyed on it — is **absent from the solver-visible
`problem_statement`**:

- The `problem_statement` is a symptom-only report: `cluster.KMeans` gives a
  slightly different `inertia_` for `n_jobs=1` than for `n_jobs>1`, with a
  reproduction script and the expectation that the results be equal.
- Token scan of `problem_statement`: `seed` = 0, `n_init` = 0, `randint` = 0,
  `sequence` = 0, `random_state` appears only as the KMeans constructor
  argument in the reproduction script (never as the per-run seed source). It
  contains NO root cause and does not mention that the two `n_jobs` regimes
  draw their per-run seeds differently.
- The diagnosis — "the `n_jobs=1` case gets a different random seed for the
  `n_init` runs than the `n_jobs!=1` case … set `random_state` to be the same
  in both cases" — lives ONLY in `hints_text` (excluded from the leakage
  baseline) and in the gold patch itself.

A faithful function-level spec of the changed operation cannot avoid naming
this discriminator. The modeled change is PURELY which key sequence drives
the single-thread selection loop: the attempt routine (`kmeans_single`) and
the selection rule (`best_inertia is None or inertia < best_inertia`) are
byte-unchanged by the patch. G-DIFF requires `Solution_prepatch.lean` — whose
impl folds over the alternate sequence, the genuine pre-patch behavior — to
FAIL under the byte-identical frozen spec. A spec that never mentions a
second key sequence can only say "the output is the best-scoring attempt over
the runs performed", which the prepatch satisfies over ITS runs — it could
not reject the prepatch, so G-DIFF could not fire. Distinguishing the
canonical sequence from the alternate one in scope IS the two-sequence
discriminator; faithful + non-leaking is provably impossible here — the
definition of a `problem_statement ↔ gold` mismatch.

(The bundle already de-narrates everything else: neutral
"attempts"/"keys"/"score" vocabulary, no `k_means`/`seed`/`inertia`/`n_jobs`
tokens in the spec view — the mechanical G-LEAK screen passes lexically. Only
the semantic two-sequence facet remains, and only that facet is relaxed.)

## Core soundness is intact (fresh unified-pipeline gates, 2026-08-05)

- **G-VERIFY: pass** — `Solution.lean` verifies (total-correctness mode,
  loop carries `decreasing`); no sorry/axioms.
- **G-DIFF: pass** — `Solution_prepatch.lean` (folds over the alternate
  sequence) genuinely fails on the discriminating
  `ensures out = bestOverKeys runFor keys` clause; spec regions byte-identical
  (`same_spec = True`).
- **G-EQ: pass** — 11 attacks re-run, none breaks the spec; positive control
  verifies. **G-PANEL-1: pass** (no verifying same-spec wrong impl).
- **G-PANEL-2: pass (FAITHFUL)** — selection rule, iteration source,
  order-only `Rat` score, and free-input `runFor` all checked against the
  real repo; no diverging input found.
- **G-CONF: pass** — R/I shadow vs the verbatim gold-patched single-thread
  selection loop: 100,007 inputs (seed 9288), 0 disagreements;
  falsifiability confirmed.
- **G-MUT: 20/20 killed.** **G-AX: skip (vacuous)** — no axioms; the sole
  callee is unchanged and carried as the universally-quantified free input
  `runFor` with no behavioral claim. **G-GOLD / G-INTEGRITY / G-HYGIENE:
  pass.**

Only the secondary no-leakage property is relaxed, for this one documented
facet (the two-per-attempt-key-sequence discriminator).
