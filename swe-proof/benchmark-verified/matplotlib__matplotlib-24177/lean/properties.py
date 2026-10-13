"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24177 (lean).

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

DEFENDED SURFACE (one total function over a list carrier)
---------------------------------------------------------
A single modeled function computes the data limits induced by a geometric path's
defining points:

  dataLimits (verts : List (Rat × Rat)) : Option (Rat × Rat × Rat × Rat)

  * with no points the result is ``none``;
  * otherwise the result is the tight axis-aligned bounding box ``(xmin, xmax,
    ymin, ymax)`` of the WHOLE point set.

The load-bearing clauses of ``problem_spec_dataLimits`` (all conjuncts of the
``some`` arm; the ``none`` arm is the frame clause):

  (F)   result = none  ↔  verts = []                       (frame / emptiness)
  (DOM) ∀ v ∈ verts, xmin ≤ v.1 ≤ xmax ∧ ymin ≤ v.2 ≤ ymax  (enclosing/dominance)
  (ATT) each of the four bounds is attained by some defining point (tightness)

WHAT DRIVES THE REJECTS. (DOM) is the discriminating clause. The defect the gold
change repairs is a point-gather that OMITS some defining points before the
extent is formed, so a coordinate extreme carried by a dropped point is not
enclosed. The F2P regression exercises exactly this: the extreme sits on an
INTERIOR point (not the seed), so a gather that fails to fold every point
undershoots it and the autoscaled limit clips the artist. Every reject rival
here is a gather that fails to fold one of the four coordinate extremes over the
whole point set; each is refuted at an input whose extreme is carried by a
non-seed point, so (DOM) is violated at that point.

WHY (ATT) IS NOT ATTACKED BY A REJECT. The F2P test asserts only the LOOSE
bounds (the autoscaled limit is ``>=`` the true max and ``<=`` the true min); it
does not assert tightness. So a faithful patch that OVER-approximated the extent
(e.g. added fixed padding) would still resolve the F2P — an over-approximation
rival would be a spec-strength artifact, not a verify-does-not-resolve break.
This mirrors the nagini sibling, whose rivals all attack the dominance clause and
never the attainment clause; porting an (ATT)-only rival would manufacture a
verify-not-resolve claim the F2P cannot back.

(ATT) is nevertheless ENFORCED by the frozen spec, and this was measured rather
than argued: an over-approximating impl that seeds the y-upper bound at a fixed
literal (so (DOM) still holds but no defining point attains the bound) does NOT
verify against the frozen spec — the audit built it and the frozen obligation
failed, while its refutation witness elaborated against it (exit 0) and failed on
the frozen solution (exit 1). It is deliberately NOT shipped as a reject case,
because its refinement argument would be false: it WOULD resolve the F2P. (ATT)
is DEFENDED by the positive controls, which must re-derive both attainment
existentials for a new impl shape.

BINDER / CLAUSE COVERAGE. The single input binder is ``verts``. The rejects vary
it across six distinct inputs, and — crucially — across all four coordinate
roles, the empty/non-empty frame, AND the point-gather itself:

  * ``drop-ymax`` — the y-upper extreme is on an interior point (the exact shape
    of the gold-repaired defect); the gather leaves ymax at the seed's y.
  * ``drop-ymin`` — the y-lower extreme is on a non-seed point.
  * ``drop-xmax`` — the x-upper extreme is on a non-seed point.
  * ``drop-xmin`` — the x-lower extreme is on a non-seed point.
  * ``skip-alternate-gather`` — the extent is formed over a strict SUBSEQUENCE of
    the defining points, attacking the gather binder itself rather than any
    frozen bound slot. This is the rival closest in shape to the defended change,
    which is about WHICH points reach the extent.
  * ``none-nonempty`` — a non-empty path yields ``none``, attacking the frame
    clause (F) directly (result = none while verts ≠ []).

Each of the four (DOM) rivals fixes a DIFFERENT one of the four bound slots, so a
rival that mishandled only, say, the y-axis would be caught by ``drop-ymax`` /
``drop-ymin`` while ``drop-xmax`` / ``drop-xmin`` independently pin the x-axis.
Without all four, a bound slot the rivals never abuse would be a slot a wrong
impl could mishandle unnoticed. The four are all bound-SLOT edits, though, and a
battery made only of those would leave the gather — the actual defended surface —
probed only indirectly; ``skip-alternate-gather`` closes that gap.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
loop's exact elaboration — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. The carrier's point-collection loops
over an ``opaque`` callee, so a witness first pins the rival's concrete output
tuple as a ``have`` (discharged by rewriting the keep-all callee to its defining
points via the frozen ``sampledVertices_keepall_prop`` and reducing the resulting
transparent fold with ``decide``), then refutes the spec at that output by
``decide``. Each was checked with two real builds to ELABORATE against its rival
and to FAIL on the frozen solution (the ``have`` predicts the rival's tuple,
which gold does not produce), so each discriminates rather than asserting a
tautology. No witness binds a hypothesis, so there is no consistency obligation.

The gold-side failure is a SEMANTIC refutation in every case, not a syntactic
accident: an independent audit rebuilt all six witnesses against both sides and
each gold build failed with ``Tactic `decide` proved that the proposition ... is
false`` on the ``have`` that predicts the rival's tuple — i.e. gold demonstrably
returns a DIFFERENT tuple at that input. No gold-side failure was an unknown
identifier, a type error, an unfolding failure, or a timeout.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models the imperative gather under fractional permissions over
a mutable input, abstracting one coordinate axis to ``List[int]`` and returning
the per-axis maximum (the lower bound being symmetric by negation). This lean
carrier is referentially transparent and models the FULL two-axis bounding box as
a pure value over ``List (Rat × Rat)``. The correspondence and omissions:

  * nagini P_dom (enclosing) ↦ (DOM) here, attacked by the four coordinate-drop
    rivals; nagini's ``rival-return-last-seed`` (the "seed and don't fold"
    regression that is the actual gold-repaired defect) ↦ ``drop-ymax`` (the seed
    keeps its y while an interior point carries the true ymax). nagini's
    ``rival-return-first`` is a further "fold drops a point" shape, subsumed by
    the per-axis drop family (same clause, all four slots). ``rival-value-mask-
    odd`` (the fold admits only every other element) is NOT subsumed by that
    family — a bound-slot edit and a gather-subsequence edit fail for different
    reasons — so it is ported directly as ``skip-alternate-gather``.
  * FRAME / PERMISSION MUTATION (nagini ``rival-frame-mutate-verts``, MANDATORY
    there) — VACUOUS here. Lean is referentially transparent: the input carries
    no heap permission, there is no read-only half-permission to overwrite and no
    aliasing, so the write-to-input rival has no counterpart and no substitute is
    fabricated. The frame OBLIGATION that survives on this carrier is the
    emptiness clause (F), which is instead attacked by ``none-nonempty``.
  * nagini's ``pos-direct-seqmax`` positive control ↦ ``pos-direct-minmax`` here
    (drop the accumulator loop, return the min/max folds directly). nagini's
    ``pos-branch-reorder`` (rewrite the comparison as the equivalent
    ``not (<=)``) has NO faithful counterpart here and a substitute is not
    fabricated: on this carrier ``v.1 > xmax`` is *notation* for ``xmax < v.1``,
    so an operand flip is the SAME TERM (audit measured
    ``example : implGold = implFlip := rfl`` -> exit 0), and a genuinely negated
    guard (``!(xmin ≤ v.1)``) cannot be proven, because the frozen ``bboxStep``
    bridge lemma is stated over the ``<``/``>`` guards and its
    ``split_ifs <;> rfl`` step no longer applies (audit built both the frozen and
    a retuned proof body; both failed). Rather than ship a reshape that is
    definitionally the frozen impl, the second positive control is
    ``pos-concat-gather``, which reshapes the load-bearing GATHER instead of a
    comparison spelling. Both shipped positives are confirmed NON-definitional by
    a measured failing ``rfl``. nagini's
    ``admiss-selfcall`` (a self-call establishing the precondition) has no
    counterpart because the frozen obligation carries NO precondition hypothesis
    (the modeled behavior is total); the honest analogue is ``admiss-ground-
    instance``, which discharges the obligation at a concrete F2P-shaped input.

AXIOM lane: the nagini ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's job
and this gate ignores it. (The bundle's one ``opaque``/``axiom`` pair — the
keep-all point sampler and its defining-point characterization — is exercised
here only as the transparent bridge inside each witness, never as an answer-key
oracle: the spec is grounded in ``verts`` via membership/order/min-max, so there
is nothing to echo.)
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24177"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The four guarded bound updates in the bbox `for` loop (impl region). Each is
# unique and lies entirely inside the impl region.
_U_XMIN = "      if v.1 < xmin then xmin := v.1\n"
_U_XMAX = "      if v.1 > xmax then xmax := v.1\n"
_U_YMIN = "      if v.2 < ymin then ymin := v.2\n"
_U_YMAX = "      if v.2 > ymax then ymax := v.2\n"

# The final return (impl region) — for the none-frame rival.
_RET_GOLD = "    return some (xmin, xmax, ymin, ymax)\n-- impl-end"

# The WHOLE seed+loop+return block (impl region) — for the direct-min/max
# positive control, which replaces the accumulator loop with the pure-helper
# folds. Non-definitional: `rfl` does NOT identify it with the frozen impl
# (audit measured `example : implGold = implDirect := rfl` -> exit 1), so this
# reshape genuinely re-exercises the postcondition rather than restating it.
_SEED_LOOP_RET = (
    "    -- Bounding box of the collected points, seeded from the first point.\n"
    "    let mut xmin := p0.1\n"
    "    let mut xmax := p0.1\n"
    "    let mut ymin := p0.2\n"
    "    let mut ymax := p0.2\n"
    "    for v in rest do\n"
    "      if v.1 < xmin then xmin := v.1\n"
    "      if v.1 > xmax then xmax := v.1\n"
    "      if v.2 < ymin then ymin := v.2\n"
    "      if v.2 > ymax then ymax := v.2\n"
    "    return some (xmin, xmax, ymin, ymax)\n"
)

# The tail of `impl_some_char`'s tactic body: the part that bridges the frozen
# accumulator fold to the returned tuple. A direct-min/max impl needs no such
# bridge (the returned tuple IS the fold), so this tail is dropped in that case
# — a TACTIC-BODY-only edit, which `variant_scope` permits.
_ISC_TAIL = (
    "  dsimp only\n"
    "  simp only [← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl]\n"
    "  exact congrArg\n"
    "    (fun t : MProd Rat (MProd Rat (MProd Rat Rat)) => some (t.2.1, t.1, t.2.2.2, t.2.2.1))\n"
    "    (returned_tuple_eq p0 rest)\n"
)

# The point-gather accumulation step (impl region) — for the concat-gather
# positive control and the skip-gather rival. This is the load-bearing gather:
# the clause the defended change is about is WHICH points reach the extent.
_GATHER_STEP = "    vertices := vertices ++ [v]\n"

# `append_loop_id`'s statement+proof, and the one place `vertices_eq` names the
# gather's step function. Retuned (tactic body / helper-lemma statement, never
# the `correct_dataLimits` statement) by the concat-gather positive control.
_APPEND_LEMMA = (
    "theorem append_loop_id (s : List (Rat × Rat)) :\n"
    "    List.foldl (fun acc v => acc ++ [v]) [] s = s := by\n"
    "  suffices h : ∀ (acc : List (Rat × Rat)),\n"
    "      List.foldl (fun acc v => acc ++ [v]) acc s = acc ++ s by\n"
)
_VERTICES_EQ_STEP = (
    "    List.foldl (fun acc v => acc ++ [v]) [] (sampledVertices verts false) "
    "= p0 :: rest := by\n"
)

# The head of the proof region — for the admissibility ground instance.
_PROOF_HEAD = (
    "theorem correct_dataLimits : ∀ (verts : List (Rat × Rat)),\n"
    "    problem_spec_dataLimits verts (implementation_dataLimits verts) := by\n"
    "  intro verts"
)


# ---- witness helpers --------------------------------------------------------
# A reject witness pins the rival's concrete output tuple (by rewriting the
# keep-all sampler to its defining points, then reducing the transparent fold),
# then refutes the spec at that output. Stated at literal inputs, so it binds no
# hypothesis (no consistency obligation).

def _wit_some(inp, outlit):
    return (
        f"example : ¬ problem_spec_dataLimits\n    {inp}\n"
        f"    (implementation_dataLimits\n      {inp}) := by\n"
        f"  have h : implementation_dataLimits\n      {inp}\n"
        f"      = some {outlit} := by\n"
        f"    unfold implementation_dataLimits\n"
        f"    rw [sampledVertices_keepall_prop]\n"
        f"    simp only [Id.run, bind, pure, List.forIn_yield_eq_foldl]\n"
        f"    decide\n"
        f"  rw [h]\n"
        f"  unfold problem_spec_dataLimits\n"
        f"  decide\n"
    )


def _wit_none(inp):
    return (
        f"example : ¬ problem_spec_dataLimits\n    {inp}\n"
        f"    (implementation_dataLimits\n      {inp}) := by\n"
        f"  have h : implementation_dataLimits\n      {inp} = none := by\n"
        f"    unfold implementation_dataLimits\n"
        f"    rw [sampledVertices_keepall_prop]\n"
        f"    simp only [Id.run, bind, pure, List.forIn_yield_eq_foldl]\n"
        f"    decide\n"
        f"  rw [h]\n"
        f"  unfold problem_spec_dataLimits\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify (else the spec is over-fit => SPEC-
    # TOO-STRONG). Each keeps the `theorem correct_dataLimits` statement
    # byte-identical; the frozen proof still closes each new shape, so no helper
    # lemma, no axiom, no assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-direct-minmax",
        "kind": "soundness",
        "expect": "verify",
        # Replace the whole seed+accumulator-loop+return with the pure helpers'
        # componentwise min/max folds, returned directly. This is the honest port
        # of the nagini `pos-direct-seqmax` control: the loop machinery existed
        # only to establish `acc == min/max`, so taking the folds directly is the
        # cheapest CORRECT impl. Crucially it is NOT definitionally the frozen
        # impl — the frozen bridge lemma `impl_some_char` needs its accumulator
        # tail dropped, which is a tactic-body edit only.
        "module": _swap(
            _swap(
                _BASE, _SEED_LOOP_RET,
                "    -- Bounding box of the collected points, taken directly as the\n"
                "    -- componentwise min/max folds over the first point and the remainder.\n"
                "    return some (listMin p0.1 (rest.map (·.1)), listMax p0.1 (rest.map (·.1)),\n"
                "                 listMin p0.2 (rest.map (·.2)), listMax p0.2 (rest.map (·.2)))\n",
            ),
            _ISC_TAIL, "",
        ),
        "rationale": "a correct reshape that returns the componentwise min/max "
                     "folds DIRECTLY, dropping the accumulator loop entirely, must "
                     "still satisfy the bounding-box postcondition (dominance + "
                     "attainment + frame); if it could not, the spec would be "
                     "over-fit to the accumulator-loop shape => SPEC-TOO-STRONG. "
                     "This reshape is genuinely non-definitional: the audit "
                     "measured `example : implGold = implDirect := rfl` FAILING "
                     "(exit 1), and the frozen `impl_some_char` tail must be "
                     "dropped for the proof to close, so the postcondition is "
                     "re-established for a new impl shape rather than restated. "
                     "Both attainment existentials are re-derived here from "
                     "`listMin_attained` / `listMax_attained` against the returned "
                     "tuple, which is what DEFENDS the (ATT) clause no reject "
                     "attacks.",
    },
    {
        "id": "pos-concat-gather",
        "kind": "soundness",
        "expect": "verify",
        # Accumulate the collected points with `List.concat` instead of `++ [v]`.
        # This reshapes the LOAD-BEARING gather (which points reach the extent is
        # exactly the clause the defended change is about), not a bound spelling.
        # Also non-definitional: `rfl` does not identify it with the frozen impl.
        "module": _swap(
            _swap(
                _swap(
                    _BASE, _GATHER_STEP,
                    "    vertices := vertices.concat v\n",
                ),
                _APPEND_LEMMA,
                "theorem append_loop_id (s : List (Rat × Rat)) :\n"
                "    List.foldl (fun acc v => acc.concat v) [] s = s := by\n"
                "  simp only [List.concat_eq_append]\n"
                "  suffices h : ∀ (acc : List (Rat × Rat)),\n"
                "      List.foldl (fun acc v => acc ++ [v]) acc s = acc ++ s by\n",
            ),
            _VERTICES_EQ_STEP,
            "    List.foldl (fun acc v => acc.concat v) [] "
            "(sampledVertices verts false) = p0 :: rest := by\n",
        ),
        "rationale": "gathering the collected points with `List.concat` instead of "
                     "`++ [v]` is a correct reshape of the POINT-GATHER itself — "
                     "the same points in the same order reach the extent — so it "
                     "must verify (else the spec is over-fit to the gather's "
                     "spelling => SPEC-TOO-STRONG). Non-definitional: the audit "
                     "measured `example : implGold = implConcat := rfl` FAILING "
                     "(exit 1), and `append_loop_id` / `vertices_eq` must be "
                     "retuned to the new step function (helper-lemma statements "
                     "and tactic bodies only; `correct_dataLimits` stays "
                     "byte-identical). This is the positive control that pins the "
                     "gather, the surface every reject rival attacks.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at a normal, F2P-shaped input rather than only provable in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the modeled
    # behavior is total), so the nagini precondition-admission probe has no binder
    # to attack here; the honest analogue discharges the spec predicate at a
    # ground non-empty input (a small polyline whose y-extreme is interior) by
    # evaluation, inside the proof region, alongside the frozen obligation. If
    # that ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the input shape the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_HEAD,
            "theorem correct_dataLimits : ∀ (verts : List (Rat × Rat)),\n"
            "    problem_spec_dataLimits verts (implementation_dataLimits verts) := by\n"
            "  have _ground : problem_spec_dataLimits [((0:Rat),(0:Rat)), ((1:Rat),(5:Rat)), ((2:Rat),(0:Rat))]\n"
            "      (implementation_dataLimits [((0:Rat),(0:Rat)), ((1:Rat),(5:Rat)), ((2:Rat),(0:Rat))]) := by\n"
            "    have h : implementation_dataLimits [((0:Rat),(0:Rat)), ((1:Rat),(5:Rat)), ((2:Rat),(0:Rat))]\n"
            "        = some ((0:Rat),(2:Rat),(0:Rat),(5:Rat)) := by\n"
            "      unfold implementation_dataLimits\n"
            "      rw [sampledVertices_keepall_prop]\n"
            "      simp only [Id.run, bind, pure, List.forIn_yield_eq_foldl]\n"
            "      decide\n"
            "    rw [h]; unfold problem_spec_dataLimits; decide\n"
            "  intro verts",
        ),
        "rationale": "the bounding-box obligation is discharged at a ground "
                     "non-empty input (a small polyline whose y-extreme is on an "
                     "interior point) by evaluation, then the frozen obligation is "
                     "closed verbatim. Verifies (else the spec is unsatisfiable at "
                     "the normal input, the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical, and the ground instance is a "
                     "`have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the frozen
    # spec that MUST be rejected. Each carries (a) the refinement argument that
    # its faithful real patch would NOT resolve the F2P, so a verifying rival is a
    # true verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input.
    #
    # The four (DOM) rivals each DROP one guarded bound update, so that bound
    # stays at the seed's coordinate and a non-seed extreme is not enclosed —
    # exactly the "gather does not fold every point" defect the gold change
    # repairs. Each is refuted at an input whose extreme is carried by a non-seed
    # point.
    # =====================================================================
    {
        "id": "drop-ymax",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the y-upper update: ymax stays at the seed's y. This is the exact
        # shape of the gold-repaired defect (an interior point carries the true
        # y-max; the gather leaves it out of the extent).
        "module": _swap(_BASE, _U_YMAX, ""),
        "refinement": "a gather that never folds the y-upper coordinate over the "
                      "whole point set leaves the y-upper limit at the first "
                      "point's y; on the F2P regression the y-extreme is on an "
                      "interior point (the seed's y is 0), so the autoscaled "
                      "y-upper limit undershoots it and the `>= maxy` assertion "
                      "FAILS. This is the defect the change repairs — it would NOT "
                      "resolve.",
        "rationale": "REJECT from the dominance clause (∀ v ∈ verts, v.2 ≤ ymax): "
                     "at an input whose y-max is on a non-seed point the rival "
                     "returns the seed's y and the spec requires the true max. If "
                     "it verified => SPEC-TOO-WEAK (admits the seed-and-don't-fold "
                     "regression).",
        "witness": _wit_some(
            "[((0:Rat),(0:Rat)), ((1:Rat),(5:Rat)), ((2:Rat),(0:Rat))]",
            "((0:Rat),(2:Rat),(0:Rat),(0:Rat))",
        ),
    },
    {
        "id": "drop-ymin",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the y-lower update: ymin stays at the seed's y.
        "module": _swap(_BASE, _U_YMIN, ""),
        "refinement": "a gather that never folds the y-lower coordinate leaves the "
                      "y-lower limit at the first point's y; on a path whose "
                      "minimum y is on a non-seed point the autoscaled y-lower "
                      "limit overshoots it and the `<= miny` assertion FAILS. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the dominance clause (∀ v ∈ verts, ymin ≤ v.2): "
                     "at an input whose y-min is on a non-seed point the rival "
                     "returns the seed's y (larger than the true min) and the spec "
                     "requires ymin ≤ every y. If it verified => SPEC-TOO-WEAK.",
        "witness": _wit_some(
            "[((0:Rat),(5:Rat)), ((1:Rat),(0:Rat)), ((2:Rat),(9:Rat))]",
            "((0:Rat),(2:Rat),(5:Rat),(9:Rat))",
        ),
    },
    {
        "id": "drop-xmax",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the x-upper update: xmax stays at the seed's x.
        "module": _swap(_BASE, _U_XMAX, ""),
        "refinement": "a gather that never folds the x-upper coordinate leaves the "
                      "x-upper limit at the first point's x; on a path whose "
                      "maximum x is on a non-seed point the autoscaled x-upper "
                      "limit undershoots it and the `>= maxx` assertion FAILS. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the dominance clause (∀ v ∈ verts, v.1 ≤ xmax): "
                     "at an input whose x-max is on a non-seed point the rival "
                     "returns the seed's x and the spec requires the true max. If "
                     "it verified => SPEC-TOO-WEAK. Pins the x-upper slot that the "
                     "y-axis rivals do not touch.",
        "witness": _wit_some(
            "[((0:Rat),(0:Rat)), ((3:Rat),(0:Rat)), ((1:Rat),(0:Rat))]",
            "((0:Rat),(0:Rat),(0:Rat),(0:Rat))",
        ),
    },
    {
        "id": "drop-xmin",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the x-lower update: xmin stays at the seed's x.
        "module": _swap(_BASE, _U_XMIN, ""),
        "refinement": "a gather that never folds the x-lower coordinate leaves the "
                      "x-lower limit at the first point's x; on a path whose "
                      "minimum x is on a non-seed point the autoscaled x-lower "
                      "limit overshoots it and the `<= minx` assertion FAILS. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the dominance clause (∀ v ∈ verts, xmin ≤ v.1): "
                     "at an input whose x-min is on a non-seed point the rival "
                     "returns the seed's x (larger than the true min) and the spec "
                     "requires xmin ≤ every x. If it verified => SPEC-TOO-WEAK. "
                     "Pins the x-lower slot the other rivals do not touch.",
        "witness": _wit_some(
            "[((5:Rat),(0:Rat)), ((1:Rat),(0:Rat)), ((9:Rat),(0:Rat))]",
            "((5:Rat),(9:Rat),(0:Rat),(0:Rat))",
        ),
    },
    {
        "id": "skip-alternate-gather",
        "kind": "uniqueness",
        "expect": "reject",
        # Gather only every OTHER collected point: the extent is formed over a
        # STRICT SUBSEQUENCE of the defining points. This attacks the gather
        # itself rather than a frozen bound slot, so it is the rival closest in
        # shape to the defended change (which is about WHICH points reach the
        # extent, not about how a bound is spelled). It is the faithful analogue
        # of the nagini `rival-value-mask-odd` shape.
        "module": _swap(
            _BASE,
            "  let mut vertices : List (Rat × Rat) := []\n"
            "  for v in sampledVertices verts false do\n"
            "    vertices := vertices ++ [v]\n",
            "  let mut vertices : List (Rat × Rat) := []\n"
            "  let mut keep : Bool := true\n"
            "  for v in sampledVertices verts false do\n"
            "    if keep then vertices := vertices ++ [v]\n"
            "    keep := !keep\n",
        ),
        "refinement": "a gather that admits only a subsequence of the points is "
                      "exactly the shape of the defect: an omitted point can carry "
                      "a coordinate extreme, so the extent formed over the "
                      "subsequence is too small and the autoscaled limit clips the "
                      "artist. On a path whose extremes sit on omitted points BOTH "
                      "the `>= max` and `<= min` assertions FAIL. It would NOT "
                      "resolve — and unlike the four bound-slot rivals it fails "
                      "for a reason no reordering of the bound updates could "
                      "repair.",
        "rationale": "REJECT from the dominance clause (∀ v ∈ verts, xmin ≤ v.1 ≤ "
                     "xmax ∧ ymin ≤ v.2 ≤ ymax): at an input whose x- and y-maxima "
                     "both sit on an omitted point, the rival's box excludes that "
                     "point entirely. If it verified => SPEC-TOO-WEAK (the spec "
                     "would not require the extent to range over the WHOLE point "
                     "set, which is the entire content of the defended change). "
                     "Attacks the GATHER binder, which the four bound-slot rivals "
                     "leave untouched.",
        "witness": _wit_some(
            "[((0:Rat),(0:Rat)), ((7:Rat),(9:Rat)), ((1:Rat),(1:Rat))]",
            "((0:Rat),(1:Rat),(0:Rat),(1:Rat))",
        ),
    },
    {
        "id": "none-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        # Return `none` even for a non-empty path: attacks the frame/emptiness
        # clause (result = none ↔ verts = []) directly.
        "module": _swap(
            _BASE, _RET_GOLD,
            "    return none\n-- impl-end",
        ),
        "refinement": "a routine that produces no data limits for a non-empty path "
                      "never updates the axes limits, so autoscaling leaves the "
                      "default range and every `<= min` / `>= max` assertion on a "
                      "non-empty path FAILS. It would NOT resolve.",
        "rationale": "REJECT from the frame clause (result = none ↔ verts = []): at "
                     "a non-empty input the rival returns none while the spec "
                     "requires none only for the empty path. If it verified => "
                     "SPEC-TOO-WEAK (the emptiness frame is unconstrained).",
        "witness": _wit_none("[((0:Rat),(0:Rat))]"),
    },
]
