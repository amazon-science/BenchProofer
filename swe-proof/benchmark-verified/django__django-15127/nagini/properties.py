# properties.py — PBT falsification battery for django__django-15127. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   derive_tags_for_setting(setting: int, override: Tags, defaults: Tags,
#                           current: Tags) -> Tags
#     Requires(Acc(override.a,1/2) and Acc(override.b,1/2) and Acc(override.c,1/2))
#     Requires(Acc(defaults.a,1/2) and Acc(defaults.b,1/2) and Acc(defaults.c,1/2))
#     Requires(Acc(current.a,1/2)  and Acc(current.b,1/2)  and Acc(current.c,1/2))
#     # all three inputs are HALF-permission => READ-ONLY value carriers
#     Ensures(<same 1/2 perms on all three inputs>)      # framing: untouched
#     Ensures(Acc(Result().a) and Acc(Result().b) and Acc(Result().c))  # fresh, full
#     Ensures(Result() is not None)
#     Ensures(Implies(setting == setting_message_tags(),
#                     Result().a is merge_slot(defaults.a, override.a)))   # slot a
#     Ensures(Implies(setting == setting_message_tags(),
#                     Result().b is merge_slot(defaults.b, override.b)))   # slot b
#     Ensures(Implies(setting == setting_message_tags(),
#                     Result().c is merge_slot(defaults.c, override.c)))   # slot c
#     Ensures(Implies(setting == setting_message_tags() and slot_present(override.c),
#                     read_slot(Result().c) == read_slot(override.c)))     # the F2P read
#     Ensures(Implies(setting != setting_message_tags(),
#                     Result().a is current.a and Result().b is current.b
#                     and Result().c is current.c))                        # else branch
#   merge_slot(d, o) is a GROUNDED @Pure helper, fully unfolded as
#     (o if o is not None else d) — a function of the args, NOT an opaque
#     answer-key. read_slot/slot_present/setting_message_tags/empty_tag likewise.
#   There is NO @ContractOnly axiom; the only callee distance is the unchanged
#   Python dict merge {**defaults, **override} composed by get_level_tags(),
#   modelled DEEPLY by merge_slot and validated == real Python by axiom_check.py
#   (G-AX, an A-reference). The axiom lane below re-runs that A-reference check.
#
# What the spec defends (the load-bearing facts):
#   * Under the message-tags identifier, the result equals the override merged
#     onto the defaults, pinned PER SLOT with `is` identity (override wins where
#     present, else the default carries). This closes all three merge classes:
#       - slot a: a built-in level the override re-tags -> override token;
#       - slot b: a built-in level the override omits   -> default survives;
#       - slot c: a custom level only the override has   -> present with override
#         token (so read_slot(Result().c) reads the override tag, NOT empty).
#     Slot c is the EXACT F2P-discriminating case (custom level 12: 'custom'):
#     pre-patch it reads '' because LEVEL_TAGS is never re-derived; post-patch it
#     reads 'custom'.
#   * Under any OTHER identifier, the result is the in-force mapping unchanged.
#   * Permission: all three inputs are held at HALF Acc (read-only value
#     carriers). A faithful impl allocates a FRESH result and never writes an
#     input, so a rival that WRITES an input to construct the merge in place
#     fails for INSUFFICIENT PERMISSION (the frame-mutation probe below).
#
# Note on the @Pure helpers (ungrounded-oracle-echo class): merge_slot is
# GROUNDED — it is a total pure function of (defaults.X, override.X) the verifier
# fully unfolds; there is no opaque answer-key value to echo without doing the
# work. The honest cheapest impl IS `return Tags(merge_slot(d.a,o.a), ...)` — the
# gold impl itself — so the "wrong echo verifies" attack has no target here (a
# slot pinned `Result().X is merge_slot(defaults.X, override.X)` can only be met
# by producing that exact value). The uniqueness attacks therefore hit the merge
# DIRECTION (default-wins), a DROPPED slot (partial-domain on the custom level),
# the STALE no-derivation branch, and the WRONG-BRANCH (apply the merge under the
# non-message-tags identifier). See `assessment`.
from pathlib import Path

INSTANCE = "django__django-15127"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    # Under any other identifier the result equals the in-force mapping: the
    # returned record holds the same level-for-level slot values as ``current``
    # (observationally the same mapping).
    return Tags(current.a, current.b, current.c)
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-control-reorder: handle the NON-message-tags branch FIRST (early return the
# in-force mapping), then fall through to the merge. This reverses the branch
# order of the gold impl. Behaviourally identical: the merge branch still returns
# Tags(merge_slot(...) per slot) and the else branch still returns
# Tags(current.*). No loop / no fold, no new lemma needed (pilot pitfalls #2/#3
# avoided). If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
_POS_REORDER = """    # impl-start
    if setting != setting_message_tags():
        return Tags(current.a, current.b, current.c)
    return Tags(merge_slot(defaults.a, override.a),
                merge_slot(defaults.b, override.b),
                merge_slot(defaults.c, override.c))
    # impl-end"""

# pos-control-inline: a local-variable reshape — compute each merged slot into a
# named local first (inlining merge_slot's grounded choice is NOT needed; we keep
# the merge_slot calls so the per-slot postcondition `Result().X is
# merge_slot(defaults.X, override.X)` is met by identity), then build the result.
# Same values, different statement shape. Must verify (else SPEC-TOO-STRONG).
_POS_INLINE = """    # impl-start
    if setting == setting_message_tags():
        ma = merge_slot(defaults.a, override.a)  # type: Optional[int]
        mb = merge_slot(defaults.b, override.b)  # type: Optional[int]
        mc = merge_slot(defaults.c, override.c)  # type: Optional[int]
        return Tags(ma, mb, mc)
    ca = current.a  # type: Optional[int]
    cb = current.b  # type: Optional[int]
    cc = current.c  # type: Optional[int]
    return Tags(ca, cb, cc)
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller function: a
# new module-level def changes the projected spec view and breaks same_spec.
# Instead we inject the admissibility witness INSIDE the impl region (elided from
# the spec view): construct concrete F2P-shaped Tags records (a re-tagged
# built-in, an omitted built-in, a custom level) and SELF-CALL
# derive_tags_for_setting on them under the message-tags identifier. The
# self-call type-checks only if the Requires (Acc(...,1/2) on each input's three
# slots) is establishable for these freshly-built records — the Tags constructor
# grants full Acc, which subsumes the 1/2 the call needs. We Assert the
# discriminating read clause on the returned mapping (the custom level reads the
# override token). The real impl then runs unchanged. If the precondition could
# not be established for this legitimate input the self-call would fail =>
# PRECOND-TOO-STRONG.
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    # NOTE (termination): this witness deliberately does NOT self-call
    # derive_tags_for_setting. The spec now carries Requires(MustTerminate(6)),
    # and an obligation level is a fixed ordinal per method, so a SELF-call can
    # never sit at a strictly lower level than its caller -- the recursive form
    # of this witness is unprovable, and in fact diverges (it was unconditional
    # with no base case: see the uniq-diverging-self-call reject case below,
    # which retains that exact shape and pins that the spec now rejects it).
    # The admissibility property is defended DIRECTLY instead: we build the same
    # F2P-shaped records and assert that each precondition conjunct
    # (Acc(...,1/2) on every slot) IS establishable for them, plus the
    # discriminating read. If the precondition could not be established for this
    # legitimate input these asserts fail => PRECOND-TOO-STRONG.
    adm_override = Tags(7, None, 12)   # re-tag built-in a; omit b; custom level c
    adm_defaults = Tags(3, 5, None)    # built-in defaults; no custom level
    adm_current = Tags(3, 5, None)     # the stale in-force mapping
    # the three Requires conjuncts hold for these freshly-built records (the
    # Tags constructor grants full Acc, which subsumes the 1/2 the call needs):
    Assert(Acc(adm_override.a, 1 / 2) and Acc(adm_override.b, 1 / 2) and Acc(adm_override.c, 1 / 2))
    Assert(Acc(adm_defaults.a, 1 / 2) and Acc(adm_defaults.b, 1 / 2) and Acc(adm_defaults.c, 1 / 2))
    Assert(Acc(adm_current.a, 1 / 2) and Acc(adm_current.b, 1 / 2) and Acc(adm_current.c, 1 / 2))
    # the discriminating F2P read holds on the derived mapping: the custom level
    # reads the override token (12), not the empty tag.
    Assert(read_slot(merge_slot(adm_defaults.c, adm_override.c)) == read_slot(adm_override.c))
    Assert(read_slot(merge_slot(adm_defaults.c, adm_override.c)) != empty_tag())
    Assert(merge_slot(adm_defaults.a, adm_override.a) is adm_override.a)
    Assert(merge_slot(adm_defaults.b, adm_override.b) is adm_defaults.b)
    # --- end admissibility witness; the real impl follows unchanged ---
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    return Tags(current.a, current.b, current.c)
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness; MANDATORY — the inputs are Acc(...,1/2) read-only).
# A rival that WRITES an input to construct the merge in place must be REJECTED
# for INSUFFICIENT PERMISSION. The gold postcondition (incl. the framing
# Ensures(Acc(input.slot,1/2))) is kept verbatim, so the rejection is
# attributable to the write, not a spec change.
# ===========================================================================

# uniq-frame-mutate-defaults: in the message-tags branch, overwrite the
# `defaults` record's slots with the merged values and RETURN `defaults` itself
# (build the merge "in place"). Writing defaults.a/.b/.c needs FULL Acc, but only
# 1/2 is held => insufficient-permission reject.
_UNIQ_FRAME_MUTATE = """    # impl-start
    if setting == setting_message_tags():
        defaults.a = merge_slot(defaults.a, override.a)
        defaults.b = merge_slot(defaults.b, override.b)
        defaults.c = merge_slot(defaults.c, override.c)
        return defaults
    return Tags(current.a, current.b, current.c)
    # impl-end"""

# uniq-frame-mutate-override: a second frame-mutation shape — overwrite the
# `override` record so its slots already hold the merged values, then return it.
# Same insufficient-permission reject (override slots are held at 1/2).
_UNIQ_FRAME_MUTATE_OV = """    # impl-start
    if setting == setting_message_tags():
        override.a = merge_slot(defaults.a, override.a)
        override.b = merge_slot(defaults.b, override.b)
        override.c = merge_slot(defaults.c, override.c)
        return override
    return Tags(current.a, current.b, current.c)
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain / wrong-merge — rivals that share the spec exactly
# and change ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-stale-no-derivation: THE PRE-PATCH BUG (== model_prepatch.py). Never
# re-derive — return the in-force `current` mapping regardless of the identifier.
# Rejected by the per-slot merge postcondition under the message-tags identifier
# (Result().a is merge_slot(...) etc.), which `current` does not satisfy.
_UNIQ_STALE = """    # impl-start
    return Tags(current.a, current.b, current.c)
    # impl-end"""

# uniq-drop-custom-slot: partial-domain on the EXACT F2P-discriminating level.
# Slots a and b merge correctly, but slot c is taken from `defaults` (None for a
# custom level the defaults never had) instead of the merge — i.e. the custom
# level is dropped. Rejected by Ensures(Result().c is merge_slot(defaults.c,
# override.c)) (and the read clause: read_slot(Result().c) would be the empty
# tag, not the override token).
_UNIQ_DROP_CUSTOM = """    # impl-start
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    defaults.c)
    return Tags(current.a, current.b, current.c)
    # impl-end"""

# uniq-default-wins: the merge DIRECTION inverted on every slot — the default
# wins where present, else the override (i.e. {**override, **defaults}, the wrong
# dict-merge order). Rejected by the per-slot pin (Result().X is
# merge_slot(defaults.X, override.X), which is override-wins).
_UNIQ_DEFAULT_WINS = """    # impl-start
    if setting == setting_message_tags():
        return Tags(merge_slot(override.a, defaults.a),
                    merge_slot(override.b, defaults.b),
                    merge_slot(override.c, defaults.c))
    return Tags(current.a, current.b, current.c)
    # impl-end"""

# uniq-wrong-branch: apply the merge under the WRONG guard — derive on a
# NON-message-tags identifier and leave the mapping stale on the message-tags
# identifier (the guard is inverted). Rejected on BOTH sides: under the
# message-tags identifier the result is `current` (fails the per-slot merge pin),
# and under another identifier the result is the merge (fails Result().X is
# current.X).
_UNIQ_WRONG_BRANCH = """    # impl-start
    if setting != setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    return Tags(current.a, current.b, current.c)
    # impl-end"""

# uniq-empty-custom: supporting near-miss — slots a and b merge correctly, but
# slot c is forced to None (empty tag) under the message-tags identifier. This is
# the precise pre-patch read behaviour at the custom level (reads '' not
# 'custom'). Rejected by Result().c is merge_slot(defaults.c, override.c) and the
# read clause.
_UNIQ_EMPTY_CUSTOM = """    # impl-start
    if setting == setting_message_tags():
        empty = None  # type: Optional[int]
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    empty)
    return Tags(current.a, current.b, current.c)
    # impl-end"""


# ===========================================================================
# TERMINATION (uniqueness; enabled by Requires(MustTerminate(6))). Before the
# obligation landed the spec demanded NOTHING of termination, so a rival that
# never reaches its return satisfied every Ensures VACUOUSLY and VERIFIED. These
# two rivals are exactly that class, and the obligation is what rejects them.
# ===========================================================================

# uniq-diverging-self-call: the ORIGINAL shape of the admissibility witness --
# an UNCONDITIONAL self-call with NO base case, evaluated before any branch.
# Under plain Python this recurses until RecursionError (verified empirically);
# it never returns, so it is a WRONG implementation. The old (obligation-free)
# spec accepted it. Now MustTerminate(6) rejects it: a self-call cannot sit at a
# strictly lower obligation level than its caller.
_UNIQ_DIVERGING_SELF_CALL = """    # impl-start
    adm_override = Tags(7, None, 12)
    adm_defaults = Tags(3, 5, None)
    adm_current = Tags(3, 5, None)
    adm = derive_tags_for_setting(setting_message_tags(),
                                  adm_override, adm_defaults, adm_current)
    Assert(read_slot(adm.c) == read_slot(adm_override.c))
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    return Tags(current.a, current.b, current.c)
    # impl-end"""

# uniq-diverging-spin-loop: an unbounded counting loop ahead of the return. Its
# invariant is TRUE but carries no MustTerminate measure, and none exists: the
# counter increases without bound and the guard never falsifies. Postconditions
# hold vacuously (the return is unreachable), so the obligation-free spec
# verified it. MustTerminate(6) rejects it -- the loop cannot discharge the
# caller's obligation.
_UNIQ_DIVERGING_SPIN = """    # impl-start
    spin = 0
    while spin >= 0:
        Invariant(spin >= 0)
        spin = spin + 1
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    return Tags(current.a, current.b, current.c)
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "structurally-different CORRECT impl: the NON-message-tags "
                     "branch is handled first (early return Tags(current.*)), then "
                     "the merge branch falls through. Reverses the gold branch order "
                     "but is behaviourally identical on both arms. No loop / no fold, "
                     "so no new lemma is needed (pilot pitfalls #2/#3 avoided). If a "
                     "faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_INLINE),
        "rationale": "local-variable reshape: compute each merged / current slot "
                     "into a typed local before constructing the result, keeping the "
                     "merge_slot calls so the per-slot `Result().X is "
                     "merge_slot(defaults.X, override.X)` pin is met by identity. Same "
                     "values, different statement shape. If it cannot verify => "
                     "SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds concrete "
                     "F2P-shaped Tags records (a re-tagged built-in, an omitted "
                     "built-in, a custom level) and SELF-CALLS "
                     "derive_tags_for_setting on them under the message-tags "
                     "identifier. The self-call type-checks only if the Requires "
                     "(Acc(...,1/2) on each input slot) is establishable for these "
                     "freshly-built records (the Tags constructor grants full Acc, "
                     "which subsumes the 1/2 the call needs). The Asserts confirm the "
                     "discriminating read clause holds on the returned mapping. If the "
                     "precondition could not be established for this legitimate input "
                     "the self-call fails => PRECOND-TOO-STRONG.",
    },

    # ---- termination (must reject; enabled by Requires(MustTerminate(6))) ----
    {
        "id": "uniq-diverging-self-call",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DIVERGING_SELF_CALL),
        "refinement": "an unconditional self-call with no base case corresponds to "
                      "a setting_changed receiver that re-enters the very "
                      "re-derivation it is performing (e.g. the receiver assigns a "
                      "watched setting, re-firing setting_changed, with no guard to "
                      "break the cycle). Django would recurse until RecursionError: "
                      "base.LEVEL_TAGS is never assigned, every message render "
                      "raises, and test_override_settings_level_tags does not merely "
                      "fail an assertion -- it never completes. A faithful patch of "
                      "this shape does NOT resolve; it HANGS.",
        "rationale": "DIVERGES: verified empirically under plain Python that this "
                     "recurses to RecursionError (unconditional self-call, no base "
                     "case, evaluated before any branch), so it never reaches a "
                     "return and is a wrong implementation. This case exists because "
                     "the obligation-free spec ACCEPTED it -- the postconditions were "
                     "claimed only of runs that reach the return, so they held "
                     "vacuously. Requires(MustTerminate(6)) now rejects it with "
                     "'Obligation leak check failed. Callee derive_tags_for_setting "
                     "might not take all unsatisfied obligations from the caller': an "
                     "obligation level is a fixed ordinal per method, so a self-call "
                     "can never be at a strictly lower level than its caller. This is "
                     "the verify-but-not-resolve hole the termination obligation "
                     "closes, pinned as a test.",
    },
    {
        "id": "uniq-diverging-spin-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DIVERGING_SPIN),
        "refinement": "an unbounded loop ahead of the assignment corresponds to a "
                      "receiver that spins (e.g. waits on a condition that never "
                      "becomes true) before re-deriving LEVEL_TAGS. base.LEVEL_TAGS "
                      "is never re-derived and the request never returns, so the F2P "
                      "test hangs rather than fails. Does NOT resolve.",
        "rationale": "DIVERGES: `while spin >= 0` with `spin = spin + 1` has a guard "
                     "that is never falsified and no decreasing measure exists, so "
                     "the return is unreachable and every Ensures holds vacuously. "
                     "The invariant `spin >= 0` is true but carries NO "
                     "MustTerminate(e) -- and none can be written, since nothing "
                     "decreases. Rejected under the obligation with 'Obligation leak "
                     "check failed. Loop might not take all unsatisfied obligations "
                     "from the context.' This is the control that demonstrates the "
                     "obligation is load-bearing on loop shapes, not only on calls.",
    },

    # ---- frame-mutation (must reject for INSUFFICIENT PERMISSION) ----
    {
        "id": "uniq-frame-mutate-defaults",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FRAME_MUTATE),
        "refinement": "writing the merged values back into the `defaults` record "
                      "and returning it corresponds to a patch that mutated the "
                      "shared module constant constants.DEFAULT_TAGS in place (rather "
                      "than building a fresh {**DEFAULT_TAGS, **MESSAGE_TAGS} dict). "
                      "That would permanently corrupt the global default family for "
                      "all subsequent reads and processes — DEFAULT_TAGS is read by "
                      "every later get_level_tags() call and by other tests; the "
                      "P2P/F2P suite (and Django's own message rendering) would see "
                      "the mutated defaults. A faithful in-place-mutation patch does "
                      "NOT resolve. (The gold patch returns a fresh dict and never "
                      "touches DEFAULT_TAGS.)",
        "rationale": "rejected for INSUFFICIENT PERMISSION: defaults.a/.b/.c are held "
                      "at Acc(defaults.X, 1/2) (read-only), but an assignment "
                      "`defaults.X = ...` requires FULL Acc. The frozen pre/post "
                      "framing (Acc(defaults.X,1/2) in both Requires and Ensures) is "
                      "kept verbatim, so the rejection is attributable to the write, "
                      "not a spec change. This is the project's #1 weakness class — a "
                      "byte-fuzzer never mutates a read-only input.",
    },
    {
        "id": "uniq-frame-mutate-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FRAME_MUTATE_OV),
        "refinement": "overwriting the `override` record's slots corresponds to a "
                      "patch that mutated settings.MESSAGE_TAGS (the user's override "
                      "dict) in place before returning it. That corrupts the user's "
                      "configured setting (and the @override_settings fixture's "
                      "snapshot it must restore on teardown), so subsequent tests see "
                      "a polluted MESSAGE_TAGS — a faithful patch that mutated the "
                      "override input does NOT resolve. Supporting frame-mutation "
                      "shape on the second read-only input.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: override.a/.b/.c are held "
                      "at Acc(override.X, 1/2); `override.X = ...` requires FULL Acc. "
                      "Framing Ensures(Acc(override.X,1/2)) is kept verbatim.",
    },

    # ---- uniqueness / partial-domain / wrong-merge (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-stale-no-derivation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_STALE),
        "refinement": "this IS the pre-patch behaviour that model_prepatch.py "
                      "reproduces and G-DIFF flags: no setting_changed receiver runs, "
                      "so base.LEVEL_TAGS is never re-derived and the in-force (stale) "
                      "mapping is returned regardless of which setting changed. The "
                      "sole F2P test_override_settings_level_tags sets "
                      "@override_settings(MESSAGE_TAGS={... 12:'custom' ...}) and "
                      "asserts base.LEVEL_TAGS == message_tags; with no re-derivation "
                      "base.LEVEL_TAGS keeps the defaults-only mapping and the custom "
                      "level reads '' — the assertion fails. Its faithful real patch "
                      "(the un-patched apps.py) is exactly what does NOT resolve.",
        "rationale": "rejected by the per-slot merge postcondition under the "
                     "message-tags identifier: Ensures(Result().a is "
                     "merge_slot(defaults.a, override.a)) (and b, c). Returning "
                     "Tags(current.*) cannot be proven equal to the merge of "
                     "defaults/override (current is an unrelated record).",
    },
    {
        "id": "uniq-drop-custom-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_CUSTOM),
        "refinement": "merging slots a and b but taking slot c from `defaults` "
                      "(rather than the override) corresponds to a patch whose "
                      "re-derivation dropped the override's custom levels — e.g. "
                      "`{**MESSAGE_TAGS, **DEFAULT_TAGS}` keys filtered to the "
                      "built-in levels, or a merge that only updated levels already "
                      "in DEFAULT_TAGS. The F2P custom level 12 ('custom') is exactly "
                      "the dropped slot: base.LEVEL_TAGS would lack key 12 and "
                      ".get(12,'') would return '' not 'custom', so "
                      "test_override_settings_level_tags fails. Does NOT resolve.",
        "rationale": "rejected by Ensures(Result().c is merge_slot(defaults.c, "
                     "override.c)): for a custom level, defaults.c is None and "
                     "override.c is the token, so merge_slot returns the token; "
                     "returning defaults.c (None) violates the pin. Also fails the "
                     "read clause read_slot(Result().c) == read_slot(override.c).",
    },
    {
        "id": "uniq-default-wins",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DEFAULT_WINS),
        "refinement": "swapping the merge_slot argument order (default wins where "
                      "present, else override) corresponds to the WRONG dict-merge "
                      "order `{**MESSAGE_TAGS, **DEFAULT_TAGS}` instead of "
                      "`{**DEFAULT_TAGS, **MESSAGE_TAGS}`. The F2P re-tags built-in "
                      "levels (e.g. ERROR -> 'bad'); with the default winning, the "
                      "built-in default tag survives and base.LEVEL_TAGS != "
                      "message_tags, so test_override_settings_level_tags fails. "
                      "Does NOT resolve.",
        "rationale": "rejected by the per-slot pin Ensures(Result().X is "
                     "merge_slot(defaults.X, override.X)) (override-wins). The rival "
                     "computes merge_slot(override.X, defaults.X) (default-wins); on a "
                     "re-tagged built-in slot (both present) these differ, so the "
                     "verifier cannot prove the identity.",
    },
    {
        "id": "uniq-wrong-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_WRONG_BRANCH),
        "refinement": "inverting the guard (derive on a NON-MESSAGE_TAGS change, "
                      "leave the mapping stale when MESSAGE_TAGS changes) corresponds "
                      "to a receiver guarded on `setting != 'MESSAGE_TAGS'`. On the "
                      "F2P's MESSAGE_TAGS change it would NOT re-derive base.LEVEL_TAGS "
                      "(custom level reads ''), failing test_override_settings_level_"
                      "tags; and it would needlessly re-derive on unrelated setting "
                      "changes. Does NOT resolve.",
        "rationale": "rejected on BOTH postcondition arms: under the message-tags "
                     "identifier the rival returns Tags(current.*), failing "
                     "Result().X is merge_slot(defaults.X, override.X); under another "
                     "identifier it returns the merge, failing Result().X is "
                     "current.X.",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-empty-custom",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_EMPTY_CUSTOM),
        "refinement": "forcing slot c to None (absent) under the message-tags "
                      "identifier is the precise pre-patch read at the custom level: "
                      "base.LEVEL_TAGS lacks key 12 so .get(12,'') returns '' rather "
                      "than 'custom'. test_override_settings_level_tags asserts "
                      "base.LEVEL_TAGS == message_tags (which contains 12:'custom'); "
                      "the missing custom key fails the assertion. Supporting "
                      "near-miss for the dropped-custom-slot attack.",
        "rationale": "rejected by Ensures(Result().c is merge_slot(defaults.c, "
                     "override.c)): when override.c is a present token merge_slot "
                     "returns that token, so the None slot cannot match; and the read "
                     "clause read_slot(Result().c) == read_slot(override.c) fails "
                     "(empty tag != override token).",
    },
]


# ===========================================================================
# AXIOM LANE — there is NO @ContractOnly axiom in this bundle. The only callee
# distance is the unchanged Python dict merge {**defaults, **override} composed
# by get_level_tags(), modelled DEEPLY by the @Pure merge_slot (an A-reference)
# and the read .get(level,'') modelled by read_slot. These probes re-run the
# bundle's own axiom_check.py logic against the real Python primitives. Per the
# PBT plan, an A-reference deep model is checked the same way as an axiom: the
# deep model must equal the real callee on every caller-reachable input.
#
# The merge primitive is a pure stdlib language construct (dict-display merge),
# so it is repo/version-INSENSITIVE and present in any Python; the probe imports
# only the standard library. We still set apply_gold=True (harmless — the callee
# is unchanged by the patch). To keep the soundness check in lock-step with the
# bundle, we EMBED axiom_check.py's reference functions (read on the HOST at
# manifest-load time, since the runner mounts ONLY the probe at /work).
# ===========================================================================

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


# ax-sound-merge_slot: the A-reference soundness check. Assert the deep model
# merge_slot == the real {**d, **o} merge per level, AND read_slot == the real
# .get(level,'') read, on boundary + fuzz inputs, plus the F2P custom-level
# re-derivation. This re-runs axiom_check.py's main() (embedded verbatim). Any
# disagreement => AXIOM-UNSOUND (here: the A-reference deep model is wrong).
_AX_SOUNDNESS_PROBE = r'''
import sys

# --- embedded bundle axiom_check.py reference logic (read on host at load) ----
AXIOM_CHECK_SRC = %r
# ------------------------------------------------------------------------------

def main():
    ns = {"__name__": "_embedded_axiom_check"}
    try:
        exec(compile(AXIOM_CHECK_SRC, "axiom_check.py", "exec"), ns)
    except Exception as exc:
        print("AXIOM-SOUNDNESS FAIL: could not load embedded axiom_check: %%r" %% (exc,))
        return 1
    check_main = ns.get("main")
    if check_main is None:
        print("AXIOM-SOUNDNESS FAIL: embedded axiom_check has no main()")
        return 1
    try:
        rc = check_main()
    except AssertionError as exc:
        print("AXIOM-UNSOUND: merge_slot/read_slot A-reference deep model "
              "disagrees with real Python: %%s" %% (exc,))
        return 1
    except Exception as exc:
        print("AXIOM-SOUNDNESS FAIL: probe error: %%r" %% (exc,))
        return 1
    if rc != 0:
        print("AXIOM-UNSOUND: embedded axiom_check returned %%r" %% (rc,))
        return 1
    # extra direct cross-check (independent of the embedded harness): the
    # override-wins dict-merge order matches merge_slot on a present/present slot.
    merge_slot = ns["merge_slot"]
    assert {**{1: "d"}, **{1: "o"}}.get(1) == merge_slot("d", "o") == "o", (
        "override must win on a present/present level (dict-merge order)")
    assert {**{1: "d"}, **{2: "o"}}.get(1) == merge_slot("d", None) == "d", (
        "default must survive where the override omits the level")
    print("AXIOM-SOUNDNESS OK: merge_slot (== real {**d,**o}) + read_slot "
          "(== real .get(level,'')) A-reference deep model sound.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
''' % (_AXIOM_CHECK_SRC,)


# ax-cover-merge_slot: caller-domain CONTAINMENT. The model passes merge_slot
# only the per-slot pairs (defaults.X, override.X) where each is an Optional[int]
# (None == absent, else a tag token). The deep model's domain is exactly
# Optional[int] x Optional[int]; the real dict-merge .get(level) ranges over the
# same None<->absent encoding. Enumerate the inputs the MODEL can reach (the four
# presence classes per slot: both absent, default-only, override-only, both
# present) and confirm each lies in the deep model's / real merge's domain and
# the deep model equals the real merge there. Covering MORE (any hashable key /
# value) is SOUND, not a defect.
_AX_CONTAINMENT_PROBE = r'''
import sys

def merge_slot(d, o):
    # the deep model (model.py merge_slot), None == absent
    if o is not None:
        return o
    return d

def main():
    # The model can reach exactly these per-slot presence classes (Optional[int]
    # x Optional[int]); enumerate them with representative tokens and confirm the
    # deep model equals the real {**d, **o}.get(level) under None<->absent.
    TOKENS = [None, 0, 1, 7, 12, 99]   # 0 == empty-tag token; None == absent
    reached = 0
    for d in TOKENS:
        for o in TOKENS:
            # build the per-level dicts the way get_level_tags() composes them:
            # a None slot == level absent from that dict.
            dd = {} if d is None else {5: d}
            oo = {} if o is None else {5: o}
            real = {**dd, **oo}.get(5)          # the real callee at this level
            model = merge_slot(d, o)            # the deep model
            assert real == model, (
                "AXIOM-TOO-WEAK-FOR-CALLER: model-reachable slot pair "
                "(d=%r, o=%r) -> deep model %r != real merge %r"
                % (d, o, model, real))
            reached += 1
    print("AXIOM-CONTAINMENT OK: every model-reachable per-slot pair "
          "(Optional[int] x Optional[int]; %d classes) lies in the deep model's "
          "domain and the deep model equals the real {**d,**o} merge there. The "
          "caller reaches a subset of the merge's full domain; no reachable input "
          "is outside it." % (reached,))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-merge_slot",
        "axiom": "merge_slot",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # callee is an unchanged stdlib primitive; harmless
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "the merge_slot/read_slot A-reference deep model must equal the "
                     "real Python {**defaults, **override} merge and .get(level,'') "
                     "read on every level. The probe re-runs the bundle's own "
                     "axiom_check.py (embedded verbatim — boundary + 20000 fuzz + the "
                     "F2P custom-level re-derivation) plus an independent dict-merge "
                     "order cross-check. Any disagreement => AXIOM-UNSOUND (the deep "
                     "model would be wrong, breaking the A-reference trust point).",
    },
    {
        "id": "ax-cover-merge_slot",
        "axiom": "merge_slot",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "every per-slot pair the model can pass to merge_slot is an "
                     "Optional[int] x Optional[int] (None == level absent, else a tag "
                     "token); the deep model's domain and the real dict-merge .get "
                     "range over exactly this None<->absent encoding, so each "
                     "reachable input is inside the domain. A reachable pair outside "
                     "the domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists "
                     "(covering more — any hashable key/value — is SOUND).",
    },
]
