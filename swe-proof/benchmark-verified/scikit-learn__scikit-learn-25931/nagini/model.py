"""Twin-artifact model for scikit-learn__scikit-learn-25931.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An anomaly estimator is fitted on a data table. Fitting performs one
  data-preparation pass that, when the table carries column labels, records that
  the estimator was fitted with labels and yields an unlabelled numeric matrix.
  When a threshold-calibration setting other than the automatic default is
  requested, fitting must additionally derive a calibration offset from per-row
  scores of that already-prepared matrix; the offset is needed afterwards, so it
  is a required product of fitting in that case.

  A label-consistency check compares the labels present on a matrix against the
  labels recorded at fit time and emits a mismatch advisory to the caller
  whenever the matrix carries no labels while the estimator was recorded as
  fitted-with-labels. Because the prepared matrix is always unlabelled, applying
  such a check to it on a labelled fit would emit a spurious advisory. The
  required behaviour: fitting emits NO label-mismatch advisory, on any input.

  The advisory is a side effect on the estimator, not a value the caller may
  keep or discard: scoring routines mutate the estimator's running advisory
  tally as a side effect of being called, so the tally records what was actually
  emitted regardless of what the caller does with any return value. The
  calibration offset is likewise not a value the caller may fabricate: it is
  furnished only by scoring per-row over the prepared training matrix, an act
  that marks the estimator with an unforgeable token witnessing that the offset
  was produced from per-row scores of that matrix. Fitting's contract requires
  both that the tally end at zero and that, when calibration is requested, the
  offset was set and carries that token.

The data table / numeric matrix is modelled as a minimal record carrying only
the touched field (whether labels are present) plus its prepared form. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# Unforgeable capability token: marks an estimator whose calibration offset was
# produced by scoring per-row over the prepared training matrix. It is an
# abstract @Predicate (the implementation cannot Fold it into existence) and is
# granted ONLY by the in-fit per-row scoring routine's postcondition (below), so
# an offset carrying it can only have come from that routine.
@ContractOnly
@Predicate
def offset_from_unvalidated_scoring(est: 'Estimator') -> bool:
    pass


# Unforgeable token marking the fit's OWN raw training input. It is granted only
# to fitting's parameter (the impl cannot Fold an abstract @Predicate into
# existence), so the impl cannot manufacture a foreign matrix that passes for the
# fit's raw input.
@ContractOnly
@Predicate
def raw_fit_input(X: 'Matrix') -> bool:
    pass


# Unforgeable token marking the prepared form of the fit's own raw input.
# Granted only by the preparation pass below, on the matrix it produces.
@ContractOnly
@Predicate
def prepared_input(X: 'Matrix') -> bool:
    pass


# The fitting data-preparation pass, modelled as a contracted callee. It casts
# the raw training input to an unlabelled numeric matrix. It CONSUMES the
# raw-input token (so it can only be applied to the fit's actual input, never a
# fabricated matrix) and GRANTS the prepared-input token on its result (so a
# routine fed that result is operating on the actual training data). It records
# the labels for later consistency checks and never emits a mismatch advisory.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
def prepare(X_raw: 'Matrix') -> 'Matrix':
    Requires(Acc(X_raw.has_labels, 1 / 2))
    Requires(raw_fit_input(X_raw))
    Requires(MustTerminate(2))
    Ensures(Acc(X_raw.has_labels, 1 / 2))
    Ensures(Acc(Result().has_labels))
    Ensures(X_raw.has_labels == Old(X_raw.has_labels))
    # The prepared form is always unlabelled.
    Ensures(Result().has_labels == False)
    Ensures(prepared_input(Result()))


# The in-fit per-row scoring routine, modelled as a contracted callee that
# fitting invokes on the prepared training matrix. It produces per-row scores of
# its argument and furnishes the calibration offset -- setting it and marking the
# estimator with the token witnessing the offset came from per-row scores of that
# matrix. It performs no label-consistency check, so it leaves the estimator's
# advisory tally unchanged. There is no other granter of the offset token, so an
# offset carrying it can only have come from here. Its argument must be the
# prepared form of the fit's own input (it carries the prepared-input token);
# the prepared form is unlabelled.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
def prepared_scorer(self: 'Estimator', X: 'Matrix') -> None:
    Requires(Acc(self.fitted_with_labels, 1 / 2))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(self.offset_set))
    Requires(Acc(X.has_labels, 1 / 2))
    Requires(X.has_labels == False)
    # The argument must be the prepared form of the fit's actual input (carrying
    # the prepared-input token), never a fabricated or foreign matrix.
    Requires(prepared_input(X))
    Requires(MustTerminate(6))
    Ensures(Acc(self.fitted_with_labels, 1 / 2))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(self.offset_set))
    Ensures(Acc(X.has_labels, 1 / 2))
    # No label-consistency check is run, so the advisory tally is unchanged.
    Ensures(self.fit_advisories == Old(self.fit_advisories))
    # The offset is produced by scoring this matrix per-row: it is now set and
    # carries the token witnessing it came from per-row scores of the matrix.
    Ensures(self.offset_set)
    Ensures(offset_from_unvalidated_scoring(self))
# axioms-end


# pure-start
@Pure
def mismatch_advisory(arg_has_labels: bool, fitted_with_labels: bool) -> int:
    """Number of label-mismatch advisories a single label-consistency check
    emits for one matrix. Deep model of the library's feature-name consistency
    check: an advisory fires exactly when the matrix carries no labels while the
    estimator was fitted with labels; all three other label combinations are
    silent for this advisory. Returns 0 or 1.
    """
    if (not arg_has_labels) and fitted_with_labels:
        return 1
    return 0
# pure-end


class Estimator:
    # An anomaly estimator. The touched fit-time state is modelled:
    #  * fitted_with_labels: whether fitting recorded that the data table carried
    #    column labels;
    #  * fit_advisories: a running tally of label-mismatch advisories emitted
    #    during fitting -- mutated by the SCORING ROUTINES as a side effect of
    #    being called, so it cannot be discarded by the caller;
    #  * offset_set: whether the required calibration offset was produced.
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        self.fitted_with_labels = False  # type: bool
        self.fit_advisories = 0  # type: int
        self.offset_set = False  # type: bool
        Ensures(Acc(self.fitted_with_labels))  # type: ignore[name-defined]
        Ensures(Acc(self.fit_advisories))  # type: ignore[name-defined]
        Ensures(Acc(self.offset_set))  # type: ignore[name-defined]
        Ensures(self.fitted_with_labels == False)
        Ensures(self.fit_advisories == 0)
        Ensures(self.offset_set == False)


class Matrix:
    # A data table / numeric matrix. Only the touched field is modelled: whether
    # the object carries column labels (a labelled DataFrame vs. an unlabelled
    # numeric array). A prepared matrix is always unlabelled.
    def __init__(self, has_labels: bool) -> None:
        Requires(MustTerminate(1))
        self.has_labels = has_labels  # type: bool
        Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
        Ensures(self.has_labels == has_labels)


# ---------------------------------------------------------------------------
# Site 1: a public scoring routine. As an UNCONDITIONAL effect of being called,
# it runs one label-consistency check on its caller-supplied argument before
# scoring; that check's advisory is added to the estimator's running tally by the
# call itself. It does NOT furnish a token-bearing offset. The per-row scores it
# produces are not modelled (no tested behaviour observes their values) -- only
# the advisory side effect is.
# ---------------------------------------------------------------------------
def validating_scorer(self: Estimator, X: Matrix) -> None:
    # pre-conditions-start
    Requires(Acc(self.fitted_with_labels, 1 / 2))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(X.has_labels, 1 / 2))
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted_with_labels, 1 / 2))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(X.has_labels, 1 / 2))
    # Being called runs the consistency check on the argument: its advisory is
    # added to the tally as a side effect (whatever the caller does afterwards,
    # the emission has happened).
    Ensures(self.fit_advisories ==
            Old(self.fit_advisories)
            + mismatch_advisory(X.has_labels, self.fitted_with_labels))
    # post-conditions-end
    # impl-start
    # one label-consistency check on the caller-supplied argument, whose advisory
    # is recorded on the estimator as it is emitted
    self.fit_advisories = self.fit_advisories \
        + mismatch_advisory(X.has_labels, self.fitted_with_labels)
    # ... per-row scoring of the validated argument follows (scores unmodelled).
    # impl-end


# ---------------------------------------------------------------------------
# Site 2: fitting. Runs one preparation pass recording whether the raw table
# carried labels and yielding a prepared (unlabelled) matrix; then, when
# calibration is requested, derives the offset from per-row scores of that
# prepared matrix. Fitting must emit NO label-mismatch advisory, and when
# calibration is requested the offset must have been produced from per-row scores
# of the prepared matrix (it carries the token).
# ---------------------------------------------------------------------------
def fit_offset(self: Estimator, X_raw: Matrix, calibration_requested: bool) -> None:
    # pre-conditions-start
    Requires(Acc(self.fitted_with_labels))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(self.offset_set))
    Requires(self.fit_advisories == 0)
    Requires(self.offset_set == False)
    Requires(Acc(X_raw.has_labels, 1 / 2))
    # X_raw is the fit's own raw training input (it carries the raw-input token).
    Requires(raw_fit_input(X_raw))
    Requires(MustTerminate(18))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted_with_labels))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(self.offset_set))
    Ensures(Acc(X_raw.has_labels, 1 / 2))
    # Fitting records whether the raw table carried labels.
    Ensures(self.fitted_with_labels == Old(X_raw.has_labels))
    # Fitting emits NO label-mismatch advisory, whether or not calibration is
    # requested and whatever labels the raw table carried.
    Ensures(self.fit_advisories == 0)
    # When calibration is requested, the offset is a REQUIRED product of fitting:
    # it must have been set, AND it must carry the token witnessing it was
    # produced from per-row scores of the prepared training matrix (so it cannot
    # have come from a label-checking pass, nor been fabricated without scoring).
    Ensures(Implies(calibration_requested, self.offset_set))
    Ensures(Implies(calibration_requested, offset_from_unvalidated_scoring(self)))
    # Conversely, when calibration is NOT requested the offset is NOT produced by
    # per-row scoring: fitting must take the short-circuit that sets the offset
    # without scoring the prepared matrix. So offset-set-by-scoring holds exactly
    # when calibration is requested -- the scorer is reached iff calibration_requested.
    Ensures(self.offset_set == calibration_requested)
    # post-conditions-end
    # impl-start
    # the fitting preparation pass: record whether the table carried labels, then
    # prepare the raw input to the unlabelled numeric matrix. This pass records
    # the labels for later consistency checks and never emits a mismatch advisory.
    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # derive the calibration offset from per-row scores of the ALREADY-
        # prepared matrix (emits no advisory and furnishes the token-bearing
        # offset).
        prepared_scorer(self, Xp)
    # impl-end
