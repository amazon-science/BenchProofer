"""properties.py — G-PBT falsification battery for sympy__sympy-24213 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct combineAddends`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method combining a sum's addends):

  combineAddends (first : Addend) (rest : List Addend)
      return (out : Combined)
    ensures out = combineSpec first rest                            -- (C1) master
    ensures checkAddends first.dim.deps rest = Check.equivalent
              → out = Combined.reported
                        (first.factor + sumFactors rest) first.dim  -- (C2)
    ensures checkAddends first.dim.deps rest = Check.disagreeing
              → out = Combined.disagreement                        -- (C3)
    ensures checkAddends first.dim.deps rest = Check.unreducible
              → out = Combined.noSignature                         -- (C4)

with ``combineSpec`` / ``checkAddends`` / ``checkStep`` / ``sumFactors``
fully-unfolded ``def``s over a transparent carrier. Each addend carries two
DISTINCT observations of its dimension:

  * ``dim.deps`` — the canonical dependency signature, PARTIAL (``none`` when the
    dimension admits no signature at all); two dimensions that both have one are
    *equivalent* exactly when it is equal, even if written differently;
  * ``dim.surf`` — the surface-expression identity; equal ``surf`` ⇒ equal
    ``deps`` but NOT conversely (two surface-distinct dimensions can share a
    signature).

TWO load-bearing decisions the spec pins, and both are attacked here.

  (i) ACCEPTANCE is driven by ``deps`` (dimensional equivalence), never by
      ``surf`` (surface identity). A surface-distinct-but-equivalent addend must
      be ACCEPTED, and the reported dimension is the first addend's.

  (ii) The TWO value-less outcomes are DISTINCT observations and neither may be
      substituted for the other. ``Combined.disagreement`` is the report that the
      equivalence test RAN — on signatures it had — and returned "not
      equivalent"; ``Combined.noSignature`` is the outcome where no equivalence
      verdict was ever produced, because a dimension in play admits no signature
      and the reduction the test is built on fails before any comparison. A
      caller can tell them apart, so a result carrier with a single value-less
      inhabitant leaves the choice between them FREE — and an impl that always
      reported the wrong one of the two would satisfy such a spec while being
      observably different from the real routine. ``Check`` / ``Combined`` are
      three-valued for exactly that reason, and ``checkStep`` fixes the
      tie-break: the LEFTMOST addend that is not certified decides, in the manner
      in which IT failed. C3 and C4 are the clauses that pin this, and
      ``rival-collapse-to-disagreement`` / ``rival-collapse-to-nosignature`` /
      ``rival-priority-inverted`` are the three rivals aimed at it.

THE CARRIER IS FULLY TRANSPARENT. ``Dim`` is a pair of identity keys (an ``Int``
surface handle and an ``Option Int`` signature handle) and the result is the
three-constructor ``Combined``; ``combineSpec`` / ``checkAddends`` / ``checkStep``
/ ``sumFactors`` compute on concrete literals. So a witness reaches the impl
through Velvet's own tester machinery (``extract_program_for combineAddends`` →
``derive_tester_for combineAddends`` → ``combineAddendsTester first rest =
false := by decide``): the extracted program is checked against the method's
postcondition at ONE concrete input, and ``decide`` closes the residual literal —
no opaque leaf, no carrier conditioning, so NO witness binds a hypothesis and
there is no joint-satisfiability obligation.

WHICH SUBJECT THE SECOND HALF IS CHECKED AGAINST — measured, not assumed, and
NOT the frozen solution. The frozen impl carries a backward ``while`` loop whose
extracted program does not reduce in the kernel, so ``decide`` against the FROZEN
tester is stuck for EVERY claim regardless of truth. Re-measured with real builds
against the CURRENT frozen text: the witness against gold exits 1 with

    Tactic `decide` failed for proposition combineAddendsTester … = false
    because its `Decidable` instance … did not reduce to `isTrue` or `isFalse`

and a FORGERY differing only in flipping the claim (``= true``, i.e. asserting
gold AGREES with the rival there) exits 1 with the same message modulo the
literal — so gold's exit code carries no information about the claim. That is the
``_STUCK_REDUCTION`` screen, and the gate does NOT accept gold as the subject
here: it falls back to a VERIFYING positive of this same spec
(``pos-control-direct``, loop-free, so it reduces) and records
``witness_subject = "a verifying positive from this battery (gold cannot
decide)"``. Against that subject the discrimination is genuine and claim-tracking,
re-measured per case: the witness exits 1 with ``Tactic `decide` proved that the
proposition … = false is false`` — a plain evaluation, the tester returning
``true`` there — while the flipped claim exits 0. So each rejection rests on an
evaluated refutation against a machine-checked correct impl of this spec, not on
a stuck kernel. Exit codes for every case: witness/rival 0, witness/gold 1
(stuck), witness/positive-subject 1 (evaluated), forgery/positive-subject 0.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION (nagini frame-mutation-overwrite-red /
    -surf, MANDATORY there) — VACUOUS. Nagini carries these because ``surf`` /
    ``red`` are held at ``Acc(list_pred(_), 1/2)`` and a store needs full
    permission. Velvet is referentially transparent: ``first`` and ``rest`` are
    immutable values, this bundle declares NO ``mut`` binder over any input, and
    there is no heap and no aliasing — so there is no read-only input to
    overwrite and no substitute probe to build. Not fabricated.
  * DIVERGENCE / NON-TERMINATION (nagini rival-vacuous-nonterminating-loop) —
    NOT a spec hole here, and not shippable as a witnessed reject case either.
    This bundle sets ``loom.semantics.termination "total"`` (Solution.lean line
    4), so the verifier discharges a termination obligation and a diverging rival
    is genuinely REJECTED — measured: an impl whose loop carries no decreasing
    measure (``while i > 0 do i := i + 1``) fails with

        error: Decreasing annotations are required in total correctness semantics

    i.e. the obligation the frozen impl discharges with ``decreasing i`` is not
    optional. So the spec does close this class; there is no vacuous-divergence
    hole to record. What cannot be SHIPPED is the reject CASE, for a measured
    tooling reason rather than a spec one: the rival is rejected before its
    extracted program exists, so its witness build also fails at the same
    decreasing-annotation error and then stalls on the same stuck ``decide``
    (measured: witness/rival exit 1, the tester never reducing). A witness whose
    rival-side build fails is ``witness-unproven``, an inconclusive outcome that
    fails the gate — so a divergence case here would break a battery that
    otherwise holds, while the property it would attest to (divergence is
    rejected) is already established by the build above. Recorded as
    DEMONSTRATED-BY-PROBE, not as a hole and not as vacuous.
  * UNIQUENESS / PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Each
    nagini value/partial-domain rival re-expresses directly onto a clause of the
    frozen spec, plus three added value rivals (wrong reported factor; a
    substituted reported dimension; a reported dimension whose signature is right
    and whose surface is synthesised) pinning the components of C2's
    ``Combined.reported … …`` that the nagini return-value rival attacks jointly,
    plus three OUTCOME-IDENTITY rivals (the two collapses and the inverted
    tie-break) pinning C3/C4 — the clauses that keep the two value-less outcomes
    apart.
  * ADMISSIBILITY (nagini admiss-f2p-shaped-caller) — RE-AIMED and SHIPPED as
    ``admiss-f2p-shaped-point``. It is true that this bundle declares no
    ``require`` clause, so there is no precondition to be too strong; but "the
    frozen obligation has no precondition" is NOT a reason to drop the lane. The
    analogue on a total carrier is the obligation being unsatisfiable or
    DEGENERATE at exactly an F2P-shaped input, and a positive that discharges the
    obligation AT that concrete input — by evaluation, as an in-region
    ``assert``, before closing the frozen obligation verbatim — tests that
    directly. Shipped, and its liveness is measured rather than asserted: the
    same case with the OPPOSITE claim at the same point
    (``combineSpec … = Combined.disagreement``) FAILS with ``Tactic `decide`
    proved that the proposition … is false``, so the assert really is evaluated
    and a false claim there does not slip through.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries three
axiom-soundness / containment probes over the real ``get_dimensional_dependencies``
/ ``equivalent_dims`` callees; that is G-AX's job (axiom_check.py / mapping.md
validate the deep A-reference ``checkStep`` == the real callee) and the G-PBT gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24213"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct combineAddends
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward per-addend loop plus the
# final three-way decision). Reject rivals replace it with a loop-free closed
# form (so their extracted program reduces under decide); the direct positive
# control replaces it with `return combineSpec first rest`.
_IMPL = (
    "    -- impl-start\n"
    "    let mut factor := first.factor\n"
    "    let mut chk : Check := Check.equivalent\n"
    "    let mut i := rest.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ rest.length\n"
    "      invariant chk = checkAddends first.dim.deps (rest.drop i)\n"
    "      invariant factor = first.factor + sumFactors (rest.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let a := rest[i - 1]!\n"
    "      chk := checkStep first.dim.deps a chk\n"
    "      factor := factor + a.factor\n"
    "      i := i - 1\n"
    "    match chk with\n"
    "    | Check.equivalent  => return Combined.reported factor first.dim\n"
    "    | Check.disagreeing => return Combined.disagreement\n"
    "    | Check.unreducible => return Combined.noSignature\n"
    "    -- impl-end"
)

assert _IMPL in _BASE, "frozen impl region drifted; update _IMPL"

# The frozen prove_correct tactic body (the whole block, unique in the file and
# elided from the spec view). The direct positive control retunes it (the loop is
# gone, so `loom_solve` + a `combineSpec` unfold closes the residual goals); every
# reject rival keeps it as-is (it fails to close the reshaped impl, which is the
# intended rejection, but the WITNESS — not the tactic failure — is what the gate
# scores). The reorder positive control keeps it byte-identical.
_PROOF = (
    "prove_correct combineAddends by\n"
    "  loom_solve\n"
    "  · -- invariant_2 maintained: peel the front element exposed by drop (i-1)\n"
    "    rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,\n"
    "        ← invariant_2]\n"
    "  · -- invariant_3 maintained: the factor accumulator gains rest[i-1]\n"
    "    rw [drop_cons_step rest i (by omega) (by omega), sumFactors_cons]\n"
    "    omega\n"
    "  all_goals (\n"
    "    -- final: each of the three outcomes matches combineSpec's own case split\n"
    "    subst done_1\n"
    "    simp only [List.drop_zero] at invariant_2 invariant_3\n"
    "    simp only [combineSpec] at *\n"
    "    simp_all)"
)

assert _PROOF in _BASE, "frozen proof region drifted; update _PROOF"


def _rival(body: str) -> str:
    """Solution.lean whose impl body is a single loop-free closed form. The
    frozen proof is kept as-is (it will fail to close the reshaped impl — the
    intended rejection; the witness is what the gate scores)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# The three-way final decision, verbatim, as every closed-form rival that keeps
# the DECISION honest must spell it. Factored out so a rival's diff against gold
# is exactly the one thing it gets wrong.
def _decide(equiv: str, disagree: str = "Combined.disagreement",
            nosig: str = "Combined.noSignature",
            arg: str = "first.dim.deps rest") -> str:
    return (f"    match checkAddends {arg} with\n"
            f"    | Check.equivalent  => return {equiv}\n"
            f"    | Check.disagreeing => return {disagree}\n"
            f"    | Check.unreducible => return {nosig}")


_REPORTED = "Combined.reported (first.factor + sumFactors rest) first.dim"


# ---- witness preamble + body. The spec is a `method` CONTRACT over a fully
# ---- transparent carrier, so a witness reaches it through Velvet's tester
# ---- machinery: `combineAddendsTester first rest = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped, so no
# ---- tactic script can mask the verdict. The loop-free rival's extracted
# ---- program reduces under `decide`; gold's loop stays stuck, so the same
# ---- witness FAILS on gold — the required discrimination. No binder, so no
# ---- consistency probe is needed.
def _witness(inp: str) -> str:
    return (
        "extract_program_for combineAddends\n"
        "prove_precondition_decidable_for combineAddends\n"
        "prove_postcondition_decidable_for combineAddends\n"
        "derive_tester_for combineAddends\n\n"
        f"example : combineAddendsTester {inp} = false := by decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `combineSpec first rest` is GROUNDED in the inputs
    # (a total fold over the actual addends), so `return combineSpec first rest`
    # is a correct fully-grounded implementation, not an ungrounded-oracle echo.
    # The loop is gone, so the frozen proof body's loop reasoning is unneeded and
    # the residual `ensures` close under `loom_solve` + a `combineSpec` unfold.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _rival("    return combineSpec first rest"),
            _PROOF,
            "prove_correct combineAddends by\n"
            "  loom_solve <;> intro h <;> simp only [combineSpec] <;> simp_all"),
        "rationale": "the master clause is literally `out = combineSpec first "
                     "rest` and `combineSpec` is GROUNDED in the inputs (a total "
                     "fold), so `return combineSpec first rest` is the honest "
                     "cheapest CORRECT impl. It MUST verify, else C1 is "
                     "SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable: "
                     "any wrong constant would fail `out = combineSpec first rest`.",
    },
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that keeps the frozen backward loop and its invariants BYTE-IDENTICAL, only
    # swapping the ORDER of the two independent accumulator updates inside the
    # loop body (factor before the check accumulator). Both updates read only
    # pre-step values and write distinct locals, so the step is semantically
    # identical and every loop invariant plus all four `ensures` still discharge
    # under the frozen proof script with NO retune. A faithful reshape that could
    # not verify would mean the postcondition is over-fit to one statement ORDER
    # => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "      chk := checkStep first.dim.deps a chk\n"
            "      factor := factor + a.factor\n",
            "      factor := factor + a.factor\n"
            "      chk := checkStep first.dim.deps a chk\n"),
        "rationale": "structurally different CORRECT reshape: the two independent "
                     "accumulator updates (the three-valued check, the factor sum) "
                     "are reordered inside the loop body, each reading only "
                     "pre-step values, keeping every loop invariant byte-identical "
                     "so all four `ensures` discharge under the frozen proof. A "
                     "faithful reshape MUST verify, else the clause is over-fit to "
                     "the statement ORDER => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a CORRECT reshape that is NOT the frozen
    # impl's control-flow shape at all. The frozen impl carries ONE loop that
    # advances BOTH accumulators together; this one SPLITS the work into two
    # independent backward loops with two independent termination measures — the
    # first computing only the three-valued check, the second only the factor
    # total — so each loop carries just one value invariant and the final
    # decision reads two locals produced by different loops. Nothing in the spec
    # ties the two accumulations to a single traversal, and a spec that rejected
    # this would be over-fit to the number of passes the frozen impl makes =>
    # SPEC-TOO-STRONG. Verified to build (exit 0).
    #
    # (This replaces an earlier forward-`take` control, which could not be
    # shipped: its proof needs a three-valued append lemma whose STATEMENT
    # contains a `match`, and stating one inside the `prove_correct` tactic block
    # crashes the elaborator — measured, `error: not a triple:
    # _inhabitedExprDummy` plus a `Lean.SMap.find!` PANIC. A tooling limit, not a
    # spec fact, so the lane is kept with a different genuine reshape rather than
    # dropped.)
    # =====================================================================
    {
        "id": "pos-control-two-loops",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _rival(
                "    let mut chk : Check := Check.equivalent\n"
                "    let mut i := rest.length\n"
                "    while i > 0\n"
                "      invariant 0 ≤ i ∧ i ≤ rest.length\n"
                "      invariant chk = checkAddends first.dim.deps (rest.drop i)\n"
                "      done_with i = 0\n"
                "      decreasing i\n"
                "    do\n"
                "      chk := checkStep first.dim.deps rest[i - 1]! chk\n"
                "      i := i - 1\n"
                "    let mut factor := first.factor\n"
                "    let mut k := rest.length\n"
                "    while k > 0\n"
                "      invariant 0 ≤ k ∧ k ≤ rest.length\n"
                "      invariant factor = first.factor + sumFactors (rest.drop k)\n"
                "      done_with k = 0\n"
                "      decreasing k\n"
                "    do\n"
                "      factor := factor + rest[k - 1]!.factor\n"
                "      k := k - 1\n"
                "    match chk with\n"
                "    | Check.equivalent  => return Combined.reported factor first.dim\n"
                "    | Check.disagreeing => return Combined.disagreement\n"
                "    | Check.unreducible => return Combined.noSignature"),
            _PROOF,
            "prove_correct combineAddends by\n"
            "  loom_solve\n"
            "  · rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,\n"
            "        ← invariant_2]\n"
            "  · rw [drop_cons_step rest k (by omega) (by omega), sumFactors_cons]\n"
            "    omega\n"
            "  all_goals (\n"
            "    subst done_1\n"
            "    subst done_2\n"
            "    simp only [List.drop_zero] at *\n"
            "    simp only [combineSpec] at *\n"
            "    simp_all)"),
        "rationale": "a CORRECT reshape with a different control-flow SHAPE: the "
                     "single fused traversal is split into two independent "
                     "backward loops with two separate termination measures, one "
                     "per accumulator, and the final decision combines locals "
                     "produced by different loops. MUST verify, else the clauses "
                     "are over-fit to the frozen impl's number of passes and to "
                     "the two accumulations sharing one traversal => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed, not dropped. The method declares no `require`, so
    # "a normal input satisfies the precondition" is not the risk; the residual
    # risk on a total carrier is the obligation being UNSATISFIABLE or DEGENERATE
    # at exactly an F2P-shaped input (a spec no impl can meet at the interesting
    # point reads exactly like one every impl meets). This case discharges, by
    # EVALUATION as an in-region `assert`, the post-image's value at the
    # F2P-shaped point — a surface-DISTINCT but deps-EQUIVALENT pair of addends,
    # the very shape the modeled change is about — and then closes the frozen
    # obligation with the impl and proof kept verbatim. So it attests two things
    # at once: the obligation is satisfiable at that point, and the value it
    # demands there is the COMBINED one (`Combined.reported 3 ⟨0, some 7⟩`), not
    # either value-less outcome. Liveness measured: the same case asserting
    # `= Combined.disagreement` at the same point FAILS (`decide` proved … is
    # false), so the assert is not a decoration.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-point",
        "kind": "admissibility",
        "expect": "verify",
        # The in-region `assert` adds ONE goal ahead of the frozen loop goals, so
        # the frozen tactic body gains exactly one leading bullet that discharges
        # it BY EVALUATION (`decide`) — the frozen bullets follow verbatim, in
        # order, closing the method's own four `ensures` as before. That is the
        # whole edit: nothing about the frozen obligation is retuned.
        "module": _swap(
            _swap(
                _BASE,
                "    -- impl-start\n",
                "    -- impl-start\n"
                "    assert (with_name_prefix `assert\n"
                "      (combineSpec ⟨1, ⟨0, some 7⟩⟩ [⟨2, ⟨1, some 7⟩⟩] "
                "= Combined.reported 3 ⟨0, some 7⟩))\n"),
            "  loom_solve\n",
            "  loom_solve\n"
            "  · -- the post-image is satisfiable and non-degenerate at this point\n"
            "    decide\n"),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at an "
                     "F2P-shaped input. At first=(factor 1, surf 0, deps 7) and "
                     "rest=[(factor 2, surf 1, deps 7)] — surface-distinct, "
                     "dimensionally equivalent — the post-image is "
                     "`Combined.reported 3 ⟨0, some 7⟩`: the summed factor paired "
                     "with the REFERENCE dimension, not either value-less "
                     "outcome. The in-region assert must discharge by evaluation "
                     "(else the obligation is unsatisfiable or degenerate at the "
                     "point the change is about => PRECOND-TOO-STRONG in its "
                     "total-carrier form), with the impl and frozen proof kept "
                     "verbatim so the method's own four `ensures` still discharge "
                     "alongside it.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- THE DISCRIMINATING RIVAL: decide on the SURFACE identity (the prepatch
    # ---- bug). Accept iff every addend's dimension is written the SAME WAY
    # ---- (`surf` equal) instead of dimensionally EQUIVALENT (`deps` equal).
    # ---- Because a surface-distinct addend can be equivalent, this wrongly
    # ---- REJECTS an all-equivalent sum, violating C2.
    {
        "id": "rival-surface-identity-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    if rest.all (fun a => a.dim.surf == first.dim.surf) then\n"
            f"      return {_REPORTED}\n"
            "    else\n"
            "      return Combined.disagreement"),
        "refinement": "its faithful real patch is the PRE-PATCH surface comparison "
                      "(structural equality of the dimension expressions). On the "
                      "F2P input (an acceleration*time addend summed with a "
                      "velocity addend — surface-distinct, dimensionally "
                      "equivalent) it reports a dimensional disagreement instead of "
                      "combining them, so it does NOT resolve.",
        "rationale": "REJECT from C2 (equivalent → reported): the rival decides on "
                     "`surf`, so on an addend that is surface-distinct but "
                     "deps-equivalent it reports a disagreement while "
                     "`checkAddends` is `equivalent` and the spec demands "
                     "`Combined.reported`. Refuted at first.dim=(surf 0, deps 7), "
                     "rest=[(surf 1, deps 7)] — equal deps, distinct surf. If it "
                     "verified ⇒ SPEC-TOO-WEAK (surface not distinguished from "
                     "equivalence).",
        "witness": _witness(
            "(⟨1, ⟨0, some 7⟩⟩ : Addend) ([⟨2, ⟨1, some 7⟩⟩] : List Addend)"),
    },

    # ---- PARTIAL-DOMAIN RIVAL: skip the first compared addend. Correct on most
    # ---- inputs but never inspects rest[0], so an inequivalent rest[0] followed
    # ---- by equivalent addends is wrongly ACCEPTED (C3 violated).
    {
        "id": "rival-skip-first-addend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_decide(_REPORTED, arg="first.dim.deps (rest.drop 1)")),
        "refinement": "its faithful real patch starts the addend comparison one "
                      "element late (skipping the first remaining addend). On a sum "
                      "whose first remaining addend is dimensionally incompatible "
                      "but later addends match the reference, it silently accepts a "
                      "wrong-dimension sum the consistency tests require to be "
                      "rejected, so it does NOT resolve.",
        "rationale": "REJECT from C3 (disagreeing → disagreement): dropping rest[0] "
                     "leaves the equivalence check blind to that addend, so a sum "
                     "with an inequivalent rest[0] and equivalent tail reports a "
                     "combined value while `checkAddends` is `disagreeing` and the "
                     "spec demands `Combined.disagreement`. Refuted at "
                     "first.dim.deps 5, rest=[(deps 9), (deps 5)]: rest[0] "
                     "mismatches the reference but the rival ignores it. Varies "
                     "`first` and `rest` to a length-2 list where element ORDER "
                     "matters. If it verified ⇒ SPEC-TOO-WEAK (partial domain).",
        "witness": _witness(
            "(⟨4, ⟨3, some 5⟩⟩ : Addend) "
            "([⟨2, ⟨0, some 9⟩⟩, ⟨3, ⟨0, some 5⟩⟩] : List Addend)"),
    },

    # ---- CONTROL-FLOW-EFFECT RIVAL: never reject (always accept). Strips the
    # ---- equivalence guard entirely and always reports a value. The
    # ---- reported/value-less distinction is the changed observable (C3, C4).
    {
        "id": "rival-never-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(f"    return {_REPORTED}"),
        "refinement": "its faithful real patch removes the dimension-compatibility "
                      "guard, accepting any sum regardless of dimensions. The "
                      "consistency tests that assert a dimensional disagreement IS "
                      "signalled on dimensionally-inconsistent sums would fail, so "
                      "it does NOT resolve.",
        "rationale": "REJECT from C3 (disagreeing → disagreement): with no guard the "
                     "rival reports a value even when some addend is inequivalent, "
                     "so on `checkAddends = disagreeing` it reports while the spec "
                     "demands `Combined.disagreement`. Refuted at first.dim.deps 3, "
                     "rest=[(deps 9)]: the rival accepts, `combineSpec` reports the "
                     "disagreement. Varies `first`. If it verified ⇒ SPEC-TOO-WEAK "
                     "(the signalled-disagreement effect dropped).",
        "witness": _witness(
            "(⟨7, ⟨2, some 3⟩⟩ : Addend) ([⟨2, ⟨0, some 9⟩⟩] : List Addend)"),
    },

    # ---- VALUE RIVAL (C2, factor component): correct three-way decision but
    # ---- reports a constant scale factor (0) instead of the total of the
    # ---- addends' factors.
    {
        "id": "rival-wrong-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_decide("Combined.reported 0 first.dim")),
        "refinement": "reporting a constant scale factor instead of the sum of the "
                      "addends' factors hands the caller the wrong accumulated "
                      "factor for the whole sum; every downstream numeric consumer "
                      "sees a corrupted factor, so the factor-and-dimension tests "
                      "would fail and it does NOT resolve.",
        "rationale": "REJECT from C2 (value): the rival's three-way decision "
                     "matches gold, but the reported factor is the constant 0, so "
                     "`out = Combined.reported 0 …` while the spec demands "
                     "`Combined.reported (first.factor + sumFactors rest) …`. "
                     "Refuted at first.factor=5, rest=[factor 6] (both equivalent): "
                     "the rival reports 0, `combineSpec` reports 11. Varies `first` "
                     "and exercises `first.factor` and `sumFactors rest`. If it "
                     "verified ⇒ SPEC-TOO-WEAK (factor component unpinned).",
        "witness": _witness(
            "(⟨5, ⟨4, some 2⟩⟩ : Addend) ([⟨6, ⟨4, some 2⟩⟩] : List Addend)"),
    },

    # ---- VALUE RIVAL (C2, dimension component): correct three-way decision and
    # ---- correct factor, but reports the FIRST remaining addend's dimension
    # ---- instead of the reference (first) addend's. Observable only when the two
    # ---- are deps-equivalent (so the sum is accepted) yet surface-distinct.
    {
        "id": "rival-wrong-dim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_decide(
            "Combined.reported (first.factor + sumFactors rest) "
            "(rest.getD 0 first).dim")),
        "refinement": "reporting a remaining addend's dimension in place of the "
                      "reference addend's yields a dimension with a different "
                      "surface expression for the sum; the factor-and-dimension "
                      "tests that assert the exact reported dimension would fail, "
                      "so it does NOT resolve.",
        "rationale": "REJECT from C2 (dimension component): the rival reports "
                     "`(rest[0]).dim` rather than `first.dim`. When rest[0] is "
                     "deps-equivalent to first (so the sum is accepted) but "
                     "surface-distinct, the two dimensions differ, so `out = "
                     "Combined.reported … rest[0].dim` while the spec demands "
                     "`Combined.reported … first.dim`. Refuted at "
                     "first.dim=(surf 6, deps 4), rest=[(surf 9, deps 4)] — equal "
                     "deps, distinct surf. Varies `first` and exercises `first.dim` "
                     "vs a rest dim that is equivalent but surface-distinct. If it "
                     "verified ⇒ SPEC-TOO-WEAK (reference dimension unpinned).",
        "witness": _witness(
            "(⟨8, ⟨6, some 4⟩⟩ : Addend) ([⟨5, ⟨9, some 4⟩⟩] : List Addend)"),
    },

    # ---- VALUE RIVAL (C2, dimension component — the OTHER facet): correct
    # ---- three-way decision and correct factor, and it reports a dimension
    # ---- with the RIGHT signature, but it SYNTHESISES the reported dimension
    # ---- from the signature (`⟨deps, deps⟩`) instead of handing back the
    # ---- reference addend's dimension. Aimed at what the other two value rivals
    # ---- leave unattacked: `rival-wrong-dim` swaps in ANOTHER addend's whole
    # ---- dimension, so both rivals could be defeated by a spec that pinned only
    # ---- the reported `deps`. This one agrees on `deps` everywhere and differs
    # ---- ONLY in `surf`, so it separates the two facets of the reported
    # ---- dimension and shows C2 pins the reference dimension as a WHOLE.
    {
        "id": "rival-synthesised-dim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_decide(
            "Combined.reported (first.factor + sumFactors rest) "
            "⟨first.dim.deps.getD 0, first.dim.deps⟩")),
        "refinement": "its faithful real patch reports a dimension REBUILT from "
                      "the canonical signature rather than the reference addend's "
                      "own dimension. Downstream consumers that compare the "
                      "reported dimension against the expected one see a "
                      "different expression for the sum even though it reduces "
                      "the same way, so the factor-and-dimension tests asserting "
                      "the exact reported dimension fail: it does NOT resolve.",
        "rationale": "REJECT from C2 (dimension component, surface facet): the "
                     "rival's decision, factor and reported SIGNATURE all agree "
                     "with the spec, and it differs only in the reported "
                     "dimension's `surf`. So `out = Combined.reported … "
                     "⟨deps, deps⟩` while the spec demands `Combined.reported … "
                     "first.dim`. Refuted at first.dim=(surf 6, deps 4), "
                     "rest=[(surf 9, deps 4)]: the reference dim is ⟨6, some 4⟩ "
                     "and the rival reports ⟨4, 4⟩. Distinct from "
                     "`rival-wrong-dim`, which substitutes another addend's WHOLE "
                     "dimension: together they show C2 pins the reference "
                     "dimension as a whole and not merely its signature. If it "
                     "verified ⇒ SPEC-TOO-WEAK (the reported dimension's surface "
                     "facet unpinned).",
        "witness": _witness(
            "(⟨8, ⟨6, some 4⟩⟩ : Addend) ([⟨5, ⟨9, some 4⟩⟩] : List Addend)"),
    },

    # ---- SIGNATURE-PARTIALITY RIVAL: treat a MISSING signature as a wildcard
    # ---- that matches anything. Correct on every dimension that HAS a signature
    # ---- (so no amount of spreading witnesses over the ordinary equivalent /
    # ---- inequivalent classes separates it from gold), and wrong exactly where
    # ---- the reference dimension admits no signature at all: there the rival
    # ---- ACCEPTS and reports a combined value, while the equivalence test
    # ---- cannot be carried out and no value may be reported. This is the rival
    # ---- the PARTIALITY of `deps` exists to reject; if it verified, that leg
    # ---- would be decoration and the spec would be back to pinning only the
    # ---- total sub-domain.
    {
        "id": "rival-missing-signature-wildcard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    if rest.all (fun a => first.dim.deps.isNone "
            "|| a.dim.deps == first.dim.deps) then\n"
            f"      return {_REPORTED}\n"
            "    else\n"
            "      return Combined.disagreement"),
        "refinement": "its faithful real patch treats a dimension that cannot be "
                      "reduced to base-dimension powers as compatible with every "
                      "addend instead of letting the failed reduction abandon the "
                      "combination. On a sum whose reference dimension admits no "
                      "signature it hands back a combined (factor, dimension) "
                      "where the real routine reports no value at all, so a "
                      "consumer that relies on the failure being signalled sees a "
                      "silently fabricated result: it does NOT resolve.",
        "rationale": "REJECT from C4 (unreducible → noSignature): when the "
                     "reference signature is ABSENT the equivalence test cannot "
                     "run, so the spec demands `Combined.noSignature` no matter "
                     "what the addends look like. The rival short-circuits that "
                     "case to acceptance and reports a value. Refuted at "
                     "first.dim=(surf 0, deps none), rest=[(surf 1, deps none)]: "
                     "the rival accepts and reports a value, `combineSpec` yields "
                     "`Combined.noSignature`. Exercises the `deps` carrier's "
                     "ABSENT case, which the value rivals leave untouched (all of "
                     "them use a present signature). If it verified ⇒ "
                     "SPEC-TOO-WEAK (the signature-partiality leg unpinned).",
        "witness": _witness(
            "(⟨1, ⟨0, none⟩⟩ : Addend) ([⟨2, ⟨1, none⟩⟩] : List Addend)"),
    },

    # ---- OUTCOME-IDENTITY RIVAL 1 (C4): the two value-less outcomes COLLAPSED
    # ---- onto the disagreement report. The rival gets every reported value
    # ---- right, gets the reject/accept DECISION right everywhere, and gets the
    # ---- disagreement case right; it is wrong only in WHICH value-less outcome
    # ---- it hands back where the equivalence test could not run at all. This is
    # ---- the rival a result carrier with a SINGLE value-less inhabitant cannot
    # ---- see: under such a carrier this impl and gold are literally the same
    # ---- function, so the choice between the two rejections would be free and
    # ---- the spec would admit an impl that reports "these dimensions disagree"
    # ---- about a pair it never compared. C4 is what closes that.
    {
        "id": "rival-collapse-to-disagreement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_decide(
            "Combined.reported (first.factor + sumFactors rest) first.dim",
            nosig="Combined.disagreement")),
        "refinement": "its faithful real patch answers a sum whose dimension "
                      "admits no base-power signature by signalling a dimensional "
                      "DISAGREEMENT — the same report it gives for two dimensions "
                      "it compared and found different — instead of letting the "
                      "failed reduction abandon the combination in its own way. "
                      "The sums whose dimensions genuinely disagree are exactly "
                      "the ones the consistency checks probe, and they probe them "
                      "by the kind of failure reported, so a routine that reports "
                      "a disagreement it never established mislabels a whole "
                      "class of sums: the consistency tests see the "
                      "disagreement signal where they must see none, and it does "
                      "NOT resolve.",
        "rationale": "REJECT from C4 (unreducible → noSignature): the rival maps "
                     "the unreducible case onto `Combined.disagreement`, so on an "
                     "input where `checkAddends` is `unreducible` it yields the "
                     "disagreement report while the spec demands "
                     "`Combined.noSignature`. Refuted at first.dim=(surf 0, deps "
                     "none), rest=[(surf 1, deps 7)]: the reference has no "
                     "signature, so no comparison happens; the rival nevertheless "
                     "claims a disagreement. Every other rival keeps the two "
                     "value-less outcomes distinct, so this one is the only case "
                     "that tests C4's SEPARATION rather than the reject decision. "
                     "If it verified ⇒ SPEC-TOO-WEAK (the identity of the "
                     "value-less outcome unpinned, i.e. one inhabitant spent on "
                     "two observably different rejections).",
        "witness": _witness(
            "(⟨1, ⟨0, none⟩⟩ : Addend) ([⟨2, ⟨1, some 7⟩⟩] : List Addend)"),
    },

    # ---- OUTCOME-IDENTITY RIVAL 2 (C3): the collapse the OTHER way. Both
    # ---- value-less outcomes are reported as the signature-less one, so a sum
    # ---- whose dimensions were compared and found different is answered as
    # ---- though nothing was ever compared. Shipped alongside rival 1 because a
    # ---- spec could pin one direction and leave the other free: a clause saying
    # ---- only "unreducible ⇒ noSignature" would reject rival 1 and ADMIT this
    # ---- one. Both directions must be pinned, so both are attacked.
    {
        "id": "rival-collapse-to-nosignature",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_decide(
            "Combined.reported (first.factor + sumFactors rest) first.dim",
            disagree="Combined.noSignature")),
        "refinement": "its faithful real patch answers a genuinely "
                      "dimensionally-inconsistent sum — two dimensions it reduced "
                      "and compared and found different — the way it answers a "
                      "sum it could not reduce at all, abandoning the combination "
                      "without reporting the disagreement it established. The "
                      "consistency checks that assert a dimensional-disagreement "
                      "IS signalled for inconsistent sums therefore see the wrong "
                      "kind of failure, and it does NOT resolve.",
        "rationale": "REJECT from C3 (disagreeing → disagreement): the rival maps "
                     "the disagreeing case onto `Combined.noSignature`, so on an "
                     "input where the test RAN and returned 'not equivalent' it "
                     "yields the signature-less outcome while the spec demands "
                     "`Combined.disagreement`. Refuted at first.dim=(surf 0, deps "
                     "3), rest=[(surf 1, deps 9)]: both signatures present and "
                     "different, so a disagreement was genuinely established. "
                     "Together with `rival-collapse-to-disagreement` this shows "
                     "the spec pins BOTH directions of the separation, not just "
                     "one. If it verified ⇒ SPEC-TOO-WEAK (the established "
                     "disagreement is not a required observation).",
        "witness": _witness(
            "(⟨1, ⟨0, some 3⟩⟩ : Addend) ([⟨2, ⟨1, some 9⟩⟩] : List Addend)"),
    },

    # ---- OUTCOME-IDENTITY RIVAL 3 (C3 + C4 jointly, the TIE-BREAK): keep both
    # ---- value-less outcomes and never confuse them — but decide between them by
    # ---- SCANNING for a disagreement anywhere first, rather than by which
    # ---- addend fails FIRST. On a list where an earlier addend has no signature
    # ---- and a later one disagrees, the real routine never reaches the later
    # ---- addend at all (the reduction on the earlier one abandons the
    # ---- combination), while this rival reports the disagreement it found by
    # ---- looking ahead. This is the rival that survives a spec which splits the
    # ---- two rejections but leaves their PRIORITY free, so it is the case that
    # ---- pins `checkStep`'s leftmost-failure ordering rather than merely the
    # ---- existence of two outcomes.
    {
        "id": "rival-priority-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    if rest.any (fun a => first.dim.deps.isSome "
            "&& a.dim.deps.isSome && a.dim.deps != first.dim.deps) then\n"
            "      return Combined.disagreement\n"
            "    else if rest.any (fun a => first.dim.deps.isNone "
            "|| a.dim.deps.isNone) then\n"
            "      return Combined.noSignature\n"
            "    else\n"
            f"      return {_REPORTED}"),
        "refinement": "its faithful real patch scans the whole sum for a pair of "
                      "dimensions that disagree before considering whether some "
                      "addend could be reduced at all, so it reports a "
                      "disagreement found in a LATER addend for a sum whose "
                      "combination the real routine abandons at an EARLIER one. "
                      "The real routine walks the addends in order and stops at "
                      "the first one it cannot carry through, so on such a sum it "
                      "reports the abandoning failure and not the disagreement; "
                      "the rival reports the disagreement. A consumer grading the "
                      "kind of failure sees the wrong one, so it does NOT resolve.",
        "rationale": "REJECT from C4 (unreducible → noSignature): `checkStep` "
                     "attempts the reduction on the reference and on the addend "
                     "BEFORE any comparison, so the leftmost non-certified addend "
                     "decides the outcome in the manner in which IT failed, and a "
                     "later disagreement cannot override an earlier missing "
                     "signature. The rival inverts that priority. Refuted at "
                     "first.dim=(surf 0, deps 3), rest=[(surf 1, deps none), "
                     "(surf 1, deps 9)]: the first remaining addend has no "
                     "signature (so `checkAddends` is `unreducible` and the spec "
                     "demands `Combined.noSignature`) while the second disagrees, "
                     "which is what the rival reports. Distinct from the two "
                     "collapse rivals: this one keeps both outcomes and gets each "
                     "SEPARATELY reachable case right, differing only in the "
                     "ORDER in which the addends' failures are resolved — so it "
                     "is the case that pins the tie-break rather than the split. "
                     "Uses a length-2 `rest` where element ORDER decides the "
                     "answer. If it verified ⇒ SPEC-TOO-WEAK (the ordering "
                     "between the two rejections unpinned).",
        "witness": _witness(
            "(⟨1, ⟨0, some 3⟩⟩ : Addend) "
            "([⟨2, ⟨1, none⟩⟩, ⟨3, ⟨1, some 9⟩⟩] : List Addend)"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The nagini sibling has 9 SPEC cases (2 soundness,
# 1 admissibility, 6 uniqueness) plus a 3-case AXIOM lane. This bundle models the
# SAME purely-functional core — combining a sum's addends into one (factor,
# dimension) or reporting one of the two distinct failures — over a transparent
# carrier (`Dim` = a surface key plus an OPTIONAL signature key; the
# three-constructor `Combined`), so the positive controls and the value /
# partial-domain rivals port near 1:1; the frame and admissibility cases are
# genuinely vacuous, divergence is CLOSED BY THE SEMANTICS and NOT a spec hole,
# two value rivals are added to pin the two components of C2's reported pair
# separately, and three OUTCOME-IDENTITY rivals are added to pin C3/C4 — the
# clauses keeping the two value-less outcomes apart and ordered.
#
#   nagini case                          -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-control-symmetric-guard          -> pos-control-reorder          RE-EXPRESSED
#   pos-control-local-ref                -> pos-control-direct           RE-EXPRESSED
#   admiss-f2p-shaped-caller             -> admiss-f2p-shaped-point       RE-AIMED
#   rival-surface-identity-guard         -> rival-surface-identity-guard PORTED
#   rival-skip-index-1                   -> rival-skip-first-addend       PORTED
#   rival-never-raise                    -> rival-never-reject            PORTED
#   frame-mutation-overwrite-red         -> (none)                       VACUOUS
#   frame-mutation-overwrite-surf        -> (none)                       VACUOUS
#   rival-vacuous-nonterminating-loop    -> (none)          DEMONSTRATED-BY-PROBE
#   rival-wrong-return-constant          -> rival-wrong-factor           RE-EXPRESSED
#   (no sibling)                         -> rival-wrong-dim               ADDED
#   (no sibling)                         -> rival-synthesised-dim         ADDED
#   (no sibling)                         -> rival-missing-signature-wildcard ADDED
#   (no sibling)                         -> pos-control-two-loops         ADDED
#   (no sibling)                         -> rival-collapse-to-disagreement ADDED
#   (no sibling)                         -> rival-collapse-to-nosignature  ADDED
#   (no sibling)                         -> rival-priority-inverted        ADDED
#   AXIOM_TESTS (3)                      -> (none)                       DROPPED (G-AX)
#
# 3 ported, 3 re-expressed, 1 re-aimed, 7 added, 2 vacuous, 1 demonstrated by
# probe, 3 dropped = 14 velvet cases (3 soundness, 1 admissibility, 10
# uniqueness). NONE of the nagini uniqueness rivals whose class is expressible is
# dropped, and no reject case from an earlier revision of this battery is dropped
# or weakened: every one of the seven is still here, attacking the same clause it
# attacked before, at the same input point.
#
# AUDIT REVISION 1 (independent re-derivation, real builds). Four corrections to
# the port's own account, each measured rather than argued:
#   1. The port claimed this bundle sets `loom.semantics.termination "partial"`.
#      It sets "total" (Solution.lean line 4). The divergence class is therefore
#      CLOSED by the spec, not a hole — measured directly (a measure-free loop
#      fails with "Decreasing annotations are required in total correctness
#      semantics"). The disposition is now DEMONSTRATED-BY-PROBE.
#   2. The port claimed each witness fails against the FROZEN solution and that
#      this is the discrimination. It does fail there, but by STUCK REDUCTION,
#      which carries no information about the claim — the flipped-claim forgery
#      fails identically. The gate does not accept that; it falls back to a
#      verifying positive of this spec, and against THAT subject the refutation
#      is a plain evaluation and does track the claim. The docstring now states
#      the subject the attestation actually rests on.
#   3. The admissibility lane was recorded VACUOUS because the method has no
#      `require`. That is not a sufficient reason: the total-carrier analogue is
#      the obligation being unsatisfiable or degenerate at an F2P-shaped input,
#      which is expressible here and is now shipped as `admiss-f2p-shaped-point`
#      (liveness measured against the opposite claim at the same point).
#   4. The two soundness positives were both definitionally near the frozen impl
#      (a statement reorder; the grounded fold itself), so neither re-derived the
#      `ensures` from a different traversal.
#
# AUDIT REVISION 2 (adversarial audit found a verifying wrong impl; the spec was
# strengthened and this battery follows it). The defect the audit exposed was in
# the RESULT CARRIER, not in any case here: the result had a single value-less
# inhabitant, so the two observably different failures of the modeled step — the
# equivalence test running and returning "not equivalent", versus the test not
# running at all because the reduction it is built on fails first — were the SAME
# post-image. An impl that always reported the wrong one of the two therefore
# satisfied every clause byte-for-byte while being observably different from the
# real routine. No case in this battery could have caught it: all seven reject
# rivals differed from gold in the accept/reject DECISION or in a reported VALUE,
# and this one differs in neither. The carrier is now three-valued (`Check` /
# `Combined`), the contract carries a clause per outcome (C2/C3/C4), and three
# new reject rivals aim at exactly the freedom that was there:
#   * `rival-collapse-to-disagreement` — the audit's class: report the
#     disagreement where no comparison ever happened;
#   * `rival-collapse-to-nosignature` — the same collapse the OTHER way, so a
#     clause pinning only one direction cannot pass this battery;
#   * `rival-priority-inverted` — keeps both outcomes and confuses neither, and is
#     wrong only about WHICH addend's failure decides, so it survives any spec
#     that splits the outcomes without ordering them.
# Case 4 of revision 1 is also settled here: `pos-control-two-loops` re-derives
# the `ensures` from a genuinely different control-flow shape (two independent
# traversals, two measures, one value invariant each). The forward-`take` reshape
# that revision 1 shipped for this purpose CANNOT be expressed under the
# three-valued accumulator: its proof needs an append lemma whose STATEMENT
# contains a `match` on the accumulator, and stating one inside the
# `prove_correct` tactic block crashes the elaborator (measured: `error: not a
# triple: _inhabitedExprDummy` plus a `Lean.SMap.find!` PANIC). That is a tooling
# limit, so the lane is kept with a different genuine reshape rather than dropped.
# The strengthened spec survived both probe directions with real builds: the three
# new wrong impls are each REJECTED and each refutable at a concrete input, the
# seven pre-existing rivals are still each REJECTED and still refutable at their
# original input points, and three correct impls (the grounded fold; the
# accumulator-update reorder under the byte-identical frozen proof; the two-loop
# split) all VERIFY.
#
# RE-EXPRESSED (pos-control-symmetric-guard -> pos-control-reorder): nagini swaps
#   the argument order of the symmetric equivalence guard; here the analogous
#   behaviour-preserving reshape swaps the ORDER of the two independent
#   accumulator updates in the loop body (each reads only pre-step values),
#   keeping every loop invariant byte-identical so the frozen proof closes with
#   no retune. Verified to build.
# RE-EXPRESSED (pos-control-local-ref -> pos-control-direct): nagini snapshots the
#   reference into a local; here the cheapest honest impl returns the grounded
#   fold `combineSpec first rest` directly. The loop is gone, so the frozen proof
#   is retuned to close the residual `ensures` under `loom_solve` + a `combineSpec`
#   unfold. Verified to build.
# PORTED (surface-identity-guard, skip-first-addend, never-reject): the central
#   discriminator (decide on `surf` not `deps`), the partial-domain skip (never
#   inspect the first remaining addend), and the control-flow-effect strip (never
#   report a disagreement) re-express DIRECTLY onto C2 / C3. Each refinement
#   argument carries over: the surface guard is the exact prepatch bug the issue
#   reports; the skip and never-reject accept a dimensionally-inconsistent sum the
#   consistency tests require rejected. All three witnesses verified to
#   discriminate (rival exit 0, gold exit ≠ 0, full rival non-verify).
# RE-EXPRESSED (rival-wrong-return-constant -> rival-wrong-factor): nagini returns
#   a constant unrelated to the reference dimension. Here the reported result
#   carries two components, so the constant-return attack is split:
#   rival-wrong-factor pins the FACTOR component (reports 0), rival-wrong-dim
#   (ADDED) pins the DIMENSION component (reports a rest addend's
#   surface-distinct dimension). Together they attack C2's reported components the
#   way the single nagini rival attacked its scalar return, at two distinct input
#   points. Both witnesses verified to discriminate.
# ADDED (rival-wrong-dim): the reported dimension must be the FIRST addend's, not
#   an equivalent-but-surface-distinct addend's — a genuine near-miss (correct
#   three-way decision and correct factor, wrong reported dimension) observable
#   only on the surface-distinct-but-equivalent sub-domain, the same discriminator
#   the central rival attacks from the accept/reject side.
# ADDED (rival-collapse-to-disagreement, rival-collapse-to-nosignature,
#   rival-priority-inverted): the outcome-identity lane, see AUDIT REVISION 2.
#   These are the only cases in the battery whose rival agrees with gold on every
#   reported VALUE and on every accept/reject DECISION; they differ solely in
#   WHICH value-less outcome is produced, or in which addend's failure decides it.
# RE-AIMED (admiss-f2p-shaped-caller -> admiss-f2p-shaped-point): the method
#   declares NO `require`, so the nagini "a normal input satisfies the
#   precondition" probe has no precondition to aim at — but that alone does NOT
#   make the lane vacuous. The total-carrier analogue is the obligation being
#   unsatisfiable or DEGENERATE at an F2P-shaped input, which is expressible here:
#   the shipped case discharges the post-image's value by evaluation, as an
#   in-region `assert`, at the surface-distinct-but-equivalent point the modeled
#   change is about, with the impl and frozen proof kept verbatim. Its liveness is
#   measured: the same assert with the opposite claim (`= Combined.disagreement`)
#   at the same point FAILS, so a false claim there does not pass.
# VACUOUS (frame-mutation-overwrite-red / -surf): nagini carries these MANDATORY
#   because `red`/`surf` are held at Acc(list_pred(_), 1/2) and a rival can store
#   into them. Velvet is referentially transparent and declares no `mut` binder —
#   `first`/`rest` are immutable values with no heap footprint — so there is no
#   read-only input to overwrite and no substitute probe. Not fabricated.
# DEMONSTRATED-BY-PROBE (rival-vacuous-nonterminating-loop): this bundle sets
#   `loom.semantics.termination "total"`, so the verifier discharges a termination
#   obligation and a diverging impl is genuinely REJECTED — measured with a real
#   build of a measure-free loop, which fails at "Decreasing annotations are
#   required in total correctness semantics". The class is closed by the spec, so
#   there is no hole to record. It is not shippable as a reject CASE for a tooling
#   reason: the rival is rejected before its extracted program exists, so the
#   witness build fails on the RIVAL side (`witness-unproven`, an inconclusive
#   outcome that fails the gate) rather than discriminating. The property is
#   established by the probe instead.
# DROPPED (AXIOM_TESTS x3): the axiom lane is G-AX's job (axiom_check.py validates
#   the deep A-reference `checkStep` == the real `equivalent_dims` /
#   `get_dimensional_dependencies`); this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Input binders: `first : Addend` (fields `factor`,
#   `dim.surf`, `dim.deps`) and `rest : List Addend` (elements' `factor` /
#   `dim.surf` / `dim.deps`, plus length and order). The ten reject witnesses
#   probe EIGHT distinct input points and vary every sub-binder. The variation is
#   MEANINGFUL rather than several spellings of one point: each point changes the
#   spec's own verdict or the value it demands — three points make `checkAddends`
#   `equivalent`, three make it `disagreeing`, and two make it `unreducible`
#   (one of those two with a `rest` whose LATER element disagrees, so the
#   tie-break is what decides), so all three legs of the outcome are entered, and
#   the two surface-distinct-but-equivalent points are exactly where `surf` and
#   `deps` disagree (the whole content of the modeled change).
#     * `dim.deps` PRESENT (equivalence key)  — every rival; distinguished from
#                                           surf by surface-identity-guard /
#                                           wrong-dim / synthesised-dim.
#     * `dim.deps` ABSENT (partiality)   — missing-signature-wildcard (both sides
#                                           absent), collapse-to-disagreement
#                                           (reference absent, addend present),
#                                           priority-inverted (an absent addend
#                                           ahead of a disagreeing one).
#     * `dim.surf` (surface key)         — surface-identity-guard (differs from
#                                           rest), wrong-dim and synthesised-dim
#                                           (reported surf differs from the
#                                           reference's while deps agrees).
#     * `first.factor` / `sumFactors`    — wrong-factor.
#     * rest length / element ORDER      — skip-first-addend and
#                                           priority-inverted (length-2, order
#                                           decides the answer); others length 1.
#   Clause coverage: C2 (equivalent → reported) is attacked from the
#   accept/reject side (surface-identity-guard wrongly reports a disagreement),
#   the factor component (wrong-factor), and the dimension component from BOTH
#   facets — a substituted whole dimension (wrong-dim) and a dimension whose
#   signature is right but whose surface is synthesised (synthesised-dim), which
#   together show C2 pins the reference dimension as a whole rather than only its
#   signature; C3 (disagreeing → disagreement) is attacked by skip-first-addend
#   and never-reject (wrongly report a value) and by collapse-to-nosignature
#   (right decision, wrong value-less outcome); C4 (unreducible → noSignature) is
#   attacked by missing-signature-wildcard (wrongly reports a value),
#   collapse-to-disagreement (right decision, wrong value-less outcome) and
#   priority-inverted (right outcomes, wrong tie-break); C1 (the master `out =
#   combineSpec` conjunction) is attacked by all. The three positive controls
#   defend the whole obligation (one of them, two-loops, re-deriving it from a
#   different control-flow shape) and the admissibility positive pins the
#   post-image's value at the F2P-shaped point. `rival-wrong-dim` and
#   `rival-synthesised-dim` share an input point deliberately: they differ in
#   WHICH wrong dimension is reported there, which is the distinction being drawn.
# WITNESS DISCRIMINATION (re-derived with real builds against the CURRENT frozen
#   text, per reject case — see the docstring section "WHICH SUBJECT THE SECOND
#   HALF IS CHECKED AGAINST" for the measured exit codes). Each witness
#   ELABORATES against its loop-free rival (exit 0: the extracted program reduces
#   to a literal that differs from `combineSpec` at the probed input). The frozen
#   loop-solution cannot serve as the second subject — `decide` against its
#   extracted tester is STUCK for every claim, so its exit code carries no
#   information and a flipped-claim forgery fails there identically. The gate
#   detects that (`_STUCK_REDUCTION`) and refutes each witness against a VERIFYING
#   positive of this same spec instead, where the refutation is a plain EVALUATION
#   that tracks the claim (witness exit 1 with "`decide` proved … is false";
#   flipped claim exit 0). No witness binds a hypothesis (the carrier is fully
#   transparent), so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
AXIOM_TESTS = []
