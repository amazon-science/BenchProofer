"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-11578 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over a two-point mode domain:

  probabilityMethodForScoring (requested : MultiClass) return (out : ProbaMethod)
      ensures (requested = MultiClass.multinomial → out = ProbaMethod.softmax)
      ensures (requested = MultiClass.ovr        → out = ProbaMethod.ovrNormalize)

``MultiClass`` is the requested multiclass mode (``ovr`` | ``multinomial``);
``ProbaMethod`` is the probability-estimation method a scored estimator applies
(``ovrNormalize`` the per-class-logistic-then-normalize estimate |
``softmax`` the cross-class estimate). The one input binder ``requested`` is a
FREE, read-only value and there is no ``require`` clause, so the admitted domain
is total: the guarantee must hold for BOTH modes.

The postcondition is two INDEPENDENT top-level clauses, one per mode, each
pinning the probability method that scores a fold to the one that MATCHES the
requested mode. The load-bearing subtlety the change corrects: the scored
estimator must operate in the REQUESTED mode, so its probability method is a
function of ``requested`` — NOT a mode-agnostic constant, and NOT the opposite
mode. The two methods yield different probabilities on a multiclass problem, so
a probabilistic score reads the wrong values whenever the method does not match.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini
    because an input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: ``requested`` is
    an immutable value (not a ``mut`` binder), there is no heap and no aliasing,
    so there is no read-only input to mutate and no substitute probe to build.
    Reported as vacuous, not fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The guarantee is a total function of the
    method's own argument stated by two concrete equalities; the ``axioms``
    region declares nothing, so there is no opaque answer key to echo. Covered
    instead by honest cheapest-reshape POSITIVE CONTROLS (``pos-*``).
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals right on part of the mode domain
    but diverging on a sub-domain (pin the wrong constant method; invert the
    mode→method mapping). Each is refuted at a concrete mode that varies the one
    input binder across BOTH of its values, so the binder is not pinned across
    the battery and each independent clause is attacked.
  * CONTROL-FLOW-EFFECT — N/A. This is a pure value computation; the modeled
    result IS the observable. Omitted.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the unchanged
probability routine is modeled DEEPLY in ``pure`` as an A-reference validated ==
the real callee by G-AX, not consumed here). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-11578"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region (everything the variants replace). It is a single
# ---- contiguous block wholly inside the one `-- impl-start` / `-- impl-end`
# ---- region and unique in Solution.lean; both facts are asserted at load by
# ---- _swap. ----------------------------------------------------------------
_GOLD_IMPL = (
    "    let out : ProbaMethod := match requested with\n"
    "      | .ovr         => ProbaMethod.ovrNormalize\n"
    "      | .multinomial => ProbaMethod.softmax\n"
    "    return out"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# The frozen proof body (the `prove_correct` tactic script). Elided from the
# consumer spec view, so a variant that adds an in-region `assert` (raising an
# extra side goal `loom_solve` leaves open) may retune it — the obligation
# STATEMENT and the `prove_correct` header are untouched, so same_spec holds.
_GOLD_PROOF = "prove_correct probabilityMethodForScoring by\n  loom_solve"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `probabilityMethodForScoringTester requested = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- mode. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. `MultiClass`/`ProbaMethod` derive
# ---- DecidableEq, so the postcondition is decidable and every witness closes
# ---- by `decide`.
def _tester(pre=""):
    m = "probabilityMethodForScoring"
    return (f"{pre}extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


def _witness(mode):
    m = "probabilityMethodForScoring"
    return (_tester()
            + f"example : {m}Tester MultiClass.{mode} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify; else the guarantee is SPEC-TOO-STRONG. Each preserves
    # the obligation and reshapes only the executable surface; the contract is
    # two point-wise equalities over an immutable enum, so no induction is
    # needed and the frozen `loom_solve` still discharges it.
    # =====================================================================
    {
        "id": "pos-inline-if",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: dispatch with a pure conditional on the requested mode
        # instead of a `match`. Returns the identical method on both modes
        # (ovrNormalize for ovr, softmax otherwise), so both equality clauses
        # still discharge under the frozen proof.
        "module": _impl(
            "    let out : ProbaMethod :=\n"
            "      if requested = MultiClass.ovr then ProbaMethod.ovrNormalize\n"
            "      else ProbaMethod.softmax\n"
            "    return out"),
        "rationale": "a correct reshape (pure if-then-else on the requested mode "
        "instead of a match) computes the identical `out` on both modes and adds "
        "no new proof obligation, so the two equality clauses still discharge "
        "under the frozen `loom_solve`; else SPEC-TOO-STRONG on impl shape.",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: same `match`, arms written in the opposite order (the
        # directive-preferred structural reshape). Observationally identical:
        # ovrNormalize for ovr, softmax for multinomial.
        "module": _impl(
            "    let out : ProbaMethod := match requested with\n"
            "      | .multinomial => ProbaMethod.softmax\n"
            "      | .ovr         => ProbaMethod.ovrNormalize\n"
            "    return out"),
        "rationale": "correct reshape: the gold dispatch with the two match arms "
        "reordered (multinomial first). Equals the frozen mapping on both modes, "
        "so both equality clauses discharge under the frozen `loom_solve`; else "
        "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous. Re-aimed at the residual
    # admissibility risk on a total domain: that the guarantee is degenerate /
    # unsatisfiable at the decisive point. This case discharges an in-region
    # `assert` pinning the F2P consequence at the multinomial mode — the scored
    # method there is softmax AND softmax is genuinely NOT the one-vs-rest
    # estimate (the two methods differ, which is why a probabilistic score
    # discriminates the modes). The impl is kept verbatim so the method's own
    # obligation still discharges; the assert is live, not decoration: a false
    # claim about the same point leaves an unsolved goal (verified out-of-band).
    # =====================================================================
    {
        "id": "admiss-f2p-multinomial-softmax",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      ((match MultiClass.multinomial with\n"
            "        | .ovr         => ProbaMethod.ovrNormalize\n"
            "        | .multinomial => ProbaMethod.softmax) = ProbaMethod.softmax\n"
            "       ∧ ProbaMethod.softmax ≠ ProbaMethod.ovrNormalize))\n"
            + _GOLD_IMPL,
            _GOLD_PROOF),
        "rationale": "the guarantee is satisfiable AND non-degenerate at the F2P "
        "corner: a multinomial request is scored with softmax, and softmax is "
        "genuinely distinct from the one-vs-rest estimate (so the multinomial "
        "request is NOT scored with the ovr method — the derived discriminating "
        "consequence). The in-region assert must discharge (else the obligation "
        "is unsatisfiable/PRECOND-TOO-STRONG); the impl is verbatim so both "
        "equality clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete mode and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary the one
    # binder `requested` over BOTH values (multinomial and ovr).
    # =====================================================================
    {
        "id": "weak-always-ovr",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug. The scored estimator's mode is pinned to the
        # mode-agnostic default (ovr) regardless of the request, so a
        # multinomial request is scored with the one-vs-rest estimate. Correct
        # on the ovr request, WRONG on the multinomial one.
        "module": _impl(
            "    let out : ProbaMethod := ProbaMethod.ovrNormalize\n"
            "    return out"),
        "refinement": "this is the pre-fix behavior: the scoring estimator is "
        "constructed without threading the requested mode, so it takes the "
        "class default (one-vs-rest) irrespective of the request. A probabilistic "
        "scorer then reads the one-vs-rest probabilities for a multinomial "
        "request, so the FAIL_TO_PASS neg_log_loss multiclass case still observes "
        "the wrong score and still fails. It would NOT resolve.",
        "rationale": "REJECT from the multinomial clause "
        "`requested = multinomial → out = softmax`: at multinomial the impl "
        "returns ovrNormalize where softmax is required. Refuted at "
        "`requested = multinomial` (where the ovr request clause is vacuously "
        "satisfied, so the rejection is attributable to the multinomial clause).",
        "witness": _witness("multinomial"),
    },
    {
        "id": "weak-always-multinomial",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain dual: pin the method to softmax regardless of the
        # request. Correct on the multinomial request, WRONG on the ovr one
        # (returns softmax where the one-vs-rest estimate is required).
        "module": _impl(
            "    let out : ProbaMethod := ProbaMethod.softmax\n"
            "    return out"),
        "refinement": "a counterpart that pins the scoring estimator to the "
        "multinomial mode regardless of the request scores an ovr request with "
        "softmax. The existing tests that exercise the one-vs-rest scoring path "
        "read the wrong (softmax) probabilities and still fail. It would NOT "
        "resolve on the ovr sub-domain.",
        "rationale": "REJECT from the ovr clause "
        "`requested = ovr → out = ovrNormalize`: at ovr the impl returns softmax "
        "where ovrNormalize is required. Refuted at `requested = ovr` — the "
        "sub-domain complementary to weak-always-ovr's, so the two constant "
        "rivals probe both binder values and both independent clauses.",
        "witness": _witness("ovr"),
    },
    {
        "id": "weak-mode-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the mapping: a multinomial request gets the one-vs-rest
        # estimate and an ovr request gets softmax. Wrong on BOTH modes — the
        # only rival that violates both clauses. Distinct impl from either
        # constant rival (not a mode-agnostic constant, but a swap).
        "module": _impl(
            "    let out : ProbaMethod := match requested with\n"
            "      | .ovr         => ProbaMethod.softmax\n"
            "      | .multinomial => ProbaMethod.ovrNormalize\n"
            "    return out"),
        "refinement": "a counterpart that threads the OPPOSITE mode into the "
        "scoring estimator feeds one-vs-rest probabilities to a multinomial "
        "request (and softmax to an ovr request). The neg_log_loss multinomial "
        "F2P case reads the wrong (one-vs-rest) vector and still fails. It would "
        "NOT resolve.",
        "rationale": "REJECT: violates BOTH clauses. Witnessed at "
        "`requested = multinomial`, where it returns ovrNormalize but the "
        "multinomial clause demands softmax — the same F2P direction as "
        "weak-always-ovr. On this two-point mode carrier the domain has only two "
        "inputs, so its witness necessarily coincides in mode with a constant "
        "rival; it is genuinely distinct as an IMPL (a mode inversion, wrong on "
        "both modes, not a constant) — see the footer's witness-distinctness note.",
        "witness": _witness("multinomial"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives, 1 admissibility, 3 uniqueness rivals) plus 2 AXIOM_TESTS. The
# sibling contracts `scoring_estimator_proba(caller_mode: int, d: PSeq[int])`
# over a mode tag AND a decision row `d`, with a @Pure selector `scoring_proba`
# unfolding to `proba_softmax(d)` / `proba_ovr(d)`. This bundle models only the
# purely functional CORE the fix turns on — the mode→probability-method
# selection — collapsing the opaque decision row `d` and the opaque transforms
# to the observable `ProbaMethod` identity (`proba_softmax` <-> `.softmax`,
# `proba_ovr` <-> `.ovrNormalize`). So the sibling's `caller_mode` is
# `requested`, and its P1..P4 clauses over `d` become the two mode clauses here.
#
#   sibling case                 -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-inline-branch            -> pos-inline-if                  PORTED
#   pos-branch-reorder           -> pos-branch-reorder             PORTED
#   admiss-precond-nonvacuous    -> admiss-f2p-multinomial-softmax RE-AIMED
#   weak-prepatch-ovr            -> weak-always-ovr                PORTED
#   weak-mode-flip               -> weak-mode-flip                 PORTED
#   weak-always-multinomial      -> weak-always-multinomial        PORTED
#   (frame-mutation)             -> (none)                         VACUOUS
#   AXIOM_TESTS (x2)             -> (none)                         DROPPED (G-AX)
#
# 5 ported, 1 re-aimed = 6 SPEC cases. Full parity with the sibling's SPEC lane
# because the sibling's clauses all live on the mode selection this bundle
# models; the decision-row binder `d` collapses under the carrier abstraction
# (the transforms differ as OPAQUE FUNCTIONS — captured by ProbaMethod identity
# and the admissibility case's `softmax ≠ ovrNormalize` fact — so no per-`d`
# rival survives; a rival differing only in `d`-handling has nothing to abuse
# here). No rival was dropped for being hard to prove.
#
# RE-AIMED (admissibility): the sibling Asserts the precondition (R1 mode in
#   domain, R2 transforms_differ) is establishable for an F2P input. There is no
#   `require` clause here, so that reading is vacuous; the case is re-aimed at
#   proving the guarantee is satisfiable and NON-degenerate at the F2P corner
#   (multinomial request -> softmax, AND softmax genuinely != the one-vs-rest
#   estimate — the sibling's P4 discriminating consequence, carried over as a
#   live in-region assert discharged by `loom_solve`).
# FRAME-MUTATION: VACUOUS. This backend is referentially transparent, has no
#   heap/aliasing, and declares NO `mut` binder — there is no read-only input to
#   overwrite and no substitute probe to build. No case fabricated.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores them.
#   (The one probability routine is an A-reference deep model validated ==
#   the real callee by axiom_check.py, carrying no module-level `axiom`.)
#
# BINDER / POINT COVERAGE. The three reject witnesses probe both mode values:
#   weak-always-ovr           requested = multinomial   (multinomial clause)
#   weak-always-multinomial   requested = ovr           (ovr clause)
#   weak-mode-flip            requested = multinomial   (multinomial clause)
#   The sole input binder `requested` is varied over BOTH of its values, so it
#   is not pinned across the battery; both INDEPENDENT top-level clauses are
#   attacked (multinomial by weak-always-ovr/weak-mode-flip, ovr by
#   weak-always-multinomial) and defended by the two positive controls and the
#   admissibility case. pts = 2 is the MAXIMUM attainable — the modeled domain
#   `MultiClass` has exactly two inhabitants.
#
# WITNESS DISTINCTNESS. weak-mode-flip and weak-always-ovr share the witness
#   input `requested = multinomial` (both return ovrNormalize where softmax is
#   required — they fail at the same input FOR THE SAME REASON, which the rule
#   permits). They are distinct as impls: weak-always-ovr is correct on the ovr
#   request (a mode-agnostic constant), whereas weak-mode-flip is ALSO wrong on
#   the ovr request (an inversion). On a two-inhabitant domain there is no third
#   input at which to separate them, so the flip's "wrong on both modes"
#   character is documented rather than witnessed at a distinct point. Neither
#   is a near-miss agreeing with gold over MORE of the domain than the other
#   (weak-mode-flip agrees with gold NOWHERE), so the near-miss "move to a
#   distinguishing input" rule does not apply.
AXIOM_TESTS = []
