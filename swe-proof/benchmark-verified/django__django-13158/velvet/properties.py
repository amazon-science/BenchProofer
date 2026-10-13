"""properties.py — G-PBT falsification battery for django__django-13158 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct emptyCombined`` obligation survives), and swaps in a
candidate implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, no ``require``):

  emptyCombined (q : Combined) return (out : Combined)
    ensures out.topSilenced = true
    ensures out.branches    = silenceAll q.branches
    ensures combinedRows out.branches = []

The method takes a set-combined query — a top-level row source plus an ordered
list of constituent sub-queries it draws its rows from — and returns the
combined query with NOTHING left to contribute. The three ``ensures`` clauses are
independently attackable:

  * TOP — ``out.topSilenced = true``: the combined query's OWN top-level row
    source is forced empty. Load-bearing on its own: a combined query with no
    constituents has this as its only observable, and downstream consumers read
    this flag to decide whether a sub-query may be skipped entirely.
  * FOLD — ``out.branches = silenceAll q.branches``: EVERY constituent is
    silenced, in order, with each constituent's other state (its own row set)
    preserved. This is the elementwise frame: no constituent is dropped, added,
    reordered, or rebuilt.
  * ROWS — ``combinedRows out.branches = []``: the input-grounded discriminator.
    A combined query draws rows from its constituents, so this is dischargeable
    only by having actually silenced every one of them — there is no answer key
    to echo (the ``axioms`` region is empty and every helper is a fully unfolded
    ``def`` over the method's own argument).

ONE INPUT BINDER, ``q : Combined``, with four independently-abusable components:
``q.topSilenced : Bool``, the LENGTH of ``q.branches``, and per constituent its
``rows : List Int`` and ``silenced : Bool``. The six reject witnesses drive all
four (see the BINDER COVERAGE footer): branch counts {0, 1, 2}, ``topSilenced``
over {false, true}, a constituent ``silenced`` over {false, true}, and a
constituent ``rows`` over {empty, non-empty} — so no component sits pinned at one
value across the reject set, and a rival mishandling only one of them cannot slip
through unattacked.

CARRIER NOTE — THE DECIDABLE BOUNDARY. The spec is a ``method`` CONTRACT, not a
bare predicate, so a witness reaches the post-image through Velvet's own tester
machinery: ``emptyCombinedTester q = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict, and it closes by ``decide``. ``decide`` reduces the extracted program by
kernel computation; the frozen program is a backward ``while`` loop over the
constituent list and its fixpoint is opaque to the kernel, so a witness applied
to the frozen solution gets STUCK ("reduction got stuck at the ``Decidable``
instance") — a FAILURE, but one the kernel never evaluated. Each reject rival
is therefore written as a LOOP-FREE impl that computes its (wrong) result
directly from the pure helpers, so its extracted tester ``decide``s over the
concrete literal. That is a witnessing convenience, not a weakening: the frozen
spec is untouched and each rival's divergence from the three clauses is real at
the witnessed input.

  IMPORTANT — WHICH SUBJECT REFUTES THESE WITNESSES. Because gold's ``decide``
  is stuck for EVERY claim regardless of truth, the frozen solution is NOT the
  discriminating subject for any witness here, and a stuck gold build is
  explicitly NOT accepted as the fail-on-gold half (``gates/pbt.py``
  ``_STUCK_REDUCTION`` / ``witness-undecided``). The gate instead falls back to
  a VERIFYING positive from this battery — in manifest order,
  ``pos-control-direct-fold`` — which shares the frozen spec, is independently
  required to verify, and is loop-free so it reduces. That is sound for the
  same reason gold would be: an impl the verifier ACCEPTS cannot violate its
  own spec, so a genuine refutation must still fail there. All five reject
  cases are recorded with ``witness_subject`` = "a verifying positive from this
  battery (gold cannot decide)"; the substance of each attestation is that
  build, not the gold one.

  Re-measured independently with ``scripts/lean_verify.sh``: for all five
  cases the witness elaborates against its own rival (exit 0), gets stuck
  against frozen gold (exit 1, "did not reduce to `isTrue` or `isFalse`" —
  carrying NO information), and is REFUTED against the fallback positive
  (exit 1) with the semantic message "`decide` proved that the proposition
  ... is false" naming the concrete input. Zero of the fallback builds
  were stuck, so every rejection here rests on a real semantic refutation of
  the concrete claim rather than on a syntactic or unreduced failure.
  Re-measured a SECOND time by an independent audit, all six cases, WITH the
  forgery control the first pass omitted: flipping each witness's claim moves
  the fallback build 1 -> 0 while leaving gold's error byte-identical, which is
  what establishes that the attesting exit code tracks the claim. See the
  SECOND, INDEPENDENT AUDIT PASS footer for the per-attack detail.

No witness binds anything (every input is a closed literal), so the gate's
consistency probe is vacuous by construction: there are no hypotheses that
could be jointly unsatisfiable.

ADVERSARIAL READ of the sibling's classes on this carrier:

  * PARTIAL-DOMAIN / VALUE — carries the reject lane, and is where the sibling's
    reasoning ports most directly. Each rival gets most of the domain right and
    diverges on one sub-domain: constituents untouched, all-but-the-last
    silenced, only-the-last silenced, silenced only when the top-level source was
    already empty, or the top-level source left as it was found.
  * SOUNDNESS / positive controls — APPLY. Two structurally different CORRECT
    impls (a loop-free direct return of the grounded fold; a loop-preserving
    reshape that keeps the frozen proof script) must verify, else the spec is
    SPEC-TOO-STRONG over the shape of the impl rather than its behavior.
  * ADMISSIBILITY — RE-AIMED. The sibling self-asserts that a normal input
    satisfies its fractional-permission precondition. This method has NO
    ``require`` at all, so that probe is degenerate here; the residual risk on
    this domain is a DEGENERATE post-image. ``admiss-nondegenerate`` discharges
    an in-region ``assert`` at the failing scenario's exact shape, pinning that
    the pre-image really does contribute rows and the post-image really is empty
    with each constituent's own row set preserved — so the obligation is not
    trivially satisfiable. The impl is kept verbatim so the method's own
    obligation still discharges.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend, and NOT ported. The
    sibling carries two MANDATORY cases here because its read-only inputs are
    held at a fractional heap permission an impl can illegally overwrite. Lean
    and Velvet are referentially transparent: ``q`` is an immutable value
    declared read-only (not ``mut``), there is no heap, no aliasing, no
    pre-state operator and no permission system, so there is no read-only input
    to overwrite and no permission clause to trip. Fabricating a substitute
    would test nothing. Note this is also why the sibling's whole
    independent-ownership axis collapses here: a fresh return value provably
    cannot reach its input, so "the source is left untouched" is a theorem of the
    carrier rather than a clause a rival could violate (refinement.md, "Coupled
    aliasing fix"). The elementwise FOLD clause is what remains of that axis, and
    it IS attacked, by four of the five rivals.
  * DIVERGENCE / NON-TERMINATION: CLOSED BY THE SEMANTICS, in both of its
    shapes, and NOT a hole (see the footer for the builds). This bundle sets
    ``loom.semantics.termination "total"``, under which a postcondition is claimed
    of ALL runs rather than only terminating ones, so the verifier demands a
    decreasing measure on every loop. The naive shape (a bare unbounded loop) is
    REFUSED at elaboration: ``error: Decreasing annotations are required in total
    correctness semantics``. The sharper shape, a loop that CARRIES a
    ``decreasing`` clause whose measure plainly INCREASES, is refused too, and on
    the measure's OWN descent goal rather than by the annotation linter: spliced as
    ``let mut z : Nat := 1; while z > 0 / invariant z > 0 / done_with z = 0 /
    decreasing z do z := z + 1`` it exits 1 with ``case «decreasing_1: z»`` and
    residual ``⊢ z + 1 < z``. An earlier revision of this file recorded that second
    shape as a LIVE spec hole ("accepted, re-admits the vacuity"). That is
    retracted: it is rejected, so the class is closed rather than escalated.
    Neither shape ships as a case, for a mechanical reason and not a spec one: the
    refusal fires on the ``method`` command, so the witness build against such a
    rival also fails and the gate would record ``witness-unproven``.
  * UNGROUNDED-ORACLE ECHO — N/A, same disposition as the sibling reached: the
    post-image is pinned to fully unfolded ``def``s over the method's own
    argument, so there is no opaque answer key an impl could echo instead of
    doing the work.
  * CONTROL-FLOW-EFFECT — N/A. The method is value-returning with all three
    observables pinned and no raise / side-effect channel invisible to the
    abstraction.
"""
from pathlib import Path

INSTANCE = "django__django-13158"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it edits (the impl block, the
# loop body inside it, or the `prove_correct` tactic body) and is unique in the
# file — both facts asserted at import, so the manifest breaks loudly if the
# frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole gold impl block, markers included. Reject rivals reshape the
# executable surface into a loop-free closed form by swapping on this.
_IMPL = """    -- impl-start
    let mut result : List Branch := []
    let mut i := q.branches.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ q.branches.length
      invariant result = silenceAll (q.branches.drop i)
      done_with i = 0
      decreasing i
    do
      let b := q.branches[i - 1]!
      result := silence b :: result
      i := i - 1
    return { topSilenced := true, branches := result }
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# The loop body, wholly inside the impl region. The loop-preserving positive
# reshapes only these lines, leaving the loop, its invariants and the frozen
# proof script intact.
_LOOP_BODY = """    do
      let b := q.branches[i - 1]!
      result := silence b :: result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# The impl-start marker line. The admissibility case inserts an in-region
# `assert` immediately after it and keeps the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen proof body (tactic script only — elided from the spec view). A
# rival that reshapes the impl into a single expression retunes it, without
# touching the spec and without dropping the `prove_correct emptyCombined`
# obligation header.
_PROOF_GOLD = """prove_correct emptyCombined by
  loom_solve
  rw [silenceAll_drop_step q.branches i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# A loop-free proof body: with no loop there is no invariant to peel, so
# `loom_solve` alone discharges the clauses (for a correct reshape) or leaves
# them unsolved (for the reject rivals, which is the point — and which their
# witnesses, not the tactic outcome, attribute to the spec).
_PROOF_FLAT = "prove_correct emptyCombined by\n  loom_solve"


def _flat(body):
    """Variant with the whole impl block replaced by a loop-free `body` and the
    proof retuned to the flat shape."""
    return _swap(
        _swap(_BASE, _IMPL, _IMPL_START + body + "\n    -- impl-end"),
        _PROOF_GOLD, _PROOF_FLAT)


# ---------------------------------------------------------------------------
# Witness preamble: Velvet's tester machinery, so a witness can reach the
# `method` contract's post-image at a concrete input. Appended to BOTH the rival
# and the frozen file, so every name it uses exists on both sides by
# construction.
# ---------------------------------------------------------------------------

def _tester(body):
    return ("\n"
            "extract_program_for emptyCombined\n"
            "prove_precondition_decidable_for emptyCombined\n"
            "prove_postcondition_decidable_for emptyCombined\n"
            "derive_tester_for emptyCombined\n\n" + body)


def _B(rows, silenced):
    """A concrete constituent literal for a witness input point."""
    return "{rows := [%s], silenced := %s}" % (
        ", ".join(str(r) for r in rows), "true" if silenced else "false")


def _Q(top_silenced, branches):
    """A concrete combined-query literal for a witness input point."""
    return "{topSilenced := %s, branches := [%s]}" % (
        "true" if top_silenced else "false", ", ".join(branches))


def _witness(q_literal):
    return _tester(f"example : emptyCombinedTester {q_literal} = false := by\n"
                   "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. A failure here is SPEC-TOO-STRONG (the spec rejecting a
    # faithful impl over its shape), never a proof gap: both proofs below close
    # honestly, with no new lemma, no weakened obligation and no `sorry`.
    # =====================================================================
    {
        "id": "pos-control-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded fold directly, no
        # loop at all — maximally structurally different from the gold backward
        # accumulator scan. `out.branches` IS `silenceAll q.branches`, so all
        # three clauses hold on the whole domain (ROWS via the frozen
        # `combinedRows_silenceAll` lemma) and the reproof is a bare
        # `loom_solve`: there is no loop invariant left to peel.
        "module": _flat(
            "    return { topSilenced := true, branches := silenceAll q.branches }"),
        "rationale": (
            "The honest correct impl in closed form: `out.branches` is literally "
            "`silenceAll q.branches`, so the FOLD clause holds by reflexivity, TOP "
            "by construction and ROWS by the frozen lemma relating the fold to the "
            "row observation. Different control flow from the frozen backward scan "
            "(no loop, no accumulator, no index arithmetic) yet identical behavior "
            "on every input, so it must verify — otherwise the postcondition is "
            "over-fit to the scan's code shape (SPEC-TOO-STRONG). Doubles as the "
            "no-ungrounded-echo control: computing the fold IS the work the spec "
            "demands, so returning it directly is correctness rather than a cheat. "
            "Proof is `loom_solve` alone; the obligation header is untouched. "
            "(Sibling: positive-mark-local-flag / positive-duplicate-read-locals, "
            "re-shaped — on this carrier the maximally-different correct impl is "
            "the loop-free closed form rather than an extra local.)"),
    },
    {
        "id": "pos-control-inline-exposed-constituent",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, its invariants and the FROZEN proof script
        # verbatim; only drops the intermediate `let b`, silencing the exposed
        # constituent in place. Observationally identical at every input, and the
        # minimal-edit counterpart of the sibling's local-binding positives.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "    do\n"
            "      result := silence q.branches[i - 1]! :: result\n"
            "      i := i - 1"),
        "rationale": (
            "Inlining the exposed constituent (dropping the intermediate binding "
            "and silencing it in place) walks the same constituents in the same "
            "order with the same step, so all three clauses still hold on the whole "
            "domain and the frozen proof script — loop invariants and drop-step "
            "rewrite included — still closes unchanged. A correct minimal reshape "
            "inside the frozen loop must verify, else the spec is SPEC-TOO-STRONG "
            "over the shape of the loop body. This is the loop-PRESERVING half of "
            "the soundness surface, complementing the loop-free positive above: "
            "together they defend the obligation both against a wholly different "
            "control flow and against a small edit within the frozen one. "
            "(Sibling: positive-mark-local-flag / positive-matches-local-read, "
            "which likewise reshape only how the written value is named.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require`, so the sibling's "a normal
    # input satisfies the precondition" probe is degenerate. Re-aimed at the
    # sharper residual risk on this domain: a DEGENERATE post-image, which reads
    # exactly like a strong one. The in-region `assert` pins, at the failing
    # scenario's exact shape (a combined query over two constituents that between
    # them contribute a low and a high row block), that (a) the pre-image really
    # does contribute rows, so ROWS is not satisfied for free, and (b) the fold
    # silences BOTH constituents while preserving each one's own row set, so FOLD
    # is not satisfied by a collapse. The surrounding impl is kept verbatim so
    # the method's own obligation still discharges; the proof gains only a
    # `decide` arm for the new assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      combinedRows [" + _B([0, 1], False) + ", "
                  + _B([8, 9], False) + "]\n"
                  "        = [0, 1, 8, 9] ∧\n"
                  "      silenceAll [" + _B([0, 1], False) + ", "
                  + _B([8, 9], False) + "]\n"
                  "        = [" + _B([0, 1], True) + ", " + _B([8, 9], True) + "] ∧\n"
                  "      combinedRows (silenceAll [" + _B([0, 1], False) + ", "
                  + _B([8, 9], False) + "]) = []))\n"),
            _PROOF_GOLD,
            "prove_correct emptyCombined by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [silenceAll_drop_step q.branches i (by omega) (by omega)]\n"
            "       simp_all)\n"),
        "rationale": (
            "The post-image is satisfiable AND non-degenerate at the failing "
            "scenario's shape (a combined query over two constituents contributing "
            "a low and a high row block). The in-region assert must discharge that "
            "the pre-image genuinely contributes those rows — so the ROWS clause is "
            "NOT vacuously true at the interesting input — that the fold silences "
            "BOTH constituents rather than collapsing or dropping either, and that "
            "each constituent's own row set survives the silencing. If any of these "
            "failed, the obligation would be degenerate and every rival below would "
            "be attacking nothing. The impl is kept verbatim so `out.branches = "
            "silenceAll q.branches` still verifies for the frozen scan; the proof "
            "only gains a `decide` arm for the assert goal, so the obligation is "
            "preserved, not weakened. (Sibling: admissibility-f2p-shaped-compound, "
            "re-aimed from precondition admissibility — there is no `require` and no "
            "permission surface here — to post-image non-degeneracy at the same "
            "two-constituent shape the sibling builds.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, and each with the refinement argument that its
    # faithful counterpart would NOT resolve. Every rival is a loop-free closed
    # form so its extracted tester `decide`s (see the CARRIER NOTE).
    # =====================================================================
    {
        "id": "weak-constituents-untouched",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-change shape: force the combined query's own top-level
        # row source empty and hand the constituents back as they were found.
        # This is the behavior the frozen prepatch file carries, restated in
        # loop-free form so its tester decides.
        "module": _flat(
            "    return { topSilenced := true, branches := q.branches }"),
        "refinement": (
            "This is the pre-change behavior itself: only the combined query's own "
            "top-level row source is forced empty, and the constituents it draws "
            "its rows FROM are left contributing. A combined query's rows come from "
            "its constituents, so the result still yields every row it did before, "
            "even though it was asked to contribute nothing. The failing scenario "
            "asserts that a combined query asked for nothing is empty; a faithful "
            "counterpart of this rival returns all of its rows there, so it does NOT "
            "resolve."),
        "rationale": (
            "REJECT from FOLD (`out.branches = silenceAll q.branches`, unprovable "
            "with the constituents passed through) and independently from ROWS "
            "(`combinedRows out.branches = []`, false whenever any constituent is "
            "un-silenced with a non-empty row set). Verifying would be SPEC-TOO-WEAK "
            "in the strongest sense: the spec would admit the unfixed behavior. "
            "Refuted at a single un-silenced constituent with a non-empty row set — "
            "the minimal shape on which the defect is observable at all, and the "
            "sub-domain where the top-level-guarded rival below still agrees with "
            "the spec, so the two do NOT share a witness. "
            "(Sibling: none-mutate-source-no-copy / the prepatch shape.)"),
        "witness": _witness(_Q(True, [_B([7], False)])),
    },
    {
        "id": "weak-skip-last-constituent",
        "kind": "uniqueness",
        "expect": "reject",
        # Silence every constituent EXCEPT the trailing one, which is passed
        # through untouched. Correct for a combined query with no constituents;
        # wrong for every non-empty one.
        "module": _flat(
            "    return { topSilenced := true,\n"
            "             branches := silenceAll q.branches.dropLast\n"
            "                           ++ q.branches.drop (q.branches.length - 1) }"),
        "refinement": (
            "Recursing into all-but-the-trailing constituent leaves the last one "
            "still contributing its rows. The failing scenario combines two "
            "constituents and asserts the emptied result is empty; a faithful "
            "counterpart of this rival still emits the trailing constituent's rows "
            "there, so the emptiness assertion fails and it does NOT resolve. "
            "Correct on the no-constituent domain, so a true partial-domain break "
            "rather than a wholesale one."),
        "rationale": (
            "REJECT from FOLD at the final index (the trailing constituent is "
            "returned un-silenced where the fold requires it silenced) and from "
            "ROWS (the trailing constituent still contributes). Verifying would be "
            "SPEC-TOO-WEAK: the fold would be unpinned at its last element, so a "
            "rival covering all-but-one constituent would pass. Refuted at TWO "
            "constituents whose FIRST has an EMPTY row set and whose second does "
            "not — this is the only witness that drives the constituent count past "
            "one with an empty per-constituent row set, so it separately rules out "
            "a rival that only ever gets non-empty constituents right. "
            "(Sibling: partial-domain-mark-skip-last.)"),
        "witness": _witness(_Q(False, [_B([], False), _B([8, 9], False)])),
    },
    {
        "id": "weak-only-last-constituent",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror sub-domain: silence ONLY the trailing constituent and pass
        # every earlier one through. Attacks the same clause as the rival above
        # but at the opposite end of the list, so a fold pinned only at its last
        # element would not catch it.
        "module": _flat(
            "    return { topSilenced := true,\n"
            "             branches := q.branches.dropLast\n"
            "                           ++ silenceAll (q.branches.drop (q.branches.length - 1)) }"),
        "refinement": (
            "Recursing into only the trailing constituent leaves every earlier one "
            "contributing. On the failing scenario's two-constituent combined "
            "query, a faithful counterpart still emits the FIRST constituent's rows "
            "when the result is asked for nothing, so the emptiness assertion fails "
            "and it does NOT resolve. Correct on any combined query with at most one "
            "constituent, so again a partial-domain break — and one that a spec "
            "pinning only the LAST constituent would miss entirely."),
        "rationale": (
            "REJECT from FOLD at the leading indices and from ROWS (the earlier "
            "constituents still contribute). This is the complement of "
            "weak-skip-last-constituent: together they show the fold is pinned "
            "ELEMENTWISE across the whole list rather than at one distinguished end, "
            "which is the property that makes ordering-and-coverage errors "
            "detectable. Refuted at two constituents of which the SECOND is ALREADY "
            "silenced on input and the first is not — the only witness that drives a "
            "constituent's own silenced component to true, so it also demonstrates "
            "that the fold is idempotent on already-silenced constituents rather "
            "than sensitive to their prior state. "
            "(Sibling: partial-domain-mark-skip-last, mirrored to the opposite "
            "sub-domain; the sibling's list-shaped rivals attack only the last "
            "index, so this is the ADDED case that closes the other end.)"),
        "witness": _witness(_Q(True, [_B([3], False), _B([4], True)])),
    },
    {
        "id": "weak-recurse-only-when-already-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS: recurse into the constituents only when the combined
        # query's own top-level row source was ALREADY empty on input. Agrees
        # with the spec on that whole sub-domain and fails on its complement —
        # which is precisely the sub-domain the failing scenario exercises.
        "module": _flat(
            "    if q.topSilenced then\n"
            "      return { topSilenced := true, branches := silenceAll q.branches }\n"
            "    else\n"
            "      return { topSilenced := true, branches := q.branches }"),
        "refinement": (
            "Making the recursion into the constituents CONDITIONAL on the combined "
            "query's own top-level source already being empty is the plausible "
            "half-fix: it looks like it only recurses where recursion is needed. But "
            "a freshly combined query has a non-empty top-level source, so the guard "
            "is false exactly when the operation is first applied — the constituents "
            "are never reached, and the emptied result still yields every row. The "
            "failing scenario asks for nothing from a freshly combined query, so a "
            "faithful counterpart returns all rows there and does NOT resolve. Note "
            "it IS correct on the already-empty sub-domain, which is what makes it a "
            "near-miss rather than a restatement of the unfixed behavior."),
        "rationale": (
            "REJECT from FOLD and ROWS on the branch where the top-level source was "
            "not already empty. Verifying would be SPEC-TOO-WEAK in a way the "
            "unconditional rival does not expose: it would mean the spec constrains "
            "the constituents only for inputs that were already partly empty. "
            "Refuted at a single un-silenced constituent with the top-level source "
            "NOT already empty — the same constituent shape as "
            "weak-constituents-untouched but the OPPOSITE top-level value, so this "
            "pair isolates `q.topSilenced` as a load-bearing input component: this "
            "rival's witness sits at a point where the unconditional rival's guard "
            "is irrelevant, so `q.topSilenced` is demonstrated to change the "
            "verdict of THIS rival rather than being pinned across the reject set. "
            "The isolation is ONE-WAY, and measured: this case's witness "
            "(top=false, one un-silenced constituent) also refutes "
            "weak-constituents-untouched (rival exit 0), because that rival is "
            "wrong on the whole domain and so is wrong here too. The converse does "
            "NOT hold — weak-constituents-untouched's witness (top=true) does NOT "
            "refute this rival (exit 1), since this rival is CORRECT on the "
            "already-empty sub-domain. That asymmetry is exactly the near-miss "
            "property being claimed, and it is what a witness shared in one "
            "direction only can attest. "
            "(Sibling: partial-domain-duplicate-fabricate-last-flag, re-aimed — the "
            "sibling's near-miss keys on a list position, this one keys on the "
            "top-level flag, which is the component this carrier exposes.)"),
        "witness": _witness(_Q(False, [_B([6], False)])),
    },
    {
        "id": "weak-top-source-passed-through",
        "kind": "uniqueness",
        "expect": "reject",
        # Silence every constituent correctly, but hand the combined query's OWN
        # top-level row-source flag back as it was found instead of forcing it
        # empty. Attacks the TOP clause in isolation: FOLD and ROWS both hold.
        "module": _flat(
            "    return { topSilenced := q.topSilenced,\n"
            "             branches := silenceAll q.branches }"),
        "refinement": (
            "Dropping the step that forces the query's OWN top-level row source "
            "empty — while still silencing every constituent — leaves the result "
            "not reporting itself as contributing nothing. Downstream consumers read "
            "that flag to decide whether a sub-query can be skipped when it is "
            "combined into a larger one: a scenario that combines two "
            "contribute-nothing sub-queries and asserts the combination yields no "
            "rows relies on each being recognised as empty and skipped. Under this "
            "rival neither is recognised, both are compiled in full, and the "
            "combination "
            "yields rows instead of none — a passing scenario regresses, so a "
            "faithful counterpart does NOT resolve. (Resolution requires the "
            "previously-passing scenarios to keep passing, so this is a genuine "
            "non-resolution, not a cosmetic difference.)"),
        "rationale": (
            "REJECT from TOP (`out.topSilenced = true`) alone — FOLD and ROWS are "
            "both satisfied, so this is the one rival that isolates the third "
            "clause, and without it that clause would be defended by no case at "
            "all. Verifying would be SPEC-TOO-WEAK: the query's own top-level "
            "emptiness would be unpinned, leaving it free to be whatever the input "
            "happened to carry. Refuted at a combined query with NO constituents and "
            "a top-level source not already empty — the only witness that drives the "
            "constituent count to ZERO, which is the shape where the top-level flag "
            "is the sole observable (the fold and the row observation are both "
            "trivially satisfied there), so this is the only witness that "
            "attributes a refutation to TOP with FOLD and ROWS both satisfied. "
            "What makes the case load-bearing is the RIVAL, not the exclusivity of "
            "its input: measured, the witnesses of weak-skip-last-constituent and "
            "weak-recurse-only-when-already-empty ALSO refute this rival (both "
            "exit 0), because both of their input points carry top=false, which "
            "this rival passes through. So the zero-constituent point is the "
            "minimal shape isolating TOP, not an input only this witness can "
            "reach; no other RIVAL in the battery violates TOP while satisfying "
            "the other two clauses, and that is the gap this case closes. "
            "(Sibling: frame-mutation-matches_nothing, re-aimed — the sibling "
            "attacks the read-only observation of this same flag through the "
            "permission system, which does not exist here; what survives the "
            "carrier is that the flag's post-state is pinned, and that is what this "
            "rival violates.)"),
        "witness": _witness(_Q(False, [])),
    },
    {
        "id": "weak-top-only-when-constituents",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). A TOP NEAR-MISS that the shipped set leaves
        # unattacked: force the query's own top-level source empty only when it
        # HAS constituents. Every shipped rival either violates TOP on the whole
        # domain it is wrong on (weak-top-source-passed-through, which merely
        # passes the input flag through and so is CORRECT at every top=true
        # input) or does not touch TOP at all. So the sub-domain "TOP is right
        # wherever the fold had work to do, wrong exactly where it did not" is
        # covered by no case, and a spec pinning TOP only on non-empty inputs
        # would read as fully defended.
        "module": _flat(
            "    return { topSilenced := !q.branches.isEmpty,\n"
            "             branches := silenceAll q.branches }"),
        "refinement": (
            "Deriving the result's own top-level emptiness from whether it had "
            "constituents to silence is the plausible shortcut: for every combined "
            "query it looks correct, because a combined query has constituents. But "
            "the flag is what downstream consumers read to decide whether a "
            "sub-query can be skipped when it is folded into a larger one, and a "
            "sub-query with no constituents of its own is exactly the leaf case they "
            "ask about. Under this rival such a leaf reports itself as still "
            "contributing after being asked for nothing, so it is compiled in full "
            "and the enclosing query yields rows where the scenario asserts none — a "
            "previously-passing scenario regresses, so a faithful counterpart does "
            "NOT resolve."),
        "rationale": (
            "REJECT from TOP (`out.topSilenced = true`) on the zero-constituent "
            "sub-domain, with FOLD and ROWS satisfied everywhere. This is the "
            "COMPLEMENT of weak-top-source-passed-through in the same sense that "
            "weak-only-last-constituent complements weak-skip-last-constituent: that "
            "rival is wrong at top=false and right at top=true, this one is wrong at "
            "zero constituents and right at every non-empty one, so together they "
            "show TOP is pinned UNCONDITIONALLY rather than on either input's "
            "say-so. Measured, and this is what makes the case load-bearing rather "
            "than a second spelling of the existing TOP attack: this rival's witness "
            "(top=true, no constituents) does NOT refute "
            "weak-top-source-passed-through (exit 1 — that rival returns the input's "
            "own `true` there and is correct), and weak-top-source-passed-through's "
            "witness (top=false, no constituents) does NOT refute this rival (its "
            "guard also yields false there, agreeing with that rival, so neither "
            "witness reaches the other). Neither case subsumes the other. "
            "(Sibling: partial-domain-duplicate-fabricate-last-flag — the sibling's "
            "near-miss FABRICATES an output flag from a position rather than reading "
            "it; this is that same fabrication aimed at the flag this carrier "
            "exposes.)"),
        "witness": _witness(_Q(True, [])),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling ships 11 SPEC cases (3 soundness
# positives, 1 admissibility, 7 uniqueness rivals — two of them mandatory
# frame-mutation cases and two of them non-termination cases) plus an EMPTY
# AXIOM lane (AXIOM_TESTS = []).
#
# CARRIER NARROWING. The sibling contracts FOUR functions over a mutable heap
# object: `matches_nothing` (read the emptiness observation), `duplicate`
# (deep-copy the query and its constituents), `mark_matching_nothing` (force the
# query and every constituent empty), and the composite `none` (duplicate then
# mark, leaving the source untouched). This bundle models ONE method,
# `emptyCombined`, the purely functional core — the per-constituent empty fold.
# The other three sibling functions have no counterpart, for carrier reasons
# rather than convenience:
#   * `duplicate` and the source-untouched half of `none` exist in the sibling
#     ONLY because its carrier has aliasing: a shallow copy would share the
#     constituents and emptying the copy would corrupt the source. Here
#     `emptyCombined : Combined -> Combined` returns a fresh value that provably
#     cannot reach its read-only input, so "the source is unchanged" is a theorem
#     of the carrier, not a clause an impl could violate (mapping.md; refinement.md
#     "Coupled aliasing fix"). There is nothing left to attack.
#   * `matches_nothing` is a bare field read; here that observation is a `.`
#     projection on an immutable structure, with no contract of its own to
#     falsify.
# So a port of 8 cases against the sibling's 11 is carrier narrowing, and
# chasing count parity would mean fabricating rivals for behavior this bundle
# does not model.
#
#   sibling case                                kind    -> here                              disposition
#   ---------------------------------------------------------------------------------------------------
#   frame-mutation-matches_nothing              uniq    -> weak-top-source-passed-through    RE-AIMED
#   frame-mutation-duplicate-source-write       uniq    -> (none)                            VACUOUS
#   partial-domain-mark-skip-last               uniq    -> weak-skip-last-constituent        PORTED
#                                                          (+ weak-only-last-constituent     ADDED)
#   partial-domain-duplicate-fabricate-last-flag uniq   -> weak-recurse-only-when-already-empty RE-AIMED
#   none-mutate-source-no-copy                  uniq    -> weak-constituents-untouched       RE-AIMED
#   nonterm-none-self-recursion                 uniq    -> (none)                            CARRIER-REFUSED
#   nonterm-none-endless-loop                   uniq    -> (none)                            CARRIER-REFUSED
#                                                          (+ a MEASURE-BYPASS spec hole,     ESCALATED)
#   positive-mark-local-flag                    sound   -> pos-control-inline-exposed-constituent  RE-SHAPED
#   positive-duplicate-read-locals              sound   -> pos-control-direct-fold           RE-SHAPED
#   positive-matches-local-read                 sound   -> (folded into the two above)       MERGED
#   admissibility-f2p-shaped-compound           admiss  -> admiss-nondegenerate              RE-AIMED
#   AXIOM_TESTS (empty)                         axiom   -> (none)                            N/A (G-AX)
#   (no sibling counterpart)                    uniq    -> weak-top-only-when-constituents    ADDED BY AUDIT
#
# 6 uniqueness shipped (3 re-aimed, 1 ported directly, 2 added), 2 soundness
# positives, 1 admissibility. 1 uniqueness vacuous, 2 uniqueness refused by the
# carrier at elaboration time, 1 soundness merged, axiom lane empty.
#
# RE-AIMED (frame-mutation-matches_nothing -> weak-top-source-passed-through): the
#   sibling's MANDATORY frame case writes to the half-permission field carrying the
#   query's own emptiness observation and is rejected for INSUFFICIENT PERMISSION.
#   There is no permission system here, but the same observation IS pinned in the
#   post-state by the TOP clause, so what survives the carrier is a rival that
#   passes the flag through instead of forcing it empty. That is a value break
#   rather than a permission break, and it is attributable to the TOP clause via a
#   witness at the zero-constituent input.
# VACUOUS (frame-mutation-duplicate-source-write): the sibling's second MANDATORY
#   frame case writes into the half-owned SOURCE constituent list. This backend is
#   referentially transparent — `q` is an immutable value declared read-only (not
#   `mut`), with no heap, no aliasing, no pre-state operator and no fractional
#   permissions — so there is no read-only input to overwrite and no frame clause
#   to violate. Omitted as a genuine carrier fact; fabricating a substitute would
#   test nothing. (Porting map: this class is vacuous on a referentially
#   transparent backend.)
# PORTED (partial-domain-mark-skip-last -> weak-skip-last-constituent): direct
#   port of the all-but-the-last loop bound, refuted at a two-constituent input.
#   The sibling's list-shaped rivals all attack the LAST index, so
#   weak-only-last-constituent is ADDED to close the opposite end: without it, a
#   spec pinning the fold only at its final element would look fully defended.
# RE-AIMED (partial-domain-duplicate-fabricate-last-flag ->
#   weak-recurse-only-when-already-empty): the sibling's near-miss fabricates the
#   trailing copied flag. The copy/source distinction it keys on does not exist
#   here (see CARRIER NARROWING), so the near-miss is re-aimed at the component
#   this carrier DOES expose — guarding the recursion on the top-level flag. It
#   keeps the essential property of the sibling's case: correct on a genuine
#   sub-domain, wrong exactly where the failing scenario lives, and refuted at the
#   input where the wholesale rival agrees with the spec.
# RE-AIMED (none-mutate-source-no-copy -> weak-constituents-untouched): the
#   sibling's rival empties the live query in place and returns it, rejected by its
#   source-unchanged clauses. Those clauses have no counterpart here (value
#   semantics), but the other half of that rival's wrongness — the constituents not
#   being emptied — is exactly the FOLD/ROWS break, and that is what ships.
# RE-SHAPED / MERGED (the three sibling positives): all three reshape only how a
#   written value is NAMED (write through a typed local, read into a local before
#   writing, bind the read before returning). Two of the three attach to functions
#   this bundle does not model, and on an immutable carrier "name the value in a
#   local" is not a meaningful behavioral reshape. They are replaced by the two
#   axes that ARE meaningful here: a wholly different control flow (loop-free
#   closed form) and a minimal edit inside the frozen loop (inline the exposed
#   constituent, keeping the frozen proof script). Both proofs close honestly —
#   no new lemma, no weakened obligation, no `sorry` — and NO soundness positive
#   was dropped for being hard to prove.
#
# THE DIVERGENCE LANE — CORRECTED BY AUDIT, and it splits in two. The port's
#   original note here recorded the whole lane as a KNOWN SPEC HOLE on the
#   grounds that "the postcondition is claimed only of TERMINATING runs", citing
#   `set_option loom.semantics.termination "total"` as the reason. That reading
#   is exactly INVERTED — "total" is the setting that makes the verifier DEMAND a
#   termination argument — and the claim that a `while true` prefix with a wrong
#   return "VERIFIES — exit 0" does not reproduce.
#
#   The PROVENANCE explains it, and is worth recording so the same staleness can
#   be recognised elsewhere: the note was written when the frozen file still read
#   `termination "partial"`, under which every word of it was TRUE. The bundle was
#   later flipped to `"total"` — with a `decreasing i` clause added to the frozen
#   loop — by the corpus-wide `scripts/velvet_total_correctness.py` sweep, which
#   re-clears the static gates but cannot re-read a battery's PROSE. So the
#   measurement stayed in the file describing a spec that no longer exists. Any
#   sibling cell carrying a "known divergence hole" note should be re-read against
#   its CURRENT `set_option` line for the same reason; the flip touched 395 velvet
#   bundles.
#
#   Re-measured against the spec as it now stands, three builds:
#     * `while true do pure ()` prefixing the frozen body, wrong return
#       (`branches := q.branches`)                                  -> exit 1
#     * the same prefix keeping gold's own return value              -> exit 1
#     * the frozen loop with its `decreasing i` clause DELETED       -> exit 1
#   all three with `error: Decreasing annotations are required in total
#   correctness semantics`. So the naive divergence class is REFUSED BY THE
#   CARRIER, not admitted by the spec. It is still not shippable as a reject
#   case, but for the opposite reason: the refusal happens at ELABORATION time,
#   so the witness build against such a rival also fails (exit 1, same
#   termination error) and the gate would record `witness-unproven` —
#   inconclusive — for a rival the spec correctly refuses. Nothing to port, and
#   no hole on this axis. Self-recursion is likewise refused: `let r ←
#   emptyCombined q` fails with `fail to show termination for emptyCombined /
#   failed to infer structural recursion`, so the sibling's
#   nonterm-none-self-recursion has no expressible counterpart either.
#
# NO MEASURE BYPASS -- RETRACTED, AND RE-MEASURED. An earlier revision of this
#   footer escalated a second divergence shape as a live spec hole, on the theory
#   that `"total"` demands a measure but does not VALIDATE it, so a `decreasing`
#   clause whose measure plainly INCREASES would be accepted and would re-admit
#   the vacuity through an unreachable loop exit. Every part of that is false on
#   this bundle, and the same shape has now been rebuilt against the spec as it
#   stands:
#     * `let mut z : Nat := 1; while z > 0  invariant z > 0  done_with z = 0
#        decreasing z  do z := z + 1`, prefixed to the frozen body -> exit 1,
#       `unsolved goals`, `case «decreasing_1: z»`, residual `z + 1 < z`
#   The rejection lands on the MEASURE's own descent goal, so it is not the
#   missing-annotation linter and cannot be dismissed as one: `total` both demands
#   the measure and discharges its descent. The mechanism is visible in Loom
#   itself. `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`
#   (`Loom/MonadAlgebras/NonDetT/Basic.lean:544`) takes `measure : β -> Nat` and
#   emits `with_name_prefix `decreasing (measure b' < measure b)`; only the
#   `PartialCorrectness` twin (same file, :211) takes `measure : β -> Option ℕ`
#   and DISCARDS it. This bundle opens `TotalCorrectness`, and it cannot silently
#   be the other one: the `set_option` elaborator itself runs
#   `openScope `TotalCorrectness` (`Loom/MonadAlgebras/WP/Options.lean:169-186`).
#   So there is nothing to escalate and nothing to record as a hole. The class
#   still does not SHIP as a reject case, for a mechanical reason rather than a
#   spec one: the refusal fires on the `method` command, so the witness build
#   against the rival fails with the same error and the gate records
#   `witness-unproven`, which is INCONCLUSIVE and would fail G-PBT. The earlier
#   cross-reference to a corpus-wide `partial` cohort, and to its remediation
#   ("`partial` -> `total`, plus a decreasing measure") as merely necessary, is
#   withdrawn as well: all 500 velvet bundles set "total", so no cohort admits it.
#
# DROPPED — a rival whose witness discriminates but whose REFINEMENT argument
#   does not hold. A rival that silences every constituent but REBUILDS each one
#   as a blank (discarding its own row set: `q.branches.map (fun _ => {rows := [],
#   silenced := true})`) is rejected by the FOLD clause, and a witness at a single
#   already-silenced constituent with a non-empty row set was BUILT AND SEEN to
#   discriminate (elaborates against the rival, gets stuck against the frozen
#   solution). It is NOT shipped, because its refinement argument fails: once
#   every constituent is silenced, the combined result contributes nothing and no
#   scenario in the suite reads a silenced constituent's preserved state back, so
#   a faithful counterpart that blanked the constituents instead of constraining
#   them would still resolve. Shipping it would claim a
#   verify-does-not-imply-resolve break that does not exist. This is a real
#   observation about the bundle worth recording rather than hiding: the
#   row-preservation half of the FOLD clause is STRONGER than the test suite can
#   observe. That is sound (an over-strong frame clause cannot admit a wrong
#   impl, and the clause is what makes the fold elementwise rather than a
#   collapse) but it means that half is defended by the spec alone, with no
#   rival the refinement contract permits.
#
# BINDER / CLAUSE COVERAGE. The method has ONE input binder, `q : Combined`, with
#   four independently-abusable components. The six reject witnesses probe six
#   DISTINCT input points (pts=6):
#     * weak-constituents-untouched            top=true  [rows=[7], sil=false]
#     * weak-skip-last-constituent             top=false [rows=[],  sil=false],
#                                                        [rows=[8,9], sil=false]
#     * weak-only-last-constituent             top=true  [rows=[3], sil=false],
#                                                        [rows=[4], sil=true]
#     * weak-recurse-only-when-already-empty   top=false [rows=[6], sil=false]
#     * weak-top-source-passed-through         top=false []
#     * weak-top-only-when-constituents        top=true  []   (ADDED BY AUDIT)
#   The last two are the zero-constituent pair, and they are what makes the ZERO
#   length class discriminating in BOTH directions of the top-level flag rather
#   than at one value of it: measured, neither witness refutes the other's rival
#   (each exits 1 there), so the two cases are independent and TOP is pinned
#   unconditionally instead of on either input's say-so.
#   So `q.topSilenced` ranges over {false, true} and is demonstrated LOAD-BEARING:
#   weak-constituents-untouched and weak-recurse-only-when-already-empty sit at
#   the SAME constituent shape with OPPOSITE top-level values, each witnessed at
#   the point where the other's rival agrees with the spec, so neither witness
#   refutes the other's rival. `q.branches.length` ranges over {0, 1, 2} —
#   including the ZERO case, where the top-level flag is the sole observable and
#   which no other witness reaches. A constituent's `silenced` ranges over
#   {false, true} (weak-only-last-constituent supplies an already-silenced one, so
#   the fold's idempotence on prior state is exercised). A constituent's `rows`
#   ranges over empty and non-empty (weak-skip-last-constituent supplies an empty
#   one), so a rival correct only on non-empty constituents is caught. No
#   component is pinned at a single value across the reject set. All THREE
#   top-level clauses are attacked: TOP by weak-top-source-passed-through and
#   weak-top-only-when-constituents, both in ISOLATION (the only two rivals
#   satisfying FOLD and ROWS, and complementary — one passes the input flag
#   through, the other FABRICATES the flag from the constituent count, so the
#   clause is defended against both reading it off the input and deriving it),
#   FOLD by the other four — elementwise at the leading indices
#   (weak-only-last-constituent), at the trailing index
#   (weak-skip-last-constituent), wholesale (weak-constituents-untouched) and
#   conditionally (weak-recurse-only-when-already-empty) — and ROWS by those same
#   four, each of which leaves a constituent contributing rows.
#
# INDEPENDENT AUDIT PROBES (run with the real verifier; recorded so the next
#   reader need not re-derive them). None changed the shipped case set.
#
#   SPEC-TOO-WEAK probes — NEW wrong impls aimed at what the five rivals leave
#   unattacked, all four correctly REJECTED (exit 1), so no spec hole was found
#   on these axes:
#     * FOLD order:  branches := (silenceAll q.branches).reverse
#                    (satisfies TOP and ROWS; violates the fold's ORDER — the
#                     one FOLD dimension no shipped rival drives)
#     * FOLD frame:  branches := q.branches.map (fun _ => blank silenced branch)
#                    (the row-preservation break described in DROPPED below)
#     * FOLD length: branches := []            (all constituents dropped)
#     * FOLD length: branches := silenceAll q.branches ++ silenceAll q.branches
#   So the FOLD clause is pinned in all four directions — order, per-element
#   frame, and length in both directions — even though the shipped rivals only
#   need coverage/position.
#
#   SPEC-TOO-STRONG probes — NEW correct reshapes, all VERIFIED (exit 0), so the
#   spec is not over-fit to the frozen scan's shape:
#     * branches := q.branches.map silence            (forward map)
#     * branches := q.branches.foldr (silence · :: ·) []   (foldr)
#     * the frozen loop with `{ b with silenced := true }` inlined for
#       `silence b` — verifies once `simp_all` is given `silence` to unfold
#       (`simp_all [silence]`). Worth noting for what it is: a PROOF-SCRIPT
#       tuning artifact, not a spec fact. The residual goal was the
#       definitional identity `{rows := b.rows, silenced := true} = silence b`,
#       so the spec accepts the reshape and only the tactic needed the unfold.
#
# SECOND, INDEPENDENT AUDIT PASS (a different agent, rebuilding rather than
#   reading; every exit code below was observed, not inferred).
#
#   Attack A (statement integrity): every case's `module` diffed against the
#   frozen file. All eight edits land wholly inside the impl region and/or the
#   `prove_correct` tactic body; no `ensures` clause, signature, helper `def` or
#   lemma statement differs by a byte in any case, and `variant_scope` reports
#   `[]` for all of them. No case restates or weakens the obligation.
#
#   Attack B/B' (witness discrimination, re-derived + FORGERY): for each reject
#   case, four builds. Witness vs rival: exit 0. Witness vs frozen gold: exit 1,
#   but STUCK (`did not reduce to isTrue or isFalse`) — so gold's exit code is
#   uninformative, which is why the gate falls back to a verifying positive.
#   Witness vs pos-control-direct-fold: exit 1 with `Tactic decide proved that
#   the proposition emptyCombinedTester <the concrete input> = false is false` —
#   a SEMANTIC refutation naming the input. FORGERY (the same witness with
#   `= false` flipped to `= true`, i.e. claiming the subject is WRONG where it is
#   right): exit 0 against the positive and exit 1 against gold with the
#   BYTE-IDENTICAL stuck message. That pair is the whole point: the flipped claim
#   changes the positive's verdict (1 -> 0) while leaving gold's unchanged, so the
#   attestation rests on the fallback build, which tracks the claim, and NOT on
#   gold's, which does not. No rejection here rests on an unknown identifier, a
#   type error, an unfolding failure or a timeout.
#
#   Attack C (is the rival wrong, or just reshaped?): each rival's divergence is
#   OBSERVABLE at its witnessed point, evidenced by the fallback refutation above
#   — a `decide` over the extracted program's actual result, which no reshaping
#   can produce. No rival is definitionally equal to gold on this carrier.
#
#   Attack D (further SPEC-TOO-WEAK probes beyond the four above), three NEW wrong
#   impls on axes the shipped set left open, all correctly REJECTED (exit 1):
#     * TOP fabricated from the constituent count (`!q.branches.isEmpty`) —
#       rejected with `unsolved goals ... ⊢ (!q.branches.isEmpty) = true`. This
#       one was a real coverage gap rather than a redundant probe, so it is now
#       SHIPPED as weak-top-only-when-constituents.
#     * silence only the constituents that actually contribute rows
#       (`if b.rows.isEmpty then b else silence b`) — TOP and ROWS hold, FOLD
#       breaks on already-empty constituents.
#     * blank the row set of already-silenced constituents only.
#
#   Attack E (further SPEC-TOO-STRONG probes): a FORWARD loop reshape — the
#   opposite traversal direction from the frozen backward scan, accumulating with
#   `result := result ++ [silence q.branches[i]!]` under
#   `invariant result = silenceAll (q.branches.take i)` and
#   `decreasing q.branches.length - i` — VERIFIES (exit 0) with its own take-step
#   lemma supplied as `have`s inside the tactic body. So the spec accepts both
#   traversal orders, which is the strongest available evidence it constrains
#   behavior rather than the frozen loop's shape. (Stated as `have`s deliberately:
#   `variant_scope` forbids a variant from declaring NEW top-level lemmas, so a
#   reshape needing an auxiliary fact must carry it inside the proof body — the
#   first attempt, with the lemma at top level, failed scope for that reason and
#   is a manifest-authoring trap worth recording.)
#
#   The admissibility assert is LOAD-BEARING, not decorative: replacing its row
#   claim with a FALSE one (`= [0,1,8,9,99]`) fails, and the same claim checked
#   standalone (`by decide`) fails while the true one succeeds. So the case's
#   `decide` arm is really discharging the stated non-degeneracy facts.
#
#   CARRIER FACT behind the VACUOUS frame verdict, demonstrated rather than
#   asserted: inserting `q := { q with topSilenced := true }` into the impl
#   region does not merely fail to be rejected by a permission clause — it does
#   not ELABORATE, with "`q` cannot be mutated, only variables declared using
#   `let mut` can be mutated". There is no writable read-only input on this
#   carrier, hence no frame clause a rival could violate.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md: the changed
#   operation is modeled deeply as the constituent fold, so there is no consumed
#   callee contract and G-AX skips); the sibling's AXIOM_TESTS is likewise empty.
#   This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
