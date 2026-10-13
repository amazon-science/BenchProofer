"""properties.py — G-PBT falsification battery for sympy__sympy-20154 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct gatherWalk`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  gatherWalk (steps : Nat) return (out : List Int)
    ensures out.length = steps
    ensures ∀ i, i < steps → out[i]! = stateAt i          (stateAt i = i + 1)

The method gathers a step-by-step walk into a list: one INDEPENDENT per-step
record per step, the record at position i being the working state as it was AT
its own step i. The working state genuinely advances one step at a time, so the
per-step values are pairwise distinct — modelled as the strictly-increasing
``stateAt i = i + 1``. The two load-bearing clauses pin (E2) the cardinality
(one record per step) and (E3) that record i recovers step i's own state. (E3)
is the discriminator: it is exactly the per-step history an aliasing enumerator —
whose gathered records all collapse onto the FINAL state — cannot reproduce.

ONE INPUT BINDER, free: ``steps`` (the number of steps gathered). The spec
predicates range over ``steps`` (both clauses) and the index ``i`` (E3). The
reject witnesses vary ``steps`` across several values (1, 2, 3, 4) so the
manifest demonstrates the post-image's dependence on the step count and on the
per-index pin rather than on a single pinned shape; a rival mishandling only one
step count would slip past a battery that probed only one. ``uniq-small-count-only``
carries the upper end specifically: it is behaviourally gold at 1, 2 and 3 and
diverges only at 4, so it is the one rival no other witness could refute.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``gatherWalkTester steps = false`` says the extracted
program's result violates the postcondition at that concrete step count) and
closes by ``decide``, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. ``decide`` reduces the
extracted program by kernel computation; a program shaped as a ``while`` loop
does NOT reduce to ``isTrue``/``isFalse`` (the loop's fixpoint is opaque to the
kernel). So each reject rival is expressed as a LOOP-FREE impl that computes its
(wrong) list directly from ``List.range`` / ``stateAt`` — still a wrong
implementation sharing the frozen spec, but one whose extracted tester
``decide``s. This is a witnessing convenience, not a weakening: the frozen spec
is untouched and each rival's divergence is real at the witnessed step count.
Every argument is a small concrete ``Nat`` literal so ``decide`` reduces without
getting stuck.

WHICH HALF OF THE DISCRIMINATION CHECK CARRIES THE WEIGHT (measured, and stated
here because the two halves are NOT symmetric on this carrier). The gate builds
each witness twice: it must elaborate against the rival and FAIL against the
frozen solution.

  * The RIVAL half is a genuine semantic refutation. The rival's impl is
    loop-free, so ``decide`` reduces the extracted program by kernel computation
    and ``gatherWalkTester k = false`` is a proof that the rival's actual output
    violates the frozen postcondition at ``k``. This is the substance of every
    reject case below.
  * The GOLD half fails for a REDUCTION reason, not a semantic one. The frozen
    impl is a ``while`` loop whose fixpoint the kernel cannot unfold, so on gold
    NO tester claim decides: ``decide`` reports "reduction got stuck at the
    Decidable instance". Measured — every one of these fails identically on the
    frozen solution: ``gatherWalkTester 2 = false`` (exit 1),
    ``gatherWalkTester 2 = true`` (exit 1), ``gatherWalkTester 0 = true``
    (exit 1, and that claim is TRUE of gold), ``gatherWalkTester 0 = false``
    (exit 1), ``gatherWalkTester 1 = true`` (exit 1). ``simp`` / ``rfl`` /
    ``grind`` / ``unfold ...; decide`` all fail the same way (exit 1 each). So
    the gold half is content-blind here and must not be read as "gold satisfies
    the spec at this input".

The tautology risk the gold half exists to exclude is therefore closed by
separate evidence rather than by that build. Against the loop-free CORRECT impl
of ``pos-control-direct``, whose extracted program DOES reduce,
``gatherWalkTester k = true`` is provable at k = 1, 2, 3, 4 (exit 0 each) and
``gatherWalkTester 4 = false`` is actively refuted ("decide proved that the
proposition ... is false", exit 1). So ``gatherWalkTester k = false`` is
demonstrably NOT a claim that holds of any impl: it separates each rival below
from a behaviourally-gold one at the same step count. That control cannot be
shipped as its own SPEC case — appending the tester directives at top level puts
them outside the elided regions, so ``markers.same_spec`` fails (checked) — so
it is recorded here as measured evidence.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: the sole input
    ``steps`` is an immutable ``Nat`` value (no ``mut`` binder among the inputs),
    there is no heap and no aliasing, and the only ownership predicate in the
    sibling is on the freshly-built OUTPUT. There is no read-only input to
    mutate and no substitute probe. Not fabricated. (See footer.)
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the reject lane: (E2)+(E3) pin
    the length and the per-index value on EVERY step count, so a rival that
    collapses every record to the final state, lags the snapshot by one step,
    mis-records only the first element, appends one extra record, reverses the
    order, or is correct only for short walks diverges from the spec at a
    concrete step count.
  * UNGROUNDED-ORACLE ECHO — N/A as a defect class. (E3) is pinned to ``stateAt``,
    but ``stateAt`` is GROUNDED — it fully unfolds to ``i + 1``, a pure function
    of the index, with body ``(i : Int) + 1``. There is no opaque answer-key to
    echo; an impl that records ``stateAt i`` at index i is doing exactly the
    required work and IS correct. The honest cheapest-impl positive control
    (pos-control-direct) records ``stateAt`` directly.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS PLACEMENT. Rivals share a refutation point only when they fail there for
the same reason. The six reject witnesses sit at step counts 2, 1, 2, 2, 3 and 4
so the manifest demonstrates the post-image's dependence on the step count and on
the per-index pin rather than on a single pinned shape. Each rival is refuted at a
step count where it genuinely diverges from the frozen spec: each witness was
rebuilt against the rival (elaborates, exit 0) and against the frozen solution
(fails, exit 1) — with the caveat about WHICH half carries the weight recorded
above.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20154"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the whole gold impl body: a single anchor lying wholly inside the impl
# ---- region and unique in the file (both facts asserted at load by _swap).
# ---- Rivals that reshape the executable surface entirely swap on this block.
_IMPL_BODY = (
    "    let mut result : List Int := []\n"
    "    let mut i := steps\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ steps\n"
    "      -- Every already-gathered record holds the snapshot of its OWN step -- an\n"
    "      -- independent value that later steps never disturb. The tail `[i .. steps)`\n"
    "      -- has been gathered so far (this loop walks the steps in reverse, each\n"
    "      -- iteration prepending one freshly-captured per-step record).\n"
    "      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`\n"
    "      -- (the snapshot step): the current per-step value is recorded by value, so\n"
    "      -- a later mutation of the working state leaves this gathered record alone.\n"
    "      let snap := stateAt (i - 1)\n"
    "      result := snap :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a rival that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, may retune it without
# ---- touching the spec or dropping the `prove_correct gatherWalk` obligation).
_PROOF_GOLD = (
    "prove_correct gatherWalk by\n"
    "  loom_solve\n"
    "  subst result\n"
    "  rw [gather_step steps i (by omega) (by omega)]\n"
)
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges (for the
# ---- soundness positive) or FAILS (for the reject rivals — which is the point).
# ---- Reject rivals retune the proof to this shape so the rejection is
# ---- attributable to the spec (the witness), not to a proof script tuned to a
# ---- loop that no longer exists.
_PROOF_FLAT = "prove_correct gatherWalk by\n  loom_solve\n"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `gatherWalkTester steps = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete step count. Checked
# ---- in a file whose `prove_correct` block has been stripped. The argument is a
# ---- small concrete Nat literal so `decide` reduces the (loop-free) extracted
# ---- program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for gatherWalk\n"
            "prove_precondition_decidable_for gatherWalk\n"
            "prove_postcondition_decidable_for gatherWalk\n"
            "derive_tester_for gatherWalk\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. Drops the `while`/prepend accumulator entirely and lays
    # the per-step values out directly with `List.range`+`stateAt`; no loop, no
    # induction lemma. Observationally identical for every input. If a faithful
    # correct impl cannot verify, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return (List.range steps).map (fun k => stateAt k)\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "rationale": (
            "a structurally-different but behaviourally-identical impl: no reverse "
            "`while` accumulator at all; the per-step values are laid out directly "
            "as `(List.range steps).map stateAt`. Produces the same length-`steps` "
            "list whose element i is `stateAt i`, so both `ensures` clauses still "
            "hold on the whole domain, and `loom_solve` discharges the (now "
            "loop-free) obligation without the gather-step lemma. A correct reshape "
            "MUST verify, else the postcondition is SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing could
    # exclude an F2P-shaped input. The residual admissibility risk on a total
    # domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point — a spec no impl can meet reads exactly like one every
    # impl meets. This case discharges an in-region `assert`, at an F2P-shaped
    # 3-step walk, that the modeled per-step observable is NON-DEGENERATE: the
    # three gathered records are the strictly-increasing distinct values
    # [1, 2, 3] (each step's OWN state), not a collapsed constant. The surrounding
    # impl is kept verbatim so the method's own obligation still discharges; the
    # proof is retuned only to clear the extra assert goal by `decide` (allowed —
    # the tactic body is elided from the spec view). The assert is live: a false
    # claim leaves the `decide` goal unsolved (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (walkSeq 3 = [1, 2, 3]))\n"),
            _PROOF_GOLD,
            "prove_correct gatherWalk by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (subst result; rw [gather_step steps i (by omega) (by omega)])\n"
            "    | decide\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "3-step walk: the three gathered records are the strictly-increasing "
            "distinct per-step states [1, 2, 3] (each step's own value), which is "
            "exactly the per-step history the fix installs — NOT a collapsed "
            "constant. The in-region assert must discharge (else the modeled "
            "observable is degenerate at the point the fix cares about); the impl "
            "is kept verbatim so the method's own `ensures` still discharges."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete step count and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is expressed as
    # a LOOP-FREE impl over `List.range`/`stateAt` so its extracted tester
    # `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "uniq-aliasing-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # The canonical modeled defect: hand out a live alias, so every gathered
        # record reads back as the FINAL state. Modeled as every record == steps.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return List.replicate steps (steps : Int)\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "this is the pre-patch behaviour (the un-copied per-yield hand-out): "
            "every gathered record aliases the single evolving working record and "
            "reads back as its FINAL state, so gathering an n-step walk yields the "
            "constant final value n times instead of the genuine per-step history. "
            "A faithful real patch that leaves the hand-out un-copied makes "
            "gathering the enumerator return the all-equal-to-final list, so the "
            "failing scenario — whose expected list is the distinct per-step "
            "partitions — still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from (E3) out[i]! = stateAt i: for steps ≥ 2 the collapse makes "
            "out[0]! = steps ≠ 1 = stateAt 0. Verifying would be SPEC-TOO-WEAK (the "
            "per-step-history clause the fix installs would be unpinned). Refuted at "
            "steps = 2, where the rival gives [2, 2] but out[0]! must be 1."
        ),
        "witness": _tester(
            "example : gatherWalkTester 2 = false := by\n"
            "  decide\n"),
    },
    {
        "id": "uniq-off-by-one-snapshot",
        "kind": "uniqueness",
        "expect": "reject",
        # Record the working state BEFORE the per-step advance, so every gathered
        # record lags one step: out[i]! == i, not i+1.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return (List.range steps).map (fun k => (k : Int))\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "records the working state BEFORE the per-step advance, so every "
            "gathered record lags one step (out[i]! = i, not i + 1). A faithful "
            "real analogue snapshots the working record at the wrong point in the "
            "mutation loop: the gathered list is a shifted history, so the ordered "
            "element-by-element comparison against the expected per-step partitions "
            "fails on every entry. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from (E3): out[i]! = i ≠ i + 1 = stateAt i on every index. "
            "Targets the per-step VALUE facet (snapshot timing), distinct from the "
            "collapse defect. Refuted at steps = 1, where the rival gives [0] but "
            "out[0]! must be 1 — the smallest step count that already exercises the "
            "index binder i = 0."
        ),
        "witness": _tester(
            "example : gatherWalkTester 1 = false := by\n"
            "  decide\n"),
    },
    {
        "id": "uniq-partial-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every step EXCEPT the first: the first record leaks the stale
        # initial state (0) instead of the step-0 snapshot (1).
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return (List.range steps).map (fun k => if k = 0 then (0 : Int) else stateAt k)\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "correct on every step EXCEPT the first, where it leaks the stale "
            "initial state (0) instead of the step-0 snapshot (1). A "
            "monotonicity/distinctness proxy (records strictly increasing) would "
            "accept 0, 2, 3, ...; only the exact per-index pin catches it. The "
            "faithful real analogue mis-records the FIRST gathered record (seeded "
            "from the pre-loop state), so the first element of every gather is "
            "wrong and the first-row comparison fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from (E3) on the single sub-domain i = 0 (out[0]! = 0 ≠ 1) "
            "while satisfying it for every i ≥ 1. This is the partial-domain attack "
            "the per-index clause defends. Refuted at steps = 2, where the rival "
            "gives [0, 2] but out[0]! must be 1 (later index 1 is correct)."
        ),
        "witness": _tester(
            "example : gatherWalkTester 2 = false := by\n"
            "  decide\n"),
    },
    {
        "id": "uniq-length-divergence",
        "kind": "uniqueness",
        "expect": "reject",
        # Per-step values all correct, but append one EXTRA (duplicate final-state)
        # record, so the list is one longer than the number of steps.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return ((List.range steps).map (fun k => stateAt k)) ++ [(steps : Int)]\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "the per-step values are all correct, but the gather appends one EXTRA "
            "(duplicate final-state) record, so the list is one longer than the "
            "number of steps. The faithful real analogue is a gather with an "
            "off-by-one loop bound / a spurious trailing yield: every scenario that "
            "asserts the exact list of gathered records (length and contents) fails "
            "because there is one extra entry. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from (E2) out.length = steps (the rival's length is steps + 1). "
            "Targets the cardinality facet that the per-element pin alone would not "
            "catch. Refuted at steps = 2, where the rival gives [1, 2, 2] of length "
            "3 ≠ 2."
        ),
        "witness": _tester(
            "example : gatherWalkTester 2 = false := by\n"
            "  decide\n"),
    },
    {
        "id": "uniq-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Same multiset of per-step values but in REVERSED index order.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return ((List.range steps).map (fun k => stateAt k)).reverse\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "records the SAME multiset of per-step values but in reversed index "
            "order. A value proxy keyed on the set/sum of records would accept it; "
            "only the per-INDEX clause catches that the k-th gathered record must be "
            "the k-th step's state. The faithful real analogue gathers the "
            "enumerator's yields in the wrong order, so the ordered list comparison "
            "fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from (E3) at index 0 for steps ≥ 2 (out[0]! = steps ≠ 1). "
            "Targets the index/order facet — a permutation the per-index pin "
            "defeats. Refuted at steps = 3, where the rival gives [3, 2, 1] but "
            "out[0]! must be 1; a step count of 3 also moves the sole binder off "
            "the values the other rivals probe."
        ),
        "witness": _tester(
            "example : gatherWalkTester 3 = false := by\n"
            "  decide\n"),
    },
    {
        "id": "uniq-small-count-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by the adversarial audit (attack D). Every rival above diverges
        # from the spec at the very step count its own witness names, so a spec
        # that only pinned the clauses for `steps <= 3` would reject all five.
        # This rival is behaviourally GOLD on every step count the rest of the
        # battery witnesses (1, 2, 3) and collapses only once the walk is longer,
        # so it is refutable only ABOVE that range: it probes that the two
        # clauses are pinned for EVERY `steps`, not merely on the small
        # neighbourhood the other witnesses inhabit.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    return (if steps ≤ 3 then (List.range steps).map (fun k => stateAt k)\n"
                  "            else List.replicate steps (0 : Int))\n"),
            _PROOF_GOLD, _PROOF_FLAT),
        "refinement": (
            "gathers the genuine per-step history only for short walks and "
            "collapses every record to a constant once the walk is longer. The "
            "faithful real analogue is a gather that keeps independent per-step "
            "records only while the enumerator stays inside some small "
            "fast-path and reverts to handing out one shared record beyond it: "
            "the scenarios whose walks are short still pass, while every longer "
            "gather reads back as the constant. Those longer scenarios — the "
            "ones whose expected value is the distinct per-step history — still "
            "fail, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from (E3) out[i]! = stateAt i, but only OUTSIDE the step "
            "counts the other five witnesses use: this rival is observationally "
            "identical to gold at steps = 1, 2, 3 (measured: its tester is "
            "provably `true` at 2 and 3, exit 0 each), so none of the existing "
            "witnesses can refute it. Refuted at steps = 4, where it gives "
            "[0, 0, 0, 0] but out[0]! must be 1. Verifying would be "
            "SPEC-TOO-WEAK in the step count: it would mean the clauses were "
            "pinned only on the small neighbourhood the battery already probed."
        ),
        "witness": _tester(
            "example : gatherWalkTester 4 = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness rivals — of which one is a
# non-termination case) plus 2 AXIOM_TESTS. This velvet bundle models the SAME
# purely-functional core (the single `gatherWalk` method), so the value surface
# (which per-step values are gathered, in what order, at what length) carries
# across intact.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-direct              -> pos-control-direct                PORTED
#   admiss-3-step-walk              -> admiss-postimage-nondegenerate    RE-AIMED
#   uniq-aliasing-collapse          -> uniq-aliasing-collapse            PORTED
#   uniq-off-by-one-snapshot        -> uniq-off-by-one-snapshot          PORTED
#   uniq-partial-first-element      -> uniq-partial-first-element        PORTED
#   uniq-length-divergence          -> uniq-length-divergence            PORTED
#   uniq-reversed-order             -> uniq-reversed-order               PORTED
#   uniq-nonterminating             -> (none)                            SPEC-CLOSED
#   ax-ref-copy-soundness/-cont.    -> (none)                            DROPPED (G-AX lane)
#   (no sibling case)               -> uniq-small-count-only             ADDED (audit)
#
# 6 ported, 1 re-aimed, 1 added by audit, 1 known-hole, 2 axiom-lane dropped.
#
# ADDED BY THE ADVERSARIAL AUDIT (uniq-small-count-only). Attack D on the ported
#   battery found that all five ported rivals diverge from the spec at the very
#   step count their own witness names, leaving the UPPER end of the sole binder
#   unprobed: a rival faithful on the witnessed neighbourhood (1, 2, 3) and wrong
#   beyond it was refutable by no existing witness. The added rival occupies
#   exactly that gap (measured: its tester is provably `true` at steps = 2 and
#   3 — exit 0 each — so it is observationally gold there; refuted at steps = 4).
#   It did NOT verify against the frozen spec, so this is a battery gap the audit
#   closed, not a spec hole.
#
# ATTACK E (spec-too-strong probe) — the frozen spec accepts every faithful
#   correct reshape tried, so no soundness hole was found. Measured, each a full
#   variant sharing the frozen spec: `return walkSeq steps` (exit 0);
#   `(List.range' 0 steps).map (fun k => stateAt k)` (exit 0);
#   `(List.range steps).map stateAt`, eta-reduced (exit 0); and a FORWARD
#   accumulator loop (`i` from 0 up, appending `stateAt i`, invariant
#   `result = (List.range' 0 i).map (fun k => stateAt k)`) — exit 0, which is the
#   load-bearing one, since it reshapes the loop DIRECTION the frozen proof's
#   gather_step lemma is tuned to and still closes.
#   ONE reshape could not be closed and is recorded as UNCERTAIN, not a hole:
#   `(List.range steps).map (fun k => (k : Int) + 1)`, which inlines `stateAt`'s
#   body instead of naming it. Four proof scripts were tried (exit 1 each). The
#   residual goal shows the obstacle is not the spec but the extracted term:
#   `List.map (fun k => k + 1) (do let a <- List.range steps; pure a)` — the
#   coercion elaborates to a monadic bind the available `simp`/`grind` sets do not
#   normalize, and the needed `List.bind_pure_comp` is not a constant in this
#   toolchain. Since the eta-reduced and `walkSeq` forms both verify, the spec is
#   very unlikely to be rejecting the BEHAVIOUR; the honest verdict is that this
#   author could not close the proof.
#
# RE-AIMED (admissibility): the sibling re-derives the precondition (steps >= 0)
#   for a normal 3-step F2P-shaped input. This method declares no `require`
#   clause, so that probe is vacuous — nothing could exclude an in-domain input.
#   It is re-aimed at the residual admissibility risk on a total domain: that the
#   post-image is degenerate at the interesting point. The case discharges an
#   in-region assert pinning the modeled per-step observable of a 3-step walk to
#   the strictly-increasing distinct values [1, 2, 3] — the per-step history the
#   fix installs, not a collapsed constant.
#
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# VACUOUS (frame-mutation): the sibling class targets a read-only input carrying
#   a fractional heap permission. This backend is referentially transparent: the
#   sole input `steps` is an immutable `Nat` value, there is no `mut` binder among
#   the inputs, and there is no heap or aliasing. The only ownership predicate in
#   the sibling is on the freshly-built OUTPUT (nothing to overwrite to satisfy
#   the postcondition vacuously). No read-only input to mutate, no permission
#   system to trip, so the class is vacuous. No substitute is fabricated (per the
#   porting map, this class is legitimately dropped rather than replaced).
#
# DROPPED (ax-ref-copy-*): the sibling's two AXIOM_TESTS validate the A-reference
#   deep model (`snap = work` by-value capture <-> `dict.copy()` per yield)
#   against the real `partitions` generator. This bundle models the record
#   duplication DEEPLY (recording `snap := stateAt (i-1)` by value); mapping.md §3
#   states there is NO consumed axiom, and the A-reference validation is G-AX's
#   job (axiom_check.py). This gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The sole input binder `steps` is varied by the reject
#   witnesses across step counts 1, 2, 3, 4 (4 distinct points); the
#   index binder i of clause (E3) is exercised down to i = 0 (the off-by-one and
#   first-element rivals fail there) and at the terminal position (the reversed
#   rival). Clause (E2) out.length = steps is attacked by uniq-length-divergence;
#   clause (E3) out[i]! = stateAt i is attacked by aliasing-collapse, off-by-one,
#   partial-first-element and reversed-order across distinct sub-domains. Rivals
#   that happen to share a step count (2) fail there for DIFFERENT reasons
#   (collapse: wrong value everywhere; first-element: wrong only at i = 0; length:
#   wrong cardinality), so none is a near-miss riding another's witness.
#
# AXIOM_TESTS: empty. The record duplication is modeled deeply (no axiomatized
#   callee); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
