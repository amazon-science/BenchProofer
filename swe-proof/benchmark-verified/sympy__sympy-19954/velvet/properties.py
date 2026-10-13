"""properties.py — G-PBT falsification battery for sympy__sympy-19954 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct pruneParallelSystems`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); the
sibling's per-case adversarial argument is carried over and re-expressed against
this backend's carrier. Case-count parity is NOT the target — the Lean-family
bundle models only the purely-functional core (one contracted ``method``), so
nagini cases attached to nagini-only machinery (fractional heap permissions)
have no counterpart. The nagini->velvet accounting block at the bottom records
exactly which sibling cases ported, which were omitted, and why.

DEFENDED SURFACE. One contracted method over four input binders:

  pruneParallelSystems (listA listB listC : List Int) (removeFlags : List Bool)
                       return (out : (List Int) × (List Int) × (List Int))
    require listA.length = listB.length
    require listB.length = listC.length
    require listC.length = removeFlags.length
    ensures out.1   = keepByMask listA removeFlags          -- (C1) load-bearing
    ensures out.2.1 = keepByMask listB removeFlags          -- (C2) load-bearing
    ensures out.2.2 = keepByMask listC removeFlags          -- (C3) load-bearing
    ensures out.1.length   = out.2.1.length                 -- (C4) alignment
    ensures out.2.1.length = out.2.2.length                 -- (C5) alignment

The method prunes THREE index-aligned parallel lists by ONE shared per-position
removal mask, so the survivors keep their mutual correspondence. ``keepByMask``
and ``numKept`` are fully-unfolded ``def``s in the ``pure`` region — total
functions of (a list, the mask), with no opaque answer key to echo. C1/C2/C3
each pin one output list to the SAME-mask filter of its own input; C4/C5 pin the
three results to equal length (the alignment consequence — a mask-driven
positional filter of equal-length inputs yields equal-length outputs).

WHICH CLAUSES CONSTRAIN THE IMPL. C1, C2, C3 are the three impl-constraining
clauses; each is a total function of (its input list, the shared ``removeFlags``)
and pins every per-position keep/drop decision. C4/C5 are their length
consequence. Every uniqueness rival below abuses one or more of C1/C2/C3 —
either dropping the mask on a list, applying the WRONG mask to a list, or
desynchronising the three lists so they no longer share one consistent snapshot.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this class
    as MANDATORY because the four inputs hold fractional heap permissions
    (``Acc(list_pred(x), 1/2)``) an impl can illegally overwrite (append /
    index-store). Lean and Velvet are referentially transparent: ``listA``,
    ``listB``, ``listC`` and ``removeFlags`` are immutable values, none is
    declared ``mut``, there is no heap and no aliasing — so there is no read-only
    input to mutate and no substitute probe to build. The two nagini frame-mut
    rivals (frame-mutate-append-blocks, frame-mutate-store-flag) are NOT ported
    and NOT replaced (per the porting map this class is vacuous here).
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
    REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
    rather than faking it is refused even earlier, by the elaborator's own
    check (``Decreasing annotations are required in total correctness
    semantics``). So divergence neither applies to this impl nor discharges the
    ``ensures`` clauses vacuously if a rival introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class. C1/C2/C3 are pinned to a
    total, fully-unfolded function of the method's own inputs (``keepByMask`` is a
    concrete ``def``; the ``axioms`` region is empty), so there is no answer key
    to echo. Any WRONG value fails C1/C2/C3 — demonstrated by every reject rival.
    Covered instead by the pos-direct-inline positive (returning the three
    ``keepByMask`` filters directly is a correct grounded impl, not an echo).
  * PARTIAL-DOMAIN / DESYNC / VALUE rivals — APPLY: the nagini uniqueness value
    rivals port onto C1/C2/C3, each diverging from gold on the exact sub-domain
    its abused clause governs.

WITNESS MECHANICS ON THIS BUNDLE. The spec is a ``method`` CONTRACT, not a bare
predicate, so a witness reaches it through Velvet's own tester machinery:
``pruneParallelSystemsTester listA listB listC removeFlags = false`` says the
extracted program's result violates the method's postcondition at that concrete
input. Checked in a file whose ``prove_correct`` block has been stripped, so no
tactic script can mask the verdict. Every carrier here is TRANSPARENT and
COMPUTABLE (``keepByMask`` on concrete ``List Int``/``List Bool`` literals), so
``decide`` fully reduces the tester at each probed input: it ELABORATES against a
wrong rival (the rival's output ≠ the required filter, so the tester is
``false``) and FAILS against the frozen solution (gold satisfies every clause, so
the tester is ``true`` and ``decide`` proves the ``= false`` goal FALSE — a
genuine failure on gold). Note this bundle's frozen impl is STRAIGHT-LINE (three
``keepByMask`` binds, no loop), so — unlike the looped siblings — gold's
extracted program reduces too; the discrimination comes from the VALUE, not from
gold's ``Exec`` staying stuck. Every witness input satisfies the three length
``require`` clauses (equal-length lists, mask length = list length), so it
reaches the postcondition and no case passes vacuously on an excluded input.
Every witness binds NO hypothesis (all literals), so no consistency probe is
needed. No banned token (sorry/admit/native_decide/axiom/opaque). Each witness
was checked out-of-band with scripts/lean_verify.sh: rival build EXIT 0, gold
build EXIT 1 — and, re-derived independently by the audit, every gold-side
failure is the SEMANTIC form "Tactic `decide` proved that the proposition
pruneParallelSystemsTester ... = false is false", i.e. the kernel reduced the
tester to `true` and refuted the claim. No gold-side failure is a stuck
reduction, a missing identifier, a type error or a timeout, so no rejection here
rests on a tactic mismatch.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the prune is modeled
DEEPLY by ``keepByMask``/``numKept`` — see mapping.md §3). There is no
axiom-soundness/containment obligation to probe here, and the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19954"
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

# The WHOLE executable body of the method: the three same-mask filters and the
# returned triple.
_IMPL = (
    "    -- Every list is filtered by the SAME per-position flags, so survivors keep\n"
    "    -- their positional correspondence across all three lists.\n"
    "    let keptA := keepByMask listA removeFlags\n"
    "    let keptB := keepByMask listB removeFlags\n"
    "    let keptC := keepByMask listC removeFlags\n"
    "    return (keptA, keptB, keptC)"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. Every carrier is transparent, so
# ---- `decide` reduces the tester at the concrete (require-satisfying) input.
_TESTER = (
    "extract_program_for pruneParallelSystems\n"
    "prove_precondition_decidable_for pruneParallelSystems\n"
    "prove_postcondition_decidable_for pruneParallelSystems\n"
    "derive_tester_for pruneParallelSystems\n\n"
)


def _witness(args: str) -> str:
    return (
        _TESTER
        + f"example : pruneParallelSystemsTester {args} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify (frozen proof unchanged). If a faithful correct impl
    # cannot verify, the spec is over-fit to the impl SHAPE => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the three filters DIRECTLY in the returned triple, with
        # no intermediate `let` bindings. C1/C2/C3 are literally
        # `out.k = keepByMask list_k removeFlags`, and `keepByMask` is GROUNDED in
        # the inputs (a total fold, no opaque answer key), so this is the honest
        # cheapest CORRECT impl — and doubles as proof the spec is not
        # echo-vulnerable (any wrong per-position map fails C1/C2/C3). The frozen
        # proof still closes (verified out-of-band: exit 0).
        "module": _with_impl(
            "    return (keepByMask listA removeFlags,\n"
            "            keepByMask listB removeFlags,\n"
            "            keepByMask listC removeFlags)"),
        "rationale": "clauses C1/C2/C3 are `out.k = keepByMask list_k removeFlags`, "
                     "pinned to a total grounded function of the inputs, so directly "
                     "returning the three filters (no intermediate locals) is the "
                     "honest cheapest CORRECT impl. Ports the nagini "
                     "echo/positive-control argument (the grounded pin is satisfiable "
                     "only by the real per-position filter; no wrong echo verifies). "
                     "Must verify, else the postcondition is over-fit to the "
                     "let-binding shape => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reorder-lets",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the three `let` binds but in REVERSED order (C, B, A) —
        # the returned triple is unchanged and each output is still its own
        # same-mask filter. Only the executable order of the (side-effect-free)
        # binds differs. The frozen proof closes unchanged (verified: exit 0). If
        # it fails the spec is over-fit to the exact bind order => SPEC-TOO-STRONG.
        "module": _with_impl(
            "    let keptC := keepByMask listC removeFlags\n"
            "    let keptB := keepByMask listB removeFlags\n"
            "    let keptA := keepByMask listA removeFlags\n"
            "    return (keptA, keptB, keptC)"),
        "rationale": "a correct impl with a DIFFERENT executable shape: the three "
                     "side-effect-free filter binds are reordered (C, B, A) while the "
                     "returned triple and each output's same-mask filter are unchanged. "
                     "Ports the nagini pos-control-branch-reorder / local-reshape "
                     "argument. Must verify (frozen proof closes), else the "
                     "postcondition is over-fit to the bind order => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling self-calls on an F2P-shaped input (four
    # equal-length parallel lists, the n==0 boundary) to show the precondition
    # ADMITS the modeled behaviour. This bundle's precondition is the three
    # length-equality `require` clauses; the frozen impl discharging all five
    # `ensures` over that required domain is the admissibility witness that the
    # post-image (the three same-mask filters plus the two alignment clauses) is
    # jointly SATISFIABLE by a gold-shaped computation. MUST verify, else
    # SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": "the frozen impl discharging all five ensures over the "
                     "require-constrained domain (three equal-length lists, mask "
                     "length = list length) is the admissibility witness that the "
                     "post-image (C1/C2/C3 plus the C4/C5 alignment clauses) is "
                     "jointly satisfiable. Re-aimed from the nagini "
                     "admiss-selfcall-empty-parallel, whose fractional-permission "
                     "half has no counterpart on this referentially-transparent "
                     "carrier; the equal-length precondition IS carried (a mismatched "
                     "input is excluded by `require`). Else SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete (require-satisfying) input and the refinement argument for why its
    # faithful real counterpart would NOT resolve the F2P. Every witness input
    # satisfies the three length requires, so it reaches the postcondition.
    # =====================================================================
    {
        "id": "prepatch-desync-AB",
        "kind": "uniqueness",
        "expect": "reject",
        # THE headline rival — the exact issue. listC is pruned correctly by the
        # shared mask, but listA/listB are left UNPRUNED, so on any input with a
        # flagged position the three lists DESYNC (listA/listB keep a position the
        # mask removed). This is the pre-patch behaviour where the two lists were
        # mutated in place while the scan ran and a second removal misfired.
        "module": _with_impl(
            "    let keptA := listA\n"
            "    let keptB := listB\n"
            "    let keptC := keepByMask listC removeFlags\n"
            "    return (keptA, keptB, keptC)"),
        "refinement": "this IS the issue: prune the representative list correctly by "
                      "the shared mask but leave the two index-aligned companion lists "
                      "UNPRUNED (the pre-patch in-place removal desync, where a second "
                      "removal landed on a shifted index — the reported crash / wrong "
                      "position). On the F2P input two or more positions are flagged, so "
                      "the companion lists keep non-minimal systems the mask removed and "
                      "desync from the pruned list — definitively non-resolving.",
        "rationale": "REJECT from C1/C2 (`out.1 = keepByMask listA removeFlags`, "
                     "`out.2.1 = keepByMask listB removeFlags`): on a flagged position "
                     "the rival returns the unfiltered listA/listB, which differ from "
                     "the shared-mask filter. Of the two alignment clauses only C5 "
                     "(`out.2.1.length = out.2.2.length`) breaks — the unpruned listB "
                     "is longer than the filtered listC — while C4 "
                     "(`out.1.length = out.2.1.length`) still HOLDS, since listA and "
                     "listB are left unpruned together and stay equal-length. C1/C2 are "
                     "therefore the load-bearing rejection source here. Refuted at "
                     "[1,2] [3,4] [5,6] [false,true] where gold drops position 1 from "
                     "all three (→ ([1],[3],[5])) but the rival returns the full "
                     "listA/listB (→ ([1,2],[3,4],[5])). If it verified => "
                     "SPEC-TOO-WEAK (admits the bug).",
        "witness": _witness("[1,2] [3,4] [5,6] [false,true]"),
    },
    {
        "id": "wrong-mask-B-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # listB is filtered by the COMPLEMENT of the shared mask (keep when
        # flagged) while listA/listC use the correct mask. A near-miss desync:
        # correct on the all-equal-flag sub-domains, wrong the moment a mixed mask
        # appears — listB no longer parallels the surviving listA/listC.
        "module": _with_impl(
            "    let keptA := keepByMask listA removeFlags\n"
            "    let keptB := keepByMask listB (removeFlags.map (fun b => !b))\n"
            "    let keptC := keepByMask listC removeFlags\n"
            "    return (keptA, keptB, keptC)"),
        "refinement": "applies a DIFFERENT (inverted) mask to the middle companion "
                      "list than to the other two — the k-th surviving entry of the "
                      "middle list no longer matches the k-th surviving entry of the "
                      "others, so the parallel-list bookkeeping is corrupt and the "
                      "downstream order check fails — non-resolving.",
        "rationale": "REJECT from C2 (`out.2.1 = keepByMask listB removeFlags`), which "
                     "is the SOLE violated clause at the probed point: the rival keeps "
                     "listB's flagged positions and drops its surviving ones (the "
                     "complement filter), contradicting the shared-mask filter. The "
                     "alignment clauses C4/C5 do NOT break here and are not the "
                     "rejection source — they break only when the mask's true-count "
                     "differs from its false-count (numKept m ≠ numKept (¬m)), which the "
                     "probed [true,false] is not; so this case isolates C2 as a pure "
                     "CONTENT violation with alignment intact. Refuted at "
                     "[1,2] [3,4] [5,6] [true,false] — a DISTINCT point from the "
                     "headline (mask [true,false] vs [false,true]), varying the "
                     "removeFlags binder — where gold keeps position 1 (→ "
                     "(...,[4],...)) but the rival keeps position 0 (→ (...,[3],...)). "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("[1,2] [3,4] [5,6] [true,false]"),
    },
    {
        "id": "partial-keep-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the mask entirely: return all three inputs unpruned. Correct on
        # the no-flag sub-domain, wrong the moment any position is flagged.
        "module": _with_impl("    return (listA, listB, listC)"),
        "refinement": "never applies the mask (leaves all three lists unpruned) — a "
                      "real patch of this shape carries every non-minimal system "
                      "forward, so the downstream computation over-counts and the F2P "
                      "order assertion fails. Correct only on the no-flag sub-domain.",
        "rationale": "REJECT from C1/C2/C3: on any input with a flagged position the "
                     "outputs keep the full inputs but each keepByMask filter drops the "
                     "flagged positions, so out.k ≠ keepByMask list_k removeFlags. "
                     "Refuted at [1] [2] [3] [true] — a single all-flagged position, a "
                     "DISTINCT point (length-1, all-true mask) — where gold returns "
                     "([],[],[]) but the rival returns ([1],[2],[3]). If it verified "
                     "=> SPEC-TOO-WEAK (domain-incomplete).",
        "witness": _witness("[1] [2] [3] [true]"),
    },
    {
        "id": "partial-drop-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-prune: return three empty lists regardless of the mask. Correct on
        # the all-flag sub-domain (every position removed), wrong as soon as any
        # position survives.
        "module": _with_impl(
            "    return (([] : List Int), ([] : List Int), ([] : List Int))"),
        "refinement": "over-prunes (removes surviving positions too) — a real patch of "
                      "this shape discards minimal systems that must remain, again "
                      "giving the downstream computation the wrong order and failing the "
                      "F2P. Correct only on the all-flag sub-domain.",
        "rationale": "REJECT from C1/C2/C3: the outputs are always empty, but keepByMask "
                     "keeps the UN-flagged positions, so on any input with a surviving "
                     "position out.k ≠ keepByMask list_k removeFlags. Refuted at "
                     "[1] [2] [3] [false] — a single surviving position, a DISTINCT "
                     "point (length-1, all-false mask) — where gold returns "
                     "([1],[2],[3]) but the rival returns ([],[],[]). If it verified "
                     "=> SPEC-TOO-WEAK (domain-incomplete).",
        "witness": _witness("[1] [2] [3] [false]"),
    },
    {
        "id": "desync-C-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of the headline: listA/listB are pruned correctly, but listC is
        # left UNPRUNED. A near-miss that proves the THIRD list is independently
        # pinned — a rival that gets C1/C2 right but rides listC along unfiltered
        # is still rejected (so no binder is left to a rival's discretion).
        "module": _with_impl(
            "    let keptA := keepByMask listA removeFlags\n"
            "    let keptB := keepByMask listB removeFlags\n"
            "    let keptC := listC\n"
            "    return (keptA, keptB, keptC)"),
        "refinement": "prunes the two companion lists correctly but leaves the third "
                      "(representative) list UNPRUNED — the pre-patch pruned that list "
                      "separately/value-based, so a faithful patch of this shape "
                      "desyncs it from the other two and the downstream order check "
                      "fails — non-resolving.",
        "rationale": "REJECT from C3 (`out.2.2 = keepByMask listC removeFlags`): on a "
                     "flagged position the rival returns the unfiltered listC, which "
                     "differs from the shared-mask filter; the alignment clause C5 "
                     "`out.2.1.length = out.2.2.length` also breaks (the unpruned listC "
                     "is longer than the filtered listB), while C4 holds (listA/listB "
                     "are both filtered correctly). Refuted at "
                     "[7,8] [9,10] [11,12] [true,false] — a DISTINCT point "
                     "with distinct listC values — where gold drops position 0 from "
                     "listC (→ (...,...,[12])) but the rival returns the full listC "
                     "(→ (...,...,[11,12])). Attacks C3 as the SOLE violated content "
                     "clause, so listC is shown independently load-bearing. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness("[7,8] [9,10] [11,12] [true,false]"),
    },
    {
        "id": "desync-A-only",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT to close a real coverage gap. Before this case NO rival
        # violated C1 alone: prepatch-desync-AB breaks C1 AND C2 together (listA and
        # listB ride along unpruned as a pair), and partial-keep-all /
        # partial-drop-all break all three at once. So the claim that "each of
        # C1/C2/C3 is the SOLE violated content clause of some rival" held for C2
        # (wrong-mask-B-inverted) and C3 (desync-C-only) but NOT for C1. Here listB
        # and listC are pruned correctly and ONLY listA rides along unfiltered, so C1
        # is the sole violated CONTENT clause and listA is shown independently
        # load-bearing.
        "module": _with_impl(
            "    let keptA := listA\n"
            "    let keptB := keepByMask listB removeFlags\n"
            "    let keptC := keepByMask listC removeFlags\n"
            "    return (keptA, keptB, keptC)"),
        "refinement": "prunes the two companion lists correctly but leaves the FIRST "
                      "list unpruned — a faithful patch of this shape desyncs that list "
                      "from the other two, so the k-th surviving entry no longer "
                      "corresponds across the three lists and the downstream order check "
                      "fails — non-resolving.",
        "rationale": "REJECT from C1 (`out.1 = keepByMask listA removeFlags`), the SOLE "
                     "violated content clause: on a flagged position the rival returns "
                     "the unfiltered listA. The alignment clause C4 "
                     "`out.1.length = out.2.1.length` also breaks (unpruned listA is "
                     "longer than the filtered listB) while C5 holds. Refuted at "
                     "[4,5] [6,7] [8,9] [false,true] — a DISTINCT point from all four "
                     "other rivals (distinct listA/listB/listC values) — where gold "
                     "drops position 1 from every list (→ ([4],[6],[8])) but the rival "
                     "returns the full listA (→ ([4,5],[6],[8])). Rebuilt out-of-band by "
                     "the audit: rival EXIT 0, gold EXIT 1 with `decide` reducing the "
                     "tester and proving the `= false` goal FALSE (a semantic "
                     "refutation, not a stuck reduction). If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness("[4,5] [6,7] [8,9] [false,true]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives + 1 admissibility + 2 frame-mutation rivals + 4 uniqueness/desync
# value rivals) and an empty AXIOM_TESTS. This velvet bundle models the SAME
# single behaviour (the shared-mask prune of three parallel lists), narrowed to
# its purely-functional core over `List Int` × `List Bool`, so the port drops the
# fractional-permission machinery and re-expresses the value rivals onto C1/C2/C3.
#
#   nagini case                 -> here
#   ------------------------------------------------------------------------
#   pos-control-branch-reorder  -> pos-reorder-lets              PORTED (re-shaped)
#   pos-control-local-reshape   -> pos-direct-inline             PORTED (re-shaped)
#   admiss-selfcall-empty-parallel -> admiss-gold-total          PORTED (re-aimed)
#   frame-mutate-append-blocks  -> (none)                        VACUOUS class
#   frame-mutate-store-flag     -> (none)                        VACUOUS class
#   prepatch-desync-blocks-nums -> prepatch-desync-AB            PORTED (headline)
#   wrong-mask-nums-inverted    -> wrong-mask-B-inverted         PORTED
#   partial-keep-all            -> partial-keep-all              PORTED
#   partial-drop-all            -> partial-drop-all              PORTED
#   (no sibling)                -> desync-C-only                 ADDED
#   (no sibling)                -> desync-A-only                 ADDED (audit)
#   AXIOM_TESTS (empty)         -> (dropped)                     AXIOM LANE
#
# 9 velvet SPEC cases: 2 soundness, 1 admissibility, 6 uniqueness.
#
# PORTED (positives): the nagini file carries two positives over the same backward
#   front-prepend fold — one that REORDERS the removal-decision branch arms, one
#   that stages the per-step heads into typed locals before prepending. On this
#   carrier the per-position filter is the pure `keepByMask` function (there is no
#   inline branch in the impl to reorder), so both re-express as executable-shape
#   reshapes of the straight-line body: pos-direct-inline inlines the three filters
#   into the returned triple (the honest cheapest correct impl, subsuming the
#   local-reshape argument and doubling as the grounded-oracle control), and
#   pos-reorder-lets reorders the three side-effect-free filter binds (the
#   reorder argument). Both verified to build with the frozen proof unchanged.
# PORTED (admissibility, re-aimed): the nagini case self-calls on four empty
#   equal-length parallel lists to establish the fractional-permission Requires.
#   This carrier has no heap permission; the precondition IS the three
#   length-equality `require` clauses, and the frozen impl discharging all five
#   ensures over that domain is the admissibility witness that the post-image is
#   jointly satisfiable. Verified to build.
#   AUDIT NOTE — this case's `module` is the frozen file BYTE-FOR-BYTE, which is the
#   weakest honest shape an expect="verify" case can have: it re-attests G-GOLD
#   (the frozen impl verifies) and nothing beyond it. The audit tried to land the
#   nagini shape properly, i.e. an actual self-call
#   `let _probe ← pruneParallelSystems [] [] [] []` in the impl region, and it is
#   NOT expressible here for a structural reason, measured not guessed: the
#   self-call makes the `method` recursive and Velvet demands a termination proof
#   it cannot infer — "fail to show termination for pruneParallelSystems ...
#   failed to eliminate recursive application pruneParallelSystems [] [] [] []"
#   (EXIT 1). A `require`-establishing self-call is therefore unavailable on this
#   carrier, and the frozen-impl form is kept as the only admissibility evidence
#   available. Its real content is carried by the two soundness positives, which
#   are genuinely different impls that must satisfy the same five clauses; the
#   audit additionally landed two FURTHER correct reshapes (a match-on-mask split
#   and a zip/filterMap impl) to confirm satisfiability is not shape-bound.
# VACUOUS (frame-mutate-append-blocks, frame-mutate-store-flag): referentially-
#   transparent backend, no `mut` parameter, no heap, no fractional permission —
#   there is no read-only input to overwrite (append / index-store), so the
#   MANDATORY nagini frame class has no counterpart. Per the porting map this
#   class is vacuous on Lean/Velvet. Not fabricated and not replaced.
#   DEMONSTRATED by the audit rather than asserted: an impl whose body attempts the
#   nagini append (`listA := listA ++ [0]`, the direct analogue of
#   `blocks.append(0)`) does not even ELABORATE — the compiler rejects it at the
#   assignment with "`listA` cannot be mutated, only variables declared using
#   `let mut` can be mutated". The rejection is a PARSE/elaboration refusal, not a
#   spec verdict, so such a rival could carry no witness that attributes anything
#   to the postcondition: there is no reachable program state in which a
#   non-`mut` input has been overwritten. That is what makes the class vacuous
#   here, as distinct from merely hard.
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
# PORTED (the four uniqueness/desync rivals) + ADDED (desync-C-only): each carries
#   a machine-checked witness that ELABORATES against the rival (tester = false by
#   decide) and FAILS against the frozen solution (tester = true, so decide proves
#   the = false goal FALSE) — two real builds per case (rival EXIT 0, gold EXIT 1).
#   prepatch-desync-AB is the headline pre-patch desync (companion lists unpruned);
#   wrong-mask-B-inverted applies the complement mask to one list; partial-keep-all
#   / partial-drop-all are the ignore-mask / over-prune domain rivals;
#   desync-C-only is ADDED as the mirror of the headline (only the third list
#   unpruned) so that each of C1/C2/C3 is attacked as the SOLE violated content
#   clause by some rival, proving each parallel list is independently pinned (the
#   binder-held-fixed lesson: no rival may ride any of listA/listB/listC along).
#
# CLAUSE / BINDER / POINT COVERAGE (recomputed by the AUDIT; the port's original
#   claim here was WRONG and is corrected). The three impl-constraining clauses are
#   C1 (listA), C2 (listB), C3 (listC), each also involving removeFlags; C4/C5 are
#   their length consequence. Content clauses violated at each rival's own witness
#   point, computed exhaustively rather than asserted:
#     prepatch-desync-AB     C1 + C2  (also breaks C5; C4 HOLDS — listA/listB ride
#                                      along unpruned together, so they stay
#                                      equal-length)
#     wrong-mask-B-inverted  C2 alone (C4/C5 both HOLD at [true,false]: the mask's
#                                      true-count equals its false-count, so the
#                                      complement filter yields the same length)
#     partial-keep-all       C1 + C2 + C3
#     partial-drop-all       C1 + C2 + C3
#     desync-C-only          C3 alone (also breaks C5; C4 holds)
#     desync-A-only          C1 alone (also breaks C4; C5 holds)  [ADDED by audit]
#   Each of C1/C2/C3 is now the SOLE violated content clause of exactly one rival —
#   C1 desync-A-only, C2 wrong-mask-B-inverted, C3 desync-C-only — so each of the
#   three parallel lists is shown INDEPENDENTLY load-bearing and no output binder
#   rides along unfiltered. Before the audit added desync-A-only this held for C2
#   and C3 only: C1 was never violated alone (prepatch-desync-AB couples it to C2,
#   and the two partial-* rivals violate all three), so a hypothetical spec that
#   dropped C1 while keeping C2/C3 would still have rejected every shipped rival.
#   The six reject witnesses probe SIX distinct points:
#     [1,2] [3,4] [5,6] [false,true]     (prepatch-desync-AB)
#     [1,2] [3,4] [5,6] [true,false]     (wrong-mask-B-inverted)
#     [1]   [2]   [3]   [true]           (partial-keep-all)
#     [1]   [2]   [3]   [false]          (partial-drop-all)
#     [7,8] [9,10] [11,12] [true,false]  (desync-C-only)
#     [4,5] [6,7] [8,9] [false,true]     (desync-A-only)
#   so pts=6, and every binder is varied: listA/listB/listC each carry distinct
#   values across witnesses, and removeFlags moves across all-true, all-false,
#   [false,true] and [true,false]. No two rivals are refuted at the same point.
#   All witness inputs satisfy the three length `require` clauses.
#
# AUDIT RECORD (independent re-derivation; see the per-case notes above).
#   * All 5 original witnesses were rebuilt out-of-band, twice each: rival EXIT 0,
#     gold EXIT 1, and every gold-side failure is the SEMANTIC form
#     "Tactic `decide` proved that the proposition ... = false is false" — the
#     kernel fully reduced the tester and refuted the concrete claim. None is a
#     stuck reduction, missing identifier, type error or timeout, so all five are
#     genuine discriminators.
#   * SPEC-TOO-WEAK probe (4 NEW wrong impls the battery did not contain, aimed at
#     what the shipped rivals leave unattacked): slot-swap of the A/B outputs;
#     order-reversal of all three survivor lists; filtering by the REVERSED mask;
#     dropping the last survivor from each list. All four were REJECTED (EXIT 1)
#     and each carries a witness that elaborates on it (EXIT 0) and fails
#     semantically on gold (EXIT 1). No spec hole found.
#   * SPEC-TOO-STRONG probe (2 NEW correct reshapes): a `match`-on-mask case split,
#     and a genuinely different function (`(list.zip mask).filterMap`) rather than a
#     re-spelling of `keepByMask`. Both VERIFY (EXIT 0) once the tactic body is
#     adapted — the zip/filterMap one needs its own bridging induction, supplied
#     inside the `prove_correct` body, which the spec view elides. So the spec is
#     not over-fit to `keepByMask`'s syntactic shape.
#   * The two length `require` clauses are load-bearing rather than decorative: they
#     are what `keepByMask_length_eq` consumes to discharge C4/C5, and the audit's
#     reshapes both had to re-establish them.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the prune is modeled deeply by keepByMask/numKept; mapping.md §3), so
# there is nothing to probe; the G-PBT gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
