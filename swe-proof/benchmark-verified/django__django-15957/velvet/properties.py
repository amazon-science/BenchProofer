"""properties.py — G-PBT falsification battery for django__django-15957 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against a
subject that is known to satisfy the spec. On this bundle that subject is NOT the
frozen solution — see the CARRIER NOTE below, which the audit corrected — but the
``witness_reference`` each reject case names.

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); the
sibling's per-case adversarial argument is carried over and re-expressed against
this backend's carrier. Case-count parity is NOT the target — the Lean-family
bundle models only the purely-functional CORE of this change (a single
contracted ``method`` over a ``List (List Int)`` carrier), so nagini cases
attached to behaviour this bundle does not model, or to nagini-only machinery,
have no counterpart. The nagini->velvet accounting block at the bottom of this
file records exactly which sibling cases ported, which were omitted, and why.

DEFENDED SURFACE. One contracted method over three input binders:

  perGroupSlice (groups : List (List Int)) (low : Nat) (high : Option Nat)
                return (out : List Int)
    ensures out = slicedGroups low high groups                 -- (C1) load-bearing

The whole obligation is (C1). ``slicedGroups`` and its per-group primitive
``groupSlice`` are fully-unfolded ``def``s in the ``pure`` region — total
functions of the three inputs, with no opaque answer key to echo. The behaviour
turns on slicing EACH independent ordered group ON ITS OWN and concatenating in
group order:
  * ``low``  — a start offset (leading rows to skip), applied per group;
  * ``high`` — an optional stop: ``none`` keeps everything after the offset, a
    concrete ``some h`` keeps only the positions in ``[low, h)``, per group;
  * ``groups`` — the ordered rows split into independent groups; the offset/stop
    are measured from the start of EACH group, not across the combined sequence.

So (C1) pins a value that depends on all three binders, and each reject rival
below abuses a distinct facet: the per-group-vs-global distinction (the exact
bug the issue reports), the lower-offset on an open-ended slice (the F2P ``[1:]``
shape), the finite-stop clause, the stop-presence clause, and a vacuous no-op.

CARRIER NOTE (decisive for the witness route). The frozen impl is a BACKWARD
``while`` loop whose extracted program (``perGroupSliceExec``) does NOT
kernel-reduce under ``decide`` — the ``prove_postcondition_decidable_for`` route
leaves the loop's ``wp`` stuck (measured; the same fold+drop-step loop shape as
django__django-11163 / astropy__astropy-13453). A STRAIGHT-LINE rival, by
contrast, has an extracted program that reduces, so a Velvet-tester witness
(``perGroupSliceTester args = false``) ELABORATES against a straight-line rival
by ``decide``. Every reject rival below is therefore authored as a straight-line
WRONG impl. The rivals stay wrong for a VALUE reason — each returns a list that
differs from ``slicedGroups`` at the probed input — not for a shape reason; the
straight-line form is only what lets the extracted program reduce so the witness
can name the counterexample.

WHAT THE FROZEN SOLUTION CANNOT DO, and how the discrimination half is carried.
The same irreducibility that makes the LOOP a bad witness subject also makes it a
USELESS one: against the frozen looped solution every witness build fails with

    Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse`
    ... reduction got stuck at the `Decidable` instance

i.e. the kernel never evaluated the claim. That exit code is NOT a refutation —
the identical error appears for a TRUE claim about the same impl, so it
discriminates nothing (this is exactly the ``_STUCK_REDUCTION`` case the gate
screens for). An earlier revision of this file described gold's stuck exit as "a
genuine failure on gold"; that was WRONG and is corrected here. Each reject case
therefore carries an explicit ``witness_reference``: ``_POS_DIRECT``, the
straight-line CORRECT impl of this same frozen spec that ships as the
``pos-direct`` positive. It shares the frozen spec byte-for-byte and it VERIFIES
(both re-checked by the gate before it is used), so it cannot violate its own
postcondition at any input — and unlike the loop it REDUCES, so refuting the
witness against it is a real, kernel-evaluated verdict. Measured, per reject
case, three real builds:

  * against the RIVAL            -> EXIT 0 (the witness holds: the rival's
                                    extracted program violates (C1) there);
  * against ``_POS_DIRECT``      -> EXIT 1 with
        Tactic `decide` proved that the proposition
          perGroupSliceTester <args> = false
        is false
    — a SEMANTIC refutation of the concrete claim, not a missing identifier, a
    type error, an unfolding failure or a timeout;
  * against the frozen solution  -> EXIT 1 by STUCK REDUCTION (recorded here for
    completeness; it attributes nothing and is not what the case rests on).

Every witness point below was additionally checked at the VALUE level with a
standalone ``decide``: the rival's expression and ``slicedGroups`` really are
unequal there (so the rival is WRONG, not merely reshaped), and each rival AGREES
with ``slicedGroups`` at the four points the other rivals are refuted at, so no
two cases collapse onto one counterexample.

ADVERSARIAL READ of the nagini classes on this carrier:
  * MEMBERSHIP-TOKEN / CONTROL-FLOW-EFFECT (nagini's load-bearing clause) —
    NOT MODELLED here, so its rivals (echo-while-sliced, echo-after-clear,
    no-clear) have NO counterpart. The nagini spec pins an UNFORGEABLE capability
    granted only by the membership-application step, because in that carrier the
    membership predicate is a control-flow effect with no value discriminator.
    This velvet bundle models a DIFFERENT, narrower thing: the net per-group
    row-set the changed helper returns (mapping.md §1-2). The membership
    predicate (``field__in=instances``) is the UNCHANGED part of the call, shared
    by both the buggy and fixed branches, so it is not on the modeled surface and
    there is no token/flag state in the carrier to forge. These nagini rivals are
    omitted as attached to unmodeled behaviour, not fabricated a substitute for.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini ``query`` is a
    full-permission mutated carrier; Lean and Velvet are referentially
    transparent — ``groups``/``low``/``high`` are immutable values, none is
    ``mut``, there is no heap and no aliasing — so there is no read-only input to
    overwrite and no substitute probe to build.
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
  * UNGROUNDED-ORACLE ECHO — N/A: (C1) is pinned to a total, fully-unfolded
    function of the method's own inputs (``slicedGroups``/``groupSlice`` are
    concrete ``def``s; the ``axioms`` region is empty), so there is no answer key
    to echo. Any WRONG value fails (C1) — demonstrated by every reject rival.
    Covered instead by the pos-direct positive (returning ``slicedGroups …``
    directly is a correct grounded impl, not an echo).
  * PARTIAL-DOMAIN / VALUE rivals — APPLY: the nagini uniqueness value rivals
    port onto (C1), each diverging from gold on the exact sub-domain its abused
    facet governs.

WITNESS PLACEMENT. The six reject witnesses probe SIX distinct input points so
that all three input binders are varied across the battery (pts = 6):
  * weak-global-slice   — groups=[[1],[2]], low=0, high=some 1:
    two independent groups where the rival slices the COMBINED row-set once
    (keeps position 0 overall = [1]) instead of each group's own [0:1] (= [1,2]);
  * weak-drop-lower-open — groups=[[1,2]], low=1, high=none:
    the exact F2P ``[1:]`` shape (offset, open stop), where the rival forgets the
    offset on an open-ended slice (keeps [1,2]) instead of dropping it (keeps [2]);
  * weak-ignore-stop     — groups=[[1,2]], low=0, high=some 1:
    a finite stop the rival ignores (keeps [1,2]) instead of honoring [0:1] (=[1]);
  * weak-spurious-stop   — groups=[[1,2,3]], low=1, high=none:
    an open-ended slice onto which the rival imposes a spurious finite stop
    (keeps [] instead of [2,3]);
  * weak-vacuous         — groups=[[1],[2]], low=1, high=none:
    a no-slice near-miss returning the rows untouched ([1,2]) where gold applies
    the offset per group (= []).
  * weak-stop-as-count   — groups=[[1,2,3]], low=1, high=some 2 (ADDED by the
    audit): the BOUNDED-window corner, the only point where an offset and a
    finite stop are both present. The rival reads the stop as a per-group count
    after the offset (keeps [2,3] = positions [1,3)) instead of as a stop
    position (keeps [2] = positions [1,2)).
``low`` is moved between 0 and 1; ``high`` between ``none``, ``some 1`` and
``some 2``; ``groups`` between one group and two, over group lengths 1, 2 and 3.
No two rivals are refuted at the same point, and each rival was checked to AGREE
with ``slicedGroups`` at the other rivals' points, so the six counterexamples are
independent rather than five spellings of one.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the transformation is
modeled DEEPLY by ``groupSlice``/``slicedGroups`` — see mapping.md §3). There is
no axiom-soundness/containment obligation to probe here, and the gate ignores
``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-15957"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward while loop that prepends
# each group's own slice.
_IMPL = (
    "    let mut result : List Int := []\n"
    "    let mut i := groups.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ groups.length\n"
    "      invariant result = slicedGroups low high (groups.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let g := groups[i - 1]!\n"
    "      result := groupSlice low high g ++ result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the (retuned) proof without disturbing the obligation.
_IMPL_TOP = "    let mut result : List Int := []\n    let mut i := groups.length"
assert _BASE.count(_IMPL_TOP) == 1, "impl top drifted from expected text"

# The FULL frozen proof body. A variant that reshapes the impl retunes this; the
# tactic body is elided from the spec view, so it is a proof reshape, not a spec
# change. Unique in the file.
_PROOF = (
    "prove_correct perGroupSlice by\n"
    "  loom_solve\n"
    "  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"

# The straight-line proof: `loom_solve` alone closes a reshaped (non-loop) goal.
_PROOF_LS = "prove_correct perGroupSlice by\n  loom_solve"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# A straight-line rival: replace the loop with a bare `return <expr>` and drop
# the loop-specific drop-step from the proof (loom_solve alone; the rival is
# EXPECTED to fail to verify, which is the point of a reject case).
def _rival(expr: str) -> str:
    return _with_impl_and_proof("    return " + expr, _PROOF_LS)


# The witness subject for every reject case: the straight-line CORRECT impl that
# also ships as the `pos-direct` positive. The frozen looped solution cannot
# serve as one — its extracted program is irreducible, so `decide` is stuck for
# EVERY claim about it (true or false) and its nonzero exit attributes nothing.
# This impl shares the frozen spec byte-for-byte and VERIFIES (the gate re-checks
# both before using it), so it cannot violate (C1) anywhere, and it REDUCES — so
# `decide` returns a real verdict and the refutation is kernel-evaluated.
_POS_DIRECT = _with_impl_and_proof(
    "    return slicedGroups low high groups", _PROOF_LS)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `perGroupSliceTester groups low high = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. There is no `require` clause, so
# ---- every input reaches the postcondition (no vacuous pass on an excluded
# ---- one). `decide` reduces the extracted STRAIGHT-LINE program of each rival;
# ---- against the frozen looped solution the `Exec` never reduces, so the
# ---- witness fails on gold — the discriminator.
_TESTER = (
    "extract_program_for perGroupSlice\n"
    "prove_precondition_decidable_for perGroupSlice\n"
    "prove_postcondition_decidable_for perGroupSlice\n"
    "derive_tester_for perGroupSlice\n\n"
)


def _witness(args: str) -> str:
    return (_TESTER +
            f"example : perGroupSliceTester {args} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl: return
    # `slicedGroups low high groups` directly. Clause (C1) IS
    # `out = slicedGroups …` and `slicedGroups` is a total, grounded function of
    # the three inputs (no opaque oracle), so returning it is a correct,
    # fully-grounded implementation, not an echo. MUST verify; else the spec is
    # over-fit to the loop SHAPE => SPEC-TOO-STRONG. The obligation is byte-
    # identical; `loom_solve` alone closes the reshaped (straight-line) goal.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": "clause (C1) `out = slicedGroups low high groups` is pinned to a "
                     "total, grounded function of the three inputs, so directly "
                     "returning it is the honest cheapest CORRECT impl. A correct "
                     "reshape MUST verify, else the postcondition is over-fit to the "
                     "loop shape => SPEC-TOO-STRONG. Also shows the spec is not "
                     "echo-vulnerable (any WRONG value fails (C1)). Built: verifies.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — same backward loop, but each per-group
    # slice is hoisted into a named local `s` before the prepend. The loop
    # direction and every invariant/`done_with` are UNCHANGED (a forward loop
    # would need an f(a++b)=f(a)++f(b) lemma against the front-recursive
    # `slicedGroups` fold), so the frozen proof script still closes. Only the
    # executable shape (a `let s :=` then a prepend) differs. MUST verify; else
    # the postcondition is over-fit to the exact expression => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-localvar",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    let mut result : List Int := []\n"
            "    let mut i := groups.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ groups.length\n"
            "      invariant result = slicedGroups low high (groups.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let g := groups[i - 1]!\n"
            "      let s := groupSlice low high g\n"
            "      result := s ++ result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "structurally-different but equivalent CORRECT impl: the "
                     "per-group slice is hoisted into a named local before the "
                     "prepend. Same backward loop, same invariants/done_with verbatim "
                     "(so the front-recursive `slicedGroups` fold needs no append "
                     "lemma and the frozen proof still closes); only the executable "
                     "shape differs. Must verify (else SPEC-TOO-STRONG). Built: "
                     "verifies with the frozen proof.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — ADDED BY AUDIT. The OPPOSITE loop
    # direction: a FORWARD loop accumulating `result ++ groupSlice … groups[i]!`
    # under the mirror invariant (`groups.take i` instead of `groups.drop i`).
    # This is the strongest available SPEC-TOO-STRONG probe on this carrier: the
    # frozen `slicedGroups` is FRONT-recursive, so a forward loop cannot reuse
    # the frozen drop-step at all — it needs a genuinely different argument (the
    # append-split `slicedGroups (a ++ b) = slicedGroups a ++ slicedGroups b`,
    # proven inline by induction, then `take (i+1) = take i ++ [groups[i]]`).
    # An over-fit postcondition would reject it; the earlier battery contained no
    # positive that reshaped the loop's CONTROL FLOW (pos-localvar keeps the
    # backward loop and every invariant verbatim), so the soundness direction was
    # only ever probed against straight-line and cosmetic reshapes. MUST verify.
    # =====================================================================
    {
        "id": "pos-forward-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    let mut result : List Int := []\n"
            "    let mut i := 0\n"
            "    while i < groups.length\n"
            "      invariant i ≤ groups.length\n"
            "      invariant result = slicedGroups low high (groups.take i)\n"
            "      done_with i = groups.length\n"
            "      decreasing groups.length - i\n"
            "    do\n"
            "      result := result ++ groupSlice low high groups[i]!\n"
            "      i := i + 1\n"
            "    return result",
            "prove_correct perGroupSlice by\n"
            "  have happ : ∀ (a b : List (List Int)),\n"
            "      slicedGroups low high (a ++ b)\n"
            "        = slicedGroups low high a ++ slicedGroups low high b := by\n"
            "    intro a b\n"
            "    induction a with\n"
            "    | nil => rfl\n"
            "    | cons x xs ihx =>\n"
            "      rw [List.cons_append, slicedGroups_cons, slicedGroups_cons, ihx,\n"
            "        List.append_assoc]\n"
            "  loom_solve\n"
            "  all_goals try simp_all\n"
            "  all_goals\n"
            "    (have hlt : i < groups.length := by omega\n"
            "     have hsplit : List.take (i + 1) groups\n"
            "         = List.take i groups ++ [groups[i]] := by\n"
            "       rw [List.take_succ, List.getElem?_eq_getElem hlt]; rfl\n"
            "     rw [hsplit, happ, slicedGroups_cons, slicedGroups_nil,\n"
            "       List.append_nil])"),
        "rationale": "correct impl with the loop direction REVERSED (forward, appending "
                     "each group's slice, under the mirror `groups.take i` invariant). "
                     "Because `slicedGroups` is front-recursive this cannot reuse the "
                     "frozen backward drop-step: the proof is retuned with an inline "
                     "append-split lemma plus the `take (i+1)` split. That makes it the "
                     "one positive here that reshapes CONTROL FLOW rather than just the "
                     "expression, so it is the real SPEC-TOO-STRONG probe — if the "
                     "postcondition were over-fit to the backward fold this would fail. "
                     "Built by the audit: EXIT 0 (verifies).",
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling self-calls on the F2P-shaped input to
    # show the modeled behaviour is ADMITTED. This bundle has NO `require` clause
    # (nothing can be PRECOND-TOO-STRONG), so the probe is re-aimed at the
    # residual admissibility risk on a transparent carrier: that the modeled
    # behaviour is DEGENERATE, i.e. does not actually demand PER-GROUP slicing.
    # An in-region assert pins that on two independent groups an offset ([1:])
    # slices EACH group on its own (dropping the leading row of BOTH), which is
    # the exact behaviour the F2P tests demand and the precise place the global-
    # slice prepatch fails. The assert is LIVE (replacing the claimed result with
    # a wrong value leaves an unsolved goal — verified out-of-band); the frozen
    # loop body follows it so the method's own `ensures` obligation still
    # discharges. The proof is retuned only to also close the added assert goal.
    # =====================================================================
    {
        "id": "admiss-f2p-pergroup",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_TOP,
                  "    assert (with_name_prefix `admiss\n"
                  "      (slicedGroups 1 none [[10, 11], [20, 21]] = [11, 21]))\n"
                  + _IMPL_TOP),
            _PROOF,
            "prove_correct perGroupSlice by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | rfl\n"
            "    | (rw [slicedGroups_drop_step low high groups i (by omega) "
            "(by omega)]; simp_all)"),
        "rationale": "the F2P headline configuration (an offset [1:] over TWO "
                     "independent ordered groups) slices EACH group on its own, "
                     "dropping the leading row of BOTH — the exact per-group behaviour "
                     "`book.authors_sliced == list(...)[1:]` exercises and the precise "
                     "place the global-slice prepatch fails. The frozen loop keeps the "
                     "ensures obligation intact, so the module verifies; this witnesses "
                     "the spec ADMITS the modeled F2P behaviour rather than being "
                     "vacuous or over-strong. LIVENESS re-measured by the audit: the "
                     "assert really is emitted as a proof goal — rebuilding this exact "
                     "case with the claimed result falsified to [11, 20] FAILS (EXIT 1), "
                     "because `rfl` cannot close the false assert goal and the fallback "
                     "branch then errors on the loop-only binder (`Unknown identifier "
                     "i`); a standalone `decide` confirms the claimed value is the true "
                     "one and the falsified one is false (EXIT 0). Independently, "
                     "`groupSlice 1 none (flatten [[10,11],[20,21]]) ≠ slicedGroups 1 "
                     "none [[10,11],[20,21]]` by `decide` (EXIT 0), so this input really "
                     "does separate per-group from global slicing. Built: verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is a
    # STRAIGHT-LINE wrong impl (so its extracted program reduces under `decide`,
    # letting the tester witness name the counterexample); it stays wrong for a
    # VALUE reason, not a shape reason. All builds recorded below.
    # =====================================================================
    {
        "id": "weak-global-slice",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: apply the offset/stop as a SINGLE slice over the
        # combined (flattened) row-set instead of per group. Correct on inputs
        # with 0/1 group; WRONG whenever ≥2 groups meet a nontrivial slice.
        "module": _rival("groupSlice low high groups.flatten"),
        "refinement": "this IS the pre-patch skeleton: a single global slice of all "
                      "related rows rather than an independent slice PER group (the "
                      "exact `AssertionError: Cannot filter a query once a slice has "
                      "been taken` behaviour the issue reports, whose faithful fix is "
                      "the per-partition window). Its faithful real patch is the "
                      "UNPATCHED global-slice path, under which each instance's "
                      "sliced attribute collects the wrong rows (the combined slice, "
                      "not that group's own slice), so every F2P assertion "
                      "`book.authors_sliced == list(...)[1:]` FAILS. A verifying rival "
                      "here would be a true verify-does-not-resolve break.",
        "rationale": "REJECT from (C1): on two singleton groups under a [0:1] slice, "
                     "`slicedGroups` keeps each group's position 0 (=[1,2]) but the "
                     "rival keeps only position 0 of the COMBINED sequence (=[1]). "
                     "Refuted at exactly the multi-group sub-domain (groups=[[1],[2]]) "
                     "where per-group and global slicing diverge. Value-level check: "
                     "`groupSlice 0 (some 1) (flatten [[1],[2]]) ≠ slicedGroups 0 "
                     "(some 1) [[1],[2]]` by `decide` (EXIT 0), so the rival is WRONG "
                     "here, not merely reshaped. Witness SEEN to discriminate: rival "
                     "EXIT 0; `_POS_DIRECT` EXIT 1 with `decide proved ... = false is "
                     "false` (a semantic refutation); frozen solution EXIT 1 by stuck "
                     "reduction, which attributes nothing and is why the case carries "
                     "an explicit witness_reference.",
        "witness": _witness("[[1], [2]] 0 (some 1)"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-drop-lower-open",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the OFFSET when the stop is open-ended: an open [k:] slice is
        # treated as [0:]. Correct whenever a finite stop is present or the offset
        # is 0; WRONG on the exact F2P `[1:]` shape (offset, open stop).
        "module": _rival(
            "match high with "
            "| none => slicedGroups 0 none groups "
            "| some h => slicedGroups low (some h) groups"),
        "refinement": "on an open-ended slice this forgets the lower offset (keeps "
                      "from position 0). The F2P tests slice with `[1:]` (offset 1, "
                      "no stop): test_m2m_forward/test_foreignkey_reverse/"
                      "test_reverse_ordering. Its faithful real patch would omit the "
                      "`GreaterThan(window, low_mark)` lower bound whenever high_mark "
                      "is None, so each group returns rows from position 0 and "
                      "`book.authors_sliced != list(...)[1:]` — does NOT resolve.",
        "rationale": "REJECT from (C1): on groups=[[1,2]], low=1, high=none "
                     "`slicedGroups` keeps [2] but the rival keeps [1,2]. Refuted at "
                     "the open-ended offset sub-domain (the exact F2P slice shape), "
                     "varying `low`=1 against the low=0 witnesses and `high`=none. "
                     "Value-level check: `slicedGroups 0 none [[1,2]] ≠ slicedGroups 1 "
                     "none [[1,2]]` by `decide` (EXIT 0). Witness SEEN to discriminate: "
                     "rival EXIT 0; `_POS_DIRECT` EXIT 1 with `decide proved ... is "
                     "false` (semantic); frozen solution EXIT 1 by stuck reduction "
                     "(attributes nothing — hence the witness_reference).",
        "witness": _witness("[[1, 2]] 1 none"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-ignore-stop",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores a finite stop entirely (treats every high as open-ended).
        # Correct whenever the stop is None or would not truncate; WRONG whenever
        # a finite stop truncates a group.
        "module": _rival("slicedGroups low none groups"),
        "refinement": "drops the finite-stop clause — an explicit `[:h]`/`[low:h]` "
                      "stop is never applied. Its faithful real patch would omit the "
                      "`LessThanOrEqual(window, high_mark)` upper bound, so a bounded "
                      "slice (e.g. `books[1:2]`, test_m2m_reverse) returns every row "
                      "from the offset onward instead of just the window, and "
                      "`author.books_sliced != list(...)[1:2]` — does NOT resolve.",
        "rationale": "REJECT from (C1): on groups=[[1,2]], low=0, high=some 1 "
                     "`slicedGroups` keeps [1] but the rival (open stop) keeps [1,2]. "
                     "Refuted at a finite-stop point, varying `high`=some 1 against "
                     "the open-stop witnesses. Value-level check: `slicedGroups 0 none "
                     "[[1,2]] ≠ slicedGroups 0 (some 1) [[1,2]]` by `decide` (EXIT 0). "
                     "Witness SEEN to discriminate: rival EXIT 0; `_POS_DIRECT` EXIT 1 "
                     "with `decide proved ... is false` (semantic); frozen solution "
                     "EXIT 1 by stuck reduction (attributes nothing — hence the "
                     "witness_reference).",
        "witness": _witness("[[1, 2]] 0 (some 1)"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-spurious-stop",
        "kind": "uniqueness",
        "expect": "reject",
        # Imposes a spurious finite stop on an OPEN-ended slice (stop := offset).
        # Correct whenever a finite stop is already present; WRONG on any open
        # slice with a nonzero offset (drops rows [1:] would keep).
        "module": _rival(
            "match high with "
            "| none => slicedGroups low (some low) groups "
            "| some h => slicedGroups low (some h) groups"),
        "refinement": "imposes a spurious finite upper bound on an unbounded `[low:]` "
                      "slice. Its faithful real patch would AND a "
                      "`LessThanOrEqual(window, …)` bound even when high_mark is None, "
                      "so an open-ended `[1:]` prefetch drops rows it should keep and "
                      "`book.authors_sliced != list(...)[1:]` (the F2P `[1:]` tests) — "
                      "does NOT resolve.",
        "rationale": "REJECT from (C1): on groups=[[1,2,3]], low=1, high=none "
                     "`slicedGroups` keeps [2,3] but the rival (stop:=1) keeps []. "
                     "Refuted at an open-ended offset over a length-3 group — a point "
                     "the other witnesses do not probe (varies `groups` to a single "
                     "length-3 group). Value-level check: `slicedGroups 1 (some 1) "
                     "[[1,2,3]] ≠ slicedGroups 1 none [[1,2,3]]` by `decide` (EXIT 0). "
                     "Witness SEEN to discriminate: rival EXIT 0; `_POS_DIRECT` EXIT 1 "
                     "with `decide proved ... is false` (semantic); frozen solution "
                     "EXIT 1 by stuck reduction (attributes nothing — hence the "
                     "witness_reference).",
        "witness": _witness("[[1, 2, 3]] 1 none"),
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "weak-vacuous",
        "kind": "uniqueness",
        "expect": "reject",
        # Vacuous near-miss: return the rows untouched (no slicing at all).
        # Correct only on inputs the slice would not change (low=0, open stop);
        # WRONG on any nontrivial slice. Cheap supporting case.
        "module": _rival("groups.flatten"),
        "refinement": "returns the related rows untouched — no per-group slice, no "
                      "offset, no stop. Its faithful real patch leaves the queryset "
                      "unfiltered by any window, so every sliced-prefetch attribute "
                      "gets ALL related rows and no F2P slice assertion holds — does "
                      "NOT resolve. (Cheap supporting near-miss.)",
        "rationale": "REJECT from (C1): on groups=[[1],[2]], low=1, high=none "
                     "`slicedGroups` keeps [] (each singleton group drops its only "
                     "row) but the rival returns [1,2]. Refuted at a two-group offset "
                     "point distinct from every other witness. Value-level check: "
                     "`flatten [[1],[2]] ≠ slicedGroups 1 none [[1],[2]]` by `decide` "
                     "(EXIT 0). Witness SEEN to discriminate: rival EXIT 0; "
                     "`_POS_DIRECT` EXIT 1 with `decide proved ... is false` "
                     "(semantic); frozen solution EXIT 1 by stuck reduction (attributes "
                     "nothing — hence the witness_reference). Supporting case; the "
                     "reasoned attacks above carry the lane.",
        "witness": _witness("[[1], [2]] 1 none"),
        "witness_reference": _POS_DIRECT,
    },

    # =====================================================================
    # ADDED BY AUDIT (uniqueness) — the BOUNDED-window corner none of the five
    # ported rivals attacks. Every shipped rival is refuted at a point where
    # either `low = 0` or `high = none`; the sub-domain where an offset and a
    # finite stop are BOTH present (the `[low:h]` shape, e.g. `books[1:2]`) was
    # unprobed, and a rival can be wrong there while agreeing with (C1) at all
    # five shipped witness points. This one reads the stop as a per-group COUNT
    # (`take h` after the offset) instead of as a stop POSITION (`take (h-low)`),
    # i.e. it keeps `[low, low+h)` rather than `[low, h)`. Machine-checked to
    # agree with `slicedGroups` at each of the five shipped points (`decide`,
    # EXIT 0 on all five), so it survives the whole ported battery — which is
    # what makes it a real gap rather than a duplicate.
    # =====================================================================
    {
        "id": "weak-stop-as-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "groups.flatMap (fun g => (g.drop low).take (high.getD g.length))"),
        "refinement": "reads a finite stop as a per-group COUNT taken AFTER the offset "
                      "rather than as a stop POSITION measured from the group's start, "
                      "so a bounded window keeps `[low, low+h)` instead of `[low, h)`. "
                      "Its faithful real patch would compare the per-partition position "
                      "against a bound offset by the start mark instead of against the "
                      "stop mark itself, so a bounded slice such as `books[1:2]` "
                      "(test_m2m_reverse) returns more rows than the window admits and "
                      "`author.books_sliced != list(...)[1:2]` — does NOT resolve. It is "
                      "exactly right on every open-ended slice and on every slice with "
                      "offset 0, which is why the ported rivals miss it.",
        "rationale": "REJECT from (C1): on groups=[[1,2,3]], low=1, high=some 2 "
                     "`slicedGroups` keeps [2] (positions [1,2)) but the rival keeps "
                     "[2,3] (two rows from position 1). Value-level check by `decide` "
                     "(EXIT 0), and the rival AGREES with `slicedGroups` at all five "
                     "other witness points (five `decide` equalities, EXIT 0), so this "
                     "case is refuted at a genuinely new point: the first with `low > 0` "
                     "AND `high = some h` together. Witness SEEN to discriminate: rival "
                     "EXIT 0; `_POS_DIRECT` EXIT 1 with `decide proved ... is false` "
                     "(semantic); frozen solution EXIT 1 by stuck reduction (attributes "
                     "nothing — hence the witness_reference).",
        "witness": _witness("[[1, 2, 3]] 1 (some 2)"),
        "witness_reference": _POS_DIRECT,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives + 1 admissibility + 7 uniqueness rivals) and 2 AXIOM_TESTS. This
# velvet bundle models a NARROWER surface than nagini's: nagini contracts the
# whole `bounded_prefetch` state machine (the un-slice/clear step, the forgeable
# `membership_applied` flag, and the UNFORGEABLE `membership_token` capability),
# whereas this bundle models only the purely-functional net effect the patch
# actually changes — the per-group row-set `slicedGroups low high groups` over a
# `List (List Int)` carrier (mapping.md §1-3). The membership predicate itself is
# the UNCHANGED, shared part of the call and is not on the modeled surface.
#
#   nagini case                 -> here
#   ------------------------------------------------------------------------
#   pos-reorder-clear-first     -> (subsumed by pos-direct)      OMITTED (below)
#   pos-reorder-writes          -> pos-localvar                  PORTED (re-shaped)
#   admiss-sliced-input         -> admiss-f2p-pergroup           PORTED (re-aimed)
#   atk-echo-sliced   (A)       -> (none)                        UNMODELLED behaviour
#   atk-echo-after-clear (B)    -> (none)                        UNMODELLED behaviour
#   atk-drop-lower-offset-only(C)-> weak-drop-lower-open         PORTED
#   atk-no-clear      (D)       -> (none)                        UNMODELLED behaviour
#   atk-swap-bounds   (E)       -> weak-ignore-stop + weak-spurious-stop  RE-EXPRESSED
#   atk-upper-always  (F)       -> weak-spurious-stop            PORTED
#   atk-vacuous       (G)       -> weak-vacuous                  PORTED
#   (added)                     -> weak-global-slice             ADDED (the bug itself)
#   (added)                     -> pos-direct                    ADDED (grounded control)
#   (added by AUDIT)            -> weak-stop-as-count            ADDED (bounded-window gap)
#   (added by AUDIT)            -> pos-forward-loop              ADDED (control-flow reshape)
#   AXIOM_TESTS (2)             -> (dropped)                     AXIOM LANE
#
# ADDED (weak-global-slice): the sibling has no single "global-vs-per-group" rival
#   because its carrier splits the change into an un-slice step + a membership
#   step. Here the whole change IS "per group, not globally", and the prepatch
#   skeleton (`groupSlice low high groups.flatten`) is exactly that global slice —
#   so this is the headline value rival and the literal prepatch failure (G-DIFF).
# ADDED (pos-direct): clause (C1) IS `out = slicedGroups …` over a total grounded
#   function, so the cheapest honest impl (return it) is a legitimate soundness
#   positive and the grounded-oracle control (any WRONG value fails (C1)). The
#   sibling's pos-reorder-clear-first is a reorder of the nagini un-slice/record
#   mutation sequence, which this carrier folds entirely into `slicedGroups`,
#   leaving no distinct executable shape to reorder; it is OMITTED as having no
#   distinct counterpart (NOT because a proof would not close). pos-reorder-writes
#   (reorder the two bound WRITES) maps to pos-localvar's hoist-into-a-local, the
#   only order-independent executable reshape this carrier admits.
# PORTED (pos-localvar): builds with the frozen proof (backward loop + drop-step);
#   only the executable shape (a named local) differs.
# PORTED (admissibility, re-aimed): no `require` clause here, so nothing can be
#   PRECOND-TOO-STRONG; the argument is carried by an in-region live assert that an
#   offset over TWO groups slices EACH on its own (the F2P per-group behaviour).
# UNMODELLED (atk-echo-sliced, atk-echo-after-clear, atk-no-clear): these attack
#   the membership-token capability and the un-slice/clear state machine, which are
#   NOT on this bundle's modeled surface — the carrier holds no is_sliced state, no
#   membership flag and no token. There is no input the modeled behaviour
#   distinguishes on which such a rival is wrong, so no discriminating witness
#   exists; these are honestly omitted as attached to unmodeled behaviour, not
#   replaced with a fabricated substitute.
# PORTED (atk-drop-lower-offset-only -> weak-drop-lower-open): the offset-only
#   [1:] sub-domain — the exact F2P slice shape — where a rival that forgets the
#   lower offset on an open-ended slice diverges from gold. Refuted at [[1,2]] 1 none.
# RE-EXPRESSED (atk-swap-bounds -> weak-ignore-stop + weak-spurious-stop): nagini's
#   swap corrupts the two nagini bound VALUES (lower<-stop, upper<-offset). This
#   carrier has no separate lower/upper mark fields — the slice is a single
#   `groupSlice low high` — so the value-of-the-bounds corruption is re-expressed
#   as the two independent facets it can actually break: honoring the finite stop
#   (weak-ignore-stop) and NOT inventing a stop on an open slice (weak-spurious-
#   stop). Together they cover the same "wrong bound value" surface faithfully.
# PORTED (atk-upper-always -> weak-spurious-stop): a spurious finite upper bound on
#   an open-ended [1:] slice; refuted at [[1,2,3]] 1 none.
# PORTED (atk-vacuous -> weak-vacuous): return the rows untouched; refuted at
#   [[1],[2]] 1 none.
# FRAME / PERMISSION-MUTATION: referentially-transparent backend, no `mut`
#   parameter, no heap, no fractional permission — vacuous. Not fabricated.
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
# PORTED (the value rivals): each carries a machine-checked witness that ELABORATES
#   against the (straight-line) rival and is REFUTED against `_POS_DIRECT`, the
#   verifying straight-line impl of this same frozen spec named as each case's
#   `witness_reference`. The six witnesses probe six distinct points that together
#   vary all three input binders — two groups vs one, `low` in {0,1}, `high` in
#   {none, some 1, some 2}, group lengths 1/2/3 — so every binder of the spec
#   predicate is varied and no rival is refuted at the same point as another
#   (pts = 6).
# AUDIT CORRECTION (witness subject). An earlier revision of this file claimed each
#   witness "FAILS against the frozen looped solution" and read that failure as
#   discrimination. Re-measured: gold's build does fail, but with
#   `decide ... did not reduce to isTrue or isFalse` — the kernel never evaluates
#   the claim, so the same error appears for a TRUE claim about gold and the exit
#   code attributes nothing (the frozen impl's `Exec` goes through the loop's
#   irreducible `wp`). The repair is the explicit `witness_reference` now on every
#   reject case: `_POS_DIRECT` shares the frozen spec, VERIFIES (so it cannot
#   violate (C1) anywhere), and REDUCES — against it each witness fails with
#   `decide proved that the proposition ... is false`, a semantic refutation of the
#   concrete claim. Three builds per case were run and their exit codes are
#   recorded in each case's `rationale`.
# AUDIT ADDITION (weak-stop-as-count): every ported rival is refuted at a point with
#   `low = 0` or `high = none`, leaving the BOUNDED-window sub-domain (`[low:h]`,
#   both marks present) unattacked. A rival reading the stop as a per-group count
#   after the offset agrees with (C1) at all five ported witness points (five
#   `decide` equalities, EXIT 0) and is wrong at [[1,2,3]] 1 (some 2). It does NOT
#   verify against the frozen spec, so this was a battery coverage gap, not a spec
#   hole.
# AUDIT ADDITION (pos-forward-loop): the soundness direction was probed only by
#   straight-line and cosmetic reshapes (pos-localvar keeps the backward loop and
#   every invariant verbatim), so nothing tested whether the postcondition tolerates
#   a different CONTROL FLOW. The forward loop cannot reuse the frozen drop-step
#   against the front-recursive `slicedGroups` and needs its own append-split
#   argument; it verifies (EXIT 0), so the spec is not over-fit to the fold
#   direction.
# AUDIT PROBES that found nothing (recorded so the negative result is not re-derived):
#   wrong impls that all FAIL as they must — reversed group order
#   (`slicedGroups low high groups.reverse`), reversed intra-group order, stop
#   off-by-one (`high.map (·+1)`), stop read as `low + h`, the complement
#   (`g.take low`), a `.dedup` of the correct answer, and `low` applied per group
#   with `high` applied globally. Correct reshapes that VERIFY — `groups.flatMap
#   (groupSlice low high)`, the take-then-drop spelling
#   (`(g.take (high.getD g.length)).drop low`), and dropping empty groups before
#   slicing (`groups.filter (· != [])`) — so the spec admits reshapes of the pure
#   expression as well as of the loop.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the transformation is modeled deeply by groupSlice/slicedGroups;
# mapping.md §3 records no axiom_check.py), so there is nothing to probe.
AXIOM_TESTS = []
