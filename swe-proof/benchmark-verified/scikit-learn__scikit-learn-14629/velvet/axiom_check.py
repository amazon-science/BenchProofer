#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14629.

The modeled method `gatherLabels` takes as input `submodels : List Submodel`,
the post-state of the UNCHANGED parent callee `MultiOutputEstimator.fit`
(`sklearn/multioutput.py:124`), consumed as a precondition (refinement.md A1):

  after a `MultiOutputClassifier` is fitted, `self.estimators_` is a list with
  one entry per target (`len == n_outputs`), each entry a fitted sub-model
  exposing a `.classes_` array of class labels, and the fit does not raise.

If that assumption were false (e.g. `estimators_` had the wrong length, or a
sub-model lacked `.classes_`), the modeled input carrier would not correspond to
reality and `out = gatheredLabels submodels` would not transliterate to the
patch expression `[e.classes_ for e in estimators_]`. This script validates the
assumption against the REAL patched repo callee, in-container (the orchestrator
applies patch.diff first). stdlib + the repo only. Exit 0 iff sound.
"""
import sys


def main():
    try:
        import numpy as np
        from sklearn.multioutput import MultiOutputClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_multilabel_classification
    except Exception as e:  # pragma: no cover
        print("G-AX FAIL: could not import the repo callee/deps: %r" % (e,))
        return 1

    # A handful of multilabel problems of varying target counts: the real fit
    # must, for each, leave estimators_ a list of length n_outputs with each
    # sub-model exposing a .classes_ array, and never raise.
    configs = [
        dict(n_samples=60, n_classes=3, n_labels=2, seed=0),
        dict(n_samples=80, n_classes=5, n_labels=3, seed=1),
        dict(n_samples=50, n_classes=2, n_labels=1, seed=2),
        dict(n_samples=70, n_classes=4, n_labels=2, seed=3),
    ]

    for cfg in configs:
        try:
            X, Y = make_multilabel_classification(
                n_samples=cfg["n_samples"], n_classes=cfg["n_classes"],
                n_labels=cfg["n_labels"], random_state=cfg["seed"])
        except Exception as e:
            print("G-AX FAIL: dataset gen raised for %r: %r" % (cfg, e))
            return 1

        n_outputs = Y.shape[1]
        clf = MultiOutputClassifier(RandomForestClassifier(
            n_estimators=2, random_state=cfg["seed"]))
        try:
            clf.fit(X, Y)
        except Exception as e:
            print("G-AX FAIL: real MultiOutputClassifier.fit raised for "
                  "%r: %r" % (cfg, e))
            return 1

        # (1) estimators_ is a list, one sub-model per target.
        est = clf.estimators_
        if not isinstance(est, list):
            print("G-AX FAIL: estimators_ is %r, expected list" % (type(est),))
            return 1
        if len(est) != n_outputs:
            print("G-AX FAIL: len(estimators_)=%d != n_outputs=%d (cfg %r)"
                  % (len(est), n_outputs, cfg))
            return 1

        # (2) each sub-model exposes a .classes_ array (the modeled labels
        #     field). The carrier is a sequence of class labels.
        for i, sub in enumerate(est):
            if not hasattr(sub, "classes_"):
                print("G-AX FAIL: estimators_[%d] lacks .classes_ (cfg %r)"
                      % (i, cfg))
                return 1
            labels = sub.classes_
            try:
                _ = list(np.asarray(labels).ravel())
            except Exception as e:
                print("G-AX FAIL: estimators_[%d].classes_ not array-like: "
                      "%r (cfg %r)" % (i, e, cfg))
                return 1

    print("G-AX OK: across %d fitted MultiOutputClassifier problems, the real "
          "(unchanged) parent fit leaves estimators_ a list of length "
          "n_outputs, each sub-model exposing a class-label array, and never "
          "raised. The A1 precondition is sound." % (len(configs),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
