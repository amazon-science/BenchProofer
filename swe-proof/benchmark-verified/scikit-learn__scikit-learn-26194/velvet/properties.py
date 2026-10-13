"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-26194 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the elided
``prove_correct`` tactic body, is changed — both regions the consumer spec view
elides, so ``markers.same_spec`` holds and the ``prove_correct
withLeadingSentinel`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation, checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: elaborates against the rival, FAILS against the frozen solution).

DEFENDED SURFACE (one contracted method):

  withLeadingSentinel (base : List Rat) return (out : List Threshold)
    require base ≠ []
    ensures out = Threshold.top :: finiteSeq base

The method anchors an ordered vector of finite decision thresholds with one
extra LEADING position, so the resulting curve starts at the corner where no
instance is predicted positive. ``base`` are the ordered finite thresholds
computed upstream; ``finiteSeq`` lifts each finite value into the threshold
domain unchanged; ``Threshold.top`` is the sentinel position that lies above
EVERY attainable finite score (modeled as its own constructor, so it is
categorically distinct from any finite ``Threshold.value r``).

The single exact-equality ensures pins the WHOLE output as a total function of
the one input ``base``, with three independent top-level facets:

  * (H) the LEADING position is the sentinel ``Threshold.top`` — not any finite
        value. This is the load-bearing discriminator: a wrong impl that leads
        with a finite value (constructor ``value _ ≠ top``) or omits the lead
        violates it.
  * (L) the LENGTH of ``out`` is ``base.length + 1`` — the tail carries every
        finite threshold, none dropped.
  * (T) the TAIL ``out.tail`` equals ``finiteSeq base`` ELEMENTWISE and IN
        ORDER — a rival that corrupts a value or reorders the tail violates it.

The sole INPUT binder is ``base : List Rat``; the post-image must hold for every
value of it, and the reject witnesses vary it (singletons and multi-element
lists, distinct values) so no facet's dependence on ``base`` goes untested.

ADVERSARIAL READ of the nagini classes (see the footer for the case-by-case
accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling's
    MANDATORY frame-mutation rival keeps the gold body then WRITES back into a
    read-only sequence input carrying only a fractional heap permission
    (``Acc(list_pred(thresholds),1/2)``), and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: every parameter
    is an immutable value, this method declares no ``mut`` binder, there is no
    heap and no aliasing. There is no read-only input to overwrite and no
    permission system to trip, so the class is vacuous. No substitute is
    fabricated.
  * DIVERGENCE / NON-TERMINATION: nothing to port, INAPPLICABLE as a shipped
    reject case, and closed by the verifier rather than vacuous. The nagini sibling
    carries NO ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case (it has 8 SPEC
    cases, none of them a divergence rival), so nothing is dropped in the port. The
    frozen impl here is loop-free, so there is no loop in the frozen body to make
    spin and this bundle ships no divergence rival; but "a diverging impl cannot be
    written at all" is withdrawn, since a rival owns the whole impl region and may
    splice a loop the frozen body does not have. Under this bundle's
    ``loom.semantics.termination "total"`` a postcondition is claimed of ALL runs,
    not only terminating ones, so the verifier demands a decreasing measure on
    every loop AND discharges its descent; the option cannot drift from the file's
    ``open TotalCorrectness DemonicChoice``, because the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` whose body is
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``.
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region is EMPTY; the post-image
    ``Threshold.top :: finiteSeq base`` is built from the method's own input via
    concrete ``def``s (``finiteSeq`` is ``xs.map Threshold.value``) and the
    constructor ``Threshold.top``. There is no opaque answer-key to echo; the
    unique satisfier IS the grounded construction, so the honest controls are
    the cheapest faithful reshapes (the ``pos-*`` cases). The carrier is fully
    TRANSPARENT, so every reject witness is stated at concrete literal inputs
    (no witness in this battery binds anything, so none needs a consistency
    probe) and discharged by ``decide`` / ``decide +kernel`` — no
    conditioning-on-an-opaque-term is needed.
  * PARTIAL-DOMAIN / VALUE — exercised on the tail facets: a rival can lead with
    the correct sentinel yet drop a tail element (L), corrupt every tail value
    (T), corrupt EXACTLY ONE tail value (T, the partial-domain form), perturb the
    tail arithmetically with its shape intact (T), or reorder the tail (T). Each
    is correct on part of the output and wrong on one facet.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is straight-line (no loop) and
the carrier is transparent, so its extracted program reduces fully under
``decide``. Each reject rival carries a machine-checked refutation ``witness`` —
a Velvet tester statement ``withLeadingSentinelTester <base> = false`` at ONE
concrete input, checked in a file whose ``prove_correct`` block has been stripped
so no tactic script can mask the verdict. (``Threshold`` derives ``DecidableEq``
in the frozen ``pure`` region, so ``prove_postcondition_decidable_for`` /
``derive_tester_for`` synthesize the tester with no added instance and no
``axiom`` / ``sorry`` / ``native_decide``.) Both halves were checked out-of-band
with ``scripts/lean_verify.sh``, and RE-CHECKED independently by the audit: every
witness ELABORATES against its rival (exit 0) and FAILS against the frozen
solution (exit 1) with the SEMANTIC message ``Tactic `decide` proved that the
proposition withLeadingSentinelTester <base> = false is false`` — i.e. the tester
returns ``true`` at every probed ``base`` on gold, so gold's failure is a decided
refutation of the concrete claim, not a missing identifier, a type error, an
unfolding failure, a stuck reduction, or a timeout. Each rejection is therefore a
genuine spec refutation, not mechanical tactic breakage.

Note on ``decide`` and ``Rat`` arithmetic (MEASURED, audit-corrected). Plain
``decide`` reduces the tester's ``Decidable`` instance through the elaborator's
whnf and gets STUCK on a ``Rat`` arithmetic redex: on the value-shift rival
(``base.map (· + 1)``) it reports ``did not reduce to `isTrue` or `isFalse` ``
after unfolding ``instDecidableEqRat``. That is a limit of the DEFAULT reduction
mode only, not of the carrier: ``decide +kernel`` evaluates the same instance in
the kernel and closes it (measured — the shift rival's witness elaborates at
exit 0, and the SAME witness fails on the frozen solution with ``decide`` proving
the proposition false). So the arithmetic value facet IS witnessable here and
carries its own rival (``weak-tail-shifted``); the earlier claim that it was
un-witnessable was wrong and is retracted. ``decide +kernel`` adds no assumption
beyond Lean's standard three (``#print axioms`` on the witness reports
``propext, Classical.choice, Quot.sound``) and is not ``native_decide``.
Structural corruptions (wrong leading constructor, dropped / planted / reordered
element) still close under plain ``decide``.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no
deep-model reference; the upstream input carrier (``_binary_clf_curve`` + drop
mask) is run as the real callee by the Docker gates (G-AX / G-CONF), not
axiomatized. Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-26194"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes, the elided `prove_correct`
# tactic body), so the spec view is untouched and same_spec holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    let out : List Threshold := Threshold.top :: finiteSeq base\n"
    "    return out\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct withLeadingSentinel by loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `withLeadingSentinelTester <base> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped. `Threshold` already derives
# ---- `DecidableEq` in the frozen `pure` region, so the tester needs no added
# ---- instance.
_TESTER = (
    "extract_program_for withLeadingSentinel\n"
    "prove_precondition_decidable_for withLeadingSentinel\n"
    "prove_postcondition_decidable_for withLeadingSentinel\n"
    "derive_tester_for withLeadingSentinel\n\n"
)


def _witness(call, tactic="decide"):
    return _TESTER + f"example : {call} = false := by\n  {tactic}\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the output value identical and only
    # reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-tail-bound-first",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the lifted finite tail to a local FIRST, then cons the
        # sentinel onto it. Same output on every input; the reproof stays a
        # `loom_solve` away (the do-block only introduces one extra let).
        "module": _impl_reproved(
            "    let rest : List Threshold := finiteSeq base\n"
            "    let out : List Threshold := Threshold.top :: rest\n"
            "    return out",
            "prove_correct withLeadingSentinel by loom_solve"),
        "rationale": "binding the lifted finite tail to a local before consing "
                     "the sentinel computes the SAME `out = Threshold.top :: "
                     "finiteSeq base` on every input; a correct reshape must "
                     "verify, else SPEC-TOO-STRONG on statement order.",
    },
    {
        "id": "pos-inline-lift",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the finite-lift `finiteSeq base` as its definitional
        # body `base.map Threshold.value` at the cons site (drop the named
        # selector). Same value; the reproof unfolds the selector.
        "module": _impl_reproved(
            "    let out : List Threshold := Threshold.top :: base.map Threshold.value\n"
            "    return out",
            "prove_correct withLeadingSentinel by loom_solve\n  <;> simp [finiteSeq]"),
        "rationale": "inlining the finite-lift as its definitional body "
                     "`base.map Threshold.value` (what `finiteSeq` unfolds to) "
                     "leaves the output identical; the reproof only unfolds the "
                     "selector. A correct reshape must verify, else "
                     "SPEC-TOO-STRONG on how the tail lift is spelled.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's admissibility probe builds a concrete
    # in-domain input and self-calls to show the precondition admits a normal
    # input. A literal self-call is NOT available here (measured during the
    # audit): `let anchored ← withLeadingSentinel probe` inside the method's own
    # body makes the `def` recursive, and under
    # `loom.semantics.termination "total"` the elaborator demands a termination
    # proof it cannot infer (`failed to eliminate recursive application`,
    # `⊢ 1 + sizeOf 1 + ... < sizeOf base`) — so the case would be an infra
    # failure, not a statement about the precondition.
    #
    # It is therefore expressed as an in-region `assert` carrying BOTH residual
    # admissibility risks, discharged from the frozen spec's own vocabulary:
    #   (i)  the precondition ADMITS a normal multi-element input — `base ≠ []`
    #        is satisfiable at a concrete `[3, 2]` (if the require were secretly
    #        unsatisfiable, or `loom_solve` could not build such a witness value,
    #        this conjunct would not discharge); and
    #   (ii) the post-image AT that admitted input has the shape the spec claims
    #        — `length = 3` (= `base.length + 1`, facet L) and `head? = some
    #        Threshold.top` (facet H) — and the LEADING facet is NON-DEGENERATE:
    #        `Threshold.top` is provably distinct from finite `Threshold.value`
    #        positions, so the head clause really forks sentinel-vs-finite
    #        instead of being vacuously satisfiable by any value.
    # The audit measured that the assert is load-bearing: replacing the
    # non-degeneracy conjunct with the FALSE `Threshold.top = Threshold.value 1`
    # makes the build fail (`unsolved goals` on the named assert obligation), so
    # this case would catch a carrier that collapsed the sentinel into a finite
    # value. The rest of the impl is kept verbatim so the method's own ensures
    # still discharges.
    # =====================================================================
    {
        "id": "admiss-sentinel-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (Threshold.top ≠ Threshold.value 1 ∧ Threshold.top ≠ Threshold.value 0\n"
            "        ∧ ((3 : Rat) :: (2 : Rat) :: []) ≠ []\n"
            "        ∧ (Threshold.top :: finiteSeq ((3 : Rat) :: (2 : Rat) :: [])).length = 3\n"
            "        ∧ (Threshold.top :: finiteSeq ((3 : Rat) :: (2 : Rat) :: [])).head?\n"
            "            = some Threshold.top))\n"
            "    let out : List Threshold := Threshold.top :: finiteSeq base\n"
            "    return out",
            "prove_correct withLeadingSentinel by loom_solve\n  <;> simp [finiteSeq]"),
        "rationale": "the precondition admits a normal multi-element input "
                     "(`[3, 2] ≠ []` discharges, so `require base ≠ []` is "
                     "satisfiable and not secretly stronger), the post-image at "
                     "that admitted input has the claimed shape (length "
                     "`base.length + 1` = 3, facet L; `head? = some "
                     "Threshold.top`, facet H), and the leading facet is "
                     "NON-DEGENERATE: `Threshold.top` is provably distinct from "
                     "finite positions `Threshold.value 1` / `Threshold.value 0`, "
                     "so the head clause really does fork sentinel-vs-finite "
                     "(else the discriminator would be vacuous). Measured "
                     "load-bearing: negating the non-degeneracy conjunct fails "
                     "the build on the named assert obligation. The impl is kept "
                     "verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-finite-lead-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE load-bearing discriminator (facet H). Leads with a finite value
        # instead of the sentinel — the pre-patch behaviour restated as a
        # uniqueness rival. Uses a constant finite lead (`value 0`) so the
        # witness reduces under `decide` (a `head! + 1` lead would leave a Rat
        # redex `decide` cannot reduce; the finite-vs-sentinel constructor
        # mismatch is what the spec refutes either way).
        "module": _impl(
            "    let out : List Threshold := Threshold.value 0 :: finiteSeq base\n"
            "    return out"),
        "refinement": "leading with a FINITE value is exactly the pre-patch "
                      "anchoring (`max + 1`, a finite number). The F2P "
                      "regression asserts the leading threshold is infinite "
                      "(`np.isinf(thresholds[0])`); a finite lead makes it False "
                      "-> the non-regression test fails -> would NOT resolve. "
                      "This is the precise change the gold introduces (G-DIFF): "
                      "the prepatch skeleton reproduces it and fails "
                      "`prove_correct` on this same head clause.",
        "rationale": "REJECT from `out = Threshold.top :: finiteSeq base` on the "
                     "leading facet (H): the post-image demands the head be the "
                     "sentinel `Threshold.top`, but the rival's head is "
                     "`Threshold.value 0` and `value _ ≠ top` by construction. "
                     "Refuted at a singleton `base` — the minimal input that "
                     "exposes the wrong leading constructor.",
        "witness": _witness("withLeadingSentinelTester [(1 : Rat)]"),
    },
    {
        "id": "weak-no-prepend",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns the finite tail unchanged with NO leading position (length n,
        # not n+1). Attacks the leading facet (H, no sentinel head) AND the
        # length facet (L).
        "module": _impl(
            "    let out : List Threshold := finiteSeq base\n"
            "    return out"),
        "refinement": "omitting the leading position returns the curve "
                      "un-anchored: the leading element is the finite maximal "
                      "score, not the infinite sentinel, and the vector is one "
                      "element short. Both F2P checks (the exact anchored array "
                      "AND `np.isinf(thresholds[0])`) fail -> would NOT resolve.",
        "rationale": "REJECT from `out = Threshold.top :: finiteSeq base` on the "
                     "leading facet (H) and the length facet (L): the rival's "
                     "output is `finiteSeq base`, whose head (for non-empty "
                     "`base`) is a finite `Threshold.value`, not `Threshold.top`, "
                     "and whose length is `base.length`, not `base.length + 1`. "
                     "Refuted at a singleton `base` distinct from the other "
                     "witnesses.",
        "witness": _witness("withLeadingSentinelTester [(3 : Rat)]"),
    },
    {
        "id": "weak-drop-first-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the tail: leads with the correct sentinel but copies
        # only `base.tail` — drops the first (largest) finite threshold. Attacks
        # the length facet (L) and the tail-content facet (T).
        "module": _impl(
            "    let out : List Threshold := Threshold.top :: finiteSeq base.tail\n"
            "    return out"),
        "refinement": "dropping the first finite threshold yields, e.g., "
                      "`[inf, 0.7, 0.0]` where the F2P expects "
                      "`[inf, 1.0, 0.7, 0.0]` — the largest finite threshold is "
                      "missing. `assert_array_almost_equal` fails -> would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = Threshold.top :: finiteSeq base` on the "
                     "length facet (L) and the tail facet (T): the tail is "
                     "`finiteSeq base.tail` (one element short, missing the "
                     "leading finite threshold) rather than `finiteSeq base`. "
                     "Refuted at a two-element `base` — the shortest input on "
                     "which dropping the first tail element is observable.",
        "witness": _witness("withLeadingSentinelTester [(1 : Rat), (2 : Rat)]"),
    },
    {
        "id": "weak-tail-value-corrupted",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE rival on the tail (facet T): leads with the correct sentinel and
        # preserves the length, but remaps every finite threshold to the
        # constant 0 — the tail values diverge from `base`. (Constant remap, not
        # arithmetic, so the witness reduces under `decide`.)
        "module": _impl(
            "    let out : List Threshold := Threshold.top :: finiteSeq (base.map (fun _ => 0))\n"
            "    return out"),
        "refinement": "replacing the finite thresholds with a constant returns a "
                      "vector whose tail no longer carries the computed scores; "
                      "the F2P `assert_array_almost_equal` on the exact tail "
                      "(e.g. `[inf, 1.0, 0.7, 0.0]`) fails -> would NOT resolve. "
                      "A faithful real patch that overwrote the threshold values "
                      "would corrupt the returned array the same way.",
        "rationale": "REJECT from `out = Threshold.top :: finiteSeq base` on the "
                     "tail-content facet (T): the tail is "
                     "`finiteSeq (base.map (fun _ => 0))`, whose elements are all "
                     "`Threshold.value 0` rather than the elements of "
                     "`finiteSeq base`. Refuted at a two-element `base` with "
                     "non-zero values (so the constant remap is observable) — a "
                     "distinct input point.",
        "witness": _witness("withLeadingSentinelTester [(2 : Rat), (3 : Rat)]"),
    },
    {
        "id": "weak-tail-shifted",
        "kind": "uniqueness",
        "expect": "reject",
        # ARITHMETIC value rival on the tail (facet T). Leads with the correct
        # sentinel and preserves length and order, but shifts every finite
        # threshold by +1 — a per-element ARITHMETIC corruption, not a constant
        # remap, so it is not subsumed by `weak-tail-value-corrupted` (that rival
        # collapses the tail to a single constant and is refuted by observing the
        # values are all equal; this one keeps the tail injective, distinct and
        # correctly ordered, and is wrong only in each value's magnitude).
        # ADDED BY AUDIT: the port dropped this class claiming `decide` could not
        # reduce the `Rat.add` redex. Measured: plain `decide` indeed gets stuck
        # (`did not reduce to isTrue or isFalse`), but `decide +kernel` closes it,
        # so the class was expressible all along.
        "module": _impl(
            "    let out : List Threshold := Threshold.top :: finiteSeq (base.map (fun r => r + 1))\n"
            "    return out"),
        "refinement": "shifting every finite threshold by a constant offset "
                      "returns an anchored vector whose tail is uniformly off by "
                      "one: the sentinel lead and the length are right, the order "
                      "is right, but every reported cut-off is wrong. The F2P "
                      "`assert_array_almost_equal` on the exact tail compares "
                      "position-wise values, so a uniformly shifted tail fails it "
                      "-> would NOT resolve. The facet this closes is that the "
                      "LEADING position being right does not license perturbing "
                      "the finite ones: an impl can satisfy (H) and (L) exactly "
                      "and still silently alter every reported cut-off.",
        "rationale": "REJECT from `out = Threshold.top :: finiteSeq base` on the "
                     "tail-content facet (T) in its ARITHMETIC form: the tail is "
                     "`finiteSeq (base.map (· + 1))`, whose elements are "
                     "`Threshold.value (r + 1)` rather than `Threshold.value r`, "
                     "and `value (r+1) ≠ value r` for every `r`. Refuted at the "
                     "singleton `[1]`, where the tail must be `[value 1]` and the "
                     "rival produces `[value 2]`.",
        # `decide +kernel`: plain `decide` reduces via the elaborator's whnf and
        # gets stuck on the `Rat.add` redex; the kernel evaluates it. Adds no
        # assumption (`#print axioms` on this witness: propext, Classical.choice,
        # Quot.sound — Lean's standard three) and is NOT `native_decide`.
        "witness": _witness("withLeadingSentinelTester [(1 : Rat)]",
                            tactic="decide +kernel"),
    },
    {
        "id": "weak-tail-last-planted",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the tail, the sibling's last-element-wrong shape
        # ported FAITHFULLY (facet T). Correct sentinel head, correct length,
        # correct values at every tail index EXCEPT the final one, which is
        # planted with the constant 0. Strictly weaker (harder) than
        # `weak-tail-value-corrupted`, which corrupts EVERY index: this rival
        # agrees with the frozen post-image on all but one position, so it probes
        # whether the exact-equality ensures is elementwise rather than merely
        # "mostly right". ADDED BY AUDIT — the port re-expressed the sibling case
        # as a whole-tail constant remap and lost the partial-domain character.
        "module": _impl(
            "    let out : List Threshold := Threshold.top :: finiteSeq (base.dropLast ++ [0])\n"
            "    return out"),
        "refinement": "planting a constant for the FINAL (smallest) threshold "
                      "leaves the anchored vector correct at every other "
                      "position, so it survives any check that looks only at the "
                      "lead, the length, or a prefix. The F2P "
                      "`assert_array_almost_equal` is position-wise over the "
                      "whole array, so a wrong last finite threshold fails it "
                      "-> would NOT resolve.",
        "rationale": "REJECT from `out = Threshold.top :: finiteSeq base` on the "
                     "tail-content facet (T), at ONE index only: the tail is "
                     "`finiteSeq (base.dropLast ++ [0])`, which agrees with "
                     "`finiteSeq base` everywhere except the last position, where "
                     "it is `Threshold.value 0`. Refuted at `[1, 4]` — a "
                     "two-element `base` whose last element is non-zero (so the "
                     "plant is observable) and whose FIRST element is correct (so "
                     "the refutation is attributable to the last index, not to a "
                     "wholesale corruption).",
        "witness": _witness("withLeadingSentinelTester [(1 : Rat), (4 : Rat)]"),
    },
    {
        "id": "weak-tail-reordered",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER rival on the tail (facet T): leads with the correct sentinel and
        # preserves length and the multiset of finite thresholds, but REVERSES
        # the tail order. Correct head and length, wrong order.
        "module": _impl(
            "    let out : List Threshold := Threshold.top :: finiteSeq base.reverse\n"
            "    return out"),
        "refinement": "reversing the finite thresholds returns them in the wrong "
                      "order (the F2P vectors are ordered `[inf, 1.0, 0.7, 0.0]`, "
                      "decreasing); `assert_array_almost_equal` is "
                      "position-wise, so a reversed tail fails it -> would NOT "
                      "resolve. The anchoring step must preserve the upstream "
                      "ordering.",
        "rationale": "REJECT from `out = Threshold.top :: finiteSeq base` on the "
                     "tail-order facet (T): the tail is `finiteSeq base.reverse`, "
                     "which differs from `finiteSeq base` position-wise whenever "
                     "`base` is not a palindrome. Refuted at a two-element `base` "
                     "with distinct values `[5, 7]` — a fresh input point where "
                     "the order genuinely differs.",
        "witness": _witness("withLeadingSentinelTester [(5 : Rat), (7 : Rat)]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness — one of which is the MANDATORY
# frame-mutation rival). Every one is accounted for below. The sibling models
# the anchoring step over a single READ-ONLY sequence input carrying a fractional
# heap permission, building the result with a verified forward `while` loop; this
# backend models the SAME step STRAIGHT-LINE as the pure `Threshold.top ::
# finiteSeq base`, with the sentinel as its own constructor. The behavioral
# surface (leading sentinel + exact ordered tail) carries across intact; the
# permission surface, the loop, and the loop-invariant region do not exist here.
#
#   sibling case                    -> here                          disposition
#   -----------------------------------------------------------------------
#   frame-mutation-write-input      -> (none)                        VACUOUS
#   partial-domain-drop-first-tail  -> weak-drop-first-tail          PORTED
#   partial-domain-last-element-wrong -> weak-tail-last-planted      PORTED (faithful,
#                                                                     added by audit)
#                                    +  weak-tail-value-corrupted    (whole-tail
#                                                                     variant, kept)
#   finite-lead-prepatch            -> weak-finite-lead-prepatch     PORTED
#   no-prepend-length-n             -> weak-no-prepend               PORTED
#   pos-control-reordered           -> pos-tail-bound-first          PORTED (reshaped
#                                                                     straight-line)
#   pos-control-cheapest-inline     -> pos-inline-lift               PORTED
#   admissibility-f2p-shaped-input  -> admiss-sentinel-nondegenerate RE-AIMED
#   (no sibling)                    -> weak-tail-reordered           ADDED (order facet)
#   (no sibling)                    -> weak-tail-shifted             ADDED by audit
#                                                                     (arithmetic value
#                                                                      facet; the port
#                                                                      had wrongly
#                                                                      called it
#                                                                      un-witnessable)
#
# 7 ported (one faithfully re-ported by the audit), 1 re-aimed, 1 vacuous;
# 2 coverage rivals added (order facet, arithmetic value facet).
#
# VACUOUS (frame-mutation-write-input): the sibling's MANDATORY frame-mutation
#   rival keeps the gold body then writes back into a read-only sequence input
#   granted only at half permission, and must be rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: every parameter is an
#   immutable value, the method declares no `mut` binder, there is no heap and no
#   aliasing. There is no read-only input to overwrite and no permission system
#   to trip, so the class is vacuous. DEMONSTRATED by the audit rather than
#   asserted, with three real builds:
#     (a) writing the input directly (`base := [0]`) does not even ELABORATE —
#         "`base` cannot be mutated, only variables declared using `let mut` can
#         be mutated" — so the sibling's attack has no syntactic image here;
#     (b) the nearest expressible analogue, SHADOWING the input with a different
#         value and building the answer off the shadow
#         (`let base : List Rat := [0]`), is REJECTED by the frozen spec
#         (`unsolved goals`) — the ensures is stated over the method's own
#         parameter, so a substituted carrier cannot satisfy it. Same outcome for
#         a `let mut` local rebound to a different value. So the class's soundness
#         concern is already covered by the exact-equality ensures, not left open;
#     (c) writing to a FRESH mutable local while still returning the correct
#         answer off the real `base` verifies — correctly, since that impl is
#         observationally the frozen one and there is no caller-visible frame to
#         corrupt.
#   No substitute is fabricated, because a fabricated one would test (b), which
#   the existing rivals already do.
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# RE-AIMED (admissibility): the sibling's admissibility self-calls on a concrete
#   in-domain input to show the fractional-permission precondition admits a
#   normal read. A literal self-call is UNAVAILABLE here, and the audit measured
#   why rather than assuming it: `let anchored ← withLeadingSentinel probe` in the
#   method's own body makes the `def` self-recursive, and under
#   `loom.semantics.termination "total"` elaboration fails with
#   `fail to show termination ... failed to eliminate recursive application`
#   (goal `⊢ 1 + sizeOf 1 + ... < sizeOf base`) — an infra failure that would
#   attest to nothing about the precondition. There is also no permission
#   surface. So the probe is expressed as an in-region assert carrying both
#   residual risks: (i) the precondition ADMITS a concrete multi-element input
#   (`[3, 2] ≠ []`), and (ii) the post-image at that input has the claimed
#   length (`base.length + 1`) and sentinel head, with the LEADING facet
#   non-degenerate (`Threshold.top ≠ Threshold.value _`). Measured load-bearing:
#   negating the non-degeneracy conjunct fails the build on the named assert.
# PORTED-RESHAPED (pos-tail-bound-first): the sibling's positive control reorders
#   independent local statements before its loop. This backend is straight-line
#   (no loop), so the reshape SPIRIT — "structurally different, behaviourally
#   identical" — is carried by binding the finite tail to a local before consing
#   the sentinel. Same output on every input; the reproof is `loom_solve`.
# PORTED (pos-inline-lift): mirrors the sibling's "cheapest honest impl" that
#   inlines the sentinel construction. Here the finite-lift `finiteSeq base` is
#   inlined to its definitional body `base.map Threshold.value`; the reproof
#   unfolds the selector.
# PORTED (weak-tail-last-planted): the sibling's last-element-wrong rival, ported
#   FAITHFULLY by the audit — it plants the constant 0 for the FINAL threshold
#   only, agreeing with the frozen post-image at every other index, which is what
#   makes it a partial-domain rival. Refuted at `[1, 4]` (non-zero last element,
#   correct first element) under plain `decide`.
# KEPT (weak-tail-value-corrupted): the whole-tail constant remap. Not redundant
#   with the above — it collapses every index, so it also pins that the tail is
#   read from `base` at all rather than merely being the right length; but it is
#   the WEAKER of the two, which is why the audit added the last-index variant
#   rather than leaving it as the port's sole stand-in for the sibling case.
# ADDED by audit (weak-tail-shifted): the arithmetic form of facet (T). The port
#   dropped this class asserting `decide` could not reduce a per-index `Rat`
#   arithmetic corruption. Half true and the wrong conclusion: plain `decide`
#   does get stuck (`did not reduce to isTrue or isFalse`, after unfolding
#   `instDecidableEqRat`), but `decide +kernel` evaluates the instance in the
#   kernel and closes it — the witness elaborates against the rival (exit 0) and
#   fails on the frozen solution by `decide` PROVING the proposition false
#   (exit 1), which is a semantic refutation, not tactic breakage. `#print axioms`
#   on the witness reports only `propext, Classical.choice, Quot.sound`.
# ADDED (weak-tail-reordered): the exact-equality ensures pins the tail ORDER as
#   an independent facet of (T). No ported rival attacks order specifically
#   (drop-first attacks length+content, value-corruption attacks values). This
#   rival preserves the sentinel head, the length, and the multiset of finite
#   thresholds but reverses their order — refuted at `[5, 7]`, the point where
#   the reversed tail differs position-wise.
#
# BINDER / FACET COVERAGE of the reject witnesses over the sole input binder
#   `base : List Rat` (7 rivals over 6 distinct input points):
#     base — [1]     (finite-lead-prepatch: singleton, wrong leading constructor);
#            [1]      (tail-shifted: same singleton, but the refutation is on the
#                      tail VALUE, not the head — the same point discriminates a
#                      different facet, so this is not a duplicated probe);
#            [3]      (no-prepend: singleton, distinct value, missing head+length);
#            [1, 2]   (drop-first-tail: two-element, first tail element dropped);
#            [1, 4]   (tail-last-planted: two-element, ONLY the last index wrong);
#            [2, 3]   (tail-value-corrupted: two-element non-zero, values remapped);
#            [5, 7]   (tail-reordered: two-element distinct, order reversed):
#            varied across singleton / multi-element and distinct values — never
#            held fixed, so every facet's dependence on `base` is probed.
#   Every independent top-level facet of the post-image is attacked: the LEADING
#   sentinel (H) — finite-lead-prepatch and no-prepend; the LENGTH (L) —
#   no-prepend and drop-first-tail; the TAIL content (T) in all three forms it can
#   be wrong — wholesale (tail-value-corrupted), at a single index
#   (tail-last-planted), and by arithmetic perturbation with the shape intact
#   (tail-shifted) — plus the TAIL ORDER (T) — tail-reordered.
#
# AUDIT PROBES that found NO spec hole (run with the real verifier; recorded so
#   the next reader does not re-spend the builds). Each of these WRONG impls was
#   written fresh against the frozen spec and REJECTED (exit 1, `unsolved goals`
#   on the frozen obligation): sentinel appended as a TRAILING position rather
#   than leading; the sentinel prepended TWICE; the sentinel prepended but the
#   tail dropped entirely on singleton inputs only (a length-guarded
#   partial-domain evasion); the first finite threshold duplicated into the tail;
#   the tail's LAST element dropped (`dropLast`); and the sentinel inserted at the
#   SECOND position instead of the first. Each of these CORRECT reshapes was
#   written fresh and VERIFIED (exit 0), so the spec is not too strong on shape:
#   `[Threshold.top] ++ finiteSeq base`; the tail built by an explicit `foldr`
#   instead of `map`; the cons guarded by a redundant `if base.isEmpty` test the
#   precondition already excludes; and the tail lifted via a double reverse
#   (`(finiteSeq base.reverse).reverse`).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (the upstream input carrier is run as the
# real callee by the Docker gates), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
