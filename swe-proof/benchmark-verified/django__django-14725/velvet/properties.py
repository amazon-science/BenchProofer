"""properties.py — G-PBT falsification battery for django__django-14725 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct saveFormset`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  saveFormset (noCreate : Bool) (existing : List Nat) (fresh : List Nat)
      (mut stored : List Nat) return (out : List Nat)
    ensures out = reported noCreate existing fresh                            (C1)
    ensures stored = storedAfter noCreate storedOld fresh                     (C2)
    ensures noCreate = true  → (out = existing ∧ stored = storedOld)          (C3)
    ensures noCreate = false → (out = existing ++ fresh
                                  ∧ stored = storedOld ++ fresh)              (C4)

  There is NO ``require``: the domain is total (every Bool / List Nat triple is
  admissible). ``reported`` and ``storedAfter`` are transparent ``def``s over the
  method's own binders — the ``axioms`` region is empty, so there is no opaque
  callee and no answer key an impl could echo.

  The method models a persistence pass over a collection of editable rows. A
  policy flag decides whether the pass may bring brand-new rows into being.
  ``existing`` / ``fresh`` are the identities the two component persistence steps
  would settle (read-only free inputs); ``stored`` is the persistent collection
  of brand-new identities the permit branch grows and the forbid branch must
  leave untouched.

  TWO INDEPENDENT OBSERVABLES, each with its own load-bearing clause pair:
    * the REPORTED list ``out`` (C1, refined per-branch by C3/C4's first
      conjunct): under the forbid policy exactly ``existing``; otherwise
      ``existing`` FOLLOWED BY ``fresh``, in that order.
    * the STORED effect (C2, refined per-branch by C3/C4's second conjunct):
      under the forbid policy ``stored = storedOld`` EXACTLY — no rows produced
      as a side effect; otherwise exactly ``storedOld ++ fresh``.
  The second observable is the sharper half and has no sibling counterpart (see
  the accounting footer): it is what forbids an impl from reporting an
  edit-only result while silently creating rows anyway.

CARRIER — witness form. The spec is a ``method`` CONTRACT, not a bare predicate,
so each witness reaches the post-image through Velvet's own tester machinery:
``extract_program_for`` → ``saveFormsetExec``, then
``prove_precondition_decidable_for`` / ``prove_postcondition_decidable_for`` /
``derive_tester_for`` synthesize the ``Decidable`` instances and the boolean
tester. ``saveFormsetTester noCreate existing fresh stored = false`` says the
extracted program's ``(out, stored)`` violates the method's postcondition at that
concrete input. Every clause equates ``List Nat`` values with decidable equality
and the frozen impl is branch-only (no loop, no fixpoint), so ``decide`` reduces
both sides at literal inputs and no assumption is needed — no conditioning on an
opaque term is required here, hence every witness head binds NOTHING and the
gate's consistency probe is trivially satisfied. Each witness is checked in a
file whose ``prove_correct`` block has been stripped, so no tactic script can
mask the verdict.

ADVERSARIAL READ of the sibling's classes on this carrier:

  * SOUNDNESS / positive controls — APPLY. Two structurally-different but
    behaviourally identical impls (negate-and-swap the branch arms; hoist the
    reported concatenation into a local) must verify, else the spec is
    SPEC-TOO-STRONG on the SHAPE of the impl rather than on its behaviour.

  * ADMISSIBILITY — RE-AIMED. The sibling's probe asserts an F2P-shaped input can
    satisfy its fractional-permission ``Requires``. This method has NO ``require``
    at all and no permission surface, so "a normal input is admissible" is
    vacuously true and tests nothing. The residual risk on a total domain is a
    DEGENERATE post-image — a spec no impl distinguishes reads exactly like one
    every impl meets. ``admiss-nondegenerate`` discharges an in-region ``assert``
    pinning all FOUR post-image components at F2P-shaped literals, and its
    liveness was checked by hand (substituting a false claim leaves an
    ``unsolved goals`` error).

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    two MANDATORY rivals here (overwrite the read-only policy flag; self-assign
    it), rejected by Nagini's permission system because the flag is held at a
    half fraction. Velvet is referentially transparent: there is no heap, no
    aliasing and no fractional-permission system. The policy flag and the two
    component results are immutable values declared read-only (not ``mut``), so
    there is no read-only input to overwrite and no permission fraction to trip.
    The class has no carrier analogue and NO substitute is fabricated. What the
    sibling's permission fraction was protecting — that the pass does not write
    state it only means to read — is covered on this carrier by the ``stored``
    frame clauses (C2 / C3's second conjunct), which the ``silent-create`` and
    ``no-store`` rivals attack directly.

  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

  * UNGROUNDED-ORACLE ECHO — N/A, for the same reason the sibling records: both
    observables are pinned to transparent functions of the method's own binders
    (``reported`` / ``storedAfter``, plus the per-branch ``++`` refinements), so
    there is no opaque answer term to echo. The sibling stands its
    cheapest-honest-impl control in for the class; the positive controls here do
    the same job.

  * PARTIAL-DOMAIN / VALUE — carries the whole reject lane. Each rival gets most
    of the domain right and diverges on ONE sub-domain: the forbid branch's
    report, the forbid branch's untouched-store frame, the permit branch's
    report order, the permit branch's store effect, its multiplicity, or the
    branch decision itself.

WITNESS PLACEMENT / BINDER COVERAGE. The single obligation is DEFENDED (two
correct reshapes verify) and ATTACKED (eleven rivals). All FOUR clauses are
attacked, on both halves of each: the reported list under forbid
(``forbid-includes-fresh``) and under permit (``permit-drops-fresh``,
``permit-swaps-order``), the stored frame under forbid (``forbid-silent-create``)
and the stored effect under permit (``permit-no-store``,
``permit-double-store``, ``permit-store-prepends``,
``permit-store-overwrites``), plus the branch decision itself
(``ignore-policy-always-create``, ``flip-policy``) and the report's dependence on
``existing`` (``report-fresh-only``). The eleven witnesses sit at ELEVEN DISTINCT
input points, moving every input binder:
  * ``noCreate`` ∈ {true, false} — five witnesses on the forbid side and six on
    the permit side, so neither branch is the only one probed;
  * ``existing`` ∈ {[1], [2], [3], [4], [5], [8]} — never pinned;
  * ``fresh``    ∈ {[2], [3], [4], [6], [7], [9], [2,3]} — including a
    MULTI-element list, so a rival mishandling only the length or the order of
    the fresh group is reachable;
  * ``stored``   ∈ {[], [0], [1], [2], [3], [4], [5], [6], [7], [8]} — including
    the EMPTY prior collection (the F2P starting state) and non-empty priors.
    The non-empty priors are load-bearing rather than decorative: they are what
    makes the collection's PRIOR CONTENTS observable, and two rivals are shipped
    that are refutable ONLY there — ``permit-store-overwrites`` (drops
    ``storedOld``, keeping just the fresh group) and ``permit-store-prepends``
    (keeps both groups but puts the prior contents last). Both agree with gold
    at ``stored = []``, so each is witnessed at a non-empty prior.
Confirmed empirically with scripts/lean_verify.sh: both positives and the
admissibility case verify, every rival FAILS to verify, and every witness
ELABORATES against its rival and FAILS against the frozen solution with
``Tactic `decide` proved that the proposition ... is false`` — i.e. gold's tester
is TRUE at each witnessed point, which is the required discrimination.
"""
from pathlib import Path

INSTANCE = "django__django-14725"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. `_BODY` is the executable body of the impl region — the five code
# lines only, so it lies ENTIRELY between `-- impl-start` and `-- impl-end` (the
# region's leading comment block and both markers are left in place, which keeps
# every swap provably inside the region the spec view elides). `_PROOF` is the
# frozen tactic body, likewise elided. Both are asserted unique at load, so this
# manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------
_BODY = """    if noCreate then
      return existing
    else
      stored := stored ++ fresh
      return existing ++ fresh"""
assert _BASE.count(_BODY) == 1, "impl body anchor drift — re-sync _BODY"

_PROOF = ("prove_correct saveFormset by\n"
          "  loom_solve <;> simp_all [reported, storedAfter]")
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"

# The admissibility case adds an in-region `assert`, whose decidable goal the
# frozen `simp_all` arm does not discharge alone; the retuned body tries `decide`
# first and falls back to the frozen tactic for the method's own obligation. The
# `prove_correct saveFormset` header is byte-identical.
_PROOF_ADMISS = ("prove_correct saveFormset by\n"
                 "  loom_solve <;> first\n"
                 "    | decide\n"
                 "    | simp_all [reported, storedAfter]")


def _rival(body):
    """A variant that replaces only the impl region's executable body."""
    return _swap(_BASE, _BODY, body)


def _witness(noCreate, existing, fresh, stored):
    """A tester witness: extract the program, synthesize the decidability
    instances and the boolean tester for `saveFormset`, then assert its
    post-image is VIOLATED at the concrete input
    (`saveFormsetTester noCreate existing fresh stored = false`). Checked in a
    file whose `prove_correct` block is stripped; binds nothing at its head, so
    there are no assumptions that could be inconsistent."""
    return (
        "extract_program_for saveFormset\n"
        "prove_precondition_decidable_for saveFormset\n"
        "prove_postcondition_decidable_for saveFormset\n"
        "derive_tester_for saveFormset\n\n"
        f"example : saveFormsetTester {noCreate} {existing} {fresh} {stored} "
        "= false := by decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally-different but CORRECT impls
    # that MUST verify. Each keeps the frozen `ensures` clauses and the frozen
    # `prove_correct saveFormset by loom_solve <;> simp_all [...]` obligation
    # verbatim; only the impl body changes. If a faithful correct impl cannot
    # verify, the spec is SPEC-TOO-STRONG on the shape of the impl.
    # =====================================================================
    {
        "id": "pos-control-negate-swap",
        "kind": "soundness",
        "expect": "verify",
        # Negate the policy test and swap the arms: handle the permit-new case
        # first. The identical transition on both arms.
        "module": _rival(
            "    if ¬ noCreate then\n"
            "      stored := stored ++ fresh\n"
            "      return existing ++ fresh\n"
            "    else\n"
            "      return existing"),
        "rationale": (
            "negating the policy test and swapping the arms produces the "
            "identical (out, stored) transition on both sub-domains — the permit "
            "arm still grows the stored collection by the fresh identities and "
            "reports the already-known ones followed by them, the forbid arm "
            "still reports only the already-known identities and leaves the "
            "collection untouched — so C1-C4 all still discharge under the "
            "frozen proof body. A correct reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG (it rejects a faithful impl over "
            "arm ORDER, not behaviour). Ports the sibling's branch-reorder "
            "positive."),
    },
    {
        "id": "pos-control-hoist-report",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the permit-branch report into a local computed BEFORE the branch
        # (so it is evaluated on both sub-domains) and return it from the permit
        # arm. A local-variable reshape; the forbid arm still reports `existing`
        # and stores nothing, so no fresh row is created on that sub-domain.
        "module": _rival(
            "    let rep := existing ++ fresh\n"
            "    if noCreate then\n"
            "      return existing\n"
            "    else\n"
            "      stored := stored ++ fresh\n"
            "      return rep"),
        "rationale": (
            "computing the permit-branch report ONCE into a local before the "
            "branch and returning it from the permit arm is a local-variable "
            "reshape: the reported list and the stored effect are unchanged on "
            "both sub-domains (the forbid arm still reports `existing` and never "
            "touches the collection — hoisting a pure concatenation creates no "
            "row), so C1-C4 still discharge under the frozen proof body. A "
            "correct reshape must verify, else SPEC-TOO-STRONG. Ports the "
            "sibling's compute-once-into-a-local positive, which is also its "
            "honest cheapest-impl stand-in for the inapplicable "
            "ungrounded-oracle-echo class."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require`, so the sibling's
    # "an F2P-shaped input satisfies the precondition" probe is vacuously true
    # here. RE-AIMED at the residual total-domain risk: a DEGENERATE post-image.
    # The in-region assert pins all four post-image components at F2P-shaped
    # literals — under the forbid policy the report is the already-known group
    # ALONE and the stored collection is unchanged; under the permit policy the
    # report is the concatenation and the collection has grown by exactly the
    # fresh group — four genuinely distinct values. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _BODY,
                "    assert (with_name_prefix `admiss (\n"
                "      reported true [1] [2] = [1] ∧ storedAfter true [9] [2] = [9] ∧\n"
                "      reported false [1] [2] = [1, 2] ∧ "
                "storedAfter false [9] [2] = [9, 2]))\n"
                + _BODY),
            _PROOF, _PROOF_ADMISS),
        "rationale": (
            "the post-image is satisfiable AND NON-DEGENERATE at F2P-shaped "
            "literals: under the forbid policy the report is the already-known "
            "group ALONE ([1], not [1,2]) and the stored collection is exactly "
            "its prior contents ([9]); under the permit policy the report is the "
            "concatenation ([1,2]) and the collection has grown by exactly the "
            "fresh group ([9,2]). Four distinct values, so the two policies are "
            "genuinely distinguished on BOTH observables — a spec that collapsed "
            "them would read like one every impl meets. The in-region assert must "
            "discharge (its liveness was checked by hand: a false claim in its "
            "place leaves an `unsolved goals` error) and the impl is verbatim so "
            "C1-C4 still discharge. RE-AIMS the sibling's precondition-"
            "admissibility probe, which is vacuous here: this method has no "
            "`require` and no permission surface."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-ignore-policy-always-create",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image defect (Solution_prepatch.lean): ignore the policy flag
        # entirely — always produce the fresh rows, growing the stored
        # collection, and always report the concatenation.
        "module": _rival(
            "    stored := stored ++ fresh\n"
            "    return existing ++ fresh"),
        "refinement": (
            "this is the pre-change behaviour: the persistence pass ignores the "
            "policy flag and unconditionally runs the brand-new-row producer, so "
            "it reports the already-known identities followed by freshly produced "
            "ones AND adds those rows to storage even when the caller asked for an "
            "edit-only pass. All three FAIL_TO_PASS scenarios submit surplus rows "
            "under the forbid-new policy and assert that the stored collection "
            "still holds only the pre-existing row — no new row was brought into "
            "being. This shape creates them, so every one of those scenarios stays "
            "RED: it is precisely what does NOT resolve."),
        "rationale": (
            "REJECT from BOTH forbid-branch clauses (C3, and C1/C2 at "
            "noCreate = true): the spec demands `out = existing` and "
            "`stored = storedOld` there, but this reports `existing ++ fresh` and "
            "leaves `storedOld ++ fresh`. Verifying would be SPEC-TOO-WEAK on the "
            "whole change. Refuted at noCreate = true, existing = [1], "
            "fresh = [2], stored = [7] — a NON-EMPTY prior collection, so the "
            "witness also shows the frame clause is stated against `storedOld` "
            "rather than against the empty list. Ports the sibling's "
            "always-concat rival."),
        "witness": _witness("true", "[1]", "[2]", "[7]"),
    },
    {
        "id": "weak-forbid-includes-fresh",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain, REPORT half: correct on the permit sub-domain and
        # correct on the forbid sub-domain's stored frame (no row is created),
        # but the forbid arm REPORTS the fresh group as though it had been.
        "module": _rival(
            "    if noCreate then\n"
            "      return existing ++ fresh\n"
            "    else\n"
            "      stored := stored ++ fresh\n"
            "      return existing ++ fresh"),
        "refinement": (
            "a faithful counterpart that keeps the forbid-new policy from "
            "creating rows but still REPORTS the surplus rows as settled hands "
            "the caller identities for rows that were never brought into being. "
            "The edit-only scenarios read the pass's report back and assert it "
            "accounts for exactly the already-known rows; a report padded with "
            "phantom identities fails that assertion, and downstream deferred "
            "per-row follow-up work would be driven over rows that do not exist. "
            "It would NOT resolve. Correct on the whole permit sub-domain and on "
            "the forbid sub-domain's stored effect — a true partial-domain break, "
            "and a NEAR-MISS of the always-create rival that agrees with gold on "
            "the frame clause the latter violates, so it gets its own witness."),
        "rationale": (
            "REJECT from the REPORT half of the forbid branch (C3's first "
            "conjunct, and C1 at noCreate = true): the spec pins `out = existing` "
            "there, this returns `existing ++ fresh`. The stored frame "
            "(`stored = storedOld`) still HOLDS, so the rejection is attributable "
            "solely to the reported-list clause — this is what isolates the two "
            "observables. Refuted at noCreate = true, existing = [3], "
            "fresh = [4], stored = [8]. Ports the sibling's "
            "restrict-includes-new partial-domain rival."),
        "witness": _witness("true", "[3]", "[4]", "[8]"),
    },
    {
        "id": "weak-forbid-silent-create",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror-image partial-domain rival, STORED half: the forbid arm
        # reports the right list but produces the fresh rows anyway. The report
        # is indistinguishable from gold's; only the side effect betrays it.
        "module": _rival(
            "    if noCreate then\n"
            "      stored := stored ++ fresh\n"
            "      return existing\n"
            "    else\n"
            "      stored := stored ++ fresh\n"
            "      return existing ++ fresh"),
        "refinement": (
            "a faithful counterpart that reports an edit-only result while still "
            "running the brand-new-row producer creates rows the caller "
            "explicitly forbade and then hides them from its own report. This is "
            "the sharpest form of the defect under test: the FAIL_TO_PASS "
            "scenarios assert on the STORED collection (the pre-existing row is "
            "the only row afterwards), not merely on the returned report, so a "
            "pass that silently persists surplus rows fails them even though its "
            "report looks right. It would NOT resolve. Its report agrees with "
            "gold on the ENTIRE domain, so it is refutable only through the "
            "stored-effect clause."),
        "rationale": (
            "REJECT from the STORED half of the forbid branch (C3's second "
            "conjunct, and C2 at noCreate = true): the spec pins "
            "`stored = storedOld` there, this leaves `storedOld ++ fresh`. The "
            "reported list matches gold everywhere, so this rival is the reason "
            "the frame clause must be stated explicitly — without it the spec "
            "would admit a silently-creating impl (directive 5). Refuted at "
            "noCreate = true, existing = [5], fresh = [6], stored = [2]. ADDED: "
            "the sibling models no stored-collection side effect at all, so it "
            "carries no counterpart (its own contract could not see this rival)."),
        "witness": _witness("true", "[5]", "[6]", "[2]"),
    },
    {
        "id": "weak-permit-drops-fresh",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the policy the OTHER way: always behave as though new rows were
        # forbidden. Correct on the forbid sub-domain; on the permit sub-domain
        # it neither reports nor stores the fresh group.
        "module": _rival("    return existing"),
        "refinement": (
            "ignoring the policy the other way — always behaving as though brand "
            "new rows were forbidden — corresponds to a counterpart that drops "
            "the new-row producer unconditionally. It would make the failing "
            "scenarios pass, but it regresses the UNCHANGED default behaviour the "
            "PASS_TO_PASS scenarios pin: a default-policy pass that submits "
            "surplus rows must create them and report their identities after the "
            "already-known ones. This shape reports only the already-known group "
            "and stores nothing, so the default-policy save scenarios fail. It "
            "does NOT resolve."),
        "rationale": (
            "REJECT from BOTH permit-branch clauses (C4, and C1/C2 at "
            "noCreate = false): the spec demands `out = existing ++ fresh` and "
            "`stored = storedOld ++ fresh` there, this leaves `out = existing` and "
            "`stored = storedOld`. Verifying would be SPEC-TOO-WEAK (the "
            "unchanged default behaviour unpinned). Refuted at noCreate = false, "
            "existing = [2], fresh = [5], stored = [1] — the permit sub-domain, "
            "which every forbid-branch rival above agrees with gold on, so no "
            "witness is shared. Ports the sibling's always-existing rival."),
        "witness": _witness("false", "[2]", "[5]", "[1]"),
    },
    {
        "id": "weak-permit-swaps-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER rival: the permit arm stores correctly and reports both groups,
        # but with the fresh group FIRST. Only the order is wrong.
        "module": _rival(
            "    if noCreate then\n"
            "      return existing\n"
            "    else\n"
            "      stored := stored ++ fresh\n"
            "      return fresh ++ existing"),
        "refinement": (
            "a counterpart that reports the freshly produced identities BEFORE "
            "the already-known ones emits the settled rows in the wrong order. "
            "The scenarios that read the report back compare it against an "
            "ordered sequence (already-known rows first, then the newly created "
            "ones), and downstream deferred per-row follow-up work is driven in "
            "report order, so a transposed report fails those assertions. It "
            "would NOT resolve. Correct on the forbid sub-domain, on the stored "
            "effect everywhere, and even on the reported MULTISET — wrong only in "
            "order, which is why the clause is stated as a list equality rather "
            "than a membership predicate."),
        "rationale": (
            "REJECT from the REPORT half of the permit branch (C4's first "
            "conjunct, and C1 at noCreate = false): the spec pins "
            "`out = existing ++ fresh`, this returns `fresh ++ existing` — "
            "concatenation is not commutative. The stored effect still holds, "
            "isolating the ordering. Refuted at noCreate = false, existing = [4], "
            "fresh = [7], stored = [] — the EMPTY prior collection (the F2P "
            "starting state), the only witness at that value of `stored`. Ports "
            "the sibling's swap-order rival."),
        "witness": _witness("false", "[4]", "[7]", "[]"),
    },
    {
        "id": "weak-flip-policy",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the policy test: create when the flag FORBIDS new rows, and
        # suppress creation when it PERMITS them. Wrong on both sub-domains.
        "module": _rival(
            "    if noCreate then\n"
            "      stored := stored ++ fresh\n"
            "      return existing ++ fresh\n"
            "    else\n"
            "      return existing"),
        "refinement": (
            "inverting the policy test corresponds to a counterpart whose guard "
            "reads the flag backwards. It creates brand-new rows exactly when the "
            "caller forbade them (failing every FAIL_TO_PASS scenario, which "
            "assert the stored collection did not grow) and suppresses them under "
            "the default policy (failing the PASS_TO_PASS default-save "
            "scenarios). It does NOT resolve on either side."),
        "rationale": (
            "REJECT from ALL FOUR clauses: on the forbid sub-domain it reports "
            "`existing ++ fresh` and stores `storedOld ++ fresh` where C3 demands "
            "`existing` / `storedOld`; on the permit sub-domain it reports "
            "`existing` and stores `storedOld` where C4 demands the "
            "concatenations. Refuted at noCreate = true, existing = [1], "
            "fresh = [2, 3], stored = [0] — the only witness with a MULTI-element "
            "fresh group, so the battery also probes a fresh group whose length "
            "and internal order a rival could mishandle. Ports the sibling's "
            "flip-condition rival."),
        "witness": _witness("true", "[1]", "[2, 3]", "[0]"),
    },
    {
        "id": "weak-report-fresh-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Degenerate near-miss: drop the already-known group from the report
        # entirely and report only the fresh group, on both sub-domains.
        "module": _rival(
            "    if noCreate then\n"
            "      return fresh\n"
            "    else\n"
            "      stored := stored ++ fresh\n"
            "      return fresh"),
        "refinement": (
            "reporting only the freshly produced identities corresponds to a "
            "counterpart that dropped the already-known-row component from the "
            "report. It would fail to account for the edited pre-existing rows "
            "that the scenarios on both policies assert are settled and returned, "
            "and under the forbid policy it also reports identities for rows that "
            "were never created. It does NOT resolve. A supporting near-miss "
            "showing the report's dependence on the already-known component "
            "itself, which every other rival holds correct."),
        "rationale": (
            "REJECT from the REPORT half on BOTH branches (C1, and C3/C4's first "
            "conjuncts): the spec pins `out` to `existing` under forbid and to "
            "`existing ++ fresh` under permit; this returns `fresh` in both cases, "
            "so the already-known component is unpinned by the impl. The stored "
            "effect still holds on both branches, isolating the report. Refuted at "
            "noCreate = true, existing = [8], fresh = [9], stored = [1] — a point "
            "no other witness occupies. Ports the sibling's return-new-only "
            "near-miss."),
        "witness": _witness("true", "[8]", "[9]", "[1]"),
    },
    {
        "id": "weak-permit-no-store",
        "kind": "uniqueness",
        "expect": "reject",
        # The permit branch's mirror of forbid-silent-create: report the fresh
        # group as settled but never actually add it to storage. Report is
        # correct everywhere; only the side effect is missing.
        "module": _rival(
            "    if noCreate then\n"
            "      return existing\n"
            "    else\n"
            "      return existing ++ fresh"),
        "refinement": (
            "a counterpart that reports the freshly produced identities under the "
            "default policy but never adds those rows to storage claims to have "
            "created rows it did not. The PASS_TO_PASS default-policy scenarios "
            "assert on the stored collection after the pass (the newly submitted "
            "rows are retrievable), which fails when nothing was persisted, even "
            "though the returned report looks correct. It does NOT resolve. Its "
            "report agrees with gold on the ENTIRE domain, so like its forbid-"
            "branch mirror it is refutable only through the stored-effect clause."),
        "rationale": (
            "REJECT from the STORED half of the permit branch (C4's second "
            "conjunct, and C2 at noCreate = false): the spec pins "
            "`stored = storedOld ++ fresh` there, this leaves `storedOld`. The "
            "reported list matches gold everywhere, so this rival isolates the "
            "permit-branch effect exactly as forbid-silent-create isolates the "
            "forbid-branch frame — together they show the stored observable is "
            "load-bearing on BOTH sub-domains, not just where the change bites. "
            "Refuted at noCreate = false, existing = [1], fresh = [4], "
            "stored = [6]. ADDED: the sibling models no stored collection, so it "
            "carries no counterpart."),
        "witness": _witness("false", "[1]", "[4]", "[6]"),
    },
    {
        "id": "weak-permit-double-store",
        "kind": "uniqueness",
        "expect": "reject",
        # Multiplicity rival: the permit arm adds the fresh group to storage
        # TWICE. Report correct; effect correct as a SET but not as an exact
        # append.
        "module": _rival(
            "    if noCreate then\n"
            "      return existing\n"
            "    else\n"
            "      stored := stored ++ fresh ++ fresh\n"
            "      return existing ++ fresh"),
        "refinement": (
            "a counterpart that adds the freshly produced rows to storage twice "
            "persists a duplicate of every newly submitted row. The "
            "default-policy scenarios assert the exact contents of the stored "
            "collection after the pass (one row per submitted row); a duplicated "
            "row makes those counts and lookups wrong. It does NOT resolve. "
            "Correct on the report everywhere, correct on the forbid sub-domain, "
            "and correct on the stored collection's MEMBERSHIP — wrong only in "
            "multiplicity."),
        "rationale": (
            "REJECT from the STORED half of the permit branch read as an EXACT "
            "equality (C4's second conjunct / C2: `stored = storedOld ++ fresh`, "
            "not a `fresh ⊆ stored` superset predicate): a second append yields "
            "`storedOld ++ fresh ++ fresh`. This is why the clause pins the "
            "multiplicity rather than membership. Refuted at noCreate = false, "
            "existing = [2], fresh = [3], stored = [5]. ADDED: no sibling "
            "counterpart (the sibling models no stored collection)."),
        "witness": _witness("false", "[2]", "[3]", "[5]"),
    },
    {
        "id": "weak-permit-store-overwrites",
        "kind": "uniqueness",
        "expect": "reject",
        # PRIOR-CONTENTS rival: the permit arm reports correctly and ends up
        # holding the fresh group, but it OVERWRITES the collection instead of
        # appending to it — the prior contents are dropped. Invisible at
        # storedOld = [], which is why its witness sits at a non-empty prior.
        "module": _rival(
            "    if noCreate then\n"
            "      return existing\n"
            "    else\n"
            "      stored := fresh\n"
            "      return existing ++ fresh"),
        "refinement": (
            "a counterpart that replaces the stored collection with just the "
            "freshly produced rows, rather than adding them to what is already "
            "there, destroys the pre-existing rows. The default-policy scenarios "
            "assert the collection holds the already-known rows AND the newly "
            "submitted ones after the pass; a pass that discards the former "
            "fails them. It does NOT resolve. Correct on the report everywhere "
            "and on the forbid sub-domain, and it even ends up holding exactly "
            "the fresh group — wrong only in that the prior contents are gone."),
        "rationale": (
            "REJECT from the STORED half of the permit branch read as an append "
            "to `storedOld` (C4's second conjunct / C2: "
            "`stored = storedOld ++ fresh`, not merely `stored = fresh`): this "
            "leaves `fresh` alone. This is the rival that makes the battery's "
            "NON-EMPTY prior values load-bearing — it agrees with gold at every "
            "point where `stored = []`, so it is refutable only at a non-empty "
            "prior. Refuted at noCreate = false, existing = [2], fresh = [6], "
            "stored = [4]. ADDED by audit: the coverage prose claimed a rival "
            "that ignores `storedOld` and overwrites the collection outright was "
            "distinguishable, but no shipped case attacked it; this lands it."),
        "witness": _witness("false", "[2]", "[6]", "[4]"),
    },
    {
        "id": "weak-permit-store-prepends",
        "kind": "uniqueness",
        "expect": "reject",
        # PRIOR-CONTENTS ORDER rival: the permit arm keeps both groups in the
        # collection but puts the prior contents LAST. Correct as a multiset,
        # and indistinguishable from gold whenever the prior is empty.
        "module": _rival(
            "    if noCreate then\n"
            "      return existing\n"
            "    else\n"
            "      stored := fresh ++ stored\n"
            "      return existing ++ fresh"),
        "refinement": (
            "a counterpart that inserts the freshly produced rows AHEAD of the "
            "collection's existing contents rather than after them yields a "
            "collection whose order does not match what the default-policy "
            "scenarios compare against (prior rows first, then the newly "
            "submitted ones), and any downstream work driven in collection "
            "order runs over them transposed. It does NOT resolve. The sharpest "
            "of the stored-effect rivals: correct on the report everywhere, on "
            "the forbid sub-domain, on the collection's MEMBERSHIP and on its "
            "MULTIPLICITY — wrong only in where the prior contents sit."),
        "rationale": (
            "REJECT from the STORED half of the permit branch read as an ORDERED "
            "append (C4's second conjunct / C2: `stored = storedOld ++ fresh`, "
            "not `fresh ++ storedOld` and not a permutation predicate): "
            "concatenation is not commutative. Together with "
            "permit-store-overwrites this pins the prior contents' presence AND "
            "their position, the two things a non-empty `stored` value is there "
            "to observe; both agree with gold at `stored = []`. Refuted at "
            "noCreate = false, existing = [1], fresh = [2], stored = [3]. "
            "ADDED by audit alongside permit-store-overwrites."),
        "witness": _witness("false", "[1]", "[2]", "[3]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 11 SPEC cases (2
# soundness positives, 1 admissibility, 8 uniqueness rivals — two of which are
# MANDATORY frame-mutation rivals) plus 2 AXIOM_TESTS. This bundle contracts ONE
# method where the sibling contracts one function plus four contract-only
# callees, and it models one thing the sibling does NOT: the persistent stored
# collection of brand-new rows, as the `mut stored` carrier with an explicit
# frame clause.
#
#   sibling case (nagini)        kind          -> here                              disposition
#   ----------------------------------------------------------------------------------------
#   pos-control-call-once        soundness     -> pos-control-hoist-report          RE-SHAPED
#   pos-control-reorder          soundness     -> pos-control-negate-swap           PORTED
#   admiss-f2p-shaped-input      admissibility -> admiss-nondegenerate              RE-AIMED
#   frame-mut-write-flag         uniqueness    -> (none)                            VACUOUS
#   frame-mut-self-assign        uniqueness    -> (none)                            VACUOUS
#   uniq-always-concat           uniqueness    -> weak-ignore-policy-always-create  PORTED
#   uniq-restrict-includes-new   uniqueness    -> weak-forbid-includes-fresh        PORTED
#   uniq-always-existing         uniqueness    -> weak-permit-drops-fresh           PORTED
#   uniq-swap-order              uniqueness    -> weak-permit-swaps-order           PORTED
#   uniq-flip-condition          uniqueness    -> weak-flip-policy                  PORTED
#   uniq-return-new-only         uniqueness    -> weak-report-fresh-only            PORTED
#   (no sibling counterpart)                   -> weak-forbid-silent-create         ADDED
#   (no sibling counterpart)                   -> weak-permit-no-store              ADDED
#   (no sibling counterpart)                   -> weak-permit-double-store          ADDED
#   (no sibling counterpart)                   -> weak-permit-store-overwrites      ADDED (audit)
#   (no sibling counterpart)                   -> weak-permit-store-prepends        ADDED (audit)
#   ax-sound-reports             axiom         -> (none)                            DROPPED (G-AX)
#   ax-cover-reports             axiom         -> (none)                            DROPPED (G-AX)
#
# 6 uniqueness ported + 1 soundness ported + 1 re-shaped + 1 re-aimed;
# 5 uniqueness ADDED (3 at port time, 2 by audit); 2 uniqueness VACUOUS; 2 axiom
# cases DROPPED. Nothing was omitted because its proof would not close — every
# positive here builds green.
#
# RE-SHAPED (pos-control-call-once -> pos-control-hoist-report): the sibling
#   computes the already-known component ONCE into a local and reuses it across
#   both arms. On this carrier that component is already a free INPUT (`existing`
#   is a parameter, not a call), so "call it once" has no analogue — there is no
#   call to hoist. The equivalent local-variable reshape is to hoist the
#   permit-branch REPORT into a local computed before the branch, which is also
#   the sharper test: the local is now evaluated on the forbid sub-domain too, so
#   the case additionally confirms that computing the concatenation there is not
#   itself a violation (only STORING would be).
# RE-AIMED (admiss-f2p-shaped-input -> admiss-nondegenerate): the sibling asserts
#   that a concrete F2P-shaped editor establishes the function's half-permission
#   `Requires`. This method has NO `require` and no permission surface, so the
#   probe is vacuously true and would test nothing. Re-aimed at the residual
#   total-domain risk — a DEGENERATE post-image — via a live in-region assert
#   pinning all four post-image components at F2P-shaped literals (both policies
#   x both observables). Liveness confirmed by hand: substituting a false claim
#   leaves `error: unsolved goals`.
# VACUOUS (frame-mut-write-flag, frame-mut-self-assign): the sibling's two
#   MANDATORY frame rivals WRITE the policy flag, which is held at a half
#   permission fraction, and are rejected by Nagini's permission system for
#   insufficient permission (not by any value clause — the sibling notes the
#   returned value would satisfy the postcondition). Velvet is referentially
#   transparent: no heap, no aliasing, no `Old`, no fractional permissions. The
#   policy flag and the two component results are immutable read-only values (not
#   `mut`), so there is nothing to overwrite and no permission fraction to trip;
#   a "rival" that rebound them would not even be expressible as a mutation.
#   The class has NO carrier analogue and no substitute is fabricated. Note that
#   what the sibling's fraction protected — the pass must not write state it only
#   reads — IS covered here, but by a value clause rather than a permission: the
#   `stored` frame (C2 / C3's second conjunct) is attacked by
#   weak-forbid-silent-create, which is strictly the more informative rival (it
#   fails on the observable the F2P scenarios actually assert on).
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# ADDED beyond the sibling (the five stored-effect rivals): the sibling's
#   contract observes only the RETURNED report; the persistent collection of
#   brand-new rows appears nowhere in its postcondition, so it cannot express a
#   rival that reports correctly while creating (or failing to create) rows. This
#   bundle carries that collection as `mut stored` with an explicit per-branch
#   frame, and the F2P scenarios assert on exactly that observable, so five
#   rivals are attacked: weak-forbid-silent-create (reports edit-only, creates
#   anyway — the sharpest form of the defect under test),
#   weak-permit-no-store (reports created rows it never persisted),
#   weak-permit-double-store (persists each fresh row twice, defeating a
#   membership-only reading of the clause), and — added by audit —
#   weak-permit-store-overwrites (drops the collection's prior contents) and
#   weak-permit-store-prepends (keeps both groups but transposes them). Each has
#   a report indistinguishable from gold's on the whole domain, so each is
#   refutable ONLY through the stored clause — which is what demonstrates that
#   observable is load-bearing. The last two are additionally the only rivals
#   that read `storedOld` itself: both agree with gold wherever the prior
#   collection is empty, so they are what make the battery's non-empty `stored`
#   values load-bearing rather than incidental.
# DROPPED (ax-sound-reports, ax-cover-reports): the axiom lane is G-AX's job and
#   this gate ignores AXIOM_TESTS. This bundle declares no consumed axiom anyway
#   (mapping.md §3: the two unchanged component steps are free-input
#   A-references validated against the real callees by axiom_check.py).
#
# CLAUSE / BINDER COVERAGE. The single obligation `prove_correct saveFormset` is
#   DEFENDED by two positives and ATTACKED by eleven rivals. All four clauses are
#   attacked on both halves: the report under forbid (weak-forbid-includes-fresh)
#   and under permit (weak-permit-drops-fresh, weak-permit-swaps-order,
#   weak-report-fresh-only); the stored frame under forbid
#   (weak-forbid-silent-create) and the stored effect under permit
#   (weak-permit-no-store, weak-permit-double-store,
#   weak-permit-store-overwrites, weak-permit-store-prepends); the branch decision
#   itself (weak-ignore-policy-always-create, weak-flip-policy). The eleven
#   witnesses sit at ELEVEN DISTINCT points:
#     * weak-ignore-policy-always-create  true  [1] [2]    [7]
#     * weak-forbid-includes-fresh        true  [3] [4]    [8]
#     * weak-forbid-silent-create         true  [5] [6]    [2]
#     * weak-permit-drops-fresh           false [2] [5]    [1]
#     * weak-permit-swaps-order           false [4] [7]    []
#     * weak-flip-policy                  true  [1] [2, 3] [0]
#     * weak-report-fresh-only            true  [8] [9]    [1]
#     * weak-permit-no-store              false [1] [4]    [6]
#     * weak-permit-double-store          false [2] [3]    [5]
#     * weak-permit-store-overwrites      false [2] [6]    [4]
#     * weak-permit-store-prepends        false [1] [2]    [3]
#   Every input binder is moved: `noCreate` takes both values (5 witnesses true,
#   6 false — neither branch is the only one probed), `existing` ranges over six
#   distinct lists, `fresh` over seven including a MULTI-element list ([2, 3], so
#   a rival mishandling the fresh group's length or internal order is reachable),
#   and `stored` over ten values including the EMPTY prior collection (the F2P
#   starting state) and non-empty priors. The non-empty priors are DEMONSTRATED
#   load-bearing, not merely asserted: weak-permit-store-overwrites (which drops
#   `storedOld`) and weak-permit-store-prepends (which puts it last) both agree
#   with gold at `stored = []`, so each is refutable only at a non-empty prior —
#   which is what distinguishes a rival overwriting the collection outright from
#   one appending to it. No binder is pinned at a single value across the reject
#   set, and each pair of rivals that agrees with gold over more of the domain
#   (forbid-includes-fresh vs. forbid-silent-create; permit-no-store vs.
#   permit-double-store; permit-store-overwrites vs. permit-store-prepends) sits
#   at separate points, so no near-miss borrows another rival's witness.
AXIOM_TESTS = []
