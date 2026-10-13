"""properties.py — G-PBT falsification battery for sympy__sympy-24213 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant sharing the FROZEN spec byte-for-byte: only text
inside ``-- impl-start``/``-- impl-end`` — and, for a case that legitimately
re-proves, inside ``-- proof-start``/``-- proof-end`` — is changed, so
``markers.same_spec`` holds and the single ``theorem
correct_factorAndDimensionOfSum`` STATEMENT stays byte-identical.
``expect:"verify"`` passes iff the file elaborates with the obligation closed
(no ``sorry``/``admit``/``native_decide``, no new ``axiom``/``theorem``);
``expect:"reject"`` passes iff it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the addend walk imperatively over two parallel read-only ``List[int]``
facets — a surface facet and a reduction facet — under fractional permissions
and a ``MustTerminate`` obligation, and splits the outcome across a value
``Ensures`` and an exceptional ``Exsures``. This Lean bundle models the SAME
single purely-functional core: the two facets are the two fields of one ``Dim``
record, the outcome is an ``Option``, and the walk is a total ``for`` loop over
one ``List (Rat × Dim)``. Every nagini case that attacks the modeled behavior
carries over; the permission and termination classes do not exist on this
carrier and are accounted for below.

DEFENDED SURFACE (one modeled behavior, one obligation).
``problem_spec_factorAndDimensionOfSum head addends result`` pins ``result``
to a single conditional, whose two arms are the two independent top-level
clauses:

  * (C-accept) when ``allDimsMatch head addends`` — every addend's canonical
    base-dimension power map equals the head's — the result is
    ``some (summedFactor head addends, head.2)``: the head's factor plus the
    sum of every addend's factor, paired with the HEAD's dimension carried
    through unchanged (both components pinned, so neither is free);
  * (C-reject) when some addend's power map differs from the head's, the result
    is ``none`` — no result at all.

The BEHAVIOURAL DISCRIMINATOR (what the fix is about): the accept/reject
decision is made on the canonical base-dimension POWER MAP (``Dim.deps``),
never on the surface symbolic identity (``Dim.name``). Two addends written with
different surface identities but the same power map must be ACCEPTED. The
pre-fix behavior decided on the surface identity; ``weak-surface-identity``
below IS that behavior, and it is the central uniqueness attack (it ports
nagini's ``rival-surface-identity-guard``). ``allDimsMatch`` is stated over
``deps`` only, so the spec never lets ``name`` influence the outcome — and a
rival that reads ``name`` is refutable at any input whose two facets disagree.
The clause is attacked in BOTH directions: ``weak-surface-identity`` reads
``name`` as the restrictive test (refusing a compatible sum), and
``weak-name-also-accepts`` reads it as an alternative ground for acceptance
(admitting an incompatible one).

BINDER STRUCTURE. The spec predicate has TWO input binders: ``head : Rat × Dim``
and ``addends : List (Rat × Dim)``. Both are load-bearing on both components:
``head`` contributes its factor to the accept-arm total AND supplies both the
reference power map and the carried-through dimension; ``addends`` contributes
every addend factor AND every power map compared. All four sub-components are
varied across the eight reject witnesses (point spread at the bottom):
``addends`` ranges over the empty list, a one-element list and a two-element
list; ``head``'s dimension ranges over four distinct ``(name, deps)`` pairs —
including a same-name/different-map pair, the mirror of the discriminating one;
head and addend factors take several distinct values; and the witnesses split
between the accept arm and the reject arm, so no binder and no arm is held
fixed. The eight reject witnesses probe eight DISTINCT input tuples.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes this class
    MANDATORY: both of its input facets are held at half permission, so a rival
    that overwrites one entry to force the accept clause vacuously is rejected
    for insufficient permission rather than for any value reason (its
    ``frame-mutation-overwrite-red`` / ``-surf`` pair). Lean is referentially
    transparent: ``head`` and ``addends`` are immutable values, there is no
    ``mut`` input binder, no aliasing, and no cell to overwrite — an impl
    CANNOT express the attack. No substitute probe is fabricated (porting map:
    vacuous here).

  * DIVERGENCE / NON-TERMINATION — PORTED (was wrongly recorded vacuous; see
    the AUDIT NOTE below). The nagini sibling carries
    ``rival-vacuous-nonterminating-loop``, a spinning impl that satisfies every
    value clause vacuously and is caught only by the termination obligation.
    The class is NOT vacuous here. An unbounded ``while true do`` inside the
    impl's ``Id.run do`` block elaborates perfectly well — the loop's ``ForIn``
    instance is opaque rather than rejected — so a diverging impl IS writable,
    it declares nothing new, and it satisfies the frozen obligation's
    STATEMENT. It is caught because the resulting output term does not depend on
    ``addends`` at all, which the spec forbids: the spec's answer at the empty
    addend list is an accept and its answer at an incompatible addend is
    ``none``, and one term cannot be both. ``weak-divergent-loop`` below IS that
    rival, with a witness that refutes it WITHOUT evaluating the opaque loop
    (it derives the contradiction from the two spec instances alone).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: both
    output components are pinned by arithmetic and structural relations on the
    actual inputs (a sum of the input factors; the head's own dimension; the
    arm chosen by an ``all`` over the input power maps). There is no opaque
    answer key to echo, and no ``opaque``/``axiom`` callee anywhere in the
    bundle — so no witness needs to condition on the carrier, and every witness
    below binds NOTHING in its head. There are therefore no hypotheses whose
    joint satisfiability could be in question.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole battery lives:
    rivals correct on part of the domain and wrong exactly where a clause
    bites. Deciding on the surface identity instead of the power map; skipping
    the first compared addend; never rejecting at all; dropping the accumulated
    factor total; replacing the carried dimension with a constant; and
    advancing the reference to the most recent addend.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet. Seven of the eight compute the rival's
concrete output by ``rfl`` in a ``have himpl`` (the ``Id.run do`` / ``for`` loop
reduces by whnf at ground inputs), rewrite the spec at that value, and close by
``simp`` on the two spec helpers; on gold each fails by plain EVALUATION, the
error naming the frozen impl's actual output at that input. The eighth
(``weak-divergent-loop``) cannot evaluate its rival at all — an unbounded loop
is an opaque term the kernel will not unfold, and a stuck ``rfl`` would
discriminate nothing — so it uses ``_witness_no_eval``, which derives the
contradiction from two spec instances without reducing the loop. Each witness
was checked with two real ``lake env lean`` builds — HOLDS of its rival, FAILS
on the frozen solution — and additionally with a FLIPPED-claim build (assert the
opposite of the witness against gold): every flip elaborates where the witness
failed, so each gold-side exit code tracks the claim rather than the shape.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve
break). Each reject case's ``refinement`` argues that its faithful real
counterpart would either reject a sum whose addends are physically compatible
but differently written (the reported defect, which the F2P case asserts must
go through), accept a sum whose addends are genuinely incompatible (which the
existing consistency tests assert must be refused), or hand back the wrong
``(factor, dimension)`` pair for an accepted sum (which the existing
factor/dimension tests pin exactly) — so the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes
no ``axiom`` — the changed comparison is modeled deeply as power-map equality —
so the nagini ``AXIOM_TESTS`` are dropped (the axiom lane is G-AX's job and
this gate ignores them regardless).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24213"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each is unique inside Solution.lean (asserted by _swap at
# import time, so the manifest breaks loudly if the frozen solution changes)
# and lies ENTIRELY inside the region it edits.
# ---------------------------------------------------------------------------
# --- impl region ---
_I_HEADER = "  let dim := head.2\n  let mut factor := head.1"   # the two prologue lets
_I_FOR = "  for a in addends do"                                # the walk
_I_GUARD = "    if dim.deps ≠ a.2.deps then"                    # the compat test
_I_ACC = "    factor := factor + a.1"                           # the factor accumulation
_I_RET = "  return some (factor, dim)"                          # the accept-arm result

# The WHOLE impl body, for rivals that restructure the loop rather than edit one
# line of it. Assembled from the anchors above so a drift in any single line is
# caught by the same assertion.
_I_ALL = (_I_HEADER + "\n" + _I_FOR + "\n" + _I_GUARD
          + "\n      return none\n" + _I_ACC + "\n" + _I_RET)

# --- proof region ---
# The frozen proof's mismatch branch: `if_pos h` fires the impl's `≠` guard,
# `if_neg …` kills the spec's accept arm. A positive that reshapes the guard has
# to re-state only the first `rw`, so the re-proof stays one token from frozen.
_P_NEG_BRANCH = """    · rw [if_pos h, if_neg (by
        simp only [Bool.and_eq_true, decide_eq_true_eq, not_and]
        intro hcon _; exact absurd hcon.symm h)]
      rfl"""

# The frozen proof's opening `simp only`, used as the prepend point for the
# admissibility positive's ground `have`. Inside the proof region.
_P_OPEN = ("  simp only [problem_spec_factorAndDimensionOfSum, "
           "implementation_factorAndDimensionOfSum,")

# ---------------------------------------------------------------------------
# Dimension literals used by the witnesses. `dV`/`dAT` are the discriminating
# pair: DISTINCT surface identities, IDENTICAL canonical power maps (the shape
# the reported defect turns on — physically the same dimension written two
# ways). `dM`/`dMA` are a second such pair over a different power map, and
# `dOne` is the empty (dimensionless) map. Every literal is a ground `Dim`
# record, so every witness reduces by `rfl`/`decide` and binds nothing.
# ---------------------------------------------------------------------------
_dV = '{ name := "sV", deps := [("length", 1), ("time", -1)] }'
_dAT = '{ name := "sAT", deps := [("length", 1), ("time", -1)] }'
_dM = '{ name := "sM", deps := [("mass", 1)] }'
_dMA = '{ name := "sMA", deps := [("mass", 1)] }'
_dOne = '{ name := "sOne", deps := [] }'


def _witness_no_eval(headA, addendsA, headB, addendsB):
    """Refute the spec WITHOUT evaluating the rival's output term.

    For a rival whose output does not reduce (an unbounded loop elaborates to an
    opaque `ForIn` term the kernel cannot unfold), `_witness`'s `rfl` is stuck,
    and a stuck build discriminates nothing — the same error appears for a TRUE
    claim. This shape avoids evaluation entirely: it asserts that the spec
    cannot hold at BOTH of two inputs at once, given only that the rival's
    output is the SAME term at both (which `rfl` sees syntactically, without
    reducing the loop). The spec's own answers at the two inputs differ — one is
    an accept, the other is `none` — so no single value satisfies both, and the
    contradiction follows from the spec alone.

    Gold FAILS this: its outputs at the two inputs are genuinely different
    terms, so the `hsame` step is refuted on the merits (the error names the two
    unequal `implementation_…` applications). The flipped claim — asserting the
    conjunction rather than its negation — BUILDS on gold and FAILS on the
    rival, so the exit codes track the claim rather than the reduction.

    Nothing is bound in either head, so there are no hypotheses at all.
    """
    return (
        f"example : ¬ (problem_spec_factorAndDimensionOfSum {headA} {addendsA}\n"
        f"      (implementation_factorAndDimensionOfSum {headA} {addendsA})\n"
        f"    ∧ problem_spec_factorAndDimensionOfSum {headB} {addendsB}\n"
        f"      (implementation_factorAndDimensionOfSum {headB} {addendsB})) := by\n"
        f"  rintro ⟨h1, h2⟩\n"
        f"  have hsame : implementation_factorAndDimensionOfSum {headA} {addendsA}\n"
        f"      = implementation_factorAndDimensionOfSum {headB} {addendsB} := by rfl\n"
        f"  unfold problem_spec_factorAndDimensionOfSum at h1 h2\n"
        f"  rw [hsame] at h1\n"
        f"  rw [h2] at h1\n"
        f"  simp [allDimsMatch, summedFactor] at h1\n")


def _witness(head, addends, value):
    """Refute the spec at one ground input.

    `himpl` computes the rival's actual output by `rfl` (ground inputs, so the
    `Id.run do` loop reduces by whnf); the spec is then unfolded at that value
    and `simp` on the two spec helpers (`allDimsMatch` decides the arm,
    `summedFactor` the factor total) closes the negation. Nothing is bound in
    the head, so there are no assumptions at all — the input is exhibited, not
    described.
    """
    return (
        f"example : ¬ problem_spec_factorAndDimensionOfSum\n"
        f"    {head} {addends}\n"
        f"    (implementation_factorAndDimensionOfSum {head} {addends}) := by\n"
        f"  have himpl : implementation_factorAndDimensionOfSum {head} {addends}\n"
        f"      = {value} := by rfl\n"
        f"  unfold problem_spec_factorAndDimensionOfSum\n"
        f"  rw [himpl]\n"
        f"  simp [allDimsMatch, summedFactor]\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_factorAndDimensionOfSum` statement byte-identical and
    # introduces no new declaration. All three were checked with a real build.
    # =====================================================================
    {
        "id": "pos-inline-reference",
        "kind": "soundness",
        "expect": "verify",
        # Drop the `let dim` prologue binding and read the reference dimension
        # off `head` at both use sites (the comparison and the carried-through
        # result). Definitionally the frozen body, so the frozen proof closes
        # unchanged — no proof authoring, no helper lemma, no assumption token.
        "module": _swaps(
            _BASE,
            (_I_HEADER, "  let mut factor := head.1"),
            (_I_GUARD, "    if head.2.deps ≠ a.2.deps then"),
            (_I_RET, "  return some (factor, head.2)"),
        ),
        "rationale": "correct reshape that eliminates the reference-dimension "
                     "prologue binding and reads it off the head pair at both "
                     "use sites. It computes the same arm and the same "
                     "(factor, dimension) pair on every input, so C-accept and "
                     "C-reject both still hold — else SPEC-TOO-STRONG. "
                     "Definitionally the frozen body, so the frozen proof "
                     "closes unchanged; statement byte-identical, no new "
                     "axiom/lemma. Ports nagini's pos-control-local-ref (there "
                     "a local snapshot of the reference is INTRODUCED and has "
                     "to be re-pinned as a loop invariant; on this carrier the "
                     "snapshot is what the frozen impl already does, so the "
                     "structurally different correct shape is its removal).",
    },
    {
        "id": "pos-symmetric-guard",
        "kind": "soundness",
        "expect": "verify",
        # The compatibility test with its two sides EXCHANGED. Power-map
        # equality is symmetric, so this decides identically; only the
        # syntactic form of the guard changes. Re-proved by symmetrizing the
        # single `if_pos` that fires that guard in the mismatch branch — the
        # rest of the frozen script is untouched.
        "module": _swaps(
            _BASE,
            (_I_GUARD, "    if a.2.deps ≠ dim.deps then"),
            (_P_NEG_BRANCH, """    · rw [if_pos (Ne.symm h), if_neg (by
        simp only [Bool.and_eq_true, decide_eq_true_eq, not_and]
        intro hcon _; exact absurd hcon.symm h)]
      rfl"""),
        ),
        "rationale": "the addend/head compatibility test with its two sides "
                     "exchanged. Power-map equality is symmetric, so the same "
                     "arm is chosen on every input and both clauses still hold "
                     "— a faithful reshape MUST verify, else SPEC-TOO-STRONG. "
                     "Re-proved by symmetrizing the one `if_pos` that fires "
                     "the reshaped guard (statement byte-identical, no new "
                     "axiom/lemma). Ports nagini's "
                     "pos-control-symmetric-guard.",
    },
    {
        "id": "pos-positive-guard",
        "kind": "soundness",
        "expect": "verify",
        # Control-flow REORDER: test compatibility POSITIVELY and put the
        # accumulation in the then-branch, the no-result exit in the else. Same
        # decision, different branch shape. Re-proved by turning the mismatch
        # branch's `if_pos` into an `if_neg` on the same hypothesis.
        "module": _swaps(
            _BASE,
            (_I_GUARD + "\n      return none\n" + _I_ACC,
             "    if dim.deps = a.2.deps then\n"
             "      factor := factor + a.1\n"
             "    else\n"
             "      return none"),
            (_P_NEG_BRANCH, """    · rw [if_neg h, if_neg (by
        simp only [Bool.and_eq_true, decide_eq_true_eq, not_and]
        intro hcon _; exact absurd hcon.symm h)]
      rfl"""),
        ),
        "rationale": "branch-REORDER positive control: the compatibility test "
                     "is written positively with the accumulation in the "
                     "then-branch and the no-result exit in the else — "
                     "identical decision, different control flow. Must verify, "
                     "else SPEC-TOO-STRONG. Re-proved by flipping the one "
                     "`if_pos` to `if_neg` on the same hypothesis (statement "
                     "byte-identical, no new axiom/lemma). No nagini "
                     "counterpart; ADDED as a second independent shape for the "
                     "obligation's defended side.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input, i.e. that the modeled behavior does not have an
    # empty in-domain accept arm. The frozen theorem carries NO precondition
    # hypotheses, so nagini's precondition-establishment call site has no
    # counterpart; the honest analogue is to discharge the spec predicate by
    # evaluation at the smallest F2P-shaped input as a `have`, then close the
    # frozen obligation verbatim. Nothing is assumed: no new declaration, the
    # ground instance is a `have` prepended to the existing tactic body, and
    # the statement is byte-identical. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground-equivalent-pair",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_OPEN,
            f"  have _ground : problem_spec_factorAndDimensionOfSum "
            f"(1, {_dAT}) [(1, {_dV})]\n"
            f"      (implementation_factorAndDimensionOfSum "
            f"(1, {_dAT}) [(1, {_dV})]) := by\n"
            f"    have himpl : implementation_factorAndDimensionOfSum "
            f"(1, {_dAT}) [(1, {_dV})]\n"
            f"        = some (1 + 1, {_dAT}) := by rfl\n"
            f"    unfold problem_spec_factorAndDimensionOfSum\n"
            f"    rw [himpl]\n"
            f"    simp [allDimsMatch, summedFactor]\n"
            + _P_OPEN),
        "rationale": "the obligation is discharged at the smallest F2P-shaped "
                     "input — a two-addend sum whose two dimensions have "
                     "DISTINCT surface identities but the SAME canonical power "
                     "map, which is exactly the reported case that must be "
                     "accepted — by evaluation as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifying shows C-accept "
                     "is satisfiable at a normal in-domain input (the analogue "
                     "of nagini's PRECOND-TOO-STRONG check: there a "
                     "contract-free caller must be able to establish the "
                     "Requires for a two-addend equal-reduction input). "
                     "Nothing is assumed: no new declaration, statement "
                     "byte-identical. Ports nagini's admiss-f2p-shaped-caller.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve, and (b) a witness pinning
    # the violation at one concrete input, seen to hold of the rival and to
    # fail on gold.
    # =====================================================================

    # ---- THE central attack: decide on the surface identity, not the map ----
    {
        "id": "weak-surface-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior: compare the SURFACE symbolic identities instead
        # of the canonical base-dimension power maps.
        "module": _swap(_BASE, _I_GUARD, "    if dim.name ≠ a.2.name then"),
        "refinement": "this IS the pre-fix behavior: the addend-compatibility "
                      "test decides on the surface symbolic identity of the "
                      "two dimensions rather than on their canonical "
                      "base-dimension power maps. A faithful real patch "
                      "keeping the surface test refuses every sum whose "
                      "addends are physically the same dimension written two "
                      "different ways — precisely the reported defect, where a "
                      "quantity recorded directly as one dimension is added to "
                      "a product of two others reducing to the same base "
                      "powers. The F2P case asserts that sum goes through, so "
                      "the faithful patch would NOT resolve.",
        "rationale": "REJECT from C-accept: the spec's arm is chosen by "
                     "`allDimsMatch`, which is stated over `deps` ONLY, so on "
                     "an input whose two dimensions share a power map the spec "
                     "demands `some (head.1 + Σ addend factors, head.2)`; the "
                     "rival compares `name`, finds them different and returns "
                     "`none`. `name` is exactly the component the spec forbids "
                     "from influencing the outcome, so if this VERIFIED the "
                     "spec could not tell the surface facet from the "
                     "reduction facet => SPEC-TOO-WEAK. Refuted at a one-addend "
                     "sum over the discriminating pair (distinct names, equal "
                     "maps). Ports nagini's rival-surface-identity-guard.",
        "witness": _witness(f"(1, {_dV})", f"[(2, {_dAT})]", "none"),
    },

    # ---- partial domain: never compare the FIRST addend ----
    {
        "id": "weak-skip-first-addend",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every addend but the first: the first is accumulated
        # without being compared to the head at all.
        "module": _swap(
            _BASE, _I_ALL,
            "  let dim := head.2\n"
            "  let mut factor := head.1\n"
            "  let mut checked := false\n"
            "  for a in addends do\n"
            "    if checked then\n"
            "      if dim.deps ≠ a.2.deps then\n"
            "        return none\n"
            "    checked := true\n"
            "    factor := factor + a.1\n"
            "  return some (factor, dim)"),
        "refinement": "its faithful real patch begins the compatibility check "
                      "one addend late, so the first addend after the head is "
                      "accepted whatever its dimension. A sum of two "
                      "physically incompatible quantities is then combined "
                      "silently, handing back a total that adds a length to a "
                      "mass and labels it with the head's dimension. The "
                      "existing consistency and factor/dimension tests assert "
                      "such a sum is REFUSED, so the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C-reject: when some addend's power map "
                     "differs from the head's, `allDimsMatch` is false and the "
                     "spec demands `none`; with the first addend never "
                     "compared the rival returns "
                     "`some (head.1 + a.1, head.2)` on a one-addend "
                     "incompatible sum. Partial-domain rival: it agrees with "
                     "gold on every input whose FIRST addend is compatible, so "
                     "it is refuted at the input that isolates that addend — a "
                     "single addend, incompatible with the head, on a "
                     "different power map (mass) from the other witnesses. "
                     "Ports nagini's rival-skip-index-1.",
        "witness": _witness(f"(3, {_dM})", f"[(1, {_dV})]", f"some (3 + 1, {_dM})"),
    },

    # ---- never reject: the compatibility test is dropped entirely ----
    {
        "id": "weak-never-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # Strip the compatibility test: every addend is accumulated, the
        # no-result arm is never reachable.
        "module": _swap(
            _BASE, _I_GUARD + "\n      return none\n" + _I_ACC, _I_ACC),
        "refinement": "its faithful real patch drops the addend-compatibility "
                      "requirement altogether, combining any sum regardless of "
                      "its addends' dimensions. Sums that must be refused are "
                      "then accepted with a meaningless total, and the "
                      "existing consistency and factor/dimension tests that "
                      "assert the refusal would fail — so the faithful patch "
                      "would NOT resolve. (It is also the strictly weaker "
                      "sibling of the reported defect: fixing an over-eager "
                      "refusal by never refusing is not the fix.)",
        "rationale": "REJECT from C-reject: with no test the no-result arm is "
                     "unreachable, but the spec demands `none` whenever any "
                     "addend's power map differs from the head's. Refuted at a "
                     "TWO-addend sum whose first addend is compatible and "
                     "second is not — a distinct input tuple from "
                     "weak-skip-first-addend (which the earlier rival handles "
                     "CORRECTLY, since it does compare the second addend), so "
                     "the two rivals do not share a witness and each is "
                     "refuted in the sub-domain its rationale claims. Ports "
                     "nagini's rival-never-raise.",
        "witness": _witness(f"(1, {_dV})", f"[(2, {_dAT}), (4, {_dM})]",
                            f"some (1 + 2 + 4, {_dV})"),
    },

    # ---- accept arm, factor component: never accumulate ----
    {
        "id": "weak-factor-not-summed",
        "kind": "uniqueness",
        "expect": "reject",
        # Decides the arm correctly but reports only the HEAD's factor,
        # dropping every addend's contribution to the total.
        "module": _swap(
            _BASE, _I_ALL,
            "  let dim := head.2\n"
            "  let factor := head.1\n"
            "  for a in addends do\n"
            "    if dim.deps ≠ a.2.deps then\n"
            "      return none\n"
            "  return some (factor, dim)"),
        "refinement": "its faithful real patch keeps the compatibility "
                      "requirement but never adds the addends' scale factors "
                      "into the running total, returning the head addend's "
                      "factor as if it were the whole sum's. Every accepted "
                      "sum then reports a numerically wrong scale factor; the "
                      "existing factor/dimension tests pin those totals "
                      "exactly (a sum of two lengths, a mixed-unit sum, a "
                      "rational-weighted difference), so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C-accept's FACTOR component: the spec pins "
                     "the accept-arm result to "
                     "`some (summedFactor head addends, head.2)` and "
                     "`summedFactor` is `head.1 + (addends.map Prod.fst).sum`; "
                     "the rival emits `some (head.1, head.2)`, which differs "
                     "whenever any addend factor is non-zero. This is the only "
                     "rival attacking the factor component — the others all "
                     "accumulate correctly — so without it a spec that left "
                     "the total unpinned would go unnoticed. Refuted on the "
                     "second discriminating pair (mass), an input tuple no "
                     "other witness uses. No nagini counterpart with this "
                     "exact shape; the nearest is "
                     "rival-wrong-return-constant, which attacks the other "
                     "component (see the accounting note).",
        "witness": _witness(f"(7, {_dM})", f"[(2, {_dMA})]", f"some (7, {_dM})"),
    },

    # ---- accept arm, dimension component: return a constant dimension ----
    {
        "id": "weak-constant-dimension",
        "kind": "uniqueness",
        "expect": "reject",
        # Decides the arm and the total correctly but replaces the carried
        # dimension with a constant (the empty power map).
        "module": _swaps(
            _BASE,
            (_I_HEADER, "  let mut factor := head.1"),
            (_I_GUARD, "    if head.2.deps ≠ a.2.deps then"),
            (_I_RET, f"  return some (factor, {_dOne})"),
        ),
        "refinement": "its faithful real patch returns a constant "
                      "dimensionless marker as the accepted sum's dimension "
                      "instead of carrying the head addend's dimension "
                      "through. Every consumer downstream of an accepted sum "
                      "then reads the wrong dimension, and the existing "
                      "factor/dimension tests assert the exact dimension of "
                      "each accepted sum, so the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C-accept's DIMENSION component: the spec "
                     "pins the accepted result's second component to `head.2` "
                     "— the frame requirement that the head's dimension is "
                     "carried through UNCHANGED — and the rival substitutes a "
                     "constant. Refuted at the degenerate EMPTY addend list, "
                     "where the arm is trivially the accept arm and the only "
                     "thing the spec still says is the frame: an input no "
                     "other witness reaches, and the one that isolates this "
                     "component from every other clause. Ports nagini's "
                     "rival-wrong-return-constant (there the returned "
                     "reference value is replaced by a constant identity).",
        "witness": _witness(f"(5, {_dAT})", "[]", f"some (5, {_dOne})"),
    },

    # ---- near-miss: advance the reference to the most recent addend ----
    {
        "id": "weak-sliding-reference",
        "kind": "uniqueness",
        "expect": "reject",
        # Compares each addend against the PREVIOUS one rather than against the
        # head, and reports the LAST addend's dimension. Agrees with gold on
        # every input where all power maps match (the comparison is then
        # chained through equals) — the near-miss is the carried dimension,
        # which is the last addend's surface identity, not the head's.
        "module": _swap(
            _BASE, _I_ALL,
            "  let mut dim := head.2\n"
            "  let mut factor := head.1\n"
            "  for a in addends do\n"
            "    if dim.deps ≠ a.2.deps then\n"
            "      return none\n"
            "    factor := factor + a.1\n"
            "    dim := a.2\n"
            "  return some (factor, dim)"),
        "refinement": "its faithful real patch re-points the reference at each "
                      "addend as it goes, so an accepted sum is labelled with "
                      "the LAST addend's dimension rather than the head "
                      "addend's. On a sum whose addends are physically equal "
                      "but differently written — exactly the case the fix is "
                      "about — the reported dimension is then the trailing "
                      "addend's surface form instead of the head's, and the "
                      "existing factor/dimension tests compare the returned "
                      "dimension against the head's, so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C-accept's DIMENSION component, and a "
                     "NEAR-MISS distinct from weak-constant-dimension: this "
                     "rival agrees with gold on the arm, on the total, and on "
                     "the dimension whenever the head and the last addend "
                     "happen to share a surface identity — it diverges only "
                     "where the two facets come apart, i.e. on the "
                     "discriminating pair the whole fix is about. So it is "
                     "refuted at its OWN input rather than at the "
                     "constant-dimension rival's: a one-addend sum whose "
                     "addend has the same power map as the head but a "
                     "different name, with the head/addend factor roles "
                     "swapped relative to weak-surface-identity. No nagini "
                     "counterpart (its carrier keeps the reference pinned by a "
                     "loop invariant, so the sliding shape is not "
                     "expressible); ADDED to give the dimension component a "
                     "near-miss attacker as well as a gross one.",
        "witness": _witness(f"(4, {_dAT})", f"[(6, {_dV})]", f"some (4 + 6, {_dV})"),
    },

    # ---- the accept decision ignores the ORDER-SENSITIVE part of the map ----
    # AUDIT-ADDED. The comparison is made permissive in the other direction from
    # weak-surface-identity: accept when EITHER the surface identity or the power
    # map matches. Every existing rival either reads `name` INSTEAD of `deps`
    # (restrictive) or drops the test entirely; none reads `name` as an
    # ALTERNATIVE ground for acceptance, so the clause "the surface identity may
    # never make an incompatible sum acceptable" had no attacker.
    {
        "id": "weak-name-also-accepts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ALL,
            "  let dim := head.2\n"
            "  let mut factor := head.1\n"
            "  for a in addends do\n"
            "    if dim.name ≠ a.2.name && dim.deps ≠ a.2.deps then\n"
            "      return none\n"
            "    factor := factor + a.1\n"
            "  return some (factor, dim)"),
        "refinement": "its faithful real patch keeps the surface-identity test "
                      "as an ADDITIONAL ground for acceptance rather than "
                      "replacing it: an addend is accepted when its surface "
                      "identity matches the head's even though the canonical "
                      "power maps differ. A sum of two physically incompatible "
                      "quantities that happen to be recorded under the same "
                      "surface identity is then combined silently, and the "
                      "existing consistency tests assert such a sum is REFUSED, "
                      "so the faithful patch would NOT resolve. It is the "
                      "permissive mirror of the reported defect: the surface "
                      "identity is still allowed to decide the outcome, just in "
                      "the accepting direction.",
        "rationale": "REJECT from C-reject, attacking the clause that the "
                     "surface identity may never influence the outcome — in the "
                     "ACCEPTING direction, which no other rival probes "
                     "(weak-surface-identity reads `name` restrictively, and "
                     "weak-never-reject drops the test for every input rather "
                     "than for the name-equal ones). `allDimsMatch` is stated "
                     "over `deps` only, so on an input whose two dimensions "
                     "share a surface identity but have DIFFERENT power maps the "
                     "spec demands `none`; the rival accepts and returns "
                     "`some (head.1 + a.1, head.2)`. Refuted at a new input "
                     "tuple built from a same-name/different-map pair, a "
                     "combination no other witness uses. AUDIT-ADDED (no nagini "
                     "counterpart).",
        "witness": _witness(
            '(1, { name := "sX", deps := [("mass", 1)] })',
            '[(2, { name := "sX", deps := [("length", 1)] })]',
            'some (1 + 2, { name := "sX", deps := [("mass", 1)] })'),
    },

    # ---- DIVERGENCE: an impl whose walk never terminates -------------------
    # AUDIT-ADDED, replacing this file's earlier claim that the class is vacuous
    # on this carrier. It is not: `while true do` elaborates inside the impl's
    # `Id.run do` block (its `ForIn` instance is opaque, not rejected), declares
    # nothing new, and keeps the frozen obligation's statement byte-identical.
    # This ports nagini's rival-vacuous-nonterminating-loop.
    {
        "id": "weak-divergent-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ALL,
            "  let mut factor := head.1\n"
            "  while true do\n"
            "    factor := factor + head.1\n"
            "  return some (factor, head.2)"),
        "refinement": "its faithful real patch replaces the addend walk with a "
                      "loop that never exits, so the routine returns no result "
                      "and raises nothing for ANY sum. The F2P case, which "
                      "requires the reported sum to go through, hangs instead of "
                      "returning, and every existing factor/dimension and "
                      "consistency test hangs with it — the harness times out, "
                      "so the faithful patch would NOT resolve. This is the "
                      "vacuous-satisfaction shape: no execution reaches a "
                      "result, so a value clause read only of terminating runs "
                      "would be satisfied by doing nothing.",
        "rationale": "REJECT covering BOTH arms at once. The rival's output term "
                     "does not mention `addends` at all — the walk is never "
                     "reached — but the spec makes the result a function of "
                     "`addends`: at the empty addend list it demands the accept "
                     "value `some (head.1, head.2)`, and at a single "
                     "incompatible addend it demands `none`. One term cannot be "
                     "both, so the two spec instances are jointly unsatisfiable "
                     "for this rival. If it VERIFIED, an impl that computes "
                     "nothing would satisfy the obligation => SPEC-TOO-WEAK in "
                     "the divergence direction. The witness uses the "
                     "no-evaluation shape (see `_witness_no_eval`) because the "
                     "unbounded loop is an opaque term the kernel cannot unfold: "
                     "a `rfl` on the rival's VALUE would be stuck, and a stuck "
                     "build discriminates nothing. Ports nagini's "
                     "rival-vacuous-nonterminating-loop.",
        "witness": _witness_no_eval(f"(1, {_dV})", "[]",
                                    f"(1, {_dV})", f"[(2, {_dM})]"),
    },
]

# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus 3 AXIOM_TESTS. This
# bundle models the SAME single purely-functional core; every sibling case that
# attacks the modeled behavior is re-expressed, the permission class is vacuous on
# this carrier (checked, see below), the termination class IS shippable here and is
# shipped, and three rivals are ADDED so that every component of the accept arm is
# attacked and the `name`-vs-`deps` clause is attacked from both sides.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------------
#   pos-control-symmetric-guard         -> pos-symmetric-guard      PORTED (re-proved)
#   pos-control-local-ref               -> pos-inline-reference     RE-EXPRESSED
#   admiss-f2p-shaped-caller            -> admiss-ground-equivalent-pair  RE-EXPRESSED
#   rival-surface-identity-guard        -> weak-surface-identity    PORTED
#   rival-skip-index-1                  -> weak-skip-first-addend   PORTED
#   rival-never-raise                   -> weak-never-reject        PORTED
#   rival-wrong-return-constant         -> weak-constant-dimension  PORTED
#   frame-mutation-overwrite-red        -> (none)                   VACUOUS
#   frame-mutation-overwrite-surf       -> (none)                   VACUOUS
#   rival-vacuous-nonterminating-loop   -> weak-divergent-loop      PORTED (audit)
#   (none)                              -> pos-positive-guard       ADDED
#   (none)                              -> weak-factor-not-summed   ADDED
#   (none)                              -> weak-sliding-reference   ADDED
#   (none)                              -> weak-name-also-accepts   ADDED (audit)
#   AXIOM_TESTS (3)                     -> (none)                   DROPPED (G-AX)
#
# RE-EXPRESSED (pos-inline-reference): the sibling's positive INTRODUCES a local
#   snapshot of the reference reduction and has to re-pin it as a loop invariant
#   because its verifier havocs the local across iterations. On this carrier the
#   frozen impl ALREADY binds that snapshot (`let dim := head.2`) and there is no
#   havoc to repair, so the analogous structurally-different-but-correct reshape
#   is its REMOVAL — read the reference off the head pair at both use sites. Same
#   argument (a read-only snapshot of the reference is interchangeable with the
#   reference itself), opposite direction.
# RE-EXPRESSED (admiss-ground-equivalent-pair): the sibling builds a
#   contract-free caller that must ESTABLISH the callee's precondition (including
#   a termination obligation) for a two-addend equal-reduction input. The frozen
#   obligation here carries NO precondition hypotheses and no termination
#   obligation, so there is no precondition to establish and no call site to
#   write; the honest analogue of "a normal F2P-shaped input is admitted" is to
#   discharge the spec predicate at that same two-addend input by evaluation, then
#   close the frozen obligation verbatim.
# VACUOUS (frame/permission mutation, 2 sibling cases): MANDATORY on the sibling's
#   carrier — both input facets are held at half permission, so a rival that
#   overwrites an entry to make the accept clause hold vacuously is rejected for
#   insufficient permission. Lean is referentially transparent: the inputs are
#   immutable values, there is no `mut` input binder, no aliasing, and no cell to
#   overwrite, so the attack cannot be WRITTEN. No substitute is fabricated.
#   Checked, not assumed: the nearest expressible analogue — rewrite a LOCAL copy
#   of the addends so every power map equals the head's, then walk the copy — was
#   built and IS rejected, but it is rejected on VALUE grounds (it returns
#   `some (…)` where the spec demands `none`), which is precisely the ground
#   `weak-never-reject` already covers with the same input tuple. So the analogue
#   is a duplicate of an existing case rather than a distinct class, and the
#   sibling's permission-lane discrimination genuinely has no counterpart here.
# PORTED, AUDIT-CORRECTED (divergence, 1 sibling case -> weak-divergent-loop):
#   this file previously recorded the class VACUOUS, on the ground that a
#   diverging implementation "is not expressible — the elaborator rejects it
#   before any spec question arises". That was measured WRONG. An unbounded
#   `while true do` inside the impl's `Id.run do` block elaborates: its `ForIn`
#   instance is opaque to the kernel, not refused by the elaborator, so the file
#   compiles as far as the obligation and the rival declares nothing new. The
#   class is therefore shippable in the reject lane and is now shipped.
#   What makes it catchable here is a VALUE fact, not a termination obligation:
#   the diverging term does not mention `addends`, while the spec makes the
#   result a function of `addends` (accept at `[]`, `none` at an incompatible
#   addend), so the two spec instances are jointly unsatisfiable. The witness
#   must not try to EVALUATE the rival — `rfl` on the opaque loop is stuck, and a
#   stuck build discriminates nothing — hence `_witness_no_eval`.
# ADDED (pos-positive-guard): a second independent correct shape for the
#   obligation's defended side (positive test with the branches exchanged),
#   re-proved by flipping one `if_pos` to `if_neg`.
# ADDED (weak-factor-not-summed): the sibling's five rivals all accumulate the
#   running total correctly — their carrier's success clause is about the
#   reference value, not a sum — so the FACTOR component of this spec's accept
#   arm would have had no attacker. It is a real load-bearing component of the
#   frozen postcondition (`summedFactor head addends`), and a spec that left it
#   unpinned would be exactly the SPEC-TOO-WEAK hole this gate exists to find.
# ADDED (weak-name-also-accepts, AUDIT): every pre-existing rival that touches the
#   `name`-vs-`deps` clause attacks it RESTRICTIVELY — reading `name` in place of
#   `deps` so a compatible sum is refused. Nothing attacked the permissive
#   direction, where `name` equality is an ADDITIONAL ground for accepting an
#   addend whose power map differs. That is an independent way for the surface
#   facet to influence the outcome, and the spec forbids both, so the clause now
#   has an attacker on each side. Its witness needs a same-name/different-map
#   pair, an input shape no other witness used.
# ADDED (weak-sliding-reference): the constant-dimension rival attacks the
#   carried dimension GROSSLY (any input refutes it). A rival that re-points the
#   reference at each addend agrees with gold over strictly more of the domain
#   and diverges only where the surface facet and the reduction facet come apart,
#   which is the sub-domain the fix is about — so it gets its own witness at that
#   input rather than sharing the gross rival's, and the manifest demonstrates
#   the sub-domain its rationale claims.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores it;
#   the bundle also declares no `opaque` callee and consumes no `axiom` (the
#   changed comparison is modeled deeply as power-map equality), so there would
#   be nothing to probe.
#
# POINT SPREAD. The eight reject witnesses probe eight DISTINCT input tuples;
# `head` is written (factor, dim) and `addends` as a list of the same. `sX1`/`sX2`
# are the MIRROR of the discriminating pair — same surface identity `sX`, DIFFERENT
# power maps (mass vs length):
#
#   (1, sV)  [(2, sAT)]            weak-surface-identity     C-accept (arm)
#   (3, sM)  [(1, sV)]             weak-skip-first-addend    C-reject
#   (1, sV)  [(2, sAT), (4, sM)]   weak-never-reject         C-reject
#   (7, sM)  [(2, sMA)]            weak-factor-not-summed    C-accept (factor)
#   (5, sAT) []                    weak-constant-dimension   C-accept (dimension)
#   (4, sAT) [(6, sV)]             weak-sliding-reference    C-accept (dimension)
#   (1, sX1) [(2, sX2)]            weak-name-also-accepts    C-reject
#   (1, sV)  [] AND (1, sV) [(2, sM)]   weak-divergent-loop  BOTH arms at once
#
# Neither binder is pinned. `addends` takes length 0, 1 (five times, with five
# different contents) and 2. `head`'s dimension takes sV, sM, sAT and sX1 —
# covering both power maps in play, both surface identities of the discriminating
# pair (in both the head and the addend position), and a same-name/different-map
# pair that no other witness uses. Head factors are 1/3/7/5/4 and addend factors
# 2/1/2+4/2/6, so neither factor slot is held fixed. Both spec arms are attacked
# (3 witnesses on C-reject, 4 on C-accept, 1 on both simultaneously), and within
# C-accept all three things it pins — which arm is chosen, the factor total, the
# carried dimension — have their own attacker. The `name`-vs-`deps` clause is
# attacked from both sides (restrictive and permissive).
#
# EVERY case in this file was checked by a real `lake env lean` build before
# shipping: the four verify cases elaborate with the obligation closed, and each
# of the eight witnesses was built twice (holds of its rival, fails on the frozen
# solution) plus a third FLIPPED-CLAIM build against gold, which elaborates —
# so each gold-side failure is a verdict on the claim, not on the file's shape.
AXIOM_TESTS = []
