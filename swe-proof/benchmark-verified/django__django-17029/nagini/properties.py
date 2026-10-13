# properties.py — PBT falsification battery for django__django-17029. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` is edited; the spec view — class,
# axioms/pure/pre-/post-conditions regions + signatures — is never touched), checked
# by Nagini verify + markers.same_spec. Axiom cases probe the single A-reference deep
# model (functools.cache cache_clear() -> currsize == 0) against the REAL stdlib
# callee (see AXIOM_TESTS at the bottom).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   clear_all_caches(registry: Registry) -> None
#   Models the gold change to Apps.clear_cache(): the registry's single cache-reset
#   operation must empty EVERY memoizing method's cache, so afterwards each method's
#   cache occupancy is zero — regardless of how full it was before. The registry is a
#   minimal class carrying one non-negative int per memoizing method:
#     * models_cache_occupancy    <- Apps.get_models.cache_info().currsize
#     * swappable_cache_occupancy <- Apps.get_swappable_settings_name.cache_info().currsize
#   The gold patch's ONE added line is self.get_swappable_settings_name.cache_clear();
#   the pre-patch code cleared only get_models. The discriminating content lives in
#   the postcondition `swappable_cache_occupancy == 0`.
#
#   PRECONDITION (three clauses: two FRAMING/permission — FULL permission — plus a
#   total-correctness obligation):
#     (P1) Requires(Acc(registry.models_cache_occupancy))      # FULL (write-capable)
#     (P2) Requires(Acc(registry.swappable_cache_occupancy))   # FULL (write-capable)
#     (P3) Requires(MustTerminate(2))                          # total correctness
#   POSTCONDITION (four clauses; two framing + two LOAD-BEARING):
#     (Q1) Ensures(Acc(registry.models_cache_occupancy))       # returns the permission
#     (Q2) Ensures(Acc(registry.swappable_cache_occupancy))    # returns the permission
#     (Q3) Ensures(registry.models_cache_occupancy == 0)       # LOAD-BEARING
#     (Q4) Ensures(registry.swappable_cache_occupancy == 0)    # LOAD-BEARING (the FIX)
#   Q3 and Q4 PIN the post-state of BOTH occupancy fields EXACTLY to 0. There is no
#   slack: a rival that leaves either field at any non-zero value (the pre-patch bug,
#   or a decrement, or a copy-of-the-other) fails Q3 or Q4.
#
# FRAME-MUTATION lane is NOT APPLICABLE here (and is correctly omitted): neither input
#   field is read-only. P1/P2 grant FULL permission Acc(registry.<field>) (NOT
#   Acc(...,1/2)), and the gold impl GENUINELY WRITES both fields — that is the whole
#   point of the operation (a cache reset mutates the registry's observable state). The
#   "overwrite a read-only Acc(...,1/2) input to satisfy the postcondition vacuously"
#   escape (the project's #1 weakness class) requires a half-permission read-only
#   input; there is none. Moreover Q3/Q4 pin the post-state to EXACTLY 0, so even an
#   adversarial overwrite cannot satisfy the postcondition vacuously — any write must
#   land on 0. See 'assessment'. (has_readonly_input is therefore FALSE for this
#   instance; per the schema, since there is no Acc(...,1/2) input, no frame-mutation
#   reject case is constructible — confirmed in mapping.md/G-EQ.)
#
# UNGROUNDED-ORACLE-ECHO lane is NOT APPLICABLE (no wrong echo constructible): the
#   pure region is EMPTY — there is no @Pure answer-key / exact marker / opaque oracle
#   in the contract. Q3/Q4 are pinned to the concrete literal 0, GROUNDED directly in
#   the required post-state (independent of any input value). There is no value an
#   "echo" could carry that satisfies Q3/Q4 yet is wrong — the unique satisfier IS
#   `field == 0`. The honest cheapest faithful impl is therefore "assign 0", which is
#   exactly the positive controls below (expect=verify), not a weakness.
#
# CONTROL-FLOW-EFFECT lane: clear_all_caches has no raise/return fork, but under
#   PARTIAL-correctness semantics a DIVERGING body (`while True: pass`) satisfies
#   Q3/Q4 vacuously — the G-PANEL-1 auditor built exactly that same-spec wrong impl
#   (atk_7: `while True: pass` inserted at the top of Apps.clear_cache, which hangs
#   the F2P test forever). The spec therefore carries (P3) Requires(MustTerminate(2))
#   — a total-correctness obligation. Nagini's obligation-leak check rejects any
#   body that loops without taking the obligation or re-calls the function under
#   spec at a non-decreasing measure. Registry.__init__ carries MustTerminate(1)
#   (strictly smaller), so constructing a fresh registry inside a variant remains
#   admissible. The weak-diverge and weak-self-echo rivals below pin this lane.
#
# PARTIAL-DOMAIN / UNIQUENESS lane is the heart of the battery: rivals that clear only
#   one cache (incl. the literal pre-patch bug), clear neither, decrement instead of
#   zero, copy one field from the other, or special-case a starting-occupancy value.
#   Each fails Q3 and/or Q4 and carries the refinement that its faithful real patch
#   would NOT resolve the F2P test_clear_cache.
#
# AXIOM lane: meta.axioms == [] (NO consumed @ContractOnly axiom). deep_model_references
#   has ONE A-reference: `functools.cache cache_clear() -> currsize == 0`. Per
#   PBT_PLAN §2.4 / §4a an A-reference deep model is validated == the real callee on
#   every caller-reachable input. functools.cache is the Python STANDARD LIBRARY (the
#   exact callee Apps.get_models / Apps.get_swappable_settings_name are wrapped with),
#   so the probes need NO repo import and run anywhere. The probes reuse the bundle's
#   own axiom_check.py logic (read on the HOST at load time and embedded into the
#   probe string per directive 6) plus the containment argument.
from pathlib import Path

INSTANCE = "django__django-17029"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY this
# block, so the edit never touches the spec (the Registry class, axioms/pure/pre-/
# post-conditions regions + the function signature). same_spec is computed over the
# spec_view, which elides every impl region, so swapping inside here is GUARANTEED
# same_spec.
_IMPL = """\
    registry.swappable_cache_occupancy = 0
    registry.models_cache_occupancy = 0"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------

# pos-reorder: structurally DIFFERENT but behaviourally identical. The model.py
# impl writes swappable then models; the gold patch order is swappable-clear then
# models-clear. Here we write models FIRST, then swappable — a pure reorder of two
# INDEPENDENT field stores (different heap locations, no aliasing, no loop, no
# lemma). The post-state of both fields is identical (== 0), so Q3/Q4 still hold.
# If it FAILS => SPEC-TOO-STRONG (a faithful, structurally-different correct impl
# is rejected).
_POS_REORDER = """\
    # Reordered (models cleared first, then swappable): two independent stores,
    # identical post-state. Mirrors the gold patch's pair of cache_clear() calls
    # in the opposite textual order.
    registry.models_cache_occupancy = 0
    registry.swappable_cache_occupancy = 0"""

# pos-localvar: structurally DIFFERENT but correct — assign the cleared value
# through a typed local instead of an inline literal. Same post-state. The local
# is bound with a proper Nagini `# type:` comment on the assignment target (not on
# a bare expression), per pilot pitfall #1.
_POS_LOCALVAR = """\
    # Clear via a typed local zero (assign-once, store-twice). Same post-state.
    zero = 0  # type: int
    registry.swappable_cache_occupancy = zero
    registry.models_cache_occupancy = zero"""

# admiss-roundtrip: an admissibility + roundtrip positive control. The precondition
# is two FULL permissions Acc(registry.<field>) plus MustTerminate(2). This control
# keeps the gold reset on the parameter `registry` VERBATIM, but FIRST constructs a
# fresh, fully-owned Registry with a non-trivial starting occupancy (5, 3) — a
# normal F2P-shaped registry (the F2P primes both caches non-empty before clearing)
# — asserts the constructor delivered that in-domain state, applies the gold reset
# to it in-line, and asserts BOTH of its occupancies are 0 afterwards. Constructing
# Registry(5, 3) needs occupancy >= 0 (admitted: 5>=0, 3>=0) and MustTerminate(1)
# (admitted: strictly smaller than the caller's MustTerminate(2) obligation, so no
# obligation leak). NOTE: the roundtrip applies the reset in-line rather than via a
# self-call `clear_all_caches(fresh)` — a self-call at the same MustTerminate
# measure is (correctly) rejected by the obligation-leak check, which is precisely
# the anti-self-echo property the spec now pins (see weak-self-echo). If the
# precondition could not admit a normal F2P-shaped registry, the construction or
# the asserts would fail => PRECOND-TOO-STRONG.
_ADMISS = """\
    # Admissibility + roundtrip: a freshly-constructed registry with non-empty
    # caches is in-domain (constructor MustTerminate(1) < caller's 2); the gold
    # reset applied to it must drive BOTH occupancies to 0.
    fresh = Registry(5, 3)
    Assert(fresh.models_cache_occupancy == 5)
    Assert(fresh.swappable_cache_occupancy == 3)
    fresh.swappable_cache_occupancy = 0
    fresh.models_cache_occupancy = 0
    Assert(fresh.models_cache_occupancy == 0)
    Assert(fresh.swappable_cache_occupancy == 0)
    # --- gold reset on the parameter, verbatim ---
    registry.swappable_cache_occupancy = 0
    registry.models_cache_occupancy = 0"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl region changes.
# ---------------------------------------------------------------------------

# weak-models-only: the PRE-PATCH bug (model_prepatch.py). Clears only the
# all-models cache and leaves the swappable cache untouched (whatever it was on
# entry). This is EXACTLY the gold patch's defect. Fails Q4.
_WEAK_MODELS_ONLY = """\
    # Pre-patch bug: clear ONLY the all-models cache; never touch swappable.
    registry.models_cache_occupancy = 0"""

# weak-swappable-only: the dual bug — clears only the swappable cache and leaves
# the all-models cache. Fails Q3. (Not a historically-real patch, but a same-spec
# wrong impl the spec must still reject; carries the corresponding refinement.)
_WEAK_SWAPPABLE_ONLY = """\
    # Inverted bug: clear ONLY the swappable cache; never touch all-models.
    registry.swappable_cache_occupancy = 0"""

# weak-neither: a no-op reset (clears nothing). Models a clear_cache() that
# accidentally short-circuits (e.g. an early return). Fails Q3 AND Q4. A bare
# `return` — None is the declared return type, so no `# type:` pitfall.
_WEAK_NEITHER = """\
    # No-op reset: clears nothing.
    return"""

# weak-decrement: instead of clearing to 0, "evict one entry" from each cache by
# decrementing the occupancy by 1 (guarded so it stays non-negative). On any cache
# that held >= 2 entries on entry it leaves a non-zero occupancy, so a later
# observer still sees stale memoized values. Fails Q3/Q4 whenever a field was != 1
# on entry. PARTIAL-DOMAIN-by-value (correct only when a field started at exactly
# 0 or 1). Reads are admitted under the FULL permission.
_WEAK_DECREMENT = """\
    # Evict one entry instead of clearing: leaves a non-zero occupancy whenever a
    # cache held >= 2 entries on entry.
    if registry.models_cache_occupancy > 0:
        registry.models_cache_occupancy = registry.models_cache_occupancy - 1
    if registry.swappable_cache_occupancy > 0:
        registry.swappable_cache_occupancy = registry.swappable_cache_occupancy - 1"""

# weak-copy-other: clear the all-models cache to 0, but set the swappable
# occupancy to the (now-cleared) all-models value. Looks like it "synchronises"
# the two, and HAPPENS to be 0 only because models was just cleared — a value
# coincidence, not a clear of the swappable cache. This is a value-proxy cheat: it
# pins swappable to a copy of another field rather than to its own emptied state.
# Here it actually verifies-or-not is the question: models is set 0 first, then
# swappable := models == 0, so the post-state IS 0 for both. This is therefore a
# CORRECT-by-coincidence impl and must VERIFY — included as a positive control to
# show the spec does not over-reject. (Kept in the reject section's neighbourhood
# for documentation but tagged soundness/verify below.)
_POS_COPY_OTHER = """\
    # Synchronise swappable to the just-cleared all-models occupancy. Correct by
    # construction: models is 0, so swappable becomes 0 too. Different shape,
    # same post-state.
    registry.models_cache_occupancy = 0
    registry.swappable_cache_occupancy = registry.models_cache_occupancy"""

# weak-stale-swappable: clear all-models, and "refresh" the swappable occupancy to
# a fixed non-zero sentinel (e.g. it re-primes one canonical lookup). Models a
# clear_cache() variant that clears get_models but then immediately repopulates the
# swappable cache. Fails Q4 (swappable_cache_occupancy must be 0, not 1).
_WEAK_STALE = """\
    # Clear all-models but re-prime the swappable cache to a non-zero occupancy.
    registry.models_cache_occupancy = 0
    registry.swappable_cache_occupancy = 1"""

# weak-diverge: CONTROL-FLOW-EFFECT / vacuous-by-divergence. The body is an
# infinite loop; under partial-correctness semantics it would satisfy Q3/Q4
# vacuously (no terminating path exists on which they could fail). This is the
# EXACT same-spec wrong impl the G-PANEL-1 auditor built (atk_7), whose faithful
# real patch inserts `while True: pass` at the top of Apps.clear_cache() — the
# F2P test_clear_cache then HANGS forever (never reaches its assertions), so it
# does not resolve. Must be REJECTED by the MustTerminate(2) obligation (P3):
# Nagini's obligation-leak check flags a loop that does not take the unsatisfied
# termination obligation.
_WEAK_DIVERGE = """\
    # Diverge instead of clearing: vacuously satisfies the postconditions under
    # partial correctness; rejected by the MustTerminate obligation.
    while True:
        pass"""

# weak-self-echo: re-derive the whole contract from the function under spec
# itself via self-recursion. Under partial correctness the self-call "returns"
# with both postconditions established for free while its faithful refinement
# is infinite recursion (clear_cache calling itself), which RecursionErrors /
# never returns and clears nothing — the F2P fails. Must be REJECTED: the
# self-call takes the same MustTerminate(2) obligation without a strictly
# smaller measure => obligation leak.
_WEAK_SELF_ECHO = """\
    # Self-echo: discharge the contract by calling the function under spec.
    clear_all_caches(registry)"""

# weak-conditional-skip: PARTIAL-DOMAIN. Clears all-models always, but only clears
# swappable when it was already small (< 2 on entry); for a swappable cache that
# held >= 2 entries it leaves it untouched. Correct on the sub-domain where the
# swappable cache started at 0 or 1, WRONG (leaves stale entries) exactly when it
# was fuller — the case the bug actually matters. A byte-fuzzer never targets this
# occupancy-class boundary. Fails Q4 on the >= 2 sub-domain.
_WEAK_CONDITIONAL = """\
    # Clear all-models; clear swappable ONLY if it was nearly-empty (< 2). Leaves a
    # fuller swappable cache stale — diverging on the >= 2 occupancy sub-domain.
    registry.models_cache_occupancy = 0
    if registry.swappable_cache_occupancy < 2:
        registry.swappable_cache_occupancy = 0"""


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but CORRECT: the two INDEPENDENT field stores "
            "are written in the opposite order (all-models first, then swappable), "
            "mirroring the gold patch's pair of cache_clear() calls. No loop / no "
            "lemma; the post-state of both fields is identical (== 0), so Q3/Q4 "
            "still hold. If it FAILS => SPEC-TOO-STRONG (a faithful correct impl "
            "rejected)."
        ),
    },
    {
        "id": "pos-localvar",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LOCALVAR),
        "rationale": (
            "structurally-different but CORRECT: the cleared value flows through a "
            "typed local `zero = 0  # type: int` (assign-once, store-twice) instead "
            "of two inline literals. Same post-state; Q3/Q4 hold. The `# type:` "
            "comment is on an assignment target (pilot pitfall #1 avoided). If it "
            "FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-copy-other",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_COPY_OTHER),
        "rationale": (
            "structurally-different but CORRECT-by-construction: all-models is "
            "cleared to 0, then swappable is set to that just-cleared value (also "
            "0). A reshaped impl with the SAME post-state (both 0); Q3/Q4 hold, so "
            "it MUST verify. Confirms the spec does not over-reject a differently-"
            "shaped correct reset. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-roundtrip",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (two FULL permissions Acc(registry.<field>) plus "
            "MustTerminate(2)) must admit a normal F2P-shaped registry: a fresh "
            "Registry(5, 3) (non-empty caches, occupancy >= 0; constructor "
            "MustTerminate(1) strictly smaller than the caller's obligation) is "
            "constructed, its in-domain state asserted, the gold reset applied to "
            "it in-line, and BOTH its occupancies asserted 0. The gold reset on "
            "the parameter follows verbatim. (The reset is applied in-line rather "
            "than via a self-call: a same-measure self-call is correctly rejected "
            "by the obligation-leak check — the anti-self-echo property pinned by "
            "weak-self-echo.) If the construction or asserts could not go through "
            "for a legitimate registry => PRECOND-TOO-STRONG. The asserts confirm "
            "the postcondition-shaped facts fire for a representative input (the "
            "F2P primes both caches before clearing)."
        ),
    },
    {
        "id": "weak-models-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MODELS_ONLY),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): clear_cache() "
            "calls only self.get_models.cache_clear() and never "
            "self.get_swappable_settings_name.cache_clear() — exactly the bug the "
            "gold patch fixes by ADDING that one line. Its faithful real patch is "
            "the UNPATCHED repo, on which the F2P test_clear_cache asserts "
            "apps.get_swappable_settings_name.cache_info().currsize == 0 after "
            "clear_cache(), which FAILS because the swappable cache still holds the "
            "result primed by get_swappable_settings_name('admin.LogEntry'). Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q4 (registry.swappable_cache_occupancy == 0): the impl "
            "leaves swappable at its arbitrary on-entry value, which the verifier "
            "cannot prove is 0. This is exactly what G-DIFF senses against "
            "model_prepatch.py. If it VERIFIES => SPEC-TOO-WEAK (the swappable "
            "clear, the discriminating content of the fix, is unpinned)."
        ),
    },
    {
        "id": "weak-swappable-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAPPABLE_ONLY),
        "refinement": (
            "the dual omission: a real patch that REPLACED the existing "
            "self.get_models.cache_clear() with the new "
            "self.get_swappable_settings_name.cache_clear() (instead of ADDING it) "
            "would clear only the swappable cache and leave get_models populated. "
            "The F2P asserts apps.get_models.cache_info().currsize == 0 as well "
            "(after apps.get_models() primes it), which FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (registry.models_cache_occupancy == 0): the all-models "
            "occupancy is left at its on-entry value, not provably 0. If it "
            "VERIFIES => SPEC-TOO-WEAK (the spec must pin EVERY memoizing method's "
            "cache to 0, not just the swappable one)."
        ),
    },
    {
        "id": "weak-neither",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NEITHER),
        "refinement": (
            "a no-op reset is what a clear_cache() that early-returned (or whose "
            "body was deleted) would do — it clears nothing, so both "
            "cache_info().currsize values stay at the primed occupancies. The F2P "
            "asserts BOTH are 0, which FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 AND Q4: both occupancy fields keep their on-entry "
            "values, neither provably 0. If it VERIFIES => SPEC-TOO-WEAK (the spec "
            "would not require ANY cache to be emptied)."
        ),
    },
    {
        "id": "weak-decrement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DECREMENT),
        "refinement": (
            "decrementing each occupancy by one models a clear_cache() that evicts "
            "a single entry per cache (e.g. pops the LRU head) instead of calling "
            "cache_clear(). For a cache that held >= 2 entries on entry it leaves a "
            "non-zero occupancy, so stale memoized values survive. The F2P primes "
            "the caches and asserts currsize == 0; a single-eviction patch leaves "
            "currsize > 0 whenever > 1 entry was cached, which FAILS. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by Q3/Q4 (each occupancy == 0): for an on-entry value v >= 2 "
            "the impl leaves v-1 > 0, so the verifier cannot prove == 0 (the "
            "Requires admits any non-negative starting occupancy). PARTIAL-DOMAIN-"
            "by-value: correct only when a field started at exactly 0 or 1. If it "
            "VERIFIES => SPEC-TOO-WEAK (the post-state would not be pinned to 0)."
        ),
    },
    {
        "id": "weak-stale-swappable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_STALE),
        "refinement": (
            "clearing all-models but leaving the swappable occupancy at a non-zero "
            "sentinel models a clear_cache() that clears get_models then immediately "
            "re-primes the swappable cache (or never fully clears it). The F2P "
            "asserts apps.get_swappable_settings_name.cache_info().currsize == 0; a "
            "value of 1 FAILS. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q4 (registry.swappable_cache_occupancy == 0): the impl "
            "sets it to 1, not 0. A supporting near-miss carrying a real refinement. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DIVERGE),
        "refinement": (
            "the faithful real patch inserts `while True: pass` at the top of "
            "Apps.clear_cache() (the literal G-PANEL-1 atk_7 attack): clear_cache() "
            "then never returns, neither wrapper's cache_clear() ever runs, and the "
            "F2P test_clear_cache HANGS forever before reaching its currsize "
            "assertions — the test run times out / fails. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by P3 (Requires(MustTerminate(2))): a body that loops forever "
            "cannot take the unsatisfied termination obligation, so Nagini fails the "
            "obligation-leak check ('Loop might not take all unsatisfied obligations "
            "from the context'). Without P3 the body satisfies Q3/Q4 VACUOUSLY under "
            "partial correctness — exactly the weakness the auditor exploited. If it "
            "VERIFIES => SPEC-TOO-WEAK (divergence admitted)."
        ),
    },
    {
        "id": "weak-self-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SELF_ECHO),
        "refinement": (
            "the faithful refinement is `def clear_cache(self): self.clear_cache()` "
            "— infinite recursion that RecursionErrors (or never returns) before "
            "clearing either cache, so the F2P test_clear_cache fails. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the obligation-leak check: clear_all_caches Requires("
            "MustTerminate(2)); the self-call would have to take the same obligation "
            "without a strictly smaller measure ('Callee clear_all_caches might not "
            "take all unsatisfied obligations from the caller'). Closes the "
            "function-under-spec self-echo escape. If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-conditional-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CONDITIONAL),
        "refinement": (
            "clearing the swappable cache only when it was already nearly-empty "
            "(< 2 entries) models a clear_cache() that skips the swappable "
            "cache_clear() on a fuller cache (e.g. a mis-guarded `if len < N` "
            "optimisation). The F2P primes the swappable cache via "
            "get_swappable_settings_name('admin.LogEntry') and asserts currsize == "
            "0; whenever the cache held >= 2 entries it stays populated, which "
            "FAILS. A genuine PARTIAL-DOMAIN break on the occupancy-class boundary. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q4 (registry.swappable_cache_occupancy == 0): on the "
            "sub-domain where swappable started at >= 2 the impl leaves it "
            "untouched (non-zero), so the verifier cannot prove == 0 for all "
            "admitted inputs. PARTIAL-DOMAIN: pins only the < 2 occupancy class. If "
            "it VERIFIES => SPEC-TOO-WEAK on the boundary a byte-fuzzer never "
            "targets."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-reference deep model `functools.cache cache_clear() ->
# currsize == 0` vs the REAL stdlib callee.
# meta.axioms == [] (NO consumed @ContractOnly axiom); deep_model_references has ONE
# A-reference: the representation refinement `method.cache_clear()` <-> `occupancy = 0`
# (refinement.md A2/A3, mapping.md §2/§3). functools.cache is the Python STANDARD
# LIBRARY — the exact module Apps.get_models / Apps.get_swappable_settings_name are
# wrapped with and that clear_cache() calls cache_clear() on — so the probes need NO
# repo import and run anywhere (Docker or host). We REUSE the bundle's own
# axiom_check.py (read on the HOST at load time, embedded into the probe string per
# directive 6) for soundness, and add the containment argument.
# ---------------------------------------------------------------------------

# Read the bundle's existing G-AX soundness check on the HOST at manifest-load time
# (it is NOT mounted in-container — directive 6) and embed its source into the probe.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

_AX_SOUND_PROBE = (
    "# AXIOM-SOUNDNESS probe: re-run the bundle's G-AX check verbatim against the\n"
    "# REAL functools.cache stdlib callee (embedded from axiom_check.py on the host).\n"
    "# Exits 0 iff cache_clear() drives cache_info().currsize to 0 from every tested\n"
    "# starting occupancy and per-wrapper independence holds.\n"
    + _AXIOM_CHECK_SRC
)

_AX_COVER_PROBE = '''\
# AXIOM-CONTAINMENT probe: every callee-input the MODEL can reach lies inside the
# A-reference callee's (functools._lru_cache_wrapper.cache_clear()) domain.
#
# What inputs can clear_all_caches actually reach? The A-reference fact is applied to
# EXACTLY two operands, one per memoizing method:
#   * Apps.get_models                 (a functools.cache-wrapped method)
#   * Apps.get_swappable_settings_name (a functools.cache-wrapped method)
# For each, the model's `*_cache_occupancy` int field refines cache_info().currsize
# (a non-negative int), and the reset refines a call to that method's cache_clear().
# The model's Requires bounds the starting occupancy only by >= 0 (Registry.__init__
# requires occupancy >= 0); cache_clear() is a NILADIC method (takes no arguments) and
# is total over a functools.cache wrapper at ANY currsize. So the only "input" the
# caller can reach is "a functools.cache wrapper at some non-negative currsize", and
# cache_clear() is defined (raises nothing, returns currsize to 0) for every such
# wrapper. Containment is therefore trivially total; we CONFIRM it by exercising
# cache_clear() on real functools.cache wrappers driven to a heavy sample of reachable
# starting occupancies (incl. 0 and large), asserting it never raises and yields
# currsize == 0.
import functools
import random
import sys

def make_wrapper():
    @functools.cache
    def f(x):
        return x * x
    return f

fails = 0
rng = random.Random(170290)

# reachable starting occupancies: the boundary set + a heavy random sample of
# non-negative ints (the model's Requires admits ANY occupancy >= 0).
occupancies = [0, 1, 2, 3, 5, 7, 16, 64, 256, 1000]
occupancies += [rng.randint(0, 5000) for _ in range(3000)]

for occ in occupancies:
    w = make_wrapper()
    for i in range(occ):
        w(i)                      # drive currsize up to occ (a reachable input)
    if w.cache_info().currsize != occ:
        fails += 1
        print("setup mismatch: wanted currsize %d got %d" % (occ, w.cache_info().currsize))
        continue
    try:
        w.cache_clear()           # the A-reference callee on a reachable input
    except Exception as e:        # noqa
        fails += 1
        print("CONTAINMENT FAIL: cache_clear() raised on reachable occupancy %d: %r" % (occ, e))
        continue
    got = w.cache_info().currsize
    if got != 0:
        fails += 1
        print("CONTAINMENT/SOUNDNESS FAIL: cache_clear() from occupancy %d left currsize %d" % (occ, got))

# Per-wrapper independence: the model reaches TWO wrappers (get_models,
# get_swappable_settings_name); clearing one is in-domain and does not depend on the
# other (motivating clearing EVERY wrapper). Confirm both can be cleared independently.
a = make_wrapper()
b = make_wrapper()
for i in range(9):
    a(i)
for i in range(4):
    b(i)
a.cache_clear()
if a.cache_info().currsize != 0 or b.cache_info().currsize != 4:
    fails += 1
    print("CONTAINMENT FAIL: clearing one wrapper not independent of the other")
b.cache_clear()
if b.cache_info().currsize != 0:
    fails += 1
    print("CONTAINMENT FAIL: second wrapper cache_clear() left currsize %d" % b.cache_info().currsize)

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside cache_clear()'s domain "
          "or mismatched" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every callee-input the model can reach (a functools.cache wrapper "
      "at any occupancy >= 0; the niladic cache_clear() on get_models / "
      "get_swappable_settings_name) lies INSIDE cache_clear()'s domain (total, raises nothing, "
      "yields currsize == 0); confirmed over %d reachable occupancies + per-wrapper independence."
      % len(occupancies))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-cache_clear",
        "axiom": "functools.cache cache_clear() -> currsize == 0",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "the single A-reference deep model is `for a functools.cache-wrapped "
            "method, after m.cache_clear() the observable occupancy "
            "m.cache_info().currsize is 0 from ANY starting occupancy` (the "
            "representation refinement method.cache_clear() <-> occupancy = 0). No "
            "consumed @ContractOnly axiom. AXIOM-SOUNDNESS: the deep model must "
            "equal the REAL callee. The probe re-runs the bundle's G-AX check "
            "(axiom_check.py, embedded from the host) against the live functools.cache "
            "over 9 boundary + 2000 fuzz starting occupancies + repeated-refill, and "
            "confirms per-wrapper independence. If the real callee disagrees anywhere "
            "=> AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-cache_clear",
        "axiom": "functools.cache cache_clear() -> currsize == 0",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: clear_all_caches applies the A-reference fact to "
            "exactly the two functools.cache wrappers (get_models, "
            "get_swappable_settings_name), each at some occupancy >= 0 (the model's "
            "Requires bounds the occupancy only by >= 0). cache_clear() is a niladic "
            "method total over a functools.cache wrapper at ANY currsize, so every "
            "reachable callee-input is INSIDE its domain. The probe drives real "
            "wrappers to a heavy sample of reachable occupancies (incl. 0 and large) "
            "and asserts cache_clear() never raises and yields currsize == 0, plus "
            "per-wrapper independence. A reachable input outside the domain => "
            "AXIOM-TOO-WEAK-FOR-CALLER (none expected: cache_clear() is total)."
        ),
    },
]
