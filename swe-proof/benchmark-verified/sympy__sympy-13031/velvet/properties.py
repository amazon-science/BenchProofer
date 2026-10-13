"""properties.py — G-PBT falsification battery for sympy__sympy-13031 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
both ``prove_correct`` obligations survive with byte-identical statements) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: it must elaborate against the rival and FAIL against the frozen
solution).

DEFENDED SURFACE (two contracted methods, the horizontal/vertical transpose
pair):

  stackHorizontally (A B : Block) return (out : Block)
    require A.cols = 0 ∨ A.rows = B.rows
    ensures out = hstackBlock A B          -- width = A.cols + B.cols (the SUM)

  stackVertically   (A B : Block) return (out : Block)
    require A.rows = 0 ∨ A.cols = B.cols
    ensures out = vstackBlock A B          -- height = A.rows + B.rows (the SUM)

Each block carries the touched facets ``(rows, cols, entries)``. THE PIN is the
accumulated extent: ``hstackBlock`` fixes the result width to ``A.cols + B.cols``
and ``vstackBlock`` fixes the result height to ``A.rows + B.rows`` — a plain sum
of the two operands' own facets, NEVER the shape of one operand alone. The
discriminating content of the modeled defect is exactly this accumulation: a
running extent that collapses to the second operand's extent (dropping the
first's) or to the first operand's (dropping the second's) diverges from the sum
at any input where BOTH operands carry that extent.

  * THE PIN is GROUNDED in the inputs (a sum of two carrier facets), NOT in an
    opaque answer key: the ``axioms`` region is empty and ``hstackBlock`` /
    ``vstackBlock`` are fully-unfolded ``def``s over the method's own arguments,
    so there is no oracle to echo (UNGROUNDED-ORACLE is N/A). The only way to
    satisfy either ``ensures`` is to produce the actual summed extent, which the
    positive controls do honestly.

  * FRAME-MUTATION is VACUOUS on this backend, and the reason is a LANGUAGE
    restriction, not a claim about proofs. The sibling class exists because a
    read-only operand may carry a fractional heap permission an impl overwrites
    to fabricate the accumulated extent. Here ``A`` and ``B`` are immutable
    ``Block`` values, no binder is ``mut``, and there is no heap or aliasing.
    Measured rather than asserted: an impl whose body opens with
    ``A.cols := A.cols + B.cols`` does not elaborate at all — ``error: `A.cols`
    cannot be mutated, only variables declared using `let mut` can be mutated``,
    followed by ``Failed to parse an assertion without names: WPGen sorry``. So
    such a rival could not carry an attributable rejection even if one wanted it:
    the file is refused before any postcondition reasoning happens, which is the
    tooling-error shape the audit brief says is neither a finding nor a real
    rival. Not fabricated (see footer).

  * The incompatible-operand RAISE path the sibling defends is VACUOUS here. The
    sibling forces a raise on ``a.cols≠0 ∧ a.rows≠b.rows``; on this backend that
    region lies OUTSIDE the precondition (``require A.cols = 0 ∨ A.rows = B.rows``
    is exactly the real callee's non-raising domain), so the spec says nothing
    about it and no admissible input reaches it. A rival that "returns instead of
    raising" there cannot be refuted by any in-domain witness — the class is
    genuinely absent, not omitted (see footer).

  * PARTIAL-DOMAIN / VALUE APPLIES and carries the reject lane: a rival whose
    result extent collapses to one operand's extent agrees with gold only on the
    sub-domain where the dropped operand's extent is zero, and diverges wherever
    it is positive. The same lane carries the cell-relocation and
    degenerate-re-measure rivals, whose agreement sub-domains are "the second
    operand stores nothing" and "the operands' cross-extents already agree"
    respectively.

FOUR INPUT BINDERS across the two obligations — ``A`` and ``B`` for each. The
reject witnesses drive both operands of each obligation to positive extents so
the surplus that the collapse drops is non-zero, and vary BOTH ``A`` and ``B`` at
each obligation, so a rival that mishandled only one operand's extent could not
slip past.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery: ``stackHorizontallyTester A B = false`` says the
extracted program's result violates the method's postcondition at that concrete
input, checked in a file whose ``prove_correct`` blocks have been stripped so no
tactic script can mask the verdict, and closed by ``decide``. Every argument is a
concrete ``Block`` literal with a small integer extent and at most one stored
cell, so ``decide`` reduces the extracted program without getting stuck. This is
a witnessing convenience, not a weakening: the frozen spec is untouched and each
rival's divergence from the modeled block is real at the witnessed input.

  The tester's guard matters for what a witness can say. ``derive_tester_for``
  emits ``if decide (pre A B) then (match exec A B with | res out => decide
  (post A B out) | _ => false) else true`` — so OUTSIDE the precondition the
  tester is ``true`` for every impl, gold and rival alike. Measured: with
  ``A = 1×2, B = 5×3`` (``A.cols ≠ 0`` and the heights disagree, i.e. outside
  ``require``) the ``= false`` witness fails against BOTH the frozen solution
  and a rival that returns a value there — exit 1 either way. That is the
  mechanical reason the incompatible-operand class is unattackable here rather
  than merely unattacked, and it is why every witness below is stated at an
  in-precondition input.

WHAT EACH REJECT LANE ATTACKS. The ``ensures`` is a single block equality, but it
pins three independent facets, and a rival corrupting one is invisible to a
witness aimed at another:

  * the ACCUMULATED extent (``A.cols + B.cols`` / ``A.rows + B.rows``) —
    ``weak-collapse-to-b-*`` drops the first operand's contribution,
    ``weak-forget-second-*`` drops the second's, on disjoint sub-domains;
  * the CELL RELOCATION (``B.entries.map (shiftRight A.cols)``) —
    ``weak-unshifted-cells-*``. Every extent witness runs at operands with no
    stored cells, so it would still discriminate with the relocation deleted;
    only a witness carrying an actual cell pins where that cell lands;
  * the DEGENERATE RE-MEASURE (the cross-extent a zero-extent first operand
    adopts) — ``weak-no-remeasure-*``. Every extent rival agrees with gold on
    that whole sub-domain, so it takes a rival that keeps the non-degenerate leg
    verbatim and a witness at a degenerate first operand to reach it.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13031"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the whole gold impl body of each method: a single anchor lying wholly
# ---- inside one impl region and unique in the file (both facts asserted at load
# ---- by _swap). Rivals reshaping the executable surface swap on these blocks.
_GOLD_H = (
    "    if A.cols = 0 ∧ A.rows ≠ B.rows then\n"
    "      return { rows := B.rows, cols := A.cols + B.cols,\n"
    "               entries := A.entries ++ B.entries.map (shiftRight A.cols) }\n"
    "    else\n"
    "      return { rows := A.rows, cols := A.cols + B.cols,\n"
    "               entries := A.entries ++ B.entries.map (shiftRight A.cols) }"
)
assert _BASE.count(_GOLD_H) == 1, "gold horizontal impl anchor drift"

_GOLD_V = (
    "    if A.rows = 0 ∧ A.cols ≠ B.cols then\n"
    "      return { rows := A.rows + B.rows, cols := B.cols,\n"
    "               entries := A.entries ++ B.entries.map (shiftDown A.rows) }\n"
    "    else\n"
    "      return { rows := A.rows + B.rows, cols := A.cols,\n"
    "               entries := A.entries ++ B.entries.map (shiftDown A.rows) }"
)
assert _BASE.count(_GOLD_V) == 1, "gold vertical impl anchor drift"

# ---- the frozen proof bodies (tactic script only; elided from the spec view).
# ---- The admissibility case introduces an in-region assert and retunes ONLY
# ---- the horizontal proof to clear the extra goal — the spec and the
# ---- `prove_correct stackHorizontally` obligation statement are untouched.
_PROOF_H = "prove_correct stackHorizontally by\n  loom_solve"
assert _BASE.count(_PROOF_H) == 1, "horizontal prove_correct body drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery.
# ---- Checked in a file whose `prove_correct` blocks have been stripped. Every
# ---- argument is a concrete Block literal so `decide` reduces the extracted
# ---- program without getting stuck.
def _tester_h(body):
    return ("extract_program_for stackHorizontally\n"
            "prove_precondition_decidable_for stackHorizontally\n"
            "prove_postcondition_decidable_for stackHorizontally\n"
            "derive_tester_for stackHorizontally\n\n" + body)


def _tester_v(body):
    return ("extract_program_for stackVertically\n"
            "prove_precondition_decidable_for stackVertically\n"
            "prove_postcondition_decidable_for stackVertically\n"
            "derive_tester_for stackVertically\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each reshapes the branch order (guarding on the
    # extents-agree case FIRST, the degenerate re-measure case SECOND) and keeps
    # the summed extent, so it is observationally identical to gold on the whole
    # admissible domain; `loom_solve` reproves the reshaped skeleton.
    # =====================================================================
    {
        "id": "pos-branch-reorder-h",
        "kind": "soundness",
        "expect": "verify",
        # Handle the heights-agree (normal sum) case FIRST; the degenerate
        # width-zero re-measure lands in the else. Same result on every input:
        # when A.rows = B.rows both legs build width A.cols + B.cols with height
        # A.rows (= B.rows), and the degenerate branch keeps B.rows and the sum.
        "module": _swap(
            _BASE, _GOLD_H,
            "    if A.rows = B.rows then\n"
            "      return { rows := A.rows, cols := A.cols + B.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftRight A.cols) }\n"
            "    else\n"
            "      return { rows := B.rows, cols := A.cols + B.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftRight A.cols) }"),
        "rationale": "reshaping stackHorizontally to guard on the heights-agree "
                     "case first (result height A.rows, width the sum A.cols + "
                     "B.cols) and the degenerate re-measure second (height B.rows, "
                     "same summed width) produces the identical block for every "
                     "admissible input, so `out = hstackBlock A B` still discharges "
                     "under `require A.cols = 0 ∨ A.rows = B.rows`. A correct "
                     "reshape that failed to verify would mean the spec is "
                     "SPEC-TOO-STRONG (over-fit to the gold branch spelling).",
    },
    {
        "id": "pos-branch-reorder-v",
        "kind": "soundness",
        "expect": "verify",
        # Transpose of the above: handle widths-agree first, degenerate
        # height-zero re-measure in the else. Same result on every input.
        "module": _swap(
            _BASE, _GOLD_V,
            "    if A.cols = B.cols then\n"
            "      return { rows := A.rows + B.rows, cols := A.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftDown A.rows) }\n"
            "    else\n"
            "      return { rows := A.rows + B.rows, cols := B.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftDown A.rows) }"),
        "rationale": "the transpose reshape of stackVertically: guard on the "
                     "widths-agree case first (result width A.cols, height the sum "
                     "A.rows + B.rows) and the degenerate re-measure second (width "
                     "B.cols, same summed height); identical block for every "
                     "admissible input, so `out = vstackBlock A B` still "
                     "discharges. Failing to verify would be SPEC-TOO-STRONG on the "
                     "symmetric obligation.",
    },

    # =====================================================================
    # ADMISSIBILITY — the residual risk on this surface (the precondition is
    # trivially met by an F2P-shaped input) is that the post-image is
    # UNSATISFIABLE / degenerate at the accumulation point the fix cares about.
    # This case discharges an in-region `assert`, at the discriminating
    # accumulation input (a 0×3 block joined horizontally with a 0×3 block — the
    # case whose running width the modeled defect collapses), that the post-image
    # is NON-DEGENERATE: the stacked width is exactly 6 (3 + 3), never 3. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; only the horizontal proof is retuned to clear the extra assert
    # goal by `decide` (allowed — the tactic body is elided from the spec view).
    # The assert is LIVE, and this was re-measured rather than assumed: changing
    # the asserted width from 6 to 3 (the collapsed value) makes the same file
    # FAIL to elaborate (exit 1), so the assert genuinely constrains and the
    # `<;> decide` retune does not blanket-close whatever it is handed. The
    # retune also cannot mask the method's own obligation: `loom_solve` still runs
    # first and `decide` only fires on goals it leaves, which is why the four
    # rivals below — verified against this same proof shape — still fail.
    # =====================================================================
    {
        "id": "admiss-f2p-accumulate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_H,
                  "    assert (with_name_prefix `admiss\n"
                  "      (hstackBlock { rows := 0, cols := 3, entries := [] } "
                  "{ rows := 0, cols := 3, entries := [] }\n"
                  "        = { rows := 0, cols := 6, entries := [] }))\n"
                  + _GOLD_H),
            _PROOF_H,
            "prove_correct stackHorizontally by\n  loom_solve <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped accumulation input: joining a 0×3 block beside a "
                     "0×3 block it demands the stacked width be exactly 6 (3 + 3), "
                     "accumulating the first operand's width rather than collapsing "
                     "to the second's alone. The in-region assert must discharge "
                     "(else the obligation is unsatisfiable / degenerate at the "
                     "point the fix cares about); the impl is kept verbatim so the "
                     "method's own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-collapse-to-b-h",
        "kind": "uniqueness",
        "expect": "reject",
        # The modeled defect on the horizontal join: return the second operand
        # alone (its shape and cells), dropping the first operand's accumulated
        # width. Correct only when A.cols = 0; diverges whenever A.cols > 0.
        "module": _swap(
            _BASE, _GOLD_H,
            "    return { rows := B.rows, cols := B.cols, entries := B.entries }"),
        "refinement": "a counterpart that collapses the horizontal result to the "
                      "second operand's shape drops the first operand's width from "
                      "the running total — the pre-fix single-operand short-circuit "
                      "for a measure-zero first operand. In the unchanged reduction "
                      "that folds the join over a sequence, the first operand's "
                      "width is discarded at every step, so a sequence of "
                      "zero-height blocks of widths 0,1,2,3 accumulates to width 3 "
                      "instead of 6 — exactly the reported regression. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = hstackBlock A B`: the pin fixes the width "
                     "to A.cols + B.cols, and returning B alone gives width B.cols, "
                     "which equals the sum only when A.cols = 0. Verifying would be "
                     "SPEC-TOO-WEAK (the width would not be pinned to the sum). "
                     "Refuted at A = 1×2, B = 1×3 (heights agree, A.cols = 2 > 0): "
                     "gold width 5, rival width 3.",
        "witness": _tester_h(
            "example : stackHorizontallyTester { rows := 1, cols := 2, entries := [] } "
            "{ rows := 1, cols := 3, entries := [] } = false := by\n  decide\n"),
    },
    {
        "id": "weak-forget-second-width-h",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: on the non-degenerate branch report width A.cols (drop
        # B.cols) instead of the sum. Correct when B.cols = 0 (where A.cols + 0 =
        # A.cols), so it needs its own discriminating input (B.cols > 0). Distinct
        # from weak-collapse-to-b-h, which keeps B.cols and drops A.cols.
        "module": _swap(
            _BASE, _GOLD_H,
            "    if A.cols = 0 ∧ A.rows ≠ B.rows then\n"
            "      return { rows := B.rows, cols := A.cols + B.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftRight A.cols) }\n"
            "    else\n"
            "      return { rows := A.rows, cols := A.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftRight A.cols) }"),
        "refinement": "a counterpart whose horizontal merge forgets to add the "
                      "second operand's width on the non-degenerate path reports the "
                      "first operand's width alone, so any join with a positive "
                      "second width under-counts. The failing scenario stacks blocks "
                      "of second-widths 0,1,2,3, so the accumulated width is wrong "
                      "(it would land on 0, not 6). Faithful but non-resolving.",
        "rationale": "REJECT from `out = hstackBlock A B`: reporting A.cols on the "
                     "non-degenerate branch is not A.cols + B.cols whenever B.cols "
                     "> 0. Verifying would be SPEC-TOO-WEAK on the second operand's "
                     "width contribution. Refuted at A = 1×3, B = 1×2 (heights "
                     "agree, B.cols = 2 > 0 — the regime where weak-collapse-to-b-h "
                     "reports the SAME width as gold, so this near-miss carries its "
                     "own discriminating input): gold width 5, rival width 3.",
        "witness": _tester_h(
            "example : stackHorizontallyTester { rows := 1, cols := 3, entries := [] } "
            "{ rows := 1, cols := 2, entries := [] } = false := by\n  decide\n"),
    },
    {
        "id": "weak-collapse-to-b-v",
        "kind": "uniqueness",
        "expect": "reject",
        # The transpose defect on the vertical join: return the second operand
        # alone, dropping the first operand's accumulated height. Correct only
        # when A.rows = 0; diverges whenever A.rows > 0. Confirms the symmetric
        # obligation is equally tight.
        "module": _swap(
            _BASE, _GOLD_V,
            "    return { rows := B.rows, cols := B.cols, entries := B.entries }"),
        "refinement": "the transpose of weak-collapse-to-b-h on the vertical join: "
                      "collapsing to the second operand's shape drops the first "
                      "operand's height. In the unchanged fold, a sequence of "
                      "zero-width blocks of heights 0,1,2,3 accumulates to height 3 "
                      "instead of 6 — the vertical face of the reported regression. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = vstackBlock A B`: the pin fixes the height "
                     "to A.rows + B.rows, and returning B alone gives height B.rows, "
                     "the sum only when A.rows = 0. Verifying would be "
                     "SPEC-TOO-WEAK. Refuted at A = 2×1, B = 3×1 (widths agree, "
                     "A.rows = 2 > 0): gold height 5, rival height 3.",
        "witness": _tester_v(
            "example : stackVerticallyTester { rows := 2, cols := 1, entries := [] } "
            "{ rows := 3, cols := 1, entries := [] } = false := by\n  decide\n"),
    },
    {
        "id": "weak-forget-second-height-v",
        "kind": "uniqueness",
        "expect": "reject",
        # Transpose near-miss: on the non-degenerate branch report height A.rows
        # (drop B.rows). Correct when B.rows = 0; needs its own discriminating
        # input (B.rows > 0). Distinct from weak-collapse-to-b-v.
        "module": _swap(
            _BASE, _GOLD_V,
            "    if A.rows = 0 ∧ A.cols ≠ B.cols then\n"
            "      return { rows := A.rows + B.rows, cols := B.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftDown A.rows) }\n"
            "    else\n"
            "      return { rows := A.rows, cols := A.cols,\n"
            "               entries := A.entries ++ B.entries.map (shiftDown A.rows) }"),
        "refinement": "a counterpart whose vertical merge forgets to add the second "
                      "operand's height on the non-degenerate path reports the first "
                      "operand's height alone, so any join with a positive second "
                      "height under-counts. The failing scenario stacks blocks of "
                      "second-heights 0,1,2,3, so the accumulated height is wrong. "
                      "Faithful but non-resolving.",
        "rationale": "REJECT from `out = vstackBlock A B`: reporting A.rows on the "
                     "non-degenerate branch is not A.rows + B.rows whenever B.rows "
                     "> 0. Verifying would be SPEC-TOO-WEAK on the second operand's "
                     "height contribution. Refuted at A = 2×3, B = 4×3 (widths "
                     "agree, B.rows = 4 > 0 — the regime where weak-collapse-to-b-v "
                     "matches gold, so this near-miss carries its own discriminating "
                     "input): gold height 6, rival height 2.",
        "witness": _tester_v(
            "example : stackVerticallyTester { rows := 2, cols := 3, entries := [] } "
            "{ rows := 4, cols := 3, entries := [] } = false := by\n  decide\n"),
    },

    # =====================================================================
    # CELL-RELOCATION rivals. The four extent rivals above all witness at
    # operands with NO stored cells (`entries := []`), so they leave the
    # `ensures`'s second facet — WHERE the second operand's stored cells land
    # in the combined block — entirely unattacked: every one of those witnesses
    # would still discriminate if the coordinate shift were deleted. These two
    # rivals keep the summed extent EXACTLY right and corrupt only the
    # relocation, so they are refutable only at an input with a stored cell.
    # =====================================================================
    {
        "id": "weak-unshifted-cells-h",
        "kind": "uniqueness",
        "expect": "reject",
        # Extent is the correct sum on both legs; the second operand's stored
        # cells are appended at their ORIGINAL coordinates instead of moved
        # right by the first operand's width. Invisible at every cell-free
        # input (and whenever A.cols = 0), so it needs an operand with a cell.
        "module": _swap(
            _BASE, _GOLD_H,
            "    if A.cols = 0 ∧ A.rows ≠ B.rows then\n"
            "      return { rows := B.rows, cols := A.cols + B.cols,\n"
            "               entries := A.entries ++ B.entries }\n"
            "    else\n"
            "      return { rows := A.rows, cols := A.cols + B.cols,\n"
            "               entries := A.entries ++ B.entries }"),
        "refinement": "a counterpart that widens the combined block correctly but "
                      "copies the second operand's stored cells across without "
                      "advancing their column index writes every one of them into "
                      "the region the first operand already occupies: cells collide "
                      "and overwrite instead of sitting side by side. The stacked "
                      "block then disagrees with the operands it was built from on "
                      "cell content at every input where the second operand stores "
                      "anything and the first has positive width, so the "
                      "stacking-equality assertions fail. Faithful but non-resolving.",
        "rationale": "REJECT from `out = hstackBlock A B`: the pin fixes the stored "
                     "cells to `A.entries ++ B.entries.map (shiftRight A.cols)`, and "
                     "appending `B.entries` unrelocated differs from that whenever "
                     "B stores a cell and A.cols > 0. Verifying would be "
                     "SPEC-TOO-WEAK on the relocation facet — the extent could be "
                     "pinned while cell placement floated free. Refuted at A = 1×2 "
                     "holding a cell at (0,0) and B = 1×3 holding a cell at (0,0): "
                     "gold places B's cell at column 0 + 2 = 2, the rival leaves it "
                     "at column 0, colliding with A's own cell.",
        "witness": _tester_h(
            "example : stackHorizontallyTester "
            "{ rows := 1, cols := 2, entries := [((0, 0), (5 : Int))] } "
            "{ rows := 1, cols := 3, entries := [((0, 0), (7 : Int))] } = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-unshifted-cells-v",
        "kind": "uniqueness",
        "expect": "reject",
        # Transpose: correct summed height, but the second operand's cells keep
        # their original row index instead of moving down by the first
        # operand's height.
        "module": _swap(
            _BASE, _GOLD_V,
            "    if A.rows = 0 ∧ A.cols ≠ B.cols then\n"
            "      return { rows := A.rows + B.rows, cols := B.cols,\n"
            "               entries := A.entries ++ B.entries }\n"
            "    else\n"
            "      return { rows := A.rows + B.rows, cols := A.cols,\n"
            "               entries := A.entries ++ B.entries }"),
        "refinement": "the transpose of weak-unshifted-cells-h: the combined block "
                      "is the right height but the second operand's cells keep their "
                      "original row, landing inside the first operand's rows rather "
                      "than below them. Cell content disagrees wherever the second "
                      "operand stores anything and the first has positive height. "
                      "Faithful but non-resolving.",
        "rationale": "REJECT from `out = vstackBlock A B`: the pin fixes the stored "
                     "cells to `A.entries ++ B.entries.map (shiftDown A.rows)`, and "
                     "appending `B.entries` unrelocated differs whenever B stores a "
                     "cell and A.rows > 0. Confirms the relocation facet is pinned on "
                     "the symmetric obligation too. Refuted at A = 2×1 holding a cell "
                     "at (0,0) and B = 3×1 holding a cell at (0,0): gold places B's "
                     "cell at row 0 + 2 = 2, the rival leaves it at row 0.",
        "witness": _tester_v(
            "example : stackVerticallyTester "
            "{ rows := 2, cols := 1, entries := [((0, 0), (5 : Int))] } "
            "{ rows := 3, cols := 1, entries := [((0, 0), (7 : Int))] } = false := by\n"
            "  decide\n"),
    },

    # =====================================================================
    # DEGENERATE RE-MEASURE rivals. Every rival above corrupts the
    # NON-degenerate leg; each is refuted at an input where both operands have
    # positive extent, and each would still be refuted if the degenerate leg
    # were deleted outright. But the degenerate operand is precisely the case
    # the spec's prose singles out — a block with zero extent on the stacking
    # axis must still contribute its measured extent and adopt the other
    # operand's cross-extent. These two rivals keep the non-degenerate leg
    # byte-identical to gold and drop ONLY the degenerate re-measure, so they
    # are refutable only at a degenerate first operand whose cross-extent
    # disagrees — the sub-domain the four extent rivals never enter.
    # =====================================================================
    {
        "id": "weak-no-remeasure-h",
        "kind": "uniqueness",
        "expect": "reject",
        # Always take the non-degenerate leg: report the first operand's own
        # height even when it is width-degenerate and the heights disagree, so
        # the combined block never adopts the second operand's height. Agrees
        # with gold on the whole heights-agree domain.
        "module": _swap(
            _BASE, _GOLD_H,
            "    return { rows := A.rows, cols := A.cols + B.cols,\n"
            "             entries := A.entries ++ B.entries.map (shiftRight A.cols) }"),
        "refinement": "a counterpart that keeps the running width correct but never "
                      "re-measures a width-degenerate first operand reports that "
                      "operand's own height for the combined block instead of the "
                      "height of the block it was stacked beside. Stacking beside a "
                      "degenerate operand is exactly how the folded multi-operand "
                      "reduction starts, so the very first step of a stacking "
                      "sequence fixes the wrong height and every later operand is "
                      "measured against it. Faithful but non-resolving.",
        "rationale": "REJECT from `out = hstackBlock A B`: the pin's height facet is "
                     "`if A.cols = 0 then B.rows else A.rows`, so on a width-zero "
                     "first operand whose height disagrees with the second's the "
                     "result must take B.rows, not A.rows. Verifying would be "
                     "SPEC-TOO-WEAK on the degenerate-operand clause the prose "
                     "singles out — the sub-domain where A.cols = 0, which every "
                     "extent rival above agrees with gold on. Refuted at A = 2×0, "
                     "B = 5×3 (A.cols = 0, heights disagree): gold height 5, rival "
                     "height 2.",
        "witness": _tester_h(
            "example : stackHorizontallyTester { rows := 2, cols := 0, entries := [] } "
            "{ rows := 5, cols := 3, entries := [] } = false := by\n  decide\n"),
    },
    {
        "id": "weak-no-remeasure-v",
        "kind": "uniqueness",
        "expect": "reject",
        # Transpose: never re-measure a height-degenerate first operand, so the
        # combined width stays A.cols instead of adopting B.cols.
        "module": _swap(
            _BASE, _GOLD_V,
            "    return { rows := A.rows + B.rows, cols := A.cols,\n"
            "             entries := A.entries ++ B.entries.map (shiftDown A.rows) }"),
        "refinement": "the transpose: the running height is right but a "
                      "height-degenerate first operand is never re-measured, so the "
                      "combined block keeps that operand's own width instead of "
                      "adopting the width of the block stacked below it — the "
                      "vertical face of the same first-step-of-the-fold error. "
                      "Faithful but non-resolving.",
        "rationale": "REJECT from `out = vstackBlock A B`: the pin's width facet is "
                     "`if A.rows = 0 then B.cols else A.cols`, so on a height-zero "
                     "first operand whose width disagrees the result must take "
                     "B.cols. Confirms the degenerate-operand clause is pinned on "
                     "the symmetric obligation. Refuted at A = 0×2, B = 4×3 "
                     "(A.rows = 0, widths disagree): gold width 3, rival width 2.",
        "witness": _tester_v(
            "example : stackVerticallyTester { rows := 0, cols := 2, entries := [] } "
            "{ rows := 4, cols := 3, entries := [] } = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 4 uniqueness rivals — one on the
# raise path, three partial-domain) plus 2 AXIOM_TESTS. This bundle models BOTH
# join kernels DEEPLY (the shape-and-cell arithmetic `hstackBlock`/`vstackBlock`,
# spelled out), so there is no axiom and no permission surface; the value surface
# (the accumulated extent) carries across, and the transpose symmetry is
# preserved by attacking both obligations.
#
#   sibling case                       -> here
#   -----------------------------------------------------------------------
#   pos-control-branch-reorder         -> pos-branch-reorder-h            PORTED
#                                         + pos-branch-reorder-v          ADDED (transpose)
#   admiss-f2p-accumulate              -> admiss-f2p-accumulate           RE-AIMED
#   frame-mutate-a-cols                -> (none)                          VACUOUS
#   partial-domain-reset-bcols         -> weak-collapse-to-b-h            PORTED
#   partial-domain-forget-bcols        -> weak-forget-second-width-h      PORTED
#   control-flow-no-raise              -> (none)                          VACUOUS
#   partial-domain-reset-below         -> weak-collapse-to-b-v            PORTED
#                                         + weak-forget-second-height-v   ADDED (transpose)
#   ax-shape-sound / ax-shape-cont.    -> (none)                          DROPPED (G-AX lane)
#   (no sibling counterpart)           -> weak-unshifted-cells-h/-v       ADDED (relocation facet)
#   (no sibling counterpart)           -> weak-no-remeasure-h/-v          ADDED (degenerate facet)
#
# 4 ported, 1 re-aimed, 6 added (2 transpose symmetry, 2 cell relocation, 2
# degenerate re-measure), 2 vacuous, 2 axiom-lane dropped.
#
# The four ADDED non-transpose rivals exist because the sibling's `Mat` carries
# only `(rows, cols)`: it has no cell store and no separate degenerate leg, so
# the relocation and re-measure facets have no sibling case to port. They are
# facets THIS carrier adds, and a battery that mirrored the sibling one-for-one
# would leave both unattacked while every case still passed honestly.
#
# VACUOUS (frame-mutate-a-cols): the sibling stores the accumulated extent back
#   into a read-only operand held at half heap permission and is rejected for
#   INSUFFICIENT PERMISSION before any value reasoning. Here `A` and `B` are
#   immutable `Block` values, no binder is `mut`, and there is no heap or
#   aliasing. Measured, not asserted: an impl body opening with
#   `A.cols := A.cols + B.cols` is refused by the ELABORATOR — "`A.cols` cannot
#   be mutated, only variables declared using `let mut` can be mutated", then
#   "Failed to parse an assertion without names: WPGen sorry". The rejection is
#   therefore a language restriction with no spec content, which is exactly what
#   makes the class vacuous rather than merely hard: there is no admissible
#   variant to write, so a case here could only ever record a tooling error.
#   No substitute is fabricated (per the porting map, this class is legitimately
#   dropped here rather than replaced).
# VACUOUS (control-flow-no-raise): the sibling forces a raise on the incompatible
#   operand pair (`a.cols≠0 ∧ a.rows≠b.rows`) and refutes an impl that returns a
#   value there instead. On this backend that region lies OUTSIDE the
#   precondition — `require A.cols = 0 ∨ A.rows = B.rows` is exactly the real
#   callee's non-raising domain (mapping.md §2) — so the spec places no obligation
#   on it and no admissible input reaches it. Demonstrated with real builds rather
#   than argued: `derive_tester_for` emits `if decide (pre …) then … else true`,
#   so at `A = 1×2, B = 5×3` (outside `require`) the tester evaluates to `true`
#   for EVERY impl. A `= false` witness there fails against the frozen solution
#   AND against a rival that returns a value on that path — exit 1 on both sides,
#   i.e. `witness-unproven`, never a refutation. The complementary `= true`
#   witness elaborates against gold (exit 0), confirming the region is
#   unconstrained rather than merely unprobed. The class collapses into the
#   precondition rather than into a value clause; not omitted, genuinely
#   absent on this carrier.
# RE-AIMED (admissibility): the sibling establishes that a half-permission input
#   is readable and a normal return is reachable. There is no permission here and
#   the precondition is trivially met, so that probe is vacuous. It is re-aimed at
#   the residual admissibility risk on this surface: that the post-image is
#   unsatisfiable / degenerate at the accumulation point. The case discharges an
#   in-region assert pinning the horizontal join of a 0×3 block beside a 0×3 block
#   to width exactly 6 — accumulating the first operand's width, not collapsing to
#   the second's.
# DROPPED (ax-shape-*): the sibling's two AXIOM_TESTS run the real callees in
#   Docker to validate the deep shape model. This bundle has NO axiom (mapping.md
#   §3: both kernels are modeled deeply; there is no A-reference to probe and no
#   axiom_check.py — G-AX is skipped), so there is no axiom lane to mirror. The
#   axiom lane is G-AX's job and this gate ignores AXIOM_TESTS regardless.
#
# TWO RESHAPES THAT ARE NOT SPEC HOLES (recorded so the next reader does not
# re-derive them as findings). Both were built; neither is a soundness hole.
#   * Inline cell relocation. Replacing `B.entries.map (shiftRight A.cols)` with
#     `B.entries.map (fun e => ((e.1.1, e.1.2 + A.cols), e.2))` — the same
#     function, beta-expanded — does NOT verify under the frozen `loom_solve`
#     (exit 1: two `out = hstackBlock A B` goals survive). That is a TACTIC gap,
#     not spec strength: `loom_solve` does not push `List.map` congruence through
#     an anonymous function. Retuning the proof body to
#     `loom_solve <;> simp only [hstackBlock] <;> congr 1 <;> (try funext e) <;>
#     (try simp [shiftRight]) <;> omega` closes it (exit 0), so the reshape IS
#     provable and the spec does not reject it. It is left out of SPEC_TESTS
#     because a positive control whose value is "the retune I had to find" tests
#     the tactic, not the spec; the four cell-free positives already cover the
#     reshape lane.
#   * Reordered cell list. Emitting `B.entries.map (shiftRight A.cols) ++
#     A.entries` (second operand's cells first) does not verify, and here the
#     spec is RIGHT to refuse it on this carrier: `Block.entries` is a `List`,
#     so the two results are genuinely distinct values — proved directly,
#     `… ≠ hstackBlock … := by decide` elaborates (exit 0) at A=1×1 holding a
#     cell and B=1×2 holding a cell. mapping.md §2 records the repo-side
#     observable as an unordered cell store, so list ORDER is finer than the
#     bijection; the spec is stricter than the carrier's observable on this one
#     facet. That is a spec-STRENGTH observation with no wrong impl behind it
#     (order is not behavior the F2P tests can see), so it is not a spec hole and
#     not a rival — noted here as the one place where the Lean model
#     distinguishes more than the Python object does.
#
# BINDER / CLAUSE COVERAGE. Each obligation carries a single `ensures` clause
#   (`out = hstackBlock A B` / `out = vstackBlock A B`), but that clause pins
#   three separable facets, and each is attacked by its own rival pair per
#   obligation — four rivals per obligation, eight in all:
#
#     facet                  horizontal                    vertical
#     ---------------------------------------------------------------------
#     accumulated extent     weak-collapse-to-b-h          weak-collapse-to-b-v
#       (both directions)    weak-forget-second-width-h    weak-forget-second-height-v
#     cell relocation        weak-unshifted-cells-h        weak-unshifted-cells-v
#     degenerate re-measure  weak-no-remeasure-h           weak-no-remeasure-v
#
#   Both obligations are defended (a branch-reorder positive each; the
#   admissibility case additionally defends the horizontal one) and attacked on
#   every facet. NO TWO RIVALS SHARE A WITNESS, because each agrees with gold on
#   a region the others diverge on:
#     * collapse-to-b matches gold exactly when A.cols=0 / A.rows=0;
#     * forget-second matches when B.cols=0 / B.rows=0;
#     * unshifted-cells matches whenever the second operand stores nothing —
#       which is true at EVERY extent witness, so it needs an operand with a
#       stored cell (A=1×2 with a cell at (0,0), B=1×3 with a cell at (0,0));
#     * no-remeasure matches on the entire non-degenerate domain, i.e. wherever
#       the cross-extents already agree — which is true at every other witness,
#       so it needs a degenerate first operand with a disagreeing cross-extent
#       (A=2×0 vs B=5×3; A=0×2 vs B=4×3).
#   Both input binders of each obligation are moved across the witness set and
#   every operand is driven to a positive collapsed extent, so the dependence of
#   the summed extent on BOTH operands is demonstrated. The variation is
#   MEANINGFUL and not two spellings of one point: each witness input is a place
#   where the frozen spec's verdict flips for its own rival and holds for every
#   other rival's, which is why dropping any single rival would leave a facet
#   with no discriminating input at all.
AXIOM_TESTS = []
