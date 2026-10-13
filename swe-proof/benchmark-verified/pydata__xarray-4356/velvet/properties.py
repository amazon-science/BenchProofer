"""properties.py — G-PBT falsification battery for pydata__xarray-4356 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct reductionMissingDecision`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  reductionMissingDecision
      (reducedSizes : List Nat) (missingCount : Nat) (requiredCount : Nat)
      (remainingDimCount : Nat) (totalSize : Nat)
      (fillAdmissible : Bool) (axisWasSequence : Bool)
      return (out : Except Unit Bool)
    ensures out = Except.ok
      (cellMissing remainingDimCount reducedSizes totalSize missingCount
         requiredCount fillAdmissible)

The method decides, for one cell of a reduced output, whether that cell must be
reported as missing — for a reduction that collapses a COLLECTION of dimensions,
no matter how many, and for BOTH output shapes:

  * SHAPED-OUTPUT arm (``remainingDimCount ≥ 1``): each cell aggregates the
    PRODUCT of the collapsed extents (``prodList reducedSizes``), and is missing
    exactly when the present count (block total minus the missing count) falls
    short of the requirement — i.e. ``prodList reducedSizes < missingCount +
    requiredCount``. The load-bearing arithmetic is the WHOLE-BLOCK product, not
    any single extent or leading prefix.
  * SINGLE-VALUE arm (``remainingDimCount = 0``): the whole input collapses to
    one value spanning ``totalSize`` elements, and that value is flagged missing
    only when its representation admits a missing marker (``fillAdmissible``) AND
    ``totalSize - missingCount < requiredCount``. For representations that cannot
    carry a marker the cell is NEVER reported missing regardless of the
    requirement — so ``fillAdmissible`` is a genuine gate, not decoration.

And the whole point of the change: the decision is produced for EVERY reduction
including one whose collapsed dimensions were named as a SEQUENCE
(``axisWasSequence``) — collapsing several dimensions is handled exactly like
collapsing one, so ``out`` is always ``Except.ok ..`` and NEVER a rejection,
independent of that flag.

There is NO opaque answer key to echo: ``cellMissing`` (and ``prodList``) are
fully unfolded ``def``s over the method's own arguments (the ``axioms`` region is
empty — the product is DEEP-modeled, not axiomatized), so the only way to satisfy
the postcondition is to compute the right decision from the right block count on
the right branch. (Directive 8.)

SEVEN INPUT BINDERS. The postcondition depends on six of them and is
DELIBERATELY independent of the seventh:

  * ``remainingDimCount`` — selects the arm (shaped-output vs single-value).
  * ``reducedSizes`` — the collapsed extents; the shaped-output block count is
    their product.
  * ``missingCount`` / ``requiredCount`` — the present-count comparison on both
    arms.
  * ``totalSize`` — the single-value arm's element span.
  * ``fillAdmissible`` — the single-value arm's marker gate.
  * ``axisWasSequence`` — DELIBERATELY FREE: the fix's whole content is that the
    decision is produced regardless of it (never a rejection). A rival that
    branches on it yet still returns ``Except.ok`` on every arm VERIFIES
    (correctly — the spec is independent of it); a rival that REJECTS on it
    (the pre-patch guard) is caught because the spec pins ``out = Except.ok ..``
    unconditionally. So the reject lane DOES probe it — via the prepatch-guard
    rival — even though the spec's value does not depend on it.

The reject witnesses below vary all seven binders across their concrete input
points; the DISCRIMINATION for each rival comes from the specific clause named in
its rationale.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``reductionMissingDecisionTester ... = false`` says
the extracted program's result violates the postcondition at that concrete
input) and closes by ``decide``, checked in a file whose ``prove_correct`` block
has been stripped so no tactic script can mask the verdict. ``decide`` reduces
the extracted program by kernel computation; a program shaped as a ``while`` loop
over the extent stream does NOT reduce to ``isTrue``/``isFalse`` (the loop's
fixpoint elaborates through ``Classical.choice``, which the kernel cannot unfold
— measured: the FROZEN gold's own tester ``decide`` reports "reduction got stuck
at the ``Decidable`` instance" on the shaped-output arm). This has TWO
consequences, and both are handled explicitly rather than papered over:

  * On the RIVAL side, each reject rival attacking the shaped-output arm is
    expressed as a LOOP-FREE impl computing its (wrong) value directly from
    ``prodList`` — still a wrong implementation sharing the frozen spec, but one
    whose extracted tester ``decide``s.
  * On the SUBJECT side, gold cannot serve as the second half's subject at all:
    a ``decide`` against it is stuck for EVERY claim, true or false, so its exit
    code would attest to a refutation that was never performed (the gate reports
    this as ``witness-undecided``, and it did so for exactly these three cases
    before this was fixed). Each shaped-output rival therefore carries a
    ``witness_reference``: ``_LOOPFREE``, a CORRECT loop-free impl of the frozen
    spec that does reduce. Sound for the reason the gate independently checks —
    the reference shares the frozen spec and VERIFIES, and an impl the verifier
    accepts cannot violate its own spec, so a genuine "the spec is violated
    here" claim must fail against it. Measured: against ``_LOOPFREE`` each of
    the three witnesses is PROVED FALSE by ``decide`` (a real refutation), while
    each holds of its rival.

Neither move is a weakening: the frozen spec is untouched in every case and each
rival's divergence from ``cellMissing`` is real at the witnessed input. The
single-value-arm rivals need none of this — that arm is loop-free in gold
itself, so they are refuted directly against the frozen solution. The ``Except``
return needs one ``deriving instance DecidableEq for Except`` in the witness
preamble (an instance, not an assumption).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its ``sizes`` input is held at a fractional heap permission
    (``Acc(list_pred(sizes),1/2)``) an impl can illegally overwrite. Lean/Velvet
    are referentially transparent: every input here is an immutable value, this
    bundle declares no ``mut`` binder among the inputs, and there is no heap and
    no aliasing — so there is no read-only field to mutate and no substitute
    probe to build. Not fabricated (per the porting map: this class is vacuous
    here).
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the reject lane: the single
    clause pins the block count and the strict boundary on EVERY input, so a
    rival that counts only a prefix of the extents, or flips the boundary, or
    drops the marker gate, or reinstates the pre-patch rejection, diverges from
    ``cellMissing`` at a concrete input.
  * UNGROUNDED-ORACLE ECHO — N/A. ``cellMissing``/``prodList`` are unfolded
    ``def``s over the method's arguments (empty ``axioms`` region); nothing to
    echo.
  * AXIOM_TESTS — dropped. The axiom lane (the ``prodList`` A-reference deep
    model vs the real array reduction) is G-AX's job; this gate ignores
    AXIOM_TESTS regardless.

WITNESS PLACEMENT. Rivals share a refutation point only when they fail there for
the same reason; every reject rival below sits at its OWN distinct input tuple
(pts=6). Between them ``remainingDimCount`` moves across the shaped-output arm
(≥1) and the single-value arm (0); ``reducedSizes`` across empty and non-empty
lengths 2 and 3; ``fillAdmissible`` and ``axisWasSequence`` across both truth
values; and ``missingCount`` / ``requiredCount`` / ``totalSize`` are driven to
values whose comparison outcome flips at the tested rival's error.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4356"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the whole gold impl body: a single anchor lying wholly inside the impl
# ---- region and unique in the file (both facts asserted at load by _swap).
# ---- Rivals reshape the executable surface by swapping on this block.
_IMPL_BODY = (
    "    if remainingDimCount ≥ 1 then\n"
    "      let mut total : Nat := 1\n"
    "      let mut i := reducedSizes.length\n"
    "      while i > 0\n"
    "        invariant 0 ≤ i ∧ i ≤ reducedSizes.length\n"
    "        invariant total = prodList (reducedSizes.drop i)\n"
    "        done_with i = 0\n"
    "        decreasing i\n"
    "      do\n"
    "        let s := reducedSizes[i - 1]!\n"
    "        total := s * total\n"
    "        i := i - 1\n"
    "      return Except.ok (decide (total < missingCount + requiredCount))\n"
    "    else\n"
    "      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"

# ---- the single scalar-branch return line, wholly inside the impl region and
# ---- unique in the file. A positive control reshapes only this line, leaving
# ---- the shaped-output loop, its invariants and the frozen proof script intact.
_SCALAR_LINE = (
    "      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))"
)
assert _BASE.count(_SCALAR_LINE) == 1, "scalar-line anchor drift"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view, so a
# ---- positive that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, may retune it without
# ---- touching the spec or dropping the `prove_correct reductionMissingDecision`
# ---- obligation). Reject rivals keep it verbatim — they FAIL to build, which is
# ---- the point, and the failure's attribution to the spec is what the witness
# ---- (not the tactic breakage) supplies.
_PROOF_GOLD = (
    "prove_correct reductionMissingDecision by\n"
    "  loom_solve <;>\n"
    "    first\n"
    "      | (rw [prodList_drop_step reducedSizes i (by omega) (by omega)]; simp_all)\n"
    "      | (simp only [cellMissing]; split <;> simp_all)"
)
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the shaped-output arm is a single expression
# ---- (no loop invariant to peel) `loom_solve` reduces both arms to the pointwise
# ---- postcondition equality, closed by unfolding `cellMissing` and splitting.
_PROOF_FLAT = (
    "prove_correct reductionMissingDecision by\n"
    "  loom_solve <;> (simp only [cellMissing]; split <;> simp_all)"
)


def _impl(new_body):
    """Full Solution.lean with ONLY the impl-region body replaced (spec untouched)."""
    return _swap(_BASE, _IMPL_BODY, new_body)


def _impl_flatproof(new_body):
    """Reshape the impl into a single-expression form AND retune the proof to the
    loop-free script (both edits land in spec-elided regions)."""
    return _swap(_swap(_BASE, _IMPL_BODY, new_body), _PROOF_GOLD, _PROOF_FLAT)


# ---- THE WITNESS REFERENCE (see the CARRIER NOTE). A CORRECT, loop-free impl of
# ---- the frozen spec: the shaped-output arm's backward product loop is replaced
# ---- by the direct pure product `prodList reducedSizes`, whose value equals the
# ---- loop's on every input, with the proof retuned to the loop-free script.
# ---- Needed because the FROZEN impl keeps that `while` loop, whose fixpoint
# ---- elaborates through `Classical.choice`: a `decide` against it is stuck for
# ---- EVERY claim, true or false, so the frozen side's exit code carries no
# ---- information and cannot witness a refutation (measured: gold's own tester
# ---- reports "reduction got stuck at the `Decidable` instance" on the
# ---- shaped-output arm). Each reject rival that attacks the SHAPED-OUTPUT arm is
# ---- therefore refuted against this reference instead of against gold. Sound
# ---- for the reason the gate itself checks: the reference shares the frozen spec
# ---- and VERIFIES, and an impl the verifier accepts cannot violate its own spec,
# ---- so a genuine "the spec is violated here" claim must fail against it.
# ---- It is ALSO shipped as the `pos-direct-product` expect="verify" case below,
# ---- so the battery itself records that loop-freeness is not what any rival is
# ---- being rejected for.
_LOOPFREE = _impl_flatproof(
    "    if remainingDimCount ≥ 1 then\n"
    "      return Except.ok (decide (prodList reducedSizes < missingCount + requiredCount))\n"
    "    else\n"
    "      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `reductionMissingDecisionTester reducedSizes missingCount requiredCount
# ---- remainingDimCount totalSize fillAdmissible axisWasSequence = false` says
# ---- the extracted program's result violates the postcondition at that concrete
# ---- input. The `Except Unit Bool` return needs `DecidableEq Except` (an
# ---- INSTANCE, derived — not an axiom/sorry/native_decide). Checked in a file
# ---- whose `prove_correct` block has been stripped. Every argument is a concrete
# ---- literal so `decide` reduces the (loop-free) extracted program.
def _tester(body):
    return ("deriving instance DecidableEq for Except\n\n"
            "extract_program_for reductionMissingDecision\n"
            "prove_precondition_decidable_for reductionMissingDecision\n"
            "prove_postcondition_decidable_for reductionMissingDecision\n"
            "derive_tester_for reductionMissingDecision\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else SPEC-TOO-STRONG. The shaped-output arm's backward
    # product LOOP is replaced by the direct pure product `prodList reducedSizes`
    # (a genuinely different term shape — no loop, no invariants), and the proof
    # is retuned to the loop-free script. Observationally identical to gold on
    # both arms (verified with two real builds during authoring).
    # =====================================================================
    {
        "id": "pos-direct-product",
        "kind": "soundness",
        "expect": "verify",
        # The SAME source the shaped-output rivals are refuted against
        # (`_LOOPFREE`), shipped as a positive so the battery itself records that
        # loop-freeness is not what any rival is being rejected for.
        "module": _LOOPFREE,
        "rationale": (
            "computes the shaped-output block count as the direct pure product "
            "`prodList reducedSizes` instead of accumulating it in a backward "
            "`while` loop — a structurally different body (no loop, no invariants) "
            "whose value equals the loop's on every input, so `out = Except.ok "
            "(cellMissing ..)` still holds on both arms. A faithful reshape MUST "
            "verify, else the postcondition is SPEC-TOO-STRONG on the shape of the "
            "counting step. Exercises the obligation on a non-trivially reshaped "
            "impl (loop eliminated, proof retuned)."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL (soundness) — keep the shaped-output loop verbatim (and the
    # frozen proof script), reshape only the SINGLE-VALUE arm: write the
    # marker-gated decision as an explicit `if fillAdmissible then .. else false`
    # instead of `fillAdmissible && ..`. `b && c` and `if b then c else false` are
    # definitionally the same Bool, so the arm's value is unchanged and the frozen
    # `loom_solve` script still closes the byte-identical obligation. MUST verify.
    # =====================================================================
    {
        "id": "pos-scalar-if-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_BODY.replace(
            "      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))",
            "      return Except.ok (if fillAdmissible then decide (totalSize - missingCount < requiredCount) else false)")),
        "rationale": (
            "reshapes the single-value arm's marker gate from `fillAdmissible && "
            "decide (..)` to `if fillAdmissible then decide (..) else false` — the "
            "same Bool by definition — leaving the shaped-output loop, its "
            "invariants and the frozen proof script untouched. A correct reshape "
            "must verify, else SPEC-TOO-STRONG on the shape of the marker gate; it "
            "also exercises the obligation on a body whose scalar arm is textually "
            "different from gold's."
        ),
    },
    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so "a normal input
    # satisfies the precondition" is vacuous; nothing could exclude an F2P-shaped
    # input. The residual admissibility risk on a total domain is that the
    # post-image is DEGENERATE at the interesting point (a spec no impl can meet
    # reads like one every impl meets). This case discharges an in-region `assert`,
    # at the F2P-shaped 3-axis shaped-output input, that the post-image is
    # NON-DEGENERATE: with a 3-extent block [4,3,2] (product 24), no missing
    # elements and a requirement of 10, the cell is NOT flagged — i.e. the WHOLE
    # block of 24 is genuinely counted as present (a first-axis count of 4 would
    # flag it, so the assert pins that the surplus axes are counted). The impl is
    # kept verbatim so the method's own obligation still discharges; the proof is
    # retuned only to clear the extra assert goal by `decide`.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (cellMissing 1 [4,3,2] 0 0 10 false = false))\n"),
            _PROOF_GOLD,
            "prove_correct reductionMissingDecision by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [prodList_drop_step reducedSizes i (by omega) (by omega)]; simp_all)\n"
            "    | (simp only [cellMissing]; split <;> simp_all)"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "3-axis shaped-output input: for a 3-extent block [4,3,2] (product 24) "
            "with no missing elements and a requirement of 10, `cellMissing` demands "
            "the cell NOT be flagged — the whole 24-element block is counted as "
            "present, not just the first extent (a first-axis count of 4 < 10 would "
            "flag it). The in-region assert must discharge (else the obligation is "
            "degenerate at the point the fix cares about); the impl is kept verbatim "
            "so the method's own `ensures` still discharges."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test. Each shaped-output rival is expressed
    # LOOP-FREE so its extracted tester `decide`s (see the CARRIER NOTE).
    # =====================================================================
    {
        "id": "weak-first-axis-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE prepatch counting bug on the shaped-output arm: count only the FIRST
        # collapsed extent (`prodList (reducedSizes.take 1)`) instead of the whole
        # block. Coincides with the product for a single reduced dimension;
        # UNDERCOUNTS for two or more with a non-unit later extent.
        "module": _impl(
            "    if remainingDimCount ≥ 1 then\n"
            "      return Except.ok (decide (prodList (reducedSizes.take 1) < missingCount + requiredCount))\n"
            "    else\n"
            "      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))"),
        "refinement": (
            "this counts a single collapsed extent rather than the product over "
            "all of them — the literal pre-patch element count for a multi-dimension "
            "reduction. On the failing multi-dimension scenario it either counts "
            "shape[x] alone instead of shape[x]*shape[y]*shape[z], flagging cells "
            "the full-block reduction keeps, so the multi-dimension result diverges "
            "from the reference all-dimensions reduction the failing test asserts "
            "equal. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the shaped-output arm of `cellMissing`: the arm pins the "
            "WHOLE-BLOCK product `prodList reducedSizes`, and this rival uses "
            "`prodList (reducedSizes.take 1)`, so the two disagree whenever the "
            "block has ≥2 extents with a non-unit later one. Verifying would be "
            "SPEC-TOO-WEAK (the block count would be unpinned beyond the first "
            "extent). Refuted at reducedSizes=[2,3], missing=0, required=3, "
            "remainingDimCount=1: first-axis count 2 < 3 flags it, whole-block "
            "count 6 ≥ 3 does not."
        ),
        "witness": _tester(
            "example : reductionMissingDecisionTester [2,3] 0 3 1 0 false false = false := by\n"
            "  decide\n"),
        # Attacks the SHAPED-OUTPUT arm, which the frozen impl computes with a
        # `while` loop whose fixpoint the kernel cannot unfold — a `decide`
        # against gold is stuck for every claim, so gold cannot serve as the
        # refutation subject. Refuted against the verifying loop-free reference
        # instead; measured, `decide` there PROVES the claim false (a real
        # refutation, not a stuck reduction).
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-two-axes-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Subtler partial-domain: product of only the FIRST TWO extents
        # (`reducedSizes.take 2`). Correct for one- or two-dimension reductions;
        # UNDERCOUNTS for three or more with a non-unit third extent — exactly the
        # F2P 3-dimension shape. A near-miss the first-axis rival does not subsume:
        # first-axis already diverges at two extents, this one agrees with gold
        # there and only diverges at three.
        "module": _impl(
            "    if remainingDimCount ≥ 1 then\n"
            "      return Except.ok (decide (prodList (reducedSizes.take 2) < missingCount + requiredCount))\n"
            "    else\n"
            "      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))"),
        "refinement": (
            "a count over only the first two collapsed extents would, on the "
            "3-dimension failing scenario, compute shape[x]*shape[y] instead of "
            "shape[x]*shape[y]*shape[z] — undercounting the block by the factor "
            "shape[z]>1, flagging cells the full-block reduction keeps, so the "
            "multi-dimension result diverges from the reference reduction. It would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from the shaped-output arm: the arm pins the product over ALL "
            "extents, this rival over a two-extent prefix, so they disagree whenever "
            "the block has ≥3 extents with a non-unit third. Verifying would be "
            "SPEC-TOO-WEAK (the count would pin only a prefix of the extents). "
            "Refuted at reducedSizes=[1,2,3] (a THREE-extent block, the F2P shape), "
            "missing=0, required=4, remainingDimCount=2: prefix count 1*2=2 < 4 "
            "flags it, whole-block count 6 ≥ 4 does not. Distinct from the "
            "first-axis rival, which agrees with gold on a two-extent block."
        ),
        "witness": _tester(
            "example : reductionMissingDecisionTester [1,2,3] 0 4 2 0 false false = false := by\n"
            "  decide\n"),
        # Shaped-output arm: gold's `while` loop cannot decide (see
        # `_LOOPFREE`). Refuted against the verifying loop-free reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-reject-on-sequence",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch guard: a reduction whose dimensions were named as a SEQUENCE
        # is REJECTED outright (Except.error) rather than producing a decision. This
        # is the exact pre-patch skeleton (Solution_prepatch.lean's do-block). The
        # frozen spec pins `out = Except.ok ..` for EVERY reduction, so it is caught
        # on any input with axisWasSequence = true.
        "module": _impl(
            "    if axisWasSequence then\n"
            "      return Except.error ()\n"
            "    else\n"
            "      if remainingDimCount ≥ 1 then\n"
            "        return Except.ok (decide (prodList reducedSizes < missingCount + requiredCount))\n"
            "      else\n"
            "        return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))"),
        "refinement": (
            "this reinstates the removed guard that rejected a multi-dimension "
            "reduction outright — the exact pre-patch behaviour the issue reports "
            "as a bug. On the failing multi-dimension scenario it raises instead of "
            "returning a value, so the operation errors where the reference "
            "reduction returns a result: it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the `out = Except.ok ..` wrapper: the spec produces a "
            "decision for EVERY reduction independent of `axisWasSequence`, and "
            "this rival returns `Except.error ()` on the sequence branch. Verifying "
            "would be SPEC-TOO-WEAK (the always-produce-a-decision guarantee "
            "unpinned). Refuted at axisWasSequence=true (with remainingDimCount=0, "
            "totalSize=5, required=3, fillAdmissible false — the single-value arm "
            "would return `ok false`, but the rival errors). This is the ONLY rival "
            "that moves `axisWasSequence` to true."
        ),
        "witness": _tester(
            "example : reductionMissingDecisionTester [] 0 3 0 5 true true = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-array-boundary-le",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on the shaped-output boundary: `≤` where the spec demands the
        # strict `<`. Right whole-block product, wrong comparator — flags the cell
        # whose present count is EXACTLY the requirement, which the spec keeps. A
        # near-miss distinct from the prefix-count rivals (correct product, wrong
        # boundary).
        "module": _impl_flatproof(
            "    if remainingDimCount ≥ 1 then\n"
            "      return Except.ok (decide (prodList reducedSizes ≤ missingCount + requiredCount))\n"
            "    else\n"
            "      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))"),
        "refinement": (
            "a `≤` boundary additionally flags the cell whose present count equals "
            "the requirement exactly. The failing scenario uses a positive "
            "requirement and a real patch with `≤` would null out cells that have "
            "EXACTLY the required number of present values — which the reference "
            "reduction keeps — so the multi-dimension result diverges from it. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the shaped-output arm's strict boundary: `cellMissing` "
            "flags iff `prodList reducedSizes < missingCount + requiredCount`, this "
            "rival iff `≤`, so they disagree at the boundary "
            "`prodList reducedSizes = missingCount + requiredCount`. Verifying "
            "would leave the strict boundary unpinned (SPEC-TOO-WEAK). Refuted at "
            "reducedSizes=[2,3] (product 6), missing=3, required=3, "
            "remainingDimCount=1: present count is exactly 3 = required, so `<` "
            "keeps the cell (6 < 6 false) and `≤` flags it (6 ≤ 6 true)."
        ),
        "witness": _tester(
            "example : reductionMissingDecisionTester [2,3] 3 3 1 0 false false = false := by\n"
            "  decide\n"),
        # Shaped-output arm: gold's `while` loop cannot decide (see
        # `_LOOPFREE`). Refuted against the verifying loop-free reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-marker-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-value arm: DROP the `fillAdmissible` marker gate, always flagging
        # on the short-count comparison. Correct whenever the representation admits
        # a marker (fillAdmissible = true); wrong for a representation that CANNOT
        # carry one, where the cell must never be flagged.
        "module": _impl(
            "    if remainingDimCount ≥ 1 then\n"
            "      let mut total : Nat := 1\n"
            "      let mut i := reducedSizes.length\n"
            "      while i > 0\n"
            "        invariant 0 ≤ i ∧ i ≤ reducedSizes.length\n"
            "        invariant total = prodList (reducedSizes.drop i)\n"
            "        done_with i = 0\n"
            "        decreasing i\n"
            "      do\n"
            "        let s := reducedSizes[i - 1]!\n"
            "        total := s * total\n"
            "        i := i - 1\n"
            "      return Except.ok (decide (total < missingCount + requiredCount))\n"
            "    else\n"
            "      return Except.ok (decide (totalSize - missingCount < requiredCount))"),
        "refinement": (
            "dropping the marker-representation gate on the single-value branch "
            "flags a cell as missing even when the result's representation cannot "
            "carry a missing marker — for such a representation the operation must "
            "leave the value untouched. The failing scenario includes exactly such "
            "a representation, where the reference reduction returns the value "
            "rather than a fill; this rival would replace it, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the single-value arm's `fillAdmissible &&` conjunct: the "
            "spec flags only when the representation admits a marker AND the count "
            "is short, this rival flags on the count alone, so they disagree "
            "whenever fillAdmissible = false and the count is short. Verifying "
            "would be SPEC-TOO-WEAK (the marker gate unpinned). Refuted at "
            "remainingDimCount=0, totalSize=5, missing=4, required=3, "
            "fillAdmissible=false: present count 1 < 3, but the gate forbids "
            "flagging (spec `false`), while the rival flags (`true`). The only "
            "rival driving the single-value arm with fillAdmissible = false and a "
            "short count."
        ),
        "witness": _tester(
            "example : reductionMissingDecisionTester [] 4 3 0 5 false false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-scalar-boundary-le",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on the SINGLE-VALUE boundary: `≤` where the spec demands `<`.
        # Keeps the marker gate; flags the value whose present count is EXACTLY the
        # requirement. Distinct from drop-marker-gate (which is wrong only when the
        # gate is closed) — this is wrong at the boundary with the gate OPEN.
        "module": _impl(
            "    if remainingDimCount ≥ 1 then\n"
            "      let mut total : Nat := 1\n"
            "      let mut i := reducedSizes.length\n"
            "      while i > 0\n"
            "        invariant 0 ≤ i ∧ i ≤ reducedSizes.length\n"
            "        invariant total = prodList (reducedSizes.drop i)\n"
            "        done_with i = 0\n"
            "        decreasing i\n"
            "      do\n"
            "        let s := reducedSizes[i - 1]!\n"
            "        total := s * total\n"
            "        i := i - 1\n"
            "      return Except.ok (decide (total < missingCount + requiredCount))\n"
            "    else\n"
            "      return Except.ok (fillAdmissible && decide (totalSize - missingCount ≤ requiredCount))"),
        "refinement": (
            "a `≤` boundary on the single-value branch additionally flags the value "
            "whose present count equals the requirement exactly. The failing "
            "scenario uses a positive requirement, and a real patch with `≤` would "
            "null out an all-dimensions result that has EXACTLY the required number "
            "of present values — which the reference reduction keeps — so the "
            "result diverges. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the single-value arm's strict boundary: `cellMissing` "
            "flags iff `totalSize - missingCount < requiredCount` (under the marker "
            "gate), this rival iff `≤`, disagreeing at the boundary "
            "`totalSize - missingCount = requiredCount`. Verifying would leave the "
            "scalar strict boundary unpinned (SPEC-TOO-WEAK). Refuted at "
            "remainingDimCount=0, totalSize=6, missing=3, required=3, "
            "fillAdmissible=true: present count 3 = required, so `<` keeps it "
            "(3 < 3 false) and `≤` flags it (3 ≤ 3 true). Exercises the "
            "single-value arm with the marker gate OPEN, unlike drop-marker-gate."
        ),
        "witness": _tester(
            "example : reductionMissingDecisionTester [] 3 3 0 6 true false = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 2 partial-domain uniqueness
# rivals: first-axis-only and first-two-axes-only) plus a 2-case AXIOM lane. This
# bundle models a WIDER decision surface than the sibling's single `flag_too_few`
# bool: velvet's `reductionMissingDecision` contracts BOTH reduction branches
# (shaped-output `remainingDimCount ≥ 1` and single-value `= 0`), the
# marker-representation gate `fillAdmissible`, and the always-produce-a-decision
# guarantee (`out = Except.ok ..` independent of `axisWasSequence`). So the port
# GAINS rivals against the branches and clauses nagini's narrower model did not
# have. Every sibling case is accounted for.
#
#   sibling case (nagini)                 kind          -> here
#   -------------------------------------------------------------------------
#   pos-control-reorder-local-bool        soundness     -> pos-direct-product        RE-EXPRESSED
#   pos-control-commuted-accumulate       soundness     -> pos-scalar-if-form        RE-EXPRESSED
#   admiss-f2p-three-axes                 admissibility -> admiss-postimage-nondeg.   RE-AIMED
#   frame-mutation-self-store             uniqueness    -> (none)                     VACUOUS
#   reject-prepatch-first-axis-only       uniqueness    -> weak-first-axis-only       PORTED
#   reject-first-two-axes-only            uniqueness    -> weak-first-two-axes-only   PORTED
#   reject-off-by-one-le-zero             uniqueness    -> weak-array-boundary-le     PORTED
#   AXIOM_TESTS (2)                       axiom         -> (none)                     DROPPED (G-AX)
#
#   ADDED (no sibling counterpart — attack surface this wider model introduces):
#     weak-reject-on-sequence   — the pre-patch multi-dimension REJECTION guard.
#         The sibling has no `Except` return (its `flag_too_few` returns a bare
#         bool and the deleted `raise` was not a separate observable in its value
#         abstraction; see the sibling's CONTROL-FLOW-EFFECT note). Velvet models
#         the raise as `Except.error` and pins `out = Except.ok ..` for EVERY
#         reduction, so the pre-patch guard IS a refutable rival here. This is the
#         single rival that moves `axisWasSequence`.
#     weak-drop-marker-gate     — drop the `fillAdmissible` conjunct on the
#         single-value branch. The sibling does not model the scalar branch or the
#         dtype/marker guard at all (its P1 is the array-branch product only), so
#         this clause has no sibling counterpart.
#     weak-scalar-boundary-le   — the strict `<` boundary on the single-value
#         branch (the scalar analogue of the sibling's off-by-one, on the branch
#         the sibling does not model).
#
# RE-EXPRESSED (positives): the sibling's two positives reshape a Nagini loop
#   (reorder pre-loop assignments / commute the multiply) around a fractional-
#   permission fold. Neither shape is expressible here; the ARGUMENT ("a
#   structurally different but faithful impl must verify") is carried by reshapes
#   that ARE expressible on this carrier: eliminate the loop entirely for the
#   direct pure product (pos-direct-product) and rewrite the marker gate as an
#   `if` (pos-scalar-if-form). Both build (one keeps the frozen proof, one retunes
#   it to the loop-free script) — verified with real builds.
# RE-AIMED (admissibility): the sibling self-calls to discharge its precondition
#   (R0-R3) at the F2P-shaped 3-axis input. This bundle declares NO `require`
#   clause, so precondition admission is vacuous; the case is re-aimed at the
#   residual total-domain risk that the post-image is DEGENERATE, discharging an
#   in-region assert that the F2P-shaped 3-extent block [4,3,2] is counted WHOLE
#   (product 24, not the first extent 4) — the exact behaviour the fix introduces.
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because `sizes` is
#   held at `Acc(list_pred(sizes),1/2)` an impl can illegally overwrite. This
#   backend is referentially transparent, declares no `mut` binder among the
#   inputs, and has no heap or aliasing — there is no read-only field to mutate
#   and no substitute probe. Not fabricated (porting map: vacuous here).
# DROPPED (AXIOM_TESTS): the sibling's axiom lane probes the `prod` deep model
#   (A-reference) against the real `np.take(shape,axis).prod()`. The axiom lane is
#   G-AX's job (mapping.md §3 / axiom_check.py); this gate ignores AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause has two top-level arms of
#   `cellMissing` plus the `out = Except.ok ..` wrapper. The shaped-output arm is
#   attacked by weak-first-axis-only, weak-first-two-axes-only and
#   weak-array-boundary-le; the single-value arm by weak-drop-marker-gate and
#   weak-scalar-boundary-le; the always-ok wrapper by weak-reject-on-sequence. Six
#   reject witnesses at six DISTINCT input points (pts=6). Across them:
#     remainingDimCount: {1,2,0,1,0,0}      — both arms exercised
#     reducedSizes:      {[2,3],[1,2,3],[],[2,3],[],[]}  — empty and lengths 2,3
#     missingCount:      {0,0,0,3,4,3}      — varied
#     requiredCount:     {3,4,3,3,3,3}      — {3,4}
#     totalSize:         {0,0,5,0,5,6}      — varied on the single-value arm
#     fillAdmissible:    {false,false,false,false,false,true}  — both values
#     axisWasSequence:   {false,false,true,false,false,false}  — both values
#   Every binder the post-image depends on is moved by some witness while the
#   discrimination for that rival comes from the named clause; `axisWasSequence`
#   (on which the spec is DELIBERATELY independent) is nonetheless probed to true
#   by weak-reject-on-sequence, which is exactly the rival that would exploit a
#   spec that allowed rejection on it. The near-misses do NOT share witnesses with
#   the coarser rivals: first-two-axes agrees with first-axis's refutation regime
#   at two extents (so it is refuted at three), and each boundary rival is refuted
#   at its own exactly-at-boundary point where the coarser rivals agree with gold.
#
# AXIOM_TESTS: dropped (G-AX lane). This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
