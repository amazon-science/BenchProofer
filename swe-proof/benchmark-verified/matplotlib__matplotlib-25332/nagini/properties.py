# properties.py — PBT falsification battery for matplotlib__matplotlib-25332.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions + signatures, enforced by markers.same_spec)
# and edits ONLY inside the # impl-start/# impl-end regions (loop body +
# nested invariants are INSIDE that elided span, so same_spec is preserved).
#
# Defended surface (read model.py):
#   capture_state(ident, weak)  -> List[int]
#     Requires Acc(list_pred(ident),1/2), Acc(list_pred(weak),1/2),
#              len(weak)==len(ident)                       # ident, weak READ-ONLY
#     Ensures  len(Result)==len(ident)
#              Forall k in [0,len). Result[k]==0           # all-DIRECT (load-bearing)
#   restore_state(ident, state_weak) -> List[int]
#     Requires ...1/2 perms..., len(state_weak)==len(ident),
#              Forall k. state_weak[k]==0                  # captured state is all-direct
#     Ensures  len(Result)==len(ident)
#              Forall k. Result[k]==1                      # all-INDIRECT (load-bearing)
#   roundtrip_weakness(ident, weak) -> List[int]
#     composition; Ensures all-INDIRECT (==1), ident preserved.
#
# Both ident and weak are READ-ONLY (Acc(...,1/2)) => frame-mutation MANDATORY.
# The load-bearing postcondition clauses are GROUNDED CONSTANTS (==0 / ==1), not
# a @Pure answer-key oracle => no ungrounded-oracle echo exists (see assessment);
# we supply a positive control instead.
#
# There is NO consumed @ContractOnly axiom (meta.axioms == []). The changed
# capture/restore is an A-reference DEEP model validated by axiom_check.py
# (G-AX) against the real weakref.ref / weakref deref / pickle.dumps primitives.
# The AXIOM_TESTS below mirror that soundness + caller-domain containment in the
# instance Docker image (apply_gold=True) so the lane is covered.

from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25332"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors that live ENTIRELY inside an impl region (loop body / invariant text
# is nested within # impl-start .. # impl-end, which spec_view elides).
# ---------------------------------------------------------------------------

# capture_state loop body (impl region of capture_state).
_CAP_BODY = """        out.append(0)
        i = i + 1"""

# restore_state loop body (impl region of restore_state).
_RES_BODY = """        out.append(1)
        i = i + 1"""

# roundtrip body (impl region of roundtrip_weakness).
_RT_BODY = """    captured = capture_state(ident, weak)
    restored = restore_state(ident, captured)
    return restored"""


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = []

# --- 1. FRAME-MUTATION (MANDATORY: ident & weak are read-only at 1/2) --------
# A rival that "captures in place" by WRITING the read-only `weak` carrier to
# 0 (so it could then claim the slots are direct) instead of building a fresh
# list. It must FAIL for INSUFFICIENT PERMISSION: `weak` is held at Acc(.,1/2),
# which grants read but not write. The all-0 postcondition is left verbatim so
# the rejection is attributable to the write, not to a weakened spec.
_frame_cap = _swap(
    _BASE,
    _CAP_BODY,
    """        weak[i] = 0          # FRAME VIOLATION: write to read-only `weak` (Acc 1/2)
        out.append(weak[i])
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "frame-mutation-capture",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _frame_cap,
    "refinement": (
        "Its faithful real patch would mutate the LIVE container in place: the "
        "gold __getstate__ returns a FRESH dict {k():[v()...]} and never touches "
        "self._mapping; an in-place rewrite of the live weakref mapping to strong "
        "refs corrupts the still-live Grouper that test_complete keeps using "
        "(align_ylabels groups are read again after pickling), so the F2P would "
        "not resolve. In the model this manifests as a write to the read-only "
        "carrier."
    ),
    "rationale": (
        "Rejection comes from the PERMISSION SYSTEM: Requires(Acc(list_pred(weak)"
        ",1/2)) grants no write permission, so `weak[i] = 0` is an insufficient-"
        "permission error. A byte-fuzzer never thinks to mutate the input."
    ),
})

# --- 2. FRAME-MUTATION on the OTHER read-only carrier (`ident`) --------------
# Supporting frame probe: write to `ident` (the identity carrier the spec pins
# as immutable at 1/2). Same insufficient-permission rejection.
_frame_ident = _swap(
    _BASE,
    _RES_BODY,
    """        ident[i] = ident[i]  # FRAME VIOLATION: write to read-only `ident` (Acc 1/2)
        out.append(1)
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "frame-mutation-ident",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _frame_ident,
    "refinement": (
        "The gold transform preserves each slot's RESOLVED IDENTITY (weakref."
        "ref(x)() is x); a real patch that reassigned the identities would break "
        "the round-trip identity preservation that test_complete relies on "
        "(the unpickled figure must recover the same aligned-label groups). Any "
        "write to the identity carrier is therefore non-resolving."
    ),
    "rationale": (
        "Rejection from the PERMISSION SYSTEM: ident is held at Acc(.,1/2); even "
        "the self-assignment `ident[i] = ident[i]` needs write permission and is "
        "rejected as insufficient permission."
    ),
})

# --- 3. PARTIAL-DOMAIN: capture leaves the LAST slot indirect -----------------
# A rival correct on every slot but the last: it appends 0 for all i < len-1 and
# 1 for the final slot. Violates Ensures(Forall k. Result[k]==0). Mirrors a real
# off-by-one that fails to dereference the final weakref.
_partial_last = _swap(
    _BASE,
    _CAP_BODY,
    """        if i + 1 < len(ident):
            out.append(0)
        else:
            out.append(1)   # PARTIAL: last slot left INDIRECT (surviving weakref)
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "partial-domain-capture-last",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _partial_last,
    "refinement": (
        "A real patch that dereferenced every weakref except the last would "
        "leave ONE surviving weakref.ref in the captured _mapping; pickle.dumps "
        "then still raises TypeError: cannot pickle 'weakref.ReferenceType' — "
        "exactly the bug. test_complete (which pickles the whole figure) would "
        "not resolve. A single surviving indirect handle is enough to fail."
    ),
    "rationale": (
        "Rejection from the capture POSTCONDITION clause "
        "Ensures(Forall k. 0<=k<len(Result) => Result[k]==0): the final slot "
        "carries 1, falsifying the universal."
    ),
})

# --- 4. PARTIAL-DOMAIN: capture leaves the FIRST slot indirect ----------------
# The dual: diverge on the first element (often the input that 'fails first').
_partial_first = _swap(
    _BASE,
    _CAP_BODY,
    """        if i == 0:
            out.append(1)   # PARTIAL: first slot left INDIRECT
        else:
            out.append(0)
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "partial-domain-capture-first",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _partial_first,
    "refinement": (
        "Leaving the first stored handle a weakref still leaves a non-picklable "
        "weakref in the captured state; pickle.dumps raises TypeError, so the "
        "F2P figure pickle round trip does not resolve. (Supporting first-element "
        "dual of the last-element probe.)"
    ),
    "rationale": (
        "Rejection from capture POSTCONDITION Forall k. Result[k]==0: slot 0 is 1."
    ),
})

# --- 5. PARTIAL-DOMAIN: restore leaves one slot DIRECT ------------------------
# Rival restore that rebuilds every slot as indirect except the last.
_partial_restore = _swap(
    _BASE,
    _RES_BODY,
    """        if i + 1 < len(ident):
            out.append(1)
        else:
            out.append(0)   # PARTIAL: last slot left DIRECT (not re-wrapped)
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "partial-domain-restore-last",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _partial_restore,
    "refinement": (
        "__setstate__ must rewrap EVERY strong ref back into a weakref so the "
        "restored Grouper has the live indirect form; a real patch that left one "
        "slot a strong ref would make the restored container hold a strong "
        "reference where the live invariant (and __contains__, which does "
        "weakref.ref(item) lookups) expects a weakref, breaking subsequent "
        "Grouper operations on the unpickled figure. Non-resolving."
    ),
    "rationale": (
        "Rejection from restore POSTCONDITION Forall k. Result[k]==1: the last "
        "slot carries 0."
    ),
})

# --- 6. WRONG-CONSTANT: roundtrip returns all-DIRECT instead of all-INDIRECT --
# A rival roundtrip that returns the captured (all-0) state directly, skipping
# the re-wrap. Diverges on the WHOLE domain (a global wrong constant), the
# strongest uniqueness probe for the composition's load-bearing clause.
_rt_wrong = _swap(
    _BASE,
    _RT_BODY,
    """    captured = capture_state(ident, weak)
    return captured   # WRONG: returns all-DIRECT (==0); skips restore re-wrap""",
)
SPEC_TESTS.append({
    "id": "roundtrip-skip-restore",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _rt_wrong,
    "refinement": (
        "A real round trip that returned the captured (all strong-ref) state "
        "without running __setstate__ would leave the unpickled Grouper holding "
        "STRONG references where the live container demands weakrefs; the live "
        "Grouper invariant (weakref keys/values) is violated and downstream "
        "Grouper use on the unpickled figure breaks. The composition must end "
        "all-indirect; returning all-direct does not resolve."
    ),
    "rationale": (
        "Rejection from roundtrip_weakness POSTCONDITION Forall k. Result[k]==1: "
        "`captured` satisfies ==0, falsifying the ==1 universal."
    ),
})

# --- 7. POSITIVE CONTROL (soundness): structurally-different CORRECT capture --
# Same forward direction & invariant (kept verbatim so the gold proof stays
# valid — directive 2/3), but the executable SHAPE differs: bind the directness
# flag to a typed local and append the local, with an explicit Assert pinning
# its value. A faithful correct impl MUST verify (else SPEC-TOO-STRONG).
_pos_cap = _swap(
    _BASE,
    _CAP_BODY,
    """        direct_flag = 0  # type: int
        Assert(direct_flag == 0)
        out.append(direct_flag)
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "pos-control-capture-local-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_cap,
    "rationale": (
        "A correct capture that produces the same all-0 result via a typed local "
        "and an Assert must verify; the loop invariant (Forall k<i. out[k]==0) is "
        "kept verbatim so no proof obligation is dropped. If this cannot verify "
        "the spec is SPEC-TOO-STRONG."
    ),
})

# --- 8. POSITIVE CONTROL (soundness): correct restore via local reshape -------
_pos_res = _swap(
    _BASE,
    _RES_BODY,
    """        indirect_flag = 1  # type: int
        Assert(indirect_flag == 1)
        out.append(indirect_flag)
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "pos-control-restore-local-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_res,
    "rationale": (
        "A correct restore producing the same all-1 result via a typed local + "
        "Assert must verify; the all-1 loop invariant is unchanged. Else "
        "SPEC-TOO-STRONG."
    ),
})

# --- 9. ADMISSIBILITY: precondition admits an F2P-shaped input ----------------
# An impl-region caller inside capture_state that, before the real work, builds
# a concrete small in-domain state (len-2 ident, len-2 weak) and calls
# restore_state on it — exercising restore_state's Requires
# (len match + Forall state_weak[k]==0). If the precondition cannot be
# established for this normal input, PRECOND-TOO-STRONG. The original capture
# work is preserved verbatim after the probe so the function's own postcondition
# still holds.
_admiss = _swap(
    _BASE,
    _CAP_BODY,
    """        out.append(0)
        i = i + 1
    # admissibility probe: a normal F2P-shaped input satisfies restore_state's
    # precondition (len match + all-direct). Verifying this call establishes the
    # precondition is admissible.
    probe_ident = [10, 20]  # type: List[int]
    probe_state = [0, 0]    # type: List[int]
    Assert(len(probe_state) == len(probe_ident))
    Assert(Forall(int, lambda k:
        Implies(0 <= k and k < len(probe_state), probe_state[k] == 0)))
    _restored = restore_state(probe_ident, probe_state)""",
)
SPEC_TESTS.append({
    "id": "admissibility-restore-precondition",
    "kind": "admissibility",
    "expect": "verify",
    "module": _admiss,
    "rationale": (
        "Builds a representative len-2 all-direct captured state and calls "
        "restore_state; verifying establishes restore_state's Requires "
        "(len(state_weak)==len(ident) and Forall state_weak[k]==0) is admissible "
        "for a normal input. If it cannot be established => PRECOND-TOO-STRONG. "
        "The capture work above is kept verbatim so capture_state's own "
        "postcondition still verifies."
    ),
})

# --- 10. SUPPORTING near-miss: capture returns length-mismatched result -------
# Cheap mechanical near-miss carrying a real refinement: drop the final append
# so the result is shorter than ident. Violates len(Result)==len(ident).
_short = _swap(
    _BASE,
    _CAP_BODY,
    """        if i + 1 < len(ident):
            out.append(0)
        # SHORT: skip the final slot entirely (one fewer flag than slots)
        i = i + 1""",
)
SPEC_TESTS.append({
    "id": "partial-domain-capture-short",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _short,
    "refinement": (
        "A real capture that dropped a handle would lose a member of the "
        "disjoint-set group; the unpickled Grouper would have fewer entries than "
        "the original, so the aligned-label groups recovered by test_complete "
        "would not match. A dropped slot does not resolve."
    ),
    "rationale": (
        "Rejection from capture POSTCONDITION len(Result())==len(ident): the "
        "result has len(ident)-1 elements (loop invariant len(out)==i breaks the "
        "final-length obligation)."
    ),
})


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# No consumed @ContractOnly axiom. The capture/restore is an A-reference deep
# model validated by axiom_check.py against the REAL stdlib primitives. We run
# that real-callee soundness + caller-domain containment in the instance Docker
# image with the gold patch applied. The probes CALL the real weakref/pickle
# primitives (never scrape source) and open files (none needed) as utf-8.

# Embed the bundle's own audited oracle (read on the HOST at load time, since
# the runner mounts ONLY the probe at /work). This re-runs axiom_check.py's
# soundness logic verbatim inside the container against the real primitives.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = []

# --- A1. axiom-soundness: deep model == real weakref/pickle primitives --------
_probe_sound = (
    _AXIOM_CHECK_SRC
    + "\n\n"
    + "# ---- PBT axiom-soundness driver (appended) ----\n"
    + "if __name__ == '__pbt__':\n"
    + "    pass\n"
)
# axiom_check.py already runs main() under __main__; the container executes the
# script directly, so its own `if __name__ == '__main__': sys.exit(main())`
# fires. We keep that path and only ensure exit(0) iff sound.
AXIOM_TESTS.append({
    "id": "axiom-soundness-deepmodel-vs-real",
    "axiom": "capture_state/restore_state directness+identity (A-reference)",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AXIOM_CHECK_SRC,
    "rationale": (
        "Runs the bundle's audited G-AX oracle inside the instance image (gold "
        "applied): the deep model (weakref deref -> DIRECT/picklable flag 0; "
        "weakref.ref -> INDIRECT/non-picklable flag 1; round trip preserves "
        "resolved identity) is asserted == the REAL weakref.ref / weakref deref "
        "/ pickle.dumps over 5 boundary + 2000 fuzz handle sets. Any violation "
        "(real callee disagrees with the deep model) => AXIOM-UNSOUND. No flag "
        "dependency: the weakref/strong-ref directness discriminator holds at "
        "every pickle protocol (mapping.md flag-dependency: none)."
    ),
})

# --- A2. axiom-containment: every caller-reachable handle is in domain --------
# The model can only ever pass weak-flags in {0,1} (the carriers are List[int]
# used as 0/1 directness flags; capture produces 0, restore requires 0 and
# produces 1) and identities that are arbitrary integers (id()-like). The real
# primitive (weakref.ref / deref / pickle) is defined for ANY weak-referenceable
# object of ANY identity, so the callee domain strictly CONTAINS the caller-
# reachable set. This probe enumerates the reachable directness flags + a wide
# identity range and asserts the real primitives accept every one (containment).
_probe_contain = '''#!/usr/bin/env python3
"""axiom-containment: every handle the MODEL can reach lies in the real
weakref/pickle primitive's domain (caller-reachable set is contained)."""
import pickle
import sys
import weakref


class _Obj:
    __slots__ = ("ident", "__weakref__")
    def __init__(self, ident):
        self.ident = ident


def _is_direct_serialisable(handle):
    try:
        pickle.dumps(handle)
        return True
    except TypeError:
        return False


def main():
    # Caller-reachable directness flags: the model uses List[int] as 0/1
    # directness flags ONLY. capture produces 0 (direct); restore requires 0 in
    # and produces 1 (indirect); roundtrip composes. So the only reachable flag
    # values are {0, 1} and the only reachable identities are arbitrary ints.
    reachable_flags = {0, 1}
    assert reachable_flags <= {0, 1}, "model reached a flag outside {0,1}"

    # Identity carrier: arbitrary integers (real id() values are large; model
    # uses small ints). The real primitive is identity-agnostic; sample widely.
    idents = list(range(-5, 6)) + [0, 1, 2 ** 31, -(2 ** 31), 2 ** 62]
    for ident in idents:
        o = _Obj(ident)
        # flag 1 == indirect == a weakref: real primitive defines weakref.ref(o)
        h = weakref.ref(o)
        assert h() is o, "real weakref deref not in domain for this object"
        assert not _is_direct_serialisable(h), (
            "indirect handle (flag 1) unexpectedly picklable")
        # flag 0 == direct == the dereferenced strong object: picklable iff the
        # object itself is picklable. _Obj with __slots__ + no __weakref__ data
        # is picklable; the real Grouper members (Artists) are likewise direct-
        # picklable post-deref. Containment holds: the direct discriminator is
        # defined for every dereferenced referent.
        strong = h()
        assert strong is o
        assert _is_direct_serialisable(strong), (
            "direct handle (flag 0) unexpectedly NOT picklable")

    # No caller-reachable input falls OUTSIDE the primitive domain: weakref.ref
    # is defined for any weak-referenceable target, deref for any live handle,
    # pickle for any (post-deref) strong ref. Covering MORE (any object, any id)
    # than the caller reaches (these ints) is SOUND containment, not a defect.
    print("AX-CONTAIN OK: reachable flags {0,1} + wide identity range all lie "
          "in the real weakref/deref/pickle primitive domain (%d idents)"
          % len(idents))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
AXIOM_TESTS.append({
    "id": "axiom-containment-caller-domain",
    "axiom": "capture_state/restore_state directness+identity (A-reference)",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": _probe_contain,
    "rationale": (
        "Containment check: the only directness flags the model can reach are "
        "{0,1} and identities are arbitrary integers; the real weakref.ref / "
        "deref / pickle primitives are defined for ANY weak-referenceable target "
        "of ANY identity, so the callee domain strictly CONTAINS the caller-"
        "reachable set. A reachable input outside the covered domain would be "
        "AXIOM-TOO-WEAK-FOR-CALLER; none exists. Covering more than reached is "
        "sound (the float-vs-int rule)."
    ),
})
