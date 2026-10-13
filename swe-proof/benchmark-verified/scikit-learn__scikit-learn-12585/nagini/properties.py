# properties.py — PBT falsification battery for scikit-learn__scikit-learn-12585.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are full
# model.py variants that share the FROZEN spec (markers.same_spec) and differ
# ONLY inside the # impl-start/# impl-end region; each is checked by Nagini
# verify. There are no @ContractOnly axioms consumed by the proof (meta.axioms
# == []), so AXIOM_TESTS is empty — the two A-reference facts are validated by
# axiom_check.py (G-AX) and are not re-litigated here.
#
# The modeled function `reproduce(est, permit_fallback)` abstracts sklearn.base.
# clone(estimator, safe). `est` is a read-only input (held at Acc(...,1/2) on all
# three boolean fields), so a frame-mutation probe is MANDATORY. The load-bearing
# postcondition clauses are:
#   (C1) Implies(is_leaf(est), permit_fallback is True)            # leaf reached normally => fallback was permitted
#   (C2) Implies(is_leaf(est) and permit_fallback and est.is_class_object,
#                Result() is est)                                  # class-object leaf identity (the F2P guarantee)
#   (C3) Implies(not is_leaf(est), Result() is not est)            # genuine instance => fresh distinct object
#   (Ex) Exsures(NotCloneableError, ... is_leaf(est) and permit_fallback is False)
#   (C4) Requires(MustTerminate(2))                                # total correctness: the dispatch must DELIVER
#        Added after the G-EQ/G-PANEL-1 audit exhibited a diverging same-spec
#        impl (correct values, then an infinite loop before returning) that
#        VERIFIED under the partial-correctness spec while its faithful real
#        patch (`while True: pass` inside clone) hung the F2P test to the
#        harness timeout — verified but NOT resolved.
# is_leaf is a @Pure helper fully unfolded as (not has_introspect) or
# is_class_object — a function of the args, NOT an opaque answer-key oracle, so
# there is no "ungrounded-oracle echo" to build (see assessment).

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12585"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# The verbatim gold impl region body (everything between # impl-start and
# # impl-end, exclusive of the marker lines). Every rival is built by replacing
# THIS whole block with a new body — guaranteeing the edit is confined to the
# impl region and same_spec holds.
_GOLD_IMPL = """    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        # Atomic reproduction of a leaf. A class object has no internal
        # parameter state, so its atomic copy is reference-identical (returned
        # as the same reference). A non-class leaf carries state, so its atomic
        # copy is a fresh, distinct object.
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    # Genuine instance: take apart and rebuild into a fresh, distinct object.
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt"""

# Sanity: the gold body must appear exactly once in the frozen model.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl body anchor drift"


# ---------------------------------------------------------------------------
# Rival impl bodies (each replaces _GOLD_IMPL; spec is untouched).
# ---------------------------------------------------------------------------

# (R1) FRAME-MUTATION — the #1 weakness class. A rival that satisfies the
# class-object identity clause (C2) the cheap way: it WRITES to the read-only
# input's is_class_object field and then returns est. `est` is held at
# Acc(...,1/2) (read-only), so writing it requires FULL permission the caller
# never granted => must fail for INSUFFICIENT PERMISSION, not for a value
# mismatch. Gold control flow and the distinct/raise branches are kept verbatim
# so the rejection is attributable solely to the write.
_IMPL_FRAME_MUTATE = """    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        # FRAME-MUTATION ATTACK: overwrite the read-only input to force the
        # is_class_object disjunct, then return est to satisfy C2 vacuously.
        est.is_class_object = True
        return est
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt"""

# (R2) NON-LEAF IDENTITY LEAK (value-level / uniqueness). Always return est on
# every path that can. This satisfies C2 (class-leaf identity) trivially, but a
# GENUINE INSTANCE (not a leaf) now also returns est, violating
# C3: Implies(not is_leaf(est), Result() is not est). A faithful real patch that
# returned the SAME estimator object for a genuine instance would break the P2P
# reconstruction tests (test_clone / test_clone_2 assert clone(clf) is a NEW
# object whose fitted attributes are absent), so it would NOT resolve.
_IMPL_NONLEAF_IDENTITY = """    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        return est
    # UNIQUENESS ATTACK: a genuine instance is returned as the SAME object,
    # skipping the take-apart/rebuild. Violates C3 (Result() is not est).
    return est"""

# (R3) PREPATCH-STYLE CLASS MISROUTE (partial-domain / the exact F2P failure).
# Drop the is_class_object disjunct from the leaf guard so a class-object that
# exposes introspection (has_introspect=True, is_class_object=True) falls through
# to the reconstruction branch and returns a FRESH, distinct object. is_leaf(est)
# is still True for it (the @Pure helper is unchanged), so this violates BOTH
# C2 (Result() is est for a class-object leaf) and, when permit_fallback is
# False, C1/Ex. This is precisely the pre-patch bug: the class param is
# reconstructed rather than returned identically, so clf.empty is clf2.empty
# FAILS — its faithful real patch does NOT resolve test_clone_estimator_types.
_IMPL_PREPATCH_MISROUTE = """    if not est.has_introspect:
        if not permit_fallback:
            raise NotCloneableError()
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    # PARTIAL-DOMAIN ATTACK: the class-object disjunct is dropped from the
    # guard, so a class-object leaf is reconstructed into a distinct object
    # instead of returned identically (the pre-patch bug).
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt"""

# (R4) CONTROL-FLOW-EFFECT: never refuse. On a leaf with the fallback FORBIDDEN
# (permit_fallback is False) the gold routine MUST raise NotCloneableError; this
# rival instead reproduces atomically (or returns est for a class leaf) and
# returns normally. That violates C1: Implies(is_leaf(est), permit_fallback is
# True) (a leaf reached normally with permit_fallback False) and the Exsures.
# A faithful real patch that returned copy.deepcopy(estimator) under safe=True
# instead of raising TypeError would break the P2P safe-mode refusals
# (test_clone non-estimator with safe=True expects a TypeError), so it would NOT
# resolve. The raise is removed but every value branch is kept gold-faithful, so
# the rejection is attributable to the missing refusal control flow.
_IMPL_NO_REFUSE = """    if (not est.has_introspect) or est.is_class_object:
        # CONTROL-FLOW-EFFECT ATTACK: the refusal is dropped; a forbidden-
        # fallback leaf returns normally instead of raising.
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt"""

# (R5) SUPPORTING near-miss (partial-domain on the non-class leaf): return est
# for a NON-CLASS leaf too. C2 only requires identity for the class-object leaf;
# but returning est for a non-class leaf is still fine for C2/C3 (a non-class
# leaf IS a leaf, so C3's `not is_leaf` antecedent is false) — so this rival is
# NOT a postcondition break by itself. The real defect it carries: it short-
# circuits BEFORE the permit_fallback check is even... no — it keeps the raise.
# Actually returning est for a non-class leaf is value-faithful to the spec
# (the spec asserts NO identity there, neither does it forbid it), so this would
# VERIFY. To make it a genuine reject we instead return est on the NON-LEAF path
# only when permit_fallback (mixing the leaf-identity into the instance branch),
# violating C3. This is the cheap supporting twin of R2.
_IMPL_INSTANCE_LEAK_GUARDED = """    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    # SUPPORTING ATTACK (partial-domain): a genuine instance returns the SAME
    # object when permit_fallback is True, distinct otherwise. Violates C3 on
    # the permit_fallback=True sub-domain only.
    if permit_fallback:
        return est
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt"""

# (R6) NON-TERMINATION — the exact break the G-PANEL-1 (spec-too-weak) audit
# found while the spec was partial-correctness only. Computes every value
# branch correctly but spins in an infinite loop on the reconstruction path
# before returning the fresh object. Under partial correctness this VERIFIED
# (C1-C3 hold on the never-reached exit) and its faithful real patch
# (`while True: pass` inserted into clone() before the reconstruction) hung
# the F2P test to the harness timeout — verified but NOT resolved. With (C4)
# Requires(MustTerminate(2)) the loop has no decreasing MustTerminate measure,
# so the caller's termination obligation leaks -> REJECTED.
_IMPL_DIVERGE = """    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    # NON-TERMINATION ATTACK: diverge before the reconstruction returns. The
    # value postconditions hold vacuously on the never-exiting path; the
    # MustTerminate obligation must reject it.
    spin = True
    while spin:
        Invariant(spin)
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt"""

# (P1) POSITIVE CONTROL (soundness): a structurally-DIFFERENT but CORRECT impl.
# Branch order is inverted — the non-leaf (genuine instance) case is handled
# FIRST, and the leaf case dispatches class-object vs non-class via a single
# trailing return on a local. No loop/fold, no induction lemma needed; every
# value branch matches gold semantics. Must VERIFY (else SPEC-TOO-STRONG).
_IMPL_POS_REORDER = """    if est.has_introspect and (not est.is_class_object):
        # Genuine instance handled first: take apart and rebuild a fresh object.
        rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                            est.is_class_object)
        return rebuilt
    # Otherwise a leaf (no introspection, or a class object).
    if not permit_fallback:
        raise NotCloneableError()
    if est.is_class_object:
        return est
    atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                            est.is_class_object)
    return atomic_copy"""

# (A1) ADMISSIBILITY: a positive-control body that constructs an F2P-shaped
# input — a class-object estimator that exposes introspection
# (is_aggregate=False, has_introspect=True, is_class_object=True), exactly
# MyEstimator(empty=MyEstimator)'s `empty` parameter — and asserts every fact
# reproduce's Requires demands of it (the construction and asserts live INSIDE
# the impl region, so they are elided from the spec_view and same_spec holds).
# It exercises exactly the facts a call site must establish for a normal input:
# the precondition's value constraint (is_aggregate is False) plus the
# spec-side leaf classification (is_leaf True for the class object). If these
# asserts fail to verify, the precondition/classification is too strong for a
# normal input (PRECOND-TOO-STRONG). A same-measure self-call is no longer
# possible under (C4) MustTerminate(2) — the callee's measure must strictly
# decrease — so admissibility is asserted directly on the probe, mirroring the
# admiss pattern of the other MustTerminate bundles.
_IMPL_ADMISS = """    # ADMISSIBILITY positive-control: a representative F2P-shaped input must be
    # admitted by reproduce's precondition, and the spec must classify it as a
    # class-object leaf (the C2 identity disjunct).
    probe = Candidate(False, True, True)  # is_aggregate=False, has_introspect, is_class_object
    Assert(probe.is_aggregate is False)   # reproduce's value precondition holds
    Assert(probe.is_class_object)         # the C2 identity disjunct applies
    Assert(is_leaf(probe))                # spec-side leaf classification
    # The real gold dispatch follows, unchanged.
    if (not est.has_introspect) or est.is_class_object:
        if not permit_fallback:
            raise NotCloneableError()
        if est.is_class_object:
            return est
        atomic_copy = Candidate(est.is_aggregate, est.has_introspect,
                                est.is_class_object)
        return atomic_copy
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt"""


SPEC_TESTS = [
    {
        "id": "frame-mutate-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_FRAME_MUTATE),
        "refinement": (
            "The rival overwrites the read-only input field est.is_class_object "
            "to force the identity disjunct and return est. The faithful real "
            "patch of this would MUTATE the caller's estimator object (set an "
            "attribute on it) as a side effect of clone() — clone is required to "
            "be a pure read of the source estimator; a mutating clone would "
            "corrupt the source and fail every P2P test that re-uses the "
            "original clf after cloning (test_clone, test_clone_2). So it does "
            "NOT resolve."
        ),
        "rationale": (
            "est is held at Acc(est.is_class_object, 1/2) (read-only). Writing "
            "it requires full permission the precondition never grants, so the "
            "assignment fails for INSUFFICIENT PERMISSION — the frame condition, "
            "not a value mismatch. This is the project's #1 weakness class."
        ),
    },
    {
        "id": "nonleaf-identity-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_NONLEAF_IDENTITY),
        "refinement": (
            "Returning the SAME estimator object for a genuine instance means "
            "clone(clf) is clf — the faithful real patch would hand back the "
            "original (already-fitted) estimator instead of a fresh unfitted "
            "reconstruction, breaking test_clone / test_clone_2 (which assert the "
            "clone is a new object without the fitted attributes). It does NOT "
            "resolve."
        ),
        "rationale": (
            "Violates C3: Implies(not is_leaf(est), Result() is not est). For a "
            "genuine instance (has_introspect and not is_class_object) is_leaf is "
            "False, so the postcondition demands a distinct object; returning est "
            "fails it."
        ),
    },
    {
        "id": "prepatch-class-misroute",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_PREPATCH_MISROUTE),
        "refinement": (
            "This is the pre-patch bug verbatim: dropping the is_class_object "
            "disjunct from the executable guard routes a class-object parameter "
            "into the reconstruction branch, returning a FRESH distinct Candidate "
            "instead of the same reference. The faithful real patch reconstructs "
            "the class via estimator.get_params(...) — which on a class raises "
            "TypeError (unbound method) — so clf.empty is clf2.empty FAILS. It is "
            "exactly the F2P test_clone_estimator_types failure; does NOT resolve."
        ),
        "rationale": (
            "Violates C2: Implies(is_leaf(est) and permit_fallback and "
            "est.is_class_object, Result() is est). is_leaf (the @Pure helper) is "
            "unchanged and True for a class object, so the spec still demands "
            "identity, but the rival returns a fresh Candidate."
        ),
    },
    {
        "id": "no-refuse-on-forbidden-leaf",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_NO_REFUSE),
        "refinement": (
            "Removing the refusal makes the routine return normally on a leaf "
            "even when the fallback is forbidden (safe=True). The faithful real "
            "patch would copy.deepcopy / return the estimator under safe=True "
            "instead of raising TypeError, breaking the P2P safe-mode contract "
            "(clone of a non-estimator with safe=True must raise TypeError). It "
            "does NOT resolve."
        ),
        "rationale": (
            "Violates C1: Implies(is_leaf(est), permit_fallback is True) and the "
            "Exsures(NotCloneableError, ... permit_fallback is False) clause — a "
            "leaf reached the normal-return path with permit_fallback False."
        ),
    },
    {
        "id": "instance-identity-leak-guarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_INSTANCE_LEAK_GUARDED),
        "refinement": (
            "Supporting partial-domain twin of nonleaf-identity-leak: a genuine "
            "instance returns the SAME object only when permit_fallback is True. "
            "On that sub-domain clone(clf, safe=False) is clf, so the faithful "
            "patch returns the original fitted estimator rather than a fresh one, "
            "breaking test_clone / test_clone_2. Does NOT resolve."
        ),
        "rationale": (
            "Violates C3 on the permit_fallback=True sub-domain: for a non-leaf "
            "the postcondition demands Result() is not est unconditionally; "
            "returning est on that sub-domain fails it."
        ),
    },
    {
        "id": "weak-diverge-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_DIVERGE),
        "refinement": (
            "The faithful real patch inserts an infinite loop (`while True: "
            "pass`) into clone() before the reconstruction returns (empirically "
            "confirmed by the G-PANEL-1 audit attack patches: the patch applies "
            "cleanly and the F2P test run hangs to the harness timeout — does "
            "NOT resolve), while the partial-correctness spec still verified it."
        ),
        "rationale": (
            "REJECTED by (C4) Requires(MustTerminate(2)): the loop has no "
            "decreasing MustTerminate measure, so the caller's termination "
            "obligation cannot be discharged (obligation leak) and verification "
            "fails. Under the previous partial-correctness spec this VERIFIED "
            "(C1-C3 held vacuously on the never-exiting path). If it VERIFIES "
            "=> SPEC-TOO-WEAK (the termination obligation is unpinned)."
        ),
    },
    {
        "id": "pos-control-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_POS_REORDER),
        "rationale": (
            "A structurally-different but CORRECT impl: the genuine-instance "
            "branch is handled FIRST, then the leaf branch dispatches class-object "
            "(identity) vs non-class (fresh) with the refusal kept. No loop / fold "
            "/ induction lemma is involved, so the gold proof obligations are "
            "discharged by the same per-branch reasoning. Must verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-class-object-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPL_ADMISS),
        "rationale": (
            "A positive-control body constructs the F2P-shaped input (a class "
            "object exposing introspection: is_aggregate=False, "
            "has_introspect=True, is_class_object=True) and asserts every fact "
            "reproduce's Requires demands of it: the value precondition "
            "(is_aggregate is False) and the spec-side classification "
            "(is_class_object, is_leaf) that arms the C2 identity guarantee. If "
            "these asserts fail to verify, the precondition/classification is "
            "too strong for a normal input (PRECOND-TOO-STRONG). The probe is "
            "inside the impl region, so it is elided from the spec_view and "
            "same_spec holds. (A same-measure self-call is impossible under "
            "(C4) MustTerminate(2); admissibility is asserted directly.)"
        ),
    },
]

# No @ContractOnly axioms are consumed (meta.axioms == []). The two A-reference
# facts (is_leaf == real guard; copy.deepcopy(cls) is cls / copy.deepcopy(obj)
# is not obj) are validated by axiom_check.py under G-AX and are not re-checked
# here.
AXIOM_TESTS = []
