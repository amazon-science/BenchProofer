# P2 adversarial audit — scikit-learn__scikit-learn-25931

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_18.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_2.lean`, `atk_3.lean`, `atk_12b.lean`, `atk_13b.lean`, `atk_14b.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `ctl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -640,10 +640,11 @@
     -- admissibility pass — so no feature-name-consistency warning is emitted and
     -- the record established from the training carrier stands. Reaching those
     -- scores is one traversal of the fitted model and the program's only one.
-    Fitting.traverse x.values fun scores =>
+    let v2 := validateInput x false ref Form.sparseByRow
+    Fitting.traverse v2.carrier.values fun scores =>
       let off := percentile scores (100.0 * contamination)
-      Fitting.done { offset := off, warned := false, reference := ref,
-                     scoreLater := scoreEntry ref }
+      Fitting.done { offset := off, warned := v2.warned, reference := v2.refAfter,
+                     scoreLater := scoreEntry v2.refAfter }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -626,7 +626,7 @@
     (contamination : Float) : Fitting :=
   -- initial validation of the training data: a reset, which describes the
   -- admissible input from the training carrier and raises no diagnostic
-  let v0 := validateInput xOrig true unrecorded Form.sparseByColumn
+  let v0 := validateInput xOrig true unrecorded Form.dense
   let x := v0.carrier
   let ref := v0.refAfter
   if contaminationAuto then
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -626,7 +626,7 @@
     (contamination : Float) : Fitting :=
   -- initial validation of the training data: a reset, which describes the
   -- admissible input from the training carrier and raises no diagnostic
-  let v0 := validateInput xOrig true unrecorded Form.sparseByColumn
+  let v0 := validateInput xOrig true unrecorded Form.sparseByRow
   let x := v0.carrier
   let ref := v0.refAfter
   if contaminationAuto then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -632,7 +632,7 @@
   if contaminationAuto then
     -- 0.5 plays a special role; we take the opposite, and the constant needs no
     -- traversal of the fitted model at all: the program is done here
-    Fitting.done { offset := -0.5, warned := false, reference := ref,
+    Fitting.done { offset := 0.5, warned := false, reference := ref,
                    scoreLater := scoreEntry ref }
   else
     -- contamination threshold configured: derive the offset from the model's
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -602,7 +602,7 @@
 forwards to can traverse — and what it hands on to the fitted model is what that
 validation returned. -/
 def scoreReport (ref : Reference) (z : InputData) : ScoreOutcome :=
-  let v := validateInput z false ref Form.sparseByRow
+  let v := validateInput z false ref Form.sparseByColumn
   { refused := v.refused, warned := v.warned, refAfter := v.refAfter,
     handedOn := v.carrier }
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -629,9 +629,8 @@
   let v0 := validateInput xOrig true unrecorded Form.sparseByColumn
   let x := v0.carrier
   let ref := v0.refAfter
+  Fitting.traverse x.values fun warmup =>
   if contaminationAuto then
-    -- 0.5 plays a special role; we take the opposite, and the constant needs no
-    -- traversal of the fitted model at all: the program is done here
     Fitting.done { offset := -0.5, warned := false, reference := ref,
                    scoreLater := scoreEntry ref }
   else
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -641,7 +641,7 @@
     -- the record established from the training carrier stands. Reaching those
     -- scores is one traversal of the fitted model and the program's only one.
     Fitting.traverse x.values fun scores =>
-      let off := percentile scores (100.0 * contamination)
+      let off := percentile x.values (100.0 * contamination)
       Fitting.done { offset := off, warned := false, reference := ref,
                      scoreLater := scoreEntry ref }
 -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -620,7 +620,7 @@
   let r := scoreReport ref z
   bif r.refused then Scored.done { r with returned := [] }
     else Scored.traverse r.handedOn.values
-           (fun scores => Scored.done { r with returned := scores })
+           (fun scores => Scored.done { r with returned := scores.reverse })
 
 def implementation_fit (xOrig : InputData) (contaminationAuto : Bool)
     (contamination : Float) : Fitting :=
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -589,7 +589,7 @@
                  form := Form.reshaped x.form accepted,
                  namesInspectable := true, contentAdmissible := true },
     refAfter := bif reset then
-                  { nFeatures := x.nFeatures, hasFeatureNames := x.hasFeatureNames }
+                  { nFeatures := x.nFeatures, hasFeatureNames := false }
                 else ref,
     refused := (!reset) && (!x.namesInspectable || !x.contentAdmissible
                              || (x.nFeatures != ref.nFeatures)),
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -584,7 +584,7 @@
 always inspectable and always admissible. -/
 def validateInput (x : InputData) (reset : Bool) (ref : Reference)
     (accepted : Form) : Validation :=
-  { carrier := { values := checked x.values, nFeatures := x.nFeatures,
+  { carrier := { values := x.values, nFeatures := x.nFeatures,
                  hasFeatureNames := false,
                  form := Form.reshaped x.form accepted,
                  namesInspectable := true, contentAdmissible := true },
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -591,7 +591,7 @@
     refAfter := bif reset then
                   { nFeatures := x.nFeatures, hasFeatureNames := x.hasFeatureNames }
                 else ref,
-    refused := (!reset) && (!x.namesInspectable || !x.contentAdmissible
+    refused := (!reset) && (!x.namesInspectable
                              || (x.nFeatures != ref.nFeatures)),
     warned := (!reset) && x.namesInspectable
                 && (ref.hasFeatureNames != x.hasFeatureNames) }
```

Attack 12 — `atk_12b.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -603,7 +603,8 @@
 validation returned. -/
 def scoreReport (ref : Reference) (z : InputData) : ScoreOutcome :=
   let v := validateInput z false ref Form.sparseByRow
-  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,
+  { refused := v.refused || (ref.hasFeatureNames && z.hasFeatureNames),
+    warned := v.warned, refAfter := v.refAfter,
     handedOn := v.carrier }
 
 /-- The public scoring entry point AS THE PROGRAM IT RUNS. It reaches the report
@@ -683,7 +684,7 @@
                Bool.false_and, hins, hcon] <;>
     first
       | rfl
-      | (intro z hc hw hn hi; simp [hi, hc, hw])
+      | (intro z hc hw hn hi; rcases hn with hn | hn <;> simp [hi, hc, hw, hn])
       | (intro z; and_intros <;> intros <;>
          first
            | (clear hout; simp_all; done)
```

Attack 13 — `atk_13b.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -640,9 +640,13 @@
     -- admissibility pass — so no feature-name-consistency warning is emitted and
     -- the record established from the training carrier stands. Reaching those
     -- scores is one traversal of the fitted model and the program's only one.
-    Fitting.traverse x.values fun scores =>
-      let off := percentile scores (100.0 * contamination)
-      Fitting.done { offset := off, warned := false, reference := ref,
+    if (Form.reshaped xOrig.form Form.sparseByColumn).traversable then
+      Fitting.traverse x.values fun scores =>
+        let off := percentile scores (100.0 * contamination)
+        Fitting.done { offset := off, warned := false, reference := ref,
+                       scoreLater := scoreEntry ref }
+    else
+      Fitting.done { offset := 0.0, warned := false, reference := ref,
                      scoreLater := scoreEntry ref }
 -- impl-end
 
@@ -652,9 +656,6 @@
     problem_spec_fit xOrig contaminationAuto contamination
       (implementation_fit xOrig contaminationAuto contamination) := by
   intro xOrig contaminationAuto contamination
-  -- what presenting a carrier to an estimator through the modeled entry point
-  -- reports, what it answers with, and what it costs, all read off the program
-  -- that entry point runs
   have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),
       ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused
       ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned
@@ -670,16 +671,18 @@
     unfold scoreEntry
     cases h : (scoreReport ref z).refused <;>
       simp [Scored.outcome, Scored.traversals, h]
-  unfold problem_spec_fit implementation_fit
+  unfold problem_spec_fit implementation_fit fitCompletes
   intro _hlvl hins hcon sc
-  cases contaminationAuto <;>
+  cases hT : (Form.reshaped xOrig.form Form.sparseByColumn).traversable <;>
+    cases contaminationAuto <;>
     refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
     simp only [Bool.false_eq_true, if_false, if_true, Fitting.result,
-               Fitting.traversals, (hout sc _ _).1, (hout sc _ _).2.1,
+               Fitting.traversals, hT, cond_true, cond_false,
+               (hout sc _ _).1, (hout sc _ _).2.1,
                (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,
                (hout sc _ _).2.2.2.2.2,
                scoreReport, validateInput, unrecorded,
-               cond_true, cond_false, Bool.not_true,
+               Bool.not_true, Bool.or_false, Bool.false_or,
                Bool.false_and, hins, hcon] <;>
     first
       | rfl
@@ -696,4 +699,6 @@
           | exact absurd trivial h
           | rfl
           | (simp))
+      | (simp_all)
+      | (intro h; exact absurd h (by simp))
 -- proof-end
```

Attack 14 — `atk_14b.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -640,10 +640,17 @@
     -- admissibility pass — so no feature-name-consistency warning is emitted and
     -- the record established from the training carrier stands. Reaching those
     -- scores is one traversal of the fitted model and the program's only one.
-    Fitting.traverse x.values fun scores =>
-      let off := percentile scores (100.0 * contamination)
-      Fitting.done { offset := off, warned := false, reference := ref,
-                     scoreLater := scoreEntry ref }
+    if (Form.reshaped xOrig.form Form.sparseByColumn).traversable then
+      Fitting.traverse x.values fun scores =>
+        let off := percentile scores (100.0 * contamination)
+        Fitting.done { offset := off, warned := false, reference := ref,
+                       scoreLater := scoreEntry ref }
+    else
+      Fitting.traverse x.values fun _ => Fitting.traverse x.values fun _ =>
+        Fitting.traverse x.values fun scores =>
+          let off := percentile scores (100.0 * contamination)
+          Fitting.done { offset := off, warned := false, reference := ref,
+                         scoreLater := scoreEntry ref }
 -- impl-end
 
 -- proof-start
@@ -652,9 +659,6 @@
     problem_spec_fit xOrig contaminationAuto contamination
       (implementation_fit xOrig contaminationAuto contamination) := by
   intro xOrig contaminationAuto contamination
-  -- what presenting a carrier to an estimator through the modeled entry point
-  -- reports, what it answers with, and what it costs, all read off the program
-  -- that entry point runs
   have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),
       ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused
       ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned
@@ -670,16 +674,18 @@
     unfold scoreEntry
     cases h : (scoreReport ref z).refused <;>
       simp [Scored.outcome, Scored.traversals, h]
-  unfold problem_spec_fit implementation_fit
+  unfold problem_spec_fit implementation_fit fitCompletes
   intro _hlvl hins hcon sc
-  cases contaminationAuto <;>
+  cases hT : (Form.reshaped xOrig.form Form.sparseByColumn).traversable <;>
+    cases contaminationAuto <;>
     refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
     simp only [Bool.false_eq_true, if_false, if_true, Fitting.result,
-               Fitting.traversals, (hout sc _ _).1, (hout sc _ _).2.1,
+               Fitting.traversals, hT, cond_true, cond_false,
+               (hout sc _ _).1, (hout sc _ _).2.1,
                (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,
                (hout sc _ _).2.2.2.2.2,
                scoreReport, validateInput, unrecorded,
-               cond_true, cond_false, Bool.not_true,
+               Bool.not_true, Bool.or_false, Bool.false_or,
                Bool.false_and, hins, hcon] <;>
     first
       | rfl
@@ -696,4 +702,6 @@
           | exact absurd trivial h
           | rfl
           | (simp))
+      | (simp_all)
+      | (intro h; exact absurd h (by simp))
 -- proof-end
```

Attack 15 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -626,7 +626,7 @@
     (contamination : Float) : Fitting :=
   -- initial validation of the training data: a reset, which describes the
   -- admissible input from the training carrier and raises no diagnostic
-  let v0 := validateInput xOrig true unrecorded Form.sparseByColumn
+  let v0 := validateInput xOrig true { nFeatures := 7, hasFeatureNames := true } Form.sparseByColumn
   let x := v0.carrier
   let ref := v0.refAfter
   if contaminationAuto then
```

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -640,7 +640,7 @@
     -- admissibility pass — so no feature-name-consistency warning is emitted and
     -- the record established from the training carrier stands. Reaching those
     -- scores is one traversal of the fitted model and the program's only one.
-    Fitting.traverse x.values fun scores =>
+    Fitting.traverse (checked x.values) fun scores =>
       let off := percentile scores (100.0 * contamination)
       Fitting.done { offset := off, warned := false, reference := ref,
                      scoreLater := scoreEntry ref }
@@ -680,7 +680,7 @@
                (hout sc _ _).2.2.2.2.2,
                scoreReport, validateInput, unrecorded,
                cond_true, cond_false, Bool.not_true,
-               Bool.false_and, hins, hcon] <;>
+               Bool.false_and, hins, hcon, checked_idem] <;>
     first
       | rfl
       | (intro z hc hw hn hi; simp [hi, hc, hw])
```

Attack 17 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -603,8 +603,8 @@
 validation returned. -/
 def scoreReport (ref : Reference) (z : InputData) : ScoreOutcome :=
   let v := validateInput z false ref Form.sparseByRow
-  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,
-    handedOn := v.carrier }
+  { refused := v.refused, warned := v.warned || !z.namesInspectable,
+    refAfter := v.refAfter, handedOn := v.carrier }
 
 /-- The public scoring entry point AS THE PROGRAM IT RUNS. It reaches the report
 above, and the traversals it spends follow from that report and from nothing
```

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -604,7 +604,7 @@
 def scoreReport (ref : Reference) (z : InputData) : ScoreOutcome :=
   let v := validateInput z false ref Form.sparseByRow
   { refused := v.refused, warned := v.warned, refAfter := v.refAfter,
-    handedOn := v.carrier }
+    handedOn := bif v.refused then z else v.carrier }
 
 /-- The public scoring entry point AS THE PROGRAM IT RUNS. It reaches the report
 above, and the traversals it spends follow from that report and from nothing
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, A-legs + model<->patch correspondence). VERDICT: SOUND. 18 same-spec attacks encoded, all verified; every one of the 8 that CLOSED had its faithful patch materialized and RUN through run_resolve; all 8 resolved. No verify=>correct break found.

**SETUP.** Own worktree at base_commit e3d1f9ac39e4bf0f31430e779acc50fb05fe1b64 created via `git worktree add --detach $D/wt`, used for `git apply --check`, removed at the end. same_spec=True for all 18 attacks + ctl (swebench_unified.markers.same_spec, lean backend) -- every edit is confined to the impl region; axioms/pure/pre/post are byte-identical.

**POSITIVE CONTROL.** ctl.lean = verbatim Solution.lean. `bash scripts/lean_verify.sh $D/ctl.lean` -> EXIT=0 (2 linter warnings only: unreachableTactic/unusedTactic on the proof's last `first` lane).

PREPATCH REPRODUCED (atk_1). Re-encoded the prepatch bug: the configured branch routed through the public scorer, i.e. `let v2 := validateInput x false ref Form.sparseByRow; Fitting.traverse v2.carrier.values ...` with `warned := v2.warned, reference := v2.refAfter`. `lean_verify.sh $D/atk_1.lean` -> EXIT=1, residual is exactly the discriminating clause: `case false.refine_1 |- (!false && true && xOrig.hasFeatureNames != false) = false`. That is refinement.md's stated G-DIFF signal and mirrors F2P test_iforest_preserve_feature_names.

GOLD CONTROL (run FIRST, alone). patch_gold_ctl.diff = bundle patch.diff verbatim. `python3 resolve_one.py gold_ctl` -> resolved=TRUE, completed=TRUE, applied=TRUE, F2P 1/1, P2P 21/21, zero failures, attempts=1, flaky=False. The oracle can refute on this instance, so every attack resolve below is informative.

ATTACKS THAT THE SPEC REJECTED (10 of 18) -- all EXIT=1, verify cmd `bash scripts/lean_verify.sh $D/atk_N.lean`: atk_1  prepatch bug (second validation pass) -- residual = the `warned = false` conjunct (above). atk_4  boundary: offset constant sign flipped -0.5 -> 0.5. atk_9  reference record drops the feature-name status (`hasFeatureNames := false` on the reset lane). atk_5  score-time accepted layout := sparseByColumn (hands the model the layout its scoring path refuses) -- unsolved goals. atk_6  control-flow-effect: traversal hoisted above the branch, so the auto arm also spends one -- unsolved goals. atk_7  ungrounded-oracle echo: threshold re-derived from the payload (`percentile x.values ...`), ignoring the traversed scores -- unsolved goals. atk_8  RETURNED-VALUE transform (`returned := scores.reverse`) -- THIS IS THE PRIOR PASS'S COUNTEREXAMPLE, re-encoded.

Now correctly REJECTED, EXIT=1. The repair (fifth `returned` field on ScoreOutcome in the frozen pure region + clause 5 leg 8 pinning it to `bif refused then [] else sc (checked z.values)`) WORKS. atk_10 crossing carrier forwards the caller's raw payload (`values := x.values`) -- unsolved goals. atk_11 refusal lane drops the content-admissibility ground -- unsolved goals. atk_18 partial domain on `handedOn`: caller's raw carrier on the REFUSING lane (`bif v.refused then z else v.carrier`) -- unsolved goals. Clause 5 leg 4 is guarded by `refused = false`, but `scoreEntry`'s traversal payload leg reaches it anyway, so the region is not actually open.

ATTACKS THAT CLOSED (8) -- each: EXIT=0, `#print axioms correct_fit` via ax_atk_N.lean, faithful patch `git apply --check`ed at base_commit, then run_resolve ONE AT A TIME (never concurrent -- same instance, --cache_level env deletes the image): atk_2  fit-time accepted layout := Form.dense (the check densifies). axioms [propext, Classical.choice, Quot.sound] CLEAN. defeq_atk_2.lean EXIT=0: `example : forall x c f, implementation_fit x c f = implementation_fitG x c f := by intro x c f; cases c <;> rfl` CLOSES -- atk_2 is the SAME Lean term as the frozen impl (the `accepted` argument is dead in the impl; it only feeds `carrier.form`, which the fit tail never reads). patch_atk_2.diff = gold + `X = np.asarray(X.todense(), dtype=tree_dtype)` after sort_indices. resolved=TRUE, F2P 1/1, P2P 21/21. atk_3  fit-time accepted layout := Form.sparseByRow.

CLEAN axioms; defeq_atk_3.lean EXIT=0, also defeq to frozen. patch_atk_3.diff = gold + `accept_sparse=["csc"]` -> `["csr"]` at fit's `_validate_data`. resolved=TRUE, F2P 1/1, P2P 21/21. atk_12b NAME-IDENTITY open region: `refused := v.refused || (ref.hasFeatureNames && z.hasFeatureNames)`. Clause 7 asks refused=false only under `xOrig.hasFeatureNames = false OR z.hasFeatureNames = false`, so refusal is unpinned exactly where both sides bear names. CLEAN axioms. patch_atk_12b.diff = gold + a raise in score_samples when the estimator holds names and `_get_feature_names(X)` is not None. resolved=TRUE, F2P 1/1, P2P 21/21 -- so the limit refinement.md declares deliberate is genuinely open in the ORACLE too, not just the model.

Not a defect. atk_13b fitCompletes-FALSE region: on a sparse carrier with a configured level, constant offset 0.0 and NO traversal. CLEAN axioms. patch = gold + `if issparse(X): self.offset_ = 0.0`. resolved=TRUE 21/21. atk_14b same region, opposite way: THREE traversals there. CLEAN axioms. patch = gold + two extra `self._score_samples(X)` calls under issparse. resolved=TRUE 21/21. (13b/14b confirm the fitCompletes guard is sound: that lane raises in the real code before any test observes it.) atk_15 the pre-reset record is non-empty (`validateInput xOrig true {nFeatures := 7, hasFeatureNames := true} ...`).

CLEAN axioms. patch sets n_features_in_/feature_names_in_ ahead of fit's `_validate_data`. resolved=TRUE 21/21 -- the reset overwrites it, so `unrecorded` is correctly dead. atk_16 A-CONSUMED PROBE (this is the direct test of the axiom leg): `Fitting.traverse (checked x.values)`, i.e. the payload re-presented a SECOND time. Only equal to the spec's `checked xOrig.values` via `checked_idem`, and the frozen script needed `checked_idem` added to its simp set. axioms = [checked_idem, propext, Classical.choice, Quot.sound] -- NOT clean, so by the stated criterion this cannot be a BROKEN witness. I resolved it anyway to ground the axiom: patch_atk_16.diff = gold + `X_again = check_array(X, accept_sparse=["csc"], dtype=tree_dtype)` before the private scorer. resolved=TRUE 21/21.

So `checked (checked v) = checked v` is TRUE of the real callee (a second check_array pass on an already-converted array is a content no-op), which is what refinement.md claims and what makes the axiom admissible rather than a hole. atk_17 partial domain on `warned`: `warned := v.warned || !z.namesInspectable`. Clause 5 leg 2 pins `warned` only under `z.namesInspectable = true`, so the uninspectable lane is unpinned. CLEAN axioms. patch_atk_17.diff = gold + a UserWarning emitted before re-raising the TypeError from `_get_feature_names` on mixed-kind labels. resolved=TRUE, F2P 1/1, P2P 21/21 -- no hidden test observes a diagnostic on that lane, so the guard is not a spec weakness the oracle can see.

PROOF-SCRIPT CAVEAT (worth recording). atk_12/13/14 first came back EXIT=1, but the residuals were MY OWN script bugs, not spec rejections: atk_13's was `introN failed: There are no additional binders` and atk_12's was `|- xOrig.hasFeatureNames = true -> z.hasFeatureNames = false`, which follows from the `hn` disjunct the frozen lane never cases on. An attacker may write their own proof, so I re-attacked with bespoke proofs (atk_12b: `rcases hn with hn | hn`; atk_13b/14b: an extra `cases hT : (Form.reshaped xOrig.form Form.sparseByColumn).traversable` ahead of the branch split) and all three then closed at EXIT=0. Judging the originals as rejections would have credited the spec with strength it does not have. The superseded atk_12/13/14 files remain in the scratch dir; the submitted attack list carries the 12b/13b/14b variants.

A-LEG / refinement.md AUDIT. Six rows, tags R(1, row 1) / A-reference(2, rows 2 and 6) / I(3, rows 3,4,5) -- no kind-3 leg. `#print axioms correct_fit` on the shipped file reports [propext, Classical.choice, Quot.sound], so no bundle axiom is proof-load-bearing, matching refinement.md's claim that no row is discharged by consuming an axiom PROPERTY. The one bundle axiom, `checked_idem`, is declared "assumed, consumed by nothing" and that is confirmed both ways: the shipped proof does not use it, and atk_16 (which does) both closes AND resolves, so the axiom is a true fact about check_array rather than a licence to cheat.

A-reference correspondence checked against the real callees in the base worktree: row 2's `accepted` layout <-> `_validate_data(X, accept_sparse=["csc"], dtype=tree_dtype)` at fit (line 291) and row 6's <-> `_validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)` in score_samples -- both call sites exist as mapping.md line 35 describes, the two ends do accept different sparse layouts, and the CSC-refusal that `Form.traversable`/`fitCompletes` encode is real (`sklearn/tree/_splitter.pyx:866  raise ValueError("X should be in csc format")`, and the scoring path's mirror on CSR). Row 6's discriminator -- routing through `_score_samples`, which omits the reset=False call, hence `warned = false` -- is exactly what atk_1's residual shows the spec enforcing.

WHAT THE atk_2/atk_3 DEFEQ RESULT MEANS. Both are byte-distinct from the frozen impl but definitionally EQUAL to it, because the fit-time `accepted` layout argument feeds only `carrier.form`, which the fit tail never reads (it reads `carrier.values`). So no predicate over `Fitting` could separate them -- yet their faithful patches both resolve 21/21. That is the sound outcome: the model collapses a distinction the oracle also cannot see. It would only be a defect if some patch in that defeq class failed to resolve, and neither of the two I built does. Worth noting for a future pass: `fitCompletes` hardcodes `Form.sparseByColumn` in the FROZEN pure region rather than reading the impl's argument, so the guard cannot be moved by an attacker either.

COVERAGE vs the required classes: partial-domain (atk_12b name-identity, atk_13b/14b fitCompletes-false, atk_17 uninspectable-warned, atk_18 refusing-lane handedOn), boundary (atk_4 constant sign, atk_9 record field), control-flow-effect (atk_6 hoisted traversal, atk_14b extra traversals, atk_8 returned-value), ungrounded-oracle echo (atk_7 threshold re-derived from payload), crossing-value (atk_5 unscorable layout, atk_10 caller's raw payload), axioms/A-legs (atk_16 checked_idem-consuming, atk_2/atk_3 dead-argument defeq, atk_15 dead initial record), plus the prepatch bug (atk_1).

**No INCONCLUSIVE conditions:** every attack reached a verifier verdict, every closing attack has a materialized patch that `git apply --check`ed clean at base_commit and an EXECUTED run_resolve result, and the gold control certified 21/21 in the same session before any attack ran. Resolves were strictly serial (9 runs total, one at a time); no ImageNotFound and no timeouts. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_18.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_2.lean`, `atk_3.lean`, `atk_12b.lean`, `atk_13b.lean`, `atk_14b.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `ctl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, A-legs + model<->patch correspondence). VERDICT: SOUND. 18 same-spec attacks encoded, all verified; every one of the 8 that CLOSED had its faithful patch materialized and RUN through run_resolve; all 8 resolved. No verify=>correct break found.

**SETUP.** Own worktree at base_commit e3d1f9ac39e4bf0f31430e779acc50fb05fe1b64 created via `git worktree add --detach $D/wt`, used for `git apply --check`, removed at the end. same_spec=True for all 18 attacks + ctl (swebench_unified.markers.same_spec, lean backend) -- every edit is confined to the impl region; axioms/pure/pre/post are byte-identical.

**POSITIVE CONTROL.** ctl.lean = verbatim Solution.lean. `bash scripts/lean_verify.sh $D/ctl.lean` -> EXIT=0 (2 linter warnings only: unreachableTactic/unusedTactic on the proof's last `first` lane).

PREPATCH REPRODUCED (atk_1). Re-encoded the prepatch bug: the configured branch routed through the public scorer, i.e. `let v2 := validateInput x false ref Form.sparseByRow; Fitting.traverse v2.carrier.values ...` with `warned := v2.warned, reference := v2.refAfter`. `lean_verify.sh $D/atk_1.lean` -> EXIT=1, residual is exactly the discriminating clause: `case false.refine_1 |- (!false && true && xOrig.hasFeatureNames != false) = false`. That is refinement.md's stated G-DIFF signal and mirrors F2P test_iforest_preserve_feature_names.

GOLD CONTROL (run FIRST, alone). patch_gold_ctl.diff = bundle patch.diff verbatim. `python3 resolve_one.py gold_ctl` -> resolved=TRUE, completed=TRUE, applied=TRUE, F2P 1/1, P2P 21/21, zero failures, attempts=1, flaky=False. The oracle can refute on this instance, so every attack resolve below is informative.

ATTACKS THAT THE SPEC REJECTED (10 of 18) -- all EXIT=1, verify cmd `bash scripts/lean_verify.sh $D/atk_N.lean`: atk_1  prepatch bug (second validation pass) -- residual = the `warned = false` conjunct (above). atk_4  boundary: offset constant sign flipped -0.5 -> 0.5. atk_9  reference record drops the feature-name status (`hasFeatureNames := false` on the reset lane). atk_5  score-time accepted layout := sparseByColumn (hands the model the layout its scoring path refuses) -- unsolved goals. atk_6  control-flow-effect: traversal hoisted above the branch, so the auto arm also spends one -- unsolved goals. atk_7  ungrounded-oracle echo: threshold re-derived from the payload (`percentile x.values ...`), ignoring the traversed scores -- unsolved goals. atk_8  RETURNED-VALUE transform (`returned := scores.reverse`) -- THIS IS THE PRIOR PASS'S COUNTEREXAMPLE, re-encoded.

Now correctly REJECTED, EXIT=1. The repair (fifth `returned` field on ScoreOutcome in the frozen pure region + clause 5 leg 8 pinning it to `bif refused then [] else sc (checked z.values)`) WORKS. atk_10 crossing carrier forwards the caller's raw payload (`values := x.values`) -- unsolved goals. atk_11 refusal lane drops the content-admissibility ground -- unsolved goals. atk_18 partial domain on `handedOn`: caller's raw carrier on the REFUSING lane (`bif v.refused then z else v.carrier`) -- unsolved goals. Clause 5 leg 4 is guarded by `refused = false`, but `scoreEntry`'s traversal payload leg reaches it anyway, so the region is not actually open.

ATTACKS THAT CLOSED (8) -- each: EXIT=0, `#print axioms correct_fit` via ax_atk_N.lean, faithful patch `git apply --check`ed at base_commit, then run_resolve ONE AT A TIME (never concurrent -- same instance, --cache_level env deletes the image): atk_2  fit-time accepted layout := Form.dense (the check densifies). axioms [propext, Classical.choice, Quot.sound] CLEAN. defeq_atk_2.lean EXIT=0: `example : forall x c f, implementation_fit x c f = implementation_fitG x c f := by intro x c f; cases c <;> rfl` CLOSES -- atk_2 is the SAME Lean term as the frozen impl (the `accepted` argument is dead in the impl; it only feeds `carrier.form`, which the fit tail never reads). patch_atk_2.diff = gold + `X = np.asarray(X.todense(), dtype=tree_dtype)` after sort_indices. resolved=TRUE, F2P 1/1, P2P 21/21. atk_3  fit-time accepted layout := Form.sparseByRow.

CLEAN axioms; defeq_atk_3.lean EXIT=0, also defeq to frozen. patch_atk_3.diff = gold + `accept_sparse=["csc"]` -> `["csr"]` at fit's `_validate_data`. resolved=TRUE, F2P 1/1, P2P 21/21. atk_12b NAME-IDENTITY open region: `refused := v.refused || (ref.hasFeatureNames && z.hasFeatureNames)`. Clause 7 asks refused=false only under `xOrig.hasFeatureNames = false OR z.hasFeatureNames = false`, so refusal is unpinned exactly where both sides bear names. CLEAN axioms. patch_atk_12b.diff = gold + a raise in score_samples when the estimator holds names and `_get_feature_names(X)` is not None. resolved=TRUE, F2P 1/1, P2P 21/21 -- so the limit refinement.md declares deliberate is genuinely open in the ORACLE too, not just the model.

Not a defect. atk_13b fitCompletes-FALSE region: on a sparse carrier with a configured level, constant offset 0.0 and NO traversal. CLEAN axioms. patch = gold + `if issparse(X): self.offset_ = 0.0`. resolved=TRUE 21/21. atk_14b same region, opposite way: THREE traversals there. CLEAN axioms. patch = gold + two extra `self._score_samples(X)` calls under issparse. resolved=TRUE 21/21. (13b/14b confirm the fitCompletes guard is sound: that lane raises in the real code before any test observes it.) atk_15 the pre-reset record is non-empty (`validateInput xOrig true {nFeatures := 7, hasFeatureNames := true} ...`).

CLEAN axioms. patch sets n_features_in_/feature_names_in_ ahead of fit's `_validate_data`. resolved=TRUE 21/21 -- the reset overwrites it, so `unrecorded` is correctly dead. atk_16 A-CONSUMED PROBE (this is the direct test of the axiom leg): `Fitting.traverse (checked x.values)`, i.e. the payload re-presented a SECOND time. Only equal to the spec's `checked xOrig.values` via `checked_idem`, and the frozen script needed `checked_idem` added to its simp set. axioms = [checked_idem, propext, Classical.choice, Quot.sound] -- NOT clean, so by the stated criterion this cannot be a BROKEN witness. I resolved it anyway to ground the axiom: patch_atk_16.diff = gold + `X_again = check_array(X, accept_sparse=["csc"], dtype=tree_dtype)` before the private scorer. resolved=TRUE 21/21.

So `checked (checked v) = checked v` is TRUE of the real callee (a second check_array pass on an already-converted array is a content no-op), which is what refinement.md claims and what makes the axiom admissible rather than a hole. atk_17 partial domain on `warned`: `warned := v.warned || !z.namesInspectable`. Clause 5 leg 2 pins `warned` only under `z.namesInspectable = true`, so the uninspectable lane is unpinned. CLEAN axioms. patch_atk_17.diff = gold + a UserWarning emitted before re-raising the TypeError from `_get_feature_names` on mixed-kind labels. resolved=TRUE, F2P 1/1, P2P 21/21 -- no hidden test observes a diagnostic on that lane, so the guard is not a spec weakness the oracle can see.

PROOF-SCRIPT CAVEAT (worth recording). atk_12/13/14 first came back EXIT=1, but the residuals were MY OWN script bugs, not spec rejections: atk_13's was `introN failed: There are no additional binders` and atk_12's was `|- xOrig.hasFeatureNames = true -> z.hasFeatureNames = false`, which follows from the `hn` disjunct the frozen lane never cases on. An attacker may write their own proof, so I re-attacked with bespoke proofs (atk_12b: `rcases hn with hn | hn`; atk_13b/14b: an extra `cases hT : (Form.reshaped xOrig.form Form.sparseByColumn).traversable` ahead of the branch split) and all three then closed at EXIT=0. Judging the originals as rejections would have credited the spec with strength it does not have. The superseded atk_12/13/14 files remain in the scratch dir; the submitted attack list carries the 12b/13b/14b variants.

A-LEG / refinement.md AUDIT. Six rows, tags R(1, row 1) / A-reference(2, rows 2 and 6) / I(3, rows 3,4,5) -- no kind-3 leg. `#print axioms correct_fit` on the shipped file reports [propext, Classical.choice, Quot.sound], so no bundle axiom is proof-load-bearing, matching refinement.md's claim that no row is discharged by consuming an axiom PROPERTY. The one bundle axiom, `checked_idem`, is declared "assumed, consumed by nothing" and that is confirmed both ways: the shipped proof does not use it, and atk_16 (which does) both closes AND resolves, so the axiom is a true fact about check_array rather than a licence to cheat.

A-reference correspondence checked against the real callees in the base worktree: row 2's `accepted` layout <-> `_validate_data(X, accept_sparse=["csc"], dtype=tree_dtype)` at fit (line 291) and row 6's <-> `_validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)` in score_samples -- both call sites exist as mapping.md line 35 describes, the two ends do accept different sparse layouts, and the CSC-refusal that `Form.traversable`/`fitCompletes` encode is real (`sklearn/tree/_splitter.pyx:866  raise ValueError("X should be in csc format")`, and the scoring path's mirror on CSR). Row 6's discriminator -- routing through `_score_samples`, which omits the reset=False call, hence `warned = false` -- is exactly what atk_1's residual shows the spec enforcing.

WHAT THE atk_2/atk_3 DEFEQ RESULT MEANS. Both are byte-distinct from the frozen impl but definitionally EQUAL to it, because the fit-time `accepted` layout argument feeds only `carrier.form`, which the fit tail never reads (it reads `carrier.values`). So no predicate over `Fitting` could separate them -- yet their faithful patches both resolve 21/21. That is the sound outcome: the model collapses a distinction the oracle also cannot see. It would only be a defect if some patch in that defeq class failed to resolve, and neither of the two I built does. Worth noting for a future pass: `fitCompletes` hardcodes `Form.sparseByColumn` in the FROZEN pure region rather than reading the impl's argument, so the guard cannot be moved by an attacker either.

COVERAGE vs the required classes: partial-domain (atk_12b name-identity, atk_13b/14b fitCompletes-false, atk_17 uninspectable-warned, atk_18 refusing-lane handedOn), boundary (atk_4 constant sign, atk_9 record field), control-flow-effect (atk_6 hoisted traversal, atk_14b extra traversals, atk_8 returned-value), ungrounded-oracle echo (atk_7 threshold re-derived from payload), crossing-value (atk_5 unscorable layout, atk_10 caller's raw payload), axioms/A-legs (atk_16 checked_idem-consuming, atk_2/atk_3 dead-argument defeq, atk_15 dead initial record), plus the prepatch bug (atk_1).

**No INCONCLUSIVE conditions:** every attack reached a verifier verdict, every closing attack has a materialized patch that `git apply --check`ed clean at base_commit and an EXECUTED run_resolve result, and the gold control certified 21/21 in the same session before any attack ran. Resolves were strictly serial (9 runs total, one at a time); no ImageNotFound and no timeouts. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL attacker (2) faithfulness-break. Reference = worktree of scikit-learn_scikit-learn.git @ e3d1f9ac39e4bf0f31430e779acc50fb05fe1b64 with patch.diff APPLIED (git apply clean). Executed against a prebuilt byte-identical patched tree (its sklearn/ensemble/`_iforest`.py diffs EMPTY vs my worktree+patch), sklearn 1.3.dev0, env sk25931 (py3.10, np1.26.4, scipy1.15.3, pandas2.3.3). Full sklearn/ensemble/tests/test_iforest.py = 22 passed; issue repro (named frame + contamination=0.05) emits no UserWarning, so the fix is present in the reference.

**ARTIFACT INTEGRITY.** scripts/lean_verify.sh Solution.lean -> exit 0 (elaborates, no sorry/admit). `#print axioms correct_fit` -> [propext, Classical.choice, Quot.sound]: no bundle axiom (checked_idem/percentile/checked/levelAdmitted) is consumed, so the proof is not leaning on an assumption. markers.same_spec(Solution, Solution_prepatch, lean tables) = True (spec_signature sha256 cda7d12bce1317afa877bd80d9f341d8f5a0efee68741cc4f2491365ad1686c0, 506 lines) -> spec region byte-identical; impl-region diff is exactly the discriminator (prepatch routes the configured branch through validateInput x false ref Form.sparseByRow, i.e. the public scorer). Prepatch verify -> 'declaration uses sorry' (fails, G-DIFF signal). NON-VACUITY, POSITIVELY: I authored and compiled `theorem prepatch_refuted (c) (hc : levelAdmitted c = true) : ¬ problem_spec_fit xBad false c (implementation_fit xBad false c)` at a concrete named dense carrier -- exit 0, axioms [propext, Classical.choice, Quot.sound]. The spec actively REFUTES the base-commit model, it does not merely fail to close it.

DIFFERENTIAL EVIDENCE (2530 total observations, 0 divergences). Built two shadow harnesses that derive each carrier's Lean image by MEASURING the real callees (`_get_feature_names` for namesInspectable/hasFeatureNames, check_array for contentAdmissible + the handed-back layout) and spy on IsolationForest.`_compute_chunked_score_samples` to read traversal count/payload/form/self-description off the object actually handed the scoring core. Sweep 1: 1160 obs over fit-kind x {dense,csr,csc,df_str,df_int} x 3 widths x {auto,0.25} crossed with 13 z-kinds x 3 widths -> 0 violations. Sweep 2 (randomized, seed 20250817, 320 trials incl. permuted/renamed string labels, coo/lil/bool/int/lol/f32, empty-row, empty-col, nan, +/-inf, mixed labels): 1370 obs, 0 violations, lanes populated complete=253 abort=21 C6=135 C7=171 (no lane vacuous).

PER-CLAUSE, ALL CONFIRMED AGAINST THE REFERENCE. C1 warned=false: no feature-name warning on any admissible fit, including the sparse+configured ABORT lane and a name-bearing sparse frame. C2: auto -> offset_ = -0.5 exactly, incl. degenerate (1,1),(2,1),(1,3),(2,2),(256,1) and huge/tiny/all-equal/mixed-magnitude contents. C3 numeric: offset_ == np.percentile(-`_compute_chunked_score_samples`(check_array(X,accept_sparse=['csc'],dtype=float32)), `100*c`) held with EXACT float equality on every completing draw, and the traversed payload IS the checked array (array_equal True, dtype float32). C4: n_features_in_/feature_names_in_ = the training carrier's, incl. after the abort.

C5 all eight legs: width mismatch -> refused; warned == (xOrig.hasFeatureNames != z.hasFeatureNames) exactly, in BOTH directions and, critically, UNCONDITIONALLY on refusal (named z at wrong width, and named z at wrong width WITH nan, both still warn -> the spec's deliberate non-guarding of the warning leg by contentAdmissible is CORRECT, measured, not assumed); refAfter unchanged on all five refusal/admission kinds; handedOn matched the six-field record equation on every accepted call (values == check_array(z,accept_sparse='csr',dtype=float32), nFeatures == z's, form == Form.reshaped z.form sparseByRow -- csc caller crosses as csr, hasFeatureNames False, and re-inspectable/re-admissible True verified by re-running both callees on the crossing object); uninspectable -> refused (TypeError) with NO warning; inadmissible -> refused; traversals = [] iff refused else exactly one over the crossing payload; returned == -`_compute_chunked_score_samples`(handedOn) exactly.

C6/C7 admission: 135+171 draws, never refused in-region, incl. content the check REWRITES (int64, bool, float32, coo, lil, dok, dia, bsr, list-of-lists, sparse-dtype frames) -- so replacing the old z.values = checked z.values antecedent with contentAdmissible is faithful, not over-strong. C8: traversals = [] on auto, [checked xOrig.values] on configured, exactly.

DOMAIN LIMITS CHECKED FOR OVER-STRENGTH (the failure mode that would condemn a correct spec is a spec too STRONG, so I probed the guards from the strong side). fitCompletes: measured that fit(sparse, configured) really does raise ValueError 'X should be in csr_matrix format' with n_features_in_ recorded and offset_ ABSENT, for BOTH csr and csc callers (the fit check's accept_sparse=['csc'] hands both back csc; the scoring path refuses csc). So withholding C3/C8 there is REQUIRED -- an unguarded clause would be the real defect. Symmetrically I verified the guard is not over-broad: the sparse UNCONFIGURED lane and everything else still carry the full C1/C4/C5/C6/C7 obligation, and I confirmed those hold post-abort.

Name identity: real code raises on permuted ['c','b','a'] and renamed ['f0','f1','XX'] -- C7's (xOrig.hasFeatureNames = false OR z.hasFeatureNames = false) antecedent correctly excludes exactly those, and C5-warned is False there in the real code, matching. levelAdmitted: {0.0,-0.1,0.6,1.0} raise InvalidParameterError with zero traversals and NO attributes left behind; {0.25,0.5} complete with exactly one traversal -- and the ORDERING contrast fires (refused level over nan content names 'contamination'; admitted level over the same content names NaN), confirming `_validate_params` is genuinely first, so the antecedent's position is faithful.

Two modelling reductions independently validated: checked_idem holds as CONTENT idempotence for both accept_sparse configs across 8 carrier kinds; and a SINGLE opaque `checked` for both call sites is faithful because check_array(X,accept_sparse=['csc']) and check_array(X,accept_sparse='csr') agree on CONTENT for every kind tested (they differ only in returned layout, which the model carries separately in `form`). I also searched for a carrier on which the two configs disagree on ADMISSIBILITY across 19 kinds -- zero disagreements, so contentAdmissible being one flag shared by both ends is sound.

HARNESS DISCRIMINATES (11/11 refuting controls FIRE, so the 0-violation result is not a dead probe): fitCompletes-collapsed, handedOn-layout-collapsed (csc-vs-csr), handedOn-caller-description, handedOn-raw-payload, refused-costs-nothing, uninspectable-refused, uninspectable-no-warning, inadmissible-refused, warn-then-content-refuse, no-warn-when-uninspectable, param-validation-is-first.

**CONCLUSION:** no input found on which problem_spec_fit disagrees with the patched callee. The spec is faithful and not over-strong; each of its three withholdings (storage form, name identity, level admission) is withheld exactly where the real patched code raises before producing the described value, and each is bounded on the other side by a measured positive obligation. No diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction from the spec view, scikit-learn__scikit-learn-25931 (lean). Verdict NO-LEAKAGE. Every number below is my own run against the SHIPPED bytes; I inherited no disposition from any file in the bundle.

(0) NO RELAXATION IS CLAIMED — checked, not assumed. `'relaxed_leakage' in json.load(meta.json)` -> False (top-level keys: axioms, conf_skip, deep_model_references, gates, instance_id, modeled_functions, opaque_callees, pbt_audit, region_hashes, schema_version, spec_provenance, verifier_pins). `find <instance-dir> -iname '*RELAX*'` -> nothing. So this is an ORDINARY leakage judgement with no unavoidability argument to inherit or re-derive, and I judged it as one. Separately I grepped mapping.md/refinement.md for text addressing an auditor (attacker|auditor|panel|G-PANEL|reviewer|'honest verdict'|NO-LEAKAGE|'do not submit') -> ZERO hits. No file in this bundle tried to tell me how to record or which verdict to submit.

(1) FRESHNESS — I am judging DIFFERENT BYTES than the last panel run, which is why I re-derived rather than re-read. Shipped Solution.lean sha256 = a7b03aa4b06dd083b33f354e09148e8c816494762a6f70795cff99aa5147dcf4, which matches the source recorded by G-LEAK (pass, 'spec view clean'). But the stamped G-PANEL-3/G-PANEL-1/G-EQ notes were taken against Solution.lean 5bddaa5c... and spec view 993b9c82..., and commit dcfe0c17a edited the spec between then and now. My recomputed spec view = 553 lines, sha256 77dab7e663041ae96923e54eb331e79f4c9e0375b0511447fbb6bc4051809bd1. The delta (git show dcfe0c17a) is a STRENGTHENING of the `returned` clause from an implication guarded on `refused = false` to a total `bif refused then [] else sc (checked z.values)`, plus `Scored.done { r with returned := [] }` on the refusal lane — orthogonal to the fix, and it adds no mechanism prose.

(2) SPEC REGION IDENTITY. markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) -> True, and the two spec views are BYTE-EQUAL (sv == svp), so the pre/post pair differ only in impl+proof and the view provably cannot be carrying a post-patch-only clause.

(3) LEAN STATUS. scripts/lean_verify.sh on shipped Solution.lean -> EXIT 0, no sorry/error (two dead-tactic linter warnings at 692 only). `#print axioms correct_fit` -> [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx, so the proof is real.

(4) THE DISCRIMINATOR IS SOLE AND PUBLIC — PROVED, NOT ASSERTED. The usual strip test fought the gold tactic block (the residual goals after removing the conjunct were trivial `checked (checked v) = checked v` and a reassociation, i.e. plumbing artifacts, not obstructions), so I replaced it with a STRONGER and fully machine-checked measurement: delta.lean puts the prepatch impl and the gold impl (renamed `gold_fit`) in ONE file over the shipped frozen spec regions and proves, for ALL x/ca/contamination and EVERY interpretation sc, that the two agree on `reference`, on `offset`, on `traversals`, and on the stored `scoreLater` entry-point program — `theorem delta_only_warned`, verify EXIT 0, zero sorry.

Two companion theorems pin where they part: `delta_warned_pre` proves the prepatch reports `warned = x.hasFeatureNames`, `delta_warned_gold` proves gold reports `warned = false`. So `warned = false` is provably the ONLY observable separating the buggy impl from the gold one. Control that the spec actually bites: ctl2.lean (full spec + prepatch impl + gold proof body verbatim) FAILS at exactly `case false.refine_1` with goal `(!false && true && xOrig.hasFeatureNames != false) = false` — unprovable at hasFeatureNames = true.

That sole discriminator is VERBATIM PUBLIC. problem_statement's 'Expected Results: Does not raise "X does not have valid feature names, but IsolationForest was fitted with feature names"' IS `warned = false` at fit time; the report even localises the cause to L337 `self.score_samples(X)` itself. There is a complete problem_statement-only derivation of the discriminator, so nothing here needed an unavoidability argument.

(5) THE MECHANISM PROSE I ADVERSARIALLY TARGETED, and why it is not a leak. Two lines are the only plausible gold-reconstruction candidates: `fitCompletes`'s 'the scoring path it uses there is the one that performs NO admissibility pass of its own' and post-conditions' 'the public entry point keeps its check'. Together they describe the gold edit's SHAPE (fit-time path unvalidated, public path still validating), so I tested whether they are forced behavioural facts or gratuitous disclosure.

They are forced: (a) I confirmed at base_commit that `accept_sparse=["csc"]` (line 291, fit) and `accept_sparse="csr"` (line 436, score_samples) BOTH pre-exist the patch — the patch changes neither — so the row/column asymmetry the prose narrates is not information about the edit; (b) the carve-out's consequence is a genuine post-patch observable I MEASURED in the official image swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-25931 with patch.diff applied via git apply: sparse + contamination=0.05 RAISES `ValueError: X should be in csr_matrix format, got csc_matrix` for both csc and csr input, while contamination='auto' succeeds (offset -0.5) and dense+contamination succeeds — and at the BASE commit the same csc+contamination fit SUCCEEDS (offset -0.5566).

A faithful spec must carve that regression-shaped divergence out or be false, so `fitCompletes` is load-bearing, not narration. The prose is also strictly behavioural: it never names `_score_samples`, `score_samples`, `_validate_data`, csr/csc, a private helper, or any 'add/rename/split' instruction.

(6) VOCABULARY SWEEP over the 553-line spec view: grep -niE for `_score_samples`|private|helper|patch|fix|bug|regress|previously|used to|no longer|'second validation'|'second time'|split|refactor|rename|csr|csc|L337|dataframe|pandas|numpy|np\.|sklearn|isolation|forest|check_is_fitted|`_validate_data`|score_samples|gold|correct(ed)|repair|solution -> ZERO substantive hits. The only matches are `hasFeatureNames` field/clause occurrences and ordinary comparative English ('rather than', 'instead of') inside modelling-rationale docstrings. Notably the phrase 'second' — the one word patch.diff's own added comment uses ('To avoid performing input validation a second time') and which appears in refinement.md and mapping.md — does NOT occur anywhere in the spec view.

**CONCLUSION:** the spec view pins the F2P behaviour using only language the public bug report already supplies, its sole discriminator is the report's own Expected Results, and its one mechanism-flavoured carve-out is a measured post-patch observable over pre-existing unpatched code. No line reconstructs the gold edit. NO-LEAKAGE.

OBSERVATIONS OUTSIDE MY FACET (not leakage, recorded for the ledger): (i) meta.json `region_hashes` are STALE against shipped bytes — recorded pure=3901291a/post-conditions=43a9ae0d/impl=65a15cc7/spec_view=0b26fac5 vs my recomputed 72cbef68/8346ef49/ab24176d/77dab7e6 — consistent with the dcfe0c17a edit landing without a region_hashes refresh; G-LEAK's own `sources` digest is fresh, so this does not undercut G-LEAK. (ii) G-EQ and G-PANEL-1 are stamped fail (BROKEN, atk_1.lean verifies but its patch fails 7/21 PASS_TO_PASS) against the OLDER 5bddaa5c bytes, so that finding is itself stale-routed and predates the returned-clause strengthening; a G-PANEL rollup fail means re-audit, not repair. Neither affects this facet. (iii) Solution_prepatch.lean's proof region is a bare `sorry` by design, so the honest control had to graft the gold proof body onto the prepatch impl — which is what ctl2.lean does.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
