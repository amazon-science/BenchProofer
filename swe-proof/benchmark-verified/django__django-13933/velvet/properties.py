"""properties.py — G-PBT falsification battery for django__django-13933 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct renderInvalidChoice`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates).

DEFENDED SURFACE (one contracted method over a fully TRANSPARENT carrier). The
routine produces the rendered text of a parametrized rejection message by
substituting the offending submitted value into a value placeholder slot:

  renderInvalidChoice (template : List Frag) (value : List Char)
      return (out : List Char)
    ensures out = rendered value template
    ensures rendered value [Frag.valueSlot] = value
    ensures ∀ c, rendered value [Frag.lit c] = [c]

The load-bearing, IMPL-CONSTRAINING clause is the first: ``out = rendered value
template``. ``rendered`` is a fully-unfolded front-recursive fold — a literal
fragment contributes its one code point, the value slot is FILLED with the
value's code points, and the whole template is the left-to-right concatenation.
There is NO opaque answer key to echo (the ``axioms`` region declares no
``axiom``; ``rendered``/``renderFrag`` are concrete ``def``s of the two actual
inputs, so the postcondition IS the substitution, directive 8). The second and
third ``ensures`` are pure facts ABOUT ``rendered`` — they do not mention
``out`` — so they hold for every impl and are corroborating anchors, not
implementation obligations. The reject lane attacks the first clause, the only
one an impl can violate; that asymmetry is recorded here rather than papered
over with rivals that could not possibly fail.

BINDER STRUCTURE (read before judging binder coverage). The load-bearing clause
depends on both inputs, and through the fold on FOUR independent sub-behaviours,
each of which some rival below attacks:

  * ``template``, per-fragment, ``valueSlot`` arm — the slot must be FILLED with
    the value, not echoed as a token and not filled with part of the value.
  * ``template``, per-fragment, ``lit`` arm — a literal must pass exactly ``[c]``
    through.
  * ``template``, the COMBINATION — the per-fragment renderings concatenate in
    left-to-right template order. Neither arm being right forces the order to be.
  * ``template``, the fold's NIL case — the empty template renders to nothing;
    a fold seeded with anything else contaminates every template.
  * ``value : List Char`` — the code points the slot is filled with; the
    substitution must reproduce the WHOLE value.

CARRIER NOTE — HOW A WITNESS REACHES THIS POSTCONDITION, AND WHAT IT IS REFUTED
AGAINST. Two measured facts shape every witness here.

1. The tester route is UNAVAILABLE. The third ``ensures`` is a ``∀ (c : Char)``
   over the whole code-point space, so ``prove_postcondition_decidable_for``
   cannot synthesise an instance and ``…Tester`` never forms. Measured: the
   directive leaves ``⊢ Decidable (∀ (c : Char), rendered value [Frag.lit c] =
   [c])`` as an unsolved goal. So each witness reaches the impl through Velvet's
   EXTRACTOR instead: ``renderInvalidChoiceExec t v`` is ``NonDetT.run
   (renderInvalidChoice t v)``, and ``renderInvalidChoiceExec t v ≠ DivM.res
   (rendered v t)`` says the extracted program's output contradicts the
   load-bearing clause at that concrete input.

2. The FROZEN impl decides nothing, so it cannot be the witness's second
   subject. The frozen impl keeps a ``while`` loop; under
   ``loom.semantics.choice "demonic"`` its fixpoint is opaque to the kernel, so
   ``decide`` against it never reduces. Measured with real builds on all five
   rivals below: the gold-side build fails with ``failed to synthesize
   Decidable …`` over the un-normalised ``forIn Lean.Loop.mk`` term — a STUCK
   REDUCTION, not a refutation. That exit code carries no information (the same
   error appears for a TRUE claim about that impl), so a witness discriminated
   only that way attests to nothing. This is the ``witness-undecided`` shape.

   The repair is the sanctioned one: every reject case names a
   ``witness_reference`` — the loop-free ``pos-direct-model`` source, which is
   ALSO shipped as an ``expect="verify"`` case, so the battery itself records
   that loop-freeness is not what any rival is being rejected for. Measured: the
   reference verifies (exit 0), and each witness fails against it by a real
   verdict — ``Tactic `decide` proved that the proposition False is false`` —
   with no stuck-reduction marker anywhere in the log. That is the required
   discrimination, and it is sound for the reason the gate documents: an impl the
   verifier accepts cannot violate its own spec, so a genuine witness must fail
   there.

   Each rival is itself written LOOP-FREE (a ``foldr``) so its own side reduces.
   That is a witnessing convenience, not a weakening: the frozen spec is
   untouched, and each rival is a genuinely wrong implementation of it. All five
   were confirmed to be rejected by the verifier on the OBLIGATION rather than by
   a tactic gap — e.g. the fold-base rival fails with ``unsolved goals, case
   «ensures_3: out = rendered value template»``, naming the load-bearing clause.

No witness below binds any hypothesis: all five state the refutation at literal
inputs, so there are no assumptions that could be jointly unsatisfiable and the
``witness-inconsistent`` forgery shape does not arise.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The sibling carries this MANDATORY (both inputs
    held at a fractional heap permission; a rival that WRITES either to satisfy
    the postcondition is rejected for insufficient permission). Lean and Velvet
    are referentially transparent: ``template`` and ``value`` are immutable
    values, the method declares no ``mut`` binder among its inputs, and there is
    no heap and no aliasing — so there is no read-only input to overwrite and no
    permission system to trip. Not fabricated, not substituted.
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
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. ``rendered`` is
    a total ``@[grind]``-anchored ``def`` of the two actual inputs (an
    A-reference validated == the real interpolation builtin by G-AX; mapping.md
    §3.1), so the postcondition IS the substitution; there is no marker to echo.
  * ADMISSIBILITY — CARRIED (``admiss-f2p-shape``). The method declares no
    ``require``, but "no precondition" is NOT the right reason to drop this lane
    on a total carrier: the analogue of PRECOND-TOO-STRONG here is the
    obligation being unsatisfiable at exactly an input of the TESTED SHAPE. So
    the positive discharges the load-bearing clause's right-hand side at a
    concrete quoted-slot-plus-literal-words template BY EVALUATION, as a
    ``have``, before closing the frozen obligation verbatim. Load-bearing:
    changing the expected string to the one that leaves the placeholder standing
    makes the same ``decide`` fail.
  * CONTROL-FLOW-EFFECT — N/A, as the sibling records: the modeled function is a
    pure value function; the rejection path carries no side effect visible to the
    ``List Char`` abstraction.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane (five rivals below).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the changed
interpolation is modeled deeply as an A-reference, not a consumed oracle). The
gate ignores ``AXIOM_TESTS`` regardless; see the accounting block at the bottom.
"""
from pathlib import Path

INSTANCE = "django__django-13933"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the whole gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Rivals that reshape the executable surface
# ---- entirely, and the loop-free positive control, swap on this block. ----
_IMPL = (
    "    -- impl-start\n"
    "    let mut result : List Char := []\n"
    "    let mut i := template.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ template.length\n"
    "      invariant result = rendered value (template.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let f := template[i - 1]!\n"
    "      result := renderFrag value f ++ result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end")
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the loop body (wholly inside the impl region, unique). The
# ---- loop-preserving positive reshapes only these lines, leaving the loop, its
# ---- invariants and the frozen proof script intact.
_LOOP_BODY = (
    "    do\n"
    "      let f := template[i - 1]!\n"
    "      result := renderFrag value f ++ result\n"
    "      i := i - 1")
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view).
# ---- A variant that reshapes the impl into one loop-free expression has no loop
# ---- invariant to peel, so the loop-tuned tail is retuned to a bare
# ---- `loom_solve`. The `prove_correct renderInvalidChoice` header — the
# ---- obligation itself — is preserved byte-identically in every variant.
_PROOF_GOLD = (
    "prove_correct renderInvalidChoice by\n"
    "  loom_solve\n"
    "  rw [rendered_drop_step value template i (by omega) (by omega)]\n"
    "  simp_all")
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

_PROOF_FLAT = "prove_correct renderInvalidChoice by\n  loom_solve"


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned to the loop-free
    shape. Used for the loop-free positive and every reject rival."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


def _rewrite_proof(proof):
    """Variant that keeps the frozen impl byte-for-byte and only prepends work
    inside the tactic body (elided from the consumer spec view). Used by the
    admissibility probe, which must discharge something at a concrete input
    BEFORE closing the frozen obligation verbatim."""
    return _swap(_BASE, _PROOF_GOLD, proof)


# ---- The concrete tested-shape input, as `List Frag` / `List Char`. A quoted
# ---- value slot, then the trailing literal words, each literal code point its
# ---- own `Frag.lit` (the template<->`List Frag` bijection of mapping.md §2).
# ---- Written as a template EXPRESSION, not as a rendered answer, so the
# ---- admissibility probe below has something to evaluate rather than restate.
_F2P_TEMPLATE = (
    "(Frag.lit '\"' :: Frag.valueSlot :: Frag.lit '\"' ::\n"
    "        \" is not one of the available choices.\".toList.map Frag.lit)")
_F2P_VALUE = "\"invalid\".toList"
_F2P_RENDERED = "\"\\\"invalid\\\" is not one of the available choices.\".toList"

# ---- The admissibility probe's tactic body: EVALUATE the load-bearing clause's
# ---- right-hand side at the concrete tested-shape input as a `have`, then close
# ---- the frozen obligation with the frozen script, byte-for-byte. `decide`
# ---- reduces the fold in the kernel, so the `have` is a real evaluation and not
# ---- a restatement; measured to FAIL (`decide` proved the proposition false)
# ---- when the expected string is changed to leave the placeholder standing.
_PROOF_ADMISS = (
    "prove_correct renderInvalidChoice by\n"
    "  have f2p_admissible :\n"
    f"      rendered {_F2P_VALUE}\n        {_F2P_TEMPLATE}\n"
    f"        = {_F2P_RENDERED} := by\n"
    "    decide\n"
    "  loom_solve\n"
    "  rw [rendered_drop_step value template i (by omega) (by omega)]\n"
    "  simp_all")


def _foldr_impl(slot_arm, lit_arm="[c]", seed="[]", stream="template"):
    """A loop-free rival: fold `renderFrag`'s two arms over the fragment stream.

    Parameterised on exactly the four sub-behaviours the binder-structure note
    above lists, so each rival differs from a CORRECT loop-free impl in one
    named place and nothing else.
    """
    return (
        "    -- impl-start\n"
        f"    let out := {stream}.foldr (fun f acc =>\n"
        f"      (match f with | .lit c => {lit_arm} | .valueSlot => {slot_arm})"
        f" ++ acc) {seed}\n"
        "    return out\n"
        "    -- impl-end")


# ---- The loop-free CORRECT impl. Shipped twice, deliberately: once as an
# ---- `expect="verify"` positive (`pos-direct-model`), and once as the
# ---- `witness_reference` every reject case is refuted against. Pairing them is
# ---- what makes the reject lane honest — the battery itself records that this
# ---- shape VERIFIES, so no rival is being rejected merely for being loop-free.
# ---- The gate re-checks it independently (shares the frozen spec, and verifies)
# ---- before using it as a subject.
_LOOPFREE = _rewrite_impl(
    "    -- impl-start\n    return rendered value template\n    -- impl-end")


# ---- witness preamble. `extract_program_for` is a directive inside the witness,
# ---- so `renderInvalidChoiceExec` exists on BOTH sides of the discrimination
# ---- check by construction (it is appended to both files). Every other name a
# ---- witness mentions (`rendered`, `Frag`, `DivM.res`) is frozen-solution
# ---- vocabulary, so no witness can pass by referencing something only one side
# ---- has.
_EXTRACT = "extract_program_for renderInvalidChoice\n\n"


def _witness(template: str, value: str) -> str:
    """`≠` between the extracted program's output and the load-bearing clause's
    right-hand side, at one concrete input. No hypotheses are bound, so there is
    nothing that could be inconsistent."""
    return _EXTRACT + (
        f"example : renderInvalidChoiceExec {template} {value}\n"
        f"    ≠ DivM.res (rendered {value} {template}) := by\n"
        "  unfold renderInvalidChoiceExec renderInvalidChoice\n"
        "  simp [NonDetT.run, pure]\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both confirmed exit 0 with real
    # `lean_verify.sh` runs.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded model directly, no
        # loop at all — maximally structurally different from the frozen backward
        # scan. Doubles as the no-ungrounded-echo control (the model IS the
        # substitution, so returning it is correct, not a cheat) and as the
        # `witness_reference` for the whole reject lane.
        "module": _LOOPFREE,
        "rationale": "the load-bearing clause `out = rendered value template` is "
                     "grounded in the inputs (a total fold over both), so returning "
                     "it directly satisfies it on the WHOLE domain and the reproof is "
                     "a bare `loom_solve` (no loop invariant to peel). If a faithful "
                     "correct reshape could not verify, the spec would be over-fit to "
                     "the scan's code shape (SPEC-TOO-STRONG). This source is also "
                     "the reject lane's `witness_reference`, so the battery records "
                     "on its own that the loop-free shape VERIFIES — no rival below "
                     "is rejected for being loop-free.",
    },
    {
        "id": "pos-piece-local",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, its invariants and the frozen proof script; only
        # names the exposed per-fragment rendering in a local `let` before
        # prepending. Observationally identical at every input.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "    do\n"
            "      let f := template[i - 1]!\n"
            "      let piece := renderFrag value f\n"
            "      result := piece ++ result\n"
            "      i := i - 1"),
        "rationale": "naming the exposed per-fragment rendering in a local `let "
                     "piece` before prepending folds the same per-fragment rendering "
                     "over the same stream in the same order, so `out = rendered value "
                     "template` still holds on the whole domain; the loop, its "
                     "invariants and the frozen proof script are untouched. A correct "
                     "reshape must verify, else SPEC-TOO-STRONG over the loop-body "
                     "shape. Complements pos-direct-model: one positive keeps the "
                     "iteration and one removes it, so neither the presence nor the "
                     "absence of the loop is what the spec is testing.",
    },
    {
        "id": "pos-forward-scan",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The frozen impl scans the template BACKWARD, prepending
        # each rendering; this positive scans FORWARD, appending. Same output at
        # every input, but the loop invariant is over `template.take j` rather
        # than `template.drop i`, so the frozen fold lemma does not apply and the
        # reproof must supply the mirror step itself. This is the reshape that
        # actually tests whether the spec is over-fit to the scan DIRECTION —
        # pos-piece-local keeps the direction and pos-direct-model removes the
        # loop, so neither probes it.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let mut result : List Char := []\n"
            "    let mut j := 0\n"
            "    while j < template.length\n"
            "      invariant j ≤ template.length\n"
            "      invariant result = rendered value (template.take j)\n"
            "      done_with j = template.length\n"
            "      decreasing template.length - j\n"
            "    do\n"
            "      result := result ++ renderFrag value template[j]!\n"
            "      j := j + 1\n"
            "    return result\n"
            "    -- impl-end",
            proof=(
                "prove_correct renderInvalidChoice by\n"
                "  have fwd_step : ∀ (v : List Char) (t : List Frag) (k : Nat), "
                "k < t.length →\n"
                "      rendered v (t.take (k + 1)) = rendered v (t.take k) ++ "
                "renderFrag v t[k]! := by\n"
                "    intro v t\n"
                "    induction t with\n"
                "    | nil => intro k hk; simp at hk\n"
                "    | cons a rest ih =>\n"
                "      intro k hk\n"
                "      cases k with\n"
                "      | zero => simp [rendered, renderFrag]\n"
                "      | succ n =>\n"
                "        have hn : n < rest.length := by simpa using hk\n"
                "        simp [List.take_succ_cons, rendered_cons, ih n hn, "
                "List.append_assoc]\n"
                "  loom_solve")),
        "rationale": "a FORWARD scan appending each per-fragment rendering computes "
                     "the same left-to-right concatenation as the frozen backward "
                     "scan, so `out = rendered value template` holds on the whole "
                     "domain — but the invariant is over `template.take j`, the "
                     "mirror of the frozen `template.drop i`, so the frozen fold "
                     "lemma is useless and the reproof supplies its own forward step. "
                     "If the spec could only be discharged in the frozen scan "
                     "direction it would be SPEC-TOO-STRONG over the iteration order, "
                     "which is precisely the freedom a real reimplementation takes. "
                     "Measured: verifies (exit 0) once `fwd_step` is in context.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at a concrete input of
    # the tested shape, not merely satisfiable in the abstract. The analogue of
    # the sibling's precondition probe on a total carrier: discharge the
    # load-bearing clause's right-hand side at that input BY EVALUATION as a
    # `have`, then close the frozen obligation verbatim.
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        # ADDED BY AUDIT (the port recorded this lane "DEGENERATE" because the
        # method declares no `require`; that is the wrong test on a total
        # carrier). The frozen impl and the frozen proof script are kept
        # byte-for-byte; the tactic body only PREPENDS a `have` that evaluates
        # the rendering of a quoted value slot followed by literal words at a
        # concrete tested-shape input, and checks it equals the string with the
        # value substituted at the slot. If the obligation were unsatisfiable at
        # exactly this shape — the placeholder not fillable, the literals not
        # passing through, the concatenation not composing — the `have` would not
        # close and the case would fail while the frozen file still verified.
        "module": _rewrite_proof(_PROOF_ADMISS),
        "rationale": "PRECOND-TOO-STRONG has no `require` to attack here, so the "
                     "lane's real content on a total carrier is that the obligation "
                     "is satisfiable AT AN F2P-SHAPED INPUT rather than only "
                     "abstractly. The `have` evaluates `rendered` in the kernel at a "
                     "quoted-slot-plus-literal-words template and pins the result to "
                     "the string carrying the value substituted at the slot; `decide` "
                     "reduces the fold, so this is an evaluation and not a "
                     "restatement of the clause. Load-bearing, measured: changing the "
                     "expected string to the one that leaves the placeholder standing "
                     "makes the same `decide` FAIL (`Tactic `decide` proved that the "
                     "proposition ... is false`), so the case distinguishes the two "
                     "renderings rather than passing on any string. The frozen impl "
                     "and frozen proof script are untouched, so a failure here could "
                     "only be the obligation's own satisfiability at that input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a refutation witness at a CONCRETE input
    # and the refinement argument that its faithful real patch would NOT resolve
    # the single FAIL_TO_PASS test. Every witness was built by hand against its
    # rival (must elaborate) and against `witness_reference` (must fail by a real
    # `decide` verdict, no stuck-reduction marker); see the CARRIER NOTE for why
    # the reference and not the frozen loop is the second subject.
    # =====================================================================
    {
        "id": "weak-placeholder-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating miss, and the pre-image behaviour: the value slot is
        # NOT filled with the value; a constant literal token is emitted in its
        # place. Correct on placeholder-free templates, wrong on every template
        # carrying a slot.
        "module": _rewrite_impl(_foldr_impl('"%(value)s".toList')),
        "witness": _witness("[Frag.valueSlot]", '"A".toList'),
        "witness_reference": _LOOPFREE,
        "refinement": "this is exactly the pre-image behaviour: the offending value is "
                      "never supplied to the renderer, so the value placeholder slot is "
                      "left standing as its literal token instead of being filled. The "
                      "single new FAIL_TO_PASS test configures a message whose template "
                      "carries a value placeholder and asserts the rendered message "
                      "EXPOSES the offending value; this rival renders the literal "
                      "placeholder token surviving instead, so the asserted message is "
                      "not produced — it would NOT resolve (the model_prepatch / G-DIFF "
                      "failure mode; the frozen prepatch skeleton is this same "
                      "behaviour).",
        "rationale": "REJECT from `out = rendered value template` via the `valueSlot` "
                     "arm: the frozen model FILLS the slot with `value`, this rival "
                     "emits a constant token there, so the two disagree on every "
                     "template containing a slot. Verifying would be SPEC-TOO-WEAK — "
                     "the substitution itself would be unpinned, which is the one "
                     "thing this spec exists to pin. Refuted at the minimal "
                     "slot-carrying template with a length-1 value.",
    },
    {
        "id": "weak-value-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        # Fills the slot with `value.drop 1` — the value's first code point is
        # lost. Correct ONLY on the empty value (`drop 1 [] = []`). A NEAR-MISS
        # relative to the verbatim rival: it does consult `value`, and at a
        # length-1 value it collapses to emitting nothing, so it gets its own
        # witness at a LENGTH-2 value where "some of the value" is visibly
        # distinct from both "none of it" and "all of it".
        "module": _rewrite_impl(_foldr_impl("value.drop 1")),
        "witness": _witness("[Frag.valueSlot]", '"AB".toList'),
        "witness_reference": _LOOPFREE,
        "refinement": "a faithful real patch that supplied the offending value minus "
                      "its first character as the substitution parameter would render "
                      "the value truncated. The FAIL_TO_PASS assertion pins the "
                      "rendered message exactly, so a message showing the value "
                      "missing its leading character reads back a different string — it "
                      "would NOT resolve. Correct only on the empty-value sub-domain, "
                      "which the tested domain does not contain.",
        "rationale": "REJECT from `out = rendered value template` via the `valueSlot` "
                     "arm, at the `value` binder: the substitution must reproduce the "
                     "WHOLE value, and this rival drops `value[0]`, so the two "
                     "disagree at every nonempty value. Verifying would be "
                     "SPEC-TOO-WEAK (value exactness unpinned — the spec would admit "
                     "an impl that shows only PART of the offending value). Witnessed "
                     "at a length-2 value, moving the `value` binder off the length-1 "
                     "point where this rival and the verbatim rival would be "
                     "indistinguishable.",
    },
    {
        "id": "weak-literal-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no sibling): attacks the OTHER arm of the per-fragment rendering
        # — the literal passthrough. Emits [] for every literal while filling the
        # slot correctly. Correct on literal-free templates, wrong on any template
        # carrying one.
        "module": _rewrite_impl(_foldr_impl("value", lit_arm="[]")),
        "witness": _witness("[Frag.lit 'x', Frag.valueSlot]", '"A".toList'),
        "witness_reference": _LOOPFREE,
        "refinement": "a real patch that dropped the literal text of the message "
                      "template while filling the placeholder would render a message "
                      "stripped of all its surrounding words. The FAIL_TO_PASS test "
                      "configures a message with literal text around the placeholder "
                      "and asserts the exact rendered string; a rival emitting only the "
                      "substituted value drops that literal text — it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = rendered value template` via the `lit c` arm: "
                     "the frozen model passes each literal through as `[c]`, this rival "
                     "emits `[]`, so the two disagree on every template containing a "
                     "literal. Verifying would be SPEC-TOO-WEAK: the spec would pin the "
                     "slot substitution while leaving the surrounding message text "
                     "unconstrained. Witnessed at a literal+slot template — the "
                     "shape that moves the `template` binder off the slot-only point "
                     "both value-arm rivals sit at.",
    },
    {
        "id": "weak-fragment-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no sibling): attacks the COMBINATION rather than either arm.
        # Both per-fragment arms are exactly right; the stream is traversed in
        # reverse, so the renderings concatenate in the wrong order. Agrees with
        # the frozen model on every template of length <= 1 and on any template
        # whose rendering happens to be order-insensitive — so it gets a witness
        # at a length-2 template with an asymmetric rendering.
        "module": _rewrite_impl(_foldr_impl("value", stream="template.reverse")),
        "witness": _witness("[Frag.lit 'x', Frag.valueSlot]", '"AB".toList'),
        "witness_reference": _LOOPFREE,
        "refinement": "a real patch that assembled the message from its fragments in "
                      "reverse order would place the substituted value BEFORE the "
                      "literal text that should precede it. The FAIL_TO_PASS assertion "
                      "compares the rendered message for exact equality, and a "
                      "reordered message is not the asserted one — it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = rendered value template` at the COMBINATION, "
                     "not at either arm: both the slot fill and the literal "
                     "passthrough are exactly the frozen model's, so no per-fragment "
                     "rival can cover this. Verifying would be SPEC-TOO-WEAK in a way "
                     "the other rivals cannot detect — the spec would pin WHAT each "
                     "fragment renders to while leaving the ORDER of concatenation "
                     "free. Witnessed at a length-2 template with a non-symmetric "
                     "rendering (a literal then a slot, over a length-2 value), the "
                     "smallest input where reversal is observable at all.",
    },
    {
        "id": "weak-fold-base-value",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no sibling): attacks the fold's NIL case. Both arms and the order
        # are exactly right, but the accumulator is seeded with `value` instead of
        # nothing, so every rendering carries a spurious copy of the value at its
        # tail. Wrong at every nonempty value INCLUDING the tested shape; the
        # witness is stated at the EMPTY template, the point that isolates the nil
        # case from the per-fragment behaviour and the only witness here reaching
        # a zero-length template.
        "module": _rewrite_impl(_foldr_impl("value", seed="value")),
        "witness": _witness("([] : List Frag)", '"A".toList'),
        "witness_reference": _LOOPFREE,
        "refinement": "a real patch that appended the offending value to the end of "
                      "the assembled message in addition to substituting it at the "
                      "placeholder would render the value DUPLICATED at the tail. The "
                      "FAIL_TO_PASS assertion compares the rendered message for exact "
                      "equality, so the trailing copy makes it a different string — it "
                      "would NOT resolve. Note this rival is wrong on the tested "
                      "template shape too, not only on the empty one; the empty "
                      "template is merely where the defect is cheapest to isolate.",
        "rationale": "REJECT from `out = rendered value template` at the fold's NIL "
                     "case: the frozen model renders the empty template to nothing, so "
                     "seeding the accumulator with `value` contaminates every "
                     "rendering. Verifying would be SPEC-TOO-WEAK: the spec would pin "
                     "the per-fragment contributions and their order while leaving the "
                     "message's baseline free, admitting an impl that emits extra text "
                     "no fragment asked for. Witnessed at the EMPTY template — the "
                     "only witness in this battery at a zero-length template, so the "
                     "`template` binder is exercised at lengths 0, 1 and 2 rather "
                     "than only at the shapes the F2P happens to use.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 2 MANDATORY frame-mutation rejects, 2
# partial-domain rejects) plus an EMPTY axiom lane. The sibling models the same
# message rendering over a `List[int]` of code points held at a FRACTIONAL heap
# permission, with the substitution computed by a verified helper carrying its own
# precondition. This backend models the substitution deeply and concretely (the
# `pure` region), so the per-fragment rendering and the value fill are transparent
# `def`s of `template`/`value`; there is no axiom, no helper precondition, and no
# permission surface.
#
#   sibling case                 -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-local-bind               -> pos-direct-model              RE-EXPRESSED
#   pos-render-tail-reshape      -> pos-piece-local               PORTED (reshaped)
#   admiss-helper-fresh-input    -> admiss-f2p-shape              PORTED (audit)
#   (no sibling)                 -> pos-forward-scan              ADDED (scan dir)
#   frame-mut-template           -> (none)                        VACUOUS (no heap/mut)
#   frame-mut-value              -> (none)                        VACUOUS (no heap/mut)
#   partial-domain-verbatim      -> weak-placeholder-verbatim     PORTED
#   partial-domain-value-trunc   -> weak-value-truncated          PORTED
#   (no sibling)                 -> weak-literal-dropped          ADDED (lit arm)
#   (no sibling)                 -> weak-fragment-order           ADDED (combination)
#   (no sibling)                 -> weak-fold-base-value          ADDED (nil case)
#   (sibling has no diverge case)-> (none)                        SPEC-CLOSED
#   AXIOM_TESTS (empty)          -> (none)                        N/A (G-AX's lane)
#
# RE-EXPRESSED (pos-local-bind): the sibling binds the helper result to a typed
#   local before returning. On this carrier the cheapest faithful reshape is a
#   loop-free direct return of the grounded model, maximally different from the
#   frozen backward scan; it closes under `loom_solve` alone.
# PORTED-RESHAPED (pos-render-tail-reshape): the sibling computes the recursive
#   tail into a local then prepends the head. That exact reshape does not exist
#   here (the frozen iteration is a backward `while`, not front recursion), so the
#   reshape SPIRIT — structurally different, behaviourally identical, loop and
#   proof intact — is carried by pos-piece-local.
# VACUOUS (frame-mut-template, frame-mut-value): the sibling holds BOTH inputs at
#   a fractional permission and makes a write to either a MANDATORY reject for
#   insufficient permission. This backend is referentially transparent:
#   `template`/`value` are immutable values, the method declares no `mut` binder
#   among its inputs, there is no heap and no aliasing. Nothing to overwrite and
#   no permission system to trip. No substitute fabricated.
# PORTED-BY-AUDIT (admiss-helper-fresh-input -> admiss-f2p-shape): the sibling
#   shows the helper's precondition admits a fresh F2P-shaped input.
#   `renderInvalidChoice` declares no `require`, and the port read that as making
#   the lane degenerate. It does not: on a total carrier the analogue is the
#   obligation being UNSATISFIABLE at exactly an input of the tested shape, which
#   a positive that discharges the obligation at that concrete input — by
#   evaluation, as a `have`, before closing the frozen obligation verbatim —
#   tests directly. Landed as `admiss-f2p-shape`, so this battery exercises all
#   three directions the gate exists to test rather than two.
# PORTED (partial-domain-verbatim, partial-domain-value-trunc): both sibling
#   partial-domain rejects port directly, re-expressed loop-free so their
#   extracted programs reduce at the witnessed literal.
# ADDED x3: the sibling's two rejects both attack the value fill. Three
#   sub-behaviours of the load-bearing clause were left undefended by a direct
#   port, and each is refutable here, so each got a rival at a fresh input point:
#   the literal passthrough (weak-literal-dropped), the ORDER in which the
#   per-fragment renderings combine (weak-fragment-order — both arms correct, so
#   no per-fragment rival can cover it), and the fold's nil case
#   (weak-fold-base-value). Without them, a rival mishandling only one of those
#   would verify and the battery would never notice.
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
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# CLAUSE / BINDER COVERAGE. Only the first `ensures` constrains the impl; the
#   other two are pure facts about the model (they do not mention `out`), true for
#   every impl, so no rival can attack them and none is authored to — stated here
#   rather than covered by a case that could not fail. The load-bearing clause is
#   attacked by all five rivals, and the obligation is defended by three positives
#   (loop removed, loop body reshaped, scan DIRECTION reversed) plus the
#   admissibility probe at a concrete tested-shape input.
#   The five reject witnesses probe five DISTINCT input tuples:
#     - ([],                       "A")   weak-fold-base-value    nil case
#     - ([valueSlot],              "A")   weak-placeholder-verbatim  slot arm
#     - ([valueSlot],              "AB")  weak-value-truncated    slot arm, value len 2
#     - ([lit 'x', valueSlot],     "A")   weak-literal-dropped    lit arm
#     - ([lit 'x', valueSlot],     "AB")  weak-fragment-order     combination
#   `template` takes lengths {0, 1, 2} and shapes {empty, slot-only, literal+slot};
#   `value` takes lengths {1, 2}. Both arms of the per-fragment rendering, the
#   concatenation ORDER, and the fold's baseline are each attacked by some rival,
#   and no binder is held at a single value across the reject lane. pts = 5.
#
# AXIOM_TESTS: empty. The sibling's axiom lane is already empty (the one
#   deep-model reference is validated by axiom_check.py / G-AX, not consumed as an
#   axiom). This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
