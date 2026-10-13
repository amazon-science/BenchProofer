"""properties.py — G-PBT falsification battery for sympy__sympy-19637 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct markerPresent`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

================================  DEFENDED SURFACE  ==========================

ONE contracted method over a single read-only input:

  markerPresent (s : List Char) return (out : Except MarkerError Bool)
      ensures out = Except.ok (markerFlag s)

The method models a flag step that inspects a working string and reports whether
a substitution marker is present in it. The pure region pins the whole outcome as
a total function of the method's own single input:

  markerFlag s = s.contains ' '

with the marker modeled as the distinguished code point (mapping.md §2, §3). The
sole ``ensures`` therefore pins TWO independent things about the result:

  * (LEG) which leg of the return carrier fires — the step is TOTAL, so the
    success leg ``Except.ok`` always fires and the failure leg
    ``Except.error MarkerError.markerUnavailable`` is NEVER produced, not even on
    the path where no marker was ever introduced (the exact path the issue's
    input reaches). A rival that surfaces the failure leg on that path fails here.
  * (VALUE) the carried flag — ``markerFlag s`` exactly: ``true`` iff the marker
    is present, ``false`` otherwise. A rival that flips the flag, pins it to a
    constant, or reports the wrong membership violates the ensures on the value.

The single INPUT binder is free (the ``pre-conditions`` region is EMPTY) and the
post-image must hold for EVERY value of it:
  * ``s`` — the working string; drives both the LEG (present vs absent marker)
    and the VALUE (which membership the flag reports).

ADVERSARIAL READ of the nagini classes (see the footer for the case-by-case
accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling records the
    class VACUOUS already: its two inputs are value types passed by value, with
    no fractional heap permission to overwrite. Here the single input ``s`` is an
    immutable ``List Char`` value; this bundle declares no ``mut`` binder, there
    is no heap and no aliasing. There is no read-only input to overwrite and no
    permission system to trip. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION — the obligation DOES reject a diverging rival
    here, but the rival is UNSHIPPABLE as a G-PBT case because its WITNESS side
    cannot be built. [AUDIT CORRECTION: the earlier text claimed this class was
    "genuinely VACUOUS" because "a diverging implementation cannot be written at
    all". That claim is FALSE and was measured false — a diverging impl is
    perfectly writable on this carrier; what fails is the witness, which is a
    different and weaker disposition.] Measured, both forms:
      - a bare diverging prefix (``while True do pure ()``) spliced ahead of the
        frozen body, proof reduced to a bare ``loom_solve`` (a scratch-copy splice;
        the bundle itself was not modified) - variant exit 1,
        ``error: Decreasing annotations are required in total correctness
        semantics``;
      - an ANNOTATED non-terminating loop that elaborates as far as the measure
        obligation (``let mut k := 1; while k > 0 invariant k > 0 done_with k = 0
        decreasing k do k := k``) — variant exit 1, residual goal ``⊢ k < k``.
    So ``loom.semantics.termination "total"`` genuinely discharges a termination
    obligation, and the measure-carrying shape above is the decisive one: it fails on
    the measure's OWN goal, so the refusal cannot be dismissed as merely the
    missing-annotation linter. (An earlier version of this passage set the result
    against a ``partial``-semantics hole recorded in an internal findings doc. There is
    no such cohort: all 500 velvet bundles set ``"total"`` and open
    ``TotalCorrectness``, and the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness`` (``Loom/MonadAlgebras/WP/Options.lean:169-186``),
    so the option and the ``open`` cannot disagree.) What blocks SHIPPING the case is
    the witness requirement, not
    the spec: the rival-side witness build — the half that MUST succeed — fails
    by STUCK REDUCTION, never by refutation. Measured on the annotated rival, at
    ``markerPresentTester ['a']``, four tactic routes all exit 1:
    ``simp [... , Lean.Loop.forIn, forIn]`` and ``unfold``+``simp`` leave the
    goal on an unreduced ``forIn Lean.Loop.mk``; ``rfl`` fails; and
    ``decide +kernel`` reports the instance ``did not reduce to `isTrue` or
    `isFalse` `` — the exact ``_STUCK_REDUCTION`` screen the gate refuses as
    ``witness-undecided``. The cause is structural, not a tactic gap: under
    ``loom.semantics.choice "demonic"`` a ``while`` elaborates through
    ``Classical.choice``, which the kernel cannot unfold, so no claim about a
    looping impl's tester reduces. ``witness_reference`` does not rescue it —
    that substitutes the GOLD-side subject, and the stuck side here is the
    rival's. Corpus-wide this is the norm rather than this cell's failing: zero
    of the 496 ``total`` velvet bundles ship a loop-divergence reject case.
    DISPOSITION: not vacuous, not a spec hole — a WITNESS-INEXPRESSIBLE class.
    The termination obligation is real and rejects the rival; the gate simply
    cannot be handed machine-checked evidence of it on this carrier. The nagini
    sibling carries no explicit ``diverge-*`` case either (its ``MustTerminate``
    obligation is discharged inline, with no loop to spin).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``Except.ok (markerFlag s)``, and ``markerFlag`` is a concrete ``def`` in
    the ``pure`` region computing the membership from the method's own argument
    (the ``axioms`` region declares only the failure-leg inductive, no opaque
    answer key). The unique satisfier IS the grounded membership, so there is no
    wrong echo to build; the honest cheapest-reshape positives stand in (one of
    them delegates to the grounded oracle directly — a control, not a weakness).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    modeled failure path (the ``UnboundLocalError`` the pre-patch produced on the
    no-marker path) IS the ``Except.error`` leg of the return carrier, so the
    fork is fully observable to the ensures; the ``prepatch-surface-failure``
    rival is its discriminator.
  * PARTIAL-DOMAIN / VALUE — the heart of this port. Rivals right on part of the
    input domain but diverging on a sub-domain: ``all-true`` is right on the
    marker-present sub-domain and wrong on the absent one; ``negate-flag`` is
    right on neither branch's value; ``all-false`` is right on the absent
    sub-domain and wrong on the present one; ``wrong-marker-membership`` reports a
    membership of the WRONG code point, so it is right wherever the two code
    points agree and wrong where they part (the marker-IDENTITY axis, which the
    flip/pin/drop rivals all leave unprobed); ``narrow-one-point`` is right on
    EVERY working string but one, which is what makes the spec's universal
    quantification over ``s`` load-bearing. Each is refuted at a concrete input.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces once the model ``def``s are unfolded. Each reject
rival carries a machine-checked refutation ``witness`` — a Velvet tester
statement ``markerPresentTester <s> = false`` at ONE concrete working string,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. (``prove_postcondition_decidable_for`` cannot on its
own synthesize ``DecidableEq`` for the ``Except MarkerError Bool`` return
carrier, so each witness first ``deriving instance DecidableEq for Except`` — an
instance, not an assumption: no ``axiom`` / ``sorry`` / ``native_decide`` is
involved, and the frozen solution rejects the witnesses all the same.) A single
``simp`` unfolding the tester / exec / method / ``markerFlag`` ``def``s reduces
each tester to a ground boolean and closes the ``= false`` goal against the
rival; the same statement leaves the residual ``False`` goal open against the
frozen solution. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (exit 0)
and FAILS against the frozen solution (exit 1), so each rejection is a genuine
spec refutation and not mechanical tactic breakage.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and this gate ignores
``AXIOM_TESTS``. The ``axioms`` region declares only the failure-leg inductive
``MarkerError`` (never an opaque callee), and ``markerFlag`` is a concrete pure
``def``; ``meta.json`` declares no consumed axiom.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19637"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — the executable statements strictly BETWEEN
# the method's `-- impl-start` / `-- impl-end` markers. Every rival and reshape
# edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction. Unique in the file (asserted by _swap).
_IMPL = (
    "    let out : Except MarkerError Bool :=\n"
    "      if s.contains ' ' then Except.ok true\n"
    "      else Except.ok false\n"
    "    return out"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = (
    "prove_correct markerPresent by\n"
    "  loom_solve\n"
    "  simp only [markerFlag]\n"
    "  split <;> simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `markerPresentTester <s> = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` block is stripped. The `Except MarkerError Bool`
# ---- return carrier needs a decidable-equality instance for the tester
# ---- derivation; it is derived, not assumed.
_TESTER = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for markerPresent\n"
    "prove_precondition_decidable_for markerPresent\n"
    "prove_postcondition_decidable_for markerPresent\n"
    "derive_tester_for markerPresent\n\n"
)

# A single `simp` unfolds the tester / exec / method / `markerFlag` `def`s and
# reduces the tester to a ground boolean, closing the `= false` goal against the
# rival (and leaving `False` open against the frozen solution).
_WTAC = (
    "  simp [markerPresentTester, markerPresentExec, markerPresent, "
    "NonDetT.run, markerFlag]\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n{_WTAC}"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the produced value identical and
    # only reshapes the executable surface / retunes the elided proof.
    # =====================================================================
    {
        "id": "pos-grounded-oracle-delegate",
        "kind": "soundness",
        "expect": "verify",
        # Return the grounded pure selector directly. `markerFlag` is fully
        # unfolded over the input (not an opaque answer key), so delegating to it
        # IS the modeled behaviour; the maximally-collapsed correct shape. The
        # proof is retuned to a bare `loom_solve` (it discharges the definitional
        # equality without the split).
        "module": _impl_reproved(
            "    return Except.ok (markerFlag s)",
            "prove_correct markerPresent by\n  loom_solve"),
        "rationale": "returning `Except.ok (markerFlag s)` satisfies "
                     "`out = Except.ok (markerFlag s)` definitionally; a correct "
                     "reshape of the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Ports the sibling's grounded-"
                     "oracle-delegate positive control (`markerFlag` is unfolded "
                     "over the input, so this is the modeled behaviour, not a "
                     "wrong echo).",
    },
    {
        "id": "pos-match-head-tail",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. The other two positives both collapse to the SAME closed
        # form `Except.ok (<membership>)` and close by unfolding alone — they are
        # two spellings of one reshape, so no positive control exercised a shape
        # whose correctness needs PROPOSITIONAL reasoning rather than unfolding.
        # This one destructures the input and recomputes the membership
        # head-vs-tail, so the ensures holds only up to `List.contains_cons` plus
        # a case split on the head code point (and `Ne.symm` for the orientation
        # of the head comparison) — a genuinely different shape whose proof cannot
        # be a bare `loom_solve`. Confirmed to verify out of band (exit 0).
        "module": _impl_reproved(
            "    let out : Except MarkerError Bool :=\n"
            "      match s with\n"
            "      | [] => Except.ok false\n"
            "      | c :: rest => Except.ok (c = ' ' || rest.contains ' ')\n"
            "    return out",
            "prove_correct markerPresent by\n"
            "  loom_solve\n"
            "  simp only [markerFlag]\n"
            "  cases s with\n"
            "  | nil => rfl\n"
            "  | cons c rest =>\n"
            "    simp only [List.contains_cons]\n"
            "    by_cases h : c = ' '\n"
            "    · subst h; simp\n"
            "    · simp [h, Ne.symm h]"),
        "rationale": "recomputing the flag by destructuring the working string — "
                     "`false` on the empty string, else the head code point being "
                     "the marker OR the marker occurring in the tail — is the same "
                     "total function as the frozen membership on every input, so it "
                     "MUST verify. Unlike the other two positives it is not the "
                     "membership in closed form: the ensures holds only up to "
                     "`List.contains_cons` and a case split on the head, so this is "
                     "the control that would catch a spec too strong for any shape "
                     "needing propositional (not definitional) reasoning.",
    },
    {
        "id": "pos-bind-membership-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the membership result to a typed local and wrap it in the
        # success leg, dropping the two-armed `if`. Same value on every input; a
        # structurally different straight-line shape. The proof is retuned to
        # close the definitional equality after unfolding `markerFlag`.
        "module": _impl_reproved(
            "    let b := s.contains ' '\n"
            "    let out : Except MarkerError Bool := Except.ok b\n"
            "    return out",
            "prove_correct markerPresent by\n  loom_solve\n  simp [markerFlag]"),
        "rationale": "binding the membership to a local and wrapping it in the "
                     "success leg (no branch) produces `Except.ok (s.contains ' ')` "
                     "= `Except.ok (markerFlag s)` on every input, so the ensures "
                     "still holds; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on the branch-vs-flat shape. Re-expresses "
                     "the sibling's flat positive control (collapse the guard into "
                     "one closed form).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is EMPTY), so the sibling's "the F2P-shaped input satisfies the
    # precondition" probe is degenerate on its face (every input is in-domain).
    # The analogue on a TOTAL-domain carrier is the obligation being unsatisfiable
    # at exactly an F2P-shaped input — which a positive that discharges the
    # obligation AT THAT CONCRETE INPUT, by evaluation, as a `have`/assert, before
    # closing the frozen obligation verbatim, tests directly. That is what this
    # case does.
    #
    # [AUDIT CORRECTION.] The case previously asserted only over `[]` and `[' ']`
    # — two abstract one-code-point probes. `[]` is not F2P-shaped: it is the
    # empty working string, and the rationale's claim that it is "the exact input
    # the issue reaches" was FALSE. The input the issue reaches is a
    # PARENTHESISED QUOTIENT that carries no marker after the earlier transforms,
    # which is a length-11 string with structure, not the empty list. The assert
    # now pins the obligation's own decision at that concrete F2P-shaped working
    # string, so the case tests what the lane exists to test rather than a
    # stand-in for it. Measured: exit 0 as written; and the mutation that flips
    # the F2P-shaped conjunct to `= true` FAILS to elaborate (exit 1, `decide`
    # proved the conjunction false), so the assert is load-bearing and is not
    # discharged by anything weaker than the real evaluation.
    #
    # The impl is kept verbatim so the method's own obligation still discharges;
    # the proof is retuned to close the assert too.
    # =====================================================================
    {
        "id": "admiss-flag-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (markerFlag (['(', '2', '*', 'x', ')', '/', '(', 'x', '-', "
            "'1', ')'] : List Char) = false ∧\n"
            "       markerFlag ['a', ' ', 'b'] = true ∧\n"
            "       markerFlag ([] : List Char) = false))\n" + _IMPL,
            "prove_correct markerPresent by\n"
            "  loom_solve\n"
            "  all_goals (first | (simp only [markerFlag]; split <;> simp_all) "
            "| decide)"),
        "rationale": "the obligation is SATISFIABLE, by evaluation, at an "
                     "F2P-SHAPED working string: a parenthesised quotient "
                     "carrying no marker — the shape the issue's input has once "
                     "the earlier transforms have run — for which the flag must "
                     "be `false` and the step must still yield a flag rather "
                     "than fail. The assert discharges that concrete instance "
                     "in-region BEFORE the frozen obligation is closed verbatim, "
                     "which is the total-carrier analogue of the sibling's "
                     "PRECOND-TOO-STRONG probe: if the obligation were "
                     "unsatisfiable at exactly this input the assert would not "
                     "elaborate. It also pins non-degeneracy — a marker-present "
                     "string gives `true` and the empty string `false`, so the "
                     "flag genuinely depends on the marker and a spec that had "
                     "collapsed the decision would fail here. Re-aims the "
                     "sibling's admissibility case at the concrete F2P-shaped "
                     "point (no precondition surface exists on this carrier).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line, refuted at a concrete input
    # by a witness that FAILS on the frozen solution, and carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # The single input binder `s` is moved across all four (empty / non-empty,
    # absent-marker / present-marker), so no value of it is pinned.
    # =====================================================================
    {
        "id": "prepatch-surface-failure",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH SHAPE: on the no-marker path, surface the FAILURE leg instead
        # of the total success leg carrying `false`. This is the modeled image of
        # the real failure — the flag consulted a value that was never
        # established, so the step raises instead of yielding a flag.
        "module": _impl(
            "    let out : Except MarkerError Bool :=\n"
            "      if s.contains ' ' then Except.ok true\n"
            "      else Except.error MarkerError.markerUnavailable\n"
            "    return out"),
        "refinement": "this IS the pre-patch: on a working string where no marker "
                      "survived, the flag step surfaces a failure rather than "
                      "yielding `false`. The F2P input reaches exactly that path "
                      "(the parenthesised expression rewrites away every marker), "
                      "so the step raises instead of returning a flag; the F2P "
                      "test that evaluates that input then errors instead of "
                      "producing the expected expression — it does NOT resolve. "
                      "It is the exact bug the change fixes, the precise "
                      "discriminator G-DIFF senses.",
        "rationale": "REJECT from `out = Except.ok (markerFlag s)` on the LEG: on "
                     "a no-marker string the post-image demands the success leg "
                     "`Except.ok false`, but the rival produces `Except.error "
                     ".markerUnavailable`. Refuted at an F2P-SHAPED working "
                     "string — a parenthesised quotient carrying no marker, the "
                     "shape the issue's input has once the earlier transforms "
                     "have run — which is the sub-domain the change targets and "
                     "where the totality clause is load-bearing. [AUDIT: the "
                     "witness previously stood at the EMPTY string `[]`, which is "
                     "in the right sub-domain but is not the shape the issue "
                     "reaches; the refutation is now stated at the real shape, "
                     "measured to elaborate against the rival (exit 0) and to "
                     "leave `⊢ False` open against the frozen solution (exit 1). "
                     "`[]` is still covered — the admissibility case pins the "
                     "flag there.]",
        "witness": _witness(
            "markerPresentTester ['(', '2', '*', 'x', ')', '/', "
            "'(', 'x', '-', '1', ')']"),
    },
    {
        "id": "all-true",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: always report the marker present. Correct on the
        # marker-present sub-domain; wrong on every absent-marker input, where the
        # flag must be `false`.
        "module": _impl(
            "    return (Except.ok true : Except MarkerError Bool)"),
        "refinement": "a faithful patch that always reports the marker present "
                      "would drive the later recovery step even on a working "
                      "string that never carried a marker, mis-routing every "
                      "no-marker case (the F2P input among them) into "
                      "post-processing that has no marker to act on. The F2P test "
                      "then observes the wrong result — it would NOT resolve.",
        "rationale": "REJECT from `out = Except.ok (markerFlag s)` on the VALUE: on "
                     "an absent-marker string the post-image demands `false`, but "
                     "the rival reports `true`. Refuted at the NON-empty "
                     "no-marker string `['a']` — moving the `s` binder off the "
                     "empty point the prepatch rival uses while staying in the "
                     "absent-marker sub-domain.",
        "witness": _witness("markerPresentTester ['a']"),
    },
    {
        "id": "all-false",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: never report the marker present. Correct on the
        # absent-marker sub-domain; wrong on every marker-present input, where the
        # flag must be `true`. Probes that the spec pins the POSITIVE case, not
        # just the negative one.
        "module": _impl(
            "    return (Except.ok false : Except MarkerError Bool)"),
        "refinement": "a faithful patch that never reports the marker present "
                      "would SKIP the recovery step even on a working string that "
                      "did carry a marker, leaving the introduced marker unresolved "
                      "in the parsed expression. On a marker-present F2P/P2P input "
                      "the marker placeholder is never substituted back, so the "
                      "result is wrong — it would NOT resolve.",
        "rationale": "REJECT from `out = Except.ok (markerFlag s)` on the VALUE: on "
                     "a marker-present string the post-image demands `true`, but "
                     "the rival reports `false`. Refuted at the single-marker "
                     "string `[' ']` — the present-marker sub-domain, the point "
                     "that shows the ensures pins the POSITIVE verdict (a "
                     "constant-false rival is silent on the absent side).",
        "witness": _witness("markerPresentTester [' ']"),
    },
    {
        "id": "negate-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-SWAP: report the NEGATION of the marker membership. Wrong on both
        # branches' value; the total success leg is kept, so the rejection is
        # purely on the postcondition value.
        "module": _impl(
            "    let out : Except MarkerError Bool :=\n"
            "      if s.contains ' ' then Except.ok false\n"
            "      else Except.ok true\n"
            "    return out"),
        "refinement": "a faithful patch reporting the inverted membership would "
                      "report the marker ABSENT precisely when it was present (and "
                      "present when absent), inverting the recovery step on every "
                      "input and corrupting both the marker-present and the "
                      "no-marker cases. The F2P test observes the wrong result — it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = Except.ok (markerFlag s)` on the VALUE: "
                     "the flag is flipped, so on any marker-present string the "
                     "post-image demands `true` and the rival yields `false`. "
                     "Refuted at the mixed string `['a', ' ']` (marker present) — "
                     "a length-2 point distinct from every other rival's, moving "
                     "the `s` binder over content and length while keeping the "
                     "success leg (so the rejection is on value, not leg).",
        "witness": _witness("markerPresentTester ['a', ' ']"),
    },
    {
        "id": "wrong-marker-membership",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION — MARKER IDENTITY. Every shipped rival either flips, pins
        # or drops the flag, so all four were refutable by a rival that reports
        # *some* membership; none asked WHICH code point the flag is the membership
        # of. This rival keeps the shape, the leg and the "report a membership"
        # discipline exactly, and changes only the code point it tests. It is right
        # on every string that holds neither code point (both `false`) and on every
        # string holding both (both `true`), and wrong precisely where the two
        # disagree — a sub-domain no other rival touches.
        "module": _impl(
            "    return (Except.ok (s.contains 'a') : Except MarkerError Bool)"),
        "refinement": "a faithful patch that keys the flag off the wrong code point "
                      "would report the marker present on a working string that "
                      "merely happens to contain that other character, and absent on "
                      "one that really does carry a marker. The recovery step is then "
                      "driven on strings with no marker to act on and skipped on "
                      "strings that need it, so the parsed expression is wrong on "
                      "both sides — the F2P test observes the wrong result and it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = Except.ok (markerFlag s)` on the VALUE, at "
                     "the MARKER IDENTITY: `markerFlag` is the membership of the "
                     "distinguished code point specifically, so a membership test "
                     "against a different code point violates the ensures wherever "
                     "the two disagree. Refuted at `['a','b']` — a length-2 string "
                     "carrying NO marker, where the post-image demands `false` and "
                     "the rival reports `true`. Also a NEW input point for the "
                     "binder (length 2, absent marker; the other length-2 point in "
                     "the battery is marker-present).",
        "witness": _witness("markerPresentTester ['a', 'b']"),
    },
    {
        "id": "narrow-one-point",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION — SURGICALLY-MINIMAL DIVERGENCE. This is the true carrier
        # counterpart of the sibling's narrow-partial-domain rival (the footer
        # records that case as having no counterpart; it has one, just not the
        # sub-domain the sibling used). Every other rival here diverges from the
        # frozen flag on at least half the input domain, so the battery never showed
        # the spec is tight against a rival that agrees with gold EVERYWHERE except
        # a single working string. A spec pinned only "up to a finite number of
        # exceptions" would pass all four shipped rivals and fail this one.
        "module": _impl(
            "    let out : Except MarkerError Bool :=\n"
            "      if s = ['b'] then Except.ok true\n"
            "      else Except.ok (s.contains ' ')\n"
            "    return out"),
        "refinement": "a faithful patch carrying a special case for one particular "
                      "working string would report a marker present in a string that "
                      "holds none, driving the recovery step against text with no "
                      "marker to substitute back on exactly that input. The flag is "
                      "then wrong on that string while looking right everywhere "
                      "else, so any test evaluating it observes the wrong result — it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = Except.ok (markerFlag s)` on the VALUE, on a "
                     "ONE-POINT sub-domain: the ensures is universally quantified "
                     "over `s`, so agreeing with the frozen flag on every other "
                     "string buys nothing. Refuted at the single-character no-marker "
                     "string `['b']`, where the post-image demands `false` and the "
                     "rival reports `true`. Shows the spec is tight even against a "
                     "minimal divergence, and moves the binder to a NEW point "
                     "(length 1, absent marker).",
        "witness": _witness("markerPresentTester ['b']"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) and no AXIOM_TESTS. It models
# `compute_processing_signal(entered: bool, key: Optional[bool])` over TWO inputs
# — an outer guard `entered` and an optional substitution key `key` (None <->
# no key was created) — with a precondition `Implies(not entered, key is None)`
# and two postcondition clauses (C1 total value, C2 absent-key -> false).
#
# This bundle models the SAME flag step, narrowed to the purely-functional core
# the Lean-family carrier can express: a single method `markerPresent (s)` whose
# flag `markerFlag s = s.contains ' '` is TOTAL over one input. mapping.md §3
# shows why the two nagini inputs collapse to one here: after the gold rewrite,
# the created key occurs in the working string IFF the string held a marker, so
# the whole (entered, key) surface reduces to "is the marker present in s". The
# `entered`/`key`-present distinction, the precondition, and the C2 clause are
# not separately modeled — they fold into the single membership and the totality
# (success-leg) obligation.
#
#   sibling case                       kind          -> here                        disposition
#   -----------------------------------------------------------------------------------------------
#   pos-control-flat-and               soundness     -> pos-bind-membership-local   RE-EXPRESSED
#   pos-control-grounded-oracle-...    soundness     -> pos-grounded-oracle-delegate PORTED
#   admissibility-f2p-shaped           admissibility -> admiss-flag-nondegenerate    RE-AIMED
#   prepatch-unconditional-read        uniqueness    -> prepatch-surface-failure     RE-EXPRESSED
#   partial-domain-hit-eq-entered      uniqueness    -> all-true                     RE-EXPRESSED
#   value-swap-negate-key              uniqueness    -> negate-flag                   PORTED
#   always-false                       uniqueness    -> all-false                     PORTED
#   narrow-partial-domain-keyfalse     uniqueness    -> narrow-one-point            RE-AIMED (audit)
#   (frame-mutation)                   -             -> (none)                        VACUOUS (both note it)
#   (no sibling counterpart)           soundness     -> pos-match-head-tail         ADDED (audit)
#   (no sibling counterpart)           uniqueness    -> wrong-marker-membership     ADDED (audit)
#
# RE-EXPRESSED (prepatch-unconditional-read -> prepatch-surface-failure): the
#   sibling's F2P rival reads the key's membership UNCONDITIONALLY on the
#   entered-but-no-key path, which is rejected because it cannot discharge the
#   @Pure accessor's `key is not None` precondition — the formal face of the
#   UnboundLocalError. This carrier has no key precondition; the SAME failure is
#   re-expressed as its observable image: on the no-marker path the step surfaces
#   the FAILURE leg (`Except.error .markerUnavailable`) instead of the total
#   success leg. Refuted at the empty (no-marker) string. Same ARGUMENT (the F2P
#   input reaches the no-marker path and the step must still yield a flag).
# RE-EXPRESSED (partial-domain-hit-eq-entered -> all-true): the sibling returns
#   the outer guard `hit = entered`, reporting processing-applied whenever the
#   transform was entered even with no key created — wrong on (True, None). Here
#   there is no `entered` binder; the eager-report partial-domain rival is
#   `all-true` (always report the marker present), wrong on every absent-marker
#   input. Same ARGUMENT (report the signal too eagerly on the no-substitution
#   sub-domain).
# PORTED (value-swap-negate-key -> negate-flag): the inverted-membership rival
#   ports one-for-one — report the NEGATION of the marker membership, refuted on
#   a marker-present string.
# PORTED (always-false -> all-false): the constant-false rival ports one-for-one;
#   correct on the absent-marker sub-domain, wrong on the present one — proving
#   the ensures pins the POSITIVE verdict.
# RE-AIMED (narrow-partial-domain-keyfalse -> narrow-one-point) [AUDIT
#   CORRECTION]. The port originally recorded this case OMITTED, reasoning that
#   the sibling's diverging sub-domain (True, False) — "a key was created but does
#   NOT occur in the rewritten text" — collapses on this carrier, since after the
#   rewrite the marker occurs IFF the string held one. That collapse argument is
#   CORRECT as far as the sibling's particular input class goes, and mapping.md §3
#   does demonstrate it. But it was applied to the wrong thing: what the sibling's
#   case TESTS is not that input class, it is that the spec is tight against a
#   SURGICALLY-MINIMAL divergence — a rival correct on every input class but one.
#   That property is fully expressible here (the ensures is universally quantified
#   over `s`, so a one-point exception violates it), and it was genuinely
#   untested: every other rival in this battery diverges on at least half the
#   domain, so a spec pinned only up to finitely many exceptions would have passed
#   the whole original battery. `narrow-one-point` re-aims the sibling's case at
#   the sub-domain that DOES exist here — a single concrete working string —
#   preserving the ARGUMENT rather than the input class. Its value-side content is
#   not, as the original footer claimed, already covered by negate-flag and
#   all-false: those two are wrong on an entire sub-domain, not on one point.
# ADDED (pos-match-head-tail) [AUDIT]. No sibling counterpart. Both original
#   positives reduce to `Except.ok (<membership>)` in closed form and close by
#   unfolding, so they are two spellings of one reshape and no positive control
#   covered a correct shape needing propositional reasoning. This one
#   destructures the input, so its proof needs `List.contains_cons` plus a case
#   split on the head code point.
# ADDED (wrong-marker-membership) [AUDIT]. No sibling counterpart (the sibling's
#   key is a bool, so "which code point is the marker" has no analogue there —
#   this is a gap the carrier OPENS rather than closes). All four original rivals
#   flip, pin or drop the flag, so each is refuted by any impl that reports some
#   membership; none pinned WHICH code point the membership is taken of.
# VACUOUS (frame-mutation): the sibling records this class VACUOUS already — both
#   its inputs are value types with no fractional heap permission to overwrite.
#   Here the single input `s` is an immutable `List Char`, this bundle declares
#   no `mut` binder, and there is no heap/aliasing/permission system. No
#   substitute is fabricated.
# WITNESS-INEXPRESSIBLE (divergence) [AUDIT CORRECTION — was recorded VACUOUS].
#   The earlier entry claimed a diverging rival "cannot be written at all" under
#   `total` semantics. That is false, and was measured false: a diverging impl IS
#   writable here and the obligation DOES reject it — the bare
#   `while True do pure ()` prefix exits 1 with `Decreasing annotations are
#   required in total correctness semantics`, and an annotated non-terminating
#   loop (`while k > 0 ... decreasing k do k := k`) exits 1 on the residual goal
#   `⊢ k < k`. So the class is neither vacuous nor a spec hole: the termination
#   obligation is live, and it is the measure's own goal that fails, not just the
#   annotation linter. (The earlier reference here to a `partial`-semantics finding in
#   an internal findings doc is withdrawn: all 500 velvet bundles read "total" and open
#   TotalCorrectness.)
#   What is genuinely inexpressible is the WITNESS, and it is the rival-side
#   build — the half that must SUCCEED — that fails. Under
#   `loom.semantics.choice "demonic"` a `while` elaborates through
#   `Classical.choice`, which the kernel cannot unfold, so the tester of a
#   looping impl does not reduce for ANY claim. Four routes measured at
#   `markerPresentTester ['a']`, all exit 1: `simp` with `Lean.Loop.forIn`/`forIn`
#   and `unfold`+`simp` both strand the goal on an unreduced `forIn Lean.Loop.mk`;
#   `rfl` fails; `decide +kernel` reports the `Decidable` instance `did not reduce
#   to `isTrue` or `isFalse``, which is verbatim the gate's `_STUCK_REDUCTION`
#   screen. `witness_reference` cannot repair it: that swaps the GOLD-side
#   subject, and the stuck side here is the rival's. Hence no shippable case —
#   a G-PBT reject case with an unbuildable rival witness records
#   `witness-unproven` and FAILS the gate, so shipping one would be worse than
#   documenting the wall. Corpus context: 0 of the 496 `total` velvet bundles
#   ship a loop-divergence reject case. The sibling carries no explicit
#   diverge-* case either.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the sole input binder of
#   the single ensures (pts = 6 distinct input points):
#     s -> `['(','2','*','x',')','/','(','x','-','1',')']`
#                       (prepatch-surface-failure): length 11, absent marker,
#                       F2P-SHAPED (a parenthesised quotient) [AUDIT: re-aimed
#                       from `[]`, which is in the right sub-domain but is not
#                       the shape the issue reaches; `[]` is still pinned by the
#                       admissibility case]
#          `['a']`      (all-true):                 length 1, absent marker
#          `[' ']`      (all-false):                length 1, present marker
#          `['a', ' ']` (negate-flag):              length 2, present marker
#          `['a', 'b']` (wrong-marker-membership):  length 2, absent marker
#          `['b']`      (narrow-one-point):         length 1, absent marker
#   The single binder `s` is moved across empty/non-empty, absent/present marker,
#   and length 0/1/2/11 — no value is pinned, the length-2 axis carries BOTH an
#   absent-marker and a present-marker point, and the reject lane now reaches a
#   structured multi-character point rather than only tiny ones.
#   Note the variation is meaningful, not two spellings of one point: `['a']`,
#   `['b']` and `['a','b']` are all absent-marker strings, but they are refuting
#   three DIFFERENT rivals and each is the point where its own rival diverges
#   from the frozen flag — `['b']` in particular is the sole point at which
#   narrow-one-point disagrees with gold at all.
#   Every independent aspect of the sole ensures is attacked:
#     * LEG (success vs failure) — prepatch-surface-failure;
#     * VALUE on the absent-marker side (post-image `false`) — all-true;
#     * VALUE on the present-marker side (post-image `true`) — all-false,
#       negate-flag;
#     * VALUE at the MARKER IDENTITY (which code point the membership is of) —
#       wrong-marker-membership;
#     * VALUE on a ONE-POINT sub-domain (tightness against a minimal divergence)
#       — narrow-one-point.
#   The obligation is defended by the three positive controls (two closed-form,
#   one needing propositional reasoning) and the admissibility case.
#
# INDEPENDENT AUDIT — SPEC-STRENGTH PROBES BEYOND THE SHIPPED CASES. Every probe
#   below was BUILT with the real verifier; none is shipped as a case (the
#   battery's own rivals already cover their axes) but each is evidence about the
#   FROZEN spec rather than about the battery.
#
#   ATTACK D (SPEC-TOO-WEAK) — 13 NEW wrong impls, each given a deliberately
#   generous proof ladder (`rfl` / the frozen split / `simp`+`decide` /
#   `simp_all`+`grind` / `decide`) so a spec hole would show up as a VERIFY.
#   ALL 13 were REJECTED (exit 1), so no hole was found. Aimed at the axes the
#   shipped rivals leave alone:
#     - error leg on the MARKER-PRESENT side, and on EVERY path (the shipped
#       prepatch rival only attacks the leg on the absent side);
#     - error leg on a ONE-POINT sub-domain (`s = ['a',' ']` only);
#     - MULTIPLICITY: parity of the marker count — agrees with gold at 0 and 1
#       markers, diverges at 2;
#     - POSITIONAL: membership of the tail only; of a bounded prefix only; of the
#       head only;
#     - OVER-APPROXIMATION: gold's membership OR a second code point's; gold's
#       membership OR a length test (right whenever gold is true, wrong on a
#       long marker-free string);
#     - UNDER-APPROXIMATION: membership AND `length ≥ 2` (wrong on the singleton
#       marker);
#     - NONDETERMINISM: `let b :| True` and `let b :| (b = true ∨ b = false)` —
#       an unconstrained/weakly-constrained choice for the flag. Both rejected
#       with the residual goal `⊢ i = decide (' ' ∈ s)`, i.e. the ensures forces
#       the choice rather than admitting any boolean, which is the demonic-choice
#       reading one wants and is not otherwise probed by the battery.
#   Each wrong impl that is refutable at a concrete point was additionally given
#   a witness and both halves built: rival exit 0, gold exit 1 with `⊢ False`.
#
#   ATTACK E (SPEC-TOO-STRONG) — 5 NEW correct reshapes; the frozen spec accepts
#   every one, so no soundness hole. `decide (' ' ∈ s)`, `!!(s.contains ' ')` and
#   `s.reverse.contains ' '` verify with a one-line `simp [markerFlag]`-family
#   proof; `s.any (· == ' ')` needs `List.any_beq'` (it is NOT definitionally
#   equal — bare `rfl` fails, which is why the ported positives alone did not
#   cover this shape); the filter/`isEmpty` reshape needs a hand induction with a
#   `beq` orientation step. Both of the latter two initially failed for me on
#   TACTIC grounds and were then closed — recorded here so the failure is not
#   mistaken for a spec hole. One further reshape, `s.eraseDups.contains ' '`, is
#   correct and reduces to the true residual goal `' ' ∈ s.eraseDups ↔ ' ' ∈ s`,
#   but no library lemma for it was found and no proof was closed: it is recorded
#   UNCERTAIN, not as a hole.
#
#   ADMISSIBILITY MUTATION — the shipped admissibility assert is load-bearing:
#   flipping its F2P-shaped conjunct to `= true` fails to elaborate (exit 1,
#   `decide` proved the conjunction false), so the case is not discharged by
#   anything weaker than the real evaluation of the flag at that input.
#
#   WITNESS FORGERY PROBE (attack B′) — for all six reject cases the gold-side
#   error is a plain evaluation (`unsolved goals ⊢ False`), and it was confirmed
#   to CARRY INFORMATION about the claim rather than being a constant: flipping
#   each witness's claim from `= false` to `= true` INVERTS both exit codes —
#   gold then builds (exit 0) and the rival fails (exit 1, `⊢ False`). So the
#   gold-side failure tracks what is asserted and none of the six is hollow.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (`markerFlag` is a concrete pure `def`, `MarkerError` is the
# failure-leg inductive, not an opaque callee), and this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
