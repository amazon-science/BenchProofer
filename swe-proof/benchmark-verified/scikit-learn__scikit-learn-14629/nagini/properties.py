# properties.py — PBT manifest for scikit-learn__scikit-learn-14629.
#
# NOT a Nagini module; an adversarial falsification battery. The runner
# (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS, writes each `module`
# to a temp file, runs Nagini verify + same_spec against the frozen model.py,
# and stamps RESULT. Spec cases are built by REGION-SURGERY: every variant is
# _BASE with edits made ONLY inside the # impl-start / # impl-end region (which
# also contains the loop invariants — both are elided by spec_view), so the
# frozen spec (axioms/pure/pre/post-conditions + signatures) is byte-for-byte
# untouched and same_spec is guaranteed.
#
# Defended surface (frozen spec of gather_output_classes):
#   Inputs are READ-ONLY: Acc(list_pred(estimators), 1/2) and, per element,
#   Acc(estimators[k].cls_vals, 1/4). The postcondition pins:
#     (frame) the input list + each touched facet are returned at the SAME
#             fractional permission (so the op cannot satisfy the spec by
#             mutating the input);
#     (P0)    Acc(list_pred(Result()))  — full permission on a fresh result;
#     (P1)    len(Result()) == len(estimators)  — one entry per sub-classifier;
#     (P2)    Forall k in [0,len): Result()[k] == est_vals(estimators[k])
#             — element-wise VALUE equality to the genuine per-output labels
#             (not a reordering / subset / constant / another output's labels).
#   est_vals is a GROUNDED @Pure accessor (returns e.cls_vals verbatim, fully
#   unfolded): there is no opaque answer-key to echo, so the ungrounded-oracle
#   class is N/A here (see assessment) — its place is taken by an honest
#   positive control + admissibility witness.

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14629"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body (everything strictly between # impl-start and
# # impl-end), used as the anchor for every region-surgery swap.
_GOLD_IMPL = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        Invariant(MustTerminate(len(estimators) - i + 1))
        # invariants-end
        result.append(est_vals(estimators[i]))
        i = i + 1
    return result"""

# Sanity: the anchor must appear verbatim & uniquely in the frozen model.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl anchor drifted from model.py"


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = []

# --- (A) POSITIVE CONTROL (soundness) ---------------------------------------
# Structurally-different but CORRECT impl: hoist est_vals(...) into a typed
# local before the append (a local-variable reshape, NOT a loop-direction flip
# — directive 3). Every gold invariant is kept VERBATIM (directive 2), so the
# loop's framing/value obligations still discharge; only the executable shape
# of the loop body changes. Must VERIFY (else SPEC-TOO-STRONG).
_POS_LOCAL = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        Invariant(MustTerminate(len(estimators) - i + 1))
        # invariants-end
        v = est_vals(estimators[i])  # type: PSeq[int]
        result.append(v)
        i = i + 1
    return result"""
SPEC_TESTS.append({
    "id": "pos-local-hoist",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_IMPL, _POS_LOCAL),
    "rationale": "A correct, structurally-different impl (hoist est_vals into a "
                 "typed local before append; all gold invariants kept verbatim) "
                 "must verify; if it cannot, the postcondition is SPEC-TOO-STRONG.",
})

# --- (B) POSITIVE CONTROL (soundness, value-equal copy) ---------------------
# The refinement explicitly admits a value-equal fix (store a copy rather than
# the reference): A4/A5 pin VALUE, not identity. Model a copy by binding the
# per-output sequence through the GROUNDED @Pure est_vals and a value-preserving
# resequence (v.drop(0) returns a FRESH PSeq value equal to v: v.drop(0) == v).
# This produces a distinct sequence value (not the stored reference) while
# remaining VALUE-equal, proving the spec is not secretly an identity pin; it
# must VERIFY.
_POS_COPY = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        Invariant(MustTerminate(len(estimators) - i + 1))
        # invariants-end
        copy = est_vals(estimators[i]).drop(0)  # type: PSeq[int]
        result.append(copy)
        i = i + 1
    return result"""
SPEC_TESTS.append({
    "id": "pos-value-copy",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_IMPL, _POS_COPY),
    "rationale": "The spec pins VALUE equality (Result()[k] == est_vals(...)), "
                 "not identity (G-EQ refinement). A value-equal 'copy' "
                 "(est_vals(...).drop(0), a fresh PSeq value equal to the "
                 "genuine labels, value-preserving) is a correct fix and MUST "
                 "verify; if it is rejected the spec has silently regressed to "
                 "an identity pin (SPEC-TOO-STRONG).",
})

# --- (C) ADMISSIBILITY ------------------------------------------------------
# The precondition must accept a normal F2P-shaped input. Keep the gold impl,
# but add an in-region Assert that an in-domain fact is provable for a non-empty
# fitted list: at i==len, the frame perms (1/2 spine, 1/4 each facet) and the
# per-position value pin hold for every position. If the Requires were too
# strong (e.g. demanded full perm it never grants, or an impossible shape) the
# loop reading est_vals at 1/4 could not be established and this would fail =>
# PRECOND-TOO-STRONG. The assert is dischargeable iff the precondition genuinely
# admits the representative input the loop walks.
_ADMISS = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        Invariant(MustTerminate(len(estimators) - i + 1))
        # invariants-end
        result.append(est_vals(estimators[i]))
        i = i + 1
    # admissibility witness: the precondition admits a normal fitted list; the
    # gathered result is non-empty exactly when there is >=1 output, and each
    # entry value-matches its sub-classifier (the F2P-shaped state).
    Assert(len(result) == len(estimators))
    Assert(Implies(len(estimators) > 0,
        result[0] == est_vals(estimators[0])))
    return result"""
SPEC_TESTS.append({
    "id": "admiss-fshaped",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
    "rationale": "Adds in-region Asserts that the gathered collection has one "
                 "entry per sub-classifier and that position 0 value-matches its "
                 "sub-classifier on a non-empty (F2P-shaped) input. Both are "
                 "provable iff the precondition admits a normal fitted list; if "
                 "it cannot the precondition is PRECOND-TOO-STRONG.",
})

# --- (D) FRAME-MUTATION (uniqueness; MANDATORY — read-only input) -----------
# The inputs are read-only: estimators[i].cls_vals is held at Acc(...,1/4). A
# rival that WRITES to that facet to manufacture the postcondition vacuously
# must be REJECTED for INSUFFICIENT PERMISSION (1/4 read perm cannot support a
# field assignment, which needs full Acc). Gold invariants kept verbatim so the
# rejection is attributable to the write, not a proof gap.
_FRAME_MUT = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        Invariant(MustTerminate(len(estimators) - i + 1))
        # invariants-end
        estimators[i].cls_vals = est_vals(estimators[i])
        result.append(estimators[i].cls_vals)
        i = i + 1
    return result"""
SPEC_TESTS.append({
    "id": "frame-mutate-input",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUT),
    "refinement": "A real patch that ASSIGNS back to estimator.classes_ "
                  "(self.estimators_[i].classes_ = ...) overwrites a fitted "
                  "sub-classifier's learned labels in place. Even when it writes "
                  "the same value here, it mutates shared sklearn estimator state "
                  "the wrapper does not own — corrupting the sub-estimators that "
                  "the P2P predict/predict_proba tests reuse (e.g. "
                  "test_multi_output_classification, ...predict_proba). The gold "
                  "patch only READS estimator.classes_ into a fresh list; this "
                  "rival's faithful real form is a write-back the gold never does "
                  "and would not resolve the suite cleanly.",
    "rationale": "Rejected by the PERMISSION SYSTEM: estimators[i].cls_vals is "
                 "held at Acc(...,1/4) (read-only) via the precondition and loop "
                 "invariant; a field assignment requires full Acc, so the write "
                 "fails for insufficient permission. A byte-fuzzer never mutates "
                 "the input — this is the #1 weakness class.",
})

# --- (E) PARTIAL-DOMAIN: drop the LAST entry --------------------------------
# Correct on every position it emits, but stops one short (loops to len-1).
# Diverges only on the final output: |Result()| == len-1. Rejected by P1
# (len(Result()) == len(estimators)).
_DROP_LAST = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators) - 1:
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        Invariant(MustTerminate(len(estimators) - i + 1))
        # invariants-end
        result.append(est_vals(estimators[i]))
        i = i + 1
    return result"""
SPEC_TESTS.append({
    "id": "partial-drop-last",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _DROP_LAST),
    "refinement": "A faithful real form gathers labels for all outputs but the "
                  "last (e.g. `[est.classes_ for est in self.estimators_[:-1]]`). "
                  "On the F2P test n_outputs==3 so classes_ has 2 entries; "
                  "`len(estimator.classes_) == n_outputs` fails and the F2P "
                  "test_multi_output_classes_ does NOT resolve.",
    "rationale": "Rejected by postcondition P1 len(Result()) == len(estimators): "
                 "the loop bound len-1 makes len(Result()) one short.",
})

# --- (F) PARTIAL-DOMAIN: wrong FIRST entry (off-by-one shift) ---------------
# Emits exactly len entries (passes P1) and is correct on positions 1..len-1,
# but position 0 carries the labels of sub-classifier 1 (a one-off shift). It
# diverges only on the first element. Rejected by P2 at k==0.
_SHIFT_FIRST = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        # (deliberately omits the per-position value pin for k<i: this impl
        # cannot establish it, which is the whole point of the attack)
        # invariants-end
        if i + 1 < len(estimators):
            result.append(est_vals(estimators[i + 1]))
        else:
            result.append(est_vals(estimators[i]))
        i = i + 1
    return result"""
SPEC_TESTS.append({
    "id": "partial-shift-first",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _SHIFT_FIRST),
    "refinement": "A faithful real form shifts the per-output assignment by one "
                  "(position 0 gets output 1's labels). The F2P test compares "
                  "each `classes[i]` against `estimator.classes_[i]` with "
                  "assert_array_equal; output 0's labels differ from output 1's "
                  "in general, so assert_array_equal fails and the F2P test does "
                  "NOT resolve.",
    "rationale": "Rejected by postcondition P2 (Result()[k] == est_vals("
                 "estimators[k])) at k==0: position 0 carries est_vals("
                 "estimators[1]) != est_vals(estimators[0]).",
})

# --- (G) VALUE double-mask / CONSTANT: emit a fixed empty sequence ----------
# Right shape (len matches via P1), but every entry is the SAME constant empty
# label sequence rather than the genuine per-output labels — the classic
# "populated but with the wrong content" defect the docstring forbids.
# Rejected by P2 wherever a sub-classifier's labels are non-empty.
_CONST_EMPTY = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        # invariants-end
        empty = PSeq()  # type: PSeq[int]
        result.append(empty)
        i = i + 1
    return result"""
SPEC_TESTS.append({
    "id": "const-empty-entry",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _CONST_EMPTY),
    "refinement": "A faithful real form populates classes_ with one empty array "
                  "per output (`[np.array([]) for _ in self.estimators_]`). The "
                  "shape passes (`len == n_outputs`) but assert_array_equal of "
                  "each empty array against the sub-classifier's real labels "
                  "([0,1,...]) fails, so the F2P test does NOT resolve. (This is "
                  "the 'populated with a constant instead of the genuine labels' "
                  "defect the model docstring explicitly forbids.)",
    "rationale": "Rejected by postcondition P2: Result()[k] is a constant empty "
                 "PSeq, which is != est_vals(estimators[k]) whenever output k "
                 "has any class labels.",
})

# --- (H) REVERSE order (supporting reorder near-miss) -----------------------
# Emits len entries (P1 holds) but in reverse output order. Rejected by P2.
_REVERSE = """    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        # invariants-end
        result.append(est_vals(estimators[len(estimators) - 1 - i]))
        i = i + 1
    return result"""
SPEC_TESTS.append({
    "id": "reverse-order",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _REVERSE),
    "refinement": "A faithful real form reverses the per-output order "
                  "(`[est.classes_ for est in reversed(self.estimators_)]`). On "
                  "the F2P test the per-position assert_array_equal fails for any "
                  "output whose labels differ from the mirrored output, so the "
                  "F2P test does NOT resolve.",
    "rationale": "Rejected by postcondition P2: position k carries est_vals("
                 "estimators[len-1-k]) != est_vals(estimators[k]) in general.",
})

# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# No @ContractOnly axiom and no A-reference deep model: the added behaviour is
# pure per-element structural gathering over an already-fitted list, modelled
# DEEPLY by the verified loop (meta.deep_model_references == [], axioms == []).
# G-AX is vacuous. There is no opaque callee whose Ensures could be unsound and
# no callee-domain to check for containment, so AXIOM_TESTS is empty by design.
AXIOM_TESTS = []
