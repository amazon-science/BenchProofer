"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25973 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct runScoringRounds`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the case's witness subject, which here is the ``witness_reference`` rather
than the frozen solution; see WITNESS SUBJECT below).

DEFENDED SURFACE (one contracted method over a split source and a round count):

  runScoringRounds (source : CvSource) (k : Nat) return (obs : List Splits)
    ensures obs = List.replicate k source.splits   -- THE load-bearing (only) clause

The single clause pins the whole modeled behaviour: running ``k`` consecutive
scoring rounds against ``source`` must record, on EVERY round, the FULL underlying
split sequence of ``source`` — so the recorded observations are that sequence
repeated exactly ``k`` times. Independent sub-behaviours the clause forces:

  * RE-READABILITY: every one of the ``k`` rounds observes the full split
    sequence, INDEPENDENT of whether ``source`` is single-pass (``reusable =
    false``, ``consumed = false``). A rival that reads the raw single-pass source
    directly sees the full sequence on the first round and the empty sequence
    thereafter — the exact exhaustion the fix removes.
  * CONTENT: each recorded round equals ``source.splits`` exactly — not an
    augmented or truncated sequence.
  * COUNT: the record has length exactly ``k`` — one full observation per round.

``source`` is a read-only VALUE (no ``mut`` binder), and the carrier is fully
transparent: ``CvSource`` / ``readObs`` / ``advance`` / ``materialize`` /
``List.replicate`` all compute on literals. So a witness reaches the impl through
Velvet's extractor (``extract_program_for runScoringRounds`` gives
``runScoringRoundsExec source k = NonDetT.run (runScoringRounds source k)``) and
states ``runScoringRoundsExec s n ≠ DivM.res (List.replicate n s.splits)`` at a
concrete ``(s, n)`` — the residual literal reduces under ``simp``. Every reject
rival is a straight-line loop-free CLOSED FORM whose extracted program DOES
reduce to a literal, so the witness ELABORATES against the rival.

WITNESS SUBJECT — why every reject case carries a ``witness_reference``. The
FROZEN impl carries a ``while`` loop, and its extracted program does NOT reduce:
the residual goal keeps a raw ``forIn Lean.Loop.mk ...`` fixpoint that ``simp``
cannot evaluate. So the frozen solution is NOT a usable second subject — its
build fails for EVERY claim about it regardless of truth, and the exit code
therefore carries no information about discrimination. Measured with real builds:
the TRUE claim ``runScoringRoundsExec {splits := [3,4], reusable := true,
consumed := false} 2 = DivM.res (List.replicate 2 [3,4])`` — which holds of the
frozen impl, since the frozen impl is correct — ALSO fails against the frozen
solution (exit 1, ``unsolved goals`` with the ``forIn`` fixpoint intact), while
the same claim elaborates (exit 0) against the loop-free closed form. A forged
witness asserting a rival is CORRECT at an agreement point likewise clears a
gold-side check. The frozen impl's failure is a STUCK REDUCTION, not a
refutation; because it surfaces as plain ``unsolved goals`` rather than one of
the ``decide``-flavoured messages, the gate's automatic stuck screen does not
catch it here, so the case must name its subject explicitly.

Each reject case therefore sets ``witness_reference`` to the loop-free
``pos-control-direct`` impl: it shares the frozen spec (``variant_scope`` clean)
and it VERIFIES (exit 0), so it cannot violate its own spec, and — unlike the
frozen loop — it REDUCES, so refuting the witness against it is a real semantic
refutation. Confirmed per case with ``scripts/lean_verify.sh``: rival exit 0,
reference exit 1 with the fully-reduced residual ``⊢ False`` (the literal was
computed and the claim genuinely contradicted), which is exactly the semantic
refutation the discrimination check is supposed to observe. No witness binds a
hypothesis (the carrier is fully transparent), so there is no joint-satisfiability
obligation.

ADVERSARIAL READ of the nagini classes on this carrier:
  * ADMISSIBILITY — PORTED (re-derived by audit; see the case for the measured
    exit codes). This bundle declares no ``require`` clause, but that retires only
    the PRECONDITION reading of the lane. The lane detects PRECOND-TOO-STRONG,
    whose analogue on a total carrier is the obligation being UNSATISFIABLE or
    DEGENERATE at exactly an F2P-shaped input — a spec no impl can meet reads like
    a spec every impl meets. Landed as an in-region ``assert`` discharged by
    EVALUATION at the reported input shape, with the frozen impl kept verbatim.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame-mutation rival (store into the source held at half permission) because
    a write needs full permission. This backend is referentially transparent,
    ``source`` is an immutable value declared with NO ``mut`` binder, and there is
    no heap and no aliasing — so there is no read-only input to overwrite and no
    substitute probe. Not fabricated (per the porting map, vacuous on Lean/Velvet).
  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini echo cheat attacks a capability
    predicate (``presents_family``) that has NO value-level witness: echoing the
    input's family size satisfies every value pin yet cannot fabricate the
    reference-tied capability. This bundle has NO such capability clause; the
    single clause is purely value-level (``obs = List.replicate k source.splits``,
    grounded in ``source.splits``). Echoing the split sequence ``k`` times is
    therefore the CORRECT answer — it IS the direct positive control below — so
    there is no wrong echo to build. The carrier collapsed the distinction the
    nagini capability kept.
  * LAUNDER (value-equal copy reported instead of the secured object) — VACUOUS
    for the same reason: the nagini token is tied to the object REFERENCE, so a
    value-equal copy fails it; here the spec observes only the value-level split
    sequence, and a value-equal copy is EQUAL. Referential transparency collapses
    the identity/value distinction the nagini launder rival exploited.
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. The nagini
    prepatch-oneshot, last-round-zero (fence-post) and off-value rivals re-express
    directly onto the RE-READABILITY / COUNT / CONTENT sub-behaviours.
  * DIVERGENCE / NON-TERMINATION — the spec REJECTS it, but it is not shippable
    as a reject case on this carrier, for a TOOLING reason measured with real
    builds (not "the proof was hard"). Under ``termination "total"`` a diverging
    rival is genuinely refused, and both shapes were built:
      - DROP the ``decreasing`` clause: refused, but by a FILE-LEVEL linter
        error — ``Decreasing annotations are required in total correctness
        semantics``. That error fires whatever else the file contains, so the
        witness file does not compile either: the same module with a trivially
        true ``example : (1:Nat) + 1 = 2 := by decide`` appended also exits 1.
        A witness therefore cannot ELABORATE against this rival, which is the
        half of the discrimination check that must SUCCEED, so the gate would
        record ``witness-unproven`` — inconclusive, not a pass.
      - KEEP ``decreasing i`` but never decrement ``i``: refused on the loop
        invariant (``invariant_4`` unsolved), and the module itself is fine (the
        trivial-claim control exits 0). But the rival still carries the ``while``
        loop, so the refutation witness does not reduce against it either —
        ``unsolved goals ⊢ ¬(NonDetT.run do let r ← forIn Lean.Loop.mk ...)``,
        the same stuck ``forIn`` term documented under WITNESS SUBJECT. So this
        shape cannot carry a discriminating witness on this carrier.
    Both are recorded here rather than dropped silently: the spec is NOT too weak
    on divergence (it rejects both), and the gap is in what a witness can be
    stated over, not in the obligation.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; ``materialize``
is a deep A-reference validated == the real ``check_cv`` by axiom_check.py — that
is G-AX's job, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25973"
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
# these keeps markers.same_spec True and the prove_correct runScoringRounds
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward round loop over a
# materialized, re-readable source). Reject rivals and the direct positive
# control replace it with a loop-free closed form so their extracted program
# reduces under simp/decide.
_IMPL = (
    "    -- impl-start\n"
    "    let mut src := materialize source\n"
    "    let mut obs : List Splits := []\n"
    "    let mut i := k\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ k\n"
    "      invariant src.reusable = true\n"
    "      invariant src.splits = source.splits\n"
    "      invariant obs = List.replicate (k - i) source.splits\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let o := readObs src\n"
    "      src := advance src\n"
    "      obs := o :: obs\n"
    "      i := i - 1\n"
    "    return obs\n"
    "    -- impl-end"
)

# The two per-round mutation statements, in gold order. The reorder positive
# control commutes them (both operate on values already bound this iteration, so
# the reshape is semantically identical and the frozen proof still closes).
_LOOP_STEP = (
    "      let o := readObs src\n"
    "      src := advance src\n"
    "      obs := o :: obs\n"
    "      i := i - 1"
)

# The frozen prove_correct tactic body (unique in the file, elided from the spec
# view). The direct positive control retunes it (the loop is gone, so loom_solve
# alone closes the residual goal); every reject rival keeps it as-is (it fails to
# close the wrong impl, which is the intended rejection, but the witness — not the
# tactic failure — is what the gate scores).
_PROOF = (
    "prove_correct runScoringRounds by\n"
    "  loom_solve\n"
    "  rw [readObs_reusable src (by assumption)]\n"
    "  rw [replicate_step source.splits k i (by omega) (by omega)]\n"
    "  simp_all"
)


def _rival(expr: str) -> str:
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`."""
    body = "    -- impl-start\n    return (" + expr + ")\n    -- impl-end"
    return _swap(
        _swap(_BASE, _IMPL, body),
        _PROOF,
        "prove_correct runScoringRounds by\n  loom_solve")


# The witness SUBJECT for every reject case: the loop-free grounded closed form.
# It is also `pos-control-direct`'s module, so the battery independently asserts
# (and the gate independently re-checks) that it shares the frozen spec and
# VERIFIES. Needed because the frozen impl's extracted `while` loop does not
# reduce, making its build fail for every claim regardless of truth — see the
# WITNESS SUBJECT paragraph in the module docstring for the measured evidence.
_CLOSED_FORM = _rival("List.replicate k source.splits")


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `runScoringRoundsExec s n` is `NonDetT.run (runScoringRounds s n)`;
# ---- `≠ DivM.res (List.replicate n s.splits)` says the impl's output
# ---- contradicts the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. The loop-free rival reduces under `simp`; gold's loop stays stuck,
# ---- so the same witness fails on gold — the required discrimination.
_EXTRACT = "extract_program_for runScoringRounds\n\n"


def _witness(src_expr: str, k_expr: str) -> str:
    return _EXTRACT + (
        "example : runScoringRoundsExec (" + src_expr + ") " + k_expr + " ≠ "
        "DivM.res (List.replicate " + k_expr + " ("
        + src_expr + " : CvSource).splits) := by\n"
        "  unfold runScoringRoundsExec runScoringRounds\n"
        "  simp [NonDetT.run, pure]\n"
    )


# Concrete carrier literals used by the reject witnesses.
_SINGLE_PASS = "{ splits := [7], reusable := false, consumed := false }"
_REUSABLE_2 = "{ splits := [3, 4], reusable := true, consumed := false }"
_REUSABLE_1 = "{ splits := [5], reusable := true, consumed := false }"
_REUSABLE_9 = "{ splits := [9], reusable := true, consumed := false }"
# An ALREADY-EXHAUSTED single-pass source: `consumed = true` was the one input
# field no case varied, so no rival probed whether the spec still demands the full
# sequence there. It does: the clause reads `source.splits`, not `readObs source`.
_SPENT = "{ splits := [2, 8], reusable := false, consumed := true }"


# The ADMISSIBILITY probe's in-region assert. The frozen impl is kept VERBATIM
# (this text is inserted directly after `-- impl-start`, so the method's own
# obligation still discharges); only the extra assert goal is added, and the
# proof body gains a fallback branch to close it. `assert` is the Loom in-region
# assertion gadget, so a FALSE claim here leaves an unsolved `admiss_1` goal —
# the case is live, not decoration.
#
# What it discharges, BY EVALUATION, at the F2P-shaped input (a fresh
# single-pass source with split sequence [7], run for k=2 rounds): the
# obligation's post-image is SATISFIABLE there (it equals a concrete record) and
# NON-DEGENERATE — it differs from both shapes a defective read produces, the
# exhausting read `[[], [7]]` and the one-round-short `[[7]]`. That is the
# analogue of the sibling's precondition-admits-this-input probe on a total
# carrier: the risk it retires is an obligation no impl can satisfy at exactly
# the reported input, which would read like a spec every impl satisfies.
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `admiss\n"
    "      (List.replicate 2 ([7] : Splits) = [[7], [7]] ∧\n"
    "       List.replicate 2 ([7] : Splits) ≠ List.replicate 1 ([] : Splits) ++ [[7]] ∧\n"
    "       List.replicate 2 ([7] : Splits) ≠ List.replicate 1 ([7] : Splits))"
    ")\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). The post-image `List.replicate k source.splits` is
    # GROUNDED in the input (a total function of `source.splits` and `k`), so
    # `return List.replicate k source.splits` is a correct fully-grounded
    # implementation, not an ungrounded-oracle echo — and it doubles as proof the
    # spec is not echo-vulnerable at the CONTENT/COUNT level (any wrong constant
    # fails `obs = List.replicate k source.splits`). The loop is gone, so the
    # frozen proof body's loop reasoning is unneeded and the residual goal closes
    # under `loom_solve` alone.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Same source as `_CLOSED_FORM`, which every reject case names as its
        # `witness_reference`: this case is what establishes that the subject the
        # refutations are checked against actually VERIFIES.
        "module": _CLOSED_FORM,
        "rationale": "the post-image `List.replicate k source.splits` is GROUNDED "
                     "in the inputs (a total function, no opaque answer key), so "
                     "returning it is the honest cheapest CORRECT impl. It MUST "
                     "verify — the clause is literally `obs = List.replicate k "
                     "source.splits` — else the single postcondition clause is "
                     "SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable at "
                     "the value level: any wrong constant/truncation/augmentation "
                     "fails the clause. Built to verify (exit 0).",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that keeps the frozen backward loop and ALL its invariants BYTE-IDENTICAL,
    # only commuting the two per-round mutation statements (`src := advance src`
    # and `obs := o :: obs`). Both operate on values already bound this iteration
    # (`o = readObs src` was read before either), so the reshape is semantically
    # identical and every loop invariant plus the obligation still discharge under
    # the frozen proof script with no retune. A faithful correct reshape that could
    # NOT verify would mean the postcondition is over-fit to one statement ORDER =>
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _LOOP_STEP,
            "      let o := readObs src\n"
            "      obs := o :: obs\n"
            "      src := advance src\n"
            "      i := i - 1"),
        "rationale": "structurally different CORRECT reshape: the two per-round "
                     "mutation statements are commuted (both read from values "
                     "already bound this iteration), keeping every loop invariant "
                     "byte-identical. `obs = List.replicate k source.splits` still "
                     "discharges under the frozen proof. A faithful reshape MUST "
                     "verify, else the clause is over-fit to statement order => "
                     "SPEC-TOO-STRONG. Built to verify (exit 0).",
    },

    # =====================================================================
    # ADMISSIBILITY — the lane that detects PRECOND-TOO-STRONG. This bundle
    # declares NO `require` clause, so the sibling's "the precondition admits
    # this input" probe has no precondition to interrogate. That does NOT make
    # the lane vacuous: on a TOTAL carrier the analogue is the obligation being
    # UNSATISFIABLE (or degenerate) at exactly an F2P-shaped input, which reads
    # like a spec every impl meets while in fact no impl can meet it. This case
    # tests that directly, by evaluation, at the reported input shape: a fresh
    # single-pass source with split sequence [7] run for k=2 rounds. The frozen
    # impl is kept VERBATIM so the method's own obligation still discharges; the
    # only additions are the in-region assert and a fallback proof branch that
    # closes the extra goal (both inside regions the spec view elides).
    #
    # Measured live, not assumed: the true claim verifies (exit 0) and each
    # conjunct flipped to a FALSE claim about the same point leaves an unsolved
    # `admiss_1` goal (exit 1) — so the assert is load-bearing.
    # =====================================================================
    {
        "id": "admiss-oneshot-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, "    -- impl-start\n",
                  "    -- impl-start\n" + _ADMISS_ASSERT),
            _PROOF,
            _PROOF + "\n  all_goals first\n    | decide\n    | simp_all"),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at the "
                     "F2P-shaped input (a fresh single-pass source with split "
                     "sequence [7], run for k=2 rounds): the required record is "
                     "the concrete [[7], [7]], and it differs from BOTH shapes a "
                     "defective read yields — the exhausting read [[], [7]] and "
                     "the one-round-short [[7]]. This bundle has no `require` "
                     "clause, so this is the total-carrier analogue of the "
                     "sibling's precondition-admits-this-input probe: it retires "
                     "the risk of an obligation no impl can discharge at exactly "
                     "the reported input, which would read like a spec every impl "
                     "satisfies => PRECOND-TOO-STRONG. The frozen impl is kept "
                     "verbatim so the ensures clause discharges too. Built to "
                     "verify (exit 0); each conjunct flipped false fails (exit 1).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- RE-READABILITY sub-behaviour: read the raw single-pass source (the
    # ---- pre-patch control flow) instead of a re-readable one ----
    {
        "id": "weak-no-materialize-oneshot",
        "kind": "uniqueness",
        "expect": "reject",
        # For a re-readable source, correct; for a single-pass source, model
        # reading the raw source directly per round: round 0 observes the full
        # sequence, every later round observes the empty sequence (exhausted).
        # This is the pre-patch behaviour, refuted at a single-pass source.
        "module": _rival(
            "if source.reusable then List.replicate k source.splits "
            "else (List.replicate (k - 1) ([] : Splits)) ++ [source.splits]"),
        "refinement": "this IS the pre-patch control flow: read the configured "
                      "single-pass source directly on every round without buffering "
                      "it into a re-readable one first. Round 0 observes the full "
                      "split sequence, every later round observes the empty sequence "
                      "(the source is exhausted) — so a multi-round run over a "
                      "single-pass split source aggregates an empty split set and "
                      "raises on the second round, exactly the reported failure. A "
                      "faithful counterpart with this defect still exhausts the "
                      "single-pass source, so the failing test would NOT resolve.",
        "rationale": "REJECT from `obs = List.replicate k source.splits` "
                     "(RE-READABILITY): for `reusable = false, consumed = false` the "
                     "rival records the full sequence once then the empty sequence, "
                     "not the full sequence `k` times. Refuted at "
                     "(single-pass source with splits [7], k=2): the rival returns "
                     "[[], [7]] while the spec requires [[7], [7]]. This is the ONLY "
                     "rival probing `reusable = false` — the load-bearing binder the "
                     "fix targets.",
        "witness": _witness(_SINGLE_PASS, "2"),
        "witness_reference": _CLOSED_FORM,
    },

    # ---- COUNT sub-behaviour: drop the final round (fence-post slip) ----
    {
        "id": "weak-last-round-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Records the full sequence on rounds 0..k-2 but the EMPTY sequence on the
        # final round — a fence-post slip that scores the last round on nothing.
        "module": _rival(
            "List.replicate (k - 1) source.splits ++ [([] : Splits)]"),
        "refinement": "a fence-post slip that scores the final round on an empty "
                      "split set (records the empty sequence on the last round) "
                      "would, in the real code, aggregate an empty cross-validation "
                      "result on that round and raise there; the faithful patch does "
                      "NOT resolve.",
        "rationale": "REJECT from `obs = List.replicate k source.splits` (COUNT / "
                     "last-round CONTENT): correct on rounds 0..k-2 but records the "
                     "empty sequence on round k-1. Refuted at (re-readable source "
                     "with splits [3,4], k=2): the rival returns [[3,4], []] while "
                     "the spec requires [[3,4], [3,4]]. Varies `k` to a "
                     "multi-round run over a re-readable source.",
        "witness": _witness(_REUSABLE_2, "2"),
        "witness_reference": _CLOSED_FORM,
    },

    # ---- CONTENT sub-behaviour: augment each recorded observation ----
    {
        "id": "weak-augmented-observation",
        "kind": "uniqueness",
        "expect": "reject",
        # Each round records the source's split sequence with a spurious extra
        # split appended — the observed sequence must equal source.splits exactly.
        "module": _rival(
            "List.replicate k (source.splits ++ [0])"),
        "refinement": "recording one more split than the source actually yields "
                      "has no faithful real-patch counterpart that resolves — the "
                      "observed split sequence is determined by the source's own "
                      "contents, and inventing an extra split is not behaviour the "
                      "gold patch produces; a real impl that fabricated a split "
                      "would score on a phantom fold and diverge from the expected "
                      "result.",
        "rationale": "REJECT from `obs = List.replicate k source.splits` (CONTENT): "
                     "each round records `source.splits ++ [0]`, not `source.splits`. "
                     "Refuted at (re-readable source with splits [5], k=1): the "
                     "rival returns [[5, 0]] while the spec requires [[5]]. Varies "
                     "`k` to a single round and `source.splits` to a singleton, "
                     "isolating the per-round CONTENT clause.",
        "witness": _witness(_REUSABLE_1, "1"),
        "witness_reference": _CLOSED_FORM,
    },

    # ---- COUNT sub-behaviour: too few rounds recorded ----
    {
        "id": "weak-undercount-rounds",
        "kind": "uniqueness",
        "expect": "reject",
        # Records the full sequence but only k-1 times — one round short.
        "module": _rival("List.replicate (k - 1) source.splits"),
        "refinement": "recording one fewer round than requested skips a scoring "
                      "round entirely; a faithful counterpart that ran the loop one "
                      "iteration short would omit a greedy selection step and "
                      "produce a different (wrong) feature set, so it would NOT "
                      "resolve the behaviour the tests fix.",
        "rationale": "REJECT from `obs = List.replicate k source.splits` (COUNT): "
                     "the record has length k-1, not k. Refuted at (re-readable "
                     "source with splits [9], k=3): the rival returns "
                     "[[9], [9]] (length 2) while the spec requires "
                     "[[9], [9], [9]] (length 3). Varies `k` to a third distinct "
                     "round count (3), attacking the length/COUNT clause directly.",
        "witness": _witness(_REUSABLE_9, "3"),
        "witness_reference": _CLOSED_FORM,
    },

    # ---- RE-READABILITY sub-behaviour at the ALREADY-EXHAUSTED source: honour
    # ---- the source's own consumed flag instead of buffering it ----
    {
        "id": "weak-respect-consumed-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. `consumed` was the one input field no case varied, so
        # nothing tested whether the spec still demands the full sequence from a
        # source that already reports itself exhausted. This rival reads the raw
        # source's OBSERVATION (empty once consumed) rather than buffering it
        # first, so it records k empty sequences at a spent source while staying
        # correct everywhere else.
        "module": _rival(
            "if source.consumed then (List.replicate k ([] : Splits)) "
            "else List.replicate k source.splits"),
        "refinement": "this is the same omission as the primary rival seen from "
                      "the other side: propagate the source's own exhaustion state "
                      "into every round rather than buffering the source into a "
                      "re-readable one up front. A caller that hands over a split "
                      "source which has already been iterated once gets an empty "
                      "split set on every round, so the aggregation raises on the "
                      "first round instead of the second — a faithful counterpart "
                      "with this defect still fails the reported behaviour, so the "
                      "failing test would NOT resolve.",
        "rationale": "REJECT from `obs = List.replicate k source.splits` "
                     "(RE-READABILITY at `consumed = true`): the clause is stated "
                     "over `source.splits`, the source's underlying sequence, NOT "
                     "over `readObs source`, so buffering is demanded even when the "
                     "source arrives already exhausted. Refuted at (spent "
                     "single-pass source with splits [2,8], k=2): the rival returns "
                     "[[], []] while the spec requires [[2,8], [2,8]]. This is the "
                     "ONLY rival varying `consumed`, the last previously-unprobed "
                     "input field, and it pins the buffering step as UNCONDITIONAL.",
        "witness": _witness(_SPENT, "2"),
        "witness_reference": _CLOSED_FORM,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation rival, 5 uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models the SAME purely-functional core — the
# per-round observation record produced by running k scoring rounds against a CV
# split source — but the carrier (`CvSource` value + `List.replicate` post-image)
# COLLAPSES the nagini capability/reference distinction, so the two capability
# rivals (echo, launder) are vacuous here and the value-level partial-domain
# rivals carry the whole port.
#
#   sibling case                     -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-local-reshape        -> pos-control-reorder            PORTED
#   pos-control-assert-shape         -> pos-control-direct             PORTED (as direct)
#   admiss-oneshot-input             -> admiss-oneshot-input           PORTED (re-derived)
#   frame-mutate-src-size            -> (none)                         VACUOUS
#   echo-no-securing                 -> (none)                         VACUOUS
#   launder-value-equal-copy         -> (none)                         VACUOUS
#   partial-domain-prepatch-oneshot  -> weak-no-materialize-oneshot    PORTED (load-bearing)
#   partial-domain-last-round-zero   -> weak-last-round-zero           PORTED
#   off-value-round0                 -> weak-augmented-observation     PORTED
#   (no sibling)                     -> weak-undercount-rounds         ADDED (COUNT clause)
#   (no sibling)                     -> weak-respect-consumed-flag     ADDED BY AUDIT
#   (no sibling)                     -> (none)                         DIVERGENCE:
#                                       spec rejects it, but no witness can
#                                       elaborate against either diverging shape
#                                       (tooling limit, measured — see docstring)
#   AXIOM_TESTS (2)                  -> (none)                         DROPPED (G-AX)
#
# 6 ported, 2 added, 3 vacuous, 2 dropped = 8 SPEC cases (2 soundness,
# 1 admissibility, 5 uniqueness). All 8 built with scripts/lean_verify.sh: both
# positives and the admissibility case verify (exit 0); each rival module fails to
# verify (exit 1, unsolved `ensures_1` goal); each witness elaborates against its
# rival (exit 0) and is REFUTED against the verifying loop-free reference (exit 1,
# residual `⊢ False` — a fully-reduced semantic contradiction, not a stuck term).
#
# AUDIT REPAIR (witness subject). As first authored, every reject case refuted its
#   witness against the FROZEN solution and the gate recorded SOUND. Re-derived
#   with real builds, that gold-side exit code carried NO information: the frozen
#   impl's extracted `while` loop does not reduce, so its build fails for every
#   claim about it. Measured — a TRUE claim about the frozen impl
#   (`runScoringRoundsExec {splits := [3,4], reusable := true, consumed := false} 2
#   = DivM.res (List.replicate 2 [3,4])`) also failed against the frozen solution
#   (exit 1, `unsolved goals` with the `forIn Lean.Loop.mk` fixpoint intact) while
#   elaborating (exit 0) against the loop-free closed form; and a forgery asserting
#   a rival is CORRECT at an agreement point cleared the gold side too. Because the
#   failure reads as plain `unsolved goals` rather than a `decide`-flavoured stuck
#   message, the gate's automatic stuck screen does not fire here. Every reject
#   case now names `witness_reference = _CLOSED_FORM` (the verifying loop-free
#   impl, which the gate independently checks shares the spec and verifies), so
#   each refutation is observed as a computed `⊢ False` rather than a stuck loop.
#   The rivals and the spec were not weakened; only the SUBJECT changed.
#
# PORTED (2 positive controls): the sibling's local-reshape (compute into a local
#   then append) ports as pos-control-reorder (commute the two per-round mutation
#   statements, all invariants byte-identical, frozen proof unchanged); the
#   sibling's assert-shape control ports as pos-control-direct (`return
#   List.replicate k source.splits`, the grounded closed form — the loop is gone
#   so loom_solve alone closes the residual).
# PORTED (3 partial-domain rivals): prepatch-oneshot re-expresses as the
#   no-materialize closed form (read the raw single-pass source: full sequence
#   round 0, empty thereafter); last-round-zero as the fence-post (empty final
#   round); off-value-round0 as the augmented per-round observation. Each
#   refinement carries over: a faithful counterpart with that defect still
#   exhausts / mis-scores the split source and the failing test would NOT resolve.
# ADDED (1): weak-undercount-rounds attacks the COUNT clause with a third distinct
#   round count (k=3), so the round-count binder `k` is varied across three values
#   (1, 2, 3) and both the length and the per-round content facets are attacked.
# ADDED BY AUDIT (1): weak-respect-consumed-flag. `consumed` was the one input
#   field NO case varied — every witness stood at `consumed = false` — so nothing
#   tested whether the spec still demands the full sequence from a source that
#   already reports itself exhausted. It does: the clause reads `source.splits`,
#   not `readObs source`, which makes the buffering step UNCONDITIONAL. The rival
#   propagates the source's own exhaustion instead and records k empty sequences
#   at a spent source; refuted at (splits [2,8], reusable false, consumed true,
#   k=2), rival exit 0 / reference exit 1 with residual `⊢ False`.
# VACUOUS (echo-no-securing): the sibling echo cheat attacks a capability
#   predicate (`presents_family`) with no value-level witness. This bundle has NO
#   capability clause — the single clause is purely the value-level split sequence
#   grounded in `source.splits` — so echoing that sequence k times is the CORRECT
#   answer (it is literally pos-control-direct). There is no wrong echo to build;
#   the carrier collapsed the distinction. Not fabricated.
# VACUOUS (launder-value-equal-copy): the sibling token is tied to the object
#   REFERENCE, so a value-equal copy fails it. This backend is referentially
#   transparent — a value-equal `CvSource` is EQUAL and the spec observes only the
#   value-level split sequence — so a laundered copy satisfies the clause and is
#   not wrong. Not fabricated.
# VACUOUS (frame-mutate-src-size): the sibling carries this MANDATORY because the
#   source is held at half permission and a rival can illegally store into it.
#   This backend is referentially transparent and declares no `mut` binder —
#   `source` is an immutable value with no heap footprint — so there is no
#   read-only input to overwrite and no substitute probe. Not fabricated.
# PORTED, RE-DERIVED BY AUDIT (admiss-oneshot-input): the previous port recorded
#   this lane VACUOUS because the bundle declares no `require` clause. That reason
#   was wrong — it retires only the PRECONDITION reading of admissibility, while
#   the lane's job is to detect PRECOND-TOO-STRONG, whose total-carrier analogue
#   is the obligation being UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped
#   input. "The post-image is total, so it is satisfiable everywhere by
#   construction" is an ARGUMENT, and this gate's currency is a machine-checked
#   case; a battery with no admissibility case tests two of the three directions
#   the gate exists for (the coverage reporter flags exactly this). Re-landed as
#   an in-region `assert`, discharged BY EVALUATION at the reported input shape (a
#   fresh single-pass source with split sequence [7], k=2 rounds): the required
#   record is the concrete [[7], [7]] and it differs from both degenerate shapes a
#   defective read yields ([[], [7]] and [[7]]). Frozen impl kept VERBATIM, so the
#   ensures clause still discharges; proof gains only a fallback branch for the
#   extra goal. Live, not decoration: the true claim verifies (exit 0) and each
#   conjunct flipped FALSE leaves an unsolved `admiss_1` goal (exit 1).
# DIVERGENCE lane: the spec REJECTS divergence (so NOT a spec hole), but the case
#   is NOT shippable here, for a tooling reason measured with real builds. Both
#   shapes were built; see the DIVERGENCE bullet in the module docstring for the
#   exit codes and error text. Dropping the `decreasing` clause trips a
#   FILE-LEVEL linter error, so the witness file does not compile at all (a
#   trivially true appended claim also exits 1) and the witness cannot ELABORATE
#   against the rival — the half that must succeed, so the gate would record
#   `witness-unproven`. Keeping `decreasing i` but never decrementing is refused
#   on `invariant_4`, but that rival retains the `while` loop, so the witness hits
#   the same stuck `forIn Lean.Loop.mk` term as gold does. Recorded as a carrier/
#   tooling limit on WITNESS EXPRESSIBILITY, not as a vacuous class and not as a
#   spec hole.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference `materialize` == the real `check_cv`); this bundle consumes no
#   axiom `ensures`, and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has input binders `source` (fields
#   `splits`, `reusable`, `consumed`) and `k`, and a single top-level clause
#   `obs = List.replicate k source.splits` with three independent sub-behaviours
#   (re-readability, content, count). The five reject witnesses probe five
#   DISTINCT input points:
#     * single-pass source, splits [7], k=2    (RE-READABILITY at `consumed=false`
#       — the fresh one-shot shape the fix targets)
#     * spent source, splits [2,8], k=2        (RE-READABILITY at `consumed=true`;
#       the ONLY witness varying `consumed`)
#     * re-readable source, splits [3,4], k=2  (COUNT / last-round content)
#     * re-readable source, splits [5], k=1    (per-round CONTENT)
#     * re-readable source, splits [9], k=3    (COUNT / length)
#   so `source.reusable` is varied (false vs true), `source.consumed` is varied
#   (false vs true), `source.splits` is varied in both length and contents ([7],
#   [2,8], [3,4], [5], [9]), and `k` is varied across three values (1, 2, 3). Each
#   sub-behaviour is attacked by at least one rival; the two positive controls
#   defend the whole obligation. No two rivals are refuted at the same input, and
#   every variation is MEANINGFUL — each probed point is one where the rival's
#   value and the spec's required value actually differ (each refutation reduces to
#   a computed `⊢ False`, so no point is two spellings of the same case).
#   pts = 5 distinct input points across 5 witnesses. The admissibility case adds a
#   sixth probed point (a fresh single-pass source, splits [7], k=2) on the
#   POSITIVE side: it is the only case that pins the obligation's required value at
#   a concrete input by evaluation rather than refuting a rival there.
# WITNESS DISCRIMINATION (re-derived by audit with three real builds per reject
#   case): each witness ELABORATES against its loop-free rival (exit 0 — the
#   extracted closed form reduces under simp to a literal that provably differs
#   from `List.replicate k source.splits` at the probed input) and is REFUTED
#   against `witness_reference` (exit 1, residual `⊢ False`: the reference reduces,
#   so the contradiction is COMPUTED and the refutation is semantic). The frozen
#   solution is deliberately NOT the subject — its loop does not reduce, so its
#   exit code discriminates nothing; see the AUDIT REPAIR note above for the
#   measured true-claim and forgery builds that established this. No witness binds
#   a hypothesis (the carrier is fully transparent), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
# SPEC PROBES the audit ran and the spec SURVIVED (no hole found): honour the
#   `consumed` flag (now shipped as a case); emit a spurious round at k=0; truncate
#   `source.splits.tail` when the source is not re-readable — all three FAILED to
#   verify (exit 1), so the clause is not too weak there. Correct reshapes that DO
#   verify: a FORWARD counting loop appending to the tail (exit 0) and a
#   `(List.range k).map (fun _ => source.splits)` closed form (exit 0) — so the
#   clause is not over-fit to the frozen loop's direction or to `List.replicate`'s
#   shape, and is not too strong.
# SECOND-AUDIT SPEC PROBES (a later, independent pass; all built for real, none
#   found a hole). Aimed at what the shipped rivals leave unattacked:
#     * per-round CONTENT ORDER — `List.replicate k source.splits.reverse`
#       (no shipped rival attacks ordering): REJECTED, exit 1.
#     * OVERCOUNT — `List.replicate (k + 1) source.splits` (shipped COUNT rivals
#       only ever undercount): REJECTED, exit 1.
#     * wrong ONLY at the EMPTY split sequence — `if source.splits = [] then
#       List.replicate (k + 1) [] else ...`, a sub-domain no shipped witness
#       stands at (every shipped witness has non-empty `splits`): REJECTED, exit 1.
#     * content truncation only on MULTI-round runs — `if k ≤ 1 then ... else
#       List.replicate k (source.splits.take 1)`, probing the k/content
#       interaction: REJECTED, exit 1.
#   Correct reshapes that VERIFY (so not too strong either): routing the post-image
#   through the pure helpers, `List.replicate k (readObs (materialize source))`
#   (exit 0 — the helpers' own lemmas carry it), and an independently re-derived
#   `(List.range k).map` closed form proven by induction on `k` (exit 0).
AXIOM_TESTS = []
