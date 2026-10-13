# refinement.md — pytest-dev__pytest-7432

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `reportSkipLocation` `do` block and the deep `fixSkipLocation` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs would be mechanically refuted by **G-CONF**; here the impl region
carries no offline R/I shadow (the only observable is a live-pytest side effect),
so `conf_skip=true` and G-CONF is a documented `status=skip` stub (mapping.md §4).
The A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested input, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `pytest_runtest_makereport` (`src/_pytest/skipping.py:291-298`)

Gold hunk:
```
                rep.outcome = "passed"
                rep.wasxfail = xfailed.reason
-    elif (
+
+    if (
         item._store.get(skipped_by_mark_key, True)
         and rep.skipped
         and type(rep.longrepr) is tuple
```

The change converts the final `elif` of the report-classification chain into a
standalone `if`. The `elif` only ran when no earlier arm of the chain matched;
the standalone `if` runs on its own terms, independent of the earlier arms.

| # | Solution.lean impl op (`reportSkipLocation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `markSkipped`, `rep` (`Report`) | `item._store.get(skipped_by_mark_key, True)`, `rep` | R | bool/structure ↔ Python truthy + report object (mapping.md §2). The report carries only the three touched fields. |
| A2 | param `priorClassification : Bool` | "an earlier `if/elif` arm matched" — the join of the four arms at `skipping.py:266,273,275,279` | R | free input modeling the UNCHANGED classification chain (mapping.md §3). The gold edit's whole effect is to make the correction NOT depend on this. |
| A3 | param `xfailReportingOff : Bool` | `item.config.option.runxfail` (`skipping.py:273`) | R | free input; the `--runxfail` configuration the issue names. The correction does not depend on it (modeled by its absence from `fixSkipLocation`). |
| A4 | `if markSkipped && rep.skipped && rep.hasStructuredLocation then { rep with locatedAtItem := true } else rep` | the standalone `if (item._store.get(...) and rep.skipped and type(rep.longrepr) is tuple): rep.longrepr = str(filename), line + 1, reason` | I | the changed control op is modeled **deeply**: the correction is a standalone decision over exactly the three repo conditions, applied regardless of `priorClassification`/`xfailReportingOff` — which IS the gold change (`elif` → `if`). The location rewrite `str(filename), line+1` is abstracted to `locatedAtItem := true` (mapping.md §2: only WHETHER the location was corrected is the changed observable). |

Discriminating content of the change — the correction must fire even when an
earlier classification arm already fired (`priorClassification = true`, which is
what `--runxfail` causes for a marker skip via the `elif ...runxfail: pass` arm
at `skipping.py:273`). This lives in `fixSkipLocation` depending ONLY on
`markSkipped`/`rep.skipped`/`rep.hasStructuredLocation`, never on
`priorClassification`. The pre-patch gated it behind `!priorClassification`;
`Solution_prepatch.lean` reproduces that and **fails** `out = fixSkipLocation
markSkipped rep` (G-DIFF) on exactly the report where `priorClassification =
true` and the three correction conditions hold.

## B. The failing prepatch

`Solution_prepatch.lean` keeps the spec byte-identical (G-DIFF requires
`same_spec`) and uses the buggy skeleton
`if !priorClassification && (markSkipped && rep.skipped && rep.hasStructuredLocation)`
— the `elif`-chained correction. `prove_correct` fails with the goal
`rep.hasStructuredLocation = true → rep = { ..., locatedAtItem := true }` left
unsolved: when `priorClassification = true` and the three conditions hold, the
buggy impl returns `rep` unchanged (`locatedAtItem` possibly `false`) while the
spec demands `locatedAtItem := true`. That is exactly the `--runxfail` regression
the issue reports: the marker-skip location is left pointing at
`src/_pytest/skipping.py` instead of the test definition.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
control-flow detachment of the skip-location correction from the classification
chain — is modeled **deeply** (the standalone `if` in `fixSkipLocation`, step
A4, an I step), not hidden behind an axiom. There are no consumed axioms: the
classification ahead of the correction is an UNCHANGED chain folded into the free
inputs `rep`/`priorClassification` (mapping.md §3), about which the spec makes no
claim.

## D. verify(Solution) ⇒ resolved

`reportSkipLocation` verifies only if its output equals `fixSkipLocation
markSkipped rep` (A4) — i.e. the location is corrected for every marker-induced
skip report carrying a tuple longrepr, INDEPENDENTLY of `priorClassification`
and `xfailReportingOff`. By R (`Bool`/`Report` ↔ Python truthy + report object,
mapping.md §2) the verified step equals the standalone-`if` correction of the
gold patch on the report the F2P test produces. There are no axioms (G-AX
vacuous) and no offline R/I shadow (G-CONF `conf_skip`, mapping.md §4); soundness
of the deep model is carried by G-VERIFY (the spec forces the correction to be
independent of the classification chain) and G-DIFF (the prepatch, gating the
correction behind `!priorClassification`, fails exactly the `locatedAtItem =
true` clause). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The trust point is refinement fidelity (this doc, G-EQ).
