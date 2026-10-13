"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5262 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region, and — for the admissibility case — the ``prove_correct``
tactic body, both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct textStreamMode`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
``witness_reference`` — see the CARRIER NOTE for why the frozen solution cannot
serve as that subject here).

DEFENDED SURFACE (one contracted method, ``textStreamMode``):

  textStreamMode (rawMode : List Char) return (out : List Char)
    ensures out = stripped rawMode                          <-- LOAD-BEARING

A text wrapper around a byte stream must present a descriptor that does not
advertise the binary marker code point (``'b'``) even when the wrapped byte
stream's own descriptor does. ``stripped`` is the fully-unfolded per-code-point
fold: each ``'b'`` contributes nothing, every other code point is kept IN ORDER.
There is NO ``require`` clause and ``rawMode`` is a free, read-only immutable
value, so the admitted domain is total: the equality must hold for EVERY
descriptor. The one top-level clause bundles two guarantees over the single
binder ``rawMode``:
  (a) DELETION — every ``'b'`` code point is removed, wherever it sits; and
  (b) PRESERVATION — every non-``'b'`` code point survives, in its original
      order and position.

GROUNDED, NOT AN ORACLE ECHO. ``stripped`` is a concrete ``def`` spelled out in
the ``pure`` region as a total front-recursive function of the method's own
argument; the ``axioms`` region declares nothing. There is no opaque answer key
to echo — the cheapest honest impl IS the real deletion — so the
ungrounded-oracle-echo class is N/A and the positive control is a
local-variable/loop reshape that stays correct.

CARRIER NOTE — why every reject case names a ``witness_reference`` (measured).
The witness reaches the contract through Velvet's tester machinery
(``textStreamModeTester rawMode = false`` says the extracted program's result
violates the postcondition at that concrete descriptor). Against a LOOP-FREE
extracted program that is decidable and ``decide`` closes it. Against the FROZEN
impl it is not: the backward ``while`` loop's fixpoint elaborates through
``Classical.choice`` under ``loom.semantics.choice "demonic"``, which the kernel
cannot unfold, so ``decide`` is stuck for EVERY claim about it, true or false.
Measured on all five witnesses below, the frozen-side build fails with

    did not reduce to `isTrue` or `isFalse`.
    ... reduction got stuck at the `Decidable` instance
      match textStreamModeTester ['r', 'b', '+'], false with ...

so the frozen-side exit code carries NO information and a witness refuted only
against it would attest to a refutation never performed (the gate reports this as
``witness-undecided``; an earlier revision of this battery recorded exactly that
on four cases). The repair is the documented one: every reject case names
``_REF_DIRECT`` as its ``witness_reference`` — a loop-free impl of the SAME
frozen spec which VERIFIES (measured, exit 0) and whose tester DOES reduce.
There ``decide`` refutes each witness SEMANTICALLY:

    error: Tactic `decide` proved that the proposition
      textStreamModeTester ['r', 'b', '+'] = false
    is false

(exit 1, all five). So each witness holds of its rival and provably FAILS of a
correct impl at the same input on the same carrier shape — the discrimination the
stuck-on-gold build cannot supply. ``_REF_DIRECT`` also ships as an
``expect="verify"`` case (``pos-control-direct-model``), so the battery itself
records that loop-freeness is not what any rival is being rejected for.

PROOF-SHAPE CONTROL — why each rejection is attributable to the SPEC, not to a
tactic mismatch. Every reject rival is loop-free, so the frozen script's
``rw [stripped_drop_step rawMode i ...]`` cannot even elaborate (the loop
variable ``i`` is gone: ``Unknown identifier `i```) — that failure mode is about
the script, not the spec. So each rival instead carries the BARE ``loom_solve``
body, which is precisely the script that CLOSES the correct loop-free impl
``_REF_DIRECT`` (exit 0, shipped as ``pos-control-direct-model``). Under that
same body every rival still fails with ``unsolved goals`` on the ``ensures``
equality (measured, all five). The confound is therefore controlled: the script
is known-sufficient for a correct impl of this shape, so the residual goal is
the postcondition itself.

BINDER / DELETION-POSITION COVERAGE. ``rawMode`` is the sole binder of the spec
predicate. The five reject witnesses probe FIVE distinct descriptors, moving the
mishandled code point across every boundary the clause must handle: an INTERIOR
marker (``['r','b','+']``), a TRAILING marker (``['r','b']``), a LEADING marker
(``['b','r']``), a lone marker as the HEAD of a one-element descriptor
(``['b']``), and a marker-FREE descriptor (``['+']``, a pure preservation point).
No two rivals share a witness point, and each point is one where the OTHER
rivals are largely correct — see the separation table in the footer. A rival that
mishandled deletion at only one position, or that over-deleted, cannot pass every
witness.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling attacks a
    read-only input held at a fractional heap permission by WRITING back into
    it. Lean and Velvet are referentially transparent: every parameter is an
    immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to overwrite and no
    substitute probe to build. Reported as vacuous, not fabricated.
  * PARTIAL-DOMAIN — APPLIES, and is the bulk of this battery. The frozen
    obligation is the FULL equality ``out = stripped rawMode``, which pins BOTH
    halves, so a rival is a genuine reject iff it diverges from that equality on
    some descriptor.
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
  * UNGROUNDED-ORACLE ECHO — N/A (see above): the post-image is a total,
    fully-unfolded function of the single input binder.

REFINEMENT HONESTY — two rivals are shipped with a NARROWED refinement claim.
The F2P assertion is a single containment check on the presented descriptor, and
the capture machinery produces one descriptor (marker at an INTERIOR position).
Three rivals leave that marker in place, so their faithful counterparts fail the
F2P outright. Two others (``weak-over-delete-plus``, ``weak-keep-head-verbatim``)
would, on that one descriptor, produce a marker-free result and so would PASS the
F2P assertion. They are still real rejects — they diverge from the frozen
``ensures`` observably — but they are NOT verify-does-not-imply-resolve breaks,
and each says so in its own ``refinement`` rather than claiming a
non-resolution it does not have. Keeping them is what gives the PRESERVATION half
and the head position machine-checked negative controls; mislabelling them would
be the corrupt artifact. See the footer for the full accounting.

AXIOM lane: the ``axioms`` region declares no ``axiom`` and the changed operation
is modeled DEEPLY as ``stripped``/``stripStep`` (an A-reference validated ==
the real callee by G-AX, out of scope for this gate). ``AXIOM_TESTS`` is dropped;
the gate ignores it regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5262"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region: the ENTIRE `-- impl-start` .. `-- impl-end` block
# ---- (the backward-fold loop). It lies wholly inside the one impl region and is
# ---- unique in Solution.lean; both facts are asserted at load by _swap. Each
# ---- variant re-emits the `-- impl-start` / `-- impl-end` markers so the region
# ---- boundary is preserved exactly. ----------------------------------------
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    let mut result : List Char := []\n"
    "    let mut i := rawMode.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ rawMode.length\n"
    "      invariant result = stripped (rawMode.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := rawMode[i - 1]!\n"
    "      result := stripStep c ++ result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)
assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- The frozen proof body (the `prove_correct` tactic script), tuned to the
# ---- frozen loop shape: it rewrites with the drop-step lemma at the loop
# ---- variable `i`. Elided from the consumer spec view. Any loop-FREE variant
# ---- must retune it — `i` does not exist there — which is why the reject rivals
# ---- and the loop-free positive carry `_PROOF_BARE` instead. The
# ---- `prove_correct textStreamMode` HEADER and the obligation statement are
# ---- never touched, so same_spec and the surviving-obligation rule both hold.
_GOLD_PROOF = (
    "prove_correct textStreamMode by\n"
    "  loom_solve\n"
    "  rw [stripped_drop_step rawMode i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"

# The bare script. Measured: it CLOSES the correct loop-free impl `_REF_DIRECT`
# (exit 0) and leaves `unsolved goals` on the `ensures` equality for every reject
# rival below. That asymmetry is the proof-shape control described in the
# docstring — the script is known-sufficient for a correct impl of the rivals'
# own shape, so a rival's residual goal is the postcondition, not the tactic.
_PROOF_BARE = "prove_correct textStreamMode by\n  loom_solve"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block.
    `body` is the text BETWEEN the markers; we wrap it back in the exact
    `-- impl-start` / `-- impl-end` markers so the region boundary is intact."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_BASE, _GOLD_IMPL, block)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_swap(_BASE, _GOLD_IMPL, block), _GOLD_PROOF, proof)


def _loopfree(body):
    """A loop-free variant under the bare script (see `_PROOF_BARE`)."""
    return _impl_proof(body, _PROOF_BARE)


# ---- THE WITNESS REFERENCE. A loop-free impl of the frozen spec that returns
# ---- the grounded post-image directly. It VERIFIES against the frozen spec
# ---- (measured, exit 0, under the bare script) and its extracted tester
# ---- REDUCES, so `decide` gives a semantic verdict there instead of getting
# ---- stuck on the frozen loop's `Classical.choice`. Every reject case is
# ---- refuted against THIS rather than against gold; the gate independently
# ---- re-checks that it shares the frozen spec and verifies before using it.
# ---- Shipped as an `expect="verify"` case too, so the battery records that
# ---- loop-freeness is not what any rival is rejected for.
_REF_DIRECT = _loopfree("    return (stripped rawMode)")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `textStreamModeTester rawMode = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete descriptor.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. `List Char` has DecidableEq, so the
# ---- postcondition is decidable and every witness closes by `decide` against a
# ---- loop-free program. No witness binds a hypothesis (every carrier value here
# ---- is a transparent literal), so no consistency probe is needed and none of
# ---- the `witness-inconsistent` risk applies.
_TESTER = ("extract_program_for textStreamMode\n"
           "prove_precondition_decidable_for textStreamMode\n"
           "prove_postcondition_decidable_for textStreamMode\n"
           "derive_tester_for textStreamMode\n\n")


def _witness(descriptor):
    return (_TESTER + "example : textStreamModeTester " + descriptor
            + " = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # (1) POSITIVE CONTROL (soundness) — structurally different but CORRECT.
    # Keeps the BACKWARD loop direction (so the front-recursive helper is
    # satisfied by the same single unfold per step, no fold-split lemma) and
    # EVERY gold invariant, renaming only the local accumulator (result -> acc)
    # and the per-step code point (c -> ch). It computes the identical deletion
    # on every descriptor and adds no new proof obligation, so the frozen
    # `loom_solve; rw [stripped_drop_step ...]; simp_all` (which references the
    # preserved loop variable `i` and the input `rawMode`) still closes it
    # unchanged. If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-rename-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let mut acc : List Char := []\n"
            "    let mut i := rawMode.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ rawMode.length\n"
            "      invariant acc = stripped (rawMode.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let ch := rawMode[i - 1]!\n"
            "      acc := stripStep ch ++ acc\n"
            "      i := i - 1\n"
            "    return acc\n"),
        "rationale": "a correct reshape with renamed locals (result->acc, c->ch) "
                     "that keeps the backward direction and EVERY gold invariant "
                     "computes the identical per-code-point deletion on every "
                     "descriptor and adds no new obligation, so the single "
                     "equality clause `out = stripped rawMode` still discharges "
                     "under the frozen proof (which is keyed on the preserved "
                     "loop variable `i` and input `rawMode`). Else SPEC-TOO-STRONG "
                     "on impl shape. Doubles as the honest cheapest positive "
                     "control: `stripped` is grounded, so the cheapest correct "
                     "impl IS the real deletion — there is no wrong echo.",
    },

    # =====================================================================
    # (2) POSITIVE CONTROL / WITNESS REFERENCE (soundness). The loop-free impl
    # that returns the grounded post-image directly. Two jobs:
    #   (a) SOUNDNESS — a correct impl of a completely different SHAPE (no loop,
    #       no invariant, no drop-step rewrite) must still verify, else the spec
    #       is SPEC-TOO-STRONG on the shape of the impl. It closes under the bare
    #       `loom_solve` (measured, exit 0).
    #   (b) It is `_REF_DIRECT`, the `witness_reference` every reject case is
    #       refuted against. Shipping it as a case in its own right is what
    #       records that loop-freeness is NOT what any rival is rejected for:
    #       this impl is loop-free too, and it VERIFIES.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        "module": _REF_DIRECT,
        "rationale": "a correct impl of a structurally DIFFERENT shape — loop-free, "
                     "returning the grounded post-image `stripped rawMode` directly "
                     "instead of accumulating it backward — must verify, else the "
                     "spec is SPEC-TOO-STRONG on impl shape. This is legitimate and "
                     "not an oracle echo precisely because `stripped` is a total "
                     "concrete `def` over the method's own argument, not an opaque "
                     "answer key (the `axioms` region declares nothing): returning "
                     "it IS performing the deletion. Also serves as the "
                     "`witness_reference` for every reject case, so its presence "
                     "here records that loop-freeness is not the ground of any "
                     "rejection — this impl is loop-free and verifies.",
    },

    # =====================================================================
    # (3) ADMISSIBILITY — no `require` clause exists, so the usual "a normal
    # input satisfies the precondition" probe is vacuous. Re-aimed at the
    # residual admissibility risk on a total domain: that the post-image is
    # DEGENERATE / unsatisfiable at the decisive point. The impl is kept
    # verbatim so the method's own obligation still discharges under the frozen
    # loop proof; an in-region `assert` pins the post-image at the F2P descriptor
    # — the one the capture machinery produces, with the marker at an INTERIOR
    # position — demanding the marker be DELETED while both non-marker code
    # points are PRESERVED in order (`stripped ['r','b','+'] = ['r','+']`). The
    # assert is live, not decoration: a false claim about the same point leaves
    # an unsolved goal. The proof is retuned only to discharge the extra
    # decidable side goal `loom_solve` leaves for the assert.
    # =====================================================================
    {
        "id": "admiss-f2p-corner-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert "
            "(stripped ['r', 'b', '+'] = ['r', '+']))\n"
            "    let mut result : List Char := []\n"
            "    let mut i := rawMode.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ rawMode.length\n"
            "      invariant result = stripped (rawMode.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := rawMode[i - 1]!\n"
            "      result := stripStep c ++ result\n"
            "      i := i - 1\n"
            "    return result\n",
            "prove_correct textStreamMode by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [stripped_drop_step rawMode i (by omega) (by omega)]; "
            "simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the F2P "
                     "corner: on the descriptor the capture machinery produces "
                     "(marker at an interior position) it must DELETE the marker "
                     "and PRESERVE both surrounding code points in order — "
                     "`stripped ['r','b','+'] = ['r','+']`, not `['r','+']` "
                     "collapsed or the marker retained. The in-region assert must "
                     "discharge (else the obligation is degenerate at the "
                     "interesting point); the loop impl is verbatim so the "
                     "equality clause still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec. Each is
    # loop-free (so its witness reduces and `decide` gives a semantic verdict),
    # carries the bare `loom_solve` script that PROVABLY closes the correct
    # loop-free impl (the proof-shape control), and names `_REF_DIRECT` as its
    # `witness_reference` (the CARRIER NOTE: the frozen loop decides nothing).
    # Each is refuted at a DISTINCT descriptor at which the other rivals are
    # largely correct — see the separation table in the footer.
    # =====================================================================

    # (4) DELETE-NOTHING — the descriptor is presented UNCHANGED (the pre-image
    # behaviour: the wrapper delegates the wrapped stream's descriptor verbatim).
    # Correct only on descriptors that already carry no marker; wrong on every
    # descriptor containing one — including the F2P descriptor. Refuted at an
    # INTERIOR marker.
    {
        "id": "weak-delete-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _loopfree("    return rawMode"),
        "refinement": "the faithful counterpart presents the wrapped stream's "
                      "descriptor unchanged (no deletion), so the presented "
                      "descriptor still carries the binary marker. The failing "
                      "observation — the marker is ABSENT from the presented "
                      "descriptor — still sees it present on the capture-produced "
                      "descriptor (marker interior), so it would NOT resolve. A "
                      "verifying rival here would be a true "
                      "verify-does-not-imply-resolve break. (This is exactly the "
                      "pre-image behaviour the fix corrects.)",
        "rationale": "REJECT from the DELETION half of `out = stripped rawMode`: "
                     "at a descriptor carrying a marker the post-image demands it "
                     "removed, but the impl keeps every code point. Refuted at "
                     "`['r','b','+']` — an INTERIOR marker, the F2P position, and "
                     "the only witness point at which the head-preserving rival "
                     "(8) is correct.",
        "witness": _witness("['r', 'b', '+']"),
        "witness_reference": _REF_DIRECT,
    },

    # (5) DELETE-LEADING-ONLY — remove only a LEADING run of the marker, keep the
    # rest of the descriptor verbatim. Correct on descriptors whose only markers
    # are leading; WRONG whenever a marker sits anywhere else. A genuine
    # partial-domain rival distinct from delete-nothing: it agrees with the frozen
    # solution on a leading-marker descriptor, so it must be refuted at a
    # NON-leading (trailing) marker to separate it. Its faithful counterpart still
    # leaves the F2P descriptor's interior marker in place.
    {
        "id": "weak-delete-leading-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _loopfree("    return (rawMode.dropWhile (· = 'b'))"),
        "refinement": "a counterpart that strips only a leading marker run leaves "
                      "every non-leading marker in place, so the presented "
                      "descriptor still advertises the marker whenever it is not "
                      "at the front — including the capture-produced descriptor, "
                      "whose marker is interior. The failing observation still "
                      "sees a marker present, so it would NOT resolve; a verifying "
                      "rival here would be a true verify-does-not-imply-resolve "
                      "break.",
        "rationale": "REJECT from the DELETION half: at `['r','b']` (a TRAILING "
                     "marker) the post-image demands `['r']` but the impl, finding "
                     "no leading marker, returns `['r','b']`. Refuted at "
                     "`['r','b']` — a NON-leading marker, chosen because on a "
                     "purely-leading marker this rival AGREES with the frozen "
                     "solution, so its leading-only nature is machine-checked "
                     "rather than shared with (4). Rivals (6), (7) and (8) are all "
                     "CORRECT at this point, so it separates this rival from each.",
        "witness": _witness("['r', 'b']"),
        "witness_reference": _REF_DIRECT,
    },

    # (6) DELETE-TRAILING-ONLY — remove only a TRAILING run of the marker, keep
    # the rest verbatim. The mirror-image partial-domain rival of (5): correct on
    # descriptors whose only markers are trailing, WRONG whenever a marker sits
    # elsewhere. Refuted at a LEADING marker — the position at which
    # delete-leading-only would be correct — so the two mirror rivals never share
    # a witness and the marker position is varied to a third boundary.
    {
        "id": "weak-delete-trailing-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _loopfree(
            "    return ((rawMode.reverse.dropWhile (· = 'b')).reverse)"),
        "refinement": "a counterpart that strips only a trailing marker run leaves "
                      "every non-trailing marker in place, so the presented "
                      "descriptor still advertises the marker whenever it is not at "
                      "the end — including the capture-produced descriptor. The "
                      "failing observation still sees a marker present, so it would "
                      "NOT resolve; a verifying rival here would be a true "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from the DELETION half: at `['b','r']` (a LEADING "
                     "marker) the post-image demands `['r']` but the impl, finding "
                     "no trailing marker, returns `['b','r']`. Refuted at "
                     "`['b','r']` — the mirror of (5)'s witness; at this leading "
                     "marker rivals (5) and (7) are both CORRECT, so the mirror "
                     "pair is separated and the marker position is moved to a "
                     "third boundary (leading).",
        "witness": _witness("['b', 'r']"),
        "witness_reference": _REF_DIRECT,
    },

    # =====================================================================
    # (7) OVER-DELETE-PLUS — deletes the marker AND also drops a NON-marker
    # code point ('+'). This is the ONLY rival attacking the PRESERVATION half
    # of `out = stripped rawMode` (rivals 4–6 and 8 all attack DELETION; the
    # positive controls and admissibility corner defend preservation only
    # POSITIVELY). Correct on descriptors with no '+', WRONG on every descriptor
    # containing one. Refuted at `['+']`, a PURE preservation point with no
    # marker at all: there the deletion half is trivially met and rivals 4, 5, 6
    # and 8 are ALL correct, so the witness isolates over-deletion exactly.
    #
    # REFINEMENT IS NARROWED, DELIBERATELY. On the one descriptor the capture
    # machinery produces this counterpart yields a marker-free result, so it
    # would PASS the failing observation. It is NOT claimed as a
    # verify-does-not-imply-resolve break — see the `refinement` field, which
    # states that plainly instead of asserting a non-resolution it does not have.
    # It is kept because it is the battery's only negative control on the
    # preservation half of the frozen equality.
    # =====================================================================
    {
        "id": "weak-over-delete-plus",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _loopfree(
            "    return (rawMode.filter (fun c => c ≠ 'b' ∧ c ≠ '+'))"),
        "refinement": "NARROWED CLAIM, stated honestly. A counterpart that also "
                      "strips the non-marker '+' code point drops a code point the "
                      "transformation must PRESERVE, so on any descriptor carrying "
                      "'+' the presented descriptor differs from the required one "
                      "and the reported descriptor loses capability information a "
                      "consumer may read. But on the single descriptor the capture "
                      "machinery produces, this counterpart's result is "
                      "marker-FREE, so it WOULD satisfy the failing observation "
                      "(which is one containment check, not an equality). This case "
                      "is therefore NOT claimed as a "
                      "verify-does-not-imply-resolve break: it is a genuine "
                      "divergence from the frozen `ensures` (the FULL equality, "
                      "which pins preservation as well as deletion) and is kept as "
                      "the only negative control on that half. Claiming a "
                      "non-resolution it does not have would be the corrupt "
                      "artifact; this states the weaker true thing.",
        "rationale": "REJECT from the PRESERVATION half of `out = stripped rawMode`: "
                     "at `['+']` (a pure non-marker descriptor) the post-image demands "
                     "`['+']` but the impl drops '+' and returns `[]`. This is the only "
                     "rival attacking preservation with a negative control; at `['+']` "
                     "the deletion half is trivially satisfied and rivals (4), (5), (6) "
                     "and (8) are ALL correct, so the witness isolates over-deletion "
                     "and pins preservation independently of every deletion witness.",
        "witness": _witness("['+']"),
        "witness_reference": _REF_DIRECT,
    },

    # =====================================================================
    # (8) KEEP-HEAD-VERBATIM — the nagini sibling's ATTACK 3 ported. Delete the
    # marker at every position EXCEPT the HEAD code point, which is passed
    # through verbatim. Correct on every descriptor whose first code point is not
    # the marker; WRONG exactly when the descriptor STARTS with the marker.
    # A NEAR-MISS: it agrees with the frozen solution on strictly more of the
    # domain than rivals 4–6 (it deletes every non-head marker correctly,
    # including the F2P descriptor's interior one), which is why it gets its own
    # witness at the point that isolates the head. Refuted at `['b']` — the
    # one-element descriptor that is nothing BUT a head marker — where rivals
    # (5), (6) and (7) are all correct and only this rival and delete-nothing
    # are wrong. This targets the head of the sequence the front-recursive fold
    # peels FIRST, the position the nagini sibling singled out.
    #
    # REFINEMENT IS NARROWED (same reasoning as (7)): the capture-produced
    # descriptor does not start with the marker, so this counterpart handles it
    # correctly and would pass the failing observation. Stated plainly below.
    # =====================================================================
    {
        "id": "weak-keep-head-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _loopfree(
            "    return (rawMode.take 1 ++ stripped (rawMode.drop 1))"),
        "refinement": "NARROWED CLAIM, stated honestly. A counterpart that passes "
                      "the head code point through verbatim leaves a marker in the "
                      "presented descriptor exactly when the wrapped stream's "
                      "descriptor STARTS with it — the faithful transformation "
                      "removes the marker wherever it sits, including at the front, "
                      "so the two differ on every leading-marker descriptor and a "
                      "consumer inspecting such a descriptor would still see a "
                      "binary advertisement. But the descriptor the capture "
                      "machinery produces does not begin with the marker, so this "
                      "counterpart handles that one correctly and WOULD satisfy the "
                      "failing observation. Not claimed as a "
                      "verify-does-not-imply-resolve break; kept because it is the "
                      "battery's only negative control on the HEAD position, the "
                      "code point the front-recursive fold peels first.",
        "rationale": "REJECT from the DELETION half of `out = stripped rawMode` at the "
                     "HEAD binder position: at `['b']` the post-image demands `[]` but "
                     "the impl returns `['b']`. A NEAR-MISS rival — it agrees with the "
                     "frozen solution on strictly more of the domain than rivals (4)-(6), "
                     "deleting every non-head marker correctly, so it needs its own "
                     "witness at the point that isolates the head rather than sharing "
                     "one. At `['b']` rivals (5), (6) and (7) are ALL correct, so this "
                     "witness demonstrates the sub-domain the rationale claims.",
        "witness": _witness("['b']"),
        "witness_reference": _REF_DIRECT,
    },
]


# ---------------------------------------------------------------------------
# WITNESS SEPARATION TABLE (computed over the carrier, then machine-checked with
# real builds). Rows are the five reject witness points; columns are the five
# rivals; `.` = this rival is CORRECT at this point, `X` = wrong (so the point
# refutes it). Read down a column for the rival's own witness (its single X that
# the manifest uses); read across a row to see how many OTHER rivals that point
# leaves untouched, which is what makes the point discriminating rather than
# generic.
#
#                       (4)nothing (5)lead (6)trail (7)over+ (8)head
#   ['r','b','+']  <-(4)     X         X        X       X       .
#   ['r','b']      <-(5)     X         X        .       .       .
#   ['b','r']      <-(6)     X         .        X       .       X
#   ['+']          <-(7)     .         .        .       X       .
#   ['b']          <-(8)     X         .        .       .       X
#
# No two rivals share a witness point, and each point is one where a majority of
# the other rivals are correct — so every witness demonstrates the specific
# sub-domain its rationale claims. `pts=5` over the single binder `rawMode`,
# moving the mishandled code point across interior / trailing / leading / head /
# marker-free positions.
#
# MEASURED, not argued. Every case below was checked out-of-band with
# `scripts/lean_verify.sh` before hand-off:
#   * `_REF_DIRECT` verifies against the frozen spec under the bare script
#     (exit 0), so it is a valid `witness_reference`.
#   * each witness ELABORATES against its own rival (exit 0, all five).
#   * each witness is REFUTED against `_REF_DIRECT` (exit 1, all five, with
#     ``Tactic `decide` proved that the proposition ... is false`` — a SEMANTIC
#     verdict, not a stuck reduction).
#   * each witness against the FROZEN solution is STUCK (exit 1 with
#     ``did not reduce to `isTrue` or `isFalse``), which is precisely why the
#     reference is needed and why an earlier revision of this battery recorded
#     `witness-undecided` on four cases.
#   * each reject module FAILS to verify under the bare script (`unsolved goals`
#     on the `ensures` equality), while that same script CLOSES the correct
#     loop-free impl — the proof-shape control.
#   * no witness binds a hypothesis, so no consistency probe applies and the
#     `witness-inconsistent` failure mode is structurally out of reach.
#
# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) over `reported_mode`; this
# bundle models the same single purely-functional core (`textStreamMode`) with
# one postcondition `out = stripped rawMode`, so every sibling case that has a
# counterpart lands on that one clause, re-expressed against the `List Char`
# carrier.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-control-rename-reshape     -> pos-control-rename-reshape        PORTED
#   admiss-self-call               -> admiss-f2p-corner-nondegenerate   RE-AIMED
#   frame-mutate-buffer-mode       -> (none)                            VACUOUS
#   weak-identity-keep-marker      -> weak-delete-nothing               PORTED
#   weak-keep-leading-marker       -> weak-keep-head-verbatim           PORTED
#   weak-over-delete-plus          -> weak-over-delete-plus             PORTED
#   + pos-control-direct-model     (added: shape-diverse positive + the
#                                   witness_reference the carrier forces)
#   + weak-delete-leading-only     (added, deletion-position coverage)
#   + weak-delete-trailing-only    (added, deletion-position coverage)
#   AXIOM_TESTS                    -> dropped (G-AX's lane)
#
# RE-AIMED (admissibility): the sibling's admissibility case self-calls
#   reported_mode on the F2P-shaped input to attest the precondition admits it.
#   This bundle has NO `require` clause, so "admits a normal input" is vacuous;
#   the case is re-aimed at proving the post-image is satisfiable and
#   NON-degenerate at the F2P descriptor (marker interior => deleted AND both
#   non-marker code points preserved in order). The in-region assert is
#   discharged symbolically against concrete literals so the retuned proof closes.
#
# VACUOUS (frame-mutation): the sibling's rival WRITES a read-only input held at
#   a fractional heap permission. This backend is referentially transparent, has
#   no heap and no aliasing, and this bundle declares NO `mut` binder — there is
#   no read-only input to overwrite, so no witness could exist and none is
#   fabricated. This is the one class where "vacuous" is the honest word.
#
# PORTED with a re-aimed input (weak-keep-leading-marker -> weak-keep-head-
#   verbatim): the sibling keeps the marker only at the head of the sequence its
#   front-recursive fold peels first. Ported directly; the only change is the
#   refutation point. The sibling argues from a leading-marker descriptor like
#   "brb+"; here the witness is the minimal `['b']`, which isolates the head
#   from every other position and is a point where three of the four other rivals
#   are correct. An earlier revision of this battery DROPPED this case as
#   "redundant with delete-trailing-only at `['b','r']`". That was wrong on the
#   near-miss rule: this rival agrees with gold over strictly MORE of the domain
#   than the delete-* rivals (it handles the F2P descriptor correctly), so
#   refuting it at a point it shares with another rival would have let its
#   rationale claim a sub-domain the manifest never demonstrated. It now carries
#   its own separating witness.
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
# REFINEMENT-CLAIM AUDIT (the correction this revision makes). The failing
#   observation is a single containment check on the presented descriptor, and
#   the capture machinery produces ONE descriptor, whose marker is INTERIOR.
#   Evaluating each rival's faithful counterpart on that descriptor:
#     weak-delete-nothing        -> marker RETAINED -> would NOT resolve  [break]
#     weak-delete-leading-only   -> marker RETAINED -> would NOT resolve  [break]
#     weak-delete-trailing-only  -> marker RETAINED -> would NOT resolve  [break]
#     weak-over-delete-plus      -> marker-free     -> WOULD pass the F2P
#     weak-keep-head-verbatim    -> marker-free     -> WOULD pass the F2P
#   The first three are true verify-does-not-imply-resolve breaks and say so. The
#   last two are NOT, and their `refinement` fields now state that explicitly
#   instead of asserting a non-resolution they do not have. Both are still real
#   rejects — each diverges observably from the frozen `ensures`, which is the
#   FULL equality and pins preservation and the head position as well as interior
#   deletion — and both are kept because they are the only negative controls on
#   those two parts of the clause. A prior revision shipped `weak-over-delete-plus`
#   claiming outright that its counterpart "would not resolve"; that claim does not
#   survive evaluating it against the actual failing observation, and overstating
#   it is exactly the kind of unearned attestation this gate exists to prevent.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   `axiom` (the changed op is modeled deeply as `stripped`/`stripStep`, an
#   A-reference), and the gate ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
