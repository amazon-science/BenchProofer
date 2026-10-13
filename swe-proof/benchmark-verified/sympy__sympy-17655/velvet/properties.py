"""properties.py — G-PBT falsification battery for sympy__sympy-17655 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct scalePoint`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (``scalePoint (factor : Rat) (coords : List Rat)
return (out : List Rat)``):
  Scale an ordered coordinate sequence by a single numeric factor — every
  coordinate multiplied by the factor, in order, count preserved. Two input
  binders, ``factor`` (the scalar) and ``coords`` (the sequence), NO ``require``
  clause (the domain is total over the two values), and TWO independent
  top-level postcondition clauses:

    (P1) out = scaleCoords coords factor    the exact per-coordinate product
    (P2) out.length = coords.length         dimension preserved

  where ``scaleCoords coords factor = coords.map (· * factor)`` is a total,
  fully-unfolded pure ``def`` over the method's OWN inputs (the ``pure`` region).
  The ``axioms`` region is EMPTY — there is no opaque answer key to echo
  (directive 8: the post-image is grounded in the actual inputs), so the only
  satisfier of P1 is the honest per-coordinate multiply.

WHY THE GOLD-SIDE WITNESS FAILURE IS SEMANTIC (re-derived, and the earlier
argument for it was WRONG — see the ``_witness_value`` comment for the full
measurement). Each reject witness FAILS against the frozen solution with an
*application type mismatch on ``hne heq``* that names the two concrete coordinate
lists: gold's ``.run`` unifies to the SPEC's list while the witness's ``hne``
demands the RIVAL's list, so the disequality is refuted on VALUE.

That shape was reached only after the obvious one was measured and rejected. An
earlier revision of this battery opened every witness with a ``simp only
[scalePoint, scaleCoords, NonDetT.run, findableEqList, ...]`` preamble and
injected through ``rw [DivM.res.injEq]``. Because the frozen impl keeps the ``:|``
choice and that simp set does not reduce ``pickSuchThat``, gold's goal stayed at
the un-reduced ``NonDetT.bind (pickSuchThat ...) ...`` and the ``rw`` simply
failed to find its pattern. The decisive test is whether gold's exit code moves
when the CLAIM moves, and it did not: a disequality TRUE of gold
(``.run ≠ DivM.res [99,99]``) and the flipped claim asserting gold is CORRECT
both failed on gold with the byte-identical ``rewrite``-pattern error. Gold's
exit code carried no information, so a forged witness would have been recorded as
a refutation. The repaired witnesses are checked by DEFEQ (``exact hne heq``),
where unification does unfold the choice; re-measured, the real claim gives
rival EXIT 0 / gold EXIT 1 and the flipped claim gives rival EXIT 1 / **gold
EXIT 0**. That flip is what makes gold's failure evidence about the spec.

CARRIER NOTE — a TRANSPARENT model, so witnesses use CONCRETE literals. Unlike
the opaque-callee siblings (matplotlib-14623's ``normalize``), ``scaleCoords`` is
a concrete ``def`` that computes at literal inputs, so each rival is refuted at a
concrete ``(factor, coords)`` point WITHOUT conditioning on any opaque term (the
witnesses bind nothing, so there is no consistency-probe obligation). The one
wrinkle is the guide's documented Rat-arithmetic pitfall: ``decide`` reduces the
``Decidable`` instance rather than computing the ``Rat`` product and gets STUCK on
``(Rat.mul _ _).num``; each value witness therefore closes the residual
coordinate (dis)equality with ``simp [Rat.mul_def, Rat.add_def, Rat.normalize]``,
the normalizer for exact-rational multiplication/addition, NOT ``decide``.

TERMINATION / DIVERGENCE LANE: REJECTED BY THE SPEC, unshippable for a WITNESS
reason, and NOT a hole. This section has been rewritten by re-measurement, and the
"known hole in the TERMINATION dimension" it used to record is RETRACTED IN FULL.

This bundle sets ``loom.semantics.termination "total"``, and every velvet bundle in
this corpus does; none sets "partial". The option is not inert and cannot disagree
with the surrounding ``open``, because the ``set_option`` elaborator itself opens
the matching scope (``Loom/MonadAlgebras/WP/Options.lean``, ``openScope``, where
"total" opens ``TotalCorrectness``), and ``Velvet/Syntax.lean:386`` opens the same
scope by default. Under total semantics a postcondition is claimed of ALL runs and
not only of terminating ones, so a diverging impl does NOT satisfy ``ensures``
vacuously.

Two shapes, both measured on scratch copies of this cell, the bundle unmodified.
  * NO annotation. A rival whose loop carries no ``decreasing`` clause is REJECTED
    (EXIT 1, ``Decreasing annotations are required in total correctness
    semantics``).
  * ANNOTATION PRESENT BUT FALSE, which is the shape the retracted text claimed
    verifies. It is REJECTED TOO, on the measure's OWN descent goal, so it cannot
    be dismissed as merely the annotation linter above. Re-run verbatim at the two
    measures that text named:
      - ``while q ≠ 1`` with ``decreasing q`` and body ``q := q + 2`` (the measure
        strictly INCREASES)  ->  EXIT 1, ``unsolved goals``, residual
        ``case decreasing_1: q ... |- q + 2 < q``;
      - a CONSTANT measure, ``decreasing j`` with ``j`` never written while the
        body advances a different counter  ->  EXIT 1, ``unsolved goals``, residual
        ``case decreasing_1: j ... |- 3 < 3``.
    The mechanism is in Loom rather than in a tactic:
    ``TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`` takes
    ``measure : β -> Nat`` and emits ``measure b' < measure b`` as a real proof
    obligation; only the ``PartialCorrectness`` twin takes an ``Option ℕ`` and
    DISCARDS it. So "total" buys termination, not merely the annotation's presence,
    and the earlier EXIT-0 measurements this section reported do not reproduce.

Why the class is still not shipped as a reject case, which is mechanical and not a
spec matter. THIS PARAGRAPH IS THE SECOND AUDIT'S CORRECTION: the reason recorded
here previously — "both refusals are emitted at the ``method`` declaration itself,
so the rival's file never defines ``scalePoint``" — is TRUE of only ONE of the two
shapes, and was measured wrong for the other. Re-measured, with a TRIVIAL witness
(``example : (1:Nat) + 1 = 2 := by decide``) used as the control that separates
"the rival's method failed to elaborate" from "the witness failed":
  * NO annotation — the control is EXIT 1, failing at the ``method`` line itself
    (``Decreasing annotations are required in total correctness semantics``). Here
    the old reason holds: the rival's method genuinely never elaborates.
  * FALSE/INCREASING annotation — the control is **EXIT 0**. The linter's descent
    goal is refused inside ``prove_correct``, which ``witness_file`` STRIPS, so the
    rival's ``scalePoint`` elaborates perfectly well in the witness file. The old
    reason is simply false for this shape.
What actually blocks the shipped shape is the rival's own loop TERM, and it blocks
on the RIVAL side, where a reject case needs its witness to hold. Measured on the
false-measure rival: the battery's defeq witness is EXIT 1 against it, and the
residual goal is the un-normalised ``NonDetT.run do let _ ← forIn Lean.Loop.mk 1
... pickSuchThat ...`` — the loop is kernel-irreducible, so ``rfl``/``decide``/
``simp [scalePoint]`` all leave the claim un-evaluated (five witness shapes tried,
all EXIT 1 on the rival: ``.run = DivM.div`` by ``rfl`` and by ``simp``, the
disequality by ``simp``, by ``decide``, and by ``intro``-then-``simp at``). That is
the SAME ``forIn Lean.Loop.mk`` irreducibility the gate itself screens for as
``loop-unification`` / ``witness-undecided``, arriving on the rival side where no
``witness_reference`` can help (a reference substitutes the GOLD subject, and the
irreducible term is the rival's). So the conclusion is unchanged and the reason is
now the measured one. Spec-side verdict: REJECT (the descent obligation is real and
is what refuses both shapes). Nothing is escalated from this class, and nothing
here is a P1/P2 soundness hole.

WITNESS MECHANICS. The impl chooses its result non-deterministically
(``let out :| out = scaleCoords coords factor``), so the method is
``noncomputable`` and no executable tester is extracted — the matplotlib-14623
pattern, NOT the loop-free-tester django-13012 pattern. Each witness therefore
reaches the post-image DIRECTLY over the method's own ``.run``, and states
``(scalePoint f c).run ≠ DivM.res (scaleCoords c f)``. It supplies ``hne``, the
disequality between the list the RIVAL returns at that point and the spec's own
``scaleCoords c f`` (closed on the Rat normalizer), and applies ``exact hne heq``.
That application is a DEFEQ check, and unification unfolds the demonic choice
(gold's equality closes by plain ``rfl``, measured EXIT 0), so against the rival
the two lists match and the witness elaborates, while against the frozen impl
``heq``'s type is the SPEC's list and the application is a type mismatch naming
both lists — the discrimination the gate requires, on VALUE. Both halves were
checked out-of-band with ``scripts/lean_verify.sh`` (two real builds per reject
case, plus a flipped-claim forgery build per case on each side): no banned token
(``sorry``/``admit``/``native_decide``/``axiom``); every witness input is
total-domain (no ``require`` to satisfy), so none is vacuously excluded.

BINDER / CLAUSE COVERAGE (pts = 4 distinct input points):
  factor — 3, 4, 7, 2 varied; coords — [1,2], [2,1,3], [1,1], [1,1] (contents,
  order, LENGTH; the two [1,1] witnesses differ in factor). P1 (value) attacked
  by weak-first-coord-unscaled (index 0), weak-last-coord-offbyfactor (boundary
  coordinate) and weak-no-scaling (factor ignored — the rival built to ABUSE the
  ``factor`` binder); P2 (length) attacked by weak-dimension-drop. No two rivals
  share an input tuple.

  The boundary witness point is deliberately LENGTH 3, not length 2. At length 2
  the last coordinate and index 1 are the same position, so a rival that
  perturbs index 1 is indistinguishable from one that perturbs the boundary, and
  a "last coordinate" claim demonstrated only at length 2 is not demonstrated at
  all. (This audit measured exactly that confusion in the first port of
  weak-last-coord-offbyfactor and re-aimed the rival; see the case comment.) The
  3-element point also gives the battery a witness at the 3-D shape the F2P
  exercises alongside the 2-D one.

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling's two frame-mutation
    rivals (writing the read-only ``point`` in place on the ``mul_right`` /
    ``mul_left`` sites and returning it) rest on nagini's fractional heap
    permission ``Acc(list_pred(point), 1/2)``. Velvet is referentially
    transparent and this bundle declares NO ``mut`` binder — both inputs are
    immutable values with no heap footprint — so there is no read-only cell to
    overwrite and no substitute probe. Per the porting map this class is VACUOUS
    here; not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. P1 pins ``out``
    to ``scaleCoords coords factor`` — a concrete ``def`` over the method's own
    arguments (empty ``axioms`` region; no opaque callee). The only satisfier is
    the grounded per-coordinate multiply; there is nothing to echo, so the
    positive controls are the cheapest faithful reshapes, not wrong echoes.
  * PARTIAL-DOMAIN / VALUE — the reject battery. Each rival gets the SHAPE right
    (or, for the length rival, keeps every surviving coordinate correct) and is
    correct on part of the domain, diverging on one coordinate, on the factor, or
    on the count.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-17655"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen scalePoint impl body (the choice bind
# ---- and the return). It lies wholly inside the single scalePoint
# ---- -- impl-start / -- impl-end region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so each edit keeps same_spec by
# ---- construction and leaves the `prove_correct scalePoint` STATEMENT intact.
_IMPL = (
    "    let out :| out = scaleCoords coords factor\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "scalePoint impl region drifted from expected text"

# ---- the frozen proof block. A tactic body is elided from the consumer spec
# ---- view, so a positive control that reshapes the impl may retune it without
# ---- touching the spec or dropping the obligation. Unique. ----
_PROVE = "prove_correct scalePoint by\n  loom_solve"
assert _BASE.count(_PROVE) == 1, "prove_correct scalePoint body drifted"


def _impl(new_impl):
    """Full Solution.lean with ONLY scalePoint's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_and_proof(new_impl, new_proof):
    """Reshape the impl AND retune the (elided) scalePoint tactic body."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROVE, new_proof)


# ---- witness mechanics: a DEFEQ-DRIVEN refutation, and why the obvious
# ---- `simp only [...]; rw [DivM.res.injEq]` shape had to be abandoned.
#
# AUDIT REPAIR (this is the load-bearing correction of this battery). Every
# witness here used to open with a `simp only [scalePoint, scaleCoords,
# NonDetT.run, findableEqList, bind, pure, ...]` preamble and then inject through
# `rw [DivM.res.injEq]`. Against a rival that shape works: the rival's `let out
# := <expr>` body is reduced by that simp set to a literal `DivM.res [...]`, the
# `rw` fires, and the residual coordinate mismatch closes on the Rat normalizer.
# Against the FROZEN impl it does NOT: gold keeps the `:|` choice, and the simp
# set does not reduce `pickSuchThat`, so the goal still reads
# `(NonDetT.bind (pickSuchThat ...) ...).run = DivM.res [...]`, the `rw` pattern
# `DivM.res ?x = DivM.res ?x` does not match, and the build fails.
#
# That gold-side failure is NOT a refutation, and it was measured rather than
# argued. The test is whether gold's exit code changes when the CLAIM changes:
#   * the shipped witness at (3,[1,2])                      -> gold EXIT 1
#   * a disequality TRUE of gold, `.run ≠ DivM.res [99,99]`  -> gold EXIT 1
#     with a byte-identical `rewrite`-pattern error (only the printed RHS moves)
#   * the flipped claim `.run = DivM.res (scaleCoords ...)`,
#     i.e. asserting gold is CORRECT there                   -> gold EXIT 1, same error
# So gold's exit code carried no information about the claim, and a forged
# "witness" asserting the frozen impl is correct would have been recorded as a
# refutation. Confirmed from the type side too: replacing the closing step with a
# deliberate type error (`exact (heq : Nat)`) prints heq's REAL type, which is
# the UNREDUCED `(NonDetT.bind (pickSuchThat ...)).run = DivM.res [1*3, 2*3]` on
# gold, versus a reduced `DivM.res [1, 2*3] = DivM.res [1*3, 2*3]` on the rival.
# The kernel never evaluated gold's claim.
#
# The repair does not need a `witness_reference`: the refutation is simply stated
# so that the claim is checked by DEFEQ instead of by rewriting. `exact hne heq`
# forces Lean to unify heq's type with `hne`'s argument type, and unification
# DOES unfold `pickSuchThat` (independently measured: gold's equality
# `(scalePoint 3 [1,2]).run = DivM.res (scaleCoords [1,2] 3)` closes by plain
# `rfl`, EXIT 0). So the choice term is definitionally the correct list, and the
# witness's disequality is genuinely FALSE on gold rather than unreducible.
#
# Re-measured on the repaired shape, gold's exit code now TRACKS the claim:
#   real claim (rival wrong at its point) -> rival EXIT 0, gold EXIT 1
#   flipped claim (impl is correct there)  -> rival EXIT 1, gold EXIT 0
# The flip flipping is the whole point: it is what makes gold's EXIT 1 evidence
# about the spec instead of evidence about tactic shape. Gold's residual error is
# the semantic one — `heq has type NonDetT.run (scalePoint 3 [1,2]) = DivM.res
# (scaleCoords [1,2] 3) but is expected to have type DivM.res [1, 2*3] = ...`,
# i.e. the concrete list gold produces is not the rival's list.
#
# Note there is deliberately NO `simp only` preamble: adding one re-introduces
# the defect, because it rewrites the goal into the un-normalised `NonDetT.bind`
# form and blocks the later defeq check.


def _witness_value(factor, coords, rival_list):
    """Refute a VALUE rival at a concrete point, by DEFEQ.

    `rival_list` is the coordinate list the RIVAL actually returns at
    (factor, coords), written as Rat arithmetic. `hne` states that list differs
    from the spec's own `scaleCoords coords factor` (closed on the Rat
    normalizer — `decide` gets stuck on `(Rat.mul _ _).num`, the documented
    carrier pitfall), and `exact hne heq` then forces the kernel to check that
    the impl's `.run` really is that list. Against the frozen impl the unifier
    unfolds the choice to the CORRECT list, the two types disagree, and the
    witness fails semantically.
    """
    return (
        f"example : (scalePoint {factor} {coords}).run "
        f"≠ DivM.res (scaleCoords {coords} {factor}) := by\n"
        "  intro heq\n"
        f"  have hne : (DivM.res ({rival_list} : List Rat))\n"
        f"      ≠ DivM.res (scaleCoords {coords} {factor}) := by\n"
        "    simp [scaleCoords, Rat.mul_def, Rat.add_def, Rat.normalize]\n"
        "  exact hne heq\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Port the nagini
    # `pos-control-localreshape` ARGUMENT ("a faithful, structurally-different
    # correct impl is not rejected") onto this carrier. The nagini reshape renames
    # locals / rewrites the loop guard; this carrier has no loop (the scaling is a
    # single delegation to the pure model), so the faithful reshapes are (a)
    # binding the pure model result directly and (b) inlining its `.map` body.
    # =====================================================================
    {
        "id": "pos-scalecoords-direct",
        "kind": "soundness",
        "expect": "verify",
        # Drop the non-deterministic choice: bind the pure model result directly.
        # Observationally identical to gold on every input, so P1/P2 both still
        # discharge and the FROZEN proof (`loom_solve`) closes the byte-identical
        # obligation (the body is definitionally the RHS of P1).
        "module": _impl(
            "    let out := scaleCoords coords factor\n"
            "    return out"),
        "rationale": "PASS SOURCE = P1/P2. Binding the pure model result directly "
                     "(dropping the non-deterministic choice) yields the SAME "
                     "coordinate list as gold on every input, so `out = scaleCoords "
                     "coords factor` and `out.length = coords.length` both hold on "
                     "the whole domain. A structurally-different faithful reshape "
                     "MUST verify; else the postcondition over-constrains the "
                     "executable shape (SPEC-TOO-STRONG). Verified out-of-band.",
    },
    {
        "id": "pos-inline-map",
        "kind": "soundness",
        "expect": "verify",
        # Inline the per-coordinate multiply as an explicit `.map`, identical in
        # value to `scaleCoords` but a different syntactic form; the elided proof
        # is retuned to fold the `.map` back to `scaleCoords`.
        "module": _impl_and_proof(
            "    let out := coords.map (· * factor)\n"
            "    return out",
            "prove_correct scalePoint by\n"
            "  loom_solve\n"
            "  all_goals (simp [scaleCoords])"),
        "rationale": "PASS SOURCE = P1/P2. Inlining the per-coordinate multiply as "
                     "an explicit `coords.map (· * factor)` produces the same list "
                     "as gold on every input (it IS `scaleCoords` unfolded), so P1 "
                     "and P2 still hold. A second faithful reshape that MUST "
                     "verify; else SPEC-TOO-STRONG on the executable staging. The "
                     "elided proof is retuned only to fold the `.map` back to "
                     "`scaleCoords`. Verified out-of-band.",
    },

    # =====================================================================
    # ADMISSIBILITY — ported from nagini `admiss-fzp-shape`. The nagini probe
    # re-established that the precondition admits a normal F2P-shaped input. This
    # method has NO `require` clause (total domain over the two values), so the
    # residual admissibility risk is that the post-image be NON-DEGENERATE on the
    # F2P shape: an in-region `assert` pins that scaling the F2P point (1,1) by 5
    # yields the full (5,5) — a genuine per-coordinate product, not a constant or
    # empty collapse. The impl is kept behaviourally identical to gold and the
    # decidable in-region `assert` is discharged, so the method's own obligation
    # still closes. MUST verify.
    # =====================================================================
    {
        "id": "admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        # AUDIT REPAIR (second audit). This case previously asserted only the 2-D
        # F2P point, while the battery's prose (here, the coverage note, and the
        # footer) claimed the F2P's 3-D shape was covered "as well as the 2-D one".
        # It was not: the sole `assert` named [1,1] and nothing in the manifest
        # discharged the obligation at a 3-D point. Both F2P shapes are now
        # asserted, each as its own named, live, decidable claim.
        "module": _impl_and_proof(
            "    -- The F2P-shaped inputs (the point (1,1) scaled by 5, and the\n"
            "    -- 3-D point (1,1,1) scaled by 5) lie in the total domain and\n"
            "    -- their post-images are non-degenerate: the full (5,5) and\n"
            "    -- (5,5,5), genuine per-coordinate products.\n"
            "    assert (with_name_prefix `admiss (scaleCoords [1,1] 5 = [5,5]))\n"
            "    assert (with_name_prefix `admiss3 (scaleCoords [1,1,1] 5 = [5,5,5]))\n"
            "    let out :| out = scaleCoords coords factor\n"
            "    return out",
            "prove_correct scalePoint by\n"
            "  loom_solve\n"
            "  all_goals (simp [scaleCoords, Rat.mul_def, Rat.normalize])"),
        "rationale": "the domain admits BOTH exact F2P input shapes (the point "
                     "(1,1) scaled by 5 and the 3-D point (1,1,1) scaled by 5) AND "
                     "the post-image is non-degenerate at each: it assembles the "
                     "full (5,5) / (5,5,5), a genuine per-coordinate product (not a "
                     "constant or empty collapse) with the count preserved. Each "
                     "in-region `assert` is a live, decidable claim about its F2P "
                     "point: a false claim leaves an unsolved goal, measured on "
                     "both legs — replacing (5,5) by (5,6) leaves `case «admiss_1: "
                     "...» |- False` (EXIT 1) and replacing (5,5,5) by (5,5,6) "
                     "leaves `case «admiss3_1: ...» |- False` (EXIT 1), so neither "
                     "assert is inert. The impl is otherwise gold, so the method's "
                     "own `ensures` discharges too. If it cannot verify => an F2P "
                     "shape would be excluded. Verified out-of-band (EXIT 0).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # distinct concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests (`5 * Point(1,1) ==
    # Point(5,5)` / `5 * Point(1,1,1) == Point3D(5,5,5)` in test_point /
    # test_point3D).
    # =====================================================================
    {
        "id": "weak-first-coord-unscaled",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every coordinate EXCEPT index 0, which is copied UNSCALED.
        # Correct shape (count preserved) and correct on the rest of the domain;
        # diverges only on the first coordinate whenever it is non-zero and
        # factor != 1. Ports the nagini partial-first-coord-unscaled rival.
        "module": _impl(
            "    let out := match coords with\n"
            "      | [] => []\n"
            "      | c :: rest => c :: rest.map (· * factor)\n"
            "    return out"),
        "refinement": "leaves the first coordinate UNSCALED (out[0] = coords[0], "
                      "not coords[0]*factor); correct on every other coordinate. "
                      "The faithful counterpart would scale the point (1,1) by 5 to "
                      "(1,5) rather than (5,5), so the failing test that asserts "
                      "left-multiplication of the point by 5 equals (5,5) FAILS — "
                      "it does NOT resolve.",
        "rationale": "REJECT from P1 (out = scaleCoords coords factor) on the "
                     "FIRST coordinate: `scaleCoords` scales index 0 like the rest, "
                     "the rival copies it unscaled, so the lists disagree whenever "
                     "coords[0] is non-zero and factor != 1. A spec admitting this "
                     "would be SPEC-TOO-WEAK (partial-domain: first element). "
                     "Refuted at factor=3, coords=[1,2]: gold's list is [3,6], the "
                     "rival's [1,6]. Discrimination comes from index 0 of `coords`.",
        # rival returns [1, 2*3] at (3,[1,2]) — index 0 copied unscaled.
        "witness": _witness_value("3", "[1,2]", "[1, 2*3]"),
    },
    {
        "id": "weak-last-coord-offbyfactor",
        "kind": "uniqueness",
        "expect": "reject",
        # Scales the boundary (LAST) coordinate by factor+1 instead of factor,
        # correct elsewhere. Correct shape and correct on every non-final
        # coordinate; diverges only on the boundary coordinate. Ports the nagini
        # partial-last-coord-offbyfactor rival — the VALUE facet the earlier port
        # wrongly dropped as "Rat arithmetic unavailable"; the Rat normalizer
        # (Rat.mul_def / Rat.add_def / Rat.normalize) decides it (see footer).
        #
        # AUDIT REPAIR. The first port wrote this rival as a two-cons match
        # (`c0 :: c1 :: rest => c0 * factor :: c1 * (factor + 1) :: ...`), which
        # perturbs INDEX 1 unconditionally — the last coordinate only when
        # `coords` happens to have length 2, and the MIDDLE coordinate on any
        # longer input. Measured on the 3-element point [2,1,3] at factor=4: the
        # old rival returned [2*4, 1*(4+1), 3*4] (`rfl`, EXIT 0), i.e. its LAST
        # coordinate 3*4=12 was scaled CORRECTLY and index 1 was the perturbed
        # one. So the "boundary/last coordinate" sub-domain the rationale and the
        # refinement both claimed was never demonstrated — the witness sat at a
        # length-2 point where last and index-1 coincide. Re-aimed at the genuine
        # boundary by peeling the coordinate sequence from the END (via
        # `.reverse`), so the off-by-factor lands on the true last coordinate at
        # EVERY length >= 1, and the witness is moved to a 3-element point where
        # last != index 1 (which also gives the battery its only 3-D-shaped
        # REJECT witness; the admissibility positive covers the 3-D F2P point on
        # the verify side — an `assert` the SECOND audit had to add, because the
        # prose claimed that coverage before any case demonstrated it).
        "module": _impl(
            "    let out := match coords.reverse with\n"
            "      | [] => []\n"
            "      | c :: rest => ((c * (factor + 1)) :: rest.map (· * factor)).reverse\n"
            "    return out"),
        "refinement": "scales the boundary (last) coordinate by factor+1 instead "
                      "of factor; correct elsewhere, at every length. The faithful "
                      "counterpart would scale the point (1,1) by 5 to (5,6) rather "
                      "than (5,5) — and the 3-D point (1,1,1) by 5 to (5,5,6) "
                      "rather than (5,5,5) — so the failing tests asserting "
                      "left-multiplication by 5 equals (5,5) / (5,5,5) FAIL — it "
                      "does NOT resolve.",
        "rationale": "REJECT from P1 on the boundary (last) coordinate: "
                     "`scaleCoords` scales it by `factor`, the rival by `factor+1`, "
                     "so the lists disagree there whenever the coordinate is "
                     "non-zero. A spec admitting this would be SPEC-TOO-WEAK "
                     "(partial-domain: off-by-factor on a boundary element). "
                     "Refuted at factor=4, coords=[2,1,3]: gold's list is "
                     "[8,4,12], the rival's [8,4,15] — the divergence is at the "
                     "LAST coordinate while indices 0 and 1 stay correct, so the "
                     "witness point has length 3 and the boundary is genuinely "
                     "distinct from index 1 (a length-2 point could not tell the "
                     "two apart). Discrimination comes from the last `coords` "
                     "element (this point moves factor=4 and the length, both "
                     "distinct from the other witnesses).",
        # rival returns [2*4, 1*4, 3*(4+1)] at (4,[2,1,3]) — the LAST coordinate
        # scaled by factor+1, indices 0 and 1 correct, so the boundary sub-domain
        # the rationale claims is the one actually demonstrated.
        "witness": _witness_value("4", "[2,1,3]", "[2*4, 1*4, 3*(4+1)]"),
    },
    {
        "id": "weak-no-scaling",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the coordinates UNCHANGED, ignoring `factor` entirely. Correct
        # shape, but the product is never taken. Built to ABUSE the `factor`
        # binder specifically: an impl that mishandled only `factor` would verify
        # against a spec that did not pin the product.
        "module": _impl(
            "    let out := coords\n"
            "    return out"),
        "refinement": "returns the coordinates unchanged (never multiplying by "
                      "`factor`); this is the shape of a patch that forwarded the "
                      "point without scaling. The faithful counterpart would scale "
                      "the point (1,1) by 5 to (1,1) rather than (5,5), so the "
                      "failing test asserting left-multiplication by 5 equals (5,5) "
                      "FAILS — it does NOT resolve.",
        "rationale": "REJECT from P1 (out = scaleCoords coords factor): the "
                     "unscaled coordinates cannot equal their per-coordinate "
                     "product whenever factor != 1. This rival ABUSES the `factor` "
                     "binder (it is ignored entirely); verifying would be "
                     "SPEC-TOO-WEAK on `factor`. Refuted at factor=7, coords=[1,1]: "
                     "gold's list is [7,7], the rival's [1,1]. Discrimination comes "
                     "from the `factor` binder — the one no coordinate-local rival "
                     "abuses.",
        # rival returns the input unchanged, [1,1], at (7,[1,1]).
        "witness": _witness_value("7", "[1,1]", "[1, 1]"),
    },
    {
        "id": "weak-dimension-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the FIRST coordinate of the result, so out.length =
        # coords.length - 1. Every surviving coordinate is scaled correctly; the
        # divergence is purely in the COUNT. Violates P2. Ports the nagini
        # dimension-drop rival.
        "module": _impl(
            "    let out := coords.tail.map (· * factor)\n"
            "    return out"),
        "refinement": "drops the first coordinate: out.length = coords.length - 1. "
                      "The faithful counterpart would scale the point (1,1) by 5 to "
                      "a 1-D point (5) rather than (5,5) — a different dimension "
                      "that is not equal to (5,5), so the failing test asserting "
                      "left-multiplication by 5 equals a 2-D (5,5) FAILS — it does "
                      "NOT resolve (and the 3-D F2P likewise loses a coordinate).",
        "rationale": "REJECT from P2 (out.length = coords.length): the rival drops "
                     "the first coordinate, so the result is one shorter than the "
                     "input whenever `coords` is non-empty. (It also violates P1, "
                     "but P2 is the load-bearing length clause it attacks.) A spec "
                     "admitting this would be SPEC-TOO-WEAK (partial-domain: length "
                     "class). Refuted at factor=2, coords=[1,1]: gold's list is "
                     "[2,2] (length 2), the rival's [2] (length 1). Discrimination "
                     "comes from the length of `coords`.",
        # rival returns [1*2] at (2,[1,1]) — the first coordinate dropped, so the
        # result is LENGTH 1 where the spec's is length 2. The defeq witness
        # refutes on the list itself, which carries the length difference.
        "witness": _witness_value("2", "[1,1]", "[1*2]"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation rivals, 3 partial-domain rivals)
# plus an EMPTY AXIOM lane. This bundle models the SAME purely-functional core —
# scaling an ordered coordinate sequence by a single factor — as ONE method
# `scalePoint` with two postcondition clauses (P1 exact per-coordinate product,
# P2 dimension preserved) over `List Rat`, where the sibling contracts two
# functions (`mul_right`, `mul_left`) over a permission-bearing List[int] carrier.
# The value surface carries across intact; the permission surface does not exist
# here.
#
#   sibling case (nagini)          -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-control-localreshape       -> pos-scalecoords-direct
#                                     + pos-inline-map               PORTED (x2)
#   admiss-fzp-shape               -> admiss-f2p-point               PORTED (re-aimed)
#   frame-mut-right                -> (none)                         VACUOUS
#   frame-mut-left                 -> (none)                         VACUOUS
#   partial-first-coord-unscaled   -> weak-first-coord-unscaled      PORTED
#   partial-last-coord-offbyfactor -> weak-last-coord-offbyfactor    PORTED
#   dimension-drop                 -> weak-dimension-drop            PORTED
#   (no sibling)                   -> weak-no-scaling                ADDED
#   AXIOM_TESTS ([])               -> (none)                         DROPPED (G-AX)
#   (no sibling; termination lane)  -> (none)                         SPEC-CLOSED
#
# All 5 attackable sibling SPEC cases PORTED (the 2 frame-mutation rivals are
# vacuous on this carrier); one reject rival added; the empty axiom lane dropped.
# 7 velvet cases total (2 soundness + 1 admissibility + 4 uniqueness).
#
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
#
# PORTED (positives): the sibling ships ONE structurally-different correct impl
#   (a local-variable reshape of the backward loop). This carrier has NO loop —
#   the operation is a single delegation to the pure model — so the reshape
#   ARGUMENT is carried by TWO honest positives: pos-scalecoords-direct (bind the
#   pure model result directly, dropping the non-deterministic choice; the FROZEN
#   proof closes it verbatim) and pos-inline-map (inline the per-coordinate
#   multiply as `coords.map (· * factor)`, an equal-value different syntactic
#   form; the elided proof is retuned to fold `.map` back to `scaleCoords`). Both
#   are correct on every input and both verify EXIT 0 out-of-band.
# PORTED-RE-AIMED (admissibility): the sibling adds a benign in-domain
#   `Assert(len(point) >= 0)` under its permission precondition. This method has
#   NO `require` clause (total domain), so the re-aimed probe instead asserts the
#   post-image is NON-DEGENERATE on the F2P shapes — scaling the point (1,1) by 5
#   yields the full (5,5), and the 3-D point (1,1,1) by 5 the full (5,5,5), genuine
#   per-coordinate products with the count preserved — via live decidable in-region
#   `assert`s discharged by a retuned proof. Verified EXIT 0. The 3-D leg was ADDED
#   by the third audit: the battery previously asserted the 2-D point only while its
#   prose claimed the 3-D F2P shape was covered too, so that sub-domain was claimed
#   and never demonstrated. Both legs are LIVENESS-CHECKED rather than assumed live
#   — falsifying either one ((5,6) / (5,5,6)) leaves that assert's own named goal
#   `|- False` at EXIT 1, so neither is an inert restatement.
# PORTED (rivals): the three nagini partial-domain rivals port 1:1 to the two
#   structural clauses: partial-first-coord-unscaled -> weak-first-coord-unscaled
#   (P1, index 0), partial-last-coord-offbyfactor -> weak-last-coord-offbyfactor
#   (P1, boundary/last coordinate), dimension-drop -> weak-dimension-drop (P2,
#   length class). Each carries a machine-checked witness at a concrete literal
#   input that ELABORATES against the rival and FAILS against gold (two real
#   builds per case).
#
#   NOTE on weak-last-coord-offbyfactor: an off-by-factor value rival needs to
#   observe `c * (factor+1) != c * factor` at a literal. `decide` reduces the
#   Decidable INSTANCE, not the value, so it gets STUCK at `(Rat.mul _ _).num`;
#   `norm_num`/`ring` are unknown in this workspace. But unfolding the operation
#   for simp decides it, measured on this very bundle:
#       example : (3 : Rat) * 4 = 12 := by decide                         -- stuck
#       example : (3 : Rat) * 4 = 12 := by simp [Rat.mul_def, Rat.normalize]  -- OK
#   So the off-by-factor VALUE facet IS expressible and this rival is LANDED (the
#   witness closes with `simp [Rat.mul_def, Rat.add_def, Rat.normalize]`), rather
#   than dropped as an unavailable-tactic gap. (Both halves of that measurement
#   re-confirmed by this audit: `decide` EXIT 1, `simp [Rat.mul_def,
#   Rat.normalize]` EXIT 0, on this bundle's own carrier.) The rival ITSELF was
#   re-aimed by the audit — as first ported it perturbed index 1 rather than the
#   last coordinate, so it did not demonstrate the boundary sub-domain its prose
#   claimed; see the case comment.
# ADDED (weak-no-scaling): return the coordinates unchanged, ignoring `factor`.
#   The sibling has no such rival; it is built here expressly to ABUSE the
#   `factor` binder — an impl that mishandled only `factor` would verify against a
#   spec that did not pin the product — so the reject lane exercises `factor`, not
#   only `coords`.
# VACUOUS (frame-mutation, x2): the two sibling frame-mutation rivals (write the
#   read-only `point` in place / write it on the delegating site) rest on nagini's
#   fractional permission Acc(list_pred(point),1/2). Velvet is referentially
#   transparent and this bundle declares NO `mut` binder — both inputs are
#   immutable values with no heap footprint — so there is no read-only cell to
#   overwrite and no substitute probe. Per the porting map this class is VACUOUS
#   here; not fabricated.
#   AUDIT DEMONSTRATION (rather than assertion): the only way to give this method
#   a writable coordinate cell is to declare the binder `mut`, and the binder list
#   sits in the method SIGNATURE — which is spec text, not impl text. Changing
#   `(coords : List Rat)` to `(mut coords : List Rat)` was measured to fail the
#   variant scope check with `spec view differs (same_spec failed)`, i.e. such a
#   rival cannot be a G-PBT case at all: it would be testing a DIFFERENT spec, not
#   attacking this one. That is what makes the class inexpressible here, and it is
#   a carrier fact, not a difficulty claim.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job. This bundle declares no
#   consumed axioms and one deep-model reference (`scaleCoords`, an A-reference
#   validated == the real point-by-scalar callee by axiom_check.py); the assembly
#   is concrete list arithmetic, and this gate ignores AXIOM_TESTS regardless.
#
# AUDIT PROBES BEYOND THE SHIPPED CASES (not cases themselves; recorded so the
# next reader knows which directions were already measured and found closed).
#   SPEC-TOO-WEAK probes — six NEW wrong impls built and run against the frozen
#   spec; ALL SIX were rejected (EXIT 1), so none is a spec hole: reverse the
#   scaled sequence; scale twice (c*factor*factor); collapse every coordinate to
#   0; append a spurious trailing 0 (length attack from the other side than
#   weak-dimension-drop); scale by factor+1 UNIFORMLY; and replace every
#   coordinate by `factor` itself (abusing the factor binder in the opposite
#   direction from weak-no-scaling). P1's `out = scaleCoords coords factor` pins
#   the whole sequence pointwise, so it has no admitted slack in any of these
#   directions.
#   SECOND-AUDIT SPEC-TOO-WEAK probes — six FURTHER new wrong impls, aimed at
#   directions the first six left alone; ALL SIX rejected (EXIT 1), so still no
#   spec hole: swap the first two coordinates (an ORDER attack that keeps the
#   multiset, which the earlier reverse-order probe only tested globally);
#   perturb index 2 specifically at length >= 3 (a MIDDLE coordinate, distinct
#   from both the index-0 and boundary rivals that ship); scale by the NEGATED
#   factor (sign, which no shipped rival moves); DUPLICATE the scaled sequence
#   (length attack that keeps every value correct and the order correct within
#   each half); return the EMPTY list (total collapse, the length clause's floor);
#   and a length-1 CORNER case that returns `[factor]` instead of `[c*factor]`
#   (correct on every other length, so it probes whether P1 is pinned at the
#   smallest non-empty shape). P1+P2 caught all six.
#   THIRD-AUDIT SPEC-TOO-WEAK probes — ten FURTHER new wrong impls, aimed at
#   directions the first twelve left alone; ALL TEN rejected (EXIT 1), each on a
#   named `ensures` goal, so still no spec hole. Six at the VALUE level: wrong
#   only when a coordinate is 0 (`if c = 0 then factor else c * factor`); the
#   product truncated to its numerator (`((c * factor).num : Rat)`, the Rat->Int
#   collapse this carrier could have admitted); a HARDCODED impl that special-cases
#   exactly the two F2P coordinate shapes and returns `coords` otherwise (the
#   answer-key/overfit attack — it fails because P1 is universally quantified over
#   `coords`, not checked at the demonstrated points); wrong only for NEGATIVE
#   factor (`if factor < 0 then c * (-factor)`); wrong only at `factor = 0`; and an
#   unconditional recursive self-call (rejected even earlier, at `fail to show
#   termination for scalePoint`). Four aimed at the DEMONIC CHOICE operator itself,
#   which no other probe touches — the residual risk that the `:|` bind, not the
#   `ensures`, is what carries P1: a choice constrained ONLY by length
#   (`out :| out.length = coords.length`), a wholly unconstrained one
#   (`out :| True`), and one pinned to the wrong value (`out :| out = coords`) are
#   each REJECTED on `ensures_2`, so the postcondition and not the choice predicate
#   is load-bearing. The fourth is the vacuity CONTROL: an INFEASIBLE choice
#   (`out = scaleCoords coords factor ∧ out ≠ scaleCoords coords factor`) does NOT
#   verify vacuously — it is refused at `failed to synthesize Findable`, i.e. the
#   carrier demands the constructive existence witness rather than letting an
#   unsatisfiable guard discharge the obligation for free.
#   SECOND-AUDIT SPEC-TOO-STRONG probes — three FURTHER faithful reshapes, all
#   provable: `(coords.map (· * factor)).map id` (EXIT 0); an `if
#   coords.isEmpty` case split that computes the same list on both branches
#   (EXIT 0, proof `cases coords <;> simp [scaleCoords]`); and a left fold that
#   appends, `coords.foldl (fun acc c => acc ++ [c * factor]) []` (EXIT 0 once the
#   fold/append accumulator lemma `∀ l acc, l.foldl … acc = acc ++ l.map …` is
#   supplied by induction — worth recording that a naive `simp [List.foldl_map]`
#   leaves `1 + tail.length = tail.length + 1` unsolved, which is a proof-effort
#   wrinkle and NOT a spec rejection; the reshape does verify).
#   THIRD-AUDIT SPEC-TOO-STRONG probes — three FURTHER faithful reshapes, all
#   provable (EXIT 0), so the spec still rejects no correct impl: a `factor = 1`
#   short-circuit that returns `coords` unchanged on that branch (the shape closest
#   to weak-no-scaling that is actually CORRECT — it verifies, which is what shows
#   the reject lane's rival is rejected for being wrong and not for its syntactic
#   form); `coords.reverse.foldl (fun acc c => c * factor :: acc) []`; and
#   `(coords.map (· * factor)).reverse.reverse`.
#   THIRD-AUDIT WITNESS RE-DERIVATION. All four reject cases rebuilt from the
#   manifest by hand, both halves plus two forgery pairs each (28 builds): rival
#   EXIT 0 / gold EXIT 1 on the shipped claim, and — the test that decides whether
#   gold's exit code carries information — the FLIPPED claim asserting gold is
#   CORRECT at the same point (`.run = DivM.res (scaleCoords c f)`, closed by
#   `rfl`) gives gold EXIT 0 / rival EXIT 1, exactly inverted. A third probe
#   asserting `.run` equals the RIVAL's literal list gives rival EXIT 0 / gold
#   EXIT 1, and one asserting it equals the CORRECT literal list gives gold EXIT 0 /
#   rival EXIT 1. So on this cell gold's exit code tracks the CLAIM in all four
#   directions, which is what makes each `Application type mismatch` a refutation on
#   VALUE rather than a tactic artifact. (The type-revealing route is uninformative
#   HERE and is recorded so the next reader does not misread it: `exact (heq : Nat)`
#   prints the same `NonDetT.run (scalePoint ...) = DivM.res (scaleCoords ...)` of
#   sort Prop on BOTH sides, because `heq` is an `intro`'d hypothesis whose type is
#   the witness's own statement — not a `simp`-reduced term. It is the flip pair,
#   not the reveal, that establishes these four.)
#   SPEC-TOO-STRONG probes — three NEW faithful reshapes, all provable, so the
#   spec rejects no correct impl among them: `coords.foldr (fun c acc =>
#   c * factor :: acc) []` (EXIT 0, proof folds via List.foldr_map),
#   `(coords.reverse.map (· * factor)).reverse` (EXIT 0, via List.map_reverse),
#   and the COMMUTED multiply `coords.map (fun c => factor * c)` (EXIT 0 once the
#   residual `∀ a ∈ coords, factor * a = a * factor` is closed with
#   `Rat.mul_comm`). Worth recording that the commuted reshape needs the
#   Rat-specific lemma: bare `mul_comm` fails to synthesize `CommMagma Rat` on
#   this carrier and `exact mul_comm a b` is EXIT 1, while `Rat.mul_comm` is
#   EXIT 0 — a tooling wrinkle of the same family as the `decide`/`Rat.mul_def`
#   one above, and NOT a spec defect.
#
# CLAUSE / BINDER COVERAGE. The operation-under-spec obligation (`prove_correct
# scalePoint`) is defended (two soundness positives + the admissibility case) and
# attacked (four reject rivals). Its value clause P1 is attacked by three rivals
# across distinct sub-domains — first coordinate unscaled, boundary coordinate
# off-by-factor, and factor ignored entirely; its length clause P2 by
# weak-dimension-drop. Both INPUT BINDERS are varied by the reject witnesses:
# `factor` over {3,4,7,2} (including weak-no-scaling, built to mishandle it) and
# `coords` over {[1,2],[2,1,3],[1,1],[1,1]} (content, order, LENGTH; the two
# [1,1] witnesses differ in factor). The four witnesses sit at four DISTINCT input
# points (pts=4), so the manifest demonstrates the post-image's dependence on
# both binders, not merely its value at a single pinned point. There is no
# free/ambient input to hold fixed.
AXIOM_TESTS = []
