"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-20676 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct initialMarkerPositions`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method over four value inputs):

  initialMarkerPositions
      (o : Orientation) (horizontalLimits verticalLimits : Rat × Rat)
      (currentSpan : Rat × Rat) return (out : Rat × Rat)
    ensures out = initialMarkerSpec o horizontalLimits verticalLimits          (C1)

The operation chooses the initial placement of the two boundary markers of an
interactive range picker: the ordered ``(lower, upper)`` limit pair of the axis
that matches the picker's orientation. ``initialMarkerSpec`` is a fully
transparent ``def`` (NOT an opaque oracle): a two-way orientation dispatch that
returns ``horizontalLimits`` on ``.horizontal`` and ``verticalLimits`` on
``.vertical``. The single top-level ``ensures`` clause pins THREE facets at once:

  * (F-orient) the RIGHT axis is chosen for the orientation — horizontal picks
    the horizontal limits, vertical the vertical limits;
  * (F-order) the pair is returned in its own order — ``(lower, upper)``, not
    reversed — because C1 is an equality on the ordered ``Rat × Rat`` pair;
  * (F-frame) the read-only ``currentSpan`` never enters the result — the
    postcondition is a function of ``o``/``horizontalLimits``/``verticalLimits``
    ALONE, so any impl that lets ``currentSpan`` leak into ``out`` fails C1.

All three facets are grounded in the input binders via ``initialMarkerSpec o
horizontalLimits verticalLimits``; there is no answer key to echo
(``initialMarkerSpec`` is a concrete ``def``, and the ``axioms`` region is
empty). The method has NO ``require`` clause, so the admitted domain is total.

CARRIER NOTE — the payload is ``Rat × Rat`` with ``DecidableEq``, so the sibling
velvet tester route IS available here (unlike the opaque-``Vertex`` bundles):
``extract_program_for`` / ``prove_precondition_decidable_for`` /
``prove_postcondition_decidable_for`` / ``derive_tester_for`` synthesise
``initialMarkerPositionsTester``, and each reject witness states
``initialMarkerPositionsTester <o> <hl> <vl> <span> = false := by decide`` at ONE
concrete input. ``decide`` computes the pair equality over ``Rat`` literals
directly (confirmed empirically: it elaborates against each rival and fails
against gold, where the tester returns ``true``). No opaque-term conditioning is
needed — every witness input is a small literal, so every witness head binds
NOTHING and the consistency probe is vacuously satisfied.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend, exactly as the nagini
    sibling itself records it N/A: the coordinate inputs are immutable value
    tuples carrying no read-only permission to trip. Lean and Velvet are
    referentially transparent; this bundle declares NO ``mut`` parameter, there
    is no heap, no aliasing, no permission system. There is no read-only input to
    overwrite and no substitute probe to fabricate (per the porting map,
    legitimately dropped, not faked). NOTE the frame ARGUMENT is not lost — it is
    re-expressed as facet F-frame above and attacked by the reject rivals that
    leak ``currentSpan`` into the result.
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
  * UNGROUNDED-ORACLE ECHO — N/A. C1 is a total function of the input binders
    (``initialMarkerSpec`` is a concrete ``def``, not an axiomatized oracle);
    there is no opaque answer key a wrong impl could echo. The cheapest correct
    impl returns ``initialMarkerSpec o horizontalLimits verticalLimits``
    directly, which the positive controls cover honestly.
  * DIRECTION-SWAP / PARTIAL-DOMAIN / ORDER / VALUE-LEAK — APPLIES, and is the
    whole reject surface (see the six rivals below).

WITNESS PLACEMENT. The six reject witnesses sit at SIX DISTINCT input points,
moving every input binder across the battery: ``o`` over {horizontal×3,
vertical×3}; ``horizontalLimits`` over {(10,20),(5,15),(2,8),(1,1),(3,9)};
``verticalLimits`` over {(30,40),(25,35),(0,0),(6,14)}; ``currentSpan`` over
{(0,0),(1,2),(0,40)} — so no facet is demonstrated at a single pinned point
(pts=6), and each binder that C1 depends on is varied by some witness. Both
sub-domains are refuted on more than one facet, and the ``reject-half-span-leak``
witness deliberately picks a span whose UPPER value AGREES with the matched axis
so that its refutation isolates the LOWER component alone — C1 is shown to bind
the pair componentwise, not just as a whole.

AUDIT NOTE (independent re-derivation, post-port). Every case's variant and every
reject witness was rebuilt from scratch against the real verifier; each gold-side
witness build was additionally read for its FAILURE TEXT, and all six fail with
``Tactic `decide` proved that the proposition ... = false is false`` — a semantic
refutation of the concrete claim, not a missing identifier, type error, stuck
reduction or timeout. Three cases were ADDED by that audit to close gaps the
original port left: ``pos-decidable-if-dispatch`` (the first positive that is NOT
definitionally equal to the frozen impl — the other two reshapes reduce to it, so
neither showed C1 constrains behaviour rather than the frozen term),
``reject-order-swap-vertical-only`` (F-order was pinned only on the horizontal
sub-domain) and ``reject-half-span-leak`` (every prior rival replaced the WHOLE
pair, so none showed C1 binds the two components separately). Wrong impls tried
against C1 and correctly REJECTED, beyond those shipped as cases: a constant
``horizontalLimits`` ignoring orientation; a constant literal pair; the matched
axis's lower limit duplicated into both slots; the matched pair min/max-normalised
(definitionally distinct from the identity even though the inputs are ordered);
and a three-value result, which the ``Rat × Rat`` carrier rejects as a TYPE error
rather than a spec violation (see the VACUOUS accounting below). No wrong impl
verified: no SPEC-TOO-WEAK hole was found. No faithful correct impl was found that
the spec rejects: the one correct reshape the FROZEN tactic script cannot follow
(the ``if``-dispatch) is admitted once the variant reproves it with ``cases o <;>
loom_solve``, which is a tactic shape-sensitivity, not a spec defect — and it now
ships as a case rather than as a claim.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20676"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body (strictly inside the
# ---- single `-- impl-start`/`-- impl-end` region) and unique in Solution.lean.
_GOLD_IMPL = """    -- impl-start
    -- Choose the boundary-marker positions by orientation: the limits of the
    -- horizontal axis for a horizontal picker, the limits of the vertical axis
    -- otherwise. `currentSpan` is deliberately unused.
    let positions : Rat × Rat :=
      match o with
      | .horizontal => horizontalLimits
      | .vertical   => verticalLimits
    return positions
    -- impl-end"""
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"


def _variant(impl_body):
    """Full Solution.lean variant with ONLY the impl region body replaced. The
    frozen `prove_correct ... by loom_solve` obligation is kept verbatim, so a
    reject rival is expected NOT to verify and its witness carries the evidence."""
    return _swap(_BASE, _GOLD_IMPL,
                 "    -- impl-start\n" + impl_body + "\n    -- impl-end")


# ---- The frozen proof script, replaced only for a positive whose impl shape the
# ---- frozen script's shape-sensitivity cannot follow. `variant_scope` permits a
# ---- variant to REPROVE the same obligation (the `prove_correct
# ---- initialMarkerPositions` header stays, and the statement lives in the spec
# ---- view that `same_spec` pins), so this changes the PROOF and never the SPEC.
_GOLD_PROOF = "prove_correct initialMarkerPositions by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof block drifted from expected text"


def _variant_reproven(impl_body, tactics):
    """A `_variant` whose tactic body is `tactics` instead of the frozen one."""
    return _swap(_variant(impl_body), _GOLD_PROOF,
                 "prove_correct initialMarkerPositions by\n" + tactics)


# ---- witness machinery. `derive_tester_for` synthesises the decidable tester
# ---- from the frozen (decidable) postcondition; the four directives are
# ---- appended to BOTH the rival file and the gold file, so the tester exists on
# ---- both sides by construction. `<name>Tester <o> <hl> <vl> <span> = false`
# ---- says the extracted program's result violates the postcondition at that
# ---- input. Checked in a file whose `prove_correct` block is stripped (so no
# ---- tactic script can mask the verdict); no `sorry`/`admit`/`native_decide`.
_TESTER = (
    "extract_program_for initialMarkerPositions\n"
    "prove_precondition_decidable_for initialMarkerPositions\n"
    "prove_postcondition_decidable_for initialMarkerPositions\n"
    "derive_tester_for initialMarkerPositions\n\n")


def _witness(o, hl, vl, span):
    return (_TESTER +
            f"example : initialMarkerPositionsTester {o} {hl} {vl} {span} "
            "= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-spec",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the inline `match` local and return the modeled choice
        # directly. This is the honest cheapest-correct impl; the frozen proof
        # (`loom_solve`) closes unchanged because the returned value is definitionally
        # `initialMarkerSpec o horizontalLimits verticalLimits`.
        "module": _variant(
            "    return initialMarkerSpec o horizontalLimits verticalLimits"),
        "rationale": "the straight-line `return initialMarkerSpec o "
                     "horizontalLimits verticalLimits` is the simplest correct "
                     "impl; it meets C1 by definition. If it fails to verify the "
                     "postcondition is over-fit to the inline-match form => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-orientation-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the orientation dispatch but write the VERTICAL arm first.
        # Same behaviour, different branch order; the frozen proof closes unchanged.
        "module": _variant(
            "    let positions : Rat × Rat :=\n"
            "      match o with\n"
            "      | .vertical   => verticalLimits\n"
            "      | .horizontal => horizontalLimits\n"
            "    return positions"),
        "rationale": "the orientation dispatch with the vertical arm written "
                     "first selects the identical value; it must satisfy C1. If it "
                     "cannot verify the spec is over-fit to the `.horizontal`-first "
                     "arm order => SPEC-TOO-STRONG.",
    },

    {
        "id": "pos-decidable-if-dispatch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the DISPATCH ITSELF, not just the arm order: decide the
        # orientation with a `DecidableEq` test (`if o = .horizontal then ... else
        # ...`) instead of pattern-matching the constructor. Behaviourally the
        # same choice, but NOT definitionally equal to the frozen `match` (checked
        # by hand: `example : ifShape = matchShape := rfl` fails), so this is a
        # genuinely different term the spec has to admit on its own merits rather
        # than by reduction. The frozen `loom_solve` alone leaves the `if` unsplit,
        # so the case reproves with `cases o <;> loom_solve` — a PROOF change the
        # variant scope permits (the obligation header and the spec view are
        # untouched), which is the correct response to a shape-sensitive tactic and
        # the reason this is NOT a SPEC-TOO-STRONG finding.
        "module": _variant_reproven(
            "    let positions : Rat × Rat :=\n"
            "      if o = Orientation.horizontal then horizontalLimits "
            "else verticalLimits\n"
            "    return positions",
            "  cases o <;> loom_solve"),
        "rationale": "deciding the orientation with the `DecidableEq` test rather "
                     "than a constructor `match` selects the identical value on "
                     "both orientations, so it must satisfy C1. This is the "
                     "strongest available positive: unlike the arm-reorder and the "
                     "direct-spec reshapes it is NOT definitionally equal to the "
                     "frozen impl, so admitting it shows C1 constrains the "
                     "BEHAVIOUR rather than the frozen term's reduction. If no "
                     "proof of the frozen obligation can close over this impl, C1 "
                     "is over-fit to the `match` form => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # nagini "a self-call on an F2P-shaped input satisfies the precondition"
    # probe is vacuous on the total domain — nothing could exclude any input.
    # Re-aimed at the residual admissibility risk: that the post-image is
    # DEGENERATE (constant / orientation-insensitive) so no rival could be
    # distinguished. This case discharges an in-region `assert`, at concrete
    # points, that the modeled choice genuinely DEPENDS on orientation — a
    # horizontal picker selects the horizontal limits and a vertical picker the
    # (different) vertical limits. The frozen impl and obligation are kept
    # verbatim so C1 still discharges; the assert is LIVE (a false claim leaves an
    # unsolved goal — confirmed empirically) and is discharged by the frozen proof.
    # =====================================================================
    {
        "id": "admiss-orientation-sensitive",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    assert (with_name_prefix `adm\n"
            "      (initialMarkerSpec Orientation.horizontal ((10:Rat),(20:Rat)) "
            "((30:Rat),(40:Rat)) = ((10:Rat),(20:Rat)) ∧\n"
            "       initialMarkerSpec Orientation.vertical ((10:Rat),(20:Rat)) "
            "((30:Rat),(40:Rat)) = ((30:Rat),(40:Rat))))\n"
            "    let positions : Rat × Rat :=\n"
            "      match o with\n"
            "      | .horizontal => horizontalLimits\n"
            "      | .vertical   => verticalLimits\n"
            "    return positions"),
        "rationale": "the post-image is non-degenerate and orientation-sensitive: "
                     "on the same limit pairs a horizontal picker selects the "
                     "horizontal limits (10,20) and a vertical picker the vertical "
                     "limits (30,40), so the spec actually constrains the result "
                     "rather than admitting a constant. The in-region assert must "
                     "discharge (else the modeled behavior would be degenerate); "
                     "the frozen impl and obligation are kept verbatim so C1 still "
                     "discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each carrying a machine-checked refutation witness at
    # a DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "reject-current-span-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change shape: seed the markers from the picker's current
        # selection span regardless of orientation (facet F-frame violated). At
        # introduction the span is the degenerate origin pair, so the markers land
        # off the axis limits.
        "module": _variant("    return currentSpan"),
        "refinement": "this is the pre-change behavior: the initial marker "
                      "positions are taken from the picker's current selection "
                      "span, which at introduction is the degenerate origin pair. "
                      "Introducing markers at those off-limit positions forces the "
                      "affected axis's view to expand to include the origin, so the "
                      "failing test's assertion that the axis view stays at its "
                      "original limits fails — exactly the reported regression. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C1 (facet F-frame): the read-only currentSpan "
                     "leaks into the result, so out = currentSpan ≠ "
                     "initialMarkerSpec o horizontalLimits verticalLimits whenever "
                     "the span differs from the orientation-matched limits. Refuted "
                     "at (horizontal, hl=(10,20), span=(0,0)), where the impl "
                     "returns (0,0) but the post-image demands (10,20). A verify "
                     "here is SPEC-TOO-WEAK (the frame clause unenforced).",
        "witness": _witness("Orientation.horizontal", "((10:Rat),(20:Rat))",
                            "((30:Rat),(40:Rat))", "((0:Rat),(0:Rat))"),
    },
    {
        "id": "reject-orientation-axis-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG axis for the orientation: horizontal selects the vertical limits
        # and vice versa (facet F-orient violated). Right shape, grounded in *a*
        # limit pair, but the wrong one for the orientation.
        "module": _variant(
            "    let positions : Rat × Rat :=\n"
            "      match o with\n"
            "      | .horizontal => verticalLimits\n"
            "      | .vertical   => horizontalLimits\n"
            "    return positions"),
        "refinement": "a counterpart that reads the opposite axis's limits places "
                      "a horizontal picker's markers at the vertical axis's range. "
                      "Those positions lie off the horizontal axis's own view, so "
                      "introducing the markers expands the horizontal view and the "
                      "failing test's assertion that it stays at its original "
                      "limits fails. It would NOT resolve.",
        "rationale": "REJECT from C1 (facet F-orient): on the horizontal "
                     "sub-domain out = verticalLimits ≠ horizontalLimits, and "
                     "symmetrically on vertical. Refuted at (horizontal, "
                     "hl=(5,15), vl=(25,35)), where the impl returns (25,35) but "
                     "the post-image demands (5,15). A verify here would mean C1 "
                     "does not bind each orientation to its own axis "
                     "(SPEC-TOO-WEAK).",
        "witness": _witness("Orientation.horizontal", "((5:Rat),(15:Rat))",
                            "((25:Rat),(35:Rat))", "((1:Rat),(2:Rat))"),
    },
    {
        "id": "reject-partial-vertical-span-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on HORIZONTAL, but on the VERTICAL sub-domain falls back to the
        # pre-change span leak. Passes the horizontal case but diverges exactly on
        # the vertical orientation — probes that BOTH orientations are pinned, not
        # just one.
        "module": _variant(
            "    let positions : Rat × Rat :=\n"
            "      match o with\n"
            "      | .horizontal => horizontalLimits\n"
            "      | .vertical   => currentSpan\n"
            "    return positions"),
        "refinement": "a counterpart that fixes only the horizontal orientation "
                      "but leaves the vertical branch seeding from the current "
                      "selection span. For a vertical picker the degenerate origin "
                      "span sits off the vertical axis's view, so introducing the "
                      "markers expands the vertical view and the failing test's "
                      "assertion fails on the vertical case even though the "
                      "horizontal case passes. It would NOT resolve both.",
        "rationale": "REJECT from C1 (facet F-orient + F-frame on the vertical "
                     "sub-domain): out = currentSpan ≠ verticalLimits when the span "
                     "differs. Refuted at (vertical, vl=(30,40), span=(0,0)), where "
                     "the impl returns (0,0) but the post-image demands (30,40) — "
                     "the vertical sub-domain no other rival isolates. A verify "
                     "here is SPEC-TOO-WEAK (only one orientation pinned).",
        "witness": _witness("Orientation.vertical", "((10:Rat),(20:Rat))",
                            "((30:Rat),(40:Rat))", "((0:Rat),(0:Rat))"),
    },
    {
        "id": "reject-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Right axis, but the pair returned REVERSED (upper, lower). Set-equal to
        # the limits, but C1 is an equality on the ORDERED pair (facet F-order).
        "module": _variant(
            "    let positions : Rat × Rat :=\n"
            "      match o with\n"
            "      | .horizontal => (horizontalLimits.2, horizontalLimits.1)\n"
            "      | .vertical   => (verticalLimits.2, verticalLimits.1)\n"
            "    return positions"),
        "refinement": "a counterpart that reports the limit pair reversed "
                      "(upper, lower) hands the boundary-handle container its "
                      "positions in swapped order; the container reports its "
                      "observed positions back as the reversed list, so the "
                      "failing test's order-sensitive equality against the axis's "
                      "own (lower, upper) view limits fails. It would NOT resolve.",
        "rationale": "REJECT from C1 (facet F-order): C1 is an equality on the "
                     "ordered Rat × Rat pair, so out = (upper, lower) ≠ "
                     "(lower, upper) whenever the two limits differ; set-equality "
                     "is not enough. Refuted at (horizontal, hl=(2,8)), where the "
                     "impl returns (8,2) but the post-image demands (2,8). A verify "
                     "here would mean C1 does not pin order (SPEC-TOO-WEAK).",
        "witness": _witness("Orientation.horizontal", "((2:Rat),(8:Rat))",
                            "((0:Rat),(0:Rat))", "((0:Rat),(0:Rat))"),
    },
    {
        "id": "reject-order-swap-vertical-only",
        "kind": "uniqueness",
        "expect": "reject",
        # F-order broken on the VERTICAL sub-domain only: the horizontal arm is
        # exactly correct, the vertical arm returns the right axis's pair reversed.
        # Strictly closer than reject-order-swap, which breaks order on BOTH arms
        # and is refuted on the horizontal one — so nothing in the battery showed
        # F-order was pinned on the vertical sub-domain independently.
        "module": _variant(
            "    let positions : Rat × Rat :=\n"
            "      match o with\n"
            "      | .horizontal => horizontalLimits\n"
            "      | .vertical   => (verticalLimits.2, verticalLimits.1)\n"
            "    return positions"),
        "refinement": "a counterpart that gets the horizontal picker exactly right "
                      "but hands the boundary-handle container the vertical axis's "
                      "limit pair reversed. The container reports its observed "
                      "positions back in the order it was given them, so the "
                      "failing test's order-sensitive equality against the vertical "
                      "axis's own (lower, upper) view limits fails on the vertical "
                      "case while the horizontal case passes. It would NOT resolve "
                      "both.",
        "rationale": "REJECT from C1 (facet F-order on the VERTICAL sub-domain): out "
                     "= (verticalLimits.2, verticalLimits.1) ≠ verticalLimits "
                     "whenever the two vertical limits differ. Refuted at (vertical, "
                     "vl=(6,14)), where the impl returns (14,6) but the post-image "
                     "demands (6,14) — the one sub-domain/facet pair no other rival "
                     "isolates (reject-order-swap is refuted on horizontal, "
                     "reject-partial-vertical-span-leak attacks F-frame). A verify "
                     "here would mean C1 pins order on one orientation only "
                     "(SPEC-TOO-WEAK).",
        "witness": _witness("Orientation.vertical", "((1:Rat),(1:Rat))",
                            "((6:Rat),(14:Rat))", "((0:Rat),(0:Rat))"),
    },
    {
        "id": "reject-half-span-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # The tightest near-miss in the battery: the orientation dispatch is
        # correct AND the upper component is taken from the right axis; only the
        # LOWER component is leaked from the read-only span. Every other rival
        # replaces the whole pair, so none of them showed C1 binds the components
        # SEPARATELY — a spec pinning only "the upper limit is right" would still
        # reject them all and admit this one.
        "module": _variant(
            "    let p : Rat × Rat :=\n"
            "      match o with\n"
            "      | .horizontal => horizontalLimits\n"
            "      | .vertical   => verticalLimits\n"
            "    return (currentSpan.1, p.2)"),
        "refinement": "a counterpart that reads the orientation-matched axis for the "
                      "upper boundary marker but still seeds the lower one from the "
                      "picker's current selection span. The lower marker then lands "
                      "off the axis's own view, so introducing the markers expands "
                      "that axis's view and the failing test's assertion that it "
                      "stays at its original limits fails — the same regression, "
                      "half repaired. It would NOT resolve.",
        "rationale": "REJECT from C1 (facet F-frame, at COMPONENT granularity): out.1 "
                     "= currentSpan.1 ≠ (initialMarkerSpec o horizontalLimits "
                     "verticalLimits).1 whenever the span's lower value differs from "
                     "the matched axis's lower limit, even though out.2 is already "
                     "correct. Refuted at (vertical, vl=(30,40), span=(0,40)), where "
                     "the impl returns (0,40) but the post-image demands (30,40) — "
                     "note the span's UPPER value is chosen to agree with the axis, "
                     "so the refutation isolates the lower component alone. A verify "
                     "here would mean C1 constrains only part of the pair "
                     "(SPEC-TOO-WEAK).",
        "witness": _witness("Orientation.vertical", "((3:Rat),(9:Rat))",
                            "((30:Rat),(40:Rat))", "((0:Rat),(40:Rat))"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus 2 AXIOM_TESTS. The
# sibling contracts `selector_initial_coords(direction, x_bound, y_bound,
# other_coords) -> List[int]` over a List[int] carrier of coordinate values, with
# a fold/identity postcondition (P4) threaded through the pure oracle
# `reported_positions(selected_bound(...))`. This bundle models the SAME choice
# more directly: a `Rat × Rat` limit pair chosen by orientation
# (`out = initialMarkerSpec o horizontalLimits verticalLimits`). The oracle-fold
# clause P4 collapses here into C1 (the oracle was a pure identity on the grounded
# selection, so it carried no independent content), and the list-length clause P1
# collapses because the carrier is a fixed 2-tuple, not a variable-length list.
# Every sibling case is accounted for below.
#
#   sibling case (nagini)               -> here
#   ---------------------------------------------------------------------
#   pos-control-vertical-first-reorder   -> pos-orientation-branch-reorder   RE-SHAPED
#   pos-control-append-grounded          -> pos-direct-spec                  RE-SHAPED
#   admiss-f2p-horizontal                -> admiss-orientation-sensitive     RE-AIMED
#   reject-prepatch-other-coords         -> reject-current-span-leak         PORTED
#   reject-direction-swap                -> reject-orientation-axis-swap     PORTED
#   reject-partial-vertical-prepatch     -> reject-partial-vertical-span-leak PORTED
#   reject-order-swap                    -> reject-order-swap                PORTED
#   reject-wrong-length-three            -> (none)                          VACUOUS (carrier)
#
# 7 ported/re-shaped/re-aimed, 1 vacuous. Plus 3 cases with NO sibling ancestor,
# added by the post-port audit to close gaps the ported set left (see the AUDIT
# NOTE in the module docstring): pos-decidable-if-dispatch,
# reject-order-swap-vertical-only, reject-half-span-leak. 10 SPEC cases total
# (4 soundness/admissibility positives, 6 uniqueness rivals).
#
# VACUOUS, RE-DERIVED INDEPENDENTLY (audit, attack F). reject-wrong-length-three is
#   the ONLY sibling case the port dropped, and the drop was re-checked by building
#   it rather than by argument: the analogous variant `return ((10:Rat),(20:Rat),
#   (10:Rat))` fails with `Application type mismatch: the argument (20, 10) has type
#   Rat × Rat but is expected to have type Rat`. That is the ELABORATOR refusing to
#   write a 3-tuple where a `Rat × Rat` is required — the arity is a type-level
#   invariant of the carrier, so there is no impl for the length clause to be
#   violated BY, and no witness could attribute such a rejection to the spec (the
#   failure is a type error, not a semantic refutation). Genuinely inexpressible
#   here, not dropped for difficulty.
#
# RE-SHAPED (positives): the sibling's append-grounded positive materialises the
#   grounded oracle value element-by-element; the structural analog here is the
#   straight-line `return initialMarkerSpec o horizontalLimits verticalLimits`.
#   The sibling's vertical-first branch reorder maps directly onto reordering the
#   orientation `match` arms (vertical first).
# RE-AIMED (admissibility): the sibling shows the F2P-shaped horizontal input lies
#   in the precondition and is pinned to the x-bound endpoints in order. This
#   method has NO `require` clause, so nothing could exclude any input on the
#   total domain — that probe is vacuous. Re-aimed at proving the post-image is
#   NON-DEGENERATE and orientation-sensitive (a horizontal picker selects the
#   horizontal limits, a vertical picker the different vertical limits), via an
#   in-region assert at concrete points discharged by the frozen proof.
# PORTED (rivals): the four sibling rivals port cheaply because both carriers pin
#   the same three facets; only the mechanics change (List[int] index conjuncts
#   P2/P3 -> a `Rat × Rat` equality C1) and each gains a machine-checked witness
#   (new work — the sibling relied on Viper's automatic postcondition discharge):
#     * reject-prepatch-other-coords: the sibling reads the unrelated (0,0)
#       extents (`other_coords`) instead of the bound; here the direct analog is
#       leaking `currentSpan` (facet F-frame). This carries the frame ARGUMENT the
#       vacuous permission-mutation class cannot express on a referentially
#       transparent backend — it is attacked as a value-leak, not a heap mutation.
#     * reject-direction-swap: read the opposite axis's limits (facet F-orient).
#     * reject-partial-vertical-prepatch: correct on horizontal, span-leak on
#       vertical (facet F-orient/F-frame on the vertical sub-domain only).
#     * reject-order-swap: right axis, reversed pair (facet F-order) — C1 is an
#       equality on the ORDERED pair, so set-equality is insufficient.
# VACUOUS (reject-wrong-length-three): the sibling returns a 3-element List[int],
#   violating the length clause P1 and the 2-element fold form P4. Here the carrier
#   is a FIXED 2-tuple `Rat × Rat`; there is no variable-length list and no way to
#   return three coordinate values, so the length clause has no counterpart and
#   the length-break rival cannot be written at all. This is carrier narrowing
#   (the 2-tuple carrier makes the arity a type-level invariant, not a spec clause
#   a rival could violate), not a dropped-because-hard omission.
#
# BINDER / CLAUSE COVERAGE. The input binders are `o`, `horizontalLimits`,
#   `verticalLimits`, `currentSpan`; the single top-level clause C1 folds three
#   facets (F-orient: right axis; F-order: right order; F-frame: no span leak). C1
#   is DEFENDED by three positive controls and the admissibility case, and ATTACKED
#   on every facet, on BOTH sub-domains, and at COMPONENT granularity:
#     F-frame  — reject-current-span-leak (whole pair, horizontal),
#                reject-partial-vertical-span-leak (whole pair, vertical),
#                reject-half-span-leak (LOWER component only, vertical);
#     F-orient — reject-orientation-axis-swap (both arms),
#                reject-partial-vertical-span-leak (vertical arm only);
#     F-order  — reject-order-swap (refuted on horizontal),
#                reject-order-swap-vertical-only (vertical arm only).
#   The three positives are graded by how much they can cheat: pos-direct-spec and
#   pos-orientation-branch-reorder are definitionally EQUAL to the frozen impl (both
#   `rfl`-provable against it), so they establish the spec admits the frozen
#   behaviour but not that it admits behaviour stated differently;
#   pos-decidable-if-dispatch is NOT (checked: the `rfl` fails), so it is the one
#   that shows C1 is a claim about the value and not about the frozen term's shape.
#   Every input binder C1 depends on is varied by some witness: `o` over
#   {horizontal×3, vertical×3}, `horizontalLimits` over
#   {(10,20),(5,15),(2,8),(1,1),(3,9)}, `verticalLimits` over
#   {(30,40),(25,35),(0,0),(6,14)}, `currentSpan` over {(0,0),(1,2),(0,40)} — the
#   span-leak rivals demonstrate the result's dependence on `currentSpan` directly,
#   and the variation is MEANINGFUL rather than two spellings of one point: each
#   witness input is one at which its own rival's returned pair differs from the
#   post-image, and the (1,1) / (0,40) entries are chosen so that the OTHER
#   component agrees, pinning the refutation to a single slot. Six DISTINCT witness
#   inputs (pts=6).
#
# WITNESS FORM. The carrier is `Rat × Rat` with DecidableEq, so the sibling velvet
#   tester route is available: `derive_tester_for` synthesises
#   `initialMarkerPositionsTester`, and each witness states
#   `initialMarkerPositionsTester <o> <hl> <vl> <span> = false := by decide` at a
#   distinct concrete input. `decide` computes the pair equality over `Rat`
#   literals; every witness head binds NOTHING (no opaque-term conditioning), so
#   the consistency probe is vacuously satisfied (no third build is even run).
#   Confirmed empirically, and re-confirmed build-by-build by the post-port audit:
#   each witness ELABORATES against its rival (exit 0) and FAILS against the frozen
#   solution (exit 1) — the required discrimination — and each rival module does NOT
#   verify under the frozen `loom_solve` proof (exit 1). The gold-side failure is
#   in every case the SEMANTIC one, `Tactic `decide` proved that the proposition
#   ... = false is false`, i.e. the kernel evaluated the tester at that input and
#   found it TRUE of the frozen impl. No gold-side build failed by unknown
#   identifier, type error, stuck reduction (`did not reduce to isTrue or isFalse`)
#   or timeout, so no witness is a syntactic pseudo-discriminator.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. This
#   bundle consumes no `axiom` (the `axioms` region is empty — the choice is
#   modeled directly by the pure `def initialMarkerSpec`; the sibling's
#   `reported_positions` @ContractOnly identity has no counterpart because the
#   consumer that reports the positions back verbatim is exercised live by G-CONF,
#   not modeled). There is nothing here for this gate to probe.
AXIOM_TESTS = []
