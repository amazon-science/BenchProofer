"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-20859 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so ``markers.same_spec``
holds and every ``theorem correct_<name>`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with every
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); it
carries over that battery's adversarial ARGUMENT and re-expresses it against this
backend's carrier. It is not a translation of the nagini text.

DEFENDED SURFACE (one total dispatch over a 4-way kind carrier)
---------------------------------------------------------------
A single modeled function classifies the parent an object is attached to and
decides three things at once:

  resolveLegendParent (p : Parent) : Except Unit (Bool × Nat)

  * an axes-kind parent yields ``ok (true, ownerFigureId)`` — an axes-level
    outcome recording the surface the axes belongs to;
  * a non-axes canvas-kind parent (top-level surface OR an embedded sub-surface,
    both recognised by ``isCanvasKind``) yields ``ok (false, selfId)`` — a
    non-axes outcome recording the parent object itself;
  * a parent that is neither is rejected (``error ()``).

The load-bearing clauses of ``problem_spec_resolveLegendParent`` (three
independent implications, all pinned for every input):

  (C1)  isAxesKind = true  → result = ok (true, ownerFigureId)
  (C2)  isAxesKind = false → isCanvasKind = true  → result = ok (false, selfId)
  (C3)  isAxesKind = false → isCanvasKind = false → result = error ()

WHAT DRIVES THE REJECTS. (C2) is the discriminating clause: it fires for BOTH
canvas kinds, so a dispatch that recognises only the top-level surface leaves the
embedded sub-surface falling through to (C3)'s reject path — exactly the defect
the gold change repairs (the narrow kind-test widened to the common canvas base).
The remaining rivals attack the value slots each clause pins: the boolean flag
and the recorded-identity ``Nat`` in each arm.

BINDER / CLAUSE COVERAGE. The spec predicate has three input binders —
``p.kind`` (drives which clause fires), ``p.selfId`` (pinned by C2's ``Nat``),
``p.ownerFigureId`` (pinned by C1's ``Nat``). The reject rivals vary the kind
across ALL FOUR constructors — ``axes`` / ``topCanvas`` / ``subCanvas`` /
``other`` — and attack, between them, every clause and BOTH value slots (the
boolean and the ``Nat``) of each of C1 and C2 plus C3's ``error`` outcome:

  * ``rival-prepatch-narrow`` — kind ``subCanvas``: the second arm tests the
    narrow top-level kind instead of canvas membership, so the embedded
    sub-surface falls to the reject path. Violates C2 (and C3's converse). This
    is the actual gold-repaired defect.
  * ``rival-canvas-narrow-mirror`` — kind ``topCanvas``: the MIRROR-image narrow
    test — the second arm recognises only the embedded sub-surface, so the
    TOP-LEVEL surface falls to the reject path. Violates C2 at the one kind no
    other rival refutes at, so C2 is pinned POINTWISE over both canvas kinds
    rather than merely at one of them.
  * ``rival-fam-wrong-canvas`` — kind ``subCanvas``: the canvas arm records
    ``ownerFigureId`` instead of ``selfId``. Violates C2's ``Nat`` slot; probes
    the ``selfId`` binder.
  * ``rival-canvas-flag-true`` — kind ``subCanvas``: the canvas arm returns the
    flag ``true``. Violates C2's BOOLEAN slot — the one value slot the rivals
    above leave unattacked (they pin C2's ``Nat`` and C1's boolean, never C2's).
  * ``rival-coord-flag-flip`` — kind ``axes``: the axes arm returns the flag
    ``false``. Violates C1's boolean slot.
  * ``rival-axes-wrong-figure`` — kind ``axes``: the axes arm records ``selfId``
    instead of ``ownerFigureId``. Violates C1's ``Nat`` slot; probes the
    ``ownerFigureId`` binder (the one the flag-flip holds correct).
  * ``rival-over-accept-foreign`` — kind ``other``: drops the reject arm and
    treats a non-canvas, non-axes parent as canvas-kind. Violates C3.
  * ``rival-input-coerce`` — kind ``other`` (and ``axes``): rebinds the input to
    a COERCED copy whose kind is canvas-like before classifying, so the dispatch
    answers about a fabricated parent rather than the given one. This is the
    lean counterpart of the sibling battery's read-only-input attack; see the
    porting notes below.

Each ``Nat``-slot rival is refuted at an input where ``selfId ≠ ownerFigureId``,
so the two identity binders are genuinely separated — a rival that confused the
two fields would be caught by ``rival-fam-wrong-canvas`` / ``rival-axes-wrong-
figure`` even though C1 and C2 differ only in which field they name.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
dispatch's exact elaboration — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet proving the
rival CONTRADICTS the spec at a concrete input — at TWO inputs, as a conjunction,
for ``rival-input-coerce``, whose rationale claims two different clause
violations and whose single-input witness would leave the second one unproven
prose. The carrier is fully
transparent (a 4-constructor ``ParentKind`` enum with ``Nat`` identities; no
``opaque`` callee), so each witness states the spec predicate directly at literal
field values and reduces the dispatch with ``simp`` (``decide`` cannot synthesise
a ``Decidable`` instance for the propositional implications, but ``simp`` on the
kind-tests and ``Id.run``/``pure`` closes the goal — see the note in
spec_guide on ``decide`` getting stuck). Each was checked with two real builds to
ELABORATE against its rival and to FAIL on the frozen solution, so each
discriminates rather than asserting a tautology. No witness binds a hypothesis
(all inputs are literal), so there is no consistency obligation.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models the dispatch under fractional permissions over a mutable
``parent`` object whose ``.tag`` heap cell is held read-only. This lean carrier is
referentially transparent and models the parent as pure data (a ``Parent``
structure with a ``ParentKind`` field and two ``Nat`` identities). The
correspondence and omissions:

  * nagini's (P-fam) — the discriminating "every canvas-family member returns a
    normal outcome recording the parent itself" clause — ↦ (C2) here, attacked by
    ``rival-prepatch-narrow`` (the narrow kind-test that drops the embedded
    sub-surface, i.e. nagini's ``rival-prepatch-narrow``) and by
    ``rival-fam-wrong-canvas`` (nagini's family-branch-wrong-canvas).
  * nagini's (P-coord) coords-flag/canvas clause ↦ (C1), attacked by
    ``rival-coord-flag-flip`` (flag) and ``rival-axes-wrong-figure`` (the recorded
    identity — a value slot nagini's flag-flip carried implicitly through its
    canvas argument; here it is a separate rival so the ``ownerFigureId`` binder
    is independently probed).
  * nagini's (P-norm)/(P-exs) foreign-reject guard ↦ (C3), attacked by
    ``rival-over-accept-foreign``.
  * nagini's two positive controls (branch-reorder, local-variable reshape) ↦
    ``pos-branch-reorder`` / ``pos-local-var-reshape`` here — structurally
    different but correct impls whose ``correct_resolveLegendParent`` proof still
    closes with the frozen tactic body (the two canvas kinds are mutually
    exclusive with the axes kind over ``ParentKind``, so reordering is
    behaviour-preserving; the ``let``-bind is definitionally transparent).
  * nagini's ``admiss-nested-parent`` ↦ ``admiss-ground-instance``: the frozen
    obligation carries NO precondition hypothesis (the modeled behavior is total),
    so there is no precondition binder to attack; the honest analogue discharges
    the spec predicate at a concrete F2P-shaped input (an embedded sub-surface
    parent — exactly the kind the F2P attaches a legend to) by evaluation, inside
    the proof region, alongside the frozen obligation.
  * FRAME / PERMISSION MUTATION (nagini ``rival-frame-mutate``, MANDATORY there)
    ↦ ``rival-input-coerce``. The PERMISSION MECHANISM is indeed vacuous here —
    Lean is referentially transparent, so there is no heap cell, no aliasing and
    no half-permission to overwrite, and nothing can be rejected for INSUFFICIENT
    PERMISSION. But the ATTACK the nagini case encodes is not about permissions:
    it is "coerce the input into a friendlier kind, then answer about the coerced
    value instead of the given one", and that IS expressible on a pure carrier by
    SHADOWING the input binder (``let p := { p with kind := .topCanvas }``) before
    the dispatch. The frozen spec reads its clauses off the ORIGINAL ``p``, so the
    coercion is observable and refutable — the rival answers ``ok (false, selfId)``
    for a foreign parent (violating C3) and for an axes parent (violating C1).
    Landed as a real rival with a real witness, per spec_guide §5 (frame
    discipline translates to pinning the result against the INPUT value).
  * DIVERGENCE / non-termination — a KNOWN HOLE, not a vacuous class. The port's
    original claim ("a diverging implementation cannot be written at all") is
    FALSE and was corrected here after measurement: ``partial def spinForever
    (n : Nat) : Except Unit (Bool × Nat) := spinForever (n + 1)`` is admissible
    inside the impl region (``partial`` is banned in a witness, not in a variant
    impl), it passes ``variant_scope``, and routing the reject arm into it is
    genuinely REJECTED — the frozen obligation cannot be closed, leaving
    ``⊢ spinForever selfId = Except.error ()`` (measured: rival exit 1).
    So the rival itself is real and the spec does require the reject arm to
    return.

    What cannot be built is an admissible WITNESS for it, and the obstruction is
    structural rather than a proof difficulty. A ``partial def`` is opaque to the
    kernel, so the refutation must be stated at a point described by hypothesis,
    which forces the witness to name ``spinForever`` — a name the frozen solution
    does not declare. Both available routes were measured:

      - naming ``spinForever``: rival exit 0, gold exit 1, but gold's error is
        ``Function expected at spinForever`` — an unknown name, i.e. exactly the
        syntactic non-discriminator the witness rule exists to reject. The gate
        screens this outright (``witness references ['spinForever'] — declared by
        the variant but not by the frozen solution``) and records the case
        MALFORMED, and a ``witness_reference`` does not help: that check is made
        against the FROZEN solution, never against the reference.
      - phrasing the hypothesis only over shared vocabulary (about
        ``implementation_resolveLegendParent`` itself): elaborates against BOTH
        the rival and gold (exit 0/0), i.e. ``witness-vacuous`` — the hypothesis
        is unsatisfiable for gold, so it proves nothing.

    Recorded as a hole in the WITNESS harness (the spec is fine; the divergence
    rival is refutable in principle but not expressible under the current
    variant-only-name rule), not as a vacuous class and not as a spec defect.

AXIOM lane: the nagini ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's job
and this gate ignores it. (The subtype relation the nagini axiom-containment probe
validated is modeled here deeply as the transparent ``isAxesKind`` / ``isCanvas
Kind`` predicates over ``ParentKind``; there is no ``opaque`` answer-key to echo,
so the spec is grounded structurally in ``p.kind`` and there is nothing to attack
in an axiom lane.)
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20859"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The whole dispatch body inside the impl region (for the reorder / local-var /
# over-accept variants that reshape the entire ladder).
_IMPL_BODY = (
    "  if isAxesKind p.kind then\n"
    "    return .ok (true, p.ownerFigureId)\n"
    "  else if isCanvasKind p.kind then\n"
    "    return .ok (false, p.selfId)\n"
    "  else\n"
    "    return .error ()"
)

# The axes arm return (impl region) — for the flag-flip and wrong-figure rivals.
_AXES_RET = "return .ok (true, p.ownerFigureId)"

# The canvas arm return (impl region) — for the wrong-canvas rival.
_CANVAS_RET = "return .ok (false, p.selfId)"

# The canvas-kind guard (impl region) — for the prepatch-narrow rival and its
# mirror image.
_CANVAS_GUARD = "else if isCanvasKind p.kind then"

# The proof head down to `intro p` (proof region) — for the admissibility ground
# instance, which inserts a `have` before `intro p`.
_PROOF_HEAD = (
    "theorem correct_resolveLegendParent :\n"
    "    ∀ (p : Parent),\n"
    "      problem_spec_resolveLegendParent p (implementation_resolveLegendParent p) := by\n"
    "  intro p"
)


# ---- witness helper ---------------------------------------------------------
# The carrier is fully transparent, so a witness states the spec predicate at a
# concrete Parent literal and reduces the dispatch with `simp` on the kind-tests
# and the `Id.run`/`pure` monad. Literal inputs only => no bound hypothesis, so
# no consistency obligation.

def _lit(kind, self_id, owner_id):
    return ("{ kind := ." + kind + ", selfId := " + str(self_id)
            + ", ownerFigureId := " + str(owner_id) + " }")


def _wit(kind, self_id, owner_id):
    lit = _lit(kind, self_id, owner_id)
    return (
        f"example : ¬ problem_spec_resolveLegendParent\n"
        f"    {lit}\n"
        f"    (implementation_resolveLegendParent\n"
        f"      {lit}) := by\n"
        f"  unfold problem_spec_resolveLegendParent implementation_resolveLegendParent\n"
        f"  simp [isAxesKind, isCanvasKind, Id.run, pure]\n"
    )


def _wit2(a, b):
    """A witness refuting the spec at TWO concrete inputs, as a conjunction.

    For a rival whose rationale claims violations of two DIFFERENT clauses, a
    single-input witness demonstrates only one of them; the second clause is then
    prose the manifest never proves. Both conjuncts must elaborate against the
    rival and the conjunction must fail on the frozen solution, so each claimed
    clause is machine-checked rather than asserted.
    """
    def clause(t):
        lit = _lit(*t)
        return (f"(¬ problem_spec_resolveLegendParent\n      {lit}\n"
                f"      (implementation_resolveLegendParent\n        {lit}))")
    return (
        f"example :\n    {clause(a)}\n    ∧ {clause(b)} := by\n"
        f"  refine ⟨?_, ?_⟩ <;>\n"
        f"    unfold problem_spec_resolveLegendParent implementation_resolveLegendParent <;>\n"
        f"    simp [isAxesKind, isCanvasKind, Id.run, pure]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify (else the spec is over-fit => SPEC-TOO-
    # STRONG). Each keeps the `theorem correct_resolveLegendParent` statement
    # byte-identical; the frozen proof (case split on the four kinds + simp) still
    # closes each shape, so no helper lemma, no axiom, no assumption token.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Classify canvas-kind FIRST, then axes in the else-if. The axes kind and
        # the two canvas kinds are mutually exclusive over ParentKind, so the same
        # arm fires on every input and the outcome is unchanged.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  if isCanvasKind p.kind then\n"
            "    return .ok (false, p.selfId)\n"
            "  else if isAxesKind p.kind then\n"
            "    return .ok (true, p.ownerFigureId)\n"
            "  else\n"
            "    return .error ()",
        ),
        "rationale": "branch-REORDER positive control: canvas membership classified "
                     "first, axes in the else-if. The axes kind and the two canvas "
                     "kinds are mutually exclusive over ParentKind, so behaviour is "
                     "identical on every input. Must verify; else SPEC-TOO-STRONG "
                     "(a correct restructured dispatch rejected). Proof: the frozen "
                     "per-kind case split + simp closes the reordered ladder.",
    },
    {
        "id": "pos-local-var-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Bind each arm's outcome to a local `let` before returning it: same
        # values, a different executable shape for the return.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  if isAxesKind p.kind then\n"
            "    let out := Except.ok (true, p.ownerFigureId)\n"
            "    return out\n"
            "  else if isCanvasKind p.kind then\n"
            "    let out2 := Except.ok (false, p.selfId)\n"
            "    return out2\n"
            "  else\n"
            "    return .error ()",
        ),
        "rationale": "local-variable reshape positive control: bind each arm's "
                     "Except outcome to a local then return it, instead of returning "
                     "the constructor inline. Same values, different executable "
                     "shape; the `let` is definitionally transparent so every clause "
                     "obligation is discharged unchanged. Must verify; else "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body closes it.",
    },

    {
        "id": "pos-match-no-monad",
        "kind": "soundness",
        "expect": "verify",
        # Drop the imperative monad entirely: a total `match` on the kind, one
        # arm per constructor, no `Id.run do`, no early `return`, and neither
        # kind-test predicate mentioned. The most structurally distant correct
        # shape available on this carrier.
        "module": _swap(
            _BASE,
            "def implementation_resolveLegendParent\n"
            "    (p : Parent) : Except Unit (Bool × Nat) := Id.run do\n" + _IMPL_BODY,
            "def implementation_resolveLegendParent\n"
            "    (p : Parent) : Except Unit (Bool × Nat) :=\n"
            "  match p.kind with\n"
            "  | .axes => .ok (true, p.ownerFigureId)\n"
            "  | .topCanvas => .ok (false, p.selfId)\n"
            "  | .subCanvas => .ok (false, p.selfId)\n"
            "  | .other => .error ()",
        ),
        "rationale": "the structurally MOST distant correct reshape: a per-"
                     "constructor `match` with no `Id.run do` monad, no early "
                     "`return`, and neither `isAxesKind` nor `isCanvasKind` "
                     "appearing in the impl at all — it enumerates the four kinds "
                     "directly. Behaviour is identical on every input (verified "
                     "against the frozen dispatch by evaluation on all four kinds). "
                     "This is the real SPEC-TOO-STRONG probe: the two reshapes above "
                     "keep the frozen ladder's guard structure, so only this one "
                     "shows the spec constrains BEHAVIOUR rather than the frozen "
                     "impl's syntactic form. Must verify; else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at a normal, F2P-shaped input rather than only provable in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the modeled
    # behavior is total), so the nagini precondition-admission probe has no binder
    # to attack; the honest analogue discharges the spec predicate at a ground
    # embedded-sub-surface input (the exact kind the F2P attaches a legend to) by
    # evaluation, inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_HEAD,
            "theorem correct_resolveLegendParent :\n"
            "    ∀ (p : Parent),\n"
            "      problem_spec_resolveLegendParent p (implementation_resolveLegendParent p) := by\n"
            "  have _ground : problem_spec_resolveLegendParent\n"
            "      { kind := .subCanvas, selfId := 7, ownerFigureId := 3 }\n"
            "      (implementation_resolveLegendParent\n"
            "        { kind := .subCanvas, selfId := 7, ownerFigureId := 3 }) := by\n"
            "    unfold problem_spec_resolveLegendParent implementation_resolveLegendParent\n"
            "    simp [isAxesKind, isCanvasKind, Id.run, pure]\n"
            "  intro p",
        ),
        "rationale": "the dispatch obligation is discharged at a ground embedded-"
                     "sub-surface input (kind subCanvas — the F2P attaches a legend "
                     "to exactly this kind) by evaluation, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior is unsatisfiable at the normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, and the ground "
                     "instance is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the frozen
    # spec that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival is a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "rival-prepatch-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        # The second arm tests the NARROW top-level kind instead of canvas
        # membership, so an embedded sub-surface falls through to the reject arm.
        "module": _swap(_BASE, _CANVAS_GUARD,
                        "else if p.kind = ParentKind.topCanvas then"),
        "refinement": "this is the pre-patch narrow kind-test (only the top-level "
                      "surface is accepted). It rejects an embedded sub-surface, so "
                      "attaching a legend to that sub-surface raises the documented "
                      "TypeError and the F2P test_subfigure_legend FAILS — the exact "
                      "bug the gold change fixes by widening the test to the common "
                      "canvas base. The rival does not resolve.",
        "rationale": "REJECT from (C2): for an embedded sub-surface isCanvasKind "
                     "holds so the spec requires ok (false, selfId), but the narrow "
                     "test sends it to the reject arm (error ()). A verifying narrow "
                     "rival => SPEC-TOO-WEAK (the discriminating widening not "
                     "enforced).",
        "witness": _wit("subCanvas", 7, 3),
    },
    {
        "id": "rival-canvas-narrow-mirror",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR of the narrow test: the second arm recognises only the
        # EMBEDDED sub-surface, so the top-level surface falls to the reject arm.
        "module": _swap(_BASE, _CANVAS_GUARD,
                        "else if p.kind = ParentKind.subCanvas then"),
        "refinement": "a narrow second arm that recognises only the embedded "
                      "sub-surface would reject the TOP-LEVEL drawing surface, so "
                      "every existing surface-level legend would raise the "
                      "documented TypeError — breaking the top-level-surface-parent "
                      "P2P tests (TestLegendFigureFunction::test_legend_no_args, "
                      "::test_legend_handle_label, ..., test_cross_figure_patch_"
                      "legend) while still accepting the sub-surface the F2P uses. "
                      "The rival does not resolve.",
        "rationale": "REJECT from (C2) at kind topCanvas — the kind NO other rival "
                     "refutes at. isCanvasKind holds for the top-level surface so "
                     "the spec requires ok (false, selfId), but this narrow test "
                     "sends it to the reject arm (error ()). Together with "
                     "rival-prepatch-narrow this pins C2 POINTWISE over BOTH canvas "
                     "kinds: neither arm may be narrowed in either direction. A "
                     "verifying mirror rival => SPEC-TOO-WEAK (C2 pinned at only "
                     "one of its two kinds).",
        "witness": _wit("topCanvas", 7, 3),
    },
    {
        "id": "rival-fam-wrong-canvas",
        "kind": "uniqueness",
        "expect": "reject",
        # The canvas arm records ownerFigureId instead of the parent's own
        # identity (selfId).
        "module": _swap(_BASE, _CANVAS_RET, "return .ok (false, p.ownerFigureId)"),
        "refinement": "models recording the parent's OWNING surface identity in the "
                      "canvas arm instead of the parent object itself; for an "
                      "embedded sub-surface parent the recorded figure would be the "
                      "owning surface, NOT the sub-surface — so the F2P assertion "
                      "`leg.figure is subfig` FAILS. The rival does not resolve.",
        "rationale": "REJECT from (C2)'s Nat slot: the canvas arm must record selfId "
                     "(the parent itself); this records ownerFigureId. Refuted at an "
                     "input where selfId ≠ ownerFigureId. A verifying rival => "
                     "SPEC-TOO-WEAK on the recorded-identity slot.",
        "witness": _wit("subCanvas", 8, 2),
    },
    {
        "id": "rival-canvas-flag-true",
        "kind": "uniqueness",
        "expect": "reject",
        # The canvas arm returns the axes-level flag TRUE.
        "module": _swap(_BASE, _CANVAS_RET, "return .ok (true, p.selfId)"),
        "refinement": "models setting the axes-level flag for a canvas-like parent; "
                      "the legend would claim to be an axes legend while recording a "
                      "drawing surface, so the downstream code that branches on that "
                      "flag would look for an owning axes that does not exist. Both "
                      "the sub-surface F2P and the figure-parent P2P tests break. "
                      "The rival does not resolve.",
        "rationale": "REJECT from (C2)'s BOOLEAN slot — the one value slot the other "
                     "rivals leave unattacked: they pin C2's Nat (fam-wrong-canvas) "
                     "and C1's boolean (coord-flag-flip), but nothing pinned C2's "
                     "flag. A canvas-like parent must yield ok (false, _); this "
                     "yields ok (true, _). A verifying rival => SPEC-TOO-WEAK on the "
                     "non-axes flag.",
        "witness": _wit("subCanvas", 7, 3),
    },
    {
        "id": "rival-coord-flag-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # The axes arm returns the flag false.
        "module": _swap(_BASE, _AXES_RET, "return .ok (false, p.ownerFigureId)"),
        "refinement": "a real patch that set the axes-level flag false for an axes "
                      "parent would mis-classify every axes legend (it would not "
                      "know its owning axes), breaking the axes-parent P2P tests "
                      "(test_legend_remove, test_legend_text_axes, ...). The rival "
                      "does not resolve.",
        "rationale": "REJECT from (C1)'s boolean slot: an axes parent must yield "
                     "ok (true, _); this yields ok (false, _). Refuted at an axes "
                     "input. A verifying flag-flip => SPEC-TOO-WEAK on the axes "
                     "flag.",
        "witness": _wit("axes", 5, 9),
    },
    {
        "id": "rival-axes-wrong-figure",
        "kind": "uniqueness",
        "expect": "reject",
        # The axes arm records the parent's own identity (selfId) instead of the
        # owning-surface identity (ownerFigureId).
        "module": _swap(_BASE, _AXES_RET, "return .ok (true, p.selfId)"),
        "refinement": "models recording the axes object's OWN identity in the axes "
                      "arm instead of the surface the axes belongs to; the recorded "
                      "figure would be the axes, not its owning surface, so the "
                      "recorded-figure invariant the axes-parent tests rely on "
                      "breaks. The rival does not resolve.",
        "rationale": "REJECT from (C1)'s Nat slot: an axes parent must record "
                     "ownerFigureId; this records selfId. Refuted at an input where "
                     "selfId ≠ ownerFigureId — pins the ownerFigureId binder that "
                     "the flag-flip holds correct. A verifying rival => "
                     "SPEC-TOO-WEAK on the axes recorded-identity slot.",
        "witness": _wit("axes", 1, 2),
    },
    {
        "id": "rival-over-accept-foreign",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the reject arm: treat anything non-axes as canvas-kind.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  if isAxesKind p.kind then\n"
            "    return .ok (true, p.ownerFigureId)\n"
            "  else\n"
            "    return .ok (false, p.selfId)",
        ),
        "refinement": "a real patch dropping the `else: raise TypeError` would let a "
                      "genuinely non-canvas, non-axes object silently build a broken "
                      "legend instead of raising the documented TypeError; the "
                      "dispatch must REJECT such a parent. The rival does not resolve "
                      "(wrong behaviour on a foreign parent).",
        "rationale": "REJECT from (C3): a parent that is neither axes nor canvas-kind "
                     "must yield error (); this over-accepts it as ok (false, _). "
                     "Refuted at kind = other. A verifying over-accept => "
                     "SPEC-TOO-WEAK on the foreign-reject guard.",
        "witness": _wit("other", 4, 6),
    },
    {
        "id": "rival-input-coerce",
        "kind": "uniqueness",
        "expect": "reject",
        # Shadow the input binder with a COERCED copy whose kind is canvas-like,
        # then run the frozen ladder verbatim on the coerced value. The lean
        # counterpart of the sibling battery's read-only-input attack: no heap to
        # write, but the binder can still be re-bound before it is classified.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let p := { p with kind := ParentKind.topCanvas }\n" + _IMPL_BODY,
        ),
        "refinement": "models coercing the parent into an accepted kind (rebinding "
                      "it to a fabricated top-level surface) instead of classifying "
                      "the parent actually passed in — the dodge that makes the "
                      "kind-test always succeed. The recorded surface would then be "
                      "the fabricated object, not the parent, so the F2P's "
                      "recorded-surface identity assertion FAILS, and a foreign "
                      "parent would be silently accepted instead of raising the "
                      "documented TypeError. The rival does not resolve.",
        "rationale": "REJECT from (C1) and (C3): every clause of the frozen spec is "
                     "read off the ORIGINAL p, so answering about a coerced copy is "
                     "observable. At kind = other the spec requires error () but the "
                     "coerced dispatch returns ok (false, selfId) (C3 violated); at "
                     "kind = axes the spec requires ok (true, ownerFigureId) but the "
                     "coercion suppresses the axes arm entirely (C1 violated). This "
                     "is the FRAME-DISCIPLINE case (spec_guide §5) — the sibling "
                     "battery's read-only-input rival, re-expressed as binder "
                     "shadowing because a pure carrier has no heap cell to "
                     "overwrite. A verifying coerce rival => SPEC-TOO-WEAK (the "
                     "result not pinned against the INPUT value).",
        # Two-input witness: this rival's rationale claims BOTH a C3 and a C1
        # violation, and a single-input witness at kind=other proves only the C3
        # half — the C1 claim would be unproven prose. The conjunction refutes at
        # kind=other (C3: spec requires error (), rival answers ok (false, selfId))
        # AND at kind=axes (C1: spec requires ok (true, ownerFigureId), but the
        # coercion suppresses the axes arm and answers ok (false, selfId)). Each
        # conjunct elaborates against the rival; the conjunction fails on gold.
        "witness": _wit2(("other", 4, 6), ("axes", 5, 9)),
    },
]
