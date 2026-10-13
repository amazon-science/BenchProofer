"""properties.py — G-PBT falsification battery for django__django-17084 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct wrappedEvaluationDecisionM`` obligation survives
with a byte-identical statement) and swaps in a candidate implementation; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against the witness's second subject — here an explicit
``witness_reference``, because the frozen loop-solution cannot decide any claim
at all; see WITNESS MECHANICS below).

DEFENDED SURFACE (one contracted method over a two-level boolean-flag carrier,
``List (List Bool)``). The method computes whether an aggregation must be
evaluated inside a wrapping outer query:

  wrappedEvaluationDecisionM (priorConditions : Bool)
                             (aggregates : List (List Bool)) return (out : Bool)
    ensures out = wrappedEvaluationDecision priorConditions aggregates

``wrappedEvaluationDecision`` and its helpers are fully unfolded ``def``s in the
``pure`` region — there is NO opaque answer key to echo. Their shape is a
three-level combination of the two input binders:

  * ``wrappedEvaluationDecision p aggs = p || referencesWindow aggs``  (top OR)
  * ``referencesWindow []        = false``                            (outer fold)
  * ``referencesWindow (a::rest) = aggregateUsesWindow a || referencesWindow rest``
  * ``aggregateUsesWindow refs   = refs.any (fun b => b)``            (inner fold)

So the single ``ensures`` clause folds THREE independent behaviours over the two
input binders:
  * (P) the TOP disjunction — the decision is ``priorConditions OR
        referencesWindow aggregates``; BOTH disjuncts must be able to force the
        wrap on their own. ``priorConditions`` collapses the pre-existing
        structural conditions the change does not touch; the second disjunct is
        the NEW behaviour this bundle pins.
  * (W) the OUTER fold — ``referencesWindow`` is the OR over EVERY requested
        aggregate, so a single window-referencing aggregate anywhere in the list
        forces the wrap, and dropping/skipping any position loses that.
  * (A) the INNER fold — one aggregate uses a window iff ANY of its
        per-reference flags is set (``refs.any``), so an aggregate referencing a
        window-using annotation alongside plain ones still triggers.

The load-bearing / discriminating consequence is the second top-level disjunct
(W over A): a single window-referencing aggregate MUST force the wrap regardless
of ``priorConditions``. That is exactly the F2P observes — an aggregate over an
annotation that carries a window flag must be evaluated wrapped
(``sql.count("select") == 2``) rather than emitting the illegal aggregate over a
window (which raises a grouping error on the backend). The reject witnesses vary
BOTH binders: ``priorConditions`` across true/false, and ``aggregates`` across
the empty list, single- and two-element outer lists (offender first vs last),
and inner lists of length 0/1/2 mixing set and clear flags — so no binder is
pinned at one value.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame-mutation rival (and its symmetric twin) that keeps the gold body
    verbatim then WRITES through a read-only sequence input held at a fractional
    heap permission (``Acc(list_pred(.),1/2)``), rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: both inputs are
    immutable values, this bundle declares no ``mut`` binder for them, and there
    is no heap, aliasing, or permission system. There is no read-only input to
    overwrite and no permission system to trip, so the class is vacuous. No
    substitute is fabricated.
  * TERMINATION / NON-TERMINATION — UNLANDABLE, but for a WITNESS reason, not a
    vacuous-verification one. The nagini sibling pins a ``MustTerminate(2)``
    obligation and rejects a diverging (``nonterm-diverge``) rival that keeps the
    gold decision but loops forever ahead of it. This bundle runs under
    ``set_option loom.semantics.termination "total"`` (read the frozen file: it is
    ``total``, NOT ``partial``), so the two dispositions must be kept apart:

    (a) The NAIVE diverging rival — a ``while spin > 0 do spin := spin + 1``
        prefix with NO ``decreasing`` clause — is GENUINELY REJECTED here, not
        vacuously admitted. Measured: exit 1,
        ``error: Decreasing annotations are required in total correctness
        semantics``. Under ``total`` the verifier discharges a termination
        obligation, so partial-correctness reasoning ("the ensures is claimed only
        of terminating runs") does NOT apply to this bundle.
    (b) It still cannot be landed as an ``expect="reject"`` case, because its
        rejection is not ATTRIBUTABLE to the spec by any witness. The missing
        measure makes the whole module uncompilable, so the witness file built on
        that rival fails too (measured: exit 1) — the gate's first half ("the
        witness ELABORATES against the rival") cannot be met, and it would record
        ``witness-unproven`` → MALFORMED-TESTS, turning a passing battery
        inconclusive. Landing it would make this cell WORSE, not better. And the
        rejection that does occur attests to the termination obligation, not to
        the wrap decision this bundle defends.

    There is NO residual measure hole, and this paragraph RETRACTS one an earlier
    revision recorded. That revision claimed a bogus NON-decreasing measure
    (``decreasing spin`` while ``spin := spin + 1``) discharges the obligation, so
    the impl VERIFIES while returning the WRONG value. Re-measured on this bundle
    with a real build: that rival is REJECTED, exit 1, on the measure's own descent
    goal: ``unsolved goals case «decreasing_1: spin» ... ⊢ spin + 1 < spin``. And
    a CONSTANT measure fares no better (``decreasing (0 : Nat)`` leaves
    ``case «decreasing_1: (0 : Nat)» ⊢ 0 < 0``). So the annotation is not merely
    recorded and dropped here: the descent obligation is emitted and it is
    unprovable for a measure that does not decrease, which means an unreachable
    loop exit cannot launder a wrong answer. The mechanism lives in the frozen
    file's own header, and both of its lines point the same way:
    ``set_option loom.semantics.termination "total"`` makes Loom's option handler
    open the ``TotalCorrectness`` scope, and the file opens that scope explicitly
    as well. ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure``
    and emits ``⌜measure b' < measure b⌝``; the ``PartialCorrectness`` twin is the
    one that takes a measure and discards it, and it is never opened here. No
    ``spec_holes`` entry is filed for this class. (See footer.)
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class, exactly as the sibling
    records: the post-image is a total, fully unfolded function of the method's
    own inputs (``wrappedEvaluationDecision`` / ``referencesWindow`` /
    ``aggregateUsesWindow`` are concrete ``def``s in the ``pure`` region; the
    ``axioms`` region is empty). There is no answer key to echo — the only echo
    of the grounded decision is the correct one, carried as the ``pos-direct``
    positive control.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. A rival can be correct on
    part of the input domain yet diverge on a sub-domain: drop one top-level
    disjunct, replace the OR combination with AND, mis-fold the per-aggregate
    inner reference set (``all`` for ``any``), or skip a position in the outer
    traversal.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``wrappedEvaluationDecisionMTester priorConditions aggregates = false`` says the
extracted program's result violates the method's postcondition at that concrete
input. It is checked in a file whose ``prove_correct`` block has been stripped,
so no tactic script can mask the verdict. No witness binds a hypothesis (every
probed input is a concrete literal that decides the postcondition), so no
consistency probe is needed, and no banned token
(sorry/admit/native_decide/axiom/opaque) appears.

THE FROZEN SOLUTION CANNOT SERVE AS THE SECOND SUBJECT, so every reject case
carries an explicit ``witness_reference``. The frozen impl computes the decision
with a backward ``while`` fold; under ``loom.semantics.choice "demonic"`` that
loop's fixpoint elaborates through ``Classical.choice``, which the kernel cannot
unfold, so ``decide`` against the frozen tester is stuck for EVERY claim
regardless of truth:

    error: Tactic `decide` failed for proposition
      wrappedEvaluationDecisionMTester false [[true]] = false
    because its `Decidable` instance ... did not reduce to `isTrue` or `isFalse`

Gold's exit code therefore carries NO information, and "the witness fails
against gold" is not evidence of discrimination here. Measured: the FORGED
non-refutation ``wrappedEvaluationDecisionMTester true [[true]] = true`` — which
asserts the ``drop-window-disjunct`` rival is CORRECT at an agreement point, the
exact OPPOSITE of a refutation — elaborates against that rival (exit 0) and
fails against gold (exit 1) by the same stuck reduction, so it would clear a
gold-subject check while attesting to nothing.

The second subject is instead ``_LOOPFREE`` (the ``pos-direct`` source): a
loop-free impl of the SAME frozen spec whose extracted program DOES reduce, and
which is independently carried as the ``pos-direct`` expect="verify" case, so the
battery itself records that loop-freeness is not what any rival is rejected for.
Each witness was rebuilt out-of-band with ``scripts/lean_verify.sh``: every one
ELABORATES against its rival (exit 0) and is REFUTED against ``_LOOPFREE`` with a
SEMANTIC verdict — ``Tactic `decide` proved that the proposition ... is false``,
the kernel deciding the concrete claim rather than getting stuck. The forged
non-refutation above is correctly ADMITTED by ``_LOOPFREE`` (exit 0), i.e. it
fails the discrimination check, which is what makes this subject a real oracle.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` and meta.json
lists no consumed axiom or deep-model reference; the whole decision is modeled
DEEPLY as ``wrappedEvaluationDecision`` / ``referencesWindow`` /
``aggregateUsesWindow``. There is no axiom-soundness / axiom-containment
obligation to probe here, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-17084"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap). ----

# The whole frozen impl body (backward `while` fold + invariants + return).
# Replacing it with a straight-line computable form lets a rival's extracted
# program reduce under `decide` so its witness can discriminate.
_IMPL = (
    "    let mut acc : Bool := false\n"
    "    let mut i := aggregates.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ aggregates.length\n"
    "      invariant acc = referencesWindow (aggregates.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let refs := aggregates[i - 1]!\n"
    "      acc := aggregateUsesWindow refs || acc\n"
    "      i := i - 1\n"
    "    return priorConditions || acc\n"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The single fold-step assignment inside the loop body (unique in the file: the
# other `aggregateUsesWindow` occurrences are in the pure region and the lemma).
_FOLD = "      acc := aggregateUsesWindow refs || acc\n"

# The first line of the impl body — an anchor to PREPEND an in-region assert
# before, keeping the frozen body intact after it.
_IMPL_HEAD = "    let mut acc : Bool := false\n"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = (
    "prove_correct wrappedEvaluationDecisionM by\n"
    "  loom_solve\n"
    "  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]\n"
    "    simp_all\n"
    "  · simp_all [wrappedEvaluationDecision]"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with the WHOLE impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_reproved(new_impl: str, new_proof: str) -> str:
    """Replace the whole impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


def _with_fold(new_fold: str, new_proof: str) -> str:
    """Reshape only the fold-step assignment AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _FOLD, new_fold), _PROOF, new_proof)


def _with_assert(assert_block: str, new_proof: str) -> str:
    """Prepend an in-region assert before the frozen body AND retune the script."""
    return _swap(_swap(_BASE, _IMPL_HEAD, assert_block + _IMPL_HEAD),
                 _PROOF, new_proof)


# ---- witness preamble. Reaches the method's postcondition through Velvet's own
# ---- tester machinery. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. This method has no
# ---- `require` clause, so every probed input is admissible and the tester
# ---- reaches the postcondition rather than vacuously passing. ----
_TESTER = (
    "extract_program_for wrappedEvaluationDecisionM\n"
    "prove_precondition_decidable_for wrappedEvaluationDecisionM\n"
    "prove_postcondition_decidable_for wrappedEvaluationDecisionM\n"
    "derive_tester_for wrappedEvaluationDecisionM\n\n"
)


def _wit(prior_lit: str, aggs_lit: str) -> str:
    return _TESTER + (
        f"example : wrappedEvaluationDecisionMTester {prior_lit} {aggs_lit} "
        "= false := by\n  decide\n")


# ---- the witness's SECOND SUBJECT. The frozen impl's backward `while` fold
# ---- elaborates through `Classical.choice` (demonic choice), which the kernel
# ---- cannot unfold, so `decide` against the frozen tester is stuck for EVERY
# ---- claim and its exit code discriminates nothing. `_LOOPFREE` is a loop-free
# ---- impl of the SAME frozen spec whose extracted program DOES reduce, so a
# ---- witness is either DECIDED FALSE against it (a real refutation) or admitted
# ---- (no discrimination). It is byte-identical to the `pos-direct` module below,
# ---- which the battery independently asserts VERIFIES — so loop-freeness is not
# ---- what any rival is being rejected for, and the gate re-checks both facts
# ---- (shares the frozen spec, and verifies) before refuting anything against it.
_LOOPFREE = _impl_reproved(
    "    return priorConditions || referencesWindow aggregates\n",
    "prove_correct wrappedEvaluationDecisionM by\n"
    "  loom_solve <;> simp_all [wrappedEvaluationDecision]")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # The honest cheapest correct impl: report the decision DIRECTLY via the
        # transparent pure function, no loop. Since the post-image is GROUNDED in
        # the inputs (not an opaque answer key), this is literally the ensures'
        # RHS, so it MUST verify — and it doubles as proof the spec is not
        # echo-vulnerable (any wrong combination fails `out = wrappedEval...`).
        # The loop is gone, so the frozen proof's backward-fold step is unneeded
        # and the residual goal closes under `loom_solve <;> simp`.
        # This same source is `_LOOPFREE`, the second subject every reject case
        # refutes its witness against: carrying it as a verifying positive is what
        # makes that subject a checked oracle rather than an assumption.
        "module": _LOOPFREE,
        "rationale": (
            "the post-image `priorConditions || referencesWindow aggregates` is "
            "GROUNDED in the two inputs (total unfolded folds, no opaque answer "
            "key), so returning it directly is the honest cheapest CORRECT impl; "
            "the ensures is literally this expression, so it MUST verify, else "
            "SPEC-TOO-STRONG. Stands in for the (N/A) ungrounded-oracle-echo "
            "class: the only echo of the grounded decision is the correct one."
        ),
    },
    {
        "id": "pos-commute-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but COMMUTE the two operands of
        # the per-step disjunction (`acc || aggregateUsesWindow refs`). The
        # accumulated value is unchanged, so the byte-identical loop invariant and
        # hence the whole ensures still hold; the frozen tactic script gains a
        # single `Bool.or_comm` rewrite to reconcile the reordered `||`.
        "module": _with_fold(
            "      acc := acc || aggregateUsesWindow refs\n",
            "prove_correct wrappedEvaluationDecisionM by\n"
            "  loom_solve\n"
            "  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]\n"
            "    simp_all [Bool.or_comm]\n"
            "  · simp_all [wrappedEvaluationDecision]"),
        "rationale": (
            "commuting the two operands of the fold-step disjunction "
            "(`acc || aggregateUsesWindow refs` for `aggregateUsesWindow refs || "
            "acc`) leaves the accumulated value identical, so the loop invariant "
            "`acc = referencesWindow (aggregates.drop i)` and hence "
            "`out = wrappedEvaluationDecision ...` still hold; a correct reshape "
            "MUST verify, else SPEC-TOO-STRONG on operand order."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — this method carries no `require` clause (the pre-conditions
    # region is empty), so the nagini "a normal input satisfies the precondition"
    # probe is vacuous: nothing could exclude an F2P-shaped input. The residual
    # admissibility risk on a total domain is that the post-image is DEGENERATE at
    # the interesting points — a spec no impl can meet reads exactly like a spec
    # every impl meets. So this case discharges an in-region `assert` at two
    # F2P-shaped points: a single window-referencing aggregate (with all other
    # conditions off) for which the decision must be TRUE, and a single
    # non-window aggregate for which it must be FALSE. The frozen body follows so
    # the method's own `ensures` obligation still discharges; the assert is live,
    # not decoration (a false claim leaves an unsolved goal — verified
    # out-of-band).
    # =====================================================================
    {
        "id": "admiss-decision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_assert(
            "    assert (with_name_prefix `admiss\n"
            "      (wrappedEvaluationDecision false [[true]] = true ∧\n"
            "       wrappedEvaluationDecision false [[false]] = false))\n",
            "prove_correct wrappedEvaluationDecisionM by\n"
            "  loom_solve\n"
            "  all_goals\n"
            "    first\n"
            "    | exact ⟨rfl, rfl⟩\n"
            "    | (rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]; simp_all)\n"
            "    | simp_all [wrappedEvaluationDecision]"),
        "rationale": (
            "the decision is non-degenerate at the F2P-shaped points: with the "
            "pre-existing conditions off, a single window-referencing aggregate "
            "must decide TRUE (wrap) and a single non-window aggregate must decide "
            "FALSE (no wrap) — not the constant-false or constant-true a "
            "degenerate/unsatisfiable obligation would admit, so the new window "
            "disjunct really does fork on that boundary. The in-region assert must "
            "discharge (else the obligation is degenerate at the interesting "
            "points); the frozen body keeps `out = wrappedEvaluationDecision ...` "
            "intact, so the module verifies. Re-aimed from the nagini "
            "admissibility probe, whose read-only fractional-permission half has "
            "no counterpart on this referentially-transparent carrier. LIVENESS "
            "re-derived by independent audit: flipping the first conjunct to the "
            "FALSE claim `wrappedEvaluationDecision false [[true]] = false` makes "
            "the module FAIL (exit 1, `unsolved goals ... ⊢ referencesWindow "
            "[[true]] = false ∧ referencesWindow [[false]] = false`), so the "
            "assert is a real obligation the verifier discharges, not decoration "
            "that any claim would satisfy."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line COMPUTABLE impl (so its witness
    # reduces under `decide`) refuted at a concrete input by a witness that fails
    # on the frozen loop-solution, and each with the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "drop-window-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour: report only the pre-existing conditions, never
        # accounting for a window-referencing aggregate. This is the exact G-DIFF
        # defect — the new window disjunct is dropped.
        "module": _with_impl("    return priorConditions\n"),
        "refinement": (
            "this is the PRE-PATCH decision: it accounts only for the pre-existing "
            "structural conditions and never for a window-referencing aggregate. "
            "Its faithful real counterpart is the unpatched decision, which leaves "
            "an aggregation over a window-carrying annotation UNWRAPPED — emitting "
            "the illegal aggregate-over-window form (a single SELECT) that the "
            "backend rejects with a grouping error, where the fix requires the "
            "wrapped two-SELECT form. The F2P asserts exactly the wrapped shape, so "
            "it would NOT resolve — the precise change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECT from `out = wrappedEvaluationDecision ...` on the top "
            "disjunction (P) / the discriminating consequence (W): with the "
            "pre-existing conditions off but a single window-referencing aggregate "
            "present, the post-image demands TRUE (the window disjunct) but this "
            "impl returns `priorConditions` = FALSE. Refuted at "
            "`priorConditions=false`, `aggregates=[[true]]` — a window-only input "
            "where the dropped disjunct is the sole cause of the wrap."
        ),
        "witness": _wit("false", "[[true]]"),
        # The frozen loop cannot decide any claim (stuck at `Classical.choice`),
        # so the refutation is checked against `_LOOPFREE` — a VERIFYING loop-free
        # impl of the same spec, which decides this witness FALSE.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "drop-prior-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the OTHER top-level disjunct: report the window fold alone,
        # ignoring the pre-existing structural conditions. Correct whenever a
        # window aggregate is present, wrong when only a prior condition demands
        # the wrap.
        "module": _with_impl("    return referencesWindow aggregates\n"),
        "refinement": (
            "reporting only the window fold and dropping the pre-existing "
            "structural conditions is what a real patch that deleted the shared "
            "prior-condition disjuncts (subquery / sliced / distinct / combinator "
            "…) would do. Those conditions are unchanged by the fix and several "
            "PASS_TO_PASS tests rely on them still forcing the wrap (e.g. the "
            "referenced-subquery wrapping test); an aggregation that must wrap "
            "purely for a pre-existing reason would then be left unwrapped, so it "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = wrappedEvaluationDecision ...` on the top "
            "disjunction (P), other direction: when `priorConditions` is TRUE but "
            "no aggregate references a window, the post-image demands TRUE (the "
            "prior disjunct) yet this impl returns `referencesWindow` = FALSE. "
            "Refuted at `priorConditions=true`, `aggregates=[]` — varies the "
            "`priorConditions` binder to true and the outer list to empty, a "
            "point no window-attacking rival shares."
        ),
        "witness": _wit("true", "[]"),
        # The frozen loop cannot decide any claim (stuck at `Classical.choice`),
        # so the refutation is checked against `_LOOPFREE` — a VERIFYING loop-free
        # impl of the same spec, which decides this witness FALSE.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "wrong-and-combination",
        "kind": "uniqueness",
        "expect": "reject",
        # Replace the top-level OR with AND: wrap only when the pre-existing
        # conditions AND a window aggregate BOTH hold. Neither disjunct can force
        # the wrap on its own.
        "module": _with_impl(
            "    return priorConditions && referencesWindow aggregates\n"),
        "refinement": (
            "combining the two conditions with AND instead of OR means the wrap "
            "fires only when a pre-existing condition AND a window aggregate BOTH "
            "hold — so a windowed aggregation with no other reason to wrap (the "
            "F2P shape) is left unwrapped, and equally an aggregation that must "
            "wrap for a pre-existing reason but references no window is left "
            "unwrapped. A faithful counterpart using `and` for the disjunct would "
            "NOT resolve either the F2P or the pre-existing wrapping tests."
        ),
        "rationale": (
            "REJECT from `out = wrappedEvaluationDecision ...` on the top "
            "disjunction (P): the post-image is an OR, so either disjunct forces "
            "TRUE alone; the AND rival needs both. Refuted at "
            "`priorConditions=true`, `aggregates=[[false]]` — a prior-only input "
            "where the post-image demands TRUE but the AND returns "
            "`true && false` = FALSE. Varies `priorConditions` to true and probes "
            "the OR-vs-AND structure, a distinct failure mode from the drop "
            "rivals."
        ),
        "witness": _wit("true", "[[false]]"),
        # The frozen loop cannot decide any claim (stuck at `Classical.choice`),
        # so the refutation is checked against `_LOOPFREE` — a VERIFYING loop-free
        # impl of the same spec, which decides this witness FALSE.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "inner-all-for-any",
        "kind": "uniqueness",
        "expect": "reject",
        # Mis-fold the per-aggregate reference set: an aggregate uses a window iff
        # ALL its per-reference flags are set, instead of ANY. Correct for a
        # single-reference aggregate, wrong for one that references a window
        # annotation alongside a non-window one.
        "module": _with_impl(
            "    return priorConditions "
            "|| aggregates.any (fun refs => refs.all (fun b => b))\n"),
        "refinement": (
            "requiring EVERY referenced annotation of an aggregate to be "
            "window-using (`all`) instead of ANY (`any`) is what a real patch that "
            "wrote the per-aggregate quantifier the wrong way would do. An "
            "aggregate that references a window-carrying annotation together with "
            "an ordinary one then reads as non-window, so the aggregation is left "
            "unwrapped and the illegal aggregate-over-window form is emitted; the "
            "failing test pins the wrapped shape for any aggregate touching a "
            "window annotation, so it would NOT resolve — a genuine sub-domain "
            "break on multi-reference aggregates."
        ),
        "rationale": (
            "REJECT from `out = wrappedEvaluationDecision ...` on the inner fold "
            "(A): `aggregateUsesWindow` is `refs.any`, so a single set flag "
            "triggers, but the rival's `refs.all` needs every flag set. Refuted at "
            "`priorConditions=false`, `aggregates=[[true, false]]` — one aggregate "
            "referencing a window annotation (flag set) and a non-window one (flag "
            "clear): gold decides TRUE (`any` = true), the rival FALSE "
            "(`all` = false). Exercises the inner reference-set binder, which the "
            "outer/top-level rivals hold at a single flag."
        ),
        "witness": _wit("false", "[[true, false]]"),
        # The frozen loop cannot decide any claim (stuck at `Classical.choice`),
        # so the refutation is checked against `_LOOPFREE` — a VERIFYING loop-free
        # impl of the same spec, which decides this witness FALSE.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the FIRST requested aggregate in the outer traversal: fold over
        # `aggregates.drop 1`. A window aggregate appearing first is never seen
        # and the wrap is missed.
        "module": _with_impl(
            "    return priorConditions "
            "|| (aggregates.drop 1).any aggregateUsesWindow\n"),
        "refinement": (
            "screening only the tail of the requested aggregates and skipping the "
            "first lets a window-referencing aggregate supplied first go unnoticed, "
            "so its aggregation is left unwrapped — diverging from gold whenever "
            "the offending aggregate is first in iteration order. A faithful "
            "counterpart with that off-by-one would NOT resolve for such queries."
        ),
        "rationale": (
            "REJECT from `out = wrappedEvaluationDecision ...` on the outer fold "
            "(W): `referencesWindow` ORs over EVERY aggregate including the head, "
            "and this impl drops the head. Refuted at `priorConditions=false`, "
            "`aggregates=[[true], [false]]` — offender first, clean tail: gold "
            "decides TRUE, the rival FALSE. Varies the outer list length and the "
            "offender's position (head)."
        ),
        "witness": _wit("false", "[[true], [false]]"),
        # The frozen loop cannot decide any claim (stuck at `Classical.choice`),
        # so the refutation is checked against `_LOOPFREE` — a VERIFYING loop-free
        # impl of the same spec, which decides this witness FALSE.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the LAST requested aggregate: fold over `aggregates.dropLast`. A
        # window aggregate appearing last is never seen and the wrap is missed —
        # the MIRROR of skip-first, so neither rival pins the offender's index.
        "module": _with_impl(
            "    return priorConditions "
            "|| aggregates.dropLast.any aggregateUsesWindow\n"),
        "refinement": (
            "an off-by-one that stops one aggregate short of the end skips the "
            "last requested aggregate, so a window-referencing aggregate appearing "
            "last is missed and its aggregation left unwrapped — diverging from "
            "gold whenever the offending aggregate is last in iteration order. A "
            "faithful counterpart with that off-by-one would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = wrappedEvaluationDecision ...` on the outer fold "
            "(W): `referencesWindow` ORs over EVERY aggregate including the last, "
            "and this impl drops the last. Refuted at `priorConditions=false`, "
            "`aggregates=[[false], [true]]` — clean head, offender last: gold "
            "decides TRUE, the rival FALSE. The MIRROR of partial-skip-first, so "
            "neither rival pins the offender's index."
        ),
        "witness": _wit("false", "[[false], [true]]"),
        # The frozen loop cannot decide any claim (stuck at `Classical.choice`),
        # so the refutation is checked against `_LOOPFREE` — a VERIFYING loop-free
        # impl of the same spec, which decides this witness FALSE.
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness — of which one is the mandatory
# frame-mutation rival, its symmetric twin a second, and one the diverging
# nonterm rival) plus 1 AXIOM_TESTS entry. The nagini sibling contracts a single
# function `requires_subquery_wrap(window_flags, subquery_flags,
# other_forces_wrap)` over TWO read-only boolean-list inputs plus a scalar, with
# the wrap decision the three-term disjunction and the window disjunct computed by
# a verified `while` loop under a `MustTerminate` obligation. This bundle models
# the SAME decision but abstracts the two flag lists into the single carrier
# `aggregates : List (List Bool)` folded by `referencesWindow` (each inner list =
# one aggregate's per-reference window flags) plus the collapsed `priorConditions`
# Bool (which absorbs the sibling's `subquery_flags` term and `other_forces_wrap`
# scalar, since neither is changed by the fix — mapping.md §1/§2). The decision
# surface carries across intact; the permission surface, the loop's termination
# obligation, and the SEPARATE subquery-flag list do not exist as independently
# attackable objects here.
#
#   sibling case          -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-direct            -> pos-direct                    PORTED (loop-free)
#   pos-reorder           -> pos-commute-fold              RE-EXPRESSED
#   admiss                -> admiss-decision-nondegenerate RE-AIMED
#   drop-window           -> drop-window-disjunct          PORTED (the G-DIFF)
#   wrong-and             -> wrong-and-combination         RE-EXPRESSED
#   swap-names            -> (none)                        VACUOUS (see below)
#   nonterm-diverge       -> (none)                        UNLANDABLE (spec hole)
#   frame-mut             -> (none)                        VACUOUS
#   frame-mut-sub         -> (none)                        VACUOUS
#   (no sibling)          -> drop-prior-disjunct           ADDED (binder cov.)
#   (no sibling)          -> inner-all-for-any             ADDED (inner-fold cov.)
#   (no sibling)          -> partial-skip-first            ADDED (outer-fold cov.)
#   (no sibling)          -> partial-skip-last             ADDED (outer-fold cov.)
#   AXIOM_TESTS (1)       -> (none)                        DROPPED (G-AX lane)
#
# 3 ported/re-expressed positives-or-diff + 4 added rivals; 3 vacuous, 1
# unlandable, 1 dropped.
#
# PORTED (pos-direct): the sibling's honest cheapest positive returns the
#   three-term disjunction directly. Here the grounded post-image is
#   `priorConditions || referencesWindow aggregates`, so the loop-free direct
#   return is the same control, reproved with `loom_solve <;> simp`. Also stands
#   in for the (N/A) ungrounded-oracle-echo class exactly as the sibling records.
# RE-EXPRESSED (pos-reorder -> pos-commute-fold): the sibling reorders two
#   independent backward loops and the final OR. This bundle has ONE outer fold
#   (the subquery term is collapsed into `priorConditions`, not a second loop), so
#   the loop-reorder has no counterpart; the reshape SPIRIT — behaviourally
#   identical, structurally different — is carried by commuting the per-step
#   disjunction of the single fold, reproved with one `Bool.or_comm`.
# RE-AIMED (admiss): the sibling re-derives in-region that the read-only
#   half-permission inputs are readable and the discriminating clause is
#   reachable/non-vacuous on an F2P-shaped input. This bundle has no `require` and
#   no permission surface, so the permission half is vacuous; re-aimed at the
#   residual total-domain risk (a degenerate decision) via an in-region assert
#   that the decision genuinely forks — a single window aggregate -> TRUE, a
#   single non-window aggregate -> FALSE.
# PORTED (drop-window-disjunct): the sibling's `drop-window` is the literal
#   pre-patch skeleton (never accumulate the window term). It ports directly onto
#   the discriminating window disjunct here (return `priorConditions` only) and is
#   the exact G-DIFF defect, backed by a machine-checked witness.
# RE-EXPRESSED (wrong-and-combination): the sibling's `wrong-and` neutralises the
#   window term by ANDing it against the subquery term inside the disjunction.
#   Here the analogous operator-confusion is replacing the TOP-level OR with AND
#   (`priorConditions && referencesWindow`), which likewise cannot let either
#   condition force the wrap alone; refuted at a prior-only input.
# ADDED (drop-prior-disjunct): the sibling's decision has three symmetric OR
#   terms; collapsing two of them into `priorConditions` here leaves that binder
#   at risk of being ignored by a battery that only ever attacks the window term.
#   This rival drops `priorConditions` and is refuted at `true []`, the sole point
#   where that binder alone decides — so `priorConditions` is not held fixed.
# ADDED (inner-all-for-any): the sibling models each aggregate's reference set as
#   a flat `any` over a flag list; the inner quantifier is a distinct behaviour
#   (A) with its own binder (an inner `List Bool`). This rival folds the inner set
#   with `all` for `any`, refuted at a multi-reference aggregate `[[true,false]]`
#   — the point that makes the inner-fold dependence observable, which every
#   single-flag rival holds fixed.
# ADDED (partial-skip-first / partial-skip-last): the outer traversal (W) is a
#   fold over EVERY requested aggregate; a rival that skips a position is a
#   genuine partial-domain break. Refuted at mirror two-element inputs (offender
#   first / offender last) so neither pins the offender's index — varying the
#   outer list length and the offending position across the reject witnesses.
# VACUOUS (swap-names): the sibling's `swap-names` is itself a CORRECT positive
#   control (variable-name provenance is not observable to the decision) — it
#   exercises the two SEPARATE accumulator variables `refs_window` / `refs_subquery`
#   of the sibling's two-loop impl. This bundle has ONE accumulator over the single
#   `aggregates` carrier and no separate subquery loop, so there are no two local
#   names to exchange; the positive it stands for is already covered by
#   pos-commute-fold (a value-preserving reshape of the single fold). No substitute
#   is fabricated.
# VACUOUS (frame-mut, frame-mut-sub): the sibling's TWO mandatory frame-mutation
#   rivals write through a read-only sequence input held at a fractional heap
#   permission (`Acc(list_pred(.),1/2)`), rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: both inputs are immutable values,
#   this bundle declares no `mut` binder for them, and there is no heap, aliasing,
#   or permission system. There is no read-only input to overwrite. No substitute
#   is fabricated (per the porting map, this class is vacuous on Lean/Velvet).
# UNLANDABLE (nonterm-diverge): the sibling rejects a diverging rival (gold
#   decision kept, an unbounded loop ahead of it) via its `MustTerminate(2)`
#   obligation. This bundle runs under `loom.semantics.termination "total"` — read
#   the frozen file; an earlier revision of this note said `"partial"` and argued
#   the disposition from partial-correctness, which is the WRONG semantics for
#   this bundle and inverts the correct reading. Corrected, with the builds:
#     * naive diverging rival (unbounded loop, NO `decreasing`): genuinely
#       REJECTED, exit 1, `Decreasing annotations are required in total
#       correctness semantics`. NOT vacuously admitted.
#     * but its witness cannot ELABORATE against it (exit 1: the module itself is
#       uncompilable without a measure), so the gate's first half fails and the
#       case would record `witness-unproven` → MALFORMED-TESTS. Landing it makes
#       the cell inconclusive rather than stronger, and the rejection it produces
#       attests to the termination obligation, not to the wrap decision.
#     * a rival that CARRIES a measure is rejected too, on the measure's own goal.
#       This RETRACTS what this entry used to claim (that `decreasing spin` with
#       `spin := spin + 1` discharges the obligation and the impl VERIFIES at
#       exit 0). Re-measured: that shape is REJECTED, exit 1, `unsolved goals case
#       «decreasing_1: spin» ... |- spin + 1 < spin`, and a constant measure
#       leaves `case «decreasing_1: (0 : Nat)» |- 0 < 0`. So no wrong answer is
#       laundered through an unreachable exit and there is no residual hole to
#       escalate; the earlier claim was measured against the wrong premise.
#   Mechanism: `set_option loom.semantics.termination "total"` itself opens the
#   `TotalCorrectness` scope (Loom `MonadAlgebras/WP/Options.lean`), the frozen file
#   opens that scope explicitly too, and `TotalCorrectness.WPGen.forWithInvariantLoop`
#   emits `measure b' < measure b` as a real goal where the `PartialCorrectness`
#   twin would discard the measure. So the class is CLOSED BY THE SEMANTICS and
#   unlandable only on witness mechanics; no `spec_holes` entry is filed for it.
# DROPPED (AXIOM_TESTS): the sibling's one containment/equivalence probe
#   (fold == Python any() over the boolean-list domain, plus the
#   contains_over_clause/subquery attribute resolution) is G-AX's job; this bundle
#   declares no axiom and no deep-model reference (the decision is modeled deeply
#   as wrappedEvaluationDecision/referencesWindow/aggregateUsesWindow), and the
#   G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE of the reject witnesses (pts = 6 distinct input
#   points). The single ensures folds three behaviours over two binders:
#     (P) top OR      — drop-window-disjunct (window disjunct), drop-prior-disjunct
#                       (prior disjunct), wrong-and-combination (OR-vs-AND);
#     (W) outer fold  — partial-skip-first, partial-skip-last (every position);
#     (A) inner fold  — inner-all-for-any (any-vs-all over one aggregate's refs).
#     priorConditions — false (drop-window, inner-all, skip-first, skip-last),
#                       true (drop-prior, wrong-and): both values exercised.
#     aggregates      — [], [[true]], [[false]], [[true,false]], [[true],[false]],
#                       [[false],[true]]: outer length 0/1/2, inner length 0/1/2,
#                       offender first / last / mixed — never held fixed.
#   Every independent top-level behaviour of the post-image is attacked and both
#   binders are varied; both positives and the admissibility case defend the whole
#   decision on gold-shaped computations.
#
# SPEC-TOO-STRONG re-derivation (independent audit, out-of-band builds). Four
#   FURTHER correct reshapes beyond the two carried positives were built against
#   the frozen spec, and ALL FOUR VERIFY (exit 0), so the spec is not over-fitted
#   to the frozen fold's shape:
#     * top-level OR commuted: `referencesWindow aggregates || priorConditions`
#       (closes with `simp_all [wrappedEvaluationDecision, Bool.or_comm]`);
#     * `aggregates.any aggregateUsesWindow` for the front-recursive fold;
#     * `aggregates.foldr (fun a b => aggregateUsesWindow a || b) false`;
#     * REVERSED traversal, `referencesWindow aggregates.reverse` (via
#       `List.any_reverse`) — the OR-fold's order-insensitivity that mapping.md §2
#       relies on to call the `List` model observationally exact, re-proven here.
#   Each needs its own bridging `have` (an induction over the list) rather than the
#   frozen script, which is a TACTIC distance, not a spec rejection — the residual
#   `ensures` goal is discharged in every case. Six wrong impls not in this battery
#   were also built (inner `headI`; wrap iff `!aggregates.isEmpty`; constant
#   `true`; top-level XOR; inner flag polarity flipped; outer `headI` only) and ALL
#   SIX are REJECTED, under both the loop-free and a `grind`-based script, so no
#   spec hole was found in either direction on the terminating domain.
#
# WITNESS MECHANICS: the tester+`decide` path is LIVE (the postcondition is a
#   Bool equality over decidable carriers, no opaque callee). Each rival is a
#   straight-line computable form whose extracted `…Exec` reduces under `decide`.
#   Gold's backward-`while` `…Exec` does NOT reduce — it stays stuck at the
#   Decidable instance for EVERY claim, true or false — so gold is NOT usable as
#   the witness's second subject and its exit code attests to nothing. Each reject
#   case therefore names `witness_reference: _LOOPFREE` (the `pos-direct` source:
#   a loop-free impl of the same spec, independently required to VERIFY), and the
#   refutation is checked there. No witness binds a hypothesis (every input is a
#   concrete literal that decides the postcondition), so no consistency probe is
#   needed. All six rebuilt with scripts/lean_verify.sh: rival exit 0; `_LOOPFREE`
#   exit 1 with `Tactic `decide` proved that the proposition ... is false` — a
#   SEMANTIC refutation of the concrete claim, not a stuck reduction. Control: the
#   forged non-refutation `...Tester true [[true]] = true` (asserting a rival is
#   CORRECT at an agreement point) is ADMITTED by `_LOOPFREE` (exit 0) and so
#   fails the discrimination check, while it would have PASSED a gold-subject
#   check (rival 0 / gold 1, both stuck) — which is why the reference is required.
AXIOM_TESTS = []
