"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24570 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct alignOffsets`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method over three read-only inputs):

  alignOffsets (hd : List (Rat × Rat)) (extent : Option Rat) (anchor : Anchor)
      return (out : Aligned)
    require hd ≠ []
    ensures out = alignSpec hd extent anchor                              (C1)

The operation places a list of boxes within a common extent: it returns the
extent, the packing descent, and one per-box offset along the aligned axis.
``alignSpec`` is a fully transparent ``def`` (NOT an opaque oracle): one branch
per anchor, each an exact arithmetic relation on that box's own
``(height, descent) = (p.1, p.2)`` pair. The single top-level ``ensures`` clause
pins, per anchor, the whole result record — and the DISCRIMINATING content is
the anchor→placement GROUPING that the issue reports reversed:

  * a LOW-EDGE anchor places each box by its own descent (``p.2``);
  * a HIGH-EDGE anchor places each box by how far it falls short of the extent
    plus its descent (``h - p.1 + p.2``);
  * a CENTRE anchor places each box at half its shortfall plus its descent
    (``(h - p.1) / 2 + p.2``);
  * a BASELINE re-derives the extent and leaves every box at 0.

The two named edge anchors that the bug swaps sit in the low-edge and high-edge
groups respectively; a rival that regroups them (or that mishandles any single
box, or halves the shortfall) contradicts C1 on the box where the two placement
formulas differ. C1 pins the WHOLE record, so a rival that gets every offset
right and the returned ``extent`` wrong contradicts it too — probed here, since
the clause is only as strong as the facets some rival actually attacks. All facets are GROUNDED in the three input binders ``hd`` /
``extent`` / ``anchor`` via ``alignSpec``; there is no answer key to echo
(``alignSpec`` is a concrete ``def`` and the ``axioms`` region is empty).

CARRIER NOTE — the impl is a STRAIGHT-LINE ``match anchor`` (no loop), and both
``Anchor`` and ``Aligned`` derive ``DecidableEq`` in the FROZEN spec view. Two
consequences shape every witness below:

  * a witness reaches the impl through Velvet's extractor
    (``extract_program_for alignOffsets`` gives ``alignOffsetsExec hd extent
    anchor = NonDetT.run (alignOffsets hd extent anchor)``) and states, at a
    concrete input, ``alignOffsetsExec … ≠ DivM.res (alignSpec …)``. Because the
    impl is a closed-form ``match``, its extracted program REDUCES under ``simp``
    to a concrete ``Aligned`` literal; the record equality is decided by
    ``Aligned.mk.injEq`` down to per-field ``Rat`` equalities.
  * ``Rat`` equality does NOT go through bare ``decide`` (its ``Decidable``
    instance gets stuck on ``Rat.num`` — measured in this workspace), so the
    residual ``Rat`` (in)equalities are closed by ``simp`` with the
    field-arithmetic unfolding lemmas ``Rat.sub_def`` / ``Rat.add_def`` (and,
    where a shortfall is halved, ``Rat.div_def`` / ``Rat.mul_def``) plus
    ``Rat.normalize``. The ``⊔`` (``Rat`` ``max``) that ``resolvedExtent`` and
    ``listMax`` produce does NOT reduce under that ``simp``, so most witnesses
    supply an explicit ``some`` extent and discriminate on a field where no
    ``⊔`` survives.
  * ``⊔`` IS nevertheless reachable, via ``decide +kernel``, and this CORRECTS an
    earlier reading of the carrier. Measured (audit 2): ``decide +kernel`` closes
    ``(2:Rat) ⊔ 0 = 2`` and ``listMax [(6:Rat),(2:Rat)] = 6``, while ``simp``,
    ``simp [max_def]``, ``rw [sup_eq_left]``, ``max_eq_left`` and bare ``decide``
    all fail on the same goal. `+kernel` bypasses the ``Decidable`` instance that
    stalls on ``Rat.num`` and evaluates in the kernel instead. So a witness whose
    DISCRIMINATING field depends on a ``max`` over the boxes is expressible after
    all — ``weak-baseline-descent-field-zero`` is exactly that witness, and the
    earlier record's claim that two such probes were "tooling-limited" was wrong
    on the tooling, not on the spec. Such a witness's gold-side failure is a real
    kernel evaluation (``Tactic `decide` proved that the proposition False is
    false``), and its flipped-claim forgery INVERTS (gold 0 / rival 1), so the
    exit code carries information about the claim.

Against each rival the witness ELABORATES (the rival's ``match`` branch reduces
to a literal that differs from ``alignSpec`` at the probed box, so ``simp`` closes
the ``≠``); against the FROZEN solution it FAILS (``alignOffsets`` reduces to the
SAME literal as ``alignSpec``, so the goal collapses to ``⊢ False`` and ``simp``
leaves it unsolved). Every reject case's two builds were run out-of-band with
``scripts/lean_verify.sh`` (rival exit 0, gold exit 1, ``⊢ False`` on gold) and
re-run independently by the audit that added the last three rivals, the
admissibility case and the third positive; see AUDIT AMENDMENTS at the foot of
this file for what that re-derivation changed and what it measured. No
witness binds a hypothesis (every input is a concrete literal), so there is no
joint-satisfiability obligation. No ``sorry``/``admit``/``native_decide``/``axiom``.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling holds ``heights``
    and ``descents`` at ``Acc(list_pred(.), 1/2)`` and its MANDATORY frame rival
    writes a value-neutral element back into a read-only input to trip
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent:
    ``hd`` is an immutable value, this bundle declares NO ``mut`` parameter, and
    there is no heap, no aliasing, and no permission system to trip. There is no
    read-only input to overwrite and no substitute probe to fabricate, so the
    class is vacuous (per the porting map, legitimately dropped, not faked).
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
  * UNGROUNDED-ORACLE ECHO — N/A. C1 is a total function of the three inputs
    (``alignSpec`` is a concrete ``def``, not an axiomatized oracle); there is no
    opaque answer key a wrong impl could echo. The cheapest correct impl returns
    ``alignSpec hd extent anchor`` directly, which the positive controls cover
    honestly (proving the spec is not echo-vulnerable — any WRONG placement fails
    C1).
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: each rival
    is correct on part of the domain (some anchors, some boxes, zero-shortfall
    boxes) and diverges where the mishandled placement bites.

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; the placement is a concrete arithmetic ``def`` over the inputs,
validated == the real patched routine by conformance_check.py / G-CONF — not this
gate's job, and the gate ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24570"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies wholly inside the impl body (between -- impl-start /
# -- impl-end, indented at 6 spaces — distinct from the 2-space `pure`-region
# copy of alignSpec) or is the whole prove_correct tactic block; both are elided
# from the consumer spec view. _swap asserts each is present exactly once, so any
# drift in Solution.lean fails loudly at import.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the closed-form `match anchor`).
# Used by the direct positive (replace with `return alignSpec …`) and the
# branch-reorder positive (permute the arms).
_IMPL = (
    "    let result : Aligned :=\n"
    "      match anchor with\n"
    "      | .baseline =>\n"
    "          let hdesc := listMax (hd.map (fun p => p.1 - p.2))\n"
    "          let desc  := listMax (hd.map (fun p => p.2))\n"
    "          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }\n"
    "      | .left | .bottom =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }\n"
    "      | .right | .top =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }\n"
    "      | .center =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The two edge-anchor arms as one block (for the group-swap rival). Their bodies
# are what the pre-patch reversed.
_EDGE = (
    "      | .left | .bottom =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }\n"
    "      | .right | .top =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }"
)
assert _BASE.count(_EDGE) == 1, "edge-anchor arms drifted"

# The low-edge arm alone (for the drop-descent rival).
_LOWER = (
    "      | .left | .bottom =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }"
)
assert _BASE.count(_LOWER) == 1, "low-edge arm drifted"

# The high-edge arm alone (for the halves-shortfall and first-box rivals).
_UPPER = (
    "      | .right | .top =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }"
)
assert _BASE.count(_UPPER) == 1, "high-edge arm drifted"

# The centre arm alone (for the centre-uses-full-shortfall rival).
_CENTER = (
    "      | .center =>\n"
    "          let h := resolvedExtent hd extent\n"
    "          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }"
)
assert _BASE.count(_CENTER) == 1, "centre arm drifted"

# The baseline arm alone (for the baseline-branch rivals added by the audit).
_BASELINE = (
    "      | .baseline =>\n"
    "          let hdesc := listMax (hd.map (fun p => p.1 - p.2))\n"
    "          let desc  := listMax (hd.map (fun p => p.2))\n"
    "          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }"
)
assert _BASE.count(_BASELINE) == 1, "baseline arm drifted"

# The head of the impl region (for the in-region admissibility assert).
_IMPL_HEAD = "    -- impl-start\n    let result : Aligned :="
assert _BASE.count(_IMPL_HEAD) == 1, "impl-region head drifted"

# The frozen prove_correct tactic block (unique, elided from the spec view).
_PROOF = (
    "prove_correct alignOffsets by\n"
    "  loom_solve\n"
    "  cases anchor <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _reject(old, new):
    """Full variant: exactly one impl-region substring replaced (proof frozen —
    the closed-form rival breaks `cases anchor <;> rfl`, which IS the intended
    rejection; the witness, not the tactic failure, is what the gate scores)."""
    return _swap(_BASE, old, new)


# ---- witness preamble. Reaches the rival's extracted program (extraction needs
# ---- no tactic script), states at a concrete input that the rival's result
# ---- differs from the transparent model `alignSpec`, and closes the `≠` by
# ---- reducing the closed-form `match` to an `Aligned` literal (`Aligned.mk.injEq`
# ---- for the record, `Rat.*_def`/`Rat.normalize` for the residual `Rat`
# ---- (in)equalities — `decide` is stuck on `Rat.num` in this workspace). Checked
# ---- in a file whose `prove_correct` block is stripped; no
# ---- `axiom`/`sorry`/`native_decide`.
def _witness(inp: str, anchor: str, rat_div: bool = False,
             kernel: bool = False) -> str:
    lemmas = "Rat.sub_def, Rat.add_def, "
    if rat_div:
        lemmas += "Rat.div_def, Rat.mul_def, "
    # `kernel=True` appends `all_goals decide +kernel`. Needed only where the
    # DISCRIMINATING field carries an unreduced `⊔` (the `max` that
    # `resolvedExtent`/`listMax` produce): `simp` with the field-arithmetic
    # lemmas leaves e.g. `¬0 = 2 ⊔ 0`, and the kernel evaluates it. Measured
    # (audit 2): `decide +kernel` closes `(2:Rat) ⊔ 0 = 2` and
    # `listMax [(6:Rat),(2:Rat)] = 6`, where `simp` / `max_def` / `sup_eq_left`
    # / `max_eq_left` / plain `decide` all fail. This is a REAL evaluation, not a
    # stuck reduction: on the frozen solution the same script reports ``Tactic
    # `decide` proved that the proposition False is false`` (the kernel decided
    # the residual), and the flipped-claim forgery INVERTS (gold 0 / rival 1),
    # so the exit code tracks the claim.
    tail = "  all_goals decide +kernel\n" if kernel else ""
    return (
        "extract_program_for alignOffsets\n\n"
        "example :\n"
        f"    alignOffsetsExec {inp} Anchor.{anchor}\n"
        f"      ≠ DivM.res (alignSpec {inp} Anchor.{anchor}) := by\n"
        "  unfold alignOffsetsExec alignOffsets\n"
        "  simp [NonDetT.run, pure, alignSpec, resolvedExtent, listMax, List.map,\n"
        f"        Aligned.mk.injEq, {lemmas}Rat.normalize]\n"
        + tail
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify (else SPEC-TOO-STRONG). Both verified out-of-band with a
    # real build.
    # =====================================================================
    {
        "id": "pos-direct-alignspec",
        "kind": "soundness",
        "expect": "verify",
        # Drop the explicit per-anchor `match` and return the modeled placement
        # directly. `alignSpec` IS the desired result (grounded in the inputs, no
        # opaque answer key), so this is the honest cheapest correct impl; it
        # doubles as proof the spec is not echo-vulnerable. The residual goal
        # closes under `loom_solve` alone, so the proof is retuned in-region
        # (the obligation statement is untouched).
        "module": _swap(
            _swap(_BASE, _IMPL, "    return alignSpec hd extent anchor"),
            _PROOF, "prove_correct alignOffsets by\n  loom_solve"),
        "rationale": "the post-image `alignSpec hd extent anchor` is GROUNDED in "
                     "the inputs (a total def, no opaque answer key), so "
                     "`return alignSpec hd extent anchor` is the honest cheapest "
                     "CORRECT impl. It MUST verify — the clause is literally "
                     "`out = alignSpec hd extent anchor` — else C1 is "
                     "SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable: "
                     "any wrong placement fails the clause.",
    },
    {
        "id": "pos-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT impl: the four-way `match` is reordered
        # to baseline / right|top / center / left|bottom. Branch ORDER changes but
        # each anchor still receives the SAME placement (the match is on the
        # anchor value, not on position), so C1 holds on the whole domain. The
        # frozen proof `cases anchor <;> rfl` is kept verbatim (it splits on the
        # anchor and each residual is still `rfl`). If a faithful reorder could
        # not verify, C1 would be over-fit to the branch ORDER => SPEC-TOO-STRONG.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Aligned :=\n"
            "      match anchor with\n"
            "      | .baseline =>\n"
            "          let hdesc := listMax (hd.map (fun p => p.1 - p.2))\n"
            "          let desc  := listMax (hd.map (fun p => p.2))\n"
            "          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun _ => (0 : Rat)) }\n"
            "      | .right | .top =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }\n"
            "      | .center =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }\n"
            "      | .left | .bottom =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }\n"
            "    return result"),
        "rationale": "structurally different CORRECT impl: the four-way `match` is "
                     "reordered (baseline / high-edge / centre / low-edge). Each "
                     "anchor still receives the SAME placement (the match is on the "
                     "anchor value, not on position), so C1 holds on the whole "
                     "domain and the frozen `cases anchor <;> rfl` proof still "
                     "closes. Must verify, else C1 is over-fit to the branch ORDER "
                     "=> SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a closed-form `match` variant carrying a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument that its faithful real counterpart would NOT resolve the
    # failing tests (the two named-edge-anchor cases of the packer layout suite).
    # =====================================================================

    # ---- ANCHOR-GROUP SWAP: the exact pre-patch grouping ----
    {
        "id": "weak-anchor-group-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Swap the two named edge anchors between the low-edge and high-edge
        # groups: one named edge gets the far-edge (shortfall+descent) placement
        # and the other gets the near-edge (descent) placement — the reverse of
        # the desired grouping. Correct only where the shortfall is 0.
        "module": _reject(
            _EDGE,
            "      | .left | .top =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun p => p.2) }\n"
            "      | .right | .bottom =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }"),
        "refinement": "this is the pre-patch grouping verbatim: the two named edge "
                      "anchors are bucketed with the opposite edge, so each lands "
                      "flush with the WRONG edge. The failing test asserts one named "
                      "edge lands flush with the near edge (offset = descent) and "
                      "the other flush with the far edge (offset = shortfall + "
                      "descent); the swap gives the OPPOSITE for both, so the "
                      "unpatched routine does NOT resolve — exactly the reported "
                      "bug.",
        "rationale": "REJECT from C1 (`out = alignSpec …`): on the near-edge named "
                     "anchor the rival returns shortfall+descent where alignSpec "
                     "demands descent, differing by the shortfall whenever it is "
                     "nonzero. Refuted at `hd=[(2,3)], extent=some 4, anchor` = the "
                     "near-edge anchor: alignSpec offsets `[3]` (descent), the rival "
                     "`[4-2+3]=[5]`. Varies hd to a single box with a nonzero "
                     "descent and a nonzero shortfall.",
        "witness": _witness("[((2:Rat),(3:Rat))] (some 4)", "bottom"),
    },

    # ---- HIGH-EDGE HALVES THE SHORTFALL: near-miss ----
    {
        "id": "weak-high-edge-halves-shortfall",
        "kind": "uniqueness",
        "expect": "reject",
        # The high-edge anchor uses the CENTRE formula (half the shortfall) instead
        # of the full shortfall, as if the far edge were the midpoint. Agrees with
        # alignSpec on every box with zero shortfall (a box at the extent); diverges
        # by half the shortfall on any shorter box.
        "module": _reject(
            _UPPER,
            "      | .right | .top =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun p => (h - p.1) / 2 + p.2) }"),
        "refinement": "a faithful counterpart that placed the high-edge box at half "
                      "its shortfall plus descent (the centre formula) rather than "
                      "the full shortfall would seat the box at the track midpoint. "
                      "The failing test for the high-edge anchor asserts the offset "
                      "is the FULL shortfall; halving it fails the closeness "
                      "assertion, so the counterpart does NOT resolve.",
        "rationale": "REJECT from C1 (high-edge facet): alignSpec demands "
                     "`h - p.1 + p.2` but the rival gives `(h - p.1)/2 + p.2`, "
                     "differing by half the shortfall whenever it is nonzero. "
                     "Refuted at `hd=[(2,0)], extent=some 4, anchor=right`: "
                     "alignSpec offsets `[4-2+0]=[2]`, the rival `[(4-2)/2+0]=[1]`. "
                     "A near-miss agreeing on zero-shortfall boxes; distinct from "
                     "the group-swap point.",
        "witness": _witness("[((2:Rat),(0:Rat))] (some 4)", "right", rat_div=True),
    },

    # ---- HIGH-EDGE FIRST-BOX ONLY: partial-domain / fence-post ----
    {
        "id": "weak-high-edge-first-box-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # High-edge placement is correct on every box EXCEPT the first, which is
        # forced to 0 (a fence-post bug treating box 0 specially). Correct on the
        # rest of the list and on any first box whose true offset is 0; wrong on a
        # first box with nonzero shortfall or descent.
        "module": _reject(
            _UPPER,
            "      | .right | .top =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0,\n"
            "            offsets := match hd with\n"
            "                       | [] => []\n"
            "                       | _ :: rest => (0 : Rat) :: rest.map (fun p => h - p.1 + p.2) }"),
        "refinement": "a faithful counterpart correct on every box but the first, "
                      "where it emits 0 (a fence-post that treats box 0 as the "
                      "baseline). The failing test checks the placement of EVERY "
                      "box — the first among them, whose true high-edge offset is "
                      "the nonzero shortfall — so its per-box closeness assertion "
                      "fails on element 0 and the counterpart does NOT resolve.",
        "rationale": "REJECT from C1 (every-box facet, index 0): alignSpec places "
                     "box 0 like the rest (`h - p.1 + p.2`), but the rival forces "
                     "it to 0, disagreeing whenever box 0's shortfall+descent is "
                     "nonzero. Refuted at `hd=[(2,0),(4,0)], extent=some 4, "
                     "anchor=top`: alignSpec offsets `[2,0]`, the rival `[0,0]`. "
                     "Varies hd to a length-2 list, discriminating on the FIRST "
                     "element — a distinct facet from the whole-branch rivals.",
        "witness": _witness("[((2:Rat),(0:Rat)), ((4:Rat),(0:Rat))] (some 4)", "top"),
    },

    # ---- LOW-EDGE DROPS THE DESCENT ----
    {
        "id": "weak-low-edge-drops-descent",
        "kind": "uniqueness",
        "expect": "reject",
        # The low-edge anchor returns 0 instead of the box's own descent
        # (collapsing the descent to the baseline). Agrees with alignSpec on every
        # zero-descent box (the F2P geometry has zero descents, so this rival would
        # PASS the failing test narrowly) but diverges on any box with a nonzero
        # descent, which the contract pins for ALL boxes.
        "module": _reject(
            _LOWER,
            "      | .left | .bottom =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun _ => (0 : Rat)) }"),
        "refinement": "a faithful counterpart that emitted a zero offset for every "
                      "low-edge box (dropping the box's own descent) would coincide "
                      "with the fix on the failing test's zero-descent geometry and "
                      "PASS it — but the library layout tests drive nonzero-descent "
                      "boxes (text with descenders) where the low-edge offset must "
                      "equal the descent, so those do NOT resolve. The spec pins ALL "
                      "boxes, not only the zero-descent ones the failing test uses.",
        "rationale": "REJECT from C1 (low-edge facet): alignSpec offsets each "
                     "low-edge box by `p.2` (its descent), but the rival returns 0, "
                     "disagreeing whenever the descent is nonzero. Refuted at "
                     "`hd=[(6,2)], extent=none, anchor=bottom`: alignSpec offsets "
                     "`[2]`, the rival `[0]`. Leaves extent=none (the resolved "
                     "extent's `max` appears only in the equal extent field, not in "
                     "the descent-only discriminating field), so this is the one "
                     "witness varying the extent binder to `none`.",
        "witness": _witness("[((6:Rat),(2:Rat))] none", "bottom"),
    },

    # ---- CENTRE USES THE FULL SHORTFALL ----
    {
        "id": "weak-center-full-shortfall",
        "kind": "uniqueness",
        "expect": "reject",
        # The centre anchor uses the far-edge formula (the full shortfall) instead
        # of half of it. Agrees with alignSpec on every zero-shortfall box; diverges
        # by half the shortfall on any shorter box. Attacks the centre sub-behaviour
        # that no edge rival touches.
        "module": _reject(
            _CENTER,
            "      | .center =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := h, descent := 0, offsets := hd.map (fun p => h - p.1 + p.2) }"),
        "refinement": "a faithful counterpart that placed the centre box at its "
                      "full shortfall plus descent rather than half of it would "
                      "seat every centred box at the far edge. The centre-anchor "
                      "test asserts the offset is HALF the shortfall; using the "
                      "full shortfall doubles it and fails the closeness assertion, "
                      "so the counterpart does NOT resolve.",
        "rationale": "REJECT from C1 (centre facet): alignSpec places each centre "
                     "box at `(h - p.1)/2 + p.2` but the rival at `h - p.1 + p.2`, "
                     "differing by half the shortfall whenever it is nonzero. "
                     "Refuted at `hd=[(2,0)], extent=some 4, anchor=center`: "
                     "alignSpec offsets `[(4-2)/2+0]=[1]`, the rival `[4-2+0]=[2]`. "
                     "Attacks the centre placement no edge rival probes.",
        "witness": _witness("[((2:Rat),(0:Rat))] (some 4)", "center", rat_div=True),
    },

    # ---- BASELINE LEAVES THE PER-BOX OFFSETS AT ITS OWN DESCENT ----
    # ADDED BY AUDIT. The original battery left the baseline anchor with no
    # dedicated rival, on the recorded ground that its branch has "no
    # box-dependent arithmetic to mishandle". That ground is FALSE as written:
    # the branch pins THREE fields, two of which (`extent`, `descent`) are
    # box-dependent reductions over hd, and the offsets field is a per-box
    # constant a rival can trivially replace with a per-box value. The positive
    # controls DEFEND the branch but no rival ATTACKED it, so a wrong baseline
    # placement was unprobed. Measured (this audit): the rival builds exit 1,
    # its witness exits 0 against the rival and 1 with `⊢ False` against the
    # frozen solution — the branch IS attackable on this carrier.
    {
        "id": "weak-baseline-offsets-descent",
        "kind": "uniqueness",
        "expect": "reject",
        # baseline emits each box's own descent instead of a flat 0, and lets
        # that leak into the descent field's companion. Agrees with alignSpec on
        # every zero-descent box (including the whole F2P geometry), diverges on
        # any box with a nonzero descent.
        "module": _reject(
            _BASELINE,
            "      | .baseline =>\n"
            "          let hdesc := listMax (hd.map (fun p => p.1 - p.2))\n"
            "          let desc  := listMax (hd.map (fun p => p.2))\n"
            "          { extent := hdesc + desc, descent := desc, offsets := hd.map (fun p => p.2) }"),
        "refinement": "a faithful counterpart that offset every baseline box by its "
                      "own descent rather than leaving it at 0 would shift each box "
                      "along the aligned axis by its descender depth. The two failing "
                      "tests drive the two named edge anchors, not the baseline "
                      "anchor, so this counterpart does not touch them and does NOT "
                      "resolve them; and it additionally breaks the baseline layouts "
                      "the library's other tests drive with nonzero-descent boxes, "
                      "where every baseline offset must be 0.",
        "rationale": "REJECT from C1 (baseline facet): alignSpec leaves every baseline "
                     "box at offset 0, but the rival emits `p.2`, disagreeing whenever "
                     "any descent is nonzero. Refuted at `hd=[(6,2)], extent=none, "
                     "anchor=baseline`: alignSpec offsets `[0]`, the rival `[2]`. "
                     "Leaves extent=none (baseline ignores the extent binder "
                     "entirely, and the `max` that survives sits only in the equal "
                     "extent/descent fields). Closes the audit-found gap: baseline "
                     "was DEFENDED by the positives but ATTACKED by no rival.",
        "witness": _witness("[((6:Rat),(2:Rat))] none", "baseline"),
    },

    # ---- LOW-EDGE ZEROES THE RETURNED EXTENT ----
    # ADDED BY AUDIT. Every original rival attacks the `offsets` field. C1 pins
    # the whole `Aligned` record, so the `extent` and `descent` fields were
    # unprobed by any rival — a rival that returns the right offsets and the
    # wrong extent was admitted by the battery's coverage, not by the spec.
    # Measured (this audit): rival exit 1, witness exit 0 / gold exit 1 `⊢ False`.
    {
        "id": "weak-low-edge-extent-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct per-box offsets, but the returned extent is 0 instead of the
        # resolved extent. Attacks a FIELD of the result record that no other
        # rival touches; agrees with alignSpec whenever the resolved extent is 0.
        "module": _reject(
            _LOWER,
            "      | .left | .bottom =>\n"
            "          let h := resolvedExtent hd extent\n"
            "          { extent := 0, descent := 0, offsets := hd.map (fun p => p.2) }"),
        "refinement": "a faithful counterpart that returned a zero extent alongside "
                      "correct low-edge offsets would report the packed track as "
                      "having no size. The failing tests read the returned extent as "
                      "well as the per-box offsets (it is what sizes the packed "
                      "artist), so a zero extent fails them for a second, independent "
                      "reason and the counterpart does NOT resolve.",
        "rationale": "REJECT from C1 (the clause pins the WHOLE `Aligned` record, not "
                     "just its offsets): alignSpec returns `extent := "
                     "resolvedExtent hd extent`, the rival returns 0, disagreeing "
                     "whenever the resolved extent is nonzero. Refuted at "
                     "`hd=[(6,2)], extent=some 4, anchor=bottom`: alignSpec extent "
                     "`4`, the rival `0`. This is the only rival probing a "
                     "NON-`offsets` field of the result, and it discriminates at an "
                     "input where the offsets agree — so its rejection is "
                     "attributable to the extent facet alone.",
        "witness": _witness("[((6:Rat),(2:Rat))] (some 4)", "bottom"),
    },

    # ---- BASELINE ZEROES THE RETURNED DESCENT FIELD ----
    # ADDED BY AUDIT 2. Measured on the shipped battery: the `descent :=` RHS is
    # BYTE-IDENTICAL to the frozen one in all seven prior rivals (frozen
    # `['desc','0','0','0']`, every rival `['desc','0','0','0']`), so the only
    # field of the `Aligned` record C1 pins that carried a nonzero value in any
    # branch was never perturbed by any rival. `weak-low-edge-extent-zero`
    # closes the `extent` field and the other six close `offsets`; the packing
    # `descent` — the sole field whose frozen value is a REDUCTION over hd
    # (`listMax (hd.map (fun p => p.2))`) rather than a constant — was admitted
    # by the battery's coverage, not by the spec.
    #
    # The prior port recorded this exact rival as unshippable ("its natural
    # witness point needs the resolved-extent `⊔` in the discriminating field,
    # which does not reduce"). That ground is FALSE, and the tooling claim
    # behind it is too: `decide +kernel` DOES evaluate `Rat` `⊔` in this
    # workspace. Measured (audit 2), variant exit 1; witness rival exit 0 / gold
    # exit 1; and the flipped-claim forgery inverts (gold exit 0 / rival exit 1
    # ``decide proved that the proposition 0 = 2 ⊔ 0 is false``), so the
    # gold-side exit code tracks the claim rather than a carrier limit.
    {
        "id": "weak-baseline-descent-field-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # baseline returns a 0 packing descent instead of the max box descent,
        # keeping the extent and the all-zero offsets correct. Agrees with
        # alignSpec on every all-zero-descent box list (including the whole F2P
        # geometry); diverges as soon as any box has a nonzero descent.
        "module": _reject(
            _BASELINE,
            "      | .baseline =>\n"
            "          let hdesc := listMax (hd.map (fun p => p.1 - p.2))\n"
            "          let desc  := listMax (hd.map (fun p => p.2))\n"
            "          { extent := hdesc + desc, descent := 0, offsets := hd.map (fun _ => (0 : Rat)) }"),
        "refinement": "a faithful counterpart that reported a zero packing descent "
                      "while placing every baseline box correctly would tell the "
                      "caller the packed group has no descender depth. The two "
                      "failing tests drive the two named edge anchors, whose "
                      "descent is 0 in both the desired and this counterpart's "
                      "behaviour, so it does NOT resolve them; and it additionally "
                      "breaks the baseline layouts the library's other tests drive, "
                      "where the returned descent is what the enclosing layout "
                      "stacks the group by, so a zeroed descent misplaces the "
                      "whole packed artist.",
        "rationale": "REJECT from C1 (the `descent` FIELD of the record, which no "
                     "other rival perturbs — measured: every prior rival's "
                     "`descent :=` RHS is byte-identical to the frozen one). "
                     "alignSpec returns `descent := listMax (hd.map (fun p => "
                     "p.2))` on the baseline branch, the rival returns 0, "
                     "disagreeing whenever any box has a nonzero descent. Refuted "
                     "at `hd=[(6,2)], extent=none, anchor=baseline`: alignSpec "
                     "descent `2`, the rival `0`, with the extent and the offsets "
                     "AGREEING at that input — so the rejection is attributable to "
                     "the descent facet alone. This is the only rival whose "
                     "discriminating field is a REDUCTION over hd rather than a "
                     "constant or a per-box formula, which is why its witness "
                     "needs the kernel to evaluate the residual `⊔`.",
        "witness": _witness("[((6:Rat),(2:Rat))] none", "baseline", kernel=True),
    },

    # =====================================================================
    # ADMISSIBILITY — ADDED BY AUDIT. The original battery recorded the nagini
    # admiss-f2p-shaped case as SUBSUMED by the positives, arguing the lone
    # `require hd ≠ []` is non-restrictive and that the positives verifying over
    # the whole domain already witness it. The first half is right and the second
    # is not: a positive verifying says the impl meets C1 under the precondition,
    # which is exactly as true when the post-image is DEGENERATE (constant in the
    # anchor) as when it is not. The residual risk on a total-ish domain is
    # non-degeneracy, and no case discharged it. This one does, in-region.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # In-region `assert` (inside impl-start, elided from the spec view):
        # the precondition is satisfiable at an F2P-shaped input, AND the modeled
        # placement genuinely DISCRIMINATES the two named edge anchors there —
        # the exact contrast the whole battery is about. The impl is kept
        # verbatim so C1 still discharges; the proof gains an arm for the assert.
        "module": _swap(
            _swap(
                _BASE, _IMPL_HEAD,
                "    -- impl-start\n"
                "    assert (with_name_prefix `admiss (\n"
                "      hd ≠ [] ∧\n"
                "      alignSpec [((2:Rat),(0:Rat))] (some 4) Anchor.bottom\n"
                "        ≠ alignSpec [((2:Rat),(0:Rat))] (some 4) Anchor.top))\n"
                "    let result : Aligned :="),
            _PROOF,
            "prove_correct alignOffsets by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (cases anchor <;> rfl)\n"
            "    | simp_all [alignSpec, resolvedExtent, Aligned.mk.injEq,\n"
            "               Rat.sub_def, Rat.add_def, Rat.normalize]\n"),
        "rationale": "ADMISSIBILITY, re-aimed for this carrier. The sole precondition "
                     "`hd ≠ []` is satisfied by an F2P-shaped input (a non-empty box "
                     "list), and — the part the positive controls do NOT establish — "
                     "the post-image is NON-DEGENERATE at that input: `alignSpec` "
                     "returns DIFFERENT records for the two named edge anchors on the "
                     "same boxes, which is the discriminating content C1 exists to "
                     "pin. A spec whose post-image collapsed the two anchors would "
                     "let both a correct and a swapped impl verify, and every "
                     "positive control would still pass. Must verify, else "
                     "PRECOND-TOO-STRONG (or a degenerate post-image). Ports the "
                     "nagini admiss-f2p-shaped, whose half-permission half has no "
                     "counterpart here; the audit found it recorded SUBSUMED on an "
                     "argument that does not cover non-degeneracy.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — ADDED BY AUDIT. Both original positives
    # keep the offset EXPRESSIONS syntactically identical to alignSpec's (one
    # returns alignSpec itself, the other only permutes the arms), so neither
    # tests whether C1 is over-fit to the ARITHMETIC FORM of a placement. This
    # one commutes an addition, which is NOT definitionally equal on `Rat`: the
    # frozen `cases anchor <;> rfl` genuinely fails on it, so the proof is
    # retuned in-region. Measured (this audit): `rfl` and `ring` and `omega`
    # arms all fail; `simp [alignSpec, Rat.add_comm]` closes it, exit 0.
    # =====================================================================
    {
        "id": "pos-commuted-high-edge-sum",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _UPPER,
                "      | .right | .top =>\n"
                "          let h := resolvedExtent hd extent\n"
                "          { extent := h, descent := 0, offsets := hd.map (fun p => p.2 + (h - p.1)) }"),
            _PROOF,
            "prove_correct alignOffsets by\n"
            "  loom_solve\n"
            "  cases anchor <;> simp [alignSpec, Rat.add_comm]"),
        "rationale": "structurally different CORRECT impl whose difference is NOT "
                     "definitional: the high-edge placement is written `p.2 + (h - "
                     "p.1)` where alignSpec writes `h - p.1 + p.2`. Equal in ℚ by "
                     "commutativity but not by `rfl` — measured, the frozen "
                     "`cases anchor <;> rfl` fails on this impl — so verifying it "
                     "requires C1 to hold up to Rat ARITHMETIC rather than up to the "
                     "syntactic form the frozen impl happens to use. Must verify, "
                     "else C1 is over-fit to the spelling of the placement "
                     "expression => SPEC-TOO-STRONG. This is the reshape the two "
                     "original positives do not test (both keep the offset "
                     "expressions byte-identical to alignSpec's).",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (3 soundness
# positives: pos-control-reorder-branches, pos-control-named-slack, echo-honest;
# 1 admissibility: admiss-f2p-shaped; 5 uniqueness rivals: frame-mutation-write-
# heights [MANDATORY], rival-anchor-group-swap, rival-upper-halves-slack,
# rival-partial-domain-first-box, rival-lower-drops-descent) plus 2 AXIOM_TESTS.
# The sibling contracts `aligned_offsets(heights, descents, total, code) ->
# List[int]` — one axis, per-anchor offset, ×2-scaled ints, code in {0,1,2,3}.
# This bundle models the SAME per-anchor placement (`out = alignSpec hd extent
# anchor`) over the richer carrier `List (Rat × Rat)` / `Option Rat` / `Anchor`
# (six named anchors, exact `Rat`), returning the whole `Aligned` record. The
# value surface — which anchor maps to which placement formula, on which box —
# carries across intact; the permission surface does not.
#
#   sibling case (nagini)              -> here                       disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder-branches        -> pos-reorder-branches       PORTED
#   pos-control-named-slack             -> pos-commuted-high-edge-sum  PORTED (audit)
#   echo-honest                         -> pos-direct-alignspec        RE-SHAPED
#   admiss-f2p-shaped                   -> admiss-nondegenerate-f2p-shaped
#                                                                     PORTED (audit)
#   frame-mutation-write-heights (MAND) -> (none)                      VACUOUS
#   rival-anchor-group-swap             -> weak-anchor-group-swap      PORTED
#   rival-upper-halves-slack            -> weak-high-edge-halves-shortfall  PORTED
#   rival-partial-domain-first-box      -> weak-high-edge-first-box-zero    PORTED
#   rival-lower-drops-descent           -> weak-low-edge-drops-descent      PORTED
#   (no sibling counterpart)            -> weak-center-full-shortfall  ADDED
#   (no sibling counterpart)            -> weak-baseline-offsets-descent
#                                                                     ADDED (audit)
#   (no sibling counterpart)            -> weak-low-edge-extent-zero   ADDED (audit)
#   (no sibling counterpart)            -> weak-baseline-descent-field-zero
#                                                                     ADDED (audit 2)
#   AXIOM_TESTS (2)                     -> (none)                      DROPPED (G-AX)
#
# 4 rivals ported + 4 added, 3 positives (1 ported / 1 re-shaped / 1 added by
# audit), 1 admissibility, frame vacuous, axiom lane dropped = 12 SPEC cases
# (3 soundness, 1 admissibility, 8 uniqueness).
#
# AUDIT AMENDMENTS (an independent re-derivation of this port; every claim below
# was re-run with the real verifier rather than argued):
#   * the ORIGINAL 7 cases all reproduce their recorded outcomes — 2 positives
#     exit 0, 5 rivals exit 1, and each of the 5 witnesses exits 0 against its
#     rival and 1 against the frozen solution with `error: unsolved goals ⊢ False`
#     (a SEMANTIC refutation, not a missing identifier / type error / stuck
#     reduction). No original case was neutered, vacuous, or definitionally
#     equal to gold, and every `expect="verify"` case's spec view is
#     byte-identical to the frozen one (sha256 0a42ef88…719f on all cases).
#   * the baseline "no dedicated rival" note was a real GAP, not a sound choice:
#     its stated ground (no box-dependent arithmetic to mishandle) is wrong —
#     the branch pins three fields, two of them reductions over hd. Closed by
#     weak-baseline-offsets-descent.
#   * NO rival probed a non-`offsets` FIELD of the returned record, though C1
#     pins the whole `Aligned`. Closed by weak-low-edge-extent-zero.
#   * the admiss-f2p-shaped SUBSUMED disposition did not cover post-image
#     NON-DEGENERACY (a positive verifies just as happily against a spec that
#     collapsed the two named edge anchors). Closed by
#     admiss-nondegenerate-f2p-shaped.
#   * both original positives keep the offset expressions byte-identical to
#     alignSpec's, so neither tested C1 against a non-definitional reshape.
#     Closed by pos-commuted-high-edge-sum.
#   * SPEC-TOO-WEAK probes that FAILED to find a hole (all rejected as they
#     should be, so no spec hole): baseline descent-field zeroed; baseline
#     offsets<-descent; high-edge extent taken from the first box; high-edge
#     extent recomputed ignoring an explicit `extent`; centre descent field set
#     to the max descent; offsets list reversed; low-edge extent zeroed; centre
#     swapping the pair components. SPEC-TOO-STRONG probes that VERIFIED as they
#     should (so no over-fitting): a named-shortfall local, an `if/else if`
#     dispatch replacing the `match`, and the commuted sum now shipped as a case.
#   * the carrier note on `⊔` is measured-CORRECT: `(2:Rat) ⊔ 0 = 2` is not
#     closed by `simp`, `max_def`, `sup_eq_left`, or `max_eq_left` in this
#     workspace (`simp made no progress`), which is why witnesses whose
#     discriminating field depends on the resolved extent supply a `some` extent.
#     Two audit probes aimed at the `none`-resolved extent were dropped for this
#     reason and are recorded as tooling-limited, not as spec findings.
#
# AUDIT 2 AMENDMENTS (a second independent re-derivation; 60 real builds. Every
# claim below is an exit code observed, not an argument):
#   * ATTACK A (statement integrity) CLEAN: all 11 prior cases' consumer spec
#     views hash sha256 0a42ef88ea1f, byte-identical to the frozen file, and
#     `markers.same_spec` holds for each. No case reformats or weakens the
#     obligation statement; the `require hd ≠ []` / `ensures out = alignSpec hd
#     extent anchor` pair is verbatim in all of them.
#   * ATTACK B/B′ (witness discrimination + FORGERY) CLEAN on all 7 prior
#     rivals. Rebuilt each witness twice (rival exit 0, gold exit 1, gold
#     residual `⊢ False` — a plain evaluation, not a missing identifier, type
#     error, stuck `decide`, or timeout), and additionally ran the flipped-claim
#     forgery on BOTH sides for every one: asserting `=` instead of `≠` VERIFIES
#     on gold (exit 0) and FAILS on the rival (exit 1), the exact inversion of
#     the real witness. So each gold-side exit code demonstrably tracks the
#     claim; none of the 7 is hollow.
#   * ATTACK C (rival wrongness) CLEAN: each of the 7 rivals differs from the
#     frozen impl OBSERVABLY at its own witness point, which the `⊢ False`/exit-0
#     pair on opposite sides proves directly (a definitionally-equal reshape
#     could not make `simp` close the `≠` against it).
#   * The ADMISSIBILITY case is genuinely checked, not decorative — verified by
#     FORGERY rather than by reading it. Two forged variants keeping the impl and
#     proof but weakening the in-region assert both FAIL (exit 1): one asserting
#     the two named edge anchors are EQUAL at the F2P-shaped input, and one
#     asserting `(1:Rat) = 2`. Both leave `case «admiss_1: …» ⊢ False` unsolved,
#     so the assert's content is what the verifier discharges.
#   * ATTACK D found NO spec hole. Eight NEW wrong impls, all correctly REJECTED
#     (exit 1, `Tactic rfl failed` on the frozen proof): high-edge recomputing
#     the extent and ignoring an explicit `some`; centre descent field set to the
#     max descent; baseline extent dropping the descent term; low-edge NEGATING
#     the descent; high-edge swapping the pair components in the shortfall;
#     baseline descent field zeroed; high-edge offsets reversed; centre halving
#     the WHOLE offset (shortfall AND descent) rather than the shortfall alone.
#   * ATTACK E found NO spec hole. Three NEW correct reshapes: `hd.map Prod.snd`
#     for the low-edge offsets VERIFIES with the frozen proof unchanged (exit 0);
#     the baseline extent commuted to `desc + hdesc` VERIFIES with `simp
#     [alignSpec, Rat.add_comm]` (exit 0); the centre written `(h - p.1) * (1/2)
#     + p.2` VERIFIES with `simp [alignSpec, mul_one_div]` (exit 0) — its
#     residual is the true `(x) * (1/2) + b = (x) / 2 + b`, so an earlier failure
#     of mine was a tactic gap, not a spec hole. C1 is not over-fit.
#   * DEFECT FOUND AND FIXED — the `descent` FIELD was unprobed. Measured on the
#     shipped battery: the `descent :=` RHS is byte-identical to the frozen one
#     (`['desc','0','0','0']`) in ALL SEVEN prior rivals. `weak-low-edge-extent-
#     zero` covers `extent` and the other six cover `offsets`, but the one field
#     whose frozen value is a REDUCTION over hd carried no rival. Closed by
#     weak-baseline-descent-field-zero (variant exit 1; witness rival exit 0 /
#     gold exit 1; forgery inverts, gold exit 0 / rival exit 1).
#   * DEFECT FOUND AND FIXED — a FALSE carrier claim. The prior record justified
#     dropping two probes as "tooling-limited" because the resolved-extent `⊔`
#     "does not reduce". `decide +kernel` DOES evaluate it: `(2:Rat) ⊔ 0 = 2` and
#     `listMax [(6:Rat),(2:Rat)] = 6` both close (exit 0) where `simp`,
#     `simp [max_def]`, `rw [sup_eq_left]`, `max_eq_left` and bare `decide` all
#     fail. The claim was wrong on the TOOLING; the fix is the new rival above,
#     whose discriminating field is `⊔`-valued. Corrected in the CARRIER NOTE.
#   * DEFECT FOUND AND FIXED — a FALSE coverage claim. The prior note asserted
#     "EVERY anchor of the six now carries a rival" and that all six anchor values
#     appear among the witness points. Measured, only FIVE distinct anchors appear;
#     `Anchor.left` is a witness point for nothing. The spec coverage is fine (the
#     match arms pair `left` with `bottom`, so the same rival body is wrong at
#     both names) but the prose overstated the evidence. Restated accurately.
#   * The DIVERGENCE lane disposition (nothing to ship) is unchanged and correct,
#     but its stated REASON is corrected. An earlier version attributed it to a
#     velvet-`partial` vacuous-verification hole recorded in an internal findings
#     doc. No velvet bundle is `partial`: all 500 set "total", and the `set_option`
#     elaborator itself runs `openScope `TotalCorrectness`
#     (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the option and the `open`
#     cannot disagree. Under `total` a diverging rival is REJECTED, and nothing
#     ships only because the refusal fires at the `method`, ahead of any appended
#     tester, so no witness can elaborate against the rival.
#
# PORTED (positives): pos-control-reorder-branches ports DIRECTLY as
#   pos-reorder-branches (permute the four `match` arms; each anchor keeps its
#   placement; the frozen `cases anchor <;> rfl` proof still closes).
#   pos-control-named-slack (introduce a `slack = total - h` local and reuse it)
#   ports as pos-commuted-high-edge-sum, added by the audit: the sibling's point
#   is that C1 must not be over-fit to the ARITHMETIC FORM of the placement, and
#   the audit measured that a named-local reshape here is definitionally equal to
#   the frozen impl (the frozen `rfl` proof closes it unchanged), so it tests
#   nothing on this carrier. Commuting the high-edge sum is the reshape that
#   actually carries the sibling's content: it is NOT closed by `rfl` (measured),
#   so verifying it requires C1 to hold up to Rat arithmetic. The audit's
#   named-shortfall probe and an `if/else if` dispatch probe both verified too and
#   are recorded above rather than shipped, being weaker than the case kept.
#   pos-direct-alignspec (the cheapest grounded impl, `return alignSpec hd extent
#   anchor`, whose residual goal closes under `loom_solve` alone) is where the
#   sibling's echo-honest control lands. All verified to build.
# RE-SHAPED (echo-honest): the sibling's echo control asserts, after each append,
#   that the appended value equals the deep model `offset_for(...)` — a redundant
#   in-loop assert demonstrating there is no wrong echo. Here there is no loop and
#   no answer key: `alignSpec` is a concrete def and `return alignSpec …` (the
#   pos-direct control) IS the grounded computation. That control already
#   demonstrates the spec is not echo-vulnerable (any wrong placement fails C1),
#   so a separate echo case would be identical. Folded, not dropped for
#   difficulty.
# PORTED, by the audit (admiss-f2p-shaped): the sibling establishes its four
#   Requires clauses are usable for an F2P-shaped input (two half-permission
#   reads, the parallel-length precondition, a legal code). Only the
#   half-permission half is inexpressible here; the SATISFIABILITY half is not,
#   and the port originally recorded the whole case SUBSUMED on the argument that
#   the positives "verify over the whole required domain, witnessing that
#   `hd ≠ []` admits the modeled inputs". The precondition half of that argument
#   holds. The NON-DEGENERACY half does not: an impl verifying against C1 says
#   nothing about whether the post-image distinguishes anything, because a spec
#   whose `alignSpec` collapsed the two named edge anchors would still be
#   satisfied by the frozen impl and every positive control would still pass. So
#   the residual risk was real and unprobed. admiss-nondegenerate-f2p-shaped
#   discharges it in-region: the precondition holds at an F2P-shaped input AND
#   `alignSpec` returns different records for the two named edge anchors on the
#   same boxes. Measured: exit 0.
# VACUOUS (frame-mutation-write-heights, MANDATORY on nagini): the sibling writes
#   a value-neutral element back into `heights`, held at Acc(list_pred(heights),
#   1/2), to trip INSUFFICIENT PERMISSION before any postcondition is considered.
#   This backend is referentially transparent: `hd` is an immutable value, this
#   bundle declares NO `mut` parameter, there is no heap, no aliasing, and no
#   permission system. There is no read-only input to overwrite and no substitute
#   probe to build, so the class is vacuous (per the porting map, legitimately
#   dropped, not fabricated). Its ARGUMENT (a real patch mutating the caller's
#   box-geometry list would corrupt shared state the layout re-reads) has no value
#   footprint the spec can force here — the placement is read-only by construction
#   (`out = alignSpec hd extent anchor`, a fresh record).
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
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# ADDED (weak-center-full-shortfall): C1 pins a per-anchor placement including the
#   CENTRE branch (half the shortfall). The four ported rivals all attack the
#   low-edge / high-edge groups; without a fifth the centre sub-behaviour would go
#   unattacked (a rival mishandling only the centre placement would verify). This
#   rival closes that gap with a machine-checked witness at anchor=center.
# AXIOM_TESTS (2, dropped): the sibling's ax-deepmodel-sound / ax-deepmodel-
#   containment validate its deep model == the real alignment routine in
#   Docker. That is G-AX's job; this gate ignores AXIOM_TESTS. This bundle
#   consumes no `axiom` and declares no deep-model reference (`alignSpec` is
#   concrete arithmetic over the inputs, validated == the real patched routine by
#   conformance_check.py / G-CONF), so there is nothing here for this gate to
#   probe.
#
# BINDER / CLAUSE COVERAGE. The obligation has three input binders — `hd`,
#   `extent`, `anchor` — and a single top-level clause C1 (`out = alignSpec hd
#   extent anchor`) folding one facet per anchor, an every-box facet, and one
#   facet per FIELD of the returned record. C1 is DEFENDED by the three positive
#   controls (over the whole required domain) plus the admissibility case, and
#   ATTACKED by all seven rivals across the anchor sub-behaviours:
#     - low-edge (descent) placement: weak-low-edge-drops-descent (and the
#       near-edge half of weak-anchor-group-swap);
#     - high-edge (shortfall+descent) placement: weak-high-edge-halves-shortfall,
#       weak-high-edge-first-box-zero (and the far-edge half of the group swap);
#     - centre (half-shortfall) placement: weak-center-full-shortfall;
#     - baseline (all-boxes-at-0) placement: weak-baseline-offsets-descent
#       (added by the audit — this branch previously had no rival);
#     - every-box (not just box 0): weak-high-edge-first-box-zero;
#     - the record's NON-`offsets` fields, which C1 also pins:
#       weak-low-edge-extent-zero (added by the audit — every other rival
#       perturbs only the `offsets` field).
#   Every anchor GROUP of the four (low-edge, high-edge, centre, baseline) now
#   carries a rival, and each rival's wrong branch covers BOTH names in its group
#   (the arms are written `| .left | .bottom =>` and `| .right | .top =>`, one
#   body per pair, so a rival perturbing the body is wrong at both names).
#   CORRECTION (audit 2): an earlier version of this note claimed "every anchor of
#   the six now carries a rival" and that every one of the six anchor values
#   appears among the witness points. Measured, the witness anchors are
#   {bottom, right, top, bottom, center, baseline, bottom, baseline} — FIVE
#   distinct values; `Anchor.left` is refuted at no witness point. That is not a
#   coverage gap in the spec (each rival's wrong body is shared by `left` and
#   `bottom` in the same match arm, so the `left` behaviour is attacked by the
#   same rival that the `bottom` witness refutes), but the prose overstated what
#   the witness POINTS demonstrate, so it is restated accurately here.
#   The eight reject witnesses probe EIGHT DISTINCT input points, varying:
#     * anchor over {bottom, right, top, bottom, center, baseline, bottom,
#       baseline} — five of the six anchor values appear as a witness point;
#       `left` is covered by shared match arms, not by a point of its own;
#     * extent over {some 4, some 4, some 4, none, some 4, none, some 4, none} —
#       the three `none` witnesses (weak-low-edge-drops-descent,
#       weak-baseline-offsets-descent, weak-baseline-descent-field-zero) exercise
#       the resolved-extent path; the first two discriminate on a field where no
#       unreduced `⊔` survives, while the third discriminates ON a `⊔`-valued
#       field and closes it in the kernel (`decide +kernel`), which is the
#       carrier correction audit 2 measured;
#     * hd over lengths {1, 1, 2, 1, 1, 1, 1, 1}, descents {3, 0, 0, 2, 0, 2, 2,
#       2}, and shortfalls {2, 2, {2,0}, 0, 2, n/a, 2, n/a} — so no rival is
#       refuted at a pinned input, both the descent and the shortfall components
#       of the placement are exercised as nonzero somewhere, box 0 vs the whole
#       list are distinguished, and the witness groups that share an anchor are
#       separated by WHICH RESULT FIELD carries the disagreement, so none is a
#       second spelling of another's point:
#         - weak-low-edge-drops-descent (offsets) vs weak-low-edge-extent-zero
#           (extent) share `bottom` but differ in the extent binder AND the field;
#         - weak-baseline-offsets-descent (offsets) vs
#           weak-baseline-descent-field-zero (descent) share `baseline` and the
#           input `hd=[(6,2)], extent=none`, and are separated purely by the
#           FIELD they disagree on — the first leaves the descent field correct,
#           the second leaves the offsets field correct. Together they pin two
#           independent facets of the one branch.
#     * result FIELD over {offsets ×6, extent ×1, descent ×1} — all three fields
#       of the `Aligned` record C1 pins now carry a rival. Before audit 2 the
#       `descent` field carried none (measured: its RHS was byte-identical to
#       frozen in all seven rivals).
# WITNESS DISCRIMINATION (re-derived by the audit with two real builds per reject
#   case — rival exit 0, gold exit 1, and the gold-side error read to confirm it
#   is `unsolved goals ⊢ False` rather than an unknown identifier, a type error,
#   or a stuck `decide`): each witness ELABORATES against its closed-form rival (the
#   `match` reduces to an `Aligned` literal differing from `alignSpec` at the
#   probed box; `simp` with `Aligned.mk.injEq` + the `Rat` field-arithmetic
#   lemmas closes the `≠`) and FAILS against the frozen solution (`alignOffsets`
#   reduces to the SAME literal as `alignSpec`, collapsing the goal to `⊢ False`,
#   which `simp` cannot close). No witness binds a hypothesis (every input is a
#   concrete literal), so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears in any witness.
AXIOM_TESTS = []
