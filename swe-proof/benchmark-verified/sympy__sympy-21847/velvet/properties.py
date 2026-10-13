"""properties.py — G-PBT falsification battery for sympy__sympy-21847 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct selectMonomials``
obligation survives with a byte-identical statement). ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must elaborate
against the rival and FAIL against the witness subject — here an explicit
``witness_reference``, for the measured reason in the CARRIER NOTE below, since
the frozen solution's loop encoding cannot decide any claim either way).

DEFENDED SURFACE (one contracted method):

  selectMonomials (candidates : List (List Nat)) (minDeg : Nat)
                                       return (out : List (List Nat))
    ensures out = selectByDegree minDeg candidates        (C1)

  ``selectByDegree`` is a total, fully-unfolded pure fold over the actual input
  ``candidates``: it keeps, in enumeration order, exactly the candidates whose
  total degree (``totalDegree p = p.sum``, the sum of a candidate's per-component
  multiplicities) is at least the supplied lower bound ``minDeg``. The single
  load-bearing ``ensures`` clause pins the result to that order-preserving
  filter. The one behavioural change the fix makes lives entirely inside the
  keep decision: the retention test is the SUM of the multiplicity vector, not
  its per-component maximum. Both `candidates` and `minDeg` are read-only value
  inputs (no `mut` binder).

CARRIER NOTE — witness route, and what the gold-side failure means.

  The spec is fully COMPUTABLE (`selectByDegree`/`totalDegree` are concrete
  `def`s; the `axioms` region is empty — no opaque callee), but the impl is a
  backward `while` loop. The `derive_tester_for` + `decide` route (the
  django-13658 pattern) is UNAVAILABLE here, and the reason is specific: velvet
  compiles `while` to `Loop.forIn.loop`, defined by `partial_fixpoint`, whose
  equation the KERNEL cannot unfold. Measured both ways — `#eval
  selectMonomialsExec [[2,1]] 3` prints `DivM.res [[2,1]]` (the compiler
  evaluates it fine), while `decide`/`simp [Loop.forIn.loop]` get stuck with
  reduction halted at the `forIn Lean.Loop.mk` gadget. So the obstruction is the
  `partial_fixpoint` loop encoding, not opacity and not a missing tactic.

  Each reject ``witness`` therefore refutes the method's Hoare triple DIRECTLY
  at a concrete, literal input —
  ``¬ triple True (selectMonomials …) (fun out => out = selectByDegree …)`` —
  reduced through ``triple_pure`` (every rival's impl is straight-line, so the
  loop gadget is absent and the `pure` triple collapses) and then discharged by
  ``decide`` on small literal vectors. Checked in a file whose ``prove_correct``
  block has been stripped so no tactic script interferes.

  CONSEQUENCE for reading the gate's two builds, stated because it is a real
  limitation of this carrier and not a defect these cases can repair: on the
  RIVAL the witness build is a genuine semantic refutation (`decide` reduces the
  straight-line impl and finds the postcondition false at the stated input). On
  GOLD the build fails with `failed to synthesize Decidable … forIn
  Lean.Loop.mk` — a STUCK REDUCTION on the loop encoding, not a semantic
  "the spec holds here".

  MEASURED, by the second audit, with the forgery experiment that decides this
  rather than reading the message: a file differing from the S-wrong-max witness
  ONLY in dropping the `¬` — i.e. asserting gold IS correct at `[[2,1]]`/`3`,
  the opposite of a refutation — fails against the frozen solution with the SAME
  error class, `failed to synthesize Decidable {True}do … forIn Lean.Loop.mk`
  (exit 1; the two logs differ only in the `¬` the pretty-printer echoes back
  out of the claim itself). So gold's exit code carries NO information about
  what the witness claims, and no case here may rest on it.

  REPAIR, landed rather than described: every reject case now names an explicit
  `witness_reference` — the straight-line `List.filter` impl of this same spec,
  which the gate independently re-verifies (shares the frozen spec AND verifies)
  before using. Against that reference the loop gadget is absent, so `decide`
  genuinely reduces and all five witnesses FAIL there with
  `Tactic `decide` proved that the proposition ¬… is false` — a semantic
  refutation of the refutation, at the concrete input each case names. The same
  forgery, built against that reference, ELABORATES (exit 0): the reference-side
  exit code tracks the claim, which is exactly the property gold's did not have.
  Pinning the subject in the manifest also stops the attestation from depending
  on the gate's implicit positive-fallback search, which is what previously
  supplied it (`gold_stuck_screen="decidable-instance"` in the prior record).

ADVERSARIAL READ of the weakness classes (others justified-N/A in `assessment`):
  * WRONG-REDUCTION / grounded-tag — APPLIES, is the sibling's headline probe
    and the exact prepatch bug: reduce by the per-component MAXIMUM instead of
    the total-degree SUM. Refutable at any vector whose max is below `minDeg`
    while its sum reaches it (`[2,1]` at `minDeg=3`) — the F2P discriminator.
    (S-wrong-max.)
  * PARTIAL-DOMAIN — APPLIES: a rival that omits the FIRST component's
    multiplicity from the total (`(p.drop 1).sum`), diverging from the fold
    whenever the first component carries decisive degree (`[1]` at `minDeg=1`).
    (S-drop-first.)
  * OFF-BY-ONE BOUNDARY — APPLIES: strict `<` instead of `≤`, correct on every
    input except the exact-equality boundary `sum == minDeg` — the heart of the
    F2P case (a candidate whose total degree equals the lower bound must be
    kept). (S-strict.)
  * FRAME-MUTATION — VACUOUS, and demonstrated rather than asserted. The
    sibling's mandatory frame-mutation rival writes to a read-only container
    held at a fractional heap permission. Here the analogous rival cannot be
    STATED: adding `candidates := candidates` to the impl region is rejected by
    velvet's own elaborator with "`candidates` cannot be mutated, only variables
    declared using `let mut` can be mutated" — a PARSE/elaboration error on the
    variant, not a spec rejection, so such a case could never attribute its
    outcome to C1 (it would land as a rejection for a reason the spec has no
    part in). There is no heap, no aliasing and no permission system to trip.
    Not fabricated (per the porting map, dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. C1 is grounded in
    `selectByDegree` (a fold over the actual inputs `candidates`/`minDeg`), not
    an opaque answer-key; the cheapest correct impl simply evaluates the fold,
    which the positive control covers honestly.
  * ADMISSIBILITY — APPLIES, and the earlier "N/A, no `require` clause" reading
    was wrong. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG is not a
    precondition that rejects a legal input; it is the OBLIGATION being
    unsatisfiable — or vacuously satisfiable — at exactly an F2P-shaped input.
    "The method has no precondition" does not address that, and the positive
    controls do not either: they discharge C1 for all inputs symbolically and
    never evaluate it anywhere, so a C1 that happened to be degenerate at the
    F2P point would still let them verify. S-admiss-f2p-eval closes this by
    EVALUATION at the concrete shape the report is about. (S-admiss-f2p-eval.)
  * DIVERGENCE / termination — APPLIES and is SHIPPABLE here, which the earlier
    port did not record at all. This bundle sets
    `loom.semantics.termination "total"`, so the verifier discharges a
    termination obligation and a loop carrying no decreasing measure is genuinely
    REJECTED rather than vacuously verified. Measured: deleting `i := i - 1` from
    the frozen loop body (leaving the `decreasing i` clause and every invariant
    in place) is rejected. It is NOT shipped as a reject CASE, and the reason is
    a witness limit rather than a disposition choice: the rival keeps the `while`
    loop, so its refutation witness cannot even elaborate — `failed to synthesize
    Decidable ¬{True}do … forIn Lean.Loop.mk [] fun x r => …` — the same gadget
    that blocks gold. A reject case whose witness cannot be built attributes
    nothing, so this is recorded as a KNOWN WITNESS-SIDE HOLE with the error
    text, not as a vacuous class and not as a silent omission.

WITNESS PLACEMENT / coverage. The single `ensures` clause C1 is attacked by FIVE
rivals at five DISTINCT input points varying BOTH binders. `candidates` ranges
over `[[2,1]]`, `[[1]]`, `[[2]]`, `[[3],[1]]`, `[[0],[2]]` and `minDeg` over
`3`, `1`, `2`, `2`, `1`. pts=5.

  The variation is meaningful in both directions, which is the property a bare
  point-count does not certify:
  * ERROR DIRECTION. S-wrong-max / S-drop-first / S-strict all wrongly DROP a
    candidate the fold keeps, so on their own they only ever witness that the
    kept set is not too SMALL. S-slack-bound and S-ignore-bound wrongly RETAIN,
    pinning the other inequality. A spec constraining just one side would have
    passed the original three and is caught by these.
  * LIST LENGTH. The original three are all refuted at a ONE-candidate list,
    where "which candidates survive" and "in what order they are returned"
    cannot come apart. The two added rivals are refuted at TWO-candidate lists.
  * BINDER ROLE. S-ignore-bound never consults `minDeg` at all, so it pins C1's
    dependence on that binder as such; the other four each compute some
    reduction of `p` and compare it to `minDeg`, so none of them does.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21847"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique in Solution.lean; both facts asserted at load by _swap) ------

# The whole loop-based impl body (text strictly between -- impl-start and
# -- impl-end). Replaced wholesale by the straight-line rivals, which abandon
# the loop entirely (the direct-triple witness needs a straight-line impl so
# `triple_pure` applies).
_IMPL = (
    "    let mut result : List (List Nat) := []\n"
    "    let mut i := candidates.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ candidates.length\n"
    "      invariant result = selectByDegree minDeg (candidates.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := candidates[i - 1]!\n"
    "      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The frozen tactic body. The positive controls abandon the loop, so they must
# also retune the proof: the frozen script's `rw [selectByDegree_drop_step …]`
# addresses a loop-body goal that no longer exists. Only the tactic body changes
# (`variant_scope` permits exactly that — the `prove_correct` header and the
# `ensures` statement stay byte-identical), so a positive control still reproves
# the SAME obligation.
_PROOF = (
    "prove_correct selectMonomials by\n"
    "  loom_solve\n"
    "  rw [selectByDegree_drop_step minDeg candidates i (by omega) (by omega)]\n"
    "  simp_all"
)

# `List.filter`-shaped correct impl: a FORWARD one-pass filter replacing the
# backward accumulate-and-prepend loop. Not definitionally equal to the frozen
# impl — `loom_solve` leaves the goal
#   `List.filter (fun p => decide (minDeg ≤ p.sum)) candidates
#      = selectByDegree minDeg candidates`
# (measured), which needs a genuine induction over `candidates` matching
# `List.filter_cons` against `selectByDegree_cons` clause by clause. That is the
# real content of C1, reproven for a new impl shape rather than restated.
_FILTER_IMPL = "    return candidates.filter (fun p => decide (minDeg ≤ p.sum))\n"
_FILTER_PROOF = (
    "prove_correct selectMonomials by\n"
    "  loom_solve\n"
    "  induction candidates with\n"
    "  | nil => rfl\n"
    "  | cons p ps ih =>\n"
    "    rw [selectByDegree_cons, List.filter_cons]\n"
    "    by_cases h : minDeg ≤ totalDegree p\n"
    "    · simp only [totalDegree] at h ⊢\n"
    "      simp [h, ih]\n"
    "    · simp only [totalDegree] at h ⊢\n"
    "      simp [h, ih]\n"
)

# `foldr`-shaped correct impl: the same keep decision expressed as a right fold
# building the kept list directly, so the accumulator is threaded by `foldr`
# rather than by a mutable loop variable.
_FOLDR_IMPL = ("    return candidates.foldr "
               "(fun p acc => (if minDeg ≤ p.sum then [p] else []) ++ acc) []\n")
_FOLDR_PROOF = (
    "prove_correct selectMonomials by\n"
    "  loom_solve\n"
    "  induction candidates with\n"
    "  | nil => rfl\n"
    "  | cons p ps ih => simp [selectByDegree_cons, ih, totalDegree]\n"
)


# ---- witness helper. The spec is a `method` CONTRACT with a computable but
# ---- loop-shaped impl, so a witness reaches it NOT through the tester
# ---- machinery (which cannot `decide` through the extracted loop) but by
# ---- refuting the method's Hoare triple directly at a concrete LITERAL input.
# ---- Checked in a file whose `prove_correct` block has been stripped.
def _witness(cands_lit, min_lit):
    return (
        f"example : ¬ (triple (l := Prop) True (selectMonomials {cands_lit} {min_lit})\n"
        f"    (fun out => out = selectByDegree {min_lit} {cands_lit})) := by\n"
        f"  unfold selectMonomials\n"
        f"  simp only [triple_pure, le_Prop_eq, true_implies]\n"
        f"  decide\n"
    )


# ---- WITNESS SUBJECT (audit repair). The frozen impl's `while` compiles to a
# ---- `partial_fixpoint` loop the kernel cannot unfold, so a `decide` against
# ---- GOLD is stuck for EVERY claim: the forgery that drops the `¬` (asserting
# ---- gold is CORRECT at the same input) fails with the same
# ---- `failed to synthesize Decidable … forIn Lean.Loop.mk` error. Gold's exit
# ---- code therefore attests to nothing, so each reject case names this
# ---- VERIFYING straight-line impl of the SAME spec as the subject to be
# ---- refuted against instead. The gate re-checks it (same frozen spec + it
# ---- must verify) before trusting it; against it `decide` genuinely reduces,
# ---- the five witnesses fail semantically, and the forgery ELABORATES — the
# ---- exit code tracks the claim. This is the same impl as
# ---- S-pos-forward-filter, which is independently required to verify.
_WITNESS_REF = _swap(_swap(_BASE, _IMPL, _FILTER_IMPL), _PROOF, _FILTER_PROOF)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the spec is SPEC-TOO-STRONG. The intermediate
    # `let p := candidates[i-1]!` binding is inlined into the prepend: the
    # accumulated `result` is DEFINITIONALLY identical, so `loom_solve` leaves
    # the same single loop-body goal and the frozen tactic script
    # (`rw [selectByDegree_drop_step …]; simp_all`) discharges it unchanged. No
    # new lemma is introduced and the obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "S-pos-forward-filter",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL, _FILTER_IMPL), _PROOF, _FILTER_PROOF),
        "rationale": "A FORWARD one-pass `List.filter` replacing the backward "
                     "accumulate-and-prepend loop. This is not a definitional "
                     "reshuffle: the loop is gone, so `loom_solve` leaves the "
                     "goal `List.filter (fun p => decide (minDeg ≤ p.sum)) "
                     "candidates = selectByDegree minDeg candidates`, which is "
                     "discharged by a fresh induction on `candidates` matching "
                     "`List.filter_cons` against `selectByDegree_cons` on both "
                     "branches of the keep decision — C1 REPROVEN for a new impl "
                     "shape, not restated. The obligation statement and the "
                     "`prove_correct` header are byte-identical; only the tactic "
                     "body differs, which is what `variant_scope` permits. A "
                     "correct reshape the spec REJECTED would mean C1 is "
                     "SPEC-TOO-STRONG: pinned to the frozen impl's traversal "
                     "order rather than to the filter it is supposed to denote.",
    },
    {
        "id": "S-pos-foldr",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL, _FOLDR_IMPL), _PROOF, _FOLDR_PROOF),
        "rationale": "A second, independent correct shape: the keep decision as "
                     "an explicit right fold that threads the kept list through "
                     "`foldr` instead of through a mutable loop variable. It "
                     "verifies via its own induction, so C1 admits at least two "
                     "structurally distinct faithful impls beyond the frozen "
                     "loop. Guards the same SPEC-TOO-STRONG direction as "
                     "S-pos-forward-filter at a different traversal shape, so a "
                     "spec that happened to accommodate `List.filter` alone "
                     "(e.g. by being stated in filter-specific terms) would "
                     "still be caught here.",
    },

    # =====================================================================
    # ADMISSIBILITY (added by the second audit). The first port recorded this
    # lane as N/A "because the method carries no `require` clause". That reason
    # is wrong on a TOTAL carrier: the analogue of PRECOND-TOO-STRONG here is the
    # obligation being unsatisfiable — or degenerate — at exactly an F2P-shaped
    # input, which the absence of a precondition does not address and which the
    # soundness positives do not test either (they discharge C1 symbolically for
    # ALL inputs and never evaluate it anywhere). This case discharges C1's own
    # postcondition BY EVALUATION at the concrete input shape the report is
    # about, as `have`s, and only then closes the frozen obligation VERBATIM —
    # frozen impl untouched, frozen tactic script untouched. So it verifies iff
    # the obligation is genuinely satisfiable, and non-degenerately, right there.
    # =====================================================================
    {
        "id": "S-admiss-f2p-eval",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct selectMonomials by\n"
            "  -- C1 is satisfiable, and non-degenerate, at an F2P-shaped input:\n"
            "  -- three generators, lower bound equal to the requested total\n"
            "  -- degree. The MIXED candidates (whose components sum to the bound\n"
            "  -- without any single component reaching it) are RETAINED alongside\n"
            "  -- the pure powers, in enumeration order.\n"
            "  have hadm_mixed : selectByDegree 3 [[3,0,0],[2,1,0],[1,1,1],[0,0,2]]\n"
            "      = [[3,0,0],[2,1,0],[1,1,1]] := by decide\n"
            "  -- and the bound is not vacuously met: a candidate below it is\n"
            "  -- dropped, so C1 is not satisfied by simply returning the input.\n"
            "  have hadm_drop : selectByDegree 3 [[0,0,2]] = [] := by decide\n"
            "  -- degenerate-shape check: the empty candidate list is admissible.\n"
            "  have hadm_nil : selectByDegree 3 [] = [] := by decide\n"
            "  loom_solve\n"
            "  rw [selectByDegree_drop_step minDeg candidates i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "ADMISSIBILITY, the lane the first port dropped. The frozen "
                     "impl and the frozen tactic script are both byte-identical "
                     "here; the only addition is three `have`s that EVALUATE C1's "
                     "postcondition at concrete literal inputs before the frozen "
                     "obligation is closed verbatim. That is the total-carrier "
                     "analogue of PRECOND-TOO-STRONG: it fails if the obligation "
                     "is unsatisfiable at an F2P-shaped input, and it pins "
                     "non-degeneracy too. `hadm_mixed` is the F2P shape itself — "
                     "three generators at lower bound 3, where the candidates "
                     "whose components SUM to the bound while no single component "
                     "reaches it ([2,1,0], [1,1,1]) must survive next to the pure "
                     "power [3,0,0], and [0,0,2] must not; a C1 that admitted only "
                     "the pure powers would make this `decide` fail. `hadm_drop` "
                     "rules out C1 being satisfiable by returning the input "
                     "unchanged, and `hadm_nil` covers the empty list. The other "
                     "two positives cannot substitute: they discharge C1 "
                     "symbolically for ALL inputs and never evaluate it at any "
                     "point, so a C1 degenerate at exactly this input would still "
                     "let both of them verify.",
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete
    # literal input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "S-wrong-max",
        "kind": "uniqueness",
        "expect": "reject",
        # THE prepatch bug: keep a candidate when the lower bound is met by its
        # per-component MAXIMUM rather than by its total degree (sum). Straight
        # line so `triple_pure` applies in the witness.
        "module": _swap(
            _BASE, _IMPL,
            "    return candidates.filter (fun p => decide (minDeg ≤ p.foldr max 0))\n"),
        "refinement": "Reducing by the largest single component instead of the "
                      "total degree is exactly the prepatch behaviour. On the "
                      "F2P discriminator a candidate whose components sum to the "
                      "requested total degree but whose largest single component "
                      "falls short (e.g. multiplicity vector [2,1], total 3, max "
                      "2, at lower bound 3) is dropped by the max rule and kept "
                      "by the sum rule. The produced set then omits the mixed "
                      "monomials the documented behaviour requires, so the "
                      "failing test asserting the full total-degree set FAILS — "
                      "this is precisely the reported bug, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 (`out = selectByDegree minDeg candidates`): "
                     "`selectByDegree` keeps a candidate iff `minDeg ≤ p.sum`, so "
                     "on any vector whose max < minDeg ≤ sum the max rule and the "
                     "sum rule disagree. Verifying would be SPEC-TOO-WEAK on the "
                     "reduction. Refuted at `candidates=[[2,1]]`, `minDeg=3` "
                     "(sum 3 ≥ 3 kept by gold, max 2 < 3 dropped by the rival).",
        "witness": _witness("[[2,1]]", "3"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "S-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the first component's multiplicity from the total degree
        # (`(p.drop 1).sum`). Correct whenever the first component is 0 or
        # irrelevant; wrong whenever the first component carries decisive degree.
        "module": _swap(
            _BASE, _IMPL,
            "    return candidates.filter (fun p => decide (minDeg ≤ (p.drop 1).sum))\n"),
        "refinement": "Summing all but the first component omits one variable's "
                      "multiplicity from the total degree. A faithful real "
                      "counterpart that dropped the first component's exponent "
                      "from the degree test would misclassify any candidate whose "
                      "first variable carries the decisive degree (e.g. a "
                      "single-variable candidate of full degree), producing a set "
                      "missing those monomials, so the failing test FAILS. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C1: the rival's kept-set is driven by the total "
                     "degree MINUS the first component, not the full sum "
                     "`selectByDegree` demands, so it disagrees whenever the "
                     "first component changes the comparison. Verifying would be "
                     "SPEC-TOO-WEAK on the total-degree sum. Refuted at "
                     "`candidates=[[1]]`, `minDeg=1` (sum 1 ≥ 1 kept by gold; "
                     "dropping the first component gives sum 0 < 1, dropped by "
                     "the rival) — a single-component sub-domain the other rivals "
                     "do not probe.",
        "witness": _witness("[[1]]", "1"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "S-strict",
        "kind": "uniqueness",
        "expect": "reject",
        # Strict `<` instead of `≤`: drops exactly the exact-equality boundary
        # `sum == minDeg`. Correct everywhere else.
        "module": _swap(
            _BASE, _IMPL,
            "    return candidates.filter (fun p => decide (minDeg < p.sum))\n"),
        "refinement": "A strict comparison corresponds to the off-by-one lower "
                      "bound: a candidate whose total degree exactly equals the "
                      "lower bound is dropped. That boundary is the heart of the "
                      "F2P case — candidates whose total degree equals the "
                      "requested minimum must be retained — so every such "
                      "candidate would vanish from the produced set and the "
                      "failing test FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1: `selectByDegree` keeps iff `minDeg ≤ p.sum`, "
                     "which a strict `<` violates exactly when `p.sum == minDeg`. "
                     "Verifying would be SPEC-TOO-WEAK on the boundary. Refuted "
                     "at `candidates=[[2]]`, `minDeg=2` (sum 2 ≥ 2 kept by gold; "
                     "2 < 2 false, dropped by the rival) — the exact-equality "
                     "boundary no other rival probes.",
        "witness": _witness("[[2]]", "2"),
        "witness_reference": _WITNESS_REF,
    },
    # -- added by audit. Every rival above errs in ONE direction only: each
    # -- wrongly DROPS a candidate the fold keeps, and each is refuted at a
    # -- single-candidate list. So C1 was never probed against an impl that
    # -- wrongly RETAINS, nor at a list where the two clauses of C1 (which
    # -- candidates survive, and in what order they are returned) could come
    # -- apart. These two close both gaps.
    {
        "id": "S-slack-bound",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one in the OPPOSITE direction to S-strict: `minDeg ≤ p.sum + 1`
        # admits every candidate one short of the lower bound.
        "module": _swap(
            _BASE, _IMPL,
            "    return candidates.filter (fun p => decide (minDeg ≤ p.sum + 1))\n"),
        "refinement": "A lower bound loosened by one retains candidates whose "
                      "total degree falls one short of the requested minimum. "
                      "The produced set is then a strict SUPERSET of the "
                      "documented one, carrying terms below the requested total "
                      "degree, so the failing test — which pins the produced set "
                      "exactly — FAILS on the extra terms. It would NOT resolve.",
        "rationale": "REJECT from C1: `selectByDegree` keeps iff `minDeg ≤ "
                     "p.sum`, so admitting `p.sum + 1 ≥ minDeg` disagrees exactly "
                     "when `p.sum + 1 = minDeg`. Refuted at "
                     "`candidates=[[3],[1]]`, `minDeg=2`: gold keeps only `[3]`, "
                     "the rival also keeps `[1]` (sum 1, one short). This is the "
                     "only rival that errs by wrongly RETAINING — the three "
                     "originals all wrongly DROP, so a spec pinning only a lower "
                     "bound on the kept set would have passed them all. It is "
                     "also refuted at a TWO-candidate list, where C1's kept-set "
                     "and order clauses can come apart.",
        "witness": _witness("[[3],[1]]", "2"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "S-ignore-bound",
        "kind": "uniqueness",
        "expect": "reject",
        # The threshold is ignored outright: every enumerated candidate is kept.
        "module": _swap(_BASE, _IMPL, "    return candidates\n"),
        "refinement": "Ignoring the lower bound returns every enumerated "
                      "candidate, including the degree-0 constant and every "
                      "term below the requested minimum. This is the behaviour "
                      "of omitting the retention test altogether; the produced "
                      "set is then the full enumeration rather than the "
                      "documented total-degree-bounded one, so the failing test "
                      "FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1: an impl that never consults `minDeg` "
                     "cannot equal `selectByDegree minDeg candidates` whenever "
                     "any candidate falls below the bound. Refuted at "
                     "`candidates=[[0],[2]]`, `minDeg=1` (gold keeps only `[2]`; "
                     "the rival also keeps `[0]`). This pins C1's DEPENDENCE on "
                     "the `minDeg` binder itself: the three original rivals all "
                     "compute some reduction of `p` and compare it to `minDeg`, "
                     "so none of them would catch a spec that failed to "
                     "constrain the bound's role at all.",
        "witness": _witness("[[0],[2]]", "1"),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness rivals split comm/noncomm) plus
# AXIOM_TESTS=[]. This bundle models only the purely-functional core — a single
# method `selectMonomials` (the sibling's two byte-identical hunks `keep_comm`
# and `keep_noncomm` collapse to ONE method here, since the R-postprocess that
# distinguishes them, `Mul`/`set`, is not modeled). Every sibling case is
# accounted for below.
#
#   sibling case              -> here
#   -------------------------------------------------------------------------
#   pos-control-reshape-comm  -> S-pos-forward-filter    PORTED (+ S-pos-foldr
#                                                         added by audit)
#   admiss-comm-selfcall      -> S-admiss-f2p-eval       PORTED by 2nd audit
#                                                         (was wrongly N/A)
#   frame-mut-comm            -> (none)                  VACUOUS
#   frame-mut-noncomm         -> (none)                  VACUOUS
#   wrong-max-comm            -> S-wrong-max             PORTED (comm+noncomm
#   wrong-max-noncomm         -> S-wrong-max               merged: one method)
#   partial-first-comm        -> S-drop-first            PORTED
#   strict-boundary-comm      -> S-strict                PORTED
#   AXIOM_TESTS               -> (none)                  G-AX's job; dropped
#
# 3 rivals + 1 positive ported (comm/noncomm merged into single rivals), 2
# vacuous; the first audit ADDED 2 rivals (S-slack-bound, S-ignore-bound) and 1
# positive (S-pos-foldr); the SECOND audit added the admissibility positive
# (S-admiss-f2p-eval) after finding the "N/A: no precondition" reason invalid on
# a total carrier. No case was dropped because its proof/witness was hard; each
# drop is a carrier limit stated with reason.
#
# VACUOUS (frame-mut-comm, frame-mut-noncomm): the sibling writes to a read-only
#   container carrying a fractional heap permission and is rejected for
#   INSUFFICIENT PERMISSION. Here the analogous variant is not merely pointless
#   but UNSTATABLE, which the audit confirmed by building it: an impl-region
#   `candidates := candidates` is rejected by velvet's elaborator with
#   "`candidates` cannot be mutated, only variables declared using `let mut` can
#   be mutated". That is an elaboration error on the variant, so the case could
#   never attribute its rejection to C1. There is no heap, no aliasing and no
#   permission system to trip. No substitute fabricated.
# PORTED (admiss-comm-selfcall) -> S-admiss-f2p-eval. The first port recorded
#   this lane N/A because "the method carries NO `require` clause, so there is no
#   precondition to be too strong". The second audit rejected that reason: the
#   absence of a precondition is exactly the reason given in the audit brief as
#   NOT sufficient. On a total carrier the analogue of PRECOND-TOO-STRONG is the
#   obligation being unsatisfiable, or degenerate, at an F2P-shaped input, and a
#   positive that discharges the obligation AT that concrete input by evaluation
#   — as `have`s, before closing the frozen obligation verbatim — tests it
#   directly. The claim that the soundness positives already cover this residual
#   risk was also false: both of them discharge C1 symbolically for ALL inputs
#   via induction and never EVALUATE it at any point, so a C1 degenerate at the
#   F2P shape would leave both verifying. S-admiss-f2p-eval evaluates it.
#   The sibling's fresh-probe self-call idiom itself does not port (it dodges a
#   Nagini framing limitation with no counterpart here), but the LANE does, which
#   is what the port had conflated.
# COMM/NONCOMM MERGE: the sibling's two hunks (`keep_comm`, `keep_noncomm`) are
#   byte-identical spec+impl differing only in name; here they abstract to the
#   single method `selectMonomials` (the enumerator that distinguishes the two
#   legs and the `Mul`/`set` postprocess are folded into the free `candidates`
#   input per mapping.md §3). So each sibling comm/noncomm pair collapses to one
#   rival — carrier narrowing, not an omission.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle has no axiom
#   (the changed reduction is modeled deeply as `totalDegree`/`selectByDegree`),
#   and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause C1
#   (`out = selectByDegree minDeg candidates`) is attacked by all FIVE rivals
#   across five distinct sub-domains — the reduction (max vs sum), the
#   omitted-first-component partial domain, the exact-equality boundary, the
#   loosened bound one step the other side of that boundary, and the bound
#   ignored entirely — refuted at five DISTINCT input points (pts=5). Binder
#   `candidates` is varied across `[[2,1]]`, `[[1]]`, `[[2]]`, `[[3],[1]]`,
#   `[[0],[2]]`; binder `minDeg` across `3`, `1`, `2`, `2`, `1`. Both error
#   directions are covered (three rivals wrongly drop, two wrongly retain) and
#   two rivals sit at multi-candidate lists. C1 is defended in the
#   SPEC-TOO-STRONG direction by TWO independent correct reshapes,
#   S-pos-forward-filter (forward `List.filter`) and S-pos-foldr (right fold),
#   each of which abandons the frozen loop and reproves C1 by its own induction.
#   Both are load-bearing rather than definitional reshuffles, which the second
#   audit MEASURED rather than assumed: each positive's impl was built against
#   the FROZEN tactic script, and both FAIL there (exit 1, `rw` addresses a
#   loop-body goal that no longer exists / unsolved goals). So each really does
#   need its own induction, and neither is definitionally equal to gold.
#   The ADMISSIBILITY direction is covered by S-admiss-f2p-eval, which evaluates
#   C1 at a three-generator F2P-shaped input rather than reasoning symbolically.
#
# SECOND-AUDIT PROBES (attacks D and E), all built; none produced a spec hole.
#   D (SPEC-TOO-WEAK — new wrong impls the battery did not contain, aimed away
#   from the existing rivals): kept list REVERSED (order clause), kept list
#   DUPLICATED (`++` with itself — multiplicity, an axis no shipped rival
#   attacks), `p.length` substituted for `p.sum` (wrong reduction of a different
#   kind), `eraseDups` on the kept list, and a LENGTH-CONDITIONED impl that
#   filters correctly only when `candidates.length ≤ 2` and returns everything
#   otherwise (a partial-domain hole that all five point-witnesses at 1-2 element
#   lists would individually miss). All five were correctly REJECTED, so C1 is
#   not too weak on order, multiplicity, reduction shape, or list length.
#   E (SPEC-TOO-STRONG — new correct reshapes): a `foldl`-based total-degree test
#   (`p.foldl (·+·) 0`, the opposite fold direction to `p.sum`'s `foldr`) VERIFIES,
#   and a doubly-negated boundary test (`!decide (p.sum < minDeg)`, which reaches
#   the same keep decision through `Nat.not_lt` rather than through `≤`) VERIFIES.
#   So C1 is not pinned to a traversal direction or to the spelling of the
#   comparison. Four faithful correct shapes verify in total; no correct reshape
#   was found that C1 rejects.
#
# AUDIT PROBES that produced no case (recorded so the next reader does not repeat
#   them). Five further wrong impls were built and all were correctly REJECTED,
#   so no SPEC-TOO-WEAK hole was found: kept-list reversed, kept list deduped via
#   `eraseDups`, comparison flipped to `p.sum ≤ minDeg`, `p.length` substituted
#   for `p.sum`, and the bound ignored (the last became S-ignore-bound). The
#   reversal and dedup rivals were deliberately NOT kept as cases: both are wrong
#   against C1, but their faithful real counterparts would still resolve the
#   failing test, because the real code applies `set(...)` to the kept list — so
#   an honest `refinement` (which must argue the counterpart would NOT resolve)
#   cannot be written for them. They are genuine C1 violations that are not
#   genuine BUG rivals, and shipping them would have attested strength the
#   consumer contract does not actually claim on that axis.
AXIOM_TESTS = []
