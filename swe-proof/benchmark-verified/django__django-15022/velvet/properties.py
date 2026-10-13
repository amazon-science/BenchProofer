"""properties.py — G-PBT falsification battery for django__django-15022 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct searchKeepsRow`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is judged by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the subject named by ``witness_reference``; see the CARRIER NOTE
for why the frozen solution cannot be that subject here).

DEFENDED SURFACE. One contracted method deciding whether a single candidate
outer row is kept by a multi-word search over its related items, parametric in
the per-(item,word) match test:

    searchKeepsRow (records : List Nat) (terms : List Nat)
                   (matchTerm : Nat → Nat → Bool) return (result : Bool)
      require 0 < terms.length
      ensures result = anyRecord matchTerm terms records

``anyRecord matchTerm terms records`` is a total, fully-unfolded pure function:
the row is kept exactly when SOME single related item clears EVERY search word
at once — ``∃ r ∈ records. ∀ t ∈ terms. matchTerm r t``. The nesting is
load-bearing: the SAME related item must satisfy every word; words may NOT be
spread across different items. The single ``ensures`` clause pins the result to
this exists-item / for-all-words quantifier nesting.

``matchTerm : Nat → Nat → Bool`` is a FREE input the spec quantifies over: the
``ensures`` holds for EVERY value of it, so the spec makes no claim about which
item matches which word. Because the result is pinned for every ``matchTerm``, a
rival that mishandled the quantifier nesting is refuted uniformly across all
instantiations of the match test.

``require 0 < terms.length``: the modeled decision is only made when at least
one search word is present (mapping.md §2 — the loop runs under a non-empty
search). The empty-word sub-domain is OUTSIDE the modeled domain, so any rival
whose ONLY divergence from the frozen decision is at zero words is not
refutable here (see the footer: the sibling's empty-terms rival is vacuous).

CARRIER NOTE — why every reject case names a ``witness_reference`` (MEASURED).
The frozen impl keeps a ``while`` loop, and under
``set_option loom.semantics.choice "demonic"`` the loop's fixpoint elaborates
through ``Classical.choice``, which the kernel cannot unfold. So ``decide``
against the FROZEN tester is stuck for every claim regardless of truth. Measured
on this cell, the gold-side build of each witness fails with

    Tactic `decide` failed for proposition
      (searchKeepsRowTester [0] [10, 11] fun r t => r == 0 && t == 10) = false
    because its `Decidable` instance ... did not reduce to `isTrue` or `isFalse`

— a REDUCTION-STUCK failure, not a refutation. That exit code carries no
information: a forged witness asserting the rival is CORRECT would fail the same
way and clear both halves. An earlier revision of this battery shipped exactly
that shape and the gate correctly recorded ``witness-undecided`` on all three
rejects. The repair is the second route the gate offers: every reject case names
``_REF_LOOPFREE`` as its ``witness_reference`` — a LOOP-FREE impl of the same
frozen spec, which the gate independently checks shares the spec and VERIFIES
before refuting the witness against it. There the tester DOES reduce and
``decide`` refutes each witness SEMANTICALLY (measured, all four):

    Tactic `decide` proved that the proposition
      (searchKeepsRowTester [0] [10, 11] fun r t => r == 0 && t == 10) = false
    is false                                                          (exit 1)

So each witness holds of its rival and provably FAILS of a verifying correct impl
of the same spec, at the same input on the same carrier shape. That is the
discrimination the stuck-on-gold build cannot supply. ``_REF_LOOPFREE`` is also
shipped as the ``expect="verify"`` case ``pos-closed-form``, so the battery
itself records that loop-freeness is NOT what any rival is rejected for.

PROOF-SHAPE CONTROL — why each rejection is attributable to the SPEC. The frozen
tactic body rewrites with ``anyRecord_drop_step ... i ...``, naming the loop
counter ``i``; against any loop-free rival that script fails with
``Unknown identifier `i```, which is a tactic mismatch and not a refutation. So
every reject rival instead carries the BARE ``loom_solve`` body — the same body
under which the CORRECT loop-free impl verifies (exit 0, ``pos-closed-form``).
Under it each rival still fails, and the single residual goal names the rival's
own expression against the post-image, e.g.

    ⊢ (terms.all fun t => records.any fun r => matchTerm r t)
        = anyRecord matchTerm terms records

which is the attribution: the rejection is the postcondition refusing the
rival's computation, not a script tuned to a shape.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating loop collapsed to the closed
    form the post-image names; the disjunction commuted) must still verify, else
    the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries a ``require 0 < terms.length`` clause, but
    it is trivially satisfiable (any non-empty word list). The residual risk on
    this surface is that the post-image is DEGENERATE at the interesting point —
    that it does not actually demand DROP for the F2P shape (two related items,
    each clearing one word but neither clearing both) while demanding KEEP when a
    single item clears all words. ``admiss-grounded`` discharges an in-region
    assert pinning both at concrete F2P-shaped inputs; the impl is kept verbatim
    so the method's own obligation still discharges. The assert is LIVE, measured:
    flipping its DROP claim to the opposite (false) claim about the SAME point
    breaks the build, so the case cannot pass by the assert being vacuous.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only heap input may carry a fractional permission an impl overwrites.
    Lean and Velvet are referentially transparent: ``records``, ``terms`` and
    ``matchTerm`` are immutable values (none declared ``mut``), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated — reported as an omission in the footer.
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
  * UNGROUNDED-ORACLE ECHO — N/A as a WRONG echo. ``anyRecord`` is a total,
    fully-unfolded ``def`` over the method's own inputs (the ``axioms`` region
    declares nothing), so evaluating it IS the correct answer; returning it
    directly is the cheapest CORRECT impl (``pos-closed-form``), a positive
    control, not a reject.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired quantifier nesting on some sub-domain and MUST be
    rejected: the for-all-words / exists-item chained semantics (the literal
    pre-patch bug — the single discriminating delta of the gold change), the
    first-item-only partial domain over the records axis, the
    exists-item / exists-word global-OR collapse, and the for-all-item
    over-restriction that attacks the existential from the opposite side. Each is
    a loop-free closed form (so its tester kernel-reduces) with a machine-checked
    refutation witness.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``searchKeepsRowTester records terms matchTerm = false`` says the extracted
program's result violates the postcondition at that concrete input, checked in a
file whose ``prove_correct`` block has been stripped (no tactic script can mask
the verdict). The free match test ``matchTerm`` is instantiated at a concrete
decidable lambda in each witness, so the tester reduces to a ground boolean; the
``require 0 < terms.length`` precondition holds at every witness input (all use a
non-empty word list), so the tester's verdict is a genuine postcondition
violation. Every carrier value is fully transparent, so no witness binds a
hypothesis and no consistency probe applies.

WITNESS PLACEMENT. The four rejects probe four DISTINCT input points, so all
three input binders are genuinely varied rather than pinned. ``records`` ranges
over a two-item list, a two-item list, a singleton, and a two-item list;
``terms`` over a two-word list, a one-word list, a two-word list, and a two-word
list; and ``matchTerm`` over four distinct match tests (a two-clause split match,
a match on the SECOND item only, a single-pair match, and a first-item-only
match ignoring the word). A rival that mishandled only a fixed shape of any one
binder would still be caught.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
per-(item,word) match test is the free input ``matchTerm``, an A-reference the
R/I legs differential-test (G-CONF's job), not a consumed contract. The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15022"
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
# these keeps markers.same_spec True and the prove_correct header byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating disjunction
# over the related items. Reject rivals replace this with a loop-free closed
# form (so their tester reduces under `decide`); the loop-free positive control
# and the witness reference do too.
_IMPL = """    -- impl-start
    let mut acc : Bool := false
    let mut i := records.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ records.length
      invariant acc = anyRecord matchTerm terms (records.drop i)
      done_with i = 0
      decreasing i
    do
      let r := records[i - 1]!
      acc := conjTerms (matchTerm r) terms || acc
      i := i - 1
    return acc
    -- impl-end"""

# The single per-iteration disjunction line; a positive control may commute it
# while keeping the loop and the invariant, so the frozen proof still closes
# (with the disjunction-commute retune).
_STEP = "      acc := conjTerms (matchTerm r) terms || acc\n"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut acc : Bool := false\n"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). It rewrites with `anyRecord_drop_step ... i ...`, which NAMES the
# loop counter, so it cannot apply to a loop-free impl: against one it fails
# with `Unknown identifier `i`` — a tactic mismatch, not a refutation. Every
# loop-free variant (positive OR rival) therefore retunes this.
_PROOF = """prove_correct searchKeepsRow by
  loom_solve
  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
  simp_all"""

# The BARE proof body. Measured: this is exactly the body under which the
# CORRECT loop-free impl VERIFIES (exit 0 — `pos-closed-form` / the witness
# reference). Every reject rival carries it, so a rival's failure cannot be
# blamed on a script tuned to the frozen loop; what fails is the postcondition,
# and the residual goal names the rival's own expression.
_PROOF_BARE = "prove_correct searchKeepsRow by\n  loom_solve"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


def _rival(body):
    """A loop-free wrong impl carrying the bare (correct-impl-sufficient) proof."""
    return _swap2(_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end",
                  _PROOF, _PROOF_BARE)


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A loop-free impl that returns the modeled decision
# directly: it shares the frozen spec, it VERIFIES (the gate re-checks both), and
# crucially its tester REDUCES, so `decide` can refute a witness against it. It
# replaces the frozen solution as the second subject of the discrimination check,
# because the frozen loop's `Classical.choice` fixpoint makes `decide` stuck for
# every claim (see the CARRIER NOTE). Shipped as `pos-closed-form` too, so the
# battery records that loop-freeness is not what any rival is rejected for.
# ---------------------------------------------------------------------------
_REF_LOOPFREE = _swap2(
    _IMPL,
    "    -- impl-start\n"
    "    return anyRecord matchTerm terms records\n"
    "    -- impl-end",
    _PROOF, _PROOF_BARE)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `searchKeepsRowTester records terms matchTerm = false` says
# ---- the extracted program's result violates the postcondition at that
# ---- concrete input. `matchTerm` is instantiated at a decidable lambda.
def _tester(body):
    return ("extract_program_for searchKeepsRow\n"
            "prove_precondition_decidable_for searchKeepsRow\n"
            "prove_postcondition_decidable_for searchKeepsRow\n"
            "derive_tester_for searchKeepsRow\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures result = anyRecord
    # matchTerm terms records` obligation and only reshapes the executable
    # surface (and, where needed, retunes the tactic body).
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same decision; the loop-specific proof is
        # retuned to the bare `loom_solve` since the impl now matches the
        # post-image syntactically. This is the SAME source as _REF_LOOPFREE, so
        # the battery itself certifies the witness reference verifies.
        "module": _REF_LOOPFREE,
        "rationale": "a loop-free impl that returns the modeled decision directly "
                     "must satisfy `result = anyRecord matchTerm terms records`; a "
                     "correct reshape of the modeled behaviour verifying is exactly "
                     "what SPEC-TOO-STRONG would deny. Exercises the obligation from "
                     "a maximally different (loop-free) control-flow shape, and "
                     "doubles as the reject lane's witness reference — so the "
                     "battery records that loop-freeness is not what any rival is "
                     "rejected for, and that the bare `loom_solve` body every rival "
                     "carries is sufficient for a CORRECT impl of this shape.",
    },
    {
        "id": "pos-commuted-or",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: commute the per-item disjunction in the loop body
        # (`acc || conjTerms (matchTerm r) terms` instead of
        # `conjTerms (matchTerm r) terms || acc`). Same value flow; the loop and
        # the front-recursive invariant are unchanged, so the frozen proof closes
        # once the drop-step rewrite is followed by `simp_all [Bool.or_comm]`.
        "module": _swap2(
            _STEP,
            "      acc := acc || conjTerms (matchTerm r) terms\n",
            _PROOF,
            "prove_correct searchKeepsRow by\n"
            "  loom_solve\n"
            "  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]\n"
            "  simp_all [Bool.or_comm]"),
        "rationale": "commuting the per-item disjunction computes the same "
                     "accumulator value-for-value with the loop and invariant "
                     "unchanged, so `result = anyRecord matchTerm terms records` "
                     "still holds and the frozen proof closes with a "
                     "`Bool.or_comm` rewrite; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG on the disjunction order). Keeps the LOOP, so "
                     "together with `pos-closed-form` the positives cover both the "
                     "loop-bearing and the loop-free shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a `require 0 < terms.length` clause,
    # but it is trivially satisfiable (any non-empty word list), so the "a
    # normal input satisfies the precondition" probe is not where the risk
    # sits. The residual risk on this surface is that the post-image is
    # DEGENERATE at the interesting point (a spec no impl can meet reads like a
    # spec every impl meets). This case discharges an in-region assert at
    # concrete F2P-shaped inputs, establishing that the post-image really does
    # demand DROP for the multi-valued-relationship shape (two related items,
    # each clearing exactly one of two words, neither clearing both) and KEEP
    # when a single item clears all words. The surrounding impl is kept verbatim
    # so the method's own obligation still discharges; the assert is LIVE
    # (measured: replacing the DROP claim with the opposite claim about the same
    # point breaks the build), and the proof's alternation gains one `decide` arm
    # to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL_TOP,
            "    assert (with_name_prefix `assert\n"
            "      (anyRecord (fun r t => (r == 0 && t == 10) || (r == 1 && t == 11)) [10, 11] [0, 1] = false ∧\n"
            "       anyRecord (fun r t => r == 1 && (t == 12 || t == 11)) [12, 11] [0, 1] = true))\n"
            + _IMPL_TOP,
            _PROOF,
            "prove_correct searchKeepsRow by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)];\n"
            "       simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: it demands DROP for a shape with two "
                     "related items where each clears exactly one of two words but "
                     "NEITHER clears both (the multi-valued-relationship case the "
                     "fix targets), and KEEP when a single item clears all words. "
                     "The in-region assert must discharge (else the obligation is "
                     "degenerate); the impl is kept verbatim so `result = anyRecord "
                     "matchTerm terms records` still verifies. Measured live: the "
                     "same case with the DROP claim replaced by the opposite claim "
                     "about the same point FAILS to build, so this cannot pass by "
                     "the assert being vacuous.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a loop-free closed form (so its tester
    # kernel-reduces), carries the bare `loom_solve` body under which a CORRECT
    # loop-free impl verifies (so the rejection is not a tactic artifact), names
    # the verifying loop-free `_REF_LOOPFREE` as the subject its witness is
    # refuted against (the frozen loop cannot decide anything), and comes with
    # the refinement argument that its faithful real counterpart would NOT
    # resolve the failing test.
    # =====================================================================
    {
        "id": "weak-chained-forall-word-exists-item",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating delta. The pre-patch chained semantics: keep the row
        # iff for EVERY word there exists SOME related item matching it (words may
        # be satisfied by DIFFERENT items). This is the ∀word∃item quantifier
        # nesting the gold change swaps to ∃item∀word.
        "module": _rival(
            "    return terms.all (fun t => records.any (fun r => matchTerm r t))"),
        "refinement": "this is the literal pre-patch behaviour: the per-word "
                      "filters are combined so that each word may be satisfied by a "
                      "different related item. Its faithful real counterpart is the "
                      "UNCHANGED chained-filter combination, which still keeps a "
                      "candidate whose related items COLLECTIVELY (but not "
                      "individually) cover the words — exactly the failing case the "
                      "issue adds (two related items, one clearing each of two "
                      "words, kept where it must be dropped) — so it would NOT "
                      "resolve.",
        "rationale": "REJECT from `result = anyRecord matchTerm terms records`: at "
                     "two related items where item 0 clears word 10 and item 1 "
                     "clears word 11, `anyRecord` requires a SINGLE item clearing "
                     "both (there is none, so it demands DROP) while the rival's "
                     "∀word∃item accumulation keeps the row. Refuted on the "
                     "F2P-shaped multi-item input `records=[0,1]`, `terms=[10,11]`, "
                     "the load-bearing behavior of the fix. Measured: under the bare "
                     "proof body the residual goal is `(terms.all fun t => "
                     "records.any fun r => matchTerm r t) = anyRecord matchTerm "
                     "terms records` — the postcondition refusing the rival's own "
                     "quantifier nesting, not a tactic mismatch.",
        "witness": _tester(
            "example : searchKeepsRowTester [0, 1] [10, 11] "
            "(fun r t => (r == 0 && t == 10) || (r == 1 && t == 11)) "
            "= false := by\n  decide\n"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-first-record-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial domain over the records axis: inspect ONLY the first related
        # item — keep iff records[0] clears all words. Correct on every input
        # whose clearing item is first (or where no item clears); diverges when
        # only a LATER related item clears all words.
        "module": _rival(
            "    return !records.isEmpty && conjTerms (matchTerm records[0]!) terms"),
        "refinement": "a counterpart that tests only the first reachable related "
                      "item drops a candidate whose only all-words-clearing item is "
                      "not first, so it fails to return rows from multi-valued "
                      "relationships whenever the matching related item is reached "
                      "later — not behaviourally the gold combination (which "
                      "existentially quantifies over ALL related items) and would "
                      "NOT resolve.",
        "rationale": "REJECT from `result = anyRecord matchTerm terms records`: "
                     "`anyRecord` is the disjunction over EVERY related item, so a "
                     "one-item check breaks the equality on any input whose "
                     "clearing item is not `records[0]`. Refuted at `records=[0,1]`, "
                     "`terms=[10]` with only the SECOND item matching — a distinct "
                     "input point and a distinct match test from the other rivals, "
                     "attacking the exists-over-ALL-items requirement. This is a "
                     "NEAR-MISS (it agrees with gold wherever the clearing item is "
                     "first), so it gets its own witness at the input that "
                     "distinguishes it rather than sharing another rival's.",
        "witness": _tester(
            "example : searchKeepsRowTester [0, 1] [10] "
            "(fun r t => r == 1 && t == 10) = false := by\n  decide\n"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-any-item-any-word",
        "kind": "uniqueness",
        "expect": "reject",
        # exists-item / exists-word: keep iff ANY (item, word) pair matches at
        # all. Collapses the per-item AND-over-words into a global OR — far too
        # permissive: keeps a row whenever any related item matches any single
        # word, even when no item clears ALL words.
        "module": _rival(
            "    return records.any (fun r => terms.any (fun t => matchTerm r t))"),
        "refinement": "a counterpart that OR-combined every per-word query into one "
                      "big disjunction keeps a candidate on ANY single field match, "
                      "so a multi-word search WIDENS instead of narrowing — it would "
                      "fail the fixed-count multi-term F2P (a multi-word search must "
                      "narrow, keeping only rows whose single related item clears "
                      "all words) and is not the AND-of-per-word gold combination. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `result = anyRecord matchTerm terms records`: the "
                     "any-pair accumulator returns keep whenever one item matches "
                     "one word, but `anyRecord` requires a single item clearing "
                     "EVERY word. Refuted at `records=[0]`, `terms=[10,11]` where "
                     "the sole item matches word 10 but not word 11 — so `anyRecord` "
                     "demands DROP while the rival keeps. A distinct input point "
                     "(a singleton item list, two words) from the other rivals, "
                     "attacking the for-all-WORDS conjunct on the records axis's "
                     "smallest non-trivial shape.",
        "witness": _tester(
            "example : searchKeepsRowTester [0] [10, 11] "
            "(fun r t => r == 0 && t == 10) = false := by\n  decide\n"),
        "witness_reference": _REF_LOOPFREE,
    },
    {
        "id": "weak-all-items-must-clear",
        "kind": "uniqueness",
        "expect": "reject",
        # ∀item∀word: the OVER-RESTRICTIVE dual. Demands that EVERY related item
        # clear every word, so it attacks the existential over `records` from the
        # opposite side to the two rivals above (which attack it by truncation and
        # by permissiveness). Agrees with gold on singleton record lists, so its
        # witness needs >= 2 items with a NON-uniform match matrix.
        "module": _rival(
            "    return records.all (fun r => conjTerms (matchTerm r) terms)"),
        "refinement": "a counterpart that required the AND-of-per-word conjunction "
                      "to hold of EVERY related item (rather than of some one item) "
                      "drops a candidate as soon as any one of its related items "
                      "fails a word — so a row whose single qualifying related item "
                      "sits alongside any non-matching sibling is discarded. That "
                      "fails the requirement that searches over multi-valued "
                      "relationships RETURN rows from related items: it is strictly "
                      "more restrictive than the gold combination, which is "
                      "existential over the related items, so it would NOT resolve.",
        "rationale": "REJECT from `result = anyRecord matchTerm terms records`: "
                     "`anyRecord` is a DISJUNCTION over the related items, so an "
                     "impl that conjoins over them breaks the equality on any input "
                     "with a mix of clearing and non-clearing items. Refuted at "
                     "`records=[0,1]`, `terms=[10,11]` with a match test true for "
                     "item 0 at EVERY word and false for item 1: `anyRecord` demands "
                     "KEEP (item 0 clears all words) while the rival drops. This is "
                     "the only rival refuted at a KEEP-demanding point — the other "
                     "three are all refuted where the spec demands DROP — so it "
                     "attacks the clause from the opposite polarity, and it is the "
                     "only witness whose match test ignores the word binder "
                     "entirely.",
        "witness": _tester(
            "example : searchKeepsRowTester [0, 1] [10, 11] "
            "(fun r _ => r == 0) = false := by\n  decide\n"),
        "witness_reference": _REF_LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (2
# soundness positives, 1 admissibility, 4 uniqueness rivals) plus an empty
# AXIOM lane. The sibling contracts a single function
# `search_retains_object(rows, terms)` over two `PSeq[int]` value sequences,
# returning the retention decision; this bundle contracts the SAME decision as
# the method `searchKeepsRow(records, terms, matchTerm)` — the per-(item,word)
# match relation, an uninterpreted `@ContractOnly` symbol on the sibling, is the
# FREE input `matchTerm : Nat → Nat → Bool` here, which the spec quantifies over.
# The value surface carries across intact; the permission surface does not exist
# here, and one sibling rival falls outside this bundle's precondition.
#
#   sibling case                 kind          -> here                                 disposition
#   -----------------------------------------------------------------------------------------------
#   pos-oracle-echo              soundness     -> pos-closed-form                       PORTED
#   pos-reshape-inner-and        soundness     -> pos-commuted-or                       PORTED (re-aimed)
#   admiss-f2p-shape             admissibility -> admiss-grounded                       RE-AIMED
#   weak-chained-filter          uniqueness    -> weak-chained-forall-word-exists-item  PORTED
#   weak-first-row-only          uniqueness    -> weak-first-record-only                PORTED
#   weak-any-row-any-term        uniqueness    -> weak-any-item-any-word                PORTED
#   weak-empty-terms-flip        uniqueness    -> (none)                                OUT-OF-DOMAIN
#   (frame-mutation, sibling N/A)              -> (none)                                VACUOUS
#   (no sibling divergence case)               -> (none)                                SPEC-CLOSED
#   (none)                       uniqueness    -> weak-all-items-must-clear             ADDED (carrier)
#
# PORTED (pos-oracle-echo -> pos-closed-form): the sibling returns the grounded
#   oracle directly; here the loop-free `return anyRecord matchTerm terms records`
#   is the exact analogue, retuning the loop proof to a bare `loom_solve`. It
#   carries extra weight on this carrier: it is also the reject lane's
#   `witness_reference`.
# PORTED / re-aimed (pos-reshape-inner-and -> pos-commuted-or): the sibling
#   reshapes the INNER all-clear fold (if/clear -> boolean AND). Here that inner
#   fold is `conjTerms`, defined in the frozen (spec-frozen) pure region and NOT
#   in the impl, so it cannot be reshaped without touching the spec. The closest
#   in-region reshape is to commute the OUTER per-item disjunction
#   (`acc || conjTerms …`), which keeps the loop and invariant and needs only a
#   `Bool.or_comm` retune of the frozen proof. Same class (a value-preserving
#   reshape that must still verify), aimed at the disjunction the impl owns.
# RE-AIMED (admiss-f2p-shape -> admiss-grounded): the sibling builds the F2P
#   "two children" 2-row x 2-term shape as fresh value-sequence literals,
#   self-calls, and asserts the call agrees with the oracle (a no-precondition
#   admissibility probe). There is no self-call/permission surface here and the
#   `require` is trivially satisfiable, so the case is re-aimed at the sharper
#   residual risk: a degenerate post-image. It discharges a live in-region assert
#   pinning DROP at the exact split-coverage shape (two items, each clearing one
#   word, neither both) and KEEP at the single-item-clears-both shape —
#   preserving the sibling's exact F2P witness points.
# PORTED (the three quantifier/partial-domain rivals): weak-chained-filter ports
#   directly to weak-chained-forall-word-exists-item (the literal pre-patch
#   ∀word∃item nesting, refuted on the F2P multi-item shape — the single
#   discriminating delta of the fix); weak-first-row-only ports to
#   weak-first-record-only (the records-axis partial domain, refuted where only a
#   later item clears all words); weak-any-row-any-term ports to
#   weak-any-item-any-word (the ∃item∃word global-OR collapse, refuted where the
#   sole item matches one of two words).
# ADDED (weak-all-items-must-clear): NOT a sibling port — added because the three
#   ported rivals all attack the post-image from the same polarity (each is
#   refuted at an input where the spec demands DROP and the rival keeps, or
#   truncates), leaving the KEEP direction of the disjunction over `records`
#   untested. The ∀item∀word over-restriction is refuted at a point where the
#   spec demands KEEP, and its match test is the only one that ignores the word
#   binder, so it varies both the polarity and the shape of `matchTerm`. Measured:
#   rejected (residual goal `(records.all fun r => conjTerms (matchTerm r) terms)
#   = anyRecord matchTerm terms records`), witness refuted against the reference.
# OUT-OF-DOMAIN (weak-empty-terms-flip): the sibling's empty-terms rival diverges
#   from gold ONLY on the empty-word sub-domain (a row with ZERO terms judged not
#   to clear the vacuous conjunction). This bundle's spec carries
#   `require 0 < terms.length`, so the empty-word input is OUTSIDE the modeled
#   domain: no witness with `terms = []` satisfies the precondition, and a rival
#   agreeing with gold on every non-empty word list is genuinely NOT wrong on
#   this carrier (its only divergence is unreachable). Dropped as out-of-domain,
#   NOT for proof cost. The sibling modeled the zero-word boundary because its
#   contract had no precondition; the velvet twin narrows the domain to the
#   branch the patch actually runs in, so the boundary is not attackable — and
#   should not be fabricated.
# VACUOUS (frame-mutation): the sibling itself marks this class N/A (both inputs
#   are value sequences with no heap permission). It is doubly vacuous here:
#   Lean/Velvet are referentially transparent, `records`, `terms` and `matchTerm`
#   are immutable values (no `mut`), there is no heap and no aliasing, so there is
#   no read-only input to overwrite. Not fabricated.
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
# BINDER / CLAUSE COVERAGE. The obligation has three input binders —
#   `records : List Nat`, `terms : List Nat`, `matchTerm : Nat → Nat → Bool` —
#   and one top-level clause, `result = anyRecord matchTerm terms records`, which
#   internally nests exists-item over for-all-words. The four reject witnesses
#   probe four DISTINCT input points (pts=4): the ∀word∃item chained rival at
#   `records=[0,1]`, `terms=[10,11]`, a two-clause split match; the first-item
#   rival at `records=[0,1]`, `terms=[10]`, a second-item-only match; the any-pair
#   rival at `records=[0]`, `terms=[10,11]`, a single-pair match; and the ∀item
#   rival at `records=[0,1]`, `terms=[10,11]`, a first-item-only match that ignores
#   the word. Thus `records` ranges over [0,1]/[0,1]/[0]/[0,1], `terms` over
#   [10,11]/[10]/[10,11]/[10,11], and `matchTerm` over four distinct match tests —
#   no binder held fixed, and `matchTerm` is varied in KIND (word-dependent vs
#   word-ignoring) as well as in value. The exists-item nesting is attacked from
#   three independent sub-domains (a later-only clearing item, a partial-clear
#   item, and a mixed clearing/non-clearing pair) and from BOTH polarities (three
#   rivals refuted where the spec demands DROP, one where it demands KEEP); the
#   ∃item∀word nesting is attacked by the ∀word∃item chained rival and the
#   ∃item∃word collapse; and the admissibility case pins both the DROP and KEEP
#   branches at the F2P shape. So no rival that mishandled only a fixed shape of
#   one binder, or only one polarity of the clause, could slip through.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job. Here the per-(item,word)
#   match test is not an axiomatized oracle but the FREE input `matchTerm` (an
#   A-reference the R/I legs differential-test), so there is no consumed contract
#   to probe in this lane, and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
