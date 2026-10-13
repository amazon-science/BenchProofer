"""properties.py — G-PBT falsification battery for django__django-14017 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct combineConditions`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  combineConditions (other : Operand) (combined : CombinedNode)
      return (out : Except CombineErr CombinedNode)
    ensures out = combineResult other combined

The method decides whether a right-hand operand may participate in a logical
combination of filter conditions, and if so yields the (unchanged) combination
result the operation would otherwise build. The pure region pins the whole
outcome as a total function of the method's own two inputs:

  combineResult other combined
    = if other.isFilterNode || other.isCondition then Except.ok combined
      else Except.error .notCombinable

with ``Operand`` reduced to the only two observables the eligibility test reads:
``isFilterNode`` (the operand is itself a filter-condition container) and
``isCondition`` (the operand advertises that it denotes a boolean condition
usable as a filter). So the sole ensures pins TWO independent behaviours:

  * (D) the eligibility DECISION — accept-vs-reject is fixed in BOTH directions
        by ``isFilterNode || isCondition``: an operand that is EITHER is accepted,
        an operand that is NEITHER is rejected. There is no slack; a rival that
        misclassifies any operand on either half of the disjunction, or on the
        neither-case, violates the ensures. The discriminating content of the
        change lives here — accept an operand that is not a filter-condition
        container but DOES advertise a boolean condition (the ``isCondition``
        half), where the pre-patch behaviour accepted only ``isFilterNode``.
  * (R) the RESULT carried on acceptance — the accepted branch surfaces the
        (unchanged) combination ``combined`` UNCHANGED. A rival that decides
        correctly but returns a different combination node violates the ensures
        on the result half.

Both INPUT binders are free (the ``require`` region is empty) and the post-image
must hold for EVERY value of each:
  * ``other``    — reduced to (``isFilterNode``, ``isCondition``); drives (D).
  * ``combined`` — the combination result carried through by (R).

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend, exactly as the nagini
    sibling already records for its own carrier (all five inputs pass-by-VALUE,
    no ``Acc(x,1/2)`` read-only heap input). Lean and Velvet are referentially
    transparent: every parameter is an immutable value, this bundle declares no
    ``mut`` binder, there is no heap and no aliasing. There is no read-only input
    to overwrite and no permission system to trip. No substitute is fabricated.
  * TERMINATION / NON-TERMINATION — CLOSED BY THE FROZEN SEMANTICS, and NOT a
    spec hole. CORRECTED BY AUDIT, and the correction is about the ARTIFACT
    moving under the prose rather than about a misreading: this text was written
    when the frozen file set ``set_option loom.semantics.termination "partial"``,
    and recorded the class as a KNOWN SPEC HOLE that admits a diverging rival,
    the right disposition for a ``partial`` bundle. The frozen ``Solution.lean``
    now sets ``"total"``, as all 500 velvet bundles do, which INVERTS the
    disposition: under
    total-correctness semantics the verifier discharges a termination obligation,
    so the diverging rival is genuinely REJECTED and there is no hole left here.
    Re-measured against the CURRENT frozen file rather than inherited from either
    revision: splicing ``while True do / pure ()`` above the frozen body and
    freeing the elided proof tail is REFUSED at exit 1 with
    ``error: Decreasing annotations are required in total correctness
    semantics``, while the frozen solution itself still verifies at exit 0. The
    spec does NOT admit a diverging impl, so there is no hole to escalate and
    nothing was silently dropped.
    It is nonetheless NOT SHIPPABLE as an ``expect="reject"`` case, for a reason
    about the WITNESS rather than the spec, and that reason is measured too: the
    same termination error is raised at the impl site, so the witness file built
    from a diverging rival does not elaborate AT ALL. Every witness shape fails
    against the rival — the tester form (``decide`` and ``decide +kernel``: the
    ``forIn Lean.Loop.mk`` term leaves the tester's ``Decidable`` instance stuck,
    ``did not reduce to `isTrue` or `isFalse```), the Hoare-triple form
    (``¬ triple …``), and even a control ``example : (1:Nat) + 1 = 2 := by
    decide``, which fails on the diverging rival at exit 1 on the termination
    error alone. Confirmed through the gate's own ``_check_witness``: outcome
    ``witness-unproven``. Since the ``expect="reject"`` contract requires the
    witness to ELABORATE against the rival, the class cannot be shipped — the
    rejection is real and is carried by the frozen ``total`` option itself, not
    by a witness. Recorded as a TOOLING limit on the witness carrier, not as a
    spec hole and not as vacuity. See footer.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``combineResult other combined``, and ``combineResult`` is a concrete
    ``def`` in the ``pure`` region computing the outcome from the method's own
    arguments (the ``axioms`` region is empty; there is no opaque answer key to
    echo). The unique satisfier IS the grounded decision-plus-result, so there is
    no wrong echo to build; the honest control is the cheapest faithful reshape
    (the ``pos-*`` cases).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    single behavioural effect (accept-vs-reject) is exactly the ``Except`` carrier
    of the return value: ``Except.error .notCombinable`` ↔ the operand is
    rejected, ``Except.ok combined`` ↔ the combination is accepted. So the
    raise/return fork is fully observable to the ensures; the sibling's
    ``weak-control-flow-no-raise`` rival (never raise, always return) collapses
    onto the accept-everything rival here (see footer).
  * PARTIAL-DOMAIN / VALUE — heavily exercised. The pre-patch and mirror rivals
    each decide correctly on ONE half of the disjunction and diverge on the
    other; the accept-everything rival is wrong only on the neither-case; the
    result rival keeps the whole decision right and mangles only the carried
    combination.
"""
from pathlib import Path

INSTANCE = "django__django-14017"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- Accept the combination when `other` is a filter-condition container OR it\n"
    "    -- advertises that it denotes a boolean condition usable as a filter; only an\n"
    "    -- operand that is neither is rejected. On acceptance the unchanged\n"
    "    -- combination `combined` is returned.\n"
    "    let result : Except CombineErr CombinedNode :=\n"
    "      if other.isFilterNode || other.isCondition then Except.ok combined\n"
    "      else Except.error .notCombinable\n"
    "    return result\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct combineConditions by\n  loom_solve\n  simp [combineResult]"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `combineConditionsTester <other> <combined> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped (so no tactic
# ---- script can mask the verdict). The `Except CombineErr CombinedNode` return
# ---- carrier needs a decidable-equality instance for the tester derivation; it
# ---- is DERIVED, not assumed — no `axiom`/`sorry`/`native_decide` is involved,
# ---- and the frozen solution rejects the witnesses all the same.
_DEC = "deriving instance DecidableEq for Except\n\n"
_TESTER = (_DEC +
           "extract_program_for combineConditions\n"
           "prove_precondition_decidable_for combineConditions\n"
           "prove_postcondition_decidable_for combineConditions\n"
           "derive_tester_for combineConditions\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the decision-plus-result value
    # identical and only reshapes the executable surface; the reproof stays
    # close to the frozen `loom_solve; simp [combineResult]` script.
    # =====================================================================
    {
        "id": "pos-negate-swap-arms",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the eligibility guard and swap the two arms (reject
        # first). Same outcome on every input — `!(a || b)` rejects exactly where
        # `a || b` accepts, and the accepting arm still surfaces the same
        # `combined`. Proof retuned (the do-block changed shape): after
        # `simp [combineResult]` the residual goal is the boolean case-split.
        "module": _impl_reproved(
            "    let out : Except CombineErr CombinedNode :=\n"
            "      if !(other.isFilterNode || other.isCondition) then Except.error .notCombinable\n"
            "      else Except.ok combined\n"
            "    return out",
            "prove_correct combineConditions by\n"
            "  loom_solve\n"
            "  simp [combineResult]\n"
            "  cases other.isFilterNode <;> cases other.isCondition <;> simp"),
        "rationale": "negating the eligibility guard and swapping the two arms "
                     "computes the SAME outcome on every input (`!(a || b)` "
                     "rejects exactly where `a || b` accepts, and the accepting "
                     "arm surfaces the same `combined`), so "
                     "`out = combineResult other combined` still holds; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on branch order.",
    },
    {
        "id": "pos-commute-disjunction",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: commute the eligibility disjunction (test the boolean-condition
        # observable first) and bind it to a typed local before the branch. Same
        # value flow (`||` is commutative); the reproof adds `Bool.or_comm`.
        "module": _impl_reproved(
            "    let eligible : Bool := other.isCondition || other.isFilterNode\n"
            "    let out : Except CombineErr CombinedNode :=\n"
            "      if eligible then Except.ok combined else Except.error .notCombinable\n"
            "    return out",
            "prove_correct combineConditions by\n"
            "  loom_solve\n"
            "  simp [combineResult, Bool.or_comm]"),
        "rationale": "commuting the eligibility disjunction (both observables are "
                     "consulted, order swapped) and binding it to a typed local "
                     "leaves the decision and the surfaced `combined` identical, "
                     "so `out = combineResult other combined` is unchanged; a "
                     "correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "order in which the two admissibility observables are read.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # analogue of PRECOND-TOO-STRONG on a TOTAL-domain carrier is the
    # OBLIGATION being unsatisfiable — or degenerate — at exactly an F2P-shaped
    # input, so this case discharges the method's OWN Hoare triple at two
    # concrete operand shapes, by evaluation, as `have`s, BEFORE the frozen
    # obligation is closed verbatim.
    #
    # STRENGTHENED BY AUDIT. The shipped case used an in-region `assert` over
    # `combineResult` at two literal operands, closed by `loom_solve <;> simp
    # [combineResult]`. Measured with real builds, that assert WAS live — its two
    # liveness twins (F2P conjunct flipped to the rejection; neither-case
    # conjunct flipped to acceptance) each fail to elaborate, exit 1 with
    # `unsolved goals` — so the case was not vacuous. But it was strictly weaker
    # than the lane calls for: an `assert` about `combineResult` restates the
    # POST-IMAGE at two points and never touches `combineConditions`, so it
    # cannot show the method's obligation is SATISFIABLE at an F2P-shaped input.
    # Replaced with two `have`s over the real triple, each proven by evaluation
    # (`unfold combineConditions; rw [triple]; simp [wp_pure, combineResult]`),
    # after which the frozen `loom_solve; simp [combineResult]` closes the
    # byte-identical obligation:
    #   * admF2p    — at the F2P discriminator (`isFilterNode=false,
    #     isCondition=true`) the triple forces `Except.ok { payload := [7] }`:
    #     the operand that merely ADVERTISES a boolean condition is accepted AND
    #     the combination is carried through unchanged;
    #   * admNeither — at the neither-case (`false,false`) the triple forces
    #     `Except.error .notCombinable`: the rejection path is live too, so the
    #     obligation is not the constant acceptance.
    # Liveness re-measured on the NEW shape with three real builds, all exit 1
    # (`unsolved goals`): flipping admF2p's target to the rejection; flipping
    # admNeither's target to acceptance; and keeping the acceptance but demanding
    # the EMPTY combination (`Except.ok { payload := [] }`), which pins the
    # carried-result half at the same point. So neither `have` is a tautology
    # `simp` would close for any target. If this case cannot verify => the
    # obligation is unsatisfiable at an F2P-shaped input / PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-condition-observable-live",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            # impl kept VERBATIM (the frozen body) — only the elided proof gains
            # the two `have`s, so the ensures still discharges on the real impl.
            "    -- Accept the combination when `other` is a filter-condition container OR it\n"
            "    -- advertises that it denotes a boolean condition usable as a filter; only an\n"
            "    -- operand that is neither is rejected. On acceptance the unchanged\n"
            "    -- combination `combined` is returned.\n"
            "    let result : Except CombineErr CombinedNode :=\n"
            "      if other.isFilterNode || other.isCondition then Except.ok combined\n"
            "      else Except.error .notCombinable\n"
            "    return result",
            "prove_correct combineConditions by\n"
            "  have admF2p : triple (l := Prop) (True)\n"
            "      (combineConditions { isFilterNode := false, isCondition := true } { payload := [7] })\n"
            "      (fun out => out = Except.ok { payload := [7] }) := by\n"
            "    unfold combineConditions\n"
            "    rw [triple]\n"
            "    simp only [le_Prop_eq]\n"
            "    intro _\n"
            "    simp [wp_pure, combineResult]\n"
            "  have admNeither : triple (l := Prop) (True)\n"
            "      (combineConditions { isFilterNode := false, isCondition := false } { payload := [7] })\n"
            "      (fun out => out = Except.error CombineErr.notCombinable) := by\n"
            "    unfold combineConditions\n"
            "    rw [triple]\n"
            "    simp only [le_Prop_eq]\n"
            "    intro _\n"
            "    simp [wp_pure, combineResult]\n"
            "  loom_solve\n"
            "  simp [combineResult]"),
        "rationale": "ADMISSIBILITY on a total carrier: the method's OWN "
                     "obligation is SATISFIABLE, and non-degenerate in BOTH "
                     "directions, at concrete F2P-shaped inputs — discharged by "
                     "evaluation as two `have`s over the real Hoare triple for "
                     "`combineConditions`, before the frozen tactic closes the "
                     "byte-identical obligation. `admF2p`: at the F2P "
                     "discriminator (`isFilterNode=false, isCondition=true`) the "
                     "triple forces `Except.ok { payload := [7] }` — the operand "
                     "that is NOT a filter-condition container but DOES advertise "
                     "a boolean condition is accepted, and the combination is "
                     "carried through unchanged. `admNeither`: at the "
                     "neither-case (`false,false`) it forces "
                     "`Except.error .notCombinable` — the rejection path is live, "
                     "so the obligation is not the constant acceptance. Each "
                     "claim is falsifiable: flipping either target, or demanding "
                     "the EMPTY combination at the accepted point, leaves "
                     "unsolved goals. If it cannot verify => the obligation is "
                     "unsatisfiable at an F2P-shaped input / PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that ELABORATES against
    # the rival and FAILS on the frozen solution, and carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-prepatch-filter-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: accept only a filter-condition container, ignoring
        # the boolean-condition observable the fix adds. Rejects an operand that
        # advertises a boolean condition but is not itself a container.
        "module": _impl(
            "    let result : Except CombineErr CombinedNode :=\n"
            "      if other.isFilterNode then Except.ok combined\n"
            "      else Except.error .notCombinable\n"
            "    return result"),
        "refinement": "this IS the pre-patch behaviour: the guard consults ONLY "
                      "whether the operand is a filter-condition container and "
                      "rejects everything else. Its faithful real counterpart is "
                      "the unchanged repo, which raises on a boolean-condition "
                      "operand combined on the right — exactly the shape the F2P "
                      "tests exercise (a boolean expression combined into a filter "
                      "condition). Those tests now assert the combination "
                      "SUCCEEDS. It would NOT resolve — the precise change the "
                      "spec senses (G-DIFF).",
        "rationale": "REJECT from `out = combineResult other combined` on the "
                     "decision (D): on `isFilterNode=false, isCondition=true` the "
                     "post-image demands `Except.ok combined` (the operand IS "
                     "eligible via the second observable) but the rival rejects. "
                     "Refuted at exactly that operand — the F2P discriminator, and "
                     "the sub-domain where the mirror rival is CORRECT.",
        "witness": _witness(
            "combineConditionsTester { isFilterNode := false, isCondition := true } "
            "{ payload := [1] }"),
    },
    {
        "id": "weak-mirror-condition-only",
        "kind": "uniqueness",
        "expect": "reject",
        # MIRROR of the pre-patch bug: accept only a boolean-condition operand,
        # reject a same-kind filter-condition container. Correct on the
        # isCondition half, wrong on the isFilterNode half.
        "module": _impl(
            "    let result : Except CombineErr CombinedNode :=\n"
            "      if other.isCondition then Except.ok combined\n"
            "      else Except.error .notCombinable\n"
            "    return result"),
        "refinement": "accepts an operand ONLY via the boolean-condition "
                      "observable, dropping the container observable from the "
                      "guard entirely. A faithful counterpart therefore rests the "
                      "whole eligibility decision on an advertised attribute "
                      "rather than on the operand's kind, so any container-kind "
                      "operand that does NOT advertise a boolean condition is "
                      "rejected where the project requires success. It would NOT "
                      "resolve. NOTE (audit, carrier caveat): on THIS repo the two "
                      "observables are not independent — a filter-condition "
                      "container advertises a boolean condition by virtue of its "
                      "kind — so the concrete operand this rival is refuted at "
                      "(`isFilterNode=true, isCondition=false`) is a GHOST point "
                      "of the Lean carrier, outside the image of the real operand "
                      "domain. The rival is still observably WRONG on the carrier "
                      "(it disagrees with `combineResult` there), and it is the "
                      "only case attacking the container half of the disjunction, "
                      "so it is kept — but its attestation is about the SPEC's "
                      "treatment of the container observable, not about a repo "
                      "regression reachable by a real operand. See the footer.",
        "rationale": "REJECT from `out = combineResult other combined` on the "
                     "decision (D): on `isFilterNode=true, isCondition=false` the "
                     "post-image demands `Except.ok combined` (eligible via the "
                     "first observable) but the rival rejects. Refuted at that "
                     "operand — the sub-domain where the pre-patch rival is "
                     "CORRECT, so this rival carries its own separating input. "
                     "This is the ONLY case that pins the container observable as "
                     "an independently sufficient ground for eligibility: it is "
                     "what forbids the spec from being read as "
                     "`isCondition`-alone. Varies the `combined` binder ([2]) "
                     "against the others.",
        "witness": _witness(
            "combineConditionsTester { isFilterNode := true, isCondition := false } "
            "{ payload := [2] }"),
    },
    {
        "id": "weak-accept-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the rejection entirely — always accept. Correct on both eligible
        # halves, wrong only on the neither-case (an operand that is neither a
        # container nor a boolean condition). Subsumes the sibling's
        # control-flow-no-raise rival: on this carrier "never raise" IS "always
        # return Except.ok".
        "module": _impl(
            "    let result : Except CombineErr CombinedNode := Except.ok combined\n"
            "    return result"),
        "refinement": "accepting any operand is what a real patch that DELETED the "
                      "guard (or its raise) would do — it never rejects, so an "
                      "operand that is neither a filter-condition container nor a "
                      "boolean condition (e.g. a plain value) is combined instead "
                      "of raising, then crashes downstream. It breaks the P2P "
                      "tests that rely on the combination REJECTING an "
                      "ineligible operand. It would NOT resolve.",
        "rationale": "REJECT from `out = combineResult other combined` on the "
                     "decision (D): on the neither-case (`isFilterNode=false, "
                     "isCondition=false`) the post-image demands "
                     "`Except.error .notCombinable` but the rival accepts. "
                     "Refuted at the neither-case — the ONLY sub-domain where this "
                     "rival diverges from gold, distinct from every guard rival "
                     "above (which are wrong on an eligible half, not the "
                     "neither-case). Varies `combined` ([3]).",
        "witness": _witness(
            "combineConditionsTester { isFilterNode := false, isCondition := false } "
            "{ payload := [3] }"),
    },
    {
        "id": "weak-exclusive-or-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # BOTH-TRUE rival: read the two admissibility observables as mutually
        # EXCLUSIVE (accept an operand that has exactly one of them) instead of
        # as a disjunction. Correct on all three of the operand classes the
        # other decision rivals attack — (false,true), (true,false),
        # (false,false) — and wrong ONLY on the fourth, (true,true): an operand
        # that is BOTH a filter-condition container AND advertises a boolean
        # condition. Added by audit: every shipped decision rival was refuted at
        # one of the other three classes, so nothing attested that the guard is
        # a genuine OR rather than an XOR on the both-true class.
        "module": _impl(
            "    let result : Except CombineErr CombinedNode :=\n"
            "      if xor other.isFilterNode other.isCondition then Except.ok combined\n"
            "      else Except.error .notCombinable\n"
            "    return result"),
        "refinement": "a faithful counterpart reads the two admissibility "
                      "observables as alternatives that exclude each other, so "
                      "it rejects an operand that satisfies BOTH — a "
                      "filter-condition container that also advertises that it "
                      "denotes a boolean condition. Such an operand is combined "
                      "by the ordinary container-and-container paths the project "
                      "has always supported, so this guard raises where the "
                      "project requires success and breaks the P2P combinable "
                      "tests. It would NOT resolve.",
        "rationale": "REJECT from `out = combineResult other combined` on the "
                     "decision (D): on `isFilterNode=true, isCondition=true` the "
                     "post-image demands `Except.ok combined` (the operand is "
                     "eligible via BOTH observables — the disjunction is true) "
                     "but the rival rejects, because an exclusive reading is "
                     "false there. Refuted at exactly that operand: the FOURTH "
                     "operand class, the one sub-domain on which every other "
                     "decision rival in this battery agrees with the spec, so "
                     "this rival carries its own separating input. Varies "
                     "`combined` ([4]).",
        "witness": _witness(
            "combineConditionsTester { isFilterNode := true, isCondition := true } "
            "{ payload := [4] }"),
    },
    {
        "id": "weak-wrong-combination-result",
        "kind": "uniqueness",
        "expect": "reject",
        # RESULT rival (R): the eligibility DECISION is exactly right — the frozen
        # guard is kept verbatim — but the accepted branch surfaces a DIFFERENT
        # combination node (the empty one) instead of the `combined` the operation
        # would build. Built to abuse the `combined` binder, the free input the
        # accepted branch carries: every decision rival above surfaces the correct
        # `combined` on its accept branch (or never reaches it), so none of them
        # attests that the result carries `combined` through unchanged. This one
        # is wrong exactly because it drops it. This is the velvet counterpart of
        # the sibling's branch-selection / merge-connector rivals: on this carrier
        # the whole internal construction of the combination is folded into the
        # opaque `combined`, so the only structural pin the ensures makes on the
        # accepted branch is that `combined` is returned UNCHANGED.
        "module": _impl(
            "    let result : Except CombineErr CombinedNode :=\n"
            "      if other.isFilterNode || other.isCondition then Except.ok { payload := [] }\n"
            "      else Except.error .notCombinable\n"
            "    return result"),
        "refinement": "a counterpart that decides eligibility correctly but "
                      "returns a DIFFERENT combination node than the operation "
                      "builds from the two operands would produce the wrong "
                      "filter for an accepted combination, so the F2P tests — "
                      "which assert the exact rows the combined filter returns — "
                      "fail on the result even though the accept/reject decision "
                      "is right. It would NOT resolve.",
        "rationale": "REJECT from `out = combineResult other combined` on the "
                     "result (R): the accepted branch of the post-image surfaces "
                     "`combined` UNCHANGED; the rival surfaces the empty node "
                     "instead, so at any accepted operand with a NON-EMPTY "
                     "`combined` the two results differ. Refuted at an eligible "
                     "operand whose `combined` is non-empty ([1]) — the point that "
                     "makes the post-image's dependence on the `combined` binder "
                     "observable (every decision rival holds this half correct). "
                     "RE-AIMED by audit: the witness previously stated the same "
                     "refutation at `isFilterNode=true, isCondition=false`, a "
                     "GHOST point of this carrier (the two observables are not "
                     "independent on the real operand domain — see the footer), so "
                     "the result half was attested only at an operand no real "
                     "input maps to. This rival is wrong at SIX of the twelve "
                     "sampled points, including the fully reachable F2P shape, so "
                     "re-aiming costs nothing and the attestation now lands inside "
                     "the reachable domain.",
        "witness": _witness(
            "combineConditionsTester { isFilterNode := false, isCondition := true } "
            "{ payload := [1] }"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness). The sibling contracts a RICHER
# surface: `combine(other_is_container, other_is_boolean_operand, other_empty,
# self_empty, conn)` models not only the admissibility guard (P1/X1) but ALSO the
# empty-operand branch selection (P2-P4) and the merge connector (P5). This
# backend narrows the carrier to the ONLY behaviour the patch changes — the
# eligibility guard — and folds the entire downstream construction (the empty
# short-circuits and the `obj.add(...)` merge, UNCHANGED by the patch; mapping.md
# §2/§3) into the opaque `combined : CombinedNode` supplied as a free input. So
# the branch-selection and connector clauses have no dedicated counterpart here:
# their structure is not modeled. That is carrier narrowing, not an omission of a
# modeled behaviour.
#
#   sibling case                    -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-control-reshape             -> pos-negate-swap-arms           PORTED
#   admiss-f2p-shape                -> admiss-condition-observable-live RE-AIMED
#   weak-prepatch-narrowed-guard    -> weak-prepatch-filter-only      PORTED
#   weak-mirror-narrowed-guard      -> weak-mirror-condition-only     PORTED
#   weak-accept-everything          -> weak-accept-everything         PORTED
#   weak-control-flow-no-raise      -> weak-accept-everything         SUBSUMED
#   weak-branch-swap (P2)           -> weak-wrong-combination-result  RE-AIMED
#   weak-wrong-merge-connector (P5) -> weak-wrong-combination-result  RE-AIMED
#   weak-diverge-no-answer          -> (none)                    SPEC-CLOSED/
#                                                                WITNESS-BLOCKED
#   (no sibling)                    -> pos-commute-disjunction        ADDED (2nd pos.)
#   (no sibling)                    -> weak-exclusive-or-guard        ADDED (audit)
#
# 3 ported, 1 re-aimed AND strengthened (admiss), 2 branch/connector rivals
# re-aimed onto the result rival, 1 subsumed, 1 spec-closed-but-witness-blocked;
# 1 extra positive and 1 extra rival added.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT — SPEC-STRENGTH PROBES (attacks D and E). All builds real;
# exit codes as observed. Nothing below is shipped as a case (the battery's five
# rivals already exhaust the four operand classes and the result half); it is
# recorded so a later reader knows the spec was probed OUTSIDE the shipped set
# and where the boundary was found.
#
# D (SPEC-TOO-WEAK: NEW wrong impls not in the battery — every one REJECTED,
#    so no spec hole was found on any of these axes):
#   and-guard (`isFilterNode && isCondition`)                    exit 1
#   always-reject (constant `Except.error`)                      exit 1
#   ignore-both-inputs (constant `Except.ok { payload := [] }`)  exit 1
#   swap-the-arms (accept the neither-case, reject the eligible) exit 1
#   payload-reversed on the accepted branch                      exit 1
#   accept only when the combination is EMPTY                    exit 1
#   `isCondition && isFilterNode || isFilterNode` (drops the
#     isCondition-alone half — a second spelling of pre-patch)   exit 1
#   payload-append `combined.payload ++ [0]`                     exit 1
#   A nondeterministic ECHO of the post-image (`let r :| r = combineResult …`)
#     does not even parse in this fragment (`unexpected token ':|'`), so the
#     directive-8 echo attack has no surface here — consistent with the
#     UNGROUNDED-ORACLE read above: the post-image is a concrete `def` over the
#     method's own arguments, not an opaque answer key.
#
# E (SPEC-TOO-STRONG: NEW faithful correct reshapes — every one VERIFIES, so no
#    soundness hole; each needed only a retuned elided proof, never a spec
#    change):
#   four-way `match` on (isFilterNode, isCondition)              exit 0
#   nested ifs (isFilterNode, then isCondition)                  exit 0
#   De Morgan guard `(!isFilterNode) && (!isCondition)`          exit 0
#   `cond` instead of `if`                                       exit 0
#   Prop-level guard `isFilterNode = true ∨ isCondition = true`  exit 0
#   early `return`s from the branches                            exit 0
#   record round-trip `{ payload := combined.payload }`          exit 0
#   NOTE: four of these first failed with `error: No goals to be solved` under
#   the two shipped positives' retuned scripts — i.e. the SCRIPT overshot, not
#   the spec refusing them; each closes under the frozen
#   `loom_solve; simp [combineResult]` or `loom_solve <;> simp_all
#   [combineResult]`. A reader must not mistake that class of failure for a
#   soundness hole.
#
# The two shipped positives were also checked for the "definitionally the frozen
# impl" evasion, and both are genuine: replacing each one's retuned proof with
# the FROZEN script verbatim FAILS (exit 1, `unsolved goals` with the two
# non-identical `if` terms displayed), so neither reshape is definitionally equal
# to the frozen body and neither passes for free.
# ---------------------------------------------------------------------------
#
# ADDED (weak-exclusive-or-guard): the eligibility test reads TWO observables, so
#   its input domain has FOUR operand classes. The ported rivals refute at three
#   of them — (false,true) prepatch, (true,false) mirror, (false,false)
#   accept-everything — and every one of those rivals is CORRECT on the fourth,
#   (true,true). So no shipped case attested that the guard is a real
#   DISJUNCTION rather than an exclusive-or on the both-true class, and a rival
#   wrong only there would have gone unattacked. The sibling's five-argument
#   decision does not isolate this axis either (its X1/P1 pair is stated over the
#   same disjunction, and it ships no both-true rival), so this is not a dropped
#   sibling case but a gap this carrier's two-observable narrowing creates.
#
# RE-AIMED, then STRENGTHENED BY AUDIT (admissibility): the sibling constructs
#   the F2P operand shapes and asserts the postcondition-pinned branch/connector.
#   This backend's method has NO precondition and no branch/connector surface, so
#   the probe is re-aimed at the residual total-domain risk: the OBLIGATION being
#   unsatisfiable or degenerate at an F2P-shaped input. The port realised that as
#   an in-region `assert` over `combineResult` at two literal operands. That
#   assert was LIVE (both liveness twins fail, exit 1) but strictly weaker than
#   the lane calls for: it restates the POST-IMAGE and never mentions
#   `combineConditions`, so it could not show the METHOD's obligation is
#   satisfiable at that input. Replaced with two `have`s discharging the real
#   Hoare triple for `combineConditions` by evaluation at the F2P discriminator
#   (forced `Except.ok { payload := [7] }`) and at the neither-case (forced
#   `Except.error .notCombinable`), before the frozen tactic closes the
#   byte-identical obligation. Verified exit 0; three liveness twins (each target
#   flipped, plus the accepted point demanding the EMPTY combination) each exit 1
#   with `unsolved goals`.
# SUBSUMED (weak-control-flow-no-raise): the sibling keeps a syntactic guard on
#   an always-false condition so it NEVER raises. On nagini the raise-vs-return
#   difference is invisible to a pure VALUE abstraction, so it needs its own
#   control-flow-effect rival. On THIS carrier the raise/return fork IS the
#   `Except` value (error ↔ reject, ok ↔ accept), so "never raise" is literally
#   "always return Except.ok" — the accept-everything rival — and refuting it at
#   the neither-case refutes both. No separate case is fabricated.
# RE-AIMED (weak-branch-swap / weak-wrong-merge-connector): the sibling's P2-P5
#   rivals attack the STRUCTURE of the constructed node (which identity branch
#   fires, which connector the merge carries). This backend folds that entire
#   construction into the opaque `combined` free input (mapping.md §2/§3: the
#   short-circuits and `obj.add` are UNCHANGED by the patch and live after the
#   guard), so there is no branch/connector structure to mis-select. The only
#   pin the ensures makes on the accepted branch is that `combined` is returned
#   UNCHANGED, and `weak-wrong-combination-result` is the rival that violates
#   exactly that — the faithful velvet analogue of "returned the wrong
#   combination result".
# SPEC-CLOSED, WITNESS-BLOCKED (weak-diverge-no-answer) — CORRECTED BY AUDIT.
#   This entry previously read "KNOWN HOLE" and described the bundle as setting
#   `loom.semantics.termination "partial"`, under which a diverging impl would
#   satisfy the `ensures` vacuously and VERIFY. That was accurate when written;
#   the frozen `Solution.lean` now sets `"total"`, as all 500 velvet bundles do,
#   so the claim no longer
#   describes the artifact and the disposition INVERTS: under `total` the verifier
#   discharges a termination obligation, so the diverging rival is genuinely
#   REJECTED and there is no spec hole here. Verified against the CURRENT file.
#   Measured, not inherited (real builds, exit codes as observed):
#     * `while True do / pure ()` spliced above the frozen body, proof tail freed
#       to `loom_solve; all_goals simp [combineResult]`  -> exit 1,
#       `error: Decreasing annotations are required in total correctness
#       semantics`. Same result with the pre-patch decision after the loop.
#     * the frozen solution itself                       -> exit 0.
#   So the class is CLOSED by the frozen semantics option: in Loom that option is
#   itself what opens `TotalCorrectness` scope, so the setting and the `open`
#   cannot disagree, and every velvet bundle in the corpus carries it. Nothing
#   needs escalating.
#   It still ships NO reject case, and the reason is a TOOLING limit on the
#   witness carrier rather than the spec. The `expect="reject"` contract requires
#   the witness to ELABORATE against the rival, and on a diverging rival the
#   termination error fires at the IMPL site, so the whole witness file fails to
#   elaborate whatever it claims. Every shape was tried against the rival, all
#   exit 1:
#     * the tester form under `decide` and under `decide +kernel` — the
#       unreduced `forIn Lean.Loop.mk` term additionally leaves the tester's
#       `Decidable` instance stuck (`did not reduce to `isTrue` or `isFalse``),
#       which is the corpus's `reduction` screen;
#     * the same with the loop GUARDED by `other.isFilterNode` (false at the
#       witness point), in case the guard let the tester reduce — it does not;
#     * the Hoare-triple form `¬ triple (l := Prop) (True) (combineConditions …)
#       (fun out => out = combineResult …)`;
#     * a CONTROL witness `example : (1:Nat) + 1 = 2 := by decide`, which also
#       fails against the diverging rival on the termination error alone — proof
#       that the failure is the rival file's compilability, not the claim.
#   Judged through the gate's own `_check_witness`: outcome `witness-unproven`.
#   A `witness_reference` does not help either: the reference replaces the
#   GOLD-side subject, and the half that fails here is the RIVAL side.
#   Disposition: the spec rejects the rival (verified by build), the battery
#   cannot express the rejection as a witnessed case, and this is recorded as a
#   witness-carrier tooling limit — NOT a spec hole (the spec is sound here) and
#   NOT vacuity (a diverging impl is writable and is refused).
# ADDED (pos-commute-disjunction): a second positive control this backend affords
#   — commute the eligibility disjunction so the two admissibility observables are
#   read in the opposite order. Guards the spec against being SPEC-TOO-STRONG on
#   the order in which the two observables are consulted, a reshape axis the
#   sibling's five-argument decision does not isolate.
#
# GHOST POINT of this carrier (established by audit; read the whole coverage
#   claim below through it). `Operand` gives the two observables as INDEPENDENT
#   `Bool` fields, but the two repository predicates they abstract are not
#   independent: a filter-condition container advertises that it denotes a boolean
#   condition BY VIRTUE OF ITS KIND (the advertisement is a class-level property of
#   the container type, inherited by every instance, not something an individual
#   operand may withhold). RE-DERIVED INDEPENDENTLY BY A SECOND AUDIT against the
#   repository at this bundle's own `base_commit`: the container type declares the
#   advertisement as a class-level attribute fixed to a true value, above the
#   method under change, so every instance inherits it and none can withhold it.
#   The claim is machine-checked against the source, not merely asserted. So on
#   the real operand domain
#
#       isFilterNode = true   ==>   isCondition = true
#
#   and the operand class (isFilterNode=true, isCondition=false) is OUTSIDE the
#   image of the abstraction map — a point of the Lean carrier that no real
#   operand maps to. Three consequences, and only the third needed a repair:
#     (a) NOT a spec hole. `combineResult` is a total function of the two booleans
#         and agrees with the desired behaviour at every REACHABLE point; the
#         guard `isFilterNode || isCondition` is true at (true,false) and at
#         (true,true) alike, so the unreachable point neither weakens nor
#         strengthens the obligation and no rival can exploit it. Nothing to
#         escalate.
#     (b) the carrier is still the right one: a narrower carrier that made the
#         implication structural would stop `weak-mirror-condition-only` from
#         attacking the container observable at all, and that observable is half
#         the disjunction the spec pins.
#     (c) but a WITNESS aimed at the ghost point attests only there.
#         `weak-wrong-combination-result` was so aimed and has been RE-AIMED to
#         the reachable F2P shape (false,true) — it is wrong at six of the twelve
#         sampled points, so nothing was lost. `weak-mirror-condition-only` is
#         refuted ONLY at the ghost point by construction (that IS its
#         sub-domain); it is kept, because it is the only case forbidding the
#         spec from being read as `isCondition`-alone, and its refinement prose
#         has been corrected to claim a spec-level fact rather than a repo
#         regression that no real operand can trigger.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (5 witnesses, 4 distinct operand points):
#     other.isFilterNode — false (prepatch), true (mirror), false (accept-all),
#                          true (xor), false (result): varied true/false.
#     other.isCondition  — true (prepatch), false (mirror), false (accept-all),
#                          true (xor), true (result): varied true/false. ALL FOUR
#                          operand classes of the two-observable domain are
#                          probed: (false,true) prepatch AND result,
#                          (true,false) mirror, (false,false) accept-all,
#                          (true,true) xor. The carrier's domain is exhausted, so
#                          no operand class is unattacked; of the four, three are
#                          REACHABLE and the fourth is the ghost point above,
#                          attacked by `mirror` alone and read accordingly.
#     combined           — [1] (prepatch), [2] (mirror), [3] (accept-all),
#                          [4] (xor), [1]-vs-[] (result): varied, and the result
#                          rival's witness DEPENDS on `combined` being non-empty
#                          (its divergence from the spec IS the dropped
#                          combination).
#   Every independent top-level behaviour of the post-image is attacked: the
#   eligibility decision on the isFilterNode half (mirror), on the isCondition
#   half (prepatch), on the neither-case (accept-everything), and on the
#   both-case (exclusive-or); and the carried result
#   (wrong-combination-result). No binder is held fixed across all rivals.
#   Each of the four DECISION rivals is refuted at an operand class where all
#   three others agree with the spec, so no two of those witnesses are two
#   spellings of the same separating input. `weak-wrong-combination-result` now
#   shares the prepatch rival's operand point (false,true) after the re-aiming
#   above, and that is deliberate rather than a collision: the two are separated
#   on the OTHER binder, not on `other`. At (false,true) with `combined = [1]`
#   the prepatch rival returns `Except.error` (wrong decision, right result-shape)
#   while the result rival returns `Except.ok { payload := [] }` (right decision,
#   wrong result), so each witness is refuting a different half of the ensures at
#   that shared operand, and neither rival satisfies the other's witness.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (`combineResult` is a deep I/R model checked
# by G-CONF, not axiomatized; meta.json gates.G-AX = skip), and this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
