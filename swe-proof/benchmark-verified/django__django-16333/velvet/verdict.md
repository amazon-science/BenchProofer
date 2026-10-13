# P2 adversarial audit — django__django-16333

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_01_prepatch.lean`, `atk_04_deferred_late.lean`, `atk_06_object_first.lean`, `atk_07_related_first.lean`, `atk_08_oracle_skip_related.lean`, `atk_09_double_announce.lean`, `atk_10_related_on_noncommit.lean`, `atk_11_partial_domain_latch.lean`, `atk_13_dodge_ask.lean`, `atk_14_credential_last.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_02_double_object.lean`, `atk_03_unguarded_related.lean`, `atk_05_double_related.lean`, `atk_12_fabricate.lean`, `atk_16_object_after_related.lean`, `atk_17_oracle_skip_if_present.lean`, `atk_18_double_prepare.lean` |

**Non-vacuity.** The positive control `atk_00_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 17 same-spec rival impls were encoded and machine-verified; 10 were REFUTED by the frozen spec and the 7 that verify all RESOLVE under the official harness. The spec pins all ten FormState components over the full domain on both the commit and non-commit paths, so every verifying impl is extensionally equal to the gold transformer composition; the surviving rivals differ only by operations the deep models prove idempotent or no-op (a second object write announces nothing because the latch is already disarmed; a second prepareDeferred/persistRelated rewrites the same state), which is precisely why their faithful patches still resolve. The prior pass's recorded counterexample (re-arming the latch between two object writes to announce twice) is re-encoded as atk_09 and is now REFUTED by the announcement-multiplicity clause `commit = true -> st.credentialChanges = stOld.credentialChanges + 1`.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -200,14 +200,14 @@
   ensures st.dataValidated = stOld.dataValidated
   do
     -- impl-start
+    -- PRE-PATCH skeleton: on commit the object is persisted but the related
+    -- collection-valued data is NOT (the deferred capability is built but never
+    -- invoked). The frozen spec requires `commit = true → relatedPersisted`, so
+    -- prove_correct MUST fail on that clause.
     st := prepareDeferred st
     st := applyCredential st
     if commit then
       st := persistObject st
-      if st.deferredSaveReady then
-        st := persistRelated st
-      else
-        st := st
     else
       st := st
     return
```

Attack 2 — `atk_02_double_object.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -204,6 +204,7 @@
     st := applyCredential st
     if commit then
       st := persistObject st
+      st := persistObject st
       if st.deferredSaveReady then
         st := persistRelated st
       else
```

Attack 3 — `atk_03_unguarded_related.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -204,10 +204,7 @@
     st := applyCredential st
     if commit then
       st := persistObject st
-      if st.deferredSaveReady then
-        st := persistRelated st
-      else
-        st := st
+      st := persistRelated st
     else
       st := st
     return
```

Attack 4 — `atk_04_deferred_late.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -200,16 +200,16 @@
   ensures st.dataValidated = stOld.dataValidated
   do
     -- impl-start
-    st := prepareDeferred st
     st := applyCredential st
     if commit then
       st := persistObject st
+      st := prepareDeferred st
       if st.deferredSaveReady then
         st := persistRelated st
       else
         st := st
     else
-      st := st
+      st := prepareDeferred st
     return
     -- impl-end
 
```

Attack 5 — `atk_05_double_related.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -202,9 +202,11 @@
     -- impl-start
     st := prepareDeferred st
     st := applyCredential st
+    st := applyCredential st
     if commit then
       st := persistObject st
       if st.deferredSaveReady then
+        st := persistRelated st
         st := persistRelated st
       else
         st := st
```

Attack 6 — `atk_06_object_first.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -201,15 +201,15 @@
   do
     -- impl-start
     st := prepareDeferred st
-    st := applyCredential st
     if commit then
       st := persistObject st
+      st := applyCredential st
       if st.deferredSaveReady then
         st := persistRelated st
       else
         st := st
     else
-      st := st
+      st := applyCredential st
     return
     -- impl-end
 
```

Attack 7 — `atk_07_related_first.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,11 +203,11 @@
     st := prepareDeferred st
     st := applyCredential st
     if commit then
-      st := persistObject st
       if st.deferredSaveReady then
         st := persistRelated st
       else
         st := st
+      st := persistObject st
     else
       st := st
     return
```

Attack 8 — `atk_08_oracle_skip_related.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -204,7 +204,7 @@
     st := applyCredential st
     if commit then
       st := persistObject st
-      if st.deferredSaveReady then
+      if st.deferredSaveReady && st.relatedWriteAccepted then
         st := persistRelated st
       else
         st := st
```

Attack 9 — `atk_09_double_announce.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -204,6 +204,8 @@
     st := applyCredential st
     if commit then
       st := persistObject st
+      st := applyCredential st
+      st := persistObject st
       if st.deferredSaveReady then
         st := persistRelated st
       else
```

Attack 10 — `atk_10_related_on_noncommit.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -204,12 +204,11 @@
     st := applyCredential st
     if commit then
       st := persistObject st
+    else
       if st.deferredSaveReady then
         st := persistRelated st
       else
         st := st
-    else
-      st := st
     return
     -- impl-end
 
```

Attack 11 — `atk_11_partial_domain_latch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -200,16 +200,29 @@
   ensures st.dataValidated = stOld.dataValidated
   do
     -- impl-start
-    st := prepareDeferred st
-    st := applyCredential st
-    if commit then
-      st := persistObject st
-      if st.deferredSaveReady then
-        st := persistRelated st
+    if st.credentialPending then
+      st := prepareDeferred st
+      st := applyCredential st
+      if commit then
+        st := persistObject st
+        if st.deferredSaveReady then
+          st := persistRelated st
+        else
+          st := st
       else
         st := st
     else
-      st := st
+      st := prepareDeferred st
+      if commit then
+        st := persistObject st
+        st := applyCredential st
+        st := persistObject st
+        if st.deferredSaveReady then
+          st := persistRelated st
+        else
+          st := st
+      else
+        st := applyCredential st
     return
     -- impl-end
 
```

Attack 12 — `atk_12_fabricate.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -200,16 +200,26 @@
   ensures st.dataValidated = stOld.dataValidated
   do
     -- impl-start
-    st := prepareDeferred st
-    st := applyCredential st
     if commit then
-      st := persistObject st
-      if st.deferredSaveReady then
-        st := persistRelated st
+      if st.objectWriteAccepted then
+        if st.relatedWriteAccepted then
+          st := { st with passwordApplied := true, deferredSaveReady := true,
+                          objectPersisted := true, relatedPersisted := true,
+                          credentialPending := false,
+                          credentialChanges := st.credentialChanges + 1,
+                          stepRefused := false }
+        else
+          st := { st with passwordApplied := true, deferredSaveReady := true,
+                          objectPersisted := true,
+                          credentialPending := false,
+                          credentialChanges := st.credentialChanges + 1,
+                          stepRefused := true }
       else
-        st := st
+        st := { st with passwordApplied := true, deferredSaveReady := true,
+                        credentialPending := true, stepRefused := true }
     else
-      st := st
+      st := { st with passwordApplied := true, deferredSaveReady := true,
+                      credentialPending := true, stepRefused := false }
     return
     -- impl-end
 
```

Attack 13 — `atk_13_dodge_ask.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,11 +203,11 @@
     st := prepareDeferred st
     st := applyCredential st
     if commit then
-      st := persistObject st
-      if st.deferredSaveReady then
+      if st.objectWriteAccepted && st.relatedWriteAccepted then
+        st := persistObject st
         st := persistRelated st
       else
-        st := st
+        st := { st with stepRefused := true }
     else
       st := st
     return
```

Attack 14 — `atk_14_credential_last.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -201,15 +201,16 @@
   do
     -- impl-start
     st := prepareDeferred st
-    st := applyCredential st
     if commit then
       st := persistObject st
+      st := applyCredential st
       if st.deferredSaveReady then
         st := persistRelated st
       else
         st := st
     else
       st := st
+    st := applyCredential st
     return
     -- impl-end
 
```

Attack 15 — `atk_15_no_object_write.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,7 +203,6 @@
     st := prepareDeferred st
     st := applyCredential st
     if commit then
-      st := persistObject st
       if st.deferredSaveReady then
         st := persistRelated st
       else
```

Attack 16 — `atk_16_object_after_related.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -208,6 +208,7 @@
         st := persistRelated st
       else
         st := st
+      st := persistObject st
     else
       st := st
     return
```

Attack 17 — `atk_17_oracle_skip_if_present.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -204,7 +204,9 @@
     st := applyCredential st
     if commit then
       st := persistObject st
-      if st.deferredSaveReady then
+      if st.relatedPersisted && st.relatedWriteAccepted then
+        st := st
+      else if st.deferredSaveReady then
         st := persistRelated st
       else
         st := st
```

Attack 18 — `atk_18_double_prepare.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -202,6 +202,7 @@
     -- impl-start
     st := prepareDeferred st
     st := applyCredential st
+    st := prepareDeferred st
     if commit then
       st := persistObject st
       if st.deferredSaveReady then
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_00_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: All 18 attack files confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet language tables) => True; only the impl region was edited, and the prove_correct script is byte-identical to the bundle's (verified by diff). Verification via `bash scripts/lean_verify.sh <file>` from the repo root, run 4-way concurrently as background jobs.

METHOD NOTE (false-negative avoided): a first generation pass strengthened the proof script with extra `cases` lines; that made loom_solve emit `error: not a triple: _inhabitedExprDummy` + a Lean SMap PANIC on atk_02/atk_03. Those were framework elaboration failures, NOT spec refutations. Regenerating with the bundle's own proof script byte-identical turned both into EXIT=0 (verifies). Had I recorded the panic as the reject lane I would have invented spec strength that is not there.

POSITIVE CONTROL: atk_00_control.lean (byte-identical copy of bundle Solution.lean) => EXIT=0.
PREPATCH REPRODUCED: atk_01_prepatch.lean => EXIT=1, unsolved goal on `ensures_5: commit = true -> st.stepRefused = !(objectWriteAccepted && relatedWriteAccepted)` (and the relatedPersisted clause). Bug reproduced.

REFUTED (EXIT=1) - 10 distinct wrong impls, with the clause that killed each:
- atk_04_deferred_late (deferred capability prepared after the object write) -> ensures_18 deferredSaveReady = true
- atk_06_object_first (object write BEFORE the credential write; announces 0 times) -> ensures_11 (declined-write frame) / multiplicity
- atk_07_related_first (related write before the object write) -> ensures_1 dataValidated frame (stepRefused cascade)
- atk_08_oracle_skip_related (UNGROUNDED-ORACLE ECHO: peek at relatedWriteAccepted and decline to ASK when it would be declined) -> ensures_5 stepRefused characterization. The "may not dodge a declined write by declining to ask" clause does real work.
- atk_09_double_announce (THE PRIOR PASS'S RECORDED COUNTEREXAMPLE: re-arm the latch between two object writes => announces twice) -> ensures_16. Now refuted; the multiplicity clause closed this hole.
- atk_10_related_on_noncommit (related data persisted only on the non-commit path) -> ensures_5
- atk_11_partial_domain_latch (PARTIAL DOMAIN on the entry latch stOld.credentialPending, which the `require` does not constrain; gold behaviour when armed, double-announce path when not) -> ensures_11. Partial-domain cheats are closed.
- atk_13_dodge_ask (guard both writes on the storage verdict and refuse directly instead of asking) -> ensures_15
- atk_14_credential_last (credential written after the object write entirely) -> ensures_11
- atk_15_no_object_write (object write dropped) -> ensures_1 frame

VERIFIED (EXIT=0) - 7 rivals; EVERY ONE had its faithful refined patch MATERIALIZED and EXECUTED through the official harness (swebench_unified.harness.run_resolve, instance django__django-16333, timeout 1800, run 3-4 way concurrently). All 7 patches were first confirmed to apply cleanly with `git apply --check` against the base_commit worktree (60a7bd8986). RESULTS - ALL RESOLVED:
- atk_02_double_object       resolved=True attempts=1 flaky=False
- atk_03_unguarded_related   resolved=True attempts=1 flaky=False
- atk_05_double_related      resolved=True attempts=1 flaky=False
- atk_12_fabricate           resolved=True attempts=1 flaky=False
- atk_16_object_after_related resolved=True attempts=1 flaky=False
- atk_17_oracle_skip_if_present resolved=True attempts=1 flaky=False
- atk_18_double_prepare      resolved=True attempts=1 flaky=False
No verifying wrong impl's faithful patch failed to resolve => no verify=>correct break.

WHY THE 7 SURVIVORS STILL RESOLVE (not luck): the spec pins ALL TEN FormState components over the FULL domain on BOTH paths (persistence, announcement count AND its multiplicity, the outstanding-change latch, the two read-only storage-verdict components as explicit mut-frames, dataValidated, and an exact iff characterization of stepRefused). Any impl satisfying that conjunction is extensionally equal to the gold transformer composition.

The 7 survivors therefore differ from gold only by operations the deep models make idempotent or no-op: a second `user.save()` announces nothing (the latch is already disarmed at base_user.py:78), a second `set_password` re-arms the same single outstanding change, a second `_save_m2m()`/`super().save(commit=False)` rewrites identical state, and atk_03 drops a guard that G-AX proves vacuously true after A2. atk_17 is a genuine ungrounded-oracle echo attempt that reads back the m2m rows to skip the write -- it resolves because on the F2P trajectory the rows are absent so the write still happens. atk_12 bypasses all four callees and writes every observable by hand; it resolves because it reimplements them faithfully. This is refinement fidelity working, not a gap.

NEGATIVE CONTROL ON THE ORACLE (guards against a rubber-stamp "everything resolves" host): neg_control_prepatch.diff (the prepatch body, `pass` in place of the save_m2m call) => resolved=False, attempts=3, flaky=False, note "patch did not resolve in 3 attempts (consistent - not flaky)". The oracle DISCRIMINATES on this instance, so the 7 True verdicts are informative.

A-LEG AUDIT (my focus per the brief). refinement.md legs A1..A7 are tagged R / A-reference / I / (I + A-reference) -- NO kind-3 and NO consumed axioms, matching the axioms-start region which declares none. Correspondence to the real callees checked by hand against the base_commit worktree; every line citation in mapping.md and refinement.md is ACCURATE: base_user.py:66 (_password declaration), :74 save, :76-78 the password_changed announcement + disarm, :106-108 set_password arming the latch; forms/models.py:505 _save_m2m, :516 the chain(many_to_many, private_fields) loop, :526 save, :547 self.save_m2m = self._save_m2m; auth/forms.py:139 UserCreationForm.save.

The claim that persistObject's announcement is sequenced AFTER super().save() returns (so a declined write leaves the change outstanding) is correct in the real source. The A6 guard `st.deferredSaveReady` <-> `hasattr(self,"save_m2m")` being I over a boolean G-AX proves true is sound, and atk_03 empirically confirms it (dropping the guard both verifies and resolves). I additionally RE-RAN the bundle's own G-AX battery. It failed from the bundle dir (ModuleNotFoundError: auth_tests -- it resolves tests/ from os.getcwd(), and its recorded  scratch has been reaped; a harness-path artifact, not a defect).

Re-run from the live base_commit worktree it passes: `cd  && PYTHONPATH= python <bundle>/axiom_check.py` => EXIT=0, reporting all 4 A-reference callees matching their FormState deep models on all 10 components after every step of 524 trajectories (24 boundary + 500 fuzz, seed 16333) over 4 configurations (accept-both, decline-related, decline-object, no-related-field), including the announcement-multiplicity sequences and the declined-write arms. The A-legs' correspondence to the real callees HOLDS.

VERDICT: SOUND. 17 wrong impls encoded and machine-verified (>=5 required), spanning partial-domain (atk_11), boundary/ordering (atk_04/06/07/14), control-flow-effect (atk_02/09/16/18), ungrounded-oracle echo (atk_08/13/17) and full fabrication (atk_12); the recorded prior counterexample re-encoded and now refuted; all 7 verifiers' faithful patches executed through run_resolve and all resolved; oracle discrimination proven by a non-resolving negative control; A-legs independently revalidated. No verify=>correct break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_01_prepatch.lean`, `atk_04_deferred_late.lean`, `atk_06_object_first.lean`, `atk_07_related_first.lean`, `atk_08_oracle_skip_related.lean`, `atk_09_double_announce.lean`, `atk_10_related_on_noncommit.lean`, `atk_11_partial_domain_latch.lean`, `atk_13_dodge_ask.lean`, `atk_14_credential_last.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_02_double_object.lean`, `atk_03_unguarded_related.lean`, `atk_05_double_related.lean`, `atk_12_fabricate.lean`, `atk_16_object_after_related.lean`, `atk_17_oracle_skip_if_present.lean`, `atk_18_double_prepare.lean` |

**Non-vacuity.** The positive control `atk_00_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 17 same-spec rival impls were encoded and machine-verified; 10 were REFUTED by the frozen spec and the 7 that verify all RESOLVE under the official harness. The spec pins all ten FormState components over the full domain on both the commit and non-commit paths, so every verifying impl is extensionally equal to the gold transformer composition; the surviving rivals differ only by operations the deep models prove idempotent or no-op (a second object write announces nothing because the latch is already disarmed; a second prepareDeferred/persistRelated rewrites the same state), which is precisely why their faithful patches still resolve. The prior pass's recorded counterexample (re-arming the latch between two object writes to announce twice) is re-encoded as atk_09 and is now REFUTED by the announcement-multiplicity clause `commit = true -> st.credentialChanges = stOld.credentialChanges + 1`.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_02_double_object.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_03_unguarded_related.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_04_deferred_late.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_05_double_related.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_06_object_first.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_07_related_first.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_08_oracle_skip_related.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_09_double_announce.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_related_on_noncommit.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_partial_domain_latch.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_fabricate.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_dodge_ask.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_credential_last.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_no_object_write.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_object_after_related.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17_oracle_skip_if_present.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18_double_prepare.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_00_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: All 18 attack files confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet language tables) => True; only the impl region was edited, and the prove_correct script is byte-identical to the bundle's (verified by diff). Verification via `bash scripts/lean_verify.sh <file>` from the repo root, run 4-way concurrently as background jobs.

METHOD NOTE (false-negative avoided): a first generation pass strengthened the proof script with extra `cases` lines; that made loom_solve emit `error: not a triple: _inhabitedExprDummy` + a Lean SMap PANIC on atk_02/atk_03. Those were framework elaboration failures, NOT spec refutations. Regenerating with the bundle's own proof script byte-identical turned both into EXIT=0 (verifies). Had I recorded the panic as the reject lane I would have invented spec strength that is not there.

POSITIVE CONTROL: atk_00_control.lean (byte-identical copy of bundle Solution.lean) => EXIT=0.
PREPATCH REPRODUCED: atk_01_prepatch.lean => EXIT=1, unsolved goal on `ensures_5: commit = true -> st.stepRefused = !(objectWriteAccepted && relatedWriteAccepted)` (and the relatedPersisted clause). Bug reproduced.

REFUTED (EXIT=1) - 10 distinct wrong impls, with the clause that killed each:
- atk_04_deferred_late (deferred capability prepared after the object write) -> ensures_18 deferredSaveReady = true
- atk_06_object_first (object write BEFORE the credential write; announces 0 times) -> ensures_11 (declined-write frame) / multiplicity
- atk_07_related_first (related write before the object write) -> ensures_1 dataValidated frame (stepRefused cascade)
- atk_08_oracle_skip_related (UNGROUNDED-ORACLE ECHO: peek at relatedWriteAccepted and decline to ASK when it would be declined) -> ensures_5 stepRefused characterization. The "may not dodge a declined write by declining to ask" clause does real work.
- atk_09_double_announce (THE PRIOR PASS'S RECORDED COUNTEREXAMPLE: re-arm the latch between two object writes => announces twice) -> ensures_16. Now refuted; the multiplicity clause closed this hole.
- atk_10_related_on_noncommit (related data persisted only on the non-commit path) -> ensures_5
- atk_11_partial_domain_latch (PARTIAL DOMAIN on the entry latch stOld.credentialPending, which the `require` does not constrain; gold behaviour when armed, double-announce path when not) -> ensures_11. Partial-domain cheats are closed.
- atk_13_dodge_ask (guard both writes on the storage verdict and refuse directly instead of asking) -> ensures_15
- atk_14_credential_last (credential written after the object write entirely) -> ensures_11
- atk_15_no_object_write (object write dropped) -> ensures_1 frame

VERIFIED (EXIT=0) - 7 rivals; EVERY ONE had its faithful refined patch MATERIALIZED and EXECUTED through the official harness (swebench_unified.harness.run_resolve, instance django__django-16333, timeout 1800, run 3-4 way concurrently). All 7 patches were first confirmed to apply cleanly with `git apply --check` against the base_commit worktree (60a7bd8986). RESULTS - ALL RESOLVED:
- atk_02_double_object       resolved=True attempts=1 flaky=False
- atk_03_unguarded_related   resolved=True attempts=1 flaky=False
- atk_05_double_related      resolved=True attempts=1 flaky=False
- atk_12_fabricate           resolved=True attempts=1 flaky=False
- atk_16_object_after_related resolved=True attempts=1 flaky=False
- atk_17_oracle_skip_if_present resolved=True attempts=1 flaky=False
- atk_18_double_prepare      resolved=True attempts=1 flaky=False
No verifying wrong impl's faithful patch failed to resolve => no verify=>correct break.

WHY THE 7 SURVIVORS STILL RESOLVE (not luck): the spec pins ALL TEN FormState components over the FULL domain on BOTH paths (persistence, announcement count AND its multiplicity, the outstanding-change latch, the two read-only storage-verdict components as explicit mut-frames, dataValidated, and an exact iff characterization of stepRefused). Any impl satisfying that conjunction is extensionally equal to the gold transformer composition.

The 7 survivors therefore differ from gold only by operations the deep models make idempotent or no-op: a second `user.save()` announces nothing (the latch is already disarmed at base_user.py:78), a second `set_password` re-arms the same single outstanding change, a second `_save_m2m()`/`super().save(commit=False)` rewrites identical state, and atk_03 drops a guard that G-AX proves vacuously true after A2. atk_17 is a genuine ungrounded-oracle echo attempt that reads back the m2m rows to skip the write -- it resolves because on the F2P trajectory the rows are absent so the write still happens. atk_12 bypasses all four callees and writes every observable by hand; it resolves because it reimplements them faithfully. This is refinement fidelity working, not a gap.

NEGATIVE CONTROL ON THE ORACLE (guards against a rubber-stamp "everything resolves" host): neg_control_prepatch.diff (the prepatch body, `pass` in place of the save_m2m call) => resolved=False, attempts=3, flaky=False, note "patch did not resolve in 3 attempts (consistent - not flaky)". The oracle DISCRIMINATES on this instance, so the 7 True verdicts are informative.

A-LEG AUDIT (my focus per the brief). refinement.md legs A1..A7 are tagged R / A-reference / I / (I + A-reference) -- NO kind-3 and NO consumed axioms, matching the axioms-start region which declares none. Correspondence to the real callees checked by hand against the base_commit worktree; every line citation in mapping.md and refinement.md is ACCURATE: base_user.py:66 (_password declaration), :74 save, :76-78 the password_changed announcement + disarm, :106-108 set_password arming the latch; forms/models.py:505 _save_m2m, :516 the chain(many_to_many, private_fields) loop, :526 save, :547 self.save_m2m = self._save_m2m; auth/forms.py:139 UserCreationForm.save.

The claim that persistObject's announcement is sequenced AFTER super().save() returns (so a declined write leaves the change outstanding) is correct in the real source. The A6 guard `st.deferredSaveReady` <-> `hasattr(self,"save_m2m")` being I over a boolean G-AX proves true is sound, and atk_03 empirically confirms it (dropping the guard both verifies and resolves). I additionally RE-RAN the bundle's own G-AX battery. It failed from the bundle dir (ModuleNotFoundError: auth_tests -- it resolves tests/ from os.getcwd(), and its recorded  scratch has been reaped; a harness-path artifact, not a defect).

Re-run from the live base_commit worktree it passes: `cd  && PYTHONPATH= python <bundle>/axiom_check.py` => EXIT=0, reporting all 4 A-reference callees matching their FormState deep models on all 10 components after every step of 524 trajectories (24 boundary + 500 fuzz, seed 16333) over 4 configurations (accept-both, decline-related, decline-object, no-related-field), including the announcement-multiplicity sequences and the declined-write arms. The A-legs' correspondence to the real callees HOLDS.

VERDICT: SOUND. 17 wrong impls encoded and machine-verified (>=5 required), spanning partial-domain (atk_11), boundary/ordering (atk_04/06/07/14), control-flow-effect (atk_02/09/16/18), ungrounded-oracle echo (atk_08/13/17) and full fabrication (atk_12); the recorded prior counterexample re-encoded and now refuted; all 7 verifiers' faithful patches executed through run_resolve and all resolved; oracle discrimination proven by a non-resolving negative control; A-legs independently revalidated. No verify=>correct break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS (too-strong / drift) AUDIT — django__django-16333. Reference = base worktree with patch.diff APPLIED (); base worktree kept only for the unchanged callees the A-references model. No input found on which commitForm's frozen postconditions disagree with the real patched UserCreationForm.save.

INTEGRITY / PROVENANCE
- Solution.lean sha256 = 99508aa5f655eb0dfbaaac17d1634653b70b3c4ccdfe766e5c0d0235ec7e3774, byte-identical to the Solution.lean source hash recorded by G-AX and G-GOLD in meta.json. Region hashes recomputed via markers.region_hashes: axioms=aaea2695..., pure=556fd9b8..., impl=873236da... all match G-HYGIENE's record exactly. markers.same_spec(Sol,Sol)=True; same_spec(Sol,Solution_prepatch)=True, confirming the prepatch rival is judged against the SAME frozen spec.
- scripts/lean_verify.sh Solution.lean -> exit 0 (elaborates, no sorry/error). axioms region is empty (no consumed axioms); all four callees are A-reference deep models, so there is no axiom hiding the changed function.
- ONE anomaly, judged benign and NOT a spec defect: the recomputed spec_view hash (1501b3b5...) differs from G-HYGIENE's recorded f002cdf6..., while axioms/pure/impl match byte-for-byte and the file sha matches G-AX. Since the spec TEXT is provably unchanged, the delta is in the spec_view projection and not in the specification: the recorded hash was stamped by an earlier revision of that projection, and no committed change to the projection lies between that revision and the one I ran. Spec content intact; a stamping question, not drift.

### WHAT I ACTUALLY RAN (empirical, end-to-end on the PATCHED reference)
Built two harnesses that drive the REAL f.save(commit) end-to-end — deliberately NOT step-by-step like axiom_check.py — and check EVERY frozen ensures clause verbatim against the observed pre/post FormState under mapping.md §2's bijection. Critically, I removed my own outer transaction.atomic() wrapper, because the real caller has none; keeping it would have masked partial writes.
- probe.py: 496 trajectories / 4960 clause checks, 6 configurations incl. ones axiom_check.py never instantiates (two m2m fields with one accepted + one declined; blank=True m2m with EMPTY selection over a required-column through model; decline-related; decline-object; no-m2m-on-form), crossed with commit=True/False, credential already outstanding, instance already stored, selection sizes, plus 400 fuzz. VIOLATIONS=0.
- entry.py: 192 trajectories / 1344 clause checks over entry states with PRE-EXISTING m2m rows planted directly (subset / superset / disjoint / exact vs the cleaned selection) on both an auto-created and a required-column through model. VIOLATIONS=0. This leg is the strongest evidence for the read-only acceptance components: it confirms relatedWriteAccepted really is a FACT ABOUT THE ENTRY STATE — set() declines iff it must ADD at least one new through row (required col, no default), and is ACCEPTED when the selection is already present (no-op) or requires only REMOVals. The spec's mut-frame claim that no step writes it holds on every one of these.
Total: 688 trajectories, 6304 clause evaluations, 0 disagreements.

PRIOR RECORDED COUNTEREXAMPLE IS REPAIRED — I re-ran it rather than trusting the record. verdict.md:6569 (attack F) reported UNFAITHFUL on 'ensures commit=true -> relatedPersisted=true' and 'stepRefused=false' via a through model with a required IntegerField (NOT NULL constraint failed ... .rank). The CURRENT frozen spec carries two components that did not exist then — objectWriteAccepted / relatedWriteAccepted (20 occurrences) — and guards those clauses on them, plus the exact-iff 'commit=true -> stepRefused = !(oOK && rOK)'. My decline-related config reproduces precisely that IntegrityError (NOT NULL constraint failed: auth_tests_m.rank) and EVERY clause holds: objectPersisted=True, credentialChanges=+1, credentialPending=False, relatedPersisted frame preserved, stepRefused=True as the iff demands. Attack F's counterexample is dead against this spec revision.

HARDEST SURVIVING CANDIDATE, pressed and rejected: PARTIAL RELATED WRITE. _save_m2m loops over m2m fields with no transaction of its own and each ManyRelatedManager.set() opens its OWN atomic, so with no outer atomic (the real caller's situation) field 1's rows COMMIT while field 2 raises. I measured this on a two-m2m model (accepted 'aaa' declared before declined 'zzz'): step refused with IntegrityError, yet 3 join rows for 'aaa' were genuinely committed to the database. This is real, un-rolled-back state the abstraction cannot see. It is nonetheless NOT a clause violation: relatedPersisted is bound by mapping.md/axiom_check.py as the CONJUNCTION over every m2m field the form exposes ('every exposed field holds exactly the selection'), so with 'zzz' empty it stays False and 'commit&!(oOK&&rOK) -> relatedPersisted = stOld.relatedPersisted' holds. Recording it as an honest abstraction-coarseness residual (an observable side effect outside the ten modeled components), uniformly applied and not load-bearing for the discriminating clause, rather than as too-strong drift — the formal clause is satisfied on the real repo.

PATCH-DELTA TRAP: explicitly guarded. I compared against the PATCHED worktree throughout, so 'relatedPersisted=true on commit' — the clause the prepatch rival is supposed to fail — was never scored as a divergence. Base was consulted only for the unchanged callees (base_user.py set_password/save, forms.py BaseModelForm.save/_save_m2m), which patch.diff does not touch.

CONCLUSION: the spec is not stronger than the patched repo on any input I could construct. Verdict FAITHFUL, confidence high; residuals above are recorded for the record, not as defects.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE/RELAXATION: no relaxation claimed. `json.load(meta.json).get('relaxed_leakage')` -> None (top keys: additional_change_sites, axioms, base_commit, changed_files, conf_skip, conf_skip_reason, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, prepatch_variants, repo, schema_version, spec_provenance, state_modeling, version); no RELAXED_LEAKAGE.md anywhere in the instance dir. So there is no unavoidability argument to re-derive, and I judged against the plain standard: spec view vs problem_statement only. hints_text is the empty string here (len 0), so it played no part either way.

SPEC REGION FROZEN: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) -> True, using the real LanguageTables from swebench_unified.backends.velvet (flavor='lean', regions axioms/pure/pre-conditions/post-conditions/invariants/impl). Reviewed the canonical markers.spec_view output, not the raw file (impl region and prove_correct body elided; the method signature + all 22 ensures + the pure region + the doc comment are what the consumer sees).

MECHANICAL SCREEN: leakage.screen(src, velvet_tables, gold_patch, problem_statement, test_patch) -> hard_failures=[], soft=[]. leakage.reviewer_directed(src) -> []. Confirmed by hand what that covers: gold-changed lines are ['if hasattr(self, "save_m2m"):', 'self.save_m2m()'] and neither normalized form appears in the view; changed symbol set is {'save'}, which is skipped only because 'save' IS public in the problem_statement ('UserCreationForm.save(commit=True)', 'should save data') -- I checked that skip is legitimate rather than a screen blind spot. Independent greps over the spec view for save_m2m / m2m / many.?to.?many / django / forms.py / patch / gold: zero hits. Narration grep (fix|patch|bug|previously|omit|forgot|missing|added|instead of|used to|no longer|regression) over the view: only hits are 'open TotalCorrectness', 'prove_correct', and line 42 'The desired behaviour (the public issue)' -- none is edit narration, and 'issue' there frames the PUBLIC issue rather than the diff.

DERIVABILITY OF THE DISCRIMINATOR FROM problem_statement ALONE: the statement says outright that UserCreationForm.save(commit=True) 'omits to call self.save_m2m()' and that m2m form-field data is therefore not saved, 'unlike its parent class django.forms.ModelForm'. So the discriminating obligation the spec pins -- `ensures commit = true -> stOld.objectWriteAccepted = true -> stOld.relatedWriteAccepted = true -> st.relatedPersisted = true`, narrated as 'must persist BOTH the object and all of its related collection-valued form data - exactly as the generic form base class does' -- is a paraphrase of the public ask, in abstracted vocabulary (relatedPersisted / collection-valued), naming no repo symbol, file, or diff line. This is the easy direction: the discriminator is public, so there is nothing here for the spec to leak.

CHECKED THE NEAREST LEAK CANDIDATE (the guard). `deferredSaveReady` <-> hasattr(self,'save_m2m') is the one component that shadows a gold-edit DETAIL (the added `if hasattr(...)` guard), so I tested whether the spec forces that shape. Built Solution.lean = gold with the guard stripped (persistRelated called unconditionally inside the commit branch, no `if st.deferredSaveReady`): scripts/lean_verify.sh -> exit 0, VERIFIES. So the frozen spec does not compel the guard, and cannot be handing the consumer the guarded shape; `ensures st.deferredSaveReady = true` states the base-class commit=False effect, which is public via the statement's own ModelForm/save_m2m sentence and visible in the pre-patch body the solver holds.

CONTROLS RUN (so the load-bearing claim is my measurement): gold Solution.lean -> lean_verify exit 0. Solution_prepatch.lean -> exit 1, and the unsolved goals are exactly the discriminating clauses: `ensures_14 ... stOld.relatedWriteAccepted = true -> st.relatedPersisted = true` with goal `stOld.relatedPersisted = true`, plus the stepRefused clause. Sha of the file I reviewed is 99508aa5f655eb0dfbaaac17d1634653b70b3c4ccdfe766e5c0d0235ec7e3774, which matches the Solution.lean source recorded for the fresh G-LEAK ('spec view clean'), G-HYGIENE, G-VERIFY, G-GOLD, G-AX, G-DIFF gates (all 12:39-12:42 today), so this review is against the current artifact.

OTHER SPEC CONTENT, JUDGED FOR LEAKAGE: the announcement-multiplicity leg (credentialPending / credentialChanges, the set_password-latch -> save-announces-once machinery) and the storage-decline leg (objectWriteAccepted / relatedWriteAccepted / stepRefused) both describe PRE-EXISTING callee behavior that the 2-line gold hunk does not touch, and both are readable off the pre-patch body the solver already has. They are anti-cheat/frame clauses, not edit disclosure -- they say nothing about what the diff adds. (Note for the record: the storage-decline leg is where meta.json's stale G-PANEL-2 fail sits, alleging the spec demands relatedPersisted=true where a required-NOT-NULL through column makes the real patched save_m2m raise IntegrityError. That is a FAITHFULNESS question on another gate's docket -- and it was recorded against the older sha 7f4ce8c2, not the 99508aa5 I reviewed -- so it does not change this verdict either way; I flag it only so the layer that owns it is not misled by my pass.)

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as its own finding per instruction): nothing in Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, axiom_check.py, conformance_check.py, or properties.py instructs a reviewer how to record or which verdict is honest. refinement.md:122 and conformance_check.py:28 merely cite G-PANEL as a gate the trust argument rests on -- ordinary provenance prose, not a directive. mapping.md correctly quarantines the pre-patch behavior it describes with 'refinement audit only, not in the consumer spec view'. verdict.md contains prior panel notes (incl. lines 6714/6731 asserting relaxation status) -- those are prior reviewers' records, not bundle directives at me; I re-derived the relaxation status myself from meta.json + a filesystem search rather than inheriting them, and reached the same result independently.

VERDICT: the spec view leaks nothing about the gold edit beyond what the public problem_statement already states; the discriminator is public in the statement itself, and the one edit detail NOT in the statement (the hasattr guard) is demonstrably not forced by the spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
