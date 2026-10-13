"""properties.py — G-PBT falsification battery for django__django-16595 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct reduceAlterField`` tactic
body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct reduceAlterField``
obligation survives) and swaps in a candidate implementation; it is judged by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE — ONE contracted method:

  reduceAlterField (op : ReduceInput) return (out : ReduceResult)
    ensures out = reduceDecision op                              -- (Q1)

  no ``require`` clause: the admitted input domain is TOTAL (all eight values of
  the three-boolean carrier reach the postcondition).

``reduceDecision`` is a total, fully unfolded ``def`` in the frozen ``pure``
region — NOT an opaque oracle (the ``axioms`` region declares no ``axiom``), so
there is no ungrounded answer key an impl could echo, and every input point
decides under ``decide``:

    reduceDecision op =
      if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField
      then ReduceResult.keepLater else ReduceResult.deferToInherited

BINDER STRUCTURE (read this before judging binder coverage). ``op`` is the sole
input binder, a record of THREE independent booleans, and (Q1) genuinely depends
on each one:

  * ``op.incomingIsAlter``  — whether the step that immediately follows is
    itself an alteration of a model field's definition. This is the disjunct the
    desired behaviour ADDS: with it removed, (Q1) still holds everywhere the
    other disjunct fires, so a rival that drops it is a PARTIAL-DOMAIN miss
    refutable only at ``(alter, ¬remove, same)``.
  * ``op.incomingIsRemove`` — whether the following step removes a model field.
    The disjunct that was already honoured. A rival keeping only the ADDED
    disjunct is the exact dual, refutable only at ``(¬alter, remove, same)``.
  * ``op.sameField``        — whether the following step targets the same model
    field. The conjunct that gates BOTH kinds; a rival that ignores it collapses
    steps that must not collapse, refutable at ``sameField = false``.

The three booleans are independent, so (Q1) is a genuine 3-input function and no
single witness point can stand in for another. The seven reject witnesses below
sit at seven DISTINCT points and move every one of the three fields across
``{false, true}``:

    (alter, remove, same) = (T,F,T) (F,T,T) (F,T,F) (F,F,T) (F,F,F) (T,T,T)
                            (T,F,F)

The last point is reached by ``weak-same-field-gates-removal-only`` (added on
audit): it is the corner where the ADDED kind observation holds while the
same-field conjunct does NOT, and it is the point a rival that attaches the
same-field guard to only ONE of the two kinds is refuted at. Without it the
battery had no witness anywhere in the ``incomingIsAlter = true,
sameField = false`` sub-domain, so a rival wrong only there would have verified
unnoticed.

ADVERSARIAL READ of the sibling battery's classes on this carrier:

  * FRAME-MUTATION (permission overwrite) — VACUOUS here, not omitted. The
    sibling carries two such cases because both of its inputs are held at a
    fractional heap permission a wrong impl can illegally overwrite to satisfy a
    clause vacuously. Lean and Velvet are referentially transparent: ``op`` is an
    immutable value, the method declares no ``mut`` binder, and there is no heap
    and no aliasing — so there is no read-only input to write to and no
    substitute probe to build. NOT fabricated.
  * PARTIAL-DOMAIN / uniqueness — APPLIES, and is the core of this battery: each
    of the two kind disjuncts and the same-field conjunct can be dropped
    independently, and the resulting rival agrees with the frozen spec over most
    of the eight-point domain.
  * CONTROL-FLOW / value-double-mask — APPLIES in narrowed form (see the
    accounting at the bottom): the sibling's masking rival exploits a two-element
    result whose second element must be a fresh value. This carrier's result is
    the binary decision only, so the masking shape here is a rival that gets the
    outcome right on one arm and inverts it on the other (``weak-always-collapse``
    / ``weak-never-collapse``).
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a concrete ``def`` over the
    method's own argument, so there is nothing opaque to echo. Carried instead by
    honest cheapest-reshape POSITIVE CONTROLS (``pos-*``).
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

WITNESS MECHANICS. The spec is a ``method`` contract, not a bare predicate, so
each witness reaches it through Velvet's own tester machinery:
``reduceAlterFieldTester op = false`` says the extracted program's result
violates the method's postcondition at that concrete ``op``. Checked in a file
whose ``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. Every input is a literal three-boolean record, so ``decide`` settles it
outright and no witness needs to CONDITION on the carrier — there are no witness
binders and therefore no satisfiability question. Each of the six was verified
out-of-band with two real builds: it ELABORATES against its rival (exit 0) and
FAILS against the frozen solution (``Tactic `decide` proved that the proposition
... is false``) — i.e. gold's build fails because ``decide`` actively REFUTES the
witness, not because of an unknown name or a parse error, which is the failure
mode that would make the second half meaningless.

Two further checks were run, because "elaborates on the rival, fails on gold" can
also be satisfied by an artifact:

  * NOT-DEGENERATE. ``reduceAlterFieldTester _ = false`` must not hold
    everywhere. At the two points where ``weak-removal-only`` AGREES with gold
    — ``(F,T,T)`` and ``(F,F,F)`` — the tester is provably TRUE against that very
    rival (``decide`` refutes ``= false``). So each witness is a claim about one
    input point, not a blanket statement the rival satisfies vacuously.
  * REJECTION IS THE SPEC'S, NOT THE TACTIC'S. Each rival's own failing build was
    read, and all seven fail with ``unsolved goals`` on the
    ``«ensures_1: out = reduceDecision op»`` case — never with a mere
    tactic-shape error, the default outcome of reshaping an impl that would make
    a reject case hollow. The residual goal is the spec obligation the rival
    cannot meet, stated in terms of the binders it mishandles; e.g.
    ``⊢ op.sameField = true`` under ``if_pos : op.incomingIsAlter = true ∨
    op.incomingIsRemove = true`` for ``weak-ignores-same-field``. Precise wording
    per rival, re-read on audit (an earlier revision of this note claimed the
    goal always "names exactly the dropped conjunct/disjunct", which overstates
    two of them — the two CONSTANT rivals drop no conjunct at all):

      weak-removal-only       ⊢ alter = true ∨ remove = true → same = false
                              (under if_neg : remove = true → same = false)
      weak-alteration-only    ⊢ alter = true ∨ remove = true → same = false
                              (under if_neg : alter = true → same = false)
      weak-ignores-same-field ⊢ same = true   (under if_pos : the kind disjunction)
      weak-same-field-only    ⊢ alter = false → remove = true (under if_pos : same = true)
      weak-same-field-gates-removal-only
                              ⊢ (alter = true ∨ remove = true) ∧ same = true
      weak-always-collapse    ⊢ (alter = true ∨ remove = true) ∧ same = true
      weak-never-collapse     ⊢ alter = true ∨ remove = true → same = false

AXIOM lane: EMPTY (the bundle declares no ``axiom`` and no deep-model reference;
the decision is modeled directly). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16595"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- anchors. `_IMPL` lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region; `_TAC` is the whole tactic body of the single
# ---- `prove_correct` (also elided from the consumer spec view). Both are
# ---- unique in Solution.lean, asserted at load time by `_swap`.
_IMPL = """    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
      return ReduceResult.keepLater
    else
      return ReduceResult.deferToInherited
"""
_TAC = "  loom_solve <;> simp_all [reduceDecision]\n"

# A reshaped impl may need its tactic script retuned; the carrier is three
# booleans, so an exhaustive case split closes any correct reshape without a new
# lemma (no `sorry`, no new `theorem`, obligation statement untouched).
_TAC_CASES = ("  loom_solve <;> (obtain ⟨a, b, c⟩ := op; "
              "cases a <;> cases b <;> cases c <;> simp_all [reduceDecision])\n")


def _impl(new_impl: str, new_tac: str | None = None) -> str:
    src = _swap(_BASE, _IMPL, new_impl)
    return src if new_tac is None else _swap(src, _TAC, new_tac)


def _guard(cond: str) -> str:
    """A rival that keeps the two-outcome shape and changes only the decision."""
    return (f"    if {cond} then\n"
            "      return ReduceResult.keepLater\n"
            "    else\n"
            "      return ReduceResult.deferToInherited\n")


_TESTER = ("extract_program_for reduceAlterField\n"
           "prove_precondition_decidable_for reduceAlterField\n"
           "prove_postcondition_decidable_for reduceAlterField\n"
           "derive_tester_for reduceAlterField\n\n")


def _witness(alter: bool, remove: bool, same: bool) -> str:
    def b(v):
        return "true" if v else "false"
    pt = (f"{{ incomingIsAlter := {b(alter)}, incomingIsRemove := {b(remove)}, "
          f"sameField := {b(same)} }}")
    return (_TESTER
            + f"example : reduceAlterFieldTester {pt} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG (or the proof is fragile). Each keeps the
    # `prove_correct` obligation; the carrier is finite and non-recursive, so
    # every reproof is an exhaustive case split — no induction, no helper
    # lemma, no assumption.
    # =====================================================================
    {
        "id": "pos-nested-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: split the single conjunction into NESTED tests — gate on the
        # same-field observation first, then on the kind of the following step.
        # `(p || q) && r` and `r` guarding `(p || q)` decide identically at
        # every one of the eight input points, so (Q1) is untouched. The frozen
        # tactic script closes it unchanged.
        "module": _impl(
            "    if op.sameField then\n"
            "      if op.incomingIsAlter || op.incomingIsRemove then\n"
            "        return ReduceResult.keepLater\n"
            "      else\n"
            "        return ReduceResult.deferToInherited\n"
            "    else\n"
            "      return ReduceResult.deferToInherited\n"),
        "rationale": "correct reshape: the one conjunction becomes two nested "
                     "tests (same-field first, then the kind disjunction). The "
                     "decision is pointwise identical on all eight inputs, so "
                     "(Q1) `out = reduceDecision op` still discharges. Must "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-accumulator",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a mutable accumulator initialised to the defer outcome and
        # overwritten only when the collapse applies, instead of a two-armed
        # return. Same decision; exercises the write-then-return shape.
        "module": _impl(
            "    let mut out : ReduceResult := ReduceResult.deferToInherited\n"
            "    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then\n"
            "      out := ReduceResult.keepLater\n"
            "    return out\n"),
        "rationale": "correct reshape: accumulator initialised to the "
                     "defer-to-existing-dispatch outcome and overwritten only "
                     "when the collapse condition holds, replacing the two-armed "
                     "return. Same decision at every input, so (Q1) holds; must "
                     "verify.",
    },
    {
        "id": "pos-hoisted-kind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the kind disjunction to a local and COMMUTE the
        # conjunction (same-field test first). `&&` is commutative and the
        # post-image pins the decision, not the term order — so this must
        # verify. The frozen script does not close the commuted form, so the
        # tactic body is retuned to an exhaustive split over the three booleans
        # (a tactic-body change only: the obligation header is untouched and no
        # new declaration or assumption appears).
        "module": _impl(
            "    let kindApplies := op.incomingIsAlter || op.incomingIsRemove\n"
            "    if op.sameField && kindApplies then\n"
            "      return ReduceResult.keepLater\n"
            "    else\n"
            "      return ReduceResult.deferToInherited\n",
            _TAC_CASES),
        "rationale": "local-binding reshape plus a COMMUTED conjunction: the "
                     "kind disjunction is bound once and tested after the "
                     "same-field observation. `&&` is commutative, so the "
                     "decision is unchanged and (Q1) holds. This is the case "
                     "that shows the spec pins the DECISION rather than the "
                     "impl's term order — must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the whole guard and swap the two arms, so the
        # defer-to-existing-dispatch outcome is returned from the THEN branch.
        # Classical negation of a decidable boolean condition, so the decision
        # is pointwise identical; tactic body retuned as above.
        "module": _impl(
            "    if !((op.incomingIsAlter || op.incomingIsRemove) && op.sameField) then\n"
            "      return ReduceResult.deferToInherited\n"
            "    else\n"
            "      return ReduceResult.keepLater\n",
            _TAC_CASES),
        "rationale": "branch-order reshape: the guard is negated and the two "
                     "arms swapped, so the defer outcome comes from the THEN "
                     "branch. Boolean negation is exact on this decidable "
                     "condition, so the decision is pointwise identical and "
                     "(Q1) still discharges; must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuously satisfied
    # (the domain is total: all eight carrier values are admitted). The
    # remaining admissibility risk on a total domain is that the post-image is
    # DEGENERATE or unsatisfiable at the interesting point — a spec no impl can
    # meet reads exactly like a spec every impl meets. So this case discharges
    # an in-region `assert` pinning the post-image at the two points that
    # differ in exactly the behaviour under change: the pair collapses when the
    # following step is a same-field alteration, and does not when that step
    # targets a different field. Both halves must be established by the
    # verifier. The frozen impl and the frozen tactic body follow verbatim, so
    # (Q1) still discharges too; the assert is live, not decoration. Liveness
    # MEASURED, not asserted: flipping either conjunct's expected outcome (the
    # collapse point to defer, or the defer point to collapse) makes the build
    # FAIL with `unsolved goals` on the `«assert_1: ...»` case and residual goal
    # `⊢ False`. So the verifier really does have to establish both halves, and
    # the case cannot pass by the assert being trivially true.
    # =====================================================================
    {
        "id": "admiss-decision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      (reduceDecision { incomingIsAlter := true, incomingIsRemove := false,\n"
            "                        sameField := true } = ReduceResult.keepLater ∧\n"
            "       reduceDecision { incomingIsAlter := true, incomingIsRemove := false,\n"
            "                        sameField := false } = ReduceResult.deferToInherited))\n"
            + _IMPL),
        "rationale": "the input domain is total (no `require`), so this probes "
                     "the other admissibility risk: that the post-image is "
                     "satisfiable AND non-degenerate at the point the desired "
                     "behaviour concerns. The in-region assert makes the "
                     "verifier establish that (Q1) demands the COLLAPSE outcome "
                     "when the following step is a same-field alteration and the "
                     "defer outcome when that same step targets a different "
                     "field — i.e. the two outcomes are both reachable and the "
                     "clause is not constantly one of them. The frozen impl and "
                     "tactic body are kept verbatim so (Q1) discharges as well. "
                     "If the assert could not be established the obligation "
                     "would be unsatisfiable at the interesting point "
                     "(PRECOND-TOO-STRONG / degenerate post-image).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Six distinct refutation
    # points; every field of `op` is moved across {false, true}.
    # =====================================================================
    {
        "id": "weak-removal-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour: admit only the removal kind into the
        # collapsing branch, so a following same-field ALTERATION defers.
        # Agrees with the frozen spec on seven of the eight input points.
        "module": _impl(_guard("op.incomingIsRemove && op.sameField")),
        "refinement": "its faithful real counterpart is the empty diff — the "
                      "pre-patch source, whose collapsing branch admits only a "
                      "following removal of the field. Two successive "
                      "alterations of the same model field are then left "
                      "uncombined, which is exactly the behaviour the issue "
                      "reports and the sole failing test asserts against: it "
                      "optimizes a run of same-field alterations and requires "
                      "the earlier ones to be dropped in favour of the last. "
                      "The rival leaves them all in place, so the test still "
                      "FAILS — it would NOT resolve.",
        "rationale": "REJECT from (Q1): the rival drops the `incomingIsAlter` "
                     "disjunct, so at a following same-field ALTERATION it "
                     "returns the defer outcome where the post-image demands "
                     "the collapse. Refuted at "
                     "`(alter=true, remove=false, same=true)` — the one point "
                     "the ADDED disjunct is solely responsible for, and the "
                     "sub-domain no other rival here probes.",
        "witness": _witness(True, False, True),
    },
    {
        "id": "weak-alteration-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact DUAL: honour the newly-admitted kind but drop the kind that
        # was already honoured. Also agrees with the spec on seven of eight.
        "module": _impl(_guard("op.incomingIsAlter && op.sameField")),
        "refinement": "its faithful real counterpart REPLACES the kind test "
                      "rather than widening it, admitting a following "
                      "alteration but no longer a following removal of the "
                      "field. The pre-existing, unchanged assertion that a "
                      "field removal absorbs an earlier alteration of that same "
                      "field then regresses: the pair is no longer combined, so "
                      "that test FAILS while the newly-fixed one passes — it "
                      "would NOT resolve.",
        "rationale": "REJECT from (Q1): the rival drops the "
                     "`incomingIsRemove` disjunct, so at a following same-field "
                     "REMOVAL it returns the defer outcome where the post-image "
                     "demands the collapse. Refuted at "
                     "`(alter=false, remove=true, same=true)` — the mirror "
                     "sub-domain of `weak-removal-only`, which is what shows "
                     "(Q1) constrains BOTH disjuncts independently and not just "
                     "the one under change.",
        "witness": _witness(False, True, True),
    },
    {
        "id": "weak-ignores-same-field",
        "kind": "uniqueness",
        "expect": "reject",
        # Both kinds admitted, but the same-field conjunct is dropped: the
        # collapse now fires for a following step on a DIFFERENT model field.
        # Correct on every same-field input, wrong off it.
        "module": _impl(_guard("op.incomingIsAlter || op.incomingIsRemove")),
        "refinement": "its faithful real counterpart widens the kind test but "
                      "drops the guard that the following step act on the SAME "
                      "model field. Independent operations on unrelated fields "
                      "or models would then be collapsed into each other and "
                      "silently lost. Many pre-existing, unchanged assertions "
                      "interleave operations on distinct fields and require them "
                      "NOT to be merged; those FAIL, so it would NOT resolve.",
        "rationale": "REJECT from (Q1): with the `sameField` conjunct removed, "
                     "a following step of an admitted kind on a DIFFERENT field "
                     "yields the collapse where the post-image demands the "
                     "defer outcome. Refuted at "
                     "`(alter=false, remove=true, same=false)` — a point holding "
                     "`sameField = false` together with an admitted kind, so it "
                     "demonstrates (Q1)'s dependence on the same-field binder. "
                     "It is the REMOVAL half of that sub-domain; "
                     "`weak-same-field-gates-removal-only` covers the "
                     "ALTERATION half at `(alter=true, remove=false, "
                     "same=false)`.",
        "witness": _witness(False, True, False),
    },
    {
        "id": "weak-same-field-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary miss: keep the same-field guard but drop the kind
        # test entirely — ANY following step on the same field collapses,
        # including kinds the desired behaviour must leave to the existing
        # dispatch. Correct wherever a kind is admitted; wrong on the rest.
        "module": _impl(_guard("op.sameField")),
        "refinement": "its faithful real counterpart keeps the same-field guard "
                      "but stops discriminating the KIND of the following step, "
                      "so every following step on that field — including a "
                      "renaming of it, or a step whose combination the "
                      "pre-existing dispatch handles specially — is collapsed "
                      "onto that step alone. The unchanged assertion that a "
                      "same-field renaming is combined by carrying the "
                      "alteration ACROSS the rename (a two-operation result, "
                      "not the rename alone) then observes the alteration "
                      "dropped outright and FAILS — it would NOT resolve.",
        "rationale": "REJECT from (Q1): dropping the kind disjunction makes the "
                     "collapse fire on a same-field step of a kind the "
                     "post-image leaves to the existing dispatch. Refuted at "
                     "`(alter=false, remove=false, same=true)` — a same-field "
                     "step of NEITHER admitted kind, a point no other rival "
                     "probes, and the near-miss that separates this rival from "
                     "`weak-always-collapse` (which is additionally wrong off "
                     "the same field).",
        "witness": _witness(False, False, True),
    },
    {
        "id": "weak-same-field-gates-removal-only",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED ON AUDIT. Both kinds are admitted into the collapsing branch,
        # but the same-field conjunct gates only the PRE-EXISTING kind: a
        # following removal must target the same field, while a following
        # alteration collapses unconditionally. Correct on seven of the eight
        # input points; wrong exactly at `(alter, ¬remove, ¬same)`, which is the
        # sub-domain no other witness in this battery occupied — every other
        # reject case holds `incomingIsAlter = false` whenever
        # `sameField = false`. A rival mis-scoping the guard this way would
        # therefore have gone unnoticed.
        "module": _impl(_guard(
            "op.incomingIsAlter || (op.incomingIsRemove && op.sameField)")),
        "refinement": "its faithful real counterpart widens the kind test but "
                      "attaches the same-field requirement to only the kind "
                      "that already had it, leaving the newly-admitted kind "
                      "ungated — the precedence slip of writing the widened "
                      "condition as a disjunction whose same-field conjunct "
                      "binds tighter than intended. A following alteration of a "
                      "DIFFERENT model's field, or of another field on the same "
                      "model, is then collapsed away and that operation is lost. "
                      "The pre-existing, unchanged assertions that interleave "
                      "alterations of distinct fields and require them NOT to be "
                      "merged FAIL, so it would NOT resolve — while the newly "
                      "fixed same-field case passes, which is what makes this "
                      "the plausible near-miss rather than an obvious one.",
        "rationale": "REJECT from (Q1): with the same-field conjunct gating only "
                     "the pre-existing kind, a following ALTERATION on a "
                     "different field yields the collapse where the post-image "
                     "demands the defer outcome. Refuted at "
                     "`(alter=true, remove=false, same=false)` — the corner "
                     "where the ADDED kind observation holds while the "
                     "same-field conjunct does not, and the only witness here "
                     "in that sub-domain. Rebuilt on audit: the witness "
                     "elaborates against the rival (exit 0) and `decide` "
                     "actively REFUTES it against the frozen solution (exit 1), "
                     "and the rival's own build fails with `unsolved goals` on "
                     "the `«ensures_1: ...»` case, residual goal "
                     "`⊢ (alter = true ∨ remove = true) ∧ same = true`.",
        "witness": _witness(True, False, False),
    },
    {
        "id": "weak-always-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # One arm of the decision, constantly: always collapse. Right on every
        # input where the collapse applies, wrong on every other — the blunt
        # value-mask counterpart of the never-collapse rival below.
        "module": _impl("    return ReduceResult.keepLater\n"),
        "refinement": "its faithful real counterpart drops the guard entirely "
                      "and always returns the following step alone, collapsing "
                      "every adjacent pair regardless of kind or target. The "
                      "optimizer would discard unrelated operations wholesale; "
                      "essentially every pre-existing assertion about which "
                      "operations survive optimization FAILS, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from (Q1): a constant collapse contradicts the "
                     "post-image at every input where the condition is false. "
                     "Refuted at `(alter=false, remove=false, same=false)` — "
                     "the all-false corner, where NEITHER the kind disjunction "
                     "nor the same-field conjunct holds, so the refutation is "
                     "attributable to the guard as a whole rather than to any "
                     "single binder.",
        "witness": _witness(False, False, False),
    },
    {
        "id": "weak-never-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # The other arm, constantly: never collapse — the do-nothing rival that
        # always defers to the pre-existing dispatch. Supporting near-miss
        # confirming the collapse outcome is reachable at all.
        "module": _impl("    return ReduceResult.deferToInherited\n"),
        "refinement": "its faithful real counterpart never combines the pair, "
                      "always leaving the decision to the pre-existing "
                      "dispatch. It resolves NOTHING — the failing test that "
                      "requires successive same-field alterations to be reduced "
                      "still fails, and the unchanged assertions that a "
                      "same-field removal absorbs an earlier alteration "
                      "regress as well. It would NOT resolve.",
        "rationale": "REJECT from (Q1): a constant defer contradicts the "
                     "post-image at every input where the collapse condition "
                     "holds. Refuted at "
                     "`(alter=true, remove=true, same=true)` — the all-true "
                     "corner, the only witness point here where BOTH kind "
                     "observations hold at once, so it also shows the "
                     "post-image treats the two kinds as a disjunction rather "
                     "than requiring exactly one.",
        "witness": _witness(True, True, True),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting
# ---------------------------------------------------------------------------
# The sibling battery has 12 SPEC cases (2 soundness positives, 1
# admissibility, and 9 expect="reject" uniqueness cases — of which 2 are the
# frame-mutation rivals and 7 are behavioural rivals) and an EMPTY axiom lane.
# This battery has 12 (4 positives, 1 admissibility, 7 rivals). Corrected on
# audit: an earlier revision of this note said "10 SPEC cases ... 5 uniqueness
# rivals", which the sibling manifest does not bear out (`len(SPEC_TESTS) == 12`,
# 9 of them `uniqueness`/`reject`). The disposition table below was already
# complete — it lists all 12 — so only the summary count was wrong.
# Case counts are not the target; what follows is the case-by-case disposition.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-reorder                   -> pos-nested-guard, pos-negated-guard  PORTED
#   pos-hoist                     -> pos-hoisted-kind                     PORTED
#   (no sibling)                  -> pos-accumulator                      NEW
#   admiss-f2p-shaped-input       -> admiss-decision-nondegenerate        PORTED (reshaped)
#   frame-write-this-kind         -> (none)                               VACUOUS
#   frame-write-nxt-kind          -> (none)                               VACUOUS
#   uniq-revert-remove-only       -> weak-removal-only                    PORTED
#   uniq-alter-only-drop-remove   -> weak-alteration-only                 PORTED
#   uniq-collapse-different-field -> weak-ignores-same-field              PORTED
#   uniq-always-none              -> weak-never-collapse                  PORTED
#   uniq-drop-rename              -> (none)                               NO CARRIER
#   uniq-rename-singleton         -> (none)                               NO CARRIER
#   uniq-rename-carry-is-nxt      -> (none)                               NO CARRIER
#   (no sibling)                  -> weak-same-field-only                 NEW
#   (no sibling)                  -> weak-always-collapse                 NEW
#   (no sibling)                  -> weak-same-field-gates-removal-only   NEW (audit)
#   AXIOM_TESTS (empty there too) -> (none)                               N/A
#
# PORTED positives. The sibling's branch-reorder argument (the kinds of a
#   following step are mutually exclusive tags, so testing them in a different
#   order cannot change which arm fires) becomes two cases here, because this
#   carrier admits two independent reshapes of the single guard: nesting the
#   conjunction (`pos-nested-guard`) and negating it while swapping the arms
#   (`pos-negated-guard`). The sibling's hoist-the-same-field-test-into-a-local
#   argument ports directly as `pos-hoisted-kind`, strengthened by also
#   commuting the conjunction so the case additionally shows the spec does not
#   pin the impl's term order. `pos-accumulator` is new: this backend's
#   write-then-return shape has no sibling counterpart and is worth defending
#   because it is the shape a real reshape most often takes here.
#
# PORTED admissibility, reshaped. The sibling's case asserts that a legitimate
#   F2P-shaped input satisfies the function's `Requires`. This method has NO
#   `require` clause, so that assertion is vacuous — the domain is total. The
#   argument was therefore re-aimed at the residual admissibility risk on a
#   total domain: that the post-image is degenerate at the point of interest.
#   The in-region assert pins BOTH outcomes at the two inputs that differ only
#   in the same-field observation, so the verifier must establish that the
#   clause really demands a collapse there and a defer here.
#
# VACUOUS, not omitted — frame-mutation. Both sibling frame cases overwrite a
#   field of an input held at a fractional heap permission. This backend is
#   referentially transparent: `op` is an immutable value, the method declares
#   no `mut` binder, there is no heap and no aliasing. There is no read-only
#   input to write to, so the class does not exist here and no substitute probe
#   was fabricated. (Directive 5's frame obligation is discharged structurally:
#   the method takes `op` by value and returns only the decision.)
#
#   DEMONSTRATED ON AUDIT. The write the sibling performs was attempted here as a
#   real build: `op.incomingIsAlter := true` spliced ahead of the frozen body
#   fails to ELABORATE — "`op.incomingIsAlter` cannot be mutated, only variables
#   declared using `let mut` can be mutated". So the class is not merely absent
#   by argument; the carrier makes the mutation unwritable. The nearest
#   expressible analogue — copy `op` into a `let mut` local, overwrite a field,
#   and decide from the copy — was also built, and it is REJECTED (residual case
#   `.false.false.true ⊢ False`). That is worth noting for what it shows: a
#   mutation-flavoured rival on this carrier is caught by (Q1) as an ordinary
#   wrong-decision rival, because the postcondition is stated over the original
#   `op`, not over whatever the impl computed with. There is nothing a frame case
#   would add that the value-level rivals do not already establish.
#
# NO CARRIER — the three rename rivals. The sibling contracts a function whose
#   result is an OPTIONAL LIST of steps, so its spec can pin the rename
#   carry-across precisely: a two-element result whose first element is the
#   following step and whose second is a fresh equivalent alteration of the
#   renamed field. This bundle's carrier is the BINARY decision (collapse onto
#   the later step, or leave the pair to the pre-existing combining dispatch) —
#   mapping.md §2 folds the rename branch's two-element result, the
#   `[self]`/list/bool fall-through, and everything else that is not exactly
#   "the later step alone" into the single `deferToInherited` tag, because the
#   behaviour under change distinguishes only that one outcome from every other.
#   The rename branch is therefore UNCHANGED infrastructure this bundle does not
#   model, and all three sibling rivals (drop the carry-across, collapse the
#   rename to a singleton, make the carried element be the rename itself) map to
#   impls that return `deferToInherited` on exactly the inputs the frozen impl
#   does. They are not wrong on this carrier: no witness can discriminate them,
#   because there is nothing to discriminate. Dropped deliberately, and NOT
#   because a proof would not close.
#
#   DEMONSTRATED ON AUDIT, not merely argued. Each of the three was
#   transliterated to this carrier and BUILT:
#     * `uniq-drop-rename` and `uniq-rename-carry-is-nxt` both fold to "defer at
#       the same-field/neither-kind point" — which is what the frozen impl
#       returns there. Built as a module: it VERIFIES (exit 0), confirming it is
#       observably identical to gold on all eight points. Shipping it as a
#       `reject` case would have been a false case; as a `verify` case it is a
#       duplicate positive. Correctly dropped as VACUOUS.
#     * `uniq-rename-singleton` (rename collapses to the later step alone) does
#       NOT fold to gold: it maps to collapsing at `(¬alter, ¬remove, same)`.
#       Built as a module: REJECTED (exit 1, `unsolved goals`, residual case
#       `.false.false.true ⊢ False`), and a witness at that point elaborates
#       against it (exit 0). But that is the SAME impl and the SAME refutation
#       point as `weak-same-field-only`, which already ships — so it is a
#       duplicate, not an omission. The sub-domain IS covered.
#   So all three dispositions hold, and the one that had residual attack value
#   was already carried under a different name. Note the SPIRIT of the "a following step of
#   an unadmitted kind must be left to the existing dispatch" half is carried by
#   `weak-same-field-only`, which collapses a same-field step of neither
#   admitted kind — the sub-domain a following rename inhabits on this carrier.
#
# NEW rivals — binder coverage, not parity. `weak-same-field-only` and
#   `weak-always-collapse` have no sibling counterpart and were added because
#   without them the reject witnesses would never hold `sameField = true` with
#   BOTH kind observations false, nor sit at the all-false corner: a rival that
#   mishandled only those regions would verify and this battery would not
#   notice. `weak-same-field-gates-removal-only` was added ON AUDIT for the same
#   reason and a measured gap: with only the original six, no witness sat
#   anywhere in the `incomingIsAlter = true, sameField = false` sub-domain (every
#   `sameField = false` witness held `incomingIsAlter = false`), so a rival that
#   gates only the pre-existing kind on the same-field observation was
#   unattacked. It was built as a real module and rejected, and its witness
#   discriminates. With all seven, the witnesses sit at seven distinct points and
#   every one of the three fields of `op` takes both values across the set.
#
# COMPLETENESS, MEASURED (audit). Binder coverage is a proxy; the stronger
#   statement was checked directly. All EIGHT single-point flips of the frozen
#   decision were built as modules — for each of the eight carrier values, an
#   impl agreeing with the frozen decision on the other seven points and
#   inverting the outcome at that one — and all eight were REJECTED, each with
#   `unsolved goals` on `«ensures_1: ...»` and a residual goal naming exactly the
#   flipped point (e.g. `case ....true.false.true ⊢ False`). Since the carrier is
#   finite with eight values and every single-point deviation is caught, (Q1)
#   pins the decision at every input: NO wrong impl of this modeled decision can
#   satisfy the spec. That is the whole SPEC-TOO-WEAK question settled by
#   exhaustion rather than by sampling, and it is why the seven rivals above are
#   a readable selection rather than a hopeful one.
#
# ---------------------------------------------------------------------------
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
# ---------------------------------------------------------------------------
# The sibling battery for this instance ships NO divergence case, so there is
# nothing to port. The class was probed here anyway, and the result is recorded
# because the two possible dispositions carry opposite information and only one
# of them is true here.
#
# This bundle sets `loom.semantics.termination "total"` (line 4) and opens
# `TotalCorrectness` (line 7), as do all 500 velvet bundles; none sets `"partial"`.
# Under TOTAL-correctness semantics the postcondition is claimed of ALL runs, not
# only of terminating ones, so the verifier demands a decreasing measure on every
# loop and discharges its descent. A diverging rival is therefore REJECTED.
# Re-measured on this bundle with real builds (tactic body reduced to a bare
# `loom_solve`, which a rival may do; only the `prove_correct` header must
# survive):
#
#   * a `while true` loop with an `invariant` and `done_with False` but NO
#     `decreasing` clause, spliced ahead of the frozen body:  REJECTED (exit 1),
#     `error: Decreasing annotations are required in total correctness semantics`
#   * the same loop CARRYING a measure its body never changes (`decreasing q`,
#     body `q := q`):                                         REJECTED (exit 1),
#     `unsolved goals`, `case «decreasing_1: q»`, residual `q < q`
#
# The second row is the decisive one. A rival that merely omits the annotation
# could be dismissed as tripping a linter; this one supplies the annotation and is
# still refused, on the MEASURE's own descent goal. The mechanism is in Loom:
# `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`
# (`Loom/MonadAlgebras/NonDetT/Basic.lean:544`) takes `measure : β -> Nat` and
# emits `measure b' < measure b`; only the `PartialCorrectness` twin (:211) takes
# an `Option ℕ` and DISCARDS it, and the `set_option` elaborator itself runs
# `openScope `TotalCorrectness` (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so
# the option and the `open` cannot drift apart.
#
# RETRACTED: an earlier revision of this block said the bundle sets `"partial"`,
# recorded three `while true` shapes as VERIFYING at exit 0 (including two
# returning a constant COLLAPSE / DEFER outcome, called "the sharp form of the
# finding"), concluded that the decision (Q1) pins is left wholly UNCONSTRAINED,
# and escalated an open `verify`-does-not-imply-`resolve` break against the spec.
# It also recorded a MEASUREMENT TRAP claiming the divergent guard must be a
# literal `true` because a data-dependent guard rejects for an unrelated reason.
# None of that survives: the literal-`true` shapes are rejected too, so the trap
# was reading a real rejection as a probe artifact. The spec ADMITS no diverging
# rival, and nothing is open.
#
# No reject case is shipped even so, for a witness-contract reason rather than a
# spec one: the rejection lands on the `method` command, so the rival's module
# never compiles and the witness the gate derives from it cannot elaborate, which
# records `witness-unproven` (INCONCLUSIVE, forcing MALFORMED-TESTS).
#
# ---------------------------------------------------------------------------
# TOOLING NOTE (audit) — a reshape class this backend cannot express, recorded so
# it is not mistaken for a spec defect. Attack E tried correct reshapes that
# `match` on a Bool inside the impl region:
#
#     let s := op.sameField
#     match s with
#     | true  => ...
#     | false => return ReduceResult.deferToInherited
#
# This is a FAITHFUL, correct impl, but it does not elaborate: the failure is
# `Failed to parse an assertion without names: WPGen (match ... with | true =>
# pure ... | false => pure ...)`. The weakest-precondition generator does not
# handle a `match` scrutinizing a Bool in this position. The control build settles
# that it is the `match` and not the `let`: the same impl with `if s && ...`
# instead of `match s with` VERIFIES (exit 0), as does an `if`-chain early-return
# reshape and an 8-way `match` on the three fields as a tuple. So this is a
# VERIFIER-FRONTEND limitation, NOT SPEC-TOO-STRONG — the spec does not reject
# the impl; the impl never reaches the spec. Two correct reshapes of this shape
# are therefore absent from the positives above for a tooling reason, and the
# reason is stated here rather than passed off as inexpressibility.
#
# ---------------------------------------------------------------------------
# AXIOM lane. The sibling's `AXIOM_TESTS` is empty and so is this one: the
# bundle declares no `axiom` and no deep-model reference (the decision is
# modeled directly from three observable booleans), so there is no axiom
# soundness or containment obligation to probe. The gate ignores AXIOM_TESTS
# regardless — that lane belongs to G-AX.
# ---------------------------------------------------------------------------
AXIOM_TESTS = []
