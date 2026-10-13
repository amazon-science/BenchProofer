"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8595 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps RESULT onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds by construction and the ``prove_correct
selectDocumentedMembers`` obligation survives with a byte-identical statement)
and swaps in a candidate implementation. ``expect="verify"`` passes iff (in
scope AND verifies); ``expect="reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: elaborates against the
rival, fails against the frozen solution).

DEFENDED SURFACE (one contracted method):

  selectDocumentedMembers (exposeAll : Bool) (published : Option (List Int))
      (roster : List Int) (requested : List Int) return (out : MemberResult)
    ensures out = decideMembers exposeAll published roster requested
    ensures (exposeAll = true ∧ published = some []) →
              out.checkOrigin = false ∧
              out.entries = roster.map (fun n => { name := n, omitted := true })
    ensures (exposeAll = true ∧ published = none) → out.checkOrigin = true

The routine decides which of a module's roster entries to document. The single
load-bearing clause is E1 (``out = decideMembers …``), pinning the whole result
to a deep, fully-unfolded pure model over the method's own inputs (the
``axioms`` region is empty — there is no opaque answer key to echo). E2 and E3
are EMPHASIS clauses entailed by E1: they name the two sub-behaviours the fix
turns on — a supplied-but-empty published list marks every entry omitted and
requests no origin filtering (E2), while an ABSENT published list documents the
full roster and requests origin filtering (E3). ``decideMembers`` composes three
modes: full-roster-no-published (``markAllExposed``), full-roster-with-published
(``markByPublished``: an entry is marked omitted exactly when its name is NOT
among the published names, so an empty published list marks EVERYTHING omitted),
and explicit-subset (``selectRequested``).

FOUR INPUT BINDERS: ``exposeAll`` (selects mode), ``published`` (the OPTIONAL
published list — presence, not truthiness, is the fix's discriminator),
``roster`` (the candidate entries) and ``requested`` (the explicit subset, read
only when ``exposeAll = false``).

THE F2P DISCRIMINATOR — AND THE TWO TIERS OF REJECT CASE. The sole FAIL_TO_PASS
observes ONE input: implicit mode with a supplied-but-empty published list
(``exposeAll = true ∧ published = some []``), and PASS_TO_PASS is empty. The
frozen solution and the pre-image skeleton differ ONLY on that input (the
pre-image treats a present-but-empty list like an absent one). So a rival is a
GENUINE verify-does-not-imply-resolve break only if its faithful real patch
produces a non-empty documented set on that exact input — i.e. it must be wrong
in the ``omitted`` marks at ``published = some []``. The first three uniqueness
cases below are that tier, and each says so in its ``refinement``.

That argument bounds which rivals are RESOLVE-breaks. It does NOT bound which
rivals are legitimate SPEC-STRENGTH probes, and conflating the two would leave
clauses the frozen spec actually STATES with no case behind them. E3
(``published = none → checkOrigin = true``) and the ``exposeAll = false`` half of
E1 (``entries = selectRequested roster requested``, which DROPS a requested name
absent from the roster) are stated obligations; a spec that admitted a rival
violating them would be weak whether or not this instance's one test notices.
So the battery ships a second tier — ``weak-absent-no-origin-check`` and
``weak-requested-unfiltered`` — labelled explicitly as spec-strength probes
rather than resolve-breaks, with the scope limitation written into their
``refinement`` instead of a fabricated F2P story. They are also what moves
``exposeAll`` off ``true`` and ``requested`` off ``[]`` in the reject lane; with
only the first tier those binders are pinned across every witness and a rival
mishandling either goes uncaught. See the footer for the full accounting.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``selectDocumentedMembersTester exposeAll published
roster requested = false`` says the extracted program's result violates the
postcondition at that concrete input) and closes by ``decide``, checked in a
file whose ``prove_correct`` block has been stripped so no frozen tactic script
can mask the verdict. ``decide`` reduces the extracted program by kernel
computation. On the ``exposeAll = true`` branch the frozen program is loop-free
(a pure ``match``), so a witness aimed there reduces against BOTH the rival (to
``isFalse`` — the ELABORATES-against-rival half) and the frozen solution (to
``isTrue``, so ``= false`` is refuted — the FAILS-on-gold half).

The ``exposeAll = false`` branch is where that boundary bites, and it was
MEASURED rather than assumed: the frozen program's ``while`` elaborates through
``Classical.choice`` under ``loom.semantics.choice "demonic"``, which the kernel
cannot unfold, so ``decide`` against the frozen impl on that branch reports
``did not reduce to `isTrue` or `isFalse` `` for ANY claim, true or false — its
exit code discriminates nothing. That does not make the branch unattackable; it
makes GOLD the wrong second subject. ``weak-requested-unfiltered`` therefore
carries a ``witness_reference``: a loop-free impl of the same spec, which the
gate independently checks shares the frozen spec and VERIFIES before refuting
the witness against it. Every witness below was checked with
``scripts/lean_verify.sh`` — each elaborates green against its rival and fails
red against its declared subject, and each red failure was read to confirm it is
a semantic refutation (``decide`` proved the proposition false) and not a stuck
reduction, unknown identifier, or type error.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A loop-free direct return of the
    grounded model, and a loop-preserving reshape that names the assembled piece
    in a local ``let``, must both verify, else the spec is SPEC-TOO-STRONG over
    the shape of the impl. Both of those are definitionally equal to the frozen
    impl once ``decideMembers`` unfolds, so on their own they only show the spec
    admits impls the KERNEL already identifies with gold —
    ``pos-control-map-published`` is the sharper control: a published branch
    built with ``roster.map`` is equal to the frozen front-recursion only via an
    induction, so it demonstrates the spec is not over-fit to the frozen
    recursive shape.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped input satisfies its
    fractional-permission precondition. This method has NO ``require`` clause and
    there is no permission surface, so that probe is degenerate; the residual
    risk is a DEGENERATE post-image. ``admiss-nondegenerate`` discharges an
    in-region ``assert`` pinning the two turning-point behaviours (empty-published
    ⇒ everything omitted + no origin filtering; absent-published ⇒ everything
    unmarked + origin filtering) at concrete F2P-shaped inputs; the impl is kept
    verbatim so the method's own obligation still discharges.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. Lean/Velvet are
    referentially transparent: ``roster``, ``published``, ``requested`` and
    ``exposeAll`` are immutable values declared read-only (not ``mut``), there is
    no heap, no aliasing and no fractional-permission system. The sibling's two
    MANDATORY frame-mutation rivals (writing the read-only ``member_names`` /
    ``all_names`` half-permission inputs) have no carrier analogue; NOT ported
    (fabricating a substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * UNGROUNDED-ORACLE ECHO — N/A. E1 pins the result to ``decideMembers`` over
    the method's own arguments, a fully-unfolded ``def``; there is no opaque
    answer-key term a wrong impl could echo. The cheapest correct impl computes
    the decision honestly (the positive controls cover this).
  * VALUE / PARTIAL-DOMAIN — carries the reject lane: the first-tier rivals get
    most of the domain right yet diverge on the ``published``-branch omitted marks
    (treat empty-published as absent; invert the omitted test; leave the first
    entry unmarked), and the second-tier probes attack the absent-published
    origin flag (E3) and the explicit-subset membership filter.

AXIOM_TESTS is empty — the bundle declares no axiom (mapping.md §3/§5: the
decision is modeled deeply and validated by G-CONF; G-AX is skipped). This gate
ignores AXIOM_TESTS regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8595"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each lies WHOLLY inside the impl region (or is the frozen proof
# body) and is unique in the file; both facts asserted at load so the manifest
# breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole `exposeAll = true` branch decision (the loop-free `match`). The
# empty-published / invert / skip-first rivals reshape ONLY this block.
_EXPOSE_MATCH = """      let r : MemberResult :=
        match published with
        | none =>
            { checkOrigin := true, entries := markAllExposed roster }
        | some pub =>
            { checkOrigin := false, entries := markByPublished pub roster }
      return r"""
assert _BASE.count(_EXPOSE_MATCH) == 1, "expose-match anchor drift"

# The loop body of the explicit-subset branch. The loop-preserving positive
# names the assembled piece in a local `let`, leaving the loop, invariants and
# frozen proof intact.
_LOOP_BODY = """      do
        let n := requested[i - 1]!
        result := (if n ∈ roster then [{ name := n, omitted := false }] else []) ++ result
        i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# The whole impl block (markers included) — the direct-model positive replaces
# it with a single grounded return.
_IMPL = _BASE[_BASE.index("    -- impl-start"):
              _BASE.index("    -- impl-end") + len("    -- impl-end")]
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift"

# The impl-start marker line — the admissibility case inserts an in-region
# `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen proof body (tactic script only; elided from the spec view).
_PROOF = _BASE[_BASE.index("prove_correct selectDocumentedMembers"):]
assert _BASE.count(_PROOF) == 1, "proof anchor drift"

# A flat proof for a loop-free impl: no loop invariant to peel, so `loom_solve`
# plus a `simp` over the grounded model discharges the equality (for a correct
# reshape) or leaves it unsolved (for the reject rivals — the point).
_PROOF_FLAT = ("prove_correct selectDocumentedMembers by\n"
               "  loom_solve <;> simp_all [decideMembers]\n")

# A proof for a published-branch reshape that is NOT definitionally equal to the
# frozen front-recursion: the bridging fact is established as an in-tactic `have`
# (no new top-level lemma) by induction over the roster, then handed to `simp_all`.
_PROOF_MAP = (
    "prove_correct selectDocumentedMembers by\n"
    "  have key : ∀ (pub rs : List Int),\n"
    "      rs.map (fun n => { name := n, omitted := decide (n ∉ pub) }) = markByPublished pub rs := by\n"
    "    intro pub rs\n"
    "    induction rs with\n"
    "    | nil => rfl\n"
    "    | cons n ns ih => simp only [List.map_cons, markByPublished_cons, ih]\n"
    "  loom_solve <;>\n"
    "    first\n"
    "      | (rw [selectRequested_drop_step roster requested i (by omega) (by omega)];\n"
    "         rw [‹result = selectRequested roster (requested.drop i)›])\n"
    "      | (subst done_1; simp_all [decideMembers])\n"
    "      | (simp_all [decideMembers, key])\n"
    "      | simp_all [decideMembers]\n")


def _tester(body):
    """A witness reaches the post-image through Velvet's own tester machinery;
    checked in a file whose `prove_correct` block has been stripped. Every
    argument is a concrete literal so `decide` reduces the (loop-free
    exposeAll-branch) extracted program without getting stuck."""
    return ("\n"
            "extract_program_for selectDocumentedMembers\n"
            "prove_precondition_decidable_for selectDocumentedMembers\n"
            "prove_postcondition_decidable_for selectDocumentedMembers\n"
            "derive_tester_for selectDocumentedMembers\n\n" + body)


def _witness(exposeAll, published, roster, requested):
    return _tester(
        f"example : selectDocumentedMembersTester {exposeAll} {published} "
        f"{roster} {requested} = false := by\n  decide\n")


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen impl shape).
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no branch structure and no loop at all — maximally different from the
        # gold match/while shape. `out` IS `decideMembers …`, so E1 holds
        # trivially and E2/E3 follow; the reproof is a flat `loom_solve` + simp.
        "module": _swap(_swap(_BASE, _IMPL,
                              "    -- impl-start\n"
                              "    return decideMembers exposeAll published roster requested\n"
                              "    -- impl-end"),
                        _PROOF, _PROOF_FLAT),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`decideMembers exposeAll published roster requested` directly (no "
            "branch, no loop). `out` IS that model, so E1 holds on the whole "
            "domain and E2/E3 follow; the reproof is `loom_solve <;> simp_all "
            "[decideMembers]`. If this fails to verify the spec is over-fit to "
            "the impl shape (SPEC-TOO-STRONG). Also the honest no-ungrounded-echo "
            "control: `decideMembers` is the real work, so a direct return is "
            "correct, not a cheat. (Sibling: pos-control-branch-reorder — a "
            "structurally different correct impl.)"),
    },
    {
        "id": "pos-control-named-piece",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole explicit-subset loop, its invariants and the frozen
        # proof script; only names the assembled fold piece in a local `let`
        # before prepending it. Observationally identical for every input.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      do\n"
            "        let n := requested[i - 1]!\n"
            "        let piece := if n ∈ roster then [{ name := n, omitted := false }] else []\n"
            "        result := piece ++ result\n"
            "        i := i - 1"),
        "rationale": (
            "naming the assembled membership piece in a local `let piece` before "
            "prepending it folds the same stream with the same step, so `out = "
            "decideMembers …` still holds on the whole domain; the loop, "
            "invariants and frozen proof script are untouched. A correct reshape "
            "inside the frozen loop must verify, else the postcondition is "
            "SPEC-TOO-STRONG. (Sibling: pos-control-branch-reorder, reshaped to a "
            "loop-preserving form.)"),
    },

    {
        "id": "pos-control-map-published",
        "kind": "soundness",
        "expect": "verify",
        # A correct reshape of the PUBLISHED branch that is NOT definitionally
        # equal to the frozen front-recursion: `roster.map` with the same
        # per-entry test, so `rfl`/`decide` do NOT close the equality and the
        # reproof must supply a real bridging induction. This is the positive
        # that distinguishes "the spec admits a differently-SHAPED correct impl"
        # from "the spec admits impls the kernel already identifies with gold".
        "module": _swap(
            _swap(_BASE, _EXPOSE_MATCH,
                  "      let r : MemberResult :=\n"
                  "        match published with\n"
                  "        | none =>\n"
                  "            { checkOrigin := true, entries := markAllExposed roster }\n"
                  "        | some pub =>\n"
                  "            { checkOrigin := false,\n"
                  "              entries := roster.map (fun n => { name := n, omitted := decide (n ∉ pub) }) }\n"
                  "      return r"),
            _PROOF, _PROOF_MAP),
        "rationale": (
            "computing the published branch as `roster.map (fun n => { name := n, "
            "omitted := decide (n ∉ pub) })` instead of the frozen front-recursive "
            "`markByPublished` is a genuinely different SHAPE — the two are equal "
            "only by an induction over the roster, which the reproof supplies as an "
            "in-tactic `have` (no new top-level lemma, so the variant scope is "
            "untouched). This is a strictly sharper soundness control than "
            "pos-control-direct-model and pos-control-named-piece, whose bodies the "
            "kernel identifies with the frozen one by unfolding alone: it shows the "
            "spec admits a correct impl that is NOT definitionally the frozen "
            "impl. If it failed, E1 would be over-fit to the frozen recursion "
            "(SPEC-TOO-STRONG)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause and no permission
    # surface, so the sibling's "a normal input satisfies the precondition"
    # probe is degenerate here. The residual admissibility risk is that the
    # post-image is DEGENERATE at the interesting point. This case discharges an
    # in-region `assert`, at concrete F2P-shaped inputs, that the post-image is
    # NON-DEGENERATE: a supplied-but-empty published list marks EVERY entry
    # omitted and requests no origin filtering (E2, the fixed behaviour), while
    # an ABSENT published list marks every entry UNMARKED and requests origin
    # filtering (E3) — two genuinely distinct outcomes on the same roster. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      decideMembers true (some []) [1, 2, 3] [] =\n"
                  "          { checkOrigin := false,\n"
                  "            entries := [{ name := 1, omitted := true }, { name := 2, omitted := true }, { name := 3, omitted := true }] } ∧\n"
                  "      decideMembers true none [1, 2, 3] [] =\n"
                  "          { checkOrigin := true,\n"
                  "            entries := [{ name := 1, omitted := false }, { name := 2, omitted := false }, { name := 3, omitted := false }] }))\n"),
            _PROOF,
            "prove_correct selectDocumentedMembers by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "      | decide\n"
            "      | (rw [selectRequested_drop_step roster requested i (by omega) (by omega)];\n"
            "         rw [‹result = selectRequested roster (requested.drop i)›])\n"
            "      | (subst done_1; simp_all [decideMembers])\n"
            "      | simp_all [decideMembers]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: a supplied-but-empty published list must mark every roster "
            "entry omitted with no origin filtering requested (E2 — the fixed "
            "behaviour), while an absent published list must leave every entry "
            "unmarked and request origin filtering (E3) — two distinct outcomes "
            "on the same roster. The in-region assert must discharge (else the "
            "obligation is degenerate / no input distinguishes the modes); the "
            "impl is kept verbatim so `out = decideMembers …` still verifies. "
            "(Sibling: admiss-cleared-flags, re-aimed from precondition "
            "admissibility to post-image non-degeneracy — this backend has no "
            "`require` clause and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # patch would NOT resolve the sole F2P (documents a non-empty set under an
    # empty published list). Every witness is aimed at the loop-free
    # `exposeAll = true` branch so its extracted tester `decide`s.
    # =====================================================================
    {
        "id": "weak-empty-published-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported bug transcribed onto the carrier: a supplied-but-empty
        # published list is treated like an ABSENT one — the full roster is
        # returned UNMARKED and origin filtering is requested, instead of every
        # entry marked omitted. Correct on absent-published, on every non-empty
        # published list, and on the explicit-subset branch; diverges ONLY on the
        # empty-published sub-domain — the exact F2P discriminator.
        "module": _swap(
            _BASE, _EXPOSE_MATCH,
            "      let r : MemberResult :=\n"
            "        match published with\n"
            "        | none =>\n"
            "            { checkOrigin := true, entries := markAllExposed roster }\n"
            "        | some pub =>\n"
            "            if pub = [] then\n"
            "              { checkOrigin := true, entries := markAllExposed roster }\n"
            "            else\n"
            "              { checkOrigin := false, entries := markByPublished pub roster }\n"
            "      return r"),
        "refinement": (
            "this is the pre-change behaviour: the truthiness short-circuit "
            "treats a present-but-empty published list identically to an absent "
            "one, so an empty published list documents the WHOLE roster unmarked. "
            "That is exactly the bug the sole F2P reports — under an empty "
            "published list the members are all shown instead of none — so the "
            "faithful patch does NOT resolve. Correct on every other input (a "
            "true partial-domain break confined to the empty-published "
            "sub-domain)."),
        "rationale": (
            "REJECT from E1/E2: when `published = some []` the spec pins "
            "`checkOrigin = false` and every entry `omitted = true`, but this "
            "rival returns `checkOrigin = true` with every entry unmarked. "
            "Verifying would be SPEC-TOO-WEAK (the empty-published behaviour "
            "unpinned). Refuted at `published = some []`, roster `[1,2]`. "
            "(Sibling: partial-domain-empty-all.)"),
        "witness": _witness("true", "(some [])", "[1, 2]", "[]"),
    },
    {
        "id": "weak-invert-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        # INVERT the omitted test: mark an entry omitted exactly when its name IS
        # among the published names (should be when it is NOT). So a published
        # list documents the entries it does NOT name and omits the ones it does
        # — the inverse of the requirement. For an empty published list it marks
        # everything UNMARKED (documents everything), reproducing the bug.
        "module": _swap(
            _BASE, _EXPOSE_MATCH,
            "      let r : MemberResult :=\n"
            "        match published with\n"
            "        | none =>\n"
            "            { checkOrigin := true, entries := markAllExposed roster }\n"
            "        | some pub =>\n"
            "            { checkOrigin := false, entries := roster.map (fun n => { name := n, omitted := decide (n ∈ pub) }) }\n"
            "      return r"),
        "refinement": (
            "a faithful counterpart that marked an entry omitted exactly when its "
            "name IS published would document precisely the entries the list does "
            "NOT name and hide the ones it does — the inverse of the requirement. "
            "For the empty published list of the sole F2P it marks nothing "
            "omitted, so all members are shown instead of none — it does NOT "
            "resolve. Correct on absent-published and on the explicit-subset "
            "branch."),
        "rationale": (
            "REJECT from E1: the spec pins `omitted = decide (n ∉ pub)`, this "
            "rival returns `decide (n ∈ pub)`. Refuted at `published = some [1]`, "
            "roster `[1,2]` — a NON-EMPTY published list (so gold marks 1 kept, 2 "
            "omitted; the rival marks 1 omitted, 2 kept). This is the point that "
            "proves the published-list CONTENT is load-bearing and separates this "
            "rival from the empty-as-absent rival (which is CORRECT at "
            "`some [1]`). Verifying would be SPEC-TOO-WEAK (the omitted test "
            "unpinned). (Sibling: weak-invert-exclusion.)"),
        "witness": _witness("true", "(some [1])", "[1, 2]", "[]"),
    },
    {
        "id": "weak-skip-first-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # OFF-BY-ONE on the published branch: leave the FIRST roster entry always
        # unmarked, marking the rest correctly. Correct for every entry except
        # the first -> under an empty published list the first member stays
        # documented when it should be omitted.
        "module": _swap(
            _BASE, _EXPOSE_MATCH,
            "      let r : MemberResult :=\n"
            "        match published with\n"
            "        | none =>\n"
            "            { checkOrigin := true, entries := markAllExposed roster }\n"
            "        | some pub =>\n"
            "            { checkOrigin := false,\n"
            "              entries := match roster with\n"
            "                         | []      => []\n"
            "                         | m :: ms => { name := m, omitted := false } :: markByPublished pub ms }\n"
            "      return r"),
        "refinement": (
            "a faithful counterpart that never marked the FIRST discovered entry "
            "omitted would leave it documented even when the published list omits "
            "it; with the empty published list of the sole F2P the first of the "
            "members stays shown instead of hidden — it does NOT resolve. Correct "
            "for every entry after the first (an off-by-one break)."),
        "rationale": (
            "REJECT from E1/E2: the spec pins EVERY entry's omitted mark (for "
            "`published = some []`, all `true`), but this rival leaves the first "
            "entry `omitted = false`. Verifying would be SPEC-TOO-WEAK (the "
            "first-entry mark unpinned). Refuted at `published = some []`, roster "
            "`[1,2,3]` (length 3, so the divergence is on a distinct roster from "
            "the empty-as-absent rival, and the surviving first-entry mark is "
            "observable past the skipped head). (Sibling: partial-domain-skip-"
            "first.)"),
        "witness": _witness("true", "(some [])", "[1, 2, 3]", "[]"),
    },
    {
        "id": "weak-absent-no-origin-check",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks clause E3 DIRECTLY: on the ABSENT-published path return the
        # full roster unmarked (correct) but do NOT ask the caller to filter by
        # origin. Correct on every `some pub` input and on the explicit-subset
        # branch; diverges only in `checkOrigin` at `published = none`.
        "module": _swap(
            _BASE, _EXPOSE_MATCH,
            "      let r : MemberResult :=\n"
            "        match published with\n"
            "        | none =>\n"
            "            { checkOrigin := false, entries := markAllExposed roster }\n"
            "        | some pub =>\n"
            "            { checkOrigin := false, entries := markByPublished pub roster }\n"
            "      return r"),
        "refinement": (
            "SCOPE, STATED HONESTLY: this rival's faithful counterpart drops the "
            "caller-side origin-filter request on the absent-published path, and "
            "the sole F2P supplies a PRESENT published list, so that test does not "
            "observe this divergence — a faithful patch of this rival would still "
            "resolve it. This case is therefore shipped as a SPEC-STRENGTH probe of "
            "clause E3, not as a verify-does-not-imply-resolve break, and it is "
            "labelled as such rather than given a fabricated F2P story. It earns "
            "its place because E3 is a clause the frozen spec actually STATES: if "
            "the spec admitted this rival, E3 would be unpinned and the modeled "
            "absent-published behaviour (document the full roster AND have the "
            "caller filter by origin) would be a claim no case could support. "
            "Behaviourally the divergence is real, not cosmetic: it changes which "
            "implicit entries the caller subsequently keeps."),
        "rationale": (
            "REJECT from E3 (`published = none → out.checkOrigin = true`) and from "
            "E1: the spec pins `checkOrigin = true` on the absent-published path, "
            "this rival returns `false`. Refuted at `published = none`, roster "
            "`[1,2]` — the only reject witness in this battery on the "
            "ABSENT-published sub-domain, so it is the one case that makes E3 "
            "attacked rather than merely asserted. Verifying would be "
            "SPEC-TOO-WEAK (E3 unpinned). (Sibling: control-flow-wrong-result / "
            "weak-absent-excludes, which the earlier port dropped as not "
            "F2P-observable; re-landed here because the clause is stated in the "
            "frozen spec and the witness discriminates.)"),
        "witness": _witness("true", "none", "[1, 2]", "[]"),
    },
    {
        "id": "weak-requested-unfiltered",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the EXPLICIT-SUBSET branch: return every requested name
        # unmarked WITHOUT checking it exists in the roster (the spec drops a
        # requested name absent from the roster). Also the only case that varies
        # `exposeAll` and `requested` off their otherwise-pinned values.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    if exposeAll then\n"
                  "      let r : MemberResult :=\n"
                  "        match published with\n"
                  "        | none =>\n"
                  "            { checkOrigin := true, entries := markAllExposed roster }\n"
                  "        | some pub =>\n"
                  "            { checkOrigin := false, entries := markByPublished pub roster }\n"
                  "      return r\n"
                  "    else\n"
                  "      return { checkOrigin := false,\n"
                  "               entries := requested.map (fun n => { name := n, omitted := false }) }\n"
                  "    -- impl-end"),
            _PROOF, _PROOF_FLAT),
        "refinement": (
            "SCOPE, STATED HONESTLY: like the case above, this rival's faithful "
            "counterpart is wrong only on the explicitly-requested-subset path, "
            "which the sole F2P (a full-roster input) does not drive, so a faithful "
            "patch would still resolve it. Shipped as a SPEC-STRENGTH probe of the "
            "`exposeAll = false` half of E1, labelled as such. It earns its place "
            "for two reasons the manifest can demonstrate: E1 pins the "
            "explicit-subset branch to `selectRequested`, which DROPS a requested "
            "name that does not exist in the roster, and this rival returns it "
            "anyway — a genuine value divergence on a sub-domain the frozen spec "
            "governs; and it is the ONLY case in the battery that moves `exposeAll` "
            "off `true` and `requested` off `[]`, so without it those two binders "
            "are pinned across the whole reject lane and a rival mishandling either "
            "would go uncaught (the coverage reporter flags exactly that)."),
        "rationale": (
            "REJECT from E1 on the `exposeAll = false` branch: the spec pins "
            "`out.entries = selectRequested roster requested`, which keeps a "
            "requested name only when `n ∈ roster`; this rival returns every "
            "requested name unconditionally. Refuted at `exposeAll = false`, "
            "`published = none`, roster `[1]`, requested `[2]` — a requested name "
            "absent from the roster, the exact point the membership filter "
            "decides. Verifying would be SPEC-TOO-WEAK (the roster-membership "
            "filter unpinned). NOTE the witness subject: the FROZEN impl's "
            "`exposeAll = false` branch is a `while` under demonic choice, which "
            "`decide` cannot reduce (measured: `did not reduce to isTrue or "
            "isFalse`), so gold cannot serve as the discriminating subject here. "
            "The case supplies a `witness_reference` — the loop-free direct-model "
            "impl, which the gate independently checks shares the frozen spec and "
            "VERIFIES — and the witness is refuted against that instead."),
        "witness": _witness("false", "none", "[1]", "[2]"),
        # Gold's loop branch is kernel-irreducible, so the second half of the
        # discrimination check is run against a VERIFYING loop-free impl of the
        # same spec (identical to pos-control-direct-model's module).
        "witness_reference": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    return decideMembers exposeAll published roster requested\n"
                  "    -- impl-end"),
            _PROOF, _PROOF_FLAT),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (1
# soundness, 1 admissibility, 7 uniqueness — two of which are MANDATORY
# frame-mutation rivals) plus an EMPTY axiom lane. The sibling contracts
# `select_module_members` over Nagini's carrier (a full-permission mutable
# `excluded` flag list plus two half-permission read-only inputs `member_names`,
# `all_names`, and a boolean Result()). This backend models the SAME decision
# DEEPLY and CONCRETELY (`decideMembers` over the `Option (List Int)` published
# list, `MemberResult`/`MemberOut` carriers), pinning the whole result to one
# grounded `ensures`. Two facts drive the porting map:
#   (a) referential transparency collapses the frame/permission class;
#   (b) the sole F2P (`test_empty_all`) observes ONLY the empty-published input
#       and PASS_TO_PASS is empty, so a rival is a genuine break only if its
#       faithful patch is wrong THERE (see the DEFENDED-SURFACE note).
#
#   sibling case                     kind          -> here                           disposition
#   -----------------------------------------------------------------------------------------------
#   pos-control-branch-reorder       soundness     -> pos-control-direct-model       RE-SHAPED
#                                                     (+ pos-control-named-piece      ADDED)
#                                                     (+ pos-control-map-published    ADDED)
#   admiss-cleared-flags             admissibility -> admiss-nondegenerate           RE-AIMED
#   frame-mutation-member-names      uniqueness    -> (none)                         VACUOUS (carrier)
#   frame-mutation-all-names         uniqueness    -> (none)                         VACUOUS (carrier)
#   weak-invert-exclusion            uniqueness    -> weak-invert-omitted            PORTED
#   partial-domain-empty-all         uniqueness    -> weak-empty-published-as-absent PORTED
#   partial-domain-skip-first        uniqueness    -> weak-skip-first-entry          PORTED
#   control-flow-wrong-result        uniqueness    -> weak-absent-no-origin-check     PORTED (tier 2)
#   weak-absent-excludes             uniqueness    -> weak-absent-no-origin-check     MERGED (tier 2)
#   (no sibling)                     uniqueness    -> weak-requested-unfiltered       ADDED (tier 2)
#   AXIOM_TESTS (none)               axiom         -> (none)                         N/A (G-AX skip)
#
# 5 uniqueness (3 tier-1 resolve-breaks + 2 tier-2 spec-strength probes),
# 1 admissibility re-aimed, 1 soundness re-shaped + 2 added; 2 uniqueness vacuous
# (frame, a genuine carrier fact).
#
# AUDIT CORRECTION (this file was repaired after its first SOUND). The port had
# dropped control-flow-wrong-result and weak-absent-excludes as "NOT
# F2P-OBSERVABLE" and recorded the reject lane's pinned `exposeAll`/`requested`
# binders as pinned BY DESIGN. The F2P-scope argument is sound as far as it goes —
# neither rival's faithful patch breaks the sole F2P — but it was applied to the
# wrong question. G-PBT judges SPEC STRENGTH, and E3 plus the `exposeAll = false`
# half of E1 are clauses the frozen spec STATES; leaving them unattacked meant the
# battery asserted them and demonstrated nothing about them. Both rivals were then
# landed with discriminating witnesses on the real verifier, which also settles
# the "not attackable here" reading: the absent-published rival refutes against
# gold directly, and the explicit-subset rival needed only a `witness_reference`
# because gold's loop is kernel-irreducible — a subject problem, not an
# expressibility one. The dropped cases were expressible; they are now shipped,
# each labelled tier-2 so no reader mistakes them for resolve-breaks.
#
# RE-SHAPED (pos-control-branch-reorder -> pos-control-direct-model): the sibling's
#   positive reorders the per-member assignment branches. On this carrier the
#   maximally-different correct impl is a loop-free direct return of the grounded
#   model `decideMembers …`; a second, loop-PRESERVING correct reshape
#   (pos-control-named-piece) is ADDED so the soundness surface is defended both
#   from a completely different control-flow shape AND from a minimal edit inside
#   the frozen loop (which keeps the frozen proof intact). Both verify.
# RE-AIMED (admiss-cleared-flags -> admiss-nondegenerate): the sibling asserts the
#   cleared-flags Requires is derivable at an F2P-shaped input. This method has no
#   `require` clause and no permission surface, so that probe is degenerate; the
#   sharper residual risk is a DEGENERATE post-image, so the case is re-aimed to a
#   live in-region assert pinning the two turning-point behaviours (empty-published
#   ⇒ all omitted + no origin filtering; absent-published ⇒ all unmarked + origin
#   filtering) at concrete F2P-shaped inputs. Verifies.
# PORTED (three value/branch rivals): partial-domain-empty-all ports directly to
#   weak-empty-published-as-absent (the literal pre-patch shape; refuted at
#   `published = some []`). weak-invert-exclusion ports to weak-invert-omitted
#   (the omitted test inverted; refuted at a NON-EMPTY published list, the point
#   that makes the list content load-bearing and separates it from the
#   empty-as-absent rival). partial-domain-skip-first ports to weak-skip-first-
#   entry (first entry left unmarked; refuted on a length-3 roster).
# VACUOUS (frame-mutation-member-names, frame-mutation-all-names): the sibling's
#   two MANDATORY frame rivals write the read-only half-permission `member_names`
#   / `all_names` inputs and are rejected for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent: every input is an immutable value
#   declared read-only (not `mut`), there is no heap, no aliasing, no fractional
#   permission. There is no read-only input to overwrite and no permission clause
#   to trip — the class has no carrier analogue. Omitted as a genuine carrier
#   fact, NOT fabricated (per the porting map, this class is vacuous on a
#   referentially-transparent backend).
# TIER 2 (weak-absent-no-origin-check <- control-flow-wrong-result +
#   weak-absent-excludes; weak-requested-unfiltered <- new): both attack clauses the
#   frozen spec states but the sole F2P does not exercise — the absent-published
#   origin flag (E3) and the explicit-subset membership filter (E1 at
#   `exposeAll = false`). Their `refinement` fields say plainly that a faithful
#   patch of either would still resolve the sole F2P, so neither is claimed as a
#   verify-does-not-imply-resolve break; they are claimed as spec-strength probes,
#   which is what G-PBT measures. Shipping them costs nothing in honesty (the scope
#   limit is written down) and buys the only reject-lane coverage of E3, of the
#   `exposeAll = false` branch, and of the `requested` binder.
#
# BINDER / CLAUSE COVERAGE. The load-bearing clause E1 (`out = decideMembers
#   exposeAll published roster requested`) has FOUR binders; E2/E3 are emphasis
#   clauses entailed by E1. The five reject witnesses probe five DISTINCT input
#   points:
#     * weak-empty-published-as-absent  (true,  some [],  [1,2],   [])
#     * weak-invert-omitted             (true,  some [1], [1,2],   [])
#     * weak-skip-first-entry           (true,  some [],  [1,2,3], [])
#     * weak-absent-no-origin-check     (true,  none,     [1,2],   [])
#     * weak-requested-unfiltered       (false, none,     [1],     [2])
#   All FOUR binders now vary in the reject lane, and each variation is
#   verdict-changing rather than a respelling of the same point:
#     - `published` ranges over {none, some [], some [1]} — the three-way
#       ABSENT / PRESENT-BUT-EMPTY / PRESENT-AND-NAMING split that is the whole
#       point of the `Option (List Int)` carrier. `none` vs `some []` is exactly
#       the distinction the frozen spec turns on, and it is load-bearing in both
#       directions here: the empty-as-absent rival is refuted at `some []` and is
#       CORRECT at `none`, while the absent-no-origin rival is refuted at `none`
#       and CORRECT at `some []`.
#     - `roster` ranges over lengths {1,2,3} with membership exercised both ways
#       (invert-omitted drives 1∈[1] and 2∉[1]).
#     - `exposeAll` takes BOTH values (weak-requested-unfiltered is the `false`
#       point), so the mode selector is attacked, not merely assumed.
#     - `requested` is non-empty and DISJOINT from the roster at that point
#       (`[2]` against roster `[1]`), which is the input the membership filter
#       decides; the positives additionally exercise the loop over it.
#   Clause coverage: E1 attacked by all five rivals, on both branches, and its
#   non-empty-published sub-domain is pinned independently of E2/E3 (a rival
#   satisfying E2 and E3 exactly while returning the roster unmarked for every
#   non-empty published list is still rejected — measured during the audit).
#   E2 (empty-published ⇒ all omitted, no origin filtering) attacked by
#   weak-empty-published-as-absent and weak-skip-first-entry, and its
#   `checkOrigin` half separately by a `decide (pub = [])` rival measured during
#   the audit. E3 (absent-published ⇒ checkOrigin true) is now ATTACKED by
#   weak-absent-no-origin-check as well as pinned by admiss-nondegenerate.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3/§5: the decision
#   is modeled deeply, validated by G-CONF; G-AX is skipped). The sibling's
#   AXIOM_TESTS is likewise empty. This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
