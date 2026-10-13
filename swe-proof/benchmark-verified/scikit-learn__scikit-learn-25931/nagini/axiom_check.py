#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25931.

The model has ONE consumed @ContractOnly callee (`prepared_scorer`) and one
abstract token predicate (`offset_from_unvalidated_scoring`) it grants; plus two
A-reference deep models (`mismatch_advisory`, `prepared`). All are validated
here against the REAL scikit-learn callees, in-container.

The checks are split by patch-state (Defect 4 fix). Some obligations are
patch-INDEPENDENT (the unchanged base callees) and run regardless; the
obligations about the routine the patch INTRODUCES (`_score_samples`) and the
post-patch end-to-end behaviour are patch-DEPENDENT and run only when the gold
patch is applied (detected via `hasattr(IsolationForest, "_score_samples")`),
so this script returns 0 both with and without `apply_gold`.

Patch-INDEPENDENT obligations (unchanged base callees):

  (A-reference 1) `mismatch_advisory(arg_has_labels, fitted_with_labels)` ==
      real `BaseEstimator._check_feature_names(X, reset=False)`: the "X does not
      have valid feature names, but ... was fitted with feature names" advisory
      fires iff (arg carries no labels) and (estimator fitted with labels); the
      other three combinations are silent for THIS advisory.

  (A-reference 2) `prepared(X) == False` for every input: the real
      `_validate_data(reset=True)` casts a labelled table to an UNLABELLED
      numeric matrix and records labels without emitting the mismatch advisory.

  The public scoring routine (`score_samples`) validates its OWN argument, so an
      unlabelled array fed to a model fitted with labels triggers exactly one
      advisory (== mismatch_advisory(False, True) == 1). True at base and gold.

Patch-DEPENDENT obligations (the routine the patch introduces + end-to-end):

  (consumed axiom `prepared_scorer`) the real `_score_samples` runs NO
      label-consistency validation pass: fed an unlabelled array on a model
      fitted WITH labels it emits ZERO advisories (model: tally unchanged), AND
      it produces a usable score array (model: furnishes the offset / grants the
      token). This is exactly why an offset carrying the token can only have come
      from a no-validation scoring pass.

  (token soundness `offset_from_unvalidated_scoring`) the gold `fit`'s only
      producer of the calibration offset in the non-auto branch is
      `_score_samples`, which runs no validation; so the post-patch `fit` with
      contamination != "auto" on a LABELLED table emits ZERO label-mismatch
      advisories (the F2P case), plus the "auto"/unlabelled variants.

Imports only scikit-learn (the library under change) + numpy + stdlib (+ pandas,
skipped cleanly if absent). Exit 0 iff every applicable observation matches.
"""
import sys
import warnings

import numpy as np

from sklearn.base import BaseEstimator
from sklearn.ensemble import IsolationForest


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def mismatch_advisory(arg_has_labels, fitted_with_labels):
    """Reference of model.py's pure `mismatch_advisory`."""
    if (not arg_has_labels) and fitted_with_labels:
        return 1
    return 0


def prepared(_X_has_labels):
    """Reference of model.py's pure `prepared`: the prepared form is always
    unlabelled."""
    return False


# --- a probe estimator that exposes the real _check_feature_names ------------

class _Probe(BaseEstimator):
    """Minimal estimator to drive the REAL BaseEstimator._check_feature_names.

    feature_names_in_ is the attribute scikit-learn consults: present iff the
    estimator was fitted with labels.
    """


def _make_frame(labelled):
    """Return an input carrying labels (a 1-column DataFrame) or not (a 2D
    numpy array). Requires pandas (skip cleanly if absent)."""
    import pandas as pd

    if labelled:
        return pd.DataFrame({"a": [-1.1, 0.3, 0.5, 100.0]})
    return np.array([[-1.1], [0.3], [0.5], [100.0]])


def _count_target_advisories(fn, target="does not have valid feature names"):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fn()
    return sum(1 for w in caught if target in str(w.message))


def _count_feature_name_advisories(probe, X):
    """Run ONE real label-consistency pass (reset=False) and count the specific
    "X does not have valid feature names, but ... fitted with feature names"
    advisory."""
    return _count_target_advisories(lambda: probe._check_feature_names(X, reset=False))


# --- patch-INDEPENDENT obligations (unchanged base callees) ------------------

def check_consistency_rule():
    """A-reference 1: mismatch_advisory == real _check_feature_names over all
    four (arg_has_labels, fitted_with_labels) combinations."""
    for fitted_with_labels in (False, True):
        for arg_has_labels in (False, True):
            probe = _Probe()
            fit_X = _make_frame(fitted_with_labels)
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                probe._check_feature_names(fit_X, reset=True)
            assert (
                hasattr(probe, "feature_names_in_") == fitted_with_labels
            ), "reset=True did not record labels as modelled"

            arg_X = _make_frame(arg_has_labels)
            observed = _count_feature_name_advisories(probe, arg_X)
            expected = mismatch_advisory(arg_has_labels, fitted_with_labels)
            assert observed == expected, (
                "consistency-rule deep model unsound: fitted_with_labels=%r "
                "arg_has_labels=%r -> real=%d model=%d"
                % (fitted_with_labels, arg_has_labels, observed, expected)
            )


def check_prepared_drops_labels():
    """A-reference 2: the real preparation pass (_validate_data, reset=True)
    drops labels — its output carries no feature names — for both labelled and
    unlabelled input, so prepared(X) == False is sound."""
    from sklearn.utils.validation import _get_feature_names

    for labelled in (False, True):
        probe = _Probe()
        X = _make_frame(labelled)
        out = probe._validate_data(X, reset=True, dtype=np.float32)
        out_labels = _get_feature_names(out)
        assert (out_labels is not None) == prepared(labelled), (
            "prepared deep model unsound: input labelled=%r -> prepared output "
            "has_labels=%r, model says %r"
            % (labelled, out_labels is not None, prepared(labelled))
        )


def check_public_score_samples_still_validates():
    """The PUBLIC scoring routine validates its own argument, so an UNLABELLED
    array fed to a model fitted WITH labels triggers exactly one advisory
    (model's mismatch_advisory(False, True) == 1). True at base and gold."""
    Xframe = _make_frame(True)            # fit with labels
    Xarray = _make_frame(False)           # score with an unlabelled array
    model = IsolationForest(random_state=0, contamination="auto").fit(Xframe)
    n = _count_target_advisories(lambda: model.score_samples(Xarray))
    assert n == mismatch_advisory(False, True) == 1, (
        "public score_samples did not validate its own argument as modelled: "
        "got %d advisories, model expects 1" % n
    )


# --- patch-DEPENDENT obligations (introduced routine + end-to-end) -----------

def check_prepared_scorer_runs_no_validation():
    """Consumed-axiom soundness for `prepared_scorer`: the real `_score_samples`
    (introduced by the patch) runs NO label-consistency validation pass. Fed an
    UNLABELLED array on a model fitted WITH labels it emits ZERO advisories
    (model: the advisory tally is unchanged by calling it), and it returns a
    usable score array (model: it furnishes the token-bearing offset)."""
    Xframe = _make_frame(True)            # fit WITH labels
    Xprepared = np.asarray(_make_frame(False), dtype=np.float32)  # already-prepared, unlabelled
    model = IsolationForest(random_state=0, contamination="auto").fit(Xframe)
    n = _count_target_advisories(lambda: model._score_samples(Xprepared))
    assert n == 0, (
        "the no-validation scorer emitted %d label-mismatch advisories; it must "
        "run no second validation pass (tally unchanged)" % n
    )
    scores = model._score_samples(Xprepared)
    assert np.asarray(scores).shape[0] == Xprepared.shape[0], (
        "the no-validation scorer did not produce one score per row, so it "
        "cannot furnish the calibration offset as the token requires"
    )


def check_offset_derives_from_prepared_training_input():
    """Provenance soundness for the `prepared_input` token (the attack10 fix):
    the gold `fit` derives `offset_` from `_score_samples(<the validated training
    X>)` — i.e. the scored matrix is the PREPARED FORM OF FIT'S OWN INPUT, not a
    foreign/fabricated array. Confirms (a) the offset equals percentile over the
    per-row scores of the prepared training data, and (b) it does NOT equal the
    offset that scoring a DIFFERENT (foreign) array would yield — so the model's
    requirement that the scorer be fed the fit's own prepared input (the
    `prepared_input` / `raw_fit_input` tokens) is faithful and load-bearing."""
    X = _make_frame(True)                 # labelled training table
    contamination = 0.05
    model = IsolationForest(random_state=0, contamination=contamination).fit(X)

    # the prepared form of fit's OWN training input (reset=False keeps fit-time
    # validation but does not re-record labels), exactly the array gold's
    # `_score_samples(X)` is fed inside fit.
    Xprepared = model._validate_data(
        X, accept_sparse="csr", dtype=np.float32, reset=False
    )
    expected = np.percentile(model._score_samples(Xprepared), 100.0 * contamination)
    assert np.isclose(model.offset_, expected), (
        "gold fit's offset_ does not derive from _score_samples of the prepared "
        "training input: offset_=%r vs percentile(_score_samples(prepared X))=%r"
        % (model.offset_, expected)
    )

    # a FOREIGN unlabelled array (different data) would yield a DIFFERENT offset,
    # so the offset is grounded in the actual training data — feeding the scorer a
    # fabricated matrix (model attack10) would not reproduce it.
    foreign = np.array([[10.0], [11.0], [12.0], [13.0]], dtype=np.float32)
    foreign_offset = np.percentile(
        model._score_samples(foreign), 100.0 * contamination
    )
    assert not np.isclose(model.offset_, foreign_offset), (
        "scoring a foreign array reproduced the offset; the prepared-input "
        "provenance constraint would not be load-bearing"
    )


def check_fit_emits_no_advisory():
    """Token soundness + end-to-end F2P: the gold `fit`'s only producer of the
    calibration offset in the non-auto branch is the no-validation scorer, so
    fitting with contamination != "auto" on a LABELLED table emits ZERO
    label-mismatch advisories (the F2P case). Also covered: 'auto' and
    unlabelled input."""
    cases = [
        (True, 0.05),    # the F2P case: labelled + non-auto contamination
        (True, "auto"),
        (False, 0.05),
        (False, "auto"),
    ]
    for labelled, contamination in cases:
        X = _make_frame(labelled)
        model = IsolationForest(random_state=0, contamination=contamination)
        n = _count_target_advisories(lambda: model.fit(X))
        assert n == 0, (
            "fit emitted %d label-mismatch advisories for labelled=%r "
            "contamination=%r; the fit path must emit none"
            % (n, labelled, contamination)
        )
        if contamination != "auto":
            model = IsolationForest(random_state=0, contamination=contamination).fit(X)
            assert hasattr(model, "offset_"), (
                "fit with contamination=%r did not set offset_; the offset is a "
                "required product of fitting (model: offset_set)" % contamination
            )


def main():
    try:
        import pandas  # noqa: F401
    except Exception:
        print("G-AX SKIP: pandas unavailable; cannot exercise labelled input")
        return 0

    # patch-independent (unchanged base callees) — always run.
    check_consistency_rule()
    check_prepared_drops_labels()
    check_public_score_samples_still_validates()

    # patch-dependent — only when the gold patch is applied (the introduced
    # private scorer exists). Without it, these obligations are about code that
    # does not yet exist, so skip them rather than fail spuriously (Defect 4).
    gold_applied = hasattr(IsolationForest, "_score_samples")
    if gold_applied:
        check_prepared_scorer_runs_no_validation()
        check_offset_derives_from_prepared_training_input()
        check_fit_emits_no_advisory()
        tail = (
            "; no-validation scorer emits 0 advisories on an unlabelled array "
            "after a labelled fit and produces per-row scores; the offset derives "
            "from _score_samples of the prepared training input (not a foreign "
            "array); post-patch fit emits 0 advisories for 4 (labelled x "
            "contamination) cases and sets offset_ when contamination != 'auto'."
        )
    else:
        tail = " (patch-dependent checks skipped: gold not applied)."

    print(
        "G-AX OK: mismatch_advisory + prepared deep models == real "
        "_check_feature_names/_validate_data over 4 label combinations; public "
        "score_samples validates its own argument (1 advisory)" + tail
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
