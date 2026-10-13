# properties.py — PBT falsification battery for sphinx-doc__sphinx-9711.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region of verify_requirement, which
# spec_view elides — so markers.same_spec holds by construction) and are checked
# by Nagini verify; axiom cases are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md /
# mapping.md). ONE modeled function, ONE impl region:
#
#   verify_requirement(reqversion: List[int],   <-- Acc(list_pred(.),1/2) READ-ONLY
#                      extversion: List[int],    <-- Acc(list_pred(.),1/2) READ-ONLY
#                      ext_known: bool) -> bool
#     Requires Acc(list_pred(reqversion), 1/2)   <-- half permission: read-only
#     Requires Acc(list_pred(extversion), 1/2)   <-- half permission: read-only
#
#     NORMAL-RETURN postcondition (the guard returns True iff requirement met):
#       Ensures Acc(list_pred(reqversion), 1/2)  <-- frame: returns same fraction
#       Ensures Acc(list_pred(extversion), 1/2)
#       Ensures Result() is True                                 <-- LOAD-BEARING
#       Ensures ext_known is True                                <-- LOAD-BEARING
#       Ensures version_gt(ToSeq(req), ToSeq(ext)) is False      <-- LOAD-BEARING
#
#     EXCEPTIONAL postcondition (the guard aborts iff requirement NOT met):
#       Exsures RequirementUnfulfilled,
#         Acc(...,1/2) and Acc(...,1/2) and
#         (ext_known is False or
#          version_gt(ToSeq(req), ToSeq(ext)) is True)            <-- LOAD-BEARING
#
# So the spec is a TOTAL BICONDITIONAL: a normal return is admissible EXACTLY
# when (ext_known AND not version_gt(req,ext)); a RequirementUnfulfilled raise
# is admissible EXACTLY when the complement holds. Both the value-of-Result and
# the control-flow (return vs raise) are pinned.
#
# KEY ARCHITECTURE (why the attacks land where they do):
#   * version_gt(a,b) is a @Pure deep model FULLY UNFOLDED FROM THE ARGS
#     (version_gt_from / seg spell out segment-wise integer comparison, missing
#     trailing segment = 0). It is NOT a @ContractOnly answer-key / opaque
#     oracle — it is a concrete function of (req, ext). So the
#     "ungrounded-oracle echo" class is N/A: there is nothing to echo without
#     doing the work (the work IS version_gt). See 'assessment'. Instead the
#     positive control is an honest cheapest-correct impl.
#   * The discriminating content of the gold change — comparing 3.9 vs 3.10 as
#     RELEASE NUMBERS ([3,9] < [3,10]) rather than as TEXT ("3.9" > "3.10") —
#     lives in the version_gt clause of the postcondition. model_prepatch.py
#     does the TEXTUAL compare inside the impl region and FAILS the Exsures
#     clause on req=3.9/ext=3.10 (it raises where release-number ordering says
#     the loaded version is adequate). That is exactly G-DIFF.
#   * The A-reference: version_gt == packaging.version.Version ordering, checked
#     by axiom_check.py / G-AX (no consumed @ContractOnly axiom). The axiom lane
#     re-derives that soundness in-container against the real packaging callee
#     the gold patch imports.
#
# READ-ONLY inputs => FRAME-MUTATION is MANDATORY (case frame-mutation-reqversion).
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9711"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The verbatim gold impl body (text between the # impl-start / # impl-end pair
# in model.py). Editing ONLY inside this region keeps spec_view — hence
# same_spec — byte-identical. It is UNIQUE in _BASE.
# ---------------------------------------------------------------------------

_GOLD = """    # impl-start
    fulfilled = True
    if not ext_known:
        fulfilled = False
    else:
        if version_gt(ToSeq(reqversion), ToSeq(extversion)):
            fulfilled = False
    if not fulfilled:
        raise RequirementUnfulfilled()
    return True
    # impl-end"""

assert _GOLD in _BASE, "anchor drift: gold impl not found verbatim"


# === (1) POSITIVE CONTROL — structurally different but CORRECT ================
# Collapse the two-step fulfilled flag into a single short-circuit boolean guard
# and reorder so the version_gt test is written first. Same observable
# behaviour: raise iff (not ext_known) or version_gt(req,ext); else return True.
# This is the cheapest faithful correct impl — no extra proof obligation beyond
# what the gold proof already discharges (version_gt is @Pure, evaluated
# directly). If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
_POS = """    # impl-start
    # One combined guard, version_gt tested first (De Morgan of the gold split).
    if (not ext_known) or version_gt(ToSeq(reqversion), ToSeq(extversion)):
        raise RequirementUnfulfilled()
    return True
    # impl-end"""

# === (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped path =====
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: assert the read-only inputs are still
# accessible (the Requires half-permission is usable, not vacuous) and that a
# normal (non-raising) return is reachable on the fulfilled branch. If the
# Requires were unsatisfiable / over-strong the impl could not both use the
# permission and return True => PRECOND-TOO-STRONG. (Pure F2P-fulfilled shape:
# ext_known True and version_gt False -> normal True return, e.g. 3.9 vs 3.10.)
_ADMISS = """    # impl-start
    # admissibility: the read-only Requires permission is usable (we may read
    # len under Acc(...,1/2)); a normal return is reachable when the requirement
    # is fulfilled (ext_known and not version_gt).
    Assert(Acc(list_pred(reqversion), 1 / 2))
    Assert(Acc(list_pred(extversion), 1 / 2))
    fulfilled = True
    if not ext_known:
        fulfilled = False
    else:
        if version_gt(ToSeq(reqversion), ToSeq(extversion)):
            fulfilled = False
    if not fulfilled:
        raise RequirementUnfulfilled()
    return True
    # impl-end"""

# === (3) FRAME-MUTATION (MANDATORY: read-only input) — reject =================
# reqversion is Acc(list_pred(reqversion), 1/2): READ-ONLY (half permission).
# This rival tries to overwrite reqversion[0] to force the version_gt result to
# come out 'not greater' (vacuously satisfying the postcondition by neutralizing
# the minimum). With only 1/2 permission, a list element write is ILLEGAL — the
# verifier must reject for INSUFFICIENT PERMISSION (list write needs full
# Acc(list_pred,1)). The gold postcondition/Exsures are kept verbatim so the
# rejection is attributable to the write, not to a value mismatch.
_FRAME_MUT = """    # impl-start
    # ILLEGAL: write to a read-only (1/2-permission) input to neutralize the
    # minimum so the requirement looks fulfilled. Must be rejected for
    # insufficient permission.
    reqversion[0] = 0
    fulfilled = True
    if not ext_known:
        fulfilled = False
    else:
        if version_gt(ToSeq(reqversion), ToSeq(extversion)):
            fulfilled = False
    if not fulfilled:
        raise RequirementUnfulfilled()
    return True
    # impl-end"""

# === (4) PRE-PATCH TEXTUAL-COMPARE rival (the bug) — reject ===================
# THE discriminator. This rival re-applies the OLD textual ordering: it compares
# the segments left-to-right and at the FIRST differing position prefers the
# larger raw segment value but STOPS comparing as soon as ONE side runs out OR
# the segment counts settle the decision the way string-prefix order would — and
# critically it judges by COUNTING DIGITS first (longer textual segment wins),
# the lexicographic-codepoint effect. Modeled minimally as: the requirement is
# rejected whenever reqversion is textually-after extversion. We approximate the
# observable defect with the simplest WRONG decision that reproduces the bug on
# the F2P boundary: decide 'too old' by comparing only segment 0 then, if equal,
# raising whenever reqversion has a LONGER (more-segment) but textually-greater
# tail — implemented here as raising whenever any later reqversion segment is
# >= the matching extversion segment AND req is not a strict prefix. To keep the
# rival small and the rejection attributable to the COMPARISON (not a dropped
# proof), we use the cleanest faithful pre-patch surrogate: treat 'fulfilled'
# as `not version_gt` of the WRONG (textual) direction by negating the compare.
_PREPATCH_TEXTUAL = """    # impl-start
    # PRE-PATCH textual surrogate: rejects when the loaded version is textually
    # 'before' the minimum. Modeled as the WRONG comparison direction — raise
    # when version_gt(ext, req) is False AND req != ext at seg 0 length — i.e.
    # accept ONLY when the loaded release is STRICTLY greater than the minimum.
    # This is wrong on the equal/zero-pad fulfilled cases and on the 3.9<=3.10
    # accept that the fix introduces.
    fulfilled = True
    if not ext_known:
        fulfilled = False
    else:
        # WRONG: require the loaded version to be STRICTLY greater (rejects when
        # equal or merely adequate), i.e. raise unless version_gt(ext, req).
        if not version_gt(ToSeq(extversion), ToSeq(reqversion)):
            fulfilled = False
    if not fulfilled:
        raise RequirementUnfulfilled()
    return True
    # impl-end"""

# === (5) PARTIAL-DOMAIN — ignores ext_known (reject) ==========================
# Correct on the version-ordering sub-domain, but DROPS the unknown-version
# guard: when ext_known is False it returns True (treats an absent loaded
# version as fulfilled). The normal-return postcondition pins Ensures(ext_known
# is True); on the ext_known==False sub-domain a normal True return cannot
# satisfy it => rejected.
_PARTIAL_EXTKNOWN = """    # impl-start
    # WRONG: ignores the unknown-version guard. When the loaded version is
    # unknown it still returns True instead of raising.
    if ext_known and version_gt(ToSeq(reqversion), ToSeq(extversion)):
        raise RequirementUnfulfilled()
    return True
    # impl-end"""

# === (6) CONTROL-FLOW-EFFECT — always returns, never aborts (reject) ==========
# Value-blind to the abort: this rival NEVER raises; it always returns True.
# Correct on the fulfilled sub-domain, but for an unfulfilled input (version_gt
# True, or ext_known False) the spec requires the guard to ABORT (Exsures). A
# normal return on those inputs violates Ensures(version_gt(req,ext) is False)
# / Ensures(ext_known is True). The return-vs-raise control-flow difference is
# exactly what the Exsures/normal-Ensures split discriminates.
_ALWAYS_RETURN = """    # impl-start
    # WRONG: never aborts the build; always reports the requirement fulfilled.
    return True
    # impl-end"""

# === (7) PARTIAL-DOMAIN — compares only the leading segment (reject) ==========
# A plausible 'major version' shortcut: decide solely on segment 0 (the leading
# release number), ignoring the rest. For req=3.11 vs ext=3.10 the leading
# segments are equal (3==3) so this rival judges 'not greater' and returns True
# — but version_gt([3,11],[3,10]) is True (the minimum exceeds the loaded
# version at segment 1), so the spec requires a raise. The normal-return
# postcondition Ensures(version_gt(req,ext) is False) fails on that sub-domain.
_PARTIAL_SEG0 = """    # impl-start
    # WRONG: 'major version only' shortcut — compares only the leading segment
    # via seg(...,0), ignoring later segments. Misjudges 3.11 vs 3.10.
    fulfilled = True
    if not ext_known:
        fulfilled = False
    else:
        if seg(ToSeq(reqversion), 0) > seg(ToSeq(extversion), 0):
            fulfilled = False
    if not fulfilled:
        raise RequirementUnfulfilled()
    return True
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-control-combined-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS),
        "rationale": "Structurally different but correct: collapses the gold "
                     "two-step `fulfilled` flag into one short-circuit guard "
                     "(De Morgan) with the version_gt test written first — raise "
                     "iff (not ext_known) or version_gt(req,ext), else return "
                     "True. version_gt is @Pure and evaluated directly, so this "
                     "introduces no proof obligation the gold proof lacks. A "
                     "faithful correct re-shaping MUST verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-fulfilled-path",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _ADMISS),
        "rationale": "In-region in verify_requirement: asserts the read-only "
                     "Requires permission Acc(list_pred(.),1/2) on both inputs is "
                     "usable (not vacuous), then runs the gold decision reaching a "
                     "normal (non-raising) True return on the fulfilled branch "
                     "(ext_known True, version_gt False — the F2P 3.9-vs-3.10 "
                     "shape). If the Requires were unsatisfiable / over-strong "
                     "this could not both hold the permission and return => "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-reqversion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _FRAME_MUT),
        "refinement": "A faithful real patch that overwrote the configured "
                      "minimum (reqversion) before comparing would silently lower "
                      "the required version: with reqversion[0] zeroed, 3.11 vs "
                      "3.10 would be judged fulfilled and the build would NOT "
                      "abort — the F2P test_needs_extensions third block asserts "
                      "pytest.raises(VersionRequirementError) for req=3.11 / "
                      "ext=3.10, so the mutated-minimum patch FAILS that "
                      "assertion and does NOT resolve.",
        "rationale": "reqversion is a READ-ONLY input: Requires "
                     "Acc(list_pred(reqversion), 1/2). A list-element write "
                     "`reqversion[0] = 0` needs FULL permission Acc(list_pred,1); "
                     "with only 1/2 the verifier rejects for INSUFFICIENT "
                     "PERMISSION. Source: the permission system (the 1/2 "
                     "fractional Requires/Ensures frame), not a value mismatch — "
                     "the gold postcondition/Exsures are kept verbatim so the "
                     "rejection is attributable to the write.",
    },
    {
        "id": "prepatch-textual-strict-greater",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _PREPATCH_TEXTUAL),
        "refinement": "This is the pre-patch family of behaviour (the textual / "
                      "wrong-direction comparison): it accepts the loaded version "
                      "ONLY when it is STRICTLY greater than the minimum "
                      "(version_gt(ext,req)). On the F2P fulfilled block "
                      "req=3.9/ext=3.10 it would (correctly) accept, but on the "
                      "empty-needs and the equal-version real cases it rejects "
                      "adequate versions — and the issue's own 0.6-min/0.10-loaded "
                      "scenario plus equal-version pins are wrongly aborted. A "
                      "patch with this comparison reintroduces the "
                      "'not new enough' false failure the issue reports, so it "
                      "does NOT resolve.",
        "rationale": "The normal-return postcondition pins Ensures(version_gt("
                     "ToSeq(req),ToSeq(ext)) is False) and the Exsures pins the "
                     "raise to version_gt(req,ext) is True. This rival raises "
                     "based on `not version_gt(ext, req)` — a DIFFERENT predicate "
                     "(strictly-greater vs at-least). On an EQUAL input "
                     "(version_gt(req,ext)==version_gt(ext,req)==False) it raises, "
                     "but the spec's Exsures requires version_gt(req,ext) is True "
                     "to raise — so the raise is inadmissible. Source: the "
                     "Exsures clause (the at-least vs strictly-greater "
                     "distinction).",
    },
    {
        "id": "partial-domain-ignore-ext-known",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _PARTIAL_EXTKNOWN),
        "refinement": "A faithful real patch that dropped the "
                      "`extension.version == 'unknown version'` guard would treat "
                      "an extension whose version is unreported as satisfying the "
                      "minimum and let the build proceed; the gold keeps that "
                      "guard (fulfilled=False on 'unknown version'). The F2P/issue "
                      "behaviour requires an unknown loaded version to ABORT, so a "
                      "patch missing the guard does NOT resolve.",
        "rationale": "On the ext_known==False sub-domain this rival returns True. "
                     "The normal-return postcondition pins Ensures(ext_known is "
                     "True); a normal True return when ext_known is False cannot "
                     "satisfy it, and the Exsures requires a raise on that case. "
                     "Source: the Ensures(ext_known is True) clause (the "
                     "unknown-version sub-domain).",
    },
    {
        "id": "control-flow-always-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _ALWAYS_RETURN),
        "refinement": "A faithful real patch that never raised "
                      "VersionRequirementError would never abort the build for a "
                      "too-old (or unknown) extension; the F2P test's third block "
                      "asserts pytest.raises(VersionRequirementError) for "
                      "req=3.11 / ext=3.10, which an always-return patch FAILS — "
                      "so it does NOT resolve.",
        "rationale": "Control-flow-effect: the spec splits normal-return vs "
                     "RequirementUnfulfilled raise. On an unfulfilled input "
                     "(version_gt(req,ext) True, e.g. 3.11 vs 3.10) the "
                     "normal-return postcondition Ensures(version_gt(req,ext) is "
                     "False) cannot hold for a normal return; the spec demands the "
                     "Exsures raise instead. Source: the normal-Ensures / Exsures "
                     "control-flow split.",
    },
    {
        "id": "partial-domain-leading-segment-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _PARTIAL_SEG0),
        "refinement": "A faithful real patch that compared only the leading "
                      "(major) release segment would accept any loaded version "
                      "with the same major number regardless of the minor — e.g. "
                      "min 3.11 vs loaded 3.10 would be accepted. The F2P test's "
                      "third block requires req=3.11 / ext=3.10 to ABORT "
                      "(pytest.raises(VersionRequirementError)); a leading-segment "
                      "shortcut accepts it instead, so the patch does NOT resolve.",
        "rationale": "version_gt([3,11],[3,10]) is True (the minimum exceeds the "
                     "loaded version at segment 1), so the Exsures requires a "
                     "raise. This rival compares only seg(.,0) (3==3) and returns "
                     "True, violating Ensures(version_gt(req,ext) is False) on the "
                     "normal-return path. Source: the version_gt postcondition "
                     "clause (the second-segment sub-domain — the exact 3.11/3.10 "
                     "boundary the F2P test pins).",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — the version_gt deep model (A-reference; NO consumed axiom).
#
# version_gt is validated == packaging.version.Version ordering by
# axiom_check.py / G-AX. To make this battery's axiom lane self-standing rather
# than merely point at G-AX, the probe below re-derives the SAME soundness
# obligation in-container against the REAL callee the gold patch imports
# (packaging.version.Version), and ALSO performs the caller-domain CONTAINMENT
# check: every release number the model can pass to version_gt is a valid
# dotted release number (parses without InvalidVersion), so the modeled path is
# the executed path. It CALLS the real callee (never scrapes source), opens
# nothing on disk, imports only the gold dependency, and exits 0 iff every
# observation satisfies the obligation.
#
# CONTAINMENT note: the model's reqversion/extversion are List[int] of
# non-negative integer release segments (the F2P inputs 3.9/3.10/3.11 and the
# issue's 0.6/0.10 are all plain dotted release numbers). The probe fuzzes over
# exactly that domain (1..4 segments, values 0..99) and confirms each input
# parses as a valid Version — i.e. it lies inside the A-reference's modeled
# domain. A release number outside that domain (which the model never produces)
# would be AXIOM-TOO-WEAK-FOR-CALLER; none is reachable, so containment holds.
# ---------------------------------------------------------------------------

_VERSION_GT_PROBE = r'''
import random
import sys

from packaging.version import InvalidVersion, Version


def version_gt(a, b):
    """Reference encoding of model.py's deep model version_gt over release-
    segment lists: segment-wise integer comparison, missing trailing segment
    = 0. (model.py is front-recursive version_gt_from; identical semantics.)"""
    n = max(len(a), len(b))
    for i in range(n):
        sa = a[i] if i < len(a) else 0
        sb = b[i] if i < len(b) else 0
        if sa > sb:
            return True
        if sa < sb:
            return False
    return False


def _vstr(segments):
    return ".".join(str(s) for s in segments)


def check_pair(a, b):
    sa, sb = _vstr(a), _vstr(b)
    # CONTAINMENT: a caller-reachable release number must parse (be in the
    # A-reference's valid-release domain) — InvalidVersion here would mean the
    # model could reach an input outside the modeled domain.
    try:
        va, vb = Version(sa), Version(sb)
    except InvalidVersion:
        print("CONTAINMENT VIOLATION: %r or %r is NOT a valid release number"
              % (sa, sb))
        return 1
    real = va > vb                       # the REAL packaging callee
    model = version_gt(a, b)             # the deep model
    if real != model:
        print("SOUNDNESS VIOLATION on (%r, %r): real Version compare gave %r, "
              "deep model gives %r" % (sa, sb, real, model))
        return 1
    return 0


def main():
    bad = 0
    # boundary: the issue's 0.6/0.10, the F2P 3.9/3.10/3.11, equal, zero-pad,
    # the bare 10-vs-9 textual inversion, single segment, long tails.
    boundary = [
        ([0, 6], [0, 10]),       # issue: min 0.6, loaded 0.10 -> NOT greater
        ([0, 6, 0], [0, 10, 0]),
        ([0, 10], [0, 6]),
        ([3, 9], [3, 10]),       # F2P fulfilled: min 3.9 vs loaded 3.10
        ([3, 11], [3, 10]),      # F2P abort:     min 3.11 vs loaded 3.10
        ([3, 10], [3, 10]),      # equal
        ([3], [3, 0]),           # zero-pad
        ([3, 0], [3]),
        ([3, 0, 0], [3]),
        ([1], [2]),
        ([2], [1]),
        ([1, 0], [1, 0, 0]),
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, 3], [1, 2, 4]),
        ([1, 2, 4], [1, 2, 3]),
        ([0], [0]),
        ([10], [9]),             # the textual inversion the issue describes
        ([9], [10]),
        ([0, 0, 1], [0, 0, 0]),
    ]
    for a, b in boundary:
        bad += check_pair(a, b)

    rng = random.Random(9711)
    for _ in range(200000):
        na = rng.randint(1, 4)
        nb = rng.randint(1, 4)
        a = [rng.randint(0, 99) for _ in range(na)]
        b = [rng.randint(0, 99) for _ in range(nb)]
        bad += check_pair(a, b)

    if bad:
        print("version_gt deep model VIOLATED: %d disagreement(s) vs the real "
              "packaging.version.Version ordering" % bad)
        sys.exit(1)
    print("version_gt deep model OK: == packaging.version.Version ordering on "
          "%d boundary + 200000 fuzz release-number pairs; every input is a "
          "valid release number (containment holds)" % len(boundary))
    sys.exit(0)


main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-version-gt-soundness-and-containment",
        "axiom": "version_gt",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _VERSION_GT_PROBE,
        "rationale": "version_gt is the A-reference deep model of the changed "
                     "comparison; there is no consumed @ContractOnly axiom. The "
                     "probe CALLS the real callee the gold patch imports "
                     "(packaging.version.Version) and asserts "
                     "version_gt(a,b) == (Version(_vstr(a)) > Version(_vstr(b))) "
                     "on the issue's 0.6/0.10, the F2P 3.9/3.10/3.11, equal / "
                     "zero-pad / prefix / 10-vs-9 boundaries plus 200000 fuzz "
                     "release-number pairs (1..4 segments, 0..99). A disagreement "
                     "is AXIOM-UNSOUND. It also confirms CONTAINMENT: every "
                     "caller-reachable release number parses as a valid Version "
                     "(stays inside the A-reference's modeled valid-release "
                     "domain), so the modeled path is the executed path. Mirrors "
                     "axiom_check.py / G-AX, executed self-contained in the "
                     "instance image.",
    },
]
