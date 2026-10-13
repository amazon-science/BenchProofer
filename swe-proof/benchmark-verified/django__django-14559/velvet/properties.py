"""properties.py — G-PBT falsification battery for django__django-14559 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct totalRowsMatched`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and be
REFUTED against a correct impl of the same spec — here the loop-free
``witness_reference``, because the frozen ``while``-loop impl decides nothing at
all; see WHY EVERY REJECT CASE CARRIES A ``witness_reference`` below).

DEFENDED SURFACE (one contracted method):

  totalRowsMatched (matched : List Nat) return (out : Nat)
    ensures out = totalMatched matched

``totalMatched`` is a total, fully-unfolded pure function of the method's own
argument: the running total (front-recursive fold with ``+``) of the sequence of
per-invocation counts, with an empty sequence totalling to zero. The single
load-bearing ``ensures`` clause pins the result to ``totalMatched matched`` — the
sum of EVERY element of the input sequence, grounded in the method's own carrier
(``matched``), never an opaque answer key. The only free INPUT BINDER is
``matched``, a ``List Nat``; its length and its element values are the two axes a
rival can abuse, and the reject witnesses below vary both (a single count, two
counts, a count at a different value, and a three-element sequence with a
repeated value and a large tail) so no rival is refuted at a point another rival
already pins.

CARRIER NARROWING (why this is far smaller than the nagini sibling). The nagini
battery contracts one function over a permission-bearing read-only integer list
plus a ``group_size`` parameter, and its rivals attack the GROUPING/offset loop
that folds per-group counts front-to-back, plus a fractional-permission frame.
This backend models only the purely-functional core the changed behavior turns
on: the aggregate is the running total of the sequence of per-invocation counts,
where that sequence (``matched``) is ALREADY the post-grouping per-invocation
counts — one element per invocation. So ``group_size``, the offset loop, and the
grouping arithmetic are not part of this carrier at all: the sibling's grouping
rivals (per-element split, sliding-window double-count) have no group structure
here to mis-slice. What survives is one obligation over one sequence binder —
"return the SUM of every element" — and every reject rival below attacks that.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * CONSTANT / PRE-PATCH ECHO — APPLIES and is the headline probe. Returning a
    constant (the pre-change behavior contributed no running total) satisfies
    nothing about the sum on a non-empty sequence. ``weak-const-zero``.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on a sub-domain (a
    single-element sequence) but dropping later contributions. ``weak-first-only``
    (reports only the leading count; right iff length ≤ 1) and
    ``weak-drop-last`` (sums all but the final count; right iff the sequence is
    empty).
  * STRUCTURAL / WRONG-AGGREGATE — the sibling's grouping rivals collapse here to
    "aggregate the wrong quantity of the sequence": ``weak-count-elements``
    returns the NUMBER of invocations rather than the sum of their counts (right
    iff every count is 1), and ``weak-double-lead`` adds the leading count twice
    (the double-count analogue; right iff the leading count is 0).
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling's class
    exists because a read-only input may carry a fractional heap permission an
    impl can overwrite, and is rejected for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent; ``matched`` is an immutable value (this
    bundle declares no ``mut`` parameter — the only ``mut`` bindings are the
    loop-local accumulator and cursor), there is no heap and no aliasing, so
    there is no read-only input to mutate and no permission system to trip.
    Reported N/A, not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. ``totalMatched`` is a total, fully-unfolded
    ``def`` of the method's own argument (the ``axioms`` region declares no
    ``axiom`` — the unchanged callee supplies only the non-negative per-invocation
    counts, carried by the ``Nat`` type and validated by G-AX, owed no consumed
    contract). There is no opaque answer key to echo — evaluating ``totalMatched``
    IS the correct answer — so there is no WRONG echo to build. Honest
    cheapest-reshape POSITIVE CONTROLS stand in.

WITNESS MECHANICS on this carrier. The spec is a ``method`` CONTRACT, not a bare
predicate, so a witness reaches it through Velvet's own tester machinery:
``totalRowsMatchedTester <seq> = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. Each reject rival is written STRAIGHT-LINE (a single
``let out := <expr>; return out``), so ITS tester reduces and ``decide`` settles
it. No ``sorry``/``admit``/``native_decide``/``axiom`` is involved.

WHY EVERY REJECT CASE CARRIES A ``witness_reference``. The FROZEN impl keeps a
``while`` loop, which under ``loom.semantics.choice "demonic"`` elaborates
through a fixpoint the kernel cannot unfold. So the frozen method's tester does
not reduce at ANY of these points — and crucially it does not reduce for a TRUE
claim either. Measured directly while porting this cell::

    example : totalRowsMatchedTester [1] = false   -- vs frozen: `decide` STUCK
    example : totalRowsMatchedTester [1] = true    -- vs frozen: `decide` STUCK

Both fail with the identical "did not reduce to `isTrue` or `isFalse`". That
means the frozen side's exit code carries NO information: it fails for
everything, so it cannot testify that a witness discriminates, and a forged
witness asserting the rival is CORRECT would clear the naive both-halves check
just as well. Treating that stuck failure as the discrimination signal is
exactly the ``witness-undecided`` defect, so each reject case instead supplies
``witness_reference=_LOOPFREE``: a loop-free variant that implements the frozen
spec CORRECTLY (it returns the running-total fold directly) and therefore both
VERIFIES and REDUCES. Refuted against that reference, each witness fails by
genuine refutation — "`decide` proved that the proposition ... is false" — not
by stuck reduction. ``_LOOPFREE`` is also shipped as the ``pos-direct-fold``
positive, so the battery itself records that loop-freeness is not what any rival
is being rejected for.

WITNESS PLACEMENT. The five reject witnesses sit at five DISTINCT input points
— ``[1]``, ``[1,2]``, ``[2]``, ``[3]``, ``[1,1,5]`` — so no two rivals share a
refutation point, and the binder ``matched`` is varied across both axes (length
1/2/3, element values 1/2/3, and a repeated-value/large-tail sequence). Each was
built against its rival (elaborates, ``decide`` closes) and against the
loop-free reference (``decide`` REFUTES it) before shipping.

DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
is REJECTED rather than admitted. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
two lines have to move together, and they do here. Under the total scope a
postcondition is claimed of ALL runs, not only of terminating ones, and the
verifier emits a descent obligation ``measure b' < measure b`` for every loop
in the impl (1 loop here, measure ``i``). A rival that loops without a measure
is refused outright (``Decreasing annotations are required in total correctness
semantics``), and a rival that supplies a CONSTANT measure to dodge that is
refused on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin <
spin``), re-measured on this bundle with a real build. Divergence therefore
does not discharge the ``ensures`` clauses vacuously. It is still not shipped
as a G-PBT reject case, and the reason is the witness contract rather than a
spec weakness. A reject case must carry a witness that ELABORATES
against the rival, and neither diverging shape gets past that. With NO measure
the descent obligation fails at the ``method`` itself, ahead of any appended
tester, and the witness file retains the ``method`` (it strips only the
``prove_correct`` obligations), so the rival module does not compile at all. With
a measure that does not decrease the refusal moves to the ``prove_correct`` site,
which IS stripped, so that module does elaborate; but the rival's post-image is
then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise to a
value a concrete-input tester can decide. Either way the gate returns
``witness-unproven``, an inconclusive outcome. Measured through
the gate's own ``_check_witness``, even ``example : True := trivial`` comes
back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
would fail the whole battery rather than pass a case. That is the right
behavior: a diverging impl has no output at any input, so there is no value for
a witness to disagree with, and its rejection is a judgement of the termination
obligation rather than a postcondition violation at a point. Recorded as
REJECTED-BY-SPEC and not expressible as a witnessed case, which is neither a
spec hole nor a battery gap.

AXIOM lane: EMPTY. The ``axioms`` region declares no consumed ``axiom`` (the
unchanged per-invocation callee is a deep A-reference — its sole relied-upon
property, non-negativity of each count, is carried by the ``Nat`` carrier and
validated == the real callee by axiom_check.py / G-AX). There is no
axiom-soundness / axiom-containment obligation to probe here, and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14559"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the one impl region and is
# ---- unique inside Solution.lean; both facts asserted at load by _swap) ------

# The whole executable body: the backward accumulator loop that folds the
# per-invocation counts and returns the running total. Replaced wholesale by
# every straight-line rival and the direct-return positive control.
_IMPL = (
    "    let mut result : Nat := 0\n"
    "    let mut i := matched.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ matched.length\n"
    "      invariant result = totalMatched (matched.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := matched[i - 1]!\n"
    "      result := c + result\n"
    "      i := i - 1\n"
    "    return result"
)

# The single accumulation step (used by the commuted-add positive control).
_STEP = "      result := c + result\n"

# The head of the impl region, an anchor for inserting an in-region admissibility
# assert directly ahead of the accumulator declaration.
_LETHEAD = "    let mut result : Nat := 0\n"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header is kept), so a variant that reshapes
# ---- the impl may retune its tactic script without touching the spec or
# ---- dropping the obligation. Unique in the file.
_PROOF = (
    "prove_correct totalRowsMatched by\n"
    "  loom_solve\n"
    "  rw [totalMatched_drop_step matched i (by omega) (by omega)]\n"
    "  simp_all"
)
# Straight-line impls leave a single point-wise goal that `loom_solve` closes.
_PROOF_TRIVIAL = "prove_correct totalRowsMatched by\n  loom_solve"


def _reshape(a_old, a_new, p_new):
    """Swap the impl region AND replace the tactic body in one variant."""
    return _swap(_swap(_BASE, a_old, a_new), _PROOF, p_new)


def _rival(expr):
    """A straight-line wrong impl returning `expr`; its tester reduces under
    `decide`, and its point-wise obligation is closed by bare `loom_solve`
    (the reproof leaves no drop-step goal — but the rival still FAILS to verify
    because `expr` ≠ totalMatched matched in general)."""
    return _reshape(_IMPL, f"    let out : Nat := {expr}\n    return out",
                    _PROOF_TRIVIAL)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; the precondition is trivial (`True`) and decides trivially.
_TESTER = (
    "extract_program_for totalRowsMatched\n"
    "prove_precondition_decidable_for totalRowsMatched\n"
    "prove_postcondition_decidable_for totalRowsMatched\n"
    "derive_tester_for totalRowsMatched\n\n"
)


def _witness(seq):
    return _TESTER + f"example : totalRowsMatchedTester {seq} = false := by\n  decide\n"


# ---- The shared witness_reference. A CORRECT, loop-free implementation of the
# ---- frozen spec: it returns the running-total fold directly, so it both
# ---- VERIFIES (checked by the gate before use, and shipped as `pos-direct-fold`)
# ---- and REDUCES under `decide`. The frozen `while` loop does neither the
# ---- second thing — its tester is stuck for a TRUE claim as much as a false one
# ---- — so every reject witness is refuted against this instead of against gold.
_LOOPFREE = _reshape(
    _IMPL, "    let out : Nat := totalMatched matched\n    return out",
    _PROOF_TRIVIAL)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the spec
    # is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the post-image is point-wise, so each reproof stays a
    # short retune away from the frozen script.
    # =====================================================================
    {
        "id": "pos-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the pure running-total fold directly instead of
        # recomputing it with a backward loop. Observationally
        # `totalMatched matched` on the whole domain; the obligation collapses to
        # a definitional equality `loom_solve` closes.
        "module": _LOOPFREE,
        "rationale": "a direct evaluation of the running-total fold satisfies "
                     "`out = totalMatched matched` on the whole domain; if it "
                     "failed to verify the post-image would be SPEC-TOO-STRONG "
                     "on the fold's own shape. Reproof is a bare `loom_solve` "
                     "(the straight-line return leaves no drop-step goal).",
    },
    {
        "id": "pos-commuted-accumulate",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: accumulate `result + c` instead of `c + result`. Nat addition
        # is commutative, so the running total is unchanged; the loop's inductive
        # step now differs by `Nat.add_comm`, supplied to the reproof.
        "module": _reshape(
            _IMPL, _IMPL.replace(_STEP, "      result := result + c\n"),
            _PROOF + " [Nat.add_comm]"),
        "rationale": "commuting the accumulation (`result + c` for `c + result`) "
                     "computes the same running total since Nat `+` is "
                     "commutative, so `out = totalMatched matched` still holds; a "
                     "correct reshape must verify (else SPEC-TOO-STRONG on the "
                     "accumulation order). The drop-step reproof is retuned with "
                     "`Nat.add_comm` for the reordered summand.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` (the precondition is
    # trivially `True`), so the sibling's "a normal input satisfies the
    # precondition" probe is not where the risk sits. The residual admissibility
    # risk on this surface is that the post-image is UNSATISFIABLE or DEGENERATE
    # at the interesting points — a spec no impl can meet reads exactly like one
    # every impl meets. This case discharges an in-region `assert` pinning the
    # post-image's value at four F2P-shaped points: the empty sequence totals to
    # zero, a singleton returns its count, a two-element sequence with a repeated
    # count sums to two (the duplicates-in-one-batch vs across-batches F2P
    # flavor), and a large lone count is returned verbatim. The assert is LIVE
    # (replacing any conjunct with a false claim about the same point leaves an
    # unsolved goal — verified during authoring). The surrounding impl is kept
    # verbatim so the method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-total-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _reshape(
            _LETHEAD,
            "    assert (with_name_prefix `admiss\n"
            "      (totalMatched [] = 0 ∧ totalMatched [1] = 1 ∧\n"
            "       totalMatched [1, 1] = 2 ∧ totalMatched [2000] = 2000))\n"
            + _LETHEAD,
            "prove_correct totalRowsMatched by\n"
            "  loom_solve\n"
            "  case _ => rw [totalMatched_drop_step matched i (by omega) "
            "(by omega)]; simp_all"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: the empty sequence totals to zero, a "
                     "singleton returns its own count, a repeated count sums to "
                     "two, and a large lone count is returned verbatim. The "
                     "in-region assert must discharge (else the obligation is "
                     "unsatisfiable / PRECOND-TOO-STRONG); the impl is kept "
                     "verbatim so the method's own `ensures` still discharges via "
                     "the drop-step reproof (the assert goal is the extra `case`).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-const-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change echo: contribute no running total, always return zero.
        # Correct only on the empty sequence; wrong on every non-empty one.
        "module": _rival("0"),
        "refinement": "a counterpart that returns a constant zero reproduces the "
                      "pre-change behavior (no aggregate was accumulated at all) "
                      "for every non-empty sequence, so the failing test that "
                      "expects the total matched-row count back (e.g. a whole "
                      "collection reporting its full size, or a repeated element "
                      "reporting one/two across batches) still observes zero and "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = totalMatched matched`: on any non-empty "
                     "sequence the fold is generally non-zero while the impl "
                     "returns zero. Verifying would be SPEC-TOO-WEAK (it would "
                     "admit the do-nothing impl). Refuted at the singleton `[1]`.",
        "witness": _witness("[1]"),
        # Gold cannot decide (its `while` loop is stuck for TRUE claims
        # too), so this witness is refuted against the correct,
        # loop-free reference instead. Verified: elaborates vs the rival,
        # `decide`-REFUTED vs the reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: report only the LEADING per-invocation count, ignoring
        # every later one. Right iff the sequence has length ≤ 1; wrong once a
        # second invocation contributes.
        "module": _rival("matched.headD 0"),
        "refinement": "a counterpart that returns only the first invocation's "
                      "count drops every later contribution, so a collection "
                      "large enough to span more than one invocation reports far "
                      "fewer matched rows than it should — the failing test that "
                      "sums the counts across all invocations still fails. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = totalMatched matched`: the fold sums the "
                     "WHOLE sequence, which the leading count alone omits once a "
                     "second element contributes. Verifying would be "
                     "SPEC-TOO-WEAK on the multi-invocation sub-domain. Refuted "
                     "at `[1, 2]`, where head 1 ≠ sum 3 (a two-element length "
                     "axis no other rival probes).",
        "witness": _witness("[1, 2]"),
        # Gold cannot decide (its `while` loop is stuck for TRUE claims
        # too), so this witness is refuted against the correct,
        # loop-free reference instead. Verified: elaborates vs the rival,
        # `decide`-REFUTED vs the reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-count-elements",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong-aggregate: return the NUMBER of invocations rather than the sum
        # of their per-invocation counts. Right iff every count is exactly 1;
        # wrong the moment any invocation matched a count other than 1.
        "module": _rival("matched.length"),
        "refinement": "a counterpart that returns the number of invocations "
                      "instead of the sum of their matched-row counts conflates "
                      "'how many batches ran' with 'how many rows matched'; the "
                      "moment any batch matches more than one row the reported "
                      "total is wrong, so the failing test that pins the true "
                      "row count still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = totalMatched matched`: the length counts "
                     "elements while the fold sums their values, and the two "
                     "differ whenever any element ≠ 1. Verifying would be "
                     "SPEC-TOO-WEAK (it would admit counting invocations for "
                     "summing counts). Refuted at `[2]`, where length 1 ≠ sum 2.",
        "witness": _witness("[2]"),
        # Gold cannot decide (its `while` loop is stuck for TRUE claims
        # too), so this witness is refuted against the correct,
        # loop-free reference instead. Verified: elaborates vs the rival,
        # `decide`-REFUTED vs the reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-double-lead",
        "kind": "uniqueness",
        "expect": "reject",
        # Double-count analogue: add the leading count twice on top of the true
        # total. Right iff the leading count is zero; an overcount otherwise.
        "module": _rival("totalMatched matched + matched.headD 0"),
        "refinement": "a counterpart that counts the leading invocation twice "
                      "reports MORE matched rows than were actually matched, the "
                      "same failure mode as summing overlapping contributions; "
                      "the failing test that pins the exact total still observes "
                      "the inflated count and still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = totalMatched matched`: adding the "
                     "leading count on top of the true fold overshoots whenever "
                     "that count is non-zero. Verifying would be SPEC-TOO-WEAK on "
                     "the exact-total value. Refuted at `[3]`, where the impl "
                     "yields 6 for a required 3 (a value axis — element 3 — no "
                     "other rival probes).",
        "witness": _witness("[3]"),
        # Gold cannot decide (its `while` loop is stuck for TRUE claims
        # too), so this witness is refuted against the correct,
        # loop-free reference instead. Verified: elaborates vs the rival,
        # `decide`-REFUTED vs the reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain (tail): sum all invocation counts EXCEPT the final one.
        # Right iff the sequence is empty; one contribution short otherwise.
        "module": _rival("totalMatched matched.dropLast"),
        "refinement": "a counterpart that omits the final invocation's count is "
                      "one contribution short on any non-empty sequence, so a "
                      "collection whose last batch matched rows reports fewer than "
                      "it should — the failing test that sums every batch still "
                      "fails. It would NOT resolve.",
        "rationale": "REJECT from `out = totalMatched matched`: dropping the last "
                     "element makes the result a partial sum, short by the final "
                     "count on any non-empty sequence. Verifying would be "
                     "SPEC-TOO-WEAK on the tail sub-domain. Refuted at "
                     "`[1, 1, 5]`, where the impl yields 2 for a required 7 (a "
                     "three-element, repeated-value, large-tail shape no other "
                     "rival probes).",
        "witness": _witness("[1, 1, 5]"),
        # Gold cannot decide (its `while` loop is stuck for TRUE claims
        # too), so this witness is refuted against the correct,
        # loop-free reference instead. Verified: elaborates vs the rival,
        # `decide`-REFUTED vs the reference.
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals — 1 of them permission-frame
# specific) plus a dropped AXIOM lane. Every SPEC case is accounted for below.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape                 -> pos-direct-fold / pos-commuted-accumulate
#                                            PORTED (split into two cheap reshapes)
#   admissibility-entry                 -> admiss-total-nondegenerate      RE-AIMED
#   frame-mutation-keys-append          -> (none)                          VACUOUS
#   const-zero-echo                     -> weak-const-zero                 PORTED
#   partial-domain-first-group-only     -> weak-first-only                 PORTED (re-carriered)
#   double-count-advance-by-one         -> weak-double-lead                PORTED (re-carriered)
#   wrong-grouping-per-element          -> weak-count-elements             RE-EXPRESSED
#                                            (+ weak-drop-last ADDED)
#
# 5 ported/re-expressed (across 6 velvet rivals+positives split), 1 re-aimed,
# 1 vacuous; the AXIOM lane dropped.
#
# CARRIER NARROWING. The sibling contracts one function over a
# permission-bearing read-only integer list PLUS a `group_size` parameter, and
# folds per-GROUP counts front-to-back via an offset loop. This backend models
# only the purely-functional core: the aggregate is the running total of the
# sequence of per-invocation counts, where that sequence (`matched : List Nat`)
# is ALREADY the post-grouping per-invocation counts (one element per
# invocation). So `group_size`, the offset loop, and the grouping arithmetic are
# NOT part of this carrier — the sibling's grouping-specific rivals have no group
# structure here to mis-slice, and are re-expressed as the wrong-aggregate rivals
# that the narrowed carrier CAN express.
#
# SIBLING pos-control-reshape -> SPLIT. The sibling reshapes the offset loop
#   (rename cursor, reorder commutative asserts, if/else step-cap). This carrier
#   has a backward accumulator loop with no group asserts, so the cheapest
#   correct reshapes are (a) returning the pure fold directly and (b) commuting
#   the accumulation. Both are shipped so the reshape argument is defended on
#   both the control structure and the accumulation order.
#
# ADMISSIBILITY re-aimed. The sibling asserts the precondition (`group_size>=1`
#   and a fractional permission) holds on a normal input. This method carries NO
#   `require` (the precondition is `True`), so that probe is vacuous; it is
#   re-aimed at the residual risk that the post-image is unsatisfiable/degenerate
#   at the interesting points, via a LIVE in-region assert pinning the fold's
#   value at the empty / singleton / repeated / large-lone-count F2P shapes.
#
# FRAME/PERMISSION-MUTATION: VACUOUS. The sibling's frame-mutation-keys-append
#   writes to a read-only input that carries only a fractional heap permission
#   and is rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent; `matched` is an immutable value and this bundle declares no
#   `mut` PARAMETER (the only `mut` bindings are the loop-local accumulator and
#   cursor), so there is no read-only input to overwrite and no permission system
#   to trip. No substitute is fabricated (per the porting map, this class is
#   legitimately dropped here rather than replaced).
#
# WRONG-GROUPING re-expressed, plus one ADDED. The sibling's per-element and
#   sliding-window grouping rivals attack how the offset loop slices groups —
#   structure this carrier does not model (its input is already per-invocation).
#   The nearest expressible structural error is aggregating the WRONG quantity of
#   the sequence: weak-count-elements returns the invocation COUNT rather than
#   the sum (right iff every count is 1). weak-drop-last is ADDED for
#   length/tail binder coverage (a partial sum short by the final count), so the
#   sequence binder is attacked on its tail as well as its head.
#
# WITNESS DISTINCTNESS / BINDER COVERAGE. The five reject witnesses probe five
#   distinct inputs — [1], [1,2], [2], [3], [1,1,5] — so no two rivals share a
#   refutation point (pts=5). The single input binder `matched` is varied across
#   both axes: length 1/2/3, element values 1/2/3, and a repeated-value/large-
#   tail sequence. The single load-bearing clause `out = totalMatched matched` is
#   attacked from five angles: the constant echo, the head-only partial sum, the
#   element-count wrong-aggregate, the leading-count overcount, and the
#   drop-last partial sum. Each witness was built against its rival (elaborates
#   under `decide`) and against the loop-free `witness_reference` (`decide`
#   REFUTES it: "proved that the proposition ... is false") before shipping. The
#   frozen solution is NOT the discrimination subject here: its `while` loop is
#   stuck under `decide` for a TRUE claim as much as a false one, so its exit code
#   would attest to a refutation never performed (`witness-undecided`).
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
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (the unchanged per-invocation callee is a deep A-reference
# validated by axiom_check.py — its non-negativity is carried by the `Nat`
# carrier), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
