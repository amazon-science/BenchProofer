"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23314 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — which the consumer spec view elides
— is changed, so ``markers.same_spec`` holds and the ``prove_correct renderStep``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, two read-only input binders):

  renderStep (visible : Bool) (renderedScene : Scene) return (out : RenderResult)
    ensures out = renderDecision visible renderedScene                  [clause A]
    ensures (visible = false) → (out.emitted = false ∧ out.scene = blank) [clause B]

  ``renderDecision`` is a TRANSPARENT total function of the two inputs:

      visible = true   →  { emitted := true,  scene := renderedScene }
      visible = false  →  { emitted := false, scene := blank }

  Clause A pins the WHOLE result — both the side-effect observable
  (``emitted``: whether any emission work ran) and the content observable
  (``scene``: what was placed on the output target) — to that function of the
  inputs. Clause B independently re-states the discriminating half: when the
  element is hidden, NO emission work is performed and nothing is placed. The
  post-image is grounded entirely in the inputs (there is no opaque answer-key
  to echo — ``Scene`` is a plain ``Nat`` and the whole carrier is transparent),
  so a wrong impl cannot verify by mirroring an oracle; it must reproduce the
  decision.

  The BEHAVIOURAL DISCRIMINATOR: an element flagged hidden must perform no
  emission and place nothing. The pre-change renderer for this element type ran
  its entire emission body unconditionally, so a hidden element still emitted
  content — the failing image-comparison scenario (a hidden subplot compared
  against an empty reference). Clause B senses exactly that: hidden ⇒
  ``emitted = false ∧ scene = blank``.

CARRIER NOTE — why this port refutes at CONCRETE literals (no conditioning).

  Unlike siblings whose postcondition is stated over opaque callees, this
  bundle's carrier is fully transparent: ``Bool`` for the decision input,
  ``Nat`` for ``Scene`` (``blank := 0``), and ``RenderResult`` derives
  ``DecidableEq``. So every reject witness reaches the method's contract through
  Velvet's own tester machinery (``renderStepTester visible renderedScene``) at
  concrete literals and closes by ``decide`` — no hypothesis about an opaque
  term is needed, so no witness binds anything and the gate's consistency probe
  has nothing to check (there are no assumptions to be inconsistent). Because the
  frozen solution is STRAIGHT-LINE it also reduces under ``decide``; the witness
  fails against gold purely because gold SATISFIES the spec at that input
  (tester returns ``true``, so ``... = false`` is provably false), which is the
  required discriminator. Checked in a file whose ``prove_correct`` block is
  stripped, so no tactic script can mask the verdict. Every reject witness below
  was run against both the rival (elaborates) and the frozen solution (fails)
  with two real builds.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION (nagini's MANDATORY #4) — VACUOUS here. The nagini sibling
    holds both inputs at a fractional heap permission (``Acc(.,1/2)``) an impl
    can illegally overwrite, and carries a rival that writes back into the
    read-only input, rejected for INSUFFICIENT PERMISSION. Lean/Velvet are
    referentially transparent: ``visible`` and ``renderedScene`` are immutable
    values (neither is a ``mut`` binder), there is no heap, no aliasing and no
    permission system to trip. No read-only field to overwrite and no substitute
    probe to build. Reported vacuous, not fabricated.
  * ADMISSIBILITY (nagini's #3) — PORTED, not N/A. The method carries no
    ``require`` clause, but "no precondition" is NOT a reason to drop this lane:
    on a total carrier the PRECOND-TOO-STRONG analogue is the OBLIGATION being
    unsatisfiable or degenerate at exactly an F2P-shaped input, and that is
    directly testable. The ``admiss-hidden-nonblank`` case below discharges, by
    evaluation in an in-region ``assert`` before closing the frozen obligation
    verbatim, that at the discriminating input (hidden element, NON-blank
    content) the two ``ensures`` clauses are JOINTLY satisfiable and that the
    obligation SEPARATES that input from its visible counterpart — so it is
    neither unmeetable nor a constant collapse every impl would meet.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent total function
    of the inputs (``renderDecision``), not an axiomatized oracle; the ``axioms``
    region is empty.

See the footer for the full nagini→velvet accounting.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23314"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole guard body (text strictly between
# ---- -- impl-start and -- impl-end). Lies wholly inside the single impl region
# ---- and is unique in Solution.lean (both facts asserted at load by _swap).
# ---- The frozen `prove_correct` body (`loom_solve <;> simp_all [renderDecision]`)
# ---- is GENERIC over the impl shape and closes for every correct reshape below,
# ---- so the soundness positives keep it verbatim; the reject rivals also keep it
# ---- (their rejection is carried by the witness, not by whether the frozen
# ---- tactic happens to break on the reshape).
_GOLD_IMPL = (
    "    if visible = false then\n"
    "      return { emitted := false, scene := blank }\n"
    "    else\n"
    "      return { emitted := true, scene := renderedScene }"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"


def _impl(body):
    """Full Solution.lean variant with only the impl body replaced (spec view and
    frozen proof untouched)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness builder. Reaches the method contract through Velvet's tester
# ---- machinery: `renderStepTester v s = false` says the extracted program's
# ---- result violates the postcondition at the concrete input (v, s). Checked in
# ---- a file whose `prove_correct` block is stripped; closes by `decide` on the
# ---- transparent carrier. Binds nothing (literal inputs), so the gate's
# ---- consistency probe is a no-op.
def _witness(call):
    return (
        "extract_program_for renderStep\n"
        "prove_precondition_decidable_for renderStep\n"
        "prove_postcondition_decidable_for renderStep\n"
        "derive_tester_for renderStep\n\n"
        f"example : {call} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the clause is SPEC-TOO-STRONG. Each keeps the
    # byte-identical obligation statement and the frozen `prove_correct` body
    # (which is generic over the impl shape); only the executable surface is
    # reshaped. Both verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-positive-guard",
        "kind": "soundness",
        "expect": "verify",
        # Rewrite the negative early-exit guard into positive form: branch on the
        # ENABLED case first, falling through to the hidden case. Same observable
        # result on both fields (clause A) and the same hidden behaviour (clause
        # B), no new lemma. If a faithful correct impl could not verify against
        # this spec, the spec would be SPEC-TOO-STRONG.
        "module": _impl(
            "    if visible = true then\n"
            "      return { emitted := true, scene := renderedScene }\n"
            "    else\n"
            "      return { emitted := false, scene := blank }"),
        "rationale": "structurally different CORRECT reshape: the negative "
                     "early-exit guard is rewritten in positive form (branch on "
                     "the enabled case first). Same result on both observables "
                     "(clause A) and the same hidden behaviour (clause B); the "
                     "frozen `prove_correct` body closes unchanged. Must verify, "
                     "else SPEC-TOO-STRONG. (Sibling: pos-control-positive-guard.)",
    },
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Stage the whole result through a single named local computed by an
        # if-expression, then return it — a flat (guard-less control-flow) shape
        # with the same value as the gold guard. Proves the spec is not over-fitted
        # to the gold's exact branch shape.
        "module": _impl(
            "    let r : RenderResult :=\n"
            "      if visible = true then { emitted := true, scene := renderedScene }\n"
            "      else { emitted := false, scene := blank }\n"
            "    return r"),
        "rationale": "second correct shape: stage the whole result through a named "
                     "local computed by an if-expression and return it "
                     "unconditionally — a flat control flow with the gold value. "
                     "Proves the spec admits a guard-less but correct shape; the "
                     "frozen proof closes unchanged. Must verify, else "
                     "SPEC-TOO-STRONG. (Sibling: pos-control-local-reshape.)",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). The method has no `require`
    # clause, so the classic "a normal input satisfies the precondition" probe
    # has no precondition to interrogate. That does NOT make the lane vacuous:
    # on a total carrier the same failure mode arrives as the OBLIGATION being
    # unsatisfiable or degenerate at the very input the behaviour under spec is
    # about. A spec no impl can meet, and a spec every impl meets, both read as
    # "verified" for reasons unrelated to the behaviour.
    #
    # So this case discharges — BY EVALUATION, in an in-region `assert`, before
    # the frozen obligation is closed verbatim — three facts at the
    # discriminating F2P-shaped input (hidden element, NON-blank content 7):
    #   (a) clause A's post-image at that input is a concrete, inhabited value;
    #   (b) clause B holds of that SAME image (both conjuncts), so the two
    #       `ensures` are JOINTLY satisfiable there — not mutually exclusive;
    #   (c) the obligation SEPARATES that input from its visible counterpart,
    #       so the post-image is not a constant collapse.
    # The impl is the frozen one verbatim (so the method's own `ensures` still
    # discharges) and the frozen `prove_correct` body is kept verbatim too — it
    # clears the extra assert goal unaided. The assert is LIVE, not decoration:
    # negating conjunct (b) leaves `⊢ blank = 7` unsolved and negating (c)
    # leaves its own goal unsolved (both measured; exit 1 each).
    # =====================================================================
    {
        "id": "admiss-hidden-nonblank",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      -- (a) clause A's post-image at the discriminating input:\n"
            "      (renderDecision false 7 = { emitted := false, scene := blank } ∧\n"
            "      -- (b) clause B holds of that same image => jointly satisfiable:\n"
            "       (renderDecision false 7).emitted = false ∧\n"
            "       (renderDecision false 7).scene = blank ∧\n"
            "      -- (c) non-degenerate: the obligation separates this input from\n"
            "      --     its visible counterpart at the same content.\n"
            "       renderDecision true 7 ≠ renderDecision false 7))\n"
            + _GOLD_IMPL),
        "rationale": "ADMISSIBILITY / PRECOND-TOO-STRONG on a total carrier. "
                     "There is no `require` clause to probe, so the lane is "
                     "re-aimed at the analogue that DOES exist here: the "
                     "obligation being unsatisfiable or degenerate at an "
                     "F2P-shaped input. At (visible=false, renderedScene=7) — a "
                     "hidden element carrying NON-blank content, the input the "
                     "discriminating clause is about — the in-region assert "
                     "evaluates that clause A's post-image is a concrete "
                     "inhabited value, that clause B holds of that same image on "
                     "BOTH conjuncts (so the two ensures are jointly satisfiable, "
                     "not mutually exclusive), and that the obligation separates "
                     "that input from its visible counterpart (so it is not a "
                     "constant collapse every impl meets). Impl and frozen "
                     "`prove_correct` body both kept verbatim, so the method's "
                     "own obligation still discharges. Must verify, else "
                     "PRECOND-TOO-STRONG. (Nagini sibling: "
                     "admissibility-readonly-and-sink, re-aimed — the sibling's "
                     "half-permission/sink-permission content has no analogue on "
                     "a referentially transparent carrier, but its QUESTION does.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary BOTH input
    # binders (visible ∈ {false, true}, renderedScene ∈ {2,3,5,6}) across four
    # distinct points (pts=4).
    # =====================================================================
    {
        "id": "partial-domain-overshoot-hidden",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: drop the visibility guard and run the emission
        # body unconditionally. Correct on the visible sub-domain; on a HIDDEN
        # element it still performs emission work and places content.
        "module": _impl(
            "    return { emitted := true, scene := renderedScene }"),
        "refinement": "this IS the pre-change behaviour: the renderer for this "
                      "element type runs its entire emission body with no early "
                      "exit on the hidden flag. For the failing scenario (a hidden "
                      "element compared against an empty reference) it still emits "
                      "content, so the rendered output is non-empty and the "
                      "image-level comparison FAILS — the faithful (guard-less) "
                      "patch does NOT resolve.",
        "rationale": "REJECT from clause B (and clause A): the body runs "
                     "unconditionally, so for a hidden element `emitted = true` "
                     "while the spec forces `emitted = false ∧ scene = blank`. "
                     "Refuted at (visible=false, renderedScene=3): the hidden "
                     "element emits work the spec forbids. Verifying would be "
                     "SPEC-TOO-WEAK on the hidden branch. (Sibling: "
                     "partial-domain-overshoot-invisible.)",
        "witness": _witness("renderStepTester false 3"),
    },
    {
        "id": "partial-domain-underdeliver-visible",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror miss: perform no emission in ANY case (always the hidden
        # result). Correct on the hidden sub-domain; on a VISIBLE element it
        # performs no work and places nothing.
        "module": _impl(
            "    return { emitted := false, scene := blank }"),
        "refinement": "a faithful counterpart that took the early exit even when "
                      "the element IS visible would perform no emission for a "
                      "normal visible element — every rendering test would come "
                      "back blank where content is expected, so the patch would "
                      "NOT resolve.",
        "rationale": "REJECT from clause A: for a visible element the spec forces "
                     "`renderDecision true renderedScene = { emitted := true, "
                     "scene := renderedScene }`, while the rival returns "
                     "`{ emitted := false, scene := blank }`. Refuted at "
                     "(visible=true, renderedScene=5). Verifying would be "
                     "SPEC-TOO-WEAK on the visible branch. (Sibling: "
                     "partial-domain-underdeliver-visible.)",
        "witness": _witness("renderStepTester true 5"),
    },
    {
        "id": "uniqueness-overdeliver-double",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level over-count on the visible branch: place DOUBLED content
        # (renderedScene + renderedScene) instead of the body's actual content.
        # Agrees with gold only when renderedScene = blank (0); diverges for every
        # non-empty scene. Attacks the `scene` field of clause A on the visible
        # branch — a sub-domain the emitted-flag rivals do not reach.
        "module": _impl(
            "    if visible = false then\n"
            "      return { emitted := false, scene := blank }\n"
            "    else\n"
            "      return { emitted := true, scene := renderedScene + renderedScene }"),
        "refinement": "a faithful counterpart that emitted the body's content "
                      "twice (or doubled the emitted primitives) on a visible "
                      "element would produce a doubled / over-drawn output, "
                      "failing the image comparison against the single-pass "
                      "reference — it would NOT resolve.",
        "rationale": "REJECT from clause A on the visible-branch `scene` field: the "
                     "spec pins `out.scene = renderedScene` exactly, so the doubled "
                     "content diverges for every renderedScene > blank. Refuted at "
                     "(visible=true, renderedScene=6): out.scene = 12 ≠ 6. This "
                     "abuses the renderedScene binder (discriminates only when it "
                     "is non-blank), a sub-domain the emitted-flag rivals do not "
                     "reach. Verifying would be SPEC-TOO-WEAK on the scene value. "
                     "(Sibling: uniqueness-overdeliver-double.)",
        "witness": _witness("renderStepTester true 6"),
    },
    {
        "id": "uniqueness-hidden-scene-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the hidden branch: report NO emission work (emitted := false,
        # correct) but LEAK the body's content onto the output target anyway
        # (scene := renderedScene instead of blank). Correct on the emitted flag
        # and on every visible input and on hidden+renderedScene==blank; diverges
        # only on a hidden element with non-blank content. Isolates the
        # `scene = blank` conjunct of clause B, which the overshoot rival (wrong on
        # `emitted`) does not pin on its own.
        "module": _impl(
            "    if visible = false then\n"
            "      return { emitted := false, scene := renderedScene }\n"
            "    else\n"
            "      return { emitted := true, scene := renderedScene }"),
        "refinement": "a faithful counterpart that skipped the emission WORK for a "
                      "hidden element yet still placed its content on the output "
                      "target would leave the hidden element's pixels present, so "
                      "the image comparison against the empty reference FAILS — it "
                      "would NOT resolve. (The observable the failing test checks "
                      "is the placed content, not merely whether a code path ran.)",
        "rationale": "REJECT from the `scene = blank` conjunct of clause B (and the "
                     "`scene` field of clause A): for a hidden element the spec "
                     "forces `scene = blank`, while the rival leaks renderedScene. "
                     "Refuted at (visible=false, renderedScene=2): out.scene = 2 ≠ "
                     "blank. This isolates the content conjunct of the hidden-case "
                     "clause — a sub-domain the overshoot rival (wrong on the "
                     "emitted flag) does not pin — and abuses the renderedScene "
                     "binder (discriminates only when it is non-blank). Verifying "
                     "would be SPEC-TOO-WEAK on the hidden-case content. (ADDED — "
                     "no direct nagini sibling; see footer.)",
        "witness": _witness("renderStepTester false 2"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 3 uniqueness rivals) plus a
# 1-entry AXIOM lane. This bundle models the SAME single behaviour — a render
# step that suppresses all emission when the element is hidden — as `renderStep`
# over the referentially-transparent carrier (`Bool` × `Scene := Nat` ->
# `RenderResult`). The nagini spec's arithmetic-tally observable (sink.work) is
# re-expressed as the pair (emitted, scene): the "nothing added when invisible"
# clause becomes the discriminating `emitted = false ∧ scene = blank`, and the
# "+ content when visible" clause becomes `out = renderDecision …`. Every sibling
# case is accounted for below.
#
#   sibling case (nagini)                 -> here
#   ---------------------------------------------------------------------
#   pos-control-positive-guard             -> pos-control-positive-guard   PORTED
#   pos-control-local-reshape              -> pos-control-local-reshape     PORTED
#   admissibility-readonly-and-sink        -> admiss-hidden-nonblank        PORTED (re-aimed)
#   frame-mutation-write-content           -> (none)                        VACUOUS
#   partial-domain-overshoot-invisible     -> partial-domain-overshoot-hidden PORTED (central)
#   partial-domain-underdeliver-visible    -> partial-domain-underdeliver-visible PORTED
#   uniqueness-overdeliver-double          -> uniqueness-overdeliver-double PORTED
#   (new, no sibling)                      -> uniqueness-hidden-scene-leak  ADDED
#   AXIOM_TESTS (1 entry)                  -> (none)                        DROPPED (G-AX)
#
# PORTED (2 positives): both nagini correct reshapes port directly — the
#   negative-guard-to-positive-guard reorder and the local-variable staging. Both
#   keep the byte-identical obligation and the frozen `prove_correct` body (which
#   is generic over the impl shape: `loom_solve <;> simp_all [renderDecision]`),
#   and both were verified to build.
# PORTED (3 rivals): the pre-change overshoot (drop the guard, always emit), the
#   mirror underdeliver (always take the hidden result), and the value-level
#   overdeliver-double port directly. The nagini tally observable (sink.work) maps
#   to the pair (emitted, scene); the overshoot/underdeliver rivals attack the
#   emitted-flag decision, the double rival attacks the scene value.
# ADDED (uniqueness-hidden-scene-leak): this carrier splits the single nagini
#   "sink.work == Old(sink.work) when invisible" clause into TWO independent
#   observables — `emitted` (did work run) and `scene` (what was placed). The
#   overshoot rival attacks `emitted`; this ADDED rival isolates the `scene =
#   blank` conjunct on the hidden branch (correct emitted flag, leaked content),
#   which no ported rival pins on its own. It exists because the velvet carrier
#   models one observable the nagini scalar tally could not separate.
# PORTED, RE-AIMED (admissibility-readonly-and-sink -> admiss-hidden-nonblank):
#   the sibling's SUBSTANCE (half-permission inputs and a writable sink
#   permission are usable) has no analogue here — both inputs are ordinary
#   immutable values and there is no permission system. Its QUESTION does: is
#   the obligation actually MEETABLE, and meetable non-trivially, at an
#   F2P-shaped input? "The method has no `require` clause" answers a different
#   question and is NOT sufficient grounds to drop the lane, because on a total
#   carrier PRECOND-TOO-STRONG arrives as an obligation unsatisfiable or
#   degenerate at exactly the interesting input rather than as an unsatisfiable
#   precondition. So the lane is ported with its target moved to the
#   obligation: at (visible=false, renderedScene=7) the case evaluates that both
#   `ensures` clauses hold JOINTLY of one concrete post-image and that the
#   obligation separates that input from its visible counterpart. Impl and
#   frozen proof body verbatim; the assert is live (negating either the joint
#   conjunct or the separation conjunct leaves an unsolved goal — both measured).
# VACUOUS (frame-mutation-write-content): the nagini sibling's MANDATORY frame
#   rival writes back into a read-only input held at Acc(.,1/2) and is rejected
#   for insufficient permission. This backend is referentially transparent:
#   `visible` and `renderedScene` are immutable values, NEITHER is a `mut` binder,
#   there is no heap, no aliasing and no permission system. No read-only field to
#   overwrite and no substitute probe to build. Reported vacuous per the porting
#   map (frame/permission-mutation is vacuous on this backend), not fabricated.
# DROPPED (AXIOM_TESTS): the nagini bundle's single axiom-soundness probe
#   (the real renderer honours the visibility flag) belongs to the G-AX lane; this
#   bundle declares NO axiom and NO deep-model reference (the emission body's
#   content is a directive-7 FREE INPUT `renderedScene`, not a consumed contract —
#   mapping.md §3). This gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Two input binders, both varied and both abused:
#     visible       -> false (overshoot, hidden-scene-leak), true (underdeliver, double)
#     renderedScene -> 3, 2, 5, 6  (hidden-scene-leak & double discriminate ONLY
#                       when it is non-blank, so the binder is genuinely abused,
#                       not merely present)
#   Both top-level clauses are attacked: clause A (`out = renderDecision …`) by
#   underdeliver (visible emitted) and double (visible scene); clause B
#   (hidden ⇒ emitted=false ∧ scene=blank) by overshoot (the emitted conjunct)
#   and hidden-scene-leak (the scene=blank conjunct). The clauses are defended by
#   the two positive controls, and their JOINT satisfiability at a hidden element
#   with non-blank content by the admissibility case. The four reject witnesses
#   probe four DISTINCT input points (pts=4); no point is pinned across the
#   battery. All three kind lanes are populated: soundness (2), admissibility (1),
#   uniqueness (4) — so all three directions this gate tests are asked here.
#
# CARRIER NOTE. The carrier is fully transparent (`Bool`, `Nat`, `DecidableEq`
#   `RenderResult`), so every witness refutes at concrete literals via the tester
#   machinery and closes by `decide` — no conditioning on an opaque term, hence no
#   witness binds anything and the consistency probe is a no-op. Each witness was
#   SEEN to discriminate with two real builds: it ELABORATES against the rival and
#   FAILS against the frozen (straight-line, `decide`-reducible) solution, whose
#   tester returns `true` because gold satisfies the spec at that input.
AXIOM_TESTS = []
