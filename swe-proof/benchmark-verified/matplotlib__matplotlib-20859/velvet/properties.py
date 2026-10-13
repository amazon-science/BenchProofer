"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-20859 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides — so
``markers.same_spec`` holds and the ``prove_correct anchorToParent`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a single read-only input):

  anchorToParent (parent : Container) return (out : Except AnchorErr Anchor)
    ensures out = anchorSpec parent                                      (C1)

  ``parent`` is the sole INPUT binder. It is one of three observable shapes:
  a plotting region (carrying its owning canvas), a figure-like canvas (of
  EITHER kind — a top-level canvas or a nested sub-canvas, distinguished by a
  boolean), or anything else. ``anchorSpec`` is a TRANSPARENT total function of
  the shape, with three independent legs:

      region c    →  ok { fromRegion := true,  canvas := c }   (bind to owner)
      canvas i _  →  ok { fromRegion := false, canvas := i }   (bind to itself,
                                                                either kind)
      other       →  error unsupportedParent                   (reject)

  C1 pins the WHOLE result: the origin flag (``fromRegion`` — did the parent
  come from a plotting region), the bound-canvas identity (``canvas``), AND
  which leg fires on which shape (region vs canvas vs rejection). Crucially the
  canvas leg fires on a figure-like canvas of EITHER kind: the boolean that
  distinguishes a top-level canvas from a nested sub-canvas does NOT gate
  acceptance. That is the discriminating behaviour the public issue reports — a
  nested sub-canvas parent must be accepted on the same footing as a top-level
  one rather than rejected. The post-image is grounded entirely in the sole
  input (``anchorSpec`` is a concrete ``def`` in the ``pure`` region, not an
  axiomatized oracle), so a wrong impl cannot verify by echoing an answer-key;
  it must reproduce the dispatch.

CARRIER NOTE — why every witness here refutes at CONCRETE literals. The whole
carrier is transparent and decidable: ``Container``, ``Anchor`` and
``AnchorErr`` all derive ``DecidableEq``, and the two Nat/Bool payloads compute.
So a witness reaches the rival's extracted program (``anchorToParentExec`` =
``NonDetT.run ∘ anchorToParent``) at a CONCRETE ``parent`` value and states that
its result differs from ``anchorSpec parent`` there, closing by ``simp`` after
unfolding the branch predicates — no hypothesis about an opaque term is needed,
so no witness binds anything and the gate's consistency probe has nothing to
check (there are no assumptions to be inconsistent). The frozen solution is
straight-line and reduces under the same script, but the witness FAILS against
gold because gold SATISFIES the spec at that input (``simp`` leaves an unsolved
``¬(x = x)``), which is the required discriminator. Checked in a file whose
``prove_correct`` block is stripped, so no tactic script can mask the verdict.
Every reject witness below was SEEN to discriminate with THREE real builds:
elaborates against the rival, FAILS against the frozen solution with a residual
goal of exactly ``False``, and — the build the gate cannot run — the OPPOSITE
claim (that the extracted program AGREES with the spec at that input, which is
true of gold) ELABORATES under the same simp set, which is what shows gold's
failure was a refutation rather than a stuck unfolding. Each rival module was
also confirmed NOT to verify, with a semantic residual goal. See the ``_witness``
docstring for why the simp set has to cover GOLD's reached predicates too.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION (nagini's MANDATORY #4) — SPLIT, and the live
    half is CARRIED (see ``rival-substitute-parent``). The nagini sibling holds
    the input at a fractional heap permission (``Acc(parent.tag, 1/2)``) and its
    mandatory rival writes back into that read-only field to trip INSUFFICIENT
    PERMISSION. The PERMISSION mechanism is genuinely vacuous here: Lean/Velvet
    are referentially transparent, ``parent`` is an immutable value, this bundle
    declares NO ``mut`` binder, and there is no heap, no aliasing and no
    permission system to trip, so nothing can be made to fail for
    insufficient-permission reasons. But the sibling rival's BEHAVIOURAL content
    is not about permissions — it is "stop classifying the caller's input and
    classify something of the impl's own choosing instead", and that is a pure
    value transformation which states directly on this carrier: shadow the input
    binder with a fabricated container just above the dispatch, leaving the
    dispatch ladder byte-verbatim. So the substitute probe the earlier accounting
    called unbuildable IS buildable, and it is built rather than argued. It
    attacks the one facet every value rival takes for granted: the others all
    read ``parent`` faithfully and err in the MAPPING, so none of them tests that
    the sole input is consulted at all.
  * ADMISSIBILITY — PARTLY vacuous, and the live part is CARRIED (see
    ``admiss-nested-parent``). The method carries NO ``require`` clause
    (precondition ≡ True), so there is genuinely no precondition to be
    over-strong and no PRECOND-TOO-STRONG probe to build; every ``parent``
    (including the nested sub-canvas the F2P attaches to) is in scope by
    construction. What a total precondition does NOT dispose of is the residual
    risk that the post-image is DEGENERATE at the discriminating input — that
    ``out = anchorSpec parent`` is satisfied there by a collapse rather than by
    the intended acceptance. That is expressible on this carrier as an in-region
    ``assert`` at concrete values, so it is stated rather than argued: the
    admissibility case pins all three legs at concrete points (a nested
    sub-canvas is ACCEPTED and bound to its own identity, a region is accepted
    and bound to its OWNING canvas, a foreign parent is rejected), which is both
    satisfiability and non-degeneracy. Its assert is live: the same case with a
    FALSE claim was built and failed.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent total function
    of the sole input (``anchorSpec`` is a concrete ``def``, not an axiomatized
    oracle); the ``axioms`` region is empty (the membership tests are modeled
    deeply and validated by G-AX as an A-reference — mapping.md §3).

See the footer for the full nagini→velvet accounting.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20859"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both facts asserted
# ---- at load by _swap). The FULL frozen impl body (for the whole-body reshapes)
# ---- and the individual dispatch fragments (for the surgical reject rivals).
_GOLD_IMPL = """    let parentIsRegion : Bool := isRegion parent
    let parentIsCanvas : Bool := isCanvas parent
    let out : Except AnchorErr Anchor :=
      if parentIsRegion then
        Except.ok { fromRegion := true, canvas := regionCanvas parent }
      else
        if parentIsCanvas then
          Except.ok { fromRegion := false, canvas := canvasId parent }
        else
          Except.error .unsupportedParent
    return out"""
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# The BROAD canvas-membership binding of the second dispatch arm — anchor for the
# narrow-test rival (swap the broad test for the narrow one).
_GOLD_CANVAS_TEST = "    let parentIsCanvas : Bool := isCanvas parent\n"
assert _BASE.count(_GOLD_CANVAS_TEST) == 1, "canvas-test anchor drifted"

# The PAIR of membership-test bindings that open the dispatch — anchor for the
# input-substitution rival, which shadows `parent` with a fabricated value
# immediately before them so every test below reads the fabrication instead of
# the real input.
_GOLD_TESTS = """    let parentIsRegion : Bool := isRegion parent
    let parentIsCanvas : Bool := isCanvas parent"""
assert _BASE.count(_GOLD_TESTS) == 1, "membership-test pair anchor drifted"

# The region-branch return — anchor for the origin-flag-flip rival.
_GOLD_REGION_RET = "Except.ok { fromRegion := true, canvas := regionCanvas parent }"
assert _BASE.count(_GOLD_REGION_RET) == 1, "region-return anchor drifted"

# The canvas-branch return — anchor for the wrong-bound-canvas rival.
_GOLD_CANVAS_RET = "Except.ok { fromRegion := false, canvas := canvasId parent }"
assert _BASE.count(_GOLD_CANVAS_RET) == 1, "canvas-return anchor drifted"

# The whole inner branch (canvas arm + rejection arm) — anchor for the
# over-accept rival, which drops the rejection.
_GOLD_INNER = """        if parentIsCanvas then
          Except.ok { fromRegion := false, canvas := canvasId parent }
        else
          Except.error .unsupportedParent"""
assert _BASE.count(_GOLD_INNER) == 1, "inner-branch anchor drifted"

# ---- proof-body anchor. The frozen tactic script (`cases parent <;> simp_all
# ---- [...]`) is tuned to the frozen nested-if impl. A positive control that
# ---- reshapes the impl into a form that tactic no longer closes may RETUNE the
# ---- body (elided from the consumer spec view) WITHOUT touching the spec or
# ---- dropping the obligation — the `prove_correct anchorToParent` header
# ---- statement stays byte-identical. Unique in the file.
_GOLD_PROOF = """prove_correct anchorToParent by
  loom_solve
  cases parent <;>
    simp_all [anchorSpec, isRegion, isCanvas, regionCanvas, canvasId]"""
assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted; update _GOLD_PROOF"


def _reject(old, new):
    """Full Solution.lean variant with only an impl fragment replaced (spec view
    and frozen proof untouched — the rival's rejection is carried by its
    witness, not by whether the frozen tactic happens to break on the reshape)."""
    return _swap(_BASE, old, new)


# ---- witness builder. Reaches the rival's extracted program through Velvet's
# ---- extractor (`extract_program_for` gives `anchorToParentExec`, which is
# ---- `NonDetT.run (anchorToParent parent)` and reduces to `DivM.res out`) and
# ---- states, at a CONCRETE `parent`, that the rival's output differs from
# ---- `anchorSpec parent`. Closed by `simp` after unfolding the branch
# ---- predicates on the transparent carrier. Binds nothing (literal input), so
# ---- the gate's consistency probe is a no-op. Checked in a file whose
# ---- `prove_correct` block is stripped; no `sorry`/`admit`/`native_decide`/
# ---- `axiom`.
#
# SIMP-SET COMPLETENESS (audit repair). The `simp_extra` list must unfold every
# branch predicate reached on BOTH sides of the discrimination check, not merely
# the ones the rival's own dispatch consults. A set sufficient for the rival but
# short of a predicate GOLD's dispatch reaches leaves the gold-side goal stuck
# with that predicate un-unfolded rather than reduced to `False`: gold still
# exits nonzero, so the case still records "rejected", but the failure is an
# UNFOLDING artifact and attests to nothing about the spec. Measured directly:
# with such a set the exact OPPOSITE claim (`anchorToParentExec inp = DivM.res
# (anchorSpec inp)` — TRUE of gold) also fails to build, so gold's exit code
# carries no information. Each set below is therefore the UNION of the
# predicates the rival and the frozen impl both reach at that input, and each was
# re-checked against a three-build control: the refutation ELABORATES against the
# rival, FAILS against gold with a residual goal of exactly `False`, and the
# opposite (true) claim about gold ELABORATES — which is what makes the gold-side
# failure a refutation rather than a stuck reduction.
def _witness(inp, simp_extra):
    return (
        "extract_program_for anchorToParent\n\n"
        f"example : anchorToParentExec ({inp})\n"
        f"    ≠ DivM.res (anchorSpec ({inp})) := by\n"
        "  unfold anchorToParentExec anchorToParent\n"
        f"  simp [NonDetT.run, pure, anchorSpec, {simp_extra}]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the clause is SPEC-TOO-STRONG. Each keeps the
    # byte-identical obligation statement; only the executable surface (and, for
    # the match reshape, the elided tactic body) is changed. Both verified
    # out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: classify the figure-like-canvas case FIRST, then the region
        # case in the else. The three shapes are mutually exclusive (a region is
        # not a canvas), so the computed outcome is identical on every leg. The
        # frozen `cases parent <;> simp_all` proof closes for this order unchanged
        # (kept verbatim).
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let parentIsCanvas : Bool := isCanvas parent\n"
            "    let out : Except AnchorErr Anchor :=\n"
            "      if parentIsCanvas then\n"
            "        Except.ok { fromRegion := false, canvas := canvasId parent }\n"
            "      else\n"
            "        if isRegion parent then\n"
            "          Except.ok { fromRegion := true, canvas := regionCanvas parent }\n"
            "        else\n"
            "          Except.error .unsupportedParent\n"
            "    return out"),
        "rationale": "branch-REORDER positive control: the figure-like-canvas case "
                     "is classified first, the region case in the else. The three "
                     "shapes are mutually exclusive, so behaviour is identical and "
                     "C1 (`out = anchorSpec parent`) still holds on every leg. The "
                     "frozen proof closes unchanged. Must verify, else "
                     "SPEC-TOO-STRONG on the dispatch order. (Sibling: "
                     "pos-branch-reorder.)",
    },
    {
        "id": "pos-match-dispatch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: replace the nested-if guard ladder over the boolean membership
        # tests with a direct `match` on the parent shape, returning the outcome
        # inline per constructor. Same values, structurally different executable
        # shape (no intermediate boolean lets). `loom_solve` discharges the
        # obligation directly for this shape, so the tactic body is retuned to
        # bare `loom_solve` (elided from the spec view); the obligation statement
        # is byte-identical.
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL,
                  "    let out : Except AnchorErr Anchor :=\n"
                  "      match parent with\n"
                  "      | .region c   => Except.ok { fromRegion := true,  canvas := c }\n"
                  "      | .canvas i _ => Except.ok { fromRegion := false, canvas := i }\n"
                  "      | .other      => Except.error .unsupportedParent\n"
                  "    return out"),
            _GOLD_PROOF,
            "prove_correct anchorToParent by\n  loom_solve"),
        "rationale": "match-dispatch positive control: the nested-if ladder over "
                     "the boolean membership tests is rewritten as a direct `match` "
                     "on the parent shape (no intermediate boolean locals). Same "
                     "values, structurally different shape; C1 holds by "
                     "construction of `anchorSpec`. The tactic body is retuned to "
                     "bare `loom_solve` (elided from the spec view); the obligation "
                     "statement is untouched. Must verify, else SPEC-TOO-STRONG. "
                     "(Sibling: pos-local-var-reshape.)",
    },

    # =====================================================================
    # ADMISSIBILITY (audit repair — the sibling's admiss-nested-parent, which the
    # port had recorded N/A). The port's reasoning was that with no `require`
    # clause there is no PRECOND-TOO-STRONG probe to build, which is true as far
    # as it goes; but the sibling case ALSO pins the residual admissibility risk
    # that survives a total precondition — that the post-image is NON-DEGENERATE
    # at a concrete F2P-shaped input, i.e. it genuinely ACCEPTS the nested
    # sub-canvas and binds it to ITSELF rather than collapsing. That IS
    # expressible here, as an in-region `assert` at concrete inputs, so the
    # omission was not forced by the carrier. Landed: the assert pins all three
    # legs at concrete points (nested sub-canvas accepted and bound to its own
    # identity; region accepted and bound to its OWNING canvas; foreign
    # rejected), which additionally rules out the degenerate reading where the
    # post-image is constant. The impl is kept byte-verbatim so the method's own
    # `ensures` still discharges; only the tactic body is retuned (to clear the
    # extra assert goal), and that body is elided from the consumer spec view, so
    # the obligation statement stays byte-identical. The assert is LIVE, not
    # decoration: the same case with a FALSE claim (the nested sub-canvas is
    # REJECTED) was built and FAILED with an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-nested-parent",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL,
                  "    assert (with_name_prefix `admiss\n"
                  "      (anchorSpec (Container.canvas 1 false)\n"
                  "         = Except.ok { fromRegion := false, canvas := 1 } ∧\n"
                  "       anchorSpec (Container.region 7)\n"
                  "         = Except.ok { fromRegion := true, canvas := 7 } ∧\n"
                  "       anchorSpec Container.other"
                  " = Except.error .unsupportedParent))\n"
                  + _GOLD_IMPL),
            _GOLD_PROOF,
            "prove_correct anchorToParent by\n"
            "  loom_solve\n"
            "  all_goals cases parent <;>\n"
            "    simp_all [anchorSpec, isRegion, isCanvas, regionCanvas, canvasId]"),
        "rationale": "ADMISSIBILITY at a concrete F2P-shaped input. The method "
                     "carries no `require`, so there is no precondition that "
                     "could exclude an input; what this pins is the residual "
                     "risk a total precondition leaves — that the post-image is "
                     "NON-DEGENERATE at the discriminating point. The assert "
                     "states that at a nested sub-canvas C1 demands ACCEPTANCE "
                     "bound to that canvas's own identity (not rejection, not a "
                     "constant), and pins the region and foreign legs at "
                     "concrete points too, so `out = anchorSpec parent` is "
                     "satisfiable and genuinely shape-dependent rather than "
                     "collapsing. The impl is verbatim so the method's own "
                     "obligation still discharges; only the elided tactic body "
                     "is retuned to clear the assert goal. Must verify, else "
                     "PRECOND-TOO-STRONG / a degenerate post-image. (Sibling: "
                     "admiss-nested-parent.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each carrying a machine-checked refutation witness
    # at a DISTINCT concrete `parent` (discriminated by the whole result value)
    # and the refinement argument for why its faithful real counterpart would NOT
    # resolve the failing test. The seven witnesses probe SIX distinct `parent`
    # points spanning all three Container shapes and both canvas kinds (pts=6).
    # =====================================================================
    {
        "id": "rival-prepatch-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug: the second dispatch arm tests the NARROW top-level-canvas
        # membership instead of the BROAD figure-like-canvas membership, so a
        # nested sub-canvas falls through to the rejection. Correct on a region /
        # a top-level canvas / a foreign parent; diverges ONLY on a nested
        # sub-canvas.
        "module": _reject(_GOLD_CANVAS_TEST,
                          "    let parentIsCanvas : Bool := isTopCanvas parent\n"),
        "refinement": "this is the pre-patch narrow membership test, which accepts "
                      "only a top-level canvas and so rejects a nested sub-canvas "
                      "with the unsupported-parent error — exactly the reported "
                      "bug. The F2P scenario attaches to a nested sub-canvas, so it "
                      "would still raise and the failing test would FAIL. The rival "
                      "does not resolve.",
        "rationale": "REJECT from C1 on the canvas leg: for a nested sub-canvas "
                     "`anchorSpec` demands `ok { fromRegion := false, canvas := i }` "
                     "but the narrow test routes it to the rejection. Refuted at "
                     "`parent = canvas 1 false` (a nested sub-canvas): the rival "
                     "errors where the post-image demands acceptance — the "
                     "nested-canvas sub-domain no other rival isolates. Verifying "
                     "would be SPEC-TOO-WEAK. (Sibling: rival-prepatch-narrow.)",
        # `isCanvas`/`canvasId` are in the set because GOLD's dispatch reaches
        # them at this input even though the rival's does not: without them the
        # gold-side goal stalls at an un-unfolded `isCanvas (canvas 1 false)`
        # instead of reducing to `False`, and the opposite (true) claim about
        # gold fails to build too — i.e. gold's exit code would discriminate
        # nothing. With them, gold's residual goal is exactly `False`.
        "witness": _witness("Container.canvas 1 false",
                            "isRegion, isCanvas, isTopCanvas, canvasId"),
    },
    {
        "id": "rival-region-flag-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # On the region branch, report the origin flag as `false` (as if the
        # parent were a figure-like canvas rather than a plotting region), while
        # keeping the bound canvas correct. Correct on the canvas/foreign shapes;
        # wrong exactly on a region parent's origin flag.
        "module": _reject(
            _GOLD_REGION_RET,
            "Except.ok { fromRegion := false, canvas := regionCanvas parent }"),
        "refinement": "a counterpart that recorded a plotting-region parent as NOT "
                      "originating from a region would mis-classify every "
                      "region-parented anchor (it would not know its owning "
                      "region), breaking the unchanged tests that anchor to a "
                      "plotting region and observe that origin. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 on the region leg: for a region parent "
                     "`anchorSpec` pins `fromRegion := true`, while the rival "
                     "returns `false`. Refuted at `parent = region 7`: the origin "
                     "flag is wrong. This abuses the region shape (the only shape "
                     "with `fromRegion := true`), a sub-domain the canvas/foreign "
                     "rivals do not reach. Verifying would be SPEC-TOO-WEAK on the "
                     "origin flag. (Sibling: rival-coord-flag-flip.)",
        "witness": _witness("Container.region 7", "isRegion, regionCanvas"),
    },
    {
        "id": "rival-canvas-wrong-binding",
        "kind": "uniqueness",
        "expect": "reject",
        # On the canvas branch, bind the child to the WRONG identity
        # (`regionCanvas parent`, which is 0 off the region shape) instead of the
        # canvas's own identity. Origin flag stays correct; the bound-canvas
        # identity is wrong for any canvas whose own identity is non-zero.
        "module": _reject(
            _GOLD_CANVAS_RET,
            "Except.ok { fromRegion := false, canvas := regionCanvas parent }"),
        "refinement": "a counterpart that bound a figure-like-canvas parent to some "
                      "other canvas identity instead of the parent itself would "
                      "attach the anchor to the wrong canvas — the F2P asserts the "
                      "anchored artist's canvas IS the sub-canvas parent, so with a "
                      "mismatched identity that assertion FAILS. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 on the canvas leg's identity field: "
                     "`anchorSpec` pins `canvas := i` (the parent canvas's own "
                     "identity), while the rival returns an unrelated identity. "
                     "Refuted at `parent = canvas 3 true` (a top-level canvas): the "
                     "bound canvas is 0 where the post-image demands 3. This abuses "
                     "the canvas-identity binder (discriminates only when the "
                     "identity is non-zero) at the OTHER canvas kind (top-level), so "
                     "the battery moves the canvas-kind boolean across "
                     "{false, true}. Verifying would be SPEC-TOO-WEAK on the "
                     "bound-canvas identity. (Sibling: rival-fam-wrong-canvas.)",
        "witness": _witness("Container.canvas 3 true",
                            "isRegion, isCanvas, canvasId, regionCanvas"),
    },
    {
        "id": "rival-over-accept-foreign",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the rejection arm: treat ANY non-region parent as a figure-like
        # canvas and bind it, so a foreign parent is silently accepted instead of
        # rejected. Correct on region/canvas shapes; wrong exactly on a foreign
        # parent.
        "module": _reject(
            _GOLD_INNER,
            "        Except.ok { fromRegion := false, canvas := canvasId parent }"),
        "refinement": "a counterpart that dropped the unsupported-parent rejection "
                      "would silently build a broken anchor from any object instead "
                      "of raising the documented error — the dispatch must REJECT a "
                      "foreign parent, which the unchanged tests observing that "
                      "rejection require. It would NOT resolve.",
        "rationale": "REJECT from C1 on the rejection leg: for a foreign parent "
                     "`anchorSpec` demands `error unsupportedParent`, while the "
                     "rival returns an `ok` anchor. Refuted at `parent = other`: the "
                     "rival accepts where the post-image demands rejection — the "
                     "foreign-reject sub-domain no other rival exercises. Verifying "
                     "would be SPEC-TOO-WEAK on the foreign-reject guard. (Sibling: "
                     "rival-over-accept-foreign.)",
        # `isCanvas` is in the set because GOLD's dispatch reaches it at this
        # input (the rival dropped that test): without it the gold-side goal
        # stalls at an un-unfolded `isCanvas Container.other = true` instead of
        # reducing to `False`, and the opposite (true) claim about gold fails to
        # build too — i.e. gold's exit code would discriminate nothing. With it,
        # gold's residual goal is exactly `False`.
        "witness": _witness("Container.other", "isRegion, isCanvas, canvasId"),
    },
    # ---- added by audit: two legs C1 pins that the ported four leave
    # ---- unattacked. Both were written as fresh wrong impls, confirmed NOT to
    # ---- verify, and given witnesses seen to discriminate with three builds
    # ---- (rival elaborates, gold fails with residual goal `False`, the opposite
    # ---- true claim about gold elaborates).
    {
        "id": "rival-region-wrong-binding",
        "kind": "uniqueness",
        "expect": "reject",
        # The region leg's IDENTITY field: bind a region parent to `canvasId`
        # (0 off the canvas shape) instead of its OWNING canvas. The ported
        # rivals attack the region leg's flag and the canvas leg's identity, but
        # nothing attacks the region leg's identity — the one field that
        # distinguishes "bound to the region's owner" from "bound to nothing".
        "module": _reject(
            _GOLD_REGION_RET,
            "Except.ok { fromRegion := true, canvas := canvasId parent }"),
        "refinement": "a counterpart that bound a region parent to some unrelated "
                      "canvas instead of the region's own owning canvas would "
                      "anchor every region-parented child to the wrong canvas, "
                      "breaking the unchanged tests that anchor to a plotting "
                      "region and then observe which canvas the child landed on. "
                      "It would NOT resolve.",
        "rationale": "REJECT from C1 on the region leg's identity field: for a "
                     "region parent `anchorSpec` pins `canvas := c` (the region's "
                     "OWNING canvas), while the rival returns 0. Refuted at "
                     "`parent = region 7`: the bound canvas is 0 where the "
                     "post-image demands 7 — the region-identity facet no ported "
                     "rival reaches (region-flag-flip moves only the flag, and "
                     "the canvas rivals never enter this leg). Verifying would be "
                     "SPEC-TOO-WEAK on the region-leg binding.",
        "witness": _witness("Container.region 7",
                            "isRegion, regionCanvas, canvasId"),
    },
    {
        "id": "rival-kind-leaks-into-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # The canvas leg reports the origin flag as the canvas KIND boolean, so a
        # nested sub-canvas (false) is right by accident while a TOP-LEVEL canvas
        # is wrong. The mirror of the ported flag rival: it makes the boolean that
        # must NOT gate behaviour observable in the result, which is the precise
        # failure mode the reported issue is about — the two canvas kinds must be
        # treated on the same footing.
        "module": _reject(
            _GOLD_CANVAS_RET,
            "Except.ok { fromRegion := isTopCanvas parent,"
            " canvas := canvasId parent }"),
        "refinement": "a counterpart that let the canvas KIND decide the origin "
                      "flag would mark a top-level canvas parent as though it had "
                      "come from a plotting region, mis-classifying every "
                      "top-level-canvas anchor while leaving the nested case "
                      "looking correct. The unchanged tests that anchor to a "
                      "top-level canvas and observe that origin would break, so "
                      "it would NOT resolve.",
        "rationale": "REJECT from C1 on the canvas leg's origin flag, at the "
                     "canvas kind the ported rivals leave correct: `anchorSpec` "
                     "pins `fromRegion := false` for a canvas of EITHER kind, "
                     "while the rival returns the kind boolean. Refuted at "
                     "`parent = canvas 5 true` (a top-level canvas), where it "
                     "reports `true`; it is accidentally right at a nested "
                     "sub-canvas, so this is a partial-domain rival isolating the "
                     "'the kind boolean must not be observable in the result' "
                     "facet. Verifying would be SPEC-TOO-WEAK on the "
                     "kind-independence of the canvas leg.",
        "witness": _witness("Container.canvas 5 true",
                            "isRegion, isCanvas, isTopCanvas, canvasId"),
    },
    # ---- added by a second audit: the value-level analogue of the sibling's
    # ---- MANDATORY read-only-input rival, which this port had recorded as
    # ---- wholly VACUOUS. The PERMISSION half is genuinely vacuous (no heap, no
    # ---- fractional permission, nothing to trip), but the sibling rival's
    # ---- BEHAVIOURAL content — discard the caller's input and dispatch on a
    # ---- fabricated stand-in instead — is a pure-value transformation that
    # ---- states directly on this carrier, and was landed rather than argued.
    {
        "id": "rival-substitute-parent",
        "kind": "uniqueness",
        "expect": "reject",
        # Shadow the input binder with a fabricated top-level canvas immediately
        # before the membership tests, so the whole dispatch classifies the
        # fabrication rather than the parent the caller passed. The dispatch
        # LADDER is byte-verbatim below the shadowing line, so the rejection is
        # attributable to the substitution alone. Wrong on every shape whose
        # image differs from the fabrication's: a region parent, a foreign
        # parent, and any canvas whose identity is non-zero.
        "module": _reject(
            _GOLD_TESTS,
            "    let parent : Container := Container.canvas 0 true\n"
            + _GOLD_TESTS),
        "refinement": "a counterpart that dispatched on a stand-in parent it "
                      "manufactured itself, rather than on the object the caller "
                      "handed it, would bind every child to that stand-in — the "
                      "F2P asserts the anchored artist's canvas IS the parent it "
                      "was constructed with, so a manufactured stand-in fails "
                      "that assertion, and the unchanged tests that anchor to a "
                      "plotting region or observe the foreign-parent rejection "
                      "break as well. It would NOT resolve.",
        "rationale": "REJECT from C1's GROUNDING in the sole input: `anchorSpec "
                     "parent` is a function of the parent actually supplied, so "
                     "an impl that classifies a value of its own making cannot "
                     "satisfy it except where the two happen to agree. Refuted "
                     "at `parent = region 9`: the rival returns the "
                     "fabrication's canvas image where the post-image demands "
                     "the region leg. This is the facet every other rival takes "
                     "for granted — the others all read `parent` correctly and "
                     "err in the mapping, so none of them tests that the input "
                     "is READ AT ALL. Verifying would be SPEC-TOO-WEAK in the "
                     "strongest available sense: the post-image would not "
                     "pin the result to the caller's own argument. (Sibling: "
                     "rival-frame-mutate, whose permission half is vacuous here "
                     "but whose behavioural half is this.)",
        "witness": _witness("Container.region 9",
                            "isRegion, isCanvas, canvasId, regionCanvas"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 4 uniqueness
# rivals) plus a 1-entry AXIOM lane. This bundle models the SAME single behaviour
# — the parent-dispatch of legend construction — as `anchorToParent` over the
# referentially-transparent carrier (`Container` -> `Except AnchorErr Anchor`).
# The nagini integer class-family tags {TAG_COORDS, TAG_TOPLEVEL, TAG_NESTED,
# TAG_FOREIGN} become the `Container` shapes {region, canvas _ true,
# canvas _ false, other}; `is_coords_artist`/`in_canvas_family` become
# `isRegion`/`isCanvas`; the `Attached(is_coords, canvas)` outcome becomes
# `Anchor { fromRegion, canvas }` (with rejection an `Except.error`). Every
# sibling SPEC case is accounted for below.
#
#   sibling case (nagini)         -> here                          status
#   ---------------------------------------------------------------------------
#   pos-branch-reorder             -> pos-branch-reorder            PORTED
#   pos-local-var-reshape          -> pos-match-dispatch            RE-SHAPED
#   admiss-nested-parent           -> admiss-nested-parent          PORTED (audit)
#   rival-frame-mutate (MANDATORY) -> rival-substitute-parent        PORTED (audit,
#                                                                    behavioural
#                                                                    half only)
#   rival-prepatch-narrow          -> rival-prepatch-narrow         PORTED (central)
#   rival-fam-wrong-canvas         -> rival-canvas-wrong-binding    PORTED
#   rival-coord-flag-flip          -> rival-region-flag-flip        PORTED
#   rival-over-accept-foreign      -> rival-over-accept-foreign     PORTED
#   (no sibling)                   -> rival-region-wrong-binding    ADDED (audit)
#   (no sibling)                   -> rival-kind-leaks-into-flag    ADDED (audit)
#   AXIOM_TESTS (1 entry)          -> (none)                        DROPPED (G-AX)
#
# 7 ported, 1 re-shaped, 0 omitted, 2 added = 10 cases here from 8 sibling cases.
# Every sibling SPEC case now has a counterpart; nothing is recorded vacuous.
#
# AUDIT AMENDMENTS (an independent audit re-derived every case; three changes):
#  1. admiss-nested-parent was recorded N/A and is now PORTED. The original
#     reasoning — no `require`, so no PRECOND-TOO-STRONG probe — is sound as far
#     as it goes, but the sibling case also pins the residual risk a total
#     precondition leaves (a DEGENERATE post-image at the discriminating input),
#     and that is expressible here as an in-region `assert` at concrete values.
#     Landed, with its liveness confirmed by building the same case with a FALSE
#     claim and seeing it fail.
#  2. Two reject witnesses had simp sets sufficient for their rival but missing a
#     predicate GOLD's dispatch reaches, so the gold-side build failed by STUCK
#     UNFOLDING rather than by refutation — measured by building the opposite
#     (true-of-gold) claim and watching it fail under the same set. Both sets were
#     completed; each now leaves gold's goal at exactly `False` while the
#     true-of-gold claim elaborates. See the `_witness` docstring.
#  3. Two rivals were added for C1 facets the ported four leave unattacked: the
#     region leg's IDENTITY field (rival-region-wrong-binding) and the
#     kind-independence of the canvas leg's origin flag
#     (rival-kind-leaks-into-flag).
#
# SECOND AUDIT (independent, re-derived every case rather than reading the first
# audit's record; one change):
#  4. The sibling's MANDATORY frame-mutation rival was recorded wholly VACUOUS,
#     on the reasoning that a referentially transparent carrier has "no read-only
#     input to overwrite and no substitute probe to build". The first clause is
#     right and the second is not: the rival's PERMISSION mechanism is indeed
#     inexpressible (no heap, no fractional permission), but its BEHAVIOURAL
#     content — dispatch on a value the impl manufactures instead of on the
#     caller's argument — is a pure value transformation, and it lands here by
#     shadowing the input binder above a byte-verbatim dispatch ladder. Landed as
#     rival-substitute-parent, with the full four-build matrix seen (rival 0,
#     gold 1 with residual goal exactly `False`, true-of-gold on gold 0,
#     true-of-gold on rival 1). This mattered beyond the accounting: it is the
#     only rival that tests C1's right-hand side is grounded in the caller's
#     argument at all, a facet the other six take for granted because they all
#     read `parent` faithfully and err only in the mapping. The MANDATORY lane is
#     therefore no longer empty on this cell.
#     Also re-derived and CONFIRMED, not changed: statement integrity on every
#     case (the `method ... ensures out = anchorSpec parent` header is
#     byte-identical in all of them, all diffs confined to the impl region plus,
#     for two cases, the elided tactic body); the admissibility case's liveness,
#     re-checked with TWO independent false-claim controls (the nested sub-canvas
#     asserted REJECTED, and the region asserted bound to canvas 0) which both
#     failed with an unsolved `admiss_1` goal; and amendment 2's hollow state,
#     reproduced from scratch by rebuilding a witness with the short simp set.
#
# PORTED (positives): the sibling's branch-reorder (classify family before
#   coords) ports directly to classifying the figure-like-canvas case before the
#   region case; the three shapes are mutually exclusive so behaviour is
#   identical, and the frozen `cases parent <;> simp_all` proof closes unchanged.
# RE-SHAPED (pos-local-var-reshape): the sibling stages the outcome through a
#   typed local before returning it. The structural analog on this carrier is to
#   drop the nested-if guard ladder over the boolean membership tests entirely
#   and dispatch by a direct `match` on the parent shape (no intermediate
#   locals); this reshapes the impl further from the frozen form, so the tactic
#   body is retuned to bare `loom_solve` (elided from the spec view) while the
#   obligation statement stays byte-identical.
# PORTED (rivals): all four sibling uniqueness rivals in the value lane port
#   directly, each attacking the same leg of the dispatch as on nagini (the fifth,
#   the MANDATORY frame rival, is accounted for separately below):
#    * rival-prepatch-narrow — the reported bug: the second arm tests the NARROW
#      top-level-canvas membership, so a nested sub-canvas is rejected. This is
#      the discriminating F2P behaviour.
#    * rival-fam-wrong-canvas -> rival-canvas-wrong-binding — the canvas branch
#      binds to the wrong canvas identity instead of the parent itself (the
#      bound-canvas-identity pin the F2P observes).
#    * rival-coord-flag-flip -> rival-region-flag-flip — the region branch reports
#      the wrong origin flag (the origin-flag pin).
#    * rival-over-accept-foreign — drop the rejection arm so a foreign parent is
#      silently accepted (the foreign-parent rejection guard).
# PORTED (admiss-nested-parent, landed by the audit): the sibling constructs a
#   concrete F2P-shaped nested parent and asserts the precondition/dispatch admit
#   it. HALF of that is genuinely vacuous here — this method carries NO `require`
#   clause (precondition ≡ True), so every `parent` including the nested
#   sub-canvas is in scope by construction and there is no PRECOND-TOO-STRONG
#   probe to build. The other half is NOT vacuous and is what the case now
#   carries: a total precondition still leaves the risk that the post-image is
#   DEGENERATE at the discriminating input (satisfied by a collapse rather than by
#   the intended acceptance), and on this carrier that is stateable directly as an
#   in-region `assert` over concrete `Container` values. The case asserts, at
#   concrete points, that a nested sub-canvas is ACCEPTED and bound to its own
#   identity, that a region is accepted and bound to its OWNING canvas, and that a
#   foreign parent is rejected — satisfiability AND non-degeneracy AND
#   shape-dependence in one obligation. The impl stays byte-verbatim so the
#   method's own `ensures` still discharges; only the elided tactic body is
#   retuned to clear the assert goal. The assert is live rather than decorative:
#   the same case with a FALSE claim (nested sub-canvas REJECTED) was built and
#   FAILED with an unsolved goal.
# PORTED (rival-frame-mutate, MANDATORY on nagini — landed by the second audit as
#   rival-substitute-parent): the sibling overwrites the read-only input
#   `parent.tag`, held at Acc(parent.tag, 1/2), to trip INSUFFICIENT PERMISSION
#   before any postcondition is considered. The MECHANISM is vacuous here and that
#   part of the original accounting stands: this backend is referentially
#   transparent, `parent` is an immutable value, this bundle declares NO `mut`
#   binder, and there is no heap, no aliasing and no permission system, so no
#   permission can be made insufficient. What the original accounting got WRONG is
#   the next sentence — that there is "no substitute probe to build". There is, and
#   it is now built. The sibling rival's behavioural content is that the impl
#   dispatches on a value of its own manufacture rather than on the caller's
#   argument; on a value carrier that is expressed by shadowing the input binder
#   with a fabricated `Container` immediately above the membership tests, leaving
#   the dispatch ladder byte-verbatim so the rejection is attributable to the
#   substitution alone. The earlier accounting was right that C1 refutes such an
#   impl — but "C1 would refute it" is an ARGUMENT, and this gate exists to
#   replace arguments with builds, so the case is carried with its own witness
#   (refuted at `parent = region 9`, seen to elaborate against the rival and to
#   fail against the frozen solution with a residual goal of exactly `False`,
#   with the opposite-claim control elaborating on gold). It is also the only rival
#   in the battery that tests that the sole input is READ at all: every other
#   rival reads `parent` faithfully and errs in the mapping.
# DROPPED (AXIOM_TESTS): the nagini bundle's single axiom-containment probe (the
#   real runtime type hierarchy agrees with the deep model over the caller-
#   reachable classes, and the discriminating "nested sub-canvas is a figure-like
#   canvas but not a top-level one" fact holds) belongs to the G-AX lane. This
#   bundle declares NO consumed `axiom` (the membership tests are modeled deeply
#   as `isRegion`/`isCanvas`/`isTopCanvas` and validated == the real callee by
#   G-AX as an A-reference — mapping.md §3). This gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. The sole input binder is `parent`; the single
#   top-level clause C1 (`out = anchorSpec parent`) folds several facets — which
#   leg fires (region / canvas / rejection), the origin flag, and the bound-canvas
#   identity. C1 is DEFENDED by the two positive controls and ATTACKED on every
#   leg, on BOTH of its fields:
#    * region leg — origin flag by rival-region-flag-flip, bound-canvas identity
#      by rival-region-wrong-binding (added by the audit);
#    * canvas leg — acceptance by rival-prepatch-narrow, bound-canvas identity by
#      rival-canvas-wrong-binding, and the KIND-INDEPENDENCE of its origin flag by
#      rival-kind-leaks-into-flag (added by the audit);
#    * rejection leg — by rival-over-accept-foreign;
#    * and the GROUNDING of C1's right-hand side in the caller's own argument —
#      i.e. that `parent` is consulted at all rather than replaced by a value the
#      impl manufactures — by rival-substitute-parent (added by the second audit,
#      the behavioural half of the sibling's MANDATORY frame rival). Every other
#      rival reads `parent` faithfully and errs in the mapping, so this facet was
#      the one no build covered.
#   `parent` is varied across SIX DISTINCT witness points (pts=6): region 7 and
#   region 9, canvas 1 false (a nested sub-canvas), canvas 3 true and canvas 5
#   true (two top-level canvases, at different identities), and other — spanning
#   all three Container shapes AND both values of the canvas-kind boolean, so no
#   rival is refuted at a pinned input and the boolean that gates the reported bug
#   is moved across {false, true}. The variation is MEANINGFUL rather than two
#   spellings of one point: each point is the sole input at which its rival's
#   output differs from `anchorSpec`, i.e. moving off it makes that rival agree
#   with the spec. The two region points are not a duplicate spelling either —
#   region 7 and region 9 refute DIFFERENT rivals, and the identity value is
#   load-bearing in each (at region 0 the region-identity rival would agree with
#   the spec, and the substitution rival is refuted by the region leg firing at
#   all rather than by the particular identity).
#
# WITNESS FORM. The carrier is fully transparent and decidable (`Container`,
#   `Anchor`, `AnchorErr` all derive `DecidableEq`; the Nat/Bool payloads
#   compute), so each witness refutes at a CONCRETE `parent` value: it reaches the
#   rival's extracted program `anchorToParentExec` and states its result differs
#   from `anchorSpec parent`, closing by `simp` after unfolding the branch
#   predicates. Every witness binds nothing (literal input), so the gate's
#   consistency probe is a no-op (no assumptions to be inconsistent).
#
#   Confirmed empirically with THREE real builds per reject case, not two. Two are
#   the gate's own: the witness ELABORATES against its rival, and FAILS against
#   the frozen solution. The third is the one the gate cannot run and the audit
#   added, because the two-build check reads gold's nonzero exit as "gold satisfies
#   C1 here" and that inference only holds if the build actually DECIDED anything:
#   build the OPPOSITE claim (`anchorToParentExec inp = DivM.res (anchorSpec inp)`,
#   which is TRUE of gold) under the same simp set and require it to ELABORATE. If
#   it does not, the refutation's gold-side failure was a stuck unfolding rather
#   than a refutation and the case attests to nothing — which is exactly what two
#   of these cases did before repair. All seven reject cases now pass all three:
#   rival exit 0, gold exit 1 with a residual goal of exactly `False`, and the
#   true-of-gold control exit 0. Each rival module was also separately confirmed
#   NOT to verify, with a semantic residual goal (a false value equation on the
#   attacked field) rather than a tactic-shape complaint.
#
#   A second independent audit re-ran that matrix from scratch on all seven,
#   adding a FOURTH build per case: the opposite claim against the RIVAL, which
#   must FAIL (the rival really does disagree at that point, so the agreement
#   claim is false there). All seven gave rival 0 / gold 1 / true-of-gold-on-gold
#   0 / true-of-gold-on-rival 1 — the full 2x2, which pins the gold-side exit as
#   tracking the CLAIM rather than the file. It also reconstructed the hollow
#   state amendment 2 describes, by rebuilding the prepatch witness with the
#   original short simp set: gold then failed with an un-unfolded
#   `isCanvas (Container.canvas 1 false)` goal AND the true-of-gold control failed
#   identically (both exit 1), so that amendment was a real repair and not a
#   cosmetic one.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. This
#   bundle consumes no `axiom` (the `axioms` region is empty — the membership
#   tests are modeled deeply and validated as an A-reference by G-AX), so there is
#   nothing here for this gate to probe.
AXIOM_TESTS = []
