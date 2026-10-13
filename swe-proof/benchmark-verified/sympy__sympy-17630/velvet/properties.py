"""properties.py — G-PBT falsification battery for sympy__sympy-17630 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region is changed — the consumer spec view
elides that region, so ``markers.same_spec`` holds and the
``prove_correct recombineMatrixNode`` obligation survives with a byte-identical
statement). ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  recombineMatrixNode (op : Int) (leadingScalar : Int) (matrixTerms : Int)
      return (out : Int)
    ensures out =
      (if op = additiveOp
       then additiveCombine matrixTerms
       else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))

THREE INPUT binders, all opaque expression handles. ``op`` is the combining
operator in effect: the branch is governed SOLELY by whether it is the
distinguished additive operator. ``matrixTerms`` is the partitioned collection
of matrix-valued terms that both branches compose. ``leadingScalar`` is the
scalar-valued term the multiplicative branch places in front of the collection —
and, crucially, the term the additive branch must NOT place in front of it.
Three opaque callees plus one opaque constant carry the behaviour —
``additiveCombine`` / ``multiplicativeCombine`` (two DISTINCT composers),
``withLeadingScalar`` (the bundle constructor that prepends the scalar), and the
``additiveOp`` sentinel constant. None carries an ``ensures`` — they are
A-referenced free symbols whose only relied-upon property is determinism.

The single load-bearing clause is one equality whose right side is an
if-then-else. It pins two independent sub-decisions:

  (discriminator)  the composition rule is decided by WHICH operator is in
                   effect (``op = additiveOp``) — and by no other quantity;
  (branch->output) the additive branch composes exactly the matrix-valued terms,
                   with NO leading scalar-valued term prepended; the
                   multiplicative branch composes them WITH the leading
                   scalar-valued term prepended. The two are not swapped and
                   neither is collapsed to a constant.

The discriminating behaviour the public issue reports is a branch->output one on
the additive arm: prepending a scalar-valued term in front of a collection of
matrix-valued terms under the additive operator is free to collapse the result
to a scalar-valued term rather than a matrix-valued one, so the additive arm
must compose the matrix-valued terms on their own. Any impl that prepends the
scalar-valued term under the additive operator cannot satisfy the clause on that
arm.

CARRIER NOTE — THE OPAQUE BOUNDARY, and how a witness reaches the post-image.
The result flows through opaque ``additiveCombine`` / ``multiplicativeCombine``
/ ``withLeadingScalar`` and the opaque ``additiveOp`` sentinel, so a ``decide``
on a literal cannot COMPUTE it. Two facts make the reject lane expressible:

  * A witness states the refutation directly over
    ``NonDetT.run (recombineMatrixNode …)`` — a ``Prop``, never IR-compiled —
    which reduces cleanly for this straight-line (loop-free) method.
  * Each witness CONDITIONS on the opaque carrier. It hypothesises just enough
    about the opaque terms at a concrete literal input to separate the rival's
    value from the spec's (one hypothesis to select the branch — ``op`` equal to
    or distinct from ``additiveOp`` — plus one ``≠`` witnessing that the rival's
    returned handle differs from the spec's there), then concludes the program's
    output differs from the spec's. Against the FROZEN impl the same goal reduces
    to a residual ``≠`` the hypothesis cannot close (gold agrees with the spec at
    every input), so the witness FAILS on gold. Both halves verified with real
    builds during authoring.

Every reject witness carries hypotheses about DISTINCT opaque terms and is
jointly satisfiable (the gate's ``consistency_probe`` cannot derive ``False``
from any of them — checked with a real build during authoring: every probe left
an unsolved ``⊢ False`` goal). No ``sorry``/``admit``/``native_decide``/
``axiom`` appears in any witness.

ADVERSARIAL READ of the nagini classes on THIS carrier (see the accounting block
at the foot of the file for the case-by-case port ledger):
  * PRECOND-TOO-STRONG / ADMISSIBILITY — APPLIES, re-aimed. The method carries no
    `require`, so the admitted domain is total and "a normal input is admitted" is
    vacuous as stated; the analogue on a total carrier is the obligation being
    UNSATISFIABLE or DEGENERATE at an F2P-shaped input, which
    `admiss-f2p-shaped-additive-arm` tests directly by discharging the clause's
    right-hand side at the concrete discriminating point before closing the frozen
    obligation verbatim. Do NOT read the absent precondition as making the lane
    inexpressible — an earlier version of this battery did, and that was a defect.
  * PARTIAL-DOMAIN / CONTROL-FLOW — APPLIES, and carries the reject lane. The
    discriminator and the two branch->output arms are transparent structure over
    the opaque callees, so a rival right on part of the input space but wrong on
    a sub-region is the natural falsifier.
  * FRAME / PERMISSION MUTATION — VACUOUS here. This backend is referentially
    transparent; ``op``/``leadingScalar``/``matrixTerms`` are immutable value
    handles with no aliasing and no fractional permission, so there is nothing to
    overwrite. The nagini sibling's own header states the same for its surface —
    all four of its inputs are pass-by-value primitives, so it holds no read-only
    ``Acc(.,1/2)`` input and records the frame-mutation class as N/A there too.
    No permission substitute is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The spec carries no pure helper/oracle; the
    postcondition is stated directly over the opaque callees via the
    if-then-else. There is nothing an impl could echo.
  * DIVERGENCE / NON-TERMINATION — VACUOUS here, and MEASURED so during the
    independent audit (correcting an earlier claim in this file, which described
    the semantics this bundle carried when the battery was authored; see item (5)
    of the audit block for the provenance). This bundle now carries
    ``set_option loom.semantics.termination "total"`` (Solution.lean line 4), NOT
    ``"partial"``, so the verifier discharges a termination obligation and a
    diverging impl is REJECTED rather than vacuously verified. Measured with real
    builds: five loop-bearing rivals (an ``Int`` counter spinning upward, a
    ``while true``, a spin on the additive arm only, a ``for`` loop, and even a
    STRUCTURALLY TERMINATING ``while 0 < i do i := i - 1``) all fail at exit 1
    with ``error: Decreasing annotations are required in total correctness
    semantics``. A SIXTH rival, added by re-measurement, closes the obvious gap in
    that list: one that DOES carry a measure, so its refusal cannot be read as the
    annotation linter alone. ``let mut k : Nat := 1`` / ``while k > 0`` with
    ``invariant k > 0``, ``done_with k = 0``, ``decreasing k``, body ``k := k + 1``,
    spliced at the impl anchor with each proof reduced to a bare ``loom_solve``, is
    REJECTED at exit 1 on the measure's OWN descent goal,
    ``case decreasing_1: k ... |- k + 1 < k``, reported as ``unsolved goals``. So
    the annotation is required to be TRUE and not merely present, and the class is
    closed on a real proof obligation rather than by a lint. The class is
    nevertheless NOT shippable as a reject case, for a reason that is about the
    carrier and not about the spec: in the annotation-free shape the failure is a
    FRONTEND error raised before any obligation is attempted, and the elaborator
    injects ``sorry`` into the generated ``WPGen`` term. So the witness file
    built over such a rival cannot elaborate either — a witness asserting only
    ``(1:Nat) + 1 = 2`` was built against the loop-bearing rival and failed with
    that same ``Decreasing annotations`` error (exit 1), while the identical
    witness against the frozen solution succeeded (exit 0). A rival no witness
    can be stated over cannot be attributed to the spec, and the mechanical
    escape hatches are all out of scope: adding a ``decreasing`` clause or a
    file-level ``set_option loom.linter.errors false`` both change the spec view
    (``same_spec`` fails), and a ``set_option ... in`` scoped inside the impl
    region does not parse. Recorded as REJECTED BY THE SPEC and unshippable for a
    witness-side reason. NOT a spec hole. The earlier label "vacuous class" is
    also withdrawn as imprecise: the class is not empty, since a diverging rival is
    perfectly writable here; it is refused, in both the annotated and the
    annotation-free shape.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-17630"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The gold impl's CODE block (the four lines strictly
# ---- inside -- impl-start / -- impl-end, after the descriptive comment). It
# ---- lies wholly inside the single impl region and is unique in Solution.lean
# ---- (both asserted at load by _swap). Every variant replaces exactly this
# ---- block; the spec, the method signature and the `prove_correct` header are
# ---- untouched, so same_spec holds and the obligation survives (its frozen
# ---- tactic script no longer closes a reshaped impl — which is the point; the
# ---- rejection is attributed to the spec by the witness, not to broken tactics).
_GOLD_CODE = (
    "    if op = additiveOp then\n"
    "      return additiveCombine matrixTerms\n"
    "    else\n"
    "      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)"
)
assert _BASE.count(_GOLD_CODE) == 1, "impl-body anchor drift — re-sync _GOLD_CODE"


def _variant(body):
    return _swap(_BASE, _GOLD_CODE, body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the clause
    # is SPEC-TOO-STRONG. Each keeps the `ensures` obligation and the frozen
    # `prove_correct … by loom_solve` body; the straight-line branch reshapes
    # leave the returned handle definitionally identical on every input, so
    # `loom_solve` closes unchanged (both verified with real builds).
    # =====================================================================
    {
        "id": "pos-control-demorgan-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Negate the discriminator test and swap the two branch BODIES to match
        # (De-Morgan-equivalent control flow). Still keyed to `op = additiveOp`;
        # returns the identical handle on every input.
        "module": _variant(
            "    if op ≠ additiveOp then\n"
            "      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)\n"
            "    else\n"
            "      return additiveCombine matrixTerms"),
        "rationale": (
            "structurally-different but CORRECT impl: negates the discriminator "
            "test and swaps the two branch BODIES to match "
            "(De-Morgan-equivalent control flow), still keyed to op = additiveOp, "
            "so out equals the if-then-else on every input. Straight-line two-way "
            "branch — no induction/lemma — so the frozen `loom_solve` obligation "
            "still discharges. Must verify; if it cannot, the clause is "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-let-inline",
        "kind": "soundness",
        "expect": "verify",
        # Same gold behavior with the additive composition bound to a local
        # BEFORE the branch (hoisted). Determinism of the opaque callee makes the
        # hoisted `additiveCombine matrixTerms` denote the same value; the
        # multiplicative branch is unchanged.
        "module": _variant(
            "    let addComposed := additiveCombine matrixTerms\n"
            "    if op = additiveOp then\n"
            "      return addComposed\n"
            "    else\n"
            "      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)"),
        "rationale": (
            "same gold behavior with the additive composition hoisted into a local "
            "bound before the branch. The opaque composer is a deterministic map, "
            "so the hoisted additiveCombine matrixTerms denotes the same value and "
            "out equals the if-then-else on every input; the frozen `loom_solve` "
            "obligation discharges. Must verify; if it cannot, the spec pins the "
            "code shape rather than the behavior (SPEC-TOO-STRONG)."),
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane) — added during the independent
    # audit, which found the lane missing entirely. This method has NO `require`
    # clause, so "a normal input satisfies the precondition" is vacuous; the
    # analogue on a TOTAL carrier is the obligation being UNSATISFIABLE or
    # DEGENERATE at exactly an F2P-shaped input, which a positive that discharges
    # the obligation AT THAT CONCRETE INPUT — by evaluation, as a `have`, before
    # closing the frozen obligation verbatim — tests directly. The gold impl
    # lines are re-emitted byte-identically after the `have`, so the real
    # obligation still discharges in full generality under the untouched frozen
    # `loom_solve`.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-additive-arm",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    have _h_admissible :\n"
            "        (if additiveOp = additiveOp then additiveCombine matrixTerms\n"
            "         else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))\n"
            "          = additiveCombine matrixTerms\n"
            "        ∧ (∀ q : Int, q ≠ additiveOp →\n"
            "            (if q = additiveOp then additiveCombine matrixTerms\n"
            "             else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))\n"
            "              = multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))\n"
            "        ∧ (∀ q : Int, q ≠ additiveOp →\n"
            "            additiveCombine matrixTerms\n"
            "              ≠ multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms) →\n"
            "            (if additiveOp = additiveOp then additiveCombine matrixTerms\n"
            "             else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))\n"
            "              ≠ (if q = additiveOp then additiveCombine matrixTerms\n"
            "                 else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))) := by\n"
            "      refine ⟨by simp, ?_, ?_⟩\n"
            "      · intro q hq; simp [hq]\n"
            "      · intro q hq hne; simp [hq]; exact hne\n"
            + _GOLD_CODE),
        "rationale": (
            "PRECOND-TOO-STRONG lane, re-aimed for a total carrier with an EMPTY "
            "pre-conditions region: the admitted domain is total, so the residual "
            "risk is not a rejected input but an obligation that is UNSATISFIABLE "
            "or DEGENERATE at the F2P-shaped input — the ADDITIVE arm, i.e. "
            "op = additiveOp, which is the arm the discriminating change serves. "
            "The `have` discharges the clause's own right-hand side at that "
            "concrete point by EVALUATION, not by restating the ensures, and its "
            "three conjuncts pin three separate things: (a) at op = additiveOp the "
            "post-image really is additiveCombine matrixTerms — the terms composed "
            "ALONE, so the obligation is satisfiable exactly where the change "
            "bites; (b) at every op distinct from additiveOp it is instead the "
            "multiplicative composition over the leading-scalar bundle, so the "
            "obligation is live on BOTH branches of the discriminator and not only "
            "on the one the gold impl happens to take first; (c) NON-DEGENERACY — "
            "wherever the two composed handles genuinely differ, the two arms' "
            "post-images differ too, so the clause is not degenerately satisfied by "
            "an if-then-else whose branches coincide. Conjunct (c) is what "
            "distinguishes this from a tautology: on an opaque carrier the two arms "
            "COULD be identified, and then every uniqueness rival in this battery "
            "would be attacking a distinction the spec does not actually draw. "
            "Liveness measured during the audit by flipping conjuncts (a) and (c) "
            "to their negations — both flipped forms FAIL to elaborate (exit 1, "
            "`unsolved goals`), so the `have` is load-bearing rather than vacuous. "
            "If this case FAILS => PRECOND-TOO-STRONG: the obligation cannot be met "
            "at the very input the change exists to serve, which no uniqueness "
            "rival would localize."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each straight-line (so its `NonDetT.run` term
    # reduces) with a machine-checked refutation witness conditioning on the
    # opaque carrier, and the refinement argument for why its faithful real
    # counterpart would NOT resolve the F2P (test_zero_matrix_add,
    # test_issue_17624).
    # =====================================================================

    # ---- branch->output, ADDITIVE arm: the additive branch must NOT prepend the
    # ---- leading scalar-valued term (the LITERAL discriminating fix) ----
    {
        "id": "uniq-additive-prepends-scalar",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch defect: under the additive operator, prepend the leading
        # scalar-valued term in front of the matrix-valued terms (as the
        # multiplicative branch does) instead of composing them on their own. The
        # combiner is still selected by the operator, but the additive arm wrongly
        # carries the leading scalar. This is exactly what the one-branch fix
        # repairs.
        "module": _variant(
            "    if op = additiveOp then\n"
            "      return additiveCombine (withLeadingScalar leadingScalar matrixTerms)\n"
            "    else\n"
            "      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)"),
        "refinement": (
            "this is the pre-patch tail: under the additive operator it prepends "
            "the operator's scalar identity in front of the matrix-valued terms "
            "before composing, instead of composing them on their own. On the "
            "reported reproducer that scalar-identity prepend collapses the "
            "additive result to a scalar-valued term rather than a matrix-valued "
            "one, so the recombined node no longer exposes the matrix interface the "
            "downstream block collapse needs — test_zero_matrix_add and "
            "test_issue_17624 stay RED. A faithful patch keeping the prepend on the "
            "additive arm would NOT resolve."),
        "rationale": (
            "REJECT from the clause's ADDITIVE arm: it demands out = "
            "additiveCombine matrixTerms (the terms alone), and this impl returns "
            "additiveCombine (withLeadingScalar leadingScalar matrixTerms). Refuted "
            "at op=0 (=additiveOp), leadingScalar=1, matrixTerms=2, where the two "
            "composed handles differ. If it verifies, the spec does not pin that "
            "the additive arm omits the leading scalar (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : (0:Int) = additiveOp)\n"
            "        (h2 : additiveCombine (withLeadingScalar 1 2) ≠ additiveCombine 2) :\n"
            "    NonDetT.run (recombineMatrixNode 0 1 2)\n"
            "      ≠ DivM.res (if (0:Int) = additiveOp then additiveCombine 2 else multiplicativeCombine (withLeadingScalar 1 2)) := by\n"
            "  unfold recombineMatrixNode\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- branch->output, MULTIPLICATIVE arm: the multiplicative branch MUST
    # ---- prepend the leading scalar-valued term (the unchanged else clause) ----
    {
        "id": "uniq-multiplicative-drops-scalar",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary error on the OTHER arm: under the multiplicative
        # operator, compose the matrix-valued terms on their own, dropping the
        # leading scalar-valued term the else clause must prepend. Correct on the
        # additive arm (a near-miss to uniq-additive-prepends-scalar), wrong on the
        # multiplicative arm — so it is refuted at a DIFFERENT, disjoint input.
        "module": _variant(
            "    if op = additiveOp then\n"
            "      return additiveCombine matrixTerms\n"
            "    else\n"
            "      return multiplicativeCombine matrixTerms"),
        "refinement": (
            "drops the leading scalar-valued term on the multiplicative arm, "
            "composing the matrix-valued terms on their own where the else clause "
            "must place the scalar in front of them. HONEST SCOPE OF THIS CASE "
            "(re-measured during audit, correcting an earlier over-claim): this "
            "rival is refuted by the SPEC, not by the test suite. On the modeled "
            "tail no scalar-valued term remains, so the leading term is the "
            "operator's own identity element, and the real multiplicative composer "
            "is free to absorb an identity factor — so a faithful real counterpart "
            "that omitted the leading term would be behaviour-preserving THERE and "
            "would still hold the matrix-product paths. This case therefore attests "
            "that the frozen clause pins the else arm's bundle SHAPE (the model's "
            "bundle constructor is opaque, so the two composed handles are "
            "genuinely distinct at the point the witness names), and it does NOT "
            "claim an F2P/PASS_TO_PASS divergence. Kept because that shape pin is "
            "real spec content and otherwise unattacked; see the accounting block's "
            "MODELING-FIDELITY note for why the model is deliberately coarser than "
            "the repo here."),
        "rationale": (
            "REJECT from the clause's MULTIPLICATIVE arm: it demands out = "
            "multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms) but "
            "this impl returns multiplicativeCombine matrixTerms. Refuted at op=1 "
            "(≠ additiveOp), leadingScalar=3, matrixTerms=4, where the two composed "
            "handles differ — the composer and the bundle constructor are opaque, so "
            "nothing identifies those handles and the hypothesis separating them is "
            "satisfiable (the gate's consistency probe leaves ⊢ False unsolved). "
            "Attacks the else arm — disjoint from uniq-additive-prepends-scalar, "
            "which is correct here. If it verifies, the multiplicative arm's "
            "leading-scalar requirement is unpinned (SPEC-TOO-WEAK). Scope caveat: "
            "this is a SHAPE pin on the model, not a test-suite divergence — see "
            "`refinement`."),
        "witness": (
            "example (h1 : ¬ ((1:Int) = additiveOp))\n"
            "        (h2 : multiplicativeCombine 4 ≠ multiplicativeCombine (withLeadingScalar 3 4)) :\n"
            "    NonDetT.run (recombineMatrixNode 1 3 4)\n"
            "      ≠ DivM.res (if (1:Int) = additiveOp then additiveCombine 4 else multiplicativeCombine (withLeadingScalar 3 4)) := by\n"
            "  unfold recombineMatrixNode\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- discriminator: the composition rule must be governed by the operator,
    # ---- not fixed to the additive composer regardless of it ----
    {
        "id": "uniq-ignore-op-always-additive",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the operator entirely and always compose additively (matrix
        # terms alone). Correct on the additive arm, wrong on the multiplicative
        # arm — where it both uses the wrong composer AND drops the leading scalar.
        "module": _variant("    return additiveCombine matrixTerms"),
        "refinement": (
            "ignores the operator and always composes additively, so a "
            "multiplicative node is recombined with the additive composer and "
            "without its leading scalar. Its faithful counterpart would recombine "
            "every product node as if it were a sum — a structurally wrong node on "
            "the whole multiplicative domain — so the matrix-product PASS_TO_PASS "
            "paths break; it would NOT resolve."),
        "rationale": (
            "REJECT from the clause's DISCRIMINATOR: on the multiplicative arm "
            "(op ≠ additiveOp) out must be multiplicativeCombine (withLeadingScalar "
            "leadingScalar matrixTerms) but the impl returns additiveCombine "
            "matrixTerms. Refuted at op=5 (≠ additiveOp), leadingScalar=6, "
            "matrixTerms=7, where the two handles differ. If it verifies, the "
            "operator no longer governs the composition rule (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : ¬ ((5:Int) = additiveOp))\n"
            "        (h2 : additiveCombine 7 ≠ multiplicativeCombine (withLeadingScalar 6 7)) :\n"
            "    NonDetT.run (recombineMatrixNode 5 6 7)\n"
            "      ≠ DivM.res (if (5:Int) = additiveOp then additiveCombine 7 else multiplicativeCombine (withLeadingScalar 6 7)) := by\n"
            "  unfold recombineMatrixNode\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- discriminator (complement): fixed to the multiplicative composer,
    # ---- ignoring the operator — wrong on the additive arm ----
    {
        "id": "uniq-ignore-op-always-multiplicative",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary degenerate rival: ignore the operator and always
        # compose multiplicatively with the leading scalar prepended. On the
        # additive arm (where the terms must be composed alone) it both uses the
        # wrong composer and prepends the leading scalar.
        "module": _variant("    return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)"),
        "refinement": (
            "ignores the operator and always composes multiplicatively with the "
            "leading scalar prepended, so an additive node is recombined with the "
            "multiplicative composer AND carries the leading scalar it must omit — "
            "the reported scalar-collapse failure reached on the whole additive "
            "domain. Its faithful counterpart never takes the additive-only branch, "
            "so test_zero_matrix_add / test_issue_17624 stay RED; it would NOT "
            "resolve. Complementary degenerate rival to "
            "uniq-ignore-op-always-additive."),
        "rationale": (
            "REJECT from the clause's DISCRIMINATOR on the additive arm: "
            "op=0 (=additiveOp) demands out = additiveCombine matrixTerms but the "
            "impl returns multiplicativeCombine (withLeadingScalar leadingScalar "
            "matrixTerms). Refuted at op=0, leadingScalar=8, matrixTerms=9, where "
            "the two handles differ. If it verifies, the operator no longer governs "
            "the composition rule on the additive arm (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : (0:Int) = additiveOp)\n"
            "        (h2 : multiplicativeCombine (withLeadingScalar 8 9) ≠ additiveCombine 9) :\n"
            "    NonDetT.run (recombineMatrixNode 0 8 9)\n"
            "      ≠ DivM.res (if (0:Int) = additiveOp then additiveCombine 9 else multiplicativeCombine (withLeadingScalar 8 9)) := by\n"
            "  unfold recombineMatrixNode\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- ARMS SWAPPED: both composers used, each on the WRONG arm. Added
    # ---- during audit: the four rivals above each get ONE arm wrong or fix the
    # ---- rule to one arm, so none of them catches an impl that keeps both
    # ---- composers and both bundle shapes and merely exchanges them. This is
    # ---- the rival that pins the PAIRING of operator to composition rule.
    {
        "id": "uniq-arms-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    if op = additiveOp then\n"
            "      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)\n"
            "    else\n"
            "      return additiveCombine matrixTerms"),
        "refinement": (
            "keeps both composition rules and both bundle shapes but exchanges "
            "which operator selects which, so EVERY node is recombined by the other "
            "operator's rule. On the additive arm it applies the multiplicative "
            "composition with the leading scalar-valued term prepended — precisely "
            "the scalar-collapse the discriminating fix removes — so the additive "
            "reproducers stay RED; and on the multiplicative arm it applies the "
            "additive composition, which recombines a product node as a sum and "
            "breaks the matrix-product paths. Wrong on the WHOLE domain in both "
            "directions, so it resolves nothing. Distinct from the two "
            "ignore-op degenerates: those collapse to a single rule and are "
            "correct on one arm, whereas this one is wrong on both."),
        "rationale": (
            "REJECT from the clause's DISCRIMINATOR->BRANCH pairing: at "
            "op=0 (=additiveOp) the clause demands out = additiveCombine "
            "matrixTerms and this impl returns multiplicativeCombine "
            "(withLeadingScalar leadingScalar matrixTerms). Refuted at op=0, "
            "leadingScalar=1, matrixTerms=2. Its rejection cannot be attributed to "
            "a missing composer or a missing bundle shape — both are present and "
            "reachable — only to the pairing, which no other case pins. If it "
            "verifies, the clause fixes the SET of composition rules without "
            "fixing which operator selects which (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : (0:Int) = additiveOp)\n"
            "        (h2 : multiplicativeCombine (withLeadingScalar 1 2) ≠ additiveCombine 2) :\n"
            "    NonDetT.run (recombineMatrixNode 0 1 2)\n"
            "      ≠ DivM.res (if (0:Int) = additiveOp then additiveCombine 2 else multiplicativeCombine (withLeadingScalar 1 2)) := by\n"
            "  unfold recombineMatrixNode\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- The BUNDLE CONSTRUCTOR's argument ORDER — the one sub-decision in the
    # ---- clause no shipped rival moved. Added during audit.
    {
        "id": "uniq-leading-scalar-arg-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    if op = additiveOp then\n"
            "      return additiveCombine matrixTerms\n"
            "    else\n"
            "      return multiplicativeCombine (withLeadingScalar matrixTerms leadingScalar)"),
        "refinement": (
            "builds the multiplicative arm's argument bundle with the two operands "
            "EXCHANGED: the collection of matrix-valued terms is placed in the "
            "leading position and the scalar-valued term behind it, where the clause "
            "requires the scalar-valued term to lead. Its faithful counterpart hands "
            "the composer's constructor a differently-ordered argument bundle, so the "
            "recombined product node is built over the wrong operand sequence — for "
            "a non-commutative matrix product the operand order is load-bearing, so "
            "the matrix-product paths do not reproduce the gold canonical form and "
            "the suite would not stay resolved. Correct on the additive arm, so it "
            "is a near-miss refuted at a multiplicative input."),
        "rationale": (
            "REJECT from the clause's MULTIPLICATIVE arm at the level of the bundle "
            "CONSTRUCTOR's operand order: the clause demands out = "
            "multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms) and "
            "this impl returns multiplicativeCombine (withLeadingScalar matrixTerms "
            "leadingScalar). Refuted at op=1 (≠ additiveOp), leadingScalar=3, "
            "matrixTerms=4, where the bundle handles differ — the constructor is "
            "opaque and NOT symmetric in its two arguments, so nothing identifies "
            "withLeadingScalar 4 3 with withLeadingScalar 3 4 and the hypothesis is "
            "satisfiable. The two leading-scalar rivals above move only the term's "
            "PRESENCE, so a rival that keeps it present but in the wrong position is "
            "caught by nothing else. If it verifies, the clause pins only which "
            "handles the bundle mentions and not their order (SPEC-TOO-WEAK)."),
        "witness": (
            "example (h1 : ¬ ((1:Int) = additiveOp))\n"
            "        (h2 : multiplicativeCombine (withLeadingScalar 4 3) ≠ multiplicativeCombine (withLeadingScalar 3 4)) :\n"
            "    NonDetT.run (recombineMatrixNode 1 3 4)\n"
            "      ≠ DivM.res (if (1:Int) = additiveOp then additiveCombine 4 else multiplicativeCombine (withLeadingScalar 3 4)) := by\n"
            "  unfold recombineMatrixNode\n"
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness rivals — one of which is a divergence
# rival) plus an empty AXIOM_TESTS lane this gate ignores. The carrier here is
# NARROWER than nagini's: nagini contracts the whole `postprocess(is_sum,
# num_matrices, num_scalars, has_explicit_matrix) -> Combo` surface with three
# boolean/count facets (E1 matrix count, E2 sum-never-scalar, E3 product scalar
# rule) over a partition that may leave a genuine scalar term; this velvet bundle
# models ONLY the recombination TAIL reached when the matrix-valued terms are
# non-empty and NO scalar-valued term remains to compose among them (mapping.md).
# That tail is exactly the two-line additive-vs-multiplicative dispatch the fix
# edits. So most nagini cases attach to a sub-domain (num_scalars>0 / the count
# facet) this bundle does not model, and have no counterpart — carrier narrowing,
# not an omission of convenience.
#
#   nagini case                          -> here                               status
#   --------------------------------------------------------------------------------
#   pos-control-reordered                -> pos-control-demorgan-reorder        PORTED
#   (+ pos-control-let-inline)           -> pos-control-let-inline              ADDED (2nd positive)
#   admiss-sum-no-scalar                 -> admiss-f2p-shaped-additive-arm      PORTED (audit: re-aimed, see below)
#   uniq-prepatch-sum-inject-identity    -> uniq-additive-prepends-scalar       PORTED
#   uniq-sum-always-scalar-supporting    -> uniq-additive-prepends-scalar       COLLAPSED (same rival here)
#   uniq-sum-with-scalar-contaminates    -> (none)                             OMITTED (num_scalars>0 tail unmodeled)
#   uniq-product-no-absorb               -> (none)                             OMITTED (num_scalars>0 tail unmodeled)
#   uniq-product-phantom-scalar          -> (none)                             OMITTED (boolean scalar-arg facet unmodeled)
#   uniq-wrong-matrix-count              -> (none)                             OMITTED (count facet unmodeled)
#   uniq-nonterm-vacuous                 -> (none)                             VACUOUS (total semantics; measured)
#   (+ multiplicative-arm / discriminator coverage)                            ADDED (3 rivals, see below)
#   (+ uniq-arms-swapped)                                                      ADDED (audit: pairing pin)
#   (+ uniq-leading-scalar-arg-order)                                          ADDED (audit: bundle operand order)
#
# 2 soundness positives (1 ported + 1 added), 1 admissibility positive (ported
# and re-aimed during the audit), and 6 uniqueness rivals shipped; 5 nagini
# uniqueness rivals omitted by carrier narrowing, 1 collapsed, 1 recorded as a
# VACUOUS class (divergence, measured under total semantics). No case was dropped
# because its proof/witness was hard; every shipped rival's witness was seen to
# discriminate with real builds.
#
# ---------------------------------------------------------------------------
# SECOND INDEPENDENT AUDIT (a later, separate pass; its findings are folded into
# the numbered list below as items (5)-(7)). All SIX shipped reject cases were
# rebuilt — witness against the rival, witness against the frozen solution,
# consistency probe — reproducing exit 0 / 1 / 1 for every one. The gold-side
# failure is `Type mismatch  h2  has type <handle> ≠ <handle>  but is expected to
# have type False`, i.e. `simp` discharged the branch and reduced the goal to
# `False` for the frozen impl.
#
# That signature is not a plain evaluation, so it was additionally subjected to
# the FORGERY test rather than merely read as semantic. For each of the six cases
# a second file was built differing from the witness ONLY in its claim — `≠`
# flipped to `=`, asserting the frozen impl AGREES with the spec at the witnessed
# point, with the final `exact h2` dropped. The result inverts cleanly for all
# six: the flipped claim BUILDS against the frozen solution (exit 0) and FAILS
# against the rival (exit 1, `unsolved goals` with the residual goal printed as
# `⊢ additiveCombine (withLeadingScalar 1 2) = additiveCombine 2`). So gold's exit
# code tracks the claim rather than the file's shape, and the witnesses are
# genuine discriminators. Each consistency probe left `⊢ False` unsolved, so no
# witness argues from a contradiction.
#
# FIRST INDEPENDENT AUDIT (adversarial re-derivation of the recorded verdict).
# Every shipped reject case was rebuilt three ways by hand — witness against the
# rival, witness against the frozen solution, consistency probe — and all four
# original rivals reproduced exit 0 / 1 / 1 with a SEMANTIC gold-side failure:
# `simp` closes the branch and reduces the goal to `False`, leaving the residual
# `h2 : <handle> ≠ <handle>` against an expected `False`. Not a missing
# identifier, not a stuck reduction, not a timeout — the frozen impl agrees with
# the clause at each witnessed point, which is exactly what must make the witness
# fail there. Each consistency probe left `⊢ False` unsolved, so no witness
# argues from a contradiction.
#
# Six defects were found and repaired across the two audits — (1)-(3) by the
# first, (5)-(7) by the second — and one modeling limit is recorded rather than
# patched away:
#
#  (1) OVER-CLAIM, corrected. uniq-multiplicative-drops-scalar previously
#      asserted its faithful counterpart loses a genuine scalar coefficient and
#      breaks the matrix-product paths. Measured against the real library at
#      base_commit: on the MODELED tail no scalar-valued term remains, so the
#      leading term is the operator's own identity element, and the real
#      multiplicative composer absorbs an identity factor — the composed result
#      is structurally identical with and without it at every input tried
#      (matrix symbols, a single factor, a zero matrix, an identity, explicit
#      dense matrices, three factors). Its `refinement` now states the honest
#      scope: the case pins the else arm's bundle SHAPE on the model and claims
#      no test-suite divergence. The case is KEPT, not dropped — see (4).
#  (2) FABRICATED CITATION, corrected. The class read-out cited a nagini field
#      `has_readonly_input=false` for this instance. No such field exists in the
#      sibling bundle — the only occurrence anywhere in the tree was this file's
#      own sentence. The conclusion is right and the sibling does state it in
#      prose, so the claim now cites what the sibling actually says.
#  (3) COVERAGE GAP, closed. The four original rivals each get one arm wrong or
#      fix the rule to one arm, and all four move the leading scalar's PRESENCE
#      only. Two sub-decisions were therefore unattacked, and each admits a wrong
#      impl the battery would have missed: the operator->rule PAIRING (both
#      composers kept, merely exchanged) and the bundle constructor's OPERAND
#      ORDER (scalar kept but not leading). Added as uniq-arms-swapped and
#      uniq-leading-scalar-arg-order; both were confirmed rejected with a
#      hand-checked discriminating witness before being shipped.
#  (4) MODELING FIDELITY (recorded, NOT a spec edit). Because the modeled tail
#      always supplies the operator's identity as the leading term, the else
#      arm's `withLeadingScalar` distinction is finer on the model than on the
#      library: the model's bundle constructor is opaque and therefore not
#      identity-absorbing, so the spec separates two handles the library
#      identifies. This makes the spec STRONGER than the repo on that arm — the
#      safe direction for a uniqueness battery (it can reject a
#      behaviour-preserving reshape, never admit a wrong impl), and it is why
#      case (1) is a shape pin rather than a resolve claim. It is a property of
#      the frozen spec and the frozen mapping, so it is documented and escalated
#      here, never edited: a spec change must re-clear the equivalence and
#      leakage gates outside this lane.
#  (5) STALE SEMANTICS CLAIM, corrected (second audit). Both the header's class
#      read-out and the accounting block asserted that this bundle carries
#      `set_option loom.semantics.termination "partial"` and concluded that
#      divergence is an open, escalated KNOWN SPEC HOLE. Solution.lean line 4 reads
#      `"total"`. PROVENANCE, re-established: the corpus-wide move to total
#      semantics is COMPLETE, the committed file at HEAD now reads `"total"` on
#      line 4 and `open TotalCorrectness DemonicChoice` on line 7, and 500 of 500
#      velvet bundles are `"total"` with none `"partial"` (the interim "494 of 500,
#      6 partial" census recorded here was a snapshot mid-sweep and is superseded).
#      Note also that the option is not inert: its own elaborator opens the matching
#      scope (`Loom/MonadAlgebras/WP/Options.lean`, `openScope`), so the
#      `set_option` and the surrounding `open` cannot disagree. So the prose was accurate when it was
#      authored and went stale underneath a frozen file that changed; it is not a
#      misreading by the port. It still had to be corrected, because a battery is
#      read against the artifact it ships beside, and the correction is not
#      cosmetic: under `total` the disposition INVERTS — the verifier
#      discharges a termination obligation, so a diverging rival is rejected, not
#      vacuously verified — which means the file was claiming a spec-strength gap
#      the frozen artifact does not have. Re-measured with real builds (five loop
#      shapes, all exit 1 on `Decreasing annotations are required in total
#      correctness semantics`) and both passages rewritten; the class is now
#      recorded as VACUOUS with the reason demonstrated, and the residual reason
#      it is still not shippable as a reject case is the frontend/`sorry` behaviour
#      documented there, not a property of the spec.
#  (6) MISSING ADMISSIBILITY LANE, closed (second audit). The battery shipped
#      soundness and uniqueness only, so of the three directions this gate exists
#      to test, PRECOND-TOO-STRONG was untested; scripts/pbt_coverage.py reports
#      exactly this. The dropped nagini case had been justified by "this method has
#      no precondition", which is not a demonstration of vacuity. Landed as
#      admiss-f2p-shaped-additive-arm, which discharges the frozen obligation's own
#      right-hand side at the concrete discriminating input by evaluation, in a
#      `have`, before closing the frozen obligation verbatim over the free
#      parameters. Verified (exit 0) and in scope (variant_problems == []).
#  (7) TAUTOLOGY GUARD on the new positive (second audit). A `have` that merely
#      restates the ensures would pass while testing nothing, so each conjunct was
#      flip-tested: replacing conjunct (a) with the claim that the additive arm
#      yields the multiplicative value, and conjunct (c) with the claim that the
#      two arms AGREE, each fails to elaborate (exit 1, `unsolved goals`). The
#      `have` is therefore load-bearing in both the satisfiability and the
#      non-degeneracy direction.
#
# SPEC-TOO-WEAK probe (attack D) — 7 NEW wrong impls the battery did not
# contain, each built and, where its witness landed, hand-checked. ALL 7 were
# REJECTED by the frozen spec; NO spec hole was found. Two are now shipped as (3)
# above. The other five: the additive arm using the wrong composer on the right
# handle; the additive arm composing the scalar handle instead of the matrix
# handle; the additive arm composing a perturbed handle (the carrier analogue of
# nagini's matrix-count attack); the multiplicative arm prepending the leading
# term TWICE (the analogue of its phantom-scalar attack); and the discriminator
# keyed to `leadingScalar` instead of `op`. All five were rejected. The last is
# not shipped because its refutation needs a different witness script than the
# shipped shape (the branch is selected via a hypothesis on a different binder)
# and uniq-arms-swapped already pins the discriminator's subject more directly.
#
# SPEC-TOO-WEAK probe, SECOND audit (attack D again, independently authored) — 8
# further NEW wrong impls, aimed at the sub-decisions the shipped rivals leave
# least probed. ALL 8 were REJECTED by the frozen spec (exit 1, `unsolved goals`);
# NO spec hole was found, in agreement with the first audit. They were: the
# additive arm with the wrong composer; the additive arm composing the SCALAR
# handle instead of the matrix handle; the multiplicative arm prepending the
# leading term TWICE; the discriminator keyed to `leadingScalar` instead of `op`;
# the multiplicative arm returning the bare BUNDLE with no composer applied; the
# additive arm returning the RAW `matrixTerms` handle uncomposed; the additive arm
# double-composing (`additiveCombine (additiveCombine …)`); and a bundle built
# from `leadingScalar` twice, losing `matrixTerms` entirely. The last four are new
# to this audit and probe the composer's PRESENCE and the bundle's operand
# IDENTITY, which the earlier set did not separate from operand ORDER.
#
# SPEC-TOO-STRONG probe, SECOND audit (attack E again) — 7 NEW correct reshapes,
# 6 of which VERIFY: the whole if-then-else bound to one local and returned; the
# guard-plus-fallthrough shape with no `else`; the multiplicative composition
# hoisted ahead of the branch; a DOUBLE-NEGATED guard (`if ¬ (op ≠ additiveOp)`);
# both arms hoisted into locals; and a redundant nested guard whose two inner arms
# coincide. So the clause pins behaviour, not code shape. The seventh reproduces
# the dependent-guard limit the first audit reported, with the identical error —
# `Failed to parse an assertion without names: WPGen (if h : op = additiveOp then
# pure (additiveCombine matrixTerms) else pure (multiplicativeCombine
# (withLeadingScalar leadingScalar matrixTerms)))`. It is a FRONTEND parse failure
# in the weakest-precondition generator's handling of a dependent `if`, raised
# before any obligation is attempted, and the identical behaviour written with the
# non-dependent guard verifies — so it is a backend expressiveness/tooling limit,
# confirmed independently, and nothing about the frozen spec follows from it.
#
# SPEC-TOO-STRONG probe (attack E) — 3 NEW correct reshapes beyond the two
# shipped positives. Two VERIFY and confirm the clause pins behaviour rather than
# code shape: the whole if-then-else bound to a single local and returned, and
# the multiplicative composition fully hoisted ahead of the branch. A third — the
# guard-plus-fallthrough shape with no `else`, the shape a patch author would
# most naturally write — also VERIFIES. One reshape did NOT elaborate: the
# dependent-guard form `if h : op = additiveOp then …`, which fails in the
# frontend with `Failed to parse an assertion without names: WPGen …` before any
# obligation is attempted. That is a BACKEND EXPRESSIVENESS limit in the
# weakest-precondition generator's handling of a dependent `if`, not a soundness
# hole in this spec — the identical behaviour stated with the non-dependent guard
# verifies. Reported as a tooling issue with its error text; nothing about the
# frozen spec follows from it.
#
# PORTED / ADDED (argument carried over; mechanics re-expressed for the opaque
# carrier):
#  * uniq-additive-prepends-scalar. The DIRECT port of the discriminating fix
#    (uniq-prepatch-sum-inject-identity): under the additive operator the
#    pre-patch tail prepends the operator's scalar identity (its empty-argument
#    composition) in front of the matrix-valued terms, which is free to collapse
#    the additive
#    result to a scalar-valued term. On this carrier the collection of
#    matrix-valued terms is ONE opaque handle (`matrixTerms`), so nagini's two
#    sum sub-domains (num_scalars==0 vs the whole is_sum domain — its 3a and its
#    supporting 3e uniq-sum-always-scalar) are indistinguishable and COLLAPSE to
#    this single additive-arm rival. Refuted where the two composed handles
#    differ (op=additiveOp, matrixTerms=2, leadingScalar=1).
#  * uniq-multiplicative-drops-scalar. Attacks the SECOND clause arm (the
#    unchanged else branch), which nagini's E2/E3 boolean facets do not surface
#    as a standalone rival on this carrier. The multiplicative branch must
#    prepend the leading scalar-valued term; dropping it recombines a product
#    node without its coefficient, breaking the matrix-product PASS_TO_PASS
#    paths. A near-miss to the additive rival — correct on the additive arm — so
#    it is refuted at a DISJOINT input (op ≠ additiveOp, matrixTerms=4).
#  * uniq-ignore-op-always-additive / uniq-ignore-op-always-multiplicative.
#    The two DISCRIMINATOR degenerates (mirror of nagini's is_sum-domain
#    attacks): ignore the operator and fix the composition rule to one arm. Each
#    is wrong on the opposite arm; refuted at op ≠ additiveOp (matrixTerms=7) and
#    op=additiveOp (matrixTerms=9) respectively. Together they establish the
#    operator governs the branch at BOTH values.
#
# OMITTED (carrier narrowing — the machinery does not exist on this carrier, not
# hard to prove):
#  * uniq-sum-with-scalar-contaminates / uniq-product-no-absorb. Both live on the
#    num_scalars>0 domain (the partition leaves a genuine scalar term, i.e.
#    nonmatrices non-empty). That is the `if nonmatrices:` path explicitly NOT
#    part of the modeled data flow (mapping.md): the modeled tail is reached only
#    when no scalar-valued term remains. No counterpart on this carrier.
#  * uniq-product-phantom-scalar. Attacks the E3 boolean `scalar_arg_present`
#    facet in the product-no-scalar sub-domain. This carrier has no boolean
#    scalar-arg facet: the multiplicative arm ALWAYS composes with the leading
#    identity prepended (multiplicativeCombine (withLeadingScalar …)), matching
#    the unchanged else clause; the "is a scalar coefficient argument present"
#    abstraction is a nagini-only view. No counterpart.
#  * uniq-wrong-matrix-count. Attacks the E1 matrix_arg_count facet. This carrier
#    abstracts the collection of matrix-valued terms to a SINGLE opaque handle
#    (`matrixTerms : Int`) with no count to mis-state. No counterpart.
#
# PORTED AND RE-AIMED (audit):
#  * admiss-sum-no-scalar -> admiss-f2p-shaped-additive-arm. The sibling asserts a
#    representative F2P-shaped input is admitted (its Requires is num_matrices>=1
#    and num_scalars>=0). This method has NO `require` clause, so the admitted
#    domain is total and there is no precondition an F2P-shaped input could fail.
#    An EARLIER version of this file concluded from that alone that the lane was
#    inexpressible and dropped it. The audit found that reasoning insufficient:
#    "the frozen obligation has no precondition" is not a demonstration of
#    vacuity, and the analogue on a total carrier is the obligation being
#    UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input. That IS testable
#    here, by a positive that discharges the obligation at the concrete
#    discriminating point (the additive arm) by evaluation before closing the
#    frozen obligation verbatim — see the shipped case, whose third conjunct also
#    rules out the degenerate reading in which the two arms coincide on this
#    opaque carrier and every uniqueness rival attacks a distinction the spec does
#    not draw. Both conjuncts were flip-tested: the negated forms fail to
#    elaborate, so the `have` is load-bearing.
#
# VACUOUS CLASS (measured, NOT a spec hole — corrected during the audit):
#  * uniq-nonterm-vacuous. An earlier version of this file recorded this as a
#    KNOWN SPEC HOLE on the stated ground that the bundle carries `partial`
#    termination semantics. That is not true of the shipped artifact: Solution.lean
#    line 4 reads `set_option loom.semantics.termination "total"` and line 7 reads
#    `open TotalCorrectness DemonicChoice` (see audit item (5) for the provenance,
#    a completed corpus-wide sweep rather than a port error). Under `total` the
#    verifier
#    discharges a termination obligation, so a diverging impl is REJECTED, not
#    vacuously verified — the disposition inverts. Measured with real builds: five
#    loop-bearing rivals, including a structurally TERMINATING countdown loop, all
#    fail at exit 1 with `Decreasing annotations are required in total correctness
#    semantics`, and a SIXTH that carries a measure (`decreasing k` over an
#    incrementing `k`) fails at exit 1 on the measure's own descent goal,
#    `case decreasing_1: k ... |- k + 1 < k`. So the annotation must be TRUE and
#    not merely present, and there is no verify-does-not-imply-resolve gap here to
#    escalate.
#    It is still not shippable as a reject case, for a carrier reason rather than a
#    spec one: the error is a FRONTEND failure raised before any obligation is
#    attempted (the elaborator injects `sorry` into the generated `WPGen` term), so
#    a witness cannot be stated over such a rival at all — a witness asserting only
#    `(1:Nat) + 1 = 2` fails against the loop-bearing rival with that same
#    `Decreasing annotations` error while succeeding against the frozen solution.
#    The mechanical escape hatches are out of scope: a `decreasing` clause or a
#    file-level `set_option loom.linter.errors false` both break `same_spec`, and a
#    `set_option ... in` scoped inside the impl region does not parse. Recorded as
#    REJECTED BY THE SPEC and unshippable for a witness-side reason, not a known
#    hole. The earlier "vacuous class" label is withdrawn as imprecise: a diverging
#    rival is writable here, and it is refused rather than absent.
#
# WITNESS DISCRIMINATION (verified during authoring with real builds, re-checked
# by the gate's two builds per reject case): each witness ELABORATES against its
# straight-line rival (its `NonDetT.run` term reduces under
# `simp [NonDetT.run, pure, h1]` to the rival's returned handle, which the second
# hypothesis separates from the spec's if-then-else value) and FAILS against the
# frozen solution (whose value equals the spec's, so the residual `≠` is a `h2`
# type-mismatch the hypothesis cannot close). Each witness's two hypotheses are
# about DISTINCT opaque terms and are jointly satisfiable — the consistency probe
# left an unsolved `⊢ False` for every one (checked with a real build). No
# `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# BINDER / CLAUSE COVERAGE. Three input binders — op, leadingScalar, matrixTerms
# — and one clause with two arms plus a discriminator. All are moved and all are
# attacked:
#   * op: additiveOp-arm attacked by uniq-additive-prepends-scalar (op=0) and
#     uniq-ignore-op-always-multiplicative (op=0); non-additive arm attacked by
#     uniq-multiplicative-drops-scalar (op=1) and uniq-ignore-op-always-additive
#     (op=5). Both branches of the discriminator exercised.
#   * matrixTerms: moved across {2,4,7,9}; every rival's refutation turns on the
#     handle composed FROM matrixTerms differing from the spec's.
#   * leadingScalar: moved across {1,3,6,8}. Its role is attacked from THREE
#     sides — uniq-additive-prepends-scalar (it must be OMITTED on the additive
#     arm), uniq-multiplicative-drops-scalar (it must be PRESENT on the
#     multiplicative arm), and uniq-leading-scalar-arg-order (it must LEAD the
#     bundle, not trail it) — so a rival mishandling only leadingScalar, in
#     either its presence or its position, is caught.
#   Four distinct input points (pts=4): (0,1,2), (1,3,4), (5,6,7), (0,8,9). No
#   unattacked binder; both clause arms and the discriminator are attacked.
#   The two audit-added rivals close the two remaining sub-decisions: the
#   operator->rule PAIRING (uniq-arms-swapped, at (0,1,2) — both composers and
#   both bundle shapes present, only their assignment to arms wrong, which no
#   single-arm rival can distinguish) and the bundle constructor's OPERAND ORDER
#   (uniq-leading-scalar-arg-order, at (1,3,4)). Coverage is advisory, so these
#   were chosen by asking which sub-decision of the clause could still be
#   mis-implemented with every shipped case passing — not by chasing a binder
#   the reporter called unmoved.
#
# AXIOM_TESTS: empty. The three opaque callees (additiveCombine /
# multiplicativeCombine / withLeadingScalar) and the constant additiveOp carry NO
# asserted ensures — they are A-referenced free symbols whose only relied-upon
# property is determinism (mapping.md; meta.json G-AX status=skip). There is no
# axiom lane to mirror, and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
