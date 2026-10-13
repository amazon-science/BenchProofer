# P2 adversarial audit — scikit-learn__scikit-learn-12973

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 27 admissible attacks re-run of 27 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 27 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 24 | `atk_prepatch.lean`, `atk1_rework_preserve.lean`, `atk2_rawgate_second.lean`, `atk3_drop_second.lean`, `atk5_partial_domain.lean`, `atk5b_partial_emptytarget.lean`, `atk6_swap_order.lean`, `atk7_config_only.lean`, `atk8_or_gate.lean`, `atk9_second_private_copy.lean`, `atk10_inverted.lean`, +13 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk4_discard_term.lean`, `atk21_offdomain_work.lean`, `atk22_offdomain_overwrite.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 27 same-spec wrong impls encoded; 24 REJECTED by lean_verify (exit 1) with genuine unsolved-goal refutations under feasible hypotheses. The 3 that VERIFY (atk4_discard_term, atk21_offdomain_work, atk22_offdomain_overwrite) each had a faithful refined patch materialized and RUN through the official harness: all three RESOLVED=True (F2P success, PASS_TO_PASS success, 0 nonempty failure lists), so none of them is a verify-but-not-resolve witness. verify => correct held on every executed probe.
```

**Attacks re-run (27):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,13 +176,24 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
-    if copy then
-      return prepareInPlace data target
+    -- BASELINE SKELETON: the two routines are gated INDEPENDENTLY, and neither
+    -- gate is the effective choice: the first goes by the configured choice, the
+    -- second by the per-call one read raw (absent reads as "leave it alone").
+    let stageOne := configuredCopy
+    let stageTwo := requestedCopy.getD true
+    if stageOne then
+      let w := prepareInPlace data target
+      if stageTwo then
+        return w
+      else
+        return searchInPlace w target
     else
       data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+      if stageTwo then
+        return data
+      else
+        data := searchInPlace data target
+        return data
     -- impl-end
 end
 
```

Attack 2 — `atk1_rework_preserve.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,7 +178,8 @@
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
-      return prepareInPlace data target
+      let w := prepareInPlace data target
+      return searchInPlace w target
     else
       data := prepareInPlace data target
       data := searchInPlace data target
```

Attack 3 — `atk2_rawgate_second.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,12 +177,20 @@
   do
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
+    let raw := requestedCopy.getD true
     if copy then
-      return prepareInPlace data target
+      let w := prepareInPlace data target
+      if raw then
+        return w
+      else
+        return searchInPlace w target
     else
       data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+      if raw then
+        return data
+      else
+        data := searchInPlace data target
+        return data
     -- impl-end
 end
 
```

Attack 4 — `atk3_drop_second.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -181,7 +181,6 @@
       return prepareInPlace data target
     else
       data := prepareInPlace data target
-      data := searchInPlace data target
       return data
     -- impl-end
 end
```

Attack 5 — `atk4_discard_term.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,7 +178,9 @@
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
-      return prepareInPlace data target
+      let w := prepareInPlace data target
+      let _discarded := searchInPlace w target
+      return w
     else
       data := prepareInPlace data target
       data := searchInPlace data target
```

Attack 6 — `atk5_partial_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,12 +177,19 @@
   do
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
-    if copy then
-      return prepareInPlace data target
+    if _h : bothRoutinesDeliver data target then
+      if copy then
+        return prepareInPlace data target
+      else
+        data := prepareInPlace data target
+        data := searchInPlace data target
+        return data
     else
-      data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+      if copy then
+        return searchInPlace data target
+      else
+        data := searchInPlace data target
+        return data
     -- impl-end
 end
 
```

Attack 7 — `atk5b_partial_emptytarget.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -181,8 +181,11 @@
       return prepareInPlace data target
     else
       data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+      if target.size == 0 then
+        return data
+      else
+        data := searchInPlace data target
+        return data
     -- impl-end
 end
 
```

Attack 8 — `atk6_swap_order.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,8 +180,8 @@
     if copy then
       return prepareInPlace data target
     else
+      data := searchInPlace data target
       data := prepareInPlace data target
-      data := searchInPlace data target
       return data
     -- impl-end
 end
```

Attack 9 — `atk7_config_only.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,7 +176,7 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
+    let copy := configuredCopy
     if copy then
       return prepareInPlace data target
     else
```

Attack 10 — `atk8_or_gate.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,7 +176,7 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
+    let copy := (requestedCopy.getD false) || configuredCopy
     if copy then
       return prepareInPlace data target
     else
```

Attack 11 — `atk9_second_private_copy.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -181,8 +181,7 @@
       return prepareInPlace data target
     else
       data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+      return searchInPlace data target
     -- impl-end
 end
 
```

Attack 12 — `atk10_inverted.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,11 +178,11 @@
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
-      return prepareInPlace data target
-    else
       data := prepareInPlace data target
       data := searchInPlace data target
       return data
+    else
+      return prepareInPlace data target
     -- impl-end
 end
 
```

Attack 13 — `atk11_preserve_reports_caller.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,7 +178,7 @@
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
-      return prepareInPlace data target
+      return data
     else
       data := prepareInPlace data target
       data := searchInPlace data target
```

Attack 14 — `atk12_rawgate_false_default.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,8 +177,13 @@
   do
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
+    let raw := requestedCopy.getD false
     if copy then
-      return prepareInPlace data target
+      if raw then
+        return prepareInPlace data target
+      else
+        let w := prepareInPlace data target
+        return searchInPlace w target
     else
       data := prepareInPlace data target
       data := searchInPlace data target
```

Attack 15 — `atk13_and_gate.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,7 +176,7 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
+    let copy := configuredCopy && (requestedCopy.getD configuredCopy)
     if copy then
       return prepareInPlace data target
     else
```

Attack 16 — `atk14_oracle_echo.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,13 +176,9 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
-    if copy then
-      return prepareInPlace data target
-    else
-      data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+    let _copy := effectiveCopy configuredCopy requestedCopy
+    data := searchInPlace (prepareInPlace data target) target
+    return data
     -- impl-end
 end
 
```

Attack 17 — `atk15_double_prepare.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -181,6 +181,7 @@
       return prepareInPlace data target
     else
       data := prepareInPlace data target
+      data := prepareInPlace data target
       data := searchInPlace data target
       return data
     -- impl-end
```

Attack 18 — `atk16_halffix_reversed.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,13 +176,20 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
-    if copy then
-      return prepareInPlace data target
+    let eff := effectiveCopy configuredCopy requestedCopy
+    if configuredCopy then
+      let w := prepareInPlace data target
+      if eff then
+        return w
+      else
+        return searchInPlace w target
     else
       data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+      if eff then
+        return data
+      else
+        data := searchInPlace data target
+        return data
     -- impl-end
 end
 
```

Attack 19 — `atk17_negated_default.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,7 +176,7 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
+    let copy := requestedCopy.getD (!configuredCopy)
     if copy then
       return prepareInPlace data target
     else
```

Attack 20 — `atk18_preserve_report_dataOld.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,7 +178,9 @@
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
-      return prepareInPlace data target
+      let w := prepareInPlace data target
+      let _ := searchInPlace w target
+      return data
     else
       data := prepareInPlace data target
       data := searchInPlace data target
```

Attack 21 — `atk19b_classical_partial.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,11 +176,16 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
+    let delivers : Bool := @decide (bothRoutinesDeliver data target) (Classical.propDecidable _)
     let copy := effectiveCopy configuredCopy requestedCopy
-    if copy then
-      return prepareInPlace data target
+    if delivers then
+      if copy then
+        return prepareInPlace data target
+      else
+        data := prepareInPlace data target
+        data := searchInPlace data target
+        return data
     else
-      data := prepareInPlace data target
       data := searchInPlace data target
       return data
     -- impl-end
```

Attack 22 — `atk20b_frame_offdomain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,12 +176,17 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
+    let delivers : Bool := @decide (bothRoutinesDeliver data target) (Classical.propDecidable _)
     let copy := effectiveCopy configuredCopy requestedCopy
-    if copy then
-      return prepareInPlace data target
+    if delivers then
+      if copy then
+        return prepareInPlace data target
+      else
+        data := prepareInPlace data target
+        data := searchInPlace data target
+        return data
     else
       data := prepareInPlace data target
-      data := searchInPlace data target
       return data
     -- impl-end
 end
```

Attack 23 — `atk21_offdomain_work.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,9 +176,13 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
+    let delivers : Bool := @decide (bothRoutinesDeliver data target) (Classical.propDecidable _)
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
-      return prepareInPlace data target
+      if delivers then
+        return prepareInPlace data target
+      else
+        return searchInPlace (prepareInPlace data target) target
     else
       data := prepareInPlace data target
       data := searchInPlace data target
```

Attack 24 — `atk22_offdomain_overwrite.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,13 +176,18 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
+    let delivers : Bool := @decide (bothRoutinesDeliver data target) (Classical.propDecidable _)
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
       return prepareInPlace data target
     else
-      data := prepareInPlace data target
-      data := searchInPlace data target
-      return data
+      if delivers then
+        data := prepareInPlace data target
+        data := searchInPlace data target
+        return data
+      else
+        data := prepareInPlace data target
+        return data
     -- impl-end
 end
 
```

Attack 25 — `atk23_target_conditioned.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,7 +176,7 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
+    let copy := if target.size == 0 then configuredCopy else effectiveCopy configuredCopy requestedCopy
     if copy then
       return prepareInPlace data target
     else
```

Attack 26 — `atk24_buffer_conditioned.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -176,7 +176,7 @@
             work = searchInPlace (prepareInPlace dataOld target) target
   do
     -- impl-start
-    let copy := effectiveCopy configuredCopy requestedCopy
+    let copy := if data.size == 0 then configuredCopy else effectiveCopy configuredCopy requestedCopy
     if copy then
       return prepareInPlace data target
     else
```

Attack 27 — `atk25_wrong_target.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -178,7 +178,7 @@
     -- impl-start
     let copy := effectiveCopy configuredCopy requestedCopy
     if copy then
-      return prepareInPlace data target
+      return prepareInPlace data (target.push 0)
     else
       data := prepareInPlace data target
       data := searchInPlace data target
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE

same_spec: verified True for ALL 27 attacks + the positive control via swebench_unified.markers.same_spec (velvet backend) against the shipped Solution.lean. Only the impl region was edited; axioms/pure/pre/post left byte-identical.

### Baseline
- positive_control pc_correct.lean (shipped impl) -> `bash scripts/lean_verify.sh <path>` exit 0.
- prepatch_reproduced: atk_prepatch.lean (= shipped Solution_prepatch.lean, the split-gate pre-change repo) -> exit 1, unsolved goals on multiple clauses. TRUE.

ATTACK BATTERY (27, run 4-at-a-time as concurrent background Bash jobs; command for each = `cd swe-proof && bash scripts/lean_verify.sh <name>.lean`)

REJECTED, exit 1 (24) -- each with the goal it could not close:
* atk_prepatch (split gate, pre-change repo)
* atk1_rework_preserve (control-flow-effect; routine 2 reworks routine 1's own buffer on the preserve leg) -> `searchInPlace (prepareInPlace dataOld target) target = prepareInPlace dataOld target` under if_pos. THIS IS THE PRIOR PASS'S RECORDED COUNTEREXAMPLE, re-encoded and still refuted.
* atk2_rawgate_second (routine 2 reads the RAW per-call value, absent=>truthy) -> same goal + the false-leg dual.
* atk3_drop_second (routine 2 never runs) -> `prepareInPlace dataOld target = searchInPlace (...) target`.
* atk5_partial_domain (partial-domain, `if bothRoutinesDeliver`) -> exit 1 but on `failed to synthesize Decidable`, i.e. a FORMALIZATION artifact, not a refutation; re-encoded properly as atk19b/atk20b below (both genuinely refuted). Retained in the list for completeness, NOT counted as one of the substantive rejections.
* atk5b_partial_emptytarget (partial-domain keyed on target.size==0)
* atk6_swap_order (routines composed in the wrong order)
* atk7_config_only (per-call choice ignored; configured gate only)
* atk8_or_gate (`copy_X or self.copy_X`)
* atk9_second_private_copy (routine 2 works on its own buffer on the overwrite leg)
* atk10_inverted (gate polarity flipped)
* atk11_preserve_reports_caller (preserve leg reports the CALLER's buffer -- the caller's-buffer-only reading of `work`)
* atk12_rawgate_false_default (raw gate, falsy absent default)
* atk13_and_gate (`configuredCopy && requested.getD configuredCopy`)
* atk14_oracle_echo (UNGROUNDED-ORACLE echo: both buffers pinned straight to the postcondition's composite, gate ignored)
* atk15_double_prepare (routine 1 applied twice)
* atk16_halffix_reversed (HALF-FIX: preprocessing keeps self.copy_X, descent gets the resolved value)
* atk17_negated_default (`requested.getD (!configured)`)
* atk18_preserve_report_dataOld (frame-correct, report-wrong)
* atk19b_classical_partial / atk20b_frame_offdomain (PARTIAL-DOMAIN via `@decide _ (Classical.propDecidable _)`; misbehave off the delivering pairs) -> BOTH refuted by ensures_4, the UNCONDITIONAL frame clause: `searchInPlace dataOld target = dataOld` / `prepareInPlace dataOld target = dataOld` under `if_neg : ¬decide (bothRoutinesDeliver dataOld target) = true`. This independently CONFIRMS refinement.md §C's claim that the frame clause's hypothesis-free status is load-bearing: it is exactly what closes the off-domain partial-domain hole.
* atk23_target_conditioned, atk24_buffer_conditioned (gate conditioned on target/buffer emptiness)
* atk25_wrong_target (preserve leg reports routine 1's output under a DIFFERENT target -- confirms the target argument is pinned in the clause)

VERIFIED, exit 0 (3) -- each patch MATERIALIZED and RESOLVED (mandatory step):

1. atk4_discard_term.lean (exit 0; re-confirmed exit 0 on a second run). Forms `searchInPlace w target` on the preserve leg, discards it, reports `w`.
   Patch: atk4_discard_term.diff (52 lines) -- gold resolution PLUS, on the truthy leg, an extra `lars_path(..., copy_X=copy_X, ...)` whose result is bound to `_discarded` and deleted.
   `git apply --check` in the base_commit worktree: OK.
   `run_resolve('scikit-learn__scikit-learn-12973', patch, run_id='eq_atk4_discard_1gij4')` -> RESOLVED=True, completed=True, note='resolved', attempts=1, F2P test_lasso_lars_fit_copyX_behaviour[False] success, all PASS_TO_PASS success, 0 nonempty failure lists.
   => NOT a break. This is refinement.md §C table row 5 ('recorded attack ported LITERALLY'), and the audit's prediction is CORRECT and now independently executed: because both routines are pure opaque transforms, forming-and-discarding is not an account of routine 2 having written anything, and with a truthy gate the real lars_path takes its defensive copy, so the buffer fit reads at :1520 genuinely still holds preprocessing's output. Gold behaviour, resolves.

2. atk21_offdomain_work.lean (exit 0). Off-domain divergence on the PRESERVE leg: where `bothRoutinesDeliver` fails, the three output clauses vacate, so it hands routine 2 a falsy gate there. Verifies because the vacated clauses assert nothing and the unconditional frame clause is still respected.
   Patch: atk21_offdomain_work.diff (72 lines) -- gold resolution plus a `_delivers` probe (`check_array(..., dtype=FLOAT_DTYPES)` then re-running the repo's own centering `X - np.average(X, axis=0)` and testing `np.all(np.isfinite(...))`, i.e. axiom_check.py's `reduction_stays_in_range`) which, on the truthy leg only when NOT delivering, flips the descent gate to False.
   `git apply --check`: OK. Probe validated to genuinely discriminate (typical F2P matrix -> True; the 1e308 witness -> False; 1e307 -> True), so the patch is a faithful non-vacuous refinement.
   `run_resolve(..., run_id='eq_atk21_offdomain_work_1gij4')` -> RESOLVED=True, completed=True, note='resolved', attempts=1, 0 nonempty failure lists.
   => NOT a break, and it is the expected outcome: the divergence lives entirely OFF the delivering pairs, and refinement.md §C documents (measured) that pre- and post-patch `fit` raise identically there, so no test can observe it.

3. atk22_offdomain_overwrite.lean (exit 0). The dual: off-domain divergence on the OVERWRITE leg (descent takes a defensive copy where the sequence does not deliver).
   Patch: atk22_offdomain_overwrite.diff (72 lines), same probe, opposite leg. `git apply --check`: OK.
   `run_resolve(..., run_id='eq_atk22_offdomain_overwrite_1gij4')` -> RESOLVED=True, completed=True, note='resolved', attempts=1, 0 nonempty failure lists.
   => NOT a break, same reason.

The atk21/atk22 pair is the sharpest available probe of the A-leg DOMAIN restriction (`bothRoutinesDeliver`), the one structural weakening this spec takes. Result: the residual freedom the hypothesis grants is real but provably unobservable -- both duals resolve. The hypothesis is a genuine domain restriction, not a smuggled escape hatch.

### REFINEMENT.MD AUDIT (§3 of the protocol)
* Leg tags: 1x R (#1, the None-resolution, mechanically checkable by G-CONF), 3x A-reference (#2 frames of BOTH callees on BOTH buffers, #3 frame of `_preprocess_data`, #4 frame of lars_path), 1x I (#5, the falsy-leg aliasing fact). NO A-consumed, NO kind-3, NO `:|`-stub, no `sorry`/`admit` in Solution.lean. Tag census matches the declared inventory; the doc's own 'no A-consumed axiom / no kind-3' claim is accurate.
* A-leg correspondence to the real callees HOLDS. axiom_check.py exercises `_preprocess_data` (routine1) and `lars_path` (routine2) DIRECTLY with fit's own argument list, never via `LassoLarsIC.fit` (the function under spec) -- the correct A-reference discipline; I confirmed this by reading routine1/routine2/observe_run. The pin table (PIN_FIT_INTERCEPT/NORMALIZE/PRECOMPUTE/MAX_ITER/POSITIVE/VERBOSE/COPY_GRAM/ALPHA_MIN/METHOD/RETURN_N_ITER) is checked complete against the call site's own text including literal kwargs (check_pin_table_complete) and each pin's provenance against the constructor default (check_pin_provenance). `in_modeled_region` decides its four conjuncts using the repo's OWN machinery (check_array/FLOAT_DTYPES, ndarray flags) -- two determinacy pins (float64, C-contiguous) on properties the signature carries no argument for, two domain conjuncts (float-dtype reachability, float64 range). `_dup` correctly uses order='A' so the layout pin stays measurable. I verified against the source that the modeled effects are real: `_preprocess_data` copies at base.py:117/elif copy and centers in place at `X -= X_offset` (base.py:149); `lars_path` does `X = X.copy('F')` at least_angle.py:176-180 only under a truthy copy_X and its column swaps `X.T[n], X.T[m] = swap(...)` (:268) otherwise land in the buffer handed on, selected via `Cov = np.dot(X.T, y)` (hence searchInPlace's genuine dependence on the target's ENTRIES); and the falsy-`precompute` pin is what keeps `Gram is None` so the descent reaches the buffer at all. `prepareInPlace`'s target argument is a STRUCTURAL/shape witness (check_X_y forces len(y)==X.shape[0]) -- consistent with the doc.
* The 'discarded-term' row (§C row 5) is the doc's one honestly-flagged residual, and I EXECUTED the resolve it predicts rather than taking it on faith: it resolves, so the flag is correct rather than a papered-over hole.

One bookkeeping nit (NOT a defect, no verdict impact): atk5_partial_domain exits 1 on a `Decidable` synthesis failure rather than an unsolved goal, so on its own it would be an inadmissible 'rejection'. I re-encoded that shape as atk19b/atk20b using `@decide _ (Classical.propDecidable _)` and both are genuinely refuted, so the partial-domain lane IS covered by a real refutation.

**CONCLUSION:** 27 same-spec attacks encoded and fully verified; 24 refuted; every one of the 3 verifying wrong impls had its faithful refined patch materialized, `git apply --check`ed at base_commit, and RUN through the official harness, and all 3 RESOLVED=True. No verify-but-not-resolve witness exists among the probes. Positive control verifies, prepatch reproduced. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 27 admissible attacks re-run of 27 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 27 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 24 | `atk_prepatch.lean`, `atk1_rework_preserve.lean`, `atk2_rawgate_second.lean`, `atk3_drop_second.lean`, `atk5_partial_domain.lean`, `atk5b_partial_emptytarget.lean`, `atk6_swap_order.lean`, `atk7_config_only.lean`, `atk8_or_gate.lean`, `atk9_second_private_copy.lean`, `atk10_inverted.lean`, +13 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk4_discard_term.lean`, `atk21_offdomain_work.lean`, `atk22_offdomain_overwrite.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 27 same-spec wrong impls encoded; 24 REJECTED by lean_verify (exit 1) with genuine unsolved-goal refutations under feasible hypotheses. The 3 that VERIFY (atk4_discard_term, atk21_offdomain_work, atk22_offdomain_overwrite) each had a faithful refined patch materialized and RUN through the official harness: all three RESOLVED=True (F2P success, PASS_TO_PASS success, 0 nonempty failure lists), so none of them is a verify-but-not-resolve witness. verify => correct held on every executed probe.
```

**Attacks re-run (27):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 27 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk1_rework_preserve.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2_rawgate_second.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk3_drop_second.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk4_discard_term.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk5_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk5b_partial_emptytarget.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk6_swap_order.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk7_config_only.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk8_or_gate.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk9_second_private_copy.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk10_inverted.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk11_preserve_reports_caller.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk12_rawgate_false_default.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk13_and_gate.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk14_oracle_echo.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk15_double_prepare.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk16_halffix_reversed.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk17_negated_default.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk18_preserve_report_dataOld.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk19b_classical_partial.lean` → rejected (same spec, does not verify — good)

Attack 22 — `atk20b_frame_offdomain.lean` → rejected (same spec, does not verify — good)

Attack 23 — `atk21_offdomain_work.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 24 — `atk22_offdomain_overwrite.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 25 — `atk23_target_conditioned.lean` → rejected (same spec, does not verify — good)

Attack 26 — `atk24_buffer_conditioned.lean` → rejected (same spec, does not verify — good)

Attack 27 — `atk25_wrong_target.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE

same_spec: verified True for ALL 27 attacks + the positive control via swebench_unified.markers.same_spec (velvet backend) against the shipped Solution.lean. Only the impl region was edited; axioms/pure/pre/post left byte-identical.

### Baseline
- positive_control pc_correct.lean (shipped impl) -> `bash scripts/lean_verify.sh <path>` exit 0.
- prepatch_reproduced: atk_prepatch.lean (= shipped Solution_prepatch.lean, the split-gate pre-change repo) -> exit 1, unsolved goals on multiple clauses. TRUE.

ATTACK BATTERY (27, run 4-at-a-time as concurrent background Bash jobs; command for each = `cd swe-proof && bash scripts/lean_verify.sh <name>.lean`)

REJECTED, exit 1 (24) -- each with the goal it could not close:
* atk_prepatch (split gate, pre-change repo)
* atk1_rework_preserve (control-flow-effect; routine 2 reworks routine 1's own buffer on the preserve leg) -> `searchInPlace (prepareInPlace dataOld target) target = prepareInPlace dataOld target` under if_pos. THIS IS THE PRIOR PASS'S RECORDED COUNTEREXAMPLE, re-encoded and still refuted.
* atk2_rawgate_second (routine 2 reads the RAW per-call value, absent=>truthy) -> same goal + the false-leg dual.
* atk3_drop_second (routine 2 never runs) -> `prepareInPlace dataOld target = searchInPlace (...) target`.
* atk5_partial_domain (partial-domain, `if bothRoutinesDeliver`) -> exit 1 but on `failed to synthesize Decidable`, i.e. a FORMALIZATION artifact, not a refutation; re-encoded properly as atk19b/atk20b below (both genuinely refuted). Retained in the list for completeness, NOT counted as one of the substantive rejections.
* atk5b_partial_emptytarget (partial-domain keyed on target.size==0)
* atk6_swap_order (routines composed in the wrong order)
* atk7_config_only (per-call choice ignored; configured gate only)
* atk8_or_gate (`copy_X or self.copy_X`)
* atk9_second_private_copy (routine 2 works on its own buffer on the overwrite leg)
* atk10_inverted (gate polarity flipped)
* atk11_preserve_reports_caller (preserve leg reports the CALLER's buffer -- the caller's-buffer-only reading of `work`)
* atk12_rawgate_false_default (raw gate, falsy absent default)
* atk13_and_gate (`configuredCopy && requested.getD configuredCopy`)
* atk14_oracle_echo (UNGROUNDED-ORACLE echo: both buffers pinned straight to the postcondition's composite, gate ignored)
* atk15_double_prepare (routine 1 applied twice)
* atk16_halffix_reversed (HALF-FIX: preprocessing keeps self.copy_X, descent gets the resolved value)
* atk17_negated_default (`requested.getD (!configured)`)
* atk18_preserve_report_dataOld (frame-correct, report-wrong)
* atk19b_classical_partial / atk20b_frame_offdomain (PARTIAL-DOMAIN via `@decide _ (Classical.propDecidable _)`; misbehave off the delivering pairs) -> BOTH refuted by ensures_4, the UNCONDITIONAL frame clause: `searchInPlace dataOld target = dataOld` / `prepareInPlace dataOld target = dataOld` under `if_neg : ¬decide (bothRoutinesDeliver dataOld target) = true`. This independently CONFIRMS refinement.md §C's claim that the frame clause's hypothesis-free status is load-bearing: it is exactly what closes the off-domain partial-domain hole.
* atk23_target_conditioned, atk24_buffer_conditioned (gate conditioned on target/buffer emptiness)
* atk25_wrong_target (preserve leg reports routine 1's output under a DIFFERENT target -- confirms the target argument is pinned in the clause)

VERIFIED, exit 0 (3) -- each patch MATERIALIZED and RESOLVED (mandatory step):

1. atk4_discard_term.lean (exit 0; re-confirmed exit 0 on a second run). Forms `searchInPlace w target` on the preserve leg, discards it, reports `w`.
   Patch: atk4_discard_term.diff (52 lines) -- gold resolution PLUS, on the truthy leg, an extra `lars_path(..., copy_X=copy_X, ...)` whose result is bound to `_discarded` and deleted.
   `git apply --check` in the base_commit worktree: OK.
   `run_resolve('scikit-learn__scikit-learn-12973', patch, run_id='eq_atk4_discard_1gij4')` -> RESOLVED=True, completed=True, note='resolved', attempts=1, F2P test_lasso_lars_fit_copyX_behaviour[False] success, all PASS_TO_PASS success, 0 nonempty failure lists.
   => NOT a break. This is refinement.md §C table row 5 ('recorded attack ported LITERALLY'), and the audit's prediction is CORRECT and now independently executed: because both routines are pure opaque transforms, forming-and-discarding is not an account of routine 2 having written anything, and with a truthy gate the real lars_path takes its defensive copy, so the buffer fit reads at :1520 genuinely still holds preprocessing's output. Gold behaviour, resolves.

2. atk21_offdomain_work.lean (exit 0). Off-domain divergence on the PRESERVE leg: where `bothRoutinesDeliver` fails, the three output clauses vacate, so it hands routine 2 a falsy gate there. Verifies because the vacated clauses assert nothing and the unconditional frame clause is still respected.
   Patch: atk21_offdomain_work.diff (72 lines) -- gold resolution plus a `_delivers` probe (`check_array(..., dtype=FLOAT_DTYPES)` then re-running the repo's own centering `X - np.average(X, axis=0)` and testing `np.all(np.isfinite(...))`, i.e. axiom_check.py's `reduction_stays_in_range`) which, on the truthy leg only when NOT delivering, flips the descent gate to False.
   `git apply --check`: OK. Probe validated to genuinely discriminate (typical F2P matrix -> True; the 1e308 witness -> False; 1e307 -> True), so the patch is a faithful non-vacuous refinement.
   `run_resolve(..., run_id='eq_atk21_offdomain_work_1gij4')` -> RESOLVED=True, completed=True, note='resolved', attempts=1, 0 nonempty failure lists.
   => NOT a break, and it is the expected outcome: the divergence lives entirely OFF the delivering pairs, and refinement.md §C documents (measured) that pre- and post-patch `fit` raise identically there, so no test can observe it.

3. atk22_offdomain_overwrite.lean (exit 0). The dual: off-domain divergence on the OVERWRITE leg (descent takes a defensive copy where the sequence does not deliver).
   Patch: atk22_offdomain_overwrite.diff (72 lines), same probe, opposite leg. `git apply --check`: OK.
   `run_resolve(..., run_id='eq_atk22_offdomain_overwrite_1gij4')` -> RESOLVED=True, completed=True, note='resolved', attempts=1, 0 nonempty failure lists.
   => NOT a break, same reason.

The atk21/atk22 pair is the sharpest available probe of the A-leg DOMAIN restriction (`bothRoutinesDeliver`), the one structural weakening this spec takes. Result: the residual freedom the hypothesis grants is real but provably unobservable -- both duals resolve. The hypothesis is a genuine domain restriction, not a smuggled escape hatch.

### REFINEMENT.MD AUDIT (§3 of the protocol)
* Leg tags: 1x R (#1, the None-resolution, mechanically checkable by G-CONF), 3x A-reference (#2 frames of BOTH callees on BOTH buffers, #3 frame of `_preprocess_data`, #4 frame of lars_path), 1x I (#5, the falsy-leg aliasing fact). NO A-consumed, NO kind-3, NO `:|`-stub, no `sorry`/`admit` in Solution.lean. Tag census matches the declared inventory; the doc's own 'no A-consumed axiom / no kind-3' claim is accurate.
* A-leg correspondence to the real callees HOLDS. axiom_check.py exercises `_preprocess_data` (routine1) and `lars_path` (routine2) DIRECTLY with fit's own argument list, never via `LassoLarsIC.fit` (the function under spec) -- the correct A-reference discipline; I confirmed this by reading routine1/routine2/observe_run. The pin table (PIN_FIT_INTERCEPT/NORMALIZE/PRECOMPUTE/MAX_ITER/POSITIVE/VERBOSE/COPY_GRAM/ALPHA_MIN/METHOD/RETURN_N_ITER) is checked complete against the call site's own text including literal kwargs (check_pin_table_complete) and each pin's provenance against the constructor default (check_pin_provenance). `in_modeled_region` decides its four conjuncts using the repo's OWN machinery (check_array/FLOAT_DTYPES, ndarray flags) -- two determinacy pins (float64, C-contiguous) on properties the signature carries no argument for, two domain conjuncts (float-dtype reachability, float64 range). `_dup` correctly uses order='A' so the layout pin stays measurable. I verified against the source that the modeled effects are real: `_preprocess_data` copies at base.py:117/elif copy and centers in place at `X -= X_offset` (base.py:149); `lars_path` does `X = X.copy('F')` at least_angle.py:176-180 only under a truthy copy_X and its column swaps `X.T[n], X.T[m] = swap(...)` (:268) otherwise land in the buffer handed on, selected via `Cov = np.dot(X.T, y)` (hence searchInPlace's genuine dependence on the target's ENTRIES); and the falsy-`precompute` pin is what keeps `Gram is None` so the descent reaches the buffer at all. `prepareInPlace`'s target argument is a STRUCTURAL/shape witness (check_X_y forces len(y)==X.shape[0]) -- consistent with the doc.
* The 'discarded-term' row (§C row 5) is the doc's one honestly-flagged residual, and I EXECUTED the resolve it predicts rather than taking it on faith: it resolves, so the flag is correct rather than a papered-over hole.

One bookkeeping nit (NOT a defect, no verdict impact): atk5_partial_domain exits 1 on a `Decidable` synthesis failure rather than an unsolved goal, so on its own it would be an inadmissible 'rejection'. I re-encoded that shape as atk19b/atk20b using `@decide _ (Classical.propDecidable _)` and both are genuinely refuted, so the partial-domain lane IS covered by a real refutation.

**CONCLUSION:** 27 same-spec attacks encoded and fully verified; 24 refuted; every one of the 3 verifying wrong impls had its faithful refined patch materialized, `git apply --check`ed at base_commit, and RUN through the official harness, and all 3 RESOLVED=True. No verify-but-not-resolve witness exists among the probes. Positive control verifies, prepatch reproduced. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

SETUP / PROVENANCE.
Reference = base_commit a7b8b9e9e16d4e15fabda5ae615086c2e1c47d8a with patch.diff APPLIED (I confirmed the container source at /w12973 already carries the gold delta: 'def fit(self, X, y, copy_X=None)' + 'if copy_X is None: copy_X = self.copy_X' + '`_preprocess_data`(..., copy_X)' at least_angle.py:1482/1503/1506, matching patch.diff hunk-for-hunk). I did NOT judge against the base version, so no patch-delta was miscounted as a divergence. Executed in sbu-local/sk12973-built:latest, conda env testbed, sklearn 0.21.dev0 / numpy 1.19.2, PYTHONPATH=/w12973.

### SPEC-REGION IDENTITY (ran, not read off the record).
markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True; the only pre/post difference is inside impl-start/impl-end, elided from the consumer view. scripts/lean_verify.sh Solution.lean -> exit 0 (verifies); Solution_prepatch.lean -> exit 1. So the discrimination the instance is about is live and I judged the audited view.

STALENESS -- WHY THE PRIOR G-PANEL-2 RECORD IS SUPERSEDED (the central finding of this re-audit).
meta.json stamps G-PANEL-2 = UNFAITHFUL at 2026-08-16T10:52:46 citing X=[[1e308],[1e308]]. Solution.lean and Solution_prepatch.lean are both mtime 14:33, and refinement.md 14:46 / mapping.md 14:37 -- i.e. the spec was REPAIRED after that verdict was stamped. The repair is precisely the fix for that witness: a new 'axiom bothRoutinesDeliver : Array Int -> Array Int -> Prop' now guards the three OUTPUT clauses, while the frame clause (data = dataOld on the truthy leg) is deliberately left UNGUARDED. Re-judging the retained 10:52 label would have carried a dead oracle verdict against a spec that no longer has the hole. I re-derived the verdict from the current bytes instead.

WHAT I MEASURED (all against the real patched fit, with a monkeypatch spy on lars_path so I could read 'work' = fit's local X at :1512 directly rather than only through coef_; my own region/delivery predicates written independently, then cross-checked against the bundle's). ~8050 in-region inputs x 6 (configuredCopy, requestedCopy) combos, across 7 probe corpora: uniform gaussians at scales 1e-3..1e3; near-overflow X (1e280..1e307.9); near-overflow y (up to float64 max); exactly-collinear and eps-collinear columns (singular Gram); Hilbert-like ill-conditioned; zero/constant/duplicate columns; denormals (1e-322..1e-300); mixed huge/tiny per-entry magnitudes; n<m wide; exact-integer-valued float ties; identical rows (zero variance); n in {1,2,3}; y in {zeros, ones, a column of X, arange, gaussian, 1e308-scale}.

Result: 0 violations of any of the four clauses. Per-clause, on every delivering pair: clause 1 (eff=true -> data = dataOld): holds, and holds on the 353 SIGNALLING pairs too (1059 truthy-leg observations, 0 violations) -- independently confirming the prose's claim that the unconditional statement is not too strong. clause 2 (eff=true -> work = prepareInPlace dataOld target): holds bitwise; the buffer handed to routine 2 exits equal to routine 1's output, i.e. routine 2 took its defensive copy. clauses 3/4 (eff=false -> both buffers = searchInPlace (prepareInPlace dataOld target) target): hold, the two buffers coincide bitwise at exit (np.may_share_memory confirms routine 2 was handed the caller's own storage on exactly the falsy leg: 4500 shares at eff=False, 0 at eff=True), and the gate forwarded to lars_path was the RESOLVED value on every combo (0 GATE2 violations) -- the actual patch semantics.

### STRUCTURAL CLAIMS THE OPAQUE SYMBOLS NEED (each could have been a faithfulness break; each checked):
prepareInPlace gate-independence (one symbol on both legs): 0 mismatches -- routine 1's output is bitwise identical for copy=True and copy=False. routine 1 truthy gate does not write the caller's buffer / falsy gate leaves it aliased to the output: 0 failures. prepareInPlace does NOT read the target's VALUES at fixed length: 0 of 500 -- so the second argument is a genuine shape witness, as claimed, not a licence to vary with y. prepareInPlace IS binary (shape-binding): same flat C-order entries under targets of different lengths give different output on 496/496 reshapes, 0 collisions -- a unary symbol could not model it.

Functional consistency of searchInPlace: I hunted P-collisions (distinct dataOld with bit-identical prepareInPlace output, via per-column constant shifts that centering cancels). 1 collision found in 500 pairs; searchInPlace agreed on it. A disagreement here would have been a real break, since one opaque binary symbol cannot take two values at one argument pair. Gate-independence of DELIVERY: 0 gate-dependent pairs out of ~8050 x 6. This is what licenses stating bothRoutinesDeliver once, ahead of the copy choice; had delivery depended on the gate, the single predicate would be unfaithful.

### NON-VACUITY (a precondition that excluded everything would be a hole, not a repair).
On 400 gaussian inputs where both legs deliver: the falsy leg mutates the caller's buffer 400/400; routine 1's output differs from dataOld 400/400; 'work' differs across the two legs 342/400; and the run's OBSERVABLE coef_ differs across legs 137/400. Zero fully-indistinguishable inputs. Across all corpora, 7695 of ~8050 in-region pairs DELIVER (only 353 signalling), so the precondition removes a thin boundary sliver, not the behaviour under test. Combined with prepatch failing at exit 1, the guarded clauses still carry the patch's full discriminating power.

RESIDUAL / LIMITS, stated honestly.
(1) mapping.md 3.3 pins eps and method='lasso' as CONSERVATIVE (self-reported as not measured load-bearing). I did not step off those pins; an off-pin run is a DIFFERENT modeled input, so this is a narrowness question for the strength lane, not a faithfulness divergence at the modeled configuration.
(2) The float32/float16 and F-order buffers are reachable in the repo but pinned out as determinacy guards. I verified the pins are real inputs rather than conveniences (the summation runs in the buffer's own precision and along the memory stride) but did not attempt to exhibit a divergence there, since the model explicitly claims nothing off-pin.
(3) precompute=False is a disclosed deliberate narrowing, and it is the setting both the F2P and the P2P observables live in; I held it throughout.
None of these is an input on which the spec disagrees with the real callee. I found no such input, so on the faithfulness question the verdict is FAITHFUL.

Counterexample / evidence:

```
None. The prior stale record's witness was re-run and is now correctly EXCLUDED, and the exclusion is not a repair-by-fiat:

X = [[1e308],[1e308]], y = [1., 2.] (the input the earlier UNFAITHFUL cited):
  my independent in_region(X)            = False
  bundle conformance_check.in_modeled_region = False
  bundle axiom_check.in_modeled_region       = False
  bundle both_routines_deliver(X, y)         = False   (BOTH check scripts)
  real fit raises ValueError('Input contains NaN, infinity...') on all 6 gate combos; lars_path never entered.
  So all three OUTPUT clauses are vacuously discharged by their bothRoutinesDeliver hypothesis, and clause 1 (unconditional) still HOLDS: caller_preserved=True on every truthy-leg combo (eff=True at (T,ABSENT), (T,True), (F,True)) even though the run raises -- exactly the asymmetry the spec's prose claims (routine 1 copies BEFORE it reduces).

mapping.md 3.5 arm-1 witness X=[[6e307]]*3: same picture (region=False, deliver=False, clause 1 holds).
mapping.md 3.5 arm-2 witness (finite 4x2 gaussian, y=[1e308,1e308,-1e308,1e308]): in_modeled_region = TRUE but both_routines_deliver = FALSE -- routine 2 IS entered and raises 'cannot convert float NaN to integer'. This is the genuinely pair-shaped arm that justifies the predicate being over (buffer, target) rather than a conjunct of in_modeled_region. Clause 1 holds there too.
CONTROL X=[[1e307],[1e307]], y=[1.,2.]: in_region=True, deliver=True, fit RETURNS, all four clauses hold. So the boundary sits strictly INSIDE the region (between 1e307 and 1e308) -- the precondition is a real gap the region admits, not the region's own edge, and it is decided by re-running the repo's own reduction, not by a magnitude threshold.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE.** No documented relaxation in this bundle, confirmed by my own measurement rather than read off the record: `ls -a velvet/` shows no RELAXED_LEAKAGE.md (present: Solution.lean, Solution_prepatch.lean, axiom_check.py, conformance_check.py, mapping.md, meta.json, properties.py, refinement.md, verdict.md, plus two transient build artifacts), and `json.load(meta.json)` has no `relaxed_leakage` key (top-level keys: additional_change_sites, axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, schema_version, spec_provenance, string_modeling, version); meta.gates['G-LEAK'].status == 'pass', not 'relaxed'. So leak.py's relaxation branch is not in play and there is no unavoidability argument to re-derive -- this is a plain leakage judgement.

BYTES / SPEC-REGION IDENTITY (ran). markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) -> True: the only pre/post difference is inside impl-start/impl-end, which leakage.spec_view replaces with 'implementation elided'. I printed the spec view myself; the prepatch impl (stageOne := configuredCopy, stageTwo := requestedCopy.getD true, two independent gates) is entirely elided. Independent verification: scripts/lean_verify.sh Solution.lean -> exit 0.

MECHANICAL SCREEN (ran, not read off the stamp). leakage.screen(Solution.lean, VelvetBackend.language, row['patch'], row['problem_statement'], test_patch=row['test_patch']) -> passed=True, hard_failures=[]. Judged against problem_statement only; hints_text is empty in instance.json anyway and I did not derive anything from it. No Lean diff markers; no gold-patch line reproduced; patched file 'sklearn/linear_model/least_angle.py' and its dotted form absent; `_patch_changed_symbols` == {'fit'} folded out as non-distinctive (len<4), and `_NARRATION_RE` over the view -> 0 hits.

MY OWN TOKEN CROSS-CHECK (beyond the screen). I extracted every identifier-shaped token from the gold patch's +/- lines and word-boundary-matched them against the spec view: hits were only {None, True, choice, def, default, optional, the, this}. Of those only 'optional' is absent from problem_statement, and it occurs as English ('the optional per-call choice') describing the Lean `Option Bool` argument, not as the Python signature default. Grep of the view for repo vocabulary -- LassoLarsIC, least_angle, sklearn, copy_X, `_preprocess_data`, lars_path, check_X_y, Gram, coef_, fit_intercept, normalize, precompute, base.py, '.py:', 'self.' -- returns 0 matches. Spec-view identifiers are all model-local (applyWithCopyChoice, effectiveCopy, prepareInPlace, searchInPlace, bothRoutinesDeliver, configuredCopy, requestedCopy, data/dataOld/work/target) plus Lean/Velvet keywords.

**DISCRIMINATOR IS PUBLIC.** Everything the four ensures clauses encode is stated in the public problem_statement: that a per-call value and a configured value both exist and 'each one is used once' so 'fit can have a mixed behaviour' (= the spec's two consumers governed by one effective choice), and the proposed resolution verbatim -- 'fit takes a default value of None and only overwrites the existing value if the user has explicitly passed it' (= effectiveCopy configured requested = requested.getD configured, plus the two-leg frame). Nothing in the view localizes the edit further than the issue text already does; in particular the view never names which callee, which file, or which line.

LOAD-BEARING TEST ON THE NARRATION (ran; this is the strip test). I built narration-stripped twins in a mktemp dir (all /- -/ blocks and non-marker -- comments removed, spec region and impl bytes otherwise untouched) and ran scripts/lean_verify.sh on both: stripped Solution -> exit 0; stripped Solution_prepatch -> exit 1 with unsolved goal `effectiveCopy configuredCopy requestedCopy = true -> searchInPlace (prepareInPlace dataOld target) target = dataOld` under if_neg : ¬configuredCopy = true, if_neg_1 : ¬requestedCopy.getD true = true. So the pre/post discrimination is carried entirely by the ensures clauses; the prose is inert and could be deleted without weakening the spec -- it is explanation, not a smuggled hint. Scratch dir removed afterwards; git status on the instance dir clean.

BUNDLE-STEERING CHECK (ran; reported as a finding in its own right). leakage.reviewer_directed over mapping.md, refinement.md and verdict.md -> [] on each. Grep of mapping.md, refinement.md, Solution*.lean, axiom_check.py, conformance_check.py, properties.py for panel/reviewer/auditor/judge/NO-LEAKAGE/'honest verdict'/'you must' -> no matches. Hits appear only in verdict.md, the gate-owned record of prior roles, and I record two observations without inheriting either: (a) verdict.md:1028-1064 carries a prior G-PANEL-3 'pass / NO-LEAKAGE' with a full argument, duplicated near-verbatim; I did not adopt it -- every measurement above is my own re-run; (b) verdict.md:67 opens 'IMPORTANT -- this is NOT the finding already recorded...', which is the G-PANEL-2 attacker asserting the novelty of its float32 finding to a reader of the record, not an instruction to this role. No file in the bundle addresses me or tells me what to submit.

STAMP FRESHNESS (why re-measuring mattered). sha256(Solution.lean) is currently dcc09b752e88..., which matches the sources digest on the freshly-stamped G-AX/G-CONF/G-DIFF/G-LEAK/G-VERIFY, but G-PANEL-1/2/3 and G-EQ are stamped against 94048abdd034... -- i.e. the prior leakage pass describes older bytes and could not have been inherited even if I wanted to. My screen, same_spec and strip test were all run on the current dcc09b7 bytes.

ORTHOGONAL FAILURE NOTED, NOT RE-JUDGED. meta.gates['G-PANEL-2'] is stamped fail (float32/float64 equal-contents twins make `_preprocess_data`'s output differ ~5.6e-08, so a unary-in-dataOld prepareInPlace cannot equal both -- a region-completeness gap making the spec too STRONG). That is the faithfulness facet, the opposite direction from revealing the gold edit, so it does not bear on leakage; I flag it only so the rollup G-PANEL fail (which echoes G-PANEL-2) is not misread as a leakage finding.

**VERDICT:** NO-LEAKAGE. Spec region byte-identical pre/post gold, mechanical screen clean on current bytes, no gold line/path/symbol/narration in the view, the prose measured non-load-bearing by the strip test (stripped gold exit 0, stripped prepatch exit 1), and every behavioural discriminator the ensures clauses encode is already stated in the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.