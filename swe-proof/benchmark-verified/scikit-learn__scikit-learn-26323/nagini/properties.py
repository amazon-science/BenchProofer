# properties.py — PBT manifest for scikit-learn__scikit-learn-26323.
#
# NOT a Nagini module. A record of adversarially-reasoned falsification cases the
# runner (swebench_nagini.pbt) executes against the FROZEN spec in model.py.
# Every spec variant is produced by `_swap` on a UNIQUE sub-anchor that lies
# strictly inside the # impl-start / # impl-end region (the loop body, the
# leftover write, or a loop invariant — invariants are NESTED inside the impl
# region so editing them keeps same_spec). The frozen axioms/pure/pre/post
# conditions are never touched, so markers.same_spec holds for every case.
#
# ===========================================================================
# DEFENDED SURFACE (model.py + refinement.md + mapping.md)
# ---------------------------------------------------------------------------
#   configure_output(children: List[Child], leftover: Child, requested: int) -> None
# In-place mutator. It propagates an output-container code `requested` (!= 0)
# to every CONFIGURABLE child (kind == 1, an estimator) and to the
# leftover-columns child WHEN it too is configurable, leaving routing sentinels
# (kind == 0) untouched. The gold patch is the ADDED hunk
#       if self.remainder not in {"passthrough", "drop"}:
#           _safe_set_output(self.remainder, transform=transform)
# i.e. ALSO configure the leftover-columns estimator. The pre-patch bug
# (model_prepatch.py) configures the looped children but NEVER the leftover —
# the F2P test_remainder_set_output fails (a leftover-columns VarianceThreshold
# returns a numpy array instead of the requested DataFrame).
#
# PERMISSIONS / read-only inputs:
#   The Requires grant FULL `Acc(children[k].kind)`, `Acc(children[k].cfg)`,
#   `Acc(leftover.kind)`, `Acc(leftover.cfg)` (no fraction) — the impl legitimately
#   writes `c.cfg` / `leftover.cfg`. There is therefore NO Acc(x, 1/2) read-only
#   *parameter*: the classic "overwrite a half-permission input -> insufficient
#   permission" frame attack is NOT available here (the only fractional
#   permission, Acc(c.kind, 1/4), is internal to the @Pure helper
#   `is_configurable`, not a boundary obligation). has_readonly_input = False.
#   HOWEVER the FRAME is still defended by the postcondition, not by permission:
#   `children[k].kind == Old(children[k].kind)` and `leftover.kind ==
#   Old(leftover.kind)` pin the classification field as INVARIANT across the
#   call. We attack that frame directly (frame-kind-mutation below): a rival that
#   reclassifies a sentinel as an estimator to make the cfg clause hold vacuously
#   is rejected — by the kind-preservation postcondition, not by a permission
#   error. We report this honestly in 'assessment'.
#
# LOAD-BEARING postcondition clauses:
#   (P1) Forall k: kind==1 => cfg==requested           (every estimator configured)
#   (P2) Forall k: kind==0 => cfg==0                    (every sentinel untouched)
#   (P3) leftover.kind==1 => leftover.cfg==requested    (THE changed clause)
#   (P4) leftover.kind==0 => leftover.cfg==0            (leftover sentinel untouched)
#   (P5) Forall k: kind==Old(kind); leftover.kind==Old(leftover.kind)  (frame)
#
# ORACLE GROUNDING: the only spec helper, `is_configurable(c) == (c.kind == 1)`,
# is a @Pure function FULLY UNFOLDED in the input field `c.kind`. It is NOT an
# opaque answer-key / marker an impl could echo without doing the work — echoing
# `is_configurable` literally IS the correct classification. So "ungrounded-
# oracle echo" has no WRONG echo to exhibit; we replace it with an honest
# cheapest-impl positive control and document this (see 'assessment').
#
# CONTROL-FLOW-EFFECT: the function returns None and has no raise/return-value
# branch; the only observable is the field mutations, fully captured by the value
# abstraction. No capability-token discriminator applies — class N/A.
#
# AXIOM LANE: meta.json axioms == [] (no @ContractOnly axiom is consumed). The
# two deep-model abstractions are A-REFERENCES validated `deep model == real
# callee` by axiom_check.py (G-AX). We carry them into the axiom lane as
# soundness/containment probes that RUN THE REAL callee in Docker on the
# gold-patched tree (see AXIOM_TESTS).
# ===========================================================================

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-26323"
FLOAT_ENCODING = None  # meta.json float_encoding is null (integer kind/cfg codes)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- unique sub-anchors inside the impl region ---------------------------
_LOOP_BODY = (
    "        c = children[i]\n"
    "        if is_configurable(c):\n"
    "            c.cfg = requested\n"
    "        i = i + 1\n"
)
_LEFTOVER = (
    "    if is_configurable(leftover):\n"
    "        leftover.cfg = requested\n"
)
_OPEN = "    i = 0\n    while i < len(children):\n"
_VIS_SENT_INV = (
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,\n"
    "                                                 children[k].cfg == 0), [[children[k]]])))"
)
_VIS_KIND_INV = (
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),\n"
    "                                                 children[k].kind == Old(children[k].kind))\n"
    "                                         , [[children[k]]])))"
)

# sanity: each anchor present exactly once in the frozen model
for _a in (_LOOP_BODY, _LEFTOVER, _OPEN, _VIS_SENT_INV, _VIS_KIND_INV):
    assert _BASE.count(_a) == 1, f"anchor drifted from model.py: {_a!r}"


# ===========================================================================
# (1) POSITIVE CONTROL (soundness) — structurally-different but CORRECT.
# Local-variable reshape + explicit else-branch in the loop body, and a hoisted
# guard local for the leftover write. Same decision, same data shape, loop kept
# forward with EVERY gold invariant verbatim (avoid-bug #2/#3: no induction
# lemma, no dropped framing assert). It MUST verify; if a faithful correct impl
# cannot satisfy the Ensures => SPEC-TOO-STRONG.
# ===========================================================================
_POS_LOOP = (
    "        c = children[i]\n"
    "        cfgable = is_configurable(c)\n"
    "        if cfgable:\n"
    "            c.cfg = requested\n"
    "        else:\n"
    "            pass  # sentinel: never configured, cfg stays at its default 0\n"
    "        i = i + 1\n"
)
_POS_LEFTOVER = (
    "    do_leftover = is_configurable(leftover)\n"
    "    if do_leftover:\n"
    "        leftover.cfg = requested\n"
)
_POS_MODULE = _swap(_swap(_BASE, _LOOP_BODY, _POS_LOOP), _LEFTOVER, _POS_LEFTOVER)


# ===========================================================================
# (2) ADMISSIBILITY — the precondition must accept a normal F2P-shaped input.
# Recovered-precond style: before running the gold work, read the actual in-scope
# parameters back through their Requires-granted predicates (len(children),
# children[0].kind/.cfg when non-empty, leftover.kind/.cfg) and ASSERT the
# domain facts the precondition promises (all listed children unconfigured;
# leftover unconfigured; requested != 0; leftover distinct from children[0]).
# If the call site cannot establish these for a normal input => PRECOND-TOO-STRONG.
# A genuine in-region self-call is avoided on purpose: constructing a fresh
# `List[Child]` with `list_pred` + the per-element Acc + the leftover-disjointness
# Forall would risk a list-construction PROOF gap (mislabeled). Reading the
# already-admitted parameters is the robust admissibility witness.
# ===========================================================================
_ADMISS_OPEN = (
    "    # admissibility witness: the Requires must admit this normal input.\n"
    "    Assert(requested != 0)                      # P-requested: genuine code\n"
    "    Assert(len(children) >= 0)                  # list_pred readable\n"
    "    Assert(leftover.cfg == 0)                   # leftover starts unconfigured\n"
    "    if len(children) > 0:\n"
    "        Assert(children[0].cfg == 0)            # listed child starts unconfigured\n"
    "        Assert(leftover is not children[0])     # leftover disjoint from children\n"
    # NOTE: the configure_output precondition does NOT constrain children[k].kind /
    # leftover.kind to {0, 1} (that bound lives only on Child.__init__, not on this
    # method's Requires). Asserting `kind == 0 or kind == 1` here therefore over-asserts
    # BEYOND the contract and is a probe bug, not a too-strong precondition -- the spec
    # is total over any integer kind (the cfg post-clauses simply do not fire for an
    # out-of-range kind). The kind-validity asserts are dropped so the witness reads
    # back ONLY facts the Requires actually promises.
    "    i = 0\n    while i < len(children):\n"
)
_ADMISS_MODULE = _swap(_BASE, _OPEN, _ADMISS_OPEN)


# ===========================================================================
# (3) PARTIAL-DOMAIN #1 — the PRE-PATCH rival (THE canonical attack).
# Drops the leftover-columns write entirely: configures the looped children but
# NEVER the leftover. This is exactly model_prepatch.py. expect=reject via P3.
# ===========================================================================
_REJ_DROP_LEFTOVER = "    pass  # BUG: leftover-columns child never configured\n"
_REJ_DROP_LEFTOVER_MODULE = _swap(_BASE, _LEFTOVER, _REJ_DROP_LEFTOVER)


# ===========================================================================
# (4) PARTIAL-DOMAIN #2 — leftover configured UNCONDITIONALLY (drops the guard).
# Sets leftover.cfg = requested even when the leftover is a routing sentinel.
# expect=reject via P4 (leftover.kind==0 => leftover.cfg==0).
# ===========================================================================
_REJ_LEFTOVER_UNCOND = "    leftover.cfg = requested  # BUG: configures even a sentinel leftover\n"
_REJ_LEFTOVER_UNCOND_MODULE = _swap(_BASE, _LEFTOVER, _REJ_LEFTOVER_UNCOND)


# ===========================================================================
# (5) VALUE-PERTURBATION (supporting) — leftover configured with the WRONG code.
# Configures the leftover estimator but to `requested + 1`, a DIFFERENT container
# code. expect=reject via P3 (must be EXACTLY requested). Cheap supporting case;
# it still carries a real refinement (a patch passing a different transform code
# to the remainder would round-trip the wrong container and not resolve).
# ===========================================================================
_REJ_LEFTOVER_WRONGVAL = (
    "    if is_configurable(leftover):\n"
    "        leftover.cfg = requested + 1  # BUG: wrong output-container code\n"
)
_REJ_LEFTOVER_WRONGVAL_MODULE = _swap(_BASE, _LEFTOVER, _REJ_LEFTOVER_WRONGVAL)


# ===========================================================================
# (6) VALUE DOUBLE-MASK / sentinel-also-configured — configures EVERY looped
# child, including routing sentinels. To keep the rejection ATTRIBUTABLE to the
# postcondition (not to a loop-invariant proof trigger), the visited-sentinel
# loop invariant is realigned to the rival's behaviour (visited sentinel ==
# requested). The rival then verifies the loop yet is rejected by the
# POSTCONDITION P2 (kind==0 => cfg==0). This is the value-proxy attack: claiming
# "configured" for a child the spec requires to stay at its default.
# ===========================================================================
_REJ_DOUBLEMASK_LOOP = (
    "        c = children[i]\n"
    "        c.cfg = requested  # BUG: configures sentinels too\n"
    "        i = i + 1\n"
)
_REJ_DOUBLEMASK_INV = (
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                                                 children[k].cfg == requested), [[children[k]]])))"
)
_REJ_DOUBLEMASK_MODULE = _swap(
    _swap(_BASE, _LOOP_BODY, _REJ_DOUBLEMASK_LOOP),
    _VIS_SENT_INV, _REJ_DOUBLEMASK_INV,
)


# ===========================================================================
# (7) FRAME-KIND-MUTATION — reclassify a sentinel as an estimator to satisfy the
# cfg clause vacuously. The rival sets `c.kind = 1; c.cfg = requested` for EVERY
# child: the per-child cfg clauses P1/P2 are then trivially satisfied (everything
# is kind==1 with cfg==requested), but the FRAME postcondition P5
# (children[k].kind == Old(children[k].kind)) is violated for the sentinels.
# To make the rejection attributable to P5 (not to the kind-preservation loop
# invariant), that invariant is dropped from the loop. expect=reject.
# This is the frame attack adapted to a FULL-permission-but-pinned field: the
# write is permitted, but the postcondition forbids changing the classification.
# (No insufficient-permission error arises because kind is not read-only here;
# see has_readonly_input note above.)
# ===========================================================================
_REJ_FRAMEKIND_LOOP = (
    "        c = children[i]\n"
    "        c.kind = 1  # FRAME ATTACK: reclassify sentinel as estimator\n"
    "        c.cfg = requested\n"
    "        i = i + 1\n"
)
# drop the kind-preservation loop invariant so the rival reaches the postcondition
_REJ_FRAMEKIND_INV = (
    "        # (kind-preservation invariant dropped by the frame-mutation rival)"
)
_REJ_FRAMEKIND_MODULE = _swap(
    _swap(_BASE, _LOOP_BODY, _REJ_FRAMEKIND_LOOP),
    _VIS_KIND_INV, _REJ_FRAMEKIND_INV,
)


SPEC_TESTS = [
    {
        "id": "pos-control-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MODULE,
        "rationale": (
            "Structurally-different but CORRECT impl: the configurability test is "
            "hoisted into a local (`cfgable` in the loop, `do_leftover` for the "
            "leftover) and an explicit else-branch documents the sentinel no-op. "
            "Same decision, same forward loop, EVERY gold invariant kept verbatim "
            "(no induction lemma, no dropped framing assert). Must verify; if it "
            "cannot satisfy the Ensures the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_MODULE,
        "rationale": (
            "Reads the actual in-scope parameters back through their Requires "
            "predicates and asserts the domain facts the precondition promises "
            "(requested != 0; every listed child and the leftover start "
            "unconfigured at cfg==0; leftover disjoint from children) for a normal "
            "F2P-shaped input, then runs the gold work. (Kind-validity asserts are "
            "NOT included: the precondition does not bound kind to {0,1}, so "
            "asserting that would over-assert beyond the contract.) If the "
            "call site cannot establish the Requires for this input => "
            "PRECOND-TOO-STRONG. A fresh-list self-call is avoided to dodge a "
            "list-construction proof gap (would mislabel)."
        ),
    },
    {
        "id": "weak-drop-leftover-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DROP_LEFTOVER_MODULE,
        "refinement": (
            "This IS the pre-patch behaviour (model_prepatch.py): the loop "
            "configures the listed children but the leftover-columns child is "
            "NEVER configured. Its faithful real patch is the UNPATCHED set_output "
            "(no `if self.remainder not in {passthrough, drop}: _safe_set_output(...)` "
            "hunk) — precisely what FAILS the F2P test_remainder_set_output: a "
            "leftover-columns VarianceThreshold returns a numpy array instead of "
            "the requested DataFrame, so `assert_frame_equal(out, df)` fails. It "
            "does NOT resolve; a verifying rival would be a true verify-not-resolve "
            "break."
        ),
        "rationale": (
            "Rejected by postcondition P3, Implies(leftover.kind==1, "
            "leftover.cfg==requested): the leftover estimator is left at cfg==0. "
            "(This is exactly the clause G-DIFF reports model_prepatch.py failing.)"
        ),
    },
    {
        "id": "weak-leftover-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_LEFTOVER_UNCOND_MODULE,
        "refinement": (
            "Drops the sentinel guard: `_safe_set_output(self.remainder, ...)` is "
            "called even when self.remainder is 'passthrough'/'drop'. Its faithful "
            "real patch (calling _safe_set_output on the string sentinel) raises "
            "AttributeError ('str' has no set_output) at fit time, breaking BOTH "
            "the F2P AND the remainder='drop'/'passthrough' P2P tests "
            "(test_column_transformer_*remainder*). It does NOT resolve."
        ),
        "rationale": (
            "Rejected by postcondition P4, Implies(leftover.kind==0, "
            "leftover.cfg==0): a sentinel leftover is forced to cfg==requested."
        ),
    },
    {
        "id": "weak-leftover-wrong-code",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_LEFTOVER_WRONGVAL_MODULE,
        "refinement": (
            "Configures the leftover estimator but to a DIFFERENT container code "
            "(requested+1). Its faithful real patch passes a transform code other "
            "than the requested one to _safe_set_output(self.remainder, ...), so "
            "the leftover estimator records the wrong container and the round-trip "
            "yields the wrong type (not the requested 'pandas' DataFrame) — the "
            "F2P assert_frame_equal fails. It does NOT resolve. (Cheap supporting "
            "value-perturbation case; carries a real refinement.)"
        ),
        "rationale": (
            "Rejected by postcondition P3, Implies(leftover.kind==1, "
            "leftover.cfg==requested): cfg is required to equal EXACTLY requested, "
            "and requested+1 != requested (requested is an arbitrary code)."
        ),
    },
    {
        "id": "weak-double-mask-sentinels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DOUBLEMASK_MODULE,
        "refinement": (
            "Configures EVERY looped child, including routing sentinels "
            "('passthrough'/'drop'). Its faithful real patch drops the generator's "
            "sentinel filter and calls _safe_set_output on the string sentinels, "
            "raising AttributeError at set_output time — breaking the remainder/"
            "passthrough/drop P2P tests AND the F2P. It does NOT resolve."
        ),
        "rationale": (
            "Rejected by postcondition P2, Implies(children[k].kind==0, "
            "children[k].cfg==0): a sentinel child is forced to cfg==requested. "
            "(The visited-sentinel loop invariant is realigned to the rival so the "
            "rejection is attributable to P2, not to a loop-invariant proof gap.)"
        ),
    },
    {
        "id": "weak-frame-kind-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_FRAMEKIND_MODULE,
        "refinement": (
            "Frame attack: instead of doing the classification work, the rival "
            "RECLASSIFIES every child as an estimator (c.kind = 1) and configures "
            "it, making the per-child cfg clauses hold vacuously. Its faithful real "
            "patch would have to MUTATE the child objects' estimator-vs-sentinel "
            "identity (turn 'passthrough'/'drop' into estimators) before "
            "configuring — there is no such operation in set_output; the real "
            "sentinels stay sentinels and calling _safe_set_output on them raises. "
            "It does NOT resolve."
        ),
        "rationale": (
            "Rejected by the FRAME postcondition P5, Forall k: children[k].kind == "
            "Old(children[k].kind): the sentinels' kind is changed from 0 to 1. "
            "Note this rejects on the kind-PRESERVATION postcondition, NOT on "
            "insufficient permission (kind is full-permission here, not "
            "Acc(.,1/2)); the kind-preservation loop invariant is dropped so the "
            "rejection is attributable to P5. This is the frame-condition defence "
            "adapted to a full-permission-but-pinned field."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — no @ContractOnly axiom is CONSUMED (meta.axioms == []), but the
# deep model abstracts two unchanged repo callees as A-REFERENCES (meta
# deep_model_references). The obligation is the same as axiom soundness: the deep
# model must EQUAL the real callee on every caller-reachable input, UNDER the
# caller's actual runtime config (gold-patched set_output, output config records
# the requested 'transform' string). We RUN the real callees in Docker on the
# gold-patched tree (apply_gold=True) and assert the deep model is faithful +
# the caller never reaches an input outside the abstracted callee's domain.
# The probes embed axiom_check.py's verified logic (read on the HOST at load
# time, per avoid-bug #6) and additionally FUZZ the boundaries/sentinels.
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


# --- A-reference 1: configuration primitive `cfg = requested` --------------
# Soundness: the real `_safe_set_output(est, transform=t)` records EXACTLY `t`
# (the deep model `cfg = requested`), for the container codes the caller actually
# requests ('pandas'/'default'), AND for fuzzed extra codes — confirming the
# write records the requested value verbatim with no transform/aliasing.
_AX_PRIMITIVE_PROBE = (
    "import sys\n"
    "# embedded axiom_check.py (host read at load time; not mounted in-container)\n"
    + _AXIOM_CHECK_SRC.replace("if __name__ == \"__main__\":\n    sys.exit(main())", "")
    + "\n\n"
    "def _fuzz_primitive():\n"
    "    from sklearn.utils._set_output import _safe_set_output, _get_output_config\n"
    "    from sklearn.preprocessing import StandardScaler\n"
    "    from sklearn.feature_selection import VarianceThreshold\n"
    "    # caller-reachable requested codes are the non-None container strings;\n"
    "    # the deep model `cfg = requested` must record EXACTLY the requested code\n"
    "    for est_cls in (StandardScaler, VarianceThreshold):\n"
    "        for transform in ('pandas', 'default'):\n"
    "            est = est_cls()\n"
    "            _safe_set_output(est, transform=transform)\n"
    "            cfg = _get_output_config('transform', est)['dense']\n"
    "            assert cfg == transform, (\n"
    "                'deep-model unsound: requested %r, recorded %r (est %s)'\n"
    "                % (transform, cfg, est_cls.__name__))\n"
    "    print('PRIMITIVE OK: _safe_set_output records the requested code exactly '\n"
    "          'for pandas/default on StandardScaler+VarianceThreshold')\n"
    "\n"
    "try:\n"
    "    check_safe_set_output_primitive()\n"
    "    _fuzz_primitive()\n"
    "except Exception as e:\n"
    "    print('PRIMITIVE VIOLATED:', repr(e))\n"
    "    sys.exit(1)\n"
    "sys.exit(0)\n"
)

# --- A-reference 2: sentinel classification `is_configurable` --------------
# Soundness + containment: the real guard `trans not in {'passthrough','drop'}`
# classifies EXACTLY the two routing strings as sentinels (kind==0) and every
# real estimator (incl. the leftover-columns VarianceThreshold the F2P uses) as
# configurable (kind==1). Containment: the only children the caller can reach are
# routing strings OR estimator instances — both are inside the guard's domain
# (the `in {...}` test is total). The end-to-end witness re-derives the WHOLE
# pinned behaviour on the real composite (the F2P reproducer): a leftover-columns
# estimator under set_output('pandas') preserves the DataFrame; under 'default'
# yields a numpy array.
_AX_CLASSIFY_PROBE = (
    "import sys\n"
    + _AXIOM_CHECK_SRC.replace("if __name__ == \"__main__\":\n    sys.exit(main())", "")
    + "\n\n"
    "def _fuzz_classification():\n"
    "    from sklearn.preprocessing import StandardScaler, Normalizer, OneHotEncoder\n"
    "    from sklearn.feature_selection import VarianceThreshold\n"
    "    # the EXACT routing sentinels (kind==0) and nothing else\n"
    "    assert _is_estimator('passthrough') is False\n"
    "    assert _is_estimator('drop') is False\n"
    "    # every real estimator the caller can hold is configurable (kind==1),\n"
    "    # including the leftover-columns VarianceThreshold used by the F2P\n"
    "    for est in (StandardScaler(), Normalizer(), OneHotEncoder(), VarianceThreshold()):\n"
    "        assert _is_estimator(est) is True, 'estimator misclassified: %r' % est\n"
    "    # containment: caller children are either a routing string or an estimator;\n"
    "    # the `in {passthrough, drop}` guard is total over both, so every\n"
    "    # caller-reachable child lies in the guard's domain (no uncovered input)\n"
    "    print('CLASSIFY OK: {passthrough, drop} are the exact sentinels; '\n"
    "          'StandardScaler/Normalizer/OneHotEncoder/VarianceThreshold are '\n"
    "          'configurable; guard total over all caller-reachable children')\n"
    "\n"
    "try:\n"
    "    check_sentinel_classification()\n"
    "    _fuzz_classification()\n"
    "    check_composite_behaviour_estimator_remainder()\n"
    "except Exception as e:\n"
    "    print('CLASSIFY VIOLATED:', repr(e))\n"
    "    sys.exit(1)\n"
    "sys.exit(0)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-safe-set-output-primitive",
        "axiom": "deep-model: cfg = requested  (~ _safe_set_output)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PRIMITIVE_PROBE,
        "rationale": (
            "A-reference 1. The deep model `cfg = requested` claims configuring an "
            "estimator records EXACTLY the requested output-container code. Runs the "
            "real _safe_set_output on real estimators for 'pandas'/'default' (the "
            "caller-reachable codes) and reads back _get_output_config(...)['dense']; "
            "any mismatch => the deep model is UNSOUND (AXIOM-UNSOUND)."
        ),
    },
    {
        "id": "ax-cover-sentinel-classification",
        "axiom": "deep-model: is_configurable  (~ trans not in {passthrough, drop})",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CLASSIFY_PROBE,
        "rationale": (
            "A-reference 2. The deep model `is_configurable(c) == (kind==1)` claims "
            "a child is configurable iff it is not a routing sentinel. Runs the real "
            "guard `trans not in {passthrough, drop}` on the two sentinels and on "
            "real estimators (incl. the F2P's VarianceThreshold): asserts the "
            "classification matches and that every caller-reachable child (a routing "
            "string OR an estimator) lies in the guard's total domain — no uncovered "
            "input (AXIOM-TOO-WEAK-FOR-CALLER would be a reachable child outside it). "
            "Also re-runs the end-to-end F2P reproducer on the real composite."
        ),
    },
]
