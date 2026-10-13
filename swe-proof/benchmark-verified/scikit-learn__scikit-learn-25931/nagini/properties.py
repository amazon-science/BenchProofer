# properties.py — PBT falsification battery for scikit-learn__scikit-learn-25931.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec (only an impl region differs,
# guaranteed by region-surgery via _swap, which edits ONLY text strictly inside
# a `# impl-start`/`# impl-end` block) and are checked by Nagini verify +
# markers.same_spec. Axiom cases are real-callee probes run in the instance image.
#
# Defended surface — the patched site is `fit_offset` (= IsolationForest.fit's
# offset hunk). Gold edit: route the in-fit offset scoring through the
# NON-validating private `_score_samples` instead of the validating public
# `score_samples`, so the already-prepared (unlabelled) array is not validated a
# second time (which on a labelled fit would emit the spurious "X does not have
# valid feature names" UserWarning -> F2P).
#
#   fit_offset(self, X_raw, calibration_requested):
#     Requires: Acc(self.fitted_with_labels) | Acc(self.fit_advisories)
#               | Acc(self.offset_set)            -- FULL perm on estimator state
#               self.fit_advisories == 0; self.offset_set == False
#               Acc(X_raw.has_labels, 1/2)        -- READ-ONLY input (half perm)
#               raw_fit_input(X_raw)              -- unforgeable provenance token
#     Ensures : self.fitted_with_labels == Old(X_raw.has_labels)
#               self.fit_advisories == 0                                 [LB: F2P]
#               Implies(calibration_requested, self.offset_set)
#               Implies(calibration_requested, offset_from_unvalidated_scoring(self))
#               self.offset_set == calibration_requested                 [biconditional]
#
# The advisory is modelled as a SIDE EFFECT on shared estimator state
# (fit_advisories, mutated by the scoring routines as the act of being called),
# NOT a discardable return value. The offset provenance is an UNFORGEABLE
# @Predicate token offset_from_unvalidated_scoring granted ONLY by prepared_scorer;
# a second pair of tokens (raw_fit_input / prepared_input) binds the scored matrix
# to fit's OWN prepared input. The control-flow effect (which scorer is invoked)
# is invisible to any value-level postcondition; the model pins it through these
# side-effect + token clauses. See 'assessment' for the ungrounded-oracle analysis.
#
# This is a multi-pass-hardened spec (4 respec rounds; 11 documented G-EQ
# attacks). The battery below reproduces the reasoned attacks as same-spec rivals
# (region-surgery on fit_offset's impl ONLY) plus the MANDATORY frame-mutation
# probe on the read-only X_raw, a structurally-different positive control, and an
# admissibility witness; and validates every consumed/A-reference axiom against
# the real sklearn callees in Docker.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25931"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no floats modeled)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen fit_offset impl body (lies ENTIRELY between fit_offset's
# # impl-start / # impl-end at model.py:241-252). Every rival _swaps a substring
# of THIS block, so the spec view (axioms/pure/pre/post + signatures) is never
# touched => same_spec holds for every case.
_FIT_GOLD = """    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # derive the calibration offset from per-row scores of the ALREADY-
        # prepared matrix (emits no advisory and furnishes the token-bearing
        # offset).
        prepared_scorer(self, Xp)"""


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY: X_raw.has_labels is read-only, Acc(...,1/2)).
#    A rival that WRITES to the read-only input to satisfy the postcondition
#    vacuously. Here it tries to "prepare in place" -- overwrite X_raw.has_labels
#    to the unlabelled state instead of going through the `prepare` callee -- then
#    score X_raw directly. Writing X_raw.has_labels needs FULL permission; the
#    contract grants only Acc(X_raw.has_labels, 1/2) (re-granted on exit), so the
#    store MUST fail for insufficient permission. The gold token/advisory clauses
#    are kept verbatim so the rejection is attributable to the write, not them.
# ---------------------------------------------------------------------------
_frame_mutation = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    # frame-mutation attack: instead of building the prepared matrix via the
    # `prepare` callee, mutate the read-only input in place to the unlabelled
    # state and score it directly. Writing X_raw.has_labels needs FULL permission
    # (we hold only Acc(X_raw.has_labels, 1/2)) => must fail on the store.
    X_raw.has_labels = False
    if calibration_requested:
        prepared_scorer(self, X_raw)""",
)


# ---------------------------------------------------------------------------
# 2. CONTROL-FLOW-EFFECT (attack11, 3rd-pass hole): drop the
#    `if calibration_requested:` guard and invoke the scorer UNCONDITIONALLY.
#    Both calibration Implies-clauses are then (positively) satisfied and the
#    tally stays 0, but offset_set becomes True regardless of calibration.
#    Rejected by the biconditional Ensures(self.offset_set == calibration_requested):
#    prepared_scorer is the SOLE granter of offset_set, so calling it when
#    calibration_requested==False makes offset_set True != False.
# ---------------------------------------------------------------------------
_uncond_scorer = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    # control-flow-effect attack: score UNCONDITIONALLY (drop the calibration
    # guard), so offset_set is True even when calibration is not requested.
    prepared_scorer(self, Xp)""",
)


# ---------------------------------------------------------------------------
# 3. THE LITERAL PRE-PATCH BUG (attack3): route the in-fit offset scoring through
#    the VALIDATING public scorer (the bug). validating_scorer adds
#    mismatch_advisory(Xp.has_labels=False, fitted_with_labels=True)==1 to the
#    tally on a labelled fit, AND grants no token. Rejected by Ensures
#    self.fit_advisories == 0 (the undiscardable side effect) -- this is exactly
#    model_prepatch.py's G-DIFF failure, the bug the F2P test catches.
# ---------------------------------------------------------------------------
_validating_path = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # pre-patch bug: route through the VALIDATING public scorer, which runs a
        # second consistency pass on the prepared (unlabelled) array and emits the
        # spurious advisory (mutating the tally) -- the F2P warning.
        validating_scorer(self, Xp)""",
)


# ---------------------------------------------------------------------------
# 4. SKIP THE SCORER (attack2): omit the offset scoring entirely. offset_set
#    stays False; on a calibration fit this violates Implies(calibration_requested,
#    offset_set) (and offset_set == calibration_requested). Refines to never
#    assigning self.offset_ -> P2P decision_function/score_samples AttributeError.
# ---------------------------------------------------------------------------
_skip_scorer = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    # skip-scorer attack: never derive the offset (offset_set stays False).""",
)


# ---------------------------------------------------------------------------
# 5. FORGE THE OFFSET TOKEN (attack4): set offset_set = True directly without
#    scoring (no prepared_scorer call). The advisory tally stays 0 and offset_set
#    is True, but the UNFORGEABLE @Predicate offset_from_unvalidated_scoring(self)
#    is granted ONLY by prepared_scorer -- the impl cannot Fold an abstract
#    predicate -- so the token clause cannot be discharged. Rejected by
#    Implies(calibration_requested, offset_from_unvalidated_scoring(self)).
# ---------------------------------------------------------------------------
_forge_token = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # forge-token attack: claim the offset is set without scoring. offset_set
        # is True but the unforgeable scoring token is never granted.
        self.offset_set = True""",
)


# ---------------------------------------------------------------------------
# 6. RAW-MATRIX (attack8, recover-verdict hole): call the no-validation scorer on
#    the RAW (possibly-labelled) table instead of the prepared form. The real
#    _score_samples(<raw DataFrame>) raises ValueError ('X should be in np.ndarray
#    format') -> fit crashes -> F2P + most P2P fail. Rejected by prepared_scorer's
#    precondition X.has_labels == False (X_raw may carry labels).
# ---------------------------------------------------------------------------
_raw_matrix = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # raw-matrix attack: score the RAW table, not the prepared form.
        prepared_scorer(self, X_raw)""",
)


# ---------------------------------------------------------------------------
# 7. FABRICATED-MATRIX (attack10, 2nd-pass hole): score a freshly-constructed
#    unlabelled Matrix(False) instead of fit's own prepared input. It satisfies
#    X.has_labels == False, but lacks the prepared_input provenance token (granted
#    only by `prepare` on fit's own X_raw). Refines to
#    np.percentile(_score_samples(<foreign array>), ...) -> WRONG offset_ ->
#    P2P test_iforest_works[42-0.25] predictions wrong -> does NOT resolve.
#    Rejected by prepared_scorer's precondition prepared_input(X) (insufficient
#    permission to the unforgeable token on a fabricated matrix).
# ---------------------------------------------------------------------------
_fabricated_matrix = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # fabricated-matrix attack: score a fresh unlabelled matrix, not fit's own
        # prepared input. It lacks the prepared_input provenance token.
        foreign = Matrix(False)
        prepared_scorer(self, foreign)""",
)


# ---------------------------------------------------------------------------
# 8. SKIP RECORDING FIT-TIME LABELS (partial-domain / supporting near-miss): do
#    not record fit-time labels (leave self.fitted_with_labels at its False init);
#    on a labelled fit this violates fitted_with_labels == Old(X_raw.has_labels).
#    Refines to not setting feature_names_in_, so later consistency checks would
#    not fire on subsequent unlabelled calls (behaviour diverges from gold). Cheap
#    supporting case; still carries a refinement.
# ---------------------------------------------------------------------------
_skip_record_labels = _swap(
    _BASE,
    _FIT_GOLD,
    """    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    # skip-record-labels attack: never record whether the table carried labels.
    if calibration_requested:
        prepared_scorer(self, Xp)""",
)


# ---------------------------------------------------------------------------
# 9. POSITIVE CONTROL (soundness): a structurally-different but CORRECT impl that
#    records the fit-time labels AFTER scoring (a different statement order than
#    model.py). prepared_scorer needs only Acc(self.fitted_with_labels, 1/2)
#    (read), so its value need not yet be set; fit_offset retains full perm to
#    write it afterwards. Old(X_raw.has_labels) is captured at entry, so recording
#    fitted_with_labels last still satisfies the postcondition. MUST VERIFY (else
#    SPEC-TOO-STRONG). This is exactly the documented positive control (refinement.md).
# ---------------------------------------------------------------------------
_pos_control = _swap(
    _BASE,
    _FIT_GOLD,
    """    # positive control: record labels AFTER scoring (different statement order).
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        prepared_scorer(self, Xp)
    self.fitted_with_labels = X_raw.has_labels""",
)


# ---------------------------------------------------------------------------
# 10. ADMISSIBILITY witness. fit_offset's own precondition includes the abstract
#     token raw_fit_input(X_raw), which the impl cannot Fold into existence, so a
#     self-call to fit_offset cannot be set up (and is not the meaningful check
#     here). Instead we witness that the PUBLIC scoring routine's precondition
#     admits a normal F2P-shaped input: construct a fresh Estimator + an unlabelled
#     Matrix and call validating_scorer on them, asserting the post-condition is
#     usable (an unlabelled-fit estimator scoring an unlabelled arg emits 0
#     advisories: mismatch_advisory(False, False) == 0). If validating_scorer's
#     Requires were too strong for a normal input this call would not establish.
#     MUST VERIFY (else PRECOND-TOO-STRONG). The fresh objects carry full perm, so
#     fit's own X_raw permissions are untouched; modular verification uses
#     validating_scorer's own contract.
# ---------------------------------------------------------------------------
_admiss = _swap(
    _BASE,
    _FIT_GOLD,
    """    self.fitted_with_labels = X_raw.has_labels
    # admissibility witness: the public scoring routine's Requires admits a normal
    # F2P-shaped input (a fresh estimator + an unlabelled matrix).
    e2 = Estimator()
    m2 = Matrix(False)
    validating_scorer(e2, m2)
    Assert(e2.fit_advisories == 0)
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        prepared_scorer(self, Xp)""",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-readonly-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mutation,
        "refinement": (
            "Overwriting X_raw.has_labels in place needs FULL permission; the "
            "contract grants only Acc(X_raw.has_labels, 1/2). A faithful real patch "
            "that mutated the caller's input DataFrame/array in place (relabelling "
            "it) instead of going through _validate_data would corrupt the caller's "
            "object and the recorded feature_names_in_ provenance -- the F2P "
            "warning-absence and the P2P offset/decision_function consumers would "
            "diverge from gold, so it would NOT resolve. Verifying here would be a "
            "verify-not-resolve break."
        ),
        "rationale": (
            "Rejection comes from the PERMISSION SYSTEM: the store "
            "X_raw.has_labels = False requires full permission on X_raw.has_labels, "
            "but fit_offset holds only Acc(X_raw.has_labels, 1/2) (read-only), "
            "re-granted on exit. The verifier fails on insufficient permission to "
            "assign X_raw.has_labels, independent of the (verbatim) token/advisory "
            "post-clauses."
        ),
    },
    {
        "id": "control-flow-unconditional-scorer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _uncond_scorer,
        "refinement": (
            "Dropping the `if calibration_requested:` guard scores even in the gold "
            "contamination=='auto' branch, where the refinement computes "
            "np.percentile(self._score_samples(X), 100.0 * 'auto') -> TypeError: "
            "can't multiply sequence by non-int -> fit crashes -> 3/5 P2P fail "
            "(gold passes 5/5) -> does NOT resolve. The control-flow effect (was "
            "the scorer reached?) is invisible to any value-level postcondition; "
            "only the biconditional pins it."
        ),
        "rationale": (
            "Rejection from Ensures(self.offset_set == calibration_requested): "
            "prepared_scorer is the SOLE granter of offset_set==True (offset_set "
            "starts False per the precondition and the impl never assigns it "
            "directly), so calling it unconditionally makes offset_set True != "
            "calibration_requested when calibration is not requested."
        ),
    },
    {
        "id": "validating-path-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _validating_path,
        "refinement": (
            "This IS the literal pre-patch line: derive the offset via the "
            "validating public score_samples, which re-runs _validate_data(reset="
            "False) -- a second consistency pass -- on the already-prepared "
            "unlabelled array while feature_names_in_ is set, emitting the spurious "
            "'X does not have valid feature names' UserWarning. The F2P test "
            "(warnings.simplefilter('error', UserWarning); model.fit(X)) raises -> "
            "does NOT resolve. model_prepatch.py reproduces exactly this (G-DIFF)."
        ),
        "rationale": (
            "Rejection from Ensures(self.fit_advisories == 0): validating_scorer's "
            "post adds mismatch_advisory(Xp.has_labels==False, fitted_with_labels=="
            "True) == 1 to the tally as a side effect of being called; the count is "
            "undiscardable shared estimator state, so fit_advisories ends at 1 != 0."
        ),
    },
    {
        "id": "skip-scorer-no-offset",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _skip_scorer,
        "refinement": (
            "Omitting the offset scoring leaves self.offset_ unassigned in the "
            "non-auto branch, so the P2P consumers (decision_function / predict / "
            "score_samples and test_iforest_works[42-0.25]) hit AttributeError -> "
            "does NOT resolve."
        ),
        "rationale": (
            "Rejection from Implies(calibration_requested, self.offset_set) and "
            "Ensures(self.offset_set == calibration_requested): with no scorer call "
            "offset_set stays False, but a calibration fit requires it True."
        ),
    },
    {
        "id": "forge-offset-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _forge_token,
        "refinement": (
            "Setting offset_set=True without scoring invents an offset_ that was "
            "never derived from per-row scores of the training matrix; the real "
            "patch has no way to produce a meaningful offset_ without scoring, so a "
            "fabricated/garbage offset_ breaks the P2P prediction thresholds -> "
            "does NOT resolve."
        ),
        "rationale": (
            "Rejection from Implies(calibration_requested, "
            "offset_from_unvalidated_scoring(self)): the token is an abstract "
            "@Predicate granted ONLY by prepared_scorer's postcondition; the impl "
            "cannot Fold it into existence (insufficient permission to the "
            "predicate), so directly setting offset_set leaves the token ungranted."
        ),
    },
    {
        "id": "raw-matrix-out-of-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _raw_matrix,
        "refinement": (
            "Feeding the no-validation scorer the RAW (possibly-labelled) table "
            "refines to self._score_samples(<raw DataFrame>), which raises "
            "ValueError ('X should be in np.ndarray format') inside "
            "_compute_chunked_score_samples -> fit crashes -> F2P + most P2P fail "
            "-> does NOT resolve."
        ),
        "rationale": (
            "Rejection from prepared_scorer's precondition Requires(X.has_labels == "
            "False): X_raw may carry labels (on a labelled fit X_raw.has_labels == "
            "True), so the callee precondition might not hold."
        ),
    },
    {
        "id": "fabricated-matrix-wrong-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fabricated_matrix,
        "refinement": (
            "Scoring a freshly-constructed Matrix(False) instead of fit's own "
            "prepared input refines to np.percentile(self._score_samples(<foreign "
            "array>), ...), yielding a WRONG offset_ (axiom_check confirms the gold "
            "offset_ differs from scoring a foreign array) -> P2P "
            "test_iforest_works[42-0.25] predictions wrong -> does NOT resolve. The "
            "value abstraction drops the offset value, so only the provenance token "
            "separates this from gold."
        ),
        "rationale": (
            "Rejection from prepared_scorer's precondition Requires(prepared_input"
            "(X)): prepared_input is an abstract @Predicate granted ONLY by "
            "`prepare` (on fit's own X_raw, which carries raw_fit_input); a "
            "fabricated Matrix(False) lacks the token -> insufficient permission to "
            "prepared_input(X)."
        ),
    },
    {
        "id": "skip-record-fit-labels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _skip_record_labels,
        "refinement": (
            "Not recording fit-time labels refines to never setting "
            "feature_names_in_; the estimator would not flag later unlabelled calls "
            "and the recorded provenance diverges from gold's, breaking the "
            "consistency behaviour the issue is about. Cheap supporting near-miss, "
            "but with a real refinement."
        ),
        "rationale": (
            "Rejection from Ensures(self.fitted_with_labels == Old(X_raw.has_labels"
            ")): with no assignment, fitted_with_labels stays at its False init, so "
            "on a labelled fit (Old(X_raw.has_labels)==True) it is False != True."
        ),
    },
    {
        "id": "pos-control-record-labels-last",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control,
        "rationale": (
            "Structurally different (records fit-time labels AFTER scoring instead "
            "of before) but behaviourally identical correct impl. prepared_scorer "
            "needs only Acc(self.fitted_with_labels, 1/2) (read), and fit_offset "
            "retains full perm to write it afterwards; Old(X_raw.has_labels) is "
            "captured at entry. MUST verify, else SPEC-TOO-STRONG. This is the "
            "documented positive control (refinement.md)."
        ),
    },
    {
        "id": "admissibility-public-scorer-normal-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "Witness that a normal F2P-shaped input establishes a modeled "
            "function's Requires: a fresh Estimator() + unlabelled Matrix(False) "
            "satisfy validating_scorer's Requires (Acc(self.fitted_with_labels,1/2) "
            "| Acc(self.fit_advisories) | Acc(X.has_labels,1/2)), and its "
            "postcondition is usable (mismatch_advisory(False,False)==0 so the "
            "tally stays 0). fit_offset's own Requires includes the abstract "
            "raw_fit_input(X_raw) token, which the impl cannot Fold, so a "
            "fit_offset self-call is not constructible -- this witnesses the "
            "establishable precondition instead. MUST verify, else PRECOND-TOO-STRONG."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. The bundle has ONE consumed @ContractOnly callee (prepared_scorer
# <-> IsolationForest._score_samples, patch-INTRODUCED) granting one abstract
# token (offset_from_unvalidated_scoring); a consumed+A-reference callee (prepare
# <-> _validate_data(reset=True)); and one A-reference deep model
# (mismatch_advisory <-> _check_feature_names(reset=False)). We reuse and
# STRENGTHEN axiom_check.py's executable soundness logic, calling the REAL
# sklearn callees in-container. Per pilot bug #6 the runner mounts only the probe
# at /work, so each probe is self-contained (imports sklearn/numpy/pandas/stdlib,
# opens nothing on disk). Per bug #4 every probe EXECUTES the real callee, never
# scrapes source. Per bug #5 no file reads, so locale is moot.
#
# Patch-state split (axiom_check.py Defect-4 logic): the unchanged base callees
# (_check_feature_names, _validate_data, public score_samples) are
# patch-INDEPENDENT (apply_gold=False -- the obligation holds at base too); the
# introduced _score_samples + end-to-end fit behaviour + offset provenance are
# patch-DEPENDENT (apply_gold=True).
# ---------------------------------------------------------------------------

# (1) A-reference soundness for mismatch_advisory / prepare (patch-independent):
#     the real _check_feature_names(reset=False) advisory == mismatch_advisory
#     over all 4 (arg,fitted) combos, AND _validate_data(reset=True) drops labels
#     (prepared form is unlabelled), AND the public score_samples still validates
#     its own arg (1 advisory). Fuzzed boundaries: both-labelled, both-unlabelled,
#     and the two mixed cases (only (unlabelled-arg, labelled-fit) advises).
_AX_BASE_PROBE = r'''
import sys
import warnings
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.ensemble import IsolationForest

def mismatch_advisory(arg_has_labels, fitted_with_labels):
    return 1 if ((not arg_has_labels) and fitted_with_labels) else 0

class _Probe(BaseEstimator):
    pass

def _make_frame(labelled):
    import pandas as pd
    if labelled:
        return pd.DataFrame({"a": [-1.1, 0.3, 0.5, 100.0]})
    return np.array([[-1.1], [0.3], [0.5], [100.0]])

def _count(fn, target="does not have valid feature names"):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fn()
    return sum(1 for w in caught if target in str(w.message))

try:
    import pandas  # noqa: F401
except Exception:
    print("SKIP: pandas unavailable"); sys.exit(0)

fail = []

# A-reference 1: mismatch_advisory == real _check_feature_names(reset=False) over
# all four (arg_has_labels, fitted_with_labels) combinations.
for fitted in (False, True):
    for arg in (False, True):
        probe = _Probe()
        fit_X = _make_frame(fitted)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            probe._check_feature_names(fit_X, reset=True)
        if hasattr(probe, "feature_names_in_") != fitted:
            fail.append("reset=True label-recording wrong fitted=%r" % fitted)
        observed = _count(lambda: probe._check_feature_names(_make_frame(arg), reset=False))
        expected = mismatch_advisory(arg, fitted)
        if observed != expected:
            fail.append("consistency-rule fitted=%r arg=%r real=%d model=%d"
                        % (fitted, arg, observed, expected))

# A-reference 2: real _validate_data(reset=True) drops labels (prepared form
# unlabelled) for BOTH labelled and unlabelled input -> prepared(X).has_labels==False.
from sklearn.utils.validation import _get_feature_names
for labelled in (False, True):
    probe = _Probe()
    out = probe._validate_data(_make_frame(labelled), reset=True, dtype=np.float32)
    if _get_feature_names(out) is not None:
        fail.append("prepared form still labelled for input labelled=%r" % labelled)

# The PUBLIC score_samples still validates its own arg: an unlabelled array fed to
# a labelled-fit estimator triggers exactly mismatch_advisory(False,True)==1.
Xframe = _make_frame(True)
Xarray = _make_frame(False)
m = IsolationForest(random_state=0, contamination="auto").fit(Xframe)
n = _count(lambda: m.score_samples(Xarray))
if n != mismatch_advisory(False, True) != 0:
    fail.append("public score_samples advisory=%d, model expects 1" % n)

if fail:
    print("AXIOM-UNSOUND:", "; ".join(fail[:6])); sys.exit(1)
print("axiom-soundness OK (base callees): mismatch_advisory == real "
      "_check_feature_names over 4 combos; _validate_data(reset=True) drops "
      "labels for labelled+unlabelled; public score_samples validates its own "
      "arg (1 advisory).")
sys.exit(0)
'''


# (2) consumed-axiom soundness for prepared_scorer + token (patch-dependent):
#     the real _score_samples runs NO validation (0 advisories on an unlabelled
#     array after a LABELLED fit) and produces one score per row (so it can
#     furnish the offset / grant the token); AND the post-patch fit emits ZERO
#     advisories AND sets offset_ when contamination != 'auto' (token soundness +
#     F2P). Fuzzes 4 (labelled x contamination) cases incl. the F2P case and the
#     'auto' short-circuit (offset NOT scoring-derived there -- grounds the
#     biconditional). Skips cleanly if gold not applied (Defect-4 guard).
_AX_SCORER_PROBE = r'''
import sys
import warnings
import numpy as np
from sklearn.ensemble import IsolationForest

def _make_frame(labelled):
    import pandas as pd
    if labelled:
        return pd.DataFrame({"a": [-1.1, 0.3, 0.5, 100.0]})
    return np.array([[-1.1], [0.3], [0.5], [100.0]])

def _count(fn, target="does not have valid feature names"):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fn()
    return sum(1 for w in caught if target in str(w.message))

try:
    import pandas  # noqa: F401
except Exception:
    print("SKIP: pandas unavailable"); sys.exit(0)

# Defect-4 guard: the introduced private scorer exists only post-patch.
if not hasattr(IsolationForest, "_score_samples"):
    print("SKIP: gold not applied (_score_samples absent); patch-dependent "
          "obligation about code that does not yet exist."); sys.exit(0)

fail = []

# consumed axiom prepared_scorer: the real _score_samples runs NO validation pass
# (0 advisories) on an unlabelled array AFTER a labelled fit, and returns one
# score per row (so it can furnish the offset the token witnesses).
Xframe = _make_frame(True)                                   # fit WITH labels
Xprepared = np.asarray(_make_frame(False), dtype=np.float32) # already-prepared
m = IsolationForest(random_state=0, contamination="auto").fit(Xframe)
n = _count(lambda: m._score_samples(Xprepared))
if n != 0:
    fail.append("no-validation scorer emitted %d advisories (must be 0)" % n)
scores = np.asarray(m._score_samples(Xprepared))
if scores.shape[0] != Xprepared.shape[0]:
    fail.append("scorer did not produce one score per row -> cannot furnish offset")

# token soundness + F2P + auto short-circuit: post-patch fit emits ZERO advisories
# for all 4 (labelled x contamination) cases and sets offset_ when != 'auto'.
for labelled, contamination in [(True, 0.05), (True, "auto"),
                                (False, 0.05), (False, "auto")]:
    X = _make_frame(labelled)
    mm = IsolationForest(random_state=0, contamination=contamination)
    n = _count(lambda: mm.fit(X))
    if n != 0:
        fail.append("fit emitted %d advisories labelled=%r contamination=%r"
                    % (n, labelled, contamination))
    if contamination != "auto":
        mm2 = IsolationForest(random_state=0, contamination=contamination).fit(X)
        if not hasattr(mm2, "offset_"):
            fail.append("fit contamination=%r did not set offset_" % contamination)

if fail:
    print("AXIOM-UNSOUND:", "; ".join(fail[:6])); sys.exit(1)
print("axiom-soundness OK (introduced scorer + end-to-end): real _score_samples "
      "emits 0 advisories on an unlabelled array after a labelled fit and "
      "produces per-row scores; post-patch fit emits 0 advisories for 4 "
      "(labelled x contamination) cases and sets offset_ when != 'auto'.")
sys.exit(0)
'''


# (3) provenance soundness for prepared_input / raw_fit_input (patch-dependent):
#     the gold offset_ DERIVES from _score_samples of fit's OWN prepared training
#     input and does NOT equal the offset that scoring a FOREIGN array yields --
#     so the prepared_input/raw_fit_input provenance constraint (the attack10/10b
#     fix) is faithful AND load-bearing. Skips cleanly if gold not applied.
_AX_PROVENANCE_PROBE = r'''
import sys
import numpy as np
from sklearn.ensemble import IsolationForest

def _make_frame(labelled):
    import pandas as pd
    if labelled:
        return pd.DataFrame({"a": [-1.1, 0.3, 0.5, 100.0]})
    return np.array([[-1.1], [0.3], [0.5], [100.0]])

try:
    import pandas  # noqa: F401
except Exception:
    print("SKIP: pandas unavailable"); sys.exit(0)

if not hasattr(IsolationForest, "_score_samples"):
    print("SKIP: gold not applied (_score_samples absent)."); sys.exit(0)

fail = []
X = _make_frame(True)
contamination = 0.05
m = IsolationForest(random_state=0, contamination=contamination).fit(X)

# the offset derives from _score_samples of fit's OWN prepared training input
# (exactly the array gold's _score_samples(X) is fed inside fit).
Xprepared = m._validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)
expected = np.percentile(m._score_samples(Xprepared), 100.0 * contamination)
if not np.isclose(m.offset_, expected):
    fail.append("offset_=%r != percentile(_score_samples(prepared X))=%r"
                % (m.offset_, expected))

# a FOREIGN unlabelled array yields a DIFFERENT offset -> the provenance
# constraint (score fit's own prepared input, not a fabricated matrix) is
# load-bearing (this is exactly what the fabricated-matrix spec attack would break).
foreign = np.array([[10.0], [11.0], [12.0], [13.0]], dtype=np.float32)
foreign_offset = np.percentile(m._score_samples(foreign), 100.0 * contamination)
if np.isclose(m.offset_, foreign_offset):
    fail.append("scoring a foreign array reproduced the offset -> provenance not "
                "load-bearing")

if fail:
    print("AXIOM-UNSOUND:", "; ".join(fail[:4])); sys.exit(1)
print("provenance-soundness OK: gold offset_ == percentile(_score_samples("
      "prepared training X)) and != the offset scoring a foreign array yields; "
      "the prepared_input/raw_fit_input tokens are faithful and load-bearing.")
sys.exit(0)
'''


# (4) CONTAINMENT for prepared_scorer (patch-dependent): every callee-input the
#     MODEL can reach for _score_samples lies in the axiom's Requires domain
#     (X.has_labels == False, i.e. an already-prepared unlabelled numeric array).
#     The model only ever passes Xp = prepare(X_raw) (the prepared, unlabelled,
#     own-input form). Containment confirms (a) the real _score_samples ACCEPTS
#     the prepared/unlabelled array (in-domain, no error) and (b) the raw labelled
#     table is genuinely OUTSIDE the domain (raises) -- so the X.has_labels==False
#     narrowing is exactly the reachable domain, never narrower than the caller
#     needs. (Covering only this is SOUND: the gold fit feeds _score_samples only
#     the validated unlabelled array, never the raw table.)
_AX_CONTAIN_PROBE = r'''
import sys
import numpy as np
from sklearn.ensemble import IsolationForest

def _make_frame(labelled):
    import pandas as pd
    if labelled:
        return pd.DataFrame({"a": [-1.1, 0.3, 0.5, 100.0]})
    return np.array([[-1.1], [0.3], [0.5], [100.0]])

try:
    import pandas  # noqa: F401
except Exception:
    print("SKIP: pandas unavailable"); sys.exit(0)

if not hasattr(IsolationForest, "_score_samples"):
    print("SKIP: gold not applied (_score_samples absent)."); sys.exit(0)

fail = []
Xframe = _make_frame(True)
m = IsolationForest(random_state=0, contamination="auto").fit(Xframe)

# (a) the ONLY callee-input the model reaches is the prepared, UNLABELLED array
#     (Xp = prepare(X_raw)). The real _score_samples accepts it without error and
#     produces one score per row -- it is comfortably IN the axiom domain
#     (X.has_labels == False).
Xprepared = np.asarray(_make_frame(False), dtype=np.float32)
try:
    s = np.asarray(m._score_samples(Xprepared))
    if s.shape[0] != Xprepared.shape[0]:
        fail.append("prepared unlabelled array: wrong score count")
except Exception as e:
    fail.append("prepared unlabelled array unexpectedly rejected: %r" % e)

# (b) the RAW labelled table is OUTSIDE the domain (the model's X.has_labels==False
#     precondition forbids it): the real _score_samples (no _validate_data) raises
#     when fed a DataFrame. This confirms the narrowed domain matches the real
#     callee's actual domain -- it is not narrower than what the caller reaches.
raw = _make_frame(True)
raised = False
try:
    m._score_samples(raw)
except Exception:
    raised = True
if not raised:
    # not fatal to containment per se, but record: if the raw table did NOT raise,
    # the X.has_labels==False narrowing would still be sound (covering less than
    # the callee's real domain is fine), so this is informational only.
    print("NOTE: raw labelled table did not raise in _score_samples (informational)")

if fail:
    print("AXIOM-TOO-WEAK-FOR-CALLER:", "; ".join(fail[:4])); sys.exit(1)
print("axiom-containment OK: the only callee-input the model reaches for "
      "_score_samples is the prepared UNLABELLED array (Xp=prepare(X_raw)), which "
      "the real _score_samples accepts (in the X.has_labels==False domain); the "
      "raw labelled table is out-of-domain (raises), matching the narrowing.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-base-callees",
        "axiom": "mismatch_advisory/prepare",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,  # unchanged base callees; holds at base too
        "probe": _AX_BASE_PROBE,
        "rationale": (
            "A-reference soundness: mismatch_advisory == real "
            "_check_feature_names(reset=False) over all 4 (arg,fitted) combos; "
            "_validate_data(reset=True) drops labels (prepared form unlabelled); "
            "public score_samples still validates its own arg (1 advisory). If the "
            "real callee disagreed -> AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-sound-prepared-scorer-token",
        "axiom": "prepared_scorer/offset_from_unvalidated_scoring",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # _score_samples + post-patch fit are patch-introduced
        "probe": _AX_SCORER_PROBE,
        "rationale": (
            "Consumed-axiom + token soundness: the real _score_samples runs NO "
            "validation (0 advisories on an unlabelled array after a labelled fit) "
            "and produces per-row scores; post-patch fit emits 0 advisories for 4 "
            "(labelled x contamination) cases and sets offset_ when != 'auto'. If "
            "the real callee emitted an advisory or failed to produce scores -> "
            "AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-sound-offset-provenance",
        "axiom": "prepared_input/raw_fit_input",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROVENANCE_PROBE,
        "rationale": (
            "Provenance soundness: the gold offset_ derives from _score_samples of "
            "fit's OWN prepared training input and != the offset scoring a foreign "
            "array yields, so the prepared_input/raw_fit_input tokens are faithful "
            "and load-bearing (the discriminator the fabricated-matrix attack "
            "exploits). If a foreign array reproduced the offset -> the provenance "
            "constraint would be vacuous (AXIOM-UNSOUND / over-claim)."
        ),
    },
    {
        "id": "ax-contain-prepared-scorer-domain",
        "axiom": "prepared_scorer",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Containment: the only callee-input the model reaches for "
            "_score_samples is Xp = prepare(X_raw) -- the prepared, UNLABELLED, "
            "own-input form -- which the real _score_samples accepts (in the "
            "X.has_labels==False domain). The raw labelled table is out-of-domain "
            "(raises), so the narrowing matches the real callee's domain and is "
            "never narrower than the caller reaches. A reachable input outside the "
            "covered domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists."
        ),
    },
]
