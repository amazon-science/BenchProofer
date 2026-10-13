#!/usr/bin/env python3
"""G-CONF differential conformance for scikit-learn__scikit-learn-13496.

Refutes the R/I refinement legs of refinement.md (A1-A8): the constructor
`configureEnsemble` forwards each of its arguments verbatim into the
configuration handed to the base ensemble machinery, INCLUDING the newly-exposed
incremental-fit reuse flag (`warm_start`).

  * SHADOW  — `configureEnsemble` transliterated to Python: assemble the
              forwarded configuration directly from the constructor arguments
              (each entry copied through; the bijection of mapping.md §2).
  * ORACLE  — the patched `IsolationForest.__init__` (the gold patch applied at
              base_commit; the harness applies patch.diff before this runs):
              construct a real `IsolationForest(...)` and read back the forwarded
              configuration off the instance (the attributes the base
              `BaseBagging.__init__`/`BaseEnsemble.__init__` set from the
              forwarded keywords).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. The discriminator is `warm_start`:
pre-patch, `IsolationForest(warm_start=...)` raises `TypeError` (no such
parameter); post-patch it is accepted and forwarded so `clf.warm_start == v`.

Runs in-container (the prebuilt SWE-Bench instance image); stdlib + sklearn only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 13496
N_FUZZ = 100_000

# The forwarded entries, in the order configureEnsemble carries them, paired with
# the attribute the base ensemble machinery exposes each on.
FORWARDED = [
    ("n_estimators", "n_estimators"),
    ("max_samples", "max_samples"),
    ("max_features", "max_features"),
    ("bootstrap", "bootstrap"),
    ("warm_start", "warm_start"),
    ("n_jobs", "n_jobs"),
    ("random_state", "random_state"),
    ("verbose", "verbose"),
]


def shadow_config(kwargs):
    """configureEnsemble transliterated: the forwarded configuration is exactly
    the caller's arguments, entry by entry. Inputs may be partial (the caller
    omits an argument to take its default); the shadow forwards only the entries
    the caller actually supplied, which is precisely what the comparison below
    checks against the oracle."""
    return {attr: kwargs[param] for param, attr in FORWARDED if param in kwargs}


def oracle_config(kwargs):
    """patch.diff's behaviour: construct the patched IsolationForest and read the
    forwarded configuration back off the instance."""
    from sklearn.ensemble import IsolationForest
    clf = IsolationForest(**kwargs)
    return {attr: getattr(clf, attr) for _param, attr in FORWARDED}


def fuzz_inputs(n, rng):
    # boundary cases first: defaults, each warm_start value, varied forwarded
    # entries.
    samples_choices = ["auto", 1, 20, 256, 0.5, 1.0]
    features_choices = [1, 2, 1.0, 0.5]
    njobs_choices = [None, 1, -1, 4]
    rstate_choices = [None, 0, 42, 12345]
    boundary = [
        dict(),                                  # all defaults (warm_start=False)
        dict(warm_start=True),
        dict(warm_start=False),
        dict(n_estimators=10, max_samples=20, warm_start=True),
        dict(n_estimators=100, bootstrap=True, warm_start=False),
    ]
    for kw in boundary:
        yield kw
    for _ in range(n):
        yield dict(
            n_estimators=rng.choice([10, 50, 100, 200]),
            max_samples=rng.choice(samples_choices),
            max_features=rng.choice(features_choices),
            bootstrap=rng.choice([True, False]),
            n_jobs=rng.choice(njobs_choices),
            random_state=rng.choice(rstate_choices),
            verbose=rng.choice([0, 1, 2]),
            warm_start=rng.choice([True, False]),
        )


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for kw in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # The shadow forwards exactly the entries the caller supplied (omitted
        # arguments take their defaults identically on both sides); every such
        # entry must be forwarded verbatim by the patched constructor.
        shadow = shadow_config(kw)
        oracle = oracle_config(kw)
        mism = {a: (shadow[a], oracle[a]) for a in shadow if oracle[a] != shadow[a]}
        if mism:
            disagreements.append((kw, mism))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kw, mism in disagreements:
            print("  args=%r mismatch(attr: shadow,oracle)=%r" % (kw, mism))
        return 1
    print("G-CONF OK: R/I shadow of configureEnsemble agrees with patched "
          "IsolationForest.__init__ forwarding (incl. warm_start) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
