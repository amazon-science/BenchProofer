import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The report-classification that runs ahead of the
--  location correction — deciding the outcome and any narrative attached to a
--  report for the various expected/unexpected-outcome cases — is UNCHANGED, and
--  its result is observed only through the free input `rep` (the already
--  classified report) below. The spec makes no behavioural claim about that
--  classification and holds for EVERY report it could produce, so there is
--  nothing to check against a real callee — hence no G-AX. The behaviour under
--  spec — the skip-location correction and its independence from how the report
--  was classified — is modeled deeply in the `pure`/`impl` regions, with no
--  outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- A test report, abstracted to only the observations the location correction
   inspects and the observable it adjusts.
   * `skipped`             — the report records the test as skipped.
   * `hasStructuredLocation` — the report carries a structured (file, line,
                         reason) record, the only shape whose location is
                         correctable.
   * `locatedAtItem`       — the reported location points at the test's own
                         definition. `false` means it points elsewhere (at the
                         place inside the framework where the skip was produced);
                         `true` means it has been corrected to the test itself. -/
structure Report where
  skipped         : Bool
  hasStructuredLocation : Bool
  locatedAtItem   : Bool
  deriving DecidableEq, Inhabited

/- The skip-location correction applied to an already-classified report.

   A report whose skip was produced by a skip/skip-if marker, that is recorded as
   skipped, and that carries a structured location triple, must have its reported
   location point at the test's own definition. Every other report is left
   exactly as the classification produced it.

   `markSkipped` records that the skip originates from a skip/skip-if marker (as
   opposed to, e.g., an imperative skip raised from within the framework). When
   all three observations hold the location is corrected (`locatedAtItem := true`);
   otherwise the report is returned unchanged. -/
def fixSkipLocation (markSkipped : Bool) (rep : Report) : Report :=
  if markSkipped && rep.skipped && rep.hasStructuredLocation then
    { rep with locatedAtItem := true }
  else
    rep
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The report post-processing step of the per-test reporting hook. It is handed:

   * `markSkipped` — whether the report's skip originates from a skip/skip-if
                     marker (the only skips whose location is correctable here);
   * `xfailReportingOff` — whether the run is configured NOT to adjust
                     expected-failure reporting (the configuration the issue is
                     about: it concerns expected-failure handling alone);
   * `priorClassification` — whether some earlier arm of the report
                     classification (an unexpected-success or an
                     expected-failure case) already handled this report;
   * `rep` — the report AS ALREADY CLASSIFIED, a read-only free input: the
                     classification ahead of this step is unchanged here, and the
                     correction must hold for every report it can produce.

   The desired behaviour is `fixSkipLocation`: a marker-induced skip whose report
   is skipped and carries a structured location triple has its location corrected
   to the test's own definition. Crucially this correction is applied to EVERY
   such report on its own terms — it does NOT depend on whether the
   expected-failure reporting is switched off, nor on whether an earlier
   classification arm handled the report. `markSkipped`, `xfailReportingOff`,
   `priorClassification`, `rep` are all read-only (none `mut`): the step reads
   them and produces a fresh corrected report, mutating nothing it is handed
   (directive 5). -/
method reportSkipLocation (markSkipped : Bool) (xfailReportingOff : Bool)
    (priorClassification : Bool) (rep : Report) return (out : Report)
  ensures out = fixSkipLocation markSkipped rep
  do
    -- impl-start
    -- The expected/unexpected-outcome classification has already produced `rep`
    -- (its result is independent of the behaviour corrected here, so the inbound
    -- configuration `xfailReportingOff` and whether an earlier arm fired,
    -- `priorClassification`, do not enter this decision). Apply the skip-location
    -- correction as its OWN check, so it is reached for every marker-induced skip
    -- report regardless of how the report was classified above.
    if markSkipped && rep.skipped && rep.hasStructuredLocation then
      return { rep with locatedAtItem := true }
    else
      return rep
    -- impl-end

prove_correct reportSkipLocation by
  loom_solve <;> simp_all [fixSkipLocation]
