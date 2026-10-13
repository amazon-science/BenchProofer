"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14053 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct buildLabels`` obligation survives with its header intact) and
swaps in a candidate implementation; the real verifier is re-run on each.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against its
``witness_reference`` — a verifying impl of the same spec, used here because the
frozen program's tester cannot be decided at all; see the CARRIER NOTE).

DEFENDED SURFACE (one contracted method, three read-only inputs, ONE clause):

  buildLabels (names : List Name) (sentinel : Int) (refs : List Int)
      return (out : List (Option Name))
    require ∀ i ∈ refs, i ≠ sentinel → (0 ≤ i ∧ i.toNat < names.length)
    ensures out = labelsOf names sentinel refs                      -- (C1)

The method resolves a list of integer references against a table of names: each
reference is either a valid position in the table (the item is labelled by that
entry) or the distinguished ``sentinel`` (the item has no label). The result
carries, for every reference IN ORDER, its resolved label.

  * (C1) pins ``out`` to ``labelsOf names sentinel refs`` — the fully-unfolded
    front-recursive resolution of the method's OWN three arguments. Every ``def``
    it is built from (``labelsOf``, ``labelOne``) is TRANSPARENT: the ``axioms``
    region declares no opaque leaf and no ``axiom``, so there is no answer-key
    oracle for a wrong impl to echo and pinning ``out`` to it is grounded, not an
    echo (spec_guide directive 8). C1 is a single top-level clause, but it is not
    a single obligation: it simultaneously pins the LENGTH (one label per
    reference), the ORDER (position-for-position), the SENTINEL branch (a
    sentinel reference resolves to "no label", and is NOT used as a position in
    the table), and the TABLE branch (a non-sentinel reference resolves to the
    entry AT THAT position — not to some other entry, and not to the reference's
    own value). The reject lane attacks all four independently.
  * The ``require`` is the only precondition, and it deliberately places NO
    obligation on a sentinel reference — the table may be shorter than the
    sentinel's magnitude. That asymmetry is the whole point of interest, and it
    is what makes ``weak-index-every-reference`` a real rival rather than a typo:
    an impl that indexes unconditionally has no precondition to lean on.

THREE INPUT BINDERS, all load-bearing and all varied by the reject witnesses:
``names`` (the table — its LENGTH and its CONTENT both matter, since a label is
a specific entry), ``sentinel`` (a free parameter, so nothing may be assumed
about its magnitude), and ``refs`` (the reference stream — its length, its order,
and which of its entries are sentinels). The seven reject witnesses drive them
across SEVEN distinct input points (pts = 7); see the COVERAGE accounting.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHAT THE GOLD-SIDE FAILURE IS WORTH.
A witness reaches the post-image through Velvet's tester machinery
(``buildLabelsTester names sentinel refs = false`` says the extracted program's
result violates the postcondition at that concrete input) and closes by
``decide``, checked in a file whose ``prove_correct`` block has been stripped so
no tactic script can mask the verdict. ``decide`` reduces the extracted program
by kernel computation. Each reject rival is expressed LOOP-FREE (a ``refs.map``
with a wrong per-reference step, or a wrong assembly of the mapped list) so its
extracted tester ``decide``s over the concrete literals; the frozen program is a
``while`` loop under ``loom.semantics.choice "demonic"`` whose fixpoint the
kernel will not unfold, so the same witness applied to the FROZEN solution does
NOT reduce to ``isTrue``/``isFalse``.

READ THAT HONESTLY. The gate's FAIL-on-gold half is therefore satisfied here for
a REDUCTION-STUCK reason, not by a semantic refutation of gold — measured
verbatim on every one of the seven:

    error: Tactic `decide` failed for proposition
      buildLabelsTester [0] (-2) [-2] = false
    because its `Decidable` instance ... did not reduce to `isTrue` or `isFalse`.

A TAUTOLOGOUS witness would produce that same failure, so that half attests
nothing about discrimination on this bundle. The CONTROL below is what does:

  DISCRIMINATION CONTROL (measured, not argued). Every reject witness was also
  built against a CORRECT loop-free impl — the same ``refs.map`` shape as the
  rivals, with the RIGHT per-reference step, which VERIFIES against the frozen
  spec (shipped as ``pos-control-map-correct-step``). There the tester DOES
  reduce, and ``decide`` refutes each witness SEMANTICALLY:
  ``Tactic `decide` proved that the proposition buildLabelsTester … = false is
  false`` (exit 1, all seven). So each witness holds of its rival and provably
  FAILS of a correct impl at the same input on the same carrier shape. That is
  the discrimination the stuck-on-gold build cannot supply.
  This is ENFORCED, not merely documented: every reject case names that impl as
  its ``witness_reference``, so the gate itself checks the reference shares the
  frozen spec and VERIFIES, then refutes the witness against IT rather than
  against the undecidable frozen tester.

Every carrier value is fully transparent (concrete ``List``/``Int``/``Option``
literals), so no witness binds a hypothesis and no consistency probe is needed.
All witnesses checked out-of-band with ``scripts/lean_verify.sh``: ELABORATES
against its rival (exit 0), refuted against the correct-step map (exit 1,
``decide`` proved it false), stuck against the frozen loop (exit 1).

PROOF-SHAPE CONTROL — why each rejection is attributable to the STEP. A reject
rival's proof body must not be a script that would also fail for a CORRECT impl
of the same shape, or the rejection attests to a tactic mismatch rather than to
the spec. Measured: the naive flat body (``loom_solve`` alone) fails IDENTICALLY
on a loop-free ``refs.map`` carrying the CORRECT per-reference step (exit 1,
``unsolved goals … ⊢ List.map (fun i => labelOne names sentinel i) refs =
labelsOf names sentinel refs``) — so it would have been exactly that confound.
Every reject rival therefore carries ``_PROOF_MAP``, a body whose ``hmap``
induction PROVABLY closes C1 for the correct step (that is
``pos-control-map-correct-step``, exit 0). Under it each rival still fails, and
the residual goal names the rival's OWN step — e.g. ``⊢ List.map (fun i =>
names[i.toNat]?) refs = labelsOf names sentinel refs`` — which is the
attribution.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally different but
    behaviourally identical impls must verify, else the spec is SPEC-TOO-STRONG
    on the shape of the impl rather than on its behaviour.
  * ADMISSIBILITY — the sibling's probe is that the precondition admits a normal,
    test-shaped input; it establishes that by a self-call whose fractional
    permissions round-trip. There is no permission surface here, so the probe
    re-aims onto what CAN go wrong on this carrier: a precondition that is
    contradictory at the input shape the failing test actually presents (a table
    SHORTER than the sentinel's magnitude — the exact configuration the sibling's
    domain predicate is about), and a DEGENERATE post-image.
    ``admiss-short-table`` discharges an in-region ``assert`` covering both.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries TWO
    MANDATORY frame-mutation rivals (write into the read-only reference stream,
    write into the read-only name table), each rejected for INSUFFICIENT
    PERMISSION because the input is held at a fractional heap permission. Lean
    and Velvet are referentially transparent: ``names``, ``sentinel`` and ``refs``
    are immutable values declared read-only (no input is ``mut`` — only the
    loop-local ``result``/``idx`` are), there is no heap, no aliasing, no ``Old``,
    and no permission system. There is no read-only input to overwrite and no
    frame clause to violate, so the class has no carrier analogue. Not ported;
    fabricating a substitute would test nothing. See the accounting.
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
    loop in the impl (1 loop here, measure ``idx``). A rival that loops without
    a measure is refused outright (``Decreasing annotations are required in
    total correctness semantics``), and a rival that supplies a CONSTANT
    measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * UNGROUNDED-ORACLE ECHO — N/A, and the sibling says so too: C1 is pinned to
    ``labelsOf``, a fully-unfolded ``def`` over the method's own arguments, so
    "echoing the model" IS doing the work. The positives cover the honest shapes.
  * CONTROL-FLOW-EFFECT — N/A. The method returns a pure list of resolved labels;
    there is no raise / side-effect difference invisible to the value
    abstraction. The pre-image's failure on a short table has a total value
    image on this carrier (the sentinel branch), so it is fully value-visible and
    ``weak-index-every-reference`` reaches it as a value rival.
  * PARTIAL-DOMAIN / VALUE / LENGTH / ORDER — carry the reject lane, seven rivals
    deep. Each gets most of the domain right and diverges on one sub-domain, and
    each is refuted at the input point that isolates it.

DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
is REJECTED rather than admitted. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
two lines have to move together, and they do here. Under the total scope a
postcondition is claimed of ALL runs, not only of terminating ones, and the
verifier emits a descent obligation ``measure b' < measure b`` for every loop
in the impl (1 loop here, measure ``idx``). A rival that loops without a
measure is refused outright (``Decreasing annotations are required in total
correctness semantics``), and a rival that supplies a CONSTANT measure to dodge
that is refused on the measure's own goal (``case «decreasing_1: spin» ... ⊢
spin < spin``), re-measured on this bundle with a real build. Divergence
therefore does not discharge the ``ensures`` clauses vacuously. It is still not
shipped as a G-PBT reject case, and the reason is the witness contract rather
than a spec weakness. A reject case must carry a witness that ELABORATES
against the rival, and neither diverging shape gets past that. With NO measure
the descent obligation fails at the ``method`` itself, ahead of any appended
tester, and the witness file retains the ``method`` (it strips only the
``prove_correct`` obligations), so the rival module does not compile at all. With
a measure that does not decrease the refusal moves to the ``prove_correct`` site,
which IS stripped, so that module does elaborate; but the rival's post-image is
then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise to a
value a concrete-input tester can decide. Either way the gate returns
``witness-unproven``, an inconclusive outcome.
Measured through the gate's own ``_check_witness``, even
``example : True := trivial`` comes back ``witness-unproven`` on this rival,
which is an INCONCLUSIVE outcome and would fail the whole battery rather than
pass a case. That is the right behavior: a diverging impl has no output at any
input, so there is no value for a witness to disagree with, and its rejection
is a judgement of the termination obligation rather than a postcondition
violation at a point. Recorded as REJECTED-BY-SPEC and not expressible as a
witnessed case, which is neither a spec hole nor a battery gap.

RETRACTED, RE-MEASURED (what the exhibit below this used to be). A superseded
revision of this docstring displayed an increasing-measure loop

    let mut spin := 0
    while spin >= 0
      invariant spin >= 0
      done_with spin < 0
      decreasing spin
    do
      spin := spin + 1
    return []

and reported that it VERIFIES at exit 0 under a bare ``loom_solve``, returning
the unambiguously wrong empty label list: a verify-does-not-imply-resolve break
and a defect of the frozen SPEC. That is FALSE, and was re-built verbatim on THIS
bundle to check rather than argued away. The shape is REJECTED, exit 1, on the
measure's OWN descent goal: ``case «decreasing_1: spin»`` with the residual
``spin + 1 < spin``, unsolved. Supplying a ``decreasing`` clause does not satisfy
the obligation by being present; its descent is proved like any other goal. So
the spec does not admit the rival, and the corpus census that revision cited (a
``partial`` cohort against a ``total`` one, from an internal findings doc now
deleted) had no referent either: all 500 velvet bundles set ``"total"``.

The disposition above therefore stands unchanged and for the reason given there:
divergence is CLOSED BY THE SEMANTICS on this cell, and unshippable only because
of the witness contract, not because the spec admits anything.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The bundle declares no ``axiom`` and
no deep-model reference at all (mapping.md §3: the whole computation is concrete
list arithmetic over the inputs, so G-AX correctly returns ``skip``), and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14053"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ANCHORS. Each lies wholly inside a region the consumer spec view elides (the
# impl region, or the `prove_correct` tactic body) and each is unique in the
# file — both facts asserted at import, so the manifest breaks LOUDLY if the
# frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole frozen impl block, markers included: the single anchor every
# loop-free variant (all seven rivals, two of the three positives, the witness
# reference) swaps out.
_IMPL = """    -- impl-start
    -- Walk the references back-to-front, prepending each resolved label.
    -- Resolution is per-reference: a sentinel reference becomes `none` directly
    -- (it is NOT used to index `names`); any other reference indexes the table.
    let mut result : List (Option Name) := []
    let mut idx := refs.length
    while idx > 0
      invariant 0 ≤ idx ∧ idx ≤ refs.length
      invariant result = labelsOf names sentinel (refs.drop idx)
      done_with idx = 0
      decreasing idx
    do
      let i := refs[idx - 1]!
      let lbl : Option Name := labelOne names sentinel i
      result := lbl :: result
      idx := idx - 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# The four loop-body lines, wholly inside the impl region and unique. The
# loop-preserving positive reshapes only these, leaving the loop, the invariants
# and (bar one unfolding) the frozen proof script alone.
_LOOP_BODY = """      let i := refs[idx - 1]!
      let lbl : Option Name := labelOne names sentinel i
      result := lbl :: result
      idx := idx - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# The impl-start marker line. The admissibility case inserts an in-region
# `assert` immediately after it and keeps the whole frozen body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen proof body (tactic script only; elided from the spec view). Every
# variant that reshapes the impl retunes it, without touching the spec and
# without dropping the `prove_correct buildLabels` obligation.
_PROOF_GOLD = """prove_correct buildLabels by
  loom_solve
  rw [labelsOf_drop_step names sentinel refs idx (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


# ---------------------------------------------------------------------------
# PROOF BODIES for the reshaped impls.
# ---------------------------------------------------------------------------

# For a loop-free `refs.map`: with no loop there is no invariant to peel, but
# `loom_solve` ALONE is not an honest body here. Measured, it leaves C1 unsolved
# for a `refs.map` carrying the CORRECT per-reference step too, so a rejection
# under it would be attributable to the missing map/model bridge rather than to
# the rival's step. `hmap` supplies exactly that bridge — mapping the CORRECT
# per-reference resolution IS the whole-list model — and it PROVABLY closes C1
# for the correct step (`pos-control-map-correct-step`, exit 0). Every reject
# rival carries this same body, so its failure is its STEP's, and the residual
# goal names that step. `have` is a tactic-local hypothesis, not a new top-level
# declaration: the frozen declaration set is unchanged.
_PROOF_MAP = """prove_correct buildLabels by
  have hmap : ∀ (rs : List Int),
      rs.map (fun i => labelOne names sentinel i) = labelsOf names sentinel rs := by
    intro rs
    induction rs with
    | nil => rfl
    | cons r rest ih => rw [List.map_cons, labelsOf_cons, ih]
  loom_solve"""

# For the impl that returns the grounded model directly: nothing is left to
# bridge, so `loom_solve` closes C1 outright.
_PROOF_DIRECT = """prove_correct buildLabels by
  loom_solve"""


def _loopfree(expr, proof=_PROOF_MAP):
    """A loop-free variant returning `expr`. Its extracted tester `decide`s at a
    concrete input, which is what makes a witness against it mean anything."""
    return _swap(
        _swap(_BASE, _IMPL,
              "    -- impl-start\n"
              f"    return {expr}\n"
              "    -- impl-end"),
        _PROOF_GOLD, proof)


# The CORRECT per-reference step, spelled through the frozen pure model.
_STEP_CORRECT = "labelOne names sentinel i"


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. The loop-free map carrying the CORRECT per-reference
# step: a machine-checked-correct impl of the frozen spec whose extracted tester
# REDUCES. Shipped as a positive control in its own right
# (`pos-control-map-correct-step`) and named by every reject case as its
# `witness_reference`, because the FROZEN impl cannot serve as the witness's
# second subject on this bundle: gold's `while` elaborates through
# `Classical.choice`, so `decide` on the frozen tester is STUCK for every claim
# regardless of truth and its exit code discriminates nothing. Refuting each
# witness against THIS impl instead is a real discrimination — an impl the
# verifier ACCEPTS cannot violate its own spec, so a witness that fails here
# fails on the spec's content and not on the kernel's inability to look.
# ---------------------------------------------------------------------------
_REFERENCE = _loopfree(f"refs.map (fun i => {_STEP_CORRECT})")


# ---------------------------------------------------------------------------
# WITNESS PLUMBING. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches the post-image through Velvet's own tester machinery:
# `buildLabelsTester names sentinel refs = false` says the extracted program's
# result violates the method's postcondition at that concrete input. The tester
# returns `true` when the PRECONDITION fails, so a `= false` claim also
# certifies the input is IN the precondition — no witness can cheat by going out
# of domain. Checked in a file whose `prove_correct` block is stripped. Every
# argument is a concrete literal, so nothing is assumed and no consistency probe
# is reached.
# ---------------------------------------------------------------------------
def _witness(names, sentinel, refs):
    return ("\n"
            "extract_program_for buildLabels\n"
            "prove_precondition_decidable_for buildLabels\n"
            "prove_postcondition_decidable_for buildLabels\n"
            "derive_tester_for buildLabels\n\n"
            f"example : buildLabelsTester {names} {sentinel} {refs} = false := by\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen code's shape rather than to its
    # behaviour).
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the frozen
        # backward scan. `out` IS the model, so C1 holds on the whole domain.
        "module": _loopfree("labelsOf names sentinel refs", _PROOF_DIRECT),
        "rationale": (
            "returns the grounded model `labelsOf names sentinel refs` directly "
            "(no loop, no accumulator), so C1 (`out = labelsOf names sentinel "
            "refs`) holds on the whole domain and `loom_solve` closes it "
            "outright. Maximally different executable shape from the frozen "
            "backward scan; if it failed to verify the spec would be over-fit to "
            "the loop's code shape (SPEC-TOO-STRONG). Also the honest "
            "no-ungrounded-echo control: the model is a transparent `def` over "
            "the method's own arguments, so returning it IS doing the "
            "per-reference resolution — any WRONG step fails C1, as the seven "
            "reject rivals demonstrate. Carries the sibling positive control's "
            "intent (a correct reshape of the accumulation) to the extreme of "
            "that axis. Measured: exit 0."),
    },
    {
        "id": "pos-control-inline-resolution",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, both invariants and (almost) the frozen proof;
        # only inlines the per-reference resolution at the use site instead of
        # calling the pure model's helper. Observationally identical everywhere.
        "module": _swap(
            _swap(_BASE, _LOOP_BODY,
                  "      let i := refs[idx - 1]!\n"
                  "      let lbl : Option Name := "
                  "if i = sentinel then none else names[i.toNat]?\n"
                  "      result := lbl :: result\n"
                  "      idx := idx - 1"),
            _PROOF_GOLD,
            "prove_correct buildLabels by\n"
            "  loom_solve\n"
            "  rw [labelsOf_drop_step names sentinel refs idx (by omega) (by omega)]\n"
            "  simp_all [labelOne]"),
        "rationale": (
            "spells the per-reference resolution out at the use site instead of "
            "going through the pure model's single-reference helper — the same "
            "sentinel test and the same table lookup, inlined. The loop, both "
            "invariants and the frozen drop-step lemma are untouched; the proof "
            "gains only the helper's own unfolding, which is exactly the "
            "difference. Observationally identical at every input, so C1 still "
            "holds; a correct reshape of the loop body must verify, else C1 is "
            "SPEC-TOO-STRONG on the shape of the body rather than on its "
            "behaviour. This is the sibling positive control's loop-preserving "
            "half (hoist/inline the per-item resolved entry) on this carrier. "
            "Measured: exit 0."),
    },
    {
        "id": "pos-control-map-correct-step",
        "kind": "soundness",
        "expect": "verify",
        # THE SHAPE-MATCHED CONTROL, and the case that makes every reject verdict
        # in this battery interpretable. It is the reject rivals' EXACT carrier
        # shape — a loop-free `refs.map` under `_PROOF_MAP` — carrying the CORRECT
        # per-reference step. Two things are measured only because it ships:
        #   (a) PROOF ATTRIBUTION. Because this verifies, a rival that fails under
        #       the same body fails for its STEP, not for a script tuned to a loop
        #       it no longer has. (The naive `loom_solve`-only body fails here
        #       too, so it would have been exactly that confound.)
        #   (b) WITNESS DISCRIMINATION. Its extracted tester REDUCES, so every
        #       reject witness can be — and was — refuted against it semantically,
        #       which the stuck-on-gold build cannot show.
        "module": _REFERENCE,
        "rationale": (
            "the loop-free positional map with the CORRECT per-reference step: "
            "mapping the model's own single-reference resolution over the stream "
            "IS the whole-list model (the `hmap` induction in the tactic body), "
            "so C1 holds by that bridge. A faithful correct impl in a different "
            "executable shape must verify, else SPEC-TOO-STRONG. It is also this "
            "battery's INTERPRETIVE CONTROL: it is the seven reject rivals' exact "
            "shape and proof body, so (a) their rejection is attributable to "
            "their step rather than to the proof script — the residual goal names "
            "the step — and (b) their witnesses are refutable against a CORRECT "
            "impl whose tester actually reduces, which is the discrimination the "
            "reduction-stuck gold build does not supply. Both measured with "
            "scripts/lean_verify.sh (exit 0 here; exit 1 and `decide` proved the "
            "proposition false for all seven witnesses). See the CARRIER NOTE."),
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling asserts that the precondition admits a normal,
    # test-shaped input, and establishes it by a self-call whose fractional
    # permissions round-trip. There is no permission surface here, so the probe
    # is re-aimed at the two things that CAN go wrong on this carrier:
    #   (1) the precondition could be CONTRADICTORY at the very input shape the
    #       failing test presents — a table SHORTER than the sentinel's
    #       magnitude, with a sentinel reference in the stream. That is the
    #       configuration the whole instance is about, and a precondition that
    #       (say) demanded every reference be a valid position would exclude it,
    #       making the spec vacuous exactly where it must bite
    #       (PRECOND-TOO-STRONG). The assert discharges the precondition AT that
    #       input.
    #   (2) the post-image could be DEGENERATE — a spec no impl distinguishes
    #       reads exactly like one every impl meets. The assert pins that the
    #       model genuinely discriminates the two branches (a sentinel reference
    #       yields no label; a real reference yields THE ENTRY AT ITS OWN
    #       POSITION, which a two-entry table makes observable).
    # The surrounding impl is kept VERBATIM so the method's own obligation still
    # discharges through the frozen proof; the tactic body gains only a `decide`
    # arm for the assert goal (the body is elided from the spec view). The assert
    # is live, not decoration: a false claim at the same point leaves an unsolved
    # goal.
    # =====================================================================
    {
        "id": "admiss-short-table",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `adm (\n"
                  "      (∀ i ∈ ([-2] : List Int), i ≠ (-2 : Int)\n"
                  "          → (0 ≤ i ∧ i.toNat < ([] : List Name).length))\n"
                  "        ∧ labelsOf [] (-2) [-2] = [none]\n"
                  "        ∧ (∀ i ∈ ([0, -2, -2] : List Int), i ≠ (-2 : Int)\n"
                  "            → (0 ≤ i ∧ i.toNat < ([0] : List Name).length))\n"
                  "        ∧ labelsOf [0] (-2) [0, -2, -2] = [some 0, none, none]\n"
                  "        ∧ labelsOf [0, 1] (-2) [1, -2, -2] = [some 1, none, none]))\n"),
            _PROOF_GOLD,
            "prove_correct buildLabels by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [labelsOf_drop_step names sentinel refs idx "
            "(by omega) (by omega)]\n"
            "       simp_all)"),
        "rationale": (
            "the precondition ADMITS the input shape the failing test presents, "
            "and the post-image is NON-DEGENERATE there. Two claims, both "
            "discharged by a live in-region assert. (1) ADMISSIBILITY PROPER: at "
            "an EMPTY table with a sentinel reference the precondition holds "
            "vacuously (the sentinel carries no position obligation) and the "
            "model still delivers a full-length answer — `labelsOf [] (-2) [-2] "
            "= [none]`. A precondition that demanded every reference be a valid "
            "position would make this input inadmissible and the spec vacuous "
            "exactly where the instance bites (PRECOND-TOO-STRONG); it does not. "
            "The one-entry table with two sentinel references — the failing "
            "test's own shape — is admitted the same way. (2) NON-DEGENERACY: "
            "`labelsOf [0, 1] (-2) [1, -2, -2] = [some 1, none, none]` pins that "
            "the model discriminates the two branches AND resolves a real "
            "reference to the entry at ITS OWN position (a two-entry table makes "
            "the difference observable), so C1 is not a claim every impl meets. "
            "The impl is kept verbatim so C1 itself still verifies through the "
            "frozen proof. Re-aims the sibling's self-call admissibility probe, "
            "whose fractional-permission round-trip has no analogue here. "
            "Measured: exit 0."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is loop-free so
    # its extracted tester `decide`s (see the CARRIER NOTE), and each carries
    # `_PROOF_MAP`, which provably closes C1 for the CORRECT step of the same
    # shape (see the PROOF-SHAPE CONTROL).
    #
    # THE FAILING TEST, abstractly. It builds several trees and compares the
    # whole rendered report against an expected string. Two of its assertions
    # ground every refinement below: one presents a SINGLE-entry name table (the
    # configuration in the issue), and one presents a TWO-entry table where the
    # split refers to the SECOND entry — so both "the table is shorter than the
    # sentinel's magnitude" and "a label must be the entry at its own position"
    # are observable, and a rival wrong on either renders a report that differs
    # from the expected string.
    # =====================================================================
    {
        "id": "weak-index-every-reference",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-IMAGE BEHAVIOUR. Drop the sentinel guard entirely: resolve EVERY
        # reference by indexing the table, including a sentinel one. Correct on
        # every non-sentinel reference — i.e. on the whole domain that contains no
        # sentinel — and wrong on every sentinel reference.
        "module": _loopfree("refs.map (fun i => names[i.toNat]?)"),
        "refinement": (
            "this IS the pre-change behaviour, and its faithful real counterpart "
            "is the unpatched code: every item's reference is fed straight into "
            "the name table, including an item whose reference is the sentinel "
            "standing for 'no entry'. The failing test presents a single-entry "
            "table together with items that reference no entry, and the sentinel "
            "is not a valid position in a table that short — so the lookup either "
            "raises (the error the issue reports, which is how the test fails "
            "today) or, on a longer table, silently returns an unrelated entry "
            "and the rendered report differs from the expected string. Either way "
            "it does NOT resolve. This is the exact defect the change corrects, "
            "so a verifying rival here would be the sharpest possible "
            "SPEC-TOO-WEAK."),
        "rationale": (
            "REJECT from C1: the model's per-reference resolution sends a "
            "sentinel reference to `none` WITHOUT indexing, but this rival "
            "indexes unconditionally. Refuted at a ONE-entry table, the reserved "
            "sentinel, and a single sentinel reference (`names = [0]`, `sentinel "
            "= -2`, `refs = [-2]`), where the spec demands `[none]` and the rival "
            "produces a spurious label (the sentinel's coercion to a position "
            "lands inside a table this short). Note the rival has no precondition "
            "to lean on: the `require` places NO position obligation on a "
            "sentinel reference, which is precisely why indexing it is unsound. "
            "This is the only witness at an empty-label expectation and the only "
            "one whose whole stream is sentinel. Ports the sibling's pre-image "
            "attack. Measured: rival exit 0, reference refuted (`decide` proved "
            "the proposition false), frozen loop stuck."),
        "witness": _witness("[0]", "(-2)", "[-2]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-first-table-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard the sentinel CORRECTLY, then resolve every real reference to the
        # FIRST table entry instead of the entry at its own position.
        # Accidentally correct whenever every real reference is 0 — which includes
        # the single-entry configuration the issue reports — and wrong as soon as
        # the table has two entries and an item refers to the second. The
        # sibling's sharpest near-miss, ported.
        "module": _loopfree(
            "refs.map (fun i => if i = sentinel then none else names[0]?)"),
        "refinement": (
            "corresponds to a patch that guards the sentinel correctly but "
            "resolves every real reference to the FIRST table entry rather than "
            "to the entry it names. It is ACCIDENTALLY correct on the "
            "single-entry configuration from the issue (there the first entry IS "
            "the only entry), which is exactly why the spec must pin the EXACT "
            "entry and not merely 'some label'. The failing test does not stop "
            "there: it also renders a tree against a TWO-entry table whose split "
            "refers to the second entry, and this rival labels it with the first "
            "— so the rendered report differs from the expected string and the "
            "test does NOT resolve."),
        "rationale": (
            "REJECT from C1: the model resolves a real reference to the entry AT "
            "ITS OWN POSITION (`names[i.toNat]?`), and this rival returns "
            "`names[0]?` regardless. Refuted at a TWO-entry table with a "
            "reference to the second entry (`names = [0, 1]`, `refs = [1]`), "
            "where the spec demands `[some 1]` and the rival yields `[some 0]`. "
            "The witness also moves `sentinel` OFF the reserved value to 5 and "
            "presents a stream containing NO sentinel at all — the sub-domain "
            "where this rival's error is the only error possible, and a binder "
            "position no other witness occupies (`sentinel` is a free parameter, "
            "so nothing about its magnitude may be assumed). Verifying would be "
            "SPEC-TOO-WEAK on the identity of the entry. Ports the sibling's "
            "wrong-entry rival. Measured: rival exit 0, reference refuted, frozen "
            "loop stuck."),
        "witness": _witness("[0, 1]", "5", "[1]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-sentinel-slots",
        "kind": "uniqueness",
        "expect": "reject",
        # LENGTH. Resolve every real reference correctly, but omit the no-label
        # slots from the result instead of carrying them. Correct on any stream
        # with no sentinel; short by one slot per sentinel otherwise.
        "module": _loopfree(
            f"(refs.filter (fun i => i ≠ sentinel)).map (fun i => {_STEP_CORRECT})"),
        "refinement": (
            "corresponds to a patch that omits the no-label items from the result "
            "rather than giving them a 'no label' placeholder — a filtering "
            "comprehension instead of a guarded one. The result is then SHORTER "
            "than the item stream, and the consumer reads it BY ITEM POSITION: "
            "every item after the first no-label one is labelled with another "
            "item's entry, or read past the end. The failing test's expected "
            "report pins the label of the item that follows a no-label one, so "
            "the render is wrong (or raises) and it does NOT resolve. Correct "
            "only on a stream in which every item has a real reference."),
        "rationale": (
            "REJECT from C1's LENGTH and POSITION content: the model emits one "
            "label per reference IN ORDER (a sentinel contributes `none`, not "
            "nothing), and this rival emits one per NON-sentinel reference. "
            "Refuted at a one-entry table and a mixed stream whose sentinel is "
            "LAST (`names = [0]`, `sentinel = -2`, `refs = [0, -2]`), where the "
            "spec demands the two-slot `[some 0, none]` and the rival returns the "
            "one-slot `[some 0]`. This is the only rival that changes the result "
            "LENGTH and the only witness whose stream mixes a real reference "
            "before a sentinel. Ports the sibling's drop-node/length rival. "
            "Measured: rival exit 0, reference refuted, frozen loop stuck."),
        "witness": _witness("[0]", "(-2)", "[0, -2]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER. Every per-reference decision is right and every slot is present;
        # only the assembly order is wrong. Isolates C1's ORDER content, which
        # every pointwise-wrong rival leaves unattacked.
        "module": _loopfree(f"(refs.map (fun i => {_STEP_CORRECT})).reverse"),
        "refinement": (
            "corresponds to a patch that accumulates the labels in the wrong "
            "direction — each label correctly resolved, the right number of them, "
            "assembled back-to-front. Because the consumer reads the result BY "
            "ITEM POSITION, every item is then labelled with another item's entry "
            "(and a no-label placeholder lands on an item that has a real "
            "reference). The failing test's expected report pins which label "
            "appears on which line, so the render differs and it does NOT "
            "resolve. A pure ORDER break: no per-reference decision is wrong, "
            "which is what makes it the sharpest attack on the positional content "
            "of the contract."),
        "rationale": (
            "REJECT from C1's ORDER content ALONE: C1 pins the resolution of the "
            "method's own stream POSITION-FOR-POSITION, and this rival returns "
            "the reversal. Every per-reference step is the model's own, so "
            "nothing but the order distinguishes it — it is the only rival whose "
            "output is a value the spec itself produces at some OTHER input. "
            "Refuted at a two-entry table with a sentinel FIRST and a real "
            "reference second (`names = [0, 1]`, `sentinel = -2`, `refs = [-2, "
            "1]`), where the spec demands `[none, some 1]` and the rival yields "
            "`[some 1, none]`. The only witness whose stream leads with a "
            "sentinel. Added on top of the sibling set, which attacks only "
            "pointwise resolution: without it a permutation of the stream would "
            "go unattacked. Measured: rival exit 0, reference refuted, frozen "
            "loop stuck."),
        "witness": _witness("[0, 1]", "(-2)", "[-2, 1]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-first-slot-unlabelled",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL DOMAIN. Correct on every slot but the FIRST, which is forced to
        # the no-label placeholder even when its reference is real. The narrowest
        # sub-domain attack in the battery: right on all but one position.
        "module": _loopfree(
            "match refs with\n"
            "      | []      => []\n"
            f"      | _ :: is => none :: is.map (fun i => {_STEP_CORRECT})"),
        "refinement": (
            "corresponds to a patch that special-cases the FIRST item — emitting "
            "the no-label placeholder for it whether or not it has a real "
            "reference — and handles every later item correctly. In the failing "
            "test's trees the first item is the top split and it DOES reference a "
            "real entry, so its name vanishes from the rendered comparison line "
            "while the rest of the report is right; the render differs from the "
            "expected string by exactly that name and it does NOT resolve. "
            "Correct on any stream whose first item has no real reference, which "
            "is why it is a partial-domain break rather than a wholesale one."),
        "rationale": (
            "REJECT from C1 on a ONE-POSITION sub-domain: the model resolves the "
            "reference at position 0 like any other, and this rival forces it to "
            "`none`. Refuted at a two-entry table whose stream leads with a real "
            "reference to the second entry and ends with a sentinel (`names = "
            "[0, 1]`, `sentinel = -2`, `refs = [1, -2]`), where the spec demands "
            "`[some 1, none]` and the rival yields `[none, none]`. Distinct from "
            "weak-reversed-order's point (which leads with the sentinel) because "
            "this rival is only wrong when position 0 carries a REAL reference — "
            "a near-miss that agrees with the spec over the rest of the domain, "
            "so it gets the input that isolates it rather than sharing another "
            "rival's. Ports the sibling's partial-domain root rival. Measured: "
            "rival exit 0, reference refuted, frozen loop stuck."),
        "witness": _witness("[0, 1]", "(-2)", "[1, -2]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-label-is-the-reference",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard the sentinel correctly, then label each real item with its own
        # REFERENCE VALUE instead of looking the entry up in the table. Under the
        # declared bijection (an entry is carried by its slot index) this
        # coincides with the spec on every IDENTITY-shaped table — including every
        # table used by the other six witnesses — and diverges only when the
        # table's content differs from its positions. The rival that forces the
        # battery to vary the CONTENT of `names`, not just its length.
        "module": _loopfree(
            "refs.map (fun i => if i = sentinel then none else some i.toNat)"),
        "refinement": (
            "corresponds to a patch that guards the no-entry case correctly but "
            "renders each item's own numeric reference in place of the entry that "
            "reference names — never consulting the table at all. The failing "
            "test supplies the table explicitly and expects its entries in the "
            "report, so every labelled line would carry a number instead of the "
            "supplied entry and the render differs from the expected string: it "
            "does NOT resolve. It is a genuine near-miss on the modelled carrier, "
            "because a table whose entries sit at their own positions makes the "
            "two answers coincide."),
        "rationale": (
            "REJECT from C1: the model resolves a real reference by LOOKING IT UP "
            "in the table (`names[i.toNat]?`), and this rival returns the "
            "reference itself, never reading `names`. This is the near-miss the "
            "other six witnesses could not expose: on every identity-shaped table "
            "(`[0]`, `[0, 1]` — the tables they use) the two agree at every "
            "position, so it is refuted at a table whose single entry differs "
            "from its position (`names = [7]`, `sentinel = 3`, `refs = [3, 0]`), "
            "where the spec demands `[none, some 7]` and the rival yields `[none, "
            "some 0]`. It is therefore the only witness that varies the CONTENT "
            "of `names` rather than only its length, and it moves `sentinel` to a "
            "third distinct value. Added on top of the sibling set, whose rivals "
            "all reach into the table and so leave 'consult the table at all' "
            "unattacked. Measured: rival exit 0, reference refuted, frozen loop "
            "stuck."),
        "witness": _witness("[7]", "3", "[3, 0]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # The guard, backwards: a sentinel reference is indexed and a real one is
        # given the no-label placeholder. Correct only on the empty stream —
        # included because it is the cheapest possible mis-wiring of the very
        # branch the instance turns on, and because it puts a real reference in
        # the sub-domain where the spec demands a LABEL and the rival gives none
        # (the dual of weak-index-every-reference's error).
        "module": _loopfree(
            "refs.map (fun i => if i ≠ sentinel then none else names[i.toNat]?)"),
        "refinement": (
            "corresponds to a patch whose guard is inverted: the item with no "
            "entry is fed to the table lookup while every item with a real "
            "reference is given the no-label placeholder. On the failing test's "
            "trees that both strips every real name from the rendered report AND "
            "reinstates the very lookup on a no-entry item that the issue reports "
            "as failing, so it does NOT resolve — it is strictly worse than the "
            "unpatched behaviour."),
        "rationale": (
            "REJECT from C1 in the direction NO other rival attacks: the model "
            "must produce a LABEL for a real reference, and this rival produces "
            "`none` there (every other rival that errs on a real reference "
            "produces the WRONG label, not no label). Refuted at a two-entry "
            "table, a stream with no sentinel, and `sentinel` at a fourth "
            "distinct value (`names = [0, 1]`, `sentinel = 7`, `refs = [1]`), "
            "where the spec demands `[some 1]` and the rival yields `[none]`. "
            "Distinct from weak-first-table-entry's point (same table and stream, "
            "different sentinel) and from it in kind: that rival returns a wrong "
            "label, this one returns none, so the two do not fail for the same "
            "reason and do not share a witness. Measured: rival exit 0, reference "
            "refuted, frozen loop stuck."),
        "witness": _witness("[0, 1]", "7", "[1]"),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The sibling battery ships 7 SPEC cases (1 soundness, 1 admissibility, 5
# uniqueness — two of which are its MANDATORY frame-mutation rivals) plus an
# empty AXIOM lane. It contracts ONE function over two READ-ONLY sequence inputs
# carrying fractional heap permissions, with a load-bearing postcondition pinning
# the result to a fully-unfolded deep model plus a separate length clause.
#
# This backend models the SAME single behaviour, so there is NO carrier narrowing
# on the function surface — unusually, the whole sibling surface has a
# counterpart here. Three refinements do change what the cases become:
#   * the reserved out-of-band value is a FREE PARAMETER (`sentinel`) rather than
#     a literal, so it becomes a third input binder the battery must vary (the
#     sibling has nothing to vary there);
#   * the sibling's two clauses (length, and the fold) collapse into ONE
#     `ensures out = labelsOf names sentinel refs`, which pins length, order and
#     both branches at once — so "attack every independent clause" becomes
#     "attack every independent CONTENT of the single clause", which the reject
#     lane does four ways (length, order, sentinel branch, table branch);
#   * there is no heap and no permission system, which is what makes the two
#     mandatory frame-mutation rivals vacuous.
#
#   sibling case                  kind          -> here                        disposition
#   ---------------------------------------------------------------------------------------
#   pos-control-single-prepend    soundness     -> pos-control-direct-model     PORTED (split)
#                                               -> pos-control-inline-resolution PORTED (split)
#   admissibility-self-call       admissibility -> admiss-short-table           RE-AIMED
#   frame-mutation-feat           uniqueness    -> (none)                       VACUOUS
#   frame-mutation-names          uniqueness    -> (none)                       VACUOUS
#   partial-domain-root-none      uniqueness    -> weak-first-slot-unlabelled   PORTED
#   wrong-entry-names0            uniqueness    -> weak-first-table-entry       PORTED
#   drop-first-node-length        uniqueness    -> weak-drop-sentinel-slots     RE-EXPRESSED
#   (no sibling)                  uniqueness    -> weak-index-every-reference   ADDED
#   (no sibling)                  uniqueness    -> weak-reversed-order          ADDED
#   (no sibling)                  uniqueness    -> weak-label-is-the-reference  ADDED
#   (no sibling)                  uniqueness    -> weak-inverted-guard          ADDED
#   (no sibling)                  soundness     -> pos-control-map-correct-step ADDED (control)
#   AXIOM_TESTS (0)               axiom         -> (none)                       N/A
#
# 11 velvet SPEC cases: 3 soundness, 1 admissibility, 7 uniqueness.
#
# PORTED, SPLIT (pos-control-single-prepend -> two positives): the sibling's one
#   correct reshape hoists the per-item resolved entry into a local and prepends
#   once instead of branching twice. On this carrier that axis has two ends worth
#   separating, so it ships as both: pos-control-inline-resolution keeps the loop,
#   both invariants and the frozen drop-step lemma and only inlines the
#   per-reference resolution (the sibling's edit, near-verbatim in spirit), and
#   pos-control-direct-model takes the same axis to its extreme by returning the
#   grounded model with no loop at all. Two ends of one axis beat one midpoint.
# RE-AIMED (admissibility-self-call -> admiss-short-table): the sibling calls
#   itself on its own in-domain parameters to show the fractional-permission
#   precondition round-trips. This backend has no permission surface and no
#   aliasing, so the self-call would be a no-op probe. The residual admissibility
#   risks here are (a) a precondition contradictory at the instance's own input
#   shape — a table SHORTER than the sentinel's magnitude — and (b) a degenerate
#   post-image. The case discharges a live in-region assert covering both, at
#   fully concrete inputs, keeping the frozen impl verbatim so C1 still verifies.
# PORTED (partial-domain-root-none -> weak-first-slot-unlabelled; wrong-entry-
#   names0 -> weak-first-table-entry): both carry across intact, including their
#   refinement arguments. The sibling's "emit the leaf placeholder at the root
#   even though it is an internal node" becomes "force position 0 to the no-label
#   placeholder even when its reference is real"; the sibling's "resolve every
#   internal node to the first table entry" becomes the same on this carrier. The
#   second keeps the sibling's key observation — that it is ACCIDENTALLY correct
#   on the single-entry configuration from the issue, which is exactly why the
#   contract must pin the EXACT entry — and now backs it with a machine-checked
#   witness on a two-entry table.
# RE-EXPRESSED (drop-first-node-length -> weak-drop-sentinel-slots): the sibling
#   drops one specific slot to make the result short, and is rejected by its
#   separate length clause. There is no separate length clause here (C1 subsumes
#   it), and a more faithful rival is available: omit the NO-LABEL slots instead
#   of placeholding them, i.e. filter rather than guard. Same defect the sibling
#   probes (a result shorter than the item stream, read by position, so every
#   later item is mislabelled) reached through the branch this instance actually
#   turns on.
# ADDED (weak-index-every-reference): the sibling has no pre-image rival in its
#   SPEC lane. Here it is the single most important reject case — it IS the
#   behaviour the change corrects (index every reference, including the reserved
#   one, against a table that need not be long enough), and the frozen
#   `Solution_prepatch.lean` is the same impl. Its rejection is what the
#   `require`'s deliberate asymmetry exists to force.
# ADDED (weak-reversed-order, weak-label-is-the-reference, weak-inverted-guard):
#   coverage the sibling set leaves open. All five sibling-derived rivals err
#   POINTWISE while consulting the table, so (a) a permutation of the stream, (b)
#   not consulting the table at all, and (c) erring in the direction of TOO FEW
#   labels rather than wrong ones were unattacked. weak-label-is-the-reference is
#   the sharpest of the three: under the declared bijection (an entry is carried
#   by its slot index) it AGREES with the spec at every position of every
#   identity-shaped table, so it is refutable only at a table whose content
#   differs from its positions — which is what forces this battery to vary the
#   CONTENT of `names` and not merely its length.
# ADDED (pos-control-map-correct-step): the interpretive control, and the
#   witness_reference. Without it two things this battery claims would be
#   unmeasured. (1) PROOF ATTRIBUTION: a reject rival's proof body must not be a
#   script that fails for a correct impl of the same shape. Measured — the naive
#   `loom_solve`-only body fails IDENTICALLY on a `refs.map` with the CORRECT
#   step, so it would have been exactly that confound; `_PROOF_MAP` verifies
#   there, so a rival's failure under it is its step's. (2) WITNESS
#   DISCRIMINATION: the frozen tester is reduction-stuck, so the gold-side build
#   discriminates nothing (see the CARRIER NOTE); every witness is instead
#   refuted semantically against this impl, which the gate enforces via
#   `witness_reference`.
# VACUOUS (frame-mutation-feat, frame-mutation-names): the sibling's TWO MANDATORY
#   frame-mutation rivals keep the gold value flow verbatim and then write back
#   into a read-only sequence input granted only at a fractional heap permission;
#   they must be rejected by the PERMISSION SYSTEM, not by a value mismatch — the
#   sibling calls this its "#1 attack". Lean and Velvet are referentially
#   transparent: `names`, `sentinel` and `refs` are immutable values declared
#   read-only (no input is `mut` — only the loop-local `result`/`idx` are), there
#   is no heap, no aliasing, no `Old` and no fractional permission. There is no
#   read-only input to overwrite and no frame clause to violate. NOT ported and no
#   substitute fabricated: a rival that assigned to a parameter would be refused
#   at ELABORATION as a binder error with no spec content whatever, so there would
#   be nothing for a witness to state and the rejection would attribute nothing to
#   the postcondition. The class is genuinely absent on this carrier; nothing is
#   claimed dropped.
# N/A (AXIOM_TESTS): the sibling ships an EMPTY axiom lane for the same reason
#   this bundle does — no contract-only callee there, no `axiom` and no deep-model
#   reference here (mapping.md §3: the whole computation is concrete list
#   arithmetic over the inputs, so G-AX returns `skip`). Nothing to drop and
#   nothing to port; the G-PBT gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``idx``). A rival that loops without
#   a measure is refused outright (``Decreasing annotations are required in
#   total correctness semantics``), and a rival that supplies a CONSTANT
#   measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# CLAUSE / BINDER / POINT COVERAGE. ONE `ensures` clause, C1
#   (`out = labelsOf names sentinel refs`), DEFENDED by all three positives and
#   the admissibility case, and ATTACKED by all seven rivals — but C1 bundles four
#   independent contents, and each is attacked on its own:
#     * the SENTINEL branch (a sentinel resolves to no label, without indexing):
#       weak-index-every-reference, weak-inverted-guard
#     * the TABLE branch (a real reference resolves to the entry AT ITS OWN
#       POSITION): weak-first-table-entry, weak-label-is-the-reference,
#       weak-inverted-guard, weak-first-slot-unlabelled
#     * LENGTH (one label per reference): weak-drop-sentinel-slots
#     * ORDER (position-for-position): weak-reversed-order
#   The `require` is exercised as a live constraint by every witness (the tester
#   returns `true` when the precondition fails, so a `= false` claim certifies the
#   input is IN the precondition) and probed directly by admiss-short-table.
#   THREE binders across SEVEN distinct input points (pts = 7):
#     * weak-index-every-reference   names [0]      sentinel -2  refs [-2]
#     * weak-first-table-entry       names [0, 1]   sentinel  5  refs [1]
#     * weak-drop-sentinel-slots     names [0]      sentinel -2  refs [0, -2]
#     * weak-reversed-order          names [0, 1]   sentinel -2  refs [-2, 1]
#     * weak-first-slot-unlabelled   names [0, 1]   sentinel -2  refs [1, -2]
#     * weak-label-is-the-reference  names [7]      sentinel  3  refs [3, 0]
#     * weak-inverted-guard          names [0, 1]   sentinel  7  refs [1]
#   No binder is pinned: `names` ranges over lengths {1, 2} AND over content
#   {identity-shaped, non-identity} — the last being what
#   weak-label-is-the-reference exists to force, since a battery whose every table
#   is identity-shaped cannot tell "look the entry up" from "return the
#   reference"; `sentinel` ranges over FOUR values {-2, 3, 5, 7}, so nothing about
#   its magnitude is assumed (it is a free parameter of the spec, and a battery
#   that pinned it at the reserved value would never notice an impl that hardcoded
#   one); `refs` ranges over lengths {1, 2}, over sentinel-first / sentinel-last /
#   sentinel-only / sentinel-absent, and over which positions carry real
#   references. admiss-short-table additionally drives `names` to the EMPTY table
#   and `refs` to length 3.
#   MEANINGFULNESS (not just distinctness): at each of the seven points the spec's
#   own answer differs from the rival's, computed value-for-value — [none] vs a
#   spurious label; [some 1] vs [some 0]; [some 0, none] vs [some 0]; [none, some
#   1] vs [some 1, none]; [some 1, none] vs [none, none]; [none, some 7] vs [none,
#   some 0]; [some 1] vs [none]. No two are two spellings of one discrimination:
#   they split by which branch is exercised, by table length, by table CONTENT, by
#   stream length, by sentinel position within the stream, by sentinel magnitude,
#   and (the fourth) by ORDER alone. Two rivals share a table and a stream
#   (weak-first-table-entry and weak-inverted-guard, `[0, 1]` / `[1]`) but not a
#   sentinel and not a failure mode — one returns the wrong label where the spec
#   demands a label, the other returns none — so neither claims a sub-domain the
#   other's witness demonstrates.
#
# WITNESS MECHANICS: the post-image is fully TRANSPARENT (`labelsOf`/`labelOne`
#   are concrete `def`s; the axioms region declares no opaque leaf), so the tester
#   + `decide` path is LIVE and no witness needs to condition on the carrier —
#   every one states its refutation at concrete literals, so no witness binds a
#   hypothesis and the gate's consistency probe is not reached. Each rival is
#   loop-free so its extracted `buildLabelsTester` `decide`s at the literals,
#   while the frozen `while`-loop tester stays STUCK. All seven checked with
#   scripts/lean_verify.sh: rival exit 0; frozen exit 1.
#   BUT THE FROZEN-SIDE FAILURE IS NOT THE DISCRIMINATOR — it is reduction-stuck
#   ("did not reduce to `isTrue` or `isFalse`"), which a tautology would also
#   produce. The discrimination is measured against pos-control-map-correct-step
#   instead: a CORRECT impl in the rivals' own shape, whose tester DOES reduce,
#   where each witness is refuted SEMANTICALLY (`decide` proved the proposition
#   false, exit 1 for all seven). That impl is named as every reject case's
#   `witness_reference`, so the gate re-derives this rather than trusting it.
AXIOM_TESTS = []
