"""properties.py — G-PBT falsification battery for sympy__sympy-18698 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct combineByTag`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against the case's ``witness_reference`` — a loop-free VERIFYING impl of the same
spec. The frozen solution cannot be that subject on this bundle; see the CARRIER
NOTE, which the audit corrected.

DEFENDED SURFACE (one contracted method over a purely-functional core):

  combineByTag (items : List Item) return (out : List Item)
    ensures out = combineAll items                 -- C1: the whole collapse
    ensures (out.map Prod.snd).Nodup               -- C2: each tag once

An ``Item`` is a value (``Content = List Int``, an ordered list of opaque atom
codes) paired with an integer tag. The method collapses the input list by tag:
every distinct tag appears EXACTLY ONCE (in first-encounter order) carrying the
COMBINATION — value concatenation, in input order — of every item that shared
that tag. Both facets are pinned:

  C1 ``out = combineAll items`` is the load-bearing clause. ``combineAll`` is a
     fully-unfolded ``def`` (a ``foldl`` of the transparent ``combineInto``) over
     the method's OWN input — there is NO opaque answer-key oracle (the
     ``axioms`` region is empty), so pinning ``out = combineAll items`` is
     grounded, not an echo. C1 combines two independent sub-obligations:
       (dim-1 / TAG SET)  which tags are reported, each exactly once, in
                          first-encounter order — a rival that fails to collapse
                          items sharing a tag reports too many entries;
       (dim-2 / VALUE)    the value recorded for a tag is the concatenation of
                          EXACTLY the values of that tag's group — a rival that
                          records the wrong value (a member dropped, a spurious
                          atom added, or the tag itself in the value slot) fails.
  C2 ``(out.map Prod.snd).Nodup`` is the structural witness of the collapse:
     after grouping, no tag is listed twice. It is implied by C1 on any correct
     impl (``combineAll`` is tag-unique), so it cannot be violated without also
     violating C1; the one rival that leaves duplicate tags (the no-collapse
     pre-image) violates both.

Both input facets of ``items`` are load-bearing: the tag (``snd``) selects which
group an item joins and drives the reported tag set; the value (``fst``) is the
content concatenated within each group. Every reject witness moves both.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY GOLD IS NOT THE SECOND SUBJECT.
The carrier is FULLY TRANSPARENT (``Item = List Int × Int``), so the reject lane
is expressible by VALUE at concrete literal inputs — no conditioning on an opaque
term is needed. Every rival below is a loop-free straight-line closed form whose
extracted program reduces by kernel computation, so the tester
``combineByTagTester items`` (from ``derive_tester_for combineByTag``) evaluates
to a literal ``Bool`` and each witness closes by ``decide`` at fully-concrete
literal inputs.

The FROZEN impl, however, is a forward ``while`` loop under
``loom.semantics.choice "demonic"``, so its extracted ``combineByTagExec`` does
NOT reduce in the kernel. AUDIT CORRECTION (an earlier revision of this note got
this wrong, and the error mattered): a witness built against the frozen solution
fails with

    Tactic `decide` failed for proposition combineByTagTester [...] = false
    because its `Decidable` instance ... did not reduce to `isTrue` or `isFalse`.
    After unfolding ... reduction got stuck at ... combineByTagPreDecidable

That is a STUCK REDUCTION, not a refutation: the kernel never evaluated the
claim, so the same error appears for a TRUE claim about the frozen impl and
gold's exit code carries NO information. It is exactly the ``witness-undecided``
condition the gate screens for (``gates/pbt.py`` ``_STUCK_REDUCTION``), so
"the witness errors against gold" is NOT the second half of the discriminator
here and must not be cited as one.

What actually discriminates is a DIFFERENT verifying impl of the same spec that
does reduce. Each reject case therefore names an explicit ``witness_reference``:
the ``pos-return-model`` source, which is loop-free (``return combineAll items``),
shares the frozen spec byte-for-byte, and is independently required to VERIFY. An
impl the verifier accepts cannot violate its own spec, so a genuine refutation
must still fail there — and it fails SEMANTICALLY, by deciding the claim false:

    Tactic `decide` proved that the proposition
      combineByTagTester [([1], 5), ([2], 5)] = false
    is false

The reference is stated rather than left to the gate's positives fallback so the
attestation is deterministic and legible from the artifact (``witness_subject``
records which impl each refutation was checked against). AUDIT-MEASURED, per
reject case, with real ``scripts/lean_verify.sh`` builds: witness-vs-rival exit
0 (elaborates), witness-vs-reference exit 1 with the semantic
``decide proved ... is false`` above, witness-vs-gold exit 1 by stuck reduction
(recorded here as the reason gold cannot serve). The carrier at every witness is
concrete, so no hypothesis is assumed and there is no joint-satisfiability
obligation (the gate's consistency probe is ``None`` for all five). No
``sorry``/``admit``/``native_decide``/``axiom`` appears.

ADVERSARIAL READ of the nagini classes on this carrier (full ledger at the foot):
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical correct impls (return the grounded model
    ``combineAll items`` directly with no loop; and the loop with the combined
    accumulator bound to a local before reassigning) must verify, else the spec
    is SPEC-TOO-STRONG on the impl shape.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries THREE
    mandatory frame rivals that WRITE through read-only inputs held at fractional
    heap permission (``Acc(list_pred(.), 1/2)``). Lean and Velvet are
    referentially transparent: ``items`` is an immutable value, this bundle
    declares NO ``mut`` binder, and there is no heap, aliasing, or permission
    system to subvert. No read-only input to overwrite, so the class has no
    carrier analogue; not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``combineAll items`` is a
    fully-unfolded pure function of the method's own argument; there is no
    answer-key term a wrong impl could echo. The cheapest correct impl computes
    the collapse honestly, which a positive control covers.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane, all against C1: each rival
    gets most of the domain right yet diverges on one facet (no collapse at all;
    a group member's value dropped; a spurious atom in every value; the tag
    recorded in the value slot; the last group dropped; the group combined in
    reverse order — the last AUDIT-ADDED, closing the ORDER sub-facet that the
    five ported rivals all left unpinned).
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
    loop in the impl (1 loop here, measure ``items.length - i``). A rival that
    loops without a measure is refused outright (``Decreasing annotations are
    required in total correctness semantics``), and a rival that supplies a
    CONSTANT measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18698"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the ENTIRE frozen loop body (between and INCLUDING
# ---- the markers). Lies wholly inside the single `-- impl-start`/`-- impl-end`
# ---- region and is unique in Solution.lean (asserted at load).
_IMPL = """    -- impl-start
    let mut result : List Item := []
    let mut i := 0
    while i < items.length
      invariant i ≤ items.length
      invariant result = (items.take i).foldl combineStep []
      done_with i = items.length
      decreasing items.length - i
    do
      let e := items[i]!
      result := combineInto result e.1 e.2
      i := i + 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen loop
# ---- body. A positive control that drops the loop retunes it to a bare
# ---- `loom_solve`; both the impl region and the `prove_correct` body are elided
# ---- from the spec view, so same_spec still holds and the `prove_correct
# ---- combineByTag` obligation survives with an identical header. Unique.
_PROOF = """prove_correct combineByTag by
  loom_solve
  case «invariant_2: result = (items.take i).foldl combineStep []» =>
    have hi : i < items.length := by omega
    rw [invariant_2, combineAll_take_step items i hi, combineStep,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  case «ensures_1: (out.map Prod.snd).Nodup» =>
    have h := combineAll_nodup items
    simp_all [combineAll]
  all_goals simp_all [combineAll]"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl_block(body):
    return "    -- impl-start\n" + body + "\n    -- impl-end"


def _rewrite_impl(body):
    """Full variant: impl body replaced, spec + frozen proof left intact. For
    rivals (expected NOT to verify) the frozen tactic script no longer closes the
    reshaped body — which is fine; the rejection is carried by the witness."""
    return _swap(_BASE, _IMPL, _impl_block(body))


def _rewrite_impl_reproved(body, proof):
    """Impl body replaced AND the proof retuned (for loop-free correct reshapes
    whose residual goal no longer needs the loop-step lemma)."""
    return _swap(_rewrite_impl(body), _PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `combineByTagTester items = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict.
def _tester(body):
    return ("extract_program_for combineByTag\n"
            "prove_precondition_decidable_for combineByTag\n"
            "prove_postcondition_decidable_for combineByTag\n"
            "derive_tester_for combineByTag\n\n" + body)


# ---- the witness_reference every reject case is refuted against. IDENTICAL text
# ---- to the `pos-return-model` positive below, so the impl the gate checks as a
# ---- reference is the same impl the battery independently asserts VERIFIES.
# ---- Loop-free (`return combineAll items`), hence kernel-reducible, which is the
# ---- property the frozen forward `while` lacks — see the CARRIER NOTE. Bound once
# ---- and shared so the gate's `_reference_ok` memoisation pays for one build.
_REFERENCE = _rewrite_impl_reproved(
    "    return combineAll items",
    "prove_correct combineByTag by\n  loom_solve")

# The generic proof script used by rivals whose reshape retunes nothing: it keeps
# `loom_solve` and follows with a broad `simp_all` over the model's own
# definitions, so a rival that still fails does so on the residual SEMANTIC goal
# (`... = List.foldl combineStep [] items` / the `Nodup` goal) rather than on a
# frozen case-tag that its shape no longer produces. Used where the frozen
# script's `case «invariant_2: ...»` tag would not exist for a loop-free body.
_GENERIC_PROOF = ("prove_correct combineByTag by\n"
                  "  loom_solve <;>\n"
                  "    simp_all [combineAll, combineStep, combineInto, List.foldl]")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded pure model `combineAll items` directly. `combineAll` is a total
        # function of the input (no opaque answer-key), so this is a correct impl,
        # not an echo. The residual goal is definitional; a bare `loom_solve`
        # closes it (the frozen loop-specific rewrite + Nodup case are not needed
        # — the tactic body is elided from the spec view, so same_spec and the
        # obligation header are untouched).
        "module": _rewrite_impl_reproved(
            "    return combineAll items",
            "prove_correct combineByTag by\n  loom_solve"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`combineAll items` directly (no loop at all — maximally different "
            "from the gold forward `while`). C1 is literally `out = combineAll "
            "items`, so it holds on the whole domain and a bare `loom_solve` "
            "discharges the definitional residual (including C2, since combineAll "
            "is tag-unique). Also the no-ungrounded-echo control: the model IS the "
            "real collapse work, so returning it is correct, not a cheat. Ports "
            "the nagini pos-control-reorder-tail-asserts as the second structurally-"
            "different positive; if it fails => SPEC-TOO-STRONG (over-fit to the "
            "loop shape)."),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Keep the forward loop but bind the combined accumulator to a typed local
        # `r` before reassigning it (a distinct data shape from the inline
        # `result := combineInto result e.1 e.2`). Observationally identical to
        # gold; the frozen proof still closes unchanged (the loop invariant and
        # step lemma are untouched).
        "module": _rewrite_impl(
            "    let mut result : List Item := []\n"
            "    let mut i := 0\n"
            "    while i < items.length\n"
            "      invariant i ≤ items.length\n"
            "      invariant result = (items.take i).foldl combineStep []\n"
            "      done_with i = items.length\n"
            "      decreasing items.length - i\n"
            "    do\n"
            "      let e := items[i]!\n"
            "      let r := combineInto result e.1 e.2\n"
            "      result := r\n"
            "      i := i + 1\n"
            "    return result"),
        "rationale": (
            "structurally-different CORRECT impl: the combined accumulator is bound "
            "to a typed local `r` before reassignment, instead of the inline "
            "`result := combineInto result e.1 e.2`. Same behaviour, different data "
            "shape; the loop invariants are kept verbatim so the frozen proof "
            "closes as-is. Ports the nagini pos-control-rename-acc (a pure local-"
            "variable reshape of the accumulator). Must verify, else the spec is "
            "over-fit to the inline-reassign form => SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-f2p-shaped. That case
    # established the read-only fractional-permission precondition on an
    # F2P-shaped input. This method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude a normal input and
    # the classic "a normal input is admitted" probe is vacuous. Re-aimed at the
    # residual admissibility risk on a total domain: that the two-clause post-image
    # is jointly SATISFIABLE by a gold-shaped computation. The frozen impl
    # discharging both ensures IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the collapse is total over every "
            "item list; the gold impl discharging both ensures is the admissibility "
            "witness that the post-image (C1 plus the tag-uniqueness C2) is jointly "
            "satisfiable. Near-trivial precisely because the precondition is empty. "
            "Re-aimed from the nagini admiss-f2p-shaped, whose fractional-permission "
            "half has no counterpart on this referentially-transparent carrier. "
            "Else SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a loop-free straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test. Each rival's extracted program reduces by kernel
    # computation, so its witness discriminates by value (see the CARRIER NOTE);
    # the frozen spec and obligation header are untouched.
    # =====================================================================
    {
        "id": "r1-no-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change behaviour (== Solution_prepatch): emit every item raw, no
        # tag-keyed collapse. Items sharing a tag stay separate, so the result is
        # the input `items` itself — the reported bug.
        "module": _rewrite_impl("    return items"),
        "refinement": (
            "this is the base-commit behaviour: the collapse tail is absent, so "
            "items that happen to share a tag are reported as separate entries "
            "instead of one combined entry. The failing test supplies a collection "
            "in which two distinct items share a tag and asserts a SINGLE combined "
            "entry (value = the combination of the two); this rival returns the two "
            "raw entries, so the assertion FAILS — it does NOT resolve. This IS the "
            "modeled bug and the prepatch discriminator (G-DIFF). Correct only when "
            "every tag is already unique (a true partial-domain break)."),
        "rationale": (
            "REJECT from BOTH clauses: on any input with a repeated tag, C1 (`out = "
            "combineAll items`) fails (too many entries, uncombined values) and C2 "
            "(tag Nodup) fails (the tag appears twice). If it verified => "
            "SPEC-TOO-WEAK (the collapse is unpinned). Refuted at "
            "items=[([1],5),([2],5)] — two distinct-valued items sharing tag 5: "
            "gold resolves [([1,2],5)], the rival keeps both raw. Ports nagini "
            "prepatch-no-consolidation."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : combineByTagTester [([1], (5:Int)), ([2], (5:Int))] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "r2-first-value-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse the tags correctly (each tag once, first-encounter order,
        # tag-unique) but keep ONLY the FIRST item's value for each tag — never
        # concatenating the rest of the group. C2 holds; C1 dim-2 (value) fails on
        # any tag whose group has >1 member with differing content. The
        # drop-group-member analogue.
        "module": _rewrite_impl(
            "    return items.foldl (fun m e => "
            "if e.2 ∈ m.map Prod.snd then m else m ++ [e]) []"),
        "refinement": (
            "keeps each tag exactly once but records only the FIRST group member's "
            "value, dropping every later member of the same group from the "
            "combination — the analogue of omitting a group member from the "
            "per-group product. The failing test supplies two distinct items "
            "sharing a tag and asserts the combined value; this rival reports only "
            "the first item's value, so the assertion FAILS — it does NOT resolve. "
            "A faithful patch that combined only the first member of each group "
            "would not resolve. Correct on every singleton group (a partial-domain "
            "break, tag set and uniqueness both correct)."),
        "rationale": (
            "REJECT from C1 dim-2 (VALUE): `combineAll` records the concatenation "
            "of a tag's whole group, but this records only the first member's "
            "value, so `out ≠ combineAll items` whenever a group has >1 member with "
            "differing content. C2 (Nodup) HOLDS here, so this isolates the value "
            "sub-obligation. If it verified => SPEC-TOO-WEAK (the group value is "
            "unpinned to its first member). Refuted at "
            "items=[([7],3),([8],3)]: gold resolves [([7,8],3)], the rival "
            "[([7],3)]. Ports nagini partial-domain-drop-group-member."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : combineByTagTester [([7], (3:Int)), ([8], (3:Int))] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "r3-spurious-atom",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct collapse but append a spurious atom code (0) to every combined
        # value — an off-by-one in the merged value (value never equal to
        # value ++ [0]). C1 dim-2 fails on every reported tag; C2 holds.
        "module": _rewrite_impl(
            "    return (combineAll items).map (fun p => (p.1 ++ [0], p.2))"),
        "refinement": (
            "records the correct group value with one spurious atom appended — the "
            "combined value shifted by an extra factor. A patch whose merged value "
            "carried an extra factor would report a value never equal to the true "
            "combination, so the exact-output assertion FAILS — it does NOT "
            "resolve. Correct nowhere on the value (every reported value carries the "
            "spurious atom), so it is refuted even at a single-item input."),
        "rationale": (
            "REJECT from C1 dim-2 (VALUE): `combineAll` pins the value to the exact "
            "group combination, and `value ++ [0] ≠ value`, so `out ≠ combineAll "
            "items` on every non-... reported tag. C2 (Nodup) holds (the tag set is "
            "untouched), isolating the value sub-obligation. If it verified => "
            "SPEC-TOO-WEAK (the value unpinned to within an extra atom). Refuted at "
            "the single-item input items=[([1],9)] — a distinct point (length 1, "
            "no repeated tag) from every other witness: gold resolves [([1],9)], "
            "the rival [([1,0],9)]. Ports nagini value-offby-product."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : combineByTagTester [([1], (9:Int))] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "r4-tag-in-value-slot",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct collapse but record the TAG itself (as a one-atom value [tag])
        # in the value slot instead of the group combination. C1 dim-2 fails
        # whenever the group's true combined value differs from [tag]; C2 holds.
        "module": _rewrite_impl(
            "    return (combineAll items).map (fun p => ([p.2], p.2))"),
        "refinement": (
            "records the TAG in the value slot instead of the group's combined "
            "value — the analogue of reporting the multiplicity where the merged "
            "factor belongs. A patch putting the tag where the combined value "
            "belongs would report the wrong content for every group, so the "
            "exact-output assertion FAILS — it does NOT resolve. Correct on the tag "
            "set and uniqueness; wrong only on the value."),
        "rationale": (
            "REJECT from C1 dim-2 (VALUE): the value must be the group combination, "
            "but this records `[tag]`, so `out ≠ combineAll items` whenever the "
            "true combined value differs from `[tag]`. C2 (Nodup) holds. If it "
            "verified => SPEC-TOO-WEAK (the value slot could carry the tag). "
            "Refuted at items=[([4],2),([5],2)]: gold resolves [([4,5],2)], the "
            "rival [([2],2)]. Ports nagini value-record-multiplicity-not-product."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : combineByTagTester [([4], (2:Int)), ([5], (2:Int))] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "r5-drop-last-group",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (length / tag set): collapse every group correctly but
        # DROP the LAST reported group, returning a list one entry short. Attacks
        # C1 dim-1 (which tags are reported) cleanly — C2 (Nodup) still holds.
        "module": _rewrite_impl("    return (combineAll items).dropLast"),
        "refinement": (
            "collapses every group correctly but omits the final reported group "
            "(an off-by-one over the reported tag set). A patch that dropped the "
            "last combined entry would return a report missing a whole tag's "
            "factor; the exact-output assertion compares the full list, so a "
            "missing final entry FAILS it — it does NOT resolve. Element-wise "
            "correct on every group it DOES emit; the break is purely the dropped "
            "final entry (the tag-set / length facet)."),
        "rationale": (
            "REJECT from C1 dim-1 (TAG SET / length): `combineAll items` has one "
            "entry per distinct tag, but `.dropLast` returns one fewer, so `out ≠ "
            "combineAll items` whenever there is >=1 distinct tag. C2 (Nodup) holds "
            "(dropLast of a nodup list is nodup). If it verified => SPEC-TOO-WEAK "
            "(the reported tag set / result length unpinned). Refuted at "
            "items=[([1],5),([2],6)] — TWO distinct tags (no collapse), a distinct "
            "point from every other witness: gold resolves [([1],5),([2],6)], the "
            "rival [([1],5)] (last entry dropped). ADDED: isolates dim-1 with C2 "
            "intact, where r1 fails dim-1 only jointly with C2."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : combineByTagTester [([1], (5:Int)), ([2], (6:Int))] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "r6-reverse-combine-order",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. Every pre-existing rival attacks WHICH values end up in a
        # group's combination (r2 drops one, r3 adds one, r4 substitutes the tag)
        # or WHICH tags are reported (r1, r5). None attacks the ORDER in which a
        # group's values are combined: each of them is refuted at an input where
        # the correct answer and the reversed-order answer differ in some OTHER
        # way too, so the frozen `acc ++ v` (running combination in first-seen
        # input order) was pinned by no case. This rival changes ONLY that: the
        # group's tag set, its length, its multiset of atoms and C2 are all
        # exactly right, and the combination is assembled `v ++ acc` — the
        # incoming value BEFORE the accumulated one.
        "module": _rewrite_impl_reproved(
            "    return items.foldl (fun mm e =>\n"
            "      if e.2 ∈ mm.map Prod.snd then\n"
            "        mm.map (fun q => if q.2 = e.2 then (e.1 ++ q.1, q.2) else q)\n"
            "      else mm ++ [e]) []",
            _GENERIC_PROOF),
        "refinement": (
            "combines each group in the REVERSE of input order. Because the "
            "combining operation on the real carrier is commutative, this rival's "
            "faithful counterpart would in fact still resolve the failing test — "
            "which is exactly why it is here as a SPEC-STRENGTH probe rather than "
            "as a verify-not-resolve claim. The frozen spec pins the combination "
            "to `acc ++ v` on the FREE MONOID of atom codes, where `++` is NOT "
            "commutative, so the model is strictly stronger than the behaviour the "
            "test grades. Recorded honestly: this case attests that the ordered "
            "combination the model DECLARES is genuinely pinned (a rival that "
            "reverses it is rejected), not that reversing it would break the "
            "repo. The order-insensitivity of the real carrier is the R-leg the "
            "bundle already declares (results compared as a multiset of "
            "(factor, multiplicity) pairs), so no F2P claim is made here."),
        "rationale": (
            "REJECT from C1 dim-2 (VALUE), on the ORDER sub-facet no other rival "
            "moves: `combineAll` records `acc ++ v` (first-seen order) while this "
            "records `v ++ acc`, so `out ≠ combineAll items` whenever a group has "
            ">=2 members with DIFFERENT values. Tag set, length, per-group atom "
            "multiset and C2 (Nodup) are all correct, which is what isolates the "
            "order facet — the residual goals are literally the two `ensures` "
            "(`... = List.foldl combineStep [] items` and the `Nodup` goal), not a "
            "tactic mismatch (AUDIT-MEASURED: the frozen script's "
            "`case «invariant_2: ...»` tag does not exist for a loop-free body, so "
            "this case uses `_GENERIC_PROOF` and its rejection is attributable to "
            "the spec). Refuted at items=[([1],5),([2],5)]: the reference resolves "
            "[([1,2],5)], the rival [([2,1],5)] — same tag, same length, same "
            "atoms, wrong order. If it verified => SPEC-TOO-WEAK (the combination "
            "order unpinned)."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : combineByTagTester [([1], (5:Int)), ([2], (5:Int))] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The nagini sibling ships 10 SPEC cases (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals — three of which are mandatory
# frame-mutation rivals) plus 2 AXIOM_TESTS this gate ignores. The nagini bundle
# contracts TWO functions — `occurs_in(xs, k)` (a membership scan) and
# `consolidate_by_multiplicity(factors, mults)` (the two-loop consolidation) —
# over index-aligned `List[int]` inputs under fractional read-only permissions.
# This velvet bundle models ONLY the purely-functional collapse core as the
# single method `combineByTag` over `List Item` (Item = List Int × Int): the
# tag-keyed grouping that combines the values of items sharing a tag. `occurs_in`
# is not a modeled function here (it is folded into `combineInto`'s membership
# test, an internal detail of the deep model), and the whole permission surface
# is absent (referential transparency). Those carrier facts make the three frame
# rivals and the occurs_in-specific case vacuous, and collapse nagini's two
# consolidation dimensions onto C1's two sub-obligations.
#
#   nagini case                          kind          -> here                     disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-rename-acc               soundness     -> pos-local-reshape         PORTED
#   pos-control-reorder-tail-asserts     soundness     -> pos-return-model          RE-SHAPED
#   admiss-f2p-shaped                    admissibility -> admiss-gold-total          RE-AIMED
#   frame-mutate-readonly-factors        uniqueness    -> (none)                     VACUOUS
#   frame-mutate-readonly-mults          uniqueness    -> (none)                     VACUOUS
#   frame-mutate-readonly-occurs-xs      uniqueness    -> (none)                     VACUOUS (+ occurs_in unmodeled)
#   value-record-multiplicity-not-product uniqueness   -> r4-tag-in-value-slot       PORTED
#   value-offby-product                  uniqueness    -> r3-spurious-atom            PORTED (re-expressed)
#   partial-domain-drop-group-member     uniqueness    -> r2-first-value-only         PORTED (re-expressed)
#   prepatch-no-consolidation            uniqueness    -> r1-no-collapse              PORTED
#   (no sibling)                         uniqueness    -> r5-drop-last-group           ADDED
#   (no sibling)                         uniqueness    -> r6-reverse-combine-order      AUDIT-ADDED
#   AXIOM_TESTS (2)                      axiom         -> (none)                       DROPPED (G-AX lane)
#
# 4 uniqueness ported (two re-expressed) + 2 added; 1 soundness ported + 1
# re-shaped; 1 admissibility re-aimed; 3 frame rivals vacuous; axiom lane dropped.
# 9 SPEC cases (2 soundness, 1 admissibility, 6 uniqueness).
#
# PORTED / RE-SHAPED (positives):
#  * pos-control-rename-acc -> pos-local-reshape. The nagini positive renames the
#    inner accumulator `acc`; on this carrier the faithful accumulator reshape is
#    binding the combined result to a typed local `r` before reassignment. Loop
#    invariants kept verbatim, frozen proof closes.
#  * pos-control-reorder-tail-asserts -> pos-return-model. The nagini positive
#    reorders two terminal book-keeping asserts (no counterpart: this bundle's
#    impl has no tail asserts). Re-shaped to the maximally-different correct impl
#    — return the grounded model `combineAll items` directly, reproved by a bare
#    `loom_solve`. Doubles as the no-ungrounded-echo control.
# RE-AIMED (admiss-f2p-shaped -> admiss-gold-total): the nagini case established
#  the fractional-permission precondition on an F2P-shaped input. This method has
#  NO `require` and no permission surface, so that probe is vacuous; re-aimed at
#  the residual total-domain risk (post-image joint satisfiability), witnessed by
#  the frozen impl discharging both ensures.
# PORTED / RE-EXPRESSED (the four value/tag/length rivals):
#  * prepatch-no-consolidation -> r1-no-collapse (return `items`; the verbatim
#    pre-change behaviour and the G-DIFF discriminator — fails C1 AND C2).
#  * partial-domain-drop-group-member -> r2-first-value-only. Nagini drops the
#    axis-0 contribution from a group's product; here the faithful analogue keeps
#    only the FIRST member's value of each group, dropping the rest — a C1 dim-2
#    (value) attack with C2 intact.
#  * value-offby-product -> r3-spurious-atom. Nagini records `acc + 1`; the value-
#    carrier analogue appends one spurious atom to every combined value (value
#    never equal to value ++ [0]) — a C1 dim-2 attack.
#  * value-record-multiplicity-not-product -> r4-tag-in-value-slot. Nagini records
#    the multiplicity `kk` in the factor slot; the direct analogue records the TAG
#    in the value slot — a C1 dim-2 attack.
# ADDED (r5-drop-last-group): drop the last reported group. Isolates C1 dim-1 (the
#  reported TAG SET / result length) with C2 (Nodup) still holding, where r1
#  fails dim-1 only jointly with C2. A clean near-miss (every emitted group
#  correct), refuted at a two-distinct-tag input no other witness uses.
# AUDIT-ADDED (r6-reverse-combine-order): combine each group in the REVERSE of
#  input order (`v ++ acc` for the frozen `acc ++ v`). The five ported/added
#  rivals above all get the ORDER facet right and diverge elsewhere, so the
#  ordered combination the model declares was pinned by no case; this rival gets
#  the tag set, the length, the per-group atom MULTISET and C2 all exactly right
#  and differs only in the order atoms are assembled. Reported honestly as a
#  spec-strength probe, NOT a verify-not-resolve claim: the real carrier's
#  combining operation is commutative (the bundle's own R-leg compares results as
#  a multiset), so its faithful counterpart would still resolve the F2P test. What
#  it attests is that the free-monoid model's ordered `++` is genuinely pinned —
#  i.e. the spec is strictly STRONGER than the graded behaviour on this facet,
#  which is sound (verify => correct is preserved; only some correct-on-the-repo
#  reshapes are excluded, and the declared refinement is what licenses that).
# VACUOUS (frame-mutate-readonly-factors / -mults / -occurs-xs): the three nagini
#  MANDATORY frame rivals write through read-only inputs held at `Acc(.,1/2)`,
#  rejected by the insufficient-permission check. This backend is referentially
#  transparent: `items` is an immutable value, no `mut` binder is declared, and
#  there is no heap, aliasing, or permission system. No read-only input to
#  overwrite and no frame clause to violate. Additionally the occurs_in frame
#  rival targets a function this bundle does not model at all (occurs_in is folded
#  into `combineInto`'s membership test). Omitted as genuine carrier facts, NOT
#  fabricated (porting map: this class is vacuous on a referentially-transparent
#  backend).
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``items.length - i``). A rival that
#   loops without a measure is refused outright (``Decreasing annotations are
#   required in total correctness semantics``), and a rival that supplies a
#   CONSTANT measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# DROPPED (AXIOM_TESTS): the nagini file's two axiom-soundness/containment probes
#  drive the real stdlib callees (operator.mul / functools.reduce as an
#  A-reference for the value combination, and the dedup==set-keying containment);
#  that is G-AX's job (this bundle reports G-AX skip — the collapse is modeled
#  deeply, mapping.md §1), and the G-PBT gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The frozen spec has two clauses over `items`
#  (whose Item facets are the value `fst` and the tag `snd`):
#    * C1 `out = combineAll items` — attacked on BOTH sub-obligations:
#        dim-1 (TAG SET / which tags, once each): r1 (no collapse), r5 (last group
#          dropped, C2 intact);
#        dim-2 (VALUE / the group combination): r2 (first member only), r3
#          (spurious atom), r4 (tag in the value slot), r6 (right atoms, wrong
#          ORDER — the sub-facet r2/r3/r4 all leave intact).
#    * C2 `(out.map Prod.snd).Nodup` — attacked by r1 (duplicate tags). C2 is
#      implied by C1 on any correct impl (combineAll is tag-unique), so it cannot
#      be violated WITHOUT violating C1; r1 (the no-collapse pre-image) is the
#      rival that leaves duplicate tags. C2 is thus attacked (r1) and defended
#      (both positives + admissibility). Not an unattacked-clause gap.
#  Both Item facets are moved and load-bearing: the TAG (`snd`) drives which group
#  an item joins and the reported tag set (r1, r4, r5 vary tags {5,3,2,6}; r4's
#  value literally depends on the tag); the VALUE (`fst`) is the combined content
#  (r2, r3, r4 turn on the group value; witnesses vary values [1],[2],[7],[8],
#  [4],[5],[1]). The six reject witnesses probe five DISTINCT input points
#  (pts=5; r6 deliberately REUSES r1's point, which is the honest thing here —
#  the order facet needs a group with >=2 differing values, and r1's point is
#  already minimal for that; what distinguishes r6 from r1 is not the input but
#  the RIVAL, which gets the tag set and C2 right where r1 fails both):
#    * r1  [([1],5),([2],5)]        (repeated tag, distinct values)
#    * r2  [([7],3),([8],3)]        (repeated tag, distinct values)
#    * r3  [([1],9)]                (single item, length 1)
#    * r4  [([4],2),([5],2)]        (repeated tag, distinct values)
#    * r5  [([1],5),([2],6)]        (two distinct tags, no collapse)
#    * r6  [([1],5),([2],5)]        (repeated tag — order facet, see above)
#  No binder is pinned at a single value across the reject set; both a collapsing
#  input (repeated tag) and a non-collapsing input (distinct tags / singleton) are
#  probed, and both C1 sub-obligations plus C2 are attacked.
# WITNESS DISCRIMINATION — AUDIT-MEASURED with real builds, and the earlier
#  authoring claim here was WRONG in its second half. Per reject case: the witness
#  ELABORATES against its loop-free rival (exit 0 — the extracted program's result
#  provably violates the ensures at the probed input, `combineByTagTester … =
#  false` closing by `decide`), and FAILS against the `witness_reference`
#  (exit 1) with `Tactic \`decide\` proved that the proposition ... is false` — a
#  SEMANTIC refutation of the concrete claim. Against the FROZEN solution the
#  witness also exits 1, but by STUCK REDUCTION (`did not reduce to \`isTrue\` or
#  \`isFalse\``, stuck at `combineByTagPreDecidable`), because the frozen forward
#  loop under `loom.semantics.choice "demonic"` is not kernel-reducible. That exit
#  code carries NO information — the same error appears for a TRUE claim — so gold
#  is NOT the discriminating subject and the original note's citation of it was a
#  defect the audit repaired (see the CARRIER NOTE). Each case now names the
#  reference explicitly rather than relying on the gate's positives fallback. The
#  carrier is fully concrete at every witness, so each closes by `decide` with no
#  hypothesis and there is no joint-satisfiability obligation (the gate's
#  consistency probe is `None` for all six). No `sorry`/`admit`/`native_decide`/
#  `axiom` appears.
AXIOM_TESTS = []
