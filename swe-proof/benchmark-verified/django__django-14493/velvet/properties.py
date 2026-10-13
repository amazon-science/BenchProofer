"""properties.py — G-PBT falsification battery for django__django-14493 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct passBudgetExceeded`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution — or, where the frozen solution cannot decide anything, against
the declared ``witness_reference``; see WITNESS SUBJECT below).

DEFENDED SURFACE (one contracted method):

  passBudgetExceeded (flags : List Bool) (limit : Nat) return (out : Bool)
    require limit ≤ flags.length
    ensures out = overBudget flags limit

A bounded sequence of refinement passes runs under a fixed budget ``limit``;
``flags[i]!`` records whether pass ``i`` still produced a change. The summary
observation returned after the whole sequence is: did the sequence run out of
its budget while changes were still happening? The grounded closed form is

    overBudget flags limit
      = decide (0 < limit) && settledThrough flags limit
      = decide (0 < limit) && decide (∀ j, j < limit → flags[j]! = true)

so it is TRUE exactly when the budget is positive AND every pass inside the
budget still reported a change. There is a single top-level ``ensures`` clause,
but ``overBudget`` composes TWO independent structural pieces, each its own
attack surface:
  (C1) the budget guard ``decide (0 < limit)`` — with a ZERO budget no pass
       runs and the value must be ``false`` (this is the whole issue: the
       zero-budget path must report a DEFINITE ``false``, never a stale value);
  (C2) the all-changed fold ``settledThrough flags limit`` (``∀ j < limit,
       flags[j]! = true``) — the value is ``true`` only if EVERY pass inside the
       budget still changed; the first change-free pass drives it ``false``.
The clause is grounded ENTIRELY in the two input binders ``flags`` and
``limit`` via the fully-decidable pure fold ``settledThrough`` — there is no
opaque oracle to echo (the ``axioms`` region is empty; ``overBudget`` /
``settledThrough`` COMPUTE the answer from the inputs). The unique satisfier IS
the grounded closed form, so ``decide`` reduces on concrete inputs and every
witness below is stated at concrete literals (no carrier conditioning needed).

ADVERSARIAL READ of the sibling's classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival writes back into a read-only input carrying only a
    fractional heap permission and is rejected for INSUFFICIENT PERMISSION.
    Lean and Velvet are referentially transparent: ``flags`` is an immutable
    value, this bundle declares no ``mut`` parameter, there is no heap and no
    aliasing. There is no read-only input to overwrite and no permission system
    to trip, so the class is vacuous. No substitute is fabricated. (See footer.)
  * UNGROUNDED-ORACLE ECHO — N/A. The clause is pinned to the grounded fold
    ``overBudget flags limit``, computed from the two inputs; there is no
    answer-key term a wrong impl could echo. The cheapest correct impl returns
    the closed form directly, which ``pos-direct`` covers honestly.
  * ADMISSIBILITY / PRECOND-TOO-STRONG — APPLIES, contrary to an earlier
    revision of this battery, which dropped the lane on the ground that the
    frozen obligation carries no interesting precondition. That is not a
    demonstration of vacuity. The analogue on a near-total carrier is the
    obligation being UNSATISFIABLE, or satisfiable only degenerately, at exactly
    an F2P-shaped input; ``admiss-f2p-satisfiable-nondegenerate`` discharges the
    obligation at that concrete input BY EVALUATION before closing the frozen
    obligation verbatim, and each of its six computed facts is load-bearing
    (negating any one breaks the build).
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface. The bug
    lives entirely in the zero-budget sub-domain: ``weak-ignore-budget`` is
    correct on every positive budget but reports a spurious ``true`` at
    ``limit = 0`` (the F2P discriminator). ``weak-ignore-settled`` is correct
    until the first change-free pass and diverges on the change-free sub-domain.
    ``weak-first-pass-only`` is a near-miss: correct for every budget ``≤ 1``
    but blind to any pass after the first, so it diverges only once a LATER pass
    settles under a budget ``≥ 2``.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
three witnesses sit at three DISTINCT input points and vary BOTH binders —
``([], 0)``, ``([false], 1)``, ``([true, false], 2)`` — so ``limit`` ranges over
{0, 1, 2} and ``flags`` over three shapes, and neither the budget guard C1 nor
the all-changed fold C2 is demonstrated at a single pinned point. The zero-budget
witness probes C1; the ``([false], 1)`` witness probes C2 at the first pass; the
``([true, false], 2)`` witness probes C2 at a LATER pass under a larger budget —
the multi-pass sub-domain no other rival isolates.

WITNESS SUBJECT — why every reject case names a ``witness_reference``. The frozen
impl carries a ``while`` loop, and under ``loom.semantics.choice "demonic"`` that
loop's fixpoint elaborates through ``Classical.choice``, which the kernel cannot
unfold. So ``decide`` against the FROZEN tester is stuck for EVERY claim, true or
false; measured here, the gold-side build reports

    Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse`.
    ... reduction got stuck at the `Decidable` instance

That is a failure the kernel never evaluated, so refuting a witness against gold
would attest to a refutation that was never performed (the gate reports this as
``witness-undecided`` and refuses the case — correctly, since a forged witness
asserting the rival is CORRECT would otherwise clear both halves). Every reject
case therefore names ``witness_reference = _LOOPFREE``: a loop-free impl of the
SAME frozen spec that returns the grounded closed form directly, shares the spec
(only the elided impl region differs), and VERIFIES. An impl the verifier accepts
cannot violate its own spec, so a genuine witness must still fail there — and all
three do, SEMANTICALLY (``decide`` proved the proposition is false, i.e. the
tester reduced to the concrete correct Bool), not by stuck reduction. That same
source ships as the ``pos-direct`` positive, so the battery records that
loop-freeness is not what any rival is being rejected for.

FORGERY CHECK (independently re-derived, all 12 builds run one at a time). The
reference side's exit code is admissible evidence only if it CHANGES when the
claim changes, so each witness was rebuilt with its claim FLIPPED (``= false``
swapped for ``= true``) against all three subjects. The reference tracks the
claim exactly, and gold does not track it at all:

    subject      witness (``= false``)          flipped (``= true``)
    rival        exit 0 (elaborates)            exit 1 ``decide`` proved false
    reference    exit 1 ``decide`` proved false  exit 0 (elaborates)
    gold         exit 1 stuck reduction          exit 1 stuck reduction (same)

So the reference's refutation is a real one — it flips polarity with the claim,
which is only possible if the kernel evaluated the tester — while gold's error is
byte-identical for a claim and its negation and therefore carries NO information
about either. That is precisely why ``witness_reference`` is required here rather
than merely convenient, and it is measured, not argued.

NOTE on rival SHAPE. Because the tester only reduces for a loop-free extracted
program, every reject rival is authored as a straight-line wrong impl over the
SAME two inputs — a legitimate impl-region reshape (``same_spec`` elides the impl
region) that both fails to verify against the frozen loop-tuned proof AND yields
a tester ``decide`` can evaluate. The loop-carrying literal-bug shapes
(uninitialised pre-loop flag; spurious-true post-loop return) collapse on this
carrier to the SAME observable spec violation as ``weak-ignore-budget`` — a
spurious ``true`` at ``limit = 0`` — and are represented by it (see footer).
"""
from pathlib import Path

INSTANCE = "django__django-14493"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen bounded-loop body. Lies wholly
# ---- inside the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    let mut exhausted := false\n"
    "    let mut i := 0\n"
    "    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)\n"
    "      invariant i ≤ limit\n"
    "      invariant exhausted = (decide (0 < i) && flags[i - 1]!)\n"
    "      invariant ∀ j, j + 1 < i → flags[j]! = true\n"
    "      done_with exhausted = overBudget flags limit\n"
    "      decreasing limit - i\n"
    "    do\n"
    "      exhausted := flags[i]!\n"
    "      i := i + 1\n"
    "    return exhausted"
)

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"

# ---- reordered pre-loop init: the two `let mut` declarations are independent
# ---- (neither reads the other), so swapping their order preserves behaviour and
# ---- every loop invariant. Used by the pos-reshape control.
_IMPL_RESHAPE = (
    "    let mut i := 0\n"
    "    let mut exhausted := false\n"
    "    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)\n"
    "      invariant i ≤ limit\n"
    "      invariant exhausted = (decide (0 < i) && flags[i - 1]!)\n"
    "      invariant ∀ j, j + 1 < i → flags[j]! = true\n"
    "      done_with exhausted = overBudget flags limit\n"
    "      decreasing limit - i\n"
    "    do\n"
    "      exhausted := flags[i]!\n"
    "      i := i + 1\n"
    "    return exhausted"
)
assert _IMPL_RESHAPE != _IMPL, "pos-reshape did not rewrite"


_PROOF = "prove_correct passBudgetExceeded by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced (frozen
    tactic script kept). The reject rivals are straight-line and expected NOT to
    verify against the loop-tuned proof; the pos controls keep a shape whose
    `loom_solve` proof still closes (verified: reorder and closed-form both do)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the frozen tactic body retuned. Both regions are
    elided from the consumer spec view, so `same_spec` still holds and the
    `prove_correct passBudgetExceeded` obligation survives with a byte-identical
    statement; only the SCRIPT that discharges it changes. Used by the correct
    reshape whose shape `loom_solve` alone cannot bridge."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- The witness REFERENCE, shared by every reject case below.
#
# The frozen impl keeps a `while` loop, and under `loom.semantics.choice
# "demonic"` that loop's fixpoint elaborates through `Classical.choice`, which
# the kernel cannot unfold. So `decide` against the FROZEN tester is stuck for
# EVERY claim regardless of truth — measured here, the gold-side build fails with
#
#   Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse`.
#   ... reduction got stuck at the `Decidable` instance
#
# which is a failure the kernel never evaluated, so its exit code attests to a
# refutation that was never performed. Refuting each witness against gold would
# therefore discriminate nothing.
#
# The repair is to refute against a loop-free impl of the SAME frozen spec that
# DOES reduce. This is that impl: it returns the grounded closed form directly,
# shares the frozen spec (only the elided impl region differs), and VERIFIES
# (machine-checked, exit 0) — and an impl the verifier accepts cannot violate its
# own spec, so a genuine witness must still fail against it. Measured: all three
# witnesses below fail against it SEMANTICALLY (`decide` proved the proposition
# is false — the tester reduces to the concrete correct Bool), not by stuck
# reduction. It is also shipped as the `pos-direct` positive, so the battery
# itself records that loop-freeness is not what any rival is rejected for.
_LOOPFREE = _impl("    let out : Bool := overBudget flags limit\n    return out")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `passBudgetExceededTester flags limit = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for passBudgetExceeded\n"
            "prove_precondition_decidable_for passBudgetExceeded\n"
            "prove_postcondition_decidable_for passBudgetExceeded\n"
            "derive_tester_for passBudgetExceeded\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two independent pre-loop `let mut` declarations. Behaviour
        # and every loop invariant are preserved; the frozen `loom_solve` proof
        # still closes (verified).
        "module": _impl(_IMPL_RESHAPE),
        "rationale": (
            "a structurally-different but CORRECT impl: the two independent "
            "pre-loop `let mut` declarations (`exhausted := false`, `i := 0`) are "
            "reordered — neither reads the other, so behaviour and all three loop "
            "invariants are preserved. The frozen `loom_solve` proof closes "
            "unchanged. If it FAILS => SPEC-TOO-STRONG (a faithful "
            "structurally-different correct impl rejected)."
        ),
    },
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest faithful impl: return the grounded closed form directly.
        # Because the ensures pins `out` to `overBudget flags limit`, computed
        # from the inputs, returning it is CORRECT, not an echo. No loop.
        "module": _LOOPFREE,
        "rationale": (
            "the HONEST cheapest faithful impl (grounded-oracle positive control). "
            "The ensures pins `out` to the fully-decidable pure fold "
            "`overBudget flags limit`, GROUNDED in the two inputs, so returning "
            "the closed form directly satisfies both structural pieces (the "
            "budget guard C1 and the all-changed fold C2) and needs no loop. "
            "Demonstrates the oracle is grounded — there is no wrong value an echo "
            "could carry. If it FAILS => SPEC-TOO-STRONG (the spec rejects the "
            "very value it pins). Doubles as the `witness_reference` every reject "
            "case below is refuted against, so the battery itself records that "
            "loop-freeness is not what any rival is being rejected for."
        ),
    },
    {
        "id": "pos-take-all-fold",
        "kind": "soundness",
        "expect": "verify",
        # A CORRECT reshape whose shape `loom_solve` alone cannot bridge: express
        # the all-changed fold C2 as a list-level `List.all` over the budget
        # prefix `flags.take limit` (rather than an index-range `∀`), and commute
        # the `&&`. Extensionally identical to the frozen closed form under the
        # `require`; the reproof supplies the prefix/index bridge, then closes.
        "module": _impl_reproved(
            "    let out : Bool := (flags.take limit).all (· == true) "
            "&& decide (0 < limit)\n"
            "    return out",
            "prove_correct passBudgetExceeded by\n"
            "  have bridge : ∀ (fl : List Bool) (lim : Nat), lim ≤ fl.length →\n"
            "      ((fl.take lim).all (· == true)) "
            "= decide (∀ j, j < lim → fl[j]! = true) := by\n"
            "    intro fl lim h\n"
            "    rw [Bool.eq_iff_iff]\n"
            "    simp only [List.all_eq_true, beq_iff_eq, decide_eq_true_eq]\n"
            "    constructor\n"
            "    · intro hh j hj\n"
            "      have hjf : j < fl.length := by omega\n"
            "      have hjt : j < (fl.take lim).length := by simp; omega\n"
            "      have := hh _ (List.getElem_mem hjt)\n"
            "      rw [List.getElem_take] at this\n"
            "      rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hjf]\n"
            "      exact this\n"
            "    · intro hh x hx\n"
            "      obtain ⟨j, hjt, rfl⟩ := List.getElem_of_mem hx\n"
            "      simp only [List.length_take] at hjt\n"
            "      have hj : j < lim := by omega\n"
            "      have hjf : j < fl.length := by omega\n"
            "      rw [List.getElem_take]\n"
            "      have := hh j hj\n"
            "      rw [List.getElem!_eq_getElem?_getD, "
            "List.getElem?_eq_getElem hjf] at this\n"
            "      exact this\n"
            "  loom_solve <;> "
            "simp [overBudget, settledThrough, bridge, Bool.and_comm]"),
        "rationale": (
            "a CORRECT reshape that the frozen tactic script alone does NOT close, "
            "which is what makes it a real SPEC-TOO-STRONG probe rather than a "
            "restatement. The all-changed fold C2 is rebuilt as a list-level "
            "`List.all` over the budget prefix `flags.take limit` instead of an "
            "index-range `∀ j < limit`, and the `&&` is commuted — a genuinely "
            "different shape that is only EXTENSIONALLY equal to the frozen closed "
            "form, and only under the `require limit ≤ flags.length` bound (the "
            "prefix has exactly `limit` elements precisely because of it). "
            "Measured: with the frozen `loom_solve` this shape is REJECTED, with "
            "the residual goal `((List.take limit flags).all fun x => x == true) "
            "&& decide (0 < limit) = overBudget flags limit` — so the reshape is "
            "not definitionally equal and the case has real content. The reproof "
            "supplies the prefix/index bridge lemma and closes (the statement is "
            "byte-identical; only the elided tactic body changes). If it FAILS => "
            "SPEC-TOO-STRONG: a faithful correct impl expressing the fold over the "
            "budget prefix would be rejected by the spec."
        ),
    },
    {
        "id": "admiss-f2p-satisfiable-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # PRECOND-TOO-STRONG lane. This carrier's obligation is total apart from
        # the modeling bound, so the analogue of nagini's permission-admissibility
        # probe is: is the obligation SATISFIABLE, by a DEFINITE value, at exactly
        # the F2P-shaped input — and is the post-image non-degenerate and the
        # `require` non-vacuous? Each fact is discharged BY EVALUATION as a `have`
        # inside the elided impl region, before the frozen body closes the frozen
        # obligation verbatim.
        "module": _impl(
            "    -- ADMISSIBILITY. The obligation is TOTAL apart from the modeling\n"
            "    -- bound `require limit ≤ flags.length`, so the live\n"
            "    -- PRECOND-TOO-STRONG question on this carrier is whether the\n"
            "    -- obligation is SATISFIABLE, and satisfiable by a DEFINITE value,\n"
            "    -- at exactly the F2P-shaped zero-budget input — and whether the\n"
            "    -- post-image is non-degenerate (not pinned to one constant) and\n"
            "    -- the `require` not vacuous. Each fact is discharged BY\n"
            "    -- EVALUATION here, before the frozen body then closes the frozen\n"
            "    -- obligation verbatim.\n"
            "    have _obligationIsSatisfiableAtF2PShape : "
            "overBudget [] 0 = false := by decide\n"
            "    have _postImageAlsoReachesTrue : "
            "overBudget [true] 1 = true := by decide\n"
            "    have _postImageForksOnALaterPass : "
            "overBudget [true, false] 2 = false := by decide\n"
            "    have _requireHoldsAtF2PShape : "
            "(0 : Nat) ≤ ([] : List Bool).length := by decide\n"
            "    have _requireHoldsAtMultiPassShape : "
            "(2 : Nat) ≤ ([true, false] : List Bool).length := by decide\n"
            "    have _requireIsNotVacuous : "
            "¬ ((3 : Nat) ≤ ([true] : List Bool).length) := by decide\n"
            + _IMPL + "\n"),
        "rationale": (
            "ADMISSIBILITY / PRECOND-TOO-STRONG — the third direction this gate "
            "exists to test, and the lane an earlier revision of this battery "
            "dropped as vacuous on the ground that the frozen obligation has no "
            "interesting precondition. That reason is wrong: the analogue on a "
            "near-total carrier is the obligation being UNSATISFIABLE (or "
            "satisfiable only degenerately) at an F2P-shaped input, which a "
            "positive discharging the obligation at that concrete input BY "
            "EVALUATION tests directly. Six facts are computed inside the elided "
            "impl region before the frozen body runs: (1) at the F2P-shaped "
            "zero-budget input `([], 0)` the obligation is satisfiable by a "
            "DEFINITE value, and that value is `false` — if the budget guard C1 "
            "made the zero-budget post-image empty or indefinite, this `decide` "
            "would not close; (2,3) the post-image is NON-DEGENERATE — it also "
            "reaches `true` (at `([true], 1)`) and forks back to `false` once a "
            "LATER pass settles (at `([true, false], 2)`), so the spec is not "
            "pinned to one constant; (4,5) the `require limit ≤ flags.length` "
            "actually ADMITS both the zero-budget F2P shape and the multi-pass "
            "shape, i.e. it is not too strong to reach the inputs the rivals are "
            "refuted at; (6) the `require` is not vacuously true either (it "
            "genuinely excludes `limit = 3` against a one-element flag list), so "
            "(4,5) are content and not a tautology. Each `have` has TEETH, checked "
            "by machine: negating any one of the six breaks the build. If this "
            "case FAILS => PRECOND-TOO-STRONG (the obligation is unsatisfiable, "
            "degenerate, or unreachable at the F2P-shaped input)."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-ignore-budget",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the budget guard C1: reports the all-changed fold alone. On a
        # ZERO budget `settledThrough flags 0` is vacuously true, so the rival
        # returns a spurious `true` where the fix demands a definite `false`.
        # Correct on every positive budget; diverges on EXACTLY the zero-budget
        # sub-domain — the F2P discriminator.
        "module": _impl(
            "    let out : Bool := settledThrough flags limit\n    return out"),
        "refinement": (
            "reporting a spurious 'still exhausting' on the zero-budget path is "
            "EXACTLY the defect class the fix forbids: with a zero budget no pass "
            "runs, yet this rival reports the sequence as never having settled. A "
            "faithful counterpart that dropped the zero-budget guard would emit "
            "the spurious 'budget exhausted' summary on the zero-budget "
            "configuration, which is precisely the crash-or-spurious-error path "
            "the failing zero-budget test forbids (that test asserts the bounded "
            "pass sequence runs to completion with no spurious 'exceeded' "
            "outcome). It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the budget-guard piece C1 (`decide (0 < limit)`): at "
            "`limit = 0` the loop never runs and the closed form is `false`, but "
            "`settledThrough flags 0` is the empty-range `∀`, vacuously `true`, so "
            "the rival returns `true`. PARTIAL-DOMAIN: correct on every "
            "`limit > 0` input, wrong on EXACTLY the zero-budget sub-domain. If it "
            "VERIFIES => SPEC-TOO-WEAK (the zero-budget boundary, the whole bug, "
            "is unpinned). Refuted at the zero-budget input `([], 0)` — the "
            "sub-domain no other rival isolates."
        ),
        "witness": _tester(
            "example : passBudgetExceededTester [] 0 = false := by\n  decide\n"),
        # Gold keeps a `while` loop, so `decide` against it is stuck for EVERY
        # claim and its exit code discriminates nothing. Refuted against the
        # verifying loop-free impl of the same spec instead; measured there as a
        # SEMANTIC refutation (`decide` proved the proposition is false).
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-ignore-settled",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the all-changed fold C2: reports exhaustion on ANY positive
        # budget, even after a change-free pass. Correct only when every pass in
        # the budget changed; diverges on the change-free sub-domain.
        "module": _impl(
            "    let out : Bool := decide (0 < limit)\n    return out"),
        "refinement": (
            "a counterpart that reported 'budget exhausted' whenever the budget "
            "was positive — ignoring whether the passes actually kept changing — "
            "would emit the spurious 'exceeded' summary the moment the sequence "
            "settled early, breaking the normal multi-pass configurations whose "
            "passes stop changing before the budget is spent (the passes settle, "
            "so the summary must be `false`). It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the all-changed piece C2 (`settledThrough flags limit`): "
            "on `([false], 1)` the single pass reported no change, so "
            "`settledThrough [false] 1 = false` and the closed form is `false`, "
            "but the rival returns `decide (0 < 1) = true`. CONTROL-FLOW / "
            "PARTIAL-DOMAIN: the change-free sub-domain is unpinned. If it "
            "VERIFIES => SPEC-TOO-WEAK (the early-settle value is unpinned). "
            "Refuted at `([false], 1)` — a positive budget whose only pass did "
            "NOT change, distinct from the zero-budget rival's input."
        ),
        "witness": _tester(
            "example : passBudgetExceededTester [false] 1 = false := by\n"
            "  decide\n"),
        # See weak-ignore-budget: gold's loop cannot decide, so the refutation is
        # checked against the verifying loop-free reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-pass-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: inspects only the FIRST pass. Correct for every budget ≤ 1
        # (and every zero budget), but blind to any pass after the first — so it
        # diverges only once a LATER pass settles under a budget ≥ 2.
        "module": _impl(
            "    let out : Bool := decide (0 < limit) && flags[0]!\n"
            "    return out"),
        "refinement": (
            "a counterpart that decided the summary from the FIRST pass alone "
            "agrees with the fix on every budget of zero or one, but under a "
            "larger budget it would report 'still exhausting' even after a later "
            "pass had settled — emitting the spurious 'exceeded' summary on the "
            "very multi-pass configurations the budget mechanism exists to handle "
            "(where an intermediate pass stops changing). It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the all-changed piece C2 over a LATER index: on "
            "`([true, false], 2)` pass 0 changed but pass 1 did not, so "
            "`settledThrough [true, false] 2 = false` and the closed form is "
            "`false`, but the rival reads only `flags[0]! = true` and returns "
            "`true`. A genuine near-miss (correct for every `limit ≤ 1`), so it "
            "gets its OWN input at `limit = 2` distinguishing it from "
            "weak-ignore-settled (which already fails at `limit = 1`). If it "
            "VERIFIES => SPEC-TOO-WEAK (the fold's dependence on passes beyond the "
            "first is unpinned). Refuted at `([true, false], 2)` — the multi-pass "
            "sub-domain, `limit = 2`, that varies both binders past every other "
            "witness."
        ),
        "witness": _tester(
            "example : passBudgetExceededTester [true, false] 2 = false := by\n"
            "  decide\n"),
        # See weak-ignore-budget: gold's loop cannot decide, so the refutation is
        # checked against the verifying loop-free reference.
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives: pos-reshape + pos-direct; 1 admissibility: admiss-reads; 1
# frame-mutation rival: frame-mut-write; 3 uniqueness rivals: weak-zero-true,
# weak-early-true, weak-prepatch). This bundle models only the purely-functional
# core — a single method `passBudgetExceeded` — where the sibling contracts one
# function `run_passes` over a permission-bearing list. The value surface carries
# across intact; the permission surface does not exist here. Every sibling case
# is accounted for below.
#
#   sibling case        -> here
#   -----------------------------------------------------------------------
#   pos-reshape         -> pos-reshape                        PORTED (reordered
#                                                             independent inits)
#   pos-direct          -> pos-direct                         PORTED (return the
#                                                             grounded closed form)
#   admiss-reads        -> admiss-f2p-satisfiable-nondegenerate
#                                                             PORTED (lane kept,
#                                                             permission mechanism
#                                                             re-aimed; see below)
#   frame-mut-write     -> (none)                             VACUOUS (see below)
#   weak-zero-true      -> weak-ignore-budget                 PORTED (reshaped)
#   weak-prepatch       -> weak-ignore-budget                 COLLAPSED (see below)
#   weak-early-true     -> weak-ignore-settled                PORTED (reshaped)
#   (new near-miss)     -> weak-first-pass-only               ADDED (binder cover)
#   (new reshape)       -> pos-take-all-fold                  ADDED (see below)
#
# 3 ported/reshaped rivals + 1 added near-miss = 3 reject cases; 3 positives; 1
# admissibility. 7 cases total.
#
# ADDED (pos-take-all-fold): a SPEC-TOO-STRONG probe with real content. The two
#   original positives are both closable by the frozen `loom_solve` unchanged,
#   which makes them honest but cheap: neither shows the spec accepts a shape the
#   frozen script did not already anticipate. This one rebuilds the all-changed
#   fold C2 as a list-level `List.all` over the budget prefix `flags.take limit`
#   (instead of an index-range `∀ j < limit`) with the `&&` commuted — correct,
#   but only EXTENSIONALLY so, and only under the `require` bound. Measured: with
#   the frozen tactic body this shape is REJECTED on the residual goal
#   `((List.take limit flags).all fun x => x == true) && decide (0 < limit) =
#   overBudget flags limit`, i.e. it is NOT definitionally equal to the frozen
#   closed form. The case therefore ships with a retuned tactic body (elided from
#   the spec view, statement byte-identical) that supplies the prefix/index bridge
#   and closes — so a faithful correct impl of this shape is demonstrated to be
#   ACCEPTED rather than assumed to be.
#
# VACUOUS (frame-mut-write): the sibling's mandatory frame-mutation rival writes
#   back into a read-only input carrying only a fractional heap permission,
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `flags` is an immutable value, this bundle declares no `mut`
#   parameter, there is no heap and no aliasing. There is no read-only input to
#   overwrite and no permission system to trip, so the class is vacuous. No
#   substitute is fabricated (per the porting map, this class is legitimately
#   dropped rather than replaced).
# PORTED (admiss-reads -> admiss-f2p-satisfiable-nondegenerate): the sibling's
#   admissibility control confirms the fractional half-permission precondition
#   admits the reads a normal input needs. The PERMISSION mechanism has no
#   counterpart here, but the LANE does, and an earlier revision of this battery
#   dropped it on the wrong reason — that this bundle's only precondition is the
#   modeling bound `require limit ≤ flags.length`, so there is nothing a read
#   could exceed. "The frozen obligation has no interesting precondition" is not
#   a demonstration of vacuity: the analogue on a near-total carrier is the
#   obligation being UNSATISFIABLE, or satisfiable only DEGENERATELY, at exactly
#   an F2P-shaped input, and a positive that discharges the obligation at that
#   concrete input by EVALUATION tests it directly. That case is now shipped, and
#   its content is machine-checked rather than argued: it computes six facts
#   inside the elided impl region — the obligation is satisfiable by a DEFINITE
#   `false` at the F2P-shaped `([], 0)`; the post-image is non-degenerate (also
#   reaches `true` at `([true], 1)`, forks back to `false` at `([true, false], 2)`
#   once a LATER pass settles); the `require` admits both of those shapes; and
#   the `require` is not itself vacuous. Negating any ONE of the six breaks the
#   build (all six negative controls measured, each exit 1), so no `have` is a
#   tautology riding along. This restores the third direction of the gate
#   (PRECOND-TOO-STRONG) that the earlier revision silently removed.
# COLLAPSED (weak-prepatch -> weak-ignore-budget): the sibling's strongest rival
#   is the literal pre-patch — the summary flag left uninitialised before the
#   loop, read stale/undefined on the zero-budget path. On this carrier the
#   pre-patch is modeled by `Solution_prepatch.lean` (the pre-loop value left
#   unconstrained, taken as `true`); its OBSERVABLE spec violation is precisely a
#   spurious `true` at `limit = 0` — the same clause (the budget guard C1) and
#   the same input as weak-ignore-budget. A loop-carrying `exhausted := true`
#   rival additionally cannot be witnessed here: the extracted tester does not
#   reduce under `decide` while a loop remains (it sticks on the fixpoint). So the
#   pre-patch argument is carried by weak-ignore-budget, which refutes exactly the
#   zero-budget defect with a `decide`-able straight-line tester. Reported as a
#   collapse, not a silent drop.
# DIVERGENCE LANE: CLOSED IN THE SPEC (was recorded as a KNOWN SPEC HOLE; no case
#   to ship, and now nothing to report). The sibling ships no `diverge-*` /
#   `nonterm-*` case, so there was never a case to carry over, and an earlier
#   revision of this footer recorded the lane as an OPEN spec hole for a different
#   reason: it read this bundle as setting `loom.semantics.termination "partial"`,
#   under which the postcondition is claimed only of TERMINATING runs, so a
#   non-terminating impl satisfied `ensures out = overBudget flags limit`
#   VACUOUSLY and VERIFIED, while its faithful real counterpart hangs the failing
#   test and never resolves, a direct verify-does-not-imply-resolve break said to
#   be corpus-wide. That census is withdrawn along with the premise: all 500
#   velvet bundles set `"total"` and none sets `"partial"`, so there is no cohort
#   to be in. It was in any case not closable inside the G-PBT lane, because a
#   reject case needs a witness refuting the rival.
#
#   The SPEC now closes it: the bundle sets `loom.semantics.termination "total"`
#   and the bounded loop carries `decreasing limit - i`. Re-measured on this
#   carrier, one build at a time:
#
#     rival: the loop replaced by `while spin = 0 / invariant spin = 0` (the body
#     re-assigns `spin := 0`, so the loop diverges and its `done_with exhausted =
#     overBudget flags limit` is discharged from the contradiction between the
#     invariant and `if_neg`, i.e. on an exit no run ever reaches):
#
#       under "partial"  -> exit 0, VERIFIES (the hole, reproduced on this cell)
#       under "total"    -> exit 1, `error: Decreasing annotations are required in
#                           total correctness semantics`
#
#   So the diverging rival this bundle used to admit is now rejected, and the lane
#   is closed by construction rather than by argument. Still no reject case is
#   shipped, but for the OPPOSITE reason to before: the rival no longer verifies,
#   so there is no spec hole for a witness to attest to — and it is rejected for
#   the MISSING ANNOTATION, which is a rejection no `witness` at a concrete input
#   could express anyway (there is no input at which the rival's returned value is
#   wrong; it returns nothing at all).
#
#   SCOPE OF WHAT `"total"` BUYS, measured and recorded so the guarantee is not
#   overread: Loom's VC generator (`WPGen.forWithInvariantLoop`,
#   Loom/MonadAlgebras/NonDetT/Basic.lean) takes the measure as a parameter but
#   emits NO decrease obligation for it — the `decreasing` elaborator
#   (CaseStudies/Macro.lean) only ERRORS when the measure is absent under
#   `"total"`. Confirmed by machine on this cell: gold with `decreasing limit`
#   (constant) and gold with `decreasing i` (strictly INCREASING) both still
#   verify, exit 0. So `"total"` on this backend enforces that every loop CARRY a
#   measure, not that the measure it carries decreases; what the flip mechanically
#   buys is that a diverging rival can no longer be authored without an annotation
#   it cannot honestly supply. The decrease itself is therefore discharged by
#   REVIEW, and the argument is recorded here rather than left implicit:
#
#     `decreasing limit - i` on `while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)`.
#     The guard is COMPOUND — the loop also stops early, when the previous pass
#     reported no change — so no measure reads off the guard alone, which is why
#     this cell needed a human argument rather than the mechanical rule. `limit - i`
#     is nonetheless correct on two facts about this body: (1) `limit` is never
#     assigned anywhere in the method, so the measure moves only with `i`; (2) the
#     body is STRAIGHT-LINE — `exhausted := flags[i]!` then `i := i + 1` — with a
#     single increment on its ONLY path. There is no branch, no `continue`, and the
#     early-stop condition is tested in the GUARD rather than acted on in the body,
#     so there is no path that leaves `i` unchanged. Every iteration that runs
#     therefore advances `i` by exactly one, and the guard supplies `i < limit` on
#     entry, so `limit - (i + 1) < limit - i` in `Nat` with no truncation (the
#     subtrahend is strictly smaller than `limit`). The measure is bounded below by
#     0, so the loop runs at most `limit` times. The early exit only makes it stop
#     SOONER, which cannot break a decrease argument — a measure has to fall on
#     every iteration the body CAN take, and taking fewer of them is safe.
#
#   The invariant `i ≤ limit` already in the loop is the same bound stated on the
#   other side, so nothing about the measure is in tension with the frozen spec.
#   The frozen `loom_solve` closes the flipped file unchanged (exit 0): no proof
#   script change was needed, because the flip adds no goal on this backend.
# ADDED (weak-first-pass-only): a near-miss with no direct sibling — inspects only
#   the first pass, correct for every budget <= 1, wrong once a LATER pass settles
#   under a budget >= 2. Added to vary the `limit` binder to 2 and attack the
#   all-changed fold C2 over an index beyond the first, so no rival leaves the
#   multi-pass sub-domain untested.
#
# BINDER / CLAUSE COVERAGE. The two input binders are `flags` and `limit`; the
#   single top-level clause `out = overBudget flags limit` composes two
#   independent structural pieces, the budget guard C1 (`decide (0 < limit)`) and
#   the all-changed fold C2 (`settledThrough flags limit`). C1 is attacked by
#   weak-ignore-budget (zero budget). C2 is attacked by weak-ignore-settled (first
#   pass) and weak-first-pass-only (a later pass). `limit` is varied across
#   {0, 1, 2} and `flags` across {[], [false], [true, false]} over three DISTINCT
#   witness inputs (pts=3), so neither piece is demonstrated at a single pinned
#   point and both binders are abused by the reject witnesses. The admissibility
#   case adds a fourth point `([true], 1)` on the POSITIVE side (where the closed
#   form is `true`), so the battery pins both polarities of the post-image and not
#   only the `false` side every reject witness lands on.
#
# SPEC-TOO-WEAK PROBES RUN AND REJECTED (attack D; no case shipped for these —
#   recorded so the unattacked surface is visible rather than assumed). Five
#   further wrong impls were built against the frozen spec and ALL were rejected
#   on a genuine unsolved postcondition goal, not tactic breakage:
#   `overBudget flags (limit - 1)` (budget off-by-one downward);
#   `decide (0<limit) && flags[limit-1]!` (last pass only);
#   `decide (0<limit) && decide (∀ j < min limit 2, flags[j]! = true)` (first two
#   passes only — a DEEPER near-miss than weak-first-pass-only, correct for every
#   `limit ≤ 2`); `settledThrough flags limit && decide (0 < flags.length)` (a
#   nonempty-FLAGS guard substituted for the positive-BUDGET guard C1 — the
#   subtlest C1 attack, since it agrees with the closed form everywhere except a
#   zero budget over a nonempty flag list); and
#   `decide (0<limit) && decide (∃ j < limit, flags[j]! = true)` (∃-changed for
#   ∀-changed). No spec hole: the single `ensures` pins `out` to the closed form
#   at every input, so it admits no wrong impl on this surface at all.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (there are no consumed
#   axioms here in any case — mapping.md §3), and this gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
