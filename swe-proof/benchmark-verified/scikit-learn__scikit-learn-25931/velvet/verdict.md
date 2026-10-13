# P2 adversarial audit — scikit-learn__scikit-learn-25931

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 10 | `atk_4_fit_vacuous_scorable_default.lean`, `atk_5_fit_vacuous_scorable_rescreen.lean`, `atk_6_fit_vacuous_hassamples_rescreen.lean`, `atk_7_fit_guarded_silent_rescreen.lean`, `atk_8_public_vacuous_advisory_none.lean`, `atk_9_public_vacuous_scorable_rescreen.lean`, `atk_10_public_double_screen_reachable.lean`, +3 more |
| does not verify against this specification, so the specification excludes it | 4 | `atk_0_prepatch_unguarded_rescreen.lean`, `atk_1_retained_offset_div_zero.lean`, `atk_2_retained_offset_inv_zero.lean`, `atk_3_fit_value_keyed_on_advisory.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND - no verifying wrong impl's faithful patch failed to resolve. 14 same-spec attacks (same_spec True for all 14 + pos_control); 4 correctly REJECTED, 10 VERIFIED, and every one of those 10 had its faithful refined patch materialized and EXECUTED through the official harness: all 10 resolved=True, F2P 1/1, P2P 21/21, identical to the certified gold control. The prior verdict.md BROKEN mechanism (offset : Rat, off/0 and (off-off) inverse) is now genuinely CLOSED by the opaque Offset carrier: atk_1 fails to elaborate with 'failed to synthesize HDiv Offset N', atk_2 with 'failed to synthesize HSub Offset Offset'. Prepatch reproduced on the discriminating goal. KEY MEASUREMENT (probe2 in the official image, gold+test patch, 22 passed): instrumenting _score_samples and splitting sites by whether fit's frame is on the stack shows the fit tail has exactly 5 reachable sites, and at EVERY ONE hasSamples=True and scorableAsGiven=True - so the vacuous-branch attacks atk_4/5/6 and the public-lane atk_8/9 misbehave only in branches no graded test enters, which is why they resolve; they are genuine spec-permitted rivals, not spec defects. screenAdvises(presentPrepared samples) is TRUE at exactly one site (the F2P test, DataFrame fit, contamination=0.05) and FALSE at the 4 contamination P2P sites, making the advisory guard a perfect F2P/P2P discriminator - which is precisely why atk_7 (the bundle's own declared positive control pos-fit-provably-silent-rescreen) had to be resolve-checked rather than trusted, and it resolves 22/22, confirming the guarded-silent-rescreen residue is harmless end to end as refinement.md A2' claims.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch_unguarded_rescreen.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,8 +460,9 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
+    -- PREPATCH: route the already-prepared fitting matrix back through the SCREEN
+    -- before reading the order statistic (the defect this cell is about).
+    let _rescreened ← screenHandle (presentPrepared samples)
     let scores := anomalyScores samples
     let off := percentileAt scores q
     return off
```

Attack 2 — `atk_1_retained_offset_div_zero.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,13 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
+    -- RETAINED COUNTEREXAMPLE (prior G-EQ BROKEN, atk_7_fit_rat_divide_by_zero):
+    -- add a correction that divides the recorded offset by zero. Total in the
+    -- reference language (= 0), non-finite in the repository.
     let scores := anomalyScores samples
     let off := percentileAt scores q
-    return off
+    let correction := off / 0
+    return off + correction
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 3 — `atk_2_retained_offset_inv_zero.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,12 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
+    -- RETAINED COUNTEREXAMPLE, second spelling (prior atk_10_fit_rat_inverse_of_zero):
+    -- add the reciprocal of the offset's own zero spread.
     let scores := anomalyScores samples
     let off := percentileAt scores q
-    return off
+    let spread := off - off
+    return off + spread⁻¹
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 4 — `atk_3_fit_value_keyed_on_advisory.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,12 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
-    let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    -- Condition the RECORDED VALUE on the labelling advisory: report the requestless
+    -- path's constant where a report would be drawn, the order statistic otherwise.
+    if screenAdvises (presentPrepared samples) then
+      return defaultOffset
+    else
+      return percentileAt (anomalyScores samples) q
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 5 — `atk_4_fit_vacuous_scorable_default.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,13 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
-    let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    -- Branch on whether the scorer can consume this matrix as it stands. Where it
+    -- can, read the order statistic; where it cannot, record the requestless
+    -- path's constant instead (the branch this method's own fence excludes).
+    if scorableAsGiven samples then
+      return percentileAt (anomalyScores samples) q
+    else
+      return defaultOffset
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 6 — `atk_5_fit_vacuous_scorable_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,14 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
-    let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    -- Branch on whether the scorer can consume this matrix as it stands. Where it
+    -- cannot, put the matrix back through the SCREEN first and then read the order
+    -- statistic; where it can, read the order statistic directly.
+    if scorableAsGiven samples then
+      return percentileAt (anomalyScores samples) q
+    else
+      let _rescreened ← screenHandle (presentPrepared samples)
+      return percentileAt (anomalyScores samples) q
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 7 — `atk_6_fit_vacuous_hassamples_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,14 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
-    let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    -- Branch on whether this matrix holds a sample at all. Where it does, read the
+    -- order statistic; where it does not, screen it first and then read it (the
+    -- branch this method's sample fence excludes).
+    if hasSamples samples then
+      return percentileAt (anomalyScores samples) q
+    else
+      let _rescreened ← screenHandle (presentPrepared samples)
+      return percentileAt (anomalyScores samples) q
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 8 — `atk_7_fit_guarded_silent_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,13 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
-    let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    -- Screen the prepared data again, but only on the branch where it is PROVABLE
+    -- that no report can be drawn about it; read the order statistic either way.
+    if screenAdvises (presentPrepared samples) then
+      return percentileAt (anomalyScores samples) q
+    else
+      let _accepted ← screenHandle (presentPrepared samples)
+      return percentileAt (anomalyScores samples) q
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 9 — `atk_8_public_vacuous_advisory_none.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -378,13 +378,17 @@
                    else some (scoreValues (anomalyScores (preparedOf handle)))
   do
     -- impl-start
-    -- Fresh handle: screen it first, and serve the scores of what that screen
-    -- prepared only where it accepted the handle.
-    let accepted ← screenHandle (presentCaller handle)
-    if accepted then
-      return some (scoreValues (anomalyScores (preparedOf handle)))
+    -- Where the screen would draw a labelling advisory about the caller's handle,
+    -- report the handle unusable instead of screening it; otherwise screen and
+    -- serve the scores of what that screen prepared.
+    if screenAdvises (presentCaller handle) then
+      return none
     else
-      return none
+      let accepted ← screenHandle (presentCaller handle)
+      if accepted then
+        return some (scoreValues (anomalyScores (preparedOf handle)))
+      else
+        return none
     -- impl-end
 
 prove_correct scorePublic by
```

Attack 10 — `atk_9_public_vacuous_scorable_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -378,11 +378,16 @@
                    else some (scoreValues (anomalyScores (preparedOf handle)))
   do
     -- impl-start
-    -- Fresh handle: screen it first, and serve the scores of what that screen
-    -- prepared only where it accepted the handle.
+    -- Screen the caller's handle; then, where the scorer cannot consume the matrix
+    -- that screen prepared, put that prepared matrix through the screen as well
+    -- before serving the scores.
     let accepted ← screenHandle (presentCaller handle)
     if accepted then
-      return some (scoreValues (anomalyScores (preparedOf handle)))
+      if scorableAsGiven (preparedOf handle) then
+        return some (scoreValues (anomalyScores (preparedOf handle)))
+      else
+        let _second ← screenHandle (presentPrepared (preparedOf handle))
+        return some (scoreValues (anomalyScores (preparedOf handle)))
     else
       return none
     -- impl-end
```

Attack 11 — `atk_10_public_double_screen_reachable.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -378,8 +378,9 @@
                    else some (scoreValues (anomalyScores (preparedOf handle)))
   do
     -- impl-start
-    -- Fresh handle: screen it first, and serve the scores of what that screen
-    -- prepared only where it accepted the handle.
+    -- Fresh handle: screen it, screen it once more to be sure, and serve the scores
+    -- of what the screen prepared only where it accepted the handle.
+    let _first ← screenHandle (presentCaller handle)
     let accepted ← screenHandle (presentCaller handle)
     if accepted then
       return some (scoreValues (anomalyScores (preparedOf handle)))
```

Attack 12 — `atk_11_fit_duplicate_scorer_value_reachable.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,14 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
-    let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    -- Take the screen-free scores, and take them again to check the second
+    -- sequence is non-empty before reading the order statistic off it.
+    let s1 := anomalyScores samples
+    let s2 := anomalyScores samples
+    if (scoreValues s2).length = 0 then
+      return percentileAt s2 q
+    else
+      return percentileAt s1 q
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 13 — `atk_12_fit_nat_div_zero_guard_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,15 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
+    -- Read the screen-free scores and gate on the average number of scores per
+    -- empty chunk; where that gate does not hold, screen the matrix again first.
     let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    let gate := (scoreValues scores).length / 0
+    if gate = 0 then
+      return percentileAt scores q
+    else
+      let _rescreened ← screenHandle (presentPrepared samples)
+      return percentileAt scores q
     -- impl-end
 
 prove_correct fitComputeOffset by
```

Attack 14 — `atk_13_fit_rat_div_zero_guard_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -460,11 +460,16 @@
   ensures offset = percentileAt (anomalyScores samples) q
   do
     -- impl-start
-    -- The data is already prepared: take its screen-free scores and read off the
-    -- requested order statistic. Nothing here screens the matrix again.
+    -- Read the screen-free scores and gate on the reciprocal of the spread of the
+    -- score count with itself; where the gate does not hold, screen again first.
     let scores := anomalyScores samples
-    let off := percentileAt scores q
-    return off
+    let n := ((scoreValues scores).length : Rat)
+    let gate := n / (n - n)
+    if gate = 0 then
+      return percentileAt scores q
+    else
+      let _rescreened ← screenHandle (presentPrepared samples)
+      return percentileAt scores q
     -- impl-end
 
 prove_correct fitComputeOffset by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all work confined there; own base_commit worktree at $D/wt from the bare mirror; no git stash; bundle untouched).

### COMMANDS (from swe-proof):
  same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('$D/atk_N.lean').read(), b.language))"  -> True for all 14 attacks + pos_control
  verify:    bash scripts/lean_verify.sh $D/<name>.lean   (launched 4-way concurrent in batches, as briefed)
  resolve:   setsid python $D/resolve_one.py <name>  -> swebench_unified.harness.run_resolve(iid, patch, timeout=3600, retries=1); JSON at $D/<name>.resolve.json
  apply:     cd $D/wt && git apply --check $D/<name>.diff  -> OK for all 10 patches + gold, re-checked AFTER the runs
RESOLVES RUN STRICTLY ONE AT A TIME (11 sequential runs on the one instance), so no ImageNotFound/404; the gold control survived and is certified.

### RESULTS (verify exit | official resolve):
  atk_0_prepatch_unguarded_rescreen        1 | n/a  PREPATCH REPRODUCED, exit 1 on '|- screenAdvises (presentPrepared samples) = false' under case <<require_1: hasSamples samples = true>> at :471:31 - byte-identical to the goal refinement.md A and verdict.md quote, so G-DIFF is genuine
  atk_1_retained_offset_div_zero           1 | n/a  retained prior-BROKEN counterexample, now CLOSED: 'failed to synthesize HDiv Offset N'
  atk_2_retained_offset_inv_zero           1 | n/a  retained, second spelling, CLOSED: 'failed to synthesize HSub Offset Offset'
  atk_3_fit_value_keyed_on_advisory        1 | n/a  correctly rejected: |- defaultOffset = percentileAt (anomalyScores samples) q (ungrounded oracle - the value may not be keyed on the labelling)
  atk_4_fit_vacuous_scorable_default       0 | resolved=True  F2P 1/1 P2P 21/21
  atk_5_fit_vacuous_scorable_rescreen      0 | resolved=True  F2P 1/1 P2P 21/21
  atk_6_fit_vacuous_hassamples_rescreen    0 | resolved=True  F2P 1/1 P2P 21/21
  atk_7_fit_guarded_silent_rescreen        0 | resolved=True  F2P 1/1 P2P 21/21  (bundle's declared positive control, now CONFIRMED end-to-end rather than trusted)
  atk_8_public_vacuous_advisory_none       0 | resolved=True  F2P 1/1 P2P 21/21
  atk_9_public_vacuous_scorable_rescreen   0 | resolved=True  F2P 1/1 P2P 21/21
  atk_10_public_double_screen_reachable    0 | resolved=True  F2P 1/1 P2P 21/21  (REACHABLE extra screening action: advises=False at all 55 measured public sites, so this branch IS taken; still resolves because `_validate_data` is idempotent and value-neutral on an already-prepared matrix)
  atk_11_fit_duplicate_scorer_value_reachable 0 | resolved=True F2P 1/1 P2P 21/21  (tests the R-VALUE rule at a reachable site: two occurrences of anomalyScores samples; faithful image binds one call and uses it twice, per mapping.md 2.1)
  atk_12_fit_nat_div_zero_guard_rescreen   0 | resolved=True  F2P 1/1 P2P 21/21  (R-ARITH residue as a GUARD, not a discard)
  atk_13_fit_rat_div_zero_guard_rescreen   0 | resolved=True  F2P 1/1 P2P 21/21  (same, in Rat, via a produced sequence's length)
  gold_control (patch.diff verbatim)         | resolved=True  F2P 1/1 P2P 21/21  <== CERTIFIED, so every attack result above is meaningful
  pos_control (frozen Solution.lean, sha 5bc4ed3f2dfd) 0 | non-vacuity OK

**ATTACK CLASS DISTINCTNESS:** prepatch (atk_0); partial-domain on the RESULT carrier's arithmetic, retained from the prior BROKEN record (atk_1, atk_2 - both now inexpressible); ungrounded-oracle / value keyed on the labelling (atk_3); partial-domain on the fit tail's OWN require fences, forging the value (atk_4) and smuggling the inadmissible re-screen into the fence-excluded branch (atk_5 scorableAsGiven, atk_6 hasSamples); control-flow-effect under a discharged guard (atk_7); partial-domain on the public lane's advisory fence (atk_8) and its scorableAsGiven fence with the inadmissible re-screen (atk_9); REACHABLE-SITE invocation multiplicity of the screen (atk_10) and of the scorer value (atk_11); boundary/R-ARITH residue promoted from a discarded number to a load-bearing GUARD (atk_12 Nat, atk_13 Rat).

WHY I DO NOT COUNT atk_10/11/12/13 AS BREAKS, having deliberately built them to be the sharpest available shapes. atk_12/13 attack the one residue mapping.md 2.2 publishes as unfenceable, but PROMOTED: 2.2 only excuses a number the text DISCARDS ('dead text'), whereas mine CONTROLS FLOW, gating the inadmissible re-screen. They verify because Nat/Rat division by zero is 0 by reference-language law, so the re-screen branch is unreachable in Lean. Under the published R-ARITH reading the faithful image reads the term back as the constant 0 and takes the ordinary branch - which is what I materialized, and it resolves.

I note the honest residual: a LITERAL per-operator transliteration would instead raise ZeroDivisionError at every reachable fit-tail site, so the safety of this shape rests entirely on R-ARITH being the intended reading. That rule is stated normatively in mapping.md 2.2 AND written into the frozen axiom comment of Solution.lean itself (so it is part of what the spec says, not an after-the-fact gloss) and it is grounded by measurement in both directions, so I apply it rather than override it.

Same for atk_11 under R-VALUE, likewise frozen into the axiom block. atk_10 is a real extra screening ACTION at a reachable site and it still resolves - because a second `_validate_data` on an already-prepared, label-free matrix is value-neutral and draws no advisory, exactly the 'what remains admissible is also harmless' case the spec states openly.

A-LEG AUDIT (my assigned focus). No kind-3; refinement.md C's claim checks out. All 13 legs are R / A-reference / I, and NOT ONE is A-consumed: A1 R, A2 R, A2' R, A2'' R, A3 A-reference+R, A4 retired, A5 A-reference, A6 R, B1 I, B2 I+A-reference, B3 A-reference+R, B3' A-reference+R, B4 A-reference. Confirmed mechanically that no axiom can be consumed: all 18 declarations in the frozen axioms region are bare 'axiom <name> : <type>' function/type symbols with no :=, no Prop, no ensures/require, so the proofs can only use symbol identity. Tag census over the table: 5 R, 3 A-reference(+R), 2 A-reference, 1 I, 1 I(+A-reference), 1 retired.

A-REFERENCE CORRESPONDENCE TO THE REAL CALLEES - verified line by line against the base_commit worktree, all exact: A5 percentileAt == np.percentile at `_iforest`.py:348; A3/B4 anomalyScores == -self.`_compute_chunked_score_samples` at :440-442; B3'/B1/B2 preparedOf and the screen == `_validate_data`(X, accept_sparse='csr', dtype=np.float32, reset=False) at :436, with score_samples at :407; A1/A2' the fit-side prepared matrix == `_validate_data`(X, accept_sparse=['csc'], dtype=tree_dtype) at :291; defaultOffset == -0.5 at :344 (the requestless path). One citation slip, NOT a wrong binding and already noted by the prior audit: refinement.md cites `_get_feature_names` as base.py:1873; it is defined at sklearn/utils/validation.py:1870 and re-exported/used from base.py. Advisory only.

SPEC STRENGTHS CONFIRMED (so any repair should not touch them): the screening-delta discipline A2' is genuinely sound - the unguarded fit re-screen (atk_0) is rejected on exactly the advisory obligation while the guarded variant (atk_7) verifies AND resolves, so the admissibility wall admits exactly the harmless re-screens as A2' claims; the ensures cannot be keyed on the labelling (atk_3 rejected); and the opaque Offset/Scores/Point/Score carriers really do close the retained arithmetic and partial-read family (atk_1, atk_2 fail to elaborate).

OBSERVATION FOR THE RECORD, not a defect claim: the fit tail's two require fences (scorableAsGiven, hasSamples) are VACUOUS on the graded surface - measured 0 reachable sites where either is false. They are faithfulness fences (they exclude regions where the repository reports nothing, per mapping.md 5) rather than fix legs, and refinement.md A5/B3 already says exactly that. The consequence is only that a rival may put arbitrary conduct in those branches and still resolve, which is spec-permitted behaviour on the tested inputs and precisely what refinement.md's claim is scoped to ('behaviourally equal to the gold patch ON THE TESTED INPUTS').

EVIDENCE in $D: <name>.lean, <name>.log (verify), <name>.diff (faithful patches), <name>.resolve.json + .resolve.log (harness), gen.py/gen2.py/gen3.py (attack generators), mkpatch.py/mkpatch2.py (patch materializers), resolve_one.py (serial resolve driver), probe/ + probe2/ (official-image reachability instrumentation), pre/ (fast in-image pre-screen, all 7 candidates 22 passed), REACHABILITY.md, verify_results.txt. No exit 124 anywhere; every resolve completed with patch_successfully_applied=True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 10 | `atk_4_fit_vacuous_scorable_default.lean`, `atk_5_fit_vacuous_scorable_rescreen.lean`, `atk_6_fit_vacuous_hassamples_rescreen.lean`, `atk_7_fit_guarded_silent_rescreen.lean`, `atk_8_public_vacuous_advisory_none.lean`, `atk_9_public_vacuous_scorable_rescreen.lean`, `atk_10_public_double_screen_reachable.lean`, +3 more |
| does not verify against this specification, so the specification excludes it | 4 | `atk_0_prepatch_unguarded_rescreen.lean`, `atk_1_retained_offset_div_zero.lean`, `atk_2_retained_offset_inv_zero.lean`, `atk_3_fit_value_keyed_on_advisory.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND - no verifying wrong impl's faithful patch failed to resolve. 14 same-spec attacks (same_spec True for all 14 + pos_control); 4 correctly REJECTED, 10 VERIFIED, and every one of those 10 had its faithful refined patch materialized and EXECUTED through the official harness: all 10 resolved=True, F2P 1/1, P2P 21/21, identical to the certified gold control. The prior verdict.md BROKEN mechanism (offset : Rat, off/0 and (off-off) inverse) is now genuinely CLOSED by the opaque Offset carrier: atk_1 fails to elaborate with 'failed to synthesize HDiv Offset N', atk_2 with 'failed to synthesize HSub Offset Offset'. Prepatch reproduced on the discriminating goal. KEY MEASUREMENT (probe2 in the official image, gold+test patch, 22 passed): instrumenting _score_samples and splitting sites by whether fit's frame is on the stack shows the fit tail has exactly 5 reachable sites, and at EVERY ONE hasSamples=True and scorableAsGiven=True - so the vacuous-branch attacks atk_4/5/6 and the public-lane atk_8/9 misbehave only in branches no graded test enters, which is why they resolve; they are genuine spec-permitted rivals, not spec defects. screenAdvises(presentPrepared samples) is TRUE at exactly one site (the F2P test, DataFrame fit, contamination=0.05) and FALSE at the 4 contamination P2P sites, making the advisory guard a perfect F2P/P2P discriminator - which is precisely why atk_7 (the bundle's own declared positive control pos-fit-provably-silent-rescreen) had to be resolve-checked rather than trusted, and it resolves 22/22, confirming the guarded-silent-rescreen residue is harmless end to end as refinement.md A2' claims.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_0_prepatch_unguarded_rescreen.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_retained_offset_div_zero.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_retained_offset_inv_zero.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_fit_value_keyed_on_advisory.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_fit_vacuous_scorable_default.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_5_fit_vacuous_scorable_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_6_fit_vacuous_hassamples_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7_fit_guarded_silent_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_8_public_vacuous_advisory_none.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_9_public_vacuous_scorable_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_10_public_double_screen_reachable.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_11_fit_duplicate_scorer_value_reachable.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_12_fit_nat_div_zero_guard_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_13_fit_rat_div_zero_guard_rescreen.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all work confined there; own base_commit worktree at $D/wt from the bare mirror; no git stash; bundle untouched).

### COMMANDS (from swe-proof):
  same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('$D/atk_N.lean').read(), b.language))"  -> True for all 14 attacks + pos_control
  verify:    bash scripts/lean_verify.sh $D/<name>.lean   (launched 4-way concurrent in batches, as briefed)
  resolve:   setsid python $D/resolve_one.py <name>  -> swebench_unified.harness.run_resolve(iid, patch, timeout=3600, retries=1); JSON at $D/<name>.resolve.json
  apply:     cd $D/wt && git apply --check $D/<name>.diff  -> OK for all 10 patches + gold, re-checked AFTER the runs
RESOLVES RUN STRICTLY ONE AT A TIME (11 sequential runs on the one instance), so no ImageNotFound/404; the gold control survived and is certified.

### RESULTS (verify exit | official resolve):
  atk_0_prepatch_unguarded_rescreen        1 | n/a  PREPATCH REPRODUCED, exit 1 on '|- screenAdvises (presentPrepared samples) = false' under case <<require_1: hasSamples samples = true>> at :471:31 - byte-identical to the goal refinement.md A and verdict.md quote, so G-DIFF is genuine
  atk_1_retained_offset_div_zero           1 | n/a  retained prior-BROKEN counterexample, now CLOSED: 'failed to synthesize HDiv Offset N'
  atk_2_retained_offset_inv_zero           1 | n/a  retained, second spelling, CLOSED: 'failed to synthesize HSub Offset Offset'
  atk_3_fit_value_keyed_on_advisory        1 | n/a  correctly rejected: |- defaultOffset = percentileAt (anomalyScores samples) q (ungrounded oracle - the value may not be keyed on the labelling)
  atk_4_fit_vacuous_scorable_default       0 | resolved=True  F2P 1/1 P2P 21/21
  atk_5_fit_vacuous_scorable_rescreen      0 | resolved=True  F2P 1/1 P2P 21/21
  atk_6_fit_vacuous_hassamples_rescreen    0 | resolved=True  F2P 1/1 P2P 21/21
  atk_7_fit_guarded_silent_rescreen        0 | resolved=True  F2P 1/1 P2P 21/21  (bundle's declared positive control, now CONFIRMED end-to-end rather than trusted)
  atk_8_public_vacuous_advisory_none       0 | resolved=True  F2P 1/1 P2P 21/21
  atk_9_public_vacuous_scorable_rescreen   0 | resolved=True  F2P 1/1 P2P 21/21
  atk_10_public_double_screen_reachable    0 | resolved=True  F2P 1/1 P2P 21/21  (REACHABLE extra screening action: advises=False at all 55 measured public sites, so this branch IS taken; still resolves because `_validate_data` is idempotent and value-neutral on an already-prepared matrix)
  atk_11_fit_duplicate_scorer_value_reachable 0 | resolved=True F2P 1/1 P2P 21/21  (tests the R-VALUE rule at a reachable site: two occurrences of anomalyScores samples; faithful image binds one call and uses it twice, per mapping.md 2.1)
  atk_12_fit_nat_div_zero_guard_rescreen   0 | resolved=True  F2P 1/1 P2P 21/21  (R-ARITH residue as a GUARD, not a discard)
  atk_13_fit_rat_div_zero_guard_rescreen   0 | resolved=True  F2P 1/1 P2P 21/21  (same, in Rat, via a produced sequence's length)
  gold_control (patch.diff verbatim)         | resolved=True  F2P 1/1 P2P 21/21  <== CERTIFIED, so every attack result above is meaningful
  pos_control (frozen Solution.lean, sha 5bc4ed3f2dfd) 0 | non-vacuity OK

**ATTACK CLASS DISTINCTNESS:** prepatch (atk_0); partial-domain on the RESULT carrier's arithmetic, retained from the prior BROKEN record (atk_1, atk_2 - both now inexpressible); ungrounded-oracle / value keyed on the labelling (atk_3); partial-domain on the fit tail's OWN require fences, forging the value (atk_4) and smuggling the inadmissible re-screen into the fence-excluded branch (atk_5 scorableAsGiven, atk_6 hasSamples); control-flow-effect under a discharged guard (atk_7); partial-domain on the public lane's advisory fence (atk_8) and its scorableAsGiven fence with the inadmissible re-screen (atk_9); REACHABLE-SITE invocation multiplicity of the screen (atk_10) and of the scorer value (atk_11); boundary/R-ARITH residue promoted from a discarded number to a load-bearing GUARD (atk_12 Nat, atk_13 Rat).

WHY I DO NOT COUNT atk_10/11/12/13 AS BREAKS, having deliberately built them to be the sharpest available shapes. atk_12/13 attack the one residue mapping.md 2.2 publishes as unfenceable, but PROMOTED: 2.2 only excuses a number the text DISCARDS ('dead text'), whereas mine CONTROLS FLOW, gating the inadmissible re-screen. They verify because Nat/Rat division by zero is 0 by reference-language law, so the re-screen branch is unreachable in Lean. Under the published R-ARITH reading the faithful image reads the term back as the constant 0 and takes the ordinary branch - which is what I materialized, and it resolves.

I note the honest residual: a LITERAL per-operator transliteration would instead raise ZeroDivisionError at every reachable fit-tail site, so the safety of this shape rests entirely on R-ARITH being the intended reading. That rule is stated normatively in mapping.md 2.2 AND written into the frozen axiom comment of Solution.lean itself (so it is part of what the spec says, not an after-the-fact gloss) and it is grounded by measurement in both directions, so I apply it rather than override it.

Same for atk_11 under R-VALUE, likewise frozen into the axiom block. atk_10 is a real extra screening ACTION at a reachable site and it still resolves - because a second `_validate_data` on an already-prepared, label-free matrix is value-neutral and draws no advisory, exactly the 'what remains admissible is also harmless' case the spec states openly.

A-LEG AUDIT (my assigned focus). No kind-3; refinement.md C's claim checks out. All 13 legs are R / A-reference / I, and NOT ONE is A-consumed: A1 R, A2 R, A2' R, A2'' R, A3 A-reference+R, A4 retired, A5 A-reference, A6 R, B1 I, B2 I+A-reference, B3 A-reference+R, B3' A-reference+R, B4 A-reference. Confirmed mechanically that no axiom can be consumed: all 18 declarations in the frozen axioms region are bare 'axiom <name> : <type>' function/type symbols with no :=, no Prop, no ensures/require, so the proofs can only use symbol identity. Tag census over the table: 5 R, 3 A-reference(+R), 2 A-reference, 1 I, 1 I(+A-reference), 1 retired.

A-REFERENCE CORRESPONDENCE TO THE REAL CALLEES - verified line by line against the base_commit worktree, all exact: A5 percentileAt == np.percentile at `_iforest`.py:348; A3/B4 anomalyScores == -self.`_compute_chunked_score_samples` at :440-442; B3'/B1/B2 preparedOf and the screen == `_validate_data`(X, accept_sparse='csr', dtype=np.float32, reset=False) at :436, with score_samples at :407; A1/A2' the fit-side prepared matrix == `_validate_data`(X, accept_sparse=['csc'], dtype=tree_dtype) at :291; defaultOffset == -0.5 at :344 (the requestless path). One citation slip, NOT a wrong binding and already noted by the prior audit: refinement.md cites `_get_feature_names` as base.py:1873; it is defined at sklearn/utils/validation.py:1870 and re-exported/used from base.py. Advisory only.

SPEC STRENGTHS CONFIRMED (so any repair should not touch them): the screening-delta discipline A2' is genuinely sound - the unguarded fit re-screen (atk_0) is rejected on exactly the advisory obligation while the guarded variant (atk_7) verifies AND resolves, so the admissibility wall admits exactly the harmless re-screens as A2' claims; the ensures cannot be keyed on the labelling (atk_3 rejected); and the opaque Offset/Scores/Point/Score carriers really do close the retained arithmetic and partial-read family (atk_1, atk_2 fail to elaborate).

OBSERVATION FOR THE RECORD, not a defect claim: the fit tail's two require fences (scorableAsGiven, hasSamples) are VACUOUS on the graded surface - measured 0 reachable sites where either is false. They are faithfulness fences (they exclude regions where the repository reports nothing, per mapping.md 5) rather than fix legs, and refinement.md A5/B3 already says exactly that. The consequence is only that a rival may put arbitrary conduct in those branches and still resolve, which is spec-permitted behaviour on the tested inputs and precisely what refinement.md's claim is scoped to ('behaviourally equal to the gold patch ON THE TESTED INPUTS').

EVIDENCE in $D: <name>.lean, <name>.log (verify), <name>.diff (faithful patches), <name>.resolve.json + .resolve.log (harness), gen.py/gen2.py/gen3.py (attack generators), mkpatch.py/mkpatch2.py (patch materializers), resolve_one.py (serial resolve driver), probe/ + probe2/ (official-image reachability instrumentation), pre/ (fast in-image pre-screen, all 7 candidates 22 passed), REACHABILITY.md, verify_results.txt. No exit 124 anywhere; every resolve completed with patch_successfully_applied=True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** faithfulness-break attacker (is the spec TOO STRONG / does a modeled function disagree with the real callee on some in-domain input?). VERDICT: FAITHFUL — no diverging input found after an executable differential search with proven-live negative controls.

REFERENCE DISCIPLINE (delta direction confirmed, so I did not condemn the patch's own fix). Fresh `git worktree --detach e3d1f9ac39e4bf0f31430e779acc50fb05fe1b64` from the upstream repository with the gold patch applied (byte-identical to gp2f_patch_25931.diff and to the dataset's `patch` field for this instance — diffed, IDENTICAL). Executable probes ran in swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-25931:latest (/testbed at ccfb450bd, whose parent IS e3d1f9ac3; sklearn 1.3.dev0, scipy 1.13.0, numpy 1.26.4, pandas 2.2.3) with /gold.diff applied so `_score_samples` exists. POSITIVE DELTA CHECK: post-patch `IsolationForest(contamination=0.05).fit(pd.DataFrame({'a':[-1.1,0.3,0.5,100]}))` emits ZERO feature-name warnings, i.e. the bug is fixed; `fitComputeOffset` contains no screen call, so Solution.lean models the POST-patch (no-re-screen) side. I therefore did NOT treat the removed re-screen as a divergence.

**PRELIMINARIES.** (a) markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) == True — the spec region under review is the one G-DIFF/G-GOLD exercised (the two files differ only inside fitComputeOffset's impl region, where prepatch adds `let _rescreened <- screenHandle (presentPrepared samples)`). (b) `scripts/lean_verify.sh GPF2b_sol_25931.lean` -> EXIT=0 (elaborates, no sorry/error).

**ENSURES CHECKED AGAINST THE REAL POST-PATCH CALLEES.** Violations counted ONLY on inputs satisfying every `require`. Instantiation: screenRefuses/screenAdvises = whether `_validate_data(X, accept_sparse='csr', dtype=np.float32, reset=False)` raises / emits a feature-name message (narrowed to the two feature-name prefixes so unrelated pandas/numpy warnings cannot fake an advisory); preparedOf = what it returns; anomalyScores = `-_compute_chunked_score_samples`; scorableAsGiven = whether that scorer consumes the prepared matrix; hasSamples = prep.shape[0] >= 1.
1. scorePublic (`result = if screenRefuses (presentCaller handle) then none else some (scoreValues (anomalyScores (preparedOf handle)))`): battery A = 312 handles across 10 model configurations (labelled/unlabelled x n 5..40, d 1..5, max_features 1.0/0.6/0.5) -> 145 in-domain, 0 branch and 0 value mismatches (np.array_equal, bit-exact, not allclose). Battery B = 31 adversarial in-domain handles x 2 model labellings incl. pandas Int64/Float64/object/bool/SparseDtype extension frames, duplicate column names, np.ma masked arrays, longdouble, complex, str-dtype, `2**62` int64, 3.5e38, -inf, all-zeros, Fortran order, strided views, 8 sparse container kinds -> 0 violations, with BOTH branches live (11 none / 20 some), so the clause is not vacuously satisfied on one side.
2. fitComputeOffset (`offset = percentileAt (anomalyScores samples) q`): 400 randomized real fits (contamination in {1e-300, 1e-9, 1e-6, 0.001, 0.01, 0.1, 0.25, 0.3, 0.4999999, 0.5}, n 1..45, d 1..6, max_features 1.0/0.6/0.5/0.34, labelled/unlabelled/csc-sparse) -> 305 in-domain, 0 violations: recorded `clf.offset_` was `==` (bit-identical) to `np.percentile(-_compute_chunked_score_samples(fit's own prepared matrix), 100.0*contamination)` in 305/305. Plus boundary cases: n=1 (sequence length 1) at contamination 1e-6 and 0.5, and an all-identical score sequence — all match. Zero fit-path feature-name advisories across the run.
3. screenHandle (`accepted = if screenRefuses then false else true`): consistent across the refusal battery (disagreeing width, 0 samples, 1e300 beyond float32, -inf, complex, mixed-type columns, permuted/renamed labellings all raise; the ordinary handle does not — negative control present).

NEGATIVE CONTROLS PROVING THE HARNESS HAS TEETH (this is what distinguishes a real clean run from a rubber stamp). I re-ran the identical comparator with deliberately WRONG postconditions; every one fired while the spec as written fired zero: NC1 wrong sign (+chunked) 20/36; NC2 branch flipped 36/36; NC3 screen-never-refuses 16/36; NC4 wrong matrix 20/36; NC5 defaultOffset(-0.5) 113/120; NC6 median instead of q 96/120; NC7 percentile of the un-negated sequence 120/120; NC8 q=contamination not `100*contamination` 109/120. So a divergence of the kind I was hunting would have been detected.

### Over-strength angles I attacked and which failed
(i) 'The requires are convenience fences that hide a disagreement.' `require scorableAsGiven (preparedOf handle) = true` excludes exactly {csr_array, csc_array, coo_array, narrower-than-recorded dense, csc fed straight to the scorer} — I measured that csr_array/csc_array/coo_array ARE accepted by the public screen (refuses=0, advises=0), the scorer then raises 'X should be in csr_matrix format, got csr_array', and `score_samples` raises too, so the excluded region is exactly where the repo has no scores; the consumable containers (dense, csr_matrix, csc_matrix, coo_matrix, bsr, dia, lil of the recorded width) are all live controls INSIDE the fence and all scored to the served values. Not vacuous, not overbroad.

(ii) 'percentileAt over-promises a total value.' Reachable-point provenance holds: contamination is refused at <=0 and >0.5 (InvalidParameterError at -1e-9, 0.0, 0.5+1e-16, 0.500001, 1.0), so reachable q = `100*contamination` lies in (0, 50]; np.percentile refuses q=-1e-9 and q=100+1e-9 but is total at 0/1e-321/50/100 and on the whole in-range interval, and refuses an empty sequence (IndexError) — which the hasSamples fence excludes (a 0-sample prepared matrix makes the chunked scorer raise gen_batches InvalidParameterError, so it is out of domain twice over).

(iii) 'An admissible fit could record a non-finite offset the clause claims a value for.' 201 admissible fits at scales 1e-38..3.5e38 -> 0 non-finite offsets.

(iv) 'R-VALUE (multiple occurrences = one production) is unsound.' anomalyScores is a function of the prepared matrix alone: screening 1x/2x/3x gives bit-identical sequences, and working_memory 1/16/1024 (i.e. different chunking) gives bit-identical sequences. preparedOf is value-neutral (prep == float32 cast of the presented numbers). scoreValues is the identity (length == n_samples, all finite, 0/60 violations).

(v) 'The advisory conditions a value, so omitting it from the value clause is wrong.' It does not — screen counts confirm the asymmetry the two-method surface rests on: score_samples performs exactly 1 `_validate_data`, `_score_samples` and `_compute_chunked_score_samples` perform 0.

(vi) screenRefuses/screenAdvises are decided by INSPECTION and are deterministic: 5 repeated screens of each of bare/df_match/df_perm/narrow/huge gave a single stable (refuses, advises) pair each.

CAVEATS, stated so this verdict is not read as broader than it is. (a) raise <-> `none` is a bundle-wide modeling convention, applied consistently on both branches; I treated it as intended rather than refutable. (b) Probes are single-version (the instance's pinned testbed image); container-kind behavior is scipy-version-sensitive, but that is the version the benchmark pins. (c) Minor PROSE overstatement, NOT an ensures divergence and NOT a finding: the axiom-block/mapping prose says a screen refuses 'a non-number', but a str-dtype array of numeric strings is in fact accepted and scored — the model and the repo AGREE on that input (both take the `some` branch), so no clause disagrees with the callee; screenRefuses is opaque and nothing is derived from the prose. (d) FAITHFUL is orthogonal to spec-too-weak: meta.json/verdict.md record a G-EQ / G-PANEL-1 failure (a Rat-division attack that verified but did not resolve, since repaired by making Offset a carrier). A too-weak spec and a faithful one are compatible; my verdict does NOT clear those gates and should not be read as doing so.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** leakage / gold-reconstruction attacker on scikit-learn__scikit-learn-25931/velvet. VERDICT NO-LEAKAGE. Every number below is my own measurement on the CURRENT bytes, Solution.lean sha256 5bc4ed3f2dfd83605007a822bd517da33be9ffab02d415e7f82a30c76961118b.

NO RELAXATION IN THIS BUNDLE -- I checked before judging. meta.json has no `relaxed_leakage` key (json 'relaxed_leakage' in m -> False) and `find -iname '*RELAX*'` over the whole instance directory returns nothing. So this is a straight leakage judgement, not a relaxation review, and I inherited no disposition from any file.

SPEC REGION IDENTITY (the thing I was asked to confirm). markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True -- the four spec regions (axioms, pure, pre-conditions, post-conditions) plus all frozen narration are byte-identical across the failing prepatch and the gold-faithful impl; spec_view is 456 lines on both. markers.region_hashes(...)['spec_view'] = 89e91b81387633badfbedcac55b742e13f66f11b8cae081274672e9705dc9c5a, which equals the value G-HYGIENE stamped, so the view I judged is the view the gate stamped. Independent confirmation that the whole spec/prose surface is shared: a unified diff of the two files differs ONLY inside the impl-start/impl-end body of fitComputeOffset (prepatch does `let rescreened <- screenHandle (presentPrepared samples)`, gold does not). Since the two files share the entire spec view byte-for-byte and one resolves while the other does not, the spec view CANNOT be encoding the gold edit -- it is by construction blind to the difference.

LOAD-BEARING TEST I RAN (the usual strip-the-narration control, since narration is where a leak would hide). I mechanically excised the entire `/- THE FITTING TAIL ... -/` docstring from both files and re-verified with scripts/lean_verify.sh: PostStripped.lean VERIFIES clean, PrepatchStripped.lean STILL FAILS at fitComputeOffset with `unsolved goals ... |- screenAdvises (presentPrepared samples) = false`. Same refutation as the unstripped prepatch (Solution_prepatch.lean:476:31). So the discriminator is carried STRUCTURALLY -- by screenHandle's `require screenAdvises presented = false`, which a Prepared-holding context cannot discharge, plus scorePublic's CallerHandle argument type that this tail cannot inhabit -- and NOT by any sentence of prose. Prose that is not load-bearing cannot be a leaking line. (I removed both scratch .lean files from the bundle afterward; `ls *.lean` shows only Solution.lean and Solution_prepatch.lean.)

PROBLEM-STATEMENT DERIVATION -- the facet the spec covers is public. The statement itself names: (a) the spurious 'X does not have valid feature names' warning; (b) that it is raised by fit(); (c) that it happens ONLY for contamination != 'auto'; (d) the mechanism verbatim -- 'when you pass contamination != "auto" the estimator essentially calls predict on the training data in order to determine the offset_ parameters' -- with a permalink to the offending line; (e) the expected result, that no such warning is raised. The spec view's fitComputeOffset says exactly that and no more: a non-default-contamination fitting tail holds an already-prepared matrix, derives the offset as the order statistic of its screen-free scores, and cannot reach a re-screen (the spurious labelling report) or a second scoring. Each of those is (d)+(e) restated in the model's vocabulary. The offset formula `percentileAt (anomalyScores samples) q` is likewise the linked line's own content.

GOLD-RECONSTRUCTION SWEEP -- what the spec view does NOT contain. The gold edit's actual shape is a method split: score_samples becomes public-validate-then-delegate, a new private `_score_samples` carries the scoring with check_is_fitted moved into it, and fit's offset step calls `_score_samples`. Token counts over the 456-line spec view: `_score_samples` 0, `score_samples` 0, `private` 0, `Private version` 0, `input validation` 0, `check_is_fitted` 0, `split` 0, `new method` 0, `disable it` 0, `removes feature names` 0, `a second time we call` 0. Also 0: np./numpy, percentile (as a repo name), IsolationForest, iforest, sklearn, contamination-as-parameter-name, `_compute_chunked_score_samples`, csr/csc, scipy, and any file:line citation.

The only hits for my leak-vocabulary greps were `validated` (line 13, 'validated == the real callees by axiom_check.py' -- a gate reference) and `helpers` (line 280, the boilerplate '-- (No pure helpers needed.)'). I checked specifically for the check_is_fitted relocation, which is the one part of the gold edit NOT derivable from the problem statement: greps for fitted-check/ordering/moved/relocated over the spec view return nothing -- 'fitted' appears only as 'the width recorded when the model was fitted', a property of the screen. So the edit's distinguishing mechanics are absent.

**THE TWO CLAUSES I PROBED HARDEST AND CLEARED.** (i) 'it must not put the heavy scorer to work a second time' -- scorer multiplicity is not obviously in the statement. But it is a consequence of the statement's own mechanism ('essentially calls predict on the training data'), it is discharged structurally by the CallerHandle argument type rather than named as a fix, and it constrains a rival's behaviour without disclosing that the means is a private helper -- many implementations satisfy it. Not a leak beyond (d). (ii) the sparse-container / scorableAsGiven fence and the Offset/Score/Point carrier discussion -- these are domain fences for the UNCHANGED modeled callees (np.percentile's partiality, the scorer's layout refusals, rational-division totality in Lean), each tied to a named axiom_check.py leg. They constrain where the spec is defined; none of them mentions or shapes the gold edit.

**BUNDLE ADDRESSING ME:** none found. I grepped verdict.md, mapping.md, refinement.md and meta.json for text instructing a reviewer how to record or which verdict is honest ('you must submit', 'record NO-LEAKAGE', 'the correct verdict is', 'do not flag', 'treat this as', reviewer/auditor/attacker forms). The only hits are ordinary record: verdict.md's per-role sections narrating what earlier agents concluded, and mapping.md:92 noting the R-VALUE rule is in the frozen axiom comment and so 'is part of what the spec says and not merely auditor commentary' -- a scoping statement about the spec, not an instruction to me. Nothing in the bundle tried to tell me what to submit.

GATES I LEAN ON, all stamped on the current sha (verified sources.Solution.lean == 5bc4ed3f for each): G-VERIFY pass (10.9s), G-DIFF pass (prepatch verification failed -- I reproduced this myself), G-GOLD pass, G-HYGIENE pass, G-INTEGRITY pass ('instance.json byte-identical; additions-only'), G-LEAK pass, G-AX pass, G-CONF pass (1200 real fits, 0 disagreements), G-MUT pass 4/4. FRESHNESS CAVEAT I record rather than rely on: G-PANEL-1 (fail), G-PANEL-2 (pass), G-PANEL-3 (pass) and G-EQ (fail) are ALL stamped on superseded bytes (sources.Solution.lean != current sha for each) -- so the recorded G-EQ/G-PANEL-1 spec-too-weak finding (atk_7_fit_rat_divide_by_zero.lean) judges a spec that has since been edited, and I did not inherit or re-derive it. It is the spec-strength lane's question and is orthogonal to leakage: a too-weak spec and a non-leaking one are compatible, so my NO-LEAKAGE does not clear that gate and must not be read as doing so.

**CONCLUSION:** the spec view is byte-identical between a resolving and a non-resolving impl, its discriminator survives full removal of the fitting-tail narration, and it contains none of the gold edit's identifying vocabulary or its one non-public element (the check_is_fitted relocation). What it does state reduces to the problem statement's own explicitly-named mechanism. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.