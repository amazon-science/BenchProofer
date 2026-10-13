"""properties.py — G-PBT falsification battery for django__django-16901 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct oddParityReduce`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is judged by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against its ``witness_reference``; see the CARRIER NOTE for why the frozen
solution cannot be that second subject here).

DEFENDED SURFACE (one contracted method over one read-only input):

    oddParityReduce (children : List Bool) return (out : Bool)
      ensures out = parityOdd children

``parityOdd children`` is a total, fully-unfolded pure function: it is ``true``
exactly when an ODD number of the operands hold (``trueCount children % 2 = 1``,
where ``trueCount`` is the running tally of the per-operand 1/0 indicators). It
is a TRANSPARENT ``def`` over the method's own argument — the ``axioms`` region
declares no ``axiom`` and no ``opaque`` leaf — so there is no answer-key oracle
for a rival to echo: the pure region COMPUTES the value from the input rather
than asserting it. This is the chained exclusive-or value the combined predicate
must produce for one row, which is the semantics the issue demands and the
failing test's oracle in spec form. The single load-bearing ``ensures`` clause
pins the result to the PARITY of the tally at EVERY operand count, so there is no
slack: a rival that diverges on ANY operand assignment contradicts the clause.

ONE INPUT BINDER, ``children : List Bool`` — the operand truth values evaluated
on one database row (child order is irrelevant to the value, since addition
commutes). The spec quantifies over every such list, so the binder is varied
along BOTH axes a rival can abuse: the row's LENGTH and its per-element VALUES.
Those two axes are the whole content of the coverage argument below.

WHY BOTH AXES MATTER (the trap this port was re-authored to close). A row whose
operands are ALL TRUE has ``trueCount children = children.length``, so on such
rows the tally and the operand count are the SAME NUMBER and a rival that reads
the count while ignoring the values is indistinguishable from the validator. A
battery probing only all-true rows therefore certifies nothing about the spec's
dependence on the operand VALUES: ``weak-count-parity`` below returns
``children.length % 2 = 1`` and agrees with the frozen solution at every all-true
row of any length. It is refuted only at a MIXED row, which is why two of the
five witness points hold at least one false operand.

ADVERSARIAL READ of the nagini classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl must still verify, else the spec is
    SPEC-TOO-STRONG on the SHAPE of the impl rather than on its VALUE.
  * ADMISSIBILITY — the method carries no ``require`` clause, so the sibling's
    "a normal input satisfies the precondition" probe is not where the risk
    sits. The residual risk on this surface is that the post-image is
    UNSATISFIABLE / DEGENERATE at the interesting point (a spec no impl can meet
    reads like a spec every impl meets). ``admiss-grounded`` discharges an
    in-region assert pinning that the post-image ACCEPTS a five-operand
    odd-count row (the shape the failing test exercises, where parity and
    "exactly one" part company), REJECTS an even-count row, and REJECTS the
    empty row.
  * FRAME-MUTATION — VACUOUS on this backend, and reported rather than
    substituted. The sibling class exists because a read-only heap input may
    carry a fractional permission an impl overwrites. Lean and Velvet are
    referentially transparent: ``children`` is an immutable value (not declared
    ``mut``), there is no heap and no aliasing, so there is no read-only input
    to mutate and no permission system to trip.
  * DIVERGENCE / non-termination - CLOSED BY THE SEMANTICS, measured rather than
    argued, in BOTH the shapes this bundle can express. It sets
    ``loom.semantics.termination "total"`` and opens ``TotalCorrectness``, so the
    verifier discharges a real termination obligation. The naive diverging rival (a
    loop with no ``decreasing`` measure) is REJECTED at the ``method`` itself, and
    is UNWITNESSABLE because that rejection makes the rival's own file
    uncompilable, so no appended witness elaborates against it. The sharper rival
    (a constant measure plus an UNREACHABLE exit) is REJECTED as well, on the
    measure's own descent goal ``⊢ 0 < 0``; a previous revision recorded that one
    as VERIFYING and escalated it as a spec hole, and that is RETRACTED. No spec
    hole is escalated from this class. See the DIVERGENCE footer for the
    measurements and the mechanism.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the parity semantics on some sub-domain and MUST be rejected:
    the "exactly one" fallback (the literal pre-image behaviour — the single
    discriminating delta of the change), the wrong-modulus reduction, the
    inverted decision, the VALUE-BLIND count-parity reduction, and the truncated
    traversal. Each is a loop-free closed form (so its extracted tester
    kernel-reduces) carrying a machine-checked refutation witness.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHAT THE GOLD-SIDE FAILURE IS WORTH.
A witness reaches the post-image through Velvet's own tester machinery
(``oddParityReduceTester children = false`` says the extracted program's result
violates the postcondition at that concrete row) and closes by ``decide``,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. ``decide`` reduces the extracted program by kernel
computation. Each reject rival is a LOOP-FREE closed form, so its tester reduces
over the concrete literal; the FROZEN program keeps a ``while`` loop whose
fixpoint elaborates through ``Classical.choice`` under
``loom.semantics.choice "demonic"``, which the kernel cannot unfold.

READ THAT HONESTLY, because it is the defect that made the previous revision of
this file MALFORMED. The gate's FAIL-on-gold half is satisfied against the frozen
solution for a REDUCTION-STUCK reason, not by a semantic refutation. Measured,
verbatim, for the ``weak-exactly-one`` witness against the frozen impl:

    error: Tactic `decide` failed for proposition
      oddParityReduceTester [true, true, true] = false
    ... did not reduce to `isTrue` or `isFalse`.

That error appears for a TRUE claim about that impl just as readily, so gold's
exit code here carries NO information and a forged witness asserting the rival
is CORRECT would clear both halves. The gate names this ``witness-undecided`` and
refuses the case; the previous revision of this battery recorded exactly that on
all three of its rejects.

The repair is the one the gate prescribes: every reject case names a
``witness_reference`` — ``pos-closed-form``'s loop-free source, a
machine-checked-correct impl of the SAME frozen spec whose extracted tester DOES
reduce. Against it each witness is refuted SEMANTICALLY (measured, all five):

    error: Tactic `decide` proved that the proposition
      oddParityReduceTester [true, true, true] = false
    is false

So each witness holds of its rival and provably FAILS of a verifying impl of the
same spec at the same input on the same carrier shape. That is the discrimination
the stuck-on-gold build cannot supply, and it is ENFORCED rather than merely
documented: the gate independently checks the reference shares the frozen spec
and VERIFIES before refuting anything against it. The reference is also shipped
as an ``expect="verify"`` case in its own right, so the battery itself records
that loop-freeness is not what any rival is being rejected for.

WITNESS PLACEMENT (pts = 5). The five rejects probe five DISTINCT rows spanning
four operand counts and both parity classes of the tally:

    weak-exactly-one     [true, true, true]              count 3, tally 3 (odd)
    weak-mod3            [true, true, true, true, true]  count 5, tally 5 (odd)
    weak-inverted        [true]                          count 1, tally 1 (odd)
    weak-count-parity    [true, true, false]             count 3, tally 2 (even)
    weak-drop-first      [true, false]                   count 2, tally 1 (odd)

The last two are MIXED rows, so the tally and the operand count come apart there
and the value axis of the binder is genuinely exercised. No rival that mishandled
only a fixed operand count, only the all-true diagonal, or only one parity class
could slip through.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the modeled
operation is a pure boolean/arithmetic reduction over already-evaluated operand
truth values (the SQL constructors that assemble the predicate are unchanged and
owed no contract — G-CONF differential-tests them end to end). There is no
consumed contract to probe in this lane, and the gate ignores ``AXIOM_TESTS``
regardless.
"""
import textwrap
from pathlib import Path

INSTANCE = "django__django-16901"
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

# The WHOLE executable body of the method: the backward accumulating loop over
# the operand truth values. Every reject rival replaces this with a loop-free
# closed form, so its extracted tester kernel-reduces (see the CARRIER NOTE).
_IMPL = """    -- impl-start
    let mut count : Nat := 0
    let mut i := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant count = trueCount (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      count := (if c then 1 else 0) + count
      i := i - 1
    return (decide (0 < count)) &&
      decide ((if children.length > 2 then count % 2 else count) = 1)
    -- impl-end"""

# The final `return` of the frozen impl (the combined predicate). Reshaping only
# this keeps the loop and its invariants, so the frozen proof still closes after
# a matching one-line retune.
_RET = ("    return (decide (0 < count)) &&\n"
        "      decide ((if children.length > 2 then count % 2 else count) = 1)")

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut count : Nat := 0"

# The closing tactic block of the frozen proof: the parenthesized, BULLET-FREE
# script that discharges the method's single remaining value goal. Bullet-free so
# the same text can be spliced into a `first | ... | ...` alternation arm (see
# `admiss-grounded`, which needs exactly that) — but NOT verbatim: Lean's
# whitespace-sensitive parser closes a parenthesized tactic group at the first
# line indented at or left of the group's opening column, so an arm nested deeper
# than this block's own 4/5-space body must RE-INDENT the continuation lines.
# `_arm()` below does that; splicing this text unshifted ends the group early with
# `unexpected token 'have'; expected ')'`. It lives in the tactic body, which the
# spec view elides, so its content is a proof detail rather than part of the
# contract, and it must stay byte-identical to Solution.lean's own closing block
# (that identity is what `_swap` asserts at import).
_CLOSE = """    (unfold parityOdd;
     have hle := trueCount_le_length children;
     by_cases hlen : children.length > 2 <;>
       simp only [hlen, if_true, if_false] <;>
       first
         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
                trueCount children = 2 := by omega;
            rcases hb with h | h | h <;> rw [h] <;> decide)
         | (by_cases hpar : trueCount children % 2 = 1 <;>
              [ (have hpos : 0 < trueCount children := by omega;
                 simp [hpar, hpos]) ; simp [hpar] ]))"""

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A variant that reshapes the impl retunes this; the tactic body is
# elided from the spec view, so that is a proof reshape, not a spec change.
_PROOF = """prove_correct oddParityReduce by
  loom_solve
  · rw [trueCount_drop_step children i (by omega) (by omega)]
    rw [‹count = trueCount (children.drop i)›]
  · injection i_3 with hc _
    subst done_1
    simp only [List.drop_zero] at invariant_2
    rw [← hc, invariant_2]
""" + _CLOSE

# The proof a loop-free variant needs: with no loop there is no drop-step goal
# and no invariant to discharge, so the single remaining goal closes by
# unfolding the post-image. Measured to close for every loop-free variant here.
_PROOF_LOOPFREE = ("prove_correct oddParityReduce by\n"
                   "  loom_solve\n"
                   "  simp_all [parityOdd]")


def _arm(indent):
    """`_CLOSE` re-indented to sit inside a `first | ...` arm at `indent` columns.

    The block is one parenthesized, semicolon-separated tactic group. Lean ends
    such a group at the first line whose indentation falls to or below the
    opening column, so every continuation line has to be pushed strictly right
    of the arm's `|`. The tactic TEXT is unchanged — only leading whitespace
    moves — so the spliced proof is the same script as Solution.lean's.
    """
    lines = textwrap.dedent(_CLOSE).rstrip("\n").split("\n")
    return "\n".join([lines[0]] + [indent + ln for ln in lines[1:]])


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


def _loopfree(body):
    """A full variant whose impl is the loop-free `body`, with the matching proof.

    `body` is the single `return` line of the closed form. The loop, its two
    invariants and its `done_with` clause all go, so the frozen proof's two
    bullet goals no longer exist and `_PROOF_LOOPFREE` replaces them.
    """
    return _swap2(_IMPL,
                  "    -- impl-start\n" + body + "\n    -- impl-end",
                  _PROOF, _PROOF_LOOPFREE)


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A loop-free impl that returns the parity bit of the
# tally directly: machine-checked-correct against the frozen spec (it is shipped
# as the `pos-closed-form` positive below, and the gate re-verifies it here
# before refuting anything against it), and — unlike the frozen loop — its
# extracted tester REDUCES, so `decide` can decide claims about it. Every reject
# case names it as its `witness_reference`, because the FROZEN impl cannot serve
# as the witness's second subject on this carrier; see the CARRIER NOTE.
# ---------------------------------------------------------------------------
_REFERENCE = _loopfree("    return decide (trueCount children % 2 = 1)")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `oddParityReduceTester children = false` says the extracted
# ---- program's result violates the postcondition at that concrete row. Checked
# ---- in a file whose `prove_correct` block is stripped. Every argument is a
# ---- concrete `List Bool` literal, so no conditioning on the carrier is needed
# ---- and the witness heads bind nothing (no consistency probe to satisfy).
def _tester(body):
    return ("extract_program_for oddParityReduce\n"
            "prove_precondition_decidable_for oddParityReduce\n"
            "prove_postcondition_decidable_for oddParityReduce\n"
            "derive_tester_for oddParityReduce\n\n" + body)


def _witness(row):
    return _tester(f"example : oddParityReduceTester {row} = false := by\n"
                   "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = parityOdd
    # children` obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-commuted-and",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: COMMUTE the final conjunction (the equality on the
        # small-arity-bypassed reduction first, the positivity guard second).
        # Same value on every row; the loop and its front-recursive invariant are
        # unchanged, so the frozen proof still closes after one extra
        # `Bool.and_comm` rewrite before the frozen closing block.
        "module": _swap2(
            _RET,
            "    return decide ((if children.length > 2 then count % 2 else count) = 1) &&\n"
            "      (decide (0 < count))",
            _PROOF,
            "prove_correct oddParityReduce by\n"
            "  loom_solve\n"
            "  · rw [trueCount_drop_step children i (by omega) (by omega)]\n"
            "    rw [‹count = trueCount (children.drop i)›]\n"
            "  · injection i_3 with hc _\n"
            "    subst done_1\n"
            "    simp only [List.drop_zero] at invariant_2\n"
            "    rw [← hc, invariant_2]\n"
            "    rw [Bool.and_comm]\n"
            + _CLOSE),
        "rationale": "commuting the final conjunction computes the same result "
                     "value-for-value with the loop and invariant unchanged, so "
                     "`out = parityOdd children` still holds and the frozen proof "
                     "closes (one added `Bool.and_comm`); a correct reshape must "
                     "verify, else SPEC-TOO-STRONG on the conjunction order. "
                     "(Sibling: pos-reorder-commute, conjunction-commute half.)",
    },
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly: return the parity bit of the whole tally. A completely
        # different control-flow shape (no loop, no accumulator, no small-arity
        # branch) computing the identical decision. This exact source is ALSO the
        # `witness_reference` every reject case is refuted against, so shipping it
        # as a positive is what records that loop-freeness is not the ground of
        # any rejection: the gate sees this same text VERIFY here.
        "module": _REFERENCE,
        "rationale": "a loop-free impl that returns the parity bit directly must "
                     "satisfy `out = parityOdd children`; a correct reshape of the "
                     "modeled behaviour verifying is exactly what SPEC-TOO-STRONG "
                     "would deny. Exercises the obligation from a maximally "
                     "different (loop-free) control-flow shape. Doubles as the "
                     "`witness_reference` for the whole reject lane, so its passing "
                     "here certifies the subject those refutations are checked "
                     "against. (Sibling: the branch-reorder half of "
                     "pos-reorder-commute, taken to its closed form.)",
    },
    {
        "id": "pos-guard-boundary",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. Move the small-arity guard from `> 2` to `≥ 2` — the one
        # boundary no other positive touches. This is NOT a no-op reshape: at
        # length exactly 2 the rival takes the parity branch where the frozen impl
        # takes the raw-tally branch, so the two impls compute the conjunction by
        # DIFFERENT routes there and the frozen closing block no longer applies
        # off-the-shelf. It is still behaviourally identical, because on a
        # two-operand row the tally is bounded by 2 and "positive and tally = 1"
        # coincides with "positive and tally % 2 = 1"; the retuned proof discharges
        # exactly that coincidence inline (no new top-level lemma, so the variant
        # stays in scope). Guards the risk that the spec is SPEC-TOO-STRONG on the
        # guard's exact form rather than on the value it selects — a spec that only
        # admitted impls whose guard is spelled one particular way would pin
        # syntax, not behaviour.
        "module": _swap2(
            "      decide ((if children.length > 2 then count % 2 else count) = 1)",
            "      decide ((if children.length ≥ 2 then count % 2 else count) = 1)",
            _PROOF,
            "prove_correct oddParityReduce by\n"
            "  loom_solve\n"
            "  · rw [trueCount_drop_step children i (by omega) (by omega)]\n"
            "    rw [‹count = trueCount (children.drop i)›]\n"
            "  · injection i_3 with hc _\n"
            "    subst done_1\n"
            "    simp only [List.drop_zero] at invariant_2\n"
            "    rw [← hc, invariant_2]\n"
            "    unfold parityOdd\n"
            "    have hle := trueCount_le_length children\n"
            "    by_cases hlen : children.length ≥ 2\n"
            "    · simp only [hlen, if_pos]\n"
            "      by_cases hpar : trueCount children % 2 = 1\n"
            "      · have hpos : 0 < trueCount children := by omega\n"
            "        simp [hpar, hpos]\n"
            "      · simp [hpar]\n"
            "    · have hb : trueCount children = 0 ∨ trueCount children = 1 := by omega\n"
            "      simp only [hlen, if_neg]\n"
            "      rcases hb with h | h <;> simp [h]"),
        "rationale": "shifting the small-arity guard to `≥ 2` selects a DIFFERENT "
                     "branch at length exactly 2 (parity instead of raw tally), so "
                     "it is not a syntactic no-op, yet it computes the same value on "
                     "every row: at length 2 the tally is at most 2, where "
                     "'positive and tally = 1' and 'positive and tally % 2 = 1' "
                     "coincide. Verifying is what SPEC-TOO-STRONG on the GUARD's "
                     "form would deny — the frozen collapse lemma is stated at "
                     "`> 2`, and the retuned proof has to re-derive the boundary "
                     "coincidence rather than cite it. Probes the length-2 boundary "
                     "that pos-commuted-and (conjunction order) and pos-closed-form "
                     "(no branch at all) both leave untouched. (Sibling: the "
                     "branch-guard-complement half of pos-reorder-commute, which "
                     "complements `> 2` to `<= 2`; taken here to the adjacent "
                     "boundary, which is the stronger form of the same probe.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries no `require` clause, so the "a normal
    # input satisfies the precondition" probe is not where the risk sits. The
    # residual risk here is that the post-image is UNSATISFIABLE / DEGENERATE at
    # the interesting point. This case discharges an in-region assert at concrete
    # rows, establishing that the post-image really does ACCEPT a five-operand
    # odd-count row (the shape the failing test exercises, where parity and
    # "exactly one" diverge), REJECT an even-count row, and REJECT the empty row.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is LIVE (a false claim about the same points leaves
    # an unsolved goal), and the proof's alternation gains one `decide` arm.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL_TOP,
            "    assert (with_name_prefix `assert\n"
            "      (parityOdd [true, true, true, true, true] = true ∧\n"
            "       parityOdd [true, true] = false ∧\n"
            "       parityOdd ([] : List Bool) = false))\n"
            "    let mut count : Nat := 0",
            _PROOF,
            "prove_correct oddParityReduce by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [trueCount_drop_step children i (by omega) (by omega)];\n"
            "       rw [‹count = trueCount (children.drop i)›])\n"
            "    | (injection i_3 with hc _;\n"
            "       subst done_1;\n"
            "       simp only [List.drop_zero] at invariant_2;\n"
            "       rw [← hc, invariant_2];\n"
            "       " + _arm("       ") + ")"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "rows the failing test exercises: it demands ACCEPT for a "
                     "five-operand row with an odd tally (where parity and "
                     "'exactly one' diverge — the case the change targets), "
                     "REJECT for a two-operand both-true row (even tally), and "
                     "REJECT for the empty row. The in-region assert must "
                     "discharge (else the obligation is unsatisfiable / "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so "
                     "`out = parityOdd children` still verifies. The closing "
                     "block reaches the alternation arm through `_arm()`, which "
                     "re-indents it: spliced unshifted it fails to PARSE "
                     "(`unexpected token 'have'`), which the gate reports as "
                     "PRECOND-TOO-STRONG even though the post-image is fine. "
                     "(Sibling: "
                     "admiss-reads, re-aimed — the half-permission read fact has "
                     "no analogue on a referentially-transparent carrier with no "
                     "`require`.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a loop-free closed form (so its extracted
    # tester kernel-reduces) with a machine-checked refutation witness at a
    # concrete row, refuted against the shared `witness_reference` because the
    # frozen loop cannot decide anything (CARRIER NOTE), plus the refinement
    # argument that its faithful real counterpart would NOT resolve the failing
    # test.
    # =====================================================================
    {
        "id": "weak-exactly-one",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image bug. Drop the parity reduction entirely: accept a row iff
        # EXACTLY ONE operand holds, at every operand count. Correct on rows of at
        # most two operands (where a tally cannot exceed two, so "exactly one"
        # coincides with "odd"), wrong the moment the tally exceeds two. The
        # nagini weak-no-mod and weak-eq-true rivals collapse to this single
        # closed form on this carrier (both reduce to `trueCount = 1`).
        "module": _loopfree(
            "    return (decide (0 < trueCount children)) && "
            "decide (trueCount children = 1)"),
        "refinement": "this is the literal pre-image behaviour: the fallback "
                      "compared the raw tally to one ('exactly one operand "
                      "holds') with no parity reduction. Its faithful real "
                      "counterpart is the UNCHANGED buggy fallback, which on the "
                      "failing test's five-clause chained exclusive-or selects the "
                      "wrong rows — a row with three holding operands is "
                      "exclusive-or-true (an odd tally) but the exactly-one "
                      "fallback rejects it. It would NOT resolve; this is the "
                      "single discriminating delta of the change. (Sibling: "
                      "weak-no-mod / weak-eq-true, merged.)",
        "rationale": "REJECT from `out = parityOdd children`: for more than two "
                     "operands `parityOdd` folds parity over the whole tally, so a "
                     "three-holding-operand row is `true` (three is odd) while the "
                     "rival tests `trueCount = 1` and returns `false`. "
                     "PARTIAL-DOMAIN: correct on the ≤2-operand sub-domain, wrong "
                     "once the tally exceeds two. Refuted at a three-operand "
                     "all-true row (count 3, tally 3).",
        "witness": _witness("[true, true, true]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-mod3",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong-modulus near-miss: reduce the tally modulo 3 instead of 2 for more
        # than two operands. Agrees with parity on tallies 0, 1, 2 (and on the
        # positivity guard), but diverges whenever the tally's remainder mod 3
        # differs from its parity — a five-holding-operand row gives
        # `5 % 3 = 2 ≠ 1` (reject) while parity demands `5 % 2 = 1` (accept). A
        # three-holding row also diverges (`3 % 3 = 0`), but this is refuted at
        # five operands to move the binder to a count distinct from
        # weak-exactly-one's.
        "module": _loopfree(
            "    return (decide (0 < trueCount children)) &&\n"
            "      decide ((if children.length > 2 then trueCount children % 3 "
            "else trueCount children) = 1)"),
        "refinement": "reducing modulo 3 is not the n-ary exclusive-or semantics "
                      "— the chained exclusive-or holds iff an ODD number of "
                      "operands hold, which is remainder mod 2, not mod 3. A real "
                      "patch with a mod-3 reduction still mis-selects rows on the "
                      "failing test's five-clause chained exclusive-or (a "
                      "five-holding-operand row is exclusive-or-true but "
                      "`5 % 3 = 2 ≠ 1`, so it is rejected). It would NOT resolve. "
                      "(Sibling: weak-mod3.)",
        "rationale": "REJECT from `out = parityOdd children`: for more than two "
                     "operands the rival's derived count is `trueCount % 3`, but "
                     "`parityOdd` requires `trueCount % 2 = 1`. On a "
                     "five-holding-operand row the rival gives `5 % 3 = 2` "
                     "(reject) while `parityOdd` is `true` (`5 % 2 = 1`). "
                     "PARTIAL-DOMAIN: agrees on tallies 0/1/2, diverges when the "
                     "mod-3 value differs from parity. Refuted at a five-operand "
                     "all-true row (count 5, tally 5) — a distinct operand count "
                     "from weak-exactly-one's, and it is a NEAR-MISS of that "
                     "rival (it agrees with gold wherever the tally is at most "
                     "two), so it carries its own separating point rather than "
                     "sharing one.",
        "witness": _witness("[true, true, true, true, true]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-count-parity",
        "kind": "uniqueness",
        "expect": "reject",
        # THE VALUE-BLIND rival, and the case this port was re-authored to add.
        # Return the parity of the operand COUNT, ignoring the operand VALUES
        # entirely. On an all-true row the tally EQUALS the count, so this rival
        # is indistinguishable from the validator at every all-true row of every
        # length — including all three rows the previous revision of this battery
        # probed. It is refuted only at a MIXED row, which is exactly why the
        # value axis of the binder has to be exercised and not just its length.
        "module": _loopfree("    return decide (children.length % 2 = 1)"),
        "refinement": "keying the decision on the NUMBER of operands rather than "
                      "on how many of them hold is not the exclusive-or at all: "
                      "it returns the same answer for every row, so the predicate "
                      "would select either all rows or none on any given query. "
                      "The failing test asserts specific row sets for chained "
                      "exclusive-ors of one through five clauses, so a real patch "
                      "computing this would mis-select on every one of them (for "
                      "the five-clause chain it selects every row, including rows "
                      "where no clause holds). It would NOT resolve. (Sibling: no "
                      "direct counterpart — the nagini carrier keeps the operand "
                      "values in a PSeq the fold consumes elementwise, so the "
                      "count/tally conflation this exploits does not arise there. "
                      "Added because on THIS carrier it is the near-miss that "
                      "survives an all-true-only witness set.)",
        "rationale": "REJECT from `out = parityOdd children`: `parityOdd` folds "
                     "parity over the TALLY of holding operands, and this rival "
                     "folds it over the LENGTH of the list, so the two agree only "
                     "where tally = length (the all-true diagonal) or where their "
                     "parities happen to coincide. The verifier leaves precisely "
                     "the goal `children.length % 2 = 1 ↔ trueCount children % 2 "
                     "= 1`, which is not a theorem. Refuted at a three-operand "
                     "row with ONE false operand (count 3, tally 2): the rival "
                     "returns `true` (count odd) where the validator returns "
                     "`false` (tally even). This is the ONLY rival here whose "
                     "witness must be a MIXED row — an all-true witness of any "
                     "length would not discriminate it, so it pins the spec's "
                     "dependence on the operand VALUES rather than on their "
                     "number.",
        "witness": _witness("[true, true, false]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # TRAVERSAL-TRUNCATION rival: fold the parity over every operand EXCEPT
        # the first. An off-by-one in the traversal rather than in the arithmetic,
        # so it attacks the clause from a different direction than the modulus
        # rivals: the reduction is right and the DOMAIN it is taken over is wrong.
        # Wrong on exactly those rows whose first operand holds.
        "module": _loopfree(
            "    return decide (trueCount (children.drop 1) % 2 = 1)"),
        "refinement": "omitting one operand from the tally is not the n-ary "
                      "exclusive-or of the operands it was given — it computes the "
                      "chained exclusive-or of a strictly smaller clause set. On "
                      "the failing test's chains a row whose first clause holds is "
                      "then classified by the parity of the REMAINING clauses, "
                      "which inverts the answer for exactly those rows (the "
                      "one-clause chain degenerates to selecting nothing at all). "
                      "It would NOT resolve. (Sibling: no direct counterpart — the "
                      "nagini battery's rivals all keep the full traversal and "
                      "vary the arithmetic; this attacks the traversal's extent, "
                      "which is a distinct way to be wrong on this carrier.)",
        "rationale": "REJECT from `out = parityOdd children`: `parityOdd` is the "
                     "parity of the tally over ALL operands, and the rival takes "
                     "it over the tail, so the two differ on exactly the rows "
                     "whose first operand holds (dropping a holding operand flips "
                     "the parity). The verifier leaves the goal `trueCount "
                     "children.tail % 2 = 1 ↔ trueCount children % 2 = 1`, which "
                     "is not a theorem. Refuted at a two-operand MIXED row whose "
                     "first operand holds (count 2, tally 1): the validator "
                     "returns `true` (tally odd) and the rival returns `false` "
                     "(the tail's tally is 0). Probes the small-arity regime at a "
                     "count no other rival's witness uses, and is the second of "
                     "the two mixed rows, so the value axis is exercised at two "
                     "different lengths.",
        "witness": _witness("[true, false]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        # Polarity rival: return the NEGATION of the parity decision. Accepts
        # exactly the rows the validator rejects and vice versa. Refuted in the
        # small-arity regime (a single operand) where the exactly-one and
        # wrong-modulus rivals AGREE with the validator, so it attacks a strictly
        # different sub-domain and pins the polarity of the result.
        "module": _loopfree("    return !decide (trueCount children % 2 = 1)"),
        "refinement": "returning the inverse decision accepts every row the "
                      "exclusive-or rejects and rejects every one it accepts, the "
                      "opposite of the intended predicate — it resolves nothing on "
                      "any exclusive-or test, and inverts the answer on every one "
                      "of the failing test's chains. (Sibling: no direct "
                      "counterpart; the polarity attack the nagini battery leaves "
                      "to Viper's own value check, made explicit here because on a "
                      "tactic-proof backend nothing checks it implicitly.)",
        "rationale": "REJECT from `out = parityOdd children`: the negated decision "
                     "contradicts the pinned value on EVERY row, accepted and "
                     "rejected alike. Verifying would be SPEC-TOO-WEAK on the "
                     "polarity of the result. Refuted at a single-operand holding "
                     "row (count 1, tally 1, odd → accept), where the rival "
                     "returns `false` — the small-arity sub-domain where "
                     "weak-exactly-one and weak-mod3 AGREE with the validator, so "
                     "this near-miss carries its own separating witness rather "
                     "than sharing one.",
        "witness": _witness("[true]"),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 1 frame-mutation rival, 1
# control-flow/non-termination rival, 3 uniqueness/partial-domain rivals) plus
# an empty AXIOM_TESTS. The sibling contracts ONE function,
# `xor_fallback_matches(operands: List[int]) -> bool`, over a `List[int]`
# carrying a fractional heap permission and a MustTerminate obligation, with the
# parity decision spelled deeply. This bundle contracts ONE method,
# `oddParityReduce`, over a `List Bool` under TOTAL-correctness semantics
# (`set_option loom.semantics.termination "total"`, Solution.lean line 4); the
# value surface carries across intact (per-operand truth values, the parity
# fold, the small-arity-bypassed reduction), and the termination obligation DOES
# have a counterpart here (the frozen loop carries `decreasing i`), while the
# permission surface does not exist. An audit corrected the claim that this
# bundle is `partial`; see the DIVERGENCE footer for what that changes.
#
#   sibling case            kind          -> here                     disposition
#   ---------------------------------------------------------------------------
#   pos-reorder-commute     soundness     -> pos-commuted-and         PORTED (commute half)
#                                         -> pos-closed-form          PORTED (reorder half)
#   admiss-reads            admissibility -> admiss-grounded          RE-AIMED
#   frame-mut-write         uniqueness    -> (none)                   VACUOUS
#   weak-no-mod             uniqueness    -> weak-exactly-one         PORTED
#   weak-eq-true            uniqueness    -> weak-exactly-one         SUBSUMED
#   weak-mod3               uniqueness    -> weak-mod3                PORTED
#   weak-nonterm            uniqueness    -> (none)                   SPLIT: see DIVERGENCE
#                                                                     (a) no measure: REJECTED,
#                                                                         unwitnessable
#                                                                     (b) const measure +
#                                                                         unreachable exit:
#                                                                         REJECTED on |- 0 < 0
#   (—)                     uniqueness    -> weak-count-parity        ADDED
#   (—)                     uniqueness    -> weak-drop-first          ADDED
#   (—)                     uniqueness    -> weak-inverted-decision   ADDED
#
# PORTED (pos-reorder-commute -> pos-commuted-and + pos-closed-form): the sibling
#   positive both COMMUTES the final conjunction and REORDERS the small-arity
#   branch. Here that splits cleanly into two independent reshapes:
#   pos-commuted-and commutes the conjunction (loop and invariant unchanged, the
#   frozen proof closes with one added `Bool.and_comm`), and pos-closed-form
#   collapses the whole loop and branch to the parity bit the post-image names (a
#   maximally different, loop-free control-flow shape, reproven by
#   `simp_all [parityOdd]`). The second also serves as the reject lane's
#   `witness_reference`.
# RE-AIMED (admiss-reads -> admiss-grounded): the sibling asserts the
#   half-permission admits reading the length and first element — a permission
#   fact with no analogue on a referentially-transparent carrier with no
#   `require` clause. Re-aimed to the sharper residual risk here: a degenerate
#   post-image. The case discharges a live in-region assert pinning ACCEPT (a
#   five-operand odd-tally row), REJECT (an even-tally row), and REJECT (the
#   empty row) at concrete inputs.
# SUBSUMED (weak-eq-true): on the sibling this is a SECOND phrasing of the
#   exactly-one bug (`total == 1` with the parity branch deleted, vs. `rhs =
#   total; rhs == 1`). On this carrier both reduce to the identical closed form
#   `decide (trueCount children = 1)`, so they collapse to a single rival
#   (weak-exactly-one). Not a distinct wrongness here; folded and noted rather
#   than duplicated as two cases with the same module text.
# VACUOUS (frame-mut-write): the sibling's mandatory frame-mutation rival writes
#   back into the read-only input held at a half permission and is rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent and
#   `children` is an immutable value (not declared `mut`), so there is no
#   read-only input to overwrite and no permission system to trip. The class
#   genuinely collapses on this carrier — omitted as vacuous, NOT fabricated,
#   per the porting map.
#
# DIVERGENCE (weak-nonterm) — TWO rivals, two different dispositions. An audit of
#   this file corrected the claim that stood here before: the previous revision
#   said this bundle runs under `loom.semantics.termination "partial"` and so
#   admits a diverging rival vacuously. That is FALSE OF THIS ARTIFACT — line 4 of
#   Solution.lean reads `set_option loom.semantics.termination "total"` — and the
#   two rivals it conflated behave oppositely. Both re-measured with real builds:
#
#   (a) NO MEASURE — `while True do pure ()` spliced at the top of the impl, proof
#       reduced to a bare `loom_solve`. REJECTED (exit 1):
#         error: Decreasing annotations are required in total correctness semantics
#       So the class is NOT a hole in the direction the old note claimed: under
#       `total` the obligation is real and this rival does not verify. It is,
#       however, UNWITNESSABLE, and that is measured rather than assumed: the
#       error is raised at the METHOD DECLARATION, so a witness file built on this
#       rival never reaches its own `example`. A trivially TRUE witness
#       (`example : 1 + 1 = 2 := by decide`) against this rival exits 1 with that
#       same declaration error, while the identical witness against the frozen
#       solution exits 0. A case shipped anyway would record `witness-unproven`
#       and force MALFORMED-TESTS, so shipping it would BREAK a sound battery.
#       Disposition: closed by the spec, unwitnessable by construction.
#
#   (b) CONSTANT MEASURE + UNREACHABLE EXIT - REJECTED TOO (exit 1), and this
#       RETRACTS the SPEC HOLE a previous revision escalated for exactly this
#       rival. The rival, verbatim as that revision wrote it:
#         let mut z : Nat := 0
#         while 0 < 1
#           invariant True
#           done_with 1 < 0
#           decreasing (0 : Nat)
#         do
#           z := z + 1
#         return false
#       The claim was that this VERIFIES at exit 0 while returning an unambiguously
#       wrong value, because the `decreasing` annotation is recorded and never
#       proven to decrease. Re-measured on this bundle with a real build, it is
#       REJECTED on the measure's OWN goal: `unsolved goals case
#       «decreasing_1: (0 : Nat)» ... |- 0 < 0`. So `ensures out = parityOdd
#       children` is never reached, the unreachable `done_with 1 < 0` launders
#       nothing, and there is no hole in this direction.
#       Mechanism, since the retracted claim came from reading the annotation alone:
#       `set_option loom.semantics.termination "total"` ITSELF opens the
#       `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean` -- the
#       option handler calls `openScope \`TotalCorrectness`), the frozen file opens
#       that scope explicitly as well, and
#       `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
#       `measure b' < measure b` as a goal. The `PartialCorrectness` twin is the one
#       that takes a measure and DISCARDS it, and it is never opened here, so the
#       two header lines agree and the descent obligation is genuinely enforced.
#       Nothing is ESCALATED from this class: no `spec_holes` entry, and the earlier
#       cross-reference to a corpus-wide "obligation accepts a non-decreasing
#       measure" finding does not apply to this cell. Not shippable as a reject case
#       either, but only on witness mechanics: the rejection attests to the
#       termination obligation rather than to the parity decision, and the rival's
#       un-normalised loop term defeats a witness of this battery's shape.
#       On the lean sibling backend the whole class is vacuous, since
#       `implementation_*` is a total Lean `def`.
#
# ADDED (weak-count-parity): the value-blind rival, and the reason this file was
#   re-authored beyond repairing the witness subject. On an ALL-TRUE row the tally
#   equals the operand count, so a rival reading `children.length` while ignoring
#   the operand values agrees with the validator at every all-true row of every
#   length — including all three rows the previous revision probed. The battery
#   would have certified a spec whose dependence on the operand VALUES it never
#   tested. Refuted at a mixed row (count 3, tally 2), where the verifier's
#   residual goal is literally `children.length % 2 = 1 ↔ trueCount children % 2
#   = 1`. No sibling counterpart: the nagini carrier's fold consumes the operand
#   values elementwise out of a PSeq, so the count/tally conflation this exploits
#   does not arise there.
# ADDED (weak-drop-first): traversal truncation — the reduction is right and the
#   domain it is taken over is wrong (the tail instead of the whole row). Attacks
#   the clause from a different direction than the arithmetic rivals and adds the
#   second MIXED witness row, at a different length (count 2, tally 1). The
#   sibling's rivals all keep the full traversal and vary the arithmetic.
# ADDED (weak-inverted-decision): a polarity near-miss. Refuted in the
#   small-arity regime (a single holding operand) where weak-exactly-one and
#   weak-mod3 AGREE with the validator, so it attacks a strictly different
#   sub-domain and moves the binder to operand count 1. The sibling leaves
#   polarity to Viper's own value check; on a tactic-proof backend nothing checks
#   it implicitly, so it is made explicit. A real divergence with a
#   machine-checked witness, not fabricated wrongness.
#
# WITNESS SUBJECT (the defect that made the previous revision MALFORMED). All
#   three of its reject cases recorded `witness-undecided`: the witnesses were
#   refuted against the FROZEN solution, whose `while` loop elaborates through
#   `Classical.choice` under `loom.semantics.choice "demonic"`, so the kernel
#   cannot reduce the tester and `decide` is stuck for EVERY claim about it
#   regardless of truth. The gold-side exit code therefore carried no information
#   and a forged witness asserting the rival CORRECT would have cleared both
#   halves. Repaired the way the gate prescribes: every reject case names
#   `pos-closed-form`'s loop-free source as its `witness_reference`, and each
#   witness was measured to be refuted there SEMANTICALLY (`decide` proved the
#   proposition false, exit 1, all five) rather than by stuck reduction. The
#   reference is gate-checked to share the frozen spec and to VERIFY before any
#   refutation is credited to it, and it is shipped as a positive in its own
#   right so the battery records that loop-freeness grounds no rejection.
#
# BINDER / CLAUSE COVERAGE. The obligation has ONE input binder,
#   `children : List Bool`, and ONE top-level clause, `out = parityOdd children`.
#   The five reject witnesses probe five DISTINCT rows (pts = 5) across FOUR
#   operand counts (1, 2, 3, 5) and BOTH parity classes of the tally, and two of
#   them are MIXED rows — so the binder is varied along both axes a rival can
#   abuse, its LENGTH and its per-element VALUES, rather than being pinned to the
#   all-true diagonal where those two axes coincide. The parity requirement is
#   attacked from two independent >2-operand arithmetic sub-domains (the
#   exactly-one fallback at count 3, the wrong modulus at count 5), from the
#   traversal's extent (count 2), from value-blindness (count 3, mixed), and the
#   result polarity is attacked in the small-arity regime (count 1); the
#   admissibility case independently pins the accept branch (odd tally), an
#   even-tally reject, and the empty row. Every rival that agrees with the
#   validator on part of the domain carries a witness at a point where it
#   actually diverges, so no rationale claims a sub-domain the manifest does not
#   demonstrate.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the modeled operation is a deep boolean/arithmetic reduction; the SQL
# constructors are unchanged and owed no contract), so there is nothing to probe
# there, and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
