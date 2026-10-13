"""properties.py — G-PBT falsification battery for sympy__sympy-13647 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct insertColumns`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec — here the declared
``witness_reference`` rather than the frozen solution, for the reason set out in
the CARRIER NOTE below).

DEFENDED SURFACE (one contracted method):

  insertColumns (srows orows : List (List Int)) (pos : Nat)
      return (out : List (List Int))
    require srows.length = orows.length
    ensures out = spliceCols pos srows orows

The method combines two equal-height row collections by placing the block of new
elements at column position ``pos`` in every row while keeping ALL the original
elements in their original order — the first ``pos`` of each original row before
the block and EVERY remaining element (the row's suffix from ``pos`` onward)
after it. The single load-bearing ``ensures`` pins ``out`` to the deep,
fully-unfolded ``spliceCols`` (the ``axioms`` region is empty — no opaque answer
key to echo), which is the per-row splice ``srow.take pos ++ orow ++
srow.drop pos``. The DISCRIMINATING content is the trailing segment: it must be
the original row's SUFFIX ``srow.drop pos`` (the elements from ``pos`` onward),
not its PREFIX — a rival that copies the prefix after the block drops every
trailing element and reads the wrong region, exactly the regression the issue
reports (the trailing identity block shifted from the bottom rows to the top).

THREE INPUT BINDERS, all free: ``srows`` (the original rows), ``orows`` (the
inserted block, one row each), and ``pos`` (the column position). All are
load-bearing: ``srows`` supplies both bands around the block, ``orows`` is the
inserted block itself, and ``pos`` splits each original row into its
before/after segments. The reject witnesses drive them to distinct shapes so the
manifest demonstrates the post-image's dependence on which region of the
original row lands after the block (``pos`` and the suffix), on the block being
present at all (``orows``), and on the split point (``pos``) — not on a single
pinned shape.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY EVERY REJECT CASE NAMES A
``witness_reference``. A witness reaches the post-image through Velvet's tester
machinery (``insertColumnsTester srows orows pos = false`` says the extracted
program's result violates the postcondition at that concrete input) and closes by
``decide``, checked in a file whose ``prove_correct`` block has been stripped so
no tactic script can mask the verdict. ``decide`` reduces the extracted program
by kernel computation, and the frozen program is a ``while`` loop under
``loom.semantics.choice "demonic"``: its fixpoint elaborates through a term the
kernel cannot unfold, so a witness applied to the FROZEN solution does not get
refuted — it gets STUCK, failing with ``did not reduce to `isTrue` or `isFalse` ``.

A stuck failure is NOT a usable fail-on-gold half, and this manifest does not
claim it as one. It was measured: for ``weak-trailing-prefix`` the shipped
witness AND a forgery asserting the exact OPPOSITE claim (``… = true``, i.e. that
the rival AGREES with the spec there) both fail against the frozen solution with
the byte-identical stuck-reduction error (exit 1 either way), so the frozen
solution's exit code carries no information about any claim, true or false.

The repair is the one the gate provides for exactly this carrier: each reject
case names a ``witness_reference`` — the loop-free ``pos-control-direct-model``
impl, which shares the frozen spec byte-for-byte and VERIFIES (so it cannot
violate its own postcondition at any input), and which the kernel CAN reduce. The
refutation is checked against that reference, where it is a genuine SEMANTIC
verdict: ``decide`` reports ``proved that the proposition … is false``, i.e. the
reference's tester is ``true`` at the very input where the rival's is ``false``.
Both directions were measured per case: the witness elaborates against the rival
(exit 0), is refuted against the reference (exit 1, ``decide proved … is false``),
and the ``= true`` forgery elaborates against the reference (exit 0) — so the
reference discriminates by VALUE and not by getting stuck.

Each reject rival is additionally expressed as a LOOP-FREE impl (a single
``zipWith`` / direct expression over the pure helpers) so its own extracted
tester ``decide``s over the concrete literal. This is a witnessing convenience,
not a weakening: the frozen spec is untouched and each rival's divergence from
``spliceCols`` is real at the witnessed input.

NON-VACUITY OF THE TESTER ITSELF. A tester that returned ``false`` everywhere
would make every witness pass for free, so the AGREEMENT direction was checked
too: for each of the four original rivals, ``insertColumnsTester … = true``
elaborates at an input where that rival happens to agree with ``spliceCols``
(``weak-trailing-prefix`` and ``weak-ignore-position`` at ``pos = 0``,
``weak-trailing-offbyone`` at ``pos`` past the row's end, ``weak-drop-block``
with an empty inserted row). So the tester tracks the postcondition's truth
value in both directions and each ``= false`` witness is a real discrimination at
a real input.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded model directly; name the
    spliced row in a local while keeping the loop and the frozen proof) must
    verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the sibling self-asserts that an F2P-shaped input satisfies
    its fractional-permission precondition. This backend's only ``require`` is
    ``srows.length = orows.length`` (met by every equal-height input) and there
    is no permission surface, so that probe is degenerate; the residual risk on
    this domain is a DEGENERATE post-image. ``admiss-nondegenerate`` discharges
    an in-region ``assert`` pinning the issue's own rows (a row whose trailing
    original element must land in the RIGHT band — the suffix behaviour the fix
    restores); the impl is kept verbatim so the method's own obligation still
    discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries this because a
    read-only row input is held at a fractional heap permission (``Acc(.,1/2)``)
    an impl can illegally overwrite. Lean/Velvet are referentially transparent:
    ``srows`` and ``orows`` are immutable ``List (List Int)`` values declared
    read-only (neither is ``mut``), there is no heap and no aliasing, so there is
    no read-only input to overwrite and no permission system to trip. The class
    has no carrier analogue; NOT ported (fabricating a substitute would test
    nothing). See the footer for the case-by-case accounting.
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
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``spliceCols pos
    srows orows``, a fully-unfolded ``def`` over the method's own arguments;
    there is no answer-key term a wrong impl could echo. The cheapest correct
    impl computes the splice honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the trailing segment read as a
    prefix, the trailing segment off by one, the split point ignored, or the
    inserted block dropped).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13647"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl body: a single anchor lying wholly inside the impl
# ---- region and unique in the file (both facts asserted at load). Reject rivals
# ---- that reshape the executable surface into a loop-free closed form swap on
# ---- this block; the two positive controls edit narrower anchors below.
_IMPL = """    let mut result : List (List Int) := []
    let mut i := srows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ srows.length
      invariant result = spliceCols pos (srows.drop i) (orows.drop i)
      done_with i = 0
      decreasing i
    do
      let s := srows[i - 1]!
      let o := orows[i - 1]!
      result := spliceRow s o pos :: result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the single row-append line, wholly inside the impl region and unique. The
# ---- loop-preserving positive reshapes only this line (naming the spliced row
# ---- in a local `let`), leaving the loop, invariants and frozen proof intact.
_ROW_LINE = "      result := spliceRow s o pos :: result"
assert _BASE.count(_ROW_LINE) == 1, "row-line anchor drift"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl into a single expression, or the
# ---- admissibility case that adds an in-region assert, retunes it without
# ---- touching the spec or dropping the `prove_correct insertColumns`
# ---- obligation.
_PROOF_GOLD = """prove_correct insertColumns by
  loom_solve
  rw [spliceCols_drop_step pos srows orows i (by omega) (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the equality (for
# ---- a correct reshape) or leaves it unsolved (for the reject rivals, which is
# ---- the point). Reject rivals retune the proof to this shape so the rejection
# ---- is attributable to the spec (via the witness), not to a proof script tuned
# ---- to a loop that no longer exists.
_PROOF_FLAT = "prove_correct insertColumns by\n  loom_solve"


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned to the flat shape."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- The subject every reject witness is refuted against, in place of the
# ---- frozen solution. See the CARRIER NOTE: `decide` against the frozen
# ---- loop-bearing program is STUCK for every claim (a `= true` forgery fails
# ---- with the byte-identical error), so the frozen solution's exit code
# ---- discriminates nothing. This is the loop-free `pos-control-direct-model`
# ---- impl — the same source that case ships, so the gate's own check that it
# ---- shares the frozen spec AND verifies is the same check that case already
# ---- makes. Against it the refutation is a real value verdict: `decide proved
# ---- that the proposition ... is false`.
_REF_IMPL = _rewrite_impl("    return spliceCols pos srows orows\n")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `insertColumnsTester srows orows pos = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped. Every argument is
# ---- a concrete integer-matrix literal so `decide` reduces the (loop-free)
# ---- extracted rival program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for insertColumns\n"
            "prove_precondition_decidable_for insertColumns\n"
            "prove_postcondition_decidable_for insertColumns\n"
            "derive_tester_for insertColumns\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop at all — maximally structurally different from the gold
        # backward scan. `out` IS `spliceCols pos srows orows`, so the ensures
        # holds trivially; the reproof is a bare `loom_solve` (no loop invariant
        # to peel).
        "module": _REF_IMPL,
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`spliceCols pos srows orows` directly (no loop). `out` IS that "
            "model, so the ensures holds on the whole domain; the reproof is "
            "`loom_solve`. If this fails to verify the spec is over-fit to the "
            "backward-scan code shape (SPEC-TOO-STRONG). Also the honest "
            "no-ungrounded-echo control: the model is the real work, so a direct "
            "return is correct, not a cheat."
        ),
    },
    {
        "id": "pos-control-named-row",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, the invariants and the frozen proof script; only
        # names the spliced row in a local `let r` before prepending it.
        # Observationally identical for every input.
        "module": _swap(
            _BASE, _ROW_LINE,
            "      let r : List Int := spliceRow s o pos\n"
            "      result := r :: result"),
        "rationale": (
            "naming the spliced row in a local `let r` before prepending it "
            "builds the same list step by step, so `out = spliceCols pos srows "
            "orows` still holds on the whole domain; the loop, invariants and "
            "frozen proof script are untouched. A correct reshape must verify, "
            "else the postcondition is SPEC-TOO-STRONG (rejects a faithful impl "
            "over the shape of the loop body)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's only `require` (`srows.length = orows.length`)
    # is met by every equal-height input, so the sibling's "a normal input
    # satisfies the precondition" probe is degenerate here. The residual
    # admissibility risk on this domain is that the post-image is DEGENERATE at
    # the interesting point — a spec no impl distinguishes reads exactly like one
    # every impl meets. This case discharges an in-region `assert`, at two fully
    # concrete F2P-shaped rows, that the post-image is NON-DEGENERATE: a row whose
    # inserted block sits between the leading original element and its trailing
    # original element must keep the trailing element AFTER the block (the SUFFIX
    # behaviour the fix restores), not before it. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the proof gains a
    # `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      spliceCols 3 [[(1:Int),0,0,0,0,0]] [[(2:Int),2]]\n"
                  "        = [[(1:Int),0,0,2,2,0,0,0]] ∧\n"
                  "      spliceCols 3 [[(0:Int),0,0,1,0,0]] [[(2:Int),2]]\n"
                  "        = [[(0:Int),0,0,2,2,1,0,0]]))\n"),
            _PROOF_GOLD,
            "prove_correct insertColumns by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [spliceCols_drop_step pos srows orows i (by omega) (by omega) (by omega)]\n"
            "       simp_all)\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "rows: inserting a two-element block at position 3 into a six-element "
            "row must place the block at columns 3,4 and keep the original "
            "elements at columns 0..2 before it and columns 3..5 AFTER it "
            "(columns 5..7 of the output) — so a row whose only nonzero trailing "
            "element sits past position 3 has that element land in the right "
            "band, not the left. The in-region assert must discharge (else the "
            "obligation is degenerate at the point the fix cares about); the impl "
            "is kept verbatim so `out = spliceCols …` still verifies."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a LOOP-FREE
    # closed form (single expression over the pure helpers) so its extracted
    # tester `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-trailing-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # The LITERAL pre-patch bug: the trailing segment after the block is the
        # original row's PREFIX (`s.take (s.length - pos)`) instead of its SUFFIX
        # (`s.drop pos`). Correct on the leading band and the block; diverges on
        # the trailing band whenever pos > 0.
        "module": _rewrite_impl(
            "    return srows.zipWith "
            "(fun s o => s.take pos ++ o ++ s.take (s.length - pos)) orows\n"),
        "refinement": (
            "this is the exact regression: after the inserted block the row "
            "copies its OWN leading elements again instead of the elements from "
            "the split point onward, so every trailing original element is "
            "dropped and replaced by a repeat of the head. On the issue's "
            "insertion (a two-column block at position 3 into the six-column "
            "identity) the trailing identity block is shifted from the bottom "
            "rows up to the top — the reported buggy output — so the scenario "
            "that pins the correct combined matrix still fails. It would NOT "
            "resolve. The canonical verify-not-resolve rival."
        ),
        "rationale": (
            "REJECT from `out = spliceCols pos srows orows`: `spliceCols` splices "
            "the trailing segment as `s.drop pos`, this rival uses "
            "`s.take (s.length - pos)`, and the two disagree whenever pos > 0 and "
            "the row has a nonzero suffix. Verifying would leave the trailing "
            "segment unpinned (SPEC-TOO-WEAK). Refuted at the issue-shaped input "
            "(pos = 3, a six-element row and a two-element block)."
        ),
        "witness": _tester(
            "example : insertColumnsTester [[(1:Int),0,0,0,0,0]] [[(2:Int),2]] 3 "
            "= false := by\n  decide\n"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "weak-trailing-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one split: the trailing segment starts at `pos + 1` instead of
        # `pos`, dropping the single original element at the split point. Correct
        # on the leading band and the block and even on rows with no element at
        # `pos`; wrong whenever the element at index `pos` should survive after
        # the block.
        "module": _rewrite_impl(
            "    return srows.zipWith "
            "(fun s o => s.take pos ++ o ++ s.drop (pos + 1)) orows\n"),
        "refinement": (
            "a faithful counterpart that started the trailing segment one place "
            "past the split point would silently discard the original element AT "
            "the split point for every row, shortening each combined row by one "
            "and shifting every element after the block; the scenario that pins "
            "the full combined matrix would get the wrong rows — it would NOT "
            "resolve. Correct on the leading band and on the inserted block (a "
            "trailing-segment-only, off-by-one break)."
        ),
        "rationale": (
            "REJECT from `out = spliceCols pos srows orows`: `spliceCols` keeps "
            "`s.drop pos` (from the split point onward), this rival keeps "
            "`s.drop (pos + 1)` (one element short), so the two disagree whenever "
            "the element at index `pos` is present. Verifying would leave the "
            "split point unpinned to within one (partial-domain SPEC-TOO-WEAK). "
            "Refuted at pos = 1 on a three-element row (`[[5,6,7]]`, block "
            "`[[9]]`), where the element 6 at the split point must survive after "
            "the block but this rival drops it."
        ),
        "witness": _tester(
            "example : insertColumnsTester [[(5:Int),6,7]] [[(9:Int)]] 1 "
            "= false := by\n  decide\n"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "weak-ignore-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the `pos` binder entirely: always insert the block at position 0
        # (`s.take 0 ++ o ++ s.drop 0`), i.e. prepend the whole block and keep the
        # whole original row after it. Correct only when pos == 0; wrong for every
        # pos > 0. This is the rival that proves `pos` is load-bearing.
        "module": _rewrite_impl(
            "    return srows.zipWith "
            "(fun s o => s.take 0 ++ o ++ s.drop 0) orows\n"),
        "refinement": (
            "a faithful counterpart that always inserted the new columns at the "
            "front regardless of the requested position would place the block at "
            "column 0 for every request; the issue's insertion at position 3 "
            "would put the two columns of twos at the LEFT edge instead of "
            "between columns 2 and 3, so the combined matrix is wrong — it would "
            "NOT resolve. Correct only for a position-0 request (an "
            "ignored-position break)."
        ),
        "rationale": (
            "REJECT from `out = spliceCols pos srows orows`: `spliceCols` splits "
            "each row at `pos`, this rival splits at 0, so the two disagree "
            "whenever pos > 0 and the leading band is non-empty. This is the "
            "sub-domain that proves `pos` is LOAD-BEARING — no other rival "
            "abuses the split point directly. Verifying would leave `pos` "
            "unenforced (SPEC-TOO-WEAK). Refuted at pos = 1 on a two-element row "
            "(`[[1,2]]`, block `[[9]]`): gold gives `[1,9,2]`, the rival "
            "`[9,1,2]`."
        ),
        "witness": _tester(
            "example : insertColumnsTester [[(1:Int),2]] [[(9:Int)]] 1 "
            "= false := by\n  decide\n"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "weak-drop-block",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the inserted block entirely: return the original rows unchanged,
        # ignoring `orows`. Correct only when every inserted row is empty; wrong
        # whenever the block has any element. This is the rival that proves
        # `orows` is load-bearing.
        "module": _rewrite_impl("    return srows\n"),
        "refinement": (
            "a faithful counterpart that returned the original matrix untouched "
            "would insert no new columns at all; the requested block would never "
            "appear in the result, so the scenario that pins the combined matrix "
            "(with the inserted columns present) still fails — it would NOT "
            "resolve. Correct only when the inserted block is empty (a "
            "dropped-block break)."
        ),
        "rationale": (
            "REJECT from `out = spliceCols pos srows orows`: `spliceCols` splices "
            "`orow` into every row, this rival ignores `orows` and returns "
            "`srows`, so the two disagree whenever any inserted row is non-empty. "
            "This is the sub-domain that proves `orows` is LOAD-BEARING — no "
            "other rival drops the block. Verifying would leave the inserted "
            "block unenforced (SPEC-TOO-WEAK). Refuted at pos = 2 on a "
            "two-element row (`[[3,4]]`, block `[[8,8]]`): gold gives "
            "`[3,4,8,8]`, the rival `[3,4]`."
        ),
        "witness": _tester(
            "example : insertColumnsTester [[(3:Int),4]] [[(8:Int),8]] 2 "
            "= false := by\n  decide\n"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "weak-last-column-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by AUDIT. The port recorded the sibling's single-output-column
        # rival as SUBSUMED-BY-CARRIER ("a one-column miss would have to be
        # encoded as an unnatural surgery on the concatenation and is not cleanly
        # expressible"). It is cleanly expressible: `dropLast ++ [0]` names the
        # final output column of the whole-list concatenation WITHOUT needing a
        # per-output-column index, forcing exactly that one position to 0 and
        # leaving every other position of every row exactly gold. The sharpest
        # near-miss in the battery — correct on the entire domain except a single
        # position per row.
        "module": _rewrite_impl(
            "    return srows.zipWith "
            "(fun s o => (s.take pos ++ o ++ s.drop pos).dropLast ++ [(0:Int)]) "
            "orows\n"),
        "refinement": (
            "a faithful counterpart that special-cased the final column of the "
            "combined row to 0 would keep every other cell right and still get "
            "the last column wrong on every row whose trailing original element "
            "is nonzero. On the issue's insertion (a two-column block at "
            "position 3 into the six-column identity) the last combined column "
            "carries the trailing diagonal entries for the lower rows, so those "
            "become 0 and the scenario that pins the full combined matrix still "
            "fails — it would NOT resolve. A one-position break: correct "
            "everywhere else, including the block and both bands."
        ),
        "rationale": (
            "REJECT from `out = spliceCols pos srows orows`: `spliceCols` keeps "
            "the row's final element as whatever the splice puts there, this "
            "rival overwrites it with 0, so the two disagree on every row whose "
            "last spliced element is nonzero. Verifying would leave the FINAL "
            "output column unpinned while every other column is pinned — the "
            "sharpest partial-domain SPEC-TOO-WEAK the surface admits. Refuted "
            "at pos = 0 on a three-element row (`[[1,2,3]]`, block `[[7,7]]`): "
            "gold gives `[7,7,1,2,3]`, the rival `[7,7,1,2,0]`."
        ),
        "witness": _tester(
            "example : insertColumnsTester [[(1:Int),2,3]] [[(7:Int),7]] 0 "
            "= false := by\n  decide\n"),
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "weak-block-rotated",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by AUDIT. The port recorded the sibling's middle-band-offset
        # rival as RE-AIMED-BY-CARRIER on the grounds that "the inserted block is
        # placed as a WHOLE list, so there is no intra-block column index to
        # offset". The OFFSET is indeed collapsed, but the sibling's attack was
        # on the block's INTERNAL column order, and that survives the row-wise
        # refinement: rotating the block by `pos` places the block's own elements
        # at the wrong columns inside the block while leaving both surrounding
        # bands, the block's length, and the split point exactly gold. So the
        # sibling's actual discriminating content is expressible here after all,
        # and weak-drop-block (block absent) does not cover it — that rival is
        # kept as the orows-PRESENCE attack; this one is the orows-ORDER attack.
        "module": _rewrite_impl(
            "    return srows.zipWith "
            "(fun s o => s.take pos ++ (o.drop pos ++ o.take pos) ++ s.drop pos) "
            "orows\n"),
        "refinement": (
            "a faithful counterpart that rotated the inserted block's own "
            "columns by the insertion position would place the new columns in "
            "the right REGION but in the wrong ORDER within it. The block would "
            "appear at the requested position, with the requested width, and "
            "both surrounding bands intact — yet the scenario that pins the full "
            "combined matrix compares cell by cell and the inserted columns are "
            "transposed, so it still fails; it would NOT resolve. Correct "
            "whenever the block is symmetric under the rotation (a "
            "block-internal-order break)."
        ),
        "rationale": (
            "REJECT from `out = spliceCols pos srows orows`: `spliceCols` "
            "inserts `orow` in its own order, this rival inserts "
            "`orow.drop pos ++ orow.take pos`, so the two disagree whenever the "
            "rotation is non-trivial (0 < pos < the block's length) and the "
            "block's elements are not all equal. This attacks `orows`'s INTERNAL "
            "ORDER, which no other rival touches — weak-drop-block attacks the "
            "block's PRESENCE and leaves its order free. Verifying would leave "
            "the block's column order unpinned (SPEC-TOO-WEAK). Refuted at "
            "pos = 1 on a two-element row (`[[4,5]]`, block `[[6,7]]`): gold "
            "gives `[4,6,7,5]`, the rival `[4,7,6,5]`."
        ),
        "witness": _tester(
            "example : insertColumnsTester [[(4:Int),5]] [[(6:Int),7]] 1 "
            "= false := by\n  decide\n"),
        "witness_reference": _REF_IMPL,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 1 mandatory frame-mutation uniqueness
# rival, 4 partial-domain uniqueness rivals) plus 3 AXIOM_TESTS. This bundle
# models the changed operation DEEPLY and CONCRETELY (the row-wise splice
# `spliceCols`/`spliceRow` over `List (List Int)`, spelled-out positional
# arithmetic), so there is no axiom and no permission surface; the value surface
# (which region of each original row lands after the block) carries across
# intact. The sibling's per-COLUMN entry banding (left `self_row[j]`, middle
# `other_row[j-pos]`, right `self_row[j-other_cols]`) is refined here to the
# per-ROW splice: because the entry rule is independent of the row index, the
# whole matrix IS the row-wise concatenation `take pos ++ orow ++ drop pos`
# (mapping.md §1, refinement.md §A). That refinement places the inserted block
# as a WHOLE list, which collapses the sibling's "middle-band offset" distinction
# (there is no intra-block index on this carrier) — re-aimed to an orows-binder
# attack below.
#
#   sibling case                           kind          -> here                       disposition
#   -----------------------------------------------------------------------------------------------
#   pos-control-echo-output-value          soundness     -> pos-control-direct-model   RE-SHAPED
#   pos-control-band-reorder               soundness     -> pos-control-named-row      RE-SHAPED
#   admiss-f2p-shaped                      admissibility -> admiss-nondegenerate       RE-AIMED
#   frame-mutate-readonly-self-row         uniqueness    -> (none)                     VACUOUS
#   partial-domain-prepatch-right-band     uniqueness    -> weak-trailing-prefix       PORTED
#   partial-domain-offbyone-right-band     uniqueness    -> weak-trailing-offbyone     PORTED
#   partial-domain-middle-band-offset      uniqueness    -> weak-drop-block            RE-AIMED (carrier)
#                                          uniqueness    -> weak-block-rotated          PORTED (audit)
#   partial-domain-last-column-zero        uniqueness    -> weak-last-column-zero       PORTED (audit)
#   ax-new-matrix-cell-soundness           axiom         -> (none)                     DROPPED (G-AX lane)
#   ax-new-matrix-cell-containment         axiom         -> (none)                     DROPPED (G-AX lane)
#   ax-output-value-fidelity               axiom         -> (none)                     DROPPED (G-AX lane)
#   (implicit) weak-ignore-position        —             -> weak-ignore-position       ADDED (pos binder)
#
# 4 uniqueness ported (two of them by the AUDIT, see below), 1 uniqueness
# re-aimed, 1 uniqueness added; 2 soundness re-shaped; 1 admissibility re-aimed;
# 1 uniqueness vacuous; 3 axiom-lane dropped. Nothing is now recorded as
# subsumed or inexpressible except the frame-mutation class, which is a genuine
# carrier fact (no heap, no permissions).
#
# RE-SHAPED (the two positives): the sibling's positives are (a) an impl that
#   binds `v = output_value(...)` directly and (b) a branch reorder of the 3-way
#   band. On this carrier the maximally-different correct impl is a loop-free
#   direct return of the grounded model `spliceCols …` (pos-control-direct-model);
#   the branch-reorder counterpart is a loop-PRESERVING minimal reshape that names
#   the spliced row in a local `let` (pos-control-named-row) and keeps the frozen
#   proof intact. Both defended surfaces (a wholly different control-flow shape AND
#   a minimal edit inside the frozen loop) are covered.
# RE-AIMED (admiss-f2p-shaped -> admiss-nondegenerate): the sibling asserts an
#   F2P-shaped input (eye(6).col_insert(3, 6x2)) satisfies its half-permission
#   Requires plus the clamped shape facts. This backend's only `require` is
#   `srows.length = orows.length` (met by every F2P input) and there is no
#   permission surface, so that probe is degenerate; the sharper residual risk is
#   a DEGENERATE post-image. The case is re-aimed to a live in-region assert
#   pinning the issue's own rows — including a row whose trailing original element
#   must land in the RIGHT band after the inserted block (the suffix behaviour the
#   fix restores).
# PORTED (weak-trailing-prefix, weak-trailing-offbyone): the sibling's two right-
#   band rivals port directly. The pre-patch right band `self_row[j-pos-other_cols]`
#   over-subtracts `pos`, reading the row's PREFIX columns `0..c-pos-1` where the
#   fix reads the suffix columns `pos..c-1`; on this carrier that is exactly
#   `s.take (s.length - pos)` in place of `s.drop pos` (weak-trailing-prefix, the
#   canonical regression). The off-by-one right band ports to
#   weak-trailing-offbyone (trailing segment starts one element late). Each is
#   refuted on the trailing-band sub-domain at a DISTINCT input.
# RE-AIMED-BY-CARRIER, THEN ALSO PORTED (partial-domain-middle-band-offset ->
#   weak-drop-block + weak-block-rotated): the sibling's middle-band rival reads
#   `other_row[j]` instead of `other_row[j-pos]`, dropping the block's insertion
#   offset. The literal `- pos` OFFSET is genuinely collapsed by the row-wise
#   refinement: the block is placed as a whole list (`++ orow ++`), so there is no
#   intra-block column index for an offset to be wrong by. weak-drop-block keeps
#   the observable half the port identified — the block's PRESENCE, proving the
#   `orows` binder load-bearing.
#
#   The AUDIT found that reading stopped one step short. The sibling's rival is
#   wrong specifically about WHICH element of the block lands at which column
#   inside the block, and that content does survive the refinement even though the
#   index does not: the block's own ORDER is observable on this carrier, because
#   `orow` appears in the post-image as a list whose element order the equality
#   pins. weak-block-rotated (added by the audit) inserts
#   `orow.drop pos ++ orow.take pos` — the requested block, at the requested
#   position, with the requested width, in the WRONG internal order — and is
#   refuted at pos = 1 on `[[4,5]]` with block `[[6,7]]` (gold `[4,6,7,5]`, rival
#   `[4,7,6,5]`). So the sibling's discriminating content is expressible after
#   all, and the `orows` binder is now attacked on both axes (presence and order)
#   rather than only on presence.
# ADDED (weak-ignore-position): the `pos` binder has no dedicated sibling rival
#   (the sibling's rivals all perturb a band index while holding `pos` in the
#   guard), but `pos` is load-bearing on this carrier's splice — it is the split
#   point. weak-ignore-position hardcodes the split to 0, proving `pos` is
#   attacked directly; refuted at pos = 1 where gold splits and the rival does not.
# VACUOUS (frame-mutate-readonly-self-row): the sibling writes into the read-only
#   input `self_row` (held at `Acc(list_pred(self_row),1/2)`) and is rejected for
#   INSUFFICIENT PERMISSION before any value reasoning. This backend is
#   referentially transparent: `srows`/`orows` are immutable `List (List Int)`
#   values, neither declared `mut`, and there is no heap, aliasing, or permission
#   system. There is no read-only input to overwrite and nothing to trip, so the
#   class has no carrier analogue. Omitted as a genuine carrier fact, NOT
#   fabricated (porting map: this class is vacuous on a referentially-transparent
#   backend).
# PORTED BY THE AUDIT (partial-domain-last-column-zero -> weak-last-column-zero):
#   the port recorded this one as SUBSUMED-BY-CARRIER, reasoning that forcing a
#   single output column to 0 is a per-OUTPUT-COLUMN perturbation and that this
#   carrier, building each row by whole-list concatenation, "has no per-output-
#   column index to single out", so the rival "would have to be encoded as an
#   unnatural surgery on the concatenation and is not cleanly expressible".
#
#   That was wrong, and the audit landed the case. Singling out an output column
#   does NOT require an index: the final column of the concatenation is named
#   directly by `dropLast ++ [0]`, which is a one-line, entirely natural surgery
#   over the same `List Int` the splice already produces. weak-last-column-zero
#   ships exactly that, and it is the sharpest near-miss in the battery — every
#   cell of every row is gold except one position per row. Refuted at pos = 0 on
#   `[[1,2,3]]` with block `[[7,7]]` (gold `[7,7,1,2,3]`, rival `[7,7,1,2,0]`).
#   The claim that the trailing rivals already covered this region was also too
#   generous: both of them perturb the whole trailing SEGMENT, so neither
#   establishes that the spec pins the last column while leaving the rest fixed.
# DROPPED (ax-*): the sibling's three AXIOM_TESTS probe the matrix constructor
#   `_new`'s value-preservation and containment, and the `output_value` A-reference
#   fidelity. This bundle has NO axiom and NO A-reference (mapping.md §3,
#   refinement.md §C: the constructor's grid-materialization IS `spliceCols`,
#   modeled deeply and validated by G-CONF; the changed index arithmetic is
#   modeled deeply too), so there is no axiom lane to mirror. The axiom lane is
#   G-AX's job and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = spliceCols pos srows
#   orows` has THREE binders — `srows`, `orows`, `pos` — and one top-level clause
#   (the whole-matrix splice), whose discriminating content is the trailing
#   segment `s.drop pos`. The six reject witnesses probe six DISTINCT input
#   points:
#     * weak-trailing-prefix     [[1,0,0,0,0,0]] [[2,2]] pos 3   (issue-shaped)
#     * weak-trailing-offbyone   [[5,6,7]]       [[9]]   pos 1
#     * weak-ignore-position     [[1,2]]         [[9]]   pos 1
#     * weak-drop-block          [[3,4]]         [[8,8]] pos 2
#     * weak-last-column-zero    [[1,2,3]]       [[7,7]] pos 0   (audit-added)
#     * weak-block-rotated       [[4,5]]         [[6,7]] pos 1   (audit-added)
#   So `pos` ranges over {0,1,2,3} — including the pos = 0 boundary, where the
#   leading band is empty — and is attacked directly (weak-ignore-position
#   hardcodes the split, and the trailing rivals depend on it); `srows` is
#   non-trivial and its trailing region is exercised by weak-trailing-prefix /
#   weak-trailing-offbyone; `orows` is attacked on BOTH axes, presence
#   (weak-drop-block drops the block) and internal order (weak-block-rotated
#   permutes it), and its width is varied ({2,1,1,2,2,2}) across the set.
#
#   The variation is meaningful rather than two spellings of one point: each
#   witness input is chosen so the rival's post-image differs from `spliceCols`
#   THERE and the other rivals' inputs would not separate it. In particular the
#   trailing segment (the fix's discriminating content) is attacked by two
#   independent rivals that diverge from gold on different sub-domains
#   (whole-suffix wrong vs one-element-short vs one-POSITION-wrong for
#   weak-last-column-zero), so no two of them share a witness. Cross-checked by
#   building the AGREEMENT direction for each of the first four rivals — a
#   `Tester ... = true` at an input where that rival coincides with gold
#   elaborates green — which shows each witness's `= false` is a value-level
#   discrimination rather than a tester that is false everywhere. No binder is
#   pinned at a single value across the reject set.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the changed op
#   is modeled deeply and concretely, validated by G-CONF, so G-AX is skipped);
#   this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
