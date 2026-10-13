"""properties.py — G-PBT falsification battery for django__django-15695 (velvet).

NOT a Velvet module; a record of adversarially-reasoned cases the G-PBT gate
executes and stamps. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the elided
``prove_correct`` tactic body, is changed — both regions the consumer spec view
elides, so ``markers.same_spec`` holds and the ``prove_correct relabelSchedule``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  relabelSchedule (beforeId : Int) (afterId : Int) return (out : List Int)
    ensures beforeId = afterId → out = []
    ensures beforeId ≠ afterId → out ≠ []

The method decides the schedule of store-mutation work a relabeling emits,
driven entirely by whether the stored identifier actually changes. The two
`ensures` clauses pin ONE observable — the zero-vs-nonzero length of the emitted
schedule — in BOTH directions:

  * (E) the EMPTY clause  `beforeId = afterId → out = []`: when the before- and
        after- identifiers coincide the relabeling is inert and MUST emit an
        empty schedule (so re-applying a relabeling that changes nothing is
        harmless rather than a fault).
  * (N) the NON-EMPTY clause `beforeId ≠ afterId → out ≠ []`: when the two
        identifiers differ the relabeling MUST proceed and emit at least one
        store-mutation operation. The exact count and order of the emitted
        operations is NOT pinned — only that the schedule is non-empty.

Both INPUT binders are free (the pre-conditions region is empty) and the
post-image must hold for EVERY value of each:
  * ``beforeId`` — the identifier carried before the relabeling.
  * ``afterId``  — the identifier carried after the relabeling.
Only the EQUALITY of the two is observable (both are `Int` identities); the
decision forks on `beforeId = afterId`, so a rival is refutable by any input
pair whose equality it mishandles.

ADVERSARIAL READ of the classes (the sibling nagini battery is the design; the
footer accounts for each of its cases):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling grants FULL
    write permission on the touched objects and closes a RESETTABLE-WITNESS
    cheat (write an observability flag, then reset it) plus a DIRECT-WRITE
    bypass (satisfy the final-name pin without issuing the observable effect).
    Both rely on a MUTABLE heap with a separate "was the effect issued" flag
    distinct from the final state. This backend is referentially transparent:
    the method declares no `mut` binder, there is no heap, and the SOLE
    observable is the returned schedule value — there is no separate flag to
    reset and no distinct "final name" state to write behind the spec's back.
    Both cheats therefore have no counterpart here; reported as omissions
    (footer), not fabricated.
  * TERMINATION / NON-TERMINATION — VACUOUS on this backend because the CARRIER
    ALREADY REFUSES DIVERGENCE, and MEASURED so by the audit. (An earlier
    revision of this file asserted the bundle runs under
    `loom.semantics.termination "partial"`. That was FALSE — `Solution.lean`
    line 4 sets `"total"` — and it is the opposite premise, so the disposition
    is re-derived here from the setting the bundle actually carries.) The
    sibling carries a `MustTerminate` obligation and rejects a diverging
    (`while True`) path plus an unbounded self-recursion, closing the audited
    G-PANEL-1 totality weakness. Under `"total"` the verifier discharges a
    termination obligation itself, so a diverging rival is rejected WITHOUT any
    spec reasoning: the audit built the differing-branch loop rival
    (`while true do i := i + 1` in place of the emit) and it is rejected at
    ELABORATION with `error: Decreasing annotations are required in total
    correctness semantics` (exit 1); a bounded-looking `while i < 1 do i := i`
    variant is rejected identically. That is why the class is not shippable as
    a reject case here rather than merely hard: a reject case must carry a
    witness that ELABORATES against the rival, and the audit built exactly that
    witness at both an equal (`5 5`) and a differing (`1 2`) input against the
    diverging rival — BOTH fail (exit 1) with the same decreasing-annotations
    error, because the rival's own file never elaborates, so no witness can ever
    hold of it. The class is therefore closed by the carrier upstream of the
    spec, and the sharper shape is refused too: a loop CARRYING a measure that does
    not decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q``, body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``, so the refusal is not merely a
    linter complaint about a missing annotation. (An earlier version of this passage
    contrasted the ``partial`` bundles in an internal findings doc "where a diverging
    rival VERIFIES and the class is a genuine spec hole". There are none: all 500
    velvet bundles set ``"total"`` and open ``TotalCorrectness``.) Recorded
    as vacuous WITH that demonstration, not as "no probe is possible", and NOT
    as a spec hole — there is nothing here for the spec to admit.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is stated directly over the
    method's own inputs (`beforeId = afterId`) and its own output (`out`); the
    `axioms` region is empty and `applyOp` is a concrete `def` marker, so there
    is no opaque answer key to echo. The honest controls are the cheapest
    faithful reshapes (the `pos-*` cases).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    single behavioural fork (inert-vs-proceed) is exactly the empty-vs-non-empty
    schedule, which IS the returned value, so both directions are fully
    observable to the ensures. The always-emit / always-inert rivals are its
    discriminators.
  * PARTIAL-DOMAIN — exercised. A rival can be correct on part of the domain and
    wrong on a sub-domain: the ordering rival proceeds only when
    `beforeId < afterId`, so it is correct on the equal case and on the
    `before < after` differing case but WRONG on the `before > after` differing
    case — refuted at exactly that sub-domain, distinct from the always-inert
    rival which is wrong on the whole differing domain.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE: its
extracted program reduces fully under `decide`. Each reject rival carries a
machine-checked refutation `witness` — a Velvet tester statement
`relabelScheduleTester <beforeId> <afterId> = false` at ONE concrete input,
checked in a file whose `prove_correct` block has been stripped so no tactic
script can mask the verdict (the return carrier `List Int` already has
`DecidableEq`, so no instance is derived and no `axiom`/`sorry`/`native_decide`
is involved). Both halves were checked out-of-band with `scripts/lean_verify.sh`:
every witness ELABORATES against its rival and FAILS (`decide` proves the
proposition false) against the frozen solution, so each rejection is a genuine
spec refutation and not mechanical tactic breakage.

INDEPENDENTLY RE-DERIVED by a later audit, which rebuilt all six builds itself
and read gold's failure text: for all three rivals the rival build is exit 0 and
the gold build is exit 1 with ``Tactic `decide` proved that the proposition
relabelScheduleTester <the concrete input> = false is false`` — a SEMANTIC
refutation of the concrete claim, never a missing identifier, type error,
unfolding failure or timeout. The audit also ran the FORGERY pair on each case
(flip the claim to `= true`, rebuild both sides): gold then VERIFIES (exit 0) and
the RIVAL fails (exit 1) with the mirror-image `decide` error, so the exit codes
invert exactly when the claim inverts and each gold-side code demonstrably
carries information ABOUT THE CLAIM. None of these cases is hollow. No witness
binds a hypothesis (all three state their refutation at literal inputs), so the
gate's consistency probe is `None` and there is no joint-satisfiability
obligation to discharge.

AUDIT PROBES beyond the shipped cases (attacks D and E; none is a spec finding,
recorded so a later reader need not re-spend the builds):
  * SPEC-TOO-WEAK (D) — four NEW wrong rivals aimed where the shipped three do
    not reach, all correctly REJECTED (exit 1, `unsolved goals` on the ensures):
    a guard on `natAbs` equality (collapses sign, so it stays inert at
    (-1,1) where the relabeling must proceed); a guard on `% 2` residue
    equality; a rival correct except that it ALSO goes inert on the differing
    pair when `beforeId = 0`; and a rival that inverts the outcome only at the
    equal pair (0,0). The `% 2` and `natAbs` rivals are the interesting ones —
    both agree with gold on the whole EQUAL sub-domain and fail only on a
    proper subset of the differing one, i.e. they are strictly nearer misses
    than always-inert — and the spec still rejects both. No spec hole found.
  * SPEC-TOO-STRONG (E) — three NEW correct reshapes, all VERIFY (exit 0) on the
    frozen `loom_solve`: the guard written symmetrically (`afterId = beforeId`),
    the guard written as `beforeId - afterId = 0`, and the whole decision
    collapsed into a single `return (if beforeId = afterId then [] else
    [applyOp])`. A fourth confirms the mapping.md A3 abstraction is really
    unpinned in the CONTENT axis as claimed, not just the count axis: emitting
    `[applyOp + 41]` verifies (exit 0), so clause (N) consumes only
    non-emptiness. No soundness hole found.

AXIOM lane: EMPTY. `meta.json` declares no consumed `axiom` and no deep-model
reference; the changed decision is modeled DEEPLY (the equality guard) and the
resolution callees are unchanged and never A-consumed (mapping.md §3). Nothing
in the proof rests on an axiom, and this gate ignores `AXIOM_TESTS` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15695"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region, verbatim — from `-- impl-start` through the body up to
# (and including) `-- impl-end`. Every rival and reshape edits ONLY this block
# (and, for reshapes/admissibility, the elided `prove_correct` tactic body), so
# the spec view is untouched and same_spec holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.\n"
    "    if beforeId = afterId then\n"
    "      return []\n"
    "    else\n"
    "      -- The relabeling proceeds: emit the store-mutation work (one unit here;\n"
    "      -- the spec consumes only its non-emptiness).\n"
    "      return [applyOp]\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct relabelSchedule by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `relabelScheduleTester <beforeId> <afterId> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. The `List Int`
# ---- return carrier already has DecidableEq, so nothing is derived or assumed.
_TESTER = (
    "extract_program_for relabelSchedule\n"
    "prove_precondition_decidable_for relabelSchedule\n"
    "prove_postcondition_decidable_for relabelSchedule\n"
    "derive_tester_for relabelSchedule\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the empty-vs-non-empty outcome
    # identical on every input and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: pivot the guard on the DIFFERING case and swap the two arms
        # (proceed first). Same outcome on every input — `beforeId ≠ afterId`
        # takes the proceed arm exactly where `beforeId = afterId` took the inert
        # arm — so both ensures clauses still hold. Proof retuned to the frozen
        # `loom_solve` (the do-block only reordered; the decision is unchanged).
        "module": _impl_reproved(
            "    if beforeId ≠ afterId then\n"
            "      return [applyOp]\n"
            "    else\n"
            "      return []",
            "prove_correct relabelSchedule by\n  loom_solve"),
        "rationale": "pivoting the guard on the differing case and swapping the "
                     "arms computes the SAME schedule on every input (proceed "
                     "exactly when `beforeId ≠ afterId`, inert exactly when "
                     "`beforeId = afterId`), so both ensures clauses (E) and (N) "
                     "still hold; a correct reshape MUST verify, else "
                     "SPEC-TOO-STRONG on branch order.",
    },
    {
        "id": "pos-multi-op-schedule",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: on the proceeding branch emit a schedule of TWO operations
        # instead of one. The spec pins only NON-EMPTINESS on that branch (the
        # count/order is deliberately unpinned — mapping.md A3, a many-to-one
        # abstraction), so a longer schedule is still correct. Verifies that the
        # spec is not accidentally over-strong on the emitted count.
        "module": _impl(
            "    if beforeId = afterId then\n"
            "      return []\n"
            "    else\n"
            "      return [applyOp, applyOp]"),
        "rationale": "the proceeding branch's clause (N) demands only `out ≠ []`, "
                     "not a specific length or content, so emitting a two-element "
                     "schedule still satisfies it while the inert branch is "
                     "unchanged; a correct impl that emits more than one unit MUST "
                     "verify, else the spec would be SPEC-TOO-STRONG on the "
                     "emitted count (which the carrier deliberately leaves free).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # analogue on a TOTAL-domain carrier is the OBLIGATION being unsatisfiable
    # at exactly an F2P-shaped input: this case discharges BOTH ensures clauses
    # at concrete inputs, BY EVALUATION, as an in-region assert, before closing
    # the frozen obligation verbatim.
    #
    # AUDIT NOTE — this case replaces a HOLLOW predecessor. The shipped version
    # asserted `((7 : Int) = 7) ∧ ((3 : Int) ≠ 4)`: a CLOSED arithmetic
    # tautology mentioning neither the method's binders, its output, nor either
    # ensures clause. Measured: replacing that whole assert with
    # `assert (with_name_prefix `assert (True))` verifies identically (exit 0),
    # so the assert carried NO information about the spec and the case tested
    # nothing while passing honestly. The `7 = 7` / `3 ≠ 4` literals also do not
    # exercise the guard — they are constants the guard never sees, so the
    # "the guard genuinely forks" claim in its rationale was not demonstrated
    # by what it asserted.
    #
    # The replacement asserts the two SCHEDULE outcomes the ensures clauses
    # demand, at the two F2P-shaped input pairs, over the decision's own
    # computable projection:
    #   (E) at an EQUAL pair  (7,7): the emitted schedule is `[]`;
    #   (N) at a DIFFERING pair (7,8): the emitted schedule is `≠ []`.
    # Both track their claims, which the audit established by flipping each in
    # turn: claiming the equal-pair schedule is NON-empty fails (exit 1,
    # `unsolved goals`), and claiming the differing-pair schedule IS empty fails
    # (exit 1, `unsolved goals`), while the conjunction as written verifies
    # (exit 0). So an obligation unsatisfiable at either F2P-shaped input would
    # break this case, which is exactly the PRECOND-TOO-STRONG direction the
    # lane exists to test. The impl tail is the frozen body verbatim and the
    # proof stays `loom_solve`, so the method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-guard-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- The obligation is SATISFIABLE at the F2P-shaped inputs: the\n"
            "    -- schedule the decision emits at an EQUAL pair is empty (clause E)\n"
            "    -- and at a DIFFERING pair is non-empty (clause N). By evaluation.\n"
            "    assert (with_name_prefix `assert\n"
            "      (((if ((7 : Int) = 7) then ([] : List Int) else [applyOp]) = [])\n"
            "        ∧ ((if ((7 : Int) = 8) then ([] : List Int) else [applyOp]) ≠ [])))\n"
            "    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.\n"
            "    if beforeId = afterId then\n"
            "      return []\n"
            "    else\n"
            "      -- The relabeling proceeds: emit the store-mutation work (one unit here;\n"
            "      -- the spec consumes only its non-emptiness).\n"
            "      return [applyOp]"),
        "rationale": "ADMISSIBILITY (the PRECOND-TOO-STRONG direction on a total "
                     "carrier): the post-image is SATISFIABLE at exactly the "
                     "F2P-shaped inputs, discharged by evaluation as an in-region "
                     "assert before the frozen obligation closes verbatim. Clause "
                     "(E) is instantiated at an EQUAL pair (7,7) — the emitted "
                     "schedule evaluates to `[]`, which is what (E) demands — and "
                     "clause (N) at a DIFFERING pair (7,8) — it evaluates to "
                     "`[applyOp] ≠ []`, which is what (N) demands. Both branches are "
                     "therefore LIVE and neither ensures clause is vacuous: the "
                     "decision genuinely forks on the equality. If either "
                     "instantiation could not discharge, the obligation would be "
                     "unsatisfiable at a normal input => PRECOND-TOO-STRONG. Unlike "
                     "a closed tautology over constants, each conjunct tracks its "
                     "claim: flipping either one (equal-pair non-empty, or "
                     "differing-pair empty) fails to elaborate.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-always-proceed",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: emit the store-mutation work UNCONDITIONALLY,
        # with no guard on identifier identity. This is Solution_prepatch.lean.
        "module": _impl("    return [applyOp]"),
        "refinement": "emitting the store-mutation work unconditionally IS the "
                      "pre-patch behaviour: the relabeling always proceeds, even "
                      "when the identifier is unchanged. The F2P re-applies the "
                      "relabeling onto an already-relabeled store (identifier "
                      "unchanged) and asserts it is a no-op; the unconditional "
                      "emit asks the backing store to re-apply a change to an "
                      "identifier already in use, which crashes (on PostgreSQL: "
                      "the target relation already exists). It would NOT resolve — "
                      "the precise defect the guard fixes (G-DIFF).",
        "rationale": "REJECT from the EMPTY clause (E): when `beforeId = afterId` "
                     "the post-image demands `out = []`, but the rival emits "
                     "`[applyOp]` (non-empty). Refuted at an equal input pair "
                     "(`beforeId = afterId`), the sub-domain where clause (E) "
                     "binds and every proceeding rival is instead correct. If it "
                     "verified => SPEC-TOO-WEAK (admits the prepatch bug).",
        "witness": _witness("relabelScheduleTester 5 5"),
    },
    {
        "id": "weak-always-inert",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: NEVER emit any store-mutation work (always inert). Correct on
        # the equal sub-domain (inert is right there), but on the differing
        # sub-domain it emits nothing where the relabeling must proceed.
        "module": _impl("    return []"),
        "refinement": "always staying inert is what a patch that dropped the "
                      "store-mutation call entirely would do: it never performs "
                      "the relabeling on the backing store, so any genuine "
                      "identifier change leaves the store under its old "
                      "identifier. The forward relabeling tests (F2P/P2P) that "
                      "assert the store carries the NEW identifier would fail — it "
                      "would NOT resolve.",
        "rationale": "REJECT from the NON-EMPTY clause (N): when "
                     "`beforeId ≠ afterId` the post-image demands `out ≠ []`, but "
                     "the rival emits `[]`. Refuted at a differing input pair "
                     "(`beforeId ≠ afterId`) with `beforeId < afterId`, varying "
                     "both binders against the equal-case witness. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _witness("relabelScheduleTester 1 2"),
    },
    {
        "id": "weak-ordering-partial",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN near-miss: proceed only when the identifier STRICTLY
        # INCREASES (beforeId < afterId), stay inert otherwise. Correct on the
        # equal case (inert) AND on the increasing differing case (proceeds), but
        # WRONG on the decreasing differing case (beforeId > afterId): it stays
        # inert where the relabeling must proceed. Agrees with gold over more of
        # the domain than the always-inert rival, so it carries its OWN
        # separating witness at the decreasing sub-domain.
        "module": _impl(
            "    if beforeId < afterId then\n"
            "      return [applyOp]\n"
            "    else\n"
            "      return []"),
        "refinement": "gating the relabeling on a strict ORDERING of the "
                      "identifiers (proceed only when the value increases) is what "
                      "a patch that replaced the identity guard with an inequality "
                      "would do. It performs the relabeling for only half of the "
                      "genuine identifier changes and skips it for the other half "
                      "(any change that decreases the identifier), leaving the "
                      "store under its old identifier there. The relabeling tests "
                      "that change an identifier in the skipped direction would "
                      "fail — it would NOT resolve.",
        "rationale": "REJECT from the NON-EMPTY clause (N): the decision must fork "
                     "on `beforeId = afterId` alone, but the rival forks on "
                     "`beforeId < afterId`, so on a differing pair with "
                     "`beforeId > afterId` it stays inert (`out = []`) where the "
                     "post-image demands `out ≠ []`. PARTIAL-DOMAIN: correct on "
                     "the equal and increasing sub-domains, wrong on the "
                     "decreasing one. Refuted at a decreasing differing pair "
                     "(`beforeId > afterId`) — the exact sub-domain where it is "
                     "wrong and the always-inert rival's witness would not "
                     "distinguish it. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("relabelScheduleTester 2 1"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness). The sibling contracts TWO functions
# (the decision step + a deep-model callee whose Requires(before != after)
# carries much of its strength) over a MUTABLE heap with FULL write permission
# and a `MustTerminate` totality obligation. This backend narrows the carrier to
# the SINGLE purely-functional core: the decision "emit iff the identifiers
# differ", modeled STRAIGHT-LINE over two read-only `Int`s under partial
# termination, with the sole observable being the empty-vs-non-empty schedule
# value. Most of the sibling's strength surface (the callee precondition, the
# mutable observability flag, the loop, the termination obligation) does not
# exist on this carrier. Every sibling case is accounted for below.
#
#   sibling case                 -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-control-reorder          -> pos-branch-reorder            PORTED
#   admiss-fshaped-reapply       -> admiss-guard-nondegenerate    RE-AIMED
#   weak-unconditional-rename    -> weak-always-proceed           PORTED (= prepatch)
#   weak-resettable-witness      -> (none)                        VACUOUS
#   weak-direct-write-no-issue   -> (none)                        VACUOUS
#   partial-domain-always-noop   -> weak-always-inert             PORTED
#   nonterm-differ-branch-loop   -> (none)                        VACUOUS
#   nonterm-self-recursion       -> (none)                        VACUOUS
#   (no sibling)                 -> pos-multi-op-schedule         ADDED (2nd pos.)
#   (no sibling)                 -> weak-ordering-partial         ADDED (binder cov.)
#
# 3 ported, 1 re-aimed, 4 vacuous; 1 extra positive + 1 binder-coverage rival
# added. Total: 2 soundness + 1 admissibility + 3 uniqueness = 6 cases.
#
# VACUOUS (weak-resettable-witness): the sibling calls the backend primitive
#   unconditionally, then on the equal-names branch RESETS a heap observability
#   flag so the post-state iff appears to hold; it is rejected because the
#   unconditional call violates the callee's Requires(old != new) BEFORE the
#   reset. This backend has no mutable heap and no separate observability flag:
#   the sole observable is the returned schedule value, which cannot be "issued
#   then reset". There is no callee precondition to violate either (the decision
#   is modeled deeply, not delegated). The cheat has no counterpart; not
#   fabricated.
# VACUOUS (weak-direct-write-no-issue): the sibling satisfies the final-name pin
#   by writing the index name DIRECTLY while never issuing the observable rename,
#   separating "final name" from "observable effect". This backend's spec pins
#   ONLY the schedule's emptiness — there is no distinct "final name" state to
#   write behind the spec's back, so the distinction the rival exploits collapses
#   on this carrier. No counterpart; not fabricated.
# VACUOUS (nonterm-differ-branch-loop, nonterm-self-recursion): the sibling
#   carries a `MustTerminate(2)` obligation and rejects a diverging `while True`
#   and a bare self-recursion, closing the audited G-PANEL-1 totality weakness.
#   This bundle sets `loom.semantics.termination "total"` (Solution.lean line 4 —
#   an earlier revision of this file said "partial", which was false and is the
#   INVERSE premise; the disposition below is re-derived from the real setting).
#   Under `"total"` the verifier discharges the termination obligation itself, so
#   the class is closed by the CARRIER upstream of the spec, and the audit
#   measured this rather than assuming it: a rival whose differing branch loops
#   (`while true do i := i + 1` in place of the emit) is rejected at ELABORATION,
#   `error: Decreasing annotations are required in total correctness semantics`
#   (exit 1); a `while i < 1 do i := i` variant is rejected identically.
#   NOT SHIPPABLE as a reject case, for a reason that is about this gate's
#   contract and not about difficulty: a reject case must carry a witness that
#   ELABORATES against the rival, and the audit built that witness against the
#   diverging rival at an equal pair (`5 5`) and a differing pair (`1 2`) — BOTH
#   fail (exit 1) with the same decreasing-annotations error, since the rival's
#   file never elaborates at all, so NO witness can hold of it. Hence vacuous
#   (the carrier already refuses divergence), not a known hole: there is nothing
#   for the spec to admit. A measure-carrying diverging loop is refused as well
#   (`while q > 0 ... decreasing q`, body `q := q`: rejected on
#   `case «decreasing_1: q»`, residual `q < q`), so this is not just the annotation
#   linter. The earlier contrast drawn here -- "the 401 `partial` bundles DO admit a
#   diverging rival (it verifies) and the class is a real spec hole" -- is withdrawn:
#   all 500 velvet bundles set "total". Not fabricated.
# RE-AIMED (admissibility): the sibling builds the exact F2P re-apply input and
#   Asserts the top-level Requires' state conjuncts hold for it (the precondition
#   admits a normal input). This backend's method has NO precondition, so that
#   probe is degenerate (every input is in-domain). It is re-aimed at the
#   total-carrier analogue — the OBLIGATION being unsatisfiable at an F2P-shaped
#   input — by discharging BOTH ensures clauses at concrete pairs, by evaluation,
#   as an in-region assert, before closing the frozen obligation verbatim.
#   REPAIRED BY AUDIT: the shipped version asserted the closed tautology
#   `((7 : Int) = 7) ∧ ((3 : Int) ≠ 4)`, which mentions no binder, no output and
#   no clause; substituting `assert (... (True))` verified identically (exit 0),
#   proving the assert carried no information and the case tested nothing while
#   passing honestly. The replacement instantiates clause (E) at an equal pair
#   (7,7) and clause (N) at a differing pair (7,8) over the emitted schedule, and
#   each conjunct tracks its claim — flipping either fails (exit 1,
#   `unsolved goals`) while the pair as written verifies (exit 0).
# PORTED (pos-branch-reorder): the sibling reframes the guard as the NEGATED
#   branch (`if old != new: issue_rename(...)`, else fall through to a no-op).
#   Carried here by pivoting the guard on the differing case and swapping the
#   proceed / inert arms — same schedule on every input; reproof is `loom_solve`.
# PORTED (weak-always-proceed = weak-unconditional-rename): the sibling drops the
#   no-op guard so the backend primitive is invoked unconditionally (this IS
#   model_prepatch.py). Carried here verbatim as the unconditional emit (this IS
#   Solution_prepatch.lean); refuted on clause (E) at an equal pair.
# PORTED (weak-always-inert = partial-domain-always-noop): the sibling treats
#   every case as a no-op. Carried here as the always-`[]` impl; refuted on
#   clause (N) at a differing pair.
# ADDED (pos-multi-op-schedule): a second positive this backend affords — the
#   proceeding branch's clause (N) pins only non-emptiness (the emitted count is
#   a many-to-one abstraction, mapping.md A3), so a two-op schedule must still
#   verify. Guards against the spec being SPEC-TOO-STRONG on the emitted count,
#   an axis the sibling's flag-based observable does not have.
# ADDED (weak-ordering-partial): a PARTIAL-DOMAIN rival that forks on a strict
#   ORDERING (`beforeId < afterId`) instead of identity. It is a near-miss —
#   correct on the equal and increasing sub-domains — so it agrees with gold over
#   more of the domain than always-inert and carries its OWN witness at the
#   decreasing sub-domain (`beforeId > afterId`). This is what varies the second
#   binder in the differing direction: without it every differing-case witness
#   would hold `beforeId < afterId`, and a rival mishandling only the
#   `beforeId > afterId` half would slip through.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders
#   (pts = 3 distinct input points):
#     beforeId — 5 (always-proceed, equal); 1 (always-inert, before<after);
#                2 (ordering, before>after): varied.
#     afterId  — 5 (equal); 2 (before<after); 1 (before>after): varied, and NOT
#                held fixed relative to beforeId — the equal case, the
#                before<after differing case, and the before>after differing case
#                are all probed, so the decision's dependence on the EQUALITY of
#                the two binders (the only observable property) is demonstrated in
#                all three regions.
#   Both independent top-level clauses of the post-image are attacked: the EMPTY
#   clause (E) by always-proceed, the NON-EMPTY clause (N) by always-inert and
#   (on a distinct sub-domain) by ordering-partial.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (the changed decision is modeled deeply; the
# resolution callees are unchanged and never A-consumed, mapping.md §3), and this
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
