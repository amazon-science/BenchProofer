#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of `implementation_fit` against
the PATCHED `IsolationForest.fit` tail (post-`patch.diff` behaviour).

The impl region is not all-A-tagged (I/R structure on the branch, the `warned`
flag, the traversal structure), so this runs a real fuzz. What is compared is the
FULL observable record the shipped spec pins, and in particular the traversal
log: `implementation_fit` returns a `Fitting` PROGRAM, and `Fitting.traversals`
is the list of payloads it traverses the fitted model over. That observable is
the one two independently-built breaking implementations forged when the model
carried it as a `Nat` output field (verdict.md CE-1/CE-2), so it is now inside
the compared tuple on every leg. So is the CARRIER the fitted estimator's public
scoring entry point hands the fitted model (`ScoreOutcome.handedOn`): an entry
point can run every admissibility check correctly and still hand the model the
caller's own object instead of the one the check re-presented, which no
comparison over flags and records can see. It is compared as a whole carrier and
not merely as a payload because what crosses is the estimator's OWN presentation
of the data, and a presentation describes itself: the same width, the storage form
THAT STEP hands content back in, no feature-name metadata of its own, and a
description the admissibility step would itself admit again. An entry point can
convert the content correctly and still hand the model that content wrapped in the
caller's description of it -- which is a different break, and one only the
description fields can see. It can also convert and describe the content
correctly and hand it on in the wrong sparse LAYOUT: the scoring path on the far
side of the crossing traverses row-indexed content and refuses column-indexed
content, so the layout is compared as one of three values rather than as a
sparseness bit, and the layout the entry point did NOT hand on is asserted to be
one the real scoring core refuses.

Note there is no shadow of a scoring FUNCTION. The Lean model declares none --
turning a payload into anomaly scores is an effect a `Fitting.traverse` node
performs, and the specification quantifies over every interpretation of it -- so
the shadow's `scores_of` is a symbolic tag standing for that interpretation,
applied identically on both legs and never given a value.

Three tiers, all of which must pass (exit 0 iff all do):

  A. SYMBOLIC FUZZ, >=1e5 inputs, pinned seed. `shadow_impl` transliterates
     Solution.lean's `implementation_fit` (including `validateInput`,
     `scoreEntry`, `checked`, and the `Fitting` program semantics);
     `reconstruct_patched` is an INDEPENDENT reconstruction of the patched
     Python control flow (`fit` tail -> `_score_samples`, and
     `_validate_data(reset=False)` for the later scoring path). Compared tuple:
     offset expression, fit-time warning, the record established,
     THE TRAVERSAL LOG, and the outcome of scoring a further fuzzed carrier --
     including the whole carrier that scoring hands the fitted model.

  B. REAL-CODE DIFFERENTIAL against the actual patched `IsolationForest` in the
     instance image, which is what makes tier A non-circular: the traversal log
     is MEASURED by spying on `_compute_chunked_score_samples` (the same callee
     `test_iforest_chunks_works1/2` mock), the offset is checked to be the
     percentile of the scores that traversal returned, the record is read off
     `n_features_in_`/`feature_names_in_`, and the later-scoring outcome is
     observed (ValueError => refused) together with the carrier that call hands
     the scoring core -- measured by the same spy, which reads all six fields of
     the object the core received off THAT object (its width, WHICH of the two
     sparse layouts it is in or whether it is dense, whether the label inspection
     reports names for it or raises on it, whether re-presenting it is accepted),
     so `handedOn` is grounded field by field against the real callee and not
     against the shadow. Carriers are presented densely and in BOTH sparse
     layouts, `fitCompletes` is asserted against what the real patched tail then
     does (below), and every sparse carrier that CROSSES into the scoring core
     carries a negative control: the core is asked to traverse the same numbers in
     both sparse layouts and must accept the one the entry point handed on and
     refuse the other.

  C. MUTATION SENSITIVITY. Twenty-two documented mutations of the shadow --
     including the three control-flow forgeries from verdict.md (hoisting the
     traversal above the branch; an extra discarded traversal; a traversal whose
     scores the continuation discards), the entry point that hands on its
     caller's object, the entry point that converts the content correctly and
     hands it on under the caller's DESCRIPTION, the entry point that converts and
     describes it correctly and hands it on in the sparse LAYOUT its own scoring
     path refuses, two that abuse the
     storage-form limit below, four that
     abuse the label-inspectability limit in either direction and four that abuse
     the content-admissibility limit in either direction -- must each be CAUGHT.
     This is what makes "0 disagreements" informative rather than a tautology.

DELIBERATE MODEL LIMIT (refinement.md, "name PRESENCE, not name IDENTITY"):
`InputData.hasFeatureNames` records only whether the estimator admits names for a
carrier, never which names. Draws where BOTH the training and the probe carrier
bear names AND the names disagree are outside the model; they are counted, and
the real code is asserted to REFUSE there, rather than being silently skipped.

PRECONDITION (refinement.md, "LABEL INSPECTABILITY"): a carrier can bear column
labels the estimator cannot ANSWER about -- labels of mixed kinds, some textual
and some not -- which is a third case beside "bears names" and "bears none": the
label inspection itself raises. `InputData.namesInspectable` carries that case,
the obligation is stated only for a training carrier whose labels can be
inspected, and the LATER carrier is under a positive obligation to be turned
away when its labels cannot be. Neither half is taken on trust. Draws whose
training carrier is not inspectable are counted, the real patched `fit` is
asserted to RAISE on them and to leave no threshold behind, and the same numbers
under homogeneous labels are asserted to fit -- the control that shows the
withheld description is about the label kinds. Probe draws that are not
inspectable are asserted REFUSED by the real public scoring path at the training
width, with the homogeneous presentation of the same numbers accepted.

PRECONDITION (refinement.md, "CONTENT ADMISSIBILITY"): establishing that a
carrier is admissible is not a pure inspection -- the check RE-PRESENTS the
content -- and there are contents it declines to re-present at all: content with
no rows to describe, content with no columns to describe, and content holding a
value that is not finite. That is a different partiality from the label one (a
bare array of non-finite numbers is perfectly answerable about, and answers "no
names"), so `InputData.contentAdmissible` carries it separately, the obligation
is stated only for a training carrier whose content the check ACCEPTS, and the
LATER carrier is under a positive obligation to be turned away when its content
is one the check declines. Neither half is taken on trust. Draws whose training
content is declined are counted, the real patched `fit` is asserted to RAISE on
them and to leave neither a threshold NOR a recorded width behind, and the
ordinary content of the same width is asserted to fit and to agree with the
shadow in full -- the control that shows the withheld description is about the
content. Probe draws whose content is declined are presented AT THE TRAINING
WIDTH, so no width check can be what refuses them, and are asserted refused by
the real public scoring path, with the ordinary content of the same width
accepted. The name diagnostic is asserted to stand on those calls: the naming
question is settled before the content is re-presented, so the carrier is warned
about and then turned away.

DELIBERATE MODEL LIMIT (refinement.md, "STORAGE FORM"): the fit-time
admissibility check admits a sparse carrier and hands it back in the ONE sparse
layout it accepts -- the column-indexed one, whichever layout the caller
presented -- and the chunked scoring path the patched tail then enters refuses
that layout outright, so a configured sparse carrier has NO offset and NO
traversal record to describe. `InputData.form` carries the layout, three-valued
because the scoring path is partial on the layout and not merely on sparseness,
and `fitCompletes x auto = auto ||
(Form.reshaped x.form Form.sparseByColumn).traversable` marks exactly the runs
that reach a result; the two clauses about the threshold and the traversal log are
asserted only there. This leg does not take that on trust: draws with
`fitCompletes = false` are counted, the real patched `fit` is asserted to RAISE
on them -- for a ROW-indexed training carrier as well as a column-indexed one,
which is what shows the guard is about the layout the CHECK hands on rather than
the layout presented -- and the SAME NUMBERS presented densely are asserted to
complete and to agree with the shadow in full, the control that shows the refusal
is about the storage form rather than about the payload. Everything the aborted
run does establish (the record) is still compared, and the sparse AUTO lane, where
`fitCompletes` is true, stays under the full obligation on both legs.

The SCORING end of the tail accepts a different sparse layout from the fitting
end, which is why the layout is a parameter of the modeled check rather than a
constant: the public entry point asks for `csr`, so a sparse carrier crosses into
the fitted model row-indexed and the scoring core can traverse it. That asymmetry
is the whole content of the handed-on carrier's layout field, and it is measured
here rather than argued (tier B's crossing control above).

stdlib-only for tiers A and C; tier B additionally needs numpy/scipy/pandas/
sklearn.
"""
import json
import os
import random
import struct
import sys
import warnings

SEED = 25931           # pinned in mapping.md / meta.json verifier_pins.conf_seed
N = 120_000            # >= 1e5 symbolic inputs
N_REAL = 300           # real-code differential draws
N_SENS = 4_000         # per-mutation sensitivity budget


# --------------------------------------------------------------------------
# R-refinement of the opaque callees. `checked` is the payload as the
# estimator's admissibility check hands it on: for this repo that is
# check_array(..., dtype=np.float32), i.e. a float32 round trip -- idempotent,
# as `checked_idem` asserts, and NOT the identity (0.1 is not a float32), so a
# shadow that traverses the caller's own payload is detectable.
# --------------------------------------------------------------------------
def f32(x):
    return struct.unpack("f", struct.pack("f", x))[0]


def checked(values):
    return tuple(f32(v) for v in values)


def scores_of(payload):
    """The interpretation of the scoring effect, symbolically.

    Lean declares no scoring function at all: a traversal of the fitted model is
    a `Fitting.traverse` node and the obligation is quantified over every
    interpretation `sc` of what such a node yields (mapping.md). Here that
    interpretation is a symbolic tag -- never given a value, applied identically
    on both legs -- so the comparison is over the STRUCTURE the offset is built
    from, which is what the Lean clause pins.
    """
    return ("scores", payload)


def percentile(scores, q):
    """Symbolic `percentile`: identical callee on both legs (mapping.md)."""
    return ("percentile", scores, q)


# The three STORAGE FORMS `Form` enumerates. Three and not two because the
# scoring path is partial on the sparse LAYOUT and not merely on sparseness: it
# traverses dense and row-indexed content and refuses column-indexed content, and
# the estimator's two admissibility checks accept DIFFERENT sparse layouts, so
# which layout a check hands on is a property of the check.
DENSE, BY_ROW, BY_COLUMN = "dense", "sparseByRow", "sparseByColumn"


def traversable(form):
    """`Form.traversable` (Solution.lean, pure region)."""
    return form != BY_COLUMN


def reshaped(arrived, accepted):
    """`Form.reshaped arrived accepted` (Solution.lean, pure region): content that
    arrives dense is handed back dense; sparse content is admitted and handed back
    in the layout the check accepts, whichever sparse layout it arrived in."""
    return DENSE if arrived == DENSE else accepted


def fit_completes(x, contamination_auto):
    """`fitCompletes x auto` (Solution.lean, pure region).

    A carrier is InputData-shaped: (values, n_features, has_names, form,
    names_inspectable, content_admissible). The fit tail reaches a RESULT when the auto arm returns
    before the scoring path, or when the form the FIT-TIME check hands its
    carrier back in is one that path can traverse. That check accepts the
    column-indexed layout, so every sparse carrier reaches the scoring path in
    that layout whichever one it arrived in, and the path refuses it -- there is
    no threshold and no traversal to describe.
    """
    return contamination_auto or traversable(reshaped(x[3], BY_COLUMN))


def precondition_holds(x, mut=None):
    """`xOrig.namesInspectable = true` AND `xOrig.contentAdmissible = true` --
    the two antecedents of the whole obligation (Solution.lean, post-conditions
    region).

    Withholding a description is only honest where the run cannot happen, so
    tier A and tier B both check this predicate against whether the real fit-time
    label inspection or the real re-presentation step raises. `mut` bends the
    predicate for tier C, in both directions on each conjunct: one forgets a
    limit, the other over-claims it onto carriers the real code fits."""
    if mut == "precond-ignores-inspection":
        return x[5]
    if mut == "precond-excludes-unnamed":
        return x[4] and x[5] and x[2]
    if mut == "precond-ignores-content":
        return x[4]
    if mut == "precond-excludes-converted":
        # over-claims the content limit onto every carrier the check has to
        # convert, which is most of them -- re-presenting content is what the
        # check is for.
        return x[4] and x[5] and checked(x[0]) == tuple(x[0])
    return x[4] and x[5]


# --------------------------------------------------------------------------
# Tier A leg 1: transliteration of Solution.lean.
# --------------------------------------------------------------------------
UNRECORDED = (0, False)          # def unrecorded : Reference


def validate_input(x, reset, ref, accepted):
    """`validateInput x reset ref accepted : Validation` -> (carrier, refAfter,
    refused, warned). Strips carrier metadata, re-presents the payload, hands the
    STORAGE form back RESHAPED for the one sparse layout this step accepts
    (`accepted`), hands back a carrier whose labels are trivially
    inspectable (it carries none), and on a consistency re-check reports refusal
    -- of a foreign width, of labels it cannot inspect at all, or of content it
    does not accept -- and the name-status warning, which it can only reach for
    labels it can inspect and which it reports before the content is
    re-presented, so a content refusal does not suppress it."""
    values, n_features, has_names, form, inspectable, content_ok = x
    carrier = (checked(values), n_features, False, reshaped(form, accepted),
               True, True)
    ref_after = (n_features, has_names) if reset else ref
    refused = (not reset) and ((not inspectable) or (not content_ok)
                               or n_features != ref[0])
    warned = (not reset) and inspectable and (ref[1] != has_names)
    return carrier, ref_after, refused, warned


def score_entry(ref, z):
    """`scoreEntry ref z : ScoreOutcome` -> (refused, warned, refAfter,
    handedOn). `handedOn` is the whole CARRIER the entry point hands the fitted
    model: the estimator's own presentation, which its admissibility check
    produced -- never the argument, and never the argument's description of
    itself -- and in the sparse layout THIS step accepts, the row-indexed one the
    scoring path it forwards to can traverse."""
    carrier, ref_after, refused, warned = validate_input(z, False, ref, BY_ROW)
    return refused, warned, ref_after, carrier


def shadow_impl(x_orig, contamination_auto, contamination, mut=None):
    """R/I shadow of `implementation_fit` (Solution.lean, post-patch), run as the
    program it is: returns (result, traversals) where result is
    (offset, warned, reference, scoreLater) and traversals is the list of
    payloads the program traversed the fitted model over (`Fitting.traversals`).

    `mut` injects a documented mutation for the tier-C sensitivity check."""
    log = []

    def traverse(payload):
        """One `Fitting.traverse` node: logs the traversal, yields the scores."""
        log.append(payload)
        return scores_of(payload)

    carrier, ref, _refused, _warned = validate_input(x_orig, True, UNRECORDED,
                                                     BY_COLUMN)
    x_values = carrier[0]

    if mut == "hoist":
        # verdict.md CE-1: the traversal is performed UNCONDITIONALLY, above the
        # branch, and the auto arm discards the array.
        pre = traverse(x_values)
    if mut == "double":
        # verdict.md CE-2: an extra discarded warm-up traversal.
        traverse(x_values)

    if contamination_auto:
        if mut == "sparse-auto-traverses" and x_orig[3] != DENSE:
            # abuses the storage-form limit: traverses on the sparse AUTO lane,
            # which the limit does not excuse.
            traverse(x_values)
        if mut == "sparse-auto-declines" and x_orig[3] != DENSE:
            # abuses the storage-form limit in the other direction: declines the
            # auto arm for every sparse carrier rather than only where the
            # scoring path is actually entered.
            return (0.0, False, ref, ("scoreLater", ref)), log
        return (-0.5, False, ref, ("scoreLater", ref)), log

    payload = x_values if mut != "no-conv" else tuple(x_orig[0])
    scores = pre if mut == "hoist" else traverse(payload)
    if mut == "decorative-traverse":
        # verdict.md CE-3: the traversal is performed and COUNTED, and then its
        # scores are discarded and the threshold taken over the payload itself.
        scores = payload
    offset = percentile(scores, 100.0 * contamination)
    if mut == "offset-const":
        offset = -0.5
    fit_warned = False
    if mut == "second-pass":
        # a second consistency pass in the tail: reintroduces the diagnostic the
        # patch removes.
        _c2, _r2, _f2, w2 = validate_input(carrier, False, ref, BY_ROW)
        fit_warned = w2
    record = ref if mut != "record-widened" else (ref[0] + 1, ref[1])
    return (offset, fit_warned, record, ("scoreLater", record)), log


def shadow_score_later(handle, z, mut=None):
    """Run the shadow's `scoreLater` on a further carrier."""
    ref = handle[1]
    refused, warned, ref_after, handed_on = score_entry(ref, z)
    if mut == "silent-later":
        warned = False
    if mut == "accept-any-width":
        refused = (not z[4])
    if mut == "later-admits-inadmissible-content":
        # the content analogue of the collapsed reading: every check performed on
        # the labels and the width, and a carrier whose content the check
        # declines handed straight on.
        refused = (not z[4]) or (z[1] != ref[0])
    if mut == "content-rewrite-as-refusal":
        # the verify-not-resolve rival clause 7's region is what closes: turns
        # away every carrier whose content the check does not hand back as it
        # found it, i.e. most of what it exists to accept.
        refused = refused or (checked(z[0]) != tuple(z[0]))
    if mut == "later-admits-uninspectable":
        # the abstraction-collapse rival: every check performed on the width, and
        # a carrier whose labels the estimator cannot inspect handed straight on.
        refused = (z[1] != ref[0])
    if mut == "later-warns-uninspectable":
        # reports a name-status delta for a carrier whose name status was never
        # readable, which the real path cannot do: it raises first.
        warned = (ref[1] != z[2])
    if mut == "forward-caller-payload":
        # every check performed and reported correctly, and then the caller's
        # own object handed to the fitted model rather than the checked one.
        handed_on = z
    if mut == "entry-accepts-column-layout":
        # the layout break: every check performed, the content converted, the
        # presentation described correctly, and handed on in the sparse layout the
        # scoring path on the far side refuses. Invisible to every comparison over
        # flags, records, content and self-description.
        c2, _r2, _f2, _w2 = validate_input(z, False, ref, BY_COLUMN)
        handed_on = c2
    if mut == "forward-caller-description":
        # subtler: the content IS the re-presented content, and it is handed on
        # wearing the caller's description of itself -- its label status, its
        # inspectability, its admissibility. The estimator's presentation
        # describes itself, and this one describes the caller's object.
        handed_on = (handed_on[0], handed_on[1], z[2], handed_on[3], z[4], z[5])
    return refused, warned, ref_after, handed_on


# --------------------------------------------------------------------------
# Tier A leg 2: independent reconstruction of the PATCHED Python.
#
#   X = self._validate_data(X, accept_sparse=["csc"], dtype=tree_dtype)  # reset
#   if self.contamination == "auto":
#       self.offset_ = -0.5
#       return self
#   self.offset_ = np.percentile(self._score_samples(X), 100.0*self.contamination)
#
# `_score_samples` (NEW in the patch) = check_is_fitted + the negation of
# `_compute_chunked_score_samples(X)`: exactly one chunked traversal of the
# fitted model, and NO `_validate_data(..., reset=False)`. `score_samples`
# (public) keeps the reset=False validation and then calls `_score_samples`.
#
# `accept_sparse=["csc"]` means a sparse carrier is admitted AND handed back
# sparse, and the chunked path refuses that form: the configured arm therefore
# ABORTS there, which the reconstruction reports rather than inventing a result.
# --------------------------------------------------------------------------
def reconstruct_patched(x_orig, contamination_auto, contamination):
    """Returns (result, traversals, abort) where `abort` is None, "labels" or
    "storage".

    "labels": `_validate_data(reset=True)` runs `_check_feature_names` FIRST, and
    the label inspection raises for labels of mixed kinds -- nothing at all is
    established, not even the width record. "content": `check_array` runs NEXT,
    before `_check_n_features`, and it declines some contents outright -- again
    nothing is established, not even the width record. "storage": the run raised
    inside the chunked scoring path, so the record stands but no threshold was
    assigned and no traversal of the fitted model completed; those fields carry
    sentinels."""
    values, n_features, has_names, form, inspectable, content_ok = x_orig
    traversals = []
    if not inspectable:
        return ((("aborted",), False, ("aborted",), ("aborted",)),
                traversals, "labels")
    if not content_ok:
        return ((("aborted",), False, ("aborted",), ("aborted",)),
                traversals, "content")
    # _validate_data(reset=True): records n_features_in_ / feature_names_in_
    # from the training carrier and hands back the converted array, in the
    # storage form it arrived in.
    converted = checked(values)
    n_features_in_, names_recorded = n_features, has_names
    record = (n_features_in_, names_recorded)
    if contamination_auto:
        # returns before ever entering the chunked scoring path
        return ((-0.5, False, record, ("scoreLater", record)), traversals, None)
    if not traversable(reshaped(form, BY_COLUMN)):
        # _score_samples -> _compute_chunked_score_samples(csc) raises: the
        # fit-time check asked for `csc`, so a sparse carrier arrives in the
        # column-indexed layout whichever one the caller presented, and that is
        # the layout the chunked path refuses. The record is established, the
        # threshold attribute never is.
        return ((("aborted",), False, record, ("scoreLater", record)),
                traversals, "storage")
    # _score_samples(X): one _compute_chunked_score_samples pass over the
    # converted training payload, no validation, hence no warning.
    traversals.append(converted)
    offset_ = percentile(scores_of(converted), 100.0 * contamination)
    return ((offset_, False, record, ("scoreLater", record)), traversals, None)


def reconstruct_score_samples(handle, z):
    """Independent reconstruction of the public `score_samples(Z)` path:
    `_validate_data(Z, accept_sparse="csr", dtype=np.float32, reset=False)`,
    which runs `_check_feature_names(reset=False)` then
    `_check_n_features(reset=False)`.

    Returns (refused, warned, record_after, handed_on, name_identity_ground)
    where `handed_on` is the CARRIER `_score_samples` receives -- the array
    `_validate_data` returned, described as it describes itself: the presented
    width, no feature-name metadata (the validated array is bare, whatever the
    caller wrapped it in), the storage form THAT STEP hands content back in
    (`accept_sparse="csr"` converts a sparse presentation of either layout to CSR
    and hands it back sparse, and leaves a dense one dense -- which is what
    `Form.reshaped z.form sparseByRow` says), and labels and content the estimator
    would read and accept again. The last flag says the refusal ground was NAME
    IDENTITY -- outside the model. The probe path asks for `csr` and converts, so
    REFUSAL is insensitive to the storage form even though what it hands on is
    not."""
    n_features_in_, names_recorded = handle[1]
    _values, n_features, has_names, form, inspectable, content_ok = z
    presentation = (checked(_values), n_features, False,
                    reshaped(form, BY_ROW), True, True)
    if not inspectable:
        # _check_feature_names calls _get_feature_names FIRST, and it raises for
        # labels of mixed kinds: the carrier is turned away before any width or
        # name-status comparison happens, so there is no warning either.
        return (True, False, (n_features_in_, names_recorded),
                presentation, False)
    # _check_feature_names: warn when exactly one side has names; raise when
    # both have names that disagree (BaseEstimator, unchanged by the patch).
    both_named = names_recorded and has_names
    warned = (names_recorded != has_names)
    if not content_ok:
        # check_array comes AFTER _check_feature_names and BEFORE
        # _check_n_features: the naming question is already settled and reported,
        # the content is declined here, and the width is never reached.
        return (True, warned, (n_features_in_, names_recorded),
                presentation, both_named)
    # _check_n_features: raise when the width disagrees with n_features_in_.
    width_bad = (n_features != n_features_in_)
    return (width_bad, warned, (n_features_in_, names_recorded),
            presentation, both_named)


# --------------------------------------------------------------------------
# Tier A driver
# --------------------------------------------------------------------------
def draw(rng):
    n_features = rng.randint(1, 4)
    n_samples = rng.randint(1, 4)
    values = [round(rng.uniform(-2.0, 2.0), 3)
              for _ in range(n_features * n_samples)]
    # 0.1-style values are not float32-exact, so the `checked` conversion is an
    # observable and a shadow that skips it is caught.
    if rng.random() < 0.5 and values:
        values[0] = 0.1
    # a sparse carrier bears no feature names in this repo (the labelled
    # presentation is the dense one), so the two flags are drawn together.
    # the LAYOUT is drawn over all three values: a sparse carrier reaches the
    # tail in the fit-time check's layout whichever one it arrived in, and which
    # layout it arrived in is what the handed-on comparison turns on at the
    # scoring end.
    form = (DENSE, BY_ROW, BY_COLUMN)[0 if rng.random() >= 0.4
                                      else (1 if rng.random() < 0.5 else 2)]
    has_names = (form == DENSE) and rng.random() < 0.5
    # labels of MIXED kinds need a labelled presentation with at least two
    # columns to exist at all; every other carrier can be answered about.
    x_insp = not (has_names and n_features >= 2 and rng.random() < 0.25)
    # content the check declines is independent of the labels and of the storage
    # form: a bare array of non-finite numbers is answerable about and sparse
    # content is admitted, so this flag is drawn on its own.
    x_content = not (rng.random() < 0.15)
    x_orig = (tuple(values), n_features, has_names, form, x_insp,
              x_content)
    contamination_auto = rng.random() < 0.35
    # the configured threshold level is drawn inside the estimator's DECLARED
    # interval for that parameter, which is also the region the description's
    # level precondition covers (`levelAdmitted`; refinement.md, "PRECONDITION
    # (CONFIGURED THRESHOLD LEVEL)"). A draw outside it would compare the shadow
    # against a run the real code never performs and the description never
    # describes: the parameter validation is the first thing fitting does, so such
    # a draw aborts before any carrier is looked at. That direction is measured
    # where it belongs, against the real callee, by axiom_check.py's leg V.
    contamination = round(rng.uniform(0.05, 0.5), 4)
    zw = n_features if rng.random() < 0.6 else rng.randint(1, 4)
    z_form = (DENSE, BY_ROW, BY_COLUMN)[0 if rng.random() >= 0.3
                                        else (1 if rng.random() < 0.5 else 2)]
    z_named = (z_form == DENSE) and rng.random() < 0.5
    z_insp = not (z_named and zw >= 2 and rng.random() < 0.35)
    z_content = not (rng.random() < 0.2)
    z = (tuple(round(rng.uniform(-2.0, 2.0), 3) for _ in range(zw)), zw,
         z_named, z_form, z_insp, z_content)
    # name identity of the probe carrier, only meaningful when both bear names
    names_agree = rng.random() < 0.5
    return x_orig, contamination_auto, contamination, z, names_agree


def compare_symbolic(rng, n, mut=None):
    """Return (disagreements, out_of_model, aborts, excluded, probes,
    content_excluded, content_probes, crossings, witness)."""
    bad = 0
    out_of_model = 0
    aborts = 0
    excluded = 0
    probes = 0
    content_excluded = 0
    content_probes = 0
    crossings = 0
    witness = None
    for _ in range(n):
        x_orig, auto, cont, z, names_agree = draw(rng)
        r_res, r_log, abort = reconstruct_patched(x_orig, auto, cont)
        # PRECONDITIONS, in BOTH directions: the obligation may be withheld
        # exactly where the real fit-time label inspection or the real
        # re-presentation step turns the training carrier away, so the two
        # antecedents together can neither miss such a carrier nor excuse one the
        # real code fits.
        if ((abort in ("labels", "content"))
                != (not precondition_holds(x_orig, mut=mut))):
            bad += 1
            if witness is None:
                witness = ("precondition", x_orig, abort,
                           precondition_holds(x_orig, mut=mut))
            continue
        if abort in ("labels", "content"):
            # nothing was established, so there is nothing to compare
            excluded += 1
            if abort == "content":
                content_excluded += 1
            continue
        if not z[4]:
            probes += 1
        if not z[5]:
            content_probes += 1
        s_res, s_log = shadow_impl(x_orig, auto, cont, mut=mut)
        s_probe = shadow_score_later(s_res[3], z, mut=mut)
        (r_refused, r_warned, r_after, r_handed,
         both_named) = reconstruct_score_samples(r_res[3], z)
        # the spec guards the handed-on leg by non-refusal, so a refused carrier
        # is compared on its flags and record only -- claiming nothing about a
        # payload that never crossed.
        if r_refused or s_probe[0]:
            s_probe = s_probe[:3]
            r_probe = (r_refused, r_warned, r_after)
        else:
            r_probe = (r_refused, r_warned, r_after, r_handed)
            if z[3] != DENSE:
                # a SPARSE carrier that crosses into the fitted model: the only
                # draws on which the handed-on leg's LAYOUT half has content, and
                # the ones the layout mutation is caught on.
                crossings += 1
        identity_disagrees = both_named and not names_agree
        # STORAGE FORM: `fitCompletes` marks the runs that reach a result. Where
        # it is false the two withheld observables are dropped -- exactly the
        # offset and the traversal log -- and nothing else is.
        if (abort == "storage") != (not fit_completes(x_orig, auto)):
            bad += 1
            if witness is None:
                witness = ("fitCompletes", x_orig, auto, abort)
            continue
        aborted = (abort == "storage")
        if aborted:
            aborts += 1
        head_s = (s_res[1], s_res[2]) if aborted else (s_res[0], s_res[1],
                                                       s_res[2], s_log)
        head_r = (r_res[1], r_res[2]) if aborted else (r_res[0], r_res[1],
                                                       r_res[2], r_log)
        if identity_disagrees:
            # Outside the model: the real code refuses on a ground the model
            # cannot see (tier B asserts that refusal against the real callee).
            # Everything else is still compared; only `refused` is dropped.
            out_of_model += 1
            a = head_s + (s_probe[1], s_probe[2])
            b = head_r + (r_warned, r_after)
        else:
            a = head_s + tuple(s_probe)
            b = head_r + tuple(r_probe)
        if a != b:
            bad += 1
            if witness is None:
                witness = (x_orig, auto, cont, z, a, b)
    return (bad, out_of_model, aborts, excluded, probes, content_excluded,
            content_probes, crossings, witness)


# --------------------------------------------------------------------------
# Tier B: real patched IsolationForest
# --------------------------------------------------------------------------
def real_leg(n_draws):
    """Differential against the REAL patched code. Returns a dict of counters
    plus the first witness and a note."""
    def unavailable(note):
        return {"checks": 0, "failures": 0, "out_of_model": 0, "aborts": 0,
                "controls": 0, "label_aborts": 0, "label_controls": 0,
                "probe_refusals": 0, "probe_controls": 0,
                "content_aborts": 0, "content_controls": 0,
                "content_probe_refusals": 0, "content_probe_controls": 0,
                "layout_crossings": 0, "layout_controls": 0,
                "witness": None, "note": note}
    try:
        import numpy as np
        import scipy.sparse as sparse
        from sklearn.ensemble import IsolationForest
        from sklearn.utils.validation import check_array
    except Exception as exc:                                   # pragma: no cover
        return unavailable(f"unavailable: {exc!r}")
    try:
        from sklearn.utils.validation import _get_feature_names
    except Exception:                                          # pragma: no cover
        _get_feature_names = None
    try:
        import pandas as pd
    except Exception:                                          # pragma: no cover
        pd = None

    orig = IsolationForest._compute_chunked_score_samples
    log = []

    def contents(X):
        """The payload contents as the scoring core received them, whatever
        storage form they arrived in."""
        arr = X.toarray() if sparse.issparse(X) else np.asarray(X)
        return tuple(np.asarray(arr).ravel().tolist())

    def layout_of(X):
        """The STORAGE FORM of a real carrier as `Form` enumerates it: dense, or
        which of the two sparse layouts. Anything sparse that is neither CSR nor
        CSC is reported verbatim so a surprise cannot pass as an expected layout."""
        if not sparse.issparse(X):
            return DENSE
        fmt = getattr(X, "format", None)
        if fmt == "csr":
            return BY_ROW
        if fmt == "csc":
            return BY_COLUMN
        return f"sparse:{fmt}"

    def describe(X):
        """The six fields of `InputData`, read off the object the scoring core
        was ACTUALLY handed -- so the model's handed-on carrier is compared as a
        carrier and not merely as a payload. Every field is a question asked of
        that object: its width, whether the label inspection reports names for it
        (or raises on it at all), its storage form -- which of the two sparse
        LAYOUTS, not merely whether it is sparse, because that is what decides
        whether the core can traverse it -- and whether the estimator's own
        admissibility check would re-present it."""
        arr = X.toarray() if sparse.issparse(X) else np.asarray(X)
        arr = np.asarray(arr)
        width = int(arr.shape[1]) if arr.ndim == 2 else 0
        if _get_feature_names is None:
            has_names, inspectable = False, True
        else:
            try:
                has_names = _get_feature_names(X) is not None
                inspectable = True
            except Exception:
                has_names, inspectable = False, False
        try:
            check_array(X, accept_sparse="csr", dtype=np.float32)
            admissible = True
        except Exception:
            admissible = False
        return (contents(X), width, has_names, layout_of(X),
                inspectable, admissible)

    def spy(self, X):
        out = orig(self, X)
        log.append((contents(X), np.asarray(out), describe(X)))
        return out

    IsolationForest._compute_chunked_score_samples = spy
    rng = np.random.RandomState(SEED)
    checks = failures = out_of_model = aborts = controls = 0
    label_aborts = label_controls = probe_refusals = probe_controls = 0
    content_aborts = content_controls = 0
    content_probe_refusals = content_probe_controls = 0
    layout_crossings = layout_controls = 0
    witness = None

    def carrier(data, labels):
        if labels is None or pd is None:
            return data
        return pd.DataFrame(data, columns=list(labels))

    def present(data, labels, form, inspectable=True):
        if form == BY_COLUMN:
            return sparse.csc_matrix(data)
        if form == BY_ROW:
            return sparse.csr_matrix(data)
        if not inspectable:
            # labels of MIXED kinds: the label inspection cannot answer at all.
            mixed = [f"c{i}" for i in range(data.shape[1])]
            mixed[-1] = data.shape[1] - 1
            return pd.DataFrame(data, columns=mixed)
        return carrier(data, labels)

    def declined_content(data, kind):
        """One of the three CONTENTS the admissibility check will not
        re-present, built from this draw's numbers. Presented as a BARE dense
        array, so the label question is answered for it and the storage form is
        the one the check accepts: the content is the only ground left."""
        if kind == "not finite":
            body = np.array(data, dtype=np.float64)
            body[0, 0] = np.nan
            return body
        if kind == "no rows":
            return np.zeros((0, data.shape[1]), dtype=np.float64)
        return np.zeros((data.shape[0], 0), dtype=np.float64)

    def consistency_warned(caught):
        for w in caught:
            m = str(w.message)
            if "fitted with feature names" in m or "fitted without feature names" in m:
                return True
        return False

    try:
        for _ in range(n_draws):
            n_samples = int(rng.randint(4, 9))
            wf = int(rng.randint(1, 4))
            data = np.round(rng.randn(n_samples, wf), 3).astype(np.float64)
            data[0, 0] = 0.1                    # not float32-exact
            # all three layouts: the fit-time check asks for `csc`, so both
            # sparse layouts reach the tail in the layout it refuses -- which is
            # what `Form.reshaped x.form sparseByColumn` says, and asserting it on
            # a ROW-indexed training carrier as well is what shows the guard is
            # about the layout the CHECK hands on and not the one presented.
            fit_form = (DENSE if rng.rand() >= 0.4
                        else (BY_ROW if rng.rand() < 0.5 else BY_COLUMN))
            fit_named = ((fit_form == DENSE) and bool(rng.rand() < 0.5)
                         and pd is not None)
            # a training carrier whose labels cannot be inspected needs a
            # labelled presentation of at least two columns
            fit_insp = not (fit_named and wf >= 2 and bool(rng.rand() < 0.3))
            labels_f = [f"c{i}" for i in range(wf)] if fit_named else None
            auto = bool(rng.rand() < 0.35)
            cont = float(np.round(rng.uniform(0.05, 0.5), 4))
            # the CONTENT lane: one draw in five presents content the check
            # declines. It replaces the presentation entirely -- bare, dense,
            # inspectable -- so the content is the only ground for the abort.
            content_kind = None
            if bool(rng.rand() < 0.2):
                content_kind = ("not finite", "no rows",
                                "no columns")[int(rng.randint(0, 3))]
            if content_kind is not None:
                fit_form = DENSE
                fit_named = False
                fit_insp = True
                labels_f = None
                body = declined_content(data, content_kind)
            else:
                body = data

            clf = IsolationForest(
                n_estimators=3, random_state=0,
                contamination=("auto" if auto else cont))
            del log[:]
            aborted = False
            label_abort = False
            content_abort = False
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                try:
                    clf.fit(present(body, labels_f, fit_form, fit_insp))
                except TypeError:
                    label_abort = True
                except ValueError:
                    # WHICH step declined is read off the estimator rather than
                    # assumed: the re-presentation runs before the width is
                    # recorded, so a record left behind means the run got past
                    # the check and aborted later, inside the scoring path.
                    if hasattr(clf, "n_features_in_"):
                        aborted = True
                    else:
                        content_abort = True
            fit_warned = consistency_warned(caught)
            fit_log = list(log)

            # --- the model's view of the same draw
            x_orig = (tuple(body.ravel().tolist()), int(body.shape[1]),
                      fit_named, fit_form, fit_insp, content_kind is None)

            # PRECONDITIONS, grounded in BOTH directions: the obligation is
            # withheld exactly where the real fit-time label inspection or the
            # real re-presentation step raises, and nowhere else.
            checks += 1
            if ((label_abort or content_abort)
                    != (not precondition_holds(x_orig))):
                failures += 1
                if witness is None:
                    witness = ("precondition", wf, fit_named, fit_insp,
                               content_kind, label_abort, content_abort)
                continue
            if content_abort:
                content_aborts += 1
                # such a fit leaves nothing at all behind to describe -- not the
                # threshold and not even the recorded width
                checks += 1
                if hasattr(clf, "offset_") or hasattr(clf, "n_features_in_"):
                    failures += 1
                    if witness is None:
                        witness = ("content-abort-left-state", content_kind,
                                   hasattr(clf, "offset_"),
                                   hasattr(clf, "n_features_in_"))
                    continue
                # CONTROL: the ORDINARY content of the same width fits and agrees
                # with the shadow in full -- so the withheld description is about
                # the content, not about this width or this estimator.
                ctl = IsolationForest(n_estimators=3, random_state=0,
                                      contamination=("auto" if auto else cont))
                del log[:]
                ctl.fit(data)
                content_controls += 1
                ctl_log = [e[0] for e in log]
                k_orig = (tuple(data.ravel().tolist()), wf, False, DENSE,
                          True, True)
                k_res, k_log = shadow_impl(k_orig, auto, cont)
                checks += 1
                ok = (list(k_log) == ctl_log
                      and k_res[2] == (int(ctl.n_features_in_),
                                       bool(hasattr(ctl, "feature_names_in_")))
                      and hasattr(ctl, "offset_"))
                if not ok:
                    failures += 1
                    if witness is None:
                        witness = ("content-control", content_kind, wf, auto,
                                   list(k_log), ctl_log)
                continue
            if label_abort:
                label_aborts += 1
                # such a fit leaves nothing at all behind to describe
                checks += 1
                if hasattr(clf, "offset_") or hasattr(clf, "n_features_in_"):
                    failures += 1
                    if witness is None:
                        witness = ("label-abort-left-state", wf,
                                   hasattr(clf, "offset_"),
                                   hasattr(clf, "n_features_in_"))
                    continue
                # CONTROL: the same numbers under HOMOGENEOUS labels at the same
                # width fit and agree with the shadow in full -- so the withheld
                # description is about the label kinds, not about this payload.
                ctl = IsolationForest(n_estimators=3, random_state=0,
                                      contamination=("auto" if auto else cont))
                del log[:]
                ctl.fit(carrier(data, labels_f))
                label_controls += 1
                ctl_log = [e[0] for e in log]
                c_orig = (x_orig[0], wf, fit_named, DENSE, True, True)
                c_res, c_log = shadow_impl(c_orig, auto, cont)
                checks += 1
                ok = (list(c_log) == ctl_log
                      and c_res[2] == (int(ctl.n_features_in_),
                                       bool(hasattr(ctl, "feature_names_in_")))
                      and hasattr(ctl, "offset_"))
                if not ok:
                    failures += 1
                    if witness is None:
                        witness = ("label-control", wf, fit_named, auto,
                                   list(c_log), ctl_log)
                continue
            s_res, s_log = shadow_impl(x_orig, auto, cont)

            # STORAGE FORM, grounded in BOTH directions: the patched tail must
            # abort exactly where `fitCompletes` is false, so the guard can
            # neither miss a run that aborts nor excuse one that completes.
            checks += 1
            if aborted != (not fit_completes(x_orig, auto)):
                failures += 1
                if witness is None:
                    witness = ("fitCompletes", wf, fit_form, auto, aborted)
                continue

            if aborted:
                aborts += 1
                # what the aborted run DID establish is still compared
                checks += 1
                real_ref = (int(clf.n_features_in_),
                            bool(hasattr(clf, "feature_names_in_")))
                if s_res[2] != real_ref or hasattr(clf, "offset_"):
                    failures += 1
                    if witness is None:
                        witness = ("aborted-record", s_res[2], real_ref,
                                   hasattr(clf, "offset_"))
                    continue
                # CONTROL: the same numbers, presented densely, complete and
                # agree with the shadow in full -- so the refusal above is
                # about the storage form and not about this payload.
                ctl = IsolationForest(n_estimators=3, random_state=0,
                                      contamination=cont)
                del log[:]
                ctl.fit(data)
                controls += 1
                ctl_log = [e[0] for e in log]
                d_res, d_log = shadow_impl(
                    (x_orig[0], wf, False, DENSE, True, True), auto, cont)
                checks += 1
                ok = (list(d_log) == ctl_log and len(ctl_log) == 1
                      and ctl.offset_ == np.percentile(-log[-1][1],
                                                       100.0 * cont))
                if not ok:
                    failures += 1
                    if witness is None:
                        witness = ("dense-control", wf, cont,
                                   list(d_log), ctl_log)
                continue

            # traversal log: payload contents, one entry per traversal
            real_traversals = [e[0] for e in fit_log]
            checks += 1
            if list(s_log) != real_traversals:
                failures += 1
                if witness is None:
                    witness = ("traversals", wf, fit_named, auto, fit_form,
                               list(s_log), real_traversals)
                continue

            # offset: the shadow says percentile(scores_of(payload), 100*c);
            # the real offset_ must be np.percentile of the NEGATED scores that
            # traversal returned, at that rank (auto branch: the constant).
            checks += 1
            if auto:
                ok = (clf.offset_ == -0.5) and (s_res[0] == -0.5)
            else:
                scores = -fit_log[-1][1]
                ok = (clf.offset_ == np.percentile(scores, 100.0 * cont)
                      and s_res[0][0] == "percentile"
                      and s_res[0][2] == 100.0 * cont)
            if not ok:
                failures += 1
                if witness is None:
                    witness = ("offset", auto, cont, fit_form, clf.offset_,
                               s_res[0])
                continue

            # record established by fitting
            checks += 1
            real_ref = (int(clf.n_features_in_),
                        bool(hasattr(clf, "feature_names_in_")))
            if s_res[2] != real_ref:
                failures += 1
                if witness is None:
                    witness = ("reference", s_res[2], real_ref)
                continue

            # later scoring through the public entry point. That path asks for
            # `csr` and converts, so a sparse probe of EITHER layout is admitted:
            # the model puts no storage condition on these clauses, and this
            # measures that -- while the carrier the call hands the scoring core
            # is asserted below to be in the ROW-indexed layout, which is the
            # property the core actually requires.
            wz = wf if rng.rand() < 0.6 else int(rng.randint(1, 4))
            zdata = np.round(rng.randn(3, wz), 3).astype(np.float64)
            probe_form = (DENSE if rng.rand() >= 0.3
                          else (BY_ROW if rng.rand() < 0.5 else BY_COLUMN))
            probe_named = ((probe_form == DENSE) and bool(rng.rand() < 0.5)
                           and pd is not None)
            probe_insp = not (probe_named and wz >= 2
                              and bool(rng.rand() < 0.35))
            # the probe CONTENT lane. It is presented AT THE TRAINING WIDTH and
            # bare, so neither a width check nor the label inspection can be what
            # turns it away; only the two width-preserving contents are used here
            # for exactly that reason.
            probe_content_kind = None
            if bool(rng.rand() < 0.2):
                probe_content_kind = ("not finite",
                                      "no rows")[int(rng.randint(0, 2))]
                wz = wf
                zdata = declined_content(
                    np.round(rng.randn(3, wf), 3).astype(np.float64),
                    probe_content_kind)
                probe_form = DENSE
                probe_named = False
                probe_insp = True
            agree = bool(rng.rand() < 0.5)
            if probe_named:
                labels_z = ([f"c{i}" for i in range(wz)] if agree
                            else [f"q{i}" for i in range(wz)])
            else:
                labels_z = None
            z = (tuple(zdata.ravel().tolist()), wz, probe_named, probe_form,
                 probe_insp, probe_content_kind is None)
            identity_ground = (probe_insp and fit_named and probe_named
                               and (labels_z != labels_f))
            del log[:]
            refused = False
            label_refused = False
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                try:
                    clf.score_samples(present(zdata, labels_z, probe_form,
                                              probe_insp))
                except TypeError:
                    label_refused = True
                    refused = True
                except ValueError:
                    refused = True
            later_warned = consistency_warned(caught)
            later_log = list(log)
            s_refused, s_warned, s_after, s_handed = shadow_score_later(
                s_res[3], z)
            real_after = (int(clf.n_features_in_),
                          bool(hasattr(clf, "feature_names_in_")))
            checks += 1
            if identity_ground:
                out_of_model += 1
                # the documented limit: the real code MUST refuse here
                if not refused:
                    failures += 1
                    if witness is None:
                        witness = ("identity-limit-not-a-refusal",
                                   labels_f, labels_z)
                    continue
                if s_after != real_after:
                    failures += 1
                    if witness is None:
                        witness = ("refAfter", s_after, real_after)
                continue
            if (s_refused, s_warned, s_after) != (refused, later_warned,
                                                  real_after):
                failures += 1
                if witness is None:
                    witness = ("scoreLater", wf, fit_named, wz, probe_named,
                               probe_form,
                               (s_refused, s_warned, s_after),
                               (refused, later_warned, real_after))
                continue
            if not probe_insp:
                probe_refusals += 1
                checks += 1
                # the POSITIVE obligation the model now carries about the LATER
                # carrier: one whose labels cannot be inspected is turned away,
                # and it is the label inspection that turns it away -- at the
                # training width, where no width check could have.
                if not label_refused:
                    failures += 1
                    if witness is None:
                        witness = ("uninspectable-probe-admitted", wf, wz,
                                   probe_named)
                    continue
                if later_warned:
                    failures += 1
                    if witness is None:
                        witness = ("uninspectable-probe-warned", wf, wz)
                    continue
                # CONTROL: the same numbers under HOMOGENEOUS labels at the same
                # width are turned away only if the width itself is foreign, so
                # the refusal above is attributable to the label kinds.
                del log[:]
                ctl_labels = False
                ctl_width = False
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        clf.score_samples(
                            carrier(zdata, [f"c{i}" for i in range(wz)]))
                    except TypeError:
                        ctl_labels = True
                    except ValueError:
                        ctl_width = True
                probe_controls += 1
                checks += 1
                if ctl_labels or ctl_width != (wz != wf):
                    failures += 1
                    if witness is None:
                        witness = ("uninspectable-probe-control", wf, wz,
                                   ctl_labels, ctl_width)
                continue
            if probe_content_kind is not None:
                content_probe_refusals += 1
                checks += 1
                # the POSITIVE obligation the model carries about the LATER
                # carrier: one whose content the check declines is turned away,
                # at the TRAINING width, where no width check could have.
                if not refused:
                    failures += 1
                    if witness is None:
                        witness = ("inadmissible-content-probe-admitted",
                                   probe_content_kind, wf, wz)
                    continue
                # and the naming question is settled BEFORE the content is
                # re-presented, so the diagnostic still stands on that call --
                # which is why the model leaves the warning leg unguarded.
                checks += 1
                if later_warned != fit_named:
                    failures += 1
                    if witness is None:
                        witness = ("inadmissible-content-probe-warning",
                                   probe_content_kind, fit_named, later_warned)
                    continue
                # CONTROL: the ORDINARY content at the same width is admitted, so
                # the refusal above is attributable to the content.
                del log[:]
                ctl_refused = False
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        clf.score_samples(
                            np.round(rng.randn(3, wf), 3).astype(np.float64))
                    except (TypeError, ValueError):
                        ctl_refused = True
                content_probe_controls += 1
                checks += 1
                if ctl_refused:
                    failures += 1
                    if witness is None:
                        witness = ("inadmissible-content-probe-control",
                                   probe_content_kind, wf)
                continue
            # handedOn, measured: a carrier the estimator did NOT turn away
            # reaches the scoring core in the content the check re-presented,
            # AND under that step's own description of it rather than the
            # caller's. The spy records the whole object that core was actually
            # handed and reads all six fields off it, so this leg is grounded
            # field by field on the real callee rather than on the shadow.
            if not refused:
                checks += 1
                real_handed = later_log[-1][2] if later_log else None
                if s_handed != real_handed:
                    failures += 1
                    if witness is None:
                        witness = ("handedOn", wf, wz, probe_form,
                                   s_handed, real_handed)
                    continue
                if probe_form != DENSE:
                    # A SPARSE carrier that CROSSED. Its layout is the only field
                    # of the handed-on carrier whose value the entry point could
                    # have chosen otherwise, so it gets its own NEGATIVE CONTROL:
                    # the scoring core is asked to traverse the same numbers in
                    # both sparse layouts, and the layout the entry point did NOT
                    # hand on must be one it REFUSES. Without that, "handed on
                    # row-indexed" would be indistinguishable from "handed on
                    # sparse", which is exactly the collapse this leg exists to
                    # rule out.
                    layout_crossings += 1
                    checks += 1
                    if real_handed[3] != BY_ROW:
                        failures += 1
                        if witness is None:
                            witness = ("crossing-layout", wf, wz, probe_form,
                                       real_handed[3])
                        continue
                    by_row = check_array(sparse.csr_matrix(zdata),
                                         accept_sparse="csr", dtype=np.float32)
                    by_col = check_array(sparse.csc_matrix(zdata),
                                         accept_sparse=["csc"],
                                         dtype=np.float32)
                    row_ok = col_refused = False
                    try:
                        orig(clf, by_row)
                        row_ok = True
                    except Exception:
                        row_ok = False
                    try:
                        orig(clf, by_col)
                    except Exception:
                        col_refused = True
                    layout_controls += 1
                    checks += 1
                    if not (row_ok and col_refused):
                        failures += 1
                        if witness is None:
                            witness = ("crossing-layout-control", wf, wz,
                                       row_ok, col_refused)
    finally:
        IsolationForest._compute_chunked_score_samples = orig
    return {"checks": checks, "failures": failures,
            "out_of_model": out_of_model, "aborts": aborts,
            "controls": controls, "label_aborts": label_aborts,
            "label_controls": label_controls,
            "probe_refusals": probe_refusals,
            "probe_controls": probe_controls,
            "content_aborts": content_aborts,
            "content_controls": content_controls,
            "content_probe_refusals": content_probe_refusals,
            "content_probe_controls": content_probe_controls,
            "layout_crossings": layout_crossings,
            "layout_controls": layout_controls,
            "witness": witness, "note": "ok"}


# --------------------------------------------------------------------------
# Tier C: mutation sensitivity
# --------------------------------------------------------------------------
MUTATIONS = {
    "no-conv": "traverses the caller's payload, not the checked one",
    "hoist": "verdict.md CE-1: traversal hoisted above the branch",
    "double": "verdict.md CE-2: extra discarded warm-up traversal",
    "decorative-traverse": ("verdict.md CE-3: traversal performed and counted, "
                            "its scores discarded, threshold taken over the "
                            "payload instead"),
    "second-pass": "a second consistency pass in the tail (reinstates warned)",
    "offset-const": "offset constant on both branches",
    "record-widened": "record not taken from the training carrier",
    "silent-later": "public scorer never warns about feature names",
    "accept-any-width": "public scorer never refuses a foreign width",
    "forward-caller-payload": ("public scorer checks correctly and then hands "
                               "the fitted model the caller's own carrier"),
    "forward-caller-description": ("public scorer converts the content "
                                   "correctly and hands it to the fitted model "
                                   "under the CALLER's description of itself, "
                                   "not the presentation's own"),
    "entry-accepts-column-layout": ("public scorer checks correctly, converts "
                                    "the content correctly and describes the "
                                    "presentation correctly, and hands the "
                                    "fitted model the sparse LAYOUT its own "
                                    "scoring path refuses"),
    "sparse-auto-traverses": ("abuses the storage-form limit: traverses on the "
                              "sparse auto lane, where the run does reach a "
                              "result and the traversal log is still pinned"),
    "precond-ignores-inspection": ("drops the inspectability precondition: "
                                   "describes a fit the label inspection "
                                   "refuses to let happen"),
    "precond-excludes-unnamed": ("over-claims the precondition: withholds the "
                                 "description from carriers that merely bear no "
                                 "labels, which the real code fits"),
    "later-admits-uninspectable": ("the collapsed reading: the public scorer "
                                   "checks the width and hands on a carrier "
                                   "whose labels it cannot inspect"),
    "later-warns-uninspectable": ("the public scorer reports a name-status "
                                  "delta for a carrier whose name status was "
                                  "never readable"),
    "sparse-auto-declines": ("abuses the storage-form limit: treats every "
                             "sparse carrier as declining, including the auto "
                             "lane that never enters the scoring path"),
    "precond-ignores-content": ("drops the content precondition: describes a fit "
                                "the re-presentation step refuses to let happen"),
    "precond-excludes-converted": ("over-claims the content precondition: "
                                   "withholds the description from every carrier "
                                   "the check has to convert, which the real code "
                                   "fits"),
    "later-admits-inadmissible-content": ("the content analogue of the collapsed "
                                          "reading: the public scorer checks the "
                                          "labels and the width and hands on a "
                                          "carrier whose content the check "
                                          "declines"),
    "content-rewrite-as-refusal": ("escalates 'the check had to convert this "
                                   "content' into a refusal, so the public "
                                   "scorer turns away most of what it exists to "
                                   "accept"),
}


def main() -> int:
    problems = []

    (bad, oom, aborts, excluded, uprobes, cexcluded, cprobes, crossings,
     witness) = compare_symbolic(random.Random(SEED), N)
    if bad:
        print(f"DISAGREE (tier A) {witness}", file=sys.stderr)
        problems.append(f"symbolic-fuzz:{bad}")
    if excluded == 0 or uprobes == 0:
        # a precondition no draw ever fell outside, or a positive obligation no
        # draw ever exercised, is not being tested at all
        print("NOTE tier A never drew a carrier with uninspectable labels",
              file=sys.stderr)
        problems.append("inspectability-unexercised")
    if cexcluded == 0 or cprobes == 0:
        print("NOTE tier A never drew a carrier whose content the check "
              "declines", file=sys.stderr)
        problems.append("content-admissibility-unexercised")
    if crossings == 0:
        # the handed-on leg's LAYOUT half only has content where a SPARSE carrier
        # crosses into the fitted model; if no draw did, the layout is untested
        print("NOTE tier A never let a sparse carrier cross into the fitted "
              "model, so the handed-on layout is unexercised", file=sys.stderr)
        problems.append("crossing-layout-unexercised")

    caught = {}
    for mut in MUTATIONS:
        mbad = compare_symbolic(random.Random(SEED + 1), N_SENS, mut=mut)[0]
        caught[mut] = mbad
        if mbad == 0:
            print(f"INSENSITIVE: mutation {mut!r} "
                  f"({MUTATIONS[mut]}) NOT caught", file=sys.stderr)
            problems.append(f"insensitive:{mut}")

    real = real_leg(N_REAL)
    rchecks, rfail, rnote = real["checks"], real["failures"], real["note"]
    room, raborts, rctl = (real["out_of_model"], real["aborts"],
                           real["controls"])
    if rfail:
        print(f"DISAGREE (tier B, real code) {real['witness']}", file=sys.stderr)
        problems.append(f"real-code:{rfail}")
    if rnote == "ok" and (raborts == 0 or rctl == 0):
        # the storage-form limit is only documented if it was exercised
        print("NOTE tier B never reached the storage-form abort",
              file=sys.stderr)
        problems.append("storage-form-unexercised")
    if rnote == "ok" and (real["content_aborts"] == 0
                          or real["content_controls"] == 0
                          or real["content_probe_refusals"] == 0
                          or real["content_probe_controls"] == 0):
        # the content precondition and the positive later-carrier obligation are
        # only grounded against the real callee if the real callee met such a
        # carrier, in both directions and with its control
        print("NOTE tier B never presented content the check declines to the "
              "real code, so neither half of that leg is grounded",
              file=sys.stderr)
        problems.append("content-admissibility-ungrounded")
    if rnote == "ok" and (real["layout_crossings"] == 0
                          or real["layout_controls"] == 0):
        # the handed-on LAYOUT is only grounded against the real callee if a
        # sparse carrier actually crossed into the fitted model and the control
        # that the OTHER sparse layout is refused actually ran
        print("NOTE tier B never let a sparse carrier cross into the scoring "
              "core, so the handed-on layout is ungrounded", file=sys.stderr)
        problems.append("crossing-layout-ungrounded")
    if rnote == "ok" and (real["label_aborts"] == 0
                          or real["label_controls"] == 0
                          or real["probe_refusals"] == 0
                          or real["probe_controls"] == 0):
        # the precondition and the positive later-carrier obligation are only
        # grounded against the real callee if the real callee met such a carrier
        print("NOTE tier B never presented uninspectable labels to the real "
              "code, so neither half of that leg is grounded", file=sys.stderr)
        problems.append("inspectability-ungrounded")
    if rnote != "ok":
        print(f"NOTE tier B skipped: {rnote}", file=sys.stderr)
        if os.path.isdir("/testbed"):
            # in the instance image the repo under test IS importable; a skip
            # here would mean the real-code leg silently vanished.
            problems.append(f"real-code-leg-unavailable:{rnote}")

    report = {
        "inputs": N,
        "disagreements": bad,
        "out_of_model_name_identity": oom,
        "out_of_model_storage_form": aborts,
        "precondition_excluded": excluded,
        "uninspectable_probes": uprobes,
        "content_precondition_excluded": cexcluded,
        "inadmissible_content_probes": cprobes,
        "sparse_crossings": crossings,
        "mutations_caught": {k: v for k, v in caught.items()},
        "real_code_checks": rchecks,
        "real_code_failures": rfail,
        "real_code_out_of_model": room,
        "real_code_storage_aborts": raborts,
        "real_code_dense_controls": rctl,
        "real_code_label_aborts": real["label_aborts"],
        "real_code_label_controls": real["label_controls"],
        "real_code_probe_refusals": real["probe_refusals"],
        "real_code_probe_controls": real["probe_controls"],
        "real_code_layout_crossings": real["layout_crossings"],
        "real_code_layout_controls": real["layout_controls"],
        "real_code_content_aborts": real["content_aborts"],
        "real_code_content_controls": real["content_controls"],
        "real_code_content_probe_refusals": real["content_probe_refusals"],
        "real_code_content_probe_controls": real["content_probe_controls"],
        "real_code_note": rnote,
        "seed": SEED,
    }
    print(json.dumps(report, sort_keys=True))
    if problems:
        print("G-CONF FAIL: " + "; ".join(problems))
        return 1
    n_caught = sum(1 for v in caught.values() if v)
    print(f"G-CONF: {N} inputs, {bad} disagreements; "
          f"{rchecks} real-code checks, {rfail} failures; "
          f"{raborts} storage-form aborts with {rctl} dense controls; "
          f"{real['label_aborts']} label-inspection aborts with "
          f"{real['label_controls']} controls and {real['probe_refusals']} "
          f"uninspectable probes turned away with {real['probe_controls']} "
          f"controls; {real['content_aborts']} content aborts with "
          f"{real['content_controls']} controls and "
          f"{real['content_probe_refusals']} inadmissible-content probes turned "
          f"away with {real['content_probe_controls']} controls; "
          f"{n_caught}/{len(MUTATIONS)} mutations caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
