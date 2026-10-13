"""properties.py — G-PBT falsification battery for sympy__sympy-13647 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_colInsert``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the whole-row builder ``insert_row(self_row, other_row, cols, other_cols,
pos)`` — a mutable forward loop that produces an entire output row under
fractional-permission (``Acc(list_pred(...),1/2)``) contracts and a per-position
postcondition pin. This Lean bundle models a much NARROWER surface: the single
purely-functional per-entry accessor ``implementation_colInsert self other pos i
j : Int``, one banded value chosen from the two operand accessors, against the
three-region postcondition ``problem_spec_colInsert``. There is no width binder,
no output container, no mutable state, and no precondition hypothesis. Most
nagini cases therefore collapse onto attacks on ONE of the three clauses of the
one modeled obligation; the mapping of each nagini case to its Lean counterpart
(or its principled omission) is in the module ``assessment`` reported to the gate.

DEFENDED SURFACE (one modeled behavior). The accessor returns, for row ``i`` and
output column ``j``, exactly the banded operand value:

  * a column left of the insertion point (``j < pos``) reads the host at the same
    column, ``self.get i j`` (LEFT band);
  * a column inside the inserted block (``pos ≤ j < pos + other.cols``) reads the
    inserted operand at the offset from the insertion point, ``other.get i (j -
    pos)`` (MIDDLE band);
  * a column to the right of the block (``pos + other.cols ≤ j``) reads the host
    at the column it occupied before insertion, ``self.get i (j - other.cols)``
    (RIGHT band).

The three guards partition every column index, so ``result`` is pinned on the
whole domain — no output value is left free.

The BEHAVIOURAL DISCRIMINATOR (the fix): the RIGHT-band index is the host column
``j - other.cols`` (shifted left by the inserted width). The pre-fix code
subtracted ``pos`` as well (``j - pos - other.cols``), over-shifting by ``pos``
and reading the wrong host column wherever a right band exists with ``pos > 0``.
The prepatch rival below IS that regression; the spec's third clause is what
refutes it.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: the
    operands are immutable ``Mat`` values with no heap permission, no read-only
    half-share to overwrite and no aliasing to exploit. The nagini frame-mutation
    rival (write into the read-only ``self_row`` before the loop) has no
    expressible instance here — the accessor cannot mutate ``self``. No substitute
    is fabricated. (Ports nagini case 4, frame-mutate-readonly-self-row →
    omitted.)

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_colInsert``
    is a total Lean ``def``; a diverging implementation cannot be written, so
    there is no non-termination rival to port (and the nagini battery carries
    none for this instance anyway).

  * UNGROUNDED-ORACLE ECHO — DOES NOT APPLY (as the nagini sibling also records).
    The postcondition is GROUNDED: each clause pins ``result`` equal to a term
    built only from the operand accessors at an index computed from the inputs.
    There is no opaque answer key an implementation could echo — the three-way
    banding IS the content. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES; this is the core of the port. Each rival is
    correct on part of the domain but diverges where one clause bites: the
    prepatch right-band over-subtraction, an off-by-one right band, the
    middle-band dropped offset, (for full clause coverage) a left-band shift, and
    the SINGLE-POSITION near-miss that forces the final output column to 0 —
    correct at every point the other four are refuted at, so it is what probes
    whether the obligation pins the whole domain rather than four band formulas.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen tactic script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating
``problem_spec_colInsert`` directly at one concrete input and refuting it. Each
was checked to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology.

This carrier makes the witnesses fully CONCRETE and ``decide``-able: ``Mat.get``
is an ordinary structure field, so a witness instantiates the two operands with
concrete integer accessor lambdas (``fun i j => i*100 + j + 1`` for the host,
its negation for the inserted block — injective, so distinct source columns give
distinct values). No opaque term blocks refutation, so no carrier conditioning is
needed; every witness cancels the ``Id.run``/``bind`` wrapper with
``simp only [Id.run, bind, pure]`` and closes by ``decide``.

BINDER / POINT SPREAD. The spec predicate binds ``self other : Mat`` and
``pos i j : Nat``. The reject witnesses move the discriminating binders rather
than fixing them at one point: ``pos`` takes ``0`` and ``3``; ``other.cols``
takes ``1``, ``2`` and ``3``; and ``j`` ranges over the LEFT band (``j=1<pos``),
the MIDDLE band (``j=4`` in ``[3,5)``), and the RIGHT band (``j=3,5,9`` past the
block). Every one of the three top-level postcondition clauses is attacked by
some rival, and no two rivals share a refutation point. The ``self`` binder takes
a DIFFERENT accessor in each witness (four distinct affine host accessors), so no
rival is refuted only at one host. ``i`` is held at a fixed
row because the banding is row-independent (each clause reads the SAME row ``i``
of an operand — a rival mishandling ``i`` is out of the modeled behavior and has
no faithful patch); this is noted for the coverage report rather than left
unexplained.

AUDIT NOTE (independent re-derivation of the SPEC-TOO-WEAK direction). The
obligation is not merely probed by the rivals below; it is machine-provably
FUNCTIONAL. An audit built, against the frozen file, a proof that any two
``result`` values satisfying ``problem_spec_colInsert`` at the same
``(self, other, pos, i, j)`` are equal (the three guards partition the column
index by ``Nat.lt_or_ge``, so exactly one clause fires and fixes ``result``), and
hence that ANY implementation discharging the frozen obligation is pointwise
equal to the frozen accessor. So there is no wrong implementation of this
accessor that can verify: the SPEC-TOO-WEAK direction is closed on the whole
domain, not just at the five refutation points below, and the value rivals are
sharp probes of a spec already known to be tight. That elaborated at exit 0.
Consistent with it, three further wrong implementations written by the audit and
NOT kept as cases (right band forgetting the shift entirely, ``result``
short-circuited to 0 whenever the inserted block is empty, and the near-miss now
kept as ``partial-domain-last-column-zero``) all failed to verify with
``unsolved goals`` naming exactly the violated clause.

AXIOM lane: EMPTY here. The bundle declares NO ``opaque`` callee and consumes no
``axiom`` — every region of the produced value is read directly off an operand
accessor at a computed index (see the Solution's ``axioms`` region). The nagini
``AXIOM_TESTS`` (new_matrix_cell soundness/containment, output_value fidelity)
belong to the G-AX lane, which this gate ignores; they are dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13647"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# positive that re-proves, the proof region) so same_spec stays byte-identical.

# The three band `return` lines of the impl. Each is the single occurrence in the
# file (the spec states the banding without the `return` keyword), so a _swap on
# any one edits ONLY that clause of the impl.
_I_LEFT = "    return self.get i j"
_I_MID = "    return other.get i (j - pos)"
_I_RIGHT = "  return self.get i (j - other.cols)"

# The whole gold impl body (used by the structural-reshape positives, which
# replace the entire `Id.run do` block).
_I_GOLD_BODY = (
    "def implementation_colInsert\n"
    "    (self other : Mat) (pos i j : Nat) : Int := Id.run do\n"
    "  if j < pos then\n"
    "    return self.get i j\n"
    "  if pos ≤ j ∧ j < pos + other.cols then\n"
    "    return other.get i (j - pos)\n"
    "  return self.get i (j - other.cols)"
)

# The frozen proof body (proof region), minus the `theorem` header line. The
# admissibility positive prepends a ground `have` before this verbatim body, so
# the theorem STATEMENT is untouched and the frozen tactic still closes the goal.
_P_INTRO = "  intro self other pos i j\n"


# ---- shared witness scaffolding ----
# The refutation snippets instantiate the two operands with concrete injective
# integer accessors, so the whole predicate is decidable after the do-wrapper is
# stripped. `_wit` assembles a witness at one concrete input point.
def _wit(pos, i, j, other_cols, self_get="fun i j => (i * 100 + j + 1 : Int)"):
    # `self_get` (the host accessor) is varied across witnesses so the `self`
    # binder is not held at one value — a rival that mishandled the host operand
    # (returned a constant, or read the wrong source) is refuted at more than one
    # host. `other_get` stays injective and sign-flipped from every host so the
    # inserted-block values never collide with a host value.
    other_get = "fun i j => -(i * 100 + j + 1 : Int)"
    self_mat = f"{{ rows := 8, cols := 8, get := {self_get} }}"
    other_mat = f"{{ rows := 8, cols := {other_cols}, get := {other_get} }}"
    return (
        f"example :\n"
        f"    ¬ problem_spec_colInsert\n"
        f"        {self_mat}\n"
        f"        {other_mat}\n"
        f"        {pos} {i} {j}\n"
        f"        (implementation_colInsert\n"
        f"          {self_mat}\n"
        f"          {other_mat}\n"
        f"          {pos} {i} {j}) := by\n"
        f"  unfold problem_spec_colInsert implementation_colInsert\n"
        f"  simp only [Id.run, bind, pure]\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation of
    # the modeled banding cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem statement byte-identical and
    # re-proves inside the proof region for the new impl shape (no helper lemma,
    # no axiom, no `sorry`/`admit`/`native_decide`).
    #
    # Ports nagini case 1 (pos-control-echo-output-value) and case 2
    # (pos-control-band-reorder): the nagini positives (a) collapse the explicit
    # 3-way branch into a direct banded value and (b) reorder the three band
    # guards. Both carry over as reshapes of the single modeled accessor, each
    # with a proof that closes for the new shape.
    # =====================================================================
    {
        "id": "pos-control-pure-branch",
        "kind": "soundness",
        "expect": "verify",
        # Drop the imperative `Id.run do` wrapper AND restate the block guard over
        # TRUNCATED Nat subtraction: `j - pos < other.cols` in place of the
        # conjunction `pos ≤ j ∧ j < pos + other.cols`. Same value on every input
        # (once the left band is excluded, `pos ≤ j`, so `j - pos` does not
        # truncate and the two guards agree), but a DIFFERENT decidable
        # proposition, so the impl is NOT definitionally equal to the frozen one —
        # AUDIT-CHECKED: `example … : alt s o p i j = implementation_colInsert
        # s o p i j := rfl` is REFUTED for this shape (`Type mismatch … rfl`),
        # whereas the earlier version of this case (the same nested if-then-else
        # keeping the frozen conjunction guard verbatim) was closed by `rfl` — it
        # was the frozen impl in different whitespace and tested nothing. The
        # re-proof must now BRIDGE the two guard forms per clause (`omega`), which
        # is the work the previous shape skipped.
        "module": _swap(
            _swap(
                _BASE,
                _I_GOLD_BODY,
                "def implementation_colInsert\n"
                "    (self other : Mat) (pos i j : Nat) : Int :=\n"
                "  if j < pos then self.get i j\n"
                "  else if j - pos < other.cols then other.get i (j - pos)\n"
                "  else self.get i (j - other.cols)",
            ),
            "  intro self other pos i j\n"
            "  unfold problem_spec_colInsert implementation_colInsert\n"
            "  simp only [Id.run, bind, pure]\n"
            "  refine ⟨?_, ?_, ?_⟩\n"
            "  · intro h\n"
            "    simp [h]\n"
            "  · rintro ⟨h1, h2⟩\n"
            "    have hlt : ¬ j < pos := by omega\n"
            "    simp [hlt, h1, h2]\n"
            "  · intro h\n"
            "    have hlt : ¬ j < pos := by omega\n"
            "    have hmid : ¬ (pos ≤ j ∧ j < pos + other.cols) := by omega\n"
            "    simp [hlt, hmid]",
            "  intro self other pos i j\n"
            "  unfold problem_spec_colInsert implementation_colInsert\n"
            "  refine ⟨?_, ?_, ?_⟩\n"
            "  · intro h\n"
            "    simp [h]\n"
            "  · rintro ⟨h1, h2⟩\n"
            "    have hlt : ¬ j < pos := by omega\n"
            "    have hmid : j - pos < other.cols := by omega\n"
            "    simp [hlt, hmid]\n"
            "  · intro h\n"
            "    have hlt : ¬ j < pos := by omega\n"
            "    have hmid : ¬ (j - pos < other.cols) := by omega\n"
            "    simp [hlt, hmid]",
        ),
        "rationale": (
            "structurally-different but CORRECT impl: the imperative `Id.run do` "
            "chain is replaced by a pure nested if-then-else AND the block guard is "
            "restated over truncated `Nat` subtraction (`j - pos < other.cols` for "
            "`pos ≤ j ∧ j < pos + other.cols`). `result` is identical on every "
            "input — below the block band the left guard has already fired, so "
            "`pos ≤ j` and `j - pos` does not truncate — so all three clauses of "
            "`problem_spec_colInsert` still hold. The guard is a DIFFERENT "
            "decidable proposition, so this impl is not definitionally equal to "
            "the frozen one (an audit checked that `rfl` REFUTES the equality, "
            "while the plain nested-if reshape with the frozen conjunction guard "
            "is closed by `rfl` and would have tested nothing): the re-proof has "
            "to bridge the two guard forms per clause with `omega`. Must verify; "
            "if it cannot, the postcondition is SPEC-TOO-STRONG — it would be "
            "pinning the syntactic FORM of the band guard rather than the banded "
            "value. Ports nagini's echo-the-banding positive to the single modeled "
            "accessor."
        ),
    },
    {
        "id": "pos-control-band-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the three band guards: test the RIGHT band first, then the LEFT
        # band, then fall through to the MIDDLE band. The guards still partition
        # every column index identically, so the value is unchanged for every j.
        "module": _swap(
            _swap(
                _BASE,
                _I_GOLD_BODY,
                "def implementation_colInsert\n"
                "    (self other : Mat) (pos i j : Nat) : Int := Id.run do\n"
                "  if pos + other.cols ≤ j then\n"
                "    return self.get i (j - other.cols)\n"
                "  if j < pos then\n"
                "    return self.get i j\n"
                "  return other.get i (j - pos)",
            ),
            "  intro self other pos i j\n"
            "  unfold problem_spec_colInsert implementation_colInsert\n"
            "  simp only [Id.run, bind, pure]\n"
            "  refine ⟨?_, ?_, ?_⟩\n"
            "  · intro h\n"
            "    simp [h]\n"
            "  · rintro ⟨h1, h2⟩\n"
            "    have hlt : ¬ j < pos := by omega\n"
            "    simp [hlt, h1, h2]\n"
            "  · intro h\n"
            "    have hlt : ¬ j < pos := by omega\n"
            "    have hmid : ¬ (pos ≤ j ∧ j < pos + other.cols) := by omega\n"
            "    simp [hlt, hmid]",
            "  intro self other pos i j\n"
            "  unfold problem_spec_colInsert implementation_colInsert\n"
            "  simp only [Id.run, bind, pure]\n"
            "  refine ⟨?_, ?_, ?_⟩\n"
            "  · intro h\n"
            "    have hr : ¬ pos + other.cols ≤ j := by omega\n"
            "    simp [hr, h]\n"
            "  · rintro ⟨h1, h2⟩\n"
            "    have hr : ¬ pos + other.cols ≤ j := by omega\n"
            "    have hlt : ¬ j < pos := by omega\n"
            "    simp [hr, hlt]\n"
            "  · intro h\n"
            "    simp [h]",
        ),
        "rationale": (
            "structurally-different but CORRECT impl: same explicit 3-way band, but "
            "the guards are REORDERED (right band tested first, then left, then the "
            "middle band falls through). The three guards still partition every "
            "column index identically so `result` is unchanged for every input; "
            "the re-proof rules out the reordered earlier guards (`hr`, `hlt`) per "
            "clause. Must verify; if it cannot, SPEC-TOO-STRONG (rejecting a "
            "faithful branch reorder). Ports nagini's band-reorder positive."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the banding
    # is total, so `∀` is unguarded), so the nagini precondition-admission probe
    # (case 3, admiss-f2p-shaped) has no binder to attack here; the honest
    # analogue discharges `problem_spec_colInsert` by evaluation at the issue's
    # ground input (eye(6).col_insert(3, 6x2) — pos=3, other.cols=2, a right-band
    # column) alongside the frozen obligation. Ports nagini case 3.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the issue's ground input (pos=3, other.cols=2,
        # a right-band column j=5) by `decide` in a `have`, then close the frozen
        # obligation verbatim. Nothing is assumed: no new declaration, the theorem
        # statement is byte-identical, the ground instance is a `have` inside the
        # existing tactic body.
        "module": _swap(
            _BASE,
            _P_INTRO,
            "  have _ground : problem_spec_colInsert\n"
            "      { rows := 6, cols := 6, get := fun i j => (i * 100 + j : Int) }\n"
            "      { rows := 6, cols := 2, get := fun i j => -(i * 100 + j : Int) }\n"
            "      3 0 5\n"
            "      (implementation_colInsert\n"
            "        { rows := 6, cols := 6, get := fun i j => (i * 100 + j : Int) }\n"
            "        { rows := 6, cols := 2, get := fun i j => -(i * 100 + j : Int) }\n"
            "        3 0 5) := by\n"
            "    unfold problem_spec_colInsert implementation_colInsert\n"
            "    simp only [Id.run, bind, pure]\n"
            "    decide\n"
            "  intro self other pos i j\n",
        ),
        "rationale": (
            "the obligation is discharged at the issue's ground input "
            "(eye(6).col_insert(3, 6x2): pos=3, other.cols=2, right-band column "
            "j=5) by `decide`, then the frozen obligation is closed verbatim. "
            "Verifies (else the modeled banding is unsatisfiable at exactly the "
            "input the F2P exercises — the analogue of PRECOND-TOO-STRONG). Nothing "
            "is assumed: no new declaration, the theorem statement is "
            "byte-identical, and the ground instance is a `have` inside the "
            "existing tactic body. Ports nagini's admissibility probe."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the frozen
    # spec that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would be
    # a true verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input (checked to
    # hold of the rival and fail on gold).
    # =====================================================================

    # ---- the fix itself: prepatch right band over-subtracts pos (nagini case 5) ----
    {
        "id": "partial-domain-prepatch-right-band",
        "kind": "uniqueness",
        "expect": "reject",
        # The LITERAL pre-patch bug: right band reads self.get i (j - pos -
        # other.cols) instead of self.get i (j - other.cols). Only the right-band
        # return is changed.
        "module": _swap(
            _BASE, _I_RIGHT, "  return self.get i (j - pos - other.cols)"
        ),
        "refinement": (
            "the LITERAL pre-patch regression: the right band over-subtracts `pos`, "
            "reading the host column `j - pos - other.cols` rather than `j - "
            "other.cols`. On the issue's eye(6).col_insert(3, 6x2 of twos) the "
            "trailing identity block is lifted from the bottom rows to the top (the "
            "buggy output in the issue), so the produced entry differs from the "
            "expected matrix and the F2P test FAILS. The canonical "
            "verify-does-not-resolve rival."
        ),
        "rationale": (
            "REJECT from the RIGHT-band clause (pos + other.cols ≤ j → result = "
            "self.get i (j - other.cols)): with pos > 0 and a right-band column the "
            "rival returns self.get i (j - pos - other.cols), a different host "
            "column, so `result` violates the third clause. If it verifies, the "
            "spec does not pin the corrected right-band index (SPEC-TOO-WEAK). "
            "Refuted at pos=3, other.cols=2, right-band j=5."
        ),
        "witness": _wit(pos=3, i=0, j=5, other_cols=2),
    },

    # ---- off-by-one right band (nagini case 6) ----
    # (host accessor differs from every other witness so the `self` binder varies)
    {
        "id": "partial-domain-offbyone-right-band",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one corrected index: right band reads self.get i (j - other.cols +
        # 1). Correct on left/middle bands; shifts every trailing host column by one.
        "module": _swap(
            _BASE, _I_RIGHT, "  return self.get i (j - other.cols + 1)"
        ),
        "refinement": (
            "an off-by-one in the corrected index: the right band reads the host "
            "column `j - other.cols + 1`. On eye(6).col_insert(0, 6x2) (pos=0, "
            "other.cols=2) output column 2 would read host column 1 instead of "
            "host column 0, losing the leading diagonal entry; the produced matrix "
            "is not the expected col_insert result and the F2P test "
            "FAILS. A real off-by-one in the corrected index would not resolve."
        ),
        "rationale": (
            "REJECT from the RIGHT-band clause: self.get i (j - other.cols + 1) "
            "reads a host column one past the pinned `j - other.cols`, so `result` "
            "violates the third clause wherever a right band exists. If it "
            "verifies, the right-band index is unpinned to within ±1 "
            "(SPEC-TOO-WEAK). Refuted at a DISTINCT point from the prepatch rival: "
            "pos=0, other.cols=3, right-band j=3 (moves both the pos and "
            "other.cols binders)."
        ),
        "witness": _wit(pos=0, i=1, j=3, other_cols=3,
                        self_get="fun i j => (i * 7 + 2 * j + 5 : Int)"),
    },

    # ---- middle-band dropped offset (nagini case 7) ----
    {
        "id": "partial-domain-middle-band-offset",
        "kind": "uniqueness",
        "expect": "reject",
        # The block band drops the insertion offset: reads other.get i j instead of
        # other.get i (j - pos). Correct only when pos == 0.
        "module": _swap(_BASE, _I_MID, "    return other.get i j"),
        "refinement": (
            "the inserted-block band drops the insertion offset, reading the "
            "operand at column `j` instead of `j - pos`. On eye(6).col_insert(3, "
            "6x2) (pos=3) the inserted columns at output columns 3,4 would be read "
            "from operand columns 3,4 (outside the width-2 block) rather than 0,1; "
            "the inserted columns are wrong (and out of range for the operand) so "
            "the F2P test FAILS. A patch dropping the `- pos` block "
            "offset would not resolve."
        ),
        "rationale": (
            "REJECT from the MIDDLE-band clause (pos ≤ j ∧ j < pos + other.cols → "
            "result = other.get i (j - pos)): other.get i j disagrees with "
            "other.get i (j - pos) whenever pos > 0, so `result` violates the "
            "second clause. If it verifies, the block-band offset is unpinned "
            "(SPEC-TOO-WEAK). Refuted in the MIDDLE band at pos=3, other.cols=2, "
            "j=4 — the only rival attacking the second clause."
        ),
        "witness": _wit(pos=3, i=2, j=4, other_cols=2,
                        self_get="fun i j => (3 * i + j + 11 : Int)"),
    },

    # ---- left-band shift (clause-coverage rival; no direct nagini analogue) ----
    {
        "id": "partial-domain-left-band-shift",
        "kind": "uniqueness",
        "expect": "reject",
        # Left band reads self.get i (j + 1) instead of self.get i j — shifts the
        # pre-insertion columns. Attacks the FIRST clause, which the value rivals
        # above (all right/middle band) never touch.
        "module": _swap(_BASE, _I_LEFT, "    return self.get i (j + 1)"),
        "refinement": (
            "the left band reads the host at column `j + 1` instead of the host's "
            "own column `j`, corrupting every column left of the insertion point. "
            "On any col_insert with pos > 0 the pre-insertion columns would be "
            "read one column too far right, so the produced matrix disagrees with "
            "the expected result and the F2P test FAILS. A patch "
            "shifting the left band would not resolve."
        ),
        "rationale": (
            "REJECT from the LEFT-band clause (j < pos → result = self.get i j): "
            "self.get i (j + 1) reads a different host column, so `result` violates "
            "the first clause for any left-band column. Included so that ALL THREE "
            "top-level clauses are attacked (the nagini value rivals only exercise "
            "the middle and right bands); if it verifies, the left band is unpinned "
            "(SPEC-TOO-WEAK). Refuted in the LEFT band at pos=3, j=1, other.cols=1 "
            "— the only rival with j < pos, and moving other.cols to 1."
        ),
        "witness": _wit(pos=3, i=2, j=1, other_cols=1,
                        self_get="fun i j => (100 * i + 4 * j + 1 : Int)"),
    },

    # ---- single-position near-miss (nagini case 8) ----
    # This case was MISSING from the port and was added by the audit: the nagini
    # battery's near-miss rival (correct on the whole domain except the final
    # output column, which is forced to 0) has a direct instance on this carrier,
    # because `Mat` carries `cols`, so the accessor can name the last output
    # column as `j + 1 = self.cols + other.cols` without any output container.
    # It is the strongest of the value rivals: it agrees with the frozen accessor
    # at every input the other four rivals refute at, so it probes whether the
    # obligation pins the WHOLE domain rather than a band's index formula.
    {
        "id": "partial-domain-last-column-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # A guard PREPENDED to the frozen banding: at the final output column
        # (j + 1 = self.cols + other.cols) return 0, otherwise fall through to the
        # verbatim frozen three-way band.
        "module": _swap(
            _BASE,
            _I_GOLD_BODY,
            "def implementation_colInsert\n"
            "    (self other : Mat) (pos i j : Nat) : Int := Id.run do\n"
            "  if j + 1 = self.cols + other.cols then\n"
            "    return 0\n"
            "  if j < pos then\n"
            "    return self.get i j\n"
            "  if pos ≤ j ∧ j < pos + other.cols then\n"
            "    return other.get i (j - pos)\n"
            "  return self.get i (j - other.cols)",
        ),
        "refinement": (
            "correct EVERYWHERE except the final output column, which is forced to "
            "0. On the issue's eye(6).col_insert(3, 6x2) the last output column "
            "would read 0 for every row, but its expected values include the "
            "trailing diagonal entry, so the produced matrix is not the expected "
            "col_insert result and the F2P test FAILS. A real one-position "
            "special-case bug would not resolve, so a verifying rival here would "
            "be a true verify-does-not-resolve break."
        ),
        "rationale": (
            "REJECT from whichever band clause covers the final column (here the "
            "RIGHT-band clause: pos + other.cols ≤ j → result = self.get i (j - "
            "other.cols)): the forced 0 differs from the pinned banded value at "
            "that one column. This is the NEAR-MISS probe — the rival agrees with "
            "the frozen accessor at every point the other four rivals are refuted "
            "at, so if it verifies the obligation pins the band index formulas but "
            "leaves a single position of the domain free (SPEC-TOO-WEAK). Refuted "
            "at a point NO other rival uses: pos=3, other.cols=2, j=9 — the last "
            "column of an 8-wide host plus a 2-wide block, moving `j` past every "
            "other witness's range and the `self` binder to a fourth accessor."
        ),
        "witness": _wit(pos=3, i=1, j=9, other_cols=2,
                        self_get="fun i j => (i * 9 + 5 * j + 3 : Int)"),
    },
]


# No AXIOM lane here: the bundle declares no `opaque` callee and consumes no
# `axiom` — every region of the produced value is read directly off an operand
# accessor at a computed index. The nagini AXIOM_TESTS (new_matrix_cell
# soundness/containment, output_value fidelity) belong to the G-AX lane, which
# this gate ignores; dropped.
AXIOM_TESTS = []
