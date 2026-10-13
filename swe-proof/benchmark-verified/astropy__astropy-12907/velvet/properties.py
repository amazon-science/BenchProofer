"""properties.py — G-PBT falsification battery for astropy__astropy-12907 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct combineParallel`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a rectangular 0/1 matrix carrier,
``List (List Int)``):

  combineParallel (left right : List (List Int)) (lc rc : Nat)
      return (out : List (List Int))
    require ∀ r ∈ left,  r.length = lc
    require ∀ r ∈ right, r.length = rc
    ensures out = blockDiag left right lc rc          -- THE load-bearing clause

The method assembles the block-diagonal dependency matrix of the parallel
composition of two transforms: the upper block is every ``left`` row widened on
the RIGHT by ``rc`` zero columns; the lower block is every ``right`` row widened
on the LEFT by ``lc`` zero columns; the two blocks are stacked. The off-diagonal
blocks are all zero, and — critically — each diagonal block keeps its OWN
internal dependency structure (its 0/1 rows are copied through, not overwritten
by a constant).

``blockDiag left right lc rc`` is a total, fully-unfolded pure function of the
method's own inputs (``(left.map (widenRight rc)) ++ (right.map (widenLeft lc))``)
in the ``pure`` region. The ``axioms`` region is empty; there is no opaque answer
key to echo (directive 8 — the post-image is grounded in the actual inputs). The
clause decomposes into four independently-attackable structural sub-behaviours:

  * UPPER-PAD  — each left row is zero-padded on the right (widenRight): the
                 left transform's outputs are independent of the right inputs, so
                 the upper-right quadrant is all zero;
  * LOWER-PAD  — each right row is zero-padded on the left (widenLeft): the right
                 transform's outputs are independent of the left inputs, so the
                 lower-left quadrant is all zero;
  * LOWER-BODY — the right rows carry their OWN 0/1 columns through unchanged
                 (not a constant fill) — the sub-behaviour the fix restores;
  * ORDER/SHAPE — one output row per operand row, blocks stacked in order (left
                 rows first, then right rows), right rows in their own order.

FOUR input binders, all free; the post-image must hold for every value of each:
  * ``left``  — the left operand's dependency rows (length and contents matter);
  * ``right`` — the right operand's dependency rows (length, contents, ORDER);
  * ``lc``    — the left input width (= left-pad amount for the lower block);
  * ``rc``    — the right input width (= right-pad amount for the upper block).
The two ``require`` clauses pin rectangularity (every real dependency matrix is
rectangular), so a witness input must respect them or the tester short-circuits
to ``true`` (precondition-false vacuously satisfies the postcondition test).

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The sibling records this class as
    already vacuous even on nagini: ``left``/``right`` are pure immutable
    sequences carrying no heap permission, so there is no read-only cell to
    overwrite. Lean/Velvet are referentially transparent a fortiori: every input
    is an immutable value, the method declares no ``mut`` binder, there is no
    heap and no aliasing. No substitute probe is fabricated (per the porting map,
    this class is legitimately dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``blockDiag left right lc rc`` — a concrete ``def`` over the
    method's own arguments (empty ``axioms`` region; no opaque callee). The only
    satisfier is the grounded assembly itself; there is nothing to echo.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. Each rival gets the SHAPE right
    (correct width lc+rc, correct row count) and is correct on part of the
    domain, but diverges on one structural sub-behaviour above.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is LOOP-FREE (two ``.map``s and
a ``++``), so its extracted tester reduces under ``decide`` — the django-13012
pattern, NOT the backward-loop pattern. Each reject rival is likewise a loop-free
expression, so its tester also ``decide``s. Each reject rival therefore carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``combineParallelTester left right lc rc = false`` at ONE concrete input,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the
tester ``decide``s to ``false`` — the rival's output violates the postcondition
there) and FAILS against the frozen solution (gold's tester ``decide``s to
``true``, so ``= false`` is refuted), so each rejection is a genuine spec
refutation and not mechanical tactic breakage. Every witness input satisfies both
``require`` clauses (rectangular rows), so it is not vacuously excluded.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references;
the whole computation is concrete list arithmetic over the inputs. Nothing in the
proof rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-12907"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` (both markers, and the comment lines, live inside the elided
# impl region). Every rival and reshape edits ONLY this block (and, for
# reshapes/admissibility, the elided `prove_correct` tactic body), so the spec
# view is untouched and same_spec holds by construction.
_IMPL = (
    "    -- Upper block: each left row keeps its own columns, zero-padded on the\n"
    "    -- right so the right transform's inputs do not appear to affect it.\n"
    "    let upper : List (List Int) := left.map (widenRight rc)\n"
    "    -- Lower block: each right row is zero-padded on the left, then carries its\n"
    "    -- OWN dependency columns — NOT a constant fill, so the right transform's\n"
    "    -- internal structure is preserved across the composition.\n"
    "    let lower : List (List Int) := right.map (widenLeft lc)\n"
    "    return upper ++ lower"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it as `loom_solve`, so the wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct combineParallel by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `combineParallelTester left right lc rc = false` says the extracted
# ---- program's result violates the postcondition at that concrete input (the
# ---- tester short-circuits to `true` when a `require` clause is false, so every
# ---- witness below uses rectangular rows that satisfy both preconditions).
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict; both the rival and the frozen impl are
# ---- loop-free, so both testers reduce under `decide`.
def _witness(call):
    return ("extract_program_for combineParallel\n"
            "prove_precondition_decidable_for combineParallel\n"
            "prove_postcondition_decidable_for combineParallel\n"
            "derive_tester_for combineParallel\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of inlining the two
    # blocks, it returns the pure model `blockDiag` directly. The frozen proof
    # (`loom_solve`) still closes the byte-identical obligation (the ensures IS
    # `out = blockDiag ...`, so the body is definitionally the RHS). Verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-blockdiag-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return blockDiag left right lc rc"),
        "rationale": "structurally different CORRECT impl: it returns the pure "
                     "block-diagonal model directly rather than inlining the two "
                     "blocks. Observationally identical on every input, so "
                     "`out = blockDiag left right lc rc` holds on the whole "
                     "domain. A faithful reshape MUST verify, else the "
                     "postcondition is SPEC-TOO-STRONG (it would reject its own "
                     "model's output).",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — branch/statement REORDER: bind the lower
    # block BEFORE the upper block, then stack them in the same order. Identical
    # values, different control flow. Keeps the whole assembly; the frozen proof
    # still closes it. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-let-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let lower : List (List Int) := right.map (widenLeft lc)\n"
            "    let upper : List (List Int) := left.map (widenRight rc)\n"
            "    return upper ++ lower"),
        "rationale": "statement-REORDER positive control: the lower block is "
                     "bound first and the upper second, then stacked in the same "
                     "order (`upper ++ lower`). Identical values, different "
                     "control-flow shape; keeps the whole assembly, so "
                     "`out = blockDiag ...` still holds. Must verify.",
    },
    # =====================================================================
    # ADMISSIBILITY — the sibling's admissibility probe re-establishes that the
    # precondition admits a normal F2P-shaped input. On this backend the residual
    # admissibility risk is twofold and both are pinned by ONE in-region assert at
    # a concrete F2P-shaped input (a 2x2 identity-like grid on each side):
    #   (a) BOTH `require` rectangularity clauses are SATISFIABLE by that input
    #       (so a real pair of 2x2 dependency matrices is in-domain); and
    #   (b) the post-image is NON-DEGENERATE there — it produces the full 4x4
    #       block-diagonal identity, with genuine zero off-diagonal quadrants and
    #       the two identity blocks preserved (not a constant/empty collapse).
    # The impl is kept verbatim so the method's own obligation still discharges;
    # the proof is retuned only to clear the extra `assert` goal (`decide`), which
    # is elided from the spec view. The assert is live (a false claim leaves an
    # unsolved goal — verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-grid",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      ((∀ r ∈ ([[1,0],[0,1]] : List (List Int)), r.length = 2) ∧\n"
            "       (∀ r ∈ ([[1,0],[0,1]] : List (List Int)), r.length = 2) ∧\n"
            "       blockDiag [[1,0],[0,1]] [[1,0],[0,1]] 2 2\n"
            "         = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]))\n"
            "    let upper : List (List Int) := left.map (widenRight rc)\n"
            "    let lower : List (List Int) := right.map (widenLeft lc)\n"
            "    return upper ++ lower",
            "prove_correct combineParallel by\n  loom_solve\n  all_goals decide"),
        "rationale": "the two `require` rectangularity clauses admit the "
                     "F2P-shaped input (a pair of 2x2 diagonal dependency "
                     "matrices) AND the post-image is non-degenerate there: it "
                     "assembles the full 4x4 block-diagonal identity, with both "
                     "off-diagonal quadrants genuinely zero and both diagonal "
                     "blocks preserved — so the obligation is neither "
                     "unsatisfiable (else PRECOND-TOO-STRONG) nor a constant "
                     "collapse. The in-region assert must discharge; the impl is "
                     "kept verbatim so the method's own `ensures` discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is a loop-free
    # expression so its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-prepatch-ones-block",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug: the lower block fills the right quadrant with a CONSTANT
        # 1-block instead of copying the right operand's own dependency rows.
        # Correct shape (width lc+rc, right row count) and correct upper block,
        # but the lower-body content is wrong wherever a right row has a 0 entry.
        "module": _impl(
            "    let upper : List (List Int) := left.map (widenRight rc)\n"
            "    let lower : List (List Int) := right.map (fun row => List.replicate lc 0 ++ row.map (fun _ => 1))\n"
            "    return upper ++ lower"),
        "refinement": "this IS the pre-fix behaviour: the lower-right block is "
                      "overwritten by a constant all-ones fill instead of the "
                      "right operand's own dependency rows. On a nested parallel "
                      "composition — where the right operand is itself a compound "
                      "whose dependency matrix has genuine 0 entries off its own "
                      "diagonal — this makes those outputs spuriously appear "
                      "dependent on every right input, the exact defect the issue "
                      "reports. The failing separability tests assert those 0 "
                      "entries survive, so this would NOT resolve.",
        "rationale": "REJECT from `out = blockDiag ...` via the LOWER-BODY "
                     "sub-behaviour of `widenLeft`: the post-image copies each "
                     "right row through unchanged, but the rival replaces it with "
                     "an all-ones row, differing wherever a right row has a 0 "
                     "entry. Verifying would be SPEC-TOO-WEAK (the block's own "
                     "structure is unpinned). Refuted at left=[[1]], right=[[1,0]], "
                     "lc=1, rc=2: gold's lower row is [0,1,0], the rival's [0,1,1].",
        "witness": _witness("combineParallelTester [[1]] [[1,0]] 1 2"),
    },
    {
        "id": "weak-firstrow-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every lower row EXCEPT the first, which it zeroes out (drops
        # the first right row's own columns). Pins the shape and is correct on the
        # rest of the domain; diverges only on the single first lower row whenever
        # the first right row has a 1.
        "module": _impl(
            "    let upper : List (List Int) := left.map (widenRight rc)\n"
            "    let lower : List (List Int) := match right with\n"
            "      | [] => []\n"
            "      | r0 :: rest => (List.replicate lc 0 ++ r0.map (fun _ => 0)) :: rest.map (widenLeft lc)\n"
            "    return upper ++ lower"),
        "refinement": "a partial-domain counterpart that zeroed the first right "
                      "operand row while copying the rest would make that one "
                      "output appear independent of ALL inputs — a wrong "
                      "separability column for the first right output. On the "
                      "failing nested models that output carries a real "
                      "dependency, so the expected matrix would not match and it "
                      "would NOT resolve. Tests that the clause pins EVERY row, "
                      "not most rows.",
        "rationale": "REJECT from `out = blockDiag ...`: `blockDiag` widens the "
                     "first right row like the rest, but the rival zeroes it, so "
                     "the lists disagree whenever the first right row has a 1 "
                     "entry. Refuted at left=[[1,1]], right=[[1]], lc=2, rc=1: "
                     "gold's lower row is [0,0,1], the rival's [0,0,0]. "
                     "Discrimination comes from the first `right` row (and this "
                     "point moves lc=2, rc=1, distinct from the other witnesses).",
        "witness": _witness("combineParallelTester [[1,1]] [[1]] 2 1"),
    },
    {
        "id": "weak-reverse-right-rows",
        "kind": "uniqueness",
        "expect": "reject",
        # Copies the right block but with its ROWS reversed. Correct shape,
        # correct upper block, correct lower-left zero-pad; equal to gold only
        # when the right operand's row sequence is a palindrome.
        "module": _impl(
            "    let upper : List (List Int) := left.map (widenRight rc)\n"
            "    let lower : List (List Int) := right.reverse.map (widenLeft lc)\n"
            "    return upper ++ lower"),
        "refinement": "a counterpart that flipped the row order of the right "
                      "operand's block would permute which right output depends on "
                      "which right input — transposing the True positions on the "
                      "lower-right diagonal. On the failing nested models the right "
                      "child's diagonal is permuted, so the assembled separability "
                      "matrix does not match the expected one and it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = blockDiag ...` via the ORDER "
                     "sub-behaviour: the post-image widens the right rows in their "
                     "own order, the rival in reverse, so for any non-palindromic "
                     "right (≥2 rows) the lower block disagrees. Refuted at "
                     "left=[[1]], right=[[1],[0]], lc=1, rc=1: gold's lower block "
                     "is [[0,1],[0,0]], the rival's [[0,0],[0,1]]. Discrimination "
                     "comes from `right`'s row order — a near-miss the "
                     "content-fill rivals do not subsume.",
        "witness": _witness("combineParallelTester [[1]] [[1],[0]] 1 1"),
    },
    {
        "id": "weak-left-leak-block",
        "kind": "uniqueness",
        "expect": "reject",
        # Dual of the gold bug: the lower-LEFT quadrant is filled with a constant
        # 1-block instead of zeros, then the actual right row. Right width still
        # lc+rc (correct shape), but the lower-left block is non-zero — a spurious
        # dependence of the right outputs on the left inputs.
        "module": _impl(
            "    let upper : List (List Int) := left.map (widenRight rc)\n"
            "    let lower : List (List Int) := right.map (fun row => List.replicate lc 1 ++ row)\n"
            "    return upper ++ lower"),
        "refinement": "the dual defect: leaving the lower-left quadrant non-zero "
                      "makes the right operand's outputs spuriously depend on the "
                      "LEFT inputs — a false off-diagonal block. The failing "
                      "separability tests require that quadrant to be all-False, "
                      "so a real patch with this bug would NOT resolve.",
        "rationale": "REJECT from `out = blockDiag ...` via the LOWER-PAD "
                     "sub-behaviour of `widenLeft` (`lc` leading ZEROS): the rival "
                     "prepends ones instead, so the lower-left block differs from "
                     "zeros whenever lc ≥ 1. Verifying would be SPEC-TOO-WEAK (the "
                     "off-diagonal-zero property is unpinned). Refuted at "
                     "left=[[1,0]], right=[[1]], lc=2, rc=1: gold's lower row is "
                     "[0,0,1], the rival's [1,1,1]. Discrimination comes from the "
                     "`lc` left-pad being zero.",
        "witness": _witness("combineParallelTester [[1,0]] [[1]] 2 1"),
    },
    {
        "id": "weak-upper-ones-pad",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the UPPER block (the mirror quadrant the gold bug did NOT touch,
        # so the transparent spec's upper-pad clause gets its own rival): each
        # left row is padded on the right with a constant 1-block instead of
        # zeros. Correct shape and correct lower block; the upper-right quadrant
        # is spuriously non-zero.
        "module": _impl(
            "    let upper : List (List Int) := left.map (fun row => row ++ List.replicate rc 1)\n"
            "    let lower : List (List Int) := right.map (widenLeft lc)\n"
            "    return upper ++ lower"),
        "refinement": "a counterpart that padded the left operand's rows on the "
                      "right with ones would make the left outputs spuriously "
                      "depend on the right inputs — a false off-diagonal block in "
                      "the UPPER-right quadrant. The failing separability tests "
                      "require that quadrant all-False, so this would NOT resolve. "
                      "(This attacks the mirror clause the well-known defect left "
                      "correct, so the transparent post-image's upper-pad "
                      "sub-behaviour is not left untested.)",
        "rationale": "REJECT from `out = blockDiag ...` via the UPPER-PAD "
                     "sub-behaviour of `widenRight` (`rc` trailing ZEROS): the "
                     "rival appends ones, so the upper-right block differs from "
                     "zeros whenever rc ≥ 1. Refuted at left=[[1],[0]], right=[[1]], "
                     "lc=1, rc=1: gold's upper block is [[1,0],[0,0]], the rival's "
                     "[[1,1],[0,1]]. Discrimination comes from the `rc` right-pad "
                     "being zero (the binder no other rival's upper block abuses).",
        "witness": _witness("combineParallelTester [[1],[0]] [[1]] 1 1"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus an EMPTY AXIOM lane.
# This bundle models the SAME purely-functional core — the block-diagonal
# assembly of the parallel composition — over `List (List Int)` instead of the
# sibling's PSeq[PSeq[int]] carrier with a deep `expected_row` oracle. The value
# surface carries across intact; there is no permission surface on either side.
#
#   sibling case                 -> here                            disposition
#   --------------------------------------------------------------------------
#   pos-expected-row-call        -> pos-blockdiag-direct            PORTED
#   pos-branch-reorder           -> pos-let-reorder                 PORTED
#   admiss-f2p-grid              -> admiss-f2p-grid                 PORTED (re-aimed)
#   weak-prepatch-ones-block     -> weak-prepatch-ones-block        PORTED
#   weak-firstrow-dropped        -> weak-firstrow-dropped           PORTED
#   weak-reverse-right-rows      -> weak-reverse-right-rows         PORTED
#   weak-left-leak-block         -> weak-left-leak-block            PORTED
#   (no sibling)                 -> weak-upper-ones-pad             ADDED
#   AXIOM_TESTS ([] )            -> (none)                          DROPPED (G-AX)
#   frame-mutation               -> (none)                          VACUOUS
#
# All 7 sibling SPEC cases PORTED (2 positives, 1 admissibility, 4 rivals); one
# rival added; the empty axiom lane dropped.
#
# PORTED (positives): pos-expected-row-call called the deep model directly for
#   every row — here the deep model is `blockDiag`, so the direct-call reshape is
#   `return blockDiag left right lc rc`. pos-branch-reorder reordered the two row
#   branches — here the assembly is two `let`-bound blocks, so the reorder binds
#   the lower block before the upper and stacks in the same order. Both keep the
#   whole assembly, so the frozen `loom_solve` closes the byte-identical
#   obligation (both verified out-of-band with real builds).
# PORTED-RE-AIMED (admissibility): the sibling constructs a concrete 2x2 0/1 grid
#   and asserts is_grid admits it. This backend has two `require` rectangularity
#   clauses (not one is_grid predicate) and no permission surface; the re-aimed
#   probe asserts BOTH clauses admit a pair of 2x2 diagonal matrices AND the
#   post-image is non-degenerate there (the full 4x4 block-diagonal identity, both
#   off-diagonal quadrants zero, both diagonal blocks preserved).
# PORTED (rivals): the four sibling rivals port directly to the four structural
#   sub-behaviours of `out = blockDiag ...`: ones-block -> LOWER-BODY,
#   firstrow-dropped -> single-row partial domain, reverse-right-rows -> ORDER,
#   left-leak-block -> LOWER-PAD. Each carries a machine-checked witness that
#   ELABORATES against the rival and FAILS against gold (two real builds per case).
# ADDED (weak-upper-ones-pad): the sibling has no upper-block rival because the
#   left-side handling was already correct pre-fix. But on THIS carrier the
#   transparent post-image pins the UPPER-PAD (widenRight) zero property as its
#   own clause, so a rival that fills the upper-right quadrant with ones is a
#   distinct SPEC-TOO-WEAK probe and the ONLY rival that abuses the `rc` right-pad.
#   Included so no top-level structural sub-behaviour of the clause is unattacked.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the assembly is concrete list arithmetic),
#   so there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
# VACUOUS (frame-mutation): the sibling already records this class as vacuous
#   (its PSeq inputs carry no heap permission). This backend is referentially
#   transparent and declares no `mut` binder — every input is an immutable value
#   with no heap footprint — so there is no read-only field to overwrite and no
#   substitute probe. Not fabricated (porting map: vacuous here).
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 5 distinct input points):
#     left  — [[1]], [[1,1]], [[1]], [[1,0]], [[1],[0]]: contents/length varied.
#     right — [[1,0]], [[1]], [[1],[0]], [[1]], [[1]]: contents, length, ORDER
#             (the reverse rival's [[1],[0]] is non-palindromic) varied.
#     lc    — 1, 2, 1, 2, 1: both widths exercised.
#     rc    — 2, 1, 1, 1, 1: both widths exercised.
#   Every top-level structural sub-behaviour of `out = blockDiag ...` is attacked:
#   UPPER-PAD (weak-upper-ones-pad), LOWER-PAD (weak-left-leak-block), LOWER-BODY
#   (weak-prepatch-ones-block), ORDER (weak-reverse-right-rows), and the
#   pin-every-row SHAPE (weak-firstrow-dropped). No two rivals share an input tuple.
AXIOM_TESTS = []
