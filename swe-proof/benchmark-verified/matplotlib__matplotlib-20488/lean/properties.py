"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-20488 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
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

DEFENDED SURFACE (one total function over an exact-rational carrier)
--------------------------------------------------------------------
A single modeled function sanitises the lower/upper bound pair of a value range
before it is handed to a display scale:

  boundedRange (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ

The three top-level clauses of ``problem_spec_boundedRange`` PARTITION the domain
and pin the output pair exactly on every input (a grounded, complete oracle —
the result is a function of the args):

  (F)  result.2 = bounds.2                                          upper-bound frame
  (P2) (logScale = true ∧ bounds.1 ≤ 0) → result.1 = floor          exact floor
  (P3) ¬(logScale = true ∧ bounds.1 ≤ 0) → result.1 = bounds.1      passthrough

Because the oracle is fully grounded in the args (``floor`` / ``bounds``), there
is no answer-key to echo, so ungrounded-oracle-echo is N/A here; the positive
controls are the cheapest grounded honest impls.

WHAT DRIVES THE REJECTS. The defect the gold change repairs is a boundary defect
at the exact-zero lower bound: the old guard fires only on a STRICTLY-negative
lower bound, so an exact-zero lower bound under a log scale slips through
untouched and is still handed to the log scale (which then rejects it). The
discriminating clause is (P2): when a log scale is in use and the lower bound is
non-positive, the sanitised lower bound must equal ``floor``. The high-value
attacks are therefore PARTIAL-DOMAIN rivals at the exact-zero boundary, plus
value/overreach rivals that probe whether (P2)/(P3) actually pin the constant and
the passthrough, plus one frame rival probing (F).

BINDER / CLAUSE COVERAGE. The spec predicate has three input binders —
``logScale``, ``floor``, ``bounds`` (whose components ``bounds.1``/``bounds.2``
play distinct roles). The reject witnesses vary all of them:

  * ``logScale`` — the reject inputs use BOTH ``true`` (the log branch: strict-lt,
    ge-passthrough, wrong-constant, overreach-clamp) and ``false`` (the non-log
    branch: nonlog-sanitizes, upper-frame). A rival that mishandled only one
    ``logScale`` value would be caught by the other family.
  * ``bounds.1`` (lower bound) — probed at ``= 0`` (the exact-zero boundary that
    is the gold-repaired defect), ``< 0`` (strictly negative), and ``> 0`` (the
    passthrough sub-domain the overreach rival abuses). (P2)'s sub-domain is
    attacked at BOTH of its points, and by rivals that are wrong at one while
    correct at the other: the two ``reject-partial-*`` rivals clamp correctly on
    the strictly-negative half and miss only ``= 0``, while
    ``reject-partial-eq-zero-only`` clamps correctly at ``= 0`` and misses the
    whole strictly-negative half. Neither point alone pins (P2).
  * ``bounds.2`` (upper bound) — the upper-frame rival ``reject-upper-not-passed``
    is refuted only because it corrupts ``bounds.2``; every other witness holds
    ``bounds.2`` at a value distinct from ``bounds.1`` so the frame clause is a
    live constraint, not vacuously satisfied.
  * ``floor`` — the wrong-constant rival returns ``floor + 1``; its witness is
    refuted precisely because (P2) pins ``floor`` and not merely a positive value.
  * the RELATION between ``floor`` and ``bounds.1`` — probed by
    ``reject-overreach-clamp-below-floor``, whose witness is the only one that
    puts ``floor`` ABOVE ``bounds.1``. Every other reject input has ``floor``
    small relative to a positive ``bounds.1``, so an impl keying off ``bounds.1 <
    floor`` rather than ``bounds.1 ≤ 0`` agrees with gold at all of them.

Each independent top-level clause is attacked: (P2) by strict-lt, ge-passthrough,
eq-zero-only, wrong-constant; (P3) by overreach-clamp (log & lb>0),
overreach-clamp-below-floor (log & 0<lb<floor, the sub-domain the whole-branch
clamp cannot isolate) and nonlog-sanitizes (non-log & lb≤0); (F) by
upper-not-passed.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
impl's exact elaboration — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec predicate at one concrete input. This carrier is exact ``ℚ``
and fully transparent (no ``opaque`` callee), so the witnesses state the spec
predicate directly at literal inputs and close by ``decide``; the one witness
whose rival returns a rational SUM (``floor + 1``) closes with
``simp only [Id.run, bind, pure]; norm_num`` instead, because ``decide`` does not
reduce ``Rat.add`` through the ``Decidable`` instance and FAILS on that rival
(measured on a real build, not assumed — SPEC_GUIDE). No witness binds a
hypothesis, so there is no consistency obligation.

Every witness states its refutation DIRECTLY as ``¬ problem_spec_boundedRange``
at the literal input, with no intermediate ``have`` pinning the rival's output
pair. That is deliberate rather than stylistic: a witness routed through the
rival's concrete output value fails on the frozen solution merely because gold
computes a DIFFERENT pair, so its gold-side exit code discriminates on output
value rather than on spec satisfaction — which is not what the second build is
supposed to attest. Stated directly, each witness's gold-side build instead
fails by refuting the claim itself: the ``decide`` witnesses report ``Tactic
`decide` proved that the proposition ... is false`` (the kernel evaluated the
spec predicate at that very input and found gold satisfies it), and the
``norm_num`` witness reports ``unsolved goals ⊢ False`` on the example's own
goal. Each was checked with two real builds: it ELABORATES against its rival
and FAILS SEMANTICALLY on the frozen solution, so each discriminates rather
than asserting a tautology.

FORGERY-CHECKED (audit, four builds per reject case). "The gold-side error looks
semantic" is not evidence; an error is evidence only if it CHANGES when the claim
changes. So each witness was rebuilt with its claim FLIPPED — the leading ``¬``
dropped, i.e. asserting that the impl SATISFIES the spec at that same input — and
built against both subjects. Every case inverts cleanly: witness = (rival 0, gold
1), flipped = (rival 1, gold 0). The gold-side exit code therefore tracks the
claim rather than the file, which is what rules out the hollow-signature class
(a stuck reduction, a missing instance, a unification failure on an unreduced
term) where both the claim and its negation fail identically.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
  * FRAME / PERMISSION MUTATION — VACUOUS here, exactly as the nagini sibling
    already notes for itself: the inputs are scalar value types passed by value,
    there is no read-only half-permission to overwrite and no aliasing, so the
    write-to-input rival has no counterpart and no substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION — VACUOUS here, and MEASURED rather than argued
    (this bundle sets no ``loom.semantics.termination``; it is a plain Lean
    ``def``, so the termination obligation is the elaborator's own). Two diverging
    rivals were built during the audit. A self-recursive body
    (``implementation_boundedRange l f b = implementation_boundedRange l f b``)
    fails to elaborate at all — ``fail to show termination for
    implementation_boundedRange`` — and the same error breaks the WITNESS file,
    which is the half that must succeed, so the case can only ever record
    ``witness-unproven``. Marking it ``partial def`` elaborates the module but
    makes the definition irreducible: the witness then fails with ``Tactic
    `unfold` failed to unfold `implementation_boundedRange```, again on the rival
    side. So the class is vacuous for a structural reason — a diverging impl on
    this carrier is not a rival the verifier REJECTS on the merits, it is a file
    that does not compile — not because the case was hard. (The nagini sibling
    carries no divergence case either.)
  * The nagini surface abstracts a single scalar lower bound and does NOT model
    the upper bound. This lean carrier models the FULL ``(lo, hi)`` pair, so it
    has an extra top-level clause (F) pinning the upper-bound passthrough. That
    clause has no nagini counterpart; it is defended by all three positive
    controls and attacked by the new ``reject-upper-not-passed`` rival (a rival
    the nagini surface could not express).
  * nagini ``pos-control-nested-reorder`` ↦ ``pos-nested-reorder`` (non-log-first
    nested-if, a structurally different but correct impl); nagini
    ``pos-control-cheapest-grounded`` ↦ ``pos-cheapest-conditional`` (a direct
    conditional expression). Both reprove the frozen obligation.
  * nagini ``admiss-f2p-shaped`` ↦ ``admiss-f2p-ground``: the frozen obligation
    carries a precondition hypothesis (``0 < floor``) but not one that could
    reject a normal input, so the honest analogue discharges the spec at the
    exact F2P input (log scale, lower bound = 0) as a ``have`` inside the proof
    body and confirms the sanitised lower bound is the strictly-positive floor,
    then closes the frozen obligation verbatim.
  * nagini reject rivals map as: ``reject-partial-strict-lt-misses-zero`` (the
    pre-patch skeleton, ``< 0``) ← nagini ``reject-partial-strict-lt-misses-zero``;
    ``reject-partial-ge-zero-passthrough`` ← nagini ``reject-partial-ge-zero-
    passthrough``; ``reject-wrong-positive-constant`` ← nagini
    ``reject-wrong-positive-constant``; ``reject-overreach-clamp-positive`` ←
    nagini ``reject-overreach-clamp-positive``; ``reject-overreach-nonlog-
    sanitizes`` ← nagini ``reject-overreach-nonlog-sanitizes``. Two rivals have
    NO nagini counterpart and were added by audit passes:
    ``reject-partial-eq-zero-only`` (the complementary half of (P2)'s sub-domain)
    and ``reject-overreach-clamp-below-floor`` (the ``floor``/``bounds.1``
    relation, which the nagini surface constrains no better).

WHAT THE nagini P1 CLAUSE BECAME (not a dropped obligation)
-----------------------------------------------------------
The nagini postcondition carries a THIRD top-level clause this spec does not
spell out — ``(P1) Implies(is_log, Result() > 0.0)``, the headline "a log scale
never receives a non-positive lower bound" guarantee. It is not weakened away
here: it is ENTAILED by (P2)/(P3) together with the ``0 < floor`` precondition,
and the entailment was machine-checked during the audit by proving, against the
frozen spec, that any ``result`` satisfying ``problem_spec_boundedRange`` with
``0 < floor`` has ``logScale = true → 0 < result.1`` (clamped branch: ``result.1
= floor > 0``; passthrough branch: ``¬(bounds.1 ≤ 0)`` gives ``0 < bounds.1 =
result.1``). The lean spec is strictly STRONGER than P1, not merely different —
``reject-wrong-positive-constant`` returns ``floor + 1``, which satisfies P1 on
every input and is still rejected, so the value pin is doing work P1 cannot.

THE POSITIVES ARE GENUINE RESHAPES (audit-verified, not asserted)
-----------------------------------------------------------------
A positive control whose "different shape" is definitionally equal to the frozen
impl would verify honestly while testing nothing. Both positives were checked
against that: each impl was substituted under the UNCHANGED frozen proof script,
and both builds FAILED — ``pos-cheapest-conditional`` with ``Failed to rewrite
using equation theorems for `Id.run` `` (it drops the monadic wrapper entirely)
and ``pos-nested-reorder`` with ``rewrite failed: Did not find an occurrence of
the pattern if logScale = true ∧ bounds.1 ≤ 0`` (its guard is genuinely split in
two). So each positive's fresh proof is re-establishing the obligation for an
impl the frozen script cannot close, which is what makes it a real
SPEC-TOO-STRONG probe.

THE ONE UNCONSTRAINED REGION, AND WHY IT IS NOT A HOLE
-------------------------------------------------------
The obligation is guarded by ``0 < floor``, so nothing is claimed when the floor
is non-positive. That region is genuinely unconstrained: an impl that returns
arbitrary garbage (e.g. the constant pair ``(42, 99)``) whenever ``floor ≤ 0``
and behaves exactly like gold otherwise VERIFIES against the frozen spec —
confirmed with a real build during the audit. This is NOT a spec hole. The
binder models a machine epsilon, which is strictly positive on every dtype the
caller can reach (the nagini sibling's axiom lane measures exactly that), so the
region is unreachable in the real program and a rival exploiting it has no
faithful real patch that could pass or fail differently. Recorded here so a
later reader does not re-derive it as a finding; a rival confined to it would be
vacuous and is deliberately not shipped.

AXIOM lane: the nagini ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's job
and this gate ignores it. (This bundle declares no ``opaque`` and no ``axiom``:
the positivity of the floor is carried as the ``0 < floor`` precondition
hypothesis on ``correct_boundedRange``, not as an axiomatized callee, so there is
nothing for the axiom lane to probe here.)
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20488"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The frozen impl body (entire `implementation_boundedRange` def, inside the
# impl region). Swapping this replaces ONLY the implementation.
_IMPL_GOLD = (
    "def implementation_boundedRange\n"
    "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
    "  let mut sLo := bounds.1\n"
    "  let sHi := bounds.2\n"
    "  if logScale = true ∧ sLo ≤ 0 then\n"
    "    sLo := floor\n"
    "  return (sLo, sHi)"
)

# The frozen proof body (entire `correct_boundedRange` theorem, inside the proof
# region). Swapping this replaces ONLY the proof; the STATEMENT is re-emitted
# byte-identically in every replacement so `same_spec` and the byte-identical
# obligation-statement rule both hold.
_PROOF_GOLD = (
    "theorem correct_boundedRange :\n"
    "    ∀ (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ), 0 < floor →\n"
    "      problem_spec_boundedRange logScale floor bounds\n"
    "        (implementation_boundedRange logScale floor bounds) := by\n"
    "  intro logScale floor bounds _hfloor\n"
    "  unfold implementation_boundedRange problem_spec_boundedRange\n"
    "  by_cases h : logScale = true ∧ bounds.1 ≤ 0\n"
    "  · rw [Id.run, if_pos h]\n"
    "    exact ⟨rfl, fun _ => rfl, fun hc => absurd h hc⟩\n"
    "  · rw [Id.run, if_neg h]\n"
    "    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩"
)

# The byte-identical theorem STATEMENT header (re-used by every proof-region
# swap so the obligation statement never changes).
_STMT = (
    "theorem correct_boundedRange :\n"
    "    ∀ (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ), 0 < floor →\n"
    "      problem_spec_boundedRange logScale floor bounds\n"
    "        (implementation_boundedRange logScale floor bounds) := by\n"
)


def _impl(new_impl: str) -> str:
    return _swap(_BASE, _IMPL_GOLD, new_impl)


def _proof(new_proof: str) -> str:
    return _swap(_BASE, _PROOF_GOLD, new_proof)


# A soundness/admissibility case may need BOTH the impl and the proof reshaped
# (a different impl needs its own closing proof). Compose the two swaps.
def _impl_and_proof(new_impl: str, new_proof: str) -> str:
    return _swap(_impl(new_impl), _PROOF_GOLD, new_proof)


# ---- witness helpers --------------------------------------------------------
# A reject witness states the frozen spec predicate directly at a concrete
# literal input and refutes it for the rival. Stated at literal inputs, so it
# binds no hypothesis (no consistency obligation).

def _wit_decide(logScale, floor, bounds) -> str:
    return (
        f"example : ¬ problem_spec_boundedRange {logScale} {floor} {bounds}\n"
        f"    (implementation_boundedRange {logScale} {floor} {bounds}) := by\n"
        f"  unfold problem_spec_boundedRange implementation_boundedRange\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify (else the spec is over-fit => SPEC-
    # TOO-STRONG). Each keeps the `theorem correct_boundedRange` STATEMENT
    # byte-identical; only the impl body and its closing tactic body change. No
    # helper lemma, no axiom, no assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-nested-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Nested-if shape, non-log branch handled first (the log clamp split into
        # two nested conditions with the CORRECT `≤ 0` boundary). Same value on
        # every input; a fresh proof closes it by case-splitting the two flags.
        "module": _impl_and_proof(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if logScale = true then\n"
            "    if sLo ≤ 0 then\n"
            "      sLo := floor\n"
            "  return (sLo, sHi)",
            _STMT +
            "  intro logScale floor bounds _hfloor\n"
            "  unfold implementation_boundedRange problem_spec_boundedRange\n"
            "  simp only [Id.run, bind, pure]\n"
            "  by_cases hl : logScale = true\n"
            "  · by_cases hb : bounds.1 ≤ 0\n"
            "    · simp [hl, hb]\n"
            "    · simp [hl, hb]\n"
            "  · simp [hl]",
        ),
        "rationale": "a structurally-different (non-log-first, nested-if) but "
                     "CORRECT impl with the same `≤ 0` boundary must satisfy "
                     "(F)/(P2)/(P3); if it cannot verify the postcondition is "
                     "over-fit to the exact conditional spelling => SPEC-TOO-STRONG. "
                     "Proof closes by case-splitting the two flags — no induction, "
                     "no new lemma, statement byte-identical.",
    },
    {
        "id": "pos-cheapest-conditional",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest faithful impl: a direct conditional expression building the
        # pair, no `Id.run do`/mutation. Same value; a fresh proof closes it.
        "module": _impl_and_proof(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ :=\n"
            "  let sLo := if logScale = true ∧ bounds.1 ≤ 0 then floor else bounds.1\n"
            "  (sLo, bounds.2)",
            _STMT +
            "  intro logScale floor bounds _hfloor\n"
            "  unfold implementation_boundedRange problem_spec_boundedRange\n"
            "  by_cases h : logScale = true ∧ bounds.1 ≤ 0\n"
            "  · simp [h]\n"
            "  · simp [h]",
        ),
        "rationale": "the oracle is fully grounded (result is a function of the "
                     "args), so the cheapest faithful impl is a direct conditional "
                     "expression; it must verify. Directive-2 grounded positive "
                     "control in place of an ungrounded-oracle echo (there is no "
                     "answer-key to echo). Statement byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at the
    # exact F2P input (log scale, lower bound = 0, floor > 0), rather than only
    # provable in the abstract. Discharged as a `have` inside the frozen proof
    # body BEFORE the frozen obligation is closed verbatim; the impl and the
    # theorem statement are unchanged, and nothing is assumed. If that ground
    # instance could not be discharged, the modeled behavior would be unsatisfiable
    # at exactly the input shape the F2P exercises (the analogue of PRECOND-TOO-
    # STRONG).
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof(
            _STMT +
            "  -- admissibility: the exact F2P input (log scale, lower bound = 0)\n"
            "  -- lies inside the precondition. STRENGTHENED BY AUDIT: the OBLIGATION\n"
            "  -- ITSELF (the spec predicate at that concrete input) is discharged by\n"
            "  -- kernel evaluation, not merely the impl's output value — an impl-value\n"
            "  -- `have` alone would still pass if the predicate were unsatisfiable\n"
            "  -- there through some other clause.\n"
            "  have _spec : problem_spec_boundedRange true 1 (0, 7)\n"
            "      (implementation_boundedRange true 1 (0, 7)) := by\n"
            "    unfold problem_spec_boundedRange implementation_boundedRange\n"
            "    decide\n"
            "  -- ...and the sanitised lower bound at that input is the strictly-\n"
            "  -- positive floor, which is the property the F2P input actually needs.\n"
            "  have _pos : (implementation_boundedRange true 1 (0, 7)).1 = 1\n"
            "      ∧ (0 : ℚ) < (implementation_boundedRange true 1 (0, 7)).1 := by\n"
            "    have h : implementation_boundedRange true 1 (0, 7) = (1, 7) := by\n"
            "      unfold implementation_boundedRange; decide\n"
            "    rw [h]; exact ⟨rfl, by norm_num⟩\n"
            "  intro logScale floor bounds _hfloor\n"
            "  unfold implementation_boundedRange problem_spec_boundedRange\n"
            "  by_cases h : logScale = true ∧ bounds.1 ≤ 0\n"
            "  · rw [Id.run, if_pos h]\n"
            "    exact ⟨rfl, fun _ => rfl, fun hc => absurd h hc⟩\n"
            "  · rw [Id.run, if_neg h]\n"
            "    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩",
        ),
        "rationale": "the obligation is discharged at the exact CI failure input "
                     "(log scale, lower bound = 0, floor > 0): the spec PREDICATE "
                     "instance at that input is closed by kernel evaluation and the "
                     "sanitised lower bound evaluates to the strictly-positive "
                     "floor, then the frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior is unsatisfiable at the normal input, the "
                     "analogue of PRECOND-TOO-STRONG). Nothing assumed: no new "
                     "declaration, statement byte-identical, ground instance is a "
                     "`have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the frozen
    # spec that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival is a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input, checked to
    # elaborate against the rival and fail on the frozen solution.
    # =====================================================================
    {
        "id": "reject-partial-strict-lt-misses-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: guard fires only on a STRICTLY-negative lower
        # bound, so an exact-zero lower bound under a log scale passes through.
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if logScale = true ∧ sLo < 0 then\n"
            "    sLo := floor\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "this IS the pre-patch guard (strictly-negative test misses "
                      "the exact-zero lower bound). Its faithful real patch leaves an "
                      "exact-zero lower bound in place for the log scale, which then "
                      "rejects it (the range becomes invalid) — exactly the CI "
                      "failure the change repairs. Does NOT resolve the F2P.",
        "rationale": "REJECT from (P2): at logScale=true, bounds.1 = 0 the rival "
                     "passes 0 through while (P2) demands result.1 = floor. If it "
                     "verified the spec would be SPEC-TOO-WEAK at the boundary.",
        "witness": _wit_decide("true", "1", "(0, 7)"),
    },
    {
        "id": "reject-partial-ge-zero-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Same defect, different surface: a `≥ 0` passthrough test leaks the
        # exact-zero lower bound (the G-MUT survivor `>` -> `>=` made explicit).
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if logScale = true ∧ sLo ≥ 0 then\n"
            "    sLo := sLo\n"
            "  else if logScale = true then\n"
            "    sLo := floor\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "the `≥ 0` passthrough keeps an exact-zero lower bound in "
                      "place for the log scale, so the faithful real patch still "
                      "hands 0 to the log scale -> the range is rejected. This is the "
                      "surviving `'>' -> '>='` mutant made explicit. Does NOT resolve "
                      "the F2P.",
        "rationale": "REJECT from (P2): at logScale=true, bounds.1 = 0 the `≥ 0` "
                     "branch passes 0 through instead of the floor; (P2) demands "
                     "result.1 = floor. A verify here is SPEC-TOO-WEAK at the bug.",
        "witness": _wit_decide("true", "3", "(0, 9)"),
    },
    {
        # ADDED BY AUDIT. The two partial-domain rivals above both clamp on the
        # STRICTLY-NEGATIVE half and miss only the exact-zero point, so (P2) was
        # attacked at `bounds.1 = 0` and at no other point of its sub-domain: no
        # shipped rival failed to clamp a strictly-NEGATIVE lower bound. This is
        # the complementary partial-domain rival — the guard fires only at
        # `= 0`, so it is CORRECT at the exact-zero boundary the other two miss
        # and wrong on the whole strictly-negative half. It keeps (P2) from being
        # pinned by a single point of its domain.
        "id": "reject-partial-eq-zero-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if logScale = true ∧ sLo = 0 then\n"
            "    sLo := floor\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "an equality guard sanitises the exact-zero lower bound but "
                      "leaves every strictly-negative one in place, so its faithful "
                      "real patch still hands a negative lower bound to the log "
                      "scale, which rejects it. It repairs the single reported input "
                      "and reintroduces the same class of failure just below it — a "
                      "point-fix, not the boundary fix. Does NOT resolve in general.",
        "rationale": "REJECT from (P2): at logScale=true, bounds.1 = -4 the guard "
                     "does not fire and the rival passes -4 through, while (P2) "
                     "demands result.1 = floor for EVERY non-positive lower bound, "
                     "not only for zero. A verify here would mean (P2) is pinned "
                     "only at the boundary point => SPEC-TOO-WEAK on the strictly-"
                     "negative half.",
        "witness": _wit_decide("true", "1", "(-4, 8)"),
    },
    {
        "id": "reject-wrong-positive-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Sanitises the right domain but to a DIFFERENT positive value (floor + 1)
        # instead of floor. Positive, but violates the value pin (P2).
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if logScale = true ∧ sLo ≤ 0 then\n"
            "    sLo := floor + 1\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "the real patch sets the lower bound to the floor (the "
                      "smallest representable positive magnitude). Returning floor+1 "
                      "hands the log scale a lower bound far above the data floor, "
                      "shifting the normalization so the rendered image no longer "
                      "matches the reference figure -> the image comparison MISMATCHES "
                      "-> the F2P FAILS. Does NOT resolve (it produces a wrong "
                      "figure).",
        "rationale": "REJECT from (P2): (P2) pins result.1 = floor exactly, not "
                     "merely positivity; floor+1 violates it at logScale=true, "
                     "bounds.1 ≤ 0. A verify here is SPEC-TOO-WEAK (P2 not pinning "
                     "the constant).",
        # `floor + 1` is a rational SUM; plain `decide` does NOT close this one —
        # measured, the rival build reports "Tactic `decide` failed for
        # proposition ... have sLo := 2 + 1" (the `Rat.add` does not reduce
        # through the `Decidable` instance, SPEC_GUIDE). So the witness reduces
        # the monadic impl with `simp only [Id.run, bind, pure]` and finishes
        # with `norm_num`, which DOES decide the rational literals.
        #
        # Stated as the DIRECT refutation of the spec predicate at the literal
        # input — no intermediate `have` pinning the rival's output pair. That
        # matters for the gold half of the discrimination check: with the value
        # scaffolding, the frozen build failed inside the `have` (gold's pair is
        # not the rival's), which discriminates on the OUTPUT VALUE rather than
        # on spec satisfaction. Direct, the frozen build instead fails with
        # `unsolved goals ⊢ False` on the example's own goal — `norm_num`
        # discharges the spec predicate for gold and is then left unable to
        # produce `False`, i.e. a semantic refutation of exactly the claim the
        # witness makes.
        "witness": (
            "example : ¬ problem_spec_boundedRange true 2 (-5, 4)\n"
            "    (implementation_boundedRange true 2 (-5, 4)) := by\n"
            "  unfold problem_spec_boundedRange implementation_boundedRange\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
        ),
    },
    {
        "id": "reject-overreach-clamp-positive",
        "kind": "uniqueness",
        "expect": "reject",
        # Clamps an already-STRICTLY-POSITIVE lower bound down to the floor in the
        # log branch (sanitises when it must not). Violates passthrough (P3).
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if logScale = true then\n"
            "    sLo := floor\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "the real patch leaves an already-positive lower bound "
                      "UNCHANGED (the guard fires only when it is non-positive). "
                      "Forcing a positive lower bound down to the floor destroys the "
                      "intended log-scale lower bound, so the rendered figure no "
                      "longer matches the reference -> the image comparison "
                      "MISMATCHES -> the F2P (and its sibling) FAIL. Does NOT "
                      "resolve.",
        "rationale": "REJECT from (P3): on the logScale=true, bounds.1 > 0 "
                     "sub-domain the passthrough branch requires result.1 = "
                     "bounds.1, but the rival returns floor. A verify here is "
                     "SPEC-TOO-WEAK (P3 not enforcing passthrough).",
        "witness": _wit_decide("true", "1", "(3, 8)"),
    },
    {
        # ADDED BY AUDIT (second pass). `reject-overreach-clamp-positive` clamps on
        # the WHOLE log branch, so it is wrong at every positive lower bound and any
        # single (P3) point catches it. That left the RELATIONAL sub-domain
        # unattacked: no shipped rival is wrong only where the lower bound is
        # strictly positive but still BELOW the floor. That band is where a
        # plausible mis-implementation actually lives — "raise anything under the
        # representable floor up to it" reads as defensive rounding rather than as a
        # bug — and it is invisible to every witness the battery shipped, because
        # each of those states its input with `floor` small relative to `bounds.1`.
        # This rival is correct at EVERY point the other rivals are probed at.
        "id": "reject-overreach-clamp-below-floor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if logScale = true ∧ sLo < floor then\n"
            "    sLo := floor\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "the real change replaces the lower bound ONLY when it is "
                      "non-positive; a strictly-positive lower bound is passed "
                      "through however small it is. Raising every sub-floor positive "
                      "lower bound up to the floor moves the lower limit installed "
                      "onto a log display scale for ranges the change must leave "
                      "alone, so the rendered figure no longer matches the reference "
                      "-> the image comparison MISMATCHES -> the F2P FAILS. Does NOT "
                      "resolve.",
        "rationale": "REJECT from (P3): the passthrough branch requires result.1 = "
                     "bounds.1 for EVERY strictly-positive lower bound, not only for "
                     "those at or above the floor. At logScale=true, floor=5, "
                     "bounds.1=2 the rival returns 5. A verify here would mean (P3) "
                     "pins the passthrough only where bounds.1 ≥ floor, leaving the "
                     "relation between the two rational binders unconstrained => "
                     "SPEC-TOO-WEAK. This is the only sub-domain the other rivals "
                     "leave untouched: it is the one whose input needs floor LARGER "
                     "than bounds.1, which no other witness here uses.",
        "witness": _wit_decide("true", "5", "(2, 9)"),
    },
    {
        "id": "reject-overreach-nonlog-sanitizes",
        "kind": "uniqueness",
        "expect": "reject",
        # Sanitises in the NON-log branch when the lower bound is non-positive
        # (drops the log-scale gate). Violates passthrough (P3) at logScale=false.
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.2\n"
            "  if sLo ≤ 0 then\n"
            "    sLo := floor\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "the real patch sanitises ONLY under a log scale. Replacing a "
                      "non-log, non-positive lower bound with the floor corrupts a "
                      "non-log display scale's lower bound (which legitimately "
                      "accepts non-positive values), changing rendered output for "
                      "non-log scales -> behaviour diverges from gold. Does NOT "
                      "resolve / regresses non-log scales.",
        "rationale": "REJECT from (P3): at logScale=false, bounds.1 ≤ 0 the "
                     "passthrough branch requires result.1 = bounds.1, but the rival "
                     "returns floor (dropping the log-scale gate). A verify here is "
                     "SPEC-TOO-WEAK (the gate in P2/P3 unenforced).",
        "witness": _wit_decide("false", "1", "(-2, 6)"),
    },
    {
        "id": "reject-upper-not-passed",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts the upper bound (returns the lower bound in both slots),
        # attacking the frame clause (F) that pins result.2 = bounds.2. This clause
        # has no nagini counterpart (the nagini surface models only the lower
        # bound); it is genuinely part of this carrier's postcondition.
        "module": _impl(
            "def implementation_boundedRange\n"
            "    (logScale : Bool) (floor : ℚ) (bounds : ℚ × ℚ) : ℚ × ℚ := Id.run do\n"
            "  let mut sLo := bounds.1\n"
            "  let sHi := bounds.1\n"
            "  if logScale = true ∧ sLo ≤ 0 then\n"
            "    sLo := floor\n"
            "  return (sLo, sHi)",
        ),
        "refinement": "the real patch never touches the upper bound (only the lower "
                      "bound is ever sanitised). An impl that overwrites the upper "
                      "bound with the lower bound installs the wrong upper limit onto "
                      "the display scale, so the rendered figure no longer matches "
                      "the reference -> the image comparison MISMATCHES -> the F2P "
                      "FAILS. Does NOT resolve.",
        "rationale": "REJECT from the frame clause (F: result.2 = bounds.2): the "
                     "rival returns bounds.1 in the upper slot, violating the "
                     "upper-bound passthrough whenever bounds.1 ≠ bounds.2. A verify "
                     "here is SPEC-TOO-WEAK (the upper-bound frame unconstrained).",
        "witness": _wit_decide("false", "1", "(5, 9)"),
    },
]
