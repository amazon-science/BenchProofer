#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-14629.

The bundle models ONE behavior: the body the gold patch adds to
`MultiOutputClassifier.fit` (`sklearn/multioutput.py`) AFTER `super().fit(...)`
has populated `self.estimators_` with the per-target fitted sub-models:

    self.classes_ = [estimator.classes_ for estimator in self.estimators_]

`implementation_collectClasses` (Solution.lean) collects, in target order, the
class labels recorded by each sub-model, returning the per-target view in
`Option` (`some` = the attribute is defined; the impl always produces
`some [...]`).

This script transliterates that R impl into Python (`shadow`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH list-comprehension behavior over `self.estimators_`.

We do NOT stand up scikit-learn's estimator machinery (heavy; the modeled value
reads only `estimator.classes_` off each already-fitted sub-model — `super().fit`
is the unchanged callee whose result enters as input data, mapping.md). Each
sub-model is represented by its `classes_` label list (`List Int`); both legs are
total functions of the sub-model list, so the edge set covers the boundary
(no sub-models, single sub-model, empty/duplicate label lists) and the fuzz loop
samples ≥1e5 random sub-model lists with varied lengths and label contents.

stdlib-only. Pinned seed: 14629 (also recorded in mapping.md).
"""
import sys

SEED = 14629
N = 120_000
MAX_SUBMODELS = 16
MAX_LABELS = 12


# --- ORACLE: the post-patch fit body, faithful in-process replica ------------
# estimators_ is a list of fitted sub-models; each exposes `.classes_`.
# self.classes_ = [estimator.classes_ for estimator in self.estimators_]
class _SubModel:
    def __init__(self, classes_):
        self.classes_ = classes_


def oracle(estimators_):
    return [estimator.classes_ for estimator in estimators_]


# --- shadow of implementation_collectClasses (the R leg) ----------------------
# Mirrors Solution.lean op-for-op: acc := []; for m in subModels: acc ++= [m.classLabels];
# result = some acc. The Python list of label-lists IS the unwrapped `some`.
def shadow(estimators_):
    acc = []
    for m in estimators_:
        acc = acc + [m.classLabels]
    return acc


class _ShadowSub:
    def __init__(self, classLabels):
        self.classLabels = classLabels


def disagree(label_lists):
    o = oracle([_SubModel(c) for c in label_lists])
    s = shadow([_ShadowSub(c) for c in label_lists])
    if o != s:
        return (label_lists, o, s)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _mk_labels(rnd):
    n = next(rnd) % (MAX_LABELS + 1)
    return [(next(rnd) % 201) - 100 for _ in range(n)]


def main() -> int:
    checked = 0

    # Edge set: 0 sub-models; one sub-model with empty / singleton / dup labels;
    # several sub-models including empty label lists.
    edges = [
        [],
        [[]],
        [[0]],
        [[7, 7, 7]],
        [[1, 2], [], [3]],
        [[-100], [100], [0, 0]],
        [[i for i in range(12)]],
    ]
    for ll in edges:
        d = disagree(ll)
        if d:
            print(f"DISAGREE edge {d[0]}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        k = next(rnd) % (MAX_SUBMODELS + 1)
        label_lists = [_mk_labels(rnd) for _ in range(k)]
        d = disagree(label_lists)
        if d:
            print(f"DISAGREE fuzz {d[0]}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
