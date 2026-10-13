#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25931
(plan §4.1).

Refutes (does not prove) the two R/I refinement legs of `fitComputeOffset`'s
impl: the modeled screening discipline of the fit offset path — it reuses the
already-prepared data, so the screening delta contributed by the offset
computation is ZERO and no feature-name re-screen occurs — and its scorer
MULTIPLICITY: the offset step invokes the screen-free scorer exactly ONCE.
Realized in Solution.lean by naming the screen-free scores as the value reference
`anomalyScores samples` (R-VALUE, mapping.md §2.1) rather than by invoking
`scorePublic`, the one scorer-invoking method in the file, which the offset
tail cannot invoke at all: that method is typed on the opaque caller-handle
type, the offset tail holds an opaque PREPARED matrix, and presenting a matrix to
a screen runs the other way and is not invertible, so no argument for it exists on
that path (mapping.md §6, refinement.md A2″).

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              over the real observables. `fitComputeOffset` performs NO screen
              at all — the one screening spelling in the file demands a matrix
              it has nothing to advise about, which the offset tail's context
              cannot establish — so the predicted observable of the
              patched fit's offset step is: no extra
              `_validate_data` call, hence no feature-name UserWarning; and its
              ONE occurrence of the score value maps to exactly ONE invocation of
              the real scorer on the non-default-contamination path (and to ZERO
              on `contamination="auto"`, where fit skips the offset step and the
              modeled method is never entered). The A-reference value legs
              (`anomalyScores`, `scoreValues`, `percentileAt`) are NOT substituted
              here — G-CONF
              isolates the R/I legs (screening discipline + multiplicity); the
              value legs stay with G-AX. So `conf_skip=false` and this is a real
              (non-skip) G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: a REAL `IsolationForest` fitted at
              base_commit with the gold patch applied (the real correctness
              oracle, G-RESOLVE). For each configuration we record whether
              `fit` emitted the spurious `UserWarning: X does not have valid
              feature names`, how many `_validate_data` calls fit performed past
              the initial one, and how many times fit invoked the screen-free
              scorer `_compute_chunked_score_samples`.

They must agree on every configuration: SHADOW == ORACLE. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Why the scorer-invocation COUNT belongs in the shadow. It is a real repository
observable — `test_iforest_chunks_works1/2` assert the exact `get_chunk_n_rows`
call count, so a second invocation on the offset path breaks PASS_TO_PASS — and
it is one the Lean logic cannot state as a clause: an invocation count is not a
value a postcondition can see, and a counting variable over it can be advanced
and then written straight back down, so a clause pinning its final value pins
bookkeeping rather than conduct (which is why the logic carries no such
variable). Solution.lean therefore carries it STRUCTURALLY (the offset path can
form no argument for the one scorer-invoking method, and a repeated VALUE
reference denotes one invocation — mapping.md §2.1, §6). This gate is where that structural claim is put against
the real observable, so a future impl that scores twice is caught here even
though no `ensures` mentions counting.

ORACLE COST / why not 10^5 live inputs:
  The oracle is a full `IsolationForest.fit` (ensemble construction + chunked
  scoring), not a pure function. Running 10^5 live fits is infeasible in the
  batched Docker gate. Following the django-13809 precedent (expensive live
  oracle), we differential-test over an exhaustive boundary grid (contamination
  in {auto, several non-default} x carrier in {DataFrame, ndarray} x several
  shapes incl. the issue's exact 1-column repro) PLUS `N_FUZZ` seeded random
  configurations, capping REAL fits at `MAX_FITS`. The cap is reported in the
  output (no silent truncation). The screening observable is a control-flow
  property of the patched source, so a bounded but varied sample exercises it
  faithfully; the value legs are covered separately and exhaustively by G-AX.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied. Imports numpy / pandas / scikit-learn only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import sys
import types
import warnings

import numpy as np

SEED = 25931
N_FUZZ = 100_000      # nominal fuzz draws requested ...
MAX_FITS = 1200       # ... capped to this many REAL fits (logged below)


def shadow_offset_step(contamination):
    """The R/I shadow of `fitComputeOffset`: it derives the offset from the
    screen-free scores of the already-prepared matrix, named as the value
    reference `anomalyScores samples`. No screen is admissible on that path, so
    the screening delta of the offset step is 0 and no feature-name re-screen
    occurs; and the ONE occurrence of that value maps to exactly one invocation
    of the real scorer (R-VALUE, mapping.md §2.1).

    Predicted observable for the patched fit:
      (warns_feature_names=False, extra_validate_calls=0, scorer_calls=1)
    on the non-default-contamination path, and scorer_calls=0 on
    `contamination="auto"`, where fit sets `offset_ = -0.5` without scoring, so
    the modeled method is never entered."""
    return (False, 0, 0 if contamination == "auto" else 1)


def oracle_fit_observable(contamination, carrier, n, d, rng):
    """patch.diff's behaviour: fit a real IsolationForest and record
    (warns_feature_names, extra_validate_calls_during_fit, scorer_calls). The
    first `_validate_data` of fit (line 291, the initial screen of raw input) is
    expected and subtracted; we count any FURTHER calls — those are the
    re-screens the bug introduced on the offset path. `scorer_calls` counts
    invocations of `_compute_chunked_score_samples`, the screen-free scorer both
    entry points sit on, which is the multiplicity observable."""
    import pandas as pd
    from sklearn.ensemble import IsolationForest

    data = rng.randn(n, d)
    if carrier == "df":
        X = pd.DataFrame(data, columns=["f%d" % i for i in range(d)])
    else:
        X = data

    clf = IsolationForest(random_state=0, contamination=contamination,
                          n_estimators=15)

    # Count _validate_data invocations and screen-free scorer invocations during
    # fit, via instance-level wrappers (does not mutate the class).
    counts = {"n": 0, "score": 0}
    orig = clf._validate_data.__func__                      # unbound
    orig_score = clf._compute_chunked_score_samples.__func__

    def counting(self, *args, **kwargs):
        counts["n"] += 1
        return orig(self, *args, **kwargs)

    def counting_score(self, *args, **kwargs):
        counts["score"] += 1
        return orig_score(self, *args, **kwargs)

    clf._validate_data = types.MethodType(counting, clf)
    clf._compute_chunked_score_samples = types.MethodType(counting_score, clf)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            clf.fit(X)
        warned = any("valid feature names" in str(x.message) for x in w)
    finally:
        del clf._validate_data                    # restore the class methods
        del clf._compute_chunked_score_samples

    extra = max(0, counts["n"] - 1)   # subtract the one expected initial screen
    return (warned, extra, counts["score"])


def configs(rng):
    """Boundary grid first, then seeded random fuzz (capped at MAX_FITS)."""
    contaminations = [0.05, 0.1, 0.25, 0.4, 0.01, "auto"]
    carriers = ["df", "nd"]
    shapes = [(4, 1), (16, 3), (40, 3), (64, 5), (8, 2)]
    # exhaustive boundary grid
    for c in contaminations:
        for carrier in carriers:
            for (n, d) in shapes:
                yield (c, carrier, n, d)
    # the issue's exact reproduction
    yield (0.05, "df", 4, 1)
    # seeded fuzz
    for _ in range(N_FUZZ):
        c = rng.choice([0.05, 0.1, 0.2, 0.3, 0.45, "auto"])
        c = float(c) if c != "auto" else "auto"
        carrier = rng.choice(["df", "nd"])
        n = int(rng.randint(4, 64))
        d = int(rng.randint(1, 6))
        yield (c, carrier, n, d)


def main():
    try:
        import pandas  # noqa: F401
    except Exception as e:
        print("G-CONF SKIP: pandas unavailable (%r)" % (e,))
        return 0

    rng = np.random.RandomState(SEED)
    disagreements = []
    count = 0
    for (c, carrier, n, d) in configs(rng):
        if count >= MAX_FITS:
            break
        count += 1
        shadow = shadow_offset_step(c)
        oracle = oracle_fit_observable(c, carrier, n, d, rng)
        # On the non-default-contamination path the offset step runs; the patched
        # behaviour must match the shadow exactly (no extra screen, no warning,
        # exactly ONE screen-free scorer invocation). On the "auto" path the
        # offset step is skipped entirely (offset_ = -0.5); there the shadow's
        # "no extra screen / no warning" still holds and the scorer count is 0.
        if shadow != oracle:
            disagreements.append((c, carrier, n, d, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d real fits:"
              % (len(disagreements), count))
        for c, carrier, n, d, sh, orc in disagreements:
            print("  contamination=%r carrier=%s n=%d d=%d shadow=%r oracle=%r"
                  % (c, carrier, n, d, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of fitComputeOffset (screening delta AND "
          "scorer multiplicity) agrees with patch.diff behaviour on %d real fits "
          "(seed=%d, capped at MAX_FITS=%d of N_FUZZ=%d requested), 0 "
          "disagreements: the patched fit performs no offset-path re-screen, "
          "raises no feature-name warning, and invokes the screen-free scorer "
          "exactly once when contamination != 'auto' (zero when it is)."
          % (count, SEED, MAX_FITS, N_FUZZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
