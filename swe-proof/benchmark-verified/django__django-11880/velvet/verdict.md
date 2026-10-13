# P2 adversarial audit — django__django-11880

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8.lean`, `atk_10.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 same-spec admissible attacks were run; 9 were REJECTED by the verifier on a genuine clause and 5 VERIFIED. All 5 verifying attacks had their faithful refined patch materialized and RUN through the official harness (swebench_unified.harness.run_resolve): all 5 RESOLVED on attempt 1 (non-flaky), i.e. they are correct echoes of the gold, not spec weaknesses. No verifying wrong impl whose patch fails to resolve exists in this battery, so verify=>correct was not falsified.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,16 +147,13 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
+    -- Skeleton under audit: the shallow duplication is followed by installing the
+    -- copy of the opaque rendering component and the copy of the validator
+    -- collection, but the table of override messages is LEFT AS THE SHARED
+    -- REFERENCE the shallow duplication handed over (no copy of it is installed).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
     result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
+    -- (no copy of the override-message table is installed here)
     result := { result with validators := validatorsCopy }
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,16 +147,10 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
     result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
+    if source.errorMessages.ref != 0 then
+      result := { result with errorMessages := messagesCopy }
     result := { result with validators := validatorsCopy }
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,11 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
     result := { result with widget := widgetCopy }
     result := { result with errorMessages := messagesCopy }
     result := { result with validators := validatorsCopy }
+    result := { result with errorMessages := source.errorMessages }
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,10 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
-    result := { result with validators := validatorsCopy }
+    result := { result with widget := { ref := source.widget.ref + 1, payload := source.widget.payload } }
+    result := { result with errorMessages := { ref := source.errorMessages.ref + 1, payload := source.errorMessages.payload } }
+    result := { result with validators := { ref := source.validators.ref + 1, payload := source.validators.payload } }
     return result
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,10 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
     result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
-    result := { result with validators := validatorsCopy }
+    result := { result with errorMessages := validatorsCopy }
+    result := { result with validators := messagesCopy }
     return result
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,9 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
-    let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
-    result := { result with validators := validatorsCopy }
+    let result : FormField :=
+      { widget := widgetCopy, errorMessages := messagesCopy,
+        validators := validatorsCopy, carried := { ref := 0, payload := 0 } }
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,15 +147,7 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
     result := { result with errorMessages := messagesCopy }
     result := { result with validators := validatorsCopy }
     return result
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,9 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
-    let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
-    result := { result with validators := validatorsCopy }
+    let result : FormField :=
+      { widget := widgetCopy, errorMessages := messagesCopy,
+        validators := validatorsCopy, carried := source.carried }
     return result
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,9 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
     result := { result with widget := widgetCopy }
     result := { result with errorMessages := messagesCopy }
-    result := { result with validators := validatorsCopy }
     return result
     -- impl-end
 
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,18 +147,11 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
-    let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
-    result := { result with validators := validatorsCopy }
-    return result
+    let w := widgetCopy
+    let m := messagesCopy
+    let v := validatorsCopy
+    let c := source.carried
+    return { widget := w, errorMessages := m, validators := v, carried := c }
     -- impl-end
 
 prove_correct deepCopyField by
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,15 +147,9 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
+    if source.errorMessages.ref != source.validators.ref then
+      result := { result with widget := widgetCopy }
     result := { result with errorMessages := messagesCopy }
     result := { result with validators := validatorsCopy }
     return result
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,16 +147,11 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
     result := { result with widget := widgetCopy }
     result := { result with errorMessages := messagesCopy }
+    result := { result with errorMessages := messagesCopy }
+    result := { result with validators := validatorsCopy }
     result := { result with validators := validatorsCopy }
     return result
     -- impl-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,10 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
     result := { result with errorMessages := messagesCopy }
     result := { result with validators := validatorsCopy }
+    result := { result with widget := widgetCopy }
     return result
     -- impl-end
 
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,17 +147,9 @@
   ensures result.carried        = source.carried
   do
     -- impl-start
-    -- Start from a shallow duplication of the field: the clone initially holds
-    -- the very same attribute objects as the source (duplicating the field
-    -- copies the references, not the objects they point at).
     let mut result := source
-    -- Install, in each slot, PRECISELY the object that slot's copy helper
-    -- returned — the opaque rendering component's copy, the override-message
-    -- table's copy, the validator collection's copy — with nothing interposed
-    -- and nothing altered afterwards.
-    result := { result with widget := widgetCopy }
-    result := { result with errorMessages := messagesCopy }
-    result := { result with validators := validatorsCopy }
+    let installed := { result with widget := widgetCopy, errorMessages := messagesCopy }
+    result := { installed with validators := validatorsCopy }
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, A-legs) on django__django-11880/velvet. Verdict SOUND.

IMPORTANT CONTEXT: the frozen Solution.lean has been REPAIRED since the recorded G-EQ/G-PANEL-2 runs. meta.json's G-EQ/G-PANEL sources record sha256=3e10370eba..., but the file on disk is 3b71c1d18b961689d6ddc135ceed3ec77679990aca8e8d275048c413f23a041e. The prior G-PANEL-2 fail (UNFAITHFUL: freshCopy over-claim on the opaque widget) is FIXED in the artifact I audited: the file now defines `freshDistinct (b a) := b.ref ≠ a.ref` and uses it for the widget leg (require + ensures), with freshCopy retained only for the two value-typed slots. So I audited the repaired bytes; the old counterexample no longer applies and I re-encoded it as atk_7/atk_13 in the new vocabulary.

PROTOCOL. same_spec via swebench_unified.markers.same_spec(velvet) = True for all 14 attacks AND the positive control. variant_scope.unsound_evasions = [] for all 15 (no new axiom/sorry/theorem, obligations preserved), so all 14 are ADMISSIBLE (floor is 5). Verification via `bash scripts/lean_verify.sh <file>`, run 4-at-a-time as background jobs.

POSITIVE CONTROL: pos.lean (byte-identical frozen Solution.lean) -> exit 0 (VERIFIES).
PREPATCH REPRODUCED: atk_1.lean = Solution_prepatch.lean (errorMessages left shallow-shared) -> exit 1, unsolved goal `freshCopy source.errorMessages source.errorMessages` (the F2P discriminator `field_copy.error_messages is not field.error_messages`). Reproduced.

STRUCTURAL FINDING that shapes the battery: the postconditions pin ALL FOUR FormField fields (three derivation clauses `result.X = XCopy` plus `result.carried = source.carried`), so a verifying impl's abstract result is UNIQUELY determined. There is therefore no room for a model-level wrong impl; the only attack surface is (a) the A-leg callee contracts and (b) the model<->patch correspondence at the unmodeled boundary. Both were attacked directly.

REJECTED (9) — each on a genuine clause, not a syntax error:
- atk_2 PARTIAL-DOMAIN (install messagesCopy only when source.errorMessages.ref != 0) -> exit 1, goals `source.errorMessages = messagesCopy`, `freshCopy source.errorMessages source.errorMessages`.
- atk_3 CONTROL-FLOW-EFFECT / last-write-wins (installs the copy then re-points the slot back at the source's own table) -> exit 1, same two goals.
- atk_4 UNGROUNDED-ORACLE ECHO (fabricates ref+1/payload objects instead of installing the helpers' answers; satisfies both freshDistinct and freshCopy but is not the callee's return value) -> exit 1 on all three derivation goals. This is exactly the attack the derivation clauses exist to kill, and they kill it.
- atk_5 CROSS-WIRED slots (messagesCopy and validatorsCopy swapped) -> exit 1, `freshCopy messagesCopy source.validators` etc.
- atk_6 RECONSTRUCTION (builds a fresh field, carried := {0,0}) -> exit 1, `{ref := 0, payload := 0} = source.carried`. The carried-identity leg (A8) does its job.
- atk_7 BOUNDARY, widget left shallow-shared -> exit 1, `freshDistinct source.widget source.widget`.
- atk_9 BOUNDARY, validators left shallow-shared -> exit 1, `freshCopy source.validators source.validators`.
- atk_11 PARTIAL-DOMAIN on the widget leg -> exit 1, `freshDistinct source.widget source.widget`.

VERIFIED (5) — every one had its faithful refined patch materialized as a real diff off base_commit and RUN through the official harness (`python3 -c "from swebench_unified.harness import run_resolve; run_resolve('django__django-11880', patch)"`), 3-then-2 concurrently:
- atk_8 (record built in one step) -> patch_atk8.diff: RESOLVED (attempts=1, flaky=false).
- atk_10 (no shallow duplication; carried threaded explicitly via __class__.__new__ + __dict__.update) -> patch_atk10.diff: RESOLVED (attempts=1). This is the sharpest probe of whether `carried` really pins the shallow copy: the refinement preserves the class and the source's own attribute objects, so it is genuinely correct, and the F2P isinstance assertion passes.
- atk_12 (idempotent double-install; each helper called twice, second answer installed) -> patch_atk12.diff: RESOLVED (attempts=1).
- atk_13 A-LEG CONTRACT GAP on the widget: widgetCopy's ONLY contract is freshDistinct (distinctness), which a SHALLOW `copy.copy(self.widget)` satisfies exactly as well as a deep one — the spec has no clause that can tell them apart. -> patch_atk13.diff: RESOLVED (attempts=1). So the deliberately weakened widget contract does NOT admit an incorrect impl on this instance's graded tests; the gap is real but not exploitable, because the widget deep-vs-shallow distinction is not observed by F2P or the 114 P2P tests.
- atk_14 A3 BOUNDARY (memo bookkeeping dropped entirely, `copy.deepcopy(self.widget)` with no memo — refinement.md A3 declares memo unmodeled) -> patch_atk14.diff: RESOLVED (attempts=1). The A3 'unmodeled' tag is thus safe on the graded surface.
All 5 are CORRECT ECHOES, not weaknesses. No verifying attack failed to resolve => verify=>correct not falsified.

REFINEMENT.MD AUDIT (§3 legs, all A/R/I, no kind-3 — confirmed). Legs: A1,A2,A8 = R; A3,A7 = I; A4,A5,A6 = A-consumed. meta.json deep_model_references=[] so there is no A-reference leg to check, and conf_skip=true is consistent with the all-A-tagged impl. I re-measured the A-legs' correspondence to the REAL callees at base_commit in my worktree (git worktree at 06909fe084f87a65459a83bd69d7cdbe4fce9a7c):
- A4 (copy.deepcopy on the opaque widget, contract freshDistinct = ref-only): 26 instantiable Widget subclasses — deepcopy distinct 26/26, `==` equal 0/26. The ref-only contract is EXACTLY right and the old freshCopy version was indeed an over-claim; the repair is correct and load-bearing.
- A5 (dict.copy, freshCopy): distinct AND equal on empty/singleton/nested — holds.
- A6 (list[:], freshCopy): distinct AND equal on empty/singleton/many/object-element — holds.
- A8 (carried aggregate = IDENTITY): measured on the MODELED callee Field.__deepcopy__ over 14 field classes: class-preserved 14/14, untouched attrs 8-14 per class, SAME object=150, DIFFERENT=0. Reproduces refinement.md's claim exactly. (Note: naive `copy.deepcopy(f)` on ChoiceField shows _choices as a distinct object, but that is ChoiceField.__deepcopy__'s OWN override, not the modeled callee Field.__deepcopy__; A8 is correctly scoped to the modeled function, so this is not a defect.)
- refinement.md §B's two cited measurements REPRODUCE: wipe-the-copied-widget => 18 P2P failures (claimed 18); substitute an unrelated TextInput => 43 failures + 1 error = 44 (claimed 44). A8's reconstruction attack => 3 failures + 95 errors, consistent with the claimed mass P2P breakage.

**MEASUREMENT HYGIENE:** my first local test run silently imported django from an unrelated installed copy, which invalidated it; the runner's 'Testing against Django installed in ...' line is what showed this, and I re-ran everything against my own base_commit worktree. All local figures above are from the intended tree.

CONCLUSION: 14 admissible same-spec attacks; 9 rejected on real clauses; 5 verified and all 5 resolved under the official harness. The derivation clauses kill the ungrounded-oracle echo, the carried-identity clause kills reconstruction, and the two boundary attacks the weakened widget contract genuinely admits (atk_13 shallow widget, atk_14 no memo) are both actually CORRECT. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8.lean`, `atk_10.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 same-spec admissible attacks were run; 9 were REJECTED by the verifier on a genuine clause and 5 VERIFIED. All 5 verifying attacks had their faithful refined patch materialized and RUN through the official harness (swebench_unified.harness.run_resolve): all 5 RESOLVED on attempt 1 (non-flaky), i.e. they are correct echoes of the gold, not spec weaknesses. No verifying wrong impl whose patch fails to resolve exists in this battery, so verify=>correct was not falsified.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, A-legs) on django__django-11880/velvet. Verdict SOUND.

IMPORTANT CONTEXT: the frozen Solution.lean has been REPAIRED since the recorded G-EQ/G-PANEL-2 runs. meta.json's G-EQ/G-PANEL sources record sha256=3e10370eba..., but the file on disk is 3b71c1d18b961689d6ddc135ceed3ec77679990aca8e8d275048c413f23a041e. The prior G-PANEL-2 fail (UNFAITHFUL: freshCopy over-claim on the opaque widget) is FIXED in the artifact I audited: the file now defines `freshDistinct (b a) := b.ref ≠ a.ref` and uses it for the widget leg (require + ensures), with freshCopy retained only for the two value-typed slots. So I audited the repaired bytes; the old counterexample no longer applies and I re-encoded it as atk_7/atk_13 in the new vocabulary.

PROTOCOL. same_spec via swebench_unified.markers.same_spec(velvet) = True for all 14 attacks AND the positive control. variant_scope.unsound_evasions = [] for all 15 (no new axiom/sorry/theorem, obligations preserved), so all 14 are ADMISSIBLE (floor is 5). Verification via `bash scripts/lean_verify.sh <file>`, run 4-at-a-time as background jobs.

POSITIVE CONTROL: pos.lean (byte-identical frozen Solution.lean) -> exit 0 (VERIFIES).
PREPATCH REPRODUCED: atk_1.lean = Solution_prepatch.lean (errorMessages left shallow-shared) -> exit 1, unsolved goal `freshCopy source.errorMessages source.errorMessages` (the F2P discriminator `field_copy.error_messages is not field.error_messages`). Reproduced.

STRUCTURAL FINDING that shapes the battery: the postconditions pin ALL FOUR FormField fields (three derivation clauses `result.X = XCopy` plus `result.carried = source.carried`), so a verifying impl's abstract result is UNIQUELY determined. There is therefore no room for a model-level wrong impl; the only attack surface is (a) the A-leg callee contracts and (b) the model<->patch correspondence at the unmodeled boundary. Both were attacked directly.

REJECTED (9) — each on a genuine clause, not a syntax error:
- atk_2 PARTIAL-DOMAIN (install messagesCopy only when source.errorMessages.ref != 0) -> exit 1, goals `source.errorMessages = messagesCopy`, `freshCopy source.errorMessages source.errorMessages`.
- atk_3 CONTROL-FLOW-EFFECT / last-write-wins (installs the copy then re-points the slot back at the source's own table) -> exit 1, same two goals.
- atk_4 UNGROUNDED-ORACLE ECHO (fabricates ref+1/payload objects instead of installing the helpers' answers; satisfies both freshDistinct and freshCopy but is not the callee's return value) -> exit 1 on all three derivation goals. This is exactly the attack the derivation clauses exist to kill, and they kill it.
- atk_5 CROSS-WIRED slots (messagesCopy and validatorsCopy swapped) -> exit 1, `freshCopy messagesCopy source.validators` etc.
- atk_6 RECONSTRUCTION (builds a fresh field, carried := {0,0}) -> exit 1, `{ref := 0, payload := 0} = source.carried`. The carried-identity leg (A8) does its job.
- atk_7 BOUNDARY, widget left shallow-shared -> exit 1, `freshDistinct source.widget source.widget`.
- atk_9 BOUNDARY, validators left shallow-shared -> exit 1, `freshCopy source.validators source.validators`.
- atk_11 PARTIAL-DOMAIN on the widget leg -> exit 1, `freshDistinct source.widget source.widget`.

VERIFIED (5) — every one had its faithful refined patch materialized as a real diff off base_commit and RUN through the official harness (`python3 -c "from swebench_unified.harness import run_resolve; run_resolve('django__django-11880', patch)"`), 3-then-2 concurrently:
- atk_8 (record built in one step) -> patch_atk8.diff: RESOLVED (attempts=1, flaky=false).
- atk_10 (no shallow duplication; carried threaded explicitly via __class__.__new__ + __dict__.update) -> patch_atk10.diff: RESOLVED (attempts=1). This is the sharpest probe of whether `carried` really pins the shallow copy: the refinement preserves the class and the source's own attribute objects, so it is genuinely correct, and the F2P isinstance assertion passes.
- atk_12 (idempotent double-install; each helper called twice, second answer installed) -> patch_atk12.diff: RESOLVED (attempts=1).
- atk_13 A-LEG CONTRACT GAP on the widget: widgetCopy's ONLY contract is freshDistinct (distinctness), which a SHALLOW `copy.copy(self.widget)` satisfies exactly as well as a deep one — the spec has no clause that can tell them apart. -> patch_atk13.diff: RESOLVED (attempts=1). So the deliberately weakened widget contract does NOT admit an incorrect impl on this instance's graded tests; the gap is real but not exploitable, because the widget deep-vs-shallow distinction is not observed by F2P or the 114 P2P tests.
- atk_14 A3 BOUNDARY (memo bookkeeping dropped entirely, `copy.deepcopy(self.widget)` with no memo — refinement.md A3 declares memo unmodeled) -> patch_atk14.diff: RESOLVED (attempts=1). The A3 'unmodeled' tag is thus safe on the graded surface.
All 5 are CORRECT ECHOES, not weaknesses. No verifying attack failed to resolve => verify=>correct not falsified.

REFINEMENT.MD AUDIT (§3 legs, all A/R/I, no kind-3 — confirmed). Legs: A1,A2,A8 = R; A3,A7 = I; A4,A5,A6 = A-consumed. meta.json deep_model_references=[] so there is no A-reference leg to check, and conf_skip=true is consistent with the all-A-tagged impl. I re-measured the A-legs' correspondence to the REAL callees at base_commit in my worktree (git worktree at 06909fe084f87a65459a83bd69d7cdbe4fce9a7c):
- A4 (copy.deepcopy on the opaque widget, contract freshDistinct = ref-only): 26 instantiable Widget subclasses — deepcopy distinct 26/26, `==` equal 0/26. The ref-only contract is EXACTLY right and the old freshCopy version was indeed an over-claim; the repair is correct and load-bearing.
- A5 (dict.copy, freshCopy): distinct AND equal on empty/singleton/nested — holds.
- A6 (list[:], freshCopy): distinct AND equal on empty/singleton/many/object-element — holds.
- A8 (carried aggregate = IDENTITY): measured on the MODELED callee Field.__deepcopy__ over 14 field classes: class-preserved 14/14, untouched attrs 8-14 per class, SAME object=150, DIFFERENT=0. Reproduces refinement.md's claim exactly. (Note: naive `copy.deepcopy(f)` on ChoiceField shows _choices as a distinct object, but that is ChoiceField.__deepcopy__'s OWN override, not the modeled callee Field.__deepcopy__; A8 is correctly scoped to the modeled function, so this is not a defect.)
- refinement.md §B's two cited measurements REPRODUCE: wipe-the-copied-widget => 18 P2P failures (claimed 18); substitute an unrelated TextInput => 43 failures + 1 error = 44 (claimed 44). A8's reconstruction attack => 3 failures + 95 errors, consistent with the claimed mass P2P breakage.

**MEASUREMENT HYGIENE:** my first local test run silently imported django from an unrelated installed copy, which invalidated it; the runner's 'Testing against Django installed in ...' line is what showed this, and I re-ran everything against my own base_commit worktree. All local figures above are from the intended tree.

CONCLUSION: 14 admissible same-spec attacks; 9 rejected on real clauses; 5 verified and all 5 resolved under the official harness. The derivation clauses kill the ungrounded-oracle echo, the carried-identity clause kills reconstruction, and the two boundary attacks the weakened widget contract genuinely admits (atk_13 shallow widget, atk_14 no memo) are both actually CORRECT. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Attacker 2 (faithfulness-break) on django__django-11880/velvet. All measurements my own, this session. Reference =, base 06909fe084 with patch.diff APPLIED (verified: `git diff --stat` = django/forms/fields.py | 1 +, and fields.py:202 holds `result.error_messages = self.error_messages.copy()`).

NO DIVERGING INPUT FOUND. Modeled callee = Field.__deepcopy__ (django/forms/fields.py:198), invoked DIRECTLY (not via copy.deepcopy, which dispatches subclass overrides) per mapping.md §1.

(1) ALL FOUR ensures HOLD ON THE REAL PATCHED CALLEE — 28 instantiable Field subclasses, zero violations:
  * freshDistinct result.widget source.widget — id(r.widget) != id(f.widget), 28/28
  * freshCopy result.errorMessages source.errorMessages — `is not` AND `==`, 28/28
  * freshCopy result.validators source.validators — `is not` AND `==`, 28/28
  * result.carried = source.carried — class preserved AND every untouched attr is the SAME object (8–14 attrs/class), 28/28
Also holds under full copy.deepcopy on the override subclasses (ChoiceField, MultiValueField, SplitDateTimeField, TypedChoiceField, MultipleChoiceField) and across a 5-field Form's base_fields with a shared memo.

(2) NO OVER-CLAIM ON THE OPAQUE WIDGET (the exact defect the stale prior fail cited). Current spec uses ref-only `freshDistinct` for the widget — it does NOT assert content equality — so the `deepcopy(w) == w` is False fact is NOT claimed. Confirmed empirically: 27/27 widget classes in django.forms.widgets give deepcopy(w) is not w (distinctness always holds); the stronger EQ clause is absent from the spec. All four widget __deepcopy__ implementations (widgets.py:203/564/875, contrib/admin/widgets.py:261) begin with `copy.copy(self)`, so distinctness holds by construction, universally.

(3) REQUIRE CONTRACTS SOUND vs REAL CALLEES. dict.copy() and list[:] give distinct+equal on boundary cases (empty, singleton, 50-entry, nested, NaN, custom-never-eq __eq__ — == holds via CPython's identity fast-path). Probed two candidate require-breaks and found BOTH UNREACHABLE in the real repo: (a) hand-seeded memo {id(w): w} makes deepcopy return the same widget — but copy.deepcopy's memo only ever maps original→copy, never object→itself (verified: atomic types aren't memoized at all, memo keys=0), and Field.__deepcopy__ seeds only memo[id(self)]=result (the field, not the widget); (b) non-Widget widget (42, 'x') is REJECTED by Field.__init__ with AttributeError ('is_required'), and error_messages/validators are always built as a plain dict/list in __init__ (fields.py:111,113) — no tuple `[:]` identity fast-path is reachable. Repo-wide grep of `.widget =` / `.error_messages =` assignments shows no path producing a non-dict/non-Widget.

(4) SOURCE NOT MUTATED — `source` correctly non-mut: all source attr identities, error_messages contents, widget id and validators unchanged across the call (incl. USE_I18N=True with gettext_lazy __proxy__ values, where dict.copy() content-equality still holds).

(5) CARRIED CLAUSE CORRECTLY SCOPED, not over-strong. On the MODELED callee, carried identity holds for every class. The subclass overrides that DO re-point extra attrs (ChoiceField._choices, MultiValueField.fields) live in ChoiceField/MultiValueField.__deepcopy__ (fields.py:768, 986), functions the patch does not touch and which mapping.md does not model — so this is not a divergence of the modeled function.

(6) DISCRIMINATOR IS EXACTLY THE PATCH DELTA. Solution.lean verifies (lean_verify.sh exit 0, positive control). Solution_prepatch.lean fails exit 1 on precisely `ensures_3: result.errorMessages = messagesCopy` and `ensures_6: freshCopy result.errorMessages source.errorMessages` — the added dict.copy() line, i.e. the F2P assertion. Manually reproduced the (absent-at-base) F2P test: isinstance(field_copy, CustomCharField)=True, field_copy.error_messages is not field.error_messages=True, == True. 114/114 forms_tests.tests.test_forms P2P pass in the reference worktree.

(7) SPEC REGION BYTE-IDENTICAL: swebench_unified.markers.same_spec(gold, prepatch, velvet_backend) = True; axioms/pure/spec_view hashes match exactly (only `impl` differs), so the prepatch failure is attributable to the impl delta alone and not to a contract edit.

STALE PRIOR FINDING, NOT RE-RECORDED: meta.json's G-PANEL-2 status=fail was recorded 12:59 against Solution.lean sha 3e10370eb…; the current file is 3b71c1d18… (G-GOLD/G-DIFF 15:44). That fail cited `freshCopy` on the widget over-claiming content equality, and its own repair control prescribed weakening to `freshDistinct` while preserving the F2P discriminator. The current spec IS that repair (lines 138/141: freshDistinct + derivation clause `result.widget = widgetCopy`), and I re-ran the repair control's logic: the prepatch still fails on the error_messages leg. Re-judging that already-repaired defect as a fresh divergence would invent spec weakness against a superseded artifact.

CONCLUSION: the spec is not too strong and does not drift. Every ensures is satisfied by the real patched callee on all 28 field classes; every require is the weakest contract sound for its real callee, with the only violations requiring inputs unconstructible through the repo's own API. No input exists on which the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Attacker 3 (leakage / gold-reconstruction) on django__django-11880/velvet. Every measurement below is my own, run this session on the CURRENT bytes.

BYTES UNDER REVIEW (matters here -- see STALE RECORDS). sha256(Solution.lean)=3b71c1d18b961689d6ddc135ceed3ec77679990aca8e8d275048c413f23a041e, sha256(Solution_prepatch.lean)=f640366e95ac24e5433273eab1a3ffe318ca2ca12edb5674bea8d393b63f4dbb. These match meta.json gates.G-LEAK/G-VERIFY/G-DIFF sources (all stamped 2026-08-15T15:44-15:46, code_version df49b939b), so the live gates I lean on ran on the bytes I read.

NO RELAXATION PRESENT. meta.json has no `relaxed_leakage` key (top-level keys: axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, object_identity_modeling, pbt_audit, repo, schema_version, spec_provenance, version) and there is no RELAXED_LEAKAGE.md anywhere in the bundle dir. So this is a strict-mode judgement with no disposition to inherit or re-derive; the facet framing does not apply.

SPEC REGION BYTE-IDENTITY. markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) = True. markers.spec_signature on both returns identical text. Velvet tables (flavor=lean, no `proof` region) => impl region elided + prove_correct tactic body elided; the two files differ only inside impl-start/impl-end. Nothing edit-specific survives into the view via the elided region.

MECHANICAL SCREEN, re-run by me. leakage.screen(Solution.lean, VelvetBackend, gold_patch, problem_statement, test_patch) -> hard_failures=[], warnings=[]. Cross-checked its inputs by hand rather than trusting the pass: the sole gold changed line `result.error_messages = self.error_messages.copy()` is absent from the view normalized or otherwise; `django/forms/fields.py` and dotted `django.forms.fields` absent; the only symbol _patch_changed_symbols extracts is `deepcopy`, which IS public in the problem_statement ("The __deepcopy__ method defined for the formfields"), so `deepCopyField`/`deepcopy` in the view are EXEMPT rather than merely tolerated. No diff markers; no _NARRATION hits. Direct greps of the view for fix/bug/patch/gold/added/missing/previously/regression/omit/f2p/test/ticket/commit/'before the change'/'was not': zero hits. Only substantive hits are `deepcopy`, `shallow`, `override`, `field`, `copy` -- and shallow/deepcopy/field/copy are all verbatim in the problem_statement.

GOLD-RECONSTRUCTION READ (my own, beyond the screen). The gold edit is one line adding an independent copy of error_messages. The problem_statement discloses that edit essentially in full: it names __deepcopy__, states it "performs a shallow copy of self and does not include additional treatment for the error_messages dictionary", and that "all copies of the same field share the same dictionary and any modification ... is immediately reflected on all other formfields". So the identity discriminator ON THE ERROR-MESSAGE TABLE is public, not spec-supplied. Two checks on whether the view adds anything:

(1) The strings `error_messages`, `dictionary`, `share` do NOT appear in the view at all -- it says "table of override messages" / `errorMessages`. So the view is strictly less explicit than the public issue on the touched attribute.

(2) The view IS asymmetric across the three slots (widget gets `freshDistinct` = ref-only; errorMessages and validators get `freshCopy` = ref+payload). I checked whether that asymmetry localizes the edit: it does NOT. The split is widget vs {errorMessages, validators}, and validators is UNTOUCHED by the patch, so the strengthened group does not single out the edited slot. The split is justified by a type property (dict/list define value equality, a widget does not) that holds independently of the patch, and mapping.md/refinement.md derive it that way. `widget` and `validator` appear in the view but not in the problem_statement -- these are pre-patch base_commit source lines (`result.widget = copy.deepcopy(...)`, `result.validators = self.validators[:]`) that the issue links to by file+line, i.e. repo state a solver reads, not gold content. Naming them widens the obligation to a superset of the edit; it does not point at it.

LOAD-BEARING TEST (strip-the-narration control, the test that matters). scripts/lean_verify.sh Solution.lean -> EXIT=0. scripts/lean_verify.sh Solution_prepatch.lean -> fails with `unsolved goals` on exactly two cases, BOTH on the errorMessages leg: `ensures_6: freshCopy result.errorMessages source.errorMessages` reducing to `freshCopy source.errorMessages source.errorMessages` (the ref-inequality conjunct becoming x != x), and `ensures_3: result.errorMessages = messagesCopy`. So the errorMessages clause is a genuine proof obligation the PRE-patch impl cannot discharge -- the spec does NOT verify against the pre-patch impl, which is the direction that matters. The discriminator is real and it is the public one.

NO REVIEWER-DIRECTED CONTENT IN THE ARTIFACTS. Ran leakage.reviewer_directed() over every regular file (Solution.lean, Solution_prepatch.lean, conformance_check.py, mapping.md, meta.json, properties.py, refinement.md, verdict.md): all clean. Greped for attacker/reviewer/auditor/panel/judge/NO-LEAKAGE/'honest verdict'/'should record'/'you must submit'. Hits exist ONLY in meta.json gates.G-PANEL* and verdict.md, and they are prior panel runs' own recorded verdicts and notes (the pipeline's log), not the bundle instructing me. Nothing in this bundle addresses me or tells me what to submit; no finding on that axis.

STALE RECORDS -- flagged, does not change my verdict. verdict.md and meta.json gates.G-PANEL-2/G-PANEL-3 judged an EARLIER artifact: both cite sha256 3e10370eba... and verdict.md asserts `grep -c freshDistinct Solution.lean` = 0 with the widget over-claimed as freshCopy. On the current bytes (3b71c1d1...) freshDistinct IS defined and used, appearing 3x, and the widget slot carries exactly the ref-only contract that verdict.md's own FIX section prescribed. So the recorded G-PANEL-2 `fail` (UNFAITHFUL, widget content over-claim) describes a defect that has since been repaired, and G-PANEL-3's recorded note likewise flagged it as an out-of-facet observation against the old bytes. I did not inherit either; my verdict is on 3b71c1d1.

Two hygiene items for the owning lanes, neither a leakage matter: (a) G-PANEL-2/verdict.md are stale-fail and should be re-run against the current sha before being read as findings; (b) G-AX is status=skip with detail 'no axiom_check.py (no axioms in bundle)' while meta.json.axioms declares two contracts and axiom_check.py is absent from the dir -- since the impl is all-A-tagged and G-CONF is a documented skip, the freshDistinct/freshCopy callee contracts currently have no executable grounding. That is a soundness-coverage gap for the G-AX/G-PANEL-2 lanes.

VERDICT: NO-LEAKAGE. The spec view reproduces no gold-patch line, no patched file or module path, no diff marker, no fix/bug narration, and no non-public patched symbol; it is strictly LESS explicit than the public problem_statement about the touched attribute (never says error_messages/dictionary/shared); its one asymmetry groups the edited slot with an untouched one and is derived from a patch-independent type property; and its discriminator -- the clone's message table must be a distinct object holding equal contents -- is derivable from the problem_statement alone, which states the shared-dictionary defect outright.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
