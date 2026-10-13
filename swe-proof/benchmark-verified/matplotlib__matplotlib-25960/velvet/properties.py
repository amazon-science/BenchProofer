"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25960 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds by
construction and the ``prove_correct axisCellExtents`` header survives with its
statement intact) and swaps in a candidate implementation. It is judged by the
real verifier: ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — ELABORATES against the rival, FAILS against the
frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  axisCellExtents (n : Nat) (s : Rat) return (out : List (Rat × Rat))
    require n ≥ 1                                       -- P1
    require s ≥ 0                                       -- P2
    ensures out.length = n                              -- C1  (structural)
    ensures out = axisExtents n s                        -- C2  (the value pin)

The method lays out ``n`` equally-sized cells along the unit axis, leaving a
uniform gap of fraction ``s`` between neighbours, and reports each cell's
``(low, high)`` extent in order from the low end.

WHICH CLAUSE CONSTRAINS THE IMPL. Two independent top-level clauses:

  * C1 (``out.length = n``) — the CARDINALITY: exactly one extent per cell, no
    more and no fewer. Independent of C2 in the sense that a rival can satisfy
    the elementwise arithmetic and still return the wrong number of extents.
  * C2 (``out = axisExtents n s``) — the full VALUE pin, a total function of both
    binders. It fixes, per index ``i``: the low edge (``i · cellPitch n s``), the
    span (``+ cellSize n s``), and the ORDER of the list (low end first).

Both clauses are GROUNDED: ``cellSize``, ``cellPitch`` and ``axisExtents`` are
transparent computable ``def``s in the ``pure`` region, written as closed forms of
the method's own two arguments. The ``axioms`` region is EMPTY — there is no
opaque answer-key oracle anywhere in this bundle, so pinning ``out = axisExtents
n s`` is honest grounding rather than an echo, and computing ``axisExtents n s``
IS doing the modeled work.

THE LOAD-BEARING DISTINCTION is the ``(1 + s)`` factor carried by the pitch.
``cellPitch n s = cellSize n s * (1 + s)`` is strictly greater than the cell size
for every ``s > 0``, so a positive requested gap genuinely SEPARATES consecutive
cells: high of cell ``i`` lies strictly below low of cell ``i+1``. A layout that
splits the axis evenly (pitch = size = ``1/n``) agrees with the pinned layout on
the whole sub-domain ``s = 0`` and diverges exactly where a gap was requested —
which is the domain the failing test drives. C2 pins the separating layout, so
the even-split reading contradicts it at every positive ``s``.

CARRIER NOTE (decisive for this port). Both binders are exact and computable:
``n : Nat`` and ``s : Rat`` (mapping.md §2 — the placement is an exact ratio
computation with no cross-cell round-off accumulation, so an exact ordered
carrier is faithful and every extent is a rational the kernel can evaluate). The
whole postcondition is therefore DECIDABLE at a concrete ``(n, s)``: no rival
needs conditioning on an opaque term, so no witness in this battery binds a
hypothesis and the gate's consistency probe is a no-op on all seven.

WITNESS SHAPE AND CLOSER (measured with real builds). The spec is a ``method``
contract, so each witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``prove_precondition_decidable_for`` /
``prove_postcondition_decidable_for`` / ``derive_tester_for``) and asserts
``axisCellExtentsTester n s = false`` at one concrete input — i.e. "the extracted
program's result at this input does NOT satisfy the contract". The closer is
``with_unfolding_all rfl``, and the choice is load-bearing rather than cosmetic:

  * a bare ``decide`` is DEAD here (the spec_guide ``Rat`` trap): it reduces the
    ``Decidable`` instance but not ``Rat`` arithmetic, and gets stuck at
    ``instDecidableEqBool (axisCellExtentsTester 2 (1 / 2)) false``. Plain
    ``rfl`` fails too (the tester is behind irreducible-by-default definitions),
    and ``simp`` on the unfolded ``cellSize``/``cellPitch``/``Rat.normalize``
    chain reports ``simp made no progress``.
  * ``decide +kernel`` DOES close the goal against each rival, and the frozen
    build does fail — but it fails with ``Reduction got stuck at the `Decidable`
    instance ... did not reduce to `isTrue` or `isFalse```. That is the exact
    signature the gate screens for as ``witness-undecided``, and screening it is
    CORRECT: an exit code produced by a reduction that never happened cannot
    attest to a refutation. So the earlier revision of this battery — which
    shipped ``decide +kernel`` on the strength of the two exit codes alone — had
    every reject case judged inconclusive (recorded MALFORMED-TESTS), even
    though each rival really is refuted here. The exit codes agreed with the
    author's claim while the frozen side had decided nothing.
  * ``with_unfolding_all rfl`` unfolds through the tester and settles the
    equation by definitional reduction, so BOTH sides return a real verdict and
    no stuck-reduction text appears on either. Not ``native_decide`` (banned, and
    compiler-trust would make the witness elaborate against gold too, defeating
    both halves at once); no banned token appears in any witness.

The discrimination is POSITIVE evidence, not accidental stuckness, and that was
measured on this bundle rather than argued. For each of the seven witness points,
three real builds with ``scripts/lean_verify.sh``:

  * ``= false`` against the RIVAL           -> exit 0 (the rival violates C1/C2);
  * ``= false`` against the FROZEN solution -> exit 1, and the error is a genuine
    verdict (``axisCellExtentsTester n s`` *is not definitionally equal to*
    ``false``), with NO stuck-reduction message;
  * ``= true``  against the FROZEN solution -> exit 0.

The third build is what makes the second one mean something: gold's failure is
"the frozen impl SATISFIES the contract at this input", the inference the
two-build check actually needs, and not a tactic that could not evaluate.
Every build behaved as stated, and TWO INDEPENDENT AUDITS re-derived them from the
gate's own `witness_file` construction, reproducing every exit code and every
error text (each gold-side failure reads `axisCellExtentsTester n s` *is not
definitionally equal to* `false`, with no stuck-reduction message).

The SECOND audit added the FORGERY check on every reject case, which is what
rules out a gold-side exit code that carries no information about the claim: for
each witness point it also built the FLIPPED claim (`= true` in place of
`= false`) against both impls. Gold's error TRACKS the claim rather than being
constant — `= false` on gold fails (exit 1) while `= true` on gold succeeds
(exit 0), and symmetrically the flipped claim FAILS against each rival (exit 1)
with the mirror-image `not definitionally equal to true` verdict. So the kernel
really is deciding the equation on both sides at every point, and no case is
passing on an error that would appear for a witness asserting gold is CORRECT
there.

The audit additionally confirmed, with real builds, the PARTIAL-DOMAIN claims the
rationales make — which no gate checks, since the gate only ever asks whether a
rival is refuted SOMEWHERE. For each rival that claims to be correct on a
sub-domain, `axisCellExtentsTester n s = true` was built against THAT RIVAL at a
point inside the claimed sub-domain and exited 0, i.e. the rival really does
satisfy the contract there: reject-even-split at (2, 0) and (5, 0) [the `s = 0`
sub-domain], reject-cell-swallows-gap at (3, 0) [same], reject-even-split-pinned
at (2, 1/2), (3, 1/3) and (4, 1/6) [correct off its pinned point],
reject-reversed-order at (1, 1/2) [reverse of a singleton], and
reject-gap-clamped-at-one at (3, 1/6), (2, 1/2) and (2, 1) [the whole `s <= 1`
sub-domain, up to and including the clamp threshold itself]. So each near-miss is
a genuine near-miss and not a rival that is simply wrong everywhere.

ADVERSARIAL READ of the nagini classes on THIS carrier (full accounting in the
footer):

  * PARTIAL-DOMAIN / UNIQUENESS — the real attack surface, ported in full. Seven
    rivals, each wrong on a sub-domain the pinned layout separates.
  * SOUNDNESS positives — APPLY. Four structurally-different CORRECT reshapes
    must still verify, else SPEC-TOO-STRONG. All four proofs close honestly (see
    below). They vary on four independent axes: the post-image `def` FOLDED
    (definitionally the frozen body), the ARITHMETIC of the stride distributed
    differently, the TRAVERSAL STRUCTURE split into two passes, and correctness
    by ARITHMETIC IDENTITY (the last cell's far edge written as the literal axis
    end, correct only via the normalization identity) rather than by shape match.
  * ADMISSIBILITY — APPLIES with real content: unlike many bundles this method
    DOES carry two ``require`` clauses (P1, P2), so the nagini "the precondition
    admits a normal grid input" probe has a genuine counterpart.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling declares this class
    N/A for its own reason (scalar-by-value args, a freshly constructed result),
    and on this carrier it is vacuous a second time over: Velvet is
    referentially transparent, ``n`` and ``s`` are immutable non-``mut`` values,
    and there is no heap, aliasing or permission system. No read-only input
    exists to overwrite. No substitute probe fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as a WRONG echo, same as nagini and for the same
    reason: the post-image is grounded in the two arguments (transparent ``def``s,
    empty ``axioms`` region), so echoing ``axisExtents n s`` IS the correct
    computation. Carried over as an honest positive control rather than a rival.
  * CONTROL-FLOW-EFFECT — N/A. The value abstraction pins the whole output (both
    the cardinality and every extent); there is no raise/side-effect channel the
    spec cannot see.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25960"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, i.e. everything strictly
# ---- between the method's `-- impl-start` and `-- impl-end`. It lies wholly
# ---- inside the single impl region and is unique in the file (both asserted at
# ---- load by _swap), so every edit keeps same_spec by construction and leaves
# ---- the `prove_correct axisCellExtents` header and statement untouched.
_IMPL = (
    "    let extents := (List.range n).map\n"
    "      (fun (i : Nat) => ((i : Rat) * cellPitch n s, "
    "(i : Rat) * cellPitch n s + cellSize n s))\n"
    "    return extents"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape whose residual goal differs from the
# ---- frozen one may retune it without touching the spec or dropping the
# ---- obligation. Unique in the file.
_PROOF = (
    "prove_correct axisCellExtents by\n"
    "  loom_solve\n"
    "  simp [axisExtents]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned, for a correct reshape whose
    residual goal is no longer the frozen one."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble + closer. The postcondition is a `method` contract, so a
# ---- witness reaches it via Velvet's tester machinery and refutes it at one
# ---- concrete (n, s). Both binders are exact and computable, so no witness
# ---- conditions on an opaque term and none binds a hypothesis (nothing for the
# ---- gate's consistency probe to check). Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script masks the verdict.
# ---- Closer is `with_unfolding_all rfl`, NOT `decide`/`decide +kernel`: bare
# ---- `decide` is stuck on Rat arithmetic (the spec_guide trap), and
# ---- `decide +kernel` closes each rival but leaves the FROZEN build failing by
# ---- stuck reduction — no verdict, which the gate correctly refuses as
# ---- `witness-undecided`. `with_unfolding_all rfl` makes both sides decide.
# ---- Not `native_decide` (banned; it would elaborate against gold too).
_TESTER = (
    "extract_program_for axisCellExtents\n"
    "prove_precondition_decidable_for axisCellExtents\n"
    "prove_postcondition_decidable_for axisCellExtents\n"
    "derive_tester_for axisCellExtents\n\n"
)


def _witness(n, s):
    """`axisCellExtentsTester n s = false` — the extracted program's result at
    this input violates the contract."""
    return (_TESTER
            + f"example : axisCellExtentsTester {n} ({s} : Rat) = false := by\n"
              "  with_unfolding_all rfl\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Both were run out-of-band: exit 0.
    # =====================================================================
    {
        "id": "pos-control-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the extents DIRECTLY via the grounded closed form,
        # dropping the inline per-index expansion. Ports the nagini pos-helpers
        # control (call the spec's own grounded helpers instead of re-inlining
        # their bodies). The frozen proof body closes unchanged.
        "module": _impl("    return (axisExtents n s)"),
        "rationale": (
            "PASS SOURCE = C1 + C2. The post-image `axisExtents n s` is GROUNDED "
            "in both arguments (a transparent computable `def` over `cellSize` / "
            "`cellPitch`, with an EMPTY axioms region — no opaque answer key), so "
            "reporting it directly is the honest cheapest CORRECT impl rather than "
            "an echo: any wrong layout still fails C2. C2 is literally that "
            "equality and C1 follows from the per-cell expansion having one entry "
            "per index, so this MUST verify; if it cannot, the spec is "
            "SPEC-TOO-STRONG. Ports the nagini pos-helpers positive (compute each "
            "extent via the spec's own grounded closed-form helpers), and doubles "
            "as evidence the grounded pin is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-factored-pitch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the cell size once and build the stride as an explicit
        # per-cell separation, size + s*size, instead of the multiplied form
        # size*(1+s). Algebraically equal, structurally different (an extra
        # binding and a distributed product). Ports the nagini pos-factored
        # control. The residual goal is no longer closed by the frozen
        # `simp [axisExtents]` — it leaves the distributivity obligation
        #   a * (c + s*c) = a * (c * (1 + s))
        # so the proof body is retuned by adding `grind` (the tactic body is
        # elided from the spec view; the obligation header and statement are
        # untouched, no lemma is added, nothing is assumed). Run out-of-band:
        # exit 0. `ring` is not a known tactic in this workspace.
        "module": _impl_reproved(
            "    let size : Rat := cellSize n s\n"
            "    let step : Rat := size + s * size\n"
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => ((i : Rat) * step, (i : Rat) * step + size))\n"
            "    return extents",
            "prove_correct axisCellExtents by\n"
            "  loom_solve\n"
            "  simp [axisExtents, cellPitch]\n"
            "  grind"),
        "rationale": (
            "PASS SOURCE = C1 + C2. A CORRECT impl that computes the stride as an "
            "explicit cell-plus-separation sum (`size + s * size`) rather than the "
            "multiplied form (`size * (1 + s)`) — the same value distributed "
            "differently, so every extent and the cardinality both still match the "
            "post-image. It MUST verify, else C2 over-fits the exact arithmetic "
            "SHAPE of the pitch rather than its VALUE (SPEC-TOO-STRONG), which "
            "would make the spec unusable by any honest reimplementation. Ports the "
            "nagini pos-factored positive (explicit per-step separation variable). "
            "Chosen deliberately as a cheap reshape: the residual goal is pure "
            "distributivity over Rat, needing no new induction and no new lemma."
        ),
    },

    {
        "id": "pos-control-two-pass",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: TWO traversals instead of one. The low edges are materialized
        # in a first pass, then a second pass pairs each with its far edge. Added
        # by audit because the other two positives do not cover this axis of
        # variation: pos-control-closed-form is the frozen body with one `def`
        # FOLDED (definitionally equal — the frozen proof body closes it
        # untouched), and pos-control-factored-pitch varies the ARITHMETIC while
        # keeping the single `List.range n |>.map` traversal. This one changes the
        # traversal STRUCTURE, so the residual goal is a map-composition
        # obligation the frozen `simp [axisExtents]` does not close on its own;
        # the proof body is retuned by adding `List.map_map` (tactic body only —
        # the obligation header and statement are untouched, no lemma is added
        # and nothing is assumed). Run out-of-band: exit 0.
        "module": _impl_reproved(
            "    let lows := (List.range n).map "
            "(fun (i : Nat) => (i : Rat) * cellPitch n s)\n"
            "    let extents := lows.map (fun (l : Rat) => (l, l + cellSize n s))\n"
            "    return extents",
            "prove_correct axisCellExtents by\n"
            "  loom_solve\n"
            "  simp [axisExtents, List.map_map]"),
        "rationale": (
            "PASS SOURCE = C1 + C2. A CORRECT impl that builds the extent list in "
            "two passes — materialize every low edge, then pair each with its far "
            "edge — rather than emitting both components of each extent in one "
            "pass. The composed map is the same function of the index, so the "
            "cardinality and every extent still match the post-image, and it MUST "
            "verify: if a spec pinned to `axisExtents n s` rejected a faithful "
            "impl merely for traversing the index range in two stages instead of "
            "one, C2 would be over-fitting the TRAVERSAL SHAPE rather than the "
            "value (SPEC-TOO-STRONG). Complements the other two positives on the "
            "one axis they leave uncovered: pos-control-closed-form folds the "
            "post-image `def` and is therefore definitionally the frozen body, "
            "and pos-control-factored-pitch varies the arithmetic inside a "
            "single-pass traversal. Here the list-building structure itself "
            "differs, which is what makes the residual obligation a genuine "
            "map-composition step rather than a reflexivity."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini admiss-grid case, ported with real content: this
    # method DOES carry two `require` clauses, so "a normal grid input is
    # admitted" is not vacuous here. The gold impl body is kept and an in-impl
    # `assert` on a concrete F2P-shaped configuration is prefixed.
    # =====================================================================
    {
        "id": "admiss-f2p-grid",
        "kind": "admissibility",
        "expect": "verify",
        # The asserted configuration is the failing test's own column axis (3
        # cells, gap fraction 1/6): it satisfies P1 (n >= 1) and P2 (s >= 0), and
        # the post-image at that point is a concrete, NON-DEGENERATE separated
        # layout — three cells of size 3/10 at lows 0, 7/20, 7/10, so consecutive
        # cells are strictly separated (3/10 < 7/20) and the axis is exactly
        # filled (last high = 1). That rules out the failure mode where an
        # unsatisfiable or degenerate post-image reads like one every impl meets.
        # The proof body is retuned to close the extra `assert` goal by kernel
        # evaluation; the obligation header and statement are untouched, no lemma
        # is added and nothing is assumed. Run out-of-band: exit 0.
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      ((3 : Nat) ≥ 1 ∧ ((1 : Rat)/6) ≥ 0 ∧\n"
            "       axisExtents 3 (1/6) = [(0, 3/10), (7/20, 13/20), (7/10, 1)]))\n"
            + _IMPL,
            "prove_correct axisCellExtents by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide +kernel\n"
            "    | simp [axisExtents]"),
        "rationale": (
            "PASS SOURCE = P1 + P2 jointly satisfiable at a normal grid input, AND "
            "C2's post-image non-degenerate there. The asserted point is the "
            "failing test's own axis configuration (3 cells, gap fraction 1/6): it "
            "meets both `require` clauses, and the pinned layout at that point is "
            "the concrete separated tiling [(0, 3/10), (7/20, 13/20), (7/10, 1)] — "
            "cells strictly separated (3/10 < 7/20) and the axis exactly filled "
            "(last high = 1). So the precondition is establishable for ordinary "
            "grid inputs and the post-image is a real, satisfiable, "
            "gap-respecting layout rather than a degenerate or contradictory one. "
            "If this cannot verify => PRECOND-TOO-STRONG (or an unsatisfiable "
            "post-image). Ports the nagini admiss-grid case."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input, plus the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    #
    # BINDER COVERAGE. Both input binders are varied by the witnesses:
    #   n:  1, 2, 3, 4          s:  0, 1/6, 1/3, 1/2, 2
    # Seven DISTINCT witness points across seven rivals — (2, 1/2), (3, 1/6),
    # (2, 1/6), (2, 0), (1, 0), (4, 1/3), (2, 2). Rivals sharing a grid size
    # (n = 2) do so at different gap fractions, and the s = 0 point is probed
    # precisely because it is the sub-domain where the even-split reading is
    # CORRECT: a rival refutable there is wrong for a reason independent of the
    # gap factor. The s = 2 point is the OTHER end of the same binder — a gap
    # wider than a cell, which `require s >= 0` admits and nothing bounds above.
    # It was added by the second audit, which found every rival refuted at
    # s <= 1/2 and hence the whole s > 1 band attacked by nothing.
    # =====================================================================
    {
        "id": "reject-even-split",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour (Solution_prepatch.lean's skeleton, the
        # G-DIFF discriminator): the requested gap fraction is dropped on the
        # floor and the axis is split evenly, pitch = size = 1/n, so consecutive
        # cells ABUT. Correct on the whole s = 0 sub-domain, wrong at every
        # positive gap.
        "module": _impl(
            "    let evenSize : Rat := 1 / (n : Rat)\n"
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => ((i : Rat) * evenSize, "
            "(i : Rat) * evenSize + evenSize))\n"
            "    return extents"),
        "refinement": (
            "this IS the pre-change reading: the requested gap fraction never "
            "reaches the placement, so the cells are tiled evenly and abut. Its "
            "faithful real counterpart is the unfixed code path — the layout "
            "positions are simply never recomputed from the requested spacing, "
            "which is exactly the reported defect (the layout is identical "
            "whatever spacing is asked for). The failing test drives a "
            "2-by-3 grid with non-zero spacing on both axes and asserts the "
            "separated coordinates: on the 3-cell axis with gap fraction 1/6 the "
            "second cell must start at 0.35 of the span, whereas the even split "
            "puts it at 1/3. So the assertion fails and the instance is NOT "
            "resolved: a verifying rival here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from C2 (`out = axisExtents n s`). The post-image's low edge "
            "is `i · cellPitch n s`, and the pitch carries the `(1 + s)` factor, "
            "so it exceeds the even step `1/n` for every `s > 0`; the rival's "
            "extents therefore differ from the pinned ones at every index `i > 0` "
            "whenever a gap is requested. Refuted at (n, s) = (2, 1/2), the "
            "smallest grid with a gap large enough to separate: the pinned layout "
            "gives cells of size 2/5 at lows 0 and 3/5, the rival gives size 1/2 "
            "at lows 0 and 1/2. Correct on the whole `s = 0` sub-domain — a "
            "genuine partial-domain break. If it verified => SPEC-TOO-WEAK (the "
            "spec admits the defect it exists to exclude)."
        ),
        "witness": _witness(2, "1/2"),
    },
    {
        "id": "reject-even-split-pinned",
        "kind": "uniqueness",
        "expect": "reject",
        # The SHARPEST partial-domain attack (nagini's weak-hdrop-partial /
        # weak-row-reflect shape): drop the gap factor on EXACTLY the failing
        # test's axis configuration and be correct on every other input. A
        # near-miss that agrees with the pinned layout over strictly more of the
        # domain than reject-even-split, so it gets its OWN witness point — the
        # only input where it is wrong.
        "module": _impl(
            "    let size : Rat := if n = 3 ∧ s = 1/6 then 1 / (n : Rat) "
            "else cellSize n s\n"
            "    let step : Rat := if n = 3 ∧ s = 1/6 then 1 / (n : Rat) "
            "else cellPitch n s\n"
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => ((i : Rat) * step, (i : Rat) * step + size))\n"
            "    return extents"),
        "refinement": (
            "correct on EVERY input except the failing test's own axis "
            "configuration (3 cells, gap fraction 1/6), where it falls back to the "
            "even gap-free tiling. Its faithful real counterpart recomputes the "
            "layout from the requested spacing in general but not for that "
            "configuration, so the test's second column starts at 1/3 of the span "
            "instead of the required 0.35 and its coordinate assertions fail — the "
            "instance is NOT resolved. Partial-domain correctness, and in "
            "particular correctness on every input the test does NOT probe, is not "
            "resolution; this is the case that would expose a spec pinning the "
            "layout only away from the tested configuration."
        ),
        "rationale": (
            "REJECT from C2. C2 is a total function of both binders — it pins the "
            "layout at EVERY `(n, s)` in the precondition's domain, with no "
            "configuration exempted — so a rival correct everywhere but at one "
            "point still contradicts it there. Refuted at (n, s) = (3, 1/6), the "
            "failing test's own column axis and the single input this rival gets "
            "wrong: the pinned layout gives lows 0, 7/20, 7/10 with size 3/10, the "
            "rival gives lows 0, 1/3, 2/3 with size 1/3. This is a NEAR-MISS of "
            "reject-even-split (it agrees with the pinned layout over strictly "
            "more of the domain), so it is refuted at its OWN distinguishing point "
            "rather than sharing that case's witness. Ports the nagini "
            "weak-hdrop-partial / weak-row-reflect pinned-to-the-tested-grid "
            "attack. If it verified => SPEC-TOO-WEAK (domain-incomplete)."
        ),
        "witness": _witness(3, "1/6"),
    },
    {
        "id": "reject-cell-swallows-gap",
        "kind": "uniqueness",
        "expect": "reject",
        # nagini R4 (weak-fatcell-gap): low edges all CORRECT — so the first cell
        # still starts at 0 and the strides are right — but each cell's span is
        # the whole stride instead of the cell size, so every cell overruns into
        # the gap that follows it and consecutive cells touch.
        "module": _impl(
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => ((i : Rat) * cellPitch n s, "
            "(i : Rat) * cellPitch n s + cellPitch n s))\n"
            "    return extents"),
        "refinement": (
            "every low edge is correct and the cardinality is correct; only each "
            "cell's SPAN is inflated to the full stride, so cells overrun the gap "
            "and touch their successor. Its faithful real counterpart takes the "
            "stride where it should take the cell size when computing the far "
            "edge. On the failing test's 3-cell axis with gap fraction 1/6 the "
            "first cell's far edge becomes 0.35 of the span instead of 0.3, so the "
            "asserted upper coordinate is wrong and the instance is NOT resolved. "
            "Note it satisfies the cardinality clause and agrees with the pinned "
            "layout on the whole `s = 0` sub-domain (where stride = size), so only "
            "the span half of the value pin excludes it."
        ),
        "rationale": (
            "REJECT from C2, specifically the SPAN component of the pinned extent "
            "(`high i = low i + cellSize n s`, not `+ cellPitch n s`). Since "
            "`cellPitch = cellSize · (1 + s)` strictly exceeds `cellSize` for "
            "`s > 0`, the rival's `high` is too large at every index (including "
            "`i = 0`, where the low edge is 0 and the lows give the rival no "
            "trouble). It satisfies C1 (`out.length = n`) exactly, which is what "
            "makes it a distinct attack from the two cardinality rivals below: it "
            "isolates the span. Refuted at (n, s) = (2, 1/6) — a gap fraction and "
            "grid size distinct from the other rivals' points: the pinned layout "
            "gives (0, 6/13) and (7/13, 1), the rival gives (0, 7/13) and "
            "(7/13, 14/13), which even leaves the unit axis. If it verified => "
            "SPEC-TOO-WEAK (the span is unpinned)."
        ),
        "witness": _witness(2, "1/6"),
    },
    {
        "id": "reject-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # The ORDER attack. mapping.md §2 records that this axis computation is
        # consumed in BOTH orientations — one axis in the listed order, the other
        # reversed, because the underlying routine indexes that axis from the far
        # end — so a rival that hands back the extents in the wrong order is
        # exactly the confusion the spec must exclude. Every extent VALUE is
        # correct and the cardinality is correct; only the order is wrong, so
        # neither C1 nor the elementwise arithmetic catches it. Note this rival is
        # refutable at s = 0, where the even-split reading is CORRECT: its defect
        # is independent of the gap factor.
        "module": _impl(
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => ((i : Rat) * cellPitch n s, "
            "(i : Rat) * cellPitch n s + cellSize n s))\n"
            "    return extents.reverse"),
        "refinement": (
            "returns exactly the right multiset of extents, the right count, and "
            "the right spacing — but ordered from the far end of the axis instead "
            "of the low end. Its faithful real counterpart consumes the layout "
            "positions of one axis in the opposite orientation to the one the "
            "coordinates are assigned in. On the failing test's 2-cell axis with "
            "non-zero spacing that reflects the grid: the cell the test expects to "
            "occupy the upper band is placed in the lower one, so its asserted "
            "lower and upper coordinates are swapped and the instance is NOT "
            "resolved. Crucially it also breaks on the gap-free sub-domain, so it "
            "is not a variant of the dropped-gap defect."
        ),
        "rationale": (
            "REJECT from C2 as a LIST equality, not merely elementwise: C2 pins "
            "`out` to `axisExtents n s`, whose defining comment fixes the order "
            "(`in order from the low end`, cell `i` at index `i`). The rival's "
            "extents are individually all correct and its length is correct, so "
            "C1 and every per-extent arithmetic property hold — ONLY the order "
            "refutes it, which is why this attack is independent of the two "
            "gap-factor rivals and of the cardinality rivals. Refuted at "
            "(n, s) = (2, 0): the pinned layout is [(0, 1/2), (1/2, 1)], the rival "
            "returns [(1/2, 1), (0, 1/2)]. That point is deliberately in the "
            "`s = 0` sub-domain where the even-split rival is CORRECT, so it "
            "probes a binder value no other witness refutes anything at, and "
            "exercises the ORDER clause with the gap factor collapsed to 1. If it "
            "verified => SPEC-TOO-WEAK (the order is unpinned)."
        ),
        "witness": _witness(2, "0"),
    },
    {
        "id": "reject-offset-by-one-stride",
        "kind": "uniqueness",
        "expect": "reject",
        # nagini R5 (weak-extra-gap): one extra stride baked into every low edge,
        # so the first cell no longer starts at the low end of the axis and the
        # last cell runs off it. Sizes and count are correct.
        "module": _impl(
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => (((i : Rat) + 1) * cellPitch n s, "
            "((i : Rat) + 1) * cellPitch n s + cellSize n s))\n"
            "    return extents"),
        "refinement": (
            "an off-by-one in the stride count: every cell is shifted one whole "
            "stride along the axis, so the first cell does not begin at the low "
            "end and the last overruns the high end. Its faithful real counterpart "
            "indexes the layout positions from one instead of zero. On the failing "
            "test's grid every asserted coordinate shifts — in particular the "
            "first cell's lower coordinate is no longer 0 and the last cell's "
            "upper coordinate exceeds the span — so the assertions fail and the "
            "instance is NOT resolved. A cheap near-miss SUPPORTING case (correct "
            "cell sizes, correct count, correct order, correct stride length) that "
            "isolates the ORIGIN of the layout."
        ),
        "rationale": (
            "REJECT from C2, specifically the low-edge component (`low i = i · "
            "cellPitch n s`, so cell 0 sits at 0). Every span, the order and the "
            "count are correct, so C1 holds and only the origin refutes it. "
            "Refuted at (n, s) = (1, 0) — the DEGENERATE single-cell gap-free "
            "grid, a boundary of the precondition's domain (`n ≥ 1` at equality, "
            "`s ≥ 0` at equality) that no other witness probes: the pinned layout "
            "is the single extent [(0, 1)], the rival returns [(1, 2)], entirely "
            "off the unit axis. Refutable even where every gap factor collapses, "
            "so like reject-reversed-order it is independent of the dropped-gap "
            "defect. If it verified => SPEC-TOO-WEAK (the origin is unpinned)."
        ),
        "witness": _witness(1, "0"),
    },
    {
        "id": "reject-extra-cell",
        "kind": "uniqueness",
        "expect": "reject",
        # The CARDINALITY attack — the only rival aimed at C1 rather than C2.
        # Every extent it emits is at the correct position with the correct span
        # and in the correct order; it simply emits one too many, expanding the
        # index range one past the last cell.
        "module": _impl(
            "    let extents := (List.range (n + 1)).map\n"
            "      (fun (i : Nat) => ((i : Rat) * cellPitch n s, "
            "(i : Rat) * cellPitch n s + cellSize n s))\n"
            "    return extents"),
        "refinement": (
            "emits one extent too many: the index range is expanded one past the "
            "last cell, so a spurious extra band is reported beyond the end of the "
            "axis. Every reported extent is at the correct position with the "
            "correct span and in the correct order. Its faithful real counterpart "
            "walks the layout positions one step past the end, and the extra band "
            "is then paired with a cell that does not exist: on the failing test's "
            "grid the reported placements no longer line up one-to-one with the "
            "cells the test indexes, so the coordinate assertions do not hold and "
            "the instance is NOT resolved."
        ),
        "rationale": (
            "REJECT from C1 (`out.length = n`) — the ONLY rival in this battery "
            "aimed at the cardinality clause rather than the value clause, which "
            "is what makes C1 independently attacked. C1 pins the count to exactly "
            "one extent per cell, so a list of length `n + 1` contradicts it at "
            "EVERY input in the domain; C2 also refutes it (the list equality is "
            "sensitive to length), but C1 alone suffices. Refuted at "
            "(n, s) = (4, 1/3): a grid size and gap fraction distinct from every "
            "other witness point, so both binders are varied here too. The mirror "
            "defect (one extent too FEW) is the same clause with the same "
            "refutation, so it is not shipped as a separate rival. If it verified "
            "=> SPEC-TOO-WEAK (the cardinality is unpinned)."
        ),
        "witness": _witness(4, "1/3"),
    },
    {
        "id": "reject-gap-clamped-at-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by a SECOND independent audit. Every other rival in this battery
        # is refuted at a gap fraction `s <= 1/2`, so the whole `s > 1` band —
        # a gap WIDER than a cell, which the precondition (`s >= 0`) admits and
        # the conformance fuzz exercises — was defended by no rival at all. This
        # one saturates the gap fraction at 1 before laying the axis out, so it
        # agrees with the pinned layout on the entire sub-domain `s <= 1` (which
        # includes all six other witness points, the tested configuration among
        # them) and diverges only once the requested gap exceeds a full cell.
        "module": _impl(
            "    let s' : Rat := if s > 1 then 1 else s\n"
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => ((i : Rat) * cellPitch n s', "
            "(i : Rat) * cellPitch n s' + cellSize n s'))\n"
            "    return extents"),
        "refinement": (
            "a ceiling on the honoured gap fraction: any requested separation "
            "wider than one cell is silently reduced to exactly one cell. Its "
            "faithful real counterpart bounds the requested spacing before "
            "deriving the placement, so every configuration asking for a gap "
            "wider than a cell is laid out too tightly — the cells are too "
            "large and sit too close together, and each reported coordinate "
            "beyond the first is wrong. On such a configuration the asserted "
            "coordinates are those of the unclamped layout, so the assertions "
            "fail and the instance is NOT resolved. Note it honours the gap "
            "exactly on the failing test's own configuration, so it is not a "
            "variant of the dropped-gap defect: it is a rival that resolves the "
            "reported symptom at the tested input while still contradicting the "
            "spec elsewhere in the admitted domain."
        ),
        "rationale": (
            "REJECT from C2. C2 pins the layout at EVERY `(n, s)` the "
            "precondition admits, and `require s >= 0` admits arbitrarily large "
            "gap fractions — nothing bounds `s` above — so a rival that honours "
            "`s` only up to 1 contradicts C2 throughout the band `s > 1`. "
            "Refuted at (n, s) = (2, 2), a gap fraction OUTSIDE the range every "
            "other witness probes (all six sit at `s <= 1/2`): the pinned layout "
            "gives cells of size 1/4 at lows 0 and 3/4, the clamping rival gives "
            "size 1/3 at lows 0 and 2/3. This is the widest-domain near-miss in "
            "the battery — correct on the whole sub-domain `s <= 1`, hence "
            "correct at all six other witness points including the tested "
            "configuration (3, 1/6) — so it is refutable ONLY out here, which is "
            "why it carries its own point. Closes the binder gap the audit "
            "found: without it the `s > 1` half of the gap binder's admitted "
            "range was defended by no rival, and a real implementation that "
            "capped the spacing would have slipped past this battery. If it "
            "verified => SPEC-TOO-WEAK (the gap fraction is pinned only up to 1)."
        ),
        "witness": _witness(2, "2"),
    },

    # =====================================================================
    # SOUNDNESS (second audit) — a correct reshape whose proof is NOT near the
    # frozen one, unlike the three positives above.
    # =====================================================================
    {
        "id": "pos-control-last-cell-snapped",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the LAST cell's far edge is written as the literal `1` (the
        # high end of the unit axis) instead of being computed as
        # `low + cellSize`. Correct — the pinned layout exactly fills the axis,
        # so the final high edge IS 1 — but only for a reason none of the other
        # positives depend on: it needs the normalization identity
        # `(n-1)·pitch + size = 1`, which holds because the denominator
        # `n + s·(n-1)` is non-zero on the whole precondition domain. Added by
        # the second audit: the three existing positives are all closed by
        # `simp`-level rewriting of the post-image, so none of them asks whether
        # the spec accepts an impl that is correct by ARITHMETIC IDENTITY rather
        # than by matching the post-image's shape. Proof retuned in the tactic
        # body only (elided from the spec view); no lemma is added, nothing is
        # assumed. Run out-of-band: exit 0.
        "module": _impl_reproved(
            "    let extents := (List.range n).map\n"
            "      (fun (i : Nat) => ((i : Rat) * cellPitch n s,\n"
            "        if i + 1 = n then 1 else (i : Rat) * cellPitch n s "
            "+ cellSize n s))\n"
            "    return extents",
            "prove_correct axisCellExtents by\n"
            "  loom_solve\n"
            "  simp [axisExtents, cellPitch, cellSize]\n"
            "  intro a ha hlast\n"
            "  have hden : (n:Rat) + s * ((n:Rat) - 1) ≠ 0 := by\n"
            "    have h1 : (1:Rat) ≤ (n:Rat) := by exact_mod_cast require_2\n"
            "    have h2 : (0:Rat) ≤ s * ((n:Rat) - 1) :=\n"
            "      Rat.mul_nonneg require_1 (by grind)\n"
            "    grind\n"
            "  have han : (a:Rat) = (n:Rat) - 1 := by\n"
            "    have h : a = n - 1 := by omega\n"
            "    subst h\n"
            "    cases n with\n"
            "    | zero => omega\n"
            "    | succ k => push_cast; grind\n"
            "  rw [han]\n"
            "  grind"),
        "rationale": (
            "PASS SOURCE = C1 + C2. A CORRECT impl that reports the final cell's "
            "far edge as the literal high end of the axis (`1`) instead of "
            "recomputing it as `low + cellSize`. The two agree because the "
            "pinned layout exactly TILES the unit axis: the last low edge is "
            "`(n-1)·cellPitch n s` and adding one `cellSize n s` lands on 1, "
            "since `(n-1)·(1+s) + 1 = n + s·(n-1)` is precisely the denominator "
            "both helpers divide by — and that denominator is non-zero "
            "everywhere the precondition holds (`n >= 1` gives `(n:Rat) >= 1` "
            "and `s >= 0` makes `s·(n-1)` non-negative). So every extent and the "
            "cardinality still match the post-image and this MUST verify; if it "
            "cannot, C2 over-fits the arithmetic ROUTE by which each edge is "
            "reached rather than the value it takes (SPEC-TOO-STRONG). Covers "
            "the axis the other three positives leave open: each of those is "
            "closed by rewriting the post-image, whereas this one is correct "
            "only via the normalization identity, so its residual obligation is "
            "a genuine arithmetic fact about the precondition's domain rather "
            "than a shape match. It also exercises the last-cell boundary of the "
            "index range, which no other positive distinguishes."
        ),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
#   nagini case                -> here                            disposition
#   -------------------------------------------------------------------------
#   pos-helpers                -> pos-control-closed-form         PORTED
#   pos-factored               -> pos-control-factored-pitch      PORTED
#   (no sibling)               -> pos-control-two-pass            NEW (audit)
#   admiss-grid                -> admiss-f2p-grid                 PORTED
#   weak-gapless-prepatch      -> reject-even-split               PORTED (central)
#   weak-hdrop-partial         -> reject-even-split-pinned        PORTED (merged)
#   weak-row-reflect           -> reject-even-split-pinned        PORTED (merged)
#                                 + reject-reversed-order         RE-EXPRESSED
#   weak-fatcell-gap           -> reject-cell-swallows-gap        PORTED
#   weak-extra-gap             -> reject-offset-by-one-stride     PORTED
#   FRAME-MUTATION (declared   -> (none)                          VACUOUS x2
#     N/A by nagini too)
#   UNGROUNDED-ORACLE ECHO     -> (folded into the positives)     N/A (grounded)
#   CONTROL-FLOW-EFFECT        -> (none)                          N/A
#   (no sibling)               -> reject-extra-cell               NEW (C1)
#   (no sibling)               -> reject-gap-clamped-at-one       NEW (audit 2)
#   (no sibling)               -> pos-control-last-cell-snapped   NEW (audit 2)
#   (no sibling)               -> (divergence)              SPEC-CLOSED (witness)
#   AXIOM_TESTS                -> (none)                          out of lane
#
# 12 velvet SPEC cases: 4 soundness, 1 admissibility, 7 uniqueness.
#
# NEW x2 (second independent audit). Both close gaps the first audit left.
#   reject-gap-clamped-at-one — BINDER-RANGE gap. Every one of the six rivals
#     was refuted at a gap fraction s <= 1/2, so the band s > 1 (a gap WIDER than
#     a cell) was inside the precondition's admitted domain, exercised by the
#     conformance fuzz, and attacked by nothing. A rival that saturates the
#     honoured gap at 1 is correct on the whole sub-domain s <= 1 — including all
#     six existing witness points and the tested configuration — so it is the
#     widest-domain near-miss here and is refutable only out past s = 1. Verified:
#     the impl fails to build, and its witness at (2, 2) elaborates against the
#     rival (exit 0) while failing against gold with the semantic `not
#     definitionally equal to false` verdict (exit 1) and no stuck reduction.
#   pos-control-last-cell-snapped — SOUNDNESS gap. The three existing positives
#     are each closed by simp-level rewriting of the post-image, so all three are
#     correct by SHAPE. None asks whether the spec accepts an impl correct by
#     ARITHMETIC IDENTITY. Writing the last cell's far edge as the literal `1`
#     is such an impl: it is right only because the pinned layout exactly tiles
#     the axis, i.e. (n-1)(1+s) + 1 = n + s(n-1), and discharging it needs the
#     denominator to be non-zero on the precondition's domain. Verified exit 0.
#     It also exercises the last-cell boundary of the index range, which no other
#     positive distinguishes.
#
# NEW (pos-control-two-pass). Added by the independent AUDIT of this battery. The
#   two ported positives leave one axis of reshaping uncovered: closed-form is the
#   frozen body with `axisExtents` FOLDED, hence definitionally equal to it (the
#   frozen proof body closes it with no retuning at all), and factored-pitch
#   varies the stride ARITHMETIC while keeping the single-pass
#   `(List.range n).map` traversal. Neither one asks whether the spec tolerates a
#   different list-BUILDING structure. The two-pass reshape does, and its residual
#   goal is a real map-composition step (`List.map_map`) rather than a
#   reflexivity, so it is the only positive whose passing is not close to
#   automatic. Verified exit 0.
#
# MERGED (weak-hdrop-partial + weak-row-reflect -> reject-even-split-pinned).
#   The nagini sibling models FOUR extents of a two-dimensional cell rectangle
#   (left/right/bottom/top) in ONE function, so it can attack the column axis and
#   the row axis as separate rivals: a horizontal-only gap drop, and a rows-
#   counted-from-the-far-end reflection. This bundle models ONE axis
#   (`axisCellExtents n s`), consumed for both orientations per mapping.md §2, so
#   "the column axis is wrong" and "the row axis is wrong" are the SAME modeled
#   behaviour at different binder values — one rival, not two. Both nagini cases
#   share the shape "wrong on exactly the tested grid, correct elsewhere", which
#   is what reject-even-split-pinned ports, at the tested column configuration
#   (3, 1/6). Carrier narrowing, not a dropped attack.
# RE-EXPRESSED (weak-row-reflect -> reject-reversed-order). The reflection half of
#   the nagini row rival does have content this carrier keeps, and it is NOT the
#   gap factor: mapping.md §2 records that this single axis computation is
#   consumed in both orientations (one axis reversed, because the underlying
#   routine indexes it from the far end), so getting the ORDER wrong is a real
#   confusion the spec must exclude. Shipped as its own rival because it is
#   refutable where every gap factor collapses (s = 0), i.e. its defect is
#   independent of the dropped-gap defect, and because it is the only rival whose
#   extents are all individually correct.
# NEW (reject-extra-cell). No nagini sibling: nagini's function returns a single
#   rectangle, so there is no cardinality to get wrong. This bundle returns a
#   LIST, and C1 (`out.length = n`) is a second independent top-level clause that
#   would otherwise be attacked by no rival at all — the port would then defend a
#   clause it never tested. Added so every independent clause is attacked.
# VACUOUS x2 (frame-mutation). The nagini sibling itself declares this class N/A
#   (its args are scalars passed by value with no read-only reference parameter,
#   and the result is freshly constructed), and on this carrier it is vacuous a
#   second time over: Velvet is referentially transparent, `n` and `s` are
#   immutable non-`mut` values, and there is no heap, aliasing or permission
#   system, so there is no read-only input a rival could overwrite. No substitute
#   probe fabricated.
# N/A (ungrounded-oracle echo). As on nagini, not applicable as a WRONG echo: the
#   post-image is grounded in the two arguments — `cellSize`, `cellPitch`,
#   `axisExtents` are transparent computable `def`s and the `axioms` region is
#   EMPTY, so there is no opaque answer key to echo and computing `axisExtents n
#   s` IS doing the modeled work. Carried over as the honest cheapest-impl
#   positive control (pos-control-closed-form) exactly as nagini does, not as a
#   rival.
# N/A (control-flow-effect). The value abstraction pins the entire output: the
#   cardinality (C1) and every extent (C2). There is no exception, side effect or
#   control-flow channel invisible to the spec.
# AXIOM_TESTS. The nagini sibling ships one A-reference axiom case (re-running the
#   real grid-position routine in Docker against the closed-form model). DROPPED:
#   the axiom lane is G-AX's job (this bundle's `axiom_check.py` carries it) and
#   this gate ignores AXIOM_TESTS. Not a battery gap.
#
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
#
# CLAUSE / BINDER / POINT COVERAGE (what replaces case-count parity).
#   OBLIGATION. The sole obligation (`prove_correct axisCellExtents`) is DEFENDED
#     by 5 positives (pos-control-closed-form, pos-control-factored-pitch,
#     pos-control-two-pass, pos-control-last-cell-snapped, admiss-f2p-grid) and
#     ATTACKED by 7 rivals.
#   CLAUSES. Both independent top-level clauses are attacked:
#     C1 (`out.length = n`)          -> reject-extra-cell
#     C2 (`out = axisExtents n s`)   -> the other six, on five INDEPENDENT
#        failure modes: the gap factor in the stride (reject-even-split,
#        reject-even-split-pinned), the SPAN (reject-cell-swallows-gap), the
#        ORDER (reject-reversed-order), the ORIGIN
#        (reject-offset-by-one-stride), and the GAP RANGE above one cell
#        (reject-gap-clamped-at-one).
#   BINDERS. Neither input binder is held fixed by the witnesses:
#     n varies over 1, 2, 3, 4;  s varies over 0, 1/6, 1/3, 1/2, 2.
#     In particular `s` is probed at 0 — the sub-domain where the dropped-gap
#     reading is CORRECT — by two rivals (reject-reversed-order,
#     reject-offset-by-one-stride) whose defects are therefore independent of the
#     gap factor, and `n` is probed at its precondition boundary `n = 1`. That is
#     the failure mode the guidance calls out (a binder every witness holds at one
#     value is a binder no rival was built to abuse): a rival that mishandled only
#     the gap-free case, or only the single-cell case, would NOT slip past this
#     battery.
#   POINTS. Seven distinct witness inputs — (2, 1/2), (3, 1/6), (2, 1/6), (2, 0),
#     (1, 0), (4, 1/3), (2, 2) — so pts=7 across 7 rivals, one per rival and no
#     two rivals refuted at the same point. The one repeated binder value
#     (n = 2, at three different gap fractions) is deliberate: (2, 1/2) separates
#     widely, (2, 1/6) is the tested gap fraction, (2, 0) collapses the gap
#     entirely. The two rivals that both drop the gap factor do NOT share a
#     witness: reject-even-split-pinned is a NEAR-MISS that agrees with the pinned
#     layout over strictly more of the domain, so it is refuted at the one input
#     it gets wrong, the tested configuration (3, 1/6) — otherwise its rationale
#     would claim a sub-domain the manifest never demonstrates.
#
# WITNESS MECHANICS (all seven re-checked with scripts/lean_verify.sh; the second
#   audit independently rebuilt every one from the gate's own `witness_file`
#   construction and additionally ran the FLIPPED claim on each side — 28 builds).
#   Each witness derives Velvet's tester for the method and asserts
#   `axisCellExtentsTester n s = false` at one concrete input, closed by
#   `with_unfolding_all rfl`. Per point, three builds:
#     `= false` vs RIVAL  -> exit 0;  `= false` vs GOLD -> exit 1 with a real
#     verdict (not definitionally equal to `false`) and NO stuck-reduction text;
#     `= true`  vs GOLD  -> exit 0.
#   The third build is what licenses reading the second: gold's failure is "the
#   frozen impl SATISFIES the contract here", not "the tactic could not evaluate".
#   CLOSER HISTORY — recorded because the failure mode was invisible in the exit
#   codes. The previous revision closed with `decide +kernel`. That does close
#   each rival and gold does exit 1, so the two-build check LOOKS satisfied; but
#   gold's exit 1 is `Reduction got stuck at the Decidable instance ... did not
#   reduce to isTrue or isFalse` — the frozen side decided nothing, so the exit
#   code attested to a refutation that was never performed. The gate flagged all
#   six as `witness-undecided` => MALFORMED-TESTS, and the gate was RIGHT: the
#   rivals are genuinely refuted, but that battery did not demonstrate it. Bare
#   `decide` is dead for the same underlying reason (the spec_guide `Rat` trap,
#   stuck at `instDecidableEqBool (axisCellExtentsTester 2 (1 / 2)) false`); plain
#   `rfl` fails on both sides; `simp` reports `made no progress`.
#   `with_unfolding_all rfl` unfolds through the tester so both sides return a
#   verdict. Not the banned `native_decide` — which, being compiler-trusted,
#   would make the witness elaborate against gold too and defeat both halves at
#   once. No banned token appears in any witness.
#   No witness binds a hypothesis (both binders are exact and computable, so
#   nothing needs conditioning on an opaque term), hence the gate's
#   witness-consistency probe is a no-op on all seven and no witness can be a
#   contradiction-powered forgery. The second audit checked the stronger property
#   directly with the flipped-claim builds above: gold's exit code changes when
#   the claim changes, so it is evidence about the claim and not about tooling.
#
# NOTHING WAS ASSUMED. No case adds an `axiom`, `sorry`, `admit`,
#   `native_decide`, or any `theorem`/`lemma` beyond the frozen set; every case
#   edits only the impl region and (for two positives and the admissibility case)
#   the `prove_correct` tactic body, both elided from the consumer spec view. The
#   obligation header and statement are byte-identical in all twelve variants. No
#   soundness positive was dropped for an unprovable proof: both reshapes were
#   chosen to keep the residual goal cheap (a distributivity step closed by
#   `grind`; note `ring` is not a known tactic in this workspace) and both were
#   run to exit 0 before shipping.
AXIOM_TESTS = []
