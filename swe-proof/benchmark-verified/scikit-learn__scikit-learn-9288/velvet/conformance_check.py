#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-9288 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the single modeled function
`selectBest` — the best-of-`n_init` selection loop of `sklearn.cluster.k_means`'s
single-thread branch. There are NO axioms in this bundle: the per-attempt run
routine `kmeans_single` (`_kmeans_single_lloyd` / `_kmeans_single_elkan`) is
UNCHANGED and folded into the free input `runFor : Key -> Run`. The impl region
is therefore pure R/I (conf_skip=false), and this gate differential-tests it.

  * SHADOW  — Solution.lean's `consider` / `bestOverKeys` model, transliterated
              to Python over the mapping.md bijection:
                Key            ↔  one int32 seed
                Run            ↔  (inertia, labels)   [score = inertia : Rat,
                                                       payload = labels]
                runFor         ↔  the seed -> run map (a free input, applied
                                  IDENTICALLY on both sides)
                bestOverKeys   ↔  foldl `consider` none keys
                consider       ↔  none -> take; some b -> take iff
                                  r.score < b.score (strict; first-wins on tie)
              The selection loop iterates the CANONICAL key sequence `keys`.

  * ORACLE  — `patch.diff`'s behaviour: the GOLD-PATCHED single-thread selection
              loop of `k_means`, transliterated VERBATIM with the real control
              flow and the fixed `for seed in seeds` / `random_state=seed`:

                  best_labels = best_inertia = None
                  seeds = ...                              # the canonical seeds
                  for seed in seeds:
                      labels, inertia = kmeans_single(..., random_state=seed)
                      if best_inertia is None or inertia < best_inertia:
                          best_labels, best_inertia = labels, inertia
                  return (best_labels, best_inertia)

Both sides are driven by the SAME fuzzed inputs: a seed list `keys` (the
`random_state.randint(..., size=n_init)` array) and a deterministic run map
`runFor` (the unchanged `kmeans_single` as a function of its seed). They must
agree on the selected run for every input. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample (e.g. wrong tie-break
direction, argmax vs argmin, or wrong iteration semantics).

The fuzz domain deliberately allows duplicate seeds and duplicate inertias so
the strict-`<` first-wins tie-break is exercised heavily (the case where a later
run ties the incumbent and must NOT replace it). Inertias are drawn as exact
integers (modeling the order-only `Rat` score, mapping.md §2) so the comparison
is unambiguous.

Runs in-container (the prebuilt SWE-Bench instance image); stdlib only — both
sides are transliterations, so no repo import or KMeans fit is needed (the live
estimator behaviour is the F2P test's job; precedent: django__django-12262,
which transliterates the gold-patched `parse_bits` loop rather than importing
it). The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 9288
N_FUZZ = 100_000


# --- the run map: the UNCHANGED kmeans_single as a function of its seed -------
# Deterministic seed -> (inertia, labels). Applied IDENTICALLY on both sides, so
# it is the free input `runFor`, not the changed op. Distinct seeds generally
# give distinct (inertia, labels); collisions are allowed (and wanted) so ties
# are exercised. `inertia` is an exact int (order-only Rat score).
def run_for(seed, inertia_range):
    r = random.Random("run:%d:%d" % (seed, inertia_range))
    inertia = r.randint(0, inertia_range)      # exact integer score (>= 0)
    labels = ("labels", seed, r.randint(0, 1_000_000))  # opaque run content
    return (inertia, labels)


# --- SHADOW: Solution.lean `bestOverKeys` / `consider`, transliterated --------
def consider(run_for_fn, acc, k):
    """consider runFor acc k  (Solution.lean pure region)."""
    r = run_for_fn(k)
    if acc is None:
        return r
    b = acc
    # `if r.score < b.score then some r else some b`  (strict; first-wins on tie)
    return r if r[0] < b[0] else b


def shadow_select(keys, run_for_fn):
    """bestOverKeys runFor keys = keys.foldl (consider runFor) none."""
    acc = None
    for k in keys:
        acc = consider(run_for_fn, acc, k)
    return acc


# --- ORACLE: the gold-patched single-thread selection loop, verbatim ----------
def oracle_select(keys, run_for_fn):
    """patch.diff behaviour: the gold-patched single-thread branch of k_means.

        seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)
        if effective_n_jobs(n_jobs) == 1:
            for seed in seeds:                       # <-- the fix
                labels, inertia, centers, n_iter_ = kmeans_single(
                    X, ..., random_state=seed)       # <-- the fix
                if best_inertia is None or inertia < best_inertia:
                    best_labels, best_centers, best_inertia, best_n_iter = ...
    """
    best_inertia = None
    best = None
    seeds = keys                                     # the canonical seed array
    for seed in seeds:
        labels, inertia = run_for_fn(seed)[1], run_for_fn(seed)[0]
        if best_inertia is None or inertia < best_inertia:
            best_inertia = inertia
            best = (inertia, labels)
    return best


def fuzz_inputs(n, rng):
    # boundary cases first
    yield []                              # n_init = 0  -> no run -> None
    yield [0]                             # single run
    yield [5, 5]                          # duplicate seeds -> tie, first wins
    yield [3, 1, 2]                       # min in the middle
    yield [2, 1, 1]                       # tie at the minimum, earliest wins
    yield [1, 2, 3, 4, 5]                 # min first
    yield [5, 4, 3, 2, 1]                 # min last
    for _ in range(n):
        # length 0..12 (n_init); seeds from a smallish range so duplicates and
        # tied inertias arise often, exercising the strict-< first-wins rule.
        length = rng.randint(0, 12)
        keys = [rng.randint(0, 20) for _ in range(length)]
        yield keys


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for keys in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # Pin the run map's inertia range per-input so ties are common but the
        # map is a pure function of the seed within this input.
        inertia_range = rng.randint(1, 8)
        run_fn = lambda s, _r=inertia_range: run_for(s, _r)
        shadow = shadow_select(keys, run_fn)
        oracle = oracle_select(keys, run_fn)
        if shadow != oracle:
            disagreements.append((keys, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for keys, sh, orc in disagreements:
            print("  keys=%r shadow=%r oracle=%r" % (keys, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectBest (bestOverKeys/consider) agrees "
          "with the gold-patched single-thread k_means selection loop on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
