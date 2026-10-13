"""properties.py — G-PBT falsification battery for django__django-13810 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct loadPipeline`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against its ``witness_reference`` — a verifying impl of the same spec, used here
because the frozen tester cannot be decided at all; see the CARRIER NOTE).

DEFENDED SURFACE (one contracted method over two read-only inputs):

  loadPipeline (init : Chain) (stages : List Stage) return (out : Chain)
    require init.flag = init.hmode
    ensures out = assemble init stages            -- (C1) the whole fold
    ensures out.flag = out.hmode                  -- (C2) the assembled state
                                                  --      is CONSISTENT

The method assembles a processing pipeline by wiring a list of configured
``stages`` left to right onto an initial state, starting from a state whose
RECORDED execution mode already matches its ACTUAL mode. Each stage is wired
under the mode the running state is recorded to run in; a stage that INSTALLS
advances BOTH the recorded and the actual mode together to the mode it was wired
at, and a stage that DECLINES must leave the running state untouched on BOTH
components.

  * (C1) pins ``out`` to ``assemble init stages`` — the fully-unfolded
    front-recursive fold of ``wireStage`` over the method's own input list. This
    is a TRANSPARENT ``def`` over the two arguments (the ``axioms`` region
    declares no opaque leaf and no ``axiom``); there is no answer-key oracle to
    echo, so pinning ``out`` to it is grounded, not an echo. Every wiring
    decision — which target mode a stage is wired at (``stageMode``), how the
    running actual mode is coerced (``adaptedMode``), and crucially that a
    DECLINING stage leaves the running state UNCHANGED — is pinned by C1 at every
    position.
  * (C2) pins the assembled state to be CONSISTENT: recorded mode equals actual
    mode. This is the health condition the assembly must preserve; a state whose
    recorded mode lies about its actual mode silently mis-wires every later stage
    and (on the real target) makes the assembled pipeline run in a mode other
    than the one it reports.

TWO INPUT BINDERS: ``init : Chain`` (constrained by ``require`` to a CONSISTENT
state, so it ranges over the two consistent values only) and ``stages : List
Stage`` (each element carries ``canSync`` / ``canAsync`` / ``usable``). Both are
load-bearing: ``init`` is the fold's seed and the consistency the postcondition
must carry through, and each ``stages`` element selects a target mode, a
coercion, and whether the running state advances or is left untouched. The
reject witnesses drive them across SIX distinct input points so the manifest
demonstrates the post-image's dependence on the seed, on ``usable``, on the
capability flags, on the DECLINE-leaves-untouched frame, and on the ORDER of the
stage stream — not on a single pinned shape (pts = 6).

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHAT THE GOLD-SIDE FAILURE IS WORTH.
A witness reaches the post-image through Velvet's tester machinery
(``loadPipelineTester init stages = false`` says the extracted program's result
violates the conjoined postcondition C1 ∧ C2 at that concrete input) and closes
by ``decide``, checked in a file whose ``prove_correct`` block has been stripped
so no tactic script can mask the verdict. ``decide`` reduces the extracted
program by kernel computation. Each reject rival is expressed as a LOOP-FREE
fold (``stages.foldl`` with a wrong per-stage step) so its extracted tester
``decide``s over the concrete literal; the frozen program is a ``while`` loop
whose fixpoint the kernel will not unfold, so the same witness applied to the
FROZEN solution does NOT reduce to ``isTrue``/``isFalse``.

READ THAT HONESTLY. The gate's FAIL-on-gold half is therefore satisfied here for
a REDUCTION-STUCK reason, not by a semantic refutation of gold — the frozen
tester is opaque to ``decide``, so gold's build would fail for a TAUTOLOGOUS
witness too. That half alone consequently attests nothing about
discrimination on this bundle, and the CONTROL below is what does:

  DISCRIMINATION CONTROL (measured, not argued). Every reject witness was also
  built against a CORRECT loop-free fold — the same ``stages.foldl`` shape as the
  rivals, with the RIGHT per-stage step, which verifies against the frozen spec
  (shipped as ``pos-control-foldl-correct-step``). There the tester DOES reduce,
  and ``decide`` refutes each witness SEMANTICALLY: `Tactic `decide` proved that
  the proposition loadPipelineTester … = false is false` (exit 1, all six). So
  each witness holds of its rival's step and provably FAILS of the correct step
  at the same input on the same carrier shape. That is the discrimination the
  stuck-on-gold build cannot supply.
  This is not merely documented, it is ENFORCED: every reject case names that
  impl as its ``witness_reference``, so the gate itself verifies the reference
  shares the frozen spec and VERIFIES, then refutes the witness against IT
  rather than against the undecidable frozen tester. The recorded
  ``witness_subject`` for all six reads "the reference impl".

Every carrier value is fully transparent, so no witness binds a hypothesis and
no consistency probe is needed. All witnesses checked out-of-band with
``scripts/lean_verify.sh``: ELABORATES against its rival (exit 0), refuted
against the correct-step fold (exit 1, `decide` proved it false), stuck against
the frozen loop (exit 1).

PROOF-SHAPE CONTROL — why each rejection is attributable to the STEP. A reject
rival's proof body must not be a script that would also fail for a CORRECT impl
of the same shape, or the rejection attests to a tactic mismatch. Measured: the
naive flat body (``loom_solve`` alone) fails IDENTICALLY on a loop-free fold with
the CORRECT step (exit 1, same two unsolved ``ensures`` goals) — so it would have
been exactly that confound. Every reject rival therefore carries
``_PROOF_FOLD``, a body whose ``hfold`` induction lemma PROVABLY closes both
clauses for the correct step (that is ``pos-control-foldl-correct-step``, exit
0). Under it each rival still fails, and the residual goal names the rival's own
step (`Type mismatch … expected (List.foldl (fun c s => <the rival's step>) init
stages).flag = …`), which is the attribution.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded model directly; keep the
    loop and the frozen proof but name the wired state in a local; or fold the
    correct per-stage step loop-free) must verify, else the spec is
    SPEC-TOO-STRONG on the shape of the impl. The third of those is also this
    battery's interpretive control — see the CARRIER NOTE.
  * ADMISSIBILITY — the sibling self-asserts that an F2P-shaped pair of
    equal-length read-only columns satisfies its fractional-permission
    precondition. This backend's only ``require`` is ``init.flag = init.hmode``
    (met by every consistent seed) and there is no permission surface, so that
    probe is degenerate; the residual risk on this domain is a DEGENERATE
    post-image. ``admiss-nondegenerate`` discharges an in-region ``assert``
    pinning that the fold genuinely discriminates the two outcomes (an installing
    stage advances the state; a declining stage leaves it untouched) and that the
    installed outcome is consistent — at concrete F2P-shaped inputs. The impl is
    kept verbatim so the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries TWO MANDATORY
    frame-mutation rivals (write into the read-only ``declines`` column, and into
    the read-only ``target_mode`` column) each rejected for INSUFFICIENT
    PERMISSION because the input is held at a fractional heap permission. Lean and
    Velvet are referentially transparent: ``init`` and ``stages`` are immutable
    values declared read-only (no input is ``mut`` — only the loop-local
    ``chain`` / ``i`` are), there is no heap, no aliasing, and no permission
    system. There is no read-only input to overwrite. The class has no carrier
    analogue; fabricating a substitute would test nothing.
  * UNGROUNDED-ORACLE ECHO — N/A. C1 is pinned to ``assemble init stages``, a
    fully-unfolded ``def`` over the method's own arguments; there is no answer-key
    term a wrong impl could echo. The cheapest correct impl computes the fold
    honestly, which the positive controls cover.
  * CONTROL-FLOW-EFFECT (raise vs return) — the only control-flow difference in
    the modeled behaviour (a stage raising ``MiddlewareNotUsed`` and being
    skipped) is ALREADY abstracted to the data field ``Stage.usable``, and its
    sole observable effect (the stage is skipped, leaving no trace on the running
    state) is fully captured by the C1 value fold's decline branch
    (``wireStage``'s ``else c``). There is no raise/side-effect difference
    invisible to the value model, so no capability-token rival is needed.
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
    loop in the impl (1 loop here, measure ``stages.length - i``). A rival that
    loops without a measure is refused outright (``Decreasing annotations are
    required in total correctness semantics``), and a rival that supplies a
    CONSTANT measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the pre-patch skip-carries-the-
    coercion bug; advancing the recorded mode on a decline; installing a declining
    stage; wiring nothing; installing without coercing the actual mode).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The bundle consumes no ``axiom`` —
the two unchanged primitives (``stageMode``, ``adaptedMode``) are A-reference
DEEP MODELS validated ``==`` the real callees by G-AX (mapping.md §3), not
consumed contracts — so there is nothing here for this gate to probe, and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13810"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Reject rivals that reshape the executable surface
# ---- into a loop-free fold swap on this block; the direct-model positive too.
_IMPL = """    -- impl-start
    let mut chain : Chain := init
    let mut i := 0
    while i < stages.length
      invariant i ≤ stages.length
      invariant chain = assemble init (stages.take i)
      done_with i = stages.length
      decreasing stages.length - i
    do
      let s := stages[i]!
      let target := stageMode chain.flag s
      let amode  := adaptedMode chain.hmode chain.flag target
      chain := if s.usable = true then { flag := target, hmode := amode } else chain
      i := i + 1
    return chain
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the loop-body lines, wholly inside the impl region and unique. The
# ---- loop-preserving positive reshapes only these (bind the wired state to a
# ---- local `next`), leaving the loop, invariants and frozen proof intact.
_LOOP_BODY = """      let s := stages[i]!
      let target := stageMode chain.flag s
      let amode  := adaptedMode chain.hmode chain.flag target
      chain := if s.usable = true then { flag := target, hmode := amode } else chain
      i := i + 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl into a loop-free fold, the direct-model
# ---- positive, and the admissibility case (which adds an in-region assert)
# ---- retune it without touching the spec or dropping the `prove_correct
# ---- loadPipeline` obligation.
_PROOF_GOLD = """prove_correct loadPipeline by
  loom_solve
  case «invariant_2: chain = assemble init (stages.take i)» =>
    have hi : i < stages.length := by omega
    rw [assemble_take_step init stages i hi, ← invariant_2, wireStage]
  case «ensures_1: out.flag = out.hmode» =>
    cases i_3
    have hlen : i = stages.length := by omega
    rw [invariant_2, hlen, List.take_length]
    exact assemble_consistent stages init require_1"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- the FOLD-BRIDGING proof body for a loop-free impl. With no loop there is
# ---- no invariant to peel, but `loom_solve` ALONE is not an honest body here:
# ---- measured, it leaves both `ensures` goals unsolved for a loop-free fold
# ---- carrying the CORRECT per-stage step too, so a rejection under it would be
# ---- attributable to the missing fold/`assemble` bridge rather than to the
# ---- rival's step. `hfold` supplies exactly that bridge — `List.foldl` of the
# ---- CORRECT step IS `assemble` — and it PROVABLY closes both clauses for the
# ---- correct step (`pos-control-foldl-correct-step`, exit 0). Every reject rival
# ---- uses this same body, so its failure is its STEP's, and the residual goal
# ---- names that step.
_PROOF_FOLD = """prove_correct loadPipeline by
  have hfold : ∀ (ss : List Stage) (c : Chain),
      ss.foldl (fun c s =>
        let target := stageMode c.flag s
        let amode  := adaptedMode c.hmode c.flag target
        if s.usable = true then ({ flag := target, hmode := amode } : Chain) else c) c
        = assemble c ss := by
    intro ss
    induction ss with
    | nil => intro c; rfl
    | cons s rest ih => intro c; rw [List.foldl_cons, assemble_cons]; exact ih _
  loom_solve
  all_goals (try rw [hfold stages init])
  all_goals first
    | rfl
    | exact assemble_consistent stages init require_1"""

# ---- the CORRECT per-stage step. Used by pos-control-foldl-correct-step (the
# ---- shape-matched positive that makes every reject rival's failure and every
# ---- witness's gold-side behaviour interpretable) and by nothing else.
_STEP_CORRECT = "if s.usable = true then ({ flag := target, hmode := amode } : Chain) else c"


def _fold_impl(step_expr):
    """The loop-free impl block: fold `step_expr` over `stages` from `init`."""
    return (
        "    -- impl-start\n"
        "    return stages.foldl (fun c s =>\n"
        "      let target := stageMode c.flag s\n"
        "      let amode  := adaptedMode c.hmode c.flag target\n"
        f"      {step_expr}) init\n"
        "    -- impl-end")


def _fold_rival(step_expr):
    """A loop-free rival: fold a WRONG per-stage step over `stages`. Its
    extracted tester `decide`s at a concrete input, so its witness reduces. The
    proof is `_PROOF_FOLD`, which closes the CORRECT step of this very shape, so
    the rejection is the step's and not the script's."""
    return _swap(_swap(_BASE, _IMPL, _fold_impl(step_expr)),
                 _PROOF_GOLD, _PROOF_FOLD)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `loadPipelineTester init stages = false` says the extracted program's
# ---- result violates the method's conjoined postcondition (C1 ∧ C2) at that
# ---- concrete input. Checked in a file whose `prove_correct` block is stripped.
# ---- Every argument is a concrete literal so `decide` reduces the (loop-free)
# ---- extracted rival program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for loadPipeline\n"
            "prove_precondition_decidable_for loadPipeline\n"
            "prove_postcondition_decidable_for loadPipeline\n"
            "derive_tester_for loadPipeline\n\n" + body)


def _witness(init_lit, stages_lit):
    return _tester(
        f"example : loadPipelineTester {init_lit} {stages_lit} = false := by\n"
        "  decide\n")


# ---- concrete literals for the witness / admissibility inputs. `require` forces
# ---- `init.flag = init.hmode`, so a legal seed is one of the two consistent
# ---- states; both are exercised. A `Stage` carries its two capability flags and
# ---- whether it installs.
_CF = "({ flag := false, hmode := false } : Chain)"   # consistent, sync seed
_CT = "({ flag := true, hmode := true } : Chain)"     # consistent, async seed
_DA = "{ canSync := false, canAsync := true, usable := false }"   # declines, async-only
_DS = "{ canSync := true, canAsync := false, usable := false }"   # declines, sync-only
_UA = "{ canSync := false, canAsync := true, usable := true }"    # installs, async-only
_US = "{ canSync := true, canAsync := false, usable := true }"    # installs, sync-only


# ---- THE WITNESS REFERENCE. The loop-free fold carrying the CORRECT per-stage
# ---- step: a machine-checked-correct impl of the frozen spec whose extracted
# ---- tester REDUCES. It is shipped as a positive control in its own right
# ---- (pos-control-foldl-correct-step) and named by every reject case as its
# ---- `witness_reference`, because the FROZEN impl cannot serve as the witness's
# ---- second subject on this bundle: gold's `while` loop elaborates through
# ---- `Classical.choice`, so `decide` on the frozen tester is STUCK for every
# ---- claim regardless of truth, and its exit code discriminates nothing. Refuting
# ---- each witness against THIS impl instead is a real discrimination: an impl the
# ---- verifier ACCEPTS cannot violate its own spec, so a witness that fails here
# ---- fails on the spec's content and not on the kernel's inability to look.
_REFERENCE = _swap(_swap(_BASE, _IMPL, _fold_impl(_STEP_CORRECT)),
                   _PROOF_GOLD, _PROOF_FOLD)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the gold forward
        # scan. `out` IS `assemble init stages`, so C1 holds trivially; C2 is the
        # consistency lemma applied to the assembled state. The reproof drops the
        # loop-invariant peel (no loop) and closes C2 with `assemble_consistent`.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    return assemble init stages\n"
                  "    -- impl-end"),
            _PROOF_GOLD,
            "prove_correct loadPipeline by\n"
            "  loom_solve\n"
            "  exact assemble_consistent stages init require_1"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`assemble init stages` directly (no loop). `out` IS that model, so "
            "C1 (`out = assemble init stages`) holds on the whole domain and C2 "
            "(`out.flag = out.hmode`) is `assemble_consistent` applied to the "
            "consistent seed. If this fails to verify the spec is over-fit to the "
            "loop code shape (SPEC-TOO-STRONG). Also the honest no-ungrounded-echo "
            "control: the fold IS the real work, so a direct return is correct, "
            "not a cheat — any WRONG per-stage step fails `out = assemble init "
            "stages`. Ports/merges the sibling pos-control-ifelse / -reorder-commit "
            "/ -inline into the maximally-different correct shape."),
    },
    {
        "id": "pos-control-named-state",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, the invariants and the frozen proof script; only
        # binds the wired state to a local `next : Chain` before the usable test.
        # Observationally identical for every input.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let s := stages[i]!\n"
            "      let tgt := stageMode chain.flag s\n"
            "      let am  := adaptedMode chain.hmode chain.flag tgt\n"
            "      let next : Chain := { flag := tgt, hmode := am }\n"
            "      chain := if s.usable = true then next else chain\n"
            "      i := i + 1"),
        "rationale": (
            "binding the wired state to a local `next` before the `usable` test "
            "wires the same stream with the same per-step update, so C1 and C2 "
            "still hold on the whole domain; the loop, invariants and frozen proof "
            "script are untouched. A correct reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG (rejects a faithful impl over the "
            "shape of the loop body). Ports the sibling pos-control-inline / "
            "-reorder-commit (a local-variable / independent-assignment reshape) "
            "to a loop-preserving form that keeps the frozen proof."),
    },

    {
        "id": "pos-control-foldl-correct-step",
        "kind": "soundness",
        "expect": "verify",
        # THE SHAPE-MATCHED CONTROL, and the case that makes every reject verdict
        # in this battery interpretable. It is the reject rivals' EXACT carrier
        # shape — a loop-free `stages.foldl` under `_PROOF_FOLD` — carrying the
        # CORRECT per-stage step. Two things are measured only because it ships:
        #   (a) PROOF ATTRIBUTION. Because this verifies, a rival that fails under
        #       the same body fails for its STEP, not for a script tuned to a loop
        #       it no longer has. (The naive `loom_solve`-only body fails here too,
        #       so it would have been a confound.)
        #   (b) WITNESS DISCRIMINATION. Its extracted tester REDUCES, so every
        #       reject witness can be — and was — refuted against it semantically
        #       (`decide` proved the proposition false), which the stuck-on-gold
        #       build cannot show.
        "module": _REFERENCE,
        "rationale": (
            "the loop-free fold with the CORRECT per-stage step: `List.foldl` of "
            "`wireStage`'s own update IS `assemble` (the `hfold` induction in the "
            "tactic body), so C1 holds by that bridge and C2 is "
            "`assemble_consistent` at the consistent seed. A faithful correct impl "
            "in a different executable shape must verify, else the spec is "
            "SPEC-TOO-STRONG on the shape of the fold. It is also the battery's "
            "INTERPRETIVE CONTROL: it is the reject rivals' exact shape and proof "
            "body, so (a) their rejection is attributable to their step rather than "
            "to the proof script, and (b) their witnesses are refutable against a "
            "CORRECT impl whose tester actually reduces — the discrimination the "
            "reduction-stuck gold build does not supply. Both measured with "
            "scripts/lean_verify.sh."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's only `require` (`init.flag = init.hmode`) is
    # met by every consistent seed, so the sibling's "an F2P-shaped input
    # satisfies the precondition" probe is degenerate here (nothing could exclude
    # a normal input, and there is no permission surface). The residual
    # admissibility risk on this domain is a DEGENERATE post-image — a spec no
    # impl distinguishes reads exactly like one every impl meets. This case
    # discharges an in-region `assert`, at fully concrete F2P-shaped inputs, that
    # the fold is NON-DEGENERATE: an installing stage genuinely advances the
    # state (F2P's participating async layer, from a sync seed, ends async), a
    # declining stage genuinely leaves the state untouched (the skip frame — the
    # discriminating content of the change), and the installed outcome is
    # consistent. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof gains a `decide` arm to clear the
    # assert goal (the tactic body is elided from the spec view). The assert is
    # live, not decoration: a false claim about the same point leaves an unsolved
    # goal (verified out-of-band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  f"      assemble {_CF} [{_UA}] = {_CT} ∧\n"
                  f"      assemble {_CF} [{_DA}] = {_CF} ∧\n"
                  f"      (assemble {_CF} [{_UA}]).flag = (assemble {_CF} [{_UA}]).hmode))\n"),
            _PROOF_GOLD,
            "prove_correct loadPipeline by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (case «invariant_2: chain = assemble init (stages.take i)» =>\n"
            "        have hi : i < stages.length := by omega\n"
            "        rw [assemble_take_step init stages i hi, ← invariant_2, wireStage])\n"
            "    | (case «ensures_1: out.flag = out.hmode» =>\n"
            "        cases i_3\n"
            "        have hlen : i = stages.length := by omega\n"
            "        rw [invariant_2, hlen, List.take_length]\n"
            "        exact assemble_consistent stages init require_1)"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at F2P-shaped "
            "inputs: from a consistent sync seed a single INSTALLING async stage "
            "advances the state to the consistent async state (the F2P's "
            "participating async layer), a single DECLINING stage leaves the seed "
            "exactly untouched (the skip-leaves-no-trace frame — the discriminating "
            "content of the fix), and the installed outcome is consistent. The "
            "in-region assert must discharge (else the obligation is degenerate / "
            "the precondition too strong); the impl is kept verbatim so `out = "
            "assemble init stages` and `out.flag = out.hmode` still verify. Sibling "
            "admiss-f2p-shaped-input re-aimed from fractional-permission "
            "admissibility to post-image non-degeneracy, since this backend's only "
            "require is `init.flag = init.hmode` and there is no permission "
            "surface."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a LOOP-FREE
    # fold (a wrong per-stage step) so its extracted tester `decide`s (see the
    # CARRIER NOTE); the frozen spec is untouched.
    #
    # F2P scenario grounding the refinements: an async request drives an assembled
    # pipeline whose configured stages are [a participating async layer, a layer
    # that declines by raising MiddlewareNotUsed]. The test asserts the assembled
    # pipeline responds cleanly (the declining layer is skipped, leaving no trace)
    # — which holds only if the assembled state is consistent (recorded mode =
    # actual mode) and the declining layer left the running state untouched.
    # =====================================================================
    {
        "id": "weak-decline-commits-coercion",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. On a DECLINED stage, commit the mode-coercion to the actual
        # mode while leaving the recorded mode behind — the pre-change behaviour.
        # A declining stage then desyncs the running state (recorded ≠ actual),
        # poisoning every later stage. Correct on every installing stage and on
        # every declining stage whose target already matches the recorded mode;
        # diverges on a declining stage whose target differs from the recorded
        # mode.
        "module": _fold_rival(
            "if s.usable = true then { flag := target, hmode := amode } "
            "else { flag := c.flag, hmode := amode }"),
        "refinement": (
            "this IS the pre-change behaviour: the running state's ACTUAL mode is "
            "coerced to the stage's target before the assembler knows whether the "
            "stage installs, and on the decline path that coercion is carried "
            "forward while the recorded mode is left behind. Its faithful real "
            "patch is exactly the un-patched assembler. The failing test drives an "
            "async request through a pipeline whose declining layer then poisons "
            "the running state — the assembled pipeline runs in a mode other than "
            "the one it reports and the async response misbehaves — so it does NOT "
            "resolve. This is the exact defect the fix corrects."),
        "rationale": (
            "REJECT from C1 (`out = assemble init stages`) AND C2 (`out.flag = "
            "out.hmode`): `assemble`'s decline branch (`wireStage`'s `else c`) "
            "leaves the running state UNCHANGED, but this rival advances the actual "
            "mode on a declining stage, so both the fold value and the consistency "
            "diverge. Refuted at a consistent sync seed and a single declining "
            "async-only stage (`init = (false,false)`, `stages = [decline,async]`), "
            "where gold leaves `(false,false)` and the rival yields `(false,true)`. "
            "Verifying would be SPEC-TOO-WEAK (admits the bug). Sibling "
            "uniq-prepatch-bug."),
        "witness": _witness(_CF, f"[{_DA}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-decline-advances-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Handle the actual-mode rollback correctly, but advance the RECORDED mode
        # on the decline branch (set flag := target, leave hmode). A declining
        # stage flips the recorded mode the next stage trusts. Diverges only on a
        # declining stage whose target differs from the recorded mode — a
        # partial-domain attack.
        "module": _fold_rival(
            "if s.usable = true then { flag := target, hmode := amode } "
            "else { flag := target, hmode := c.hmode }"),
        "refinement": (
            "corresponds to a patch that advanced the RECORDED mode on the decline "
            "path (moving the recorded-mode write out of the install-only branch so "
            "it also runs when the stage is skipped). A declining stage would then "
            "flip the recorded mode while the actual mode stays, so every later "
            "stage is wired under a false belief about the running pipeline and the "
            "assembled pipeline is built for the wrong mode. The async F2P observes "
            "the resulting pipeline; with the recorded mode corrupted on a decline "
            "it would NOT resolve. A partial-domain break — diverges only when a "
            "declining stage's target differs from the recorded mode."),
        "rationale": (
            "REJECT from C1 AND C2: the decline branch of `assemble` leaves BOTH "
            "components unchanged, but this rival advances the recorded mode on a "
            "declining stage, desyncing it from the actual mode. Refuted at a "
            "consistent async seed and a single declining sync-only stage (`init = "
            "(true,true)`, `stages = [decline,sync]`), where gold leaves "
            "`(true,true)` and the rival yields `(false,true)`. This drives `init` "
            "to the async seed and the stage flags to sync-only (both opposite to "
            "the prepatch-bug witness), so the two rivals do not share a point. "
            "Sibling uniq-decline-advances-flag."),
        "witness": _witness(_CT, f"[{_DS}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-install-declining-stage",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the `usable` gate: wire EVERY stage as if it installed. A
        # declining stage then advances the running state instead of being
        # skipped. Correct on every installing stage; diverges on any declining
        # stage. Attacks C1 alone (the wired state stays internally consistent).
        "module": _fold_rival("({ flag := target, hmode := amode } : Chain)"),
        "refinement": (
            "corresponds to a patch that ignores the decline signal and installs "
            "every configured stage — a declining layer that Django requires be "
            "SKIPPED (it raised MiddlewareNotUsed) would instead be wired into the "
            "assembled pipeline. The failing test expects the declining layer to be "
            "skipped (leaving no trace on the running state); forcing it to install "
            "changes the assembled pipeline, so it does NOT resolve. Correct on "
            "every stage that genuinely installs."),
        "rationale": (
            "REJECT from C1 (`out = assemble init stages`): `assemble` leaves the "
            "running state untouched on a `usable = false` stage, but this rival "
            "advances it. Refuted at a consistent sync seed and a two-stage list "
            "`[installing async, declining sync]` (`init = (false,false)`), where "
            "gold installs the first (→ `(true,true)`) then skips the second "
            "(stays `(true,true)`), while the rival wires the second too and lands "
            "at `(false,false)`. This is the only witness at length 2 and the only "
            "one that exercises a decline AFTER an install, so `stages.length` and "
            "the running-state-carried target are both moved. Sibling "
            "uniq-frame-mutate-declines re-expressed on this carrier: forcing a "
            "declining layer to participate, but as a value-level `usable` bypass "
            "(there is no read-only column to overwrite here — see accounting)."),
        "witness": _witness(_CF, f"[{_UA}, {_DS}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-wire-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        # Treat every stage as declining: never advance the running state, return
        # the seed unchanged. Correct only when NO stage installs; diverges on any
        # installing stage. Attacks C1 alone.
        "module": _fold_rival("c"),
        "refinement": (
            "corresponds to a patch whose loop never installs any stage (e.g. an "
            "unconditional skip). The assembled pipeline would be just the base "
            "state with no configured stage wired, so the participating layer never "
            "runs and the F2P's expected adaptation / clean response through the "
            "assembled pipeline never appears — it does NOT resolve. Correct only "
            "on an all-declining configuration."),
        "rationale": (
            "REJECT from C1 (`out = assemble init stages`): on any input with an "
            "installing stage the fold advances the running state, but this rival "
            "returns the seed. Refuted at a consistent sync seed and a single "
            "installing async-only stage (`init = (false,false)`, `stages = "
            "[install,async]`), where gold advances to `(true,true)` and the rival "
            "returns `(false,false)`. Sibling uniq-skip-all — the supporting "
            "near-miss for the install/decline gate, at the dual point to "
            "weak-install-declining-stage (a stage that SHOULD install but does "
            "not)."),
        "witness": _witness(_CF, f"[{_UA}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-install-stale-hmode",
        "kind": "uniqueness",
        "expect": "reject",
        # On the INSTALL branch, advance the recorded mode to the target but leave
        # the ACTUAL mode stale (drop the mode-coercion). An installing stage then
        # records a target it did not actually coerce the pipeline to. Correct on
        # every declining stage and on every installing stage whose target already
        # equals the running actual mode; diverges otherwise. Attacks C1 AND C2.
        "module": _fold_rival(
            "if s.usable = true then { flag := target, hmode := c.hmode } else c"),
        "refinement": (
            "corresponds to a patch that advanced the recorded mode on install but "
            "dropped the adapter's coercion of the running pipeline's actual mode "
            "(recording a target the pipeline was never actually converted to). "
            "Every installing stage whose target differs from the running actual "
            "mode then leaves the assembled pipeline recording a mode it does not "
            "run in; the async F2P awaits the reported type and gets the stale one "
            "— it does NOT resolve. Correct on every declining stage."),
        "rationale": (
            "REJECT from C1 AND C2: `assemble`'s install branch sets `hmode := "
            "adaptedMode …` (the coerced actual mode), but this rival keeps the "
            "stale actual mode while advancing the recorded mode, so the wired "
            "state is inconsistent whenever the target differs from it. Refuted at "
            "a consistent async seed and a single installing sync-only stage "
            "(`init = (true,true)`, `stages = [install,sync]`), where gold coerces "
            "to `(false,false)` and the rival lands at `(false,true)` — an "
            "inconsistent state. This is the only witness that moves `init` to the "
            "async seed with an INSTALLING sync stage, so the install-branch "
            "coercion is exercised on its own. Sibling uniq-drop-wrap "
            "(participating layer committed without its full coercion)."),
        "witness": _witness(_CT, f"[{_US}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER. Every per-stage decision is right and every stage is wired, but
        # the stages are consumed in the opposite order. C2 still holds honestly
        # (the reversed list is assembled by the same fold from the same
        # consistent seed, and the tactic body discharges it with
        # `assemble_consistent stages.reverse`), so this rival isolates C1's
        # ORDER content — the one thing the other five leave unattacked, since
        # each of them diverges pointwise per stage.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    return assemble init stages.reverse\n"
                  "    -- impl-end"),
            _PROOF_GOLD,
            "prove_correct loadPipeline by\n"
            "  loom_solve\n"
            "  exact assemble_consistent stages.reverse init require_1"),
        "refinement": (
            "corresponds to a patch that walks the configured stages in the "
            "opposite order from the one the assembler must consume them in. Each "
            "stage is still wired, and wired correctly for the state it sees, so "
            "the assembled state is internally consistent — but it is the state a "
            "DIFFERENT configuration would produce. The failing test drives an "
            "async request through a pipeline whose stages have distinct "
            "capabilities, so the mode the assembled pipeline ends up in depends on "
            "which stage was wired last; walking them backwards lands the pipeline "
            "in the other mode and the async response misbehaves — it does NOT "
            "resolve. A pure ORDER break: no per-stage decision is wrong."),
        "rationale": (
            "REJECT from C1 (`out = assemble init stages`) ALONE: C1 pins the fold "
            "over the method's own input list IN ORDER, and this rival returns the "
            "fold over the reversal. C2 is satisfied honestly (proved, not evaded — "
            "`assemble_consistent` applies to the reversed list just as well), which "
            "is what makes the case an ORDER probe rather than another consistency "
            "probe: it is the only rival whose output is a state gold reaches at "
            "some OTHER input, so nothing but the order distinguishes it. Refuted at "
            "a consistent sync seed and `[installing sync, installing async]` (`init "
            "= (false,false)`, a SIXTH input point and the only one whose two stages "
            "both install), where gold wires sync then async and lands at "
            "`(true,true)` while the rival wires async then sync and lands at "
            "`(false,false)`. Added by audit: the five ported rivals all diverge "
            "pointwise per stage, so a permutation of the stage stream was "
            "unattacked. Shares its impl SHAPE and proof body with "
            "pos-control-direct-model (which verifies), so the rejection is the "
            "reversal's."),
        "witness": _witness(_CF, f"[{_US}, {_UA}]"),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (3
# soundness positives, 1 admissibility, 5 uniqueness — two of which are the
# MANDATORY frame-mutation rivals) plus an AXIOM lane of 2 probes. The sibling
# contracts `assemble_chain(target_mode, declines, base_async)` over two
# READ-ONLY half-permission `List[int]` columns and a scalar, returning a
# (handler-trace, async-flag) pair, with the load-bearing (H)/(A) folds
# `final_handler` / `final_async`. This backend models the SAME assembly DEEPLY
# and CONCRETELY: the two parallel columns collapse to a single `List Stage`
# (each element carries the capability flags and the install/decline bit), and
# the running (handler-trace, async-flag) pair collapses to a `Chain`
# (recorded-mode `flag`, actual-mode `hmode`) — the handler TRACE is not
# observable, only whether the assembled state is CONSISTENT. That refinement is
# what narrows the two frame-mutation rivals away and re-expresses the (H)/(A)
# fold attacks as attacks on `assemble` + consistency.
#
#   sibling case                    kind          -> here                          disposition
#   -----------------------------------------------------------------------------------------
#   pos-control-ifelse              soundness     -> pos-control-direct-model      MERGED
#   pos-control-reorder-commit      soundness     -> pos-control-named-state       MERGED/RE-EXPR
#   pos-control-inline              soundness     -> (folded into the two above)   MERGED
#   admiss-f2p-shaped-input         admissibility -> admiss-nondegenerate          RE-AIMED
#   uniq-prepatch-bug               uniqueness    -> weak-decline-commits-coercion PORTED
#   uniq-decline-advances-flag      uniqueness    -> weak-decline-advances-flag    PORTED
#   uniq-drop-wrap                  uniqueness    -> weak-install-stale-hmode      RE-EXPRESSED
#   uniq-frame-mutate-declines      uniqueness    -> (none) / weak-install-...     VACUOUS (+re-expr)
#   uniq-frame-mutate-target        uniqueness    -> (none)                        VACUOUS
#   uniq-skip-all                   uniqueness    -> weak-wire-nothing             PORTED
#   (no sibling)                    uniqueness    -> weak-install-declining-stage  ADDED
#   (no sibling)                    soundness     -> pos-control-foldl-correct-step ADDED (audit)
#   (no sibling)                    uniqueness    -> weak-reversed-order            ADDED (audit)
#   AXIOM_TESTS (2)                 axiom         -> (none)                        DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 3 soundness, 1 admissibility, 6 uniqueness.
#
# ADDED BY AUDIT (pos-control-foldl-correct-step, weak-reversed-order). The port
#   shipped SOUND, and both halves of every reject case behaved as declared, but
#   two things it claimed were not demonstrated and are now measured:
#   (1) The five reject rivals all carried a `loom_solve`-only proof body, and
#       that body was measured to fail IDENTICALLY on a loop-free fold with the
#       CORRECT per-stage step. So each rejection was, as shipped, consistent with
#       a mere tactic mismatch. pos-control-foldl-correct-step is that exact shape
#       with the right step; it VERIFIES under `_PROOF_FOLD`, which every rival now
#       carries, so a rival's failure is now attributable to its step (the residual
#       goal names the step) rather than to a missing fold/`assemble` bridge.
#   (2) The port's FAIL-on-gold half was satisfied by REDUCTION-STUCK builds
#       (`decide` "did not reduce to isTrue or isFalse" on the frozen `while`), a
#       failure mode a TAUTOLOGOUS witness would also produce. The same positive
#       control fixes this too: its tester reduces, so each witness was refuted
#       against a CORRECT impl semantically (`decide` proved the proposition
#       false). See the CARRIER NOTE.
#   (3) All five ported rivals diverge POINTWISE PER STAGE (a wrong per-stage
#       step), so C1's ORDER content — that the fold consumes the stage stream in
#       the method's own input order — was attacked by nothing. weak-reversed-order
#       closes that: every per-stage decision is right and C2 is discharged
#       honestly, so only the permutation distinguishes it.
#
# MERGED (pos-control-ifelse / -reorder-commit / -inline -> two positives): the
#   sibling carries THREE correct reshapes of the loop body (rewrite the decline
#   `continue` as a positive if/else; reorder the two independent commit
#   assignments; inline the `adapted` temporary). On this carrier the per-stage
#   update is a single record construction inside `wireStage`, not a multi-line
#   commit with a reorderable pair of statements, so the three sibling reshapes
#   are the SAME edit here. They are covered by two structurally-distinct correct
#   controls: pos-control-direct-model (loop-free direct return of the grounded
#   fold — maximally different, and the honest no-echo control) and
#   pos-control-named-state (loop-preserving, binds the wired state to a local —
#   the inline/reorder reshape, keeping the frozen proof intact). Shipping a third
#   near-identical reshape would add no coverage.
# RE-AIMED (admiss-f2p-shaped-input -> admiss-nondegenerate): the sibling asserts
#   an F2P-shaped pair of equal-length read-only columns satisfies its
#   half-permission Requires. This backend's only `require` is `init.flag =
#   init.hmode` (met by every consistent seed) and there is no permission surface,
#   so that probe is degenerate; the sharper residual risk is a DEGENERATE
#   post-image, so the case is re-aimed to a live in-region assert that the fold
#   discriminates install (state advances) from decline (state untouched) and that
#   the installed outcome is consistent — at F2P-shaped inputs.
# PORTED (uniq-prepatch-bug, uniq-decline-advances-flag, uniq-skip-all): the
#   pre-patch skip-carries-the-coercion bug, advancing the recorded mode on a
#   decline, and wiring nothing all carry across intact — only the carrier changes
#   from a `List[int]` trace fold to the `Chain` consistency fold. Each keeps its
#   sibling refinement argument (unpatched assembler / recorded-mode desync /
#   nothing installed all fail the same async F2P), now backed by a machine-checked
#   witness at a DISTINCT input point.
# RE-EXPRESSED (uniq-drop-wrap -> weak-install-stale-hmode): the sibling drops the
#   wrapper token on the participating branch (commits the adaptation without its
#   full transform). The observable of that on this carrier is that an installing
#   stage advances the recorded mode without the matching ACTUAL-mode coercion, so
#   the assembled state becomes inconsistent — the same "a participating layer is
#   committed without its full transform" attack, re-expressed against C1/C2.
# ADDED (weak-install-declining-stage): a rival that ignores the `usable` gate and
#   installs a DECLINING stage. Without it, no witness would exercise a decline
#   that FOLLOWS an install, nor a length-2 configuration; it moves `stages.length`
#   off 1 and probes the install/decline gate from the "forced to participate"
#   side. It is also the referentially-transparent RE-EXPRESSION of the sibling's
#   uniq-frame-mutate-declines intent (force a declining layer to participate) —
#   there the attack is a write into the read-only `declines` column; here there
#   is no column to overwrite, so the same wrong behaviour is reached by a
#   value-level `usable` bypass. A real divergence with a machine-checked witness.
# VACUOUS (uniq-frame-mutate-declines, uniq-frame-mutate-target): the sibling's TWO
#   MANDATORY frame-mutation rivals write into a read-only half-permission input
#   (`declines[i] = 0`, `target_mode[i] = 0`) and are rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: `init` and `stages` are
#   immutable values declared read-only (no input is `mut` — only the loop-local
#   `chain`/`i`), there is no heap, no aliasing, no `Old`, and no permission
#   system. There is no read-only input to overwrite and no frame clause to
#   violate, so the class has no carrier analogue. NOT ported as a permission
#   probe (fabricating a substitute would test nothing); the behavioural INTENT of
#   the declines-write rival (force a declining layer to participate) is instead
#   re-expressed as the value-level weak-install-declining-stage above.
#   AUDIT CONFIRMATION (this is the part the port asserted rather than measured):
#   the nearest expressible analogue — assigning to the read-only parameter
#   itself, `stages := []` inside the impl region — was actually BUILT, and the
#   carrier refuses it at ELABORATION, not at the postcondition: "`stages` cannot
#   be mutated, only variables declared using `let mut` can be mutated" (exit 1).
#   So a ported frame-mutation rival would reject for a PARSE/binder reason with
#   no spec content whatever, and there is nothing for a witness to state. The
#   class is genuinely absent on this carrier, as the port claimed.
# DROPPED (AXIOM_TESTS, 2): the sibling's axiom-soundness / containment probes over
#   the real django callees are G-AX's job (axiom_check.py / mapping.md — here the
#   two unchanged primitives `stageMode`/`adaptedMode` are A-reference deep models,
#   not consumed axioms); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``stages.length - i``). A rival that
#   loops without a measure is refused outright (``Decreasing annotations are
#   required in total correctness semantics``), and a rival that supplies a
#   CONSTANT measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# CLAUSE / BINDER / POINT COVERAGE. Two independent `ensures` clauses:
#   C1 `out = assemble init stages` (the whole fold) and C2 `out.flag = out.hmode`
#   (the assembled state is CONSISTENT). BOTH are DEFENDED by the three positives
#   and the admissibility case (gold discharges both) and BOTH are ATTACKED: C1 by
#   all six rivals; C2 (independently — the rival's output is inconsistent) by
#   weak-decline-commits-coercion, weak-decline-advances-flag, and
#   weak-install-stale-hmode. weak-install-declining-stage, weak-wire-nothing and
#   weak-reversed-order diverge on C1 while producing an internally-consistent
#   state, so they attack C1 alone — and weak-reversed-order is the sharpest of
#   the three, since it discharges C2 by PROOF rather than incidentally. The two
#   binders are moved across SIX distinct input points (pts = 6):
#     * weak-decline-commits-coercion  init (false,false)  [decline async]        len 1
#     * weak-decline-advances-flag     init (true,true)    [decline sync]          len 1
#     * weak-install-declining-stage   init (false,false)  [install async, decline sync] len 2
#     * weak-wire-nothing              init (false,false)  [install async]         len 1
#     * weak-install-stale-hmode       init (true,true)    [install sync]          len 1
#     * weak-reversed-order            init (false,false)  [install sync, install async] len 2
#   So `init` ranges over BOTH consistent seeds {(false,false),(true,true)} (the
#   require admits only these two); `Stage.usable` ranges over {true,false};
#   `Stage.canSync` and `Stage.canAsync` each range over {true,false} (async-only
#   and sync-only stages both appear on both the install and decline sides); and
#   `stages.length` ranges over {1,2}. No binder is pinned at a single value across
#   the reject set. Every witness states its refutation at concrete literals (no
#   bound hypothesis), so no consistency probe is needed.
#   MEANINGFULNESS (not just distinctness): at each of the six points gold's own
#   output differs from the rival's, computed value-for-value — (false,false) vs
#   (false,true); (true,true) vs (false,true); (true,true) vs (false,false);
#   (true,true) vs (false,false); (false,false) vs (false,true); (true,true) vs
#   (false,false). No two points are two spellings of the same discrimination:
#   they split by seed, by which branch is exercised, by which capability drives
#   the target, by stream length, and (the sixth) by ORDER alone.
#
# WITNESS MECHANICS: the post-image is fully TRANSPARENT (`assemble` / `wireStage`
#   / `stageMode` / `adaptedMode` are concrete `def`s; the axioms region declares
#   no opaque leaf), so the tester + `decide` path is LIVE. Each rival is loop-free
#   (a `stages.foldl`, or the direct `assemble … .reverse`) so its extracted
#   `loadPipelineTester` `decide`s at the concrete literal, while gold's
#   `while`-loop tester (well-founded recursion) stays STUCK. All six checked with
#   scripts/lean_verify.sh: rival exit 0; gold exit 1.
#   BUT THE GOLD-SIDE FAILURE IS NOT THE DISCRIMINATOR — it is reduction-stuck
#   ("did not reduce to isTrue or isFalse"), which a tautology would also produce.
#   The discrimination is measured against pos-control-foldl-correct-step instead:
#   a CORRECT impl in the rivals' own shape, whose tester DOES reduce, where each
#   witness is refuted semantically (`decide` proved the proposition false, exit 1
#   for all six). See the CARRIER NOTE.
AXIOM_TESTS = []
