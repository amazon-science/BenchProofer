"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14087 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside ``-- impl-start`` /
``-- impl-end``, or inside the ``prove_correct`` tactic body, is changed — both
regions the consumer spec view elides, so ``markers.same_spec`` holds by
construction and the ``prove_correct recordClassResult`` header survives), and
swaps in a candidate implementation. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness ELABORATES against the rival
and FAILS against the frozen solution).

DEFENDED SURFACE — ONE contracted method over a decidable value carrier:

  recordClassResult (perClassEffective perClassRequested : Bool)
                    (coefByPerClass coefByJoint : Coef)      -- Coef = List Rat
                    (auxActive : Bool) (auxValue : Rat)
      return (out : Coef × Option Rat)
    ensures out.1 = chooseCoef perClassEffective coefByPerClass coefByJoint
    ensures out.2 = chooseAux  auxActive auxValue

with the two pure decisions fully unfolded in the ``pure`` region:

    chooseCoef p a b = if p then a else b
    chooseAux  q v   = if q then some v else none

There is NO ``require`` clause (the domain is total: every combination of the six
binders is admissible), and the ``axioms`` region is EMPTY — both post-images are
concrete functions of the method's own arguments, so there is no opaque answer key
for a rival to echo (directive 8 is satisfied structurally).

TWO INDEPENDENT top-level clauses, each with its own load-bearing content:

  * CLAUSE 1 (``out.1``) — SELECTION. The committed vector must be the candidate
    named by the strategy actually IN EFFECT. Three separable sub-behaviours:
      (1a) the decision consults ``perClassEffective``, never the merely
           REQUESTED flag ``perClassRequested`` (the two are independent binders
           and can disagree);
      (1b) the true branch commits the per-class candidate (not the joint one);
      (1c) the committed value is one of the two PREPARED candidates, carried
           through unchanged — not a fabricated vector of the right shape.
  * CLAUSE 2 (``out.2``) — GUARDED RECORD. The auxiliary slot carries the
    prepared value exactly when the auxiliary mode is in effect, and is EMPTY
    otherwise. Three separable sub-behaviours:
      (2a) mode off ⇒ ``none`` (no value may be synthesized from data that does
           not apply);
      (2b) mode on  ⇒ ``some auxValue`` — the PREPARED auxiliary quantity, not
           some other in-scope number, and unconditionally in that quantity: the
           record may not be suppressed for particular values of it;
      (2c) the guard is not inverted.

The clauses are INDEPENDENT: ``out.1`` never mentions ``auxActive``/``auxValue``
and ``out.2`` never mentions the strategy flags or the candidates. So a battery
that attacked only one of them would leave a rival that mishandled the other
entirely undetected, and each clause below carries its own rivals.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case accounting
in the footer):

  * ECHOABLE-VALUE / UNFORGEABLE-CAPABILITY. The sibling's headline attack is an
    ECHO: its site-1 value clause is satisfiable by returning the value argument
    with no read performed, so it needs an unforgeable rank-indexed capability
    token to pin the control-flow effect the value abstraction drops. That whole
    apparatus has NO counterpart here, and for a reason that STRENGTHENS this
    surface rather than weakening it: this bundle does not model the read at all.
    It models the SELECTION BETWEEN two candidate vectors that surrounding,
    unchanged code has already prepared — so the discriminating content is a
    value relation among the method's own arguments (``out.1`` must equal one
    specific argument), and the analogue of the echo attack (commit something
    other than the selected candidate) is refuted directly by clause 1 with no
    capability machinery needed. ``weak-fabricated-vector`` is that attack in its
    strongest form on this carrier: it fabricates a vector of the right length
    from the correctly-selected candidate, so it gets the SHAPE right and is
    refuted only by the value relation.
  * PARTIAL-DOMAIN. Heavily exercised, and the sibling's central class. Each
    selection rival is correct on part of the domain and diverges exactly where
    the two strategy flags disagree, or on one layout only. The tightest member
    is ``weak-either-flag`` (added by audit), which agrees with the frozen
    decision on three of the four flag combinations.
  * VALUE-SUBSTITUTION. Ported: record an in-scope number that is NOT the
    prepared auxiliary quantity.
  * INVERTED-BRANCH. Ported for both clauses (the negated-selection rival is
    subsumed by the hardcode pair for clause 1; clause 2 keeps its own).
  * FRAME / PERMISSION-MUTATION — VACUOUS, exactly as the sibling records it. The
    sibling states this class does not apply even on nagini: every parameter is an
    immutable by-value scalar or option with no heap reference held at partial
    permission. Lean/Velvet are referentially transparent a fortiori — no heap, no
    aliasing, and the method declares no ``mut`` binder. No substitute probe is
    fabricated.
  * DIVERGENCE / NON-TERMINATION — CORRECTED BY AUDIT. An earlier revision of
    this footer asserted that the bundle runs under
    ``set_option loom.semantics.termination "total"`` and that a non-terminating
    impl therefore VERIFIES vacuously, recording the class as an open spec hole.
    That was factually wrong about this artifact: line 4 of the frozen file reads
    ``set_option loom.semantics.termination "total"``, so the verifier DOES
    discharge a termination obligation here and the naive diverging rival is
    REJECTED. Re-measured with real builds during the audit, on two rivals — a
    ``while true do pure ()`` prefix ahead of the frozen body, and the same prefix
    returning the unambiguously wrong ``([], none)`` — both exit 1 with
    ``error: Decreasing annotations are required in total correctness semantics``,
    i.e. a rejection attributable to the spec's own totality obligation.
    The class is nonetheless NOT shipped as a reject case, for a demonstrated
    MECHANICAL reason and not a spec one: that error is raised on the METHOD
    DECLARATION, which the witness file retains after the ``prove_correct`` block
    is stripped. So a witness against a diverging rival fails on the loop error
    before reaching its claim (measured: both rivals' witness builds exit 1 on
    ``Decreasing annotations are required …`` plus a stuck
    ``Tactic `decide` failed for proposition``). Witness half 1 — elaborate
    against the rival — is unmeetable, so the case could only ever record
    ``witness-unproven``. This disposition tracks the ``termination`` option and
    must be re-derived if it ever moves.
    NOTHING remains open here, and this paragraph RETRACTS the "strictly narrower
    successor class" a previous revision escalated. That revision claimed the
    totality obligation accepts a NON-DECREASING measure, and reported a
    ``while true`` prefix carrying ``decreasing (1 : Nat)`` and returning the
    unambiguously wrong ``([], none)`` as VERIFYING at exit 0 in scope with the
    frozen header intact. RE-MEASURED on this cell with a real build, that exact
    shape is REJECTED at exit 1 on the measure's OWN descent goal:
    ``unsolved goals case «decreasing_1: (1 : Nat)» ... ⊢ 1 < 1``. A constant
    ``decreasing (0 : Nat)`` fares the same way (``⊢ 0 < 0``). So the
    strict-decrease side condition IS proven and the constant measure fails it;
    the corpus-wide escalation is withdrawn, and no spec hole is reported from
    this class.
    THE MECHANISM, so the retraction does not rest on one build:
    ``set_option loom.semantics.termination "total"`` itself opens the
    ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``, the
    ``openScope `TotalCorrectness`` arm), line 7 of the frozen file opens it again
    explicitly, and ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the
    ``measure`` and emits ``⌜measure b' < measure b⌝`` as a goal the proof must
    discharge. Only the ``PartialCorrectness`` twin takes a measure and drops it,
    which is why the two lines have to move together and do here. The class stays
    unshipped for the WITNESS reason above, not a semantic one.

WITNESS MECHANICS. The frozen impl is loop-free (two ``if`` expressions and a
pair), so its extracted tester reduces under ``decide``; every rival below is
likewise a loop-free expression, so the tester+``decide`` route is live on both
sides and no carrier-conditioning is needed (no witness binds anything, so no
consistency probe applies). Each reject case therefore carries a machine-checked
``recordClassResultTester … = false`` at ONE concrete literal input, checked in a
file whose ``prove_correct`` block has been stripped so no tactic script can mask
the verdict. Both halves were checked out-of-band with ``scripts/lean_verify.sh``:
every witness ELABORATES against its own rival (exit 0), and the tester was
separately confirmed to reduce to ``true`` on the FROZEN solution at all eight
witness points (so ``= false`` fails there — ``decide proved that the proposition
… is false``). No witness uses ``sorry``/``admit``/``native_decide``. The method
has no ``require`` clause, so no witness input can be vacuously excluded by a
false precondition. No witness binds a hypothesis, so the gate's consistency
probe does not apply to any case here (verified: ``consistency_probe`` returns
``None`` for all nine).

Independently re-derived during audit with real builds: all 9 rival-side witness
builds exit 0, all 9 gold-side builds exit 1, and every gold-side failure is the
SEMANTIC form ``decide proved that the proposition … is false`` — never a missing
identifier, type error, stuck reduction or timeout. The FORGERY pair was built at
every witness point as well: the FLIPPED claim
(``recordClassResultTester … = true``, i.e. asserting the frozen solution is
CORRECT there) elaborates against the frozen solution (exit 0) and FAILS against
each rival (exit 1, ``decide proved that the proposition … = true is false``). So
each side's exit code TRACKS the claim rather than the file, which is what rules
out a gold-side failure that only looks like a refutation.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(both decisions consume only values prepared by unchanged surrounding code), so
there is nothing for an axiom probe to falsify — and this gate ignores
``AXIOM_TESTS`` regardless. The sibling's three axiom cases are dropped here.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14087"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end`. The comment lines are kept in the anchor so the substring is
# unique and lies wholly inside the elided impl region. Every variant edits ONLY
# this block (and, for the reshapes/admissibility probe, the elided
# `prove_correct` tactic body), so the spec view is untouched.
_IMPL = (
    "    -- Commit the coefficient vector matching the strategy in effect, and the\n"
    "    -- auxiliary mixing value only when the auxiliary mode applies.\n"
    "    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint\n"
    "    let aux : Option Rat := if auxActive then some auxValue else none\n"
    "    return (coef, aux)"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof, verbatim. A correct RESHAPE may retune this block (elided
# from the spec view, and the `prove_correct recordClassResult` header is kept
# byte-identical); rivals leave it alone, so a wrong impl leaves the
# postcondition goal unsolved and the rival module fails to build — which is what
# expect="reject" requires. The witness, not the module build, is what attributes
# each rejection to the spec.
_PROOF = ("prove_correct recordClassResult by\n"
          "  loom_solve <;> simp only [chooseCoef, chooseAux]")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (correct reshapes only)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `recordClassResultTester pe pr cpc cj aa av = false` says the extracted
# ---- program's output violates the postcondition at that concrete input. The
# ---- method has no `require` clause, so no input short-circuits the tester.
def _witness(call):
    return ("extract_program_for recordClassResult\n"
            "prove_precondition_decidable_for recordClassResult\n"
            "prove_postcondition_decidable_for recordClassResult\n"
            "derive_tester_for recordClassResult\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — call the two pure decisions DIRECTLY
    # instead of inlining their `if` expressions. Observationally identical on
    # every input, so both clauses hold on the whole domain and the frozen proof
    # still closes the byte-identical obligation. Verified out-of-band (exit 0).
    # =====================================================================
    {
        "id": "pos-direct-model-call",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    return (chooseCoef perClassEffective coefByPerClass coefByJoint,\n"
            "            chooseAux auxActive auxValue)"),
        "rationale": "structurally different CORRECT impl: it returns the two "
                     "pure decisions applied directly rather than inlining their "
                     "branch expressions, and drops the two intermediate `let` "
                     "bindings. Identical on every value of all six binders, so "
                     "both `ensures` clauses hold across the whole domain. A "
                     "faithful reshape MUST verify — if it did not, the "
                     "postcondition would be rejecting its own model's output "
                     "(SPEC-TOO-STRONG, over-fit to one way of spelling the "
                     "decisions).",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — BOTH branch tests NEGATED with the arms
    # swapped: `if !perClassEffective then coefByJoint else coefByPerClass` and
    # `if !auxActive then none else some auxValue`. Provably equal to the frozen
    # form (case analysis on two Bools), but a genuinely different control-flow
    # shape: the frozen `simp only` alone does NOT close it, so the proof is
    # retuned inside the elided tactic body with a two-Bool case split — the
    # `prove_correct recordClassResult` header stays byte-identical and no lemma
    # or assumption is added. Verified out-of-band (exit 0).
    # =====================================================================
    {
        "id": "pos-negated-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    let coef : Coef := if !perClassEffective then coefByJoint else coefByPerClass\n"
            "    let aux : Option Rat := if !auxActive then none else some auxValue\n"
            "    return (coef, aux)",
            "prove_correct recordClassResult by\n"
            "  loom_solve <;> simp only [chooseCoef, chooseAux] <;> "
            "(cases perClassEffective <;> cases auxActive <;> simp)"),
        "rationale": "structurally different CORRECT impl: BOTH decisions are "
                     "written with the test negated and the arms swapped, which is "
                     "provably equivalent by case analysis on the two booleans yet "
                     "is a real control-flow reshape (the frozen tactic line alone "
                     "leaves the goal `(if (!p) = true then b else a) = if p = true "
                     "then a else b` unsolved). The proof is retuned inside the "
                     "elided tactic body with a two-boolean case split — same "
                     "obligation statement, no new lemma, nothing assumed. Must "
                     "verify, else SPEC-TOO-STRONG (the clauses would be pinned to "
                     "the polarity of the frozen branch tests rather than to the "
                     "behaviour).",
    },
    # =====================================================================
    # ADMISSIBILITY — the sibling's admissibility probe re-establishes that the
    # precondition admits a normal F2P-shaped input and lets the intended
    # computation be established. This method has NO `require` clause, so
    # "admits the input" is trivial; the residual admissibility risk on this
    # carrier is that the two post-images could be DEGENERATE — satisfiable by a
    # constant, or agreeing on both branches, in which case the clauses would pin
    # nothing even though they verify. One in-region assert pins, at concrete
    # values of both flags, that each decision (a) takes the intended value on
    # each branch and (b) genuinely DIFFERS between its two branches. The impl is
    # kept verbatim so the method's own obligation still discharges; the proof is
    # retuned only to clear the extra assert goal. Assert liveness was confirmed
    # out-of-band: flipping one conjunct to a false claim leaves the build failing.
    # =====================================================================
    {
        "id": "admiss-decisions-non-degenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (chooseCoef true [1] [2] = [1] ∧ chooseCoef false [1] [2] = [2] ∧\n"
            "       chooseCoef true [1] [2] ≠ chooseCoef false [1] [2] ∧\n"
            "       chooseAux true (3 : Rat) = some 3 ∧ chooseAux false (3 : Rat) = none ∧\n"
            "       chooseAux true (3 : Rat) ≠ chooseAux false (3 : Rat)))\n"
            "    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint\n"
            "    let aux : Option Rat := if auxActive then some auxValue else none\n"
            "    return (coef, aux)",
            "prove_correct recordClassResult by\n"
            "  loom_solve <;> simp only [chooseCoef, chooseAux]\n"
            "  all_goals decide"),
        "rationale": "the modeled domain is TOTAL (no `require` clause), so both "
                     "clauses must be satisfiable AND non-degenerate at a normal "
                     "input. The in-region assert pins, at concrete values, that "
                     "each decision takes its intended value on BOTH branches and "
                     "that the two branches genuinely DIFFER — so neither clause "
                     "collapses to a constant or to a branch-insensitive value. "
                     "The impl is kept verbatim so the method's own `ensures` "
                     "discharges too. If the assert could not be discharged the "
                     "clauses would be excluding the intended per-branch "
                     "behaviour (PRECOND-TOO-STRONG); if it were discharged "
                     "vacuously the clauses would pin nothing, which the two "
                     "disequality conjuncts rule out.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete literal input and the refinement argument that its faithful
    # counterpart would NOT resolve the failing tests. CLAUSE 1 first.
    # =====================================================================
    {
        "id": "weak-requested-not-effective",
        "kind": "uniqueness",
        "expect": "reject",
        # THE headline defect: select on the merely-REQUESTED strategy flag
        # instead of the one in effect. Correct wherever the two flags agree;
        # wrong exactly where they disagree.
        "module": _impl(
            "    let coef : Coef := if perClassRequested then coefByPerClass else coefByJoint\n"
            "    let aux : Option Rat := if auxActive then some auxValue else none\n"
            "    return (coef, aux)"),
        "refinement": "this is the pre-fix behaviour: the selection consults the "
                      "strategy as originally requested rather than the one in "
                      "effect. Whenever the request is the deferred form, the "
                      "requested-flag test is false while the effective layout is "
                      "the per-class one, so the branch reads the stored "
                      "coefficients under the wrong layout — an out-of-range "
                      "access on an array with fewer axes than the read supplies, "
                      "which raises rather than returning. The failing no-refit "
                      "shape assertions for the deferred-strategy configuration "
                      "never get a result at all, so a faithful counterpart does "
                      "NOT resolve.",
        "rationale": "REJECT from clause 1 (`out.1 = chooseCoef "
                     "perClassEffective …`) via sub-behaviour 1a: the post-image "
                     "selects on `perClassEffective`, the rival on the "
                     "independent binder `perClassRequested`, so the two disagree "
                     "at every input where the flags differ and the candidates "
                     "differ. Verifying would be SPEC-TOO-WEAK (the clause would "
                     "not pin WHICH flag drives the decision — the entire content "
                     "of this behaviour). Refuted at perClassEffective=true, "
                     "perClassRequested=false, candidates [1] vs [2]: the spec "
                     "commits [1], the rival [2]. Five of the eight witnesses "
                     "make the two strategy flags DISAGREE (this one, "
                     "weak-aux-unconditional, weak-aux-wrong-quantity, "
                     "weak-aux-inverted-guard and weak-either-flag), and the "
                     "disagreement is load-bearing at BOTH polarities: it is "
                     "what refutes this rival here (effective=true, "
                     "requested=false) and what refutes weak-either-flag at "
                     "the mirrored point (effective=false, requested=true).",
        "witness": _witness("recordClassResultTester true false [1] [2] true 3"),
    },
    {
        "id": "weak-hardcode-per-class",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the flags entirely and always commit the per-class candidate.
        # Correct on the per-class layout, wrong on the joint one.
        "module": _impl(
            "    let coef : Coef := coefByPerClass\n"
            "    let aux : Option Rat := if auxActive then some auxValue else none\n"
            "    return (coef, aux)"),
        "refinement": "a counterpart that always took the per-class read-out "
                      "would, on the joint layout, index the stored coefficients "
                      "with one axis too few — silently producing a vector of the "
                      "wrong extent for that class rather than the averaged one. "
                      "The failing no-refit tests assert the exact coefficient "
                      "shape for the joint configuration, so it does NOT resolve.",
        "rationale": "REJECT from clause 1 via sub-behaviour 1b: the post-image "
                     "commits the JOINT candidate when the effective strategy is "
                     "not the per-class one, but the rival commits the per-class "
                     "candidate unconditionally, so it disagrees at every input "
                     "with perClassEffective=false and distinct candidates. "
                     "Verifying would be SPEC-TOO-WEAK (the false branch of the "
                     "selection would be unpinned). Refuted at "
                     "perClassEffective=false with candidates [4,7] vs [5]: the "
                     "spec commits [5], the rival [4,7]. It is one of two "
                     "witnesses holding BOTH the auxiliary mode off and the "
                     "effective strategy false (the other is "
                     "weak-aux-unconditional, whose rival is correct on clause "
                     "1 and so does not probe the selection there), and one of "
                     "two whose candidates have different lengths — a length "
                     "difference is what makes the mis-selection observable to "
                     "a shape-level reading as well as to the value relation.",
        "witness": _witness("recordClassResultTester false false [4, 7] [5] false 0"),
    },
    {
        "id": "weak-hardcode-joint",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror hardcode: always commit the joint candidate. Correct on the
        # joint layout, wrong on the per-class one. Kept as its own case because
        # it is the near-miss the previous rival does NOT subsume — the two are
        # wrong on complementary halves of the strategy domain, so a witness for
        # one says nothing about the other.
        "module": _impl(
            "    let coef : Coef := coefByJoint\n"
            "    let aux : Option Rat := if auxActive then some auxValue else none\n"
            "    return (coef, aux)"),
        "refinement": "a counterpart that always took the joint read-out would, "
                      "on the per-class layout, supply one index axis more than "
                      "the stored coefficients have — the out-of-range access the "
                      "issue reports, which raises instead of returning. The "
                      "failing no-refit assertions for the per-class "
                      "configuration then never run, so it does NOT resolve.",
        "rationale": "REJECT from clause 1 via sub-behaviour 1b, on the "
                     "COMPLEMENTARY half of the strategy domain from "
                     "weak-hardcode-per-class: the post-image commits the "
                     "per-class candidate when the effective strategy IS the "
                     "per-class one, the rival commits the joint candidate "
                     "regardless. Neither rival subsumes the other (each is "
                     "correct exactly where the other is wrong), so it gets its "
                     "own witness at the opposite value of perClassEffective. "
                     "Refuted at perClassEffective=true (both flags true, so the "
                     "requested flag cannot explain the failure) with candidates "
                     "[6] vs [8,9]: the spec commits [6], the rival [8,9].",
        "witness": _witness("recordClassResultTester true true [6] [8, 9] true 2"),
    },
    {
        "id": "weak-fabricated-vector",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's ECHO attack in its strongest form on this carrier: select
        # the CORRECT candidate, take its length, and commit a same-length vector
        # of zeros. Gets the shape right on the whole domain and consults the
        # right flag; only the value relation refutes it.
        "module": _impl(
            "    let coef : Coef := List.replicate\n"
            "      (if perClassEffective then coefByPerClass.length else coefByJoint.length) 0\n"
            "    let aux : Option Rat := if auxActive then some auxValue else none\n"
            "    return (coef, aux)"),
        "refinement": "a counterpart that emitted a correctly-shaped placeholder "
                      "instead of the prepared averaged coefficients would pass a "
                      "shape check while recording coefficients that were never "
                      "fitted — the aggregation branch would commit a degenerate "
                      "vector for every class. The failing tests are run through "
                      "an estimator whose subsequent behaviour depends on those "
                      "values, and the surrounding no-refit contract requires the "
                      "committed vector to be the averaged read-out, so it does "
                      "NOT resolve.",
        "rationale": "REJECT from clause 1 via sub-behaviour 1c, the analogue of "
                     "the sibling's ECHO probe: this rival consults the RIGHT "
                     "flag and produces the RIGHT extent, so it is not caught by "
                     "any flag- or shape-level reasoning — only by the clause's "
                     "value relation, which requires the committed vector to BE "
                     "the selected prepared candidate rather than merely to look "
                     "like it. Verifying would be SPEC-TOO-WEAK (the clause would "
                     "constrain only the shape, and the sibling's whole "
                     "unforgeable-token apparatus would be needed here too). "
                     "Refuted at perClassEffective=true with candidate [3]: the "
                     "spec commits [3], the rival [0]. This witness is the only "
                     "one that holds the auxiliary mode off while the effective "
                     "strategy is true.",
        "witness": _witness("recordClassResultTester true true [3] [9] false 5"),
    },
    {
        "id": "weak-either-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit. The TIGHTEST near-miss on clause 1: commit the
        # per-class candidate when EITHER strategy flag names it. Strictly
        # closer to the frozen decision than weak-requested-not-effective —
        # correct on three of the four flag combinations, wrong only at
        # (effective=false, requested=true) — so the four pre-existing clause-1
        # witnesses all sit at points where it AGREES with the spec and none of
        # them refutes it. It pins the direction of sub-behaviour 1a that the
        # battery previously left unattacked: not merely "consult the effective
        # flag" but "the requested flag must not be able to OVERRIDE it".
        "module": _impl(
            "    let coef : Coef := if perClassEffective || perClassRequested then coefByPerClass else coefByJoint\n"
            "    let aux : Option Rat := if auxActive then some auxValue else none\n"
            "    return (coef, aux)"),
        "refinement": "a counterpart that took the per-class read-out whenever "
                      "EITHER the effective or the originally-requested "
                      "strategy named it would, on a fit whose request is the "
                      "per-class form but whose strategy in effect is the joint "
                      "one, index the stored coefficients with one axis too few "
                      "— silently committing a vector of the wrong extent for "
                      "that class instead of the averaged joint read-out. The "
                      "failing shape assertions for that configuration pin the "
                      "exact coefficient extent, so it does NOT resolve.",
        "rationale": "REJECT from clause 1 via sub-behaviour 1a, in the "
                     "direction weak-requested-not-effective does NOT cover. "
                     "That rival replaces the effective flag; this one lets the "
                     "requested flag override it, so it agrees with the frozen "
                     "decision on three of the four flag combinations and is "
                     "wrong only at (effective=false, requested=true). "
                     "Measured: every other clause-1 witness in this battery "
                     "sits at a point where this rival is CORRECT, so without "
                     "its own witness the near-miss would be unattacked. "
                     "Verifying would be SPEC-TOO-WEAK (the clause would pin "
                     "which flag is consulted but not that the requested flag "
                     "is irrelevant). Refuted at effective=false, "
                     "requested=true with candidates [13] vs [14,15]: the spec "
                     "commits [14,15], the rival [13].",
        "witness": _witness("recordClassResultTester false true [13] [14, 15] true 6"),
    },
    # ---- CLAUSE 2 rivals ------------------------------------------------
    {
        "id": "weak-aux-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # The second pre-fix defect: record the auxiliary value unconditionally,
        # never leaving the slot empty. Correct whenever the mode IS in effect.
        "module": _impl(
            "    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint\n"
            "    let aux : Option Rat := some auxValue\n"
            "    return (coef, aux)"),
        "refinement": "this is the second pre-fix behaviour: the auxiliary value "
                      "is recorded with no guard. Outside the auxiliary mode the "
                      "table it is averaged from is the degenerate one-element "
                      "placeholder, so the recorded per-class entry is derived "
                      "from data that does not apply and the assembled result "
                      "attribute no longer has one well-formed entry per class. "
                      "The failing tests assert exactly that per-class shape for "
                      "the non-auxiliary modes, so a faithful counterpart does "
                      "NOT resolve.",
        "rationale": "REJECT from clause 2 (`out.2 = chooseAux auxActive "
                     "auxValue`) via sub-behaviour 2a: the post-image is `none` "
                     "when the mode is off, but the rival records `some auxValue` "
                     "there. Verifying would be SPEC-TOO-WEAK (the empty-slot arm "
                     "would be unpinned — and clause 2 is INDEPENDENT of clause 1, "
                     "so none of the selection rivals probes it). Refuted at "
                     "auxActive=false with auxValue=4: the spec records `none`, "
                     "the rival `some 4`. (An earlier revision claimed this was "
                     "the only witness holding perClassEffective=false with the "
                     "requested flag true; counted mechanically during the audit, "
                     "weak-either-flag and weak-aux-wrong-quantity share that "
                     "flag pair. The claim is withdrawn — it was never "
                     "load-bearing for this rejection, which turns only on the "
                     "auxActive=false arm; the witness point itself is still "
                     "distinct from every other case's tuple.)",
        "witness": _witness("recordClassResultTester false true [2] [7] false 4"),
    },
    {
        "id": "weak-aux-wrong-quantity",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard correct, value wrong: record a DIFFERENT in-scope number (the
        # leading entry of the per-class candidate) instead of the prepared
        # auxiliary quantity. Satisfies "occupied exactly when the mode is on".
        "module": _impl(
            "    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint\n"
            "    let aux : Option Rat := if auxActive then some (coefByPerClass.headD 0) else none\n"
            "    return (coef, aux)"),
        "refinement": "a counterpart that recorded a different in-scope quantity "
                      "— a number lifted out of the coefficient read-out rather "
                      "than the prepared auxiliary average — would fill the "
                      "auxiliary result attribute with values that are not the "
                      "auxiliary quantity at all. The recorded entry is asserted "
                      "against the auxiliary grid in the failing configuration, "
                      "so it does NOT resolve.",
        "rationale": "REJECT from clause 2 via sub-behaviour 2b: the rival gets "
                     "the GUARD exactly right (occupied iff the mode is in "
                     "effect) and is refuted purely by the identity of the "
                     "recorded value, which the clause grounds in the prepared "
                     "input `auxValue`. Verifying would be SPEC-TOO-WEAK (the "
                     "value would be ungrounded — any in-scope number would do). "
                     "Refuted at auxActive=true, auxValue=5 with per-class "
                     "candidate [11]: the spec records `some 5`, the rival "
                     "`some 11`. Distinct from the unconditional rival, which is "
                     "correct at every input where the mode IS on and so is not "
                     "refuted here.",
        "witness": _witness("recordClassResultTester false true [11] [12] true 5"),
    },
    {
        "id": "weak-aux-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard inverted: empty when the mode is on, occupied when it is off.
        # Wrong on BOTH arms — a near-miss kept as a cheap supporting case, given
        # its own witness because the arm it shares with the unconditional rival
        # is the one where THAT rival is correct.
        "module": _impl(
            "    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint\n"
            "    let aux : Option Rat := if auxActive then none else some auxValue\n"
            "    return (coef, aux)"),
        "refinement": "a counterpart with the guard inverted would leave the slot "
                      "empty precisely in the mode where the auxiliary value is "
                      "meaningful, and fill it from the degenerate placeholder "
                      "table in every other mode — so BOTH the auxiliary and the "
                      "non-auxiliary configurations record the wrong entry. Every "
                      "failing case asserts the auxiliary result attribute, so it "
                      "does NOT resolve.",
        "rationale": "REJECT from clause 2 via sub-behaviour 2c: both arms of the "
                     "guard are swapped, so the rival disagrees with the "
                     "post-image at EVERY input (`none` where `some auxValue` is "
                     "required and conversely). Given its own witness rather than "
                     "sharing one: on the mode-off arm it fails for the same "
                     "reason as weak-aux-unconditional, but on the mode-ON arm — "
                     "where that rival is correct — only this one is wrong, so its "
                     "witness is placed there (auxActive=true, auxValue=7: the "
                     "spec records `some 7`, the rival `none`).",
        "witness": _witness("recordClassResultTester true false [5] [6] true 7"),
    },
    {
        "id": "weak-aux-nonzero-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit (attack D). The TIGHTEST near-miss on clause 2, and the
        # one the pre-existing battery measurably left unattacked: the guard is
        # strengthened with an extra value test, so the slot is occupied exactly
        # when the mode is in effect AND the prepared quantity is non-zero. It
        # therefore agrees with the frozen decision at EVERY input except the
        # single sub-domain auxActive=true, auxValue=0 — and no pre-existing
        # witness sits there (measured: all eight of them exit 1 against this
        # rival, i.e. none refutes it). It pins the direction of sub-behaviour 2b
        # the value-substitution rival does not reach: not merely "the recorded
        # value must be the prepared one" but "the record must not be conditioned
        # on that value at all".
        "module": _impl(
            "    let coef : Coef := if perClassEffective then coefByPerClass else coefByJoint\n"
            "    let aux : Option Rat := if auxActive && auxValue != 0 then some auxValue else none\n"
            "    return (coef, aux)"),
        "refinement": "a counterpart that suppressed the record whenever the "
                      "prepared auxiliary quantity happened to be zero would "
                      "leave the slot empty for exactly those classes whose "
                      "averaged auxiliary value came out at the bottom of the "
                      "grid — a per-class entry silently missing from the "
                      "assembled result attribute rather than present and zero. "
                      "The failing tests assert one well-formed entry per class "
                      "for the auxiliary configuration, so it does NOT resolve.",
        "rationale": "REJECT from clause 2 (`out.2 = chooseAux auxActive "
                     "auxValue`) via sub-behaviour 2b, in the direction "
                     "weak-aux-wrong-quantity does NOT cover. That rival keeps "
                     "the guard exact and corrupts the VALUE; this one keeps the "
                     "value exact and makes the GUARD depend on it, so it is "
                     "correct at every input except auxActive=true with "
                     "auxValue=0. Measured during the audit: every one of the "
                     "eight pre-existing witnesses sits at a point where this "
                     "rival AGREES with the spec, so the sub-domain was "
                     "genuinely unattacked — the battery's binder table varied "
                     "auxValue over 0,2,3,4,5,6,7 but never paired the zero with "
                     "the mode ON. Verifying would be SPEC-TOO-WEAK (clause 2 "
                     "would pin the guard only up to a value-dependent "
                     "exception). Refuted at auxActive=true, auxValue=0: the spec "
                     "records `some 0`, the rival `none`.",
        "witness": _witness("recordClassResultTester true true [8] [9] true 0"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 13 SPEC cases (2
# soundness, 1 admissibility, 10 uniqueness) plus 3 AXIOM cases, over TWO
# contracted functions. (An earlier revision of this footer said 12/9; the
# sibling manifest actually loads 13/10 — counted mechanically during the
# audit. The disposition rows below were complete; only the totals were off.)
# This bundle contracts ONE method whose two `ensures` clauses model the same
# two decisions — but over a narrower surface: the sibling's site 1 models the
# ACCESS (a rank-indexed read capability plus an echoable value), whereas here
# the two candidate vectors are already prepared and the modeled decision is
# which one is committed. That narrowing dissolves the sibling's entire
# capability-token apparatus (4 cases) into ONE value-level clause, which is why
# the port is 9 cases rather than 13 — carrier narrowing, not thinning.
#
#   sibling case                      -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-control-site1-branch-reshape  -> pos-negated-branches          PORTED (merged)
#   pos-control-site2-init-override   -> pos-negated-branches          PORTED (merged)
#   (no sibling)                      -> pos-direct-model-call         ADDED
#   admiss-site1-arity-establishable  -> admiss-decisions-non-degenerate PORTED (re-aimed)
#   rival-echo-no-read                -> weak-fabricated-vector        PORTED (re-expressed)
#   rival-unresolved-operand          -> weak-requested-not-effective  PORTED
#   rival-hardcode-independent        -> weak-hardcode-per-class       PORTED
#   (no sibling)                      -> weak-hardcode-joint           ADDED
#   (no sibling)                      -> weak-either-flag              ADDED (audit)
#   rival-forge-rank-joint            -> (none)                        OMITTED (no carrier)
#   rival-forge-rank-independent      -> (none)                        OMITTED (no carrier)
#   rival-forge-rank-unresolved       -> (none)                        OMITTED (no carrier)
#   rival-diverge-loop                -> (none)                        SPEC-CLOSED
#   rival-site2-always-value          -> weak-aux-unconditional        PORTED
#   rival-site2-wrong-value           -> weak-aux-wrong-quantity       PORTED
#   rival-site2-inverted              -> weak-aux-inverted-guard       PORTED
#   (no sibling)                      -> weak-aux-nonzero-only         ADDED (audit)
#   frame-mutation (sibling: N/A)     -> (none)                        VACUOUS
#   AXIOM_TESTS (3)                   -> (none)                        DROPPED (G-AX)
#
# PORTED (positives, MERGED): the sibling's two positives reshape one site each
#   (site 1's branch test rewritten as an equivalent comparison; site 2's
#   if/else rewritten as init-then-override). Here both decisions live in ONE
#   method, so the equivalent-reshape argument applies to both clauses at once
#   and pos-negated-branches carries it: both tests negated with arms swapped,
#   provably equal by case analysis, with the proof retuned inside the elided
#   tactic body (the frozen `simp only` genuinely does NOT close it — measured).
# ADDED (pos-direct-model-call): the merge would otherwise leave only one
#   positive, and this one is a DIFFERENT kind of reshape (drop the intermediate
#   bindings and apply the pure decisions directly) that the frozen proof closes
#   unchanged. Both positives were verified out-of-band with real builds.
# PORTED-RE-AIMED (admissibility): the sibling asserts its precondition admits an
#   F2P-shaped input and that the arity-matching access is establishable there.
#   This method has NO `require` clause, so admission is trivial and the residual
#   risk is DEGENERACY of the two post-images; the re-aimed assert pins that each
#   decision hits its intended value on both branches AND that the branches
#   differ. Assert liveness confirmed out-of-band (a falsified conjunct fails).
# PORTED-RE-EXPRESSED (rival-echo-no-read -> weak-fabricated-vector): the
#   sibling's echo returns the value argument with no access performed, and is
#   caught only by an unforgeable capability token because its value clause is
#   satisfiable without doing the work. Here the committed vector must EQUAL one
#   of the method's own prepared arguments, so the strongest echo-shaped attack
#   available is a correctly-shaped fabrication — and the value relation refutes
#   it directly. Same argument (a result that merely looks right must not
#   satisfy the clause), re-expressed on a carrier that needs no token.
# OMITTED (the three rival-forge-rank-* cases): NO COUNTERPART ON THIS CARRIER,
#   and not for difficulty. Those rivals attack a rank ARGUMENT passed to a
#   capability-granting callee — they forge self-consistency between the access
#   they perform and the rank they claim to have checked it against. This bundle
#   models no access, no rank, and no capability: the spec's `axioms` region is
#   empty and the whole obligation is a value relation among prepared inputs.
#   There is no rank argument to forge, so any "port" would have to invent a
#   modeled quantity the spec does not have. Their shared ADVERSARIAL CONTENT —
#   that a rival may pick the wrong layout and still look internally consistent —
#   IS carried, by the two hardcode rivals and weak-requested-not-effective,
#   which cover exactly the three wrong-layout choices the forge cases make
#   (always-joint, always-per-class, driven-by-the-requested-flag).
# SPEC REJECTS IT, MECHANICALLY UNWITNESSABLE (rival-diverge-loop) — disposition
#   CORRECTED BY AUDIT. The previous revision of this row claimed the bundle runs
#   under `partial` semantics and recorded the class as a known spec hole. Line 4
#   of the frozen file actually reads `termination "total"`, so the spec REJECTS
#   the diverging rival: measured, a `while true do pure ()` prefix (both ahead of
#   the frozen body and returning the wrong `([], none)`) exits 1 with
#   `Decreasing annotations are required in total correctness semantics` — the
#   totality obligation, i.e. attributable to the spec, exactly the direction the
#   sibling's MustTerminate(2) closes it in. Not shipped anyway, for a MECHANICAL
#   reason: the missing-measure error is raised on the METHOD DECLARATION, which
#   survives the witness file's `prove_correct` strip, so every witness against a
#   diverging rival fails on that error before reaching its claim (measured on
#   both rivals: exit 1 on the loop error, plus `decide` stuck). Witness half 1 is
#   unmeetable, so the case could only record `witness-unproven`. Re-derive this
#   if the `termination` option ever moves.
#   The "narrower successor class" a previous revision escalated is RETRACTED. It
#   claimed the totality obligation accepts a NON-DECREASING measure, reporting
#   `while true` + `decreasing (1 : Nat)`, returning the wrong `([], none)`, as
#   VERIFYING at exit 0 in scope with the frozen header intact. RE-MEASURED here:
#   that shape is REJECTED at exit 1 on the measure's own descent goal,
#       unsolved goals
#       case «decreasing_1: (1 : Nat)» ... |- 1 < 1
#   and a constant `decreasing (0 : Nat)` likewise leaves `|- 0 < 0`. The
#   strict-decrease condition IS proven; no spec hole is escalated from this class.
#   Mechanism: line 4's `set_option loom.semantics.termination "total"` itself
#   opens the `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean`,
#   `openScope `TotalCorrectness`), line 7 opens it again, and
#   `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
#   `measure b' < measure b` as a goal; only the `PartialCorrectness` twin drops
#   it. The class stays unshipped for the WITNESS reason above.
# VACUOUS (frame-mutation): the sibling records this class as inapplicable on its
#   own carrier (only immutable by-value parameters, no reference held at partial
#   permission). Here a fortiori: referentially transparent, no heap, no aliasing,
#   no `mut` binder. No substitute probe fabricated.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores it;
#   this bundle declares no axioms and no deep-model references, so there is
#   nothing to probe.
#
# BINDER / CLAUSE COVERAGE of the 9 reject witnesses (9 DISTINCT input points),
# in manifest order (weak-either-flag is the 5th and weak-aux-nonzero-only the
# 9th, both added by audit):
#   perClassEffective — true, false, true, true, false, false, false, true, true
#   perClassRequested — false, false, true, true, true, true, true, false, true
#   coefByPerClass    — [1], [4,7], [6], [3], [13], [2], [11], [5], [8]
#   coefByJoint       — [2], [5], [8,9], [9], [14,15], [7], [12], [6], [9]
#   auxActive         — true, false, true, false, true, false, true, true, true
#   auxValue          — 3, 0, 2, 5, 6, 4, 5, 7, 0
#   No two witnesses share an input tuple, and the flag PAIR
#   (perClassEffective, perClassRequested) takes all 4 distinct combinations —
#   so no rival that mishandled one flag while agreeing on the other could hide.
#   The auxiliary PAIR (auxActive, auxValue==0) likewise takes both polarities of
#   the zero on BOTH arms of the guard — the gap the audit measured and closed:
#   before weak-aux-nonzero-only, auxValue=0 appeared only alongside
#   auxActive=false, so a guard conditioned on the value being non-zero agreed
#   with the spec at all eight witness points.
#   Every sub-behaviour of both clauses is attacked: 1a in BOTH directions
#   (weak-requested-not-effective replaces the effective flag;
#   weak-either-flag lets the requested flag override it), 1b on each branch
#   (weak-hardcode-per-class / weak-hardcode-joint), 1c
#   (weak-fabricated-vector), 2a (weak-aux-unconditional), 2b in BOTH directions
#   (weak-aux-wrong-quantity corrupts the value under an exact guard;
#   weak-aux-nonzero-only keeps the value and conditions the guard ON it), 2c
#   (weak-aux-inverted-guard). Both INDEPENDENT top-level clauses carry >=1
#   verify case and >=1 reject case.
#
# AUDIT ADDENDUM — probes run against the FROZEN spec that found no hole. Five
# further wrong impls were built and all were REJECTED on a genuine unsolved
# postcondition goal (not a tactic artifact): selection driven by the auxiliary
# mode flag; the auxiliary slot guarded by the strategy flag; the correct
# candidate REVERSED (shape and multiset preserved); the auxiliary slot filled
# with `some 0` instead of `none` outside the mode; and the guard weakened to a
# conjunction of both flags. Four further CORRECT reshapes were built and all
# VERIFY: `match` on the booleans, `cond` instead of `ite`, selection by
# indexing a two-element table of candidates with the aux slot built as
# `(if _ then [v] else []).head?`, and a single `if` returning whole pairs. The
# last needed the same two-boolean case split pos-negated-branches uses; with
# the frozen tactic line alone it fails on a residual goal that is nonetheless
# TRUE, i.e. a tactic gap and not a spec-too-strong hole. The demonic-choice
# vacuity probes (`let coef :| ...`) do not elaborate on this carrier at all
# (measured this audit: `unexpected token ':|'; expected ':=' or '|'`), so
# unforced choice is not an available evasion here.
#
# SECOND AUDIT ADDENDUM (independent, attacks A–G, all with real builds).
# Attack A: every case's spec view — the frozen file minus the impl region body
#   and the `prove_correct` block — is BYTE-IDENTICAL to the frozen one, and
#   every variant keeps the `prove_correct recordClassResult by` header verbatim.
#   Checked mechanically over all cases; no reformatted statement anywhere.
# Attack B/B′: all 9 reject witnesses rebuilt on both sides plus the forgery pair
#   — see WITNESS MECHANICS above for the exit codes. Every gold-side signature is
#   a plain `decide` evaluation, and the flipped claim inverts both sides, so no
#   case rests on a syntactic failure.
# Attack C: no reject rival is observably identical to the frozen impl — the
#   witness pair proves that for each of the 9 directly (a claim that holds of
#   the rival and fails of gold at a concrete literal input IS an observable
#   difference on this carrier). No vacuous case to drop.
# Attack D: eight NEW wrong impls, none of them in the battery, all REJECTED on a
#   genuine unsolved `ensures_1`/`ensures_2` goal: the auxiliary value taken from
#   the JOINT candidate's head; selection on the XOR of the two flags; selection
#   on their conjunction; the auxiliary record additionally conditioned on the
#   strategy flag; the selected candidate's `tail`; a single-point tamper
#   (`if sel = [42] then []`); the auxiliary value DOUBLED; and the guard
#   conditioned on the value being non-zero. The last one agreed with the spec at
#   all eight pre-existing witness points, so it was landed as
#   weak-aux-nonzero-only rather than merely reported. No probe verified, so
#   attack D found no spec hole.
# Attack E: six NEW correct reshapes, all VERIFY: `=  true`-spelled guards and
#   doubly-negated guards (both under the frozen tactic line), `cond`, an
#   `Option.map` over a unit guard, a `head?` over a singleton list, and a
#   four-way `match` on the two booleans. The `match` reshape needs `simp_all`
#   where the frozen `simp only` leaves `i_1 : false = true ⊢ False` — a residual
#   goal that is TRUE, so a tactic gap, not a SPEC-TOO-STRONG hole. No faithful
#   correct impl was found that the spec rejects.
# Admissibility liveness: each of the six conjuncts in
#   admiss-decisions-non-degenerate was falsified in turn and the build FAILS in
#   all six cases (exit 1), so no conjunct is discharged vacuously and the assert
#   is load-bearing in every direction it claims. Additionally, the F2P-shaped
#   analogue on a total carrier was built directly: the derived tester evaluates
#   to `true` on the frozen solution at a normal input with the two strategy
#   flags DISAGREEING and the auxiliary mode off, appended after the frozen
#   obligation (exit 0) — so the obligation is satisfiable at exactly the input
#   shape the failing configuration has, which is the PRECOND-TOO-STRONG
#   direction this lane exists to test.
# Attack G: the coverage reporter is clean (obl=1, 6 binders, 9 points). The one
#   place its "binder varies" reading was NOT meaningful is the pairing fixed
#   above: auxValue took seven distinct values but only ever met the mode-ON arm
#   at non-zero ones.
AXIOM_TESTS = []
