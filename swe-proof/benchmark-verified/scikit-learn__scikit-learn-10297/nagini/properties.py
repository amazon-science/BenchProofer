# properties.py — PBT manifest for scikit-learn__scikit-learn-10297.
#
# NOT a Nagini module: a record of adversarially-reasoned falsification cases the
# runner (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are
# full model.py variants that share the FROZEN spec byte-for-byte (region surgery
# edits ONLY inside an # impl-start/# impl-end block) and differ only in the impl;
# each is checked by Nagini verify + markers.same_spec. There are no axioms in
# this bundle, so AXIOM_TESTS is empty (see assessment).
#
# Defended surface (from model.py):
#   configure_classifier_cv(store_cv_values: bool) -> EngineConfig
#     Requires(True);  load-bearing post: Result().retain_values == store_cv_values
#     (the gold constructor forwarding super().__init__(..., store_cv_values=...)).
#   stored_cv_values(cfg: EngineConfig, n_samples, n_targets, n_alphas) -> Optional[CvRecord]
#     Requires(Acc(cfg.retain_values, 1/2))  <-- cfg is a READ-ONLY (half-perm) input
#     Requires(n_samples>=0 and n_targets>=1 and n_alphas>=0)
#     load-bearing posts: (Result() is not None) == cfg.retain_values ;
#       Implies(Result() is not None, rank==3 and n_samples/n_targets/n_alphas pinned).
#
# There is NO @Pure answer-key / oracle in the contract: every postcondition is
# grounded directly in the arguments (the boolean flag and the three integer axis
# lengths), so there is no ungrounded-oracle echo to construct. The frame-mutation
# attack (cfg held at 1/2 permission) IS applicable and is mandatory.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10297"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Reusable swap targets — each lands strictly inside an # impl-start/# impl-end
# region, so the frozen spec (signatures + Requires/Ensures) is never touched.
# ---------------------------------------------------------------------------
_CFG_IMPL = "cfg = EngineConfig(store_cv_values)\n    return cfg"
_SCV_IMPL = (
    "    if cfg.retain_values:\n"
    "        record = CvRecord(3, n_samples, n_targets, n_alphas)"
    "  # type: Optional[CvRecord]\n"
    "        return record\n"
    "    return None"
)


# === 1. FRAME-MUTATION (mandatory: cfg is read-only at Acc(...,1/2)) =========
# A rival that WRITES cfg.retain_values to satisfy the postcondition vacuously.
# Holding only 1/2 permission, the assignment `cfg.retain_values = True` cannot
# be framed -> Nagini rejects for INSUFFICIENT PERMISSION. The gold invariants
# are kept verbatim so the rejection is attributable solely to the write.
_FRAME_MUT = _swap(
    _BASE, _SCV_IMPL,
    "    cfg.retain_values = True  # illegal: only Acc(cfg.retain_values, 1/2) held\n"
    "    record = CvRecord(3, n_samples, n_targets, n_alphas)"
    "  # type: Optional[CvRecord]\n"
    "    return record",
)

# === 2. PARTIAL-DOMAIN: wrong on the binary (n_targets == 1) sub-domain ======
# Correct rank-3 record for n_targets > 1, but on the n_targets==1 boundary it
# emits the pre-patch regressor shape (rank 2, target axis collapsed). The spec
# pins rank==3 and n_targets==n_targets UNCONDITIONALLY, so this is rejected.
_PARTIAL_DOMAIN = _swap(
    _BASE, _SCV_IMPL,
    "    if cfg.retain_values:\n"
    "        if n_targets > 1:\n"
    "            big = CvRecord(3, n_samples, n_targets, n_alphas)"
    "  # type: Optional[CvRecord]\n"
    "            return big\n"
    "        flat = CvRecord(2, n_samples, n_targets, n_alphas)"
    "  # type: Optional[CvRecord]\n"
    "        return flat\n"
    "    return None",
)

# === 3. CONTROL-FLOW-EFFECT: retention guard inverted ========================
# Returns a (correctly-shaped) record exactly when retention is OFF and None when
# ON. Invisible to a value-only abstraction of the record, but caught by the
# control-flow clause (Result() is not None) == cfg.retain_values.
_FLOW_INVERTED = _swap(
    _BASE, _SCV_IMPL,
    "    if cfg.retain_values:\n"
    "        return None\n"
    "    record = CvRecord(3, n_samples, n_targets, n_alphas)"
    "  # type: Optional[CvRecord]\n"
    "    return record",
)

# === 4. UNIQUENESS: forwarding ignored (configure returns a constant flag) ===
# `configure_classifier_cv` always builds EngineConfig(True), ignoring the
# requested flag. Caught by Result().retain_values == store_cv_values when the
# caller passes False (the pre-patch reality, but constant-True instead of
# constant-False, attacking from the other side).
_IGNORE_FLAG = _swap(
    _BASE, _CFG_IMPL,
    "cfg = EngineConfig(True)  # ignores the requested flag\n    return cfg",
)

# === 5. UNIQUENESS: forwarding negated =======================================
# `configure_classifier_cv` forwards the negation of the requested flag. Caught
# by Result().retain_values == store_cv_values for either boolean value.
_NEGATE_FLAG = _swap(
    _BASE, _CFG_IMPL,
    "cfg = EngineConfig(not store_cv_values)  # forwards the negation\n    return cfg",
)

# === 6. UNIQUENESS: rank not pinned (rank 2 instead of 3) ====================
# Builds a record with rank 2 (the flattened (samples, penalties) form) on EVERY
# retained case -- the model_prepatch_2.py defect. Caught by Result().rank == 3.
_RANK_TWO = _swap(
    _BASE, _SCV_IMPL,
    "    if cfg.retain_values:\n"
    "        record = CvRecord(2, n_samples, n_targets, n_alphas)"
    "  # type: Optional[CvRecord]\n"
    "        return record\n"
    "    return None",
)

# === 7. POSITIVE CONTROL (soundness): branch reordered, distinct locals ======
# Structurally different but CORRECT: early-return None on the not-retained
# branch, then build the rank-3 record with differently-named locals. Keeps
# every gold proof obligation (no induction/fold lemma needed -- direct field
# assignment). MUST verify, else SPEC-TOO-STRONG.
_POS_CONTROL = _swap(
    _BASE, _SCV_IMPL,
    "    if not cfg.retain_values:\n"
    "        return None\n"
    "    out = CvRecord(3, n_samples, n_targets, n_alphas)"
    "  # type: Optional[CvRecord]\n"
    "    return out",
)

# === 8. ADMISSIBILITY: precondition admits an F2P-shaped binary input ========
# Inside configure_classifier_cv's impl (which holds FULL permission on cfg),
# build a retained config and call stored_cv_values on the F2P binary boundary
# (n_samples=5, n_targets=1, n_alphas=3): retain True, n_targets==1 boundary.
# stored_cv_values needs only Acc(cfg.retain_values, 1/2) and returns it, so the
# subsequent `return cfg` still type-checks. If the Requires cannot be met for
# this normal input -> PRECOND-TOO-STRONG. The asserts on the returned record
# confirm the postcondition is reachable (non-None, rank 3, axes pinned).
_ADMISS = _swap(
    _BASE, _CFG_IMPL,
    "cfg = EngineConfig(True)\n"
    "    probe = stored_cv_values(cfg, 5, 1, 3)  # type: Optional[CvRecord]\n"
    "    Assert(probe is not None)\n"
    "    Assert(probe.rank == 3)\n"
    "    Assert(probe.n_samples == 5)\n"
    "    Assert(probe.n_targets == 1)\n"
    "    Assert(probe.n_alphas == 3)\n"
    "    out = EngineConfig(store_cv_values)  # type: EngineConfig\n"
    "    return out",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-cfg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": (
            "The gold retention branch in _RidgeGCV.fit only READS "
            "self.store_cv_values to choose cv_values_shape; it never re-assigns "
            "the engine's retention flag. A faithful patch that mutated the "
            "config's store_cv_values during the fit-shape computation would "
            "corrupt the estimator's recorded configuration and diverge from the "
            "F2P observable (which reads store_cv_values back unchanged and "
            "asserts the retained shape), so it would NOT resolve."
        ),
        "rationale": (
            "stored_cv_values holds cfg only at Acc(cfg.retain_values, 1/2); a "
            "write needs full permission, so Nagini rejects for INSUFFICIENT "
            "PERMISSION. This is the #1 weakness class and the mandatory "
            "read-only-input probe."
        ),
    },
    {
        "id": "partial-domain-binary-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_DOMAIN,
        "refinement": (
            "This is exactly the pre-patch regressor behaviour (the "
            "len(y.shape)==1 branch, model_prepatch_2.py) restricted to the "
            "binary case. The F2P test test_ridge_classifier_cv_store_cv_values "
            "fits a binary target and asserts "
            "r.cv_values_.shape == (n_samples, 1, n_alphas) (rank 3, n_targets=1); "
            "a patch that collapses the target axis for the binary input yields "
            "shape (n_samples, n_alphas) (rank 2) and FAILS that assertion, so it "
            "would NOT resolve."
        ),
        "rationale": (
            "The postcondition pins rank==3 and n_targets==n_targets "
            "UNCONDITIONALLY (the always-present target axis). The n_targets==1 "
            "sub-domain divergence violates rank==3, so Nagini rejects."
        ),
    },
    {
        "id": "control-flow-retention-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FLOW_INVERTED,
        "refinement": (
            "A faithful patch that populated cv_values_ exactly when "
            "store_cv_values is False (and left it absent when True) inverts the "
            "documented contract. The F2P test sets store_cv_values=True and "
            "asserts r.cv_values_.shape exists and is rank-3; with retention "
            "inverted, cv_values_ is never set when requested -> AttributeError / "
            "test failure, so it would NOT resolve."
        ),
        "rationale": (
            "The clause (Result() is not None) == cfg.retain_values pins the "
            "None/not-None control flow to the flag; inverting the guard makes "
            "Result() None exactly when retain_values is True, violating it. "
            "Nagini rejects."
        ),
    },
    {
        "id": "uniqueness-ignore-requested-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _IGNORE_FLAG,
        "refinement": (
            "Hard-coding the engine to always retain ignores the caller's "
            "request, just as the pre-patch constructor ignored it (model_prepatch.py "
            "used the constant False; this uses constant True). Either constant "
            "breaks the forwarding the gold patch adds; the estimator's "
            "store_cv_values would not echo the requested value and the broader "
            "estimator contract / P2P expectations would break, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "Result().retain_values == store_cv_values is violated whenever the "
            "caller passes False (Nagini must prove it for ALL inputs satisfying "
            "Requires(True), and False is admitted). Nagini rejects."
        ),
    },
    {
        "id": "uniqueness-negate-requested-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NEGATE_FLAG,
        "refinement": (
            "Forwarding the negation of store_cv_values is the opposite of the "
            "gold super().__init__(..., store_cv_values=store_cv_values) "
            "forwarding; the configured estimator would retain iff the caller "
            "asked it NOT to, so the F2P (store_cv_values=True) leaves cv_values_ "
            "unset and the test fails -> would NOT resolve."
        ),
        "rationale": (
            "Result().retain_values == store_cv_values is violated for every "
            "boolean value under negation; Nagini rejects."
        ),
    },
    {
        "id": "uniqueness-rank-two-everywhere",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RANK_TWO,
        "refinement": (
            "Building the retained record at rank 2 on every retained case is the "
            "model_prepatch_2.py defect (the flattened (samples, penalties) form). "
            "The classifier always label-binarizes y to a 2-D matrix, so the engine "
            "always produces rank-3 cv_values_; the F2P asserts shape "
            "(n_samples, n_targets, n_alphas). A rank-2 record fails that shape "
            "assertion for both the binary and multilabel cases -> would NOT resolve."
        ),
        "rationale": (
            "Implies(Result() is not None, Result().rank == 3) is violated by a "
            "rank-2 record; Nagini rejects."
        ),
    },
    {
        "id": "pos-control-reordered-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "A structurally-different but CORRECT impl: early-return None on the "
            "not-retained branch, then build the same rank-3 record with a "
            "differently-named local. No fold/induction lemma is needed (direct "
            "field assignment), so the gold proof remains valid. MUST verify; "
            "failure would indicate SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-f2p-binary-boundary",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "A self-call positive control: configure_classifier_cv (holding full "
            "permission on a freshly-built retained config) calls stored_cv_values "
            "on the F2P binary boundary (n_samples=5, n_targets=1, n_alphas=3). "
            "The Requires (Acc(cfg.retain_values,1/2); n_samples>=0, n_targets>=1, "
            "n_alphas>=0) must hold for this normal input, and the asserts confirm "
            "the postcondition is reachable (non-None, rank 3, axes pinned). If it "
            "cannot verify -> PRECOND-TOO-STRONG."
        ),
    },
]


# No @ContractOnly axioms and no A-reference deep models in this bundle (meta.json
# axioms == [], deep_model_references == []; G-AX vacuous). Both modelled
# behaviours are the CHANGED code, modelled directly (refinement.md is all R/I).
# axiom_check.py is a reference witness, not a soundness obligation. So there is
# nothing to probe in the axiom lane.
AXIOM_TESTS = []
