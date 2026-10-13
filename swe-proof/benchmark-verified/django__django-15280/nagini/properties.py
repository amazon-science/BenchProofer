# properties.py — PBT falsification battery for django__django-15280.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant that shares the FROZEN spec verbatim
# (markers.same_spec) and edits ONLY inside the # impl-start / # impl-end region;
# the runner checks Nagini verify + same_spec. AXIOM_TESTS is empty: this bundle
# consumes no @ContractOnly axiom and has no A-reference deep model (meta.axioms
# == [], deep_model_references == []); the only callee fidelity (the kind-I
# FieldCacheMixin cache abstraction) is G-AX's axiom_check.py, not a PBT lane.
#
# DEFENDED SURFACE (what this spec pins):
#   link_children_to_parents(slot_full, slot_value, supplied) -> None
#   Load-bearing postcondition, for every child k in 0..len-1:
#       slot_value[k] == linked_parent(slot_full[k], Old(slot_value[k]), supplied[k])
#   with @Pure linked_parent(was_full, old, supplied) = old if was_full==1 else supplied.
#   So: a POPULATED slot (slot_full[k]==1) keeps Old(slot_value[k]); an EMPTY slot
#   (slot_full[k]==0) takes supplied[k]. The gold fix added exactly the guard
#   `if not is_cached(rel_obj)` around the slot write so a populated slot survives.
#
#   PERMISSIONS: slot_value is at FULL list_pred (legitimately mutated). slot_full
#   and supplied are at Acc(..., 1/2) — READ-ONLY (required AND ensured). The
#   oracle linked_parent is GROUNDED in the args (was_full, Old(slot_value[k]),
#   supplied[k]) — there is no opaque answer-key to echo, so the
#   ungrounded-oracle-echo class is N/A here (see 'assessment').

from pathlib import Path

INSTANCE = "django__django-15280"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region (verbatim from model.py). Every variant is produced by
# _swap on a substring that lies STRICTLY inside # impl-start / # impl-end, so
# same_spec is guaranteed (the spec view elides the whole impl region).
# ---------------------------------------------------------------------------

# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but CORRECT impl: descend the index from len-1 to 0
# instead of ascending 0..len-1, and phrase the guard as the equality test
# `slot_full[i] == 0` (empty) instead of `!= 1`. The per-child guarantee is
# independent across indices, so reverse order is still correct. The two loop
# invariants are RE-FRAMED for the descending walk (processed = [i, len); not-yet
# = [0, i)) so every gold proof obligation it still needs is kept (directive 2):
# we do NOT delete the prefix/suffix framing, we mirror it. If a faithful correct
# impl in a different shape cannot verify => SPEC-TOO-STRONG.
#
# PROOF HINTS (in-region only, same_spec preserved): the descending walk inspects
# slot_full[i] AFTER `i = i - 1`, so re-establishing the [i, len) "processed"
# invariant needs (a) the 0/1-occupancy fact restated as a loop invariant (the
# precondition is only known at entry; slot_full is read-only so it is trivially
# preserved) and (b) three Asserts that instantiate the quantified invariants /
# precondition at the single index i for Nagini's case-split. These live entirely
# inside the elided impl region (Asserts in the body, an Invariant in the loop
# head) — the frozen spec view is untouched. Without them Nagini cannot
# auto-discharge the trigger instantiation for the reverse loop: this was a
# PROOF-ENGINEERING gap, not SPEC-TOO-STRONG.
_POS_REVERSE = _swap(
    _BASE,
    """    i = 0
    while i < len(slot_value):
        # invariants-start
        Invariant(Acc(list_pred(slot_value)))
        Invariant(Acc(list_pred(slot_full), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(len(slot_value) == Old(len(slot_value)))
        Invariant(len(slot_value) == len(slot_full))
        Invariant(len(slot_value) == len(supplied))
        Invariant(0 <= i and i <= len(slot_value))
        # Children already processed satisfy the per-child guarantee.
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                    slot_value[k] == linked_parent(slot_full[k],
                                                   Old(slot_value[k]),
                                                   supplied[k])),
            [[slot_value[k]]])))
        # Children not yet processed still hold their original parent.
        Invariant(Forall(int, lambda k: (
            Implies(i <= k and k < len(slot_value),
                    slot_value[k] == Old(slot_value[k])),
            [[slot_value[k]]])))
        Invariant(MustTerminate(len(slot_value) - i + 1))
        # invariants-end
        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
    """    i = len(slot_value)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(slot_value)))
        Invariant(Acc(list_pred(slot_full), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(len(slot_value) == Old(len(slot_value)))
        Invariant(len(slot_value) == len(slot_full))
        Invariant(len(slot_value) == len(supplied))
        Invariant(0 <= i and i <= len(slot_value))
        # Children at indices [i, len) are already processed: guarantee holds.
        Invariant(Forall(int, lambda k: (
            Implies(i <= k and k < len(slot_value),
                    slot_value[k] == linked_parent(slot_full[k],
                                                   Old(slot_value[k]),
                                                   supplied[k])),
            [[slot_value[k]]])))
        # Children at indices [0, i) are not yet processed: original parent.
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                    slot_value[k] == Old(slot_value[k])),
            [[slot_value[k]]])))
        # slot_full is a 0/1 occupancy flag (carried from the precondition;
        # slot_full is read-only at 1/2, so this is trivially preserved). The
        # descending walk inspects slot_full[i] AFTER decrementing i, so it needs
        # the flag-domain fact in-loop to reason about the unwritten (==1) branch.
        # This is a PROOF hint (a loop invariant inside the elided impl region) —
        # same_spec is preserved; the frozen spec is untouched.
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < len(slot_full),
                    slot_full[k] == 0 or slot_full[k] == 1),
            [[slot_full[k]]])))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        i = i - 1
        # Index i was not-yet-processed at the top, so it still holds its original
        # parent (from the [0, i+1) not-yet invariant) and is 0/1-occupied. These
        # Asserts instantiate the quantified invariants/precondition at index i so
        # Nagini can do the case-split that re-establishes the [i, len) guarantee.
        Assert(slot_value[i] == Old(slot_value[i]))
        Assert(slot_full[i] == 0 or slot_full[i] == 1)
        if slot_full[i] == 0:
            slot_value[i] = supplied[i]
        # Now index i satisfies the per-child guarantee, extending [i+1, len).
        Assert(slot_value[i] == linked_parent(slot_full[i],
                                              Old(slot_value[i]),
                                              supplied[i]))""",
)


# === ADMISSIBILITY ========================================================
# A self-call confirming the precondition admits a normal F2P-shaped input: a
# small mixed collection (one already-populated slot, one empty slot — exactly
# the nested-prefetch scenario the F2P observes). We APPEND the caller inside the
# single existing impl region (after the loop, before # impl-end) so same_spec is
# preserved (a second top-level function with no contracts would otherwise leak
# into the spec view). We build the three parallel lists, establish the 0/1
# occupancy precondition, and self-call. If the Requires cannot be met for this
# legitimate input => PRECOND-TOO-STRONG. (Typed locals + len/element pins so
# list_pred, the len equalities, and the 0/1-occupancy Forall are establishable.)
_ADMIT = _swap(
    _BASE,
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1
    # impl-end""",
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1
    # An F2P-shaped admissibility witness: one populated slot, one empty slot.
    sf = [1, 0]  # type: List[int]
    sv = [7, -1]  # type: List[int]
    sup = [9, 5]  # type: List[int]
    Assert(len(sf) == len(sv))
    Assert(len(sup) == len(sv))
    # Each slot_full entry is 0 or 1 (the precondition's occupancy clause).
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(sf),
                                          sf[k] == 0 or sf[k] == 1),
                                  [[sf[k]]])))
    Assert(Acc(list_pred(sv)))
    Assert(Acc(list_pred(sf), 1 / 2))
    Assert(Acc(list_pred(sup), 1 / 2))
    # impl-end""",
)


# === FRAME-MUTATION (MANDATORY: slot_full / supplied are Acc(..., 1/2)) =====
# Rival that WRITES to the read-only input `supplied` to satisfy the postcondition.
# Idea: instead of writing slot_value, mutate supplied so that... — but supplied
# is at 1/2 permission, so ANY store to it is rejected for INSUFFICIENT PERMISSION,
# regardless of whether it would help the postcondition. We keep the gold guarded
# write intact (so the rejection is attributable solely to the added illegal store
# to a read-only input, not to a value mismatch). The gold invariants are kept.
# expect=reject, for insufficient permission on supplied (the 1/2 frame).
_FRAME_SUPPLIED = _swap(
    _BASE,
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        supplied[i] = slot_value[i]
        i = i + 1""",
)
# refinement: the real loop NEVER assigns to instances_dict[...] (the `supplied`
# source); a faithful patch that wrote back into the supplied-parent collection
# would corrupt the parent map shared across children and break the prefetch
# bookkeeping -> the F2P assertNumQueries(0) and the P2P prefetch tests would NOT
# pass. So a verifying frame-mutation rival is a true verify-not-resolve break.

# Second frame-mutation rival: write to slot_full (the other read-only 1/2 input),
# e.g. mark every processed slot as "full" to make the not-yet-processed invariant
# trivially follow. Rejected for insufficient permission on slot_full.
_FRAME_SLOTFULL = _swap(
    _BASE,
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        slot_full[i] = 1
        i = i + 1""",
)
# refinement: is_cached(rel_obj) reads _state.fields_cache membership; the real
# loop never forces a child's cache to "occupied" without storing a parent. A
# patch that flipped the occupancy flag without the matching parent store would
# leave is_cached True but the slot value wrong -> the F2P's
# `house.rooms.first().house.address` would read a stale/missing parent and the
# assertNumQueries(0) (and the deferred-field correctness) would fail.


# === PARTIAL-DOMAIN =======================================================
# Rival correct on most of the domain but diverging on the LAST element: skip the
# guarded write when i is the final index (i == len-1). On a single-element empty
# collection, or any collection whose last child has an empty slot needing the
# supplied parent, the last slot is left at its old value instead of `supplied`,
# violating the postcondition for k == len-1. expect=reject (postcondition Forall).
_PARTIAL_LAST = _swap(
    _BASE,
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
    """        if slot_full[i] != 1 and i != len(slot_value) - 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
)
# refinement: the real fix guards EVERY child by is_cached; a faithful patch that
# instead skipped linking the last prefetched row would leave that child's parent
# slot unpopulated, so accessing its parent fires a DB query -> the F2P
# assertNumQueries(0) fails (a query for the un-linked last child). The P2P
# reverse-FK/m2m prefetch tests that expect all children linked would also fail.

# Second partial-domain rival: invert the guard sense — write whenever the slot
# is ALREADY populated and skip empty slots (correct only on the all-populated
# sub-domain, wrong everywhere an empty slot exists). expect=reject.
_PARTIAL_INVERT = _swap(
    _BASE,
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
    """        if slot_full[i] == 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
)
# refinement: this is precisely the pre-patch bug's mirror — it OVERWRITES the
# populated (nested-prefetched, more-specific) parent and FAILS to link the empty
# slots. Both halves break the F2P: the nested-prefetched parent is clobbered AND
# the un-cached children are never linked -> queries fire, assertNumQueries fails.


# === CONTROL-FLOW-EFFECT (the prepatch bug, as the canonical uniqueness probe) =
# The unconditional write (drop the guard entirely): slot_value[i] = supplied[i]
# for EVERY child. This is exactly model_prepatch.py's body and the pre-patch
# Django code. It overwrites a populated slot, so on a child with slot_full==1 and
# supplied != Old(slot_value) the postcondition
#   slot_value[k] == linked_parent(1, Old(slot_value[k]), supplied[k]) == Old(slot_value[k])
# is violated (the value differs). expect=reject (postcondition / loop invariant).
_UNCONDITIONAL = _swap(
    _BASE,
    """        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1""",
    """        slot_value[i] = supplied[i]
        i = i + 1""",
)
# refinement: this IS the bug the gold patch fixes. The F2P
# test_nested_prefetch_is_not_overwritten_by_related_object FAILS pre-patch (the
# outer `only('name')` parent clobbers the nested `only('address')` parent, so
# `house.address` fires a query: assertNumQueries(0) -> 1 != 0). A verifying
# unconditional rival would be a catastrophic SPEC-TOO-WEAK (the prepatch passes).


SPEC_TESTS = [
    {
        "id": "pos-reverse-descending",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REVERSE,
        "rationale": "structurally-different CORRECT impl (descending walk, guard "
                     "phrased as slot_full[i]==0, invariants mirrored for [i,len) "
                     "processed). Per-child guarantee is index-independent, so it "
                     "must verify; if not => SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-mixed-collection",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMIT,
        "rationale": "self-call on an F2P-shaped mixed collection (one populated "
                     "slot, one empty) establishes the precondition (len equalities "
                     "+ 0/1 occupancy) and calls the function; if the Requires can't "
                     "be met for a normal input => PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutate-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_SUPPLIED,
        "refinement": "the real loop never writes back into instances_dict (the "
                      "supplied-parent source); a patch mutating the shared supplied "
                      "collection would corrupt cross-child parent bookkeeping so the "
                      "F2P assertNumQueries(0) and the reverse-FK/m2m P2P prefetch "
                      "tests would NOT pass.",
        "rationale": "supplied is Acc(list_pred(supplied), 1/2) (read-only, required "
                     "AND ensured); ANY store to supplied[i] is rejected for "
                     "INSUFFICIENT PERMISSION (permission system), independent of "
                     "the postcondition. Gold guarded write kept verbatim so the "
                     "rejection is attributable to the illegal write.",
    },
    {
        "id": "frame-mutate-slot_full",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_SLOTFULL,
        "refinement": "is_cached reads cache-key membership; the real loop never "
                      "forces occupancy without a matching parent store. A patch "
                      "flipping the flag without writing the right parent leaves "
                      "is_cached True but the parent wrong -> F2P "
                      "house.rooms.first().house.address reads stale/missing parent, "
                      "assertNumQueries(0) fails.",
        "rationale": "slot_full is Acc(list_pred(slot_full), 1/2) (read-only); the "
                     "store slot_full[i]=1 is rejected for INSUFFICIENT PERMISSION "
                     "(permission system). Gold guarded write kept verbatim.",
    },
    {
        "id": "partial-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_LAST,
        "refinement": "a faithful patch that skipped linking the last prefetched "
                      "child leaves that child's parent slot unpopulated, so accessing "
                      "its parent fires a DB query -> the F2P assertNumQueries(0) "
                      "fails and reverse-FK/m2m P2P prefetch tests (all children "
                      "linked) fail.",
        "rationale": "for k == len(slot_value)-1 with an empty slot, the impl leaves "
                     "slot_value[k] == Old(slot_value[k]) but the postcondition "
                     "demands linked_parent(0, Old, supplied[k]) == supplied[k]; the "
                     "Forall postcondition is violated on the last index.",
    },
    {
        "id": "partial-invert-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_INVERT,
        "refinement": "this writes the populated (nested-prefetched, more-specific) "
                      "parent and never links empty slots — both halves break the "
                      "F2P: the nested parent is clobbered AND uncached children are "
                      "never linked, so queries fire and assertNumQueries fails.",
        "rationale": "on an empty slot (slot_full[k]==0) the impl leaves the old "
                     "value, but the postcondition demands supplied[k]; on a populated "
                     "slot it writes supplied[k] but the postcondition demands "
                     "Old(slot_value[k]). Postcondition Forall violated.",
    },
    {
        "id": "uncond-overwrite-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNCONDITIONAL,
        "refinement": "this IS the pre-patch Django code (model_prepatch.py body): "
                      "the F2P test_nested_prefetch_is_not_overwritten_by_related_"
                      "object FAILS because the outer only('name') parent clobbers "
                      "the nested only('address') parent, so house.address fires a "
                      "query (1 != 0).",
        "rationale": "drops the occupancy guard -> on a populated slot with "
                     "supplied != Old(slot_value), slot_value[k] becomes supplied[k] "
                     "but linked_parent(1, Old, supplied) == Old(slot_value[k]); the "
                     "per-child postcondition / loop invariant is violated. This is "
                     "the discriminating bug the spec is built to sense (G-DIFF).",
    },
]

# No @ContractOnly axiom and no A-reference deep model in this bundle
# (meta.axioms == [], deep_model_references == []). The kind-I FieldCacheMixin
# cache abstraction's fidelity is validated by axiom_check.py / G-AX, which is a
# separate gate, not a PBT axiom lane. So there is nothing to probe here.
AXIOM_TESTS = []
