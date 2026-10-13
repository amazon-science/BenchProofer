"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7432 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region is changed — which the consumer spec
view elides, so ``markers.same_spec`` holds and the
``prove_correct reportSkipLocation`` obligation survives untouched) and swaps in
a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method over four read-only inputs, whose whole
postcondition is a single equality against a total pure decision function:

  reportSkipLocation (markSkipped xfailReportingOff priorClassification : Bool)
                     (rep : Report) return (out : Report)
    ensures out = fixSkipLocation markSkipped rep

where ``Report`` carries three booleans (``skipped``,
``hasStructuredLocation``, ``locatedAtItem``) and

  fixSkipLocation markSkipped rep =
    if markSkipped && rep.skipped && rep.hasStructuredLocation
    then { rep with locatedAtItem := true } else rep

There is no ``require`` clause, so the admitted domain is total (all 2^6 = 64
input points).

The single ``ensures`` clause is one record equality, but it decomposes into
THREE independently attackable FACETS, because the right-hand side pins every
field of ``out`` and pins the guard exactly:

  (F-fire) ``out.locatedAtItem = true`` on EXACTLY the sub-domain
      ``markSkipped && rep.skipped && rep.hasStructuredLocation``. This is the
      behaviour under spec: a marker-induced skip whose report is recorded
      skipped and carries a structured location record must have its reported
      location point at the test's own definition. Two directions of attack:
      UNDER-FIRE (the correction is suppressed on part of that sub-domain) and
      OVER-FIRE (the correction is applied outside it).
  (F-independence) the right-hand side does NOT mention ``xfailReportingOff`` or
      ``priorClassification`` AT ALL. The correction is owed to every qualifying
      report on its own terms, whatever the expected-failure reporting
      configuration is and whether or not an earlier arm of the report
      classification already handled the report. Any rival whose firing decision
      READS either of those two binders is refutable — this is the load-bearing
      facet for the failing test, and the one whose two binders a careless
      battery would leave pinned.
  (F-frame) ``out.skipped`` and ``out.hasStructuredLocation`` must equal
      ``rep``'s verbatim (the record-update syntax touches only
      ``locatedAtItem``), and on the complement sub-domain ``out = rep`` entirely
      — including ``out.locatedAtItem = rep.locatedAtItem``. The step produces a
      corrected report and alters nothing else it was handed.

BINDER STRUCTURE (read before judging binder coverage). The method binds four
inputs; ``fixSkipLocation`` reads two of them (``markSkipped``, ``rep``) and the
other two (``xfailReportingOff``, ``priorClassification``) are pinned as
IRRELEVANT — a rival that consults either one is wrong precisely because the
spec forbids it. So all four binders are load-bearing for refutation even though
only two appear on the right-hand side, and the ten reject witnesses vary every
one of them: ``markSkipped`` over {true, false}, ``xfailReportingOff`` over
{true, false}, ``priorClassification`` over {true, false}, and ``rep`` over five
distinct field triples, including reports that already have
``locatedAtItem = true`` (so the frame direction is probed, not just the firing
direction). The ten witnesses sit at ten DISTINCT input points; no binder is
held at one value across the battery.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — the PERMISSION half is VACUOUS here. The
    nagini sibling holds the report at full heap permission and reasons about
    which fields the step may write; Lean and Velvet are referentially
    transparent, with no heap, no aliasing and no fractional permissions. The
    four inputs are read-only value binders (none ``mut``). What the nagini
    sibling itself flagged as the VALUE-frame counterpart does port, because the
    frozen postcondition pins the whole output record: see
    ``weak-clobber-location-shape`` and ``weak-clobber-skipped-outcome`` (each
    writes one of the two fields the correction must leave alone) and
    ``weak-uncorrect-on-fire`` (writes the WRONG value into the field it does
    correct). Nothing fabricated for the permission half.
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region declares no ``axiom``.
    The report classification that runs ahead of this step is UNCHANGED and is
    folded into the FREE INPUTS ``rep`` and ``priorClassification`` (mapping.md
    §3); the behaviour under spec is modeled DEEPLY as the total function
    ``fixSkipLocation`` over transparent booleans. There is no opaque answer key
    to echo, so every witness computes by ``decide`` at literal inputs and no
    case needs to condition on the carrier.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
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

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``reportSkipLocationTester markSkipped xfailReportingOff priorClassification rep
= false`` says the extracted program's observable violates the postcondition at
that concrete input. Checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict. Every carrier is ``Bool`` /
a ``Report`` of three ``Bool``s with derived ``DecidableEq``, so every witness
closes by ``decide`` at literal inputs — no hypothesis binders, hence no
satisfiability question to answer. Each of the ten reject witnesses below was run
against BOTH the rival (exit 0) and the frozen solution (exit 1, ``decide``
reporting the proposition FALSE — a SEMANTIC refutation, not a stuck reduction or
an unknown name) with two real builds, and was SEEN to discriminate. The tester
they assert against was separately confirmed to be a two-way oracle rather than
constantly false; see ORACLE INTEGRITY at the foot of this file.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the unchanged
classification ahead of this step is a directive-7 free input and the behaviour
under spec is modeled deeply — no consumed oracle). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7432"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean; both facts are
# ---- asserted at load by _swap, so the manifest breaks loudly if the frozen
# ---- solution ever changes. -------------------------------------------------
_GOLD_IMPL = (
    "    if markSkipped && rep.skipped && rep.hasStructuredLocation then\n"
    "      return { rep with locatedAtItem := true }\n"
    "    else\n"
    "      return rep"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl-region body replaced.

    The frozen `prove_correct reportSkipLocation by loom_solve <;> simp_all
    [fixSkipLocation]` is kept verbatim in EVERY case: the three positive
    controls below all discharge under it unchanged (confirmed with real
    builds), so no case needs to retune the elided proof body and every case is
    trivially attributable to the impl alone.
    """
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped by
# ---- the gate. `reportSkipLocationTester … = false` says the extracted
# ---- program's observable violates the postcondition at that input. No
# ---- `axiom`/`sorry`/`native_decide`, and no hypothesis binders (so nothing to
# ---- be jointly unsatisfiable); the frozen solution rejects each witness.
def _report(skipped, structured, located):
    return ("({ skipped := %s, hasStructuredLocation := %s, "
            "locatedAtItem := %s } : Report)" % (skipped, structured, located))


def _tester(mark, xfail_off, prior, rep):
    return (
        "extract_program_for reportSkipLocation\n"
        "prove_precondition_decidable_for reportSkipLocation\n"
        "prove_postcondition_decidable_for reportSkipLocation\n"
        "derive_tester_for reportSkipLocation\n\n"
        f"example : reportSkipLocationTester {mark} {xfail_off} {prior} {rep}\n"
        "    = false := by\n  decide\n"
    )


# The failing-test scenario, in this carrier's vocabulary: a skip owed to a
# skip/skip-if marker (markSkipped = true), recorded skipped with a structured
# location record that has NOT yet been corrected (rep = ⟨true, true, false⟩),
# under the configuration that switches expected-failure reporting off
# (xfailReportingOff = true) — the configuration under which an earlier
# classification arm consumes the report (priorClassification = true).
_F2P_REP = _report("true", "true", "false")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG on impl shape.
    # Each keeps the byte-identical one-clause obligation AND the frozen
    # `prove_correct` tactic body; all three were confirmed to verify with real
    # builds. Nothing is assumed: no new axiom/theorem/lemma, no `sorry`,
    # `admit` or `native_decide` anywhere.
    # =====================================================================
    {
        "id": "pos-control-single-exit",
        "kind": "soundness",
        "expect": "verify",
        # Single-exit reshape: build the whole corrected report into one typed
        # local through an `if`-expression, then return it once — instead of the
        # gold's two early returns. Observationally identical.
        "module": _impl(
            "    let out := if markSkipped && rep.skipped "
            "&& rep.hasStructuredLocation then\n"
            "        ({ rep with locatedAtItem := true } : Report)\n"
            "      else\n"
            "        rep\n"
            "    return out"),
        "rationale": (
            "a correct single-exit reshape: accumulate the outcome into one "
            "typed local via an `if`-expression and return it once, rather than "
            "the frozen shape's two early returns. The returned record equals "
            "`fixSkipLocation markSkipped rep` at every one of the 64 input "
            "points, so the single `ensures` clause still discharges under the "
            "FROZEN proof script; if a faithful reshape failed to verify the "
            "spec would be SPEC-TOO-STRONG on impl shape rather than on "
            "behaviour. Defends F-fire, F-independence and F-frame together. "
            "(Sibling: pos-minimal — the nagini sibling's cheapest-honest-impl "
            "control; here the frozen impl is ALREADY minimal, since the "
            "location-irrelevant classification chain the sibling drops is not "
            "modeled at all but folded into the free inputs, so the "
            "cheapest-impl control is re-aimed at the exit-shape reshape.)"),
    },
    {
        "id": "pos-control-guard-local",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable reshape: read the three-observation decision into a
        # named boolean local before branching on it.
        "module": _impl(
            "    let correctable := markSkipped && rep.skipped "
            "&& rep.hasStructuredLocation\n"
            "    if correctable then\n"
            "      return { rep with locatedAtItem := true }\n"
            "    else\n"
            "      return rep"),
        "rationale": (
            "the local-variable reshape: read the three-observation firing "
            "decision into a named boolean local, then branch on the local. "
            "Since the inputs are read-only value binders (none `mut`) the local "
            "equals the inline condition at every input, so the correction fires "
            "on exactly the same sub-domain and the one clause discharges under "
            "the FROZEN proof. Must verify. Defends F-fire. (Sibling: "
            "pos-localshape — the sibling reads the structured-location "
            "observation into a local before the write; the same reshape here, "
            "widened to the whole conjunction because this carrier has no "
            "in-place write for the read to race with.)"),
    },
    {
        "id": "pos-control-classification-split",
        "kind": "soundness",
        "expect": "verify",
        # Reorder/duplicate relative to the classification: case-split on
        # `priorClassification` FIRST and apply the identical correction in BOTH
        # arms. Correct precisely BECAUSE the correction is owed independently of
        # how the report was classified — the positive-control mirror of the
        # weak-gate-on-* rivals below.
        "module": _impl(
            "    if priorClassification then\n"
            "      if markSkipped && rep.skipped && rep.hasStructuredLocation then\n"
            "        return { rep with locatedAtItem := true }\n"
            "      else\n"
            "        return rep\n"
            "    else\n"
            "      if markSkipped && rep.skipped && rep.hasStructuredLocation then\n"
            "        return { rep with locatedAtItem := true }\n"
            "      else\n"
            "        return rep"),
        "rationale": (
            "case-split on `priorClassification` up front and apply the "
            "IDENTICAL correction in both arms. This is correct exactly because "
            "the correction is owed on the report's own terms whatever the "
            "classification did — it INSPECTS the classification binder without "
            "letting it change the answer, which is the strongest positive "
            "control for F-independence: it shows the spec forbids DEPENDING on "
            "that binder without forbidding a shape that merely mentions it. "
            "Discharges under the FROZEN proof (confirmed). (Sibling: "
            "pos-reorder — the sibling moves the correction ahead of the "
            "location-irrelevant classification chain to show the ordering is "
            "immaterial; that chain is not modeled here, so the same argument is "
            "carried by splitting on the classification binder instead.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the frozen method declares NO `require` clause, so the
    # usual "a normal input satisfies the precondition" probe is vacuous
    # (nothing could exclude the failing-test-shaped input). Re-aimed at the
    # residual admissibility risk on a total domain: that the post-image is
    # DEGENERATE / trivially met at the points that matter. The case discharges
    # an in-region `assert` pinning BOTH corners as non-degenerate. The assert
    # is LIVE: the same shape with the second conjunct falsified leaves an
    # unsolved goal (confirmed out-of-band), so it cannot pass vacuously.
    # =====================================================================
    {
        "id": "admiss-both-corners-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `adm\n"
            "      (fixSkipLocation true { skipped := true, "
            "hasStructuredLocation := true, locatedAtItem := false }\n"
            "         = { skipped := true, hasStructuredLocation := true, "
            "locatedAtItem := true }\n"
            "       ∧ fixSkipLocation false { skipped := true, "
            "hasStructuredLocation := true, locatedAtItem := false }\n"
            "         = { skipped := true, hasStructuredLocation := true, "
            "locatedAtItem := false }))\n"
            + _GOLD_IMPL),
        "rationale": (
            "the modeled behaviour is non-degenerate at BOTH corners of the "
            "failing-test-shaped input. With a marker-induced skip that is "
            "recorded skipped and carries a structured location record, the step "
            "GENUINELY corrects the location (`locatedAtItem` flips false -> "
            "true, the other two fields untouched); with the same report but the "
            "marker observation absent it GENUINELY leaves the report alone "
            "(`locatedAtItem` stays false). So the post-image is neither "
            "unsatisfiable at that input (else PRECOND-TOO-STRONG — vacuous here "
            "since there is no `require`, hence the re-aim) nor a constant "
            "collapse that any impl meets. The in-region assert must discharge, "
            "and the impl and frozen proof are kept verbatim so "
            "`out = fixSkipLocation markSkipped rep` still discharges too. "
            "(Sibling: admiss-f2p — the sibling self-calls the function on a "
            "freshly built failing-test-shaped report and asserts the corrected "
            "line; here the same two claims are made directly against the pure "
            "decision function, since this carrier has no precondition to "
            "establish and no heap object to construct.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Every rival was confirmed
    # to be REJECTED by a real build (`unsolved goals` on the frozen
    # obligation), and every witness was confirmed to discriminate (elaborates
    # against the rival, `decide` proves the proposition FALSE against gold).
    # Witnesses probe nine DISTINCT input points and vary all four binders.
    # =====================================================================
    {
        "id": "weak-gate-on-classification",
        "kind": "uniqueness",
        "expect": "reject",
        # THE CENTRAL ATTACK (== the pre-image skeleton, Solution_prepatch.lean):
        # make the correction conditional on no earlier classification arm having
        # handled the report. Attacks F-independence through
        # `priorClassification`.
        "module": _impl(
            "    if !priorClassification && (markSkipped && rep.skipped "
            "&& rep.hasStructuredLocation) then\n"
            "      return { rep with locatedAtItem := true }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "this is the pre-image behaviour, and it is exactly what the failing "
            "test observes. Under the configuration that switches "
            "expected-failure reporting off, an earlier arm of the report "
            "classification consumes the report, so a step whose correction is "
            "reachable only when NO earlier arm fired never corrects the "
            "location. The reported skip location then points at a place inside "
            "the framework rather than at the test's own definition, so "
            "`TestXFail::test_xfail_run_with_skip_mark[test_input1-expected1]` — "
            "which runs the reporting summary with that switch given and matches "
            "`SKIPPED [1] test_sample.py:2: unconditional skip` — fails its "
            "`fnmatch_lines` assertion and the instance does NOT resolve. A "
            "rival that verified here would be a true "
            "verify-does-not-imply-resolve break."),
        "rationale": (
            "REJECT from F-independence: `fixSkipLocation markSkipped rep` does "
            "not mention `priorClassification` at all, so at "
            "markSkipped=true, priorClassification=true and "
            "rep=⟨skipped:=true, hasStructuredLocation:=true, "
            "locatedAtItem:=false⟩ the spec demands "
            "`out.locatedAtItem = true` while the rival returns `rep` unchanged. "
            "Refuted at markSkipped=true, xfailReportingOff=true, "
            "priorClassification=true, rep=⟨true,true,false⟩ — the "
            "failing-test-shaped point. (Sibling: rej-prepatch-elif.)"),
        "witness": _tester("true", "true", "true", _F2P_REP),
    },
    {
        "id": "weak-gate-on-xfail-switch",
        "kind": "uniqueness",
        "expect": "reject",
        # The same defect expressed against the OTHER irrelevant binder: gate the
        # correction on the expected-failure reporting switch being ON. A NEAR
        # MISS of the rival above — it agrees with gold wherever
        # priorClassification and xfailReportingOff coincide, so it needs its own
        # distinguishing point (priorClassification=false, xfailReportingOff=true).
        "module": _impl(
            "    if !xfailReportingOff && (markSkipped && rep.skipped "
            "&& rep.hasStructuredLocation) then\n"
            "      return { rep with locatedAtItem := true }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "gating the correction on the expected-failure reporting switch "
            "reproduces the observed defect semantically rather than "
            "structurally: whenever that switch is given the correction never "
            "fires, so the reported skip location for a marker-induced skip "
            "still points inside the framework. That is precisely the "
            "parametrization the failing test adds "
            "(`test_input1-expected1`, the run WITH the switch), so its "
            "`SKIPPED [1] test_sample.py:2:` assertion fails and the instance "
            "does NOT resolve. The switch concerns expected-failure handling "
            "alone and must not reach skip-location reporting at all — a real "
            "patch tying the two together leaves the reported issue unfixed."),
        "rationale": (
            "REJECT from F-independence through the OTHER irrelevant binder: the "
            "right-hand side does not mention `xfailReportingOff`, so with the "
            "switch on and a qualifying report the spec demands the correction "
            "while the rival suppresses it. Refuted at markSkipped=true, "
            "xfailReportingOff=true, priorClassification=FALSE, "
            "rep=⟨true,true,false⟩ — deliberately a different point from "
            "weak-gate-on-classification (which holds priorClassification=true): "
            "these two rivals agree with each other wherever the two binders "
            "coincide, so each is refuted at the point where only ITS binder is "
            "the one being wrongly consulted, and neither shares the other's "
            "witness. Together they show the spec's independence claim is "
            "enforced on BOTH toggles, not just one. (Sibling: "
            "rej-runxfail-guard.)"),
        "witness": _tester("true", "true", "false", _F2P_REP),
    },
    {
        "id": "weak-overfire-drop-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-FIRE on F-fire: drop the marker observation from the firing
        # decision, so the location is corrected for skips that did NOT come from
        # a skip/skip-if marker.
        "module": _impl(
            "    if rep.skipped && rep.hasStructuredLocation then\n"
            "      return { rep with locatedAtItem := true }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "dropping the marker observation corrects the reported location for "
            "every skipped report carrying a structured location record, "
            "including skips raised imperatively from inside the framework "
            "rather than owed to a skip/skip-if marker. Those skips are "
            "legitimately reported at the place that produced them; rewriting "
            "their location to the test definition moves it to the wrong line, "
            "so the skip-reporting tests in the 77-test PASS_TO_PASS set (the "
            "imperative-skip and reason-reporting cases) start failing and the "
            "instance does NOT resolve — a real patch that over-corrects trades "
            "one wrong location for another."),
        "rationale": (
            "REJECT from F-fire in the OVER-FIRE direction: with markSkipped= "
            "false the guard `markSkipped && …` is false, so the spec pins "
            "`out = rep` (in particular `out.locatedAtItem = false`), yet the "
            "rival corrects the location. Refuted at markSkipped=FALSE, "
            "xfailReportingOff=false, priorClassification=false, "
            "rep=⟨true,true,false⟩ — the only witness in the battery that holds "
            "markSkipped=false with BOTH irrelevant binders also false, so the "
            "marker binder is varied independently of them "
            "(weak-clobber-location-shape is the other witness with both "
            "irrelevant binders false, but it holds markSkipped=true). "
            "(Sibling: rej-overfire.)"),
        "witness": _tester("false", "false", "false", _F2P_REP),
    },
    {
        "id": "weak-overfire-drop-skipped",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-FIRE at the SECOND conjunct: drop the recorded-skipped
        # observation. The only witness that moves `rep.skipped` off `true`
        # while the other two firing observations still qualify the report.
        "module": _impl(
            "    if markSkipped && rep.hasStructuredLocation then\n"
            "      return { rep with locatedAtItem := true }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "dropping the recorded-skipped observation corrects the location of "
            "reports that are NOT skip outcomes at all — a marked test that "
            "actually ran and failed, or one whose outcome an earlier "
            "classification arm rewrote away from skipped, still carries the "
            "marker but must keep the location the classification produced. A "
            "real patch omitting that check rewrites the location component of "
            "non-skip reports, misplacing failure locations in the reporting "
            "summary, so the PASS_TO_PASS reporting tests over marked tests that "
            "run and fail break and the instance does NOT resolve."),
        "rationale": (
            "REJECT from F-fire in the OVER-FIRE direction at the "
            "recorded-skipped conjunct: with rep.skipped=false the guard is "
            "false so the spec pins `out = rep`, yet the rival corrects the "
            "location. This is a NEAR MISS of weak-overfire-drop-marker — the "
            "two agree except exactly where the marker and skipped observations "
            "disagree — so it gets its own point: markSkipped=true, "
            "xfailReportingOff=false, priorClassification=true, "
            "rep=⟨skipped:=FALSE, hasStructuredLocation:=true, "
            "locatedAtItem:=false⟩. This is the only witness that moves "
            "`rep.skipped` off true while the OTHER two firing observations "
            "still qualify the report, so it isolates that conjunct: "
            "weak-correct-unconditionally also carries rep.skipped=false, but "
            "with hasStructuredLocation=false as well, so it cannot attribute a "
            "rejection to the recorded-skipped observation alone. Without this "
            "case a rival mishandling that observation alone would go "
            "unnoticed. (Sibling: rej-overfire, "
            "carried to the second conjunct of the firing decision — the nagini "
            "sibling attacks only the marker conjunct, and this carrier splits "
            "the report's observations into separately-addressable fields of "
            "`Report`, so each conjunct needs its own rival for the binder to be "
            "discriminated.)"),
        "witness": _tester("true", "false", "true",
                           _report("false", "true", "false")),
    },
    {
        "id": "weak-overfire-drop-structured",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-FIRE at the THIRD conjunct: drop the structured-location
        # observation. The only witness that moves `rep.hasStructuredLocation`
        # off `true` while the other two firing observations still qualify.
        "module": _impl(
            "    if markSkipped && rep.skipped then\n"
            "      return { rep with locatedAtItem := true }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "dropping the structured-location observation claims the location "
            "was corrected for reports whose long-form representation is NOT the "
            "structured (file, line, reason) record — a plain string, an absent "
            "representation, or an exception rendering. Those shapes carry no "
            "location component to rewrite; a real patch that attempts the "
            "rewrite unconditionally either corrupts the representation or "
            "raises while building the reporting summary, so the "
            "skip-without-a-structured-representation cases in PASS_TO_PASS "
            "break and the instance does NOT resolve."),
        "rationale": (
            "REJECT from F-fire in the OVER-FIRE direction at the "
            "structured-location conjunct: with rep.hasStructuredLocation=false "
            "the guard is false so the spec pins `out = rep`, yet the rival "
            "claims the location was corrected. Refuted at markSkipped=true, "
            "xfailReportingOff=true, priorClassification=false, "
            "rep=⟨skipped:=true, hasStructuredLocation:=FALSE, "
            "locatedAtItem:=false⟩ — the only witness moving that observation "
            "off true while the other two firing observations still qualify the "
            "report (weak-correct-unconditionally also carries "
            "hasStructuredLocation=false, but with rep.skipped=false too, so it "
            "cannot isolate this conjunct), and a different point from both "
            "other over-fire rivals "
            "(each of the three keeps the other two conjuncts satisfied, so each "
            "is refuted only where ITS conjunct is the one wrongly ignored). "
            "(Sibling: rej-overfire, carried to the third conjunct.)"),
        "witness": _tester("true", "true", "false",
                           _report("true", "false", "false")),
    },
    {
        "id": "weak-clobber-location-shape",
        "kind": "uniqueness",
        "expect": "reject",
        # F-frame: corrects the location correctly, but ALSO overwrites the
        # structured-location observation on the way. The value-frame analogue of
        # the sibling's frame-mutation case.
        "module": _impl(
            "    if markSkipped && rep.skipped && rep.hasStructuredLocation then\n"
            "      return { rep with locatedAtItem := true, "
            "hasStructuredLocation := false }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "correcting the location while also flipping the recorded "
            "representation SHAPE is not a location correction — downstream "
            "reporting selects how to render a skip from that shape, so a real "
            "patch that clears it renders the corrected skip line in the wrong "
            "form. The failing test matches the summary line "
            "`SKIPPED [1] test_sample.py:2: unconditional skip` literally, and a "
            "report no longer presenting as a structured (file, line, reason) "
            "record does not produce that line at all — so the failing test "
            "still fails, and the PASS_TO_PASS reason-reporting and "
            "skip-folding cases break as well. Does NOT resolve."),
        "rationale": (
            "REJECT from F-frame: `fixSkipLocation` is a record update touching "
            "ONLY `locatedAtItem`, so the clause pins "
            "`out.hasStructuredLocation = rep.hasStructuredLocation`; the rival "
            "clears it. This is the VALUE-frame counterpart the nagini sibling "
            "flagged — with no heap and no fractional permissions there is no "
            "permission error to commit, but the frozen postcondition pins the "
            "whole output record, so writing a field the correction must leave "
            "alone is refutable. Refuted at markSkipped=true, "
            "xfailReportingOff=false, priorClassification=false, "
            "rep=⟨true,true,TRUE⟩ — a report already located at the test "
            "definition, so the `locatedAtItem` facet is satisfied and the "
            "rejection is attributable to the frame facet ALONE, not to a firing "
            "disagreement. (Sibling: rej-frame-mutation.)"),
        "witness": _tester("true", "false", "false",
                           _report("true", "true", "true")),
    },
    {
        "id": "weak-clobber-skipped-outcome",
        "kind": "uniqueness",
        "expect": "reject",
        # F-frame at the OTHER framed field. Added by audit: every other rival
        # leaves `out.skipped = rep.skipped`, so before this case the frame facet
        # was demonstrated on `hasStructuredLocation` only and a rival clearing
        # the recorded-skipped observation on the way past was unattacked.
        "module": _impl(
            "    if markSkipped && rep.skipped && rep.hasStructuredLocation then\n"
            "      return { rep with locatedAtItem := true, skipped := false }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "correcting the location while also clearing the recorded-skipped "
            "observation does not just relocate the report, it changes what "
            "OUTCOME the report records — the corrected report no longer presents "
            "as a skip at all. The failing test matches a line in the "
            "short-test-summary that is emitted only for reports still counted as "
            "skips (`SKIPPED [1] test_sample.py:2: unconditional skip`), so a real "
            "patch that clears the outcome on the way past drops the report out of "
            "that summary section entirely: the failing test still fails, and the "
            "PASS_TO_PASS skip-counting and skip-folding cases break too. Does "
            "NOT resolve."),
        "rationale": (
            "REJECT from F-frame at the field the OTHER frame rival leaves alone: "
            "`fixSkipLocation` is a record update touching ONLY `locatedAtItem`, "
            "so the clause equally pins `out.skipped = rep.skipped`, and this "
            "rival clears it. Refuted at markSkipped=true, xfailReportingOff=true, "
            "priorClassification=true, rep=⟨true,true,TRUE⟩ — an already-located "
            "report, so the `locatedAtItem` facet is satisfied and the rejection "
            "is attributable to the frame facet on `skipped` ALONE. A tenth "
            "DISTINCT input point (the only witness holding all three of "
            "markSkipped, xfailReportingOff and priorClassification true). Added "
            "by the audit lane: the nine ported rivals all agree with gold on "
            "`out.skipped`, so the frame facet was demonstrated on "
            "`hasStructuredLocation` only. Confirmed with three real builds — the "
            "rival is rejected on the frozen obligation (`unsolved goals`), the "
            "witness elaborates against it (exit 0) and `decide` proves the "
            "proposition false against the frozen solution (exit 1). (Sibling: "
            "rej-frame-mutation, carried to the second framed field — the nagini "
            "sibling's report exposes only the shape flag and the line number, so "
            "its frame clause (P1) has a single field to attack, while this "
            "carrier's `Report` frames two.)"),
        "witness": _tester("true", "true", "true",
                           _report("true", "true", "true")),
    },
    {
        "id": "weak-uncorrect-on-fire",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-level: fires on exactly the right sub-domain but writes the WRONG
        # value into the field it corrects. The Bool-carrier analogue of the
        # sibling's off-by-one.
        "module": _impl(
            "    if markSkipped && rep.skipped && rep.hasStructuredLocation then\n"
            "      return { rep with locatedAtItem := false }\n"
            "    else\n"
            "      return rep"),
        "refinement": (
            "firing on exactly the right reports but writing the WRONG location "
            "into them is the value-level defect: the corrected report is made "
            "to point somewhere other than the test's own definition. The "
            "failing test asserts the definition location literally "
            "(`test_sample.py:2`), so a location that is merely rewritten rather "
            "than rewritten TO the definition fails the same assertion the "
            "unfixed behaviour fails, and the instance does NOT resolve. "
            "Recognising the right reports is not sufficient — the value stored "
            "has to be the right one."),
        "rationale": (
            "REJECT from F-fire on the value axis: on the firing sub-domain the "
            "clause pins `out.locatedAtItem = true`, and the rival stores false. "
            "It is refutable across the WHOLE firing sub-domain — including "
            "reports arriving with `locatedAtItem = false`, where the rival "
            "returns ⟨true,true,false⟩ against the spec's demanded "
            "⟨true,true,true⟩ (verified with a real build at markSkipped=true, "
            "xfailReportingOff=false, priorClassification=true, "
            "rep=⟨true,true,false⟩: the witness elaborates against the rival and "
            "`decide` proves it false against gold). The witness is nonetheless "
            "placed at a report that arrives ALREADY located — markSkipped=true, "
            "xfailReportingOff=false, priorClassification=true, "
            "rep=⟨true,true,TRUE⟩ — so that the rival's disagreement with gold is "
            "a pure value-axis one (gold leaves the field at true and the rival "
            "actively clears it) rather than one confounded with the report "
            "simply never having been corrected. That is a different point from "
            "weak-clobber-location-shape (which holds priorClassification=false) "
            "and from every other witness. (Sibling: rej-offbyone, "
            "re-expressed: the sibling stores the definition line without its "
            "`+ 1`, pinning a wrong NUMERIC location; this carrier abstracts the "
            "location to WHETHER it is the test's own definition, so the "
            "off-by-one becomes storing the wrong boolean at the right time.)"),
        "witness": _tester("true", "false", "true",
                           _report("true", "true", "true")),
    },
    {
        "id": "weak-correct-unconditionally",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-FIRE, maximal: correct every report, whatever it is.
        "module": _impl("    return { rep with locatedAtItem := true }"),
        "refinement": (
            "claiming the location was corrected for EVERY report — passed, "
            "failed, expected-failure, unexpectedly-passing, imperatively "
            "skipped — corrects the marker-induced skips but clobbers the "
            "location of everything else. The step is owed the correction only "
            "on its own narrow sub-domain; a real patch that rewrites every "
            "report's location scrambles unrelated reports throughout the "
            "reporting summary, breaking the bulk of the 77-test PASS_TO_PASS "
            "set (the expected-failure, unexpected-pass and failure-reporting "
            "cases). Does NOT resolve."),
        "rationale": (
            "REJECT from F-fire in the OVER-FIRE direction with the guard gone "
            "entirely: off the firing sub-domain the clause pins `out = rep`, "
            "and this rival always writes `locatedAtItem := true`. Refuted at "
            "markSkipped=false, xfailReportingOff=true, priorClassification="
            "true, rep=⟨FALSE,FALSE,false⟩ — the all-negative report, a corner "
            "no other witness visits (it is the only witness with both report "
            "observations false), so the guard's total absence is demonstrated "
            "at a point where nothing about the report qualifies it. (Sibling: "
            "rej-touch-else.)"),
        "witness": _tester("false", "true", "true",
                           _report("false", "false", "false")),
    },
    {
        "id": "weak-never-correct",
        "kind": "uniqueness",
        "expect": "reject",
        # UNDER-FIRE, maximal: hand the report back untouched, always. Cheap
        # supporting case; still carries its refinement.
        "module": _impl("    return rep"),
        "refinement": (
            "handing every report back untouched never corrects any skip "
            "location, so a marker-induced skip is always reported at the place "
            "inside the framework that produced it rather than at the test's own "
            "definition. Both parametrizations of the reporting test then fail "
            "their `SKIPPED [1] test_sample.py:2:` assertion — including the one "
            "in PASS_TO_PASS that already passed before the change — so the "
            "instance does NOT resolve. Cheap supporting case; the "
            "classification-independence and per-conjunct attacks above are the "
            "primary battery."),
        "rationale": (
            "REJECT from F-fire in the UNDER-FIRE direction: on the firing "
            "sub-domain the clause demands `out.locatedAtItem = true` and the "
            "rival leaves `rep.locatedAtItem`. Refuted at markSkipped=true, "
            "xfailReportingOff=FALSE, priorClassification=true, "
            "rep=⟨true,true,false⟩ — deliberately with the expected-failure "
            "switch OFF, so this rival is caught on the sub-domain where "
            "weak-gate-on-xfail-switch is CORRECT (that rival consults the "
            "switch, which is off here, so it fires exactly as gold does): the "
            "correction is owed even when nothing about the CONFIGURATION is "
            "unusual. Note this point does NOT separate this rival from "
            "weak-gate-on-classification, which is also refuted here "
            "(priorClassification=true suppresses its correction too, confirmed "
            "with a real build, exit 0); the point that isolates the two gate-on "
            "rivals from each other is each one's own witness. (Sibling: "
            "rej-noop.)"),
        "witness": _tester("true", "false", "true", _F2P_REP),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 11 SPEC cases (3 soundness
# positives, 1 admissibility, 7 uniqueness rivals) and an EMPTY axiom lane, and
# contracts a void step over EIGHT scalar parameters — a WRITABLE report object
# carrying a boolean shape flag and an INTEGER line number, a definition-line
# number, the marker and recorded-skip observations, and four separate booleans
# for the individual outcome-classification arms — with three postcondition
# clauses (a shape frame, an implication pinning the corrected line to the
# definition line plus one, and its frame complement).
#
# THIS bundle models a narrower and more transparent surface: one method, one
# `ensures` clause, `out = fixSkipLocation markSkipped rep`, over four read-only
# boolean/record binders. Three differences drive the whole port:
#
#   * The sibling's LINE NUMBER (an Int pinned to `definition_line + 1`) is
#     abstracted here to the single boolean `locatedAtItem` — WHETHER the
#     reported location is the test's own definition (mapping.md §2). So the
#     sibling's arithmetic attack has a boolean counterpart, not none.
#   * The sibling's four outcome-classification booleans
#     (`unexpected_success`, `xfail_exception`, `xfailed_present`, and the
#     not-skipped combination) are folded here into the SINGLE free input
#     `priorClassification` — "some earlier arm handled this report" —
#     because the classification is unchanged and the spec makes no claim about
#     it (mapping.md §3). Rivals attacking individual arms therefore collapse
#     onto one rival attacking that binder.
#   * The sibling's `rep` is a mutable heap object; here it is an immutable
#     record and the whole post-state is pinned by one equality, so the frame
#     clauses (P1)/(P3) are not separate `ensures` lines but facets of that
#     equality — still separately attackable, which is why the frame and
#     value-level rivals both port.
#
# Every sibling case is accounted for below.
#
#   sibling case (nagini)      -> here
#   ---------------------------------------------------------------------------
#   pos-reorder                -> pos-control-classification-split   RE-AIMED
#   pos-minimal                -> pos-control-single-exit            RE-AIMED
#   pos-localshape             -> pos-control-guard-local            PORTED
#   admiss-f2p                 -> admiss-both-corners-nondegenerate  RE-AIMED
#   rej-prepatch-elif          -> weak-gate-on-classification       PORTED (central)
#   rej-runxfail-guard         -> weak-gate-on-xfail-switch          PORTED
#   rej-offbyone               -> weak-uncorrect-on-fire             RE-EXPRESSED
#   rej-frame-mutation         -> weak-clobber-location-shape        RE-EXPRESSED
#                               + weak-clobber-skipped-outcome       WIDENED (audit)
#   rej-overfire               -> weak-overfire-drop-marker          PORTED
#                               + weak-overfire-drop-skipped         WIDENED
#                               + weak-overfire-drop-structured      WIDENED
#   rej-touch-else             -> weak-correct-unconditionally       PORTED
#   rej-noop                   -> weak-never-correct                 PORTED
#   AXIOM_TESTS (0)            -> (none)                             N/A, already empty
#
# PORTED (the two gate-on rivals): the sibling's central attack restores the
#   pre-image control flow so the correction hangs off the classification chain
#   and is suppressed when an earlier arm fires; here that is
#   `weak-gate-on-classification`, gating on `!priorClassification` (and it is
#   byte-for-byte the impl of the bundle's own Solution_prepatch.lean).
#   `rej-runxfail-guard` expresses the same defect as a guard on the
#   expected-failure reporting switch; here that is `weak-gate-on-xfail-switch`.
#   The sibling lets both share the failing-test input; here they do NOT share a
#   witness, because they are near-misses of each other that agree wherever the
#   two binders coincide — each is refuted at the point where only ITS binder is
#   wrongly consulted, which is what makes the manifest demonstrate the
#   sub-domain each rationale claims.
# RE-EXPRESSED (rej-offbyone -> weak-uncorrect-on-fire): the sibling stores
#   `definition_line` instead of `definition_line + 1`, a wrong NUMERIC location
#   at the right time. This carrier abstracts the location to a boolean, so the
#   arithmetic off-by-one has no numeral to be off by; the surviving content of
#   the attack — fire on exactly the right reports but store the wrong value —
#   is `locatedAtItem := false` on the firing sub-domain. It is refutable across
#   that WHOLE sub-domain (measured: also at `rep.locatedAtItem = false`, where
#   the rival returns the report uncorrected against the spec's demanded
#   correction); its witness is placed at a report that ARRIVES already located so
#   that the disagreement is a pure value-axis one — gold leaves the field true and
#   the rival actively clears it — rather than one confounded with the report never
#   having been corrected at all.
# RE-EXPRESSED + WIDENED (rej-frame-mutation -> two rivals): the sibling writes the
#   shape flag alongside the line and is caught by the explicit shape frame (P1).
#   Here the single equality pins every field of the output record, so overwriting
#   a framed field is refuted by that clause's frame facet. The sibling's report
#   exposes only the shape flag and the line, so (P1) has ONE field to attack;
#   this carrier's `Report` frames TWO (`hasStructuredLocation` and `skipped`), and
#   the nine originally-ported rivals all agree with gold on `out.skipped`, so the
#   frame facet was demonstrated on one field only. The audit lane added
#   `weak-clobber-skipped-outcome` for the other. Both witnesses sit at an
#   already-located report so the firing facet is satisfied and each rejection is
#   attributable to the frame facet on its own field alone.
# WIDENED (rej-overfire -> three rivals): the sibling drops the marker conjunct
#   only. The firing decision has THREE conjuncts, and on this carrier the other
#   two are separately-addressable fields of the `Report` record rather than
#   separate scalar parameters, so a rival mishandling only `rep.skipped` or only
#   `rep.hasStructuredLocation` would verify unless each conjunct gets its own
#   rival AND its own witness. `weak-overfire-drop-skipped` is the only witness
#   that moves `rep.skipped` off true while the other two firing observations still
#   qualify the report, and `weak-overfire-drop-structured` the only one that moves
#   `rep.hasStructuredLocation` off true on the same terms — so each isolates its
#   own conjunct. (`weak-correct-unconditionally` carries both of those
#   observations false at once, which is why it cannot attribute a rejection to
#   either conjunct individually.) These are the same
#   attack CLASS as the sibling's, carried to the conjuncts the sibling left
#   untested — added for binder discrimination, not invented as new adversarial
#   content.
# RE-AIMED (positives): `pos-minimal` drops the sibling's all-`pass` outcome
#   chain, and `pos-reorder` moves the correction ahead of it — but that chain is
#   NOT MODELED here (it is folded into the free inputs), so the frozen impl is
#   already minimal and there is no chain to reorder against. The two arguments
#   are carried by `pos-control-single-exit` (collapse to one typed local and one
#   exit) and `pos-control-classification-split` (case-split on the
#   classification binder and apply the identical correction in both arms — the
#   positive mirror of F-independence: the spec forbids DEPENDING on that binder,
#   not MENTIONING it). `pos-localshape` ports directly as
#   `pos-control-guard-local`. All three discharge under the FROZEN proof body,
#   so no case retunes the elided proof and every case is attributable to the
#   impl region alone.
# RE-AIMED (admiss-f2p): the sibling self-calls the function on a freshly
#   constructed failing-test-shaped report and asserts the corrected line and the
#   preserved shape, establishing that a normal input satisfies the `Requires`.
#   This method declares NO `require` clause, so that probe is vacuous — nothing
#   could exclude the input. It is re-aimed at the residual total-domain risk (a
#   degenerate / trivially-met post-image) by an in-region assert that both
#   corners are non-degenerate: a genuine correction at the qualifying report and
#   a genuine no-op at the same report without the marker observation. The assert
#   is LIVE — falsifying its second conjunct leaves an unsolved goal (confirmed
#   out-of-band) — and the impl plus frozen proof are kept verbatim so the
#   method's own obligation discharges too.
# N/A (AXIOM_TESTS): the sibling's axiom lane is already EMPTY (no
#   `@ContractOnly` callees, no deep-model references) and so is this bundle's
#   `axioms` region. Nothing to drop and nothing to probe; the axiom lane is
#   G-AX's job and this gate ignores AXIOM_TESTS regardless.
#
# FRAME / PERMISSION-MUTATION: the PERMISSION half is VACUOUS on this carrier.
#   Lean and Velvet are referentially transparent — no heap, no aliasing, no
#   fractional permissions — and all four inputs are read-only value binders
#   (none `mut`). The sibling itself records the permission attack as
#   inapplicable even on nagini (the report is held at FULL permission because
#   the step is supposed to write it, and there is no `Acc(.,1/2)` read-only
#   field to overwrite) and ships the VALUE-frame counterpart instead. That
#   counterpart is what ports, three times over: weak-clobber-location-shape and
#   weak-clobber-skipped-outcome (each writes one of the two fields the correction
#   must leave alone) and weak-uncorrect-on-fire (write the wrong value into the
#   field it does correct). No substitute was fabricated for the permission half.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
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
#
# BINDER / CLAUSE / POINT COVERAGE. All three facets of the single `ensures`
#   clause are attacked and defended. F-fire is attacked in the UNDER-FIRE
#   direction by weak-never-correct and (per-binder) by the two gate-on rivals,
#   in the OVER-FIRE direction by the three drop-conjunct rivals and
#   weak-correct-unconditionally, and on the VALUE axis by weak-uncorrect-on-fire;
#   F-independence by weak-gate-on-classification and weak-gate-on-xfail-switch;
#   F-frame by weak-clobber-location-shape and weak-clobber-skipped-outcome, one
#   per framed field (and by every over-fire rival, each of which violates
#   `out = rep` off the firing sub-domain). All three are defended
#   by the three positive controls, and F-fire's two directions additionally by
#   the admissibility case's two corners. The ten reject witnesses probe ten
#   DISTINCT input points (pts=10):
#
#     mark  xfailOff prior  rep(skipped, structured, located)   case
#     ----------------------------------------------------------------------
#     true  true     true   (true,  true,  false)   weak-gate-on-classification
#     true  true     false  (true,  true,  false)   weak-gate-on-xfail-switch
#     false false    false  (true,  true,  false)   weak-overfire-drop-marker
#     true  false    true   (false, true,  false)   weak-overfire-drop-skipped
#     true  true     false  (true,  false, false)   weak-overfire-drop-structured
#     true  false    false  (true,  true,  true)    weak-clobber-location-shape
#     true  true     true   (true,  true,  true)    weak-clobber-skipped-outcome
#     true  false    true   (true,  true,  true)    weak-uncorrect-on-fire
#     false true     true   (false, false, false)   weak-correct-unconditionally
#     true  false    true   (true,  true,  false)   weak-never-correct
#
#   so `markSkipped` is varied over {true, false}, `xfailReportingOff` over
#   {true, false}, `priorClassification` over {true, false}, and `rep` over five
#   distinct triples covering every field in both polarities. Each conjunct of the
#   firing decision is ISOLATED by exactly one witness — the only witness with
#   `rep.skipped` false while the other two observations still qualify the report
#   is weak-overfire-drop-skipped, and the only one with
#   `rep.hasStructuredLocation` false on those terms is
#   weak-overfire-drop-structured (weak-correct-unconditionally carries both false
#   at once, so it isolates neither); `rep.locatedAtItem` is true only at the three
#   frame/value rivals. No binder is pinned across the battery, and neither
#   irrelevant binder is held at one value (the lesson from the two known
#   real failures: a spec whose independence claim is only ever probed with the
#   second toggle at `true` never tests that claim at all).
#
#   Each witness was SEEN to discriminate with two real builds: it ELABORATES
#   against the rival (exit 0) and FAILS against the frozen solution (exit 1,
#   `decide` reporting the proposition FALSE — not a tactic mismatch). Every
#   rival was also confirmed REJECTED by a real build (`unsolved goals` on the
#   frozen obligation) and every positive confirmed to VERIFY, so no case in this
#   manifest is expected to pass for a reason the gate has not already been shown
#   to observe. No witness binds a hypothesis, so no witness can be
#   `witness-inconsistent`.
#
# ORACLE INTEGRITY (audit lane, measured). The reject witnesses all assert
#   `reportSkipLocationTester … = false`, so they would be hollow if that tester
#   were constantly false. Checked with two extra builds that it is a TWO-WAY
#   oracle: asserting `= true` against the frozen solution at a point where gold
#   is correct ELABORATES (exit 0), and asserting `= false` against a RIVAL at a
#   point where that rival AGREES with gold FAILS with `decide` proving the
#   proposition false (exit 1). So each `= false` witness carries real
#   information about the rival at its point. Separately, the admissibility
#   assert was re-confirmed LIVE: falsifying its second conjunct leaves
#   `⊢ False` unsolved (exit 1), so it cannot discharge vacuously.
#
# PROOF-SHAPE SENSITIVITY of the frozen tactic body (audit lane, measured; a
#   property of the frozen proof script, NOT a spec hole). The three positive
#   controls discharge under the frozen
#   `loom_solve <;> simp_all [fixSkipLocation]` unchanged, but that body is not
#   shape-agnostic: two further FAITHFUL correct reshapes — commuting the three
#   guard conjuncts, and adding a redundant `&& !rep.locatedAtItem` (redundant
#   because on the firing sub-domain the spec's demanded output has
#   `locatedAtItem = true` either way) — leave an unsolved `ensures_1` goal under
#   it. Both were then PROVEN against the byte-identical frozen `ensures` with a
#   retuned tactic body that `variant_scope` admits (`loom_solve <;> obtain
#   ⟨s, st, lo⟩ := rep <;> revert … <;> decide`, exit 0). So the spec is NOT
#   too strong on impl shape — every faithful reshape tried is provable — and the
#   residual gap is only that the frozen one-liner needs retuning for some
#   shapes. Recorded rather than shipped as a positive control, since the three
#   existing positives already defend all three facets under the frozen proof and
#   the point of a positive control is the spec, not the tactic.
AXIOM_TESTS = []
