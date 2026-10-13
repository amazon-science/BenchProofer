"""properties.py — G-PBT falsification manifest for django__django-13810 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case is a complete solution file that edits
ONLY the implementation region (and, for the soundness positives, the proof
body), so `variant_scope.same_spec` holds by construction, the
`theorem correct_loadPipeline` STATEMENT is byte-identical in every case, and any
rejection is attributable to the postcondition rather than to a tampered spec.
No case introduces an axiom, a helper lemma, a `sorry`/`admit`, or
`native_decide`.

DEFENDED SURFACE
----------------
One obligation, one modeled function:

    implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain

pinned by a postcondition with TWO independent top-level clauses:

    (1) result = assemble init stages
    (2) init.consistent → result.consistent

`Chain` carries two coupled booleans — the mode the partially-assembled pipeline
is RECORDED to run in (`flag`) and the mode it ACTUALLY runs in (`hmode`) — and
`Stage` carries three (`canSync`, `canAsync`, `usable`). Clause (1) pins the
result to the left-to-right `wireStage` fold, so it constrains the whole
traversal: the ORDER stages are wired in, which mode each is wired under
(`stageMode`), how the running pipeline is coerced (`adaptedMode`), and — the
discriminating content of this instance — that a stage which declines to install
itself (`usable = false`) leaves the running pipeline EXACTLY as it was, in both
components. Clause (2) is the health property: a consistent base yields a
consistent result, i.e. every stage was wired under a faithful view of the
running pipeline.

The carrier is fully TRANSPARENT — `stageMode`, `adaptedMode`, `wireStage` and
`assemble` are concrete `def`s over `Bool` and `List Stage`, with no `opaque`
callee anywhere — so every rival is refutable at a concrete literal input and no
carrier conditioning is needed. Each witness accordingly binds nothing, which
also means there are no hypotheses that could be jointly unsatisfiable.

The two clauses are attacked SEPARATELY and deliberately. A rival can break (2)
while satisfying (1) nowhere, and — more interesting — a rival can satisfy (2)
everywhere while breaking (1): `ignore-declined` below installs every stage
unconditionally, which happens to keep recorded and actual modes in step, so
only clause (1) refutes it. Without a clause-(1) attacker the battery would
attest to a fold it never tested.

Both INPUT binders are varied by the reject witnesses. `init` is probed at three
points — consistent-async `(true, true)`, consistent-sync `(false, false)`, and
the INCONSISTENT `(false, true)`, which moves `init.hmode` independently of
`init.flag` and exercises clause (1) outside clause (2)'s antecedent. `stages` is
probed at seven distinct lists spanning declining and installing stages, both
capability flags in every combination that matters, and both a one-stage and a
two-stage traversal (the latter is what makes the wiring ORDER observable).

All THREE lanes are present: `soundness` (three reshaped correct impls),
`admissibility` (the obligation discharged by evaluation at the F2P-shaped
input), and `uniqueness` (seven rivals). The admissibility lane is what tests
the third direction this gate exists for, and it is landed rather than argued
away — see the porting note on `admiss-f2p-shaped-ground` for why "the frozen
obligation has no precondition" is not a reason to omit it.

PORTING NOTES — which nagini cases ported, which were omitted and why
--------------------------------------------------------------------
The nagini sibling models the assembly walk over two parallel read-only integer
columns plus a running token trace, and contracts it with two fold clauses (H)
and (A) under fractional read permissions. This bundle models the purely
functional core: the two coupled mode booleans threaded through the walk. That
narrowing is what decides each disposition below.

  * `pos-control-ifelse` -> `pos-negated-branch` (the decline test rewritten as
    its negation, so the install and skip arms trade places). Proof re-closed for
    the new impl shape.
  * `pos-control-inline` -> `pos-guarded-update` (the two `let` temporaries
    dropped and the coercion inlined into a guarded update, so the skip arm
    disappears from the source entirely). Proof re-closed.
  * `pos-control-reorder-commit` -> `pos-fold-form` (a structurally different
    CORRECT impl: the whole traversal as a pure left fold rather than an
    imperative accumulator loop). The nagini original swapped two independent
    assignments; on this carrier the two components are written as one record
    literal, so the assignment-order reshape has no counterpart and this stands
    in its place as the shape-diversity positive. Proof re-closed.
  * `uniq-prepatch-bug` -> `commit-coercion-on-decline`, the direct port and the
    only rival whose refutation point IS the F2P input.
  * `uniq-decline-advances-flag` -> `decline-advances-recorded-mode`, the direct
    port: nagini's clause (A) attack becomes the clause-(2) attack on the OTHER
    component of the running pipeline.
  * `uniq-skip-all` -> `never-install`, the direct port.
  * `uniq-drop-wrap` is DROPPED as not-wrong-on-this-carrier. Its nagini target
    is a per-stage derivation step that is mode-PRESERVING; nagini observes it
    because its carrier records a token trace of every derivation, whereas this
    bundle observes only the mode pair, in which that step is the identity. A
    rival dropping it is therefore observationally equal to gold here, and no
    discriminating witness exists — as required, it is dropped rather than
    shipped with a witness that does not discriminate.
  * `uniq-frame-mutate-declines` / `uniq-frame-mutate-target` are VACUOUS. They
    attack a write through a read-only reference held at a fractional
    permission; Lean is referentially transparent, there is no aliasing and no
    permission to escape, so the class does not exist on this carrier. No
    substitute is fabricated. What the frame obligation becomes here is
    STRUCTURAL and is already covered: clause (1) pins the result against both
    inputs, so `ignore-declined` and `wrong-wiring-mode` (which mishandle
    `stages` entries) and `reversed-traversal` (which mishandles their order)
    are the analogues, and they are refuted on the spec, not on a permission.
  * `admiss-f2p-shaped-input` -> `admiss-f2p-shaped-ground`, LANDED. The frozen
    obligation carries no precondition hypothesis, so there is no `Requires` to
    be over-strong in nagini's literal sense — but that is NOT a reason to drop
    the lane, and an earlier revision of this manifest wrongly dropped it on
    exactly that argument. The analogue on a total carrier is the obligation
    being UNSATISFIABLE at an F2P-shaped input, which is a real failure mode a
    universally-quantified statement can have (it is provable only because no
    reachable input witnesses it). The positive discharges the spec predicate at
    the concrete F2P-shaped point BY EVALUATION as a `have`, then closes the
    frozen obligation verbatim. Demonstrated to do real work: the same `have`
    with the claim NEGATED fails (`decide` proves the negation false), so the
    evaluation genuinely decides the obligation at that point rather than
    passing vacuously.
  * The DIVERGENCE class has no nagini counterpart here (the sibling carries no
    `diverge-*` / `nonterm-*` / `weak-diverge` case), and on lean it is
    genuinely vacuous rather than a spec hole: `implementation_loadPipeline` is a
    total Lean `def` over a `for` loop on a finite list, so a non-terminating
    implementation cannot be written at all and there is nothing for the spec to
    admit vacuously. Contrast velvet under partial termination semantics, where
    the same class is a KNOWN SPEC HOLE (the corpus-wide termination-semantics finding).
  * `AXIOM_TESTS` are dropped: the axiom lane belongs to G-AX and this gate
    ignores them.

Three rivals have NO nagini counterpart and were added because the modeled
surface has structure nagini's carrier does not expose to attack:
`ignore-declined` (the only clause-(1)-only attacker), `wrong-wiring-mode` and
`wrong-coercion` (the two per-stage primitives clause (1) folds over), and
`reversed-traversal` (the traversal ORDER, which is meaningless in a permission
model but is the whole content of a list fold).

WITNESSES
---------
Every `expect="reject"` case carries a `witness`: a Lean snippet proving the
rival violates the spec at ONE concrete input, checked in a file with the frozen
obligation removed so no tactic script can interfere. Each was built both ways
with scripts/lean_verify.sh and SEEN to discriminate — it elaborates against its
rival (exit 0) and FAILS against the frozen solution (exit 1, `decide` reporting
the negated proposition is false). A witness that merely reshaped the impl would
fail the first half; a tautology would fail the second.
"""
from pathlib import Path

INSTANCE = "django__django-13810"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of a substring lying wholly inside the
    region being edited. Asserts the anchor still matches and is unique, so a
    frozen-solution edit breaks this manifest loudly instead of silently
    producing a variant that tests something else."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the impl region (the four executable lines
# of the accumulator loop) or, for the positives that reprove, inside the proof
# region. All are unique in the frozen file.
# ---------------------------------------------------------------------------

_LOOP_HEAD = "    for s in stages do"
_PICK_MODE = "      let target := stageMode chain.flag s"
_COERCE = "      let amode  := adaptedMode chain.hmode chain.flag target"
_UPDATE = ("      chain := if s.usable = true then "
           "{ flag := target, hmode := amode } else chain")

# The whole impl body, for the positives that replace the loop outright.
_IMPL_ALL = (
    "def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=\n"
    "  Id.run do\n"
    "    let mut chain : Chain := init\n"
    + _LOOP_HEAD + "\n" + _PICK_MODE + "\n" + _COERCE + "\n" + _UPDATE + "\n"
    "    return chain"
)

# The frozen obligation's tactic body, replaced verbatim by the positives that
# reprove. The STATEMENT above `:= by` is never touched.
_PROOF_ALL = (
    "theorem correct_loadPipeline : ∀ (init : Chain) (stages : List Stage),\n"
    "    problem_spec_loadPipeline init stages (implementation_loadPipeline init stages) := by\n"
    "  intro init stages\n"
    "  unfold problem_spec_loadPipeline implementation_loadPipeline\n"
    "  have h := forIn_loadPipeline_helper stages init\n"
    "  simp only [Id.run] at h ⊢\n"
    "  rw [h]\n"
    "  exact ⟨rfl, assemble_consistent stages init⟩\n"
)

assert _BASE.count(_IMPL_ALL) == 1 and _BASE.count(_PROOF_ALL) == 1


# ===========================================================================
# SOUNDNESS POSITIVES — expect "verify". A structurally DIFFERENT but CORRECT
# implementation must still verify; if one cannot, the spec is over-fit to the
# frozen source shape (SPEC-TOO-STRONG). Each reproves the SAME obligation
# statement inside the proof region: no helper lemma is added (the frozen
# `assemble_consistent` discharges clause (2) unchanged in all three), and the
# per-shape traversal equality is proved inline by the same accumulator
# induction the frozen proof uses.
# ===========================================================================

# (pos-negated-branch) The install test is written as its negation, so the skip
# arm comes first and the install arm second. Same per-stage semantics: the
# running pipeline advances exactly when the stage installs itself.
_POS_NEGATED = _swap(
    _swap(_BASE, _UPDATE,
          "      chain := if s.usable = false then chain"
          " else { flag := target, hmode := amode }"),
    _PROOF_ALL,
    "theorem correct_loadPipeline : ∀ (init : Chain) (stages : List Stage),\n"
    "    problem_spec_loadPipeline init stages (implementation_loadPipeline init stages) := by\n"
    "  intro init stages\n"
    "  unfold problem_spec_loadPipeline implementation_loadPipeline\n"
    "  have key : ∀ (ss : List Stage) (c : Chain),\n"
    "      Id.run (forIn ss c\n"
    "        (fun s c => do\n"
    "          pure PUnit.unit\n"
    "          pure (ForInStep.yield\n"
    "            (let target := stageMode c.flag s\n"
    "             let amode  := adaptedMode c.hmode c.flag target\n"
    "             if s.usable = false then c else { flag := target, hmode := amode }))))\n"
    "        = assemble c ss := by\n"
    "    intro ss\n"
    "    induction ss with\n"
    "    | nil => intro c; simp [assemble, Id.run, pure]\n"
    "    | cons s rest ih =>\n"
    "      intro c\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind, pure] at ih ⊢\n"
    "      rw [ih]\n"
    "      simp only [assemble, wireStage]\n"
    "      cases hu : s.usable <;> simp [hu]\n"
    "  have h := key stages init\n"
    "  simp only [Id.run] at h ⊢\n"
    "  rw [h]\n"
    "  exact ⟨rfl, assemble_consistent stages init⟩\n")

# (pos-guarded-update) Both `let` temporaries are dropped and the mode choice /
# coercion are inlined into a GUARDED update, so the skip arm vanishes from the
# source: nothing is written when the stage declines. Behaviourally identical.
_POS_GUARDED = _swap(
    _swap(_BASE, _IMPL_ALL,
          "def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=\n"
          "  Id.run do\n"
          "    let mut chain : Chain := init\n"
          "    for s in stages do\n"
          "      if s.usable = true then\n"
          "        chain := { flag := stageMode chain.flag s,\n"
          "                   hmode := adaptedMode chain.hmode chain.flag"
          " (stageMode chain.flag s) }\n"
          "    return chain"),
    _PROOF_ALL,
    "theorem correct_loadPipeline : ∀ (init : Chain) (stages : List Stage),\n"
    "    problem_spec_loadPipeline init stages (implementation_loadPipeline init stages) := by\n"
    "  intro init stages\n"
    "  unfold problem_spec_loadPipeline implementation_loadPipeline\n"
    "  have key : ∀ (ss : List Stage) (c : Chain),\n"
    "      Id.run (forIn ss c\n"
    "        (fun s c => do\n"
    "          if s.usable = true then do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield\n"
    "              ({ flag := stageMode c.flag s,\n"
    "                 hmode := adaptedMode c.hmode c.flag (stageMode c.flag s) } : Chain))\n"
    "          else do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield c)))\n"
    "        = assemble c ss := by\n"
    "    intro ss\n"
    "    induction ss with\n"
    "    | nil => intro c; simp [assemble, Id.run, pure]\n"
    "    | cons s rest ih =>\n"
    "      intro c\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind, pure] at ih ⊢\n"
    "      cases hu : s.usable <;> simp only [hu, ih, assemble, wireStage] <;> simp [hu]\n"
    "  have h := key stages init\n"
    "  simp only [Id.run] at h ⊢\n"
    "  rw [h]\n"
    "  exact ⟨rfl, assemble_consistent stages init⟩\n")

# (pos-fold-form) A different KIND of implementation: the whole traversal as a
# pure left fold, with no imperative accumulator and no do-block at all.
_POS_FOLD = _swap(
    _swap(_BASE, _IMPL_ALL,
          "def implementation_loadPipeline (init : Chain) (stages : List Stage) : Chain :=\n"
          "  stages.foldl\n"
          "    (fun c s =>\n"
          "      if s.usable = true then\n"
          "        { flag := stageMode c.flag s,\n"
          "          hmode := adaptedMode c.hmode c.flag (stageMode c.flag s) }\n"
          "      else c)\n"
          "    init"),
    _PROOF_ALL,
    "theorem correct_loadPipeline : ∀ (init : Chain) (stages : List Stage),\n"
    "    problem_spec_loadPipeline init stages (implementation_loadPipeline init stages) := by\n"
    "  intro init stages\n"
    "  unfold problem_spec_loadPipeline implementation_loadPipeline\n"
    "  have key : ∀ (ss : List Stage) (c : Chain),\n"
    "      List.foldl\n"
    "        (fun c s =>\n"
    "          if s.usable = true then\n"
    "            { flag := stageMode c.flag s,\n"
    "              hmode := adaptedMode c.hmode c.flag (stageMode c.flag s) }\n"
    "          else c) c ss = assemble c ss := by\n"
    "    intro ss\n"
    "    induction ss with\n"
    "    | nil => intro c; simp [assemble]\n"
    "    | cons s rest ih =>\n"
    "      intro c\n"
    "      simp only [List.foldl_cons, assemble, wireStage]\n"
    "      rw [ih]\n"
    "  rw [key stages init]\n"
    "  exact ⟨rfl, assemble_consistent stages init⟩\n")


# ===========================================================================
# ADMISSIBILITY — expect "verify". The frozen obligation is universally
# quantified with no precondition hypothesis, so nagini's literal
# PRECOND-TOO-STRONG has no direct analogue; the analogue on a TOTAL carrier is
# the obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
# universally-quantified statement can be while still being provable (provable
# because nothing reachable witnesses it). This case tests that directly: it
# discharges the spec predicate at the concrete F2P-shaped point by EVALUATION
# as a `have`, then closes the frozen obligation verbatim. Nothing is assumed —
# no new declaration, statement byte-identical, the ground instance is a `have`
# prepended to the existing tactic body.
#
# The F2P-shaped point. The configuration is processed as two stages: the first
# DECLINES to install itself and advertises only the synchronous capability; the
# second INSTALLS and advertises both. The base pipeline is built and recorded in
# the asynchronous mode, so `init` is the consistent-async `(true, true)` — which
# is also the point `commit-coercion-on-decline` refutes at, i.e. the coercion on
# the declining stage is real here and the ground instance is not a trivial one.
_ADM_INIT = "{ flag := true, hmode := true }"
_ADM_STAGES = ("[{ canSync := true, canAsync := false, usable := false },\n"
               "       { canSync := true, canAsync := true, usable := true }]")

_P_INTRO = "  intro init stages\n"
assert _BASE.count(_P_INTRO) == 1

_ADM_GROUND = _swap(
    _BASE, _P_INTRO,
    "  have _ground : problem_spec_loadPipeline " + _ADM_INIT + "\n"
    "      " + _ADM_STAGES + "\n"
    "      (implementation_loadPipeline " + _ADM_INIT + "\n"
    "        " + _ADM_STAGES + ") := by\n"
    "    unfold problem_spec_loadPipeline Chain.consistent\n"
    "    decide\n"
    + _P_INTRO)


# ===========================================================================
# UNIQUENESS RIVALS — expect "reject". Each shares the spec exactly and edits
# only the impl region; each carries a witness SEEN to discriminate. A verifying
# rival here would be a genuine verify-does-not-imply-resolve break.
# ===========================================================================

# (commit-coercion-on-decline) THE bug. A declining stage does NOT leave the
# running pipeline as it was: the coercion the stage tentatively applied is
# committed to the ACTUAL mode while the RECORDED mode stays behind. This is the
# prepatch impl of this bundle, byte-for-byte.
_RIV_PREPATCH = _swap(
    _BASE, _UPDATE,
    "      chain := if s.usable = true then { flag := target, hmode := amode }\n"
    "               else { flag := chain.flag, hmode := amode }")

# (decline-advances-recorded-mode) The mirror-image rollback failure, on the
# OTHER component: the declining stage leaves the actual mode alone (correct) but
# advances the RECORDED mode to the target it would have been wired at.
_RIV_DECLINE_FLAG = _swap(
    _BASE, _UPDATE,
    "      chain := if s.usable = true then { flag := target, hmode := amode }\n"
    "               else { flag := target, hmode := chain.hmode }")

# (ignore-declined) The declining case is not distinguished at all: every stage
# is treated as installing itself. Note this rival keeps recorded and actual
# modes in step, so clause (2) never refutes it — it is the clause-(1)-only
# attacker, and the reason the fold equality has to be tested in its own right.
_RIV_IGNORE_DECL = _swap(_BASE, _UPDATE,
                         "      chain := { flag := target, hmode := amode }")

# (never-install) The opposite extreme: nothing is ever wired on, so the result
# is the base pipeline whatever the stages say. Correct only on an all-declining
# list; the supporting near-miss for the rollback attacks.
_RIV_NEVER = _swap(_BASE, _UPDATE, "      chain := chain")

# (wrong-wiring-mode) The mode a stage is wired under ignores the mode the
# running pipeline is currently recorded to run in, taking the stage's
# asynchronous capability unconditionally. Attacks the per-stage mode choice that
# clause (1)'s fold composes.
_RIV_WRONG_MODE = _swap(_BASE, _PICK_MODE, "      let target := s.canAsync")

# (wrong-coercion) The coercion's own test is inverted: the running pipeline is
# left in its current actual mode exactly when it needed converting, and
# converted when it already matched. Attacks the other per-stage primitive.
_RIV_WRONG_COERCE = _swap(
    _BASE, _COERCE,
    "      let amode  := if chain.flag = target then target else chain.hmode")

# (reversed-traversal) Every stage is wired, and each is wired correctly given
# the running pipeline it sees — but the list is traversed in the opposite
# direction, so each stage sees a different running pipeline. Attacks the ORDER
# clause (1) fixes; no other rival moves it.
_RIV_REVERSED = _swap(_BASE, _LOOP_HEAD, "    for s in stages.reverse do")


# --- witnesses --------------------------------------------------------------
# Each states the negation of the spec predicate at one concrete literal input.
# `clause=1` refutes the fold equality directly; `clause=2` discharges the
# consistency antecedent (`by unfold Chain.consistent; decide`) and refutes the
# consequent. Nothing is bound by the `example` head, so there are no
# hypotheses and no satisfiability question to raise.

def _chain(flag: str, hmode: str) -> str:
    return f"{{ flag := {flag}, hmode := {hmode} }}"


def _stage(can_sync: str, can_async: str, usable: str) -> str:
    return (f"{{ canSync := {can_sync}, canAsync := {can_async}, "
            f"usable := {usable} }}")


def _wit(init: str, stages: str, clause: int) -> str:
    reach = ("  have hc := h.2 (by unfold Chain.consistent; decide)\n"
             if clause == 2 else "  have hc := h.1\n")
    return (
        f"example : ¬ problem_spec_loadPipeline {init} {stages}\n"
        f"    (implementation_loadPipeline {init} {stages}) := by\n"
        "  intro h\n"
        + reach +
        "  simp only [implementation_loadPipeline, assemble, wireStage, stageMode,\n"
        "    adaptedMode, Chain.consistent, Id.run, pure, bind] at hc\n"
        "  exact absurd hc (by decide)\n"
    )


# init points: consistent-async, consistent-sync, and an INCONSISTENT base that
# moves `init.hmode` independently of `init.flag`.
_INIT_ASYNC = _chain("true", "true")
# The admissibility ground instance is stated at this same base (it is defined
# above, before `_chain` exists). Pinned so the two cannot drift apart: the
# admissibility rationale claims its point coincides with
# commit-coercion-on-decline's refutation base, and that claim has to stay true.
assert _ADM_INIT == _INIT_ASYNC
_INIT_SYNC = _chain("false", "false")
_INIT_SKEWED = _chain("false", "true")

# A declining stage that can only run synchronously. On an async-recorded
# pipeline it is wired at a target the pipeline does not already match, so the
# coercion is real and a failure to roll it back is observable. This is exactly
# the shape the F2P input presents at its first stage.
_DECLINE_SYNC_ONLY = _stage("true", "false", "false")
# A declining stage that can only run asynchronously — the mirror case, where
# the target differs from a SYNC-recorded pipeline.
_DECLINE_ASYNC_ONLY = _stage("false", "true", "false")
# Installing stages.
_INSTALL_ASYNC_ONLY = _stage("false", "true", "true")
_INSTALL_SYNC_ONLY = _stage("true", "false", "true")
_INSTALL_BOTH = _stage("true", "true", "true")


SPEC_TESTS = [
    # ---- soundness positives (must VERIFY; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NEGATED,
        "rationale":
            "structurally different but CORRECT: the install test is written as its "
            "negation, so the skip arm is first and the install arm second. The running "
            "pipeline still advances exactly when the stage installs itself and is still "
            "left untouched when it declines, so both clauses hold: the traversal equals "
            "`assemble init stages` and `init.consistent → result.consistent` follows "
            "from the frozen whole-list lemma unchanged. Reproved inside the proof region "
            "with the same accumulator induction plus a case split on the install flag; "
            "the obligation statement is byte-identical and no lemma was added. If the "
            "spec cannot admit an inverted branch order it is over-fit to one source "
            "shape => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-guarded-update",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_GUARDED,
        "rationale":
            "a local-variable reshape that removes a whole branch from the source: both "
            "`let` temporaries are dropped, the mode choice and the coercion are inlined "
            "into a GUARDED update, and the skip arm disappears entirely — nothing is "
            "written when a stage declines, rather than the pipeline being rewritten to "
            "itself. Same value at every stage, so `result = assemble init stages` still "
            "holds and clause (2) still follows from the frozen whole-list lemma. "
            "Reproved by the same induction with the guard's own case split. Must verify; "
            "else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-fold-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLD,
        "rationale":
            "a different KIND of implementation, not just a different branch order: the "
            "whole traversal as a pure left fold, with no imperative accumulator and no "
            "do-block. This replaces nagini's assignment-reorder positive, which has no "
            "counterpart here (the two pipeline components are written as a single record "
            "literal, so there is no assignment order to swap). Reproved by induction "
            "relating the fold to `assemble`; clause (2) again comes from the frozen "
            "whole-list lemma. If the spec admits only the accumulator-loop form it is "
            "over-fit to the imperative shape => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must VERIFY; else the obligation is unsatisfiable at
    # an F2P-shaped input — the total-carrier analogue of PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_GROUND,
        "rationale":
            "the obligation is discharged at the concrete F2P-shaped input — a base "
            "pipeline built and recorded asynchronous, `(true, true)`, and two "
            "processed stages, the first DECLINING and synchronous-capable only, the "
            "second INSTALLING and both-capable — by EVALUATION as a `have`, after "
            "which the frozen obligation is closed verbatim. The frozen statement has "
            "no precondition hypothesis, so nagini's literal PRECOND-TOO-STRONG does "
            "not port; what ports is the failure mode a universally-quantified "
            "obligation CAN have on a total carrier, namely being unsatisfiable at "
            "exactly a normal F2P-shaped input (provable only because nothing "
            "reachable witnesses it). This case rules that out at the one input the "
            "instance is actually about. The ground `have` does real work rather than "
            "passing vacuously: the same `have` with the claim NEGATED fails, `decide` "
            "reporting the negated proposition false, so the evaluation genuinely "
            "decides both clauses at that point. Nothing is assumed — no new "
            "declaration, the obligation statement is byte-identical, and the ground "
            "instance is a `have` prepended to the existing tactic body. Note the "
            "point is the same one `commit-coercion-on-decline` refutes at, so the "
            "coercion on the declining stage is live here and the instance is not "
            "trivially satisfied.",
    },

    # ---- uniqueness rivals (must be REJECTED; else SPEC-TOO-WEAK) ----
    {
        "id": "commit-coercion-on-decline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "witness": _wit(_INIT_ASYNC, f"[{_DECLINE_SYNC_ONLY}]", 2),
        "refinement":
            "this is the behaviour before the change, and the one the reported issue "
            "describes: a stage that declines to install itself is skipped, but the "
            "mode-coercion it tentatively applied to the running pipeline is kept, so "
            "the next stage inherits a pipeline whose recorded mode no longer describes "
            "how it actually runs. Its faithful real patch is simply the unchanged code, "
            "so the sole F2P — which drives an asynchronous request through a "
            "configuration whose first processed stage declines and whose second "
            "installs, and asserts a clean 200/b'OK' response plus the exact skip log "
            "records — fails exactly as reported (the finished pipeline reports "
            "asynchronous while actually running synchronously, and the response object "
            "cannot be awaited). It does NOT resolve, so a verifying rival would be a "
            "true verify-does-not-imply-resolve break.",
        "rationale":
            "rejected by clause (2), `init.consistent → result.consistent`: the fold's "
            "skip arm leaves both components untouched, so a consistent base stays "
            "consistent, whereas this rival advances the actual mode while holding the "
            "recorded mode fixed and so desynchronises them on the first declining "
            "stage. Witness at the F2P-shaped point — an async-consistent base "
            "(true, true) and a single declining stage that can only run synchronously, "
            "so the target differs from the recorded mode and the coercion is real. "
            "SEEN to elaborate against the rival and to fail on the frozen solution "
            "(`decide` reports the negated proposition false there). This is the only "
            "rival whose refutation point is the F2P input itself.",
    },
    {
        "id": "decline-advances-recorded-mode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DECLINE_FLAG,
        "witness": _wit(_INIT_SYNC, f"[{_DECLINE_ASYNC_ONLY}]", 2),
        "refinement":
            "the mirror-image rollback failure: the declining stage leaves the actual "
            "mode alone but advances the RECORDED mode to the target it would have been "
            "wired at. Its faithful real patch moves the recorded-mode update out of the "
            "branch that only runs when a stage installs successfully, so a skipped "
            "stage still reports its mode. Every later stage is then wired under a mode "
            "the running pipeline does not actually have, and the final top-of-stack "
            "coercion is chosen from the wrong recorded mode; the F2P's asynchronous "
            "request through a declining-then-installing configuration observes the "
            "resulting pipeline and does NOT resolve.",
        "rationale":
            "rejected by clause (2) on the other component: the fold's skip arm passes "
            "the recorded mode through unchanged, so `result.consistent` follows from "
            "`init.consistent`; advancing it on a decline breaks that. A PARTIAL-DOMAIN "
            "attack — it agrees with the frozen solution unless a declining stage's "
            "target differs from the running recorded mode — so the witness is placed at "
            "a different point from commit-coercion-on-decline rather than shared with "
            "it: a sync-consistent base (false, false) and a declining stage that can "
            "only run asynchronously, which is precisely the sub-domain the rationale "
            "claims. SEEN to elaborate against the rival and fail on the frozen "
            "solution.",
    },
    {
        "id": "ignore-declined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_DECL,
        "witness": _wit(_INIT_SKEWED,
                        f"[{_INSTALL_ASYNC_ONLY}, {_DECLINE_SYNC_ONLY}]", 1),
        "refinement":
            "a stage that declines to install itself is not distinguished at all: every "
            "configured stage is wired on. Its faithful real patch drops the skip path, "
            "so a stage that declines at wire-up time is nonetheless installed into the "
            "pipeline. The F2P configuration contains exactly such a stage and asserts "
            "both that it is skipped (via its log record) and that the resulting "
            "pipeline serves an asynchronous request cleanly; installing it changes the "
            "recorded mode the rest of the pipeline is assembled under and drops the "
            "asserted record, so the F2P does NOT resolve.",
        "rationale":
            "this rival keeps the recorded and actual modes in step at every stage, so "
            "clause (2) holds of it EVERYWHERE and cannot refute it; it is rejected "
            "solely by clause (1), `result = assemble init stages`, whose skip arm "
            "returns the running pipeline unchanged. That is why the fold equality has "
            "to be attacked in its own right — without this case the battery would "
            "attest to a traversal it never tested. The witness therefore refutes "
            "clause (1) directly, and does so from the INCONSISTENT base (false, true), "
            "which moves `init.hmode` independently of `init.flag` and demonstrates that "
            "clause (1) binds outside clause (2)'s antecedent. Two stages, one "
            "installing and one declining. SEEN to elaborate against the rival and fail "
            "on the frozen solution.",
    },
    {
        "id": "never-install",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEVER,
        "witness": _wit(_INIT_SYNC, f"[{_INSTALL_ASYNC_ONLY}]", 1),
        "refinement":
            "the opposite extreme: nothing is ever wired on, so the finished pipeline is "
            "the base pipeline whatever the configuration says. Its faithful real patch "
            "is a traversal whose body never commits, e.g. one that always takes the "
            "skip path. Being honest about which tests separate it: the F2P does NOT. "
            "Both log records the F2P asserts are emitted during the DECLINING stage's "
            "own iteration, before any commit would happen, and the F2P's other stage is "
            "a transparent pass-through whose installation does not change the 200/b'OK' "
            "response — so the F2P passes under this rival, and the non-resolution comes "
            "entirely from the P2P set. There it is catastrophic: every sibling test that "
            "asserts an installed stage's OWN effect (a status code it sets, content it "
            "appends, a hook it registers) sees an empty pipeline and fails. Since "
            "`resolved` requires the whole P2P list to pass, that patch does NOT resolve, "
            "so a verifying rival is still a verify-does-not-imply-resolve break; it is "
            "recorded here explicitly rather than left to read as an F2P claim.",
        "rationale":
            "rejected by clause (1), `result = assemble init stages`: on an input where "
            "the fold advances the running pipeline this rival returns `init` unchanged. "
            "The supporting near-miss for the two rollback attacks. Being precise about "
            "the sub-domain, since the obvious characterisation is WRONG: it is not "
            "'correct exactly on the all-declining lists'. Returning `init` also agrees "
            "with the fold whenever the installing stages happen to be wired at modes "
            "that leave the pipeline where it already was — e.g. a sync-consistent base "
            "(false, false) with a single INSTALLING sync-capable stage, where the fold "
            "also lands on (false, false). So the all-declining lists are a proper "
            "SUBSET of its agreement set, and the witness has to be placed at a point "
            "where the fold genuinely moves. Witness at a sync-consistent base "
            "(false, false) with "
            "one installing stage that can only run asynchronously, so the base is "
            "provably not the answer. SEEN to elaborate against the rival and fail on "
            "the frozen solution.",
    },
    {
        "id": "wrong-wiring-mode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_MODE,
        "witness": _wit(_INIT_SYNC, f"[{_INSTALL_BOTH}]", 1),
        "refinement":
            "the mode a stage is wired under ignores the mode the running pipeline is "
            "currently recorded to run in, taking the stage's asynchronous capability "
            "unconditionally. Its faithful real patch drops the arm that keeps a "
            "synchronous-capable stage synchronous on a synchronously-recorded pipeline, "
            "so a stage advertising both capabilities is always wired asynchronously. "
            "Being honest about the sub-domain: this rival AGREES with the frozen "
            "solution on the F2P input itself (there the recorded mode is asynchronous "
            "throughout, where the dropped arm never fires), so the non-resolution comes "
            "from the P2P set rather than the F2P — the sibling tests in the same module "
            "that drive a SYNCHRONOUS request through a both-capable stage would then "
            "see it wired asynchronously and fail. Since `resolved` requires the whole "
            "P2P list to pass, that patch does NOT resolve, so a verifying rival is "
            "still a verify-does-not-imply-resolve break; it is recorded here explicitly "
            "rather than left to read as an F2P claim.",
        "rationale":
            "attacks the per-stage mode choice that clause (1)'s fold composes: the "
            "modelled choice keeps a stage synchronous when the recorded mode is "
            "synchronous and the stage supports it, and falls back to the asynchronous "
            "capability otherwise. Rejected by clause (1). Witness at exactly the point "
            "the dropped arm governs — a sync-consistent base (false, false) and one "
            "installing stage advertising BOTH capabilities, where the frozen solution "
            "wires synchronously and the rival asynchronously. This is the only witness "
            "whose stage sets `canSync` and `canAsync` both true, so it is the only one "
            "that separates the two capability fields. SEEN to elaborate against the "
            "rival and fail on the frozen solution.",
    },
    {
        "id": "wrong-coercion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_COERCE,
        "witness": _wit(_INIT_ASYNC, f"[{_INSTALL_SYNC_ONLY}]", 2),
        "refinement":
            "the coercion's own test is inverted: the running pipeline is left in its "
            "current actual mode exactly when it needed converting to the target, and "
            "converted when it already matched. Its faithful real patch flips the "
            "condition under which the running pipeline is adapted before a stage is "
            "wired onto it, so a pipeline that actually runs in one mode is handed to a "
            "stage expecting the other. As with wrong-wiring-mode, the F2P input does "
            "not separate this from correct behaviour (its one installing stage is wired "
            "at the mode the pipeline is already recorded at); the non-resolution comes "
            "from the P2P tests that drive a stage of one capability onto a pipeline of "
            "the other, which are exactly the inputs where the coercion has to fire. "
            "Those fail, so `resolved` is not reached and the rival's verification would "
            "still be a verify-does-not-imply-resolve break.",
        "rationale":
            "attacks the OTHER per-stage primitive clause (1) folds over — the "
            "coercion applied to the running pipeline — and does so through clause (2): "
            "with the test inverted, an installing stage records the target mode while "
            "the actual mode is left at the pipeline's old value, so a consistent base "
            "yields an inconsistent result. Witness at an async-consistent base "
            "(true, true) with one installing stage that can only run synchronously, so "
            "the target differs from the recorded mode and the coercion is the "
            "load-bearing step. Distinct from wrong-wiring-mode's point (which holds the "
            "mode choice itself wrong on a both-capable stage), so neither rival's "
            "claimed sub-domain rests on the other's witness. SEEN to elaborate against "
            "the rival and fail on the frozen solution.",
    },
    {
        "id": "reversed-traversal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSED,
        "witness": _wit(_INIT_SYNC,
                        f"[{_INSTALL_SYNC_ONLY}, {_INSTALL_ASYNC_ONLY}]", 1),
        "refinement":
            "every stage is wired, and each is wired correctly given the running "
            "pipeline it sees — but the configured list is traversed in the opposite "
            "direction, so each stage sees a DIFFERENT running pipeline and the finished "
            "pipeline composes them in the opposite order. Its faithful real patch "
            "iterates the configured stages the other way round. The order stages are "
            "processed in is part of the configuration's meaning: requests would flow "
            "through them backwards, and the mode each stage is wired under depends on "
            "every stage ahead of it. Being honest about which tests separate it: the F2P "
            "does NOT. Its two asserted log records are both emitted during the DECLINING "
            "stage's own iteration and name that stage, so they appear in the same "
            "relative order whichever end the traversal starts from, and its other stage "
            "is a transparent pass-through — the F2P passes under this rival. The "
            "non-resolution comes from the P2P set: the sibling tests configured with TWO "
            "stages pin their relative composition (which stage's effect wraps which — an "
            "asserted content ordering, a short-circuit that must happen before the other "
            "stage's hook runs), and reversing the traversal inverts exactly that. Since "
            "`resolved` requires the whole P2P list to pass, it does NOT resolve; recorded "
            "explicitly rather than left to read as an F2P claim.",
        "rationale":
            "attacks the traversal ORDER, which clause (1) fixes by equating the result "
            "to the LEFT-TO-RIGHT `assemble` fold and which no other rival moves — a "
            "class with no nagini counterpart, since order is meaningless in a "
            "permission model but is the entire content of a list fold. Rejected by "
            "clause (1). Witness needs at least two stages and needs them "
            "order-sensitive: a sync-consistent base (false, false) with an installing "
            "sync-only stage followed by an installing async-only one, where wiring them "
            "the other way round yields a different final pipeline. SEEN to elaborate "
            "against the rival and fail on the frozen solution.",
    },
]
