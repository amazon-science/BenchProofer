#!/usr/bin/env python3
"""G-AX — validate the bundle's axiom (`checked_idem`) and the deep model of the
input-validation step (A-reference `validateInput`) against the REAL
scikit-learn callees, in-container.

The Lean model under test (Solution.lean, impl region):

    validateInput x reset ref =
      { carrier  := { values := checked x.values, nFeatures := x.nFeatures,
                      hasFeatureNames := false, isSparse := x.isSparse,
                      namesInspectable := true, contentAdmissible := true },
        refAfter := bif reset then {x.nFeatures, x.hasFeatureNames} else ref,
        refused  := (!reset) && (!x.namesInspectable || !x.contentAdmissible
                                 || (x.nFeatures != ref.nFeatures)),
        warned   := (!reset) && x.namesInspectable
                      && (ref.hasFeatureNames != x.hasFeatureNames) }

and the axioms region's

    axiom checked_idem : ∀ v, checked (checked v) = checked v

Fifteen legs, all exercised against the real callee (`BaseEstimator._validate_data`
/ `BaseEstimator._validate_params` / `check_array` / `score_samples` /
`_compute_chunked_score_samples` / `_get_feature_names` on a fitted
`IsolationForest`):

  W  `warned` — a feature-name-consistency warning is emitted iff this is a
     consistency re-check (reset=False) AND the carrier's name status DISAGREES
     with the record (fitted with names, carrier has none, or the reverse).
  R  `refused` — a re-check turns the carrier away iff its width disagrees with
     the record. Widths are VARIED independently of the fit width.
  A  `refAfter` — reset=True RE-DESCRIBES the record from the supplied carrier
     (`n_features_in_`, `feature_names_in_`); reset=False leaves it untouched.
  M  `carrier.hasFeatureNames := false` — what validation hands back carries no
     feature-name metadata, so a downstream re-check sees a nameless carrier.
  I  `checked_idem` — re-presenting content already in the accepted numeric form
     is a content no-op, so the payload after a second validation is bit-identical
     to the payload after the first.
  E  `ScoreOutcome.handedOn` is a whole CARRIER, and the carrier it names is the
     estimator's OWN presentation of the data rather than the caller's
     description of it. The model pins every field of that presentation, so every
     field is measured here: its width is the width that was presented, its
     storage form is the layout THIS step hands content back in (the dense
     direction here; the sparse directions are legs F and S), it advertises no
     feature-name metadata
     (leg M), its content is the re-presented content (leg I), and — the
     part a presentation asserts about ITSELF — it is a description the estimator
     would inspect and admit AGAIN: the label question is answered for it rather
     than raising, and re-presenting it to the admissibility check succeeds.
     The IN-LOOP CONTROL is the name-bearing carrier: where the caller's object
     DOES bear labels the two descriptions disagree, so the pinned
     `hasFeatureNames = false` is an answer the real callee could have given
     otherwise, and the count of such observations is reported. Legs L and D are
     the refuting controls for the other two halves: there ARE carriers the label
     inspection refuses to answer for and contents the admissibility check
     declines, so "inspectable and admissible" is not a property everything has.
     The observed value is the one the PATCHED entry point hands on: after the
     patch the public scoring entry point admits its argument and then calls the
     private, non-validating scoring routine, so the admissibility step's output
     IS the carrier that crosses. `_validate_data`, `check_array` and
     `_get_feature_names` are untouched by the patch, so this leg reads the same
     callee either side of it.
  H  `ScoreOutcome.handedOn`'s CONTENT — what the fitted estimator's public scoring entry
     point hands the fitted model is the payload the admissibility check
     RE-PRESENTED, not the caller's own object. Compared value-for-value against
     the scoring core applied to `check_array`'s output.
  C  `checked` is observably NOT the identity. The battery's conditioning
     witnesses assume exactly this (`checked v ≠ v` at a probed payload) and the
     bundle's one axiom deliberately does not supply it, so it is measured.
  P  NEGATIVE CONTROL for H. The collapsed reading — "the entry point hands on
     its own argument" — predicts that a raw nested Python list reaches the
     fitted model unchanged. It does not: the public entry point accepts such a
     payload and the scoring core REFUSES it, so the value that crosses is
     demonstrably the check's output. A leg no observation can refute is not
     grounding, which is why this one is here.
  S  `InputData.isSparse`, the carrier's STORAGE FORM, and the NEGATIVE
     CONTROL for it. The collapsed reading of `InputData` — two carriers of the
     same numeric content are one carrier — predicts one behaviour for a dense and
     a sparse presentation of the same numbers. The real callees give two: the
     fit-time admissibility check ADMITS sparse content and hands it back in the
     ONE sparse layout it accepts, while the scoring path the fitting tail uses,
     which performs no admissibility pass of its own, REFUSES content in that
     layout. The control is the dense
     presentation of the SAME numbers, which that path traverses without
     complaint — so the refusal is attributable to the form and not to the numbers
     or to a half-fitted model. Measured with estimators fitted on each form in
     turn, for the same reason.
  F  `InputData.form`, the carrier's storage form, is THREE-valued, and the
     layout a validation step hands content back in is a property of THAT STEP.
     A sparseness bit would say the two ends of the tail agree about sparse
     content; they do not, and the difference is observable, so it is measured
     rather than abstracted. Each end is asked for all three presentations of the
     same numbers: the end the public scoring entry point uses hands a sparse
     presentation back ROW-INDEXED whichever layout arrived, the end the fitting
     entry point uses hands the same presentations back COLUMN-INDEXED, and both
     leave a dense presentation dense. That is why `Form.reshaped` takes the
     accepted layout as an argument instead of preserving the arrived one.
     The NEGATIVE CONTROL is what makes the distinction load-bearing rather than
     cosmetic: the non-validating scoring path on the far side of the crossing is
     handed the same numbers in each sparse layout in turn and must TRAVERSE the
     row-indexed one and REFUSE the column-indexed one. So an entry point that
     converted and described its argument correctly and handed it on
     column-indexed would leave the fitted model unable to score it — the layout
     is not a free choice, and a model that could not see it would admit that
     entry point. Measured with estimators fitted on each of the three
     presentations, so the accepted layout is shown to be a property of the step
     rather than of the estimator's own history.
  N  NEGATIVE CONTROL for the model's deliberate limit. The collapsed reading of
     `InputData` — a carrier's labels do not matter, only whether it HAS labels —
     predicts one behaviour for a matched-label and a mismatched-label carrier of
     the same width and label kind. The real callee gives two: admitted, refused.
     Measured as a PAIR, so the contrast and not merely the refusal is on record.
  L  `InputData.namesInspectable`, and the NEGATIVE CONTROL for it. Deciding
     whether a carrier bears recordable feature names is not a total operation,
     and the model says so: the obligation is asked only of a carrier the
     estimator will INSPECT, and a carrier it will not is required to be turned
     away afterwards. Both halves are claims about `_get_feature_names` — the
     callee `hasFeatureNames` abstracts — so both are measured: presented with
     column labels of MIXED kinds it RAISES instead of reporting a status, so
     fitting on such a carrier leaves no estimator at all, and the fitted
     estimator's public scoring path turns such a carrier away whatever its width
     and whatever the estimator holds on record (measured with estimators fitted
     with and without names). The control is the SAME payload at the SAME width
     under HOMOGENEOUS labels, which that path reads and scores — so the refusal
     is attributable to the label kinds and not to the frame, the width or the
     numbers. Without that control, "the estimator turns such a carrier away"
     would be indistinguishable from "the estimator turns frames away".

  D  `InputData.contentAdmissible`, and the NEGATIVE CONTROL for it. Deciding
     that a carrier's CONTENT is admissible is not a total operation either, and
     it is a different partiality from the label one: the check re-presents the
     content, and there are contents it declines to re-present at all. The model
     says so in the same two directions as the label case — the obligation is
     asked only of a training carrier whose content the check ACCEPTS, and a later
     carrier whose content it does not is required to be turned away — so both
     directions are measured, at fit time and through the fitted estimator's
     public scoring path, over the three contents the check declines: content with
     no rows to describe, content with no columns to describe, and content holding
     a value that is not finite. The fit-time half also asserts that such a fit
     leaves NOTHING behind (neither the threshold nor the recorded width), which
     is what makes withholding the description there a domain limit rather than a
     weakening. The control is the ordinary finite content of the SAME width,
     which fits and scores — so the refusal is attributable to the content and not
     to the width, the labels or the estimator. The three contents are also
     measured to be INSPECTABLE (they are bare arrays: the label question is
     answered for them, and answered "no names"), which is what shows this leg is
     not leg L again under another name.

  V  The CONFIGURED THRESHOLD LEVEL's own domain — the spec's `levelAdmitted`
     precondition — and the NEGATIVE CONTROL for it. The level is a bare `Float`
     in the model, so the description would otherwise be making claims about
     levels the real estimator never works with: it DECLARES that parameter as
     either the unconfigured marker or a level in a bounded interval and validates
     it as the first thing fitting does. Both directions are measured, at every
     level the battery configures and at levels outside the declared interval
     including both endpoints, and each observation reads four things rather than
     one — whether the fit raised (and, when it did, whether it raised about THAT
     parameter), whether it left a threshold and a recorded width behind, HOW MANY
     times it traversed the training payload (the count C8 pins, read by
     instrumenting the chunked scoring routine the model's traversal node stands
     for), and whether the estimator it left behind can score at all. At an
     admitted level: no raise, both attributes present, exactly one traversal,
     scores. At a refused one: raises about the parameter, nothing left behind,
     ZERO traversals, no scoring. The levels the battery configures are the
     refuting control for the levels outside the interval — a leg where everything
     raised would be indistinguishable from "this estimator never fits" — and the
     boundary pair (the open lower endpoint refused, the closed upper endpoint
     admitted) is read on every trial. The leg also measures the ORDER the
     precondition is stated in, as a contrast: presented with a refused level over
     content the admissibility check declines, the estimator complains about the
     PARAMETER, while the same content at an admitted level complains about the
     CONTENT — which is what shows the parameter validation runs before the
     estimator looks at a carrier at all, and not merely that it runs.

VACUITY IS A FAILURE. Every leg's observation count is printed and a leg that
fired zero times fails the probe, as does a zero count for either negative
control: a leg that never ran asserts nothing about the real callee.

It also RECORDS, through leg N and the `names_differ` branch, the model's
deliberate limit (refinement.md, "name PRESENCE, not name IDENTITY"): where BOTH
the record and the carrier bear names AND the names disagree, the real callee
RAISES. Those configurations are asserted to raise
rather than compared against the model, and the count is reported — this is the
machine-checked basis for the guards on the spec's two admission clauses.

Metadata note: a DataFrame whose columns are all NON-strings is one whose labels
the estimator declines to treat as names (it records no `feature_names_in_`), the
`hasFeatureNames = false` image in mapping.md; that case is exercised too. A
DataFrame whose columns MIX the two is a different thing entirely and is NOT that
image — the estimator does not answer the question there, it raises — which is
what `namesInspectable = false` stands for and what leg L measures.

stdlib + repo deps (numpy/pandas/sklearn, present in the eval image). exit 0 iff
every leg matches the real callee on every observation.
"""
import sys
import warnings

import numpy as np
import scipy.sparse as sp

try:
    import pandas as pd
except Exception as e:  # pragma: no cover
    print(f"G-AX skip: pandas unavailable ({e})", file=sys.stderr)
    sys.exit(0)

from sklearn.ensemble import IsolationForest
from sklearn.utils.validation import check_array

try:
    from sklearn.utils.validation import _get_feature_names
except Exception:                                          # pragma: no cover
    _get_feature_names = None

SEED = 25931            # pinned in mapping.md / meta.json verifier_pins.ax_seed

# Column-label kinds and whether the estimator admits them AS feature names.
#   None      -> a bare ndarray: no names
#   "str"     -> string columns: names recorded
#   "int"     -> integer columns: labels the estimator declines to treat as names
LABEL_KINDS = (None, "str", "int")

# Leg V. The CONFIGURED threshold levels the specification's precondition assumes
# the estimator admits: every `contamination` literal a configured-lane witness in
# properties.py stands at (twelve of them), plus 0.25 — which the battery uses on
# the UNCONFIGURED lane, where the model's precondition says nothing — and the
# declared interval's closed upper endpoint.
ADMITTED_LEVELS = (0.05, 0.1, 0.15, 0.2, 0.22, 0.25, 0.28, 0.3, 0.35, 0.4,
                   0.42, 0.45, 0.5)
# Levels outside the declared interval, which is what makes leg V discriminating
# rather than a restatement of "IsolationForest fits". The open lower endpoint and
# the first value above the closed upper one are both here, so the leg reads the
# boundary itself and not only values far from it. 0.6, 0.65 and 0.75 are the
# Floats the battery's UNCONFIGURED-lane witnesses carry alongside the
# unconfigured marker: as CONFIGURED levels the estimator refuses them, which is
# exactly why the model's precondition is an implication over the branch selector
# rather than a constraint on the binder.
REFUSED_LEVELS = (0.0, -0.2, 0.55, 0.6, 0.65, 0.7, 0.75, 0.9, 1.5,
                  float("nan"), float("inf"))


def labels_for(kind, width, tag="c"):
    if kind is None:
        return None
    if kind == "int":
        return list(range(width))
    return [f"{tag}{i}" for i in range(width)]


def admits_names(kind):
    """Model image of a label kind: `InputData.hasFeatureNames`."""
    return kind == "str"


def carrier(data, kind, tag="c"):
    labels = labels_for(kind, data.shape[1], tag)
    if labels is None:
        return data
    return pd.DataFrame(data, columns=labels)


DENSE, BY_ROW, BY_COLUMN = "dense", "sparseByRow", "sparseByColumn"


def layout_of(x):
    """Model image of a carrier's STORAGE FORM: `InputData.form`, three-valued.

    Anything not sparse is dense; a sparse carrier is named by WHICH index it
    carries, because the scoring path is partial on exactly that.
    """
    if not sp.issparse(x):
        return DENSE
    fmt = getattr(x, "format", None)
    if fmt == "csr":
        return BY_ROW
    if fmt == "csc":
        return BY_COLUMN
    return f"sparse:{fmt}"


def reshaped(arrived, accepted):
    """`Form.reshaped`: a dense carrier stays dense, a sparse one comes back in
    whichever sparse layout the step it reached accepts."""
    return DENSE if arrived == DENSE else accepted


def presented(data, form):
    """The same numbers in one of the three storage forms."""
    if form == BY_ROW:
        return sp.csr_matrix(data)
    if form == BY_COLUMN:
        return sp.csc_matrix(data)
    return data


def layout_control(clf, data):
    """Leg F: which layout each end of the tail hands content back in, and the
    control that the two are not interchangeable.

    Returns (score_side, fit_side, core_traversed_row, core_refused_column),
    where the first two map each presented form to the form handed back.
    """
    score_side = {}
    fit_side = {}
    for form in (DENSE, BY_ROW, BY_COLUMN):
        x = presented(data, form)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            score_side[form] = layout_of(clf._validate_data(
                x, accept_sparse="csr", dtype=np.float32, reset=False))
        fit_side[form] = layout_of(check_array(
            x, accept_sparse=["csc"], dtype=np.float32))
    by_row = check_array(sp.csr_matrix(data), accept_sparse="csr",
                         dtype=np.float32)
    by_col = check_array(sp.csc_matrix(data), accept_sparse=["csc"],
                         dtype=np.float32)
    traversed = True
    try:
        clf._compute_chunked_score_samples(by_row)
    except Exception:
        traversed = False
    refused = False
    try:
        clf._compute_chunked_score_samples(by_col)
    except Exception:
        refused = True
    return score_side, fit_side, traversed, refused


def is_consistency_warning(message):
    """The feature-name-CONSISTENCY diagnostic, as distinct from the
    "names must all be strings" notice the metadata check emits at fit time."""
    m = str(message)
    return ("fitted with feature names" in m
            or "fitted without feature names" in m)


def fresh(data, kind):
    """A freshly fitted estimator whose record comes from this carrier."""
    clf = IsolationForest(random_state=0, n_estimators=3, contamination="auto")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf.fit(carrier(data, kind))
    return clf


def record_of(clf):
    """The `Reference` the estimator holds: (nFeatures, hasFeatureNames)."""
    return (int(clf.n_features_in_), bool(hasattr(clf, "feature_names_in_")))


def observe(clf, x, reset):
    """One real `_validate_data` observation: (refused, warned, record_after,
    out_payload, name_identity_raise)."""
    refused = False
    identity = False
    out = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            out = clf._validate_data(x, accept_sparse="csr",
                                     dtype=np.float32, reset=reset)
        except ValueError as exc:
            refused = True
            identity = "feature names should match" in str(exc)
    warned = any(is_consistency_warning(w.message) for w in caught)
    return refused, warned, record_of(clf), out, identity


def name_identity_control(clf, fit_width):
    """Leg N: the PAIR that refutes the collapsed reading of `InputData`.

    Two carriers of the same width, the same payload and the same label KIND,
    differing only in the labels themselves. A model that records label PRESENCE
    alone maps both to one value and so must predict one behaviour; the real
    callee admits the matched one and turns the mismatched one away. Returns
    (admitted_matched, refused_mismatched, raised_on_name_identity).
    """
    body = np.round(np.full((3, fit_width), 0.25), 4)
    matched = pd.DataFrame(body, columns=labels_for("str", fit_width, "c"))
    mismatched = pd.DataFrame(body, columns=labels_for("str", fit_width, "q"))
    refused_matched = observe(clf, matched, reset=False)[0]
    refused_mismatched, _w, _a, _o, identity = observe(clf, mismatched,
                                                       reset=False)
    return (not refused_matched), refused_mismatched, identity


def mixed_labels(width, tag="c"):
    """Column labels of MIXED kinds: some strings, some not.

    This is the label shape the estimator cannot answer about — not a shape it
    answers "no names" to. Needs at least two columns to exist at all, which is
    why leg L runs at widths >= 2.
    """
    labels = [f"{tag}{i}" for i in range(width)]
    labels[-1] = width - 1                       # one non-string label
    return labels


def label_inspection_control(clf, fit_width, body):
    """Leg L: whether the estimator can INSPECT a carrier's labels, plus the
    control that the inspection is what decides.

    Three observations at ONE width over ONE payload, differing only in the
    column labels:
      * mixed labels  -> the label inspection itself raises, so the carrier
        cannot be given a feature-name status at all;
      * mixed labels through the fitted estimator's PUBLIC scoring path -> the
        carrier is turned away (the model's `refused = true`), at the TRAINING
        width, so a width check cannot be what turned it away;
      * homogeneous labels, same payload, same width -> read and scored (the
        NEGATIVE CONTROL: this is what makes the refusal attributable to the
        labels rather than to the frame or the numbers).
    Returns (inspection_raised, entry_refused, control_scored, control_read).
    """
    mixed = pd.DataFrame(body, columns=mixed_labels(fit_width))
    plain = pd.DataFrame(body, columns=labels_for("str", fit_width, "c"))

    inspection_raised = False
    if _get_feature_names is not None:
        try:
            _get_feature_names(mixed)
        except TypeError:
            inspection_raised = True

    entry_refused = False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            clf.score_samples(mixed)
    except TypeError:
        entry_refused = True

    control_scored = False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = clf.score_samples(plain)
        control_scored = np.asarray(out).shape[0] == body.shape[0]
    except Exception:
        control_scored = False

    control_read = True
    if _get_feature_names is not None:
        try:
            control_read = _get_feature_names(plain) is not None
        except Exception:
            control_read = False
    return inspection_raised, entry_refused, control_scored, control_read


def fit_on_uninspectable(width, body):
    """Leg L, the precondition half: fitting on a carrier whose labels cannot be
    inspected leaves no fitted estimator to describe. Returns
    (fit_raised, control_fitted)."""
    mixed = pd.DataFrame(body, columns=mixed_labels(width))
    plain = pd.DataFrame(body, columns=labels_for("str", width, "c"))
    raised = False
    clf = IsolationForest(random_state=0, n_estimators=3, contamination=0.25)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            clf.fit(mixed)
    except TypeError:
        raised = True
    left_behind = hasattr(clf, "offset_")
    ctl = IsolationForest(random_state=0, n_estimators=3, contamination=0.25)
    fitted = False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ctl.fit(plain)
        fitted = hasattr(ctl, "offset_")
    except Exception:
        fitted = False
    return raised, left_behind, fitted


def payload_provenance(clf, rows):
    """Leg P: the negative control for what the entry point hands on.

    A raw nested Python list is a payload the admissibility check CONVERTS and
    the scoring core cannot consume. So if the public entry point accepts it and
    the scoring core refuses it, the value that crossed into the fitted model was
    the check's output and not the caller's object -- which is what
    `ScoreOutcome.handedOn = checked z.values` says. Returns
    (entry_point_accepted, scoring_core_refused).
    """
    raw = [[float(v) for v in row] for row in rows]
    accepted = True
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            clf.score_samples(raw)
    except Exception:
        accepted = False
    core_refused = False
    try:
        clf._compute_chunked_score_samples(raw)
    except Exception:
        core_refused = True
    return accepted, core_refused


def storage_form_control(clf, data):
    """Leg S: the storage-form distinction the model carries, and its control.

    `validateInput` hands its caller a carrier whose `isSparse` is the one it was
    given, and `fitCompletes` reads that field to say where the fitting tail runs
    to a result at all. Both are claims about the real callees, so both are
    measured here: what the fit-time check does to the storage form, and what the
    non-validating scoring path does with the result. Returns
    (check_kept_sparse, check_kept_dense, core_refused_sparse,
    core_accepted_dense).
    """
    x_dense = check_array(data, accept_sparse=["csc"], dtype=np.float32)
    x_sparse = check_array(sp.csc_matrix(data), accept_sparse=["csc"],
                           dtype=np.float32)
    refused = False
    try:
        clf._compute_chunked_score_samples(x_sparse)
    except Exception:
        refused = True
    dense_ok = True
    try:
        clf._compute_chunked_score_samples(x_dense)
    except Exception:
        dense_ok = False
    return (sp.issparse(x_sparse), not sp.issparse(x_dense), refused, dense_ok)


def inadmissible_contents(width, body):
    """The three CONTENTS the estimator's admissibility check declines, at one
    width and over one ordinary payload.

    None of the three is a label question: each is a bare array, so the label
    inspection answers about all of them (and answers "no names"). They are
    contents the re-presentation step itself will not perform.
    """
    nonfinite = np.array(body, dtype=np.float64)
    nonfinite[0, 0] = np.nan
    return {
        "no rows": np.zeros((0, width), dtype=np.float64),
        "no columns": np.zeros((body.shape[0], 0), dtype=np.float64),
        "not finite": nonfinite,
    }


def content_admissibility_control(width, body, fit_kind):
    """Leg D: the CONTENT domain of the admissibility check, in both directions,
    with the ordinary content of the same width as the negative control.

    Returns (per_content, control_fitted, control_scored) where `per_content`
    maps each declined content to
    (fit_raised, fit_left_something_behind, entry_refused, inspectable).
    """
    ctl = fresh(body, fit_kind)
    control_fitted = hasattr(ctl, "offset_") and hasattr(ctl, "n_features_in_")
    control_scored = False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = ctl.score_samples(np.asarray(body))
        control_scored = np.asarray(out).shape[0] == body.shape[0]
    except Exception:
        control_scored = False

    per_content = {}
    for name, bad in inadmissible_contents(width, body).items():
        est = IsolationForest(random_state=0, n_estimators=3,
                             contamination=0.25)
        fit_raised = False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                est.fit(bad)
        except ValueError:
            fit_raised = True
        left_behind = (hasattr(est, "offset_")
                       or hasattr(est, "n_features_in_"))
        entry_refused = False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ctl.score_samples(bad)
        except ValueError:
            entry_refused = True
        inspectable = True
        if _get_feature_names is not None:
            try:
                inspectable = _get_feature_names(bad) is None
            except Exception:
                inspectable = False
        per_content[name] = (fit_raised, left_behind, entry_refused,
                             inspectable)
    return per_content, control_fitted, control_scored


def _traversal_counter():
    """Count the fitted model's scoring traversals of the training payload.

    C8 reads the traversals off the modeled program's STRUCTURE, so what the real
    code spends at a level its parameter validation refuses has to be counted
    rather than inferred. The chunked scoring routine is the traversal the model's
    `Fitting.traverse` node stands for, and a run that never reaches it performs
    none.

    Returns (box, restore); `box["n"]` is the count.
    """
    from sklearn.ensemble import _iforest as _if

    orig = getattr(IsolationForest, "_compute_chunked_score_samples", None)
    box = {"n": 0, "available": orig is not None}
    if orig is None:                                       # pragma: no cover
        return box, (lambda: None)

    def counted(self, X):
        box["n"] += 1
        return orig(self, X)

    IsolationForest._compute_chunked_score_samples = counted
    _if.IsolationForest._compute_chunked_score_samples = counted

    def restore():
        IsolationForest._compute_chunked_score_samples = orig
        _if.IsolationForest._compute_chunked_score_samples = orig

    return box, restore


def parameter_domain(level, body):
    """Leg V at one configured threshold level: what the real estimator does.

    Returns (raised, message, fitted, traversals, scored, counted_available).
    """
    est = IsolationForest(random_state=0, n_estimators=3, contamination=level)
    box, restore = _traversal_counter()
    raised, message = False, ""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            est.fit(body)
    except ValueError as e:        # InvalidParameterError is a ValueError
        raised, message = True, str(e)
    finally:
        restore()
    fitted = hasattr(est, "offset_") and hasattr(est, "n_features_in_")
    scored = False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = est.score_samples(body)
        scored = np.asarray(out).shape[0] == body.shape[0]
    except Exception:
        scored = False
    return raised, message, fitted, box["n"], scored, box["available"]


def validation_order_control(body):
    """Leg V's ORDERING half, as a contrast rather than a single reading.

    The model's precondition comes FIRST because the estimator validates its
    configured parameters before it looks at a carrier at all. Presented with a
    refused level AND content the admissibility check declines, the real estimator
    must therefore complain about the PARAMETER; presented with the same content
    at an admitted level it must complain about the CONTENT. Reading only the
    first of those would not distinguish "the parameter is checked first" from
    "the parameter is checked at all".

    Returns {"refused": message-or-None, "admitted": message-or-None}.
    """
    bad = np.array(body, dtype=np.float64)
    bad[0, 0] = np.nan
    out = {}
    for tag, level in (("refused", 0.9), ("admitted", 0.25)):
        est = IsolationForest(random_state=0, n_estimators=3,
                              contamination=level)
        msg = None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                est.fit(bad)
        except ValueError as e:
            msg = str(e)
        out[tag] = msg
    return out


def main() -> int:                                     # noqa: C901
    rng = np.random.RandomState(SEED)
    checks = 0
    failures = 0
    identity_limit = 0
    nonidentity = 0
    content_seen = 0
    legs = {"W": 0, "R": 0, "A": 0, "M": 0, "I": 0, "E": 0,
            "H": 0, "C": 0, "P": 0, "N": 0, "S": 0, "F": 0, "L": 0,
            "D": 0, "V": 0}
    uninspectable = 0
    described_differently = 0
    layout_obs = 0
    layout_ctl = 0
    levels_admitted = 0
    levels_refused = 0

    def fail(msg):
        nonlocal failures
        failures += 1
        if failures <= 12:
            print("MISMATCH " + msg, file=sys.stderr)

    for trial in range(6):
        n = int(rng.randint(4, 12))
        for fit_width in (1, 2, 3):
            # payloads that are NOT float32-exact, so `checked` is observable
            data = np.round(rng.randn(n, fit_width), 4).astype(np.float64)
            data[0, 0] = 0.1
            for fit_kind in LABEL_KINDS:
                ref_model = (fit_width, admits_names(fit_kind))

                # --- leg A (reset=True) and the fit-time record itself
                clf = fresh(data, fit_kind)
                checks += 1
                legs["A"] += 1
                if record_of(clf) != ref_model:
                    fail(f"fit record: model={ref_model} "
                         f"real={record_of(clf)} fit_kind={fit_kind}")

                # --- leg N: the matched/mismatched label PAIR
                if fit_kind == "str":
                    checks += 1
                    legs["N"] += 1
                    ok_matched, refused_mismatched, ident = \
                        name_identity_control(clf, fit_width)
                    if not ok_matched:
                        fail("a carrier whose labels MATCH the record was "
                             f"refused (fit_width={fit_width})")
                    if not (refused_mismatched and ident):
                        fail("a carrier whose labels DIFFER from the record at "
                             "the same width and kind was not turned away on "
                             f"name identity (fit_width={fit_width}); the "
                             "model's deliberate limit would then be spurious")

                for chk_width in (1, 2, 3):
                    cdata = np.round(rng.randn(3, chk_width), 4).astype(np.float64)
                    for chk_kind in LABEL_KINDS:
                        for same_names in (True, False):
                            tag = "c" if same_names else "q"
                            x = carrier(cdata, chk_kind, tag)
                            x_names = admits_names(chk_kind)
                            names_differ = (
                                admits_names(fit_kind) and x_names
                                and (labels_for(chk_kind, chk_width, tag)
                                     != labels_for(fit_kind, fit_width, "c")))

                            # ---- reset=False: refused / warned / refAfter
                            refused, warned, after, out, identity = observe(
                                clf, x, reset=False)
                            checks += 1
                            if names_differ:
                                # documented model limit: must be a refusal
                                identity_limit += 1
                                if not refused:
                                    fail("name-identity disagreement did not "
                                         f"refuse: fit={fit_kind}/{fit_width} "
                                         f"chk={chk_kind}/{chk_width}")
                                if after != ref_model:
                                    fail(f"refAfter after refusal: "
                                         f"model={ref_model} real={after}")
                                continue
                            legs["R"] += 1
                            legs["W"] += 1
                            legs["A"] += 1
                            want_refused = (chk_width != fit_width)
                            want_warned = (ref_model[1] != x_names)
                            if refused != want_refused:
                                fail(f"refused: model={want_refused} "
                                     f"real={refused} fit={fit_kind}/{fit_width}"
                                     f" chk={chk_kind}/{chk_width}")
                            if not refused and warned != want_warned:
                                fail(f"warned: model={want_warned} "
                                     f"real={warned} fit={fit_kind} "
                                     f"chk={chk_kind}")
                            if after != ref_model:
                                fail("reset=False re-described the record: "
                                     f"model={ref_model} real={after}")
                            if refused:
                                continue

                            # ---- leg M: the returned carrier bears no names
                            if _get_feature_names is not None:
                                checks += 1
                                legs["M"] += 1
                                if _get_feature_names(out) is not None:
                                    fail("validation handed back a carrier that "
                                         "still bears feature names")

                            # ---- leg E: the presentation DESCRIBES ITSELF as
                            # the estimator's own, not as the caller's object.
                            # The model's handed-on carrier pins all six fields;
                            # `values` is leg I below and `hasFeatureNames` is
                            # leg M above, so what is left is the width, the
                            # storage form, and whether the presentation is one
                            # the estimator would inspect and admit AGAIN.
                            checks += 1
                            legs["E"] += 1
                            if int(np.asarray(out).shape[1]) != chk_width:
                                fail("validation handed back a carrier of a "
                                     f"different width: model={chk_width} "
                                     f"real={np.asarray(out).shape[1]}")
                            if layout_of(out) != reshaped(layout_of(x), BY_ROW):
                                fail("validation handed back a carrier in a "
                                     "storage form the model does not predict "
                                     f"(in={layout_of(x)} "
                                     f"out={layout_of(out)})")
                            # inspectable AGAIN: the label question is answered
                            # for the presentation rather than raising on it.
                            if _get_feature_names is not None:
                                try:
                                    _get_feature_names(out)
                                except Exception as exc:
                                    fail("the presentation validation handed "
                                         "back is one the label inspection "
                                         f"refuses to answer for: {exc!r}")
                            # admissible AGAIN: re-presenting it is accepted.
                            try:
                                check_array(out, accept_sparse="csr",
                                            dtype=np.float32)
                            except Exception as exc:
                                fail("the presentation validation handed back "
                                     "is content its own admissibility check "
                                     f"declines: {exc!r}")
                            # IN-LOOP CONTROL for the label field: where the
                            # caller's object bears names, the two descriptions
                            # differ, so `hasFeatureNames := false` is an answer
                            # the real callee could have given otherwise.
                            if x_names:
                                described_differently += 1
                                if (_get_feature_names is not None
                                        and _get_feature_names(x) is None):
                                    fail("a name-bearing carrier was read as "
                                         "nameless, so this control cannot "
                                         "separate the presentation's "
                                         "description from the caller's")

                            # ---- leg I: checked_idem, on the real callee
                            checks += 1
                            legs["I"] += 1
                            once = check_array(np.asarray(x if chk_kind is None
                                                          else x.to_numpy()),
                                               accept_sparse="csr",
                                               dtype=np.float32)
                            twice = check_array(once, accept_sparse="csr",
                                                dtype=np.float32)
                            if not (once.shape == twice.shape
                                    and np.array_equal(once, twice)
                                    and once.dtype == twice.dtype):
                                fail("checked_idem: re-presenting an already "
                                     "converted payload changed its content")
                            # and the payload validation hands on IS that form
                            if not np.array_equal(np.asarray(out), once):
                                fail("carrier.values != checked x.values")

                            # ---- leg C: `checked` is observably not identity
                            raw = np.asarray(x if chk_kind is None
                                             else x.to_numpy(),
                                             dtype=np.float64)
                            checks += 1
                            legs["C"] += 1
                            if not np.array_equal(raw, once):
                                nonidentity += 1

                            # ---- leg H: what the entry point hands the model
                            checks += 1
                            legs["H"] += 1
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                entry = clf.score_samples(x)
                            via_checked = -clf._compute_chunked_score_samples(
                                once)
                            if not np.array_equal(np.asarray(entry),
                                                  np.asarray(via_checked)):
                                fail("the public scoring entry point did not "
                                     "hand the fitted model the payload the "
                                     "admissibility check re-presented")

                            # ---- leg A (reset=True re-describes from x)
                            clf2 = fresh(data, fit_kind)
                            _r2, w2, after2, _o2, _i2 = observe(clf2, x,
                                                                reset=True)
                            checks += 1
                            legs["A"] += 1
                            want_after2 = (chk_width, x_names)
                            if after2 != want_after2:
                                fail(f"reset=True refAfter: model={want_after2}"
                                     f" real={after2}")
                            if w2:
                                fail("reset=True emitted a consistency warning")

    # ---- leg L: label INSPECTABILITY, both halves, with the homogeneous-label
    # ---- carrier as the negative control on every observation
    for fit_width in (2, 3, 4):
        body = np.round(rng.randn(4, fit_width), 4).astype(np.float64)
        for fit_kind in ("str", "int", None):
            clf = fresh(body, fit_kind)
            checks += 1
            legs["L"] += 1
            uninspectable += 1
            raised, entry_refused, ctl_scored, ctl_read = \
                label_inspection_control(clf, fit_width, body)
            if _get_feature_names is not None and not raised:
                fail("the label inspection RETURNED a status for labels of mixed "
                     "kinds, so a carrier the estimator cannot answer about would "
                     f"not exist (fit={fit_kind}/{fit_width})")
            if not entry_refused:
                fail("the fitted estimator's public scoring path did NOT turn "
                     "away a carrier whose labels it cannot inspect, at the "
                     "training width — so requiring that refusal would be "
                     f"over-strength (fit={fit_kind}/{fit_width})")
            if not ctl_scored:
                fail("that same path refused the HOMOGENEOUSLY labelled carrier "
                     "of the same payload at the same width, so this control "
                     "cannot attribute the refusal to the label kinds "
                     f"(fit={fit_kind}/{fit_width})")
            if fit_kind == "str" and not ctl_read:
                fail("the label inspection could not read homogeneous string "
                     "labels, so the control is not a control "
                     f"(fit={fit_kind}/{fit_width})")

        # the precondition half: such a fit leaves nothing behind to describe
        checks += 1
        legs["L"] += 1
        fit_raised, left_behind, ctl_fitted = fit_on_uninspectable(
            fit_width, body)
        if not fit_raised:
            fail("fitting on a carrier whose labels cannot be inspected did NOT "
                 "raise, so withholding the description there would be a "
                 f"weakening rather than a domain limit (width={fit_width})")
        if left_behind:
            fail("that fit left a threshold behind, so there WOULD be something "
                 f"for the description to describe (width={fit_width})")
        if not ctl_fitted:
            fail("the homogeneously labelled control fit produced no threshold "
                 f"either, so this control attributes nothing (width={fit_width})")

    # ---- leg D: the CONTENT domain of the admissibility check, both halves,
    # ---- with the ordinary content of the same width as the negative control
    for fit_width in (1, 2, 3):
        body = np.round(rng.randn(4, fit_width), 4).astype(np.float64)
        for fit_kind in ("str", None):
            checks += 1
            legs["D"] += 1
            per_content, ctl_fitted, ctl_scored = \
                content_admissibility_control(fit_width, body, fit_kind)
            if not ctl_fitted:
                fail("the control fit on ORDINARY content of the same width "
                     "produced no threshold and no recorded width, so this leg's "
                     f"contrast attributes nothing (fit={fit_kind}/{fit_width})")
            if not ctl_scored:
                fail("the fitted estimator's public scoring path refused the "
                     "ordinary content of the training width, so the control "
                     f"cannot separate content from width (fit={fit_kind}/{fit_width})")
            for name, (fit_raised, left_behind, entry_refused, inspectable) \
                    in per_content.items():
                content_seen += 1
                if not fit_raised:
                    fail("fitting on content the admissibility check declines "
                         f"({name}) did NOT raise, so withholding the "
                         "description there would be a weakening rather than a "
                         f"domain limit (fit={fit_kind}/{fit_width})")
                if left_behind:
                    fail(f"that fit ({name}) left a threshold or a recorded "
                         "width behind, so there WOULD be something for the "
                         f"description to describe (fit={fit_kind}/{fit_width})")
                if not entry_refused:
                    fail("the fitted estimator's public scoring path did NOT "
                         f"turn away content the check declines ({name}), so "
                         "requiring that refusal would be over-strength "
                         f"(fit={fit_kind}/{fit_width})")
                if not inspectable:
                    fail(f"the declined content ({name}) is one the label "
                         "inspection cannot answer about either, so this "
                         "observation does not separate the content ground from "
                         f"the label ground (fit={fit_kind}/{fit_width})")

    # ---- leg P: the negative control for the handed-on payload
    for fit_width in (1, 2, 3):
        data = np.round(rng.randn(5, fit_width), 4).astype(np.float64)
        clf = fresh(data, None)
        rows = np.round(rng.randn(3, fit_width), 4)
        checks += 1
        legs["P"] += 1
        accepted, core_refused = payload_provenance(clf, rows)
        if not accepted:
            fail("the public scoring entry point refused a payload its own "
                 "admissibility check converts")
        if not core_refused:
            fail("the scoring core accepted the caller's raw payload, so this "
                 "control cannot separate handing on the check's output from "
                 "handing on the argument")

    # ---- leg S: the storage form, and the control that the form is what decides
    for fit_width in (2, 3):
        data = np.round(rng.randn(9, fit_width), 4).astype(np.float64)
        for fit_form in ("dense", "sparse"):
            clf = IsolationForest(random_state=0, n_estimators=3,
                                  contamination="auto")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                clf.fit(sp.csc_matrix(data) if fit_form == "sparse" else data)
            checks += 1
            legs["S"] += 1
            kept_sparse, kept_dense, refused, dense_ok = \
                storage_form_control(clf, data)
            if not kept_sparse:
                fail("the fit-time admissibility check did not hand a sparse "
                     "carrier back in a sparse form, so carrying the storage "
                     f"form through validation would be wrong (fit={fit_form})")
            if not kept_dense:
                fail("the fit-time admissibility check turned a dense carrier "
                     f"into a sparse one (fit={fit_form})")
            if not refused:
                fail("the scoring path the fitting tail uses ACCEPTED content in "
                     "the form the check hands a sparse carrier back in, so the "
                     "storage-form distinction the model carries would be "
                     f"spurious (fit={fit_form})")
            if not dense_ok:
                fail("that same path refused the DENSE presentation of the same "
                     "numbers, so this control cannot attribute the refusal to "
                     f"the storage form (fit={fit_form})")

    # ---- leg F: WHICH sparse layout each end hands back, and the control that
    # the layout the entry point did NOT hand on is one the core refuses
    want_score = {DENSE: DENSE, BY_ROW: BY_ROW, BY_COLUMN: BY_ROW}
    want_fit = {DENSE: DENSE, BY_ROW: BY_COLUMN, BY_COLUMN: BY_COLUMN}
    for fit_width in (2, 3):
        data = np.round(rng.randn(9, fit_width), 4).astype(np.float64)
        for fit_form in (DENSE, BY_ROW, BY_COLUMN):
            clf = IsolationForest(random_state=0, n_estimators=3,
                                  contamination="auto")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                clf.fit(presented(data, fit_form))
            checks += 1
            legs["F"] += 1
            score_side, fit_side, traversed, refused = layout_control(clf, data)
            for arrived in (DENSE, BY_ROW, BY_COLUMN):
                layout_obs += 1
                if score_side[arrived] != want_score[arrived]:
                    fail("the step the public scoring entry point uses handed a "
                         f"{arrived} presentation back as "
                         f"{score_side[arrived]}, not {want_score[arrived]} "
                         f"(fit={fit_form})")
                if fit_side[arrived] != want_fit[arrived]:
                    fail("the step the fitting entry point uses handed a "
                         f"{arrived} presentation back as "
                         f"{fit_side[arrived]}, not {want_fit[arrived]} "
                         f"(fit={fit_form})")
            if not traversed:
                fail("the scoring path the fitting tail uses REFUSED the layout "
                     "the public scoring entry point hands content on in, so a "
                     "carrier could not cross into the fitted model at all "
                     f"(fit={fit_form})")
            if not refused:
                fail("that same path ACCEPTED the other sparse layout too, so "
                     "which layout the entry point hands on would not be "
                     f"observable and the model would not need to say (fit="
                     f"{fit_form})")
            layout_ctl += 1
    # ---- leg V: the configured threshold LEVEL's own domain, in both
    # ---- directions, with the levels the battery configures as the control
    for fit_width in (2, 3):
        body = np.round(rng.randn(6, fit_width), 4).astype(np.float64)
        for level in ADMITTED_LEVELS:
            checks += 1
            legs["V"] += 1
            levels_admitted += 1
            raised, msg, fitted, traversals, scored, counted = \
                parameter_domain(level, body)
            if not counted:
                fail("the scoring routine the model's traversal node stands for "
                     "is not present on this estimator, so the traversal count "
                     f"cannot be read (level={level})")
            if raised:
                fail("the parameter validation REFUSED a level the description "
                     f"assumes it admits ({level}): {msg[:120]}")
            if not fitted:
                fail(f"fitting at level {level} left no threshold and no "
                     "recorded width behind, so the description would be about "
                     f"a run that does not happen (width={fit_width})")
            if traversals != 1:
                fail(f"fitting at level {level} traversed the training payload "
                     f"{traversals} times, not once, so C8's count would be "
                     f"wrong on the configured branch (width={fit_width})")
            if not scored:
                fail(f"the estimator fitted at level {level} would not score "
                     f"its own training payload (width={fit_width})")
        for level in REFUSED_LEVELS:
            checks += 1
            legs["V"] += 1
            levels_refused += 1
            raised, msg, fitted, traversals, scored, _c = \
                parameter_domain(level, body)
            if not raised:
                fail(f"the parameter validation ADMITTED the level {level}, "
                     "outside the declared interval, so the precondition the "
                     "description carries would be narrowing a domain the real "
                     f"estimator serves (width={fit_width})")
            elif "contamination" not in msg:
                fail(f"fitting at level {level} raised about something other "
                     f"than that parameter, so this observation does not "
                     f"attribute the refusal to the level: {msg[:120]}")
            if fitted:
                fail(f"fitting at the refused level {level} left a threshold or "
                     "a recorded width behind, so there WOULD be something for "
                     f"the description to describe (width={fit_width})")
            if traversals:
                fail(f"fitting at the refused level {level} still traversed the "
                     f"training payload {traversals} times, so withholding C8 "
                     f"there would be a weakening (width={fit_width})")
            if scored:
                fail(f"the estimator left behind at the refused level {level} "
                     "scored a payload, so the run did leave a usable model "
                     f"behind (width={fit_width})")

        # the ORDERING half: the parameter validation runs BEFORE the estimator
        # looks at the carrier, which is why the model's precondition comes first
        checks += 1
        legs["V"] += 1
        order = validation_order_control(body)
        if order["refused"] is None:
            fail("a refused level over content the admissibility check declines "
                 f"did not raise at all (width={fit_width})")
        elif "contamination" not in order["refused"]:
            fail("a refused level over content the check declines raised about "
                 "the CONTENT, so the parameter validation does not come first "
                 f"and the precondition's order would be wrong (width={fit_width})")
        if order["admitted"] is None:
            fail("the same declined content at an ADMITTED level did not raise, "
                 "so this control cannot separate the two grounds "
                 f"(width={fit_width})")
        elif "contamination" in order["admitted"]:
            fail("the same declined content at an ADMITTED level still raised "
                 "about the parameter, so the ordering reading attributes "
                 f"nothing (width={fit_width})")

    # A leg that never fired asserts nothing about the real callee, and a
    # negative control that never fired cannot show the leg it guards is
    # discriminating. Either way the probe would report success while testing
    # less than it claims, so both are failures here rather than a footnote.
    vacuous = [k for k, v in legs.items() if v == 0]
    if identity_limit == 0:
        vacuous.append("name-identity refusals")
    if nonidentity == 0:
        vacuous.append("re-presentation non-identity (leg C never differed)")
    if uninspectable == 0:
        vacuous.append("carriers whose labels the estimator cannot inspect")
    if content_seen == 0:
        vacuous.append("contents the admissibility check declines")
    if layout_obs == 0:
        vacuous.append("the layout each end of the tail hands content back in "
                       "(leg F)")
    if layout_ctl == 0:
        vacuous.append("the scoring path's refusal of the layout the entry "
                       "point did NOT hand on (leg F's negative control)")
    if described_differently == 0:
        vacuous.append("carriers whose OWN description differs from the "
                       "presentation's (leg E's in-loop control)")
    if levels_admitted == 0:
        vacuous.append("configured threshold levels the validation admits")
    if levels_refused == 0:
        vacuous.append("configured threshold levels the validation refuses "
                       "(leg V's refuting control)")
    for v in vacuous:
        fail(f"VACUOUS: no observation exercised {v}")

    print(f"G-AX legs: " + ", ".join(f"{k}={v}" for k, v in legs.items())
          + f"; name-identity refusals confirmed: {identity_limit}"
          + f"; payloads where re-presentation changed content: {nonidentity}"
          + f"; uninspectable-label refusals confirmed: {uninspectable}"
          + f"; declined-content observations: {content_seen}"
          + f"; layout observations: {layout_obs}"
          + f"; layout negative controls: {layout_ctl}"
          + f"; levels admitted/refused: {levels_admitted}/{levels_refused}"
          + f"; carriers described differently from their presentation: "
          + f"{described_differently}")
    print(f"G-AX: {checks} observations, {failures} mismatches")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
