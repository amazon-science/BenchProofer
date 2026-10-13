#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-10297.

The bundle models ONE step: the configuration recorded by the cross-validated
ridge *classifier* constructor `RidgeClassifierCV.__init__`. The modeled value is
the estimator's stored configuration (the touched `self.*` attributes) as a pure
function of the constructor options (mapping.md):

    alphas         (sequence, stored verbatim)
    fit_intercept  (bool)
    normalize      (bool)
    scoring        (None | scorer-id)
    cv             (None | splitter-id)
    class_weight   (None | weighting-id)
    store_cv_values(bool)

Post-patch rule: every supplied option is stored verbatim onto the like-named
attribute; in particular `store_cv_values` is forwarded to the parent initializer
and recorded as supplied.

This check runs against the REAL patched constructor (the orchestrator applies
the gold patch before running, `apply_gold=True`): for each fuzzed option tuple
we construct a `RidgeClassifierCV`, read back the seven attributes (the ORACLE),
and compare to the op-for-op transliteration of
`implementation_initClassifierCV` (the SHADOW, refinement.md): record each
supplied option verbatim. They must agree on every input — in particular when
`store_cv_values=True` (the case the prepatch drops).

stdlib + sklearn (already in the instance image). Pinned seed: 10297 (mapping.md).
"""
import random
import sys

SEED = 10297
N = 120_000

from sklearn.linear_model import RidgeClassifierCV


# --- ORACLE: the real patched constructor's stored configuration -------------
def oracle_config(alphas, fit_intercept, normalize, scoring, cv,
                  class_weight, store_cv_values):
    est = RidgeClassifierCV(
        alphas=alphas, fit_intercept=fit_intercept, normalize=normalize,
        scoring=scoring, cv=cv, class_weight=class_weight,
        store_cv_values=store_cv_values)
    return (
        tuple(est.alphas) if isinstance(est.alphas, (list, tuple)) else est.alphas,
        est.fit_intercept,
        est.normalize,
        est.scoring,
        est.cv,
        est.class_weight,
        est.store_cv_values,
    )


# --- SHADOW of implementation_initClassifierCV (the R/I leg) -----------------
# Mirrors Solution.lean: store every supplied option verbatim onto its field
# (cfg starts with classWeight := none then is overwritten with class_weight).
def shadow_config(alphas, fit_intercept, normalize, scoring, cv,
                  class_weight, store_cv_values):
    cfg = {
        "alphas": alphas, "fit_intercept": fit_intercept,
        "normalize": normalize, "scoring": scoring, "cv": cv,
        "store_cv_values": store_cv_values, "class_weight": None,
    }
    cfg["class_weight"] = class_weight
    return (
        tuple(cfg["alphas"]) if isinstance(cfg["alphas"], (list, tuple)) else cfg["alphas"],
        cfg["fit_intercept"],
        cfg["normalize"],
        cfg["scoring"],
        cfg["cv"],
        cfg["class_weight"],
        cfg["store_cv_values"],
    )


def disagree(args):
    got = oracle_config(*args)
    want = shadow_config(*args)
    if got != want:
        return (args, got, want)
    return None


# identity-only option pools (mapping.md: scoring/cv/class_weight are stored
# verbatim and only their identity is observed at construction).
SCORING_POOL = [None, "neg_mean_squared_error", "r2", "accuracy"]
CV_POOL = [None, 2, 3, 5, 10]
CLASS_WEIGHT_POOL = [None, "balanced", {1: 1.0, -1: 2.0}, {0: 0.5}]


def _enumerate_edge():
    cases = []
    base_alphas = (0.1, 1.0, 10.0)
    # the F2P shape: store_cv_values=True with a real alphas list
    cases.append(([1e-1, 1e0, 1e1], True, False, None, None, None, True))
    cases.append(([1e-1, 1e0, 1e1], True, False, None, None, None, False))
    # toggle each flag, both retention settings
    for scv in (True, False):
        cases.append((base_alphas, True, True, None, None, None, scv))
        cases.append((base_alphas, False, False, None, None, None, scv))
        cases.append((base_alphas, True, False, "r2", 3, "balanced", scv))
    return cases


def main() -> int:
    checked = 0
    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        nalpha = rng.randint(1, 5)
        alphas = [round(rng.uniform(1e-3, 1e3), 4) for _ in range(nalpha)]
        args = (
            alphas,
            rng.choice([True, False]),
            rng.choice([True, False]),
            rng.choice(SCORING_POOL),
            rng.choice(CV_POOL),
            rng.choice(CLASS_WEIGHT_POOL),
            rng.choice([True, False]),
        )
        d = disagree(args)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
