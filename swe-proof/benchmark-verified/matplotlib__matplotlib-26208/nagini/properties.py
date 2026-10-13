# properties.py — PBT manifest for matplotlib__matplotlib-26208. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes
# and stamps with RESULT. Spec cases are full model.py variants that share the
# frozen spec exactly (region-surgery: ONLY the per-function impl region is
# edited) and are checked by Nagini verify + markers.same_spec; axiom cases would
# be real-callee Docker probes (none here — the axioms region is empty).
#
# Defended surface (read adversarially from model.py):
#   Two builder functions, build_companion_sharing_horizontal /
#   build_companion_sharing_vertical, with IDENTICAL structure. Each:
#     Requires(Acc(source.descriptor, 1/2))           # READ-ONLY input (half perm)
#     Requires(source.descriptor is not None)
#     Ensures(Acc(source.descriptor, 1/2))            # returns the half perm
#     Ensures(source.descriptor is not None)          # source unchanged
#     Ensures(Acc(Result().descriptor))               # full perm on result field
#     Ensures(Result().descriptor is source.descriptor)   # <-- LOAD-BEARING: identity
#     Ensures(Result().descriptor is not None)
#   The load-bearing clause is `Result().descriptor is source.descriptor` — pure
#   reference identity, GROUNDED in the input (source.descriptor), not an opaque
#   @Pure answer-key. So there is no ungrounded-oracle to echo: the only way to
#   satisfy it is to actually copy the reference (see 'assessment' below). The
#   real attack surfaces are: (a) FRAME-MUTATION on the half-permission source
#   (MANDATORY), (b) the prepatch partial-domain miss (omit the copy), (c) a
#   value-double-mask that satisfies the weaker `is not None` clause with a FRESH
#   descriptor but breaks identity.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26208"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two per-function impl regions (byte-exact, each unique on _BASE because of
# the horizontal/vertical suffix). All edits stay strictly between
# # impl-start / # impl-end, so same_spec is GUARANTEED.
# ---------------------------------------------------------------------------
_IMPL_H = (
    "    companion_horizontal = CoordinateAxis()\n"
    "    companion_horizontal.descriptor = source_horizontal.descriptor\n"
    "    return companion_horizontal"
)
_IMPL_V = (
    "    companion_vertical = CoordinateAxis()\n"
    "    companion_vertical.descriptor = source_vertical.descriptor\n"
    "    return companion_vertical"
)


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally different but CORRECT.
#    Instead of the direct field-to-field copy, read the source descriptor into
#    a typed local first, then write that local onto the companion. Same
#    reference is propagated (identity preserved), only the executable shape
#    differs (an extra local binding). No framing assert is dropped — the proof
#    obligation is the same. If this fails to verify => SPEC-TOO-STRONG.
# ===========================================================================
_POS_H = (
    "    companion_horizontal = CoordinateAxis()\n"
    "    shared = source_horizontal.descriptor  # type: Optional[UnitDescriptor]\n"
    "    companion_horizontal.descriptor = shared\n"
    "    return companion_horizontal"
)
_POS_V = (
    "    companion_vertical = CoordinateAxis()\n"
    "    shared = source_vertical.descriptor  # type: Optional[UnitDescriptor]\n"
    "    companion_vertical.descriptor = shared\n"
    "    return companion_vertical"
)

_pos = _swap(_BASE, _IMPL_H, _POS_H)
_pos = _swap(_pos, _IMPL_V, _POS_V)


# ===========================================================================
# 2. ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input.
#    The F2P (test_twin_units) builds a source axis that HAS a unit descriptor
#    (ax1.plot of categorical data => xaxis.units is not None), then twins it.
#    Asserting the precondition fact `source.descriptor is not None` at the top
#    of the impl must succeed (it is exactly the Requires). If the assert can't
#    be established for the in-domain input => PRECOND-TOO-STRONG. Keeps the
#    correct copy so it still verifies the postcondition.
# ===========================================================================
_ADM_H = (
    "    Assert(source_horizontal.descriptor is not None)\n"
    "    companion_horizontal = CoordinateAxis()\n"
    "    companion_horizontal.descriptor = source_horizontal.descriptor\n"
    "    return companion_horizontal"
)
_ADM_V = (
    "    Assert(source_vertical.descriptor is not None)\n"
    "    companion_vertical = CoordinateAxis()\n"
    "    companion_vertical.descriptor = source_vertical.descriptor\n"
    "    return companion_vertical"
)

_adm = _swap(_BASE, _IMPL_H, _ADM_H)
_adm = _swap(_adm, _IMPL_V, _ADM_V)


# ===========================================================================
# 3. FRAME-MUTATION (uniqueness, MANDATORY) — write to the READ-ONLY source.
#    The source's descriptor is held at Acc(..., 1/2): half permission, a
#    read-only input. A rival that WRITES to source_horizontal.descriptor (here
#    overwriting it with the companion's fresh None, a classic "mutate the input
#    to make the postcondition fall out" move) needs FULL permission on
#    source.descriptor and therefore must be REJECTED for insufficient
#    permission. Every gold invariant is kept verbatim so the rejection is
#    attributable to the write, not to a broken postcondition. We mutate BOTH
#    sites so a single same-spec variant exercises the frame condition on each.
#    refinement: a faithful real patch that wrote `self.xaxis.units = <...>`
#    would CORRUPT the source frame's own units (the bug report is precisely
#    that ax1's state must NOT be disturbed by building the twin); such a patch
#    would not resolve test_twin_units (and would regress the data-limit
#    behaviour the issue is about).
# ===========================================================================
_FRAME_H = (
    "    companion_horizontal = CoordinateAxis()\n"
    "    source_horizontal.descriptor = companion_horizontal.descriptor\n"
    "    companion_horizontal.descriptor = source_horizontal.descriptor\n"
    "    return companion_horizontal"
)
_FRAME_V = (
    "    companion_vertical = CoordinateAxis()\n"
    "    source_vertical.descriptor = companion_vertical.descriptor\n"
    "    companion_vertical.descriptor = source_vertical.descriptor\n"
    "    return companion_vertical"
)

_frame = _swap(_BASE, _IMPL_H, _FRAME_H)
_frame = _swap(_frame, _IMPL_V, _FRAME_V)


# ===========================================================================
# 4. PREPATCH / PARTIAL-DOMAIN (uniqueness) — omit the copy entirely.
#    The companion is built fresh (descriptor is None) and returned without the
#    propagation. This is the base_commit behaviour (model_prepatch.py) and the
#    EXACT bug: it satisfies nothing of `Result().descriptor is source.descriptor`
#    and must be REJECTED on that postcondition. We omit at BOTH sites.
#    refinement: this is verbatim the pre-patch tree — twin.<axis>.units stays
#    None, so test_twin_units[x]/[y] FAIL on both `is not None` and
#    `is source.units`; G-AX classifies it 'prepatch'. A patch matching it
#    does not resolve.
# ===========================================================================
_PRE_H = (
    "    companion_horizontal = CoordinateAxis()\n"
    "    return companion_horizontal"
)
_PRE_V = (
    "    companion_vertical = CoordinateAxis()\n"
    "    return companion_vertical"
)

_pre = _swap(_BASE, _IMPL_H, _PRE_H)
_pre = _swap(_pre, _IMPL_V, _PRE_V)


# ===========================================================================
# 5. VALUE-DOUBLE-MASK / WRONG-DESCRIPTOR (uniqueness) — satisfy the weaker
#    `is not None` clause with a FRESH descriptor, breaking identity.
#    The postcondition has both `Result().descriptor is not None` (weak) and
#    `Result().descriptor is source.descriptor` (the load-bearing identity). A
#    rival that assigns a brand-new UnitDescriptor() to the companion makes the
#    result non-None (passing the weak clause) but it is NOT the source's object,
#    so the identity clause must REJECT it. This is the sharpest uniqueness probe:
#    it proves the spec is not satisfied by "any non-None descriptor".
#    refinement: a real patch that did `ax2.xaxis.units = <a new converter/
#    UnitData>` instead of `self.xaxis.units` would give the twin a DIFFERENT
#    descriptor object; test_twin_units asserts `ax2.<axis>.units is
#    ax1.<axis>.units` (object identity), so such a patch FAILS the F2P and does
#    not resolve.
# ===========================================================================
_MASK_H = (
    "    companion_horizontal = CoordinateAxis()\n"
    "    fresh = UnitDescriptor()\n"
    "    companion_horizontal.descriptor = fresh\n"
    "    return companion_horizontal"
)
_MASK_V = (
    "    companion_vertical = CoordinateAxis()\n"
    "    fresh = UnitDescriptor()\n"
    "    companion_vertical.descriptor = fresh\n"
    "    return companion_vertical"
)

_mask = _swap(_BASE, _IMPL_H, _MASK_H)
_mask = _swap(_mask, _IMPL_V, _MASK_V)


# ===========================================================================
# 6. SUPPORTING near-miss: identity at H, but a FRESH descriptor at V.
#    A single same-spec variant where ONLY the vertical site is corrupted to a
#    fresh descriptor while the horizontal site stays correct. This confirms the
#    two functions are independently pinned (the spec is not a single shared
#    obligation that one correct site could satisfy for both). Must be REJECTED
#    (on build_companion_sharing_vertical's identity clause).
#    refinement: matches a half-fix that only patched twinx and forgot twiny —
#    test_twin_units[y] would still FAIL; partial fix does not resolve.
# ===========================================================================
_half = _swap(_BASE, _IMPL_V, _MASK_V)  # horizontal stays the correct gold copy


SPEC_TESTS = [
    {
        "id": "pos-control-local-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos,
        "rationale": "structurally-different correct impl (read source.descriptor "
                     "into a typed local, then write it) propagates the SAME "
                     "reference; the identity postcondition still holds. If it "
                     "fails to verify => SPEC-TOO-STRONG. (Both sites reshaped.)",
    },
    {
        "id": "admiss-precond-usable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _adm,
        "rationale": "Assert(source.descriptor is not None) at the top of impl "
                     "succeeds because it is exactly the Requires; the F2P input "
                     "(a source axis that acquired a unit descriptor) is admitted. "
                     "If it cannot be established => PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutate-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame,
        "refinement": "a faithful real patch that wrote to self.<axis>.units would "
                      "CORRUPT the source frame's own units; the bug report is that "
                      "ax1 must be left undisturbed when twinning, so such a patch "
                      "regresses behaviour and does not resolve test_twin_units.",
        "rationale": "source.descriptor is held at Acc(...,1/2) (read-only); a WRITE "
                     "to it needs FULL permission, so the variant must be rejected "
                     "for INSUFFICIENT PERMISSION (the permission system, not a "
                     "postcondition). Gold invariants kept verbatim => rejection is "
                     "attributable to the write.",
    },
    {
        "id": "prepatch-omit-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pre,
        "refinement": "verbatim the base_commit tree: twin.<axis>.units stays None, "
                      "so test_twin_units[x]/[y] FAIL on both `is not None` and "
                      "`is source.units` (G-AX 'prepatch'). Does not resolve.",
        "rationale": "the fresh companion keeps descriptor is None, violating "
                     "Ensures(Result().descriptor is source.descriptor) and "
                     "Ensures(Result().descriptor is not None). Rejection from the "
                     "identity postcondition clause.",
    },
    {
        "id": "wrong-fresh-descriptor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mask,
        "refinement": "a real patch assigning a NEW descriptor (e.g. a fresh "
                      "UnitData/converter) instead of self.<axis>.units gives the "
                      "twin a different object; test_twin_units asserts object "
                      "IDENTITY (ax2.units is ax1.units), so it FAILS and does not "
                      "resolve.",
        "rationale": "a fresh UnitDescriptor() makes Result().descriptor non-None "
                     "(satisfying the WEAK clause) but it is not source.descriptor, "
                     "so the load-bearing identity clause "
                     "Ensures(Result().descriptor is source.descriptor) rejects it. "
                     "Proves the spec is not satisfied by 'any non-None descriptor'.",
    },
    {
        "id": "half-fix-vertical-only-broken",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _half,
        "refinement": "matches a half-fix that patched twinx but not twiny: "
                      "test_twin_units[y] still FAILS. Partial fix does not resolve.",
        "rationale": "horizontal site is the correct gold copy (verifies) but the "
                     "vertical site returns a fresh descriptor, so "
                     "build_companion_sharing_vertical's identity postcondition "
                     "rejects the variant. Confirms the two sites are independently "
                     "pinned (not one shared obligation).",
    },
]


# No @ContractOnly axioms (meta.axioms == []; the axioms region is empty). The
# single deep-model A-reference (descriptor propagation == real twinx/twiny) is
# validated out-of-band by axiom_check.py (G-AX) which runs the REAL builders in
# Docker; there is no consumed-axiom obligation for the PBT axiom lane to probe.
AXIOM_TESTS = []
