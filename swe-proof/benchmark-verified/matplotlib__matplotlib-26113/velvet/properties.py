"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26113 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct accumulateBins`` obligation survives with a byte-
identical header) and swaps in a candidate implementation; it is checked by the
real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the ``witness_reference`` — a loop-free impl of the same frozen spec that the
gate independently checks VERIFIES (see ``_WITNESS_REF``; the frozen impl cannot
serve as that subject here, and the audit note there records why with the exit
codes that measured it).

DEFENDED SURFACE (one contracted method over three read-only inputs):

  accumulateBins (reduceBin : List Float → Float) (minPop : Nat)
                 (bins : List (List Float)) return (out : List (Option Float))
    ensures out = aggregateSeq reduceBin minPop bins                     (C1)

The operation collapses each group of values to a single aggregate when the
group is populated ENOUGH — its size reaches the minimum population — and
otherwise leaves the group empty (no aggregate). ``aggregateSeq`` is a fully
transparent front-recursive ``def`` (NOT an opaque oracle): per group, it emits
``some (reduceBin group)`` exactly when ``group.length ≥ minPop`` and ``none``
otherwise, in order, for every group. The single top-level ``ensures`` clause
pins three facets at once: (a) the POPULATION-THRESHOLD selection rule — a group
is aggregated iff its size is AT LEAST the minimum (the boundary group whose
size EQUALS the minimum is aggregated, not dropped); (b) the aggregate emitted
for a kept group is produced from THAT group; (c) every group contributes, in
order, so the output has one entry per input group. All three are grounded in
the three input binders via ``aggregateSeq reduceBin minPop bins``; there is no
answer key to echo (``aggregateSeq``/``binAggregate`` are concrete ``def``s, and
the ``axioms`` region is empty). The method has NO ``require`` clause, so the
admitted domain is total.

CARRIER NOTE — the per-group aggregate is a ``Float`` and the bin reducer
``reduceBin`` is a FREE FUNCTION input. Two consequences shape every witness:

  * A group's aggregate VALUE is a ``Float`` produced by an arbitrary reducer;
    ``derive_tester_for`` needs a decidable postcondition, but equality on
    ``List (Option Float)`` reduces to ``Float`` equality, which ``decide`` will
    not compute (measured: the tester's ``Decidable`` instance stays stuck on
    ``Float`` equality). So the ``…Tester args = false`` route is UNAVAILABLE on
    this carrier.
  * What IS decidable without any ``Float`` fact is the STRUCTURE of the result:
    which entries are ``some`` vs ``none`` (``Option.isSome``), and the list's
    LENGTH. Every rival below either mis-selects which groups are kept (so its
    ``some``/``none`` pattern differs from ``aggregateSeq``'s) or drops a group
    (so its length differs). Each witness ``extract_program_for``s the rival
    (extraction needs no decidability — it just names ``accumulateBinsExec``) and
    states, at a concrete input built from a universally-quantified reducer ``r``,
    that the rival's RESULT differs from the transparent model:

        accumulateBinsExec r m bins ≠ DivM.res (aggregateSeq r m bins)

    proved by taking ``congrArg`` of the selection structure
    (``fun l => l.map Option.isSome``) or of ``List.length`` on the assumed
    equality and closing the false residual with ``simp [aggregateSeq,
    binAggregate]``. Because the reducer stays a free variable ``r``, each
    refutation holds for EVERY reducer — a strictly stronger statement than any
    single concrete reducer could make, and the reason the ``reduceBin`` binder
    is abused maximally rather than pinned. The frozen impl is a ``while`` loop
    whose extracted ``…Exec`` does NOT reduce under this script (the
    ``forIn``/invariant-gadget form stays stuck), so the frozen impl CANNOT serve
    as the discrimination subject: the failure there is a type mismatch at
    ``DivM.res.inj``, which occurs for a true claim too. Each witness is
    therefore refuted against ``_WITNESS_REF`` instead, where the residual is
    decided on the merits. Six of the eight witnesses bind only the fresh reducer
    ``r`` (NO hypotheses), so no consistency probe is needed; the
    order-sensitivity witness of ``weak-reverse-order``'s sibling
    ``weak-aggregate-provenance`` binds one reducer-disagreement hypothesis,
    whose satisfiability the gate's probe checks (measured: it does not derive
    ``False``).

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    holds ``occupancies`` at ``Acc(list_pred(occupancies), 1/2)`` and its
    MANDATORY frame rival overwrites that read-only input to trip INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: the three inputs
    are immutable values, this bundle declares NO ``mut`` parameter, and there is
    no heap, no aliasing, and no permission system to trip. There is no read-only
    input to overwrite and no substitute probe to fabricate, so the class is
    vacuous (per the porting map, legitimately dropped, not faked). Its ARGUMENT
    (a patch mutating the per-group value lists in place would corrupt the
    aggregate) has no value footprint the spec can force here — the output is
    read-only by construction (``out = aggregateSeq reduceBin minPop bins``, a
    fresh list).
  * UNGROUNDED-ORACLE ECHO — N/A. C1 is a total function of the three inputs
    (``aggregateSeq`` is a concrete ``def``, not an axiomatized oracle); there is
    no opaque answer key a wrong impl could echo. The cheapest correct impl
    returns ``aggregateSeq reduceBin minPop bins`` directly, covered honestly by
    a positive control.
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
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: rivals
    right on part of the domain but mis-selecting at the population boundary
    (prepatch strict, over-inclusive, first-group-only), ignoring the threshold
    (constant kept / constant empty), reordering the aggregates (reverse), or
    dropping the last group (length).

WITNESS PLACEMENT. The eight reject witnesses sit at EIGHT DISTINCT
``(minPop, bins)`` points — moving ``minPop`` over {0,1,2,3} and ``bins`` over
one-group (empty / singleton / two-value), two-group (both non-empty / one
empty), so no clause is demonstrated at a single pinned point (pts=8).
``reduceBin`` is a free variable in every witness (abused for all reducers at
once). Facet (a) the threshold selection rule is attacked by prepatch-strict,
over-inclusive, constant-kept, constant-empty and partial-first; facet (b) the
aggregate's provenance by aggregate-provenance; facet (c)/order by reverse;
facet (c)/length by drop-last.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the selection is
modeled directly by the pure ``def``s ``binAggregate``/``aggregateSeq``; the
reducer and the group populations are FREE INPUTS). There is nothing here for
this gate to probe, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26113"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean.
# The ENTIRE frozen backward-fold loop body (used for whole-body reject rivals
# and the straight-line positive controls).
_GOLD_IMPL = """    -- impl-start
    let mut result : List (Option Float) := []
    let mut i := bins.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ bins.length
      invariant result = aggregateSeq reduceBin minPop (bins.drop i)
      done_with i = 0
      decreasing i
    do
      let b := bins[i - 1]!
      result := binAggregate reduceBin minPop b :: result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# The loop guard alone (unique inside the impl region) — for the guard-reshape
# positive control that keeps the whole loop scaffold + framing invariants.
_GOLD_GUARD = "    while i > 0\n"
assert _BASE.count(_GOLD_GUARD) == 1, "loop-guard anchor drifted"

# The first line of the impl body — for prepending the admissibility assert.
_GOLD_IMPL_HEAD = "    -- impl-start\n    let mut result : List (Option Float) := []"
assert _BASE.count(_GOLD_IMPL_HEAD) == 1, "impl-head anchor drifted"

# The single loop-body accumulation step — for the operator-form positive that
# keeps the whole loop scaffold but re-spells the per-bin decision.
_GOLD_STEP = "      result := binAggregate reduceBin minPop b :: result"
assert _BASE.count(_GOLD_STEP) == 1, "loop-step anchor drifted"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- backward-fold loop (it discharges the loop-body goal via the drop-step
# ---- lemma). A positive control that reshapes the impl away from that loop, or
# ---- re-spells the per-bin decision, must retune the tactic body; both the impl
# ---- region and the `prove_correct` body are elided from the spec view, so
# ---- same_spec still holds and the `prove_correct accumulateBins` obligation
# ---- survives with an identical header. Unique in the file.
_GOLD_PROOF = """prove_correct accumulateBins by
  loom_solve
  rw [aggregateSeq_drop_step reduceBin minPop bins i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted from expected text"

# A reshaped straight-line impl (no loop) leaves `loom_solve` a goal that closes
# without the loop-body drop-step lemma; retune to the bare tactic.
_PROOF_STRAIGHT = "prove_correct accumulateBins by\n  loom_solve"


def _reject(impl_body):
    """Full Solution.lean variant with ONLY the impl region body replaced by a
    straight-line rival (frozen tactic script kept — expected NOT to verify)."""
    return _swap(_BASE, _GOLD_IMPL,
                 "    -- impl-start\n" + impl_body + "\n    -- impl-end")


# ---- WITNESS REFERENCE (audit repair). Every witness below states its
# ---- refutation as `accumulateBinsExec … ≠ DivM.res (aggregateSeq …)` and
# ---- takes `congrArg` of a projection through `DivM.res.inj h`. Against the
# ---- FROZEN impl that script cannot even be STATED: the frozen `…Exec` is a
# ---- `while` loop, so it elaborates to an unreduced
# ---- `NonDetT.run (forIn Lean.Loop.mk …)` rather than to a `DivM.res _`, and
# ---- `DivM.res.inj h` fails with
# ---- `Application type mismatch: … but is expected to have type
# ---- DivM.res ?m = DivM.res ?m` (measured: exit 1 for all eight witnesses,
# ---- followed by `Invalid field notation: Type of l is not known`).
# ---- That is a TYPE error, not a refutation — the same error appears for a
# ---- claim that is TRUE of the frozen impl, so the gold-side exit code
# ---- discriminates nothing. Measured directly: the AGREEMENT claim
# ---- `accumulateBinsExec r 0 [[1.0]] = DivM.res (aggregateSeq r 0 [[1.0]])`
# ---- (the OPPOSITE of a refutation, and true of the prepatch-strict rival at
# ---- `minPop=0`) also elaborates against that rival (exit 0) and also fails
# ---- against the frozen impl (exit 1) — clearing both halves of the
# ---- discrimination check while asserting the rival is CORRECT. It is the
# ---- `_STUCK_REDUCTION` defect class arriving as a type mismatch instead of a
# ---- stuck `decide`, so the gate's own repair applies: refute each witness
# ---- against a `witness_reference` — a loop-free impl of the SAME frozen spec
# ---- that the gate independently checks shares the spec and VERIFIES.
# ---- `bins.map (binAggregate reduceBin minPop)` is that impl: point-free over
# ---- the frozen `binAggregate`, shape-distinct from every rival, and its
# ---- `…Exec` reduces to `pure (List.map …)` so the injection applies and the
# ---- residual is decided on the merits. Measured against this reference:
# ---- all eight witnesses fail SEMANTICALLY — `simp` reduces the projected
# ---- hypothesis to `True`, i.e. it PROVED the equation for the reference and
# ---- could not for the rival (a `reveal` probe replacing the closing step with
# ---- `exact (h3 : Nat)` prints `h3 : True` against the reference and, for the
# ---- provenance case, the CONCRETE equation `r [2.0,1.0] = r [1.0,2.0]`
# ---- against the rival) — the reference itself
# ---- verifies (exit 0), and the forged agreement claim above ELABORATES
# ---- against it (exit 0) — so that forgery is now caught as
# ---- `witness-vacuous` instead of being recorded as a refutation.
_WITNESS_REF = _swap(
    _swap(_BASE, _GOLD_IMPL,
          "    -- impl-start\n"
          "    return bins.map (binAggregate reduceBin minPop)\n"
          "    -- impl-end"),
    _GOLD_PROOF,
    "prove_correct accumulateBins by\n"
    "  loom_solve\n"
    "  induction bins with\n"
    "  | nil => simp [aggregateSeq]\n"
    "  | cons b bs ih => simp [aggregateSeq, ih]\n")


# ---- witness preambles. Both reach the rival's extracted program (extraction
# ---- needs no decidability — it just names `accumulateBinsExec`) and state, at
# ---- a concrete input built from a universally-quantified reducer `r`, that the
# ---- rival's result differs from the transparent model `aggregateSeq`. Checked
# ---- in a file whose `prove_correct` block is stripped; no
# ---- `axiom`/`sorry`/`native_decide`.
#
# STRUCTURE discriminator (`Option.isSome`): closes when the rival keeps/drops a
# different set of groups than the threshold rule dictates.
def _witness_isSome(binders, inp):
    return (
        "extract_program_for accumulateBins\n\n"
        f"example {binders} :\n"
        f"    accumulateBinsExec {inp}\n"
        f"      ≠ DivM.res (aggregateSeq {inp}) := by\n"
        "  unfold accumulateBinsExec accumulateBins\n"
        "  intro h\n"
        "  have h3 := congrArg (fun l => l.map Option.isSome) (DivM.res.inj h)\n"
        "  simp [aggregateSeq, binAggregate] at h3\n")


# LENGTH discriminator: closes when the rival emits a list of the wrong length
# (a dropped group), without needing any per-entry fact.
def _witness_len(binders, inp):
    return (
        "extract_program_for accumulateBins\n\n"
        f"example {binders} :\n"
        f"    accumulateBinsExec {inp}\n"
        f"      ≠ DivM.res (aggregateSeq {inp}) := by\n"
        "  unfold accumulateBinsExec accumulateBins\n"
        "  intro h\n"
        "  have h3 := congrArg List.length (DivM.res.inj h)\n"
        "  simp [aggregateSeq, binAggregate] at h3\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded model `aggregateSeq reduceBin minPop bins` directly. It is a
        # total function of the three inputs (no opaque answer key), so this is a
        # correct impl, not an echo. The residual goal is definitional, closed by
        # a bare `loom_solve` (the loop-body drop-step lemma is no longer needed
        # and is dropped — the tactic body is elided from the spec view, so
        # same_spec and the obligation header are untouched).
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL,
                  "    -- impl-start\n"
                  "    return aggregateSeq reduceBin minPop bins\n"
                  "    -- impl-end"),
            _GOLD_PROOF, _PROOF_STRAIGHT),
        "rationale": "a straight-line `return aggregateSeq reduceBin minPop bins` "
                     "is the simplest correct impl; it meets C1 by definition. If "
                     "it fails to verify the postcondition is over-fit to the loop "
                     "form => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-not-lt-form",
        "kind": "soundness",
        "expect": "verify",
        # Keep the ENTIRE backward-fold scaffold and both framing invariants
        # VERBATIM, but re-spell the per-group decision: instead of the frozen
        # `binAggregate` (whose guard is `bin.length ≥ minPop`), inline the
        # logically-equivalent `¬ (b.length < minPop)` form. Same behaviour,
        # different operator shape; the loop invariant now discharges from the
        # not-less-than spelling by pure `Nat` reasoning, so the tactic body is
        # retuned to fold `binAggregate` and `Nat.not_lt` (the obligation header
        # is untouched). If this CORRECT impl fails to verify, the spec is over-fit
        # to the literal `≥` operator => SPEC-TOO-STRONG.
        "module": _swap(
            _swap(_BASE, _GOLD_STEP,
                  "      result := (if ¬ (b.length < minPop) then some (reduceBin b) "
                  "else none) :: result"),
            _GOLD_PROOF,
            "prove_correct accumulateBins by\n"
            "  loom_solve\n"
            "  rw [aggregateSeq_drop_step reduceBin minPop bins i (by omega) (by omega)]\n"
            "  simp only [binAggregate, Nat.not_lt, ge_iff_le]\n"
            "  simp_all\n"),
        "rationale": "the per-group decision re-spelled as `¬ (b.length < minPop)` "
                     "(the same integer relation as the frozen `≥ minPop` guard); "
                     "the entire backward-fold scaffold and both framing invariants "
                     "are kept verbatim. Must verify, else the spec is over-fit to "
                     "the `≥` spelling of the threshold => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-guard-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Keep the ENTIRE backward-fold scaffold, both framing invariants and the
        # per-group decision VERBATIM, but rewrite the loop guard `i > 0` as the
        # logically-equivalent `¬ (i = 0)`. Same behaviour, different guard shape;
        # the frozen invariant discharges exactly as before, so the frozen proof
        # is kept unchanged.
        "module": _swap(_BASE, _GOLD_GUARD, "    while ¬ (i = 0)\n"),
        "rationale": "the loop guard `i > 0` rewritten as the equivalent "
                     "`¬ (i = 0)`; the backward-fold scaffold, both framing "
                     "invariants and the front-recursive drop-step proof are kept "
                     "verbatim. Must verify, else the spec is over-fit to the `>` "
                     "spelling of the guard => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # nagini "a self-call on an F2P-shaped input satisfies the precondition" probe
    # is vacuous on the total domain — nothing could exclude any input. The
    # analogue on a TOTAL carrier is the obligation being UNSATISFIABLE at exactly
    # an F2P-shaped input, so this case discharges the obligation at that concrete
    # input, by evaluation, as an in-region `assert`, before closing the frozen
    # obligation verbatim.
    #
    # AUDIT REPAIR — the previous form of this case asserted only that the emitted
    # LENGTH varies with the input:
    #
    #   (aggregateSeq (fun _ => 0.0) 1 [[1.0]]).length = 1 ∧
    #   (aggregateSeq (fun _ => 0.0) 1 ([] : List (List Float))).length = 0
    #
    # That assert is LIVE (measured: falsifying the `= 1` to `= 99` makes the
    # module fail, exit 1) but it is BLIND TO THE THRESHOLD RULE the spec exists to
    # pin: the output has one entry per input group whatever the selection decides,
    # so the length is 1 whether the group is kept or dropped. Measured directly —
    # the identical length claim at `minPop=2`, where that group is DROPPED
    # (`[none]`, not `[some _]`), also verifies (exit 0). So the old assert would
    # have discharged just as happily against a spec that dropped the boundary
    # group, i.e. against the pre-change selection rule, and it tested nothing this
    # battery's reject lane needs.
    #
    # Re-aimed at the F2P-shaped point itself: pin the aggregate sequence's VALUE
    # (not its length) at the boundary population — where the group's population
    # EQUALS the minimum, which is the one input the whole reject surface turns on
    # — and at the neighbouring drop and empty points. Measured: this discharges
    # (exit 0) and, with the boundary entry flipped to the pre-change `[none]`,
    # FAILS (exit 1) — so unlike the length form it can actually see the selection
    # rule. `loom_solve` now leaves the assert as its own goal ahead of the loop
    # body goal, so the tactic body is retuned to close it by evaluation first
    # (the tactic body is elided from the spec view; the obligation header and the
    # frozen loop are untouched, so C1 still discharges verbatim).
    # =====================================================================
    {
        "id": "admiss-boundary-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _GOLD_IMPL_HEAD,
                "    -- impl-start\n"
                "    assert (with_name_prefix `adm\n"
                "      (aggregateSeq (fun _ => (0.0:Float)) 1 [[(1.0:Float)]] "
                "= [some (0.0:Float)] ∧\n"
                "       aggregateSeq (fun _ => (0.0:Float)) 2 [[(1.0:Float)]] = [none] ∧\n"
                "       aggregateSeq (fun _ => (0.0:Float)) 1 ([] : List (List Float)) = []))\n"
                "    let mut result : List (Option Float) := []"),
            _GOLD_PROOF,
            "prove_correct accumulateBins by\n"
            "  loom_solve\n"
            "  · simp [aggregateSeq, binAggregate]\n"
            "  · rw [aggregateSeq_drop_step reduceBin minPop bins i (by omega) "
            "(by omega)]\n"
            "    simp_all\n"),
        "rationale": "the obligation is SATISFIABLE at the F2P-shaped input — the "
                     "group whose population EQUALS the minimum. The in-region "
                     "assert discharges, by evaluation, that at that boundary point "
                     "the modeled sequence is `[some aggregate]` (the group is "
                     "KEPT), that one population short of it the sequence is "
                     "`[none]`, and that the empty input maps to the empty "
                     "sequence; then the frozen obligation is closed verbatim. If "
                     "the assert could not discharge, the spec would be "
                     "unsatisfiable at exactly the input the operation is defined "
                     "for => PRECOND-TOO-STRONG. Unlike a claim about the emitted "
                     "LENGTH (which is one-per-group whatever the selection "
                     "decides, and so discharges equally against the pre-change "
                     "rule), this pins the boundary VALUE and therefore actually "
                     "exercises the threshold rule.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line impl carrying a machine-checked
    # refutation witness at a DISTINCT concrete `(minPop, bins)` point and the
    # refinement argument that its faithful real counterpart would NOT resolve the
    # failing test `test_hexbin_mincnt_behavior_upon_C_parameter[png]`.
    # =====================================================================
    {
        "id": "weak-prepatch-strict",
        "kind": "uniqueness",
        "expect": "reject",
        # THE regressed shape: aggregate a group only when its population is
        # STRICTLY GREATER than the minimum (`>`), dropping the boundary group
        # whose population EQUALS the minimum. Correct only away from the boundary;
        # wrong at population == minPop.
        "module": _reject(
            "    return bins.map (fun b => if b.length > minPop then some (reduceBin b) "
            "else none)"),
        "refinement": "this is the pre-change behavior — the strict comparison at "
                      "the population boundary. On the failing test the minimum "
                      "population is one and there are groups whose population is "
                      "exactly one: this rival drops them (value-aggregation "
                      "regime) while the bare-count regime keeps them, so the two "
                      "renders DIFFER and the check-figures-equal assertion FAILS. "
                      "It would NOT resolve (this is exactly the bug the change "
                      "fixes).",
        "rationale": "REJECT from C1 facet (a) (the threshold selection rule): at "
                     "the boundary population == minPop the spec keeps the group "
                     "(`some`), the rival drops it (`none`). Refuted at "
                     "`minPop=1, bins=[[1.0]]` (population 1 == minPop 1): gold "
                     "resolves `[some (r [1.0])]`, the rival `[none]` — their "
                     "`isSome` patterns `[true]` vs `[false]` differ.",
        "witness": _witness_isSome("(r : List Float → Float)", "r 1 [[(1.0:Float)]]"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-over-inclusive",
        "kind": "uniqueness",
        "expect": "reject",
        # The opposite-direction off-by-one: aggregate a group when its population
        # reaches ONE LESS than the minimum (`≥ minPop - 1`), keeping a group the
        # spec drops. Correct away from the boundary; wrong at population == minPop-1.
        "module": _reject(
            "    return bins.map (fun b => if b.length ≥ minPop - 1 then some (reduceBin b) "
            "else none)"),
        "refinement": "an over-relaxed threshold that keeps groups one population "
                      "short of the minimum. It aggregates sparse groups the bare-"
                      "count regime clears, so the value-aggregation render shows "
                      "spurious cells the count render does not and the check-"
                      "figures-equal assertion FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (a): at population == minPop-1 the spec "
                     "drops the group (`none`), the rival keeps it (`some`). "
                     "Refuted at `minPop=1, bins=[[]]` (population 0 == minPop-1): "
                     "gold resolves `[none]`, the rival `[some (r [])]` — `isSome` "
                     "`[false]` vs `[true]`. Varies `bins` to an EMPTY group and "
                     "`minPop` to the low end no other witness pins here.",
        "witness": _witness_isSome("(r : List Float → Float)", "r 1 [([] : List Float)]"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-constant-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the threshold entirely: aggregate EVERY group (always `some`),
        # regardless of population. Applies the reducer to the empty list to keep
        # the shape well-typed (the VALUE is irrelevant — the witness discriminates
        # on `some` vs `none`, not on the aggregate).
        "module": _reject("    return bins.map (fun _ => some (reduceBin []))"),
        "refinement": "drops the population guard entirely so every group is "
                      "aggregated. The value-aggregation render then keeps every "
                      "hexagon — including the empty out-of-data cells the minimum "
                      "population is meant to drop — while the bare-count render "
                      "drops them, so the two DIFFER and the check-figures-equal "
                      "assertion FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (a): on any UNDER-populated group the "
                     "spec emits `none`, the rival emits `some`. Refuted at "
                     "`minPop=2, bins=[[1.0]]` (population 1 < minPop 2): gold "
                     "resolves `[none]`, the rival `[some (r [])]` — `isSome` "
                     "`[false]` vs `[true]`. Varies `minPop` to 2.",
        "witness": _witness_isSome("(r : List Float → Float)", "r 2 [[(1.0:Float)]]"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-constant-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror: ignore the threshold the OTHER way — never aggregate any
        # group (always `none`). Wrong on any group the spec keeps.
        "module": _reject("    return bins.map (fun _ => none)"),
        "refinement": "never aggregates any group, so the value-aggregation render "
                      "shows NO cells while the bare-count render shows the "
                      "populated ones — the two DIFFER and the check-figures-equal "
                      "assertion FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (a): on any group whose population "
                     "reaches the minimum the spec emits `some`, the rival emits "
                     "`none`. Refuted at `minPop=0, bins=[[]]` (population 0 ≥ "
                     "minPop 0, so kept): gold resolves `[some (r [])]`, the rival "
                     "`[none]` — `isSome` `[true]` vs `[false]`. Varies `minPop` to "
                     "0 (the kept-empty-group edge no other witness reaches).",
        "witness": _witness_isSome("(r : List Float → Float)", "r 0 [([] : List Float)]"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-partial-first-group",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (first group): correct on every group EXCEPT index 0, for
        # which it uses the pre-change strict `>` (dropping a boundary first group
        # the spec keeps). Diverges only on the first-group sub-domain — the kind of
        # bug a fuzzer that only checks "most" groups misses.
        "module": _reject(
            "    return bins.zipIdx.map (fun (b, k) => if k = 0 then "
            "(if b.length > minPop then some (reduceBin b) else none) "
            "else binAggregate reduceBin minPop b)"),
        "refinement": "special-cases the first group with the pre-change strict "
                      "comparison. When the first group's population is exactly the "
                      "minimum it is dropped from the value-aggregation render but "
                      "kept in the count render, so the check-figures-equal "
                      "assertion FAILS at that cell. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (a) restricted to index 0: at the first "
                     "group with population == minPop the spec keeps it (`some`), "
                     "the rival drops it (`none`), while later groups are correct. "
                     "Refuted at `minPop=1, bins=[[1.0], [2.0]]`: gold resolves "
                     "`[some (r [1.0]), some (r [2.0])]`, the rival "
                     "`[none, some (r [2.0])]` — `isSome` `[true,true]` vs "
                     "`[false,true]`. A first-group drop distinct from the whole-"
                     "domain prepatch rival.",
        "witness": _witness_isSome("(r : List Float → Float)",
                                   "r 1 [[(1.0:Float)], [(2.0:Float)]]"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the correct per-group decision to every group, but emit the results
        # in REVERSED group order. Correct only when the emitted list is a
        # palindrome of `some`/`none`; wrong when reversal changes the pattern.
        "module": _reject(
            "    return (bins.reverse).map (fun b => binAggregate reduceBin minPop b)"),
        "refinement": "reverses the group order of the aggregate sequence. The "
                      "downstream render places each aggregate at its hexagon's "
                      "grid position, so a reversed sequence maps aggregates to the "
                      "WRONG cells and the rendered figure DIFFERS from the count "
                      "render pixel-for-pixel — the check-figures-equal assertion "
                      "FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (c) (order/per-position correspondence): "
                     "the spec pins each group's aggregate to its position, the "
                     "rival transposes them. Refuted at `minPop=1, "
                     "bins=[[1.0], []]`: gold resolves `[some (r [1.0]), none]`, "
                     "the rival `[none, some (r [1.0])]` — `isSome` `[true,false]` "
                     "vs `[false,true]`. The only rival attacking ORDER; varies "
                     "`bins` to a mixed populated/empty two-group shape. The "
                     "reducer input `reduceBin` is left a FREE variable `r` here "
                     "(as in every witness), so the refutation holds for ALL "
                     "reducers rather than pinning `reduceBin` to a value.",
        "witness": _witness_isSome("(r : List Float → Float)",
                                   "r 1 [[(1.0:Float)], ([] : List Float)]"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-drop-last-group",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (length): decide every EMITTED group correctly but DROP
        # the final group, returning a list one entry short. Meets facet (a)/(b)
        # on the groups it emits but violates facet (c) (one entry per group).
        "module": _reject(
            "    return (bins.take (bins.length - 1)).map "
            "(fun b => binAggregate reduceBin minPop b)"),
        "refinement": "omits the last group from the aggregate sequence (an off-by-"
                      "one over the group list). The rendered figure is missing the "
                      "final hexagon's cell, so the check-figures-equal comparison "
                      "against the count render FAILS. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (c) (one entry per group / length): the "
                     "spec emits one entry per input group, the rival emits one "
                     "fewer. Refuted at `minPop=3, bins=[[1.0], [2.0]]`: gold "
                     "resolves a length-2 list, the rival a length-1 list — "
                     "discriminated by `List.length`, no per-entry fact needed. The "
                     "only rival attacking LENGTH; varies `minPop` to 3.",
        "witness": _witness_len("(r : List Float → Float)",
                                "r 3 [[(1.0:Float)], [(2.0:Float)]]"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-aggregate-provenance",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION — facet (b), the aggregate's PROVENANCE, which the
        # battery previously recorded as "not attackable in isolation on this
        # carrier". It is: this rival keeps EXACTLY the right groups (the
        # `≥ minPop` selection is verbatim) and emits one entry per group in
        # order, so facets (a) and (c) are satisfied and NO `isSome`/length
        # projection can see it — but it builds each aggregate from a PERMUTED
        # copy of the group (`reduceBin b.reverse`) instead of from the group the
        # spec names. The refutation needs the reducer to be able to TELL two
        # arrangements apart, which is not a theorem for a free `r` — so, unlike
        # the other six, this witness CONDITIONS on the carrier: it states the
        # refutation at a point described by hypothesis
        # (`hr : r [1.0, 2.0] ≠ r [2.0, 1.0]`) rather than at one it computes.
        # That is legitimate exactly when the hypothesis is satisfiable, which is
        # what the gate's consistency probe checks; measured, the probe FAILS to
        # derive `False` from `hr` alone (exit 1 against both the reference and
        # the frozen impl), so the counterexample input exists.
        "module": _reject(
            "    return bins.map (fun b => if b.length ≥ minPop then "
            "some (reduceBin b.reverse) else none)"),
        "refinement": "aggregates each kept group from a REARRANGED copy of that "
                      "group's values rather than from the values as collected. "
                      "For an order-sensitive reducer the aggregate is a different "
                      "number, so the value-aggregation render colours that cell "
                      "differently from the reference render and the check-figures-"
                      "equal assertion FAILS. It would NOT resolve: the selection "
                      "is right but the aggregate is computed from the wrong "
                      "arrangement.",
        "rationale": "REJECT from C1 facet (b) (the aggregate is produced from ITS "
                     "OWN group, as given): the spec pins each kept entry to "
                     "`some (reduceBin group)`, the rival emits "
                     "`some (reduceBin group.reverse)`. Selection and length are "
                     "untouched, so this is the one rival no `isSome`/`length` "
                     "projection can catch — it is discriminated by projecting the "
                     "aggregate VALUE out with `Option.getD`. Refuted at "
                     "`minPop=1, bins=[[1.0, 2.0]]` under the satisfiable "
                     "hypothesis that the reducer distinguishes the two "
                     "arrangements of that group; a two-VALUE group, the shape no "
                     "other witness uses (all others use groups of size ≤ 1, where "
                     "reversal is invisible).",
        # The value-projection discriminator: push `Option.getD` through the
        # assumed equality so the residual is the reducer disagreement `hr`
        # refutes. Measured: elaborates against the rival (exit 0) and fails
        # against the verifying reference with the SEMANTIC residual
        # `hr : ¬r [1.0,2.0] = r [2.0,1.0] ⊢ False` (exit 1).
        "witness": (
            "extract_program_for accumulateBins\n\n"
            "example (r : List Float → Float)\n"
            "    (hr : r [(1.0:Float), (2.0:Float)] ≠ r [(2.0:Float), (1.0:Float)]) :\n"
            "    accumulateBinsExec r 1 [[(1.0:Float), (2.0:Float)]]\n"
            "      ≠ DivM.res (aggregateSeq r 1 [[(1.0:Float), (2.0:Float)]]) := by\n"
            "  unfold accumulateBinsExec accumulateBins\n"
            "  intro h\n"
            "  have h3 := congrArg (fun l => l.map (fun o => o.getD (r [(1.0:Float)]))) "
            "(DivM.res.inj h)\n"
            "  simp [aggregateSeq, binAggregate] at h3\n"
            "  exact hr h3.symm\n"),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 5 uniqueness
# rivals) plus 2 AXIOM_TESTS. The sibling contracts
# `populated_bins(occupancies: List[int], threshold: int) -> List[bool]`,
# abstracting each per-hexagon C-value list to its occupancy (an int) and the
# accum entry to a bool populated-flag; it returns the per-bin flags. This bundle
# models the SAME selection rule but keeps the payload richer: each group is a
# `List Float`, and the per-group result is `Option Float` (`some aggregate` when
# kept, `none` when dropped) — the faithful model of "a real aggregate vs np.nan".
# The reducer is a FREE FUNCTION input. So the sibling's occupancy-only rivals
# re-express against this carrier, and two facets the sibling folds into its
# per-element bool (order and the aggregate's provenance) become separately
# attackable here.
#
#   sibling case (nagini)              -> here
#   ---------------------------------------------------------------------
#   pos-decision-count-form             -> pos-not-lt-form               RE-SHAPED
#   pos-oracle-local-reshape            -> pos-direct-model              RE-SHAPED
#   admiss-selfcall                     -> admiss-boundary-satisfiable   RE-AIMED
#   rival-frame-mutate-occupancies(MAND)-> (none)                        VACUOUS
#   rival-prepatch-strict-gt            -> weak-prepatch-strict          PORTED
#   rival-off-by-one-over-inclusive     -> weak-over-inclusive           PORTED
#   rival-constant-true                 -> weak-constant-kept            PORTED
#   (constant-false, implicit mirror)   -> weak-constant-empty           ADDED
#   rival-partial-first-bin             -> weak-partial-first-group      PORTED
#   rival-drop-last-bin                 -> weak-drop-last-group          PORTED
#   (no sibling counterpart)            -> weak-reverse-order            ADDED
#   (no sibling counterpart)            -> weak-aggregate-provenance     ADDED (audit)
#
# 8 ported/re-aimed, 1 vacuous, 3 added (constant-empty mirror; reverse-order;
# aggregate-provenance, added by the audit to close facet (b), which this battery
# had recorded as inexpressible — see the coverage note above).
# Plus a THIRD positive (pos-guard-reshape) added — a guard re-spelling that
# keeps the frozen proof verbatim, cheap defence of C1 against loop-form
# over-fitting.
#
# RE-SHAPED (positives): the sibling's `pos-decision-count-form` computes the
#   flag as `not (occ < t)` instead of `occ >= t`; the analog here inlines
#   `¬ (b.length < minPop)` in place of the frozen `≥ minPop` guard (retuning the
#   tactic body, elided from the spec view). The sibling's `pos-oracle-local-
#   reshape` computes via the grounded oracle directly; the analog here drops the
#   loop and returns the grounded model `aggregateSeq reduceBin minPop bins`.
# RE-AIMED (admissibility): the sibling establishes a self-call on an F2P-shaped
#   input satisfies the read-only half-permission precondition. This method has
#   NO `require` clause, so nothing could exclude any input on the total domain —
#   that probe is vacuous in its literal form. The analogue on a TOTAL carrier is
#   the obligation being UNSATISFIABLE at exactly an F2P-shaped input, so the case
#   discharges the obligation AT that input, by evaluation, as an in-region assert
#   before closing the frozen obligation verbatim. Re-aimed BY THE AUDIT from the
#   emitted LENGTH to the boundary VALUE: the length form was live but blind to
#   the threshold rule (the output is one entry per group whatever the selection
#   decides, so the identical length claim also discharges at a `minPop` where
#   that group is DROPPED — measured, exit 0), whereas pinning
#   `aggregateSeq _ 1 [[1.0]] = [some _]` fails (exit 1) when flipped to the
#   pre-change `[none]`.
# PORTED (rivals): prepatch strict `>`, over-inclusive `≥ minPop-1`, constant-
#   kept (the sibling's constant-True), partial-first-group, and drop-last-group
#   port their sibling arguments directly onto the richer `Option Float` carrier
#   — the sibling's per-bin bool becomes this bundle's `some`/`none` selection,
#   discriminated by `Option.isSome` (or by `List.length` for the length rival).
# ADDED: (1) weak-constant-empty — the mirror of constant-kept (always `none`),
#   attacking the kept sub-domain the sibling's constant-True leaves to the other
#   direction; it isolates the kept-empty-group edge at `minPop=0`. (2) weak-
#   reverse-order — this carrier keeps GROUP ORDER observable (the sibling's
#   List[bool] is equally ordered, but its rivals never attack order); the render
#   maps each aggregate to its grid cell, so a reversed sequence is a genuine
#   defect. No sibling counterpart; a real coverage gain for facet (c).
#   (3) weak-aggregate-provenance (AUDIT) — the richer payload makes the
#   aggregate's PROVENANCE observable in a way the sibling's per-bin bool cannot
#   be: a rival with the right selection and the right length can still build the
#   aggregate from a rearranged copy of the group. Refuted under a satisfiable
#   order-sensitivity hypothesis on the free reducer; the only rival no
#   `isSome`/`length` projection can catch, and the only witness in the battery
#   that needs the consistency probe.
# VACUOUS (rival-frame-mutate-occupancies, MANDATORY on nagini): the sibling
#   overwrites the read-only input `occupancies[i]`, held at Acc(list_pred(
#   occupancies), 1/2), to trip INSUFFICIENT PERMISSION before any postcondition
#   is considered. This backend is referentially transparent: the inputs are
#   immutable values, this bundle declares NO `mut` parameter, there is no heap,
#   no aliasing, and no permission system. There is no read-only input to
#   overwrite and no substitute probe to build, so the class is vacuous (per the
#   porting map, legitimately dropped, not fabricated). Its ARGUMENT (a patch
#   mutating the per-hexagon value lists in place would corrupt the aggregate) has
#   no value footprint the spec can force here — the output is read-only by
#   construction (`out = aggregateSeq reduceBin minPop bins`, a fresh list).
# DIVERGENCE lane - the class is CLOSED BY THE SEMANTICS here, and a diverging
#   rival is REJECTED rather than admitted. This bundle sets
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
# BINDER / CLAUSE COVERAGE. Input binders: `reduceBin`, `minPop`, `bins`. The
#   single top-level clause C1 (`out = aggregateSeq reduceBin minPop bins`) folds
#   three facets — (a) the population-threshold selection rule, (b) the aggregate
#   is produced from its own group, (c) one entry per group in order. C1 is
#   DEFENDED by the three positive controls and the admissibility case and
#   ATTACKED by all eight rivals: facet (a) by weak-prepatch-strict, weak-over-
#   inclusive, weak-constant-kept, weak-constant-empty, weak-partial-first-group;
#   facet (b) by weak-aggregate-provenance; facet (c)/order by weak-reverse-order;
#   facet (c)/length by weak-drop-last-group. Facet (b) (aggregate provenance) IS
#   attackable in isolation on this carrier, contrary to what this battery claimed
#   before the audit: a rival applying the reducer to a rearranged copy of the
#   right group is refutable via `r bin1 ≠ r bin2`, which is indeed not a THEOREM
#   for the free reducer `r` — but a witness does not have to prove its
#   discriminating point, it may state the refutation at a point described by
#   HYPOTHESIS, and the gate's consistency probe then confirms the hypothesis is
#   satisfiable (measured: `hr : r [1.0,2.0] ≠ r [2.0,1.0]` yields no `False`).
#   `reduceBin` is a FREE variable `r` in every witness — abused for ALL reducers
#   at once (the provenance witness additionally assumes only that `r` is
#   order-sensitive, the weakest condition under which the defect is observable
#   at all), the strongest available variation (never pinned to a value).
#   `minPop` is varied over {0,1,2,3} across the witnesses; `bins` over one-group
#   (empty / singleton / two-value) and two-group (both populated / one empty)
#   shapes. Eight DISTINCT `(minPop, bins)` points (pts=8), so no rival is refuted
#   at a pinned input and every facet is demonstrated.
#
# SPEC PROBES run by the audit and NOT shipped (they found nothing to ship; the
#   record is here so the next reader does not have to re-measure). Eight further
#   WRONG impls were built against the frozen spec and ALL were rejected (exit 1),
#   so no spec hole was found in the too-weak direction: a reversed comparison
#   (`minPop ≥ b.length`), `≥ minPop + 1` (the prepatch rule re-spelled so no
#   subtraction appears), a right-selection rival whose aggregate comes from a
#   CONSTANT list, `rotateLeft 1` (a permutation that preserves length), an extra
#   trailing `none` (length + 1), a guard reading the OUTER `bins.length` instead
#   of the group's own population, an aggregate built from `bins.flatten`, and a
#   rival correct except that `minPop = 0` drops everything. Three further CORRECT
#   reshapes were built and DO verify, so no hole in the too-strong direction
#   either: `foldr`, the point-free `bins.map (binAggregate …)`, and the
#   reverse-map-reverse round trip. Two more correct reshapes could not be closed
#   and are recorded as UNCERTAIN rather than as holes — a forward-index loop
#   (append-at-tail, which needs an `aggregateSeq`-over-`++` distribution lemma
#   the frozen file does not export, and a new top-level lemma is out of variant
#   scope) and a `Nat.le`-spelled guard (`Decidable (minPop.le _)` is not
#   synthesized, an elaboration limit rather than a spec judgement).
#
# WITNESS FORM. The tester route is unavailable (equality on `List (Option Float)`
#   reduces to `Float` equality, on which `decide` stays stuck — measured), and
#   the frozen `while`-loop `…Exec` does not reduce under the witness script. So
#   each rival is a STRAIGHT-LINE impl whose `…Exec` reduces, and each witness
#   asserts the rival's extracted output differs from the transparent model
#   `aggregateSeq` at its concrete point — discriminated via `Option.isSome` (the
#   selection structure), `List.length`, or `Option.getD` (the aggregate value,
#   for the provenance rival). Confirmed empirically, with exit codes, by the
#   audit: each rival module does NOT verify; each positive verifies; each witness
#   ELABORATES against its rival (exit 0) and FAILS against `_WITNESS_REF`
#   (exit 1) with a SEMANTIC residual (`h3 : True ⊢ False` for the seven
#   projection witnesses; for the provenance witness, `Invalid field symm: the
#   environment does not contain True.symm, h3 has type True` — the same `True`,
#   reached one step earlier because that witness closes via `h3.symm`).
#   The forgery test (attack B′) is what establishes those `True`s are refutations
#   rather than a tactic mismatch: the AGREEMENT claim `accumulateBinsExec r 0
#   [[1.0]] = DivM.res (aggregateSeq r 0 [[1.0]])` ELABORATES against the
#   reference (exit 0) where every real witness FAILS (exit 1), so the
#   reference-side exit code tracks the CLAIM and not merely the impl shape.
#   The discrimination is NOT taken against the frozen impl:
#   its `…Exec` never reduces to a `DivM.res _`, so `DivM.res.inj` is a type
#   error there for any claim, true or false — measured, and the reason
#   `witness_reference` is set on every reject case (see `_WITNESS_REF`).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. This
#   bundle consumes no `axiom` (the `axioms` region is empty — the selection is
#   modeled directly by the pure `def`s `binAggregate`/`aggregateSeq`; the reducer
#   and group populations are free inputs), so there is nothing here to probe.
AXIOM_TESTS = []
