# properties.py — PBT falsification battery for django__django-13109. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md + mapping.md + the gold patch):
#   validate_reference(value: int, complete_rows: List[int], curated_rows: List[int]) -> None
#   The relational-field reference check ForeignObject.validate (related.py:917).
#   The single changed token is `_default_manager` -> `_base_manager`: the check
#   must consult the COMPLETE (base-manager) collection, not the curated default
#   collection. A reference to a genuinely-stored row that the curated default
#   manager hides (e.g. an archived row) must PASS; an absent key must be REJECTED.
#
#   Preconditions (TWO inputs, BOTH READ-ONLY, plus a termination obligation):
#     (P1) Requires(Acc(list_pred(complete_rows), 1 / 2))   # HALF perm => no write
#     (P2) Requires(Acc(list_pred(curated_rows),  1 / 2))   # HALF perm => no write
#     (P3) Requires(MustTerminate(2))   # total correctness: the check must ANSWER
#          # (return or raise); a diverging impl (bare self-recursion, endless
#          # loop) can no longer satisfy Q3/Q4 vacuously. Measure 2 => the impl
#          # may call the pure helpers but may NOT re-invoke itself.
#   Postcondition:
#     (Q1) Ensures(Acc(list_pred(complete_rows), 1 / 2))    # returns the read perm
#     (Q2) Ensures(Acc(list_pred(curated_rows),  1 / 2))    # returns the read perm
#     (Q3) Ensures(reference_holds(value, ToSeq(complete_rows)))     # LOAD-BEARING:
#          # returns normally exactly when present(value, complete_rows)
#          # AND choice_permitted(value) — decided over COMPLETE_ROWS ONLY.
#     (Q4) Exsures(ReferenceInvalid, ... and not reference_holds(value,
#          ToSeq(complete_rows)))   # raises exactly when the reference does NOT
#          # hold over COMPLETE_ROWS — again the curated collection is ABSENT.
#
#   reference_holds(k, c) == present(k, c) and choice_permitted(k)  [@Pure].
#   present is a front-recursive membership fold over the PSeq [@Pure].
#   choice_permitted is @Pure @ContractOnly with Ensures(True) — the unchanged
#   limit_choices_to narrowing; an OPAQUE deterministic per-key predicate with NO
#   value claim (it is the SECOND conjunct of reference_holds; the proof cannot
#   prove present => choice_permitted, so a rival that drops it must be rejected).
#
# WHICH WEAKNESS CLASSES APPLY:
#   * FRAME-MUTATION (MANDATORY): BOTH complete_rows and curated_rows are
#     Acc(...,1/2) read-only. Two rivals WRITE to each input; both must be
#     REJECTED for INSUFFICIENT PERMISSION. (#1 weakness class; a byte-fuzzer
#     never thinks to mutate the input.)
#   * PARTIAL-DOMAIN / THE ACTUAL BUG: the discriminator is "consult curated_rows
#     instead of complete_rows" (= the prepatch behaviour, model_prepatch.py) and
#     "miss a stored row at a position" (off-by-one head skip). Both reject on the
#     archived-but-stored witness class.
#   * UNGROUNDED-ORACLE ECHO: Q3 is pinned to reference_holds, which is GROUNDED in
#     the arguments (present(value, complete_rows) is fully unfolded; the only
#     opaque term, choice_permitted, carries Ensures(True) so it makes NO value
#     claim an echo could exploit). There is therefore no WRONG echo of a @Pure
#     answer-key that could verify. So instead of a wrong-echo case we include the
#     two honest cheapest-impl baselines a "forgot to do the work" patch produces:
#     always-return ("never reject") and always-raise ("always reject"); both are
#     rejected by Q3 / Q4. See 'assessment'.
#   * IGNORE-CHOICE: a rival that decides on present() alone (drops the
#     choice_permitted conjunct) — rejected because the proof cannot establish
#     choice_permitted(value) on the return path (it is @ContractOnly/opaque).
#   * CONTROL-FLOW-EFFECT: N/A as a *separate* token. The sole observable effect of
#     this function IS its control flow — return-normally vs raise — and that is
#     already pinned by Q3 (return) and Q4 (raise) over complete_rows. Every rival
#     below is discriminated precisely on that return/raise boundary; there is no
#     additional side-effect invisible to the value abstraction (the function
#     returns None and mutates nothing). See 'assessment'.
#
# AXIOM lane: ONE @ContractOnly axiom (choice_permitted, A-consumed) and ONE
#   A-reference deep model (the base-vs-default manager subset, modeled DEEPLY as
#   membership over complete_rows). choice_permitted's contract is Ensures(True)
#   (the WEAKEST possible) so axiom-soundness is vacuous (nothing can violate True)
#   and axiom-containment is trivial (domain = all ints, the caller only passes an
#   int). The MEANINGFUL axiom-lane obligation is the A-reference: the deep model
#   "complete_rows == the base-manager key set, and the check decides over it"
#   must equal the REAL Django managers. We re-run axiom_check.py's logic in the
#   instance image (gold applied) as the axiom-soundness/containment probe: it
#   drives the real ForeignKey.validate and confirms the base manager exposes
#   every stored row, the default manager is a strict subset, the archived witness
#   validates, an absent key is rejected, and choice_permitted (limit_choices_to)
#   is empty + deterministic. See AXIOM_TESTS.
from pathlib import Path

INSTANCE = "django__django-13109"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, VERBATIM — everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`, INCLUDING the nested invariants region.
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms / pure / pre-/post-conditions regions + the signature). same_spec is
# computed over the spec_view, which elides every impl region (and the nested
# invariants), so swapping inside here is guaranteed same_spec.
_IMPL = """\
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        # `found` tracks membership over the suffix already scanned.
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 1, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-reorder-decision: structurally-different but CORRECT. Keeps the gold
# backward scan and EVERY gold proof obligation VERBATIM (the same loop bound, the
# same three invariants, the same two per-step drop() framing asserts) — only the
# FINAL DECISION is reshaped from `if not (found and choice): raise; return` into
# the equivalent positive form `if found and choice: return; raise`. Same
# behaviour (return-normally iff found and choice_permitted), different executable
# shape; the gold loop proof stays valid (no loop-direction flip, no dropped
# framing assert). If it fails => SPEC-TOO-STRONG (a faithful correct impl rejected).
_POS_REORDER = """\
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        # `found` tracks membership over the suffix already scanned.
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    # Reshaped decision (positive form), behaviourally identical to the gold's
    # `if not (found and choice_permitted(value)): raise; return`.
    if found and choice_permitted(value):
        return
    raise ReferenceInvalid()
"""

# admiss-reads: an admissibility positive control. The non-trivial precondition is
# the pair of half-permissions Acc(list_pred(complete_rows),1/2) /
# Acc(list_pred(curated_rows),1/2). This control confirms the spec ADMITS the
# reads a normal F2P-shaped input needs: it reads len() of BOTH collections and
# asserts the reads succeed under the half-permissions before running the gold
# body. If the precondition rejected a legitimate normal input => PRECOND-TOO-
# STRONG. No write, so no permission demand beyond the spec and no proof gap.
_ADMISS = """\
    # Admissibility: a normal pair of (possibly empty) collections is in-domain;
    # the half-permissions admit reading both lengths.
    Assert(len(complete_rows) >= 0)
    Assert(len(curated_rows) >= 0)
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        Assert(complete_rows[i - 1] == complete_rows[i - 1])  # read admitted at 1/2
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
"""


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVALS (MANDATORY — BOTH inputs are Acc(...,1/2) read-only).
# Each keeps the gold body VERBATIM so the rejection is attributable SOLELY to the
# added write; each must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-complete: WRITE BACK into the read-only base-manager collection
# (complete_rows[0] = complete_rows[0], a no-op STORE). It demands FULL write
# permission on complete_rows, which the caller granted only at 1/2. The verifier
# must reject for insufficient permission.
_FRAME_COMPLETE = """\
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if len(complete_rows) > 0:
        # Frame violation: write back into the read-only (Acc(...,1/2)) input.
        complete_rows[0] = complete_rows[0]
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
"""

# frame-mut-curated: WRITE BACK into the read-only DEFAULT-manager collection
# (curated_rows[0] = curated_rows[0]). curated_rows is also Acc(...,1/2); the
# store demands full permission not granted. Reject for insufficient permission.
# (curated_rows is the collection the spec deliberately keeps OUT of the decision,
# so an attacker who reasons "I'm allowed to touch curated_rows" is wrong — it is
# read-only too.)
_FRAME_CURATED = """\
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if len(curated_rows) > 0:
        # Frame violation: write back into the read-only (Acc(...,1/2)) input.
        curated_rows[0] = curated_rows[0]
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly and changes only the function impl region.
# ---------------------------------------------------------------------------

# weak-curated-bug: THE ACTUAL PRE-PATCH BUG (model_prepatch.py reborn) — the check
# decides over the CURATED default collection instead of the COMPLETE base
# collection. The scan + membership fold + invariants are rewritten over
# `curated_rows` (internally self-consistent, so the loop verifies), but the final
# `found` then tracks membership over curated_rows. Q3/Q4 are pinned over
# complete_rows; on the discriminating witness (a key in complete_rows but hidden
# from curated_rows, and choice-permitted) this impl RAISES while Q3 requires
# normal return (or, equivalently, the Exsures clause `not reference_holds(value,
# complete_rows)` is FALSE on that raise). Must be rejected.
_WEAK_CURATED = """\
    found = False  # type: bool
    i = len(curated_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(curated_rows), 1 / 2))
        Invariant(0 <= i and i <= len(curated_rows))
        Invariant(found == present(value, ToSeq(curated_rows).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(curated_rows).drop(i - 1)[0] == curated_rows[i - 1])
        Assert(ToSeq(curated_rows).drop(i - 1).drop(1) == ToSeq(curated_rows).drop(i))
        if curated_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
"""

# weak-skip-head: PARTIAL-DOMAIN / off-by-one. Scans complete_rows but STOPS at
# i=1, never inspecting index 0. `found` then tracks membership over
# complete_rows.drop(1) (every row except the first). Correct for every value not
# uniquely at index 0, but on a value that is stored ONLY at index 0 (and choice-
# permitted) it RAISES while Q3 demands return (Q4's `not reference_holds` is
# false on the raise). Targets the stored row that fails first (the head element).
_WEAK_SKIP_HEAD = """\
    found = False  # type: bool
    i = len(complete_rows)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(1 <= i and i <= len(complete_rows))
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
"""

# weak-ignore-choice: drops the choice_permitted conjunct — decides on membership
# alone. Returns normally whenever `found` (i.e. present(value, complete_rows)) is
# true, regardless of choice_permitted(value). Q3 requires reference_holds =
# present AND choice_permitted; on the return path the proof has `present` but
# CANNOT establish choice_permitted(value) (it is @ContractOnly/opaque), so Q3
# fails. Must be rejected — this is why the axiom is consumed as the SECOND
# conjunct (mapping.md §3.1) rather than membership alone.
_WEAK_IGNORE_CHOICE = """\
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if not found:
        raise ReferenceInvalid()
    return
"""

# weak-always-return: the cheapest "forgot to do the work" baseline that never
# rejects — always accept the reference. Returns normally even when no stored row
# carries the key. Rejected by Q3: on a value absent from complete_rows,
# reference_holds is false but the impl returns. Cheap supporting near-miss with a
# real refinement (a check that never raises admits dangling references).
_WEAK_ALWAYS_RETURN = """\
    # Never reject: accept every reference without consulting any collection.
    return
"""

# weak-always-raise: the cheapest "forgot to do the work" baseline that always
# rejects — reject every reference. Rejected by the Exsures clause Q4: on a value
# present in complete_rows AND choice-permitted, `not reference_holds(value,
# complete_rows)` is FALSE, so raising violates the Exsures. Cheap supporting
# near-miss with a real refinement (a check that always raises rejects every
# valid reference, failing every accept-expecting F2P/P2P).
_WEAK_ALWAYS_RAISE = """\
    # Always reject: raise without consulting any collection.
    raise ReferenceInvalid()
"""


SPEC_TESTS = [
    {
        "id": "pos-reorder-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but CORRECT: identical gold backward scan and "
            "every gold proof obligation kept verbatim (loop bound, three "
            "invariants, two per-step drop() framing asserts); only the final "
            "decision is reshaped into the equivalent positive form "
            "`if found and choice_permitted: return; raise`. Same return/raise "
            "behaviour. If it fails => SPEC-TOO-STRONG (a faithful correct impl "
            "rejected for a non-spec reason)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition is the pair of half-permissions Acc(list_pred("
            "complete_rows),1/2) / Acc(list_pred(curated_rows),1/2). This control "
            "asserts len(complete_rows)>=0, len(curated_rows)>=0 and re-reads each "
            "scanned element under the half-permission before the gold body, "
            "confirming a normal F2P-shaped input is in-domain. If it fails => "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-complete",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_COMPLETE),
        "refinement": (
            "the gold patch reads the base-manager queryset and consults it; it "
            "NEVER writes back into the related model's row collection. A faithful "
            "real patch that mutated the queried rows (an in-place edit of the "
            "stored data during a read-only validation) would corrupt the related "
            "model's state and diverge from the gold's read-only check — it would "
            "not be the gold patch and would not faithfully resolve. The store "
            "here is a no-op only by coincidence; the spec must forbid ANY write."
        ),
        "rationale": (
            "REJECTED by the permission system: complete_rows is granted at "
            "Acc(...,1/2) (P1); the store complete_rows[0]=complete_rows[0] demands "
            "FULL write permission, unavailable, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold scan/decision is kept verbatim so "
            "the rejection is attributable solely to the write. If it verifies => "
            "the read-only frame is not enforced (frame-mutation, #1 weakness "
            "class)."
        ),
    },
    {
        "id": "frame-mut-curated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_CURATED),
        "refinement": (
            "the gold patch reads neither manager's rows for WRITING; curated_rows "
            "(the default-manager queryset) is consulted in the BUGGY prepatch and "
            "ignored by the fix, never written. A faithful real patch that wrote "
            "into the default-manager rows during validation would mutate stored "
            "state and diverge from the gold read-only check — not the gold patch, "
            "does NOT resolve. Important: the spec keeps curated_rows OUT of the "
            "decision, but it is STILL read-only — an attacker may not 'use up' "
            "its permission with a write."
        ),
        "rationale": (
            "REJECTED by the permission system: curated_rows is granted at "
            "Acc(...,1/2) (P2); the store curated_rows[0]=curated_rows[0] demands "
            "FULL write permission, unavailable => INSUFFICIENT PERMISSION. The "
            "gold body is kept verbatim so the rejection is attributable to the "
            "write. If it verifies => the second read-only input's frame is not "
            "enforced."
        ),
    },
    {
        "id": "weak-curated-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CURATED),
        "refinement": (
            "this is EXACTLY the pre-patch behaviour (model_prepatch.py): the check "
            "consults `_default_manager` (curated_rows) instead of `_base_manager` "
            "(complete_rows). Its faithful real patch IS the unpatched repo, which "
            "raises ValidationError for an archived-but-stored, choice-permitted "
            "row hidden by the default manager — failing the F2P tests "
            "test_FK_validates_using_base_manager and "
            "test_validate_foreign_key_to_model_with_overridden_manager, which "
            "assert that such a reference is VALID. Does NOT resolve (G-DIFF: the "
            "spec's whole purpose is sensing this base-vs-default manager choice)."
        ),
        "rationale": (
            "REJECTED by Q3 / Q4 over complete_rows: the loop is rewritten over "
            "curated_rows (self-consistent invariants => the loop itself verifies), "
            "so `found` tracks membership over curated_rows. On the discriminating "
            "witness (value in complete_rows, hidden from curated_rows, choice-"
            "permitted) the impl raises, but reference_holds(value, complete_rows) "
            "is TRUE, so the Exsures clause `not reference_holds(...)` is FALSE "
            "(and Q3 on the dual case is unmet). No spec relation ties found-over-"
            "curated to membership-over-complete. If it verifies => SPEC-TOO-WEAK "
            "(the curated narrowing would be allowed to influence the decision)."
        ),
    },
    {
        "id": "weak-skip-head",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SKIP_HEAD),
        "refinement": (
            "an off-by-one real patch whose base-manager membership test skipped "
            "the first row of the queryset would reject a reference whose only "
            "stored row sorts to that head position — failing the accept-expecting "
            "F2P on that input class while passing on every other. A true "
            "PARTIAL-DOMAIN break (the stored row that fails first), not a blanket "
            "wrong impl. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 / Q4 over complete_rows: the loop stops at i=1 so "
            "`found` tracks membership over complete_rows.drop(1). On a value "
            "present ONLY at index 0 and choice-permitted, found is false => the "
            "impl raises, but reference_holds(value, complete_rows) is TRUE, so the "
            "Exsures clause `not reference_holds(...)` is FALSE. If it verifies => "
            "SPEC-TOO-WEAK on the head sub-domain (the row the scan inspects last)."
        ),
    },
    {
        "id": "weak-ignore-choice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_CHOICE),
        "refinement": (
            "a real patch that switched to _base_manager but DROPPED the "
            "`complex_filter(get_limit_choices_to())` narrowing would accept a "
            "stored row that violates the field's limit_choices_to restriction — a "
            "reference the gold rejects. P2P tests exercising limit_choices_to "
            "(e.g. the model_forms limit-choices fixtures) would fail. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (reference_holds = present AND choice_permitted): on "
            "the return path the proof establishes `present(value, complete_rows)` "
            "but CANNOT establish choice_permitted(value) (it is @Pure "
            "@ContractOnly / opaque, Ensures(True), no value claim), so the second "
            "conjunct of reference_holds is unprovable and Q3 fails. This is why "
            "choice_permitted is consumed as the SECOND conjunct (mapping.md §3.1). "
            "If it verifies => SPEC-TOO-WEAK (limit_choices_to unpinned)."
        ),
    },
    {
        "id": "weak-always-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_RETURN),
        "refinement": (
            "a real patch whose validate() always returned (never raised) would "
            "accept references to rows that are NOT stored at all — a dangling FK — "
            "failing the accept/reject contract the F2P+P2P validation tests pin "
            "(e.g. an absent key must raise ValidationError). Does NOT resolve. "
            "Cheap supporting baseline with a genuine refinement."
        ),
        "rationale": (
            "REJECTED by Q3 (reference_holds(value, ToSeq(complete_rows))): on a "
            "value absent from complete_rows, reference_holds is FALSE, yet the "
            "impl returns normally, so Q3 is violated. If it verifies => "
            "SPEC-TOO-WEAK (the no-raise condition would not be pinned)."
        ),
    },
    {
        "id": "weak-always-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_RAISE),
        "refinement": (
            "a real patch whose validate() always raised would reject EVERY "
            "reference, failing every accept-expecting test (the F2P archived-row "
            "validation and every P2P form whose FK points at a genuinely-stored "
            "row). Does NOT resolve. Cheap supporting baseline with a genuine "
            "refinement."
        ),
        "rationale": (
            "REJECTED by the Exsures clause Q4 (`not reference_holds(value, "
            "ToSeq(complete_rows))`): on a value present in complete_rows AND "
            "choice-permitted, reference_holds is TRUE so `not reference_holds` is "
            "FALSE, and raising violates the Exsures. If it verifies => "
            "SPEC-TOO-WEAK (the must-raise condition would not be pinned)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — the A-reference deep model (base-vs-default manager) + the
# A-consumed choice_permitted axiom, validated against the REAL Django callees in
# the instance image with the gold patch applied.
# ---------------------------------------------------------------------------
#
# Why these two cases (and not more): choice_permitted carries Ensures(True), the
# WEAKEST contract — axiom-soundness is vacuously satisfied (no real callee output
# can violate `True`) and axiom-containment is trivial (the axiom's domain is all
# ints; the caller only ever passes the int `value`). So the load-bearing
# obligation is the A-REFERENCE deep model: that complete_rows really IS the
# base-manager key set and the post-patch check decides over it. We embed the
# bundle's own axiom_check.py (read on the HOST at load time — it is NOT mounted
# in-container, per pilot bug #6) so the probe drives the REAL ForeignKey.validate
# and the REAL managers, asserting:
#   * base manager exposes EVERY stored row (== complete_rows);
#   * default manager is a STRICT, non-empty subset (curated_rows < complete_rows);
#   * the archived witness (in base, hidden by default) is in complete_rows and an
#     absent key is in neither => the discriminating witness class is realizable;
#   * the real validate accepts a live key and rejects an absent key;
#   * choice_permitted (limit_choices_to) is empty + deterministic across managers.
# It opens no files (no codec issue, pilot bug #5) and imports only Django + stdlib.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

AXIOM_TESTS = [
    {
        "id": "ax-ref-manager-subset",
        "axiom": "present / complete-vs-curated collection (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": (
            "the A-reference deep model — complete_rows == the base-manager key "
            "set and the post-patch check decides membership over it — must equal "
            "the REAL Django managers. The embedded axiom_check.py drives the real "
            "ForeignKey.validate / _base_manager / _default_manager (gold applied): "
            "base manager exposes every stored row, default manager is a strict "
            "subset, the archived witness is in base but hidden by default, an "
            "absent key is rejected and a live key accepted, choice_permitted "
            "(empty limit_choices_to) is deterministic across managers. Exit 0 iff "
            "the deep model matches reality; rc!=0 => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-choice-permitted",
        "axiom": "choice_permitted",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "# choice_permitted(key: int) has domain = all ints (Ensures(True), no\n"
            "# value claim). The caller validate_reference only ever passes the int\n"
            "# `value` to choice_permitted (mapping.md A5/§3.1). Containment check:\n"
            "# every int the caller can reach lies in the axiom's int domain. We\n"
            "# enumerate boundary + sentinel + fuzzed ints the caller could pass and\n"
            "# assert each is an int (the axiom's whole Requires domain) — there is\n"
            "# no reachable caller input OUTSIDE it, so the axiom is not\n"
            "# too-weak-for-caller. (Covering MORE than the caller reaches would be\n"
            "# sound anyway, per the float-vs-int rule; here domain == reachable.)\n"
            "import random\n"
            "vals = [0, 1, -1, 2, -2, 2**31, -(2**31), 2**63, -(2**63), 10**18]\n"
            "for _ in range(200):\n"
            "    vals.append(random.randint(-(2**40), 2**40))\n"
            "bad = [v for v in vals if not isinstance(v, int)]\n"
            "if bad:\n"
            "    print('AXIOM-TOO-WEAK-FOR-CALLER: reachable non-int input %r' % (bad[:5],))\n"
            "    sys.exit(1)\n"
            "print('CONTAINMENT OK: all %d caller-reachable values are ints, inside '\n"
            "      'choice_permitted domain (all ints); no input escapes the axiom '\n"
            "      'Requires.' % (len(vals),))\n"
            "sys.exit(0)\n"
        ),
        "rationale": (
            "choice_permitted's Requires domain is all ints; the caller only ever "
            "passes the int `value` (mapping.md A5). Every caller-reachable input "
            "lies inside the axiom's domain => not AXIOM-TOO-WEAK-FOR-CALLER. A "
            "reachable input outside the int domain (impossible here, since `value` "
            "is typed int) would be the only defect. Self-contained, stdlib only, "
            "exit 0 iff covered."
        ),
    },
]
