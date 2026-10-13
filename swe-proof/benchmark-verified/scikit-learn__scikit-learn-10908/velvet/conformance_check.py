#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-10908.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`featureNamesRun`:
              the `hasattr`-guarded establishment step, the readiness guard, and
              the index-ordered term projection), transliterated to Python over
              the real repo type. The A-reference callees `_validate_vocabulary`
              / `_check_vocabulary` are left as the REAL repo callees (G-CONF
              isolates the R/I legs; the A-reference legs stay with G-AX).
  * ORACLE  — `patch.diff`'s behaviour: the real patched
              `CountVectorizer.get_feature_names`, applied at base_commit with the
              gold patch applied (the harness applies patch.diff before this runs).

Observable output = (outcome, fixed_vocabulary_, vocabulary_-as-sorted-pairs)
where outcome is either ("ok", terms-in-index-order) or ("raise", ExceptionType).
They must agree on every Requires-satisfying input (vocabulary None or a
well-formed unique non-empty list; estimator never fitted). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sklearn only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sklearn.feature_extraction.text import CountVectorizer


SEED = 10908
N_FUZZ = 100_000


def _observe(cv, run):
    """Run `run(cv)` and capture the observable (outcome, flag, index) tuple."""
    try:
        names = run(cv)
        outcome = ("ok", list(names))
    except Exception as exc:                       # NotFittedError / ValueError
        outcome = ("raise", type(exc).__name__)
    flag = getattr(cv, "fixed_vocabulary_", "<unset>")
    if hasattr(cv, "vocabulary_"):
        index = sorted(cv.vocabulary_.items(), key=lambda p: p[1])
    else:
        index = "<unset>"
    return (outcome, flag, index)


def shadow_run(cv):
    """featureNamesRun transliterated: the impl region's R/I orchestration,
    delegating to the REAL A-reference callees. Mirrors Solution.lean exactly:
      st := if st.index = none then materializeIndex supplied st else st
      match readinessGuard st with error e => e | ok _ => featureList ...
    """
    if not hasattr(cv, "vocabulary_"):             # st.index = none  (R/I guard)
        cv._validate_vocabulary()                  # materializeIndex (A-reference)
    cv._check_vocabulary()                         # readinessGuard   (A-reference)
    # featureList: terms in ascending index order (I)
    return [t for t, i in sorted(cv.vocabulary_.items(), key=lambda p: p[1])]


def oracle_run(cv):
    """patch.diff's behaviour: the real patched get_feature_names."""
    return list(cv.get_feature_names())


def fuzz_inputs(n, rng):
    pool = ["beer", "burger", "celeri", "coke", "pizza", "salad", "sparkling",
            "tomato", "water", "and", "document", "first", "is", "one",
            "second", "the", "third", "this", "alpha", "zeta", "x", "q9", "m"]
    # boundary cases first (plan §4.1 step 4)
    yield None                                     # unfitted, no vocabulary
    yield ["beer"]
    yield ["beer", "burger"]
    yield ["beer", "burger", "celeri", "coke", "pizza", "salad", "sparkling",
           "tomato", "water"]
    yield ["and", "document", "first", "is", "one", "second", "the", "third",
           "this"]
    yield ["z", "y", "x", "w"]                      # descending terms
    for _ in range(n):
        if rng.random() < 0.02:
            yield None
            continue
        k = rng.randint(1, len(pool))
        yield rng.sample(pool, k)                   # unique, non-empty


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for supplied in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # Two FRESH, never-fitted estimators with the same constructor input, so
        # the shadow and oracle observe the same starting state independently.
        shadow_obs = _observe(CountVectorizer(vocabulary=supplied), shadow_run)
        oracle_obs = _observe(CountVectorizer(vocabulary=supplied), oracle_run)
        if shadow_obs != oracle_obs:
            disagreements.append((supplied, shadow_obs, oracle_obs))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  vocab=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of getFeatureInventory (hasattr-guarded "
          "establishment + readiness guard + index-ordered projection) agrees "
          "with patch.diff behaviour on %d (vocabulary, unfitted-estimator) "
          "inputs (seed=%d), 0 disagreements; outcome + fixed_vocabulary_ + "
          "vocabulary_ order all match." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
