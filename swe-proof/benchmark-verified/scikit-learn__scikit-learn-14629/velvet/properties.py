"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14629 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct gatherLabels`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against a subject known to satisfy the spec). That subject is NOT the frozen
solution here — its loop makes every claim undecidable, so its exit code
discriminates nothing — but the loop-free ``witness_reference`` each reject case
names; see the CARRIER NOTE for the builds that establish this.

DEFENDED SURFACE (one contracted method):

  gatherLabels (submodels : List Submodel) return (out : List (List Int))
    ensures out = gatheredLabels submodels        -- (C1) element-wise value+order
    ensures out.length = submodels.length          -- (C2) one entry per sub-model

The method records, for a fitted multi-target model, one class-label collection
per per-target sub-model, in sub-model order. A ``Submodel`` exposes only the
touched field ``labels : List Int`` (the class-label collection that sub-model
learned). The load-bearing clause (C1) pins ``out`` element-wise to the
fully-unfolded pure model ``gatheredLabels``:

  ``gatheredLabels [] = []``
  ``gatheredLabels (s :: ss) = s.labels :: gatheredLabels ss``

so (C1) already fixes length, order, and per-position value; (C2) restates the
length half explicitly (mirroring the tested ``len(...) == n_outputs``). There
is NO opaque answer-key to echo: the ``axioms`` region is empty and
``gatheredLabels`` is a fully-unfolded ``def`` over the method's own argument,
so the unique satisfier IS the honestly-gathered per-sub-model label list. The
single top-level clause combines several independently-attackable
sub-obligations:

  * PER-POSITION VALUE: ``out[k]`` equals the k-th sub-model's ``labels`` (not a
    constant, not another sub-model's labels);
  * ORDER: the collection is in sub-model order (no reversal / permutation);
  * LENGTH: ``out`` has exactly one entry per sub-model (no off-by-one).

The single INPUT BINDER is ``submodels``.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY GOLD CANNOT BE THE SECOND
SUBJECT. This bundle runs under ``loom.semantics.termination "total"`` (so every
loop must carry a decreasing measure; see the DIVERGENCE entry below, whose
disposition this setting fixes). The gold impl is a backward ``while`` loop (the
front-recursive-fold pattern), so its extracted tester does NOT reduce: the
``forIn Lean.Loop.mk`` fixpoint survives, and ``decide`` on the tester reports
``did not reduce to `isTrue` or `isFalse` ... reduction got stuck``. Every reject
rival below is instead a loop-free straight-line closed form whose extracted
tester DOES reduce by kernel computation. A witness reaches the impl through
Velvet's derived tester (``derive_tester_for gatherLabels`` gives
``gatherLabelsTester : List Submodel → Bool``, deciding whether the impl meets
its own contract at an input) and states ``gatherLabelsTester s = false`` at a
fully-concrete input: the rival provably violates the contract at ``s``, so the
witness ELABORATES against the rival.

The FROZEN SOLUTION cannot serve as the discriminating second subject here, and
every reject case therefore carries an explicit ``witness_reference``. Measured
with real ``scripts/lean_verify.sh`` builds against the frozen file, the witness
fails with ``Tactic `decide` failed for proposition gatherLabelsTester [...] =
false because its `Decidable` instance ... did not reduce to `isTrue` or
`isFalse```. The kernel never evaluates the claim, so gold's exit code is 1
regardless of truth and discriminates NOTHING. This is the ``_STUCK_REDUCTION``
defect class of ``swebench_unified.gates.pbt``; its ``_stuck_screen``
classifies these logs as the ``reduction`` screen, i.e. the gate DOES catch this
one automatically, which is why every case names a reference rather than relying
on the fallback.

So each reject case names ``witness_reference`` = the loop-free
``return gatheredLabels submodels`` impl (``_REF_IMPL``, the same source as the
``pos-return-model`` positive). The gate independently checks a reference shares
the frozen spec and VERIFIES before using it, and both hold (measured: exit 0).
That subject is truth-SENSITIVE, which is the whole point, and it was verified to
be so by the flipped-claim experiment rather than assumed: against the reference
the refutation ``gatherLabelsTester s = false`` FAILS with the SEMANTIC ``Tactic
`decide` proved that the proposition gatherLabelsTester [...] = false is false``
(exit 1), while the SAME file with only the claim flipped to ``= true``
ELABORATES (exit 0). Both polarities measured at all four inputs. Per-case exit
codes, all re-measured: each witness elaborates against its rival (exit 0, and
the flipped ``= true`` claim fails there, exit 1) and is semantically refuted
against the reference (exit 1). The carrier at every witness is concrete (``List
Submodel`` literals over ``List Int`` labels), so ``decide`` closes the residual
literal, no hypothesis is assumed, and there is no joint-satisfiability
obligation.

WITHDRAWN CLAIM (recorded because the earlier text asserted the opposite, and
the correction is the reason the witness shape changed). An earlier revision
stated its refutations as ``gatherLabelsExec s ≠ DivM.res (gatheredLabels s)``
and claimed the reference subject was truth-sensitive under that shape. Attack
B′ refutes this: under the ``≠``-over-the-extractor shape the reference-side
build fails for the refutation AND for its exact opposite alike — the flipped
``=`` claim, which is TRUE of the reference, fails with ``error: No goals to be
solved`` (``simp`` closes the equational goal, leaving ``decide`` nothing to do).
An exit code that is 1 for a true claim and 1 for a false one carries no
information, so under that shape the reference-side rejection attested to
nothing. Measured concretely: a witness asserting the RIVAL is correct at an
agreement point (``gatherLabelsExec [] = DivM.res (gatheredLabels [])``)
elaborated against the rival (exit 0) and failed against the reference (exit 1),
i.e. the forgery cleared BOTH halves and would have been recorded ``rejected``.
The tester shape now shipped is immune: that same forgery, restated as
``gatherLabelsTester ([] : List Submodel) = true``, elaborates against the rival
AND against the reference (exit 0 both), so the gate records it
``witness-vacuous`` rather than passing.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical correct impls (return the grounded pure model
    ``gatheredLabels submodels`` directly with no loop; and the loop with the
    per-sub-model label collection bound to a typed local before prepending)
    must verify, else the spec is SPEC-TOO-STRONG on the impl shape. The
    direct-model form reproves with a bare ``loom_solve``; the local reshape
    keeps the frozen ``loom_solve; rw [gatheredLabels_drop_step …]; simp_all``
    proof (only the elided impl / tactic regions change).
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame rival that WRITES through a read-only input held at a fractional heap
    permission (``Acc(estimators[i].cls_vals, 1/4)``): a rival that assigns back
    onto a fitted sub-model's learned labels, rejected for insufficient
    permission. Lean and Velvet are referentially transparent: ``submodels`` is
    an immutable value, this bundle declares NO ``mut`` binder for it, and there
    is no heap and no aliasing — so there is no read-only input to overwrite and
    no permission system to trip. Not fabricated (per the porting map, this class
    is vacuous on a referentially-transparent backend). See the footer.
  * DIVERGENCE / NON-TERMINATION — NOT a spec hole here, and NOT shippable as a
    reject case; the blocker is the witness contract, not the spec. This bundle
    runs under ``loom.semantics.termination "total"``, so the verifier DISCHARGES
    a termination obligation and a rival whose loop carries no decreasing measure
    is genuinely REJECTED — the ``partial``-semantics vacuity hole an earlier
    revision recorded here does NOT apply to this bundle. Measured directly: the
    frozen loop with its ``decreasing i`` clause deleted fails with ``error:
    Decreasing annotations are required in total correctness semantics`` (exit 1),
    so the spec does reject divergence. It is nevertheless not shipped as a case,
    for a mechanical reason rather than a spec reason: ``witness_file`` retains the
    rival's impl, so the same termination error fires in the WITNESS build too
    (measured: exit 1 against the rival, where the contract requires exit 0), and
    the gate scores a reject case whose witness does not hold of its rival as
    ``witness-unproven`` — inconclusive, which is a gate ERROR, not a pass. So the
    class is CLOSED BY THE SEMANTICS and unshippable as a witness-bearing case;
    the sibling carries no ``diverge-*`` case to port either.
  * ADMISSIBILITY — PORTED as ``admiss-f2p-shaped``. The sibling's control asserts
    an F2P-shaped fitted list establishes its half-permission ``Requires``. This
    backend's method has NO ``require`` clause (the ``pre-conditions`` region is
    empty), so that exact question is trivially yes — but the absence of a
    precondition does NOT make the lane vacuous, it RELOCATES the probe: on a total
    carrier the PRECOND-TOO-STRONG analogue is the OBLIGATION being unsatisfiable,
    or degenerate, at exactly an F2P-shaped input. The ported case discharges the
    post-image at a concrete three-target input BY EVALUATION (satisfiability, the
    length clause, non-constancy, and order-asymmetry) as ``have``s that must build
    BEFORE the frozen obligation is closed verbatim. The reject lane does NOT
    subsume this: it shows four WRONG impls fail, which is non-degeneracy of the
    spec against rivals, not satisfiability of the obligation at a real input —
    an unsatisfiable obligation would also reject all four.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a fully-unfolded pure function
    of the input binder; there is no answer-key term a wrong impl could echo. The
    cheapest correct impl gathers the labels honestly, which the positive
    controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the last entry dropped; the order
    reversed; every entry a constant empty collection; the leading position
    off-by-one).
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14629"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the ENTIRE frozen loop body (between and INCLUDING
# ---- the markers). Lies wholly inside the single `-- impl-start`/`-- impl-end`
# ---- region and is unique in Solution.lean (both facts asserted at load by
# ---- _swap / the assert below).
_IMPL = """    -- impl-start
    let mut result : List (List Int) := []
    let mut i := submodels.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ submodels.length
      invariant result = gatheredLabels (submodels.drop i)
      done_with i = 0
      decreasing i
    do
      let s := submodels[i - 1]!
      result := s.labels :: result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen loop
# ---- body. The direct positive control drops the loop entirely and retunes the
# ---- body to a bare `loom_solve`; both the impl region and the `prove_correct`
# ---- body are elided from the spec view, so same_spec still holds and the
# ---- `prove_correct gatherLabels` obligation survives with an identical header.
# ---- Unique in the file.
_PROOF = """prove_correct gatherLabels by
  loom_solve
  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _rewrite_impl(body):
    """Full variant: impl body replaced, spec + frozen proof left intact. For
    reject rivals (expected NOT to verify — the frozen loop-tuned proof cannot
    close the reshaped body) and for the local-reshape positive control (the
    invariants are kept verbatim so the frozen proof still discharges)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, so a witness reaches the
# ---- impl through Velvet's DERIVED TESTER: `derive_tester_for gatherLabels`
# ---- builds `gatherLabelsTester : List Submodel → Bool`, which decides "does
# ---- this impl meet its own contract at this input". The witness asserts
# ---- `gatherLabelsTester s = false` — the impl VIOLATES the contract at the
# ---- concrete input `s`. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict.
#
# ---- WHY THIS SHAPE AND NOT `gatherLabelsExec s ≠ DivM.res (gatheredLabels s)`.
# ---- The `≠`-over-the-extractor shape was measured NON-DISCRIMINATING on this
# ---- carrier, in the precise sense attack B′ tests for: build the witness, then
# ---- build the SAME file with the claim FLIPPED (`=` for `≠`, i.e. asserting the
# ---- impl is CORRECT at `s`) and compare the second subject's exit codes. Under
# ---- the `≠` shape both fail against the reference impl (exit 1 for the
# ---- refutation, exit 1 for its exact opposite: `error: No goals to be solved`,
# ---- because `simp` has already closed the equational goal and leaves `decide`
# ---- nothing to do). An exit code that is 1 whether the claim is TRUE or FALSE
# ---- carries no information about the claim, so it cannot attest to a
# ---- refutation. Under the TESTER shape the exit code tracks the claim on BOTH
# ---- subjects (all measured, four inputs x both polarities):
# ----   rival  `= false` -> exit 0   |  rival  `= true` -> exit 1
# ----   ref    `= false` -> exit 1   |  ref    `= true` -> exit 0
# ---- and the reference-side failure is the SEMANTIC `Tactic \`decide\` proved
# ---- that the proposition gatherLabelsTester [...] = false is false`. That pair
# ---- is a genuine refutation: the same file with only the claim changed gets the
# ---- opposite verdict.
def _witness(inp):
    return (
        "extract_program_for gatherLabels\n"
        "prove_precondition_decidable_for gatherLabels\n"
        "prove_postcondition_decidable_for gatherLabels\n"
        "derive_tester_for gatherLabels\n\n"
        "example : gatherLabelsTester " + inp + " = false := by\n"
        "  decide\n"
    )


# ---- The witness's second SUBJECT. The frozen loop-solution cannot decide any
# ---- claim: its extracted tester does not reduce, so the witness build against it
# ---- fails with `Tactic \`decide\` failed ... did not reduce to \`isTrue\` or
# ---- \`isFalse\` ... reduction got stuck` (measured; the gate's own
# ---- `_stuck_screen` classifies this log as the `reduction` screen). A failure
# ---- the kernel never evaluated attests to nothing, so refuting a witness there
# ---- would be evidence-free.
# ---- Every reject case is refuted against THIS impl instead: loop-free, so its
# ---- tester reduces by kernel computation, and a VERIFYING impl of the
# ---- byte-identical frozen spec — which the gate re-checks itself before trusting
# ---- it. An impl the verifier accepts cannot violate its own spec, so a genuine
# ---- "the spec is violated at s" witness must still fail here, and it fails
# ---- SEMANTICALLY (`decide` proved `gatherLabelsTester s = false` is false),
# ---- not by a stuck term. Truth-sensitivity re-measured per case: the same
# ---- witness with the claim flipped to `= true` ELABORATES against this subject
# ---- (exit 0) where the refutation FAILS (exit 1), so the exit code here does
# ---- track what is claimed.
_REF_IMPL = _swap(_rewrite_impl("    return gatheredLabels submodels"),
                  _PROOF, "prove_correct gatherLabels by\n  loom_solve")

# ---- ADMISSIBILITY subject. The method has NO `require` clause, so "is this input
# ---- admitted" is trivially yes and the sibling's permission-establishing half has
# ---- no analogue. The lane is NOT vacuous for that reason, though: on a total
# ---- carrier the PRECOND-TOO-STRONG analogue is the OBLIGATION being unsatisfiable
# ---- — or degenerate — at exactly an F2P-shaped input, which a positive that
# ---- discharges it at that concrete input by EVALUATION tests directly. These
# ---- `have`s do that and are then `clear`ed, so the frozen tactic script runs from
# ---- a byte-identical context and reproves the real obligation verbatim rather
# ---- than being aided by them.
_ADMISS_INPUT = ("[{ labels := [0, 1] }, { labels := [0, 1, 2] }, "
                 "{ labels := [1] }]")
_ADMISS_PROOF = (
    "prove_correct gatherLabels by\n"
    f"  have hsat : gatheredLabels {_ADMISS_INPUT}\n"
    "      = [[0, 1], [0, 1, 2], [1]] := by decide\n"
    f"  have hlen : (gatheredLabels {_ADMISS_INPUT}).length = 3 := by decide\n"
    f"  have hconst : gatheredLabels {_ADMISS_INPUT}\n"
    "      ≠ [([] : List Int), [], []] := by decide\n"
    f"  have horder : gatheredLabels {_ADMISS_INPUT}\n"
    f"      ≠ (gatheredLabels {_ADMISS_INPUT}).reverse := by decide\n"
    "  clear hsat hlen hconst horder\n"
    "  loom_solve\n"
    "  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]\n"
    "  simp_all\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded pure model `gatheredLabels submodels` directly. `gatheredLabels`
        # is a total function of the input (no opaque answer-key), so this is a
        # correct impl, not an echo. The residual goal is definitional (`out =
        # gatheredLabels submodels` and the length clause via
        # `gatheredLabels_length`), closed by a bare `loom_solve`; the frozen
        # loop-specific rewrite is not needed and is dropped (the tactic body is
        # elided from the spec view, so same_spec and the obligation header are
        # untouched).
        "module": _REF_IMPL,
        "rationale": (
            "the cheapest honest correct impl returns the grounded pure model "
            "`gatheredLabels submodels` directly (no loop at all — maximally "
            "different from the gold backward `while`). Clause (C1) is literally "
            "`out = gatheredLabels submodels`, so it holds on the whole domain and "
            "(C2) follows by `gatheredLabels_length`; a bare `loom_solve` "
            "discharges the definitional residual. If this failed the spec would "
            "be over-fit to the loop shape (SPEC-TOO-STRONG). Also the honest "
            "no-ungrounded-echo control: the model IS the real per-sub-model "
            "gathering, so returning it is correct, not a cheat. (Sibling: "
            "pos-local-hoist / pos-value-copy — a structurally-different correct "
            "impl.)"),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Keep the backward loop but bind the per-sub-model label collection into a
        # typed local `ls` before prepending (a distinct data shape from the inline
        # `s.labels :: result`). Observationally identical to gold; the loop
        # invariants are kept verbatim, so the frozen `loom_solve; rw
        # [gatheredLabels_drop_step …]; simp_all` proof still closes.
        "module": _rewrite_impl(
            "    let mut result : List (List Int) := []\n"
            "    let mut i := submodels.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ submodels.length\n"
            "      invariant result = gatheredLabels (submodels.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let s := submodels[i - 1]!\n"
            "      let ls := s.labels\n"
            "      result := ls :: result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": (
            "structurally-different CORRECT impl: the per-sub-model label "
            "collection is bound to a typed local `ls` before prepending, instead "
            "of the inline `s.labels :: result`. Same behaviour, different data "
            "shape; the loop invariants are kept verbatim so the frozen proof "
            "(`loom_solve; rw [gatheredLabels_drop_step …]; simp_all`) still "
            "discharges. Must verify, else the spec is over-fit to the inline "
            "prepend form => SPEC-TOO-STRONG. (Sibling: pos-local-hoist — a "
            "typed-local reshape of the loop body.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE, and NON-DEGENERATE, at
    # an F2P-shaped input. On a require-free total carrier this is what replaces
    # the sibling's "the precondition admits a normal input" probe; it is the only
    # lane that can detect PRECOND-TOO-STRONG, so it is not droppable merely
    # because the `pre-conditions` region is empty.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl kept BYTE-FOR-BYTE; only the elided tactic body gains a
        # preamble of `have`s that EVALUATE the post-image at a concrete
        # F2P-shaped input (three targets, whose label collections are NOT all
        # equal and are NOT a palindrome — so the point discriminates against both
        # the constant and the reversal defects). Each is discharged by `decide`,
        # then all four are `clear`ed so the frozen script reproves the real
        # obligation from an unchanged context.
        "module": _swap(_BASE, _PROOF, _ADMISS_PROOF),
        "rationale": (
            "PASS SOURCE = the frozen obligation is SATISFIABLE and NON-DEGENERATE "
            "at an F2P-shaped input. The method declares no `require`, so the "
            "sibling's 'does the precondition admit this input' question is "
            "trivially yes; what carries over on this carrier is the sharper half — "
            "the post-image must actually ADMIT a value at the input shape the "
            "failing test sets up (three targets, each with its own class-label "
            "collection), and must not be degenerate there. `hsat` EVALUATES the "
            "post-image at that concrete input and pins it to "
            "[[0,1],[0,1,2],[1]]; `hlen` pins the length clause (C2) to 3 = the "
            "number of sub-models; `hconst` shows the post-image is NOT the "
            "all-empty collection, so (C1) is not satisfiable by a constant there; "
            "`horder` shows it is NOT equal to its own reversal, so the point "
            "genuinely discriminates ORDER (a palindromic input would not — "
            "measured: the same case over "
            "[{labels:=[0,1]},{labels:=[0,1,2]},{labels:=[0,1]}] FAILS on `horder` "
            "precisely because that input IS order-symmetric). If the obligation "
            "were unsatisfiable at an F2P-shaped input, or degenerate there, these "
            "`decide`s would fail => PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE. "
            "LIVENESS measured per `have`, so this is not a tautology spliced in to "
            "fill a lane: falsifying any one of the four makes the file FAIL (exit "
            "1) where the true form elaborates (exit 0) — a wrong `hsat` literal, "
            "`hlen` at 4, `hconst` flipped to `=`, and `horder` flipped to `=` were "
            "each built and each failed. The impl is the frozen one verbatim and "
            "the `have`s are `clear`ed before `loom_solve`, so the spec is untouched "
            "and the real obligation is still closed by the frozen script. "
            "(Sibling: admiss-fshaped, re-aimed from its half-permission `Requires` "
            "— which has no counterpart here — onto obligation satisfiability.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test. Each rival's extracted program reduces by kernel
    # computation, so its witness discriminates by value (see the CARRIER NOTE);
    # the frozen spec and obligation header are untouched.
    # =====================================================================
    {
        "id": "r1-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (length): gather every sub-model correctly but DROP THE
        # LAST one, returning a list one element short. Attacks the LENGTH clause
        # (C2, and the length half implicit in C1).
        "module": _rewrite_impl("    return (gatheredLabels submodels).dropLast"),
        "refinement": (
            "a faithful patch that gathered labels for all sub-models but the last "
            "(e.g. iterating over `self.estimators_[:-1]`) records one entry too "
            "few. The failing test asserts `len(classes_) == n_outputs` and then "
            "compares each entry positionally; with a sub-model dropped the length "
            "assertion FAILS, so it would NOT resolve. Element-wise correct on "
            "every entry it DOES emit; the break is purely the dropped tail element "
            "(the length clause). Sibling: partial-drop-last."),
        "rationale": (
            "REJECT from the LENGTH clause: `gatheredLabels submodels` has one "
            "entry per sub-model, but `.dropLast` returns one fewer, so both `out "
            "= gatheredLabels submodels` (C1) and `out.length = submodels.length` "
            "(C2) fail whenever `submodels` is non-empty. If it verified => "
            "SPEC-TOO-WEAK (result length not pinned). Refuted at "
            "`[{labels:=[1]}, {labels:=[2]}]` (length 2): gold gives [[1],[2]], the "
            "rival [[1]]."),
        "witness": _witness("[{ labels := [1] }, { labels := [2] }]"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "r2-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (order): emit one entry per sub-model (LENGTH holds) but in
        # REVERSED sub-model order. Attacks the ORDER sub-obligation.
        "module": _rewrite_impl("    return (gatheredLabels submodels).reverse"),
        "refinement": (
            "a faithful patch that gathered the per-sub-model labels in reversed "
            "sub-model order (e.g. iterating `reversed(self.estimators_)`) keeps "
            "the right count but mis-orders the collection. The failing test "
            "compares each `classes_[i]` positionally against sub-model i's labels "
            "with `assert_array_equal`; whenever two sub-models carry different "
            "labels the mirrored position mismatches and the assertion FAILS, so it "
            "would NOT resolve. Length-correct; the break is purely the order. "
            "Sibling: reverse-order."),
        "rationale": (
            "REJECT from the ORDER sub-obligation of (C1): position k carries "
            "sub-model (len-1-k)'s labels, ≠ sub-model k's labels in general. (C2) "
            "still holds (length preserved), so ONLY the value/order half of (C1) "
            "rejects it — if it verified => SPEC-TOO-WEAK (order unpinned). Refuted "
            "at `[{labels:=[7]}, {labels:=[8]}]`: gold gives [[7],[8]], the rival "
            "[[8],[7]]."),
        "witness": _witness("[{ labels := [7] }, { labels := [8] }]"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "r3-const-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE / CONSTANT: right shape (one entry per sub-model, LENGTH holds) but
        # every entry the SAME constant empty label collection rather than the
        # genuine per-sub-model labels — the classic "populated but with the wrong
        # content" defect. Attacks the PER-POSITION VALUE sub-obligation.
        "module": _rewrite_impl("    return submodels.map (fun _ => ([] : List Int))"),
        "refinement": (
            "a faithful patch that populated the collection with one empty array "
            "per sub-model (`[np.array([]) for _ in self.estimators_]`) has the "
            "right length but the wrong content. The failing test's "
            "`assert_array_equal` of each empty array against a sub-model's real "
            "labels ([0,1,...]) FAILS on any sub-model with class labels, so it "
            "would NOT resolve. This is the 'populated with a constant instead of "
            "the genuine labels' defect. Sibling: const-empty-entry."),
        "rationale": (
            "REJECT from the PER-POSITION VALUE sub-obligation of (C1): `out[k]` is "
            "a constant `[]`, ≠ sub-model k's `labels` whenever that sub-model has "
            "any label. (C2) still holds (length preserved), so ONLY (C1) rejects "
            "it — if it verified => SPEC-TOO-WEAK (content unpinned). Refuted at "
            "`[{labels:=[5]}]` (a single non-empty sub-model): gold gives [[5]], "
            "the rival [[]]. Varies `submodels` to a length-1 list, the input the "
            "multi-element rivals never probe."),
        "witness": _witness("[{ labels := [5] }]"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "r4-shift-first",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (shift): emit one entry per sub-model (LENGTH holds), but
        # every position k < len-1 carries sub-model k+1's labels and the final
        # position repeats the LAST sub-model's labels. Machine-checked with `#eval`
        # at [{[1]},{[2]},{[3]}]: gold [[1],[2],[3]], rival [[2],[3],[3]]. So it is
        # a whole-vector left-shift-with-tail-repeat, NOT a defect confined to the
        # leading position: position 1 is also wrong ([3] vs the required [2]). It
        # remains a distinct attack from r2 (reverse) — the two disagree with gold
        # at different positions and are refuted at different inputs — but it is
        # NOT the "correct on every non-first position" near-miss the port's prose
        # claimed. Corrected here after re-deriving the rival's actual values.
        "module": _rewrite_impl(
            "    return (match submodels with\n"
            "      | [] => []\n"
            "      | _ :: _ =>\n"
            "        gatheredLabels (submodels.drop 1) ++ "
            "(match submodels.getLast? with | some l => [l.labels] | none => []))"),
        "refinement": (
            "a faithful patch that shifted the per-sub-model assignment by one "
            "(each position gets the NEXT sub-model's labels, the last position "
            "repeating the final sub-model) keeps the right count but mis-assigns "
            "positions. The failing test compares each `classes_[i]` positionally "
            "against sub-model i's labels; sub-model 0's labels differ from "
            "sub-model 1's in general, so `assert_array_equal` FAILS at position 0 "
            "and it would NOT resolve. Distinct from r2: a shift-with-tail-repeat "
            "loses one sub-model's labels entirely and duplicates another, where a "
            "reversal is a permutation that keeps the multiset — two different "
            "wrong ways to mis-assign positions, refuted at different inputs. "
            "Sibling: partial-shift-first."),
        "rationale": (
            "REJECT from the PER-POSITION VALUE sub-obligation of (C1): position k "
            "carries sub-model (k+1)'s labels for k < len-1, and the last position "
            "repeats the final sub-model's labels, so `out ≠ gatheredLabels "
            "submodels` as soon as two adjacent sub-models differ. (C2) still holds "
            "(length preserved), so ONLY (C1) rejects it — if it verified => "
            "SPEC-TOO-WEAK (the position-to-sub-model assignment unpinned). "
            "Machine-checked by `#eval` at `[{labels:=[1]}, {labels:=[2]}, "
            "{labels:=[3]}]` (length 3): gold gives [[1],[2],[3]], the rival "
            "[[2],[3],[3]] — wrong at position 0 AND at position 1."),
        "witness": _witness(
            "[{ labels := [1] }, { labels := [2] }, { labels := [3] }]"),
        "witness_reference": _REF_IMPL,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 4 partial-domain /
# value rivals) plus an EMPTY AXIOM lane (the added behaviour is a pure per-element
# structural gather, modeled deeply; no consumed axiom). The sibling contracts
# `gather_output_classes(estimators)` over a `List` of sub-classifiers under
# fractional read-only permissions (`Acc(list_pred(estimators), 1/2)`,
# `Acc(estimators[k].cls_vals, 1/4)`) and partial correctness. This backend models
# the SAME per-sub-model label gather DEEPLY and CONCRETELY (`gatheredLabels` over
# `List Submodel` with only the touched `labels : List Int` field), pins it with an
# element-wise `ensures` plus an explicit length `ensures`, runs under PARTIAL
# termination semantics, and has NO precondition and NO permission surface. Those
# carrier facts make two sibling classes vacuous/degenerate here.
#
#   nagini case                kind          -> here                 disposition
#   ---------------------------------------------------------------------------------
#   pos-local-hoist            soundness     -> pos-local-reshape     PORTED
#   pos-value-copy             soundness     -> pos-return-model      RE-SHAPED
#   admiss-fshaped             admissibility -> admiss-f2p-shaped     RE-AIMED
#   frame-mutate-input         uniqueness    -> (none)                VACUOUS
#   partial-drop-last          uniqueness    -> r1-drop-last          PORTED
#   partial-shift-first        uniqueness    -> r4-shift-first        PORTED
#   const-empty-entry          uniqueness    -> r3-const-empty        PORTED
#   reverse-order              uniqueness    -> r2-reverse-order      PORTED
#   AXIOM_TESTS (0)            axiom         -> (none)                N/A (empty; G-AX)
#
# 4 uniqueness ported + 2 soundness (1 ported, 1 re-shaped) + 1 admissibility
# re-aimed; 1 frame-mutation vacuous. 7 SPEC cases (2 soundness, 1 admissibility,
# 4 uniqueness).
#
# PORTED (pos-local-hoist -> pos-local-reshape): the sibling hoists
#   `est_vals(estimators[i])` into a typed local before the append, keeping every
#   loop invariant verbatim. Here the analogous reshape binds `s.labels` into a
#   local `ls` before prepending, invariants kept verbatim, frozen proof closes.
# RE-SHAPED (pos-value-copy -> pos-return-model): the sibling's second positive is
#   a value-equal "copy" (`est_vals(...).drop(0)`) proving the spec pins VALUE not
#   identity. Lean/Velvet are value-equational — `out = gatheredLabels submodels`
#   is already a value equality with no identity notion to distinguish, so a
#   `.drop(0)`-style copy is literally the same term and adds nothing. The
#   maximally-different correct impl here instead drops the loop and returns the
#   grounded model directly; it also serves as the no-ungrounded-echo control (the
#   model is the real work, not an answer-key). Both positives verified to build.
# PORTED (the four partial-domain / value rivals) — each re-expresses DIRECTLY onto
#   a sub-obligation of (C1)/(C2):
#   partial-drop-last -> r1-drop-last (loop bound one short -> length one short;
#     attacks (C2)). reverse-order -> r2-reverse-order (reversed sub-model order;
#     attacks the ORDER half of (C1), length preserved). const-empty-entry ->
#     r3-const-empty (every entry a constant empty collection; attacks the
#     PER-POSITION VALUE half of (C1), length preserved). partial-shift-first ->
#     r4-shift-first (each position carries the NEXT sub-model's labels, the last
#     repeating the final one; attacks the position-to-sub-model assignment of
#     (C1) — `#eval`-checked as [[2],[3],[3]] against gold's [[1],[2],[3]], i.e.
#     wrong at positions 0 and 1, not a first-position-only near-miss). Each refinement
#     argument carries over verbatim: a faithful counterpart with that defect still
#     produces a `classes_` the F2P test's length / positional `assert_array_equal`
#     rejects, so it would NOT resolve.
# RE-AIMED (admiss-fshaped -> admiss-f2p-shaped): the sibling's admissibility
#   control adds in-region Asserts that an F2P-shaped fitted list satisfies the
#   half-permission `Requires` (the loop reads each facet at 1/4). This backend's
#   method has NO `require` clause (the pre-conditions region is empty), so that
#   exact question is trivially yes and the permission surface has no analogue —
#   but the LANE is not therefore vacuous, and an earlier revision of this file was
#   wrong to record it as degenerate. On a total carrier the PRECOND-TOO-STRONG
#   analogue is the OBLIGATION being unsatisfiable (or degenerate) at exactly an
#   F2P-shaped input, so the probe RELOCATES onto satisfiability: the ported case
#   discharges the post-image at a concrete three-target input by EVALUATION (value,
#   length, non-constancy, order-asymmetry) as `have`s that build before the frozen
#   obligation is closed verbatim, then `clear`s them so the frozen script reproves
#   the real obligation from an unchanged context. The earlier "the reject lane
#   already demonstrates this" argument does NOT hold: four WRONG impls failing is
#   non-degeneracy against rivals, not satisfiability at a real input — an
#   UNSATISFIABLE obligation would reject all four too, and would pass that test
#   while being the exact defect this lane exists to catch.
# VACUOUS (frame-mutate-input): the sibling's MANDATORY frame rival ASSIGNS back
#   onto `estimators[i].cls_vals`, held read-only at `Acc(...,1/4)`, rejected by
#   the insufficient-permission check (a real write-back would corrupt shared
#   sub-estimator state the P2P tests reuse). This backend is referentially
#   transparent: `submodels` is an immutable value, no `mut` binder is declared for
#   it, and there is no heap, no aliasing, and no permission system. There is no
#   read-only input to overwrite and no frame clause to violate, so the class has
#   no carrier analogue. Omitted as a genuine carrier fact, NOT fabricated (porting
#   map: this class is vacuous on a referentially-transparent backend).
# DIVERGENCE / NON-TERMINATION: the sibling carries NO diverge-*/nonterm-*/
#   weak-diverge case, so there is nothing to port. The disposition here is CLOSED
#   BY THE SEMANTICS, and an earlier revision of this file recorded it wrongly as a
#   known `partial`-semantics hole — that text described a setting this bundle does
#   not use. `Solution.lean` sets `loom.semantics.termination "total"` and the frozen
#   loop carries a `decreasing i` clause, so the verifier discharges a termination
#   obligation and a diverging rival is genuinely REJECTED, not vacuously accepted.
#   Measured: deleting `decreasing i` from the frozen loop yields `error: Decreasing
#   annotations are required in total correctness semantics` (exit 1). So there is no
#   vacuity hole to record. It is still not SHIPPED as a reject case, for a
#   mechanical reason: `witness_file` retains the rival's impl, so that same
#   termination error fires in the witness build against the rival (measured: exit 1,
#   where the witness contract requires exit 0), and the gate scores such a case
#   `witness-unproven` => inconclusive => gate ERROR. The class is therefore closed
#   by the semantics and unshippable as a witness-bearing case, which is a property
#   of the witness contract rather than of this spec.
# AXIOM_TESTS: the sibling's axiom lane is EMPTY (no @ContractOnly axiom; the gather
#   is modeled deeply, `meta.deep_model_references == []`, `axioms == []`). Nothing
#   to drop, and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder
#   `submodels : List Submodel` and two top-level clauses: (C1) `out =
#   gatheredLabels submodels` (per-position value + order + length) and (C2)
#   `out.length = submodels.length`. All sub-obligations are attacked:
#     * PER-POSITION VALUE (C1): r3 (every entry a constant), r4 (position 0
#       off-by-one) — two distinct sub-domains.
#     * ORDER (C1): r2 (reversed).
#     * LENGTH (C1 + C2): r1 (drops the last entry).
#   The four reject witnesses probe four DISTINCT input points (pts=4):
#     * r1  [{labels:=[1]}, {labels:=[2]}]                      (length 2)
#     * r2  [{labels:=[7]}, {labels:=[8]}]                      (length 2)
#     * r3  [{labels:=[5]}]                                     (length 1)
#     * r4  [{labels:=[1]}, {labels:=[2]}, {labels:=[3]}]       (length 3)
#   So `submodels` ranges over lengths {1, 2, 3} and distinct label contents; no
#   two rivals are refuted at the same input. Each point is MEANINGFUL, not two
#   spellings of one: at r3's length-1 input r1 (`dropLast`) and r2 (`reverse`)
#   would each be indistinguishable from gold in one of the two clauses, and r4's
#   length-3 input is the shortest at which shift-with-tail-repeat separates from
#   reversal. The single binder is genuinely varied — the only binder the modeled
#   behaviour has. The two positive controls defend the whole obligation, and the
#   admissibility case adds a FIFTH distinct point — a length-3 input whose entries
#   are pairwise unequal AND order-asymmetric ([[0,1],[0,1,2],[1]]) — at which the
#   obligation is shown satisfiable by evaluation. That point is deliberately not a
#   palindrome: at an order-symmetric input the order-discrimination conjunct is
#   false, which was measured (the same case over [[0,1],[0,1,2],[0,1]] fails).
# WITNESS DISCRIMINATION — RE-DERIVED under the FORGERY test, which is what forced
#   the witness shape to change. Each witness states `gatherLabelsTester s = false`
#   over Velvet's derived tester and ELABORATES against its loop-free rival (exit 0,
#   four real builds), while the SAME file with the claim flipped to `= true` FAILS
#   against that rival (exit 1) — so the rival-side exit code tracks the claim too.
#   The frozen solution CANNOT be the second subject: its extracted tester does not
#   reduce, and the build fails with `Tactic \`decide\` failed ... did not reduce to
#   \`isTrue\` or \`isFalse\` ... reduction got stuck`, which the gate's own
#   `_stuck_screen` classifies as the `reduction` screen. So every reject case
#   carries `witness_reference` = `_REF_IMPL`, the loop-free VERIFYING impl of the
#   same frozen spec (gate-checked: shares the spec, exit 0). Against THAT subject
#   the discrimination is real and — measured, not assumed — truth-SENSITIVE: the
#   refutation fails with the SEMANTIC `Tactic \`decide\` proved that the
#   proposition gatherLabelsTester [...] = false is false` (exit 1) while the
#   flipped `= true` claim ELABORATES (exit 0). Both polarities were built at all
#   four inputs; the exit code therefore carries information about the claim, which
#   is the property the previous `≠`-over-the-extractor shape LACKED (there both
#   polarities failed on the reference, the flipped one with `No goals to be
#   solved`, so a forgery asserting a rival is CORRECT at an agreement point
#   cleared both halves — measured, and the reason that shape was withdrawn; see
#   the CARRIER NOTE's WITHDRAWN CLAIM). Under the shipped tester shape that same
#   forgery elaborates against BOTH subjects (exit 0 each) and is therefore caught
#   as `witness-vacuous`. The carrier is fully concrete at every witness, so each
#   closes by `decide` with no hypothesis and there is no joint-satisfiability
#   obligation (`consistency_probe` returns None). No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
# SPEC-TOO-WEAK PROBES beyond the shipped rivals (attack D; each a NEW wrong impl
#   built for real, NONE verified — no spec hole found). Six probes, all exit 1,
#   aimed at what the shipped four leave unattacked:
#     * `(gatheredLabels submodels).tail`            — drops the FIRST entry
#     * `gatheredLabels submodels ++ [([]: List Int)]` — one entry too MANY (r1's mirror)
#     * `submodels.map (fun s => s.labels.reverse)`  — right entries, each REVERSED
#         INTERNALLY (attacks value-inside-the-entry, which every shipped rival
#         leaves alone: r1/r2/r4 permute or drop whole entries, r3 blanks them)
#     * `submodels.map (fun _ => (submodels.headD default).labels)` — every position
#         echoes the FIRST sub-model's labels (right length, right first entry)
#     * `submodels.map (fun s => s.labels.eraseDups)` — per-entry de-duplication
#     * `submodels.map (fun s => s.labels.take 1)`   — per-entry TRUNCATION
#   So (C2) pins the length in both directions, and (C1) pins the content of each
#   entry, not merely which entry lands at which position.
# SPEC-TOO-STRONG PROBES beyond the shipped positives (attack E; NEW correct
#   reshapes, all CLOSED, so no soundness hole): `submodels.map (fun s => s.labels)`,
#   `submodels.foldr (fun s acc => s.labels :: acc) []`, and `gatheredLabels
#   (submodels.drop 0)` are faithful correct impls in shapes the battery does not
#   otherwise contain (`map`, `foldr`, and a value-equal reshape of the direct model
#   return, versus the gold backward `while`). None closes under a bare `loom_solve`
#   — that leaves the honest residual `⊢ List.map (fun s => s.labels) submodels =
#   gatheredLabels submodels`, an extensional fact about the pure model rather than a
#   spec defect — but each verifies (exit 0) once the tactic body supplies the
#   structural induction the reshape needs. The induction must be applied under
#   `all_goals`, since `loom_solve` leaves the length clause alongside the value
#   clause:
#     prove_correct gatherLabels by
#       loom_solve
#       all_goals induction submodels with
#         | nil => rfl
#         | cons s ss ih => simp [gatheredLabels, ih]
#   (Measured: without `all_goals` the `map` reshape still closes but the `foldr` one
#   does NOT — it exits 1 leaving `⊢ List.foldr (fun s acc => s.labels :: acc) []
#   submodels = gatheredLabels submodels`. An earlier revision of this footer gave
#   the `all_goals`-free script for both; that was wrong for `foldr` and is
#   corrected here.) So the spec admits correct impls in at least five distinct
#   shapes and is not over-fit to the frozen loop.
AXIOM_TESTS = []
