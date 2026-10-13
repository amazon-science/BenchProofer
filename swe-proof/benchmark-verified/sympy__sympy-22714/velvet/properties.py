"""properties.py — G-PBT falsification battery for sympy__sympy-22714 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct imaginaryCoordCheck`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  imaginaryCoordCheck (coords : List Coord) return (out : Bool)
    ensures out = anyImaginary coords

The method decides whether a candidate point's coordinate list must be rejected
as carrying an imaginary coordinate. A coordinate is abstracted (``Coord``) to
three independent booleans:

  * ``numeric``     — the coordinate is a concrete number;
  * ``imagNonzero`` — its imaginary part is RIGOROUSLY determined to be nonzero
                      (a strict three-valued judgement: true only when provably
                      not zero; false when provably zero OR undecidable);
  * ``imagPresent`` — a COARSE indicator that a non-trivial imaginary-part object
                      is carried. It can be true even when the imaginary part is
                      in fact zero but left unsimplified. This observation is
                      DELIBERATELY distinct from ``imagNonzero`` and is what the
                      decision must NOT consult.

The single load-bearing ``ensures`` pins ``out`` to the fully-unfolded pure model
``anyImaginary``:

  ``anyImaginary [] = false``
  ``anyImaginary (c :: cs) = coordImaginary c || anyImaginary cs``
  ``coordImaginary c = c.numeric && c.imagNonzero``

There is NO opaque answer-key to echo: the ``axioms`` region is empty and
``anyImaginary`` / ``coordImaginary`` are fully-unfolded ``def``s over the
method's own argument, so the unique satisfier IS the honestly-computed
disjunction. The single top-level clause combines several independently-
attackable sub-obligations:

  * NUMERIC conjunct — a coordinate counts as imaginary ONLY when it is a
    concrete number; a symbolic coordinate whose imaginary part is provably
    nonzero must NOT trigger (the numeric guard is load-bearing);
  * NONZERO conjunct on the RIGHT observation — the decision reads the strict
    provably-nonzero judgement ``imagNonzero``, NOT the coarse ``imagPresent``.
    A coordinate that is numeric with ``imagPresent = true`` but
    ``imagNonzero = false`` (a real coordinate whose imaginary part is carried
    unsimplified) must be ACCEPTED — this is the direction the fix restores;
  * POLARITY — the trigger fires on the provably-nonzero outcome, not on its
    negation; a coordinate whose imaginary part is provably zero or undecided
    must NOT trigger;
  * ELEMENT-WISE / POSITIONAL — the per-coordinate test is applied across the
    WHOLE list, no position special-cased, disjunction over every element (so
    both list order/length and each coordinate participate).

The single input binder is ``coords``; each ``Coord`` field (``numeric``,
``imagNonzero``, ``imagPresent``) and the list length/position are the sub-binders
the model reads (or, for ``imagPresent``, must IGNORE). The reject witnesses below
move every one of these off any fixed value.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY GOLD IS NOT THE SUBJECT. The gold
impl is a backward ``while`` loop, which under
``loom.semantics.choice "demonic"`` elaborates through ``Classical.choice``; the
kernel cannot unfold that, so ``decide`` against gold's extracted
``imaginaryCoordCheckExec`` is STUCK rather than false. That is NOT a
discriminator, and an earlier revision of this note wrongly treated it as one.
Measured with real ``scripts/lean_verify.sh`` builds against the FROZEN solution:

  * the refutation ``tester [numeric ∧ present ∧ ¬nonzero] = false``  -> exit 1,
    "Tactic `decide` failed … did not reduce to `isTrue` or `isFalse`";
  * the exact OPPOSITE claim ``… = true`` (i.e. that gold is WRONG in the other
    direction)                                                        -> exit 1,
    byte-identical error;
  * the syntactic tautology ``tester C = tester C``                    -> exit 1,
    same error — a claim that is true of EVERY impl;
  * the control ``1 + 1 = 2``                                          -> exit 0,
    so the cell is not simply broken.

Gold's exit code therefore carries no information: a forged "witness" asserting
gold is CORRECT at an agreement point would clear a naive two-halves check.
So every reject case below names an explicit ``witness_reference``
(``_POS_RETURN_MODEL``): the loop-free correct impl of this SAME frozen spec,
which the gate independently checks shares the spec and VERIFIES. An impl the
verifier accepts cannot violate its own spec, so a genuine refutation must still
fail there — and against it the failure is a real REFUTATION, measured as
"Tactic `decide` proved that the proposition … is false" (exit 1) for every
value witness, while each elaborates green (exit 0) against its own rival. Each rival
is a loop-free straight-line closed form whose extracted program reduces by
kernel computation, so ``imaginaryCoordCheckTester coords`` evaluates to a
literal ``Bool`` and each witness closes by ``decide`` at fully-concrete
``List Coord`` literals. The carrier at every witness is a concrete literal, so
no hypothesis is assumed and there is no joint-satisfiability obligation.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical correct impls (return the grounded pure model
    ``anyImaginary coords`` directly with no loop; and the loop with the
    per-coordinate test bound to a local before OR-ing) must verify, else the
    spec is SPEC-TOO-STRONG on the impl shape. The direct-model form reproves
    with a bare ``loom_solve``; the local-reshape keeps the frozen
    ``loom_solve; rw [anyImaginary_drop_step …]; simp_all`` proof (only the
    tactic body — elided from the spec view — is retuned where needed). These
    replace the sibling's grounded-echo control too: the model IS the real
    per-coordinate work, so returning it is honest, not an ungrounded echo.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries MANDATORY
    frame rivals that WRITE through read-only inputs held at fractional heap
    permissions (``Acc(list_pred(coord_extra), 1/2)`` / ``coord_kind``). Lean and
    Velvet are referentially transparent: ``coords`` is an immutable value, this
    bundle declares NO ``mut`` binder for it (the two ``mut`` locals ``result`` /
    ``i`` are the loop's own state, not inputs), and there is no heap and no
    aliasing — so there is no read-only input to overwrite and no permission
    system to trip. Not fabricated (per the porting map, this class is vacuous on
    a referentially-transparent backend). See the footer for the accounting.
  * DIVERGENCE / NON-TERMINATION — the spec CLOSES this class, but it is not
    expressible as a witness-bearing reject case on this carrier. Two corrections
    to what an earlier revision of this file recorded, both measured:
      (1) That revision said this bundle sets
          ``loom.semantics.termination "partial"`` and deferred to the
          corpus-wide `partial` spec hole. That is no longer true of this
          artifact: ``Solution.lean`` line 4 now sets ``"total"`` and the frozen
          loop carries a ``decreasing i`` measure. The note was most likely
          accurate when written and was overtaken by the corpus-wide remediation
          of that very hole; either way a battery must describe the artifact it
          ships beside, so the disposition is restated here against the frozen
          file as it now stands. The correction runs in the SPEC's favour: the
          spec is stronger than the note claimed, not weaker.
      (2) Under ``"total"`` the verifier discharges a termination obligation, and
          the diverging rival IS rejected: the frozen loop with only its
          ``decreasing i`` annotation deleted fails with
          ``error: Decreasing annotations are required in total correctness
          semantics`` (exit 1, measured). So is the sharper shape that CARRIES a
          measure the verifier cannot show decreasing, which is the one that
          cannot be dismissed as merely the missing-annotation linter: spliced as
          ``let mut q : Nat := 1; while q > 0 / invariant 0 ≤ q / done_with q = 0
          / decreasing q do q := q``, it is REJECTED on the measure's OWN descent
          goal, ``case «decreasing_1: q»``, residual ``⊢ q < q``. The rejection is
          uniform across the corpus: all 500 velvet bundles set ``"total"`` and
          open ``TotalCorrectness``, none sets ``"partial"``.
    It still cannot SHIP as a reject case, and the reason is a property of the
    witness protocol rather than of the spec or of the author's effort. A reject
    case's witness must ELABORATE against the rival, but the missing-measure error
    is raised at the METHOD DECLARATION, so every file built on that rival fails
    before reaching any witness — measured with a trivially true witness
    (``example : 1 + 1 = 2 := by decide``) against this rival: exit 1, same
    ``Decreasing annotations are required`` error. So no witness whatsoever can
    hold of it, and a case shipped anyway records ``witness-unproven`` (measured:
    the gate returned exactly that, forcing MALFORMED-TESTS). This is the correct
    and complete disposition: the class needs no reject case because the spec
    already rejects it, and it can carry none because the rejection happens too
    early for a witness to observe. Nothing here is a hole in the frozen spec.
  * ADMISSIBILITY — SHIPPED as ``admiss-obligation-satisfiable-at-f2p``. An
    earlier revision recorded this class DEGENERATE because the method has no
    ``require`` clause, and then argued the reject lane's own failures were the
    non-degeneracy demonstration. That reasoning is not the admissibility probe:
    the analogue on a total carrier with an empty precondition is the obligation
    being UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
    discharges the obligation at that concrete input — by evaluation, as a
    ``have``, before closing the frozen obligation verbatim — tests directly. The
    shipped case does that at the input this instance turns on, and its liveness
    is measured: the same case asserting the OPPOSITE value at that input FAILS
    to elaborate (exit 1), so the ``have`` is load-bearing, not decoration.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a fully-unfolded pure function
    of the single input binder; there is no answer-key term a wrong impl could
    echo. The cheapest correct impl computes the disjunction honestly, which the
    positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the coarse ``imagPresent``
    consulted instead of ``imagNonzero`` — the prepatch bug; the polarity
    inverted; the numeric conjunct dropped; the first coordinate skipped; the
    whole screen dropped; the coarse flag demanded as an EXTRA conjunct).

AUDIT RE-DERIVATION (independent, real ``scripts/lean_verify.sh`` builds). Every
claim in the CARRIER NOTE above was re-measured rather than trusted, and the
gold-side uninformativeness re-confirmed: against the FROZEN solution the
refutation, the flipped claim ``… = true``, and the syntactic tautology
``tester C = tester C`` all fail with the identical
"did not reduce to `isTrue` or `isFalse`" (exit 1) while ``1 + 1 = 2`` builds
green (exit 0) — so ``witness_reference`` is not an evasion here but the only
sound second subject. Against the reference the same three builds SEPARATE: the
refutation fails by "Tactic `decide` proved that the proposition … is false"
(exit 1), the flipped claim ELABORATES (exit 0), and the tautology elaborates
(exit 0). The reference's exit code therefore tracks the claim, which is what
makes each rejection attributable.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22714"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen loop body. Lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap / the assert below). The leading comment
# ---- lines inside the region are kept OUTSIDE the anchor so a reshape that
# ---- keeps them is a clean single swap.
_IMPL = """    let mut result : Bool := false
    let mut i := coords.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ coords.length
      invariant result = anyImaginary (coords.drop i)
      done_with i = 0
      decreasing i
    do
      let c := coords[i - 1]!
      result := coordImaginary c || result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen loop
# ---- body. A positive control that drops the loop entirely retunes it to a bare
# ---- `loom_solve`; both the impl region and the `prove_correct` body are elided
# ---- from the spec view, so same_spec still holds and the `prove_correct
# ---- imaginaryCoordCheck` obligation survives with an identical header. Unique.
_PROOF = """prove_correct imaginaryCoordCheck by
  loom_solve
  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _rewrite_impl(body):
    """Full variant: impl body replaced, spec + frozen proof left intact. For
    rivals (expected NOT to verify) and for the local-reshape positive (whose
    loop invariants are kept, so the frozen proof still closes)."""
    return _swap(_BASE, _IMPL, body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `imaginaryCoordCheckTester coords = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped, so no tactic
# ---- script can mask the verdict.
def _tester(call):
    return ("extract_program_for imaginaryCoordCheck\n"
            "prove_precondition_decidable_for imaginaryCoordCheck\n"
            "prove_postcondition_decidable_for imaginaryCoordCheck\n"
            "derive_tester_for imaginaryCoordCheck\n\n"
            f"example : {call} = false := by\n  decide\n")


def _coord(numeric, imag_nonzero, imag_present):
    return ("{ numeric := %s, imagNonzero := %s, imagPresent := %s }"
            % (numeric, imag_nonzero, imag_present))


# ---- The loop-free correct impl, hoisted: it is BOTH the `pos-return-model`
# ---- positive AND the declared `witness_reference` for every reject case. The
# ---- frozen impl's backward `while` elaborates through `Classical.choice`, which
# ---- the kernel cannot unfold, so `decide` against gold's tester is stuck for
# ---- EVERY claim regardless of truth (measured: the refutation, the exact
# ---- OPPOSITE claim `tester … = true`, and the syntactic tautology
# ---- `tester … = tester …` all fail with the identical
# ---- "did not reduce to `isTrue` or `isFalse`", while `1 + 1 = 2` builds green).
# ---- Gold's exit code therefore carries NO information and cannot be the second
# ---- half of the discriminator. This impl can: it shares the frozen spec, it
# ---- VERIFIES, and being loop-free its extracted program reduces by kernel
# ---- computation — so an impl the verifier accepts cannot violate its own spec,
# ---- and each witness genuinely FAILS against it by REFUTATION ("Tactic `decide`
# ---- proved that the proposition … is false"), not by stuck reduction.
_POS_RETURN_MODEL = _swap(
    _rewrite_impl("    return anyImaginary coords"),
    _PROOF, "prove_correct imaginaryCoordCheck by\n  loom_solve")


# ---- The F2P-shaped coordinate: a concrete NUMBER whose coarse imaginary-part
# ---- indicator is set while the strict provably-nonzero judgement is NOT. This
# ---- is the point the instance turns on, and the admissibility case below shows
# ---- the frozen obligation is SATISFIABLE there rather than unsatisfiable.
_F2P_COORD = _coord("true", "false", "true")
_TRIGGER_COORD = _coord("true", "true", "true")

# ---- ADMISSIBILITY, discharged BY EVALUATION at the F2P-shaped input as two
# ---- `have`s, BEFORE the frozen obligation is closed verbatim. Only the tactic
# ---- body changes (elided from the spec view), so same_spec holds and the
# ---- `prove_correct imaginaryCoordCheck` header is byte-identical.
_PROOF_ADMISS = (
    "prove_correct imaginaryCoordCheck by\n"
    f"  have hadmit : anyImaginary [{_F2P_COORD}] = false := by decide\n"
    f"  have hreject : anyImaginary [{_F2P_COORD}, {_TRIGGER_COORD}] = true := by decide\n"
    "  loom_solve\n"
    "  rw [anyImaginary_drop_step coords i (by omega) (by omega)]\n"
    "  simp_all")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded pure model `anyImaginary coords` directly. `anyImaginary` is a
        # total function of the input (no opaque answer-key), so this is a correct
        # impl, not an echo. The residual goal is definitional, closed by a bare
        # `loom_solve` (the frozen loop-specific rewrite is not needed and is
        # dropped — the tactic body is elided from the spec view, so same_spec and
        # the obligation header are untouched). Confirmed with a real build.
        "module": _POS_RETURN_MODEL,
        "rationale": (
            "the cheapest honest correct impl returns the grounded pure model "
            "`anyImaginary coords` directly (no loop at all — maximally different "
            "from the gold backward `while`). The ensures is literally "
            "`out = anyImaginary coords`, so it holds on the whole domain and a "
            "bare `loom_solve` discharges the definitional residual. If this "
            "failed the spec would be over-fit to the loop shape (SPEC-TOO-STRONG). "
            "Also the honest no-ungrounded-echo control: the model IS the real "
            "per-coordinate work, so returning it is correct, not a cheat. "
            "(Sibling: pos-reorder / pos-echo.)"),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Keep the backward loop but compute the per-coordinate imaginary test
        # into a local `e` before OR-ing (a distinct data shape from the inline
        # `coordImaginary c || result`). Observationally identical to gold; the
        # frozen `loom_solve; rw [anyImaginary_drop_step …]; simp_all` proof still
        # closes (invariants kept verbatim). Confirmed with a real build.
        "module": _rewrite_impl(
            "    let mut result : Bool := false\n"
            "    let mut i := coords.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ coords.length\n"
            "      invariant result = anyImaginary (coords.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := coords[i - 1]!\n"
            "      let e := coordImaginary c\n"
            "      result := e || result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": (
            "structurally-different CORRECT impl: the per-coordinate imaginary "
            "test is bound to a typed local `e` before OR-ing, instead of the "
            "inline `coordImaginary c || result`. Same behaviour, different data "
            "shape; the loop invariants are kept verbatim so the frozen proof "
            "(`loom_solve; rw [anyImaginary_drop_step …]; simp_all`) still "
            "discharges. Must verify, else the spec is over-fit to the inline OR "
            "form => SPEC-TOO-STRONG. (Sibling: pos-reorder — the reordered "
            "trigger bound to a local boolean.)"),
    },

    # =====================================================================
    # ADMISSIBILITY / PRECOND-TOO-STRONG — added under audit. The port recorded
    # this lane DEGENERATE ("the method has no `require` clause"), which is not
    # the probe: on a total carrier with an empty precondition the analogue is the
    # obligation being UNSATISFIABLE at exactly an F2P-shaped input. This case
    # tests that directly, by EVALUATION at that concrete input, as `have`s that
    # precede the frozen obligation — which still closes verbatim afterwards.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _PROOF_ADMISS),
        "rationale": (
            "PASS SOURCE = the frozen obligation is SATISFIABLE at the input this "
            "instance turns on, and demands the ACCEPT verdict there. `hadmit` "
            "evaluates the post-image at the single-coordinate list "
            "[numeric ∧ present ∧ ¬nonzero] and closes "
            "`anyImaginary … = false` by `decide`: the spec really does ADMIT a "
            "concrete-number coordinate whose coarse imaginary indicator is set "
            "while the strict provably-nonzero judgement is not, rather than being "
            "unsatisfiable at that point. `hreject` then evaluates the post-image "
            "at that same coordinate followed by a genuinely triggering one and "
            "closes `= true`, so the spec is not degenerately-accepting either: "
            "both verdicts are reachable by computation at F2P-shaped carriers. If "
            "the post-image at the admitting point were unsatisfiable by any "
            "computation — the total-carrier analogue of a precondition no "
            "in-domain input meets — `hadmit` could not be discharged and this "
            "case would FAIL => PRECOND-TOO-STRONG. The `have`s are LIVE, not "
            "decoration: the same case with `hadmit` claiming `= true` instead "
            "FAILS to elaborate (measured out-of-band, exit 1, `Tactic `decide` "
            "proved that the proposition … is false`), so a false claim about this "
            "point does not close. Only the tactic body changes — elided from the "
            "spec view — so the frozen `ensures` and the `prove_correct` header "
            "are untouched and the real obligation is still discharged by the "
            "frozen script that follows. (Sibling: admiss-drain, re-aimed: the "
            "sibling establishes its half-permission `Requires` admits an "
            "F2P-shaped input; this carrier has no permission surface, so the "
            "satisfiable-at-F2P obligation is the analogue.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing tests. Each rival's extracted program reduces by kernel
    # computation, so its witness discriminates by value (see the CARRIER NOTE);
    # the frozen spec and obligation header are untouched.
    # =====================================================================
    {
        "id": "rej-coarse-present",
        "kind": "uniqueness",
        "expect": "reject",
        # THE prepatch bug: key the screen off the COARSE imaginary-part-present
        # indicator (`imagPresent`) instead of the strict provably-nonzero
        # judgement (`imagNonzero`). Wrong precisely on a numeric coordinate whose
        # imaginary part is carried unsimplified (present but provably zero).
        "module": _rewrite_impl(
            "    return coords.any (fun c => c.numeric && c.imagPresent)"),
        "refinement": (
            "reproduces the base-commit decision rule: it consults the coarse "
            "imaginary-part-present indicator rather than the strict "
            "provably-nonzero judgement. The failing scenario constructs a point "
            "with expression-evaluation suppressed, so a genuinely REAL coordinate "
            "carries its imaginary part unsimplified — the coarse indicator reads "
            "true even though the part is provably zero — and the constructor "
            "WRONGLY rejects the point (the ValueError the issue reports). The F2P "
            "test constructs exactly such a point and asserts it is admitted; this "
            "rival rejects it, so it does NOT resolve. This IS the modeled bug and "
            "the prepatch discriminator (G-DIFF). Correct on every coordinate whose "
            "two imaginary observations agree (a genuine imaginary has both true; a "
            "simplified real has both false), a true partial-domain break."),
        "rationale": (
            "REJECT from the NONZERO-conjunct sub-obligation: the spec reads the "
            "strict `imagNonzero`, but this reads the coarse `imagPresent`. On a "
            "numeric coordinate with `imagPresent = true` and "
            "`imagNonzero = false` the spec demands the coordinate NOT count "
            "(`anyImaginary = false`), but the rival returns true. If it verified "
            "=> SPEC-TOO-WEAK (the coarse-vs-strict distinction the fix turns on "
            "is unpinned). Refuted at coords=[numeric ∧ present ∧ ¬nonzero]: gold "
            "resolves false, the rival true. This witness is the ONLY one that "
            "sets `imagPresent` true while `imagNonzero` is false — the value the "
            "bug turns on. (Sibling: rej-extra.)"),
        # Gold cannot serve as the discriminating subject here: its backward
        # `while` elaborates through `Classical.choice`, so `decide` on its
        # tester is STUCK for every claim and its exit code attests to nothing
        # (see _POS_RETURN_MODEL). Refuted against the loop-free VERIFYING impl
        # of the same spec instead, where the failure is a real refutation.
        "witness_reference": _POS_RETURN_MODEL,
        "witness": _tester(
            "imaginaryCoordCheckTester [%s]"
            % _coord("true", "false", "true")),
    },
    {
        "id": "rej-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the load-bearing polarity: trigger on the NEGATION of the
        # provably-nonzero judgement (fire when the imaginary part is provably
        # zero or undecided) instead of on the provably-nonzero outcome.
        "module": _rewrite_impl(
            "    return coords.any (fun c => c.numeric && !c.imagNonzero)"),
        "refinement": (
            "inverts the screen: it rejects a numeric coordinate whose imaginary "
            "part is NOT provably nonzero (i.e. provably zero or undecided) and "
            "permits genuine imaginaries. A faithful patch writing the inverted "
            "test raises on ordinary REAL points (every PASS_TO_PASS point "
            "construction — test_point / test_Point2D / test_point3D — carries "
            "numeric real coordinates that are provably non-imaginary) and permits "
            "genuine imaginary coordinates the constructor must reject. It "
            "regresses the P2P suite and still mishandles the F2P case, so it does "
            "NOT resolve."),
        "rationale": (
            "REJECT from the POLARITY sub-obligation: `coordImaginary` fires on "
            "`imagNonzero = true`, so a numeric coordinate with "
            "`imagNonzero = false` must NOT count, but the rival counts it. If it "
            "verified => SPEC-TOO-WEAK (the trigger polarity unpinned). Refuted at "
            "coords=[numeric ∧ ¬nonzero ∧ ¬present]: gold resolves false, the rival "
            "true. Distinct from rej-coarse-present: here `imagPresent` is FALSE, "
            "so the divergence is attributable to the polarity flip on "
            "`imagNonzero` alone, not to reading the coarse field."),
        # Gold cannot serve as the discriminating subject here: its backward
        # `while` elaborates through `Classical.choice`, so `decide` on its
        # tester is STUCK for every claim and its exit code attests to nothing
        # (see _POS_RETURN_MODEL). Refuted against the loop-free VERIFYING impl
        # of the same spec instead, where the failure is a real refutation.
        "witness_reference": _POS_RETURN_MODEL,
        "witness": _tester(
            "imaginaryCoordCheckTester [%s]"
            % _coord("true", "false", "false")),
    },
    {
        "id": "rej-drop-numeric",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the numeric conjunct: trigger on `imagNonzero` alone, ignoring
        # whether the coordinate is a concrete number. Wrong on a symbolic
        # coordinate whose imaginary part is (abstractly) provably nonzero but
        # which is NOT numeric, so must be accepted.
        "module": _rewrite_impl(
            "    return coords.any (fun c => c.imagNonzero)"),
        "refinement": (
            "drops the concrete-number guard, so it screens on the imaginary "
            "judgement alone. A faithful patch omitting the concrete-number conjunct "
            "would reject a symbolic coordinate carrying a provably-nonzero "
            "imaginary component (which the real guard, being keyed on concrete-"
            "numberhood first, leaves to construction) — over-rejecting "
            "non-numeric coordinates "
            "the constructor must accept, regressing the symbolic-point P2P "
            "constructions. Does NOT resolve."),
        "rationale": (
            "REJECT from the NUMERIC-conjunct sub-obligation: `coordImaginary c = "
            "c.numeric && c.imagNonzero`, so a coordinate with `numeric = false` "
            "must NOT count regardless of `imagNonzero`, but the rival counts it. "
            "If it verified => SPEC-TOO-WEAK (the numeric guard unpinned — the "
            "ONLY rival on which `numeric` is the deciding value). Refuted at "
            "coords=[¬numeric ∧ nonzero ∧ ¬present]: gold resolves false, the "
            "rival true. This witness is the only one setting `numeric` false. "
            "(No direct sibling — added to attack the numeric conjunct, which the "
            "sibling's list carrier folds into the kind==1 fact.)"),
        # Gold cannot serve as the discriminating subject here: its backward
        # `while` elaborates through `Classical.choice`, so `decide` on its
        # tester is STUCK for every claim and its exit code attests to nothing
        # (see _POS_RETURN_MODEL). Refuted against the loop-free VERIFYING impl
        # of the same spec instead, where the failure is a real refutation.
        "witness_reference": _POS_RETURN_MODEL,
        "witness": _tester(
            "imaginaryCoordCheckTester [%s]"
            % _coord("false", "true", "false")),
    },
    {
        "id": "rej-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (first element): skip the FIRST coordinate entirely and
        # screen the rest correctly. Diverges only when the sole triggering
        # coordinate is first.
        "module": _rewrite_impl(
            "    return (match coords with\n"
            "      | [] => false\n"
            "      | _ :: cs => anyImaginary cs)"),
        "refinement": (
            "a faithful patch that began the imaginary screen from the SECOND "
            "coordinate (e.g. `any(... for a in coords[1:])`) would never inspect "
            "the first coordinate of a point, so an imaginary FIRST coordinate is "
            "wrongly permitted — the constructor stops raising on points whose "
            "imaginary coordinate is leading. It over-permits genuine imaginaries "
            "and regresses the imaginary-rejection behaviour the constructor keeps, "
            "so it does NOT resolve. Correct on every point whose triggering "
            "coordinate is not first, agreeing with gold over more of the domain "
            "than the wholesale rivals and refuted at the distinguishing "
            "first-coordinate input."),
        "rationale": (
            "REJECT from the ELEMENT-WISE/POSITIONAL sub-obligation at the FIRST "
            "coordinate: `anyImaginary` disjoins over EVERY element, but this drops "
            "the head, so `out` differs from the model whenever coordinate 0 is the "
            "sole trigger. If it verified => SPEC-TOO-WEAK (the first-coordinate "
            "sub-domain unpinned). Refuted at coords=[triggering, non-triggering]: "
            "gold resolves true, the rival false. This is the ONLY multi-element "
            "witness, and the only one exercising list position/length. "
            "(Sibling: rej-drop-first.)"),
        # Gold cannot serve as the discriminating subject here: its backward
        # `while` elaborates through `Classical.choice`, so `decide` on its
        # tester is STUCK for every claim and its exit code attests to nothing
        # (see _POS_RETURN_MODEL). Refuted against the loop-free VERIFYING impl
        # of the same spec instead, where the failure is a real refutation.
        "witness_reference": _POS_RETURN_MODEL,
        "witness": _tester(
            "imaginaryCoordCheckTester [%s, %s]"
            % (_coord("true", "true", "true"), _coord("false", "false", "false"))),
    },
    {
        "id": "rej-aggregator-all",
        "kind": "uniqueness",
        "expect": "reject",
        # AGGREGATOR: keep the per-coordinate test EXACTLY right but disjoin with
        # the wrong quantifier — require EVERY coordinate to trigger instead of
        # SOME. Wrong on any mixed list. Added by audit: the shipped rivals all
        # attacked the per-coordinate predicate or a position, leaving the
        # aggregation operator itself unprobed.
        "module": _rewrite_impl(
            "    return coords.all (fun c => c.numeric && c.imagNonzero)"),
        "witness_reference": _POS_RETURN_MODEL,
        "refinement": (
            "swaps the aggregation quantifier: it rejects a point only when ALL "
            "of its coordinates are imaginary. A faithful patch writing `all(...)` "
            "instead of `any(...)` stops rejecting a point with one imaginary and "
            "one real coordinate — the ordinary mixed case — so genuinely "
            "imaginary points are admitted and the imaginary-rejection behaviour "
            "the P2P suite exercises regresses. It also admits the empty and "
            "all-real lists correctly, so it agrees with gold on much of the "
            "domain. Does NOT resolve."),
        "rationale": (
            "REJECT from the ELEMENT-WISE aggregation sub-obligation, at the "
            "OPERATOR rather than at a position: `anyImaginary` is a DISJUNCTION "
            "over the list, so a list with one triggering and one non-triggering "
            "coordinate must yield true, but a conjunction yields false. If it "
            "verified => SPEC-TOO-WEAK (the spec would not pin `any` vs `all`). "
            "Refuted at coords=[triggering, non-triggering]: gold resolves true, "
            "the rival false. Distinct from rej-drop-first, which keeps the "
            "disjunction and drops an ELEMENT; here every element is inspected "
            "and the combining operator is wrong. (No sibling — the nagini "
            "carrier has no standalone aggregator rival.) The witness is aimed at "
            "an input DISTINCT from rej-drop-first's: the non-triggering "
            "coordinate here is (numeric \u2227 \u00acnonzero \u2227 \u00acpresent) rather than the "
            "all-false coordinate, so the two cases no longer share a probe point, "
            "and this one additionally shows the break does not depend on the "
            "second coordinate being non-numeric. RE-AIMED under audit: the "
            "shipped witness was byte-identical to rej-drop-first's, so the "
            "manifest's own claim that the reject witnesses probe DISTINCT input "
            "points was false of this pair."),
        "witness": _tester(
            "imaginaryCoordCheckTester [%s, %s]"
            % (_coord("true", "true", "true"), _coord("true", "false", "false"))),
    },
    {
        "id": "rej-require-present",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-RESTRICTION on the coarse observation: keep both correct conjuncts
        # but demand the coarse indicator TOO. Added by audit: every shipped rival
        # attacked the decision by making it fire too often or read the wrong
        # field, so the direction where the coarse field is consulted to SUPPRESS a
        # genuine trigger -- the "imagPresent must be IGNORED" obligation in its
        # other polarity -- was unprobed.
        "module": _rewrite_impl(
            "    return coords.any (fun c => c.numeric && c.imagNonzero "
            "&& c.imagPresent)"),
        "witness_reference": _POS_RETURN_MODEL,
        "refinement": (
            "consults the coarse imaginary-part indicator as an EXTRA requirement "
            "on top of the correct test. A faithful patch conjoining the coarse "
            "truthiness with the strict provably-nonzero judgement stops rejecting "
            "a coordinate whose imaginary part is rigorously nonzero but whose "
            "coarse indicator does not read true, so a genuinely imaginary "
            "coordinate the constructor must reject is admitted and the "
            "imaginary-rejection behaviour the P2P suite exercises regresses. It "
            "agrees with gold wherever the two imaginary observations agree, which "
            "is most of the domain and notably the whole failing scenario -- so it "
            "would look like it resolves while silently regressing. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from the same NONZERO-vs-COARSE sub-obligation as "
            "rej-coarse-present but in the OPPOSITE polarity: that rival "
            "SUBSTITUTES the coarse `imagPresent` for the strict `imagNonzero` and "
            "over-rejects; this one keeps `imagNonzero` and ADDS `imagPresent`, so "
            "it under-rejects. `coordImaginary c = c.numeric && c.imagNonzero` "
            "mentions the coarse field nowhere, so a coordinate with "
            "`numeric = true`, `imagNonzero = true` and `imagPresent = false` must "
            "COUNT, but the rival drops it. If it verified => SPEC-TOO-WEAK: the "
            "spec would pin only that the coarse field cannot be SUBSTITUTED for "
            "the strict one, not that it must be IGNORED, and that is a weaker "
            "claim than the one the ensures makes. Refuted at "
            "coords=[numeric \u2227 nonzero \u2227 \u00acpresent]: gold resolves true, the rival "
            "false. This is the ONLY witness at that field combination -- the one "
            "assignment of the three booleans no shipped rival moved to -- and the "
            "only rival that errs by UNDER-rejecting on the coarse field. (No "
            "sibling -- added by audit.)"),
        "witness": _tester(
            "imaginaryCoordCheckTester [%s]"
            % _coord("true", "true", "false")),
    },
    {
        "id": "rej-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (tail): consult ONLY the first coordinate and ignore
        # every later one — the positional mirror of rej-drop-first. Added by
        # audit: rej-drop-first probes a skipped HEAD, so a trigger in the TAIL
        # was the one positional sub-domain no shipped rival moved off.
        "module": _rewrite_impl(
            "    return (match coords with\n"
            "      | [] => false\n"
            "      | c :: _ => coordImaginary c)"),
        "witness_reference": _POS_RETURN_MODEL,
        "refinement": (
            "screens only the leading coordinate. A faithful patch testing just "
            "the first coordinate (e.g. dropping the aggregation and inspecting "
            "`coords[0]`) never inspects a later one, so a point whose imaginary "
            "coordinate is NOT leading is wrongly permitted and the constructor "
            "stops raising on it. Correct on every single-element list and on any "
            "point whose trigger is leading, so it agrees with gold over a large "
            "sub-domain and breaks on the trailing-coordinate one. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from the ELEMENT-WISE/POSITIONAL sub-obligation at a "
            "NON-FIRST coordinate: `anyImaginary` disjoins over EVERY element, "
            "but this reads only the head, so `out` differs from the model "
            "whenever the sole trigger is later in the list. If it verified => "
            "SPEC-TOO-WEAK (the trailing-coordinate sub-domain unpinned). Refuted "
            "at coords=[non-triggering, triggering]: gold resolves true, the "
            "rival false. The positional MIRROR of rej-drop-first (which drops "
            "the head and keeps the tail), so together they pin both ends of the "
            "list. (No sibling — added by audit.)"),
        "witness": _tester(
            "imaginaryCoordCheckTester [%s, %s]"
            % (_coord("false", "false", "false"), _coord("true", "true", "true"))),
    },
    {
        "id": "rej-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE / collapse: never reject — drop the screen entirely. Correct on
        # every all-accepting list, diverges on any genuine imaginary coordinate.
        "module": _rewrite_impl("    return false"),
        "refinement": (
            "deletes the imaginary screen, so every coordinate list is admitted. A "
            "faithful patch removing the guard permits genuinely imaginary "
            "coordinates the constructor must reject (a point with a provably "
            "nonzero imaginary coordinate constructs without error), regressing the "
            "imaginary-rejection behaviour the P2P suite exercises. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from the whole postcondition: a constant `false` contradicts "
            "`anyImaginary coords` on any list with a triggering coordinate "
            "(numeric ∧ nonzero). If it verified => SPEC-TOO-WEAK (the trigger "
            "collapsed to one value). Refuted at coords=[numeric ∧ nonzero ∧ "
            "present]: gold resolves true, the rival false. (Sibling: "
            "rej-const-false.)"),
        # Gold cannot serve as the discriminating subject here: its backward
        # `while` elaborates through `Classical.choice`, so `decide` on its
        # tester is STUCK for every claim and its exit code attests to nothing
        # (see _POS_RETURN_MODEL). Refuted against the loop-free VERIFYING impl
        # of the same spec instead, where the failure is a real refutation.
        "witness_reference": _POS_RETURN_MODEL,
        "witness": _tester(
            "imaginaryCoordCheckTester [%s]"
            % _coord("true", "true", "true")),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals — two of which are MANDATORY
# frame-mutation rivals; AXIOM_TESTS present but this gate ignores them). The
# sibling contracts `screen_coordinates(coord_kind, coord_verdict, coord_extra)`
# over THREE index-aligned `List[int]` inputs under fractional read-only
# permissions and partial correctness. This backend models the SAME imaginary-
# coordinate screen DEEPLY and CONCRETELY: the three index-aligned nagini lists
# collapse to ONE `List Coord`, whose per-element `numeric` / `imagNonzero` /
# `imagPresent` fields are exactly the nagini `coord_kind==1` / `coord_verdict==0`
# / `coord_extra==1` facts. The screen is pinned by a single element-wise
# `ensures out = anyImaginary coords`; the method runs with NO precondition and NO
# permission surface. Those carrier facts make two sibling classes
# vacuous/degenerate here.
#
#   nagini case        kind          -> here                          disposition
#   ------------------------------------------------------------------------------
#   pos-reorder        soundness     -> pos-local-reshape              PORTED
#   pos-echo           soundness     -> pos-return-model               RE-SHAPED
#   admiss-drain       admissibility -> admiss-obligation-             RE-AIMED
#                                       satisfiable-at-f2p             (audit)
#   rej-extra          uniqueness    -> rej-coarse-present             PORTED
#   rej-polarity       uniqueness    -> rej-polarity                   PORTED
#   rej-drop-first     uniqueness    -> rej-drop-first                 PORTED
#   rej-const-false    uniqueness    -> rej-const-false                PORTED
#   rej-frame-extra    uniqueness    -> (none)                         VACUOUS
#   rej-frame-kind     uniqueness    -> (none)                         VACUOUS
#   (no sibling)       uniqueness    -> rej-drop-numeric               ADDED
#   (no sibling)       uniqueness    -> rej-aggregator-all             ADDED (audit)
#   (no sibling)       uniqueness    -> rej-head-only                  ADDED (audit)
#   (no sibling)       uniqueness    -> rej-require-present            ADDED (audit)
#   AXIOM_TESTS        axiom         -> (none)                         N/A (G-AX)
#
# 4 uniqueness ported + 4 added; 2 soundness (1 ported, 1 re-shaped);
# 1 admissibility RE-AIMED and landed; 2 frame-mutation vacuous; axiom lane
# dropped. 11 SPEC cases (2 soundness, 1 admissibility, 8 uniqueness).
#
# THREE DISPOSITIONS WERE CORRECTED UNDER AUDIT, all three because the recorded
# reason was false of this artifact rather than merely thin:
#   * admiss-drain was recorded DEGENERATE ("the method has no `require`, and the
#     reject lane's failures are the non-degeneracy demonstration"). The reject
#     lane demonstrates the post-image is not degenerate; it does NOT test the
#     PRECOND-TOO-STRONG direction, which on a total carrier with an empty
#     precondition is the obligation being unsatisfiable at an F2P-shaped input.
#     Landed as admiss-obligation-satisfiable-at-f2p, with its liveness measured.
#   * the DIVERGENCE class was recorded a known corpus-wide hole on the ground
#     that this bundle is `partial`; it now reads `total` (Solution.lean line 4),
#     the note having been overtaken by the corpus-wide remediation of that hole,
#     under
#     which the diverging rival IS rejected, measured. The recorded reason was
#     therefore false, and false in the spec's DISfavour. No case ships, because
#     the rejection fires at the method declaration and no witness can elaborate
#     against such a rival (measured with a trivially true witness); see the
#     docstring for the full measurement. The class is closed by the spec.
#   * rej-aggregator-all's witness was byte-identical to rej-drop-first's, so the
#     footer's claim that the reject witnesses probe DISTINCT input points was
#     false of that pair. RE-AIMED to a genuinely distinct point.
#
# RE-SHAPED (pos-echo -> pos-return-model): the sibling's grounded-echo positive
#   folds the per-step decision through the grounded pure helper. On this carrier
#   the maximally-different correct impl drops the loop entirely and returns the
#   grounded model `anyImaginary coords`; it doubles as the no-ungrounded-echo
#   control (the model is the real work, not an answer-key). PORTED / re-shaped
#   (pos-reorder -> pos-local-reshape): the sibling's positive reorders the trigger
#   conjunction and binds a local boolean; that maps directly to binding the
#   per-coordinate `coordImaginary c` into a local `e` before OR-ing, keeping the
#   invariants verbatim so the frozen proof closes.
# PORTED (the four value/branch rivals):
#   rej-extra -> rej-coarse-present (the prepatch bug: consult the coarse
#     imaginary-present indicator `imagPresent` instead of the strict
#     provably-nonzero `imagNonzero`; the F2P discriminator). rej-polarity ->
#     rej-polarity (invert the provably-nonzero polarity). rej-drop-first ->
#     rej-drop-first (skip the first coordinate; refuted at the distinguishing
#     first-coordinate input). rej-const-false -> rej-const-false (delete the
#     screen; the value-collapse rival).
# ADDED (rej-drop-numeric): drop the concrete-number conjunct and screen on the
#   imaginary judgement alone. On the nagini carrier the numeric fact is folded
#   into `coord_kind==1` inside the same conjunct as the verdict, so the sibling
#   has no standalone rival for it; the velvet `Coord` splits `numeric` and
#   `imagNonzero` into independent fields, so the numeric conjunct is separately
#   attackable and is the ONLY rival keying on `numeric`. Added so every conjunct
#   of `coordImaginary` is attacked on its own.
# RE-AIMED (admiss-drain -> admiss-obligation-satisfiable-at-f2p): the sibling's
#   control asserts the loop drains to i==0 under its half-permission
#   precondition. This backend's method has NO `require` clause and no permission
#   surface, so that exact assertion has no analogue — but the LANE does. On a
#   total carrier the PRECOND-TOO-STRONG analogue is the obligation being
#   UNSATISFIABLE at an F2P-shaped input, and the shipped case discharges the
#   obligation at that concrete input by evaluation, as `have`s, before closing
#   the frozen obligation verbatim. Its liveness is measured out-of-band: the same
#   case asserting the OPPOSITE value at that input fails to elaborate (exit 1),
#   so the `have` cannot be satisfied by a false claim.
# VACUOUS (rej-frame-extra, rej-frame-kind): the sibling's two MANDATORY frame
#   rivals WRITE to a read-only input (`coord_extra[i-1] = 0` / `coord_kind[i-1] =
#   0`) held at `Acc(list_pred(.), 1/2)`, rejected by the insufficient-permission
#   check. This backend is referentially transparent: `coords` is an immutable
#   value, NO `mut` binder is declared for it (the `mut` locals are the loop's own
#   `result`/`i`, not inputs), and there is no heap, no aliasing, and no permission
#   system. There is no read-only input to overwrite and no frame clause to
#   violate, so the class has no carrier analogue. Omitted as a genuine carrier
#   fact, NOT fabricated (porting map: this class is vacuous on a referentially-
#   transparent backend).
# DIVERGENCE / NON-TERMINATION: no case ships, and the reason is NOT the one the
#   earlier revision gave. It claimed `loom.semantics.termination "partial"` and
#   deferred to the corpus-wide `partial` hole; Solution.lean line 4 now sets
#   `"total"` (that hole having since been remediated corpus-wide), under which the verifier discharges a termination obligation and the
#   diverging rival is REJECTED (measured: the frozen loop minus only its
#   `decreasing i` annotation fails with `Decreasing annotations are required in
#   total correctness semantics`, exit 1). What blocks the case is the witness
#   protocol: that error is raised at the METHOD DECLARATION, so a witness file
#   built on the rival never reaches its own `example` — measured with a trivially
#   true witness (`1 + 1 = 2`) against the rival, exit 1 with the identical error.
#   A case shipped anyway records `witness-unproven` and forces MALFORMED-TESTS
#   (measured). So the class is CLOSED BY THE SPEC and carries no case because the
#   rejection is too early for a witness to observe, not because it is vacuous and
#   not because the spec admits it.
# BINDER / CLAUSE COVERAGE. The single `ensures out = anyImaginary coords` binds
#   `out` and `coords`; the element-wise model reads each `Coord`'s `numeric` and
#   `imagNonzero` and must IGNORE `imagPresent`, over the whole list. All
#   sub-obligations are attacked:
#     * NONZERO vs COARSE (read `imagNonzero`, not `imagPresent`): rej-coarse-
#       present (numeric ∧ present ∧ ¬nonzero -> gold false, rival true).
#     * POLARITY (fire on nonzero, not its negation): rej-polarity (numeric ∧
#       ¬nonzero ∧ ¬present -> gold false, rival true).
#     * NUMERIC conjunct (require concrete number): rej-drop-numeric (¬numeric ∧
#       nonzero ∧ ¬present -> gold false, rival true — the ONLY rival keying on
#       `numeric`).
#     * POSITIONAL / element-wise: rej-drop-first (first coordinate skipped ->
#       gold true, rival false — the ONLY multi-element witness).
#     * VALUE collapse / whole clause: rej-const-false (numeric ∧ nonzero ∧
#       present -> gold true, rival false).
#     * AGGREGATOR (`any`, not `all`): rej-aggregator-all — one triggering + one
#       non-triggering coordinate -> gold true, rival false. Attacks the combining
#       OPERATOR rather than an element or a position (added by audit).
#     * POSITIONAL, TAIL: rej-head-only — trigger NOT leading -> gold true, rival
#       false. The mirror of rej-drop-first, so both ends of the list are pinned
#       (added by audit).
#     * COARSE FIELD MUST BE IGNORED, under-rejecting direction:
#       rej-require-present — the coarse flag demanded as an EXTRA conjunct
#       (numeric ∧ nonzero ∧ ¬present -> gold true, rival false). The polarity
#       MIRROR of rej-coarse-present, which substitutes the coarse field and
#       over-rejects; together they pin that `imagPresent` is neither a substitute
#       for nor an addition to `imagNonzero` (added by audit).
#   The eight reject witnesses probe DISTINCT input points and move
#   every `Coord` field off any fixed value:
#     * rej-coarse-present    [(true,  false, true )]
#     * rej-polarity          [(true,  false, false)]
#     * rej-drop-numeric      [(false, true,  false)]
#     * rej-require-present   [(true,  true,  false)]
#     * rej-drop-first        [(true,  true,  true ), (false, false, false)]
#     * rej-aggregator-all    [(true,  true,  true ), (true,  false, false)]
#     * rej-head-only         [(false, false, false), (true,  true,  true )]
#     * rej-const-false       [(true,  true,  true )]
#   So `numeric` ranges over {true, false}, `imagNonzero` over {true, false},
#   `imagPresent` over {true, false}, and the list length over {1, 2}. No field is
#   pinned at a single value across the reject set. All four combinations of
#   (`imagNonzero`, `imagPresent`) at `numeric = true` are now probed — (F,T),
#   (F,F), (T,F), (T,T) — which is what makes the coarse-vs-strict distinction
#   pinned in both directions rather than only in the over-rejecting one; the
#   (T,F) point was missing before the audit. Every reject witness now probes a
#   point no other reject witness probes.
# WITNESS DISCRIMINATION. Each witness ELABORATES against its loop-free rival
#   (the extracted program's result provably violates the ensures at the probed
#   input, `imaginaryCoordCheckTester … = false` closing by `decide`; exit 0) and
#   is REFUTED against the declared `witness_reference` `_POS_RETURN_MODEL` — the
#   loop-free impl of the same frozen spec that VERIFIES — with "Tactic `decide`
#   proved that the proposition … is false" (exit 1). It is NOT refuted against
#   the frozen solution, whose `Classical.choice`-bearing loop makes `decide`
#   stuck for every claim including tautologies; see the CARRIER NOTE for the four
#   builds that establish gold's exit code is uninformative, INDEPENDENTLY
#   RE-MEASURED under audit, together with the mirror-image measurement that makes
#   the reference admissible: against the reference the refutation FAILS (exit 1,
#   by refutation), the flipped claim ELABORATES (exit 0) and the tautology
#   ELABORATES (exit 0), so the reference's exit code tracks the claim while gold's
#   does not. The carrier is a
#   fully concrete literal at every witness, so each closes by `decide` with no
#   hypothesis and there is no joint-satisfiability obligation. No `sorry`/
#   `admit`/`native_decide`/`axiom` appears.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (the sibling models the
#   per-coordinate test as an A-reference validated by axiom_check.py, not a
#   consumed axiom — mapping.md §3), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
