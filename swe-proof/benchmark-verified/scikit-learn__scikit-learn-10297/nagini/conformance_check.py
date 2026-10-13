#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-10297
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model IS Python: two minimal carrier
classes (EngineConfig, CvRecord) whose __init__ bodies are plain field
assignments, plus the two modeled functions run directly. There are no @Pure
helpers with executable content and no @ContractOnly callees (the axioms
region is empty), so no PSeq shim is needed.

ORACLE: the REAL patched repo estimator the model models per mapping.md —
`sklearn.linear_model.RidgeClassifierCV`. The gate applies the gold patch to
/testbed before this script runs and sets PYTHONPATH so the patched package
is what imports here; this script does NOT apply any patch itself.

Type bridge (mapping.md section 2):
  * the caller-supplied retention flag maps identically to the model's bool
    parameter; the configured engine's retention attribute maps identically
    to EngineConfig.retain_values — observed on the oracle side as the
    constructed estimator's `store_cv_values` attribute;
  * the retained per-alpha values array (or its absence) maps to
    Optional[CvRecord]: absence of the fitted attribute <-> None; when
    present, (ndim, shape[0], shape[1], shape[2]) <->
    (rank, n_samples, n_targets, n_alphas);
  * n_targets on the oracle side is the column count of the label-binarized
    target matrix the classifier builds internally; the bridge computes it
    with the same (unchanged) LabelBinarizer transform on the raw target, so
    the shadow's n_targets input is derived from the raw input, never read
    back from the oracle's output.

Input domain: configure_classifier_cv's precondition is True over a bool, so
every flag value (under any combination of the other constructor settings) is
Requires-satisfying. stored_cv_values' precondition admits n_samples >= 0,
n_targets >= 1, n_alphas >= 0, but the real estimator's fit raises on the
degenerate empty extents instead of returning a record, and a classification
fit needs at least two classes present; generation for the fit-based
comparison is therefore restricted to the estimator's operating domain
(n_samples >= 5, n_alphas >= 1, targets with every class/column active) —
the same domain the shipped test battery exercises.

>= 1e5 Requires-satisfying inputs: 100000 constructor-forwarding fuzz cases
(flag + varied other settings) + boundary cases + 900+ fit-based shape cases
(binary / multiclass / multilabel targets, both flag values). Pinned fuzz
seed: 10297.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 10297
N_FLAG_FUZZ = 100_000
N_FIT_FUZZ = 300          # iterations; each runs 3 fits (binary/multiclass/multilabel)

from typing import List, Optional


# --- the impl region of model.py, verbatim, contract calls stripped -----------

class EngineConfig:
    """The configuration handed to the underlying cross-validation engine.
    Only the touched field is modelled: whether the per-alpha values are
    retained."""

    def __init__(self, retain_values: bool) -> None:
        # impl-start
        self.retain_values = retain_values  # type: bool
        # impl-end


class CvRecord:
    """The retained cross-validation values record. Modelled by its axis count
    and the three axis lengths (samples, targets, penalties)."""

    def __init__(self, rank: int, n_samples: int, n_targets: int,
                 n_alphas: int) -> None:
        # impl-start
        self.rank = rank            # type: int
        self.n_samples = n_samples  # type: int
        self.n_targets = n_targets  # type: int
        self.n_alphas = n_alphas    # type: int
        # impl-end


def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
    # impl-start
    cfg = EngineConfig(store_cv_values)
    return cfg
    # impl-end


def stored_cv_values(cfg: EngineConfig, n_samples: int, n_targets: int,
                     n_alphas: int) -> Optional[CvRecord]:
    # impl-start
    if cfg.retain_values:
        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
        return record
    return None
    # impl-end


# --- bridge helpers ------------------------------------------------------------

def binarized_target_columns(y):
    """n_targets for a raw target, per the bridge: the column count of the
    label-binarized 2-D target matrix the classifier builds internally.
    Computed with the same (unchanged) transformer on the raw input."""
    from sklearn.preprocessing import LabelBinarizer
    Y = LabelBinarizer(pos_label=1, neg_label=-1).fit_transform(y)
    if Y.ndim == 1:
        return 1
    return Y.shape[1]


def check_flag_case(RidgeClassifierCV, flag, kwargs):
    """Diff behaviour (1): the configured engine's retention flag equals the
    caller-requested flag."""
    shadow_cfg = configure_classifier_cv(flag)
    est = RidgeClassifierCV(store_cv_values=flag, **kwargs)
    real_flag = est.store_cv_values
    if shadow_cfg.retain_values != real_flag:
        return ("DISAGREEMENT (flag forwarding)\n  requested=%r kwargs=%r\n"
                "  shadow retain_values=%r\n  real store_cv_values=%r"
                % (flag, kwargs, shadow_cfg.retain_values, real_flag))
    return None


def check_fit_case(RidgeClassifierCV, X, y, alphas, flag):
    """Diff behaviour (2): the retained record vs the fitted estimator's
    retained values array (or both absent)."""
    n_samples = X.shape[0]
    n_alphas = len(alphas)
    n_targets = binarized_target_columns(y)

    cfg = configure_classifier_cv(flag)
    shadow_rec = stored_cv_values(cfg, n_samples, n_targets, n_alphas)
    shadow_obs = (None if shadow_rec is None else
                  (shadow_rec.rank, shadow_rec.n_samples,
                   shadow_rec.n_targets, shadow_rec.n_alphas))

    est = RidgeClassifierCV(alphas=alphas, store_cv_values=flag)
    est.fit(X, y)
    if hasattr(est, "cv_values_"):
        arr = est.cv_values_
        real_obs = (arr.ndim,) + tuple(arr.shape)
        # a rank-k array observation carries k axis lengths; pad/truncate is
        # never applied — a rank mismatch is reported as-is below
    else:
        real_obs = None

    if shadow_obs != real_obs:
        return ("DISAGREEMENT (retained record)\n"
                "  flag=%r n_samples=%d n_targets=%d n_alphas=%d\n"
                "  y=%r\n  shadow=(rank, samples, targets, penalties)=%r\n"
                "  real=(ndim, *shape)=%r"
                % (flag, n_samples, n_targets, n_alphas, y.tolist(),
                   shadow_obs, real_obs))
    return None


# --- input generation -----------------------------------------------------------

def flag_kwargs(rng):
    """Varied constructor settings orthogonal to the modelled flag."""
    n_alphas = rng.randint(1, 5)
    return {
        "alphas": [10.0 ** rng.uniform(-3, 3) for _ in range(n_alphas)],
        "fit_intercept": rng.random() < 0.5,
        "normalize": rng.random() < 0.5,
    }


def boundary_fit_cases():
    X = np.array([[-1.0, -1.0], [-1.0, 0.0], [-0.8, -1.0],
                  [1.0, 1.0], [1.0, 0.0]])
    y_bin = np.array([1, 1, 1, -1, -1])
    y_multi = np.array([[1, 1, 1, -1, -1],
                        [1, -1, 1, -1, 1],
                        [-1, -1, 1, -1, -1]]).transpose()
    alphas3 = [1e-1, 1e0, 1e1]
    return [
        (X, y_bin, alphas3, True),      # binary target, retention on
        (X, y_bin, alphas3, False),     # retention off: both sides absent
        (X, y_multi, alphas3, True),    # multilabel target
        (X, y_multi, alphas3, False),
        (X, y_bin, [1.0], True),        # single penalty candidate
        (X, np.array([0, 1, 2, 1, 0]), alphas3, True),  # 3-class 1-D target
    ]


def main():
    from sklearn.linear_model import RidgeClassifierCV  # REAL patched callee

    checked = 0
    rng = random.Random(SEED)
    nprng = np.random.RandomState(SEED)

    # --- behaviour (1): flag forwarding, cheap, 1e5 fuzz cases ---------------
    for v in (True, False):
        err = check_flag_case(RidgeClassifierCV, v, {})
        if err:
            print(err)
            return 1
        checked += 1
    for _ in range(N_FLAG_FUZZ):
        err = check_flag_case(RidgeClassifierCV, rng.random() < 0.5,
                              flag_kwargs(rng))
        if err:
            print(err)
            return 1
        checked += 1

    # --- behaviour (2): retained record, fit-based, boundary + fuzz ----------
    n_fit = 0
    for X, y, alphas, flag in boundary_fit_cases():
        err = check_fit_case(RidgeClassifierCV, X, y, alphas, flag)
        if err:
            print(err)
            return 1
        checked += 1
        n_fit += 1

    for i in range(N_FIT_FUZZ):
        n_samples = int(nprng.randint(5, 18))
        n_features = int(nprng.randint(2, 6))
        n_alphas = int(nprng.randint(1, 5))
        alphas = list(np.logspace(-2, 2, n_alphas))
        Xf = nprng.randn(n_samples, n_features)
        # mostly retention on (the informative side); a slice with it off
        flag = (i % 5 != 4)

        # binary 1-D target, both classes present
        yb = nprng.randint(0, 2, size=n_samples)
        yb[0], yb[1] = 0, 1
        err = check_fit_case(RidgeClassifierCV, Xf, yb, alphas, flag)
        if err:
            print(err)
            return 1
        checked += 1
        n_fit += 1

        # multiclass 1-D target (3..4 classes, each present)
        ncls = int(nprng.randint(3, 5))
        if n_samples >= ncls + 1:
            ym = nprng.randint(0, ncls, size=n_samples)
            ym[:ncls] = np.arange(ncls)
            err = check_fit_case(RidgeClassifierCV, Xf, ym, alphas, flag)
            if err:
                print(err)
                return 1
            checked += 1
            n_fit += 1

        # multilabel indicator target, every column active both ways
        ncol = int(nprng.randint(2, 5))
        Ym = nprng.randint(0, 2, size=(n_samples, ncol))
        Ym[0, :] = 0
        Ym[1, :] = 1
        err = check_fit_case(RidgeClassifierCV, Xf, Ym, alphas, flag)
        if err:
            print(err)
            return 1
        checked += 1
        n_fit += 1

    print("G-CONF OK: shadow impl == real estimator on %d inputs "
          "(%d flag-forwarding + %d fit-based shape checks, seed %d)."
          % (checked, checked - n_fit, n_fit, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "fit_cases": n_fit,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
