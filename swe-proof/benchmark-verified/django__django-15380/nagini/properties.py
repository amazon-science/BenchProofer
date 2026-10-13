# properties.py — PBT falsification battery for django__django-15380.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that SHARES the frozen spec
# (region-surgery: only text inside # impl-start / # impl-end is edited, so
# markers.same_spec holds by construction) and swaps only the implementation.
# The runner checks each with Nagini verify + same_spec.
#
# Defended surface (read from model.py + refinement.md + instance.json):
#   resolve_field_states(prior_registry, later_registry, correspondence, later)
#   selects two descriptors from three READ-ONLY registries (each is
#   Acc(dict_pred(...), 1/2)). Load-bearing postcondition clauses:
#     (P0) Result()[0] == prior_registry[prior_name(correspondence, later)]
#     (P1) Result()[1] == later_registry[later]      <- the discriminating clause
#          (the gold-patched line: later descriptor keyed by the LATER name,
#           never by the prior name). The pre-patch bug keyed it by old_name and
#           crashed (KeyError) on a renamed model — model_prepatch.py reproduces
#           this and fails the later_registry[old_name] access precondition.
#     (frame) all three Acc(...,1/2) returned; both required keys still present.
#   prior_name is a @Pure helper GROUNDED in the args (fully unfolded:
#   correspondence[later] if later in correspondence else later) — it is NOT an
#   opaque answer-key oracle, so there is no "wrong echo" to build (see the
#   assessment / the honest cheapest-impl positive control instead).
from pathlib import Path

INSTANCE = "django__django-15380"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region (verbatim). Every variant replaces exactly this block,
# so the spec view (everything else) is byte-identical => same_spec holds.
_GOLD_IMPL = """    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = later_registry[later]  # type: int
    return (old_descriptor, new_descriptor)"""


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness). Structurally different but CORRECT: the two
#    descriptor lookups are reordered (later first, prior second) and the result
#    tuple is built from named locals computed in the opposite order. Value
#    reasoning is unchanged (same @Pure prior_name call, same two subscriptions),
#    so the gold proof obligations still discharge. MUST verify; if it cannot,
#    SPEC-TOO-STRONG.
_POS_REORDER = """    new_descriptor = later_registry[later]  # type: int
    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    return (old_descriptor, new_descriptor)"""

# 1b. POSITIVE CONTROL #2: inline prior_name's body as a conditional expression
#    (correspondence[later] if later in correspondence else later) bound to a
#    typed local. prior_name is @Pure with exactly this body, so Nagini unfolds
#    it and proves the inlined value == prior_name(correspondence, later); the
#    membership guard matches dict_pred's subscription discipline. MUST verify.
_POS_INLINE = """    old_name = correspondence[later] if later in correspondence else later  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = later_registry[later]  # type: int
    return (old_descriptor, new_descriptor)"""


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY. A self-call on an F2P-shaped RENAMED-model input proves the
#    precondition admits the very configuration the bug concerns (later=2, prior
#    name=1, the model present only under its later name in later_registry). If
#    the Requires cannot be established for this legitimate input => PRECOND-TOO-
#    STRONG. We keep the gold impl and add, after it, a verifying helper that
#    builds such a state and calls resolve_field_states. Editing stays inside
#    the impl region (the helper is appended after the gold return, still before
#    # impl-end), so same_spec holds.
_ADMISS = """    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = later_registry[later]  # type: int
    return (old_descriptor, new_descriptor)


def _admiss_caller() -> None:
    # Renamed model: later name 2, prior name 1; later registry holds it only
    # under 2; prior registry holds it under 1; correspondence maps 2 -> 1.
    prior_reg = {1: 100}  # type: Dict[int, int]
    later_reg = {2: 200}  # type: Dict[int, int]
    corr = {2: 1}  # type: Dict[int, int]
    # Establish the two membership preconditions for this F2P-shaped input.
    Assert(2 in later_reg)
    Assert(prior_name(corr, 2) in prior_reg)
    res = resolve_field_states(prior_reg, later_reg, corr, 2)  # type: Tuple[int, int]
    Assert(res[1] == later_reg[2])"""


# ---------------------------------------------------------------------------
# 3. FRAME-MUTATION (MANDATORY — all three registries are Acc(...,1/2)
#    read-only). A rival that, to make a PRE-PATCH-STYLE later lookup succeed,
#    WRITES the renamed model's later descriptor into the later registry under
#    the PRIOR name (later_registry[old_name] = later_registry[later]) and then
#    reads later_registry[old_name]. With only 1/2 permission the write is
#    illegal, so this MUST fail for INSUFFICIENT PERMISSION. The gold invariants
#    (the two membership facts, the returned 1/2 perms) are untouched, so the
#    rejection is attributable to the write, not to a value mismatch.
#    Refinement: its faithful real patch (self.to_state.models[old_name] = ...
#    then read by old_name) MUTATES the shared to_state registry during rename
#    detection and re-introduces keying the later descriptor by the prior name —
#    it would corrupt to_state for every later model lookup and does NOT match
#    the gold one-line key fix, so it would not faithfully resolve the F2P.
_FRAME_MUTATE = """    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    later_registry[old_name] = later_registry[later]
    new_descriptor = later_registry[old_name]  # type: int
    return (old_descriptor, new_descriptor)"""

# 3b. FRAME-MUTATION supporting: write the result tuple's later slot by mutating
#    the prior_registry (a read-only input) — overwrite prior_registry[old_name]
#    so a later read echoes a value. Illegal under 1/2 permission. (Cheap
#    supporting near-miss; carries the same frame-condition refinement.)
_FRAME_MUTATE_PRIOR = """    old_name = prior_name(correspondence, later)  # type: int
    new_descriptor = later_registry[later]  # type: int
    prior_registry[old_name] = new_descriptor
    old_descriptor = prior_registry[old_name]  # type: int
    return (old_descriptor, new_descriptor)"""


# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN — the pre-patch bug itself. Key the LATER descriptor by the
#    PRIOR name (later_registry[old_name]) instead of by `later`. Correct on the
#    unchanged-name subdomain (old_name == later, so both lookups coincide), but
#    on a RENAMED model (old_name != later) the later registry has no entry under
#    old_name. This is exactly model_prepatch.py. It MUST be rejected: the spec
#    only guarantees `prior_name(...) in prior_registry`, NOT
#    `prior_name(...) in later_registry`, so the later_registry[old_name] access
#    precondition is UNPROVABLE. Refinement: its faithful real patch is the
#    pre-patch line self.to_state.models[app_label, old_model_name], which raises
#    KeyError on test_rename_field_with_renamed_model (the F2P) — it does NOT
#    resolve.
_PARTIAL_PREPATCH = """    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = later_registry[old_name]  # type: int
    return (old_descriptor, new_descriptor)"""

# 4b. PARTIAL-DOMAIN swap — return the two descriptors in the SAME slots but
#    derive the LATER slot from the prior registry under the later name
#    (prior_registry[later]). On the unchanged-name subdomain where a caller
#    happens to have later present in prior_registry the value may coincide, but
#    in general prior_registry[later] != later_registry[later] and `later` is not
#    guaranteed a key of prior_registry, so (P1) and the access precondition both
#    fail. MUST be rejected. Refinement: looking the later descriptor up in the
#    PRIOR-state registry is neither the gold line nor the pre-patch line; it
#    fetches the wrong (or a missing) ModelState and would not resolve the F2P.
_PARTIAL_WRONGREG = """    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = prior_registry[later]  # type: int
    return (old_descriptor, new_descriptor)"""

# 4c. PARTIAL-DOMAIN — prior slot keyed by the LATER name instead of the prior
#    name (prior_registry[later]). Coincides with gold only when old_name ==
#    later (unchanged model); on a renamed model it fetches the wrong / a missing
#    prior descriptor, breaking (P0) and possibly the access precondition. MUST
#    be rejected. Refinement: this swaps the UNCHANGED prior-state lookup to the
#    later name — it regresses the (correct, untouched) old_model_state line and
#    would mis-detect renames, not resolving the F2P.
_PARTIAL_PRIORWRONG = """    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[later]  # type: int
    new_descriptor = later_registry[later]  # type: int
    return (old_descriptor, new_descriptor)"""

# 4d. PARTIAL-DOMAIN supporting — swap the two result slots (later descriptor in
#    slot 0, prior descriptor in slot 1). Both lookups are individually legal, so
#    no permission/access failure, but (P0)/(P1) are violated whenever the two
#    descriptors differ. MUST be rejected on the postcondition value clauses.
#    Refinement: returning the descriptors transposed feeds the later ModelState
#    where the prior is expected (and vice versa) into the rename scan, mis-
#    comparing fields — it would not resolve the F2P.
_PARTIAL_SWAP = """    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = later_registry[later]  # type: int
    return (new_descriptor, old_descriptor)"""


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_REORDER),
        "rationale": "structurally-different CORRECT impl (lookups reordered, "
                     "later computed first) keeps the same @Pure prior_name call "
                     "and the same two subscriptions, so every gold proof "
                     "obligation still discharges; must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-inline-priorname",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_INLINE),
        "rationale": "inlines prior_name's @Pure body as a guarded conditional "
                     "expression; Nagini unfolds the pure helper and proves the "
                     "inlined value == prior_name(correspondence, later), so the "
                     "postcondition (P0) still holds; must verify.",
    },
    {
        "id": "admiss-renamed-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "a self-call on an F2P-shaped RENAMED-model input "
                     "(later=2, prior name=1, model present only under its later "
                     "name) establishes both membership preconditions and "
                     "verifies; the precondition admits the configuration the bug "
                     "concerns (else PRECOND-TOO-STRONG).",
    },
    {
        "id": "frame-mutate-later-registry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUTATE),
        "refinement": "the faithful real patch writes self.to_state.models under "
                      "the prior name then reads by the prior name — it mutates "
                      "the shared later-state registry during rename detection and "
                      "re-keys the later descriptor by the prior name, corrupting "
                      "to_state for every other lookup; it does NOT match the gold "
                      "one-line key change and would not faithfully resolve the F2P.",
        "rationale": "rejected by the PERMISSION SYSTEM: later_registry is "
                     "Acc(dict_pred,1/2), so the write later_registry[old_name]=... "
                     "fails for insufficient permission. A byte-fuzzer never tries "
                     "mutating a read-only input.",
    },
    {
        "id": "frame-mutate-prior-registry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUTATE_PRIOR),
        "refinement": "writing into self.from_state.models during rename detection "
                      "mutates the prior-state registry the autodetector shares "
                      "across the whole loop; not the gold change and would "
                      "corrupt subsequent prior-state lookups, not resolving the F2P.",
        "rationale": "rejected by the PERMISSION SYSTEM: prior_registry is "
                     "Acc(dict_pred,1/2); the write prior_registry[old_name]=... "
                     "fails for insufficient permission (supporting frame case).",
    },
    {
        "id": "partial-prepatch-laterkey",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_PREPATCH),
        "refinement": "this IS the pre-patch line "
                      "self.to_state.models[app_label, old_model_name]; on "
                      "test_rename_field_with_renamed_model the renamed model is "
                      "absent from to_state under its prior name, raising the "
                      "KeyError the issue reports — it does NOT resolve the F2P.",
        "rationale": "rejected by the ACCESS PRECONDITION of later_registry[old_name]: "
                     "the spec guarantees only prior_name(...) in prior_registry, "
                     "never in later_registry, so the subscription is unprovable on "
                     "the renamed subdomain (old_name != later). This is the "
                     "discriminating clause (P1) / model_prepatch.py.",
    },
    {
        "id": "partial-later-from-prior-registry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_WRONGREG),
        "refinement": "fetching the later descriptor from the PRIOR-state registry "
                      "(by the later name) is neither the gold nor the pre-patch "
                      "line; it returns the wrong (or a missing) ModelState into the "
                      "rename scan and would not resolve the F2P.",
        "rationale": "rejected by (P1) Result()[1]==later_registry[later] and by "
                     "the access precondition: `later` is not guaranteed a key of "
                     "prior_registry, and prior_registry[later] != later_registry[later] "
                     "in general.",
    },
    {
        "id": "partial-prior-by-latername",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_PRIORWRONG),
        "refinement": "this regresses the UNCHANGED prior-state lookup "
                      "(old_model_state = from_state[old_model_name]) to key it by "
                      "the later name; on a renamed model the prior descriptor is "
                      "wrong/missing and rename detection mis-fires — it would not "
                      "resolve the F2P.",
        "rationale": "rejected by (P0) Result()[0]==prior_registry[prior_name(...)] "
                     "and the access precondition: `later` need not be a key of "
                     "prior_registry, and prior_registry[later] != "
                     "prior_registry[prior_name(...)] on the renamed subdomain.",
    },
    {
        "id": "partial-swap-slots",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_SWAP),
        "refinement": "returning the prior and later descriptors transposed feeds "
                      "the later ModelState where the prior is expected into the "
                      "field-rename comparison, mis-detecting renames — it would not "
                      "resolve the F2P.",
        "rationale": "both lookups are legal (no permission failure) but the value "
                     "clauses (P0) Result()[0]==prior_registry[prior_name(...)] and "
                     "(P1) Result()[1]==later_registry[later] are violated whenever "
                     "the two descriptors differ; rejected on the postcondition "
                     "(supporting case).",
    },
]


# No @ContractOnly axioms and no A-reference deep model the verifier consumes:
# the descriptor-selection logic is modelled deeply (prior_name + the two guarded
# subscriptions). The dict-semantics A-reference is validated out-of-band by
# axiom_check.py (G-AX); there is no consumed axiom obligation to probe here.
AXIOM_TESTS = []
