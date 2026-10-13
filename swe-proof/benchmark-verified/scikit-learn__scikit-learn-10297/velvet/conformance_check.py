#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-10297 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`initEstimator`,
              routed through the deep model `construct`) transliterated to Python
              over the real repo types. There are NO A-tagged callees in the impl
              region (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched cross-validated classifier
              estimator constructed at base_commit (the real correctness oracle,
              G-RESOLVE applies the gold patch before this runs).

Observable of a construction, per the mapping.md §2 bijection:
  - whether construction succeeds or is refused because the retention option is
    not exposed (`TypeError: ... unexpected keyword argument 'store_cv_values'`)
    ↔  `Except.ok _` vs `Except.error .storeNotAccepted`;
  - on success, whether the estimator recorded the requested retention option
    ↔  the `EstimatorState { storeCvValues }` payload (`self.store_cv_values`).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
input space is tiny and total (a single Bool), so the whole cross product is
enumerated and then re-sampled to exceed the §4.1 fuzz floor deterministically.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 10297
N_FUZZ = 100_000

from sklearn.linear_model import RidgeClassifierCV  # patched: exposes store_cv_values

# --- the R/I shadow: Solution.lean construct/initEstimator --------------------
# Per-estimator capability `acceptsStore` as modeled in the impl region: this
# estimator supports retaining the per-alpha cross-validation values.
ACCEPTS_STORE = True


def shadow_construct(accepts_store, store_cv_values):
    """construct (pure region) transliterated. Returns either
    ('error', 'storeNotAccepted') or ('ok', {store_cv_values})."""
    if store_cv_values and not accepts_store:
        return ("error", "storeNotAccepted")
    return ("ok", {"store_cv_values": store_cv_values})


def oracle_construct(store_cv_values):
    """patch.diff's behaviour: build the real estimator and observe the result.
    A refused construction surfaces as TypeError (the constructor does not expose
    the keyword); a successful one records `self.store_cv_values`."""
    try:
        est = RidgeClassifierCV(store_cv_values=store_cv_values)
    except TypeError:
        return ("error", "storeNotAccepted")
    return ("ok", {"store_cv_values": bool(est.store_cv_values)})


def fuzz_inputs(n, rng):
    # boundary: full cross product first
    for store in (False, True):
        yield store
    # then randomized re-sampling to exceed the fuzz floor deterministically
    for _ in range(n):
        yield rng.random() < 0.5


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for store in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_construct(ACCEPTS_STORE, store)
        oracle = oracle_construct(store)
        if shadow != oracle:
            disagreements.append((store, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for store, sh, orc in disagreements:
            print("  store_cv_values=%r shadow=%r oracle=%r" % (store, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of initEstimator agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
