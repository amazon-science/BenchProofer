#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14710
(nagini).

SHADOW: the impl regions of model.py's two contracted functions
(`primary_score_target`, `secondary_score_target`), copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The
model IS Python; the loops run directly. `ToSeq`/`PSeq` are shimmed as plain
tuples so the proof-only local assignment inside the loop stays verbatim (its
value is only consumed by stripped Assert lines). The @Pure helpers carry no
impl-region content the loops call (they are spec vocabulary only), so they
are not needed by the shadow. The axioms region is empty — no @ContractOnly
callee.

ORACLE: the REAL patched repo method the model models per mapping.md —
`BaseHistGradientBoosting._check_early_stopping_scorer` in
sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py. The gate
applies the gold patch to /testbed before this script runs and sets
PYTHONPATH so the patched package is what imports here; this script does NOT
apply any patch itself. The two modeled sites are the two target values that
method hands to `self.scorer_` (train target always; validation target when
`self._use_validation_data`). To observe them, a real estimator instance
(classifier or regressor — the real classes, so the real classifier dispatch
runs) is built without fitting, given the state the method reads
(`classes_`, `_use_validation_data`, score lists) and a capturing `scorer_`;
the method is then invoked and the captured y values are diffed against the
shadow outputs.

Type bridge (mapping.md section 2):
  * `is_clf` <-> which real estimator class receives the call (classifier vs
    regressor) — the real dispatch predicate evaluates on the real class;
  * `use_secondary` <-> the `_use_validation_data` attribute; the secondary
    site is only compared when it is True (the model's precondition);
  * `labels: List[int]` <-> the `classes_` array (the table of distinct
    original class values). Integer tables map identically; a string-table
    battery maps each distinct value to its table position's int via the
    value<->int bijection, applied to the captured output;
  * `target: List[int]` <-> the encoded integer-index target array. The real
    arrays hold integral values in int or float dtype (the repo stores
    targets in a float dtype); the bridge is int() per element, exercised
    over int64 / float64 / float32 carriers;
  * the shadow's returned List[int] <-> the y value captured from the
    scorer call at the corresponding site (element-wise, after the label
    bijection for the string battery).

Input domain (Requires): targets of any length whose every element is a
valid index into a non-empty labels table (in_index_range); labels
duplicates are not excluded by the contract, but real class tables hold
distinct values, so fuzz tables are distinct (boundary battery still probes
a duplicate-value table). For the regressor side the index-range premise is
vacuous; targets are arbitrary ints.

>= 1e5 Requires-satisfying inputs: 100000 fuzz method invocations (each
checks the primary site and, when the held-out flag is set, the secondary
site) + 2000 string-table invocations + boundary cases. Pinned fuzz seed:
14710 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 14710
N_FUZZ = 100_000
N_STRING_FUZZ = 2_000

from typing import List

# --- shims so the impl region below runs verbatim -----------------------------
ToSeq = tuple                       # PSeq view of a list -> plain tuple


def PSeq(*xs):                      # PSeq literal -> plain tuple
    return tuple(xs)


# --- impl regions of model.py, verbatim, contract calls stripped --------------

def primary_score_target(is_clf: bool, labels: List[int],
                         target: List[int]) -> List[int]:
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            out = out + [target[j]]
            j = j + 1
        return out
    # impl-end


def secondary_score_target(use_secondary: bool, is_clf: bool,
                           labels: List[int],
                           target: List[int]) -> List[int]:
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            out = out + [target[j]]
            j = j + 1
        return out
    # impl-end


# --- oracle harness ------------------------------------------------------------

class CapturingScorer(object):
    """Stands in for scorer_: records the y each scoring call receives (the
    modeled value) and returns a float like a real scorer would."""

    def __init__(self):
        self.captured = []

    def __call__(self, est, X, y):
        self.captured.append(np.asarray(y).copy())
        return 0.0


def real_scored_targets(clf_cls, reg_cls, is_clf, classes, y_train, y_val,
                        use_val):
    """Invoke the REAL patched method on a real (unfitted) estimator carrying
    exactly the state the method reads, and return the captured scorer
    targets: (train_y, val_y_or_None)."""
    cls = clf_cls if is_clf else reg_cls
    est = cls.__new__(cls)                       # real class => real dispatch
    est.train_score_ = []
    est.validation_score_ = []
    est._use_validation_data = use_val
    # the method's trailing stopping-decision helper reads these two knobs;
    # they do not touch the modeled values (the y handed to the scorer)
    est.n_iter_no_change = 5
    est.tol = 1e-7
    if classes is not None:
        est.classes_ = np.asarray(classes)
    scorer = CapturingScorer()
    est.scorer_ = scorer
    X_train = np.zeros((len(y_train), 1))
    X_val = np.zeros((len(y_val), 1))
    est._check_early_stopping_scorer(X_train, y_train, X_val, y_val)
    train_y = scorer.captured[0]
    val_y = scorer.captured[1] if use_val else None
    if use_val:
        assert len(scorer.captured) == 2
    else:
        assert len(scorer.captured) == 1
    return train_y, val_y


def check_case(clf_cls, reg_cls, is_clf, labels, t_train, t_val, use_val,
               dtype, label_map=None):
    """Run one method invocation and diff both modeled sites.

    labels: List[int] (the model carrier). label_map: optional dict mapping
    each original class value in the real table to its model int (the string
    battery); None means the real table IS the int carrier. Returns an error
    string or None. Also returns the number of site-inputs checked."""
    if label_map is None:
        classes = np.asarray(labels) if is_clf else None
        to_int = lambda v: int(v)
    else:
        # real table = the original values, model table = their int images
        inv = {iv: v for v, iv in label_map.items()}
        classes = np.asarray([inv[m] for m in labels], dtype=object) \
            if is_clf else None
        to_int = lambda v: label_map[v]

    y_train = np.asarray(t_train, dtype=dtype)
    y_val = np.asarray(t_val, dtype=dtype)

    real_train, real_val = real_scored_targets(
        clf_cls, reg_cls, is_clf, classes, y_train, y_val, use_val)

    checked = 0
    # site #1 — the always-scored (train) target
    shadow_train = primary_score_target(is_clf, list(labels), list(t_train))
    real_train_ints = [to_int(v) for v in real_train]
    if shadow_train != real_train_ints:
        return ("DISAGREEMENT (primary site)\n"
                "  is_clf=%r use_val=%r dtype=%s labels=%r target=%r\n"
                "  shadow=%r\n  real  =%r"
                % (is_clf, use_val, dtype, labels, t_train,
                   shadow_train, real_train_ints)), checked
    checked += 1

    # site #2 — the held-out target, only in-domain when the flag is set
    if use_val:
        shadow_val = secondary_score_target(True, is_clf, list(labels),
                                            list(t_val))
        real_val_ints = [to_int(v) for v in real_val]
        if shadow_val != real_val_ints:
            return ("DISAGREEMENT (secondary site)\n"
                    "  is_clf=%r use_val=%r dtype=%s labels=%r target=%r\n"
                    "  shadow=%r\n  real  =%r"
                    % (is_clf, use_val, dtype, labels, t_val,
                       shadow_val, real_val_ints)), checked
        checked += 1
    return None, checked


def boundary_cases():
    """(is_clf, labels, t_train, t_val, use_val, dtype)"""
    return [
        (True, [10], [0, 0, 0], [0], True, np.int64),          # k=1 table
        (True, [10, 20], [], [], True, np.int64),               # empty targets
        (True, [10, 20], [], [1, 0], True, np.float64),         # empty train only
        (True, [5, 6, 7], [2, 1, 0, 2, 0], [0, 2], True, np.float64),
        (True, [5, 6, 7], [2, 1, 0], [0], False, np.int64),     # no held-out
        (True, [-3, 0, 3], [0, 1, 2, 2], [1], True, np.float32),
        (True, [7, 7], [0, 1, 0], [1], True, np.int64),         # duplicate values
        (False, [0], [4, -2, 0, 9], [3, 3], True, np.int64),    # regressor
        (False, [0], [1000000, -1000000], [0], False, np.float64),
        (False, [0], [], [], True, np.float64),
    ]


def main():
    # REAL patched module (import path per mapping.md); importing the module
    # directly does not require the experimental enable shim.
    from sklearn.ensemble._hist_gradient_boosting.gradient_boosting import (
        HistGradientBoostingClassifier, HistGradientBoostingRegressor)
    clf_cls, reg_cls = HistGradientBoostingClassifier, HistGradientBoostingRegressor

    rng = random.Random(SEED)
    checked = 0

    # --- boundary ---------------------------------------------------------
    for is_clf, labels, tt, tv, uv, dt in boundary_cases():
        err, n = check_case(clf_cls, reg_cls, is_clf, labels, tt, tv, uv, dt)
        checked += n
        if err:
            print(err)
            return 1

    # --- fuzz, int-carrier tables ------------------------------------------
    dtypes = (np.int64, np.float64, np.float32)
    for it in range(N_FUZZ):
        is_clf = rng.random() < 0.75           # decode branch is the informative one
        use_val = rng.random() < 0.75
        k = rng.randint(1, 8)
        labels = rng.sample(range(-1000, 1000), k)
        n_tr = rng.randint(0, 20)
        n_va = rng.randint(0, 20)
        if is_clf:
            t_train = [rng.randint(0, k - 1) for _ in range(n_tr)]
            t_val = [rng.randint(0, k - 1) for _ in range(n_va)]
        else:
            t_train = [rng.randint(-500, 500) for _ in range(n_tr)]
            t_val = [rng.randint(-500, 500) for _ in range(n_va)]
        dt = dtypes[it % 3]
        err, n = check_case(clf_cls, reg_cls, is_clf, labels, t_train, t_val,
                            use_val, dt)
        checked += n
        if err:
            print(err)
            return 1

    # --- fuzz, string tables through the value<->int bijection --------------
    pool = ['x', 'y', 'z', 'cat', 'dog', 'alpha', 'beta', 'q', 'foo', 'bar']
    for it in range(N_STRING_FUZZ):
        k = rng.randint(1, 6)
        values = sorted(rng.sample(pool, k))     # a sorted distinct table
        label_map = {v: i * 3 + 1 for i, v in enumerate(values)}
        labels = [label_map[v] for v in values]
        use_val = rng.random() < 0.75
        t_train = [rng.randint(0, k - 1) for _ in range(rng.randint(0, 20))]
        t_val = [rng.randint(0, k - 1) for _ in range(rng.randint(0, 20))]
        dt = np.float64 if it % 2 else np.int64
        err, n = check_case(clf_cls, reg_cls, True, labels, t_train, t_val,
                            use_val, dt, label_map=label_map)
        checked += n
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real scored targets on %d site-inputs "
          "(both modeled sites, int + string class tables, int/float target "
          "carriers, seed %d)." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
